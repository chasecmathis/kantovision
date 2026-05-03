"""WebSocket message handlers for battle operations."""

from __future__ import annotations

import logging

from app.battle.db import fetch_team, save_result
from app.battle.engine import resolve_turn
from app.battle.manager import (
    create_battle,
    get_battle,
    get_battle_by_user,
    remove_battle,
    submit_move,
    update_battle,
)
from app.battle.matchmaking import dequeue, enqueue, try_match
from app.battle.state import BattleStatus
from app.config import get_settings
from app.sockets.caches import cache_battle_end
from app.sockets.connections import manager
from app.sockets.message_types import (
    MSG_BATTLE_END,
    MSG_BATTLE_START,
    MSG_ERROR,
    MSG_MATCH_FOUND,
    MSG_MOVE_RECEIVED,
    MSG_OPPONENT_DISCONNECTED,
    MSG_QUEUE_JOINED,
    MSG_QUEUE_LEFT,
    MSG_TURN_RESULT,
)
from app.sockets.serializers import serialize_battle_state
from app.sockets.timers import (
    cancel_move_timeout,
    clear_turn_timestamp,
    opponent_id,
    start_grace_period,
    start_turn_timers,
)

logger = logging.getLogger(__name__)


async def handle_join_queue(user_id: str, data: dict) -> None:
    team_id = data.get("team_id")
    if not team_id:
        await manager.send_to_user(user_id, {"type": MSG_ERROR, "message": "team_id required"})
        return

    if get_battle_by_user(user_id):
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Already in an active battle"}
        )
        return

    enqueue(user_id, team_id)
    match = try_match()

    if match is None:
        await manager.send_to_user(user_id, {"type": MSG_QUEUE_JOINED})
        return

    entry1, entry2 = match
    try:
        team1 = await fetch_team(entry1.team_id, entry1.user_id)
        team2 = await fetch_team(entry2.team_id, entry2.user_id)
    except Exception:
        logger.exception(
            "Failed to load teams for match (user1=%s, user2=%s) — re-queuing",
            entry1.user_id,
            entry2.user_id,
        )
        enqueue(entry1.user_id, entry1.team_id)
        enqueue(entry2.user_id, entry2.team_id)
        for uid in [entry1.user_id, entry2.user_id]:
            await manager.send_to_user(
                uid, {"type": MSG_ERROR, "message": "Failed to load team data"}
            )
        return

    state = create_battle(entry1, entry2, team1, team2)
    logger.info(
        "Match found: battle_id=%s player1=%s player2=%s",
        state.id,
        entry1.user_id,
        entry2.user_id,
    )

    await manager.join_room(state.id, entry1.user_id)
    await manager.join_room(state.id, entry2.user_id)

    for uid, opp in [(entry1.user_id, entry2.user_id), (entry2.user_id, entry1.user_id)]:
        await manager.send_to_user(
            uid,
            {
                "type": MSG_MATCH_FOUND,
                "battle_id": state.id,
                "opponent_id": opp,
            },
        )

    turn_started_at = start_turn_timers(
        state.id, entry1.user_id, entry2.user_id, on_forfeit=handle_forfeit
    )

    await manager.broadcast_to_room(
        state.id,
        {
            "type": MSG_BATTLE_START,
            "battle_id": state.id,
            "state": serialize_battle_state(state),
            "turn_started_at": turn_started_at,
        },
    )


async def handle_leave_queue(user_id: str) -> None:
    dequeue(user_id)
    await manager.send_to_user(user_id, {"type": MSG_QUEUE_LEFT})


async def handle_make_move(user_id: str, data: dict) -> None:
    battle_id = data.get("battle_id")
    move_slot = data.get("move_slot")

    if not battle_id or move_slot is None:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "battle_id and move_slot required"}
        )
        return

    state = get_battle(battle_id)
    if not state or state.status != BattleStatus.ACTIVE:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Battle not found or already ended"}
        )
        return

    if user_id != state.player1.user_id and user_id != state.player2.user_id:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Not a participant in this battle"}
        )
        return

    # Validate move_slot is in bounds for the active Pokémon
    player = state.player1 if user_id == state.player1.user_id else state.player2
    active_mon = player.team[player.active_index]
    move_slot_int = int(move_slot)
    if move_slot_int < 0 or move_slot_int >= len(active_mon.moves):
        await manager.send_to_user(
            user_id,
            {
                "type": MSG_ERROR,
                "message": (
                    f"Invalid move_slot {move_slot_int} (Pokémon has {len(active_mon.moves)} moves)"
                ),
            },
        )
        return

    # Ignore duplicate moves from the same player
    if user_id in state.pending_moves:
        return

    both_ready = submit_move(battle_id, user_id, move_slot_int)
    cancel_move_timeout(user_id)

    if not both_ready:
        await manager.broadcast_to_room(battle_id, {"type": MSG_MOVE_RECEIVED, "user_id": user_id})
        return

    # Both moves are in — resolve the turn
    state = get_battle(battle_id)  # re-fetch after mutation
    if not state:
        return

    p1_move = state.pending_moves.get(state.player1.user_id, 0)
    p2_move = state.pending_moves.get(state.player2.user_id, 0)

    result = resolve_turn(state, p1_move, p2_move)
    update_battle(result.new_state)

    logger.info("Turn %d resolved in battle_id=%s", result.new_state.turn, battle_id)

    if result.battle_over:
        clear_turn_timestamp(battle_id)
        cache_battle_end(result.new_state, "all_fainted")
        await manager.broadcast_to_room(
            battle_id,
            {
                "type": MSG_TURN_RESULT,
                "log": result.log_entries,
                "state": serialize_battle_state(result.new_state),
            },
        )
        logger.info(
            "Battle ended: battle_id=%s winner=%s turns=%d",
            battle_id,
            result.winner_id,
            result.new_state.turn,
        )
        await manager.broadcast_to_room(
            battle_id,
            {
                "type": MSG_BATTLE_END,
                "winner_id": result.winner_id,
                "reason": "all_fainted",
            },
        )
        await save_result(result.new_state)
        await manager.leave_room(battle_id)
        remove_battle(battle_id)
    else:
        turn_started_at = start_turn_timers(
            battle_id,
            result.new_state.player1.user_id,
            result.new_state.player2.user_id,
            on_forfeit=handle_forfeit,
        )
        await manager.broadcast_to_room(
            battle_id,
            {
                "type": MSG_TURN_RESULT,
                "log": result.log_entries,
                "state": serialize_battle_state(result.new_state),
                "turn_started_at": turn_started_at,
            },
        )


async def handle_forfeit(user_id: str, data: dict) -> None:
    battle_id = data.get("battle_id")
    if not battle_id:
        return

    state = get_battle(battle_id)
    if not state or state.status != BattleStatus.ACTIVE:
        return

    winner_id = opponent_id(state, user_id)
    state.status = BattleStatus.ENDED
    state.winner_id = winner_id

    # Cancel any pending move timeouts for both players
    cancel_move_timeout(state.player1.user_id)
    cancel_move_timeout(state.player2.user_id)

    logger.info(
        "Battle forfeited: battle_id=%s forfeiter=%s winner=%s", battle_id, user_id, winner_id
    )

    clear_turn_timestamp(battle_id)
    cache_battle_end(state, "forfeit")
    await manager.broadcast_to_room(
        battle_id,
        {
            "type": MSG_BATTLE_END,
            "winner_id": winner_id,
            "reason": "forfeit",
        },
    )
    await save_result(state)
    await manager.leave_room(battle_id)
    remove_battle(battle_id)


async def handle_disconnect(user_id: str) -> None:
    """On disconnect, start a grace period instead of forfeiting immediately."""
    settings = get_settings()
    state = get_battle_by_user(user_id)
    if not state or state.status != BattleStatus.ACTIVE:
        return

    logger.info("User disconnected from active battle: user_id=%s battle_id=%s", user_id, state.id)
    await manager.send_to_user(
        opponent_id(state, user_id),
        {
            "type": MSG_OPPONENT_DISCONNECTED,
            "message": (
                f"Opponent disconnected. Waiting {settings.ws_grace_period_seconds}s for reconnect."
            ),
        },
    )
    start_grace_period(user_id, state.id, on_forfeit=handle_forfeit)

"""WebSocket message handlers for battle operations."""

from __future__ import annotations

import logging

from app.battle.actions import Action, MoveAction, SwitchAction
from app.battle.db import fetch_team, save_result
from app.battle.engine import TurnEngine
from app.battle.manager import (
    create_battle,
    get_battle,
    get_battle_by_user,
    remove_battle,
    submit_action,
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
    MSG_FORCED_SWITCH,
    MSG_MATCH_FOUND,
    MSG_MOVE_RECEIVED,
    MSG_OPPONENT_DISCONNECTED,
    MSG_QUEUE_JOINED,
    MSG_QUEUE_LEFT,
    MSG_TEAM_PREVIEW,
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
    # Start in team preview phase
    state.status = BattleStatus.TEAM_PREVIEW
    update_battle(state)

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

    # Send team preview instead of battle_start
    await manager.broadcast_to_room(
        state.id,
        {
            "type": MSG_TEAM_PREVIEW,
            "battle_id": state.id,
            "state": serialize_battle_state(state),
        },
    )


async def handle_select_lead(user_id: str, data: dict) -> None:
    """Handle a player's lead selection during team preview."""
    battle_id = data.get("battle_id")
    lead_index = data.get("lead_index", 0)

    if not battle_id:
        await manager.send_to_user(user_id, {"type": MSG_ERROR, "message": "battle_id required"})
        return

    state = get_battle(battle_id)
    if not state or state.status != BattleStatus.TEAM_PREVIEW:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Not in team preview phase"}
        )
        return

    if user_id != state.player1.user_id and user_id != state.player2.user_id:
        await manager.send_to_user(user_id, {"type": MSG_ERROR, "message": "Not a participant"})
        return

    player = state.player1 if user_id == state.player1.user_id else state.player2
    lead_index = int(lead_index)
    if lead_index < 0 or lead_index >= len(player.team):
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": f"Invalid lead_index {lead_index}"}
        )
        return

    if player.team[lead_index].fainted:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Cannot select a fainted lead"}
        )
        return

    # Record selection
    state.lead_selections[user_id] = lead_index
    update_battle(state)

    # If both have selected, start the battle
    if len(state.lead_selections) == 2:
        # Apply lead selections
        for uid, idx in state.lead_selections.items():
            p = state.player1 if uid == state.player1.user_id else state.player2
            p.active_index = idx

        state.status = BattleStatus.ACTIVE
        state.lead_selections.clear()
        update_battle(state)

        turn_started_at = start_turn_timers(
            state.id,
            state.player1.user_id,
            state.player2.user_id,
            on_forfeit=handle_forfeit,
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
    else:
        # Notify opponent that we're waiting
        await manager.broadcast_to_room(battle_id, {"type": MSG_MOVE_RECEIVED, "user_id": user_id})


async def handle_leave_queue(user_id: str) -> None:
    dequeue(user_id)
    await manager.send_to_user(user_id, {"type": MSG_QUEUE_LEFT})


async def handle_make_action(user_id: str, data: dict) -> None:
    battle_id = data.get("battle_id")
    action_data = data.get("action")

    if not battle_id or not action_data:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "battle_id and action required"}
        )
        return

    state = get_battle(battle_id)
    if not state or state.status != BattleStatus.ACTIVE:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Battle not found or already ended"}
        )
        return

    # Reject actions while waiting for forced switches
    if state.awaiting_switch:
        await manager.send_to_user(
            user_id,
            {"type": MSG_ERROR, "message": "Waiting for forced switch selection"},
        )
        return

    if user_id != state.player1.user_id and user_id != state.player2.user_id:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Not a participant in this battle"}
        )
        return

    player = state.player1 if user_id == state.player1.user_id else state.player2
    active_mon = player.team[player.active_index]

    action_type = action_data.get("type")

    if action_type == "move":
        move_index = action_data.get("move_index", 0)
        move_index = int(move_index)
        if move_index < 0 or move_index >= len(active_mon.moves):
            await manager.send_to_user(
                user_id,
                {
                    "type": MSG_ERROR,
                    "message": (
                        f"Invalid move_index {move_index}"
                        f" (has {len(active_mon.moves)} moves)"
                    ),
                },
            )
            return
    elif action_type == "switch":
        switch_to = action_data.get("switch_to_index")
        if switch_to is None:
            await manager.send_to_user(
                user_id, {"type": MSG_ERROR, "message": "switch_to_index required"}
            )
            return
        switch_to = int(switch_to)
        if switch_to < 0 or switch_to >= len(player.team):
            await manager.send_to_user(
                user_id, {"type": MSG_ERROR, "message": f"Invalid switch_to_index {switch_to}"}
            )
            return
        if switch_to == player.active_index:
            await manager.send_to_user(
                user_id, {"type": MSG_ERROR, "message": "Cannot switch to current active Pokémon"}
            )
            return
        if player.team[switch_to].fainted:
            await manager.send_to_user(
                user_id, {"type": MSG_ERROR, "message": "Cannot switch to a fainted Pokémon"}
            )
            return
    else:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": f"Unknown action type: {action_type!r}"}
        )
        return

    # Ignore duplicate actions from the same player
    if user_id in state.pending_actions:
        return

    both_ready = submit_action(battle_id, user_id, action_data)
    cancel_move_timeout(user_id)

    if not both_ready:
        await manager.broadcast_to_room(battle_id, {"type": MSG_MOVE_RECEIVED, "user_id": user_id})
        return

    # Both actions are in — resolve the turn
    state = get_battle(battle_id)  # re-fetch after mutation
    if not state:
        return

    p1_action_data = state.pending_actions.get(
        state.player1.user_id, {"type": "move", "move_index": 0}
    )
    p2_action_data = state.pending_actions.get(
        state.player2.user_id, {"type": "move", "move_index": 0}
    )

    action_p1 = _parse_action(state.player1.user_id, p1_action_data)
    action_p2 = _parse_action(state.player2.user_id, p2_action_data)

    engine = TurnEngine()
    result = engine.resolve_turn(state, action_p1, action_p2)
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
    elif result.forced_switches:
        # Some players need to pick a replacement
        new_state = result.new_state
        new_state.awaiting_switch = set(result.forced_switches)
        update_battle(new_state)

        await manager.broadcast_to_room(
            battle_id,
            {
                "type": MSG_TURN_RESULT,
                "log": result.log_entries,
                "state": serialize_battle_state(new_state),
            },
        )

        # Send forced_switch to each player that needs to choose
        for uid in result.forced_switches:
            player = new_state.player1 if uid == new_state.player1.user_id else new_state.player2
            available = [
                {"index": i, "name": m.name, "species_id": m.species_id}
                for i, m in enumerate(player.team)
                if not m.fainted
            ]
            await manager.send_to_user(
                uid,
                {
                    "type": MSG_FORCED_SWITCH,
                    "battle_id": battle_id,
                    "available": available,
                },
            )
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


async def handle_submit_switch(user_id: str, data: dict) -> None:
    """Handle a forced switch selection after a faint."""
    battle_id = data.get("battle_id")
    switch_to = data.get("switch_to_index")

    if not battle_id or switch_to is None:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "battle_id and switch_to_index required"}
        )
        return

    state = get_battle(battle_id)
    if not state or state.status != BattleStatus.ACTIVE:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Battle not found or not active"}
        )
        return

    if user_id not in state.awaiting_switch:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Not awaiting a switch from you"}
        )
        return

    switch_to = int(switch_to)
    player = state.player1 if user_id == state.player1.user_id else state.player2

    if switch_to < 0 or switch_to >= len(player.team):
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": f"Invalid switch_to_index {switch_to}"}
        )
        return
    if player.team[switch_to].fainted:
        await manager.send_to_user(
            user_id, {"type": MSG_ERROR, "message": "Cannot switch to a fainted Pokémon"}
        )
        return

    # Apply the forced switch via engine
    engine = TurnEngine()
    result = engine.apply_forced_switch(state, user_id, switch_to)
    update_battle(result.new_state)

    # Remove from awaiting set
    result.new_state.awaiting_switch.discard(user_id)

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
        return

    if result.needs_switch:
        # Switched-in mon fainted from hazards, need another pick
        result.new_state.awaiting_switch.add(user_id)
        update_battle(result.new_state)

        await manager.broadcast_to_room(
            battle_id,
            {
                "type": MSG_TURN_RESULT,
                "log": result.log_entries,
                "state": serialize_battle_state(result.new_state),
            },
        )
        available = [
            {"index": i, "name": m.name, "species_id": m.species_id}
            for i, m in enumerate(player.team)
            if not m.fainted
        ]
        await manager.send_to_user(
            user_id,
            {
                "type": MSG_FORCED_SWITCH,
                "battle_id": battle_id,
                "available": available,
            },
        )
        return

    update_battle(result.new_state)

    # Broadcast the switch result
    await manager.broadcast_to_room(
        battle_id,
        {
            "type": MSG_TURN_RESULT,
            "log": result.log_entries,
            "state": serialize_battle_state(result.new_state),
        },
    )

    # If all forced switches resolved, start the next turn
    if not result.new_state.awaiting_switch:
        turn_started_at = start_turn_timers(
            battle_id,
            result.new_state.player1.user_id,
            result.new_state.player2.user_id,
            on_forfeit=handle_forfeit,
        )
        # Send a turn_result with the timer to signal turn start
        await manager.broadcast_to_room(
            battle_id,
            {
                "type": MSG_TURN_RESULT,
                "log": [],
                "state": serialize_battle_state(result.new_state),
                "turn_started_at": turn_started_at,
            },
        )


def _parse_action(player_id: str, action_data: dict) -> Action:
    """Convert a raw action dict into a typed Action object."""
    if action_data.get("type") == "switch":
        return SwitchAction(
            player_id=player_id,
            switch_to_index=int(action_data["switch_to_index"]),
        )
    return MoveAction(
        player_id=player_id,
        move_index=int(action_data.get("move_index", 0)),
    )


async def handle_forfeit(user_id: str, data: dict) -> None:
    battle_id = data.get("battle_id")
    if not battle_id:
        return

    state = get_battle(battle_id)
    if not state or state.status not in (BattleStatus.ACTIVE, BattleStatus.TEAM_PREVIEW):
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
    if not state or state.status not in (BattleStatus.ACTIVE, BattleStatus.TEAM_PREVIEW):
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

from __future__ import annotations

import asyncio
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.battle.engine import resolve_turn
from app.battle.manager import (
    create_battle,
    get_battle,
    get_battle_by_user,
    remove_battle,
    submit_move,
    update_battle,
)
from app.battle.matchmaking import dequeue, enqueue, is_queued, try_match
from app.battle.state import BattleState, MoveSlot, PlayerState, PokemonBattleState, StoredSlot
from app.config import get_settings
from app.database import get_db
from app.dependencies import UserIdDep
from app.repositories import move_repo
from app.sockets.connections import manager
from app.sockets.tickets import consume_ticket, issue_ticket

logger = logging.getLogger(__name__)
router = APIRouter(tags=["battle-ws"])

# ─── Per-connection rate limiter ──────────────────────────────────────────────

# user_id → list of recent message timestamps (monotonic clock)
_rate_windows: dict[str, list[float]] = {}


def _is_rate_limited(user_id: str) -> bool:
    """Return True if the user has exceeded ws_rate_limit_per_second messages/s."""
    settings = get_settings()
    limit = settings.ws_rate_limit_per_second
    now = asyncio.get_running_loop().time()
    window = _rate_windows.setdefault(user_id, [])
    # Prune timestamps older than 1 second
    _rate_windows[user_id] = [t for t in window if now - t < 1.0]
    _rate_windows[user_id].append(now)
    return len(_rate_windows[user_id]) > limit


# ─── Stat calculation (level 50) ─────────────────────────────────────────────


def _stat(base: int, iv: int, ev: int, *, is_hp: bool = False) -> int:
    inner = (2 * base + iv + ev // 4) * 50 // 100
    return inner + 60 if is_hp else inner + 5


async def _build_pokemon(slot: StoredSlot) -> PokemonBattleState:
    b = slot.base_stats
    iv = slot.ivs
    ev = slot.evs

    move_names = [n for n in slot.move_names if n]
    if move_names:
        move_rows = await asyncio.to_thread(move_repo.get_moves_bulk, get_db(), move_names)
        moves = [move_repo.to_move_slot(row) for name in move_names if (row := move_rows.get(name))]
    else:
        moves = []

    if not moves:
        moves = [
            MoveSlot(
                name="struggle", power=50, accuracy=100, pp=1, type="normal", category="physical"
            )
        ]

    # base_stats and evs/ivs both use underscore format (special_attack, special_defense)
    return PokemonBattleState(
        species_id=slot.pokemon_id,
        name=slot.species_name or f"#{slot.pokemon_id}",
        current_hp=_stat(b.get("hp", 45), iv.get("hp", 31), ev.get("hp", 0), is_hp=True),
        max_hp=_stat(b.get("hp", 45), iv.get("hp", 31), ev.get("hp", 0), is_hp=True),
        attack=_stat(b.get("attack", 45), iv.get("attack", 31), ev.get("attack", 0)),
        defense=_stat(b.get("defense", 45), iv.get("defense", 31), ev.get("defense", 0)),
        special_attack=_stat(
            b.get("special_attack", 45), iv.get("special_attack", 31), ev.get("special_attack", 0)
        ),
        special_defense=_stat(
            b.get("special_defense", 45),
            iv.get("special_defense", 31),
            ev.get("special_defense", 0),
        ),
        speed=_stat(b.get("speed", 45), iv.get("speed", 31), ev.get("speed", 0)),
        types=slot.types or ["normal"],
        moves=moves,
    )


async def _fetch_team(team_id: str, user_id: str) -> list[PokemonBattleState]:
    result = await asyncio.to_thread(
        lambda: (
            get_db()
            .table("teams")
            .select("slots")
            .eq("id", team_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    )
    slots_raw: list = (result.data or {}).get("slots", [])

    mons: list[PokemonBattleState] = []
    for raw in slots_raw:
        if raw is None:
            continue
        try:
            slot = StoredSlot(**raw)
            mons.append(await _build_pokemon(slot))
        except Exception:
            continue

    if not mons:
        raise ValueError(f"No valid Pokémon found in team {team_id}")
    return mons


# ─── State serialization ──────────────────────────────────────────────────────


def _ser_state(state: BattleState) -> dict:
    def ser_move(m: MoveSlot) -> dict:
        return {
            "name": m.name,
            "power": m.power,
            "accuracy": m.accuracy,
            "pp": m.pp,
            "type": m.type,
            "category": m.category,
        }

    def ser_mon(m: PokemonBattleState) -> dict:
        return {
            "species_id": m.species_id,
            "name": m.name,
            "current_hp": m.current_hp,
            "max_hp": m.max_hp,
            "attack": m.attack,
            "defense": m.defense,
            "special_attack": m.special_attack,
            "special_defense": m.special_defense,
            "speed": m.speed,
            "types": m.types,
            "moves": [ser_move(mv) for mv in m.moves],
            "fainted": m.fainted,
        }

    def ser_player(p: PlayerState) -> dict:
        return {
            "user_id": p.user_id,
            "active_index": p.active_index,
            "team": [ser_mon(m) for m in p.team],
        }

    return {
        "id": state.id,
        "player1": ser_player(state.player1),
        "player2": ser_player(state.player2),
        "turn": state.turn,
        "status": state.status,
        "winner_id": state.winner_id,
        "log": state.log[-30:],
    }


# ─── Battle result persistence ────────────────────────────────────────────────


async def _save_result(state: BattleState) -> None:
    try:
        await asyncio.to_thread(
            lambda: (
                get_db()
                .table("battles")
                .insert(
                    {
                        "player1_id": state.player1.user_id,
                        "player2_id": state.player2.user_id,
                        "winner_id": state.winner_id,
                        "turns": state.turn,
                    }
                )
                .execute()
            )
        )
    except Exception:
        logger.exception("Failed to persist battle result for battle_id=%s", state.id)


# ─── Move timeout ─────────────────────────────────────────────────────────────

# Tracks per-player move timeout tasks: user_id → asyncio.Task
_move_timeouts: dict[str, asyncio.Task] = {}

# Tracks when the current turn timer started: battle_id → epoch seconds (float)
_turn_started_at: dict[str, float] = {}

# Short-lived cache of recent battle results so reconnecting users see the summary.
# user_id → {winner_id, reason, ended_at}
_RECENT_BATTLE_TTL = 300  # 5 minutes
_recent_battle_ends: dict[str, dict] = {}


def _cache_battle_end(state: BattleState, reason: str) -> None:
    ts = time.time()
    for uid in [state.player1.user_id, state.player2.user_id]:
        _recent_battle_ends[uid] = {"winner_id": state.winner_id, "reason": reason, "ended_at": ts}


def _pop_recent_battle_end(user_id: str) -> dict | None:
    entry = _recent_battle_ends.pop(user_id, None)
    if entry and time.time() - entry["ended_at"] < _RECENT_BATTLE_TTL:
        return entry
    return None


def _start_move_timeout(user_id: str, battle_id: str) -> None:
    """Start (or restart) the move timeout countdown for a player."""
    existing = _move_timeouts.pop(user_id, None)
    if existing:
        existing.cancel()
    _move_timeouts[user_id] = asyncio.create_task(_move_timeout(user_id, battle_id))


def _start_turn_timers(battle_id: str, user_id1: str, user_id2: str) -> float:
    """Start move timers for both players and record the turn start timestamp."""
    ts = time.time()
    _turn_started_at[battle_id] = ts
    _start_move_timeout(user_id1, battle_id)
    _start_move_timeout(user_id2, battle_id)
    return ts


def _cancel_move_timeout(user_id: str) -> None:
    task = _move_timeouts.pop(user_id, None)
    if task:
        task.cancel()


async def _move_timeout(user_id: str, battle_id: str) -> None:
    """Auto-forfeit a player who hasn't submitted a move within the timeout window."""
    settings = get_settings()
    try:
        await asyncio.sleep(settings.move_timeout_seconds)
        _move_timeouts.pop(user_id, None)
        state = get_battle(battle_id)
        if not state or state.status != "active":
            return
        if user_id in state.pending_moves:
            return  # move was submitted; race condition, no-op
        logger.info(
            "Move timeout for user_id=%s in battle_id=%s — auto-forfeiting", user_id, battle_id
        )
        await manager.send_to_user(
            user_id,
            {
                "type": "error",
                "message": "Move timeout — you took too long and forfeited.",
            },
        )
        await _handle_forfeit(user_id, {"battle_id": battle_id})
    except asyncio.CancelledError:
        pass


# ─── Reconnect grace period ───────────────────────────────────────────────────

# Tracks users with active grace periods: user_id → pending forfeit task
_pending_forfeits: dict[str, asyncio.Task] = {}


async def _grace_period(user_id: str, battle_id: str) -> None:
    """Forfeit the battle if the user hasn't reconnected within the grace window."""
    settings = get_settings()
    try:
        await asyncio.sleep(settings.ws_grace_period_seconds)
        _pending_forfeits.pop(user_id, None)
        await _handle_forfeit(user_id, {"battle_id": battle_id})
    except asyncio.CancelledError:
        pass


def _opponent_id(state: BattleState, user_id: str) -> str:
    return state.player2.user_id if user_id == state.player1.user_id else state.player1.user_id


# ─── Message handlers ─────────────────────────────────────────────────────────


async def _handle_join_queue(user_id: str, data: dict) -> None:
    team_id = data.get("team_id")
    if not team_id:
        await manager.send_to_user(user_id, {"type": "error", "message": "team_id required"})
        return

    if get_battle_by_user(user_id):
        await manager.send_to_user(
            user_id, {"type": "error", "message": "Already in an active battle"}
        )
        return

    enqueue(user_id, team_id)
    match = try_match()

    if match is None:
        await manager.send_to_user(user_id, {"type": "queue_joined"})
        return

    entry1, entry2 = match
    try:
        team1 = await _fetch_team(entry1.team_id, entry1.user_id)
        team2 = await _fetch_team(entry2.team_id, entry2.user_id)
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
                uid, {"type": "error", "message": "Failed to load team data"}
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
                "type": "match_found",
                "battle_id": state.id,
                "opponent_id": opp,
            },
        )

    turn_started_at = _start_turn_timers(state.id, entry1.user_id, entry2.user_id)

    await manager.broadcast_to_room(
        state.id,
        {
            "type": "battle_start",
            "battle_id": state.id,
            "state": _ser_state(state),
            "turn_started_at": turn_started_at,
        },
    )


async def _handle_leave_queue(user_id: str) -> None:
    dequeue(user_id)
    await manager.send_to_user(user_id, {"type": "queue_left"})


async def _handle_make_move(user_id: str, data: dict) -> None:
    battle_id = data.get("battle_id")
    move_slot = data.get("move_slot")

    if not battle_id or move_slot is None:
        await manager.send_to_user(
            user_id, {"type": "error", "message": "battle_id and move_slot required"}
        )
        return

    state = get_battle(battle_id)
    if not state or state.status != "active":
        await manager.send_to_user(
            user_id, {"type": "error", "message": "Battle not found or already ended"}
        )
        return

    if user_id != state.player1.user_id and user_id != state.player2.user_id:
        await manager.send_to_user(
            user_id, {"type": "error", "message": "Not a participant in this battle"}
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
                "type": "error",
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
    _cancel_move_timeout(user_id)

    if not both_ready:
        await manager.broadcast_to_room(battle_id, {"type": "move_received", "user_id": user_id})
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
        _turn_started_at.pop(battle_id, None)
        _cache_battle_end(result.new_state, "all_fainted")
        await manager.broadcast_to_room(
            battle_id,
            {
                "type": "turn_result",
                "log": result.log_entries,
                "state": _ser_state(result.new_state),
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
                "type": "battle_end",
                "winner_id": result.winner_id,
                "reason": "all_fainted",
            },
        )
        await _save_result(result.new_state)
        await manager.leave_room(battle_id)
        remove_battle(battle_id)
    else:
        turn_started_at = _start_turn_timers(
            battle_id, result.new_state.player1.user_id, result.new_state.player2.user_id
        )
        await manager.broadcast_to_room(
            battle_id,
            {
                "type": "turn_result",
                "log": result.log_entries,
                "state": _ser_state(result.new_state),
                "turn_started_at": turn_started_at,
            },
        )


async def _handle_forfeit(user_id: str, data: dict) -> None:
    battle_id = data.get("battle_id")
    if not battle_id:
        return

    state = get_battle(battle_id)
    if not state or state.status != "active":
        return

    winner_id = _opponent_id(state, user_id)
    state.status = "ended"
    state.winner_id = winner_id

    # Cancel any pending move timeouts for both players
    _cancel_move_timeout(state.player1.user_id)
    _cancel_move_timeout(state.player2.user_id)

    logger.info(
        "Battle forfeited: battle_id=%s forfeiter=%s winner=%s", battle_id, user_id, winner_id
    )

    _turn_started_at.pop(battle_id, None)
    _cache_battle_end(state, "forfeit")
    await manager.broadcast_to_room(
        battle_id,
        {
            "type": "battle_end",
            "winner_id": winner_id,
            "reason": "forfeit",
        },
    )
    await _save_result(state)
    await manager.leave_room(battle_id)
    remove_battle(battle_id)


async def _handle_disconnect(user_id: str) -> None:
    """On disconnect, start a grace period instead of forfeiting immediately."""
    settings = get_settings()
    state = get_battle_by_user(user_id)
    if not state or state.status != "active":
        return

    logger.info("User disconnected from active battle: user_id=%s battle_id=%s", user_id, state.id)
    await manager.send_to_user(
        _opponent_id(state, user_id),
        {
            "type": "opponent_disconnected",
            "message": (
                f"Opponent disconnected. Waiting {settings.ws_grace_period_seconds}s for reconnect."
            ),
        },
    )
    task = asyncio.create_task(_grace_period(user_id, state.id))
    _pending_forfeits[user_id] = task


# ─── Ticket endpoint ──────────────────────────────────────────────────────────


@router.post("/ws/ticket")
async def create_ws_ticket(user: UserIdDep) -> dict:
    """
    Exchange a valid JWT (via Authorization header) for a short-lived WebSocket ticket.
    The ticket is single-use and expires in 30 seconds.
    """
    return {"ticket": issue_ticket(user.id)}


# ─── WebSocket endpoint ───────────────────────────────────────────────────────


@router.websocket("/ws/battle")
async def battle_ws(
    ws: WebSocket,
    ticket: Annotated[str, Query()],
) -> None:
    # Validate the single-use ticket — no JWT in the URL
    user_id = consume_ticket(ticket)
    if not user_id:
        await ws.close(code=4001, reason="Invalid or expired ticket")
        return

    await ws.accept()
    await manager.connect(ws, user_id)
    logger.info("WebSocket connected: user_id=%s", user_id)

    # Cancel any pending forfeit from a prior disconnect
    pending_forfeit = _pending_forfeits.pop(user_id, None)
    if pending_forfeit:
        pending_forfeit.cancel()

    # Re-join any in-progress battle or restore queue state
    existing = get_battle_by_user(user_id)
    if existing:
        await manager.join_room(existing.id, user_id)
        if pending_forfeit:
            # Reconnect: notify opponent and send current state
            logger.info("User reconnected to battle: user_id=%s battle_id=%s", user_id, existing.id)
            await manager.send_to_user(
                _opponent_id(existing, user_id),
                {
                    "type": "opponent_reconnected",
                },
            )
            await manager.send_to_user(
                user_id,
                {
                    "type": "battle_resumed",
                    "battle_id": existing.id,
                    "state": _ser_state(existing),
                    "turn_started_at": _turn_started_at.get(existing.id, time.time()),
                },
            )
        else:
            # Fresh connect with an existing battle (e.g. page refresh mid-match)
            await manager.send_to_user(
                user_id,
                {
                    "type": "battle_start",
                    "battle_id": existing.id,
                    "state": _ser_state(existing),
                    "turn_started_at": _turn_started_at.get(existing.id, time.time()),
                },
            )
    else:
        recent_end = _pop_recent_battle_end(user_id)
        if recent_end:
            # Battle ended while user was away — show them the result
            await manager.send_to_user(
                user_id,
                {
                    "type": "battle_end",
                    "winner_id": recent_end["winner_id"],
                    "reason": recent_end["reason"],
                },
            )
        elif is_queued(user_id):
            # User navigated away while in queue — restore queue state
            await manager.send_to_user(user_id, {"type": "queue_joined"})

    try:
        while True:
            try:
                data = await ws.receive_json()
            except Exception:
                break

            if _is_rate_limited(user_id):
                logger.warning("Rate limit exceeded for user_id=%s — closing connection", user_id)
                await ws.close(code=4029, reason="Too many messages")
                break

            match data.get("type"):
                case "join_queue":
                    await _handle_join_queue(user_id, data)
                case "leave_queue":
                    await _handle_leave_queue(user_id)
                case "make_move":
                    await _handle_make_move(user_id, data)
                case "forfeit":
                    await _handle_forfeit(user_id, data)
                case unknown:
                    await manager.send_to_user(
                        user_id,
                        {
                            "type": "error",
                            "message": f"Unknown message type: {unknown!r}",
                        },
                    )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user_id)
        await _handle_disconnect(user_id)
        _rate_windows.pop(user_id, None)
        logger.info("WebSocket disconnected: user_id=%s", user_id)

"""Move timeout and reconnect grace-period management."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from app.battle.manager import get_battle
from app.battle.state import BattleState, BattleStatus
from app.config import get_settings
from app.sockets.connections import manager
from app.sockets.message_types import MSG_ERROR

logger = logging.getLogger(__name__)

# user_id → asyncio.Task for the pending move timeout
_move_timeouts: dict[str, asyncio.Task] = {}

# battle_id → epoch seconds when the current turn started
_turn_started_at: dict[str, float] = {}

# user_id → asyncio.Task for the pending disconnect-forfeit grace period
_pending_forfeits: dict[str, asyncio.Task] = {}


# ─── Move timeout ────────────────────────────────────────────────────────────


def start_move_timeout(
    user_id: str,
    battle_id: str,
    on_forfeit: Callable[[str, dict], Awaitable[None]],
) -> None:
    """Start (or restart) the move timeout countdown for a player."""
    existing = _move_timeouts.pop(user_id, None)
    if existing:
        existing.cancel()
    _move_timeouts[user_id] = asyncio.create_task(_move_timeout(user_id, battle_id, on_forfeit))


def start_turn_timers(
    battle_id: str,
    uid1: str,
    uid2: str,
    on_forfeit: Callable[[str, dict], Awaitable[None]],
) -> float:
    """Start move timers for both players and record the turn start timestamp."""
    ts = time.time()
    _turn_started_at[battle_id] = ts
    start_move_timeout(uid1, battle_id, on_forfeit)
    start_move_timeout(uid2, battle_id, on_forfeit)
    return ts


def cancel_move_timeout(user_id: str) -> None:
    task = _move_timeouts.pop(user_id, None)
    if task:
        task.cancel()


def clear_turn_timestamp(battle_id: str) -> None:
    _turn_started_at.pop(battle_id, None)


def get_turn_started_at(battle_id: str) -> float | None:
    return _turn_started_at.get(battle_id)


async def _move_timeout(
    user_id: str,
    battle_id: str,
    on_forfeit: Callable[[str, dict], Awaitable[None]],
) -> None:
    """Auto-forfeit a player who hasn't submitted a move within the timeout window."""
    settings = get_settings()
    try:
        await asyncio.sleep(settings.move_timeout_seconds)
        _move_timeouts.pop(user_id, None)
        state = get_battle(battle_id)
        if not state or state.status != BattleStatus.ACTIVE:
            return
        if user_id in state.pending_actions:
            return  # action was submitted; race condition, no-op
        logger.info(
            "Move timeout for user_id=%s in battle_id=%s — auto-forfeiting", user_id, battle_id
        )
        await manager.send_to_user(
            user_id,
            {
                "type": MSG_ERROR,
                "message": "Move timeout — you took too long and forfeited.",
            },
        )
        await on_forfeit(user_id, {"battle_id": battle_id})
    except asyncio.CancelledError:
        pass


# ─── Reconnect grace period ─────────────────────────────────────────────────


def start_grace_period(
    user_id: str,
    battle_id: str,
    on_forfeit: Callable[[str, dict], Awaitable[None]],
) -> None:
    """Start the grace-period countdown for a disconnected player."""
    task = asyncio.create_task(_grace_period(user_id, battle_id, on_forfeit))
    _pending_forfeits[user_id] = task


def cancel_grace_period(user_id: str) -> asyncio.Task | None:
    """Cancel and return the pending forfeit task, or None if there isn't one."""
    return _pending_forfeits.pop(user_id, None)


def has_pending_forfeit(user_id: str) -> bool:
    return user_id in _pending_forfeits


async def _grace_period(
    user_id: str,
    battle_id: str,
    on_forfeit: Callable[[str, dict], Awaitable[None]],
) -> None:
    """Forfeit the battle if the user hasn't reconnected within the grace window."""
    settings = get_settings()
    try:
        await asyncio.sleep(settings.ws_grace_period_seconds)
        _pending_forfeits.pop(user_id, None)
        await on_forfeit(user_id, {"battle_id": battle_id})
    except asyncio.CancelledError:
        pass


# ─── Helpers ─────────────────────────────────────────────────────────────────


def opponent_id(state: BattleState, user_id: str) -> str:
    return state.player2.user_id if user_id == state.player1.user_id else state.player1.user_id


# ─── Testing ─────────────────────────────────────────────────────────────────


def _reset_for_testing() -> None:
    """Cancel all tasks and clear all timer state. Call this in test teardown fixtures."""
    for task in list(_pending_forfeits.values()):
        task.cancel()
    _pending_forfeits.clear()
    for task in list(_move_timeouts.values()):
        task.cancel()
    _move_timeouts.clear()
    _turn_started_at.clear()

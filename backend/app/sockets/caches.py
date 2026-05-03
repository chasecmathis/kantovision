"""Short-lived caches for reconnection state."""

from __future__ import annotations

import time

from app.battle.state import BattleState
from app.config import get_settings

# user_id → {winner_id, reason, ended_at}
_recent_battle_ends: dict[str, dict] = {}


def cache_battle_end(state: BattleState, reason: str) -> None:
    """Store the battle result for both players so reconnecting users see the outcome."""
    ts = time.time()
    for uid in [state.player1.user_id, state.player2.user_id]:
        _recent_battle_ends[uid] = {"winner_id": state.winner_id, "reason": reason, "ended_at": ts}


def pop_recent_battle_end(user_id: str) -> dict | None:
    """Pop and return the cached battle-end result if it hasn't expired, else None."""
    ttl = get_settings().recent_battle_end_ttl_seconds
    entry = _recent_battle_ends.pop(user_id, None)
    if entry and time.time() - entry["ended_at"] < ttl:
        return entry
    return None


def sweep_expired() -> int:
    """Remove all expired entries. Returns the count of entries removed."""
    ttl = get_settings().recent_battle_end_ttl_seconds
    now = time.time()
    expired = [uid for uid, data in _recent_battle_ends.items() if now - data["ended_at"] >= ttl]
    for uid in expired:
        del _recent_battle_ends[uid]
    return len(expired)


def _reset_for_testing() -> None:
    """Clear all cache state. Call this in test teardown fixtures."""
    _recent_battle_ends.clear()

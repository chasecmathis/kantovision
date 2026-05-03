"""Per-connection WebSocket rate limiter."""

from __future__ import annotations

import asyncio

from app.config import get_settings

# user_id → list of recent message timestamps (monotonic clock)
_rate_windows: dict[str, list[float]] = {}


def is_rate_limited(user_id: str) -> bool:
    """Return True if the user has exceeded ws_rate_limit_per_second messages/s."""
    settings = get_settings()
    limit = settings.ws_rate_limit_per_second
    now = asyncio.get_running_loop().time()
    window = _rate_windows.setdefault(user_id, [])
    # Prune timestamps older than 1 second
    _rate_windows[user_id] = [t for t in window if now - t < 1.0]
    _rate_windows[user_id].append(now)
    return len(_rate_windows[user_id]) > limit


def clear_user(user_id: str) -> None:
    """Remove rate-limit state for a disconnected user."""
    _rate_windows.pop(user_id, None)


def _reset_for_testing() -> None:
    """Clear all rate-limit state. Call this in test teardown fixtures."""
    _rate_windows.clear()

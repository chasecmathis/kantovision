from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class QueueEntry:
    user_id: str
    team_id: str
    joined_at: float = field(default_factory=time.time)


_queue: deque[QueueEntry] = deque()


def enqueue(user_id: str, team_id: str) -> None:
    """Add a player to the queue, replacing any existing entry."""
    dequeue(user_id)
    _queue.append(QueueEntry(user_id=user_id, team_id=team_id))


def dequeue(user_id: str) -> bool:
    """Remove a player from the queue. Returns True if they were present."""
    for entry in list(_queue):
        if entry.user_id == user_id:
            _queue.remove(entry)
            return True
    return False


def try_match() -> tuple[QueueEntry, QueueEntry] | None:
    """Pop two players from the front of the queue if available."""
    if len(_queue) >= 2:
        return _queue.popleft(), _queue.popleft()
    return None


def queue_position(user_id: str) -> int:
    """Return 1-indexed position in queue, or 0 if not present."""
    for i, entry in enumerate(_queue):
        if entry.user_id == user_id:
            return i + 1
    return 0

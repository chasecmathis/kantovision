from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

TICKET_TTL = 30.0  # seconds

@dataclass
class _Ticket:
    user_id: str
    expires_at: float


_tickets: dict[str, _Ticket] = {}


def issue_ticket(user_id: str) -> str:
    """Create a short-lived, single-use ticket and return its ID."""
    ticket_id = str(uuid.uuid4())
    _tickets[ticket_id] = _Ticket(user_id=user_id, expires_at=time.monotonic() + TICKET_TTL)
    return ticket_id


def _reset_for_testing() -> None:
    """Clear all ticket state. Call this in test teardown fixtures."""
    _tickets.clear()


def consume_ticket(ticket_id: str) -> str | None:
    """
    Validate and consume a ticket. Returns the associated user_id on success,
    or None if the ticket doesn't exist or has expired. Always deletes the ticket.
    """
    ticket = _tickets.pop(ticket_id, None)
    if ticket is None or time.monotonic() > ticket.expires_at:
        return None
    return ticket.user_id

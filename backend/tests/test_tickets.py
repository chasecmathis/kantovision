"""Tests for the WebSocket ticket system."""
import time

from app.sockets.tickets import _tickets, consume_ticket, issue_ticket


class TestIssueTicket:
    def test_returns_string(self):
        ticket = issue_ticket("user-1")
        assert isinstance(ticket, str)
        assert len(ticket) > 0

    def test_unique_tickets(self):
        t1 = issue_ticket("user-1")
        t2 = issue_ticket("user-1")
        assert t1 != t2

    def test_ticket_stored_with_correct_user(self):
        ticket = issue_ticket("user-abc")
        assert ticket in _tickets
        assert _tickets[ticket].user_id == "user-abc"

    def test_ticket_has_future_expiry(self):
        before = time.monotonic()
        ticket = issue_ticket("user-1")
        assert _tickets[ticket].expires_at > before


class TestConsumeTicket:
    def test_valid_ticket_returns_user_id(self):
        ticket = issue_ticket("user-1")
        result = consume_ticket(ticket)
        assert result == "user-1"

    def test_single_use_second_consume_returns_none(self):
        ticket = issue_ticket("user-1")
        consume_ticket(ticket)
        result = consume_ticket(ticket)
        assert result is None

    def test_unknown_ticket_returns_none(self):
        result = consume_ticket("not-a-real-ticket")
        assert result is None

    def test_expired_ticket_returns_none(self, monkeypatch):
        ticket = issue_ticket("user-1")
        # Capture expires_at before pop() removes it from _tickets
        future_time = _tickets[ticket].expires_at + 1
        monkeypatch.setattr("app.sockets.tickets.time.monotonic", lambda: future_time)
        result = consume_ticket(ticket)
        assert result is None

    def test_expired_ticket_is_removed(self, monkeypatch):
        ticket = issue_ticket("user-1")
        future_time = _tickets[ticket].expires_at + 1
        monkeypatch.setattr("app.sockets.tickets.time.monotonic", lambda: future_time)
        consume_ticket(ticket)
        assert ticket not in _tickets

    def test_valid_ticket_is_removed_after_consume(self):
        ticket = issue_ticket("user-1")
        consume_ticket(ticket)
        assert ticket not in _tickets

    def test_different_users_independent_tickets(self):
        t1 = issue_ticket("user-1")
        t2 = issue_ticket("user-2")
        assert consume_ticket(t1) == "user-1"
        assert consume_ticket(t2) == "user-2"

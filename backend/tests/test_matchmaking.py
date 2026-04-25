"""Tests for the matchmaking queue."""

from app.battle.matchmaking import (
    dequeue,
    enqueue,
    is_queued,
    queue_position,
    try_match,
)


class TestEnqueue:
    def test_adds_user_to_queue(self):
        enqueue("user-1", "team-1")
        assert is_queued("user-1")

    def test_multiple_users(self):
        enqueue("user-1", "team-1")
        enqueue("user-2", "team-2")
        assert is_queued("user-1")
        assert is_queued("user-2")

    def test_re_enqueue_replaces_existing(self):
        enqueue("user-1", "team-old")
        enqueue("user-1", "team-new")
        # Should still be in the queue exactly once
        assert queue_position("user-1") != 0
        (entry,) = (
            e
            for e in __import__("app.battle.matchmaking", fromlist=["_queue"])._queue
            if e.user_id == "user-1"
        )  # noqa: E501
        assert entry.team_id == "team-new"


class TestDequeue:
    def test_removes_user(self):
        enqueue("user-1", "team-1")
        result = dequeue("user-1")
        assert result is True
        assert not is_queued("user-1")

    def test_returns_false_when_not_queued(self):
        result = dequeue("user-not-there")
        assert result is False

    def test_only_removes_target_user(self):
        enqueue("user-1", "team-1")
        enqueue("user-2", "team-2")
        dequeue("user-1")
        assert not is_queued("user-1")
        assert is_queued("user-2")


class TestTryMatch:
    def test_returns_none_when_empty(self):
        assert try_match() is None

    def test_returns_none_with_one_player(self):
        enqueue("user-1", "team-1")
        assert try_match() is None
        # User should still be in queue
        assert is_queued("user-1")

    def test_returns_pair_when_two_players(self):
        enqueue("user-1", "team-1")
        enqueue("user-2", "team-2")
        result = try_match()
        assert result is not None
        entry1, entry2 = result
        assert entry1.user_id == "user-1"
        assert entry2.user_id == "user-2"

    def test_removes_matched_players_from_queue(self):
        enqueue("user-1", "team-1")
        enqueue("user-2", "team-2")
        try_match()
        assert not is_queued("user-1")
        assert not is_queued("user-2")

    def test_fifo_ordering(self):
        enqueue("user-1", "team-1")
        enqueue("user-2", "team-2")
        enqueue("user-3", "team-3")
        # First match should be user-1 and user-2
        e1, e2 = try_match()
        assert e1.user_id == "user-1"
        assert e2.user_id == "user-2"
        # user-3 remains
        assert is_queued("user-3")


class TestIsQueued:
    def test_true_when_queued(self):
        enqueue("user-1", "team-1")
        assert is_queued("user-1") is True

    def test_false_when_not_queued(self):
        assert is_queued("user-nobody") is False

    def test_false_after_dequeue(self):
        enqueue("user-1", "team-1")
        dequeue("user-1")
        assert is_queued("user-1") is False


class TestQueuePosition:
    def test_returns_zero_when_not_queued(self):
        assert queue_position("user-nobody") == 0

    def test_first_in_is_position_1(self):
        enqueue("user-1", "team-1")
        assert queue_position("user-1") == 1

    def test_second_in_is_position_2(self):
        enqueue("user-1", "team-1")
        enqueue("user-2", "team-2")
        assert queue_position("user-2") == 2

    def test_position_updates_after_match(self):
        enqueue("user-1", "team-1")
        enqueue("user-2", "team-2")
        enqueue("user-3", "team-3")
        try_match()  # removes user-1 and user-2
        assert queue_position("user-3") == 1

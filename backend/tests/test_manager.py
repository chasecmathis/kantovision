"""Tests for the in-memory battle manager."""

from app.battle.manager import (
    create_battle,
    get_battle,
    get_battle_by_user,
    remove_battle,
    submit_move,
    update_battle,
)
from tests.helpers import make_pokemon, make_queue_entry


def _make_battle(user1: str = "user-1", user2: str = "user-2"):
    entry1 = make_queue_entry(user1, "team-1")
    entry2 = make_queue_entry(user2, "team-2")
    team1 = [make_pokemon(name="Mon1")]
    team2 = [make_pokemon(name="Mon2")]
    return create_battle(entry1, entry2, team1, team2)


class TestCreateBattle:
    def test_returns_battle_state(self):
        state = _make_battle()
        assert state.id is not None
        assert state.player1.user_id == "user-1"
        assert state.player2.user_id == "user-2"

    def test_battle_is_active(self):
        state = _make_battle()
        assert state.status == "active"

    def test_unique_ids(self):
        s1 = _make_battle("u1", "u2")
        s2 = _make_battle("u3", "u4")
        assert s1.id != s2.id

    def test_teams_assigned_correctly(self):
        state = _make_battle()
        assert state.player1.team[0].name == "Mon1"
        assert state.player2.team[0].name == "Mon2"


class TestGetBattle:
    def test_returns_existing_battle(self):
        state = _make_battle()
        fetched = get_battle(state.id)
        assert fetched is not None
        assert fetched.id == state.id

    def test_returns_none_for_unknown_id(self):
        assert get_battle("not-a-real-id") is None


class TestGetBattleByUser:
    def test_finds_battle_for_player1(self):
        state = _make_battle("u1", "u2")
        fetched = get_battle_by_user("u1")
        assert fetched is not None
        assert fetched.id == state.id

    def test_finds_battle_for_player2(self):
        state = _make_battle("u1", "u2")
        fetched = get_battle_by_user("u2")
        assert fetched is not None
        assert fetched.id == state.id

    def test_returns_none_for_unknown_user(self):
        _make_battle("u1", "u2")
        assert get_battle_by_user("u-nobody") is None


class TestUpdateBattle:
    def test_replaces_state(self):
        state = _make_battle()
        state.turn = 99
        update_battle(state)
        fetched = get_battle(state.id)
        assert fetched.turn == 99

    def test_mutates_in_place(self):
        state = _make_battle()
        state.log.append("Test log entry")
        update_battle(state)
        assert get_battle(state.id).log == ["Test log entry"]


class TestRemoveBattle:
    def test_removes_battle(self):
        state = _make_battle()
        battle_id = state.id
        remove_battle(battle_id)
        assert get_battle(battle_id) is None

    def test_removes_user_mappings(self):
        state = _make_battle("u1", "u2")
        remove_battle(state.id)
        assert get_battle_by_user("u1") is None
        assert get_battle_by_user("u2") is None

    def test_no_error_on_unknown_id(self):
        # Should not raise
        remove_battle("not-a-real-id")


class TestSubmitMove:
    def test_returns_false_after_first_submission(self):
        state = _make_battle("u1", "u2")
        result = submit_move(state.id, "u1", 0)
        assert result is False

    def test_returns_true_after_both_submit(self):
        state = _make_battle("u1", "u2")
        submit_move(state.id, "u1", 0)
        result = submit_move(state.id, "u2", 1)
        assert result is True

    def test_move_stored_correctly(self):
        state = _make_battle("u1", "u2")
        submit_move(state.id, "u1", 2)
        fetched = get_battle(state.id)
        assert fetched.pending_moves["u1"] == 2

    def test_returns_false_for_unknown_battle(self):
        result = submit_move("no-such-battle", "u1", 0)
        assert result is False

    def test_returns_false_for_ended_battle(self):
        state = _make_battle("u1", "u2")
        state.status = "ended"
        update_battle(state)
        result = submit_move(state.id, "u1", 0)
        assert result is False

"""Tests for app.repositories.move_repo."""
from unittest.mock import MagicMock

import pytest

from app.repositories.move_repo import MoveRow, get_move, get_moves_bulk, to_move_slot
from app.battle.state import MoveSlot


def _make_db(data):
    """Build a mock Supabase client that returns `data` from .execute()."""
    execute = MagicMock()
    execute.return_value = MagicMock(data=data)
    chain = MagicMock()
    chain.maybe_single.return_value = chain
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.in_.return_value = chain
    chain.execute = execute
    db = MagicMock()
    db.table.return_value = chain
    return db, execute


class TestGetMove:
    def test_returns_move_row_when_found(self):
        row = {
            "id": 1, "name": "tackle", "power": 40, "accuracy": 100,
            "pp": 35, "type": "normal", "damage_class": "physical", "flavor_text": None,
        }
        db, _ = _make_db(row)
        result = get_move(db, "tackle")
        assert result is not None
        assert result.name == "tackle"
        assert result.power == 40
        assert result.damage_class == "physical"

    def test_returns_none_when_not_found(self):
        db, _ = _make_db(None)
        result = get_move(db, "nonexistent-move")
        assert result is None

    def test_handles_nullable_power_and_accuracy(self):
        row = {
            "id": 2, "name": "growl", "power": None, "accuracy": 100,
            "pp": 40, "type": "normal", "damage_class": "status", "flavor_text": "Lowers ATK.",
        }
        db, _ = _make_db(row)
        result = get_move(db, "growl")
        assert result is not None
        assert result.power is None
        assert result.damage_class == "status"


class TestGetMovesBulk:
    def test_returns_dict_keyed_by_name(self):
        rows = [
            {"id": 1, "name": "tackle", "power": 40, "accuracy": 100,
             "pp": 35, "type": "normal", "damage_class": "physical", "flavor_text": None},
            {"id": 2, "name": "ember", "power": 40, "accuracy": 100,
             "pp": 25, "type": "fire", "damage_class": "special", "flavor_text": None},
        ]
        db, _ = _make_db(rows)
        result = get_moves_bulk(db, ["tackle", "ember"])
        assert "tackle" in result
        assert "ember" in result
        assert result["tackle"].type == "normal"
        assert result["ember"].type == "fire"

    def test_empty_names_returns_empty_dict(self):
        db = MagicMock()
        result = get_moves_bulk(db, [])
        assert result == {}
        db.table.assert_not_called()

    def test_missing_moves_not_in_result(self):
        rows = [
            {"id": 1, "name": "tackle", "power": 40, "accuracy": 100,
             "pp": 35, "type": "normal", "damage_class": "physical", "flavor_text": None},
        ]
        db, _ = _make_db(rows)
        result = get_moves_bulk(db, ["tackle", "nonexistent"])
        assert "tackle" in result
        assert "nonexistent" not in result

    def test_queries_correct_table(self):
        db, _ = _make_db([])
        get_moves_bulk(db, ["tackle"])
        db.table.assert_called_once_with("moves")


class TestToMoveSlot:
    def test_converts_row_to_move_slot(self):
        row = MoveRow(id=1, name="flamethrower", power=90, accuracy=100,
                      pp=15, type="fire", damage_class="special", flavor_text=None)
        slot = to_move_slot(row)
        assert isinstance(slot, MoveSlot)
        assert slot.name == "flamethrower"
        assert slot.power == 90
        assert slot.type == "fire"
        assert slot.category == "special"

    def test_defaults_none_power_to_50(self):
        row = MoveRow(id=2, name="growl", power=None, accuracy=100,
                      pp=40, type="normal", damage_class="status", flavor_text=None)
        slot = to_move_slot(row)
        assert slot.power == 50

    def test_defaults_none_accuracy_to_100(self):
        row = MoveRow(id=3, name="swift", power=60, accuracy=None,
                      pp=20, type="normal", damage_class="special", flavor_text=None)
        slot = to_move_slot(row)
        assert slot.accuracy == 100

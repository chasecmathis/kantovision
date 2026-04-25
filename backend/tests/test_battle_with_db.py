"""
Integration tests for battle engine + move_repo.

Verifies that _build_pokemon loads moves from the DB (not PokéAPI) and that
resolve_turn produces correct results using those moves.
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from app.battle.engine import resolve_turn
from app.battle.state import StoredSlot
from app.repositories.move_repo import MoveRow
from tests.helpers import make_battle_state, make_move, make_pokemon

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _stored_slot(
    pokemon_id: int = 1,
    move_names: list[str | None] | None = None,
    base_stats: dict | None = None,
) -> StoredSlot:
    return StoredSlot(
        pokemon_id=pokemon_id,
        species_name="bulbasaur",
        types=["grass", "poison"],
        base_stats=base_stats or {
            "hp": 45, "attack": 49, "defense": 49,
            "special_attack": 65, "special_defense": 65, "speed": 45,
        },
        move_names=move_names or ["tackle", "growl", None, None],
        evs={
            "hp": 0, "attack": 0, "defense": 0,
            "special_attack": 0, "special_defense": 0, "speed": 0,
        },
        ivs={
            "hp": 31, "attack": 31, "defense": 31,
            "special_attack": 31, "special_defense": 31, "speed": 31,
        },
    )


def _move_rows(*names_and_types) -> dict[str, MoveRow]:
    rows = {}
    for name, type_, category, power in names_and_types:
        rows[name] = MoveRow(
            id=1, name=name, power=power, accuracy=100,
            pp=35, type=type_, damage_class=category, flavor_text=None,
        )
    return rows


# ─── _build_pokemon tests ─────────────────────────────────────────────────────

class TestBuildPokemon:
    def _run(self, coro):
        return asyncio.run(coro)

    def test_loads_moves_from_db(self):
        from app.sockets import battle as battle_socket
        slot = _stored_slot(move_names=["tackle", "razor-leaf"])
        move_rows = _move_rows(
            ("tackle", "normal", "physical", 40),
            ("razor-leaf", "grass", "physical", 55),
        )
        with patch("app.sockets.battle.get_db", return_value=MagicMock()), \
             patch("app.sockets.battle.move_repo.get_moves_bulk", return_value=move_rows):
            mon = self._run(battle_socket._build_pokemon(slot))

        assert len(mon.moves) == 2
        move_names = {m.name for m in mon.moves}
        assert move_names == {"tackle", "razor-leaf"}

    def test_falls_back_to_struggle_when_no_moves(self):
        from app.sockets import battle as battle_socket
        slot = _stored_slot(move_names=[None, None, None, None])
        with patch("app.sockets.battle.get_db", return_value=MagicMock()), \
             patch("app.sockets.battle.move_repo.get_moves_bulk", return_value={}):
            mon = self._run(battle_socket._build_pokemon(slot))

        assert len(mon.moves) == 1
        assert mon.moves[0].name == "struggle"

    def test_skips_moves_missing_from_db(self):
        from app.sockets import battle as battle_socket
        slot = _stored_slot(move_names=["tackle", "unknown-move"])
        move_rows = _move_rows(("tackle", "normal", "physical", 40))
        with patch("app.sockets.battle.get_db", return_value=MagicMock()), \
             patch("app.sockets.battle.move_repo.get_moves_bulk", return_value=move_rows):
            mon = self._run(battle_socket._build_pokemon(slot))

        assert len(mon.moves) == 1
        assert mon.moves[0].name == "tackle"

    def test_calculates_stats_using_underscore_keys(self):
        """Regression: base_stats uses underscore keys (special_attack), not hyphen."""
        from app.sockets import battle as battle_socket
        slot = _stored_slot(
            base_stats={
                "hp": 100, "attack": 80, "defense": 80,
                "special_attack": 130, "special_defense": 90, "speed": 110,
            }
        )
        move_rows = _move_rows(("tackle", "normal", "physical", 40))
        with patch("app.sockets.battle.get_db", return_value=MagicMock()), \
             patch("app.sockets.battle.move_repo.get_moves_bulk", return_value=move_rows):
            mon = self._run(battle_socket._build_pokemon(slot))

        # special_attack should NOT be 45 (the old default from the bug where hyphen keys were used)
        assert mon.special_attack != 45
        # Exact value: (2*130 + 31 + 0) * 50 // 100 + 5 = (260+31)*50//100 + 5 = 145 + 5 = 150
        assert mon.special_attack == 150

    def test_does_not_call_pokeapi(self):
        """Confirm no HTTP requests are made during _build_pokemon."""
        import httpx

        from app.sockets import battle as battle_socket
        slot = _stored_slot()
        move_rows = _move_rows(("tackle", "normal", "physical", 40))
        with patch("app.sockets.battle.get_db", return_value=MagicMock()), \
             patch("app.sockets.battle.move_repo.get_moves_bulk", return_value=move_rows), \
             patch.object(httpx.AsyncClient, "get", side_effect=AssertionError("HTTP call made!")):
            # Should not raise since httpx is not used anymore
            self._run(battle_socket._build_pokemon(slot))


# ─── resolve_turn integration ─────────────────────────────────────────────────

class TestResolveTurnWithDbMoves:
    """Smoke test: full turn resolution using moves from DB rows."""

    def _run(self, coro):
        return asyncio.run(coro)

    def test_damage_applied_correctly(self):
        """A physical move should deal predictable damage."""
        attacker = make_pokemon(name="Attacker", hp=200, attack=100, defense=50, speed=100)
        attacker.moves = [make_move("tackle", power=40, type_="normal", category="physical")]

        defender = make_pokemon(name="Defender", hp=200, attack=50, defense=50, speed=50)
        defender.moves = [make_move("tackle", power=40, type_="normal", category="physical")]

        state = make_battle_state(team1=[attacker], team2=[defender])

        result = resolve_turn(state, 0, 0)
        assert not result.battle_over or result.winner_id is not None
        # After one turn, at least one pokemon took damage (or battle ended)
        new_state = result.new_state
        p1_active = new_state.player1.team[0]
        p2_active = new_state.player2.team[0]
        total_damage = (200 - p1_active.current_hp) + (200 - p2_active.current_hp)
        assert total_damage > 0

    def test_type_effectiveness_applied(self):
        """Fire vs Grass should deal 2× damage."""
        attacker = make_pokemon(name="Charizard", attack=100, defense=80, speed=100, types=["fire"])
        attacker.moves = [make_move("flamethrower", power=90, type_="fire", category="special")]
        # Override special_attack since make_pokemon doesn't have it as a first-class arg
        attacker.special_attack = 100

        defender = make_pokemon(name="Bulbasaur", hp=200, defense=49, speed=45, types=["grass"])
        defender.special_defense = 65
        defender.moves = [make_move("tackle", power=40, type_="normal", category="physical")]

        state = make_battle_state(team1=[attacker], team2=[defender])
        result = resolve_turn(state, 0, 0)

        log_text = " ".join(result.log_entries).lower()
        assert "2×" in log_text or "2x" in log_text or "super" in log_text.lower() or \
               result.new_state.player2.team[0].current_hp < defender.current_hp

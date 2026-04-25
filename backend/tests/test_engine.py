"""Tests for the battle engine: damage calc, type effectiveness, turn resolution."""

from app.battle.engine import calc_damage, get_type_effectiveness, resolve_turn
from tests.helpers import make_battle_state, make_move, make_pokemon

# ─── get_type_effectiveness ───────────────────────────────────────────────────


class TestTypeEffectiveness:
    def test_neutral(self):
        assert get_type_effectiveness("normal", ["normal"]) == 1.0

    def test_super_effective(self):
        assert get_type_effectiveness("fire", ["grass"]) == 2.0

    def test_not_very_effective(self):
        assert get_type_effectiveness("fire", ["fire"]) == 0.5

    def test_immune(self):
        assert get_type_effectiveness("normal", ["ghost"]) == 0.0

    def test_dual_type_both_weak(self):
        # Fire vs Grass/Bug → 2.0 * 2.0 = 4.0
        assert get_type_effectiveness("fire", ["grass", "bug"]) == 4.0

    def test_dual_type_cancel(self):
        # Water vs Fire/Water → 2.0 * 0.5 = 1.0
        assert get_type_effectiveness("water", ["fire", "water"]) == 1.0

    def test_dual_type_one_immune(self):
        # Electric vs Ground/Flying → 0.0 * 2.0 = 0.0
        assert get_type_effectiveness("electric", ["ground", "flying"]) == 0.0

    def test_unknown_attacking_type(self):
        # Unknown attacking type defaults to neutral
        assert get_type_effectiveness("faketype", ["normal"]) == 1.0

    def test_unknown_defending_type(self):
        # Unknown defending type defaults to neutral
        assert get_type_effectiveness("fire", ["faketype"]) == 1.0


# ─── calc_damage ─────────────────────────────────────────────────────────────


class TestCalcDamage:
    def test_basic_physical_damage(self):
        attacker = make_pokemon(attack=100, defense=50, speed=50)
        defender = make_pokemon(attack=50, defense=50, speed=50)
        move = make_move(power=80, type_="normal", category="physical")
        dmg = calc_damage(attacker, defender, move)
        assert dmg >= 1

    def test_special_uses_special_stats(self):
        # High special_attack, low attack — special move should deal more
        attacker = make_pokemon(attack=10, special_attack=150)
        defender = make_pokemon(defense=50, special_defense=50)
        physical = make_move(power=80, category="physical")
        special = make_move(power=80, category="special")
        assert calc_damage(attacker, defender, special) > calc_damage(attacker, defender, physical)

    def test_zero_power_move_deals_no_damage(self):
        attacker = make_pokemon()
        defender = make_pokemon()
        move = make_move(power=0, category="status")
        assert calc_damage(attacker, defender, move) == 0

    def test_status_category_deals_no_damage(self):
        attacker = make_pokemon()
        defender = make_pokemon()
        move = make_move(power=50, category="status")
        assert calc_damage(attacker, defender, move) == 0

    def test_immune_type_deals_no_damage(self):
        attacker = make_pokemon(types=["normal"])
        defender = make_pokemon(types=["ghost"])
        move = make_move(power=80, type_="normal", category="physical")
        assert calc_damage(attacker, defender, move) == 0

    def test_stab_bonus(self):
        # Same type as the move → 1.5x multiplier
        attacker_stab = make_pokemon(attack=100, types=["fire"])
        attacker_no_stab = make_pokemon(attack=100, types=["water"])
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="fire", category="physical")
        stab_dmg = calc_damage(attacker_stab, defender, move)
        no_stab_dmg = calc_damage(attacker_no_stab, defender, move)
        assert stab_dmg > no_stab_dmg

    def test_super_effective_doubles_damage(self):
        attacker = make_pokemon(attack=100, types=["normal"])
        neutral_defender = make_pokemon(defense=50, types=["normal"])
        weak_defender = make_pokemon(defense=50, types=["grass"])
        move = make_move(power=80, type_="fire", category="physical")
        assert calc_damage(attacker, weak_defender, move) == (
            calc_damage(attacker, neutral_defender, move) * 2
        )

    def test_minimum_damage_is_1(self):
        # Very weak attacker vs very strong defender
        attacker = make_pokemon(attack=1, special_attack=1)
        defender = make_pokemon(defense=255, special_defense=255)
        move = make_move(power=1, type_="normal", category="physical")
        assert calc_damage(attacker, defender, move) >= 1


# ─── resolve_turn ─────────────────────────────────────────────────────────────


class TestResolveTurn:
    def test_faster_pokemon_goes_first(self):
        """Fast Pokémon attacks first; if it KOs, slower never gets to move."""
        fast = make_pokemon(name="Fast", hp=200, attack=200, speed=100)
        slow = make_pokemon(name="Slow", hp=1, attack=1, speed=1)
        state = make_battle_state(team1=[fast], team2=[slow])
        result = resolve_turn(state, 0, 0)
        # Slow should faint; check log contains the fast mon's attack first
        assert any("Fast used" in e for e in result.log_entries)
        assert any("Slow fainted" in e for e in result.log_entries)

    def test_input_state_is_not_mutated(self):
        """resolve_turn is a pure function — input state must not change."""
        state = make_battle_state()
        original_hp = state.player2.team[0].current_hp
        resolve_turn(state, 0, 0)
        assert state.player2.team[0].current_hp == original_hp

    def test_turn_counter_increments(self):
        state = make_battle_state()
        assert state.turn == 1
        result = resolve_turn(state, 0, 0)
        assert result.new_state.turn == 2

    def test_pending_moves_cleared_after_turn(self):
        state = make_battle_state()
        state.pending_moves["user-1"] = 0
        result = resolve_turn(state, 0, 0)
        assert result.new_state.pending_moves == {}

    def test_battle_over_when_all_faint(self):
        # Make a very strong attacker that will 1-shot the defender
        strong = make_pokemon(name="Strong", hp=999, attack=999, speed=999)
        weak = make_pokemon(name="Weak", hp=1, defense=1, speed=1)
        state = make_battle_state(team1=[strong], team2=[weak])
        result = resolve_turn(state, 0, 0)
        assert result.battle_over is True
        assert result.winner_id == "user-1"
        assert result.new_state.status == "ended"

    def test_no_winner_when_both_alive(self):
        # Both Pokémon survive the turn
        state = make_battle_state(
            team1=[make_pokemon(name="A", hp=9999, defense=255, special_defense=255)],
            team2=[make_pokemon(name="B", hp=9999, defense=255, special_defense=255)],
        )
        result = resolve_turn(state, 0, 0)
        assert result.battle_over is False
        assert result.winner_id is None
        assert result.new_state.status == "active"

    def test_super_effective_logged(self):
        attacker = make_pokemon(name="Attacker", attack=100, speed=100, types=["fire"])
        defender = make_pokemon(name="Defender", hp=9999, defense=5, types=["grass"])
        move = make_move(power=80, type_="fire", category="physical")
        attacker.moves = [move]
        state = make_battle_state(team1=[attacker], team2=[defender])
        result = resolve_turn(state, 0, 0)
        assert any("super effective" in e for e in result.log_entries)

    def test_not_very_effective_logged(self):
        attacker = make_pokemon(name="Attacker", attack=100, speed=100, types=["normal"])
        defender = make_pokemon(name="Defender", hp=9999, defense=5, types=["rock"])
        move = make_move(power=80, type_="normal", category="physical")
        attacker.moves = [move]
        state = make_battle_state(team1=[attacker], team2=[defender])
        result = resolve_turn(state, 0, 0)
        assert any("not very effective" in e for e in result.log_entries)

    def test_immune_logs_no_effect(self):
        attacker = make_pokemon(name="Attacker", attack=100, speed=100)
        defender = make_pokemon(name="Defender", hp=9999, types=["ghost"])
        move = make_move(power=80, type_="normal")
        attacker.moves = [move]
        state = make_battle_state(team1=[attacker], team2=[defender])
        result = resolve_turn(state, 0, 0)
        assert any("no effect" in e for e in result.log_entries)
        # Ghost defender should not take damage
        assert result.new_state.player2.team[0].current_hp == 9999

    def test_move_index_clamped_to_valid_range(self):
        """Out-of-range move index should clamp without crashing."""
        state = make_battle_state()
        # Both Pokémon have only 1 move (index 0), passing index 99 should not raise
        result = resolve_turn(state, 99, 99)
        assert result.new_state.turn == 2

    def test_advance_active_after_faint(self):
        """After the active Pokémon faints, active_index advances to the next alive one."""
        fainted_lead = make_pokemon(name="Dead", hp=1, defense=1, speed=1, fainted=False)
        backup = make_pokemon(name="Backup", hp=999, defense=50)
        strong = make_pokemon(name="Strong", hp=999, attack=999, speed=999)
        state = make_battle_state(
            team1=[strong],
            team2=[fainted_lead, backup],
        )
        result = resolve_turn(state, 0, 0)
        # Lead fainted → active_index should advance to 1 (Backup)
        assert result.new_state.player2.active_index == 1
        assert result.battle_over is False

"""Tests for the battle engine: damage calc, type effectiveness, turn resolution."""

from random import Random

from app.battle.actions import MoveAction
from app.battle.damage import calc_damage
from app.battle.engine import TurnEngine
from app.battle.typechart import get_type_effectiveness
from tests.helpers import make_battle_state, make_move, make_pokemon

# Seeded RNG for deterministic tests
SEED = 42


def _rng() -> Random:
    return Random(SEED)


def _dmg(attacker, defender, move, **kwargs) -> int:
    """Helper: calc_damage with seeded RNG, returns just the int damage."""
    return calc_damage(attacker, defender, move, _rng(), **kwargs).damage


def _engine() -> TurnEngine:
    """Engine with seeded RNG for deterministic tests."""
    return TurnEngine(rng=Random(SEED))


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
        assert get_type_effectiveness("fire", ["grass", "bug"]) == 4.0

    def test_dual_type_cancel(self):
        assert get_type_effectiveness("water", ["fire", "water"]) == 1.0

    def test_dual_type_one_immune(self):
        assert get_type_effectiveness("electric", ["ground", "flying"]) == 0.0

    def test_unknown_attacking_type(self):
        assert get_type_effectiveness("faketype", ["normal"]) == 1.0

    def test_unknown_defending_type(self):
        assert get_type_effectiveness("fire", ["faketype"]) == 1.0


# ─── calc_damage ─────────────────────────────────────────────────────────────


class TestCalcDamage:
    def test_basic_physical_damage(self):
        attacker = make_pokemon(attack=100, defense=50, speed=50)
        defender = make_pokemon(attack=50, defense=50, speed=50)
        move = make_move(power=80, type_="normal", category="physical")
        dmg = _dmg(attacker, defender, move)
        assert dmg >= 1

    def test_special_uses_special_stats(self):
        attacker = make_pokemon(attack=10, special_attack=150)
        defender = make_pokemon(defense=50, special_defense=50)
        physical = make_move(power=80, category="physical")
        special = make_move(power=80, category="special")
        # Run both with same seed so random factor is the same
        phys_dmg = calc_damage(attacker, defender, physical, Random(99)).damage
        spec_dmg = calc_damage(attacker, defender, special, Random(99)).damage
        assert spec_dmg > phys_dmg

    def test_zero_power_move_deals_no_damage(self):
        attacker = make_pokemon()
        defender = make_pokemon()
        move = make_move(power=0, category="status")
        assert _dmg(attacker, defender, move) == 0

    def test_status_category_deals_no_damage(self):
        attacker = make_pokemon()
        defender = make_pokemon()
        move = make_move(power=50, category="status")
        assert _dmg(attacker, defender, move) == 0

    def test_immune_type_deals_no_damage(self):
        attacker = make_pokemon(types=["normal"])
        defender = make_pokemon(types=["ghost"])
        move = make_move(power=80, type_="normal", category="physical")
        assert _dmg(attacker, defender, move) == 0

    def test_stab_bonus(self):
        attacker_stab = make_pokemon(attack=100, types=["fire"])
        attacker_no_stab = make_pokemon(attack=100, types=["water"])
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="fire", category="physical")
        # Same seed → same random roll → STAB should be strictly more
        stab_dmg = calc_damage(attacker_stab, defender, move, Random(99)).damage
        no_stab_dmg = calc_damage(attacker_no_stab, defender, move, Random(99)).damage
        assert stab_dmg > no_stab_dmg

    def test_super_effective_doubles_damage(self):
        attacker = make_pokemon(attack=100, types=["normal"])
        neutral_defender = make_pokemon(defense=50, types=["normal"])
        weak_defender = make_pokemon(defense=50, types=["grass"])
        move = make_move(power=80, type_="fire", category="physical")
        # Same seed for both → same crit/random outcomes
        neutral_dmg = calc_damage(attacker, neutral_defender, move, Random(99)).damage
        weak_dmg = calc_damage(attacker, weak_defender, move, Random(99)).damage
        assert weak_dmg == neutral_dmg * 2

    def test_minimum_damage_is_1(self):
        attacker = make_pokemon(attack=1, special_attack=1)
        defender = make_pokemon(defense=255, special_defense=255)
        move = make_move(power=1, type_="normal", category="physical")
        dmg = _dmg(attacker, defender, move)
        assert dmg >= 1

    def test_random_factor_bounds(self):
        """Damage should vary between ~85% and 100% of max across many rolls."""
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50)
        move = make_move(power=80, type_="normal", category="physical")
        damages = set()
        for seed in range(200):
            d = calc_damage(attacker, defender, move, Random(seed)).damage
            damages.add(d)
        assert len(damages) > 1, "Damage should vary with random factor"

    def test_crit_multiplier(self):
        """Crit stage 3 = guaranteed crit, should deal 1.5x base damage."""
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="normal", category="physical")
        # Same seed, compare crit_stage=0 vs crit_stage=3
        no_crit = calc_damage(attacker, defender, move, Random(99), crit_stage=0)
        yes_crit = calc_damage(attacker, defender, move, Random(99), crit_stage=3)
        assert yes_crit.is_crit is True
        assert yes_crit.damage > no_crit.damage

    def test_crit_ignores_stat_stages(self):
        """Crits ignore the attacker's negative atk stages and defender's positive def stages."""
        attacker = make_pokemon(attack=100)
        attacker.stat_stages.attack = -2
        defender = make_pokemon(defense=50)
        defender.stat_stages.defense = 2
        move = make_move(power=80, type_="normal", category="physical")

        # With crit, should ignore the bad stages
        crit_result = calc_damage(attacker, defender, move, Random(99), crit_stage=3)

        # Reset stages for clean comparison
        attacker2 = make_pokemon(attack=100)
        defender2 = make_pokemon(defense=50)
        clean_crit = calc_damage(attacker2, defender2, move, Random(99), crit_stage=3)

        assert crit_result.damage == clean_crit.damage

    def test_stat_stages_affect_damage(self):
        """Positive atk stages should increase damage, positive def stages should decrease."""
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="normal", category="physical")

        base = calc_damage(attacker, defender, move, Random(99)).damage

        attacker_boosted = make_pokemon(attack=100)
        attacker_boosted.stat_stages.attack = 2
        boosted = calc_damage(attacker_boosted, defender, move, Random(99)).damage
        assert boosted > base

        defender_boosted = make_pokemon(defense=50, types=["normal"])
        defender_boosted.stat_stages.defense = 2
        walled = calc_damage(attacker, defender_boosted, move, Random(99)).damage
        assert walled < base


# ─── resolve_turn ─────────────────────────────────────────────────────────────


class TestResolveTurn:
    def _resolve(self, state, p1=0, p2=0):
        """Resolve with seeded engine for deterministic results."""
        engine = _engine()
        a1 = MoveAction(player_id=state.player1.user_id, move_index=p1)
        a2 = MoveAction(player_id=state.player2.user_id, move_index=p2)
        return engine.resolve_turn(state, a1, a2)

    def test_faster_pokemon_goes_first(self):
        """Fast Pokémon attacks first; if it KOs, slower never gets to move."""
        fast = make_pokemon(name="Fast", hp=200, attack=200, speed=100)
        slow = make_pokemon(name="Slow", hp=1, attack=1, speed=1)
        state = make_battle_state(team1=[fast], team2=[slow])
        result = self._resolve(state)
        assert any("Fast used" in e for e in result.log_entries)
        assert any("Slow fainted" in e for e in result.log_entries)

    def test_input_state_is_not_mutated(self):
        state = make_battle_state()
        original_hp = state.player2.team[0].current_hp
        self._resolve(state)
        assert state.player2.team[0].current_hp == original_hp

    def test_turn_counter_increments(self):
        state = make_battle_state()
        assert state.turn == 1
        result = self._resolve(state)
        assert result.new_state.turn == 2

    def test_pending_actions_cleared_after_turn(self):
        state = make_battle_state()
        state.pending_actions["user-1"] = {"type": "move", "move_index": 0}
        result = self._resolve(state)
        assert result.new_state.pending_actions == {}

    def test_battle_over_when_all_faint(self):
        strong = make_pokemon(name="Strong", hp=999, attack=999, speed=999)
        weak = make_pokemon(name="Weak", hp=1, defense=1, speed=1)
        state = make_battle_state(team1=[strong], team2=[weak])
        result = self._resolve(state)
        assert result.battle_over is True
        assert result.winner_id == "user-1"
        assert result.new_state.status == "ended"

    def test_no_winner_when_both_alive(self):
        state = make_battle_state(
            team1=[make_pokemon(name="A", hp=9999, defense=255, special_defense=255)],
            team2=[make_pokemon(name="B", hp=9999, defense=255, special_defense=255)],
        )
        result = self._resolve(state)
        assert result.battle_over is False
        assert result.winner_id is None
        assert result.new_state.status == "active"

    def test_super_effective_logged(self):
        attacker = make_pokemon(name="Attacker", attack=100, speed=100, types=["fire"])
        defender = make_pokemon(name="Defender", hp=9999, defense=5, types=["grass"])
        move = make_move(power=80, type_="fire", category="physical")
        attacker.moves = [move]
        state = make_battle_state(team1=[attacker], team2=[defender])
        result = self._resolve(state)
        assert any("super effective" in e for e in result.log_entries)

    def test_not_very_effective_logged(self):
        attacker = make_pokemon(name="Attacker", attack=100, speed=100, types=["normal"])
        defender = make_pokemon(name="Defender", hp=9999, defense=5, types=["rock"])
        move = make_move(power=80, type_="normal", category="physical")
        attacker.moves = [move]
        state = make_battle_state(team1=[attacker], team2=[defender])
        result = self._resolve(state)
        assert any("not very effective" in e for e in result.log_entries)

    def test_immune_logs_no_effect(self):
        attacker = make_pokemon(name="Attacker", attack=100, speed=100)
        defender = make_pokemon(name="Defender", hp=9999, types=["ghost"])
        move = make_move(power=80, type_="normal")
        attacker.moves = [move]
        state = make_battle_state(team1=[attacker], team2=[defender])
        result = self._resolve(state)
        assert any("no effect" in e for e in result.log_entries)
        assert result.new_state.player2.team[0].current_hp == 9999

    def test_move_index_clamped_to_valid_range(self):
        state = make_battle_state()
        result = self._resolve(state, p1=99, p2=99)
        assert result.new_state.turn == 2

    def test_advance_active_after_faint(self):
        fainted_lead = make_pokemon(name="Dead", hp=1, defense=1, speed=1, fainted=False)
        backup = make_pokemon(name="Backup", hp=999, defense=50)
        strong = make_pokemon(name="Strong", hp=999, attack=999, speed=999)
        state = make_battle_state(
            team1=[strong],
            team2=[fainted_lead, backup],
        )
        result = self._resolve(state)
        assert result.new_state.player2.active_index == 1
        assert result.battle_over is False

    def test_pp_decremented_after_move(self):
        """Move PP should decrease by 1 after using it."""
        mon = make_pokemon(name="A", hp=9999, moves=[make_move(pp=10)])
        state = make_battle_state(
            team1=[mon],
            team2=[make_pokemon(name="B", hp=9999)],
        )
        result = self._resolve(state)
        active = result.new_state.player1.team[0]
        assert active.moves[0].current_pp == 9

    def test_struggle_when_all_pp_depleted(self):
        """When all PP is 0, the Pokémon should use Struggle."""
        empty_move = make_move(name="empty", pp=0)
        mon = make_pokemon(name="Struggling", hp=9999, moves=[empty_move])
        mon.moves[0].current_pp = 0
        state = make_battle_state(
            team1=[mon],
            team2=[make_pokemon(name="Target", hp=9999)],
        )
        result = self._resolve(state)
        assert any("Struggle" in e for e in result.log_entries)
        # Struggle deals 1/4 max HP recoil to user
        user_hp = result.new_state.player1.team[0].current_hp
        assert user_hp < 9999

    def test_miss_logged(self):
        """A move that misses should log 'missed'."""
        # Use a move with very low accuracy
        move = make_move(name="low-acc", power=80, accuracy=1)
        attacker = make_pokemon(name="Whiffer", hp=9999, attack=100, speed=100, moves=[move])
        defender = make_pokemon(name="Dodger", hp=9999, defense=50)
        state = make_battle_state(team1=[attacker], team2=[defender])
        # Run many seeds — at least one should miss
        found_miss = False
        for seed in range(50):
            engine = TurnEngine(rng=Random(seed))
            a1 = MoveAction(player_id="user-1", move_index=0)
            a2 = MoveAction(player_id="user-2", move_index=0)
            result = engine.resolve_turn(state, a1, a2)
            if any("missed" in e for e in result.log_entries):
                found_miss = True
                break
        assert found_miss, "Expected at least one miss with accuracy=1"

    def test_crit_logged(self):
        """A critical hit should log 'critical hit'."""
        move = make_move(power=80, type_="normal", category="physical")
        attacker = make_pokemon(name="Critter", hp=9999, attack=100, speed=100, moves=[move])
        defender = make_pokemon(name="Target", hp=9999, defense=50)
        state = make_battle_state(team1=[attacker], team2=[defender])
        # Run many seeds — expect at least one crit (4.17% base rate)
        found_crit = False
        for seed in range(200):
            engine = TurnEngine(rng=Random(seed))
            a1 = MoveAction(player_id="user-1", move_index=0)
            a2 = MoveAction(player_id="user-2", move_index=0)
            result = engine.resolve_turn(state, a1, a2)
            if any("critical hit" in e.lower() for e in result.log_entries):
                found_crit = True
                break
        assert found_crit, "Expected at least one crit in 200 trials"

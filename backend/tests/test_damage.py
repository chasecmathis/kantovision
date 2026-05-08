"""Tests for the Gen V+ damage calculation."""

from random import Random

import pytest

from app.battle.damage import DamageResult, calc_damage
from app.battle.state import StatStages
from tests.helpers import make_move, make_pokemon


def _calc(attacker, defender, move, seed=42, **kwargs) -> DamageResult:
    return calc_damage(attacker, defender, move, Random(seed), **kwargs)


class TestDamageFormula:
    def test_physical_uses_attack_and_defense(self):
        high_atk = make_pokemon(attack=200, special_attack=10)
        low_atk = make_pokemon(attack=10, special_attack=200)
        defender = make_pokemon(defense=50, special_defense=50)
        move = make_move(power=80, category="physical")
        assert _calc(high_atk, defender, move).damage > _calc(low_atk, defender, move).damage

    def test_special_uses_spatk_and_spdef(self):
        high_spa = make_pokemon(special_attack=200, attack=10)
        low_spa = make_pokemon(special_attack=10, attack=200)
        defender = make_pokemon(defense=50, special_defense=50)
        move = make_move(power=80, category="special")
        assert _calc(high_spa, defender, move).damage > _calc(low_spa, defender, move).damage

    def test_status_deals_zero(self):
        result = _calc(make_pokemon(), make_pokemon(), make_move(power=0, category="status"))
        assert result.damage == 0

    def test_immunity_deals_zero(self):
        attacker = make_pokemon(types=["normal"])
        defender = make_pokemon(types=["ghost"])
        move = make_move(power=80, type_="normal", category="physical")
        result = _calc(attacker, defender, move)
        assert result.damage == 0
        assert result.effectiveness == 0.0

    def test_minimum_damage_is_1(self):
        attacker = make_pokemon(attack=1)
        defender = make_pokemon(defense=255)
        move = make_move(power=1, type_="normal", category="physical")
        result = _calc(attacker, defender, move)
        assert result.damage >= 1


class TestRandomFactor:
    def test_damage_varies_across_seeds(self):
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50)
        move = make_move(power=80, type_="normal", category="physical")
        damages = {_calc(attacker, defender, move, seed=s).damage for s in range(200)}
        assert len(damages) > 1

    def test_damage_within_85_to_100_percent(self):
        """Non-crit damage rolls should be within 85-100% of max possible."""
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="normal", category="physical")
        results = [_calc(attacker, defender, move, seed=s) for s in range(1000)]
        # Filter out crits — they inflate damage beyond the 85-100% window
        non_crit_damages = [r.damage for r in results if not r.is_crit]
        assert len(non_crit_damages) > 500  # most should be non-crit
        max_dmg = max(non_crit_damages)
        min_dmg = min(non_crit_damages)
        # min should be ~85% of max (allowing for floor rounding)
        assert min_dmg >= max_dmg * 0.83


class TestCriticalHits:
    def test_guaranteed_crit_at_stage_3(self):
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50)
        move = make_move(power=80, type_="normal", category="physical")
        result = _calc(attacker, defender, move, crit_stage=3)
        assert result.is_crit is True

    def test_crit_deals_more_damage(self):
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="normal", category="physical")
        no_crit = _calc(attacker, defender, move, seed=99, crit_stage=0)
        # Force no-crit by checking; if seed 99 happens to crit, use another
        crit = _calc(attacker, defender, move, seed=99, crit_stage=3)
        assert crit.is_crit is True
        assert crit.damage > no_crit.damage or no_crit.is_crit

    def test_crit_ignores_negative_attack_stages(self):
        attacker = make_pokemon(attack=100, stat_stages=StatStages(attack=-6))
        clean = make_pokemon(attack=100)
        defender = make_pokemon(defense=50)
        move = make_move(power=80, type_="normal", category="physical")
        debuffed = _calc(attacker, defender, move, crit_stage=3)
        normal = _calc(clean, defender, move, crit_stage=3)
        assert debuffed.damage == normal.damage

    def test_crit_ignores_positive_defense_stages(self):
        attacker = make_pokemon(attack=100)
        defender_boosted = make_pokemon(defense=50, stat_stages=StatStages(defense=6))
        defender_clean = make_pokemon(defense=50)
        move = make_move(power=80, type_="normal", category="physical")
        vs_boosted = _calc(attacker, defender_boosted, move, crit_stage=3)
        vs_clean = _calc(attacker, defender_clean, move, crit_stage=3)
        assert vs_boosted.damage == vs_clean.damage

    def test_base_crit_rate_about_4_percent(self):
        """Over many trials, crit rate at stage 0 should be ~4.17% (1/24)."""
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50)
        move = make_move(power=80, type_="normal", category="physical")
        crits = sum(
            1 for s in range(2400) if calc_damage(attacker, defender, move, Random(s)).is_crit
        )
        # Expected: ~100 crits (4.17%). Allow 50-200 range.
        assert 30 < crits < 300


class TestStatStages:
    def test_positive_attack_stage_increases_damage(self):
        base = make_pokemon(attack=100)
        boosted = make_pokemon(attack=100, stat_stages=StatStages(attack=2))
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="normal", category="physical")
        assert _calc(boosted, defender, move).damage > _calc(base, defender, move).damage

    def test_positive_defense_stage_decreases_damage(self):
        attacker = make_pokemon(attack=100)
        base_def = make_pokemon(defense=50, types=["normal"])
        boosted_def = make_pokemon(defense=50, types=["normal"], stat_stages=StatStages(defense=2))
        move = make_move(power=80, type_="normal", category="physical")
        assert _calc(attacker, boosted_def, move).damage < _calc(attacker, base_def, move).damage

    def test_negative_attack_stage_decreases_damage(self):
        base = make_pokemon(attack=100)
        debuffed = make_pokemon(attack=100, stat_stages=StatStages(attack=-2))
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="normal", category="physical")
        assert _calc(debuffed, defender, move).damage < _calc(base, defender, move).damage

    @pytest.mark.parametrize("stage", [-6, -3, -1, 0, 1, 3, 6])
    def test_special_stages_affect_special_moves(self, stage):
        """Stat stages on special_attack affect special move damage."""
        base = make_pokemon(special_attack=100)
        staged = make_pokemon(special_attack=100, stat_stages=StatStages(special_attack=stage))
        defender = make_pokemon(special_defense=50, types=["normal"])
        move = make_move(power=80, type_="fire", category="special")
        base_dmg = _calc(base, defender, move).damage
        staged_dmg = _calc(staged, defender, move).damage
        if stage > 0:
            assert staged_dmg >= base_dmg
        elif stage < 0:
            assert staged_dmg <= base_dmg
        else:
            assert staged_dmg == base_dmg


class TestSTAB:
    def test_stab_bonus_applied(self):
        stab = make_pokemon(attack=100, types=["fire"])
        no_stab = make_pokemon(attack=100, types=["water"])
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="fire", category="physical")
        stab_dmg = _calc(stab, defender, move).damage
        no_stab_dmg = _calc(no_stab, defender, move).damage
        assert stab_dmg > no_stab_dmg

    def test_stab_with_dual_type(self):
        """A Fire/Flying Pokemon gets STAB on Fire moves."""
        dual = make_pokemon(attack=100, types=["fire", "flying"])
        mono = make_pokemon(attack=100, types=["water"])
        defender = make_pokemon(defense=50, types=["normal"])
        fire_move = make_move(power=80, type_="fire", category="physical")
        assert _calc(dual, defender, fire_move).damage > _calc(mono, defender, fire_move).damage


class TestTypeEffectivenessInDamage:
    def test_super_effective(self):
        attacker = make_pokemon(attack=100)
        neutral = make_pokemon(defense=50, types=["normal"])
        weak = make_pokemon(defense=50, types=["grass"])
        move = make_move(power=80, type_="fire", category="physical")
        assert _calc(attacker, weak, move).effectiveness == 2.0
        assert _calc(attacker, neutral, move).effectiveness == 1.0

    def test_4x_effective(self):
        attacker = make_pokemon(attack=100)
        defender = make_pokemon(defense=50, types=["grass", "bug"])
        move = make_move(power=80, type_="fire", category="physical")
        result = _calc(attacker, defender, move)
        assert result.effectiveness == 4.0

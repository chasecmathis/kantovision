"""Tests for stat stage system: apply_stat_change, clamping, multipliers, log messages."""

from random import Random

import pytest

from app.battle.actions import MoveAction
from app.battle.engine import TurnEngine
from app.battle.pipeline import TurnContext
from app.battle.state import StatStages
from app.battle.stats import get_stat_stage_multiplier
from tests.helpers import make_battle_state, make_move, make_pokemon

SEED = 42


def _engine(seed=SEED) -> TurnEngine:
    return TurnEngine(rng=Random(seed))


def _resolve(engine, state, p1=0, p2=0):
    a1 = MoveAction(player_id=state.player1.user_id, move_index=p1)
    a2 = MoveAction(player_id=state.player2.user_id, move_index=p2)
    return engine.resolve_turn(state, a1, a2)


def _ctx(state=None) -> TurnContext:
    return TurnContext(state or make_battle_state(), Random(SEED))


# ─── Stat stage multiplier table ────────────────────────────────────────────


class TestStatStageMultiplier:
    @pytest.mark.parametrize(
        "stage,expected",
        [
            (-6, 2 / 8),
            (-5, 2 / 7),
            (-4, 2 / 6),
            (-3, 2 / 5),
            (-2, 2 / 4),
            (-1, 2 / 3),
            (0, 1.0),
            (1, 3 / 2),
            (2, 4 / 2),
            (3, 5 / 2),
            (4, 6 / 2),
            (5, 7 / 2),
            (6, 8 / 2),
        ],
    )
    def test_combat_stat_multiplier(self, stage, expected):
        mult = get_stat_stage_multiplier(stage, is_accuracy_evasion=False)
        assert abs(mult - expected) < 0.01

    @pytest.mark.parametrize(
        "stage,expected",
        [
            (-6, 3 / 9),
            (-3, 3 / 6),
            (0, 1.0),
            (3, 6 / 3),
            (6, 9 / 3),
        ],
    )
    def test_accuracy_evasion_multiplier(self, stage, expected):
        mult = get_stat_stage_multiplier(stage, is_accuracy_evasion=True)
        assert abs(mult - expected) < 0.01


# ─── TurnContext.apply_stat_change ──────────────────────────────────────────


class TestApplyStatChange:
    def test_raise_one_stage(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test")
        actual = ctx.apply_stat_change(mon, "attack", 1)
        assert actual == 1
        assert mon.stat_stages.attack == 1
        assert any("rose" in e and "Test" in e for e in ctx.log)

    def test_lower_one_stage(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test")
        actual = ctx.apply_stat_change(mon, "defense", -1)
        assert actual == -1
        assert mon.stat_stages.defense == -1
        assert any("fell" in e and "Test" in e for e in ctx.log)

    def test_raise_two_stages_says_sharply(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test")
        ctx.apply_stat_change(mon, "attack", 2)
        assert mon.stat_stages.attack == 2
        assert any("sharply" in e for e in ctx.log)

    def test_lower_two_stages_says_harshly(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test")
        ctx.apply_stat_change(mon, "defense", -2)
        assert mon.stat_stages.defense == -2
        assert any("harshly" in e for e in ctx.log)

    def test_raise_three_stages_says_drastically(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test")
        ctx.apply_stat_change(mon, "speed", 3)
        assert mon.stat_stages.speed == 3
        assert any("drastically" in e for e in ctx.log)

    def test_lower_three_stages_says_severely(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test")
        ctx.apply_stat_change(mon, "speed", -3)
        assert mon.stat_stages.speed == -3
        assert any("severely" in e for e in ctx.log)

    def test_clamp_at_plus_six(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test", stat_stages=StatStages(attack=5))
        actual = ctx.apply_stat_change(mon, "attack", 3)
        assert actual == 1  # only went from 5 → 6
        assert mon.stat_stages.attack == 6

    def test_clamp_at_minus_six(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test", stat_stages=StatStages(defense=-5))
        actual = ctx.apply_stat_change(mon, "defense", -3)
        assert actual == -1  # only went from -5 → -6
        assert mon.stat_stages.defense == -6

    def test_already_at_max_logs_wont_go_higher(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test", stat_stages=StatStages(attack=6))
        actual = ctx.apply_stat_change(mon, "attack", 1)
        assert actual == 0
        assert any("won't go any higher" in e for e in ctx.log)

    def test_already_at_min_logs_wont_go_lower(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test", stat_stages=StatStages(defense=-6))
        actual = ctx.apply_stat_change(mon, "defense", -1)
        assert actual == 0
        assert any("won't go any lower" in e for e in ctx.log)

    def test_source_appears_in_log(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test")
        ctx.apply_stat_change(mon, "attack", -1, source="Intimidate")
        assert any("Intimidate" in e for e in ctx.log)

    def test_multiple_stat_changes_accumulate(self):
        ctx = _ctx()
        mon = make_pokemon(name="Test")
        ctx.apply_stat_change(mon, "speed", 2)
        ctx.apply_stat_change(mon, "speed", 2)
        ctx.apply_stat_change(mon, "speed", 2)
        assert mon.stat_stages.speed == 6


# ─── get_effective_stat with stages ─────────────────────────────────────────


class TestEffectiveStat:
    def test_positive_stages_increase_stat(self):
        ctx = _ctx()
        mon = make_pokemon(attack=100, stat_stages=StatStages(attack=2))
        effective = ctx.get_effective_stat(mon, "attack")
        assert effective == 200  # 100 * (4/2)

    def test_negative_stages_decrease_stat(self):
        ctx = _ctx()
        mon = make_pokemon(defense=100, stat_stages=StatStages(defense=-2))
        effective = ctx.get_effective_stat(mon, "defense")
        assert effective == 50  # 100 * (2/4)

    def test_zero_stages_no_change(self):
        ctx = _ctx()
        mon = make_pokemon(speed=80)
        effective = ctx.get_effective_stat(mon, "speed")
        assert effective == 80

    def test_effective_stat_minimum_one(self):
        ctx = _ctx()
        mon = make_pokemon(speed=1, stat_stages=StatStages(speed=-6))
        effective = ctx.get_effective_stat(mon, "speed")
        assert effective >= 1


# ─── Integration: stat stage moves in full turn ─────────────────────────────


class TestStatStageMoveIntegration:
    def test_swords_dance_raises_attack_two(self):
        """Swords Dance should raise the user's attack by 2 stages."""
        user = make_pokemon(
            name="Dancer",
            hp=9999,
            speed=100,
            moves=[make_move(name="swords-dance", power=0, type_="normal", category="status")],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[user], team2=[other])

        result = _resolve(_engine(), state)
        dancer = result.new_state.player1.team[0]
        assert dancer.stat_stages.attack == 2
        assert any("sharply" in e for e in result.log_entries)

    def test_dragon_dance_raises_attack_and_speed(self):
        user = make_pokemon(
            name="DDancer",
            hp=9999,
            speed=100,
            moves=[make_move(name="dragon-dance", power=0, type_="dragon", category="status")],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[user], team2=[other])

        result = _resolve(_engine(), state)
        mon = result.new_state.player1.team[0]
        assert mon.stat_stages.attack == 1
        assert mon.stat_stages.speed == 1

    def test_shell_smash_raises_and_lowers(self):
        user = make_pokemon(
            name="Smasher",
            hp=9999,
            speed=100,
            moves=[make_move(name="shell-smash", power=0, type_="normal", category="status")],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[user], team2=[other])

        result = _resolve(_engine(), state)
        mon = result.new_state.player1.team[0]
        assert mon.stat_stages.attack == 2
        assert mon.stat_stages.special_attack == 2
        assert mon.stat_stages.speed == 2
        assert mon.stat_stages.defense == -1
        assert mon.stat_stages.special_defense == -1

    def test_growl_lowers_opponent_attack(self):
        user = make_pokemon(
            name="Growler",
            hp=9999,
            speed=100,
            moves=[make_move(name="growl", power=0, type_="normal", category="status")],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50)
        state = make_battle_state(team1=[user], team2=[target])

        result = _resolve(_engine(), state)
        target_state = result.new_state.player2.team[0]
        assert target_state.stat_stages.attack == -1

    def test_screech_lowers_opponent_defense_two(self):
        user = make_pokemon(
            name="Screecher",
            hp=9999,
            speed=100,
            moves=[make_move(name="screech", power=0, type_="normal", category="status")],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50)
        state = make_battle_state(team1=[user], team2=[target])

        result = _resolve(_engine(), state)
        target_state = result.new_state.player2.team[0]
        assert target_state.stat_stages.defense == -2

    def test_close_combat_self_stat_drops(self):
        """Close Combat should lower the user's defense and special defense by 1."""
        user = make_pokemon(
            name="Fighter",
            hp=9999,
            attack=100,
            speed=100,
            moves=[
                make_move(name="close-combat", power=120, type_="fighting", category="physical")
            ],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50, types=["normal"])
        state = make_battle_state(team1=[user], team2=[target])

        result = _resolve(_engine(), state)
        fighter = result.new_state.player1.team[0]
        assert fighter.stat_stages.defense == -1
        assert fighter.stat_stages.special_defense == -1

    def test_overheat_self_spa_drop(self):
        """Overheat should lower the user's special attack by 2."""
        user = make_pokemon(
            name="Blazer",
            hp=9999,
            special_attack=100,
            speed=100,
            moves=[make_move(name="overheat", power=130, type_="fire", category="special")],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50, types=["normal"])
        state = make_battle_state(team1=[user], team2=[target])

        result = _resolve(_engine(), state)
        blazer = result.new_state.player1.team[0]
        assert blazer.stat_stages.special_attack == -2

    def test_stat_stages_persist_across_turns(self):
        """Stat boosts from one turn should persist to the next."""
        user = make_pokemon(
            name="DDancer",
            hp=9999,
            attack=100,
            speed=100,
            moves=[make_move(name="dragon-dance", power=0, type_="dragon", category="status")],
        )
        other = make_pokemon(
            name="Other",
            hp=9999,
            speed=50,
            moves=[make_move(name="tackle", power=40)],
        )
        state = make_battle_state(team1=[user], team2=[other])

        engine = _engine()
        # Turn 1: Dragon Dance
        r1 = _resolve(engine, state)
        assert r1.new_state.player1.team[0].stat_stages.attack == 1

        # Turn 2: Dragon Dance again
        r2 = _resolve(engine, r1.new_state)
        assert r2.new_state.player1.team[0].stat_stages.attack == 2
        assert r2.new_state.player1.team[0].stat_stages.speed == 2

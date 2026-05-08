"""Tests for move secondary effects: status infliction, stat drops, flinch, recoil, drain."""

from random import Random

import pytest

from app.battle.actions import MoveAction
from app.battle.effects.base import MoveEffectSpec, StatChange
from app.battle.effects.moves.effects import apply_move_effect, apply_status_move_effect
from app.battle.effects.registry import MOVE_EFFECT_REGISTRY
from app.battle.engine import TurnEngine
from app.battle.enums import StatusCondition, VolatileStatus
from app.battle.pipeline import TurnContext
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


# ─── Registry ───────────────────────────────────────────────────────────────


class TestMoveEffectRegistry:
    def test_common_moves_registered(self):
        for name in [
            "flamethrower",
            "thunderbolt",
            "ice-beam",
            "sludge-bomb",
            "close-combat",
            "swords-dance",
            "dragon-dance",
            "iron-head",
            "drain-punch",
            "brave-bird",
            "will-o-wisp",
            "thunder-wave",
        ]:
            assert name in MOVE_EFFECT_REGISTRY, f"{name} not registered"

    def test_flamethrower_spec(self):
        spec = MOVE_EFFECT_REGISTRY["flamethrower"]
        assert spec.status == StatusCondition.BURN
        assert spec.status_chance == 10

    def test_close_combat_spec(self):
        spec = MOVE_EFFECT_REGISTRY["close-combat"]
        assert len(spec.self_stat_changes) == 2
        stats = {sc.stat for sc in spec.self_stat_changes}
        assert stats == {"defense", "special_defense"}

    def test_iron_head_spec(self):
        spec = MOVE_EFFECT_REGISTRY["iron-head"]
        assert spec.flinch_chance == 30

    def test_drain_punch_spec(self):
        spec = MOVE_EFFECT_REGISTRY["drain-punch"]
        assert spec.drain_fraction == 0.5

    def test_brave_bird_spec(self):
        spec = MOVE_EFFECT_REGISTRY["brave-bird"]
        assert abs(spec.recoil_fraction - 1 / 3) < 0.01


# ─── Secondary status infliction ────────────────────────────────────────────


class TestSecondaryStatus:
    def test_status_infliction_with_100_percent_chance(self):
        ctx = _ctx()
        spec = MoveEffectSpec(status=StatusCondition.BURN, status_chance=100)
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def", types=["normal"])
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert defender.status == StatusCondition.BURN

    def test_status_infliction_respects_chance(self):
        """With 10% chance, most rolls should not inflict status."""
        spec = MoveEffectSpec(status=StatusCondition.BURN, status_chance=10)
        burns = 0
        for seed in range(200):
            ctx = _ctx()
            defender = make_pokemon(name="Def", types=["normal"])
            attacker = make_pokemon(name="Atk")
            apply_move_effect(ctx, spec, attacker, defender, 50, Random(seed))
            if defender.status == StatusCondition.BURN:
                burns += 1
        # 10% → ~20 in 200. Allow 3-40.
        assert 3 < burns < 40, f"Expected ~10% burn rate, got {burns}/200"

    def test_status_not_applied_to_fainted(self):
        ctx = _ctx()
        spec = MoveEffectSpec(status=StatusCondition.BURN, status_chance=100)
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def", fainted=True)
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert defender.status == StatusCondition.NONE

    def test_status_not_applied_if_already_statused(self):
        ctx = _ctx()
        spec = MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=100)
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def", status=StatusCondition.BURN)
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert defender.status == StatusCondition.BURN  # unchanged

    def test_type_immunity_prevents_status(self):
        ctx = _ctx()
        spec = MoveEffectSpec(status=StatusCondition.BURN, status_chance=100)
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def", types=["fire"])
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert defender.status == StatusCondition.NONE


# ─── Stat changes on target ─────────────────────────────────────────────────


class TestTargetStatChanges:
    def test_stat_drop_at_100_percent(self):
        ctx = _ctx()
        spec = MoveEffectSpec(
            stat_changes=[StatChange(stat="defense", stages=-1)],
            stat_chance=100,
        )
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert defender.stat_stages.defense == -1

    def test_stat_drop_respects_chance(self):
        """With 10% chance, most rolls should not apply the drop."""
        spec = MoveEffectSpec(
            stat_changes=[StatChange(stat="special_defense", stages=-1)],
            stat_chance=10,
        )
        drops = 0
        for seed in range(200):
            ctx = _ctx()
            defender = make_pokemon(name="Def")
            attacker = make_pokemon(name="Atk")
            apply_move_effect(ctx, spec, attacker, defender, 50, Random(seed))
            if defender.stat_stages.special_defense < 0:
                drops += 1
        assert 3 < drops < 40, f"Expected ~10% drop rate, got {drops}/200"

    def test_stat_drop_not_applied_to_fainted(self):
        ctx = _ctx()
        spec = MoveEffectSpec(
            stat_changes=[StatChange(stat="defense", stages=-1)],
            stat_chance=100,
        )
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def", fainted=True)
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert defender.stat_stages.defense == 0


# ─── Self stat changes ──────────────────────────────────────────────────────


class TestSelfStatChanges:
    def test_self_stat_change_always_applies(self):
        """Self stat changes from damaging moves always apply (no chance roll)."""
        ctx = _ctx()
        spec = MoveEffectSpec(
            self_stat_changes=[
                StatChange(stat="defense", stages=-1),
                StatChange(stat="special_defense", stages=-1),
            ],
        )
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert attacker.stat_stages.defense == -1
        assert attacker.stat_stages.special_defense == -1

    def test_self_stat_not_applied_if_fainted(self):
        ctx = _ctx()
        spec = MoveEffectSpec(
            self_stat_changes=[StatChange(stat="attack", stages=1)],
        )
        attacker = make_pokemon(name="Atk", fainted=True)
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert attacker.stat_stages.attack == 0


# ─── Flinch ─────────────────────────────────────────────────────────────────


class TestFlinch:
    def test_flinch_adds_volatile_status(self):
        ctx = _ctx()
        spec = MoveEffectSpec(flinch_chance=100)
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert VolatileStatus.FLINCH in defender.volatile_statuses

    def test_flinch_respects_chance(self):
        spec = MoveEffectSpec(flinch_chance=30)
        flinches = 0
        for seed in range(200):
            ctx = _ctx()
            defender = make_pokemon(name="Def")
            attacker = make_pokemon(name="Atk")
            apply_move_effect(ctx, spec, attacker, defender, 50, Random(seed))
            if VolatileStatus.FLINCH in defender.volatile_statuses:
                flinches += 1
        # 30% → ~60 in 200. Allow 30-100.
        assert 30 < flinches < 100, f"Expected ~30% flinch rate, got {flinches}/200"

    def test_flinch_not_applied_to_fainted(self):
        ctx = _ctx()
        spec = MoveEffectSpec(flinch_chance=100)
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def", fainted=True)
        apply_move_effect(ctx, spec, attacker, defender, 50, Random(0))
        assert VolatileStatus.FLINCH not in defender.volatile_statuses

    def test_flinch_prevents_action_in_battle(self):
        """A flinched Pokemon should not be able to act."""
        fast = make_pokemon(
            name="Fast",
            hp=9999,
            attack=100,
            speed=200,
            moves=[make_move(name="iron-head", power=80, type_="steel", category="physical")],
        )
        slow = make_pokemon(
            name="Slow",
            hp=9999,
            speed=10,
            types=["normal"],
            moves=[make_move(name="tackle", power=40)],
        )
        state = make_battle_state(team1=[fast], team2=[slow])

        # Run many trials to find one where flinch occurs
        for seed in range(100):
            engine = TurnEngine(rng=Random(seed))
            result = _resolve(engine, state)
            if any("flinched" in e for e in result.log_entries):
                # Slow should not have used a move
                assert not any("Slow used" in e for e in result.log_entries)
                return
        pytest.fail("Expected at least one flinch in 100 trials")


# ─── Recoil ─────────────────────────────────────────────────────────────────


class TestRecoil:
    def test_recoil_damages_attacker(self):
        ctx = _ctx()
        spec = MoveEffectSpec(recoil_fraction=1 / 3)
        attacker = make_pokemon(name="Atk", hp=300)
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 90, Random(0))
        # Recoil = max(1, int(90 * 1/3)) = 30
        assert attacker.current_hp == 270
        assert any("recoil" in e for e in ctx.log)

    def test_recoil_minimum_one(self):
        ctx = _ctx()
        spec = MoveEffectSpec(recoil_fraction=1 / 3)
        attacker = make_pokemon(name="Atk", hp=300)
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 1, Random(0))
        # Recoil = max(1, int(1 * 1/3)) = max(1, 0) = 1
        assert attacker.current_hp == 299

    def test_recoil_no_damage_if_zero_dealt(self):
        ctx = _ctx()
        spec = MoveEffectSpec(recoil_fraction=1 / 3)
        attacker = make_pokemon(name="Atk", hp=300)
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 0, Random(0))
        assert attacker.current_hp == 300

    def test_recoil_can_faint_attacker(self):
        ctx = _ctx()
        spec = MoveEffectSpec(recoil_fraction=1 / 3)
        attacker = make_pokemon(name="Atk", hp=300)
        attacker.current_hp = 5
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 90, Random(0))
        assert attacker.fainted

    def test_recoil_not_applied_if_attacker_fainted(self):
        ctx = _ctx()
        spec = MoveEffectSpec(recoil_fraction=1 / 3)
        attacker = make_pokemon(name="Atk", fainted=True)
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 90, Random(0))
        # Should not crash or further reduce HP
        assert attacker.current_hp == 0

    def test_brave_bird_recoil_in_battle(self):
        """Brave Bird should deal 1/3 recoil in a real turn."""
        user = make_pokemon(
            name="Bird",
            hp=9999,
            attack=100,
            speed=100,
            moves=[make_move(name="brave-bird", power=120, type_="flying", category="physical")],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50, types=["normal"])
        state = make_battle_state(team1=[user], team2=[target])

        result = _resolve(_engine(), state)
        assert any("recoil" in e for e in result.log_entries)
        bird = result.new_state.player1.team[0]
        assert bird.current_hp < 9999  # took recoil damage


# ─── Drain ──────────────────────────────────────────────────────────────────


class TestDrain:
    def test_drain_heals_attacker(self):
        ctx = _ctx()
        spec = MoveEffectSpec(drain_fraction=0.5)
        attacker = make_pokemon(name="Atk", hp=300)
        attacker.current_hp = 200
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 100, Random(0))
        # Heal = max(1, int(100 * 0.5)) = 50
        assert attacker.current_hp == 250
        assert any("restored" in e for e in ctx.log)

    def test_drain_does_not_overheal(self):
        ctx = _ctx()
        spec = MoveEffectSpec(drain_fraction=0.5)
        attacker = make_pokemon(name="Atk", hp=100)
        attacker.current_hp = 99
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 100, Random(0))
        assert attacker.current_hp == 100  # capped at max_hp

    def test_drain_minimum_one(self):
        ctx = _ctx()
        spec = MoveEffectSpec(drain_fraction=0.5)
        attacker = make_pokemon(name="Atk", hp=300)
        attacker.current_hp = 200
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 1, Random(0))
        # Heal = max(1, int(1 * 0.5)) = max(1, 0) = 1
        assert attacker.current_hp == 201

    def test_drain_no_heal_if_zero_damage(self):
        ctx = _ctx()
        spec = MoveEffectSpec(drain_fraction=0.5)
        attacker = make_pokemon(name="Atk", hp=300)
        attacker.current_hp = 200
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 0, Random(0))
        assert attacker.current_hp == 200

    def test_drain_not_applied_if_fainted(self):
        ctx = _ctx()
        spec = MoveEffectSpec(drain_fraction=0.5)
        attacker = make_pokemon(name="Atk", fainted=True)
        defender = make_pokemon(name="Def")
        apply_move_effect(ctx, spec, attacker, defender, 100, Random(0))
        assert attacker.current_hp == 0

    def test_giga_drain_heals_in_battle(self):
        """Giga Drain should heal the attacker in a real turn."""
        user = make_pokemon(
            name="Drainer",
            hp=9999,
            special_attack=100,
            speed=100,
            moves=[make_move(name="giga-drain", power=75, type_="grass", category="special")],
        )
        user.current_hp = 5000
        # Target uses a status move so it doesn't damage the drainer
        target = make_pokemon(
            name="Target",
            hp=9999,
            speed=50,
            types=["normal"],
            moves=[make_move(name="growl", power=0, type_="normal", category="status")],
        )
        state = make_battle_state(team1=[user], team2=[target])

        result = _resolve(_engine(), state)
        drainer = result.new_state.player1.team[0]
        assert drainer.current_hp > 5000
        assert any("restored" in e for e in result.log_entries)


# ─── Status move effects ────────────────────────────────────────────────────


class TestStatusMoveEffect:
    def test_status_move_stat_changes_always_apply(self):
        """Status moves apply stat changes at 100% (ignoring stat_chance)."""
        ctx = _ctx()
        spec = MoveEffectSpec(
            stat_changes=[StatChange(stat="defense", stages=-2)],
            stat_chance=10,  # this should be ignored for status moves
        )
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def")
        apply_status_move_effect(ctx, spec, attacker, defender, Random(0))
        assert defender.stat_stages.defense == -2

    def test_status_move_self_stat_changes(self):
        ctx = _ctx()
        spec = MoveEffectSpec(
            self_stat_changes=[
                StatChange(stat="attack", stages=2),
                StatChange(stat="speed", stages=1),
            ],
        )
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def")
        apply_status_move_effect(ctx, spec, attacker, defender, Random(0))
        assert attacker.stat_stages.attack == 2
        assert attacker.stat_stages.speed == 1

    def test_status_move_inflicts_status(self):
        ctx = _ctx()
        spec = MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=100)
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="Def", types=["normal"])
        apply_status_move_effect(ctx, spec, attacker, defender, Random(0))
        assert defender.status == StatusCondition.PARALYSIS

    def test_status_move_logs_failure(self):
        """If status fails (e.g. type immunity), should log it."""
        ctx = _ctx()
        spec = MoveEffectSpec(status=StatusCondition.BURN, status_chance=100)
        attacker = make_pokemon(name="Atk")
        defender = make_pokemon(name="FireMon", types=["fire"])
        apply_status_move_effect(ctx, spec, attacker, defender, Random(0))
        assert defender.status == StatusCondition.NONE
        assert any("didn't affect" in e for e in ctx.log)


# ─── Composed effects ───────────────────────────────────────────────────────


class TestComposedEffects:
    def test_flare_blitz_burn_and_recoil(self):
        """Flare Blitz should be able to inflict burn AND deal recoil."""
        spec = MOVE_EFFECT_REGISTRY["flare-blitz"]
        assert spec.status == StatusCondition.BURN
        assert spec.status_chance == 10
        assert abs(spec.recoil_fraction - 1 / 3) < 0.01

        # Test that both can apply
        # Force burn by using a seed that gives <= 10
        for seed in range(100):
            ctx = _ctx()
            a = make_pokemon(name="Atk", hp=300)
            d = make_pokemon(name="Def", types=["normal"])
            apply_move_effect(ctx, spec, a, d, 90, Random(seed))
            if d.status == StatusCondition.BURN:
                assert a.current_hp < 300  # recoil also applied
                return
        pytest.fail("Expected burn in 100 trials with 10% chance")

    def test_volt_tackle_para_and_recoil(self):
        spec = MOVE_EFFECT_REGISTRY["volt-tackle"]
        assert spec.status == StatusCondition.PARALYSIS
        assert spec.status_chance == 10
        assert abs(spec.recoil_fraction - 1 / 3) < 0.01


# ─── Full battle integration ────────────────────────────────────────────────


class TestMoveEffectIntegration:
    def test_thunderbolt_can_paralyze(self):
        """Thunderbolt has 10% chance to paralyze — should happen in some trials."""
        user = make_pokemon(
            name="Zapper",
            hp=9999,
            special_attack=100,
            speed=100,
            moves=[make_move(name="thunderbolt", power=90, type_="electric", category="special")],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50, types=["normal"])

        for seed in range(100):
            state = make_battle_state(team1=[user], team2=[target])
            engine = TurnEngine(rng=Random(seed))
            result = _resolve(engine, state)
            if result.new_state.player2.team[0].status == StatusCondition.PARALYSIS:
                assert any("paralyzed" in e for e in result.log_entries)
                return
        pytest.fail("Expected paralysis in 100 trials")

    def test_psychic_can_lower_spdef(self):
        """Psychic has 10% chance to lower SpDef — should happen in some trials."""
        user = make_pokemon(
            name="Psych",
            hp=9999,
            special_attack=100,
            speed=100,
            moves=[make_move(name="psychic", power=90, type_="psychic", category="special")],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50, types=["normal"])

        for seed in range(100):
            state = make_battle_state(team1=[user], team2=[target])
            engine = TurnEngine(rng=Random(seed))
            result = _resolve(engine, state)
            if result.new_state.player2.team[0].stat_stages.special_defense < 0:
                return
        pytest.fail("Expected SpDef drop in 100 trials")

    def test_will_o_wisp_burns_target(self):
        """Will-o-Wisp should burn the target."""
        user = make_pokemon(
            name="Burner",
            hp=9999,
            speed=100,
            moves=[
                make_move(name="will-o-wisp", power=0, type_="fire", category="status", accuracy=85)
            ],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50, types=["normal"])

        # Status moves with accuracy can miss; find a seed where it hits
        for seed in range(100):
            state_copy = make_battle_state(team1=[user], team2=[target])
            engine = TurnEngine(rng=Random(seed))
            result = _resolve(engine, state_copy)
            target_state = result.new_state.player2.team[0]
            if target_state.status == StatusCondition.BURN:
                assert any("burned" in e for e in result.log_entries)
                return
        pytest.fail("Expected burn in 100 trials")

    def test_low_sweep_lowers_opponent_speed(self):
        """Low Sweep should lower opponent's speed by 1 (100% chance)."""
        user = make_pokemon(
            name="Sweeper",
            hp=9999,
            attack=100,
            speed=100,
            moves=[make_move(name="low-sweep", power=65, type_="fighting", category="physical")],
        )
        target = make_pokemon(name="Target", hp=9999, speed=50, types=["normal"])
        state = make_battle_state(team1=[user], team2=[target])

        result = _resolve(_engine(), state)
        target_state = result.new_state.player2.team[0]
        assert target_state.stat_stages.speed == -1

    def test_struggle_recoil_no_double_recoil(self):
        """Struggle recoil is handled by the engine, not by MoveEffectSpec.
        A Pokemon with no PP should take Struggle recoil but not effect-based recoil."""
        mon = make_pokemon(
            name="Struggler",
            hp=400,
            attack=50,
            speed=100,
            moves=[make_move(name="tackle", power=40, pp=0)],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50, types=["normal"])
        state = make_battle_state(team1=[mon], team2=[other])

        result = _resolve(_engine(), state)
        assert any("recoil" in e for e in result.log_entries)
        # Count recoil messages — should be exactly 1 (from Struggle)
        recoil_msgs = [e for e in result.log_entries if "recoil" in e]
        assert len(recoil_msgs) == 1

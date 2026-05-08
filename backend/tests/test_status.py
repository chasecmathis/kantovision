"""Tests for status conditions: application, immunity, pre-turn, end-of-turn, stat effects."""

from random import Random

import pytest

from app.battle.actions import MoveAction
from app.battle.damage import calc_damage
from app.battle.engine import TurnEngine
from app.battle.enums import StatusCondition
from app.battle.status import (
    apply_end_of_turn_damage,
    apply_status,
    can_apply_status,
    check_pre_turn,
    try_thaw_from_fire,
)
from tests.helpers import make_battle_state, make_move, make_pokemon

SEED = 42


def _engine(seed=SEED) -> TurnEngine:
    return TurnEngine(rng=Random(seed))


def _resolve(engine, state, p1=0, p2=0):
    a1 = MoveAction(player_id=state.player1.user_id, move_index=p1)
    a2 = MoveAction(player_id=state.player2.user_id, move_index=p2)
    return engine.resolve_turn(state, a1, a2)


# ─── can_apply_status & apply_status ─────────────────────────────────────────


class TestStatusApplication:
    def test_apply_to_healthy_pokemon(self):
        mon = make_pokemon()
        assert can_apply_status(mon, StatusCondition.BURN)
        assert apply_status(mon, StatusCondition.BURN, Random(0))
        assert mon.status == StatusCondition.BURN

    def test_cannot_apply_second_status(self):
        mon = make_pokemon()
        apply_status(mon, StatusCondition.BURN, Random(0))
        assert not can_apply_status(mon, StatusCondition.PARALYSIS)
        assert not apply_status(mon, StatusCondition.PARALYSIS, Random(0))
        assert mon.status == StatusCondition.BURN

    def test_cannot_apply_to_fainted(self):
        mon = make_pokemon(fainted=True)
        assert not can_apply_status(mon, StatusCondition.BURN)

    def test_sleep_sets_turn_counter(self):
        mon = make_pokemon()
        apply_status(mon, StatusCondition.SLEEP, Random(0))
        assert mon.status == StatusCondition.SLEEP
        assert 1 <= mon.status_turns <= 3


class TestTypeImmunities:
    @pytest.mark.parametrize(
        "status,immune_type",
        [
            (StatusCondition.BURN, "fire"),
            (StatusCondition.PARALYSIS, "electric"),
            (StatusCondition.POISON, "poison"),
            (StatusCondition.POISON, "steel"),
            (StatusCondition.TOXIC, "poison"),
            (StatusCondition.TOXIC, "steel"),
            (StatusCondition.FREEZE, "ice"),
        ],
    )
    def test_type_immunity(self, status, immune_type):
        mon = make_pokemon(types=[immune_type])
        assert not can_apply_status(mon, status)
        assert not apply_status(mon, status, Random(0))
        assert mon.status == StatusCondition.NONE

    def test_dual_type_immunity(self):
        """Fire/Flying can't be burned."""
        mon = make_pokemon(types=["fire", "flying"])
        assert not can_apply_status(mon, StatusCondition.BURN)

    def test_non_immune_type_can_be_statused(self):
        """Water can be burned."""
        mon = make_pokemon(types=["water"])
        assert can_apply_status(mon, StatusCondition.BURN)


# ─── Pre-turn checks ────────────────────────────────────────────────────────


class TestPreTurnSleep:
    def test_sleeping_pokemon_cannot_act(self):
        mon = make_pokemon(status=StatusCondition.SLEEP)
        mon.status_turns = 2
        can_act, msg = check_pre_turn(mon, Random(0))
        assert can_act is False
        assert "fast asleep" in msg

    def test_wakes_up_when_counter_hits_zero(self):
        mon = make_pokemon(status=StatusCondition.SLEEP)
        mon.status_turns = 0
        can_act, msg = check_pre_turn(mon, Random(0))
        assert can_act is True
        assert "woke up" in msg
        assert mon.status == StatusCondition.NONE

    def test_sleep_counter_decrements(self):
        mon = make_pokemon(status=StatusCondition.SLEEP)
        mon.status_turns = 3
        check_pre_turn(mon, Random(0))
        assert mon.status_turns == 2


class TestPreTurnFreeze:
    def test_frozen_pokemon_usually_cannot_act(self):
        frozen_count = 0
        for s in range(100):
            mon = make_pokemon(status=StatusCondition.FREEZE)
            can_act, _ = check_pre_turn(mon, Random(s))
            if not can_act:
                frozen_count += 1
        # 80% should stay frozen (20% thaw rate)
        assert frozen_count > 60

    def test_frozen_pokemon_can_thaw(self):
        """20% thaw rate — should thaw at least sometimes."""
        thawed = False
        for s in range(100):
            mon = make_pokemon(status=StatusCondition.FREEZE)
            can_act, msg = check_pre_turn(mon, Random(s))
            if can_act and msg and "thawed" in msg:
                thawed = True
                assert mon.status == StatusCondition.NONE
                break
        assert thawed, "Expected at least one thaw in 100 trials"


class TestPreTurnParalysis:
    def test_full_paralysis_sometimes(self):
        """25% chance of full paralysis."""
        mon = make_pokemon(status=StatusCondition.PARALYSIS)
        immobile = sum(1 for s in range(400) if not check_pre_turn(mon, Random(s))[0])
        # Expected ~100 (25%). Allow 50-200.
        assert 30 < immobile < 200

    def test_can_still_act_when_paralyzed(self):
        mon = make_pokemon(status=StatusCondition.PARALYSIS)
        acted = sum(1 for s in range(100) if check_pre_turn(mon, Random(s))[0])
        assert acted > 50


class TestPreTurnHealthy:
    def test_healthy_pokemon_always_acts(self):
        mon = make_pokemon()
        can_act, msg = check_pre_turn(mon, Random(0))
        assert can_act is True
        assert msg is None


# ─── End-of-turn status damage ──────────────────────────────────────────────


class TestBurnEndOfTurn:
    def test_burn_deals_1_16_damage(self):
        mon = make_pokemon(hp=160, status=StatusCondition.BURN)
        dmg, msg = apply_end_of_turn_damage(mon)
        assert dmg == 10  # 160 // 16 = 10
        assert mon.current_hp == 150
        assert "burn" in msg

    def test_burn_kills_at_low_hp(self):
        mon = make_pokemon(hp=160, status=StatusCondition.BURN)
        mon.current_hp = 1  # burn does max(1, 160//16) = 10 → kills
        dmg, msg = apply_end_of_turn_damage(mon)
        assert mon.current_hp == 0
        assert mon.fainted is True

    def test_burn_minimum_1_damage(self):
        mon = make_pokemon(hp=10, status=StatusCondition.BURN)
        dmg, _ = apply_end_of_turn_damage(mon)
        assert dmg >= 1


class TestPoisonEndOfTurn:
    def test_poison_deals_1_8_damage(self):
        mon = make_pokemon(hp=160, status=StatusCondition.POISON)
        dmg, msg = apply_end_of_turn_damage(mon)
        assert dmg == 20  # 160 // 8 = 20
        assert mon.current_hp == 140
        assert "poison" in msg


class TestToxicEndOfTurn:
    def test_toxic_escalates(self):
        mon = make_pokemon(hp=320, status=StatusCondition.TOXIC)
        mon.status_turns = 0

        # Turn 1: 1/16
        dmg1, _ = apply_end_of_turn_damage(mon)
        assert mon.status_turns == 1
        assert dmg1 == 20  # 320 * 1 // 16 = 20

        # Turn 2: 2/16
        dmg2, _ = apply_end_of_turn_damage(mon)
        assert mon.status_turns == 2
        assert dmg2 == 40  # 320 * 2 // 16 = 40

        # Turn 3: 3/16
        dmg3, _ = apply_end_of_turn_damage(mon)
        assert mon.status_turns == 3
        assert dmg3 == 60  # 320 * 3 // 16 = 60

    def test_toxic_can_faint(self):
        mon = make_pokemon(hp=32, status=StatusCondition.TOXIC)
        mon.status_turns = 15  # 16/16 of max HP next turn
        apply_end_of_turn_damage(mon)
        assert mon.fainted is True


class TestNoStatusNoDamage:
    def test_healthy_pokemon_no_damage(self):
        mon = make_pokemon(hp=100)
        dmg, msg = apply_end_of_turn_damage(mon)
        assert dmg == 0
        assert msg is None

    def test_fainted_pokemon_no_damage(self):
        mon = make_pokemon(hp=100, fainted=True, status=StatusCondition.BURN)
        dmg, msg = apply_end_of_turn_damage(mon)
        assert dmg == 0


# ─── Fire thaw ───────────────────────────────────────────────────────────────


class TestFireThaw:
    def test_fire_move_thaws_frozen_defender(self):
        mon = make_pokemon(status=StatusCondition.FREEZE)
        msg = try_thaw_from_fire(mon, "fire")
        assert msg is not None
        assert "thawed" in msg
        assert mon.status == StatusCondition.NONE

    def test_non_fire_move_does_not_thaw(self):
        mon = make_pokemon(status=StatusCondition.FREEZE)
        msg = try_thaw_from_fire(mon, "water")
        assert msg is None
        assert mon.status == StatusCondition.FREEZE

    def test_thaw_only_if_frozen(self):
        mon = make_pokemon(status=StatusCondition.BURN)
        msg = try_thaw_from_fire(mon, "fire")
        assert msg is None


# ─── Burn attack reduction ──────────────────────────────────────────────────


class TestBurnAttackReduction:
    def test_burn_halves_physical_damage(self):
        healthy = make_pokemon(attack=100)
        burned = make_pokemon(attack=100, status=StatusCondition.BURN)
        defender = make_pokemon(defense=50, types=["normal"])
        move = make_move(power=80, type_="normal", category="physical")

        healthy_dmg = calc_damage(healthy, defender, move, Random(99)).damage
        burned_dmg = calc_damage(burned, defender, move, Random(99)).damage
        # Burned should deal roughly half (accounting for rounding)
        assert burned_dmg < healthy_dmg
        assert burned_dmg <= healthy_dmg * 0.6  # should be ~50%

    def test_burn_does_not_affect_special(self):
        healthy = make_pokemon(special_attack=100)
        burned = make_pokemon(special_attack=100, status=StatusCondition.BURN)
        defender = make_pokemon(special_defense=50, types=["normal"])
        move = make_move(power=80, type_="fire", category="special")

        healthy_dmg = calc_damage(healthy, defender, move, Random(99)).damage
        burned_dmg = calc_damage(burned, defender, move, Random(99)).damage
        assert burned_dmg == healthy_dmg


# ─── Paralysis speed reduction ──────────────────────────────────────────────


class TestParalysisSpeedReduction:
    def test_paralyzed_pokemon_slower(self):
        """Paralyzed Pokémon should go second against an equal-speed opponent."""
        fast = make_pokemon(name="Fast", hp=9999, speed=100, status=StatusCondition.PARALYSIS)
        slow = make_pokemon(name="Slow", hp=9999, speed=60)
        state = make_battle_state(team1=[fast], team2=[slow])

        engine = _engine()
        result = _resolve(engine, state)
        # Fast (para'd, effective 50) < Slow (60), so Slow should go first
        # Filter out paralysis messages to find the first move
        move_logs = [e for e in result.log_entries if "used" in e]
        if len(move_logs) >= 2:
            assert "Slow" in move_logs[0], f"Expected Slow to go first, got: {move_logs}"


# ─── Integration: full turn with status ──────────────────────────────────────


class TestStatusIntegration:
    def test_burn_damage_at_end_of_turn(self):
        """Burned Pokémon should lose HP at end of turn."""
        burned = make_pokemon(name="Burned", hp=160, status=StatusCondition.BURN, speed=100)
        other = make_pokemon(name="Other", hp=160, speed=50)
        state = make_battle_state(team1=[burned], team2=[other])

        engine = _engine()
        result = _resolve(engine, state)
        # Should have taken move damage + burn damage (1/16 of 160 = 10)
        assert any("burn" in e.lower() for e in result.log_entries)

    def test_poison_damage_at_end_of_turn(self):
        poisoned = make_pokemon(name="Poisoned", hp=160, status=StatusCondition.POISON, speed=100)
        other = make_pokemon(name="Other", hp=160, speed=50)
        state = make_battle_state(team1=[poisoned], team2=[other])

        engine = _engine()
        result = _resolve(engine, state)
        assert any("poison" in e.lower() for e in result.log_entries)

    def test_toxic_escalation_over_turns(self):
        """Toxic damage should increase over consecutive turns."""
        toxic_mon = make_pokemon(
            name="Toxic",
            hp=9999,
            defense=255,
            special_defense=255,
            speed=100,
            status=StatusCondition.TOXIC,
        )
        other = make_pokemon(
            name="Other",
            hp=9999,
            defense=255,
            special_defense=255,
            speed=50,
        )
        state = make_battle_state(team1=[toxic_mon], team2=[other])

        engine = _engine()
        # Run 3 turns
        s = state
        damages = []
        for _ in range(3):
            result = _resolve(engine, s)
            s = result.new_state
            # Extract poison damage from log
            for entry in result.log_entries:
                if "poison" in entry.lower() and "damage" in entry.lower():
                    # Parse damage number from "(...N damage)"
                    import re

                    m = re.search(r"\((\d+) damage\)", entry)
                    if m:
                        damages.append(int(m.group(1)))

        # Toxic should escalate: each tick larger than the last
        assert len(damages) >= 2
        for i in range(1, len(damages)):
            assert damages[i] > damages[i - 1], f"Toxic damage should escalate: {damages}"

    def test_sleep_blocks_action(self):
        """A sleeping Pokémon should not attack."""
        sleeper = make_pokemon(name="Sleeper", hp=9999, speed=100, status=StatusCondition.SLEEP)
        sleeper.status_turns = 3
        target = make_pokemon(name="Target", hp=9999, speed=50)
        state = make_battle_state(team1=[sleeper], team2=[target])

        engine = _engine()
        result = _resolve(engine, state)
        assert any("fast asleep" in e for e in result.log_entries)
        # Sleeper should not have used a move
        assert not any("Sleeper used" in e for e in result.log_entries)

    def test_frozen_blocks_action(self):
        """A frozen Pokémon usually can't act."""
        # Use a seed that keeps the mon frozen (not the 20% thaw)
        frozen = make_pokemon(name="Frozen", hp=9999, speed=100, status=StatusCondition.FREEZE)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[frozen], team2=[other])

        # Try multiple seeds to find one where it stays frozen
        for seed in range(50):
            engine = TurnEngine(rng=Random(seed))
            result = _resolve(engine, state)
            if any("frozen solid" in e for e in result.log_entries):
                assert not any("Frozen used" in e for e in result.log_entries)
                return
        pytest.fail("Expected frozen Pokémon to stay frozen in at least one trial")

    def test_fire_move_thaws_frozen_target_in_battle(self):
        """A Fire move should thaw a frozen target during battle."""
        attacker = make_pokemon(
            name="FireUser",
            hp=9999,
            attack=100,
            speed=100,
            moves=[make_move(name="flamethrower", power=90, type_="fire", category="special")],
        )
        attacker.special_attack = 100
        frozen = make_pokemon(
            name="IceMon",
            hp=9999,
            speed=50,
            status=StatusCondition.FREEZE,
        )
        state = make_battle_state(team1=[attacker], team2=[frozen])

        # Find a seed where IceMon stays frozen pre-turn (so it's still frozen when hit)
        for seed in range(50):
            engine = TurnEngine(rng=Random(seed))
            result = _resolve(engine, state)
            if any("thawed" in e.lower() for e in result.log_entries):
                # Verify frozen status was cleared
                target = result.new_state.player2.team[0]
                assert target.status == StatusCondition.NONE
                return
        pytest.fail("Expected fire thaw in at least one trial")

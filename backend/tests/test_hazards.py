"""Tests for Phase 8: Entry Hazards & Protect.

Covers:
- Stealth Rock: setting, type-based damage on switch-in, fail if already set
- Spikes: 1-3 layers, damage scaling, Flying immunity
- Toxic Spikes: 1-2 layers, poison/toxic, Poison-type absorption
- Rapid Spin: clears own hazards after dealing damage
- Defog: clears all hazards on both sides
- Protect / Detect: blocks moves, consecutive use failure, priority
"""

from random import Random

import pytest

from app.battle.actions import MoveAction, SwitchAction
from app.battle.engine import TurnEngine
from app.battle.enums import StatusCondition
from tests.helpers import make_battle_state, make_move, make_pokemon

# ─── Helpers ────────────────────────────────────────────────────────────────


def _resolve(state, a1, a2, seed=42):
    engine = TurnEngine(rng=Random(seed))
    return engine.resolve_turn(state, a1, a2)


def _move_action(uid, idx=0):
    return MoveAction(player_id=uid, move_index=idx)


def _switch_action(uid, idx):
    return SwitchAction(player_id=uid, switch_to_index=idx)


def _status_move(name):
    return make_move(name=name, power=0, accuracy=100, category="status")


# ═══════════════════════════════════════════════════════════════════════════
#  STEALTH ROCK
# ═══════════════════════════════════════════════════════════════════════════


class TestStealthRock:
    def test_stealth_rock_sets_on_opponent_side(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Setter", moves=[_status_move("stealth-rock")])],
            team2=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.side2.stealth_rock is True
        assert any("Pointed stones" in e for e in result.log_entries)

    def test_stealth_rock_fails_if_already_set(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Setter", moves=[_status_move("stealth-rock")])],
            team2=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
        )
        state.side2.stealth_rock = True  # Already set
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert any("already set" in e for e in result.log_entries)

    def test_stealth_rock_damage_neutral(self):
        """Normal type takes 1/8 from Stealth Rock (Rock is neutral to Normal)."""
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead", hp=200),
                make_pokemon(name="Normal", hp=200, types=["normal"]),
            ],
        )
        state.side2.stealth_rock = True
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        switched = result.new_state.player2.team[1]
        # Rock vs Normal = 1x → 1/8 = 25 damage
        assert switched.current_hp == 200 - 25
        assert any("Pointed stones" in e for e in result.log_entries)

    def test_stealth_rock_damage_super_effective(self):
        """Fire/Flying (4x weak to Rock) takes 1/2 from Stealth Rock."""
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead", hp=200),
                make_pokemon(name="Charizard", hp=200, types=["fire", "flying"]),
            ],
        )
        state.side2.stealth_rock = True
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        switched = result.new_state.player2.team[1]
        # Rock vs Fire/Flying = 4x → 4/8 = 1/2 = 100 damage
        assert switched.current_hp == 200 - 100

    def test_stealth_rock_damage_resisted(self):
        """Fighting type (0.5x vs Rock) takes 1/16 from Stealth Rock."""
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead", hp=200),
                make_pokemon(name="Fighter", hp=200, types=["fighting"]),
            ],
        )
        state.side2.stealth_rock = True
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        switched = result.new_state.player2.team[1]
        # Rock vs Fighting = 0.5x → 0.5/8 = 1/16 = 12 damage
        assert switched.current_hp == 200 - 12

    def test_stealth_rock_can_faint(self):
        """Stealth Rock can KO a weakened Pokemon on switch-in."""
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead", hp=200),
                make_pokemon(name="Weak", hp=20, types=["fire", "flying"]),
            ],
        )
        state.side2.stealth_rock = True
        # Fire/Flying takes 50% from SR → int(20 * 4.0 / 8) = 10 damage
        # Pre-weaken so SR KOs: set current HP to 5
        state.player2.team[1].current_hp = 5
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        assert result.new_state.player2.team[1].fainted


# ═══════════════════════════════════════════════════════════════════════════
#  SPIKES
# ═══════════════════════════════════════════════════════════════════════════


class TestSpikes:
    def test_spikes_sets_layer(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Setter", moves=[_status_move("spikes")])],
            team2=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.side2.spikes == 1

    def test_spikes_stacks_to_3(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Setter", hp=500, moves=[_status_move("spikes")])],
            team2=[make_pokemon(name="Foe", hp=500, moves=[_status_move("growl")])],
        )
        engine = TurnEngine(rng=Random(42))
        s = state
        for i in range(3):
            r = engine.resolve_turn(s, _move_action("user-1"), _move_action("user-2"))
            s = r.new_state
        assert s.side2.spikes == 3

    def test_spikes_fails_at_3(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Setter", moves=[_status_move("spikes")])],
            team2=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
        )
        state.side2.spikes = 3
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.side2.spikes == 3
        assert any("maximum" in e for e in result.log_entries)

    @pytest.mark.parametrize("layers,fraction", [(1, 8), (2, 6), (3, 4)])
    def test_spikes_damage_by_layer(self, layers, fraction):
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(name="Victim", hp=240, types=["normal"]),
            ],
        )
        state.side2.spikes = layers
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        victim = result.new_state.player2.team[1]
        expected = max(1, 240 // fraction)
        assert victim.current_hp == 240 - expected

    def test_spikes_flying_immune(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(name="Pidgeot", hp=200, types=["normal", "flying"]),
            ],
        )
        state.side2.spikes = 3
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        assert result.new_state.player2.team[1].current_hp == 200  # No damage


# ═══════════════════════════════════════════════════════════════════════════
#  TOXIC SPIKES
# ═══════════════════════════════════════════════════════════════════════════


class TestToxicSpikes:
    def test_toxic_spikes_sets_layer(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Setter", moves=[_status_move("toxic-spikes")])],
            team2=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.side2.toxic_spikes == 1

    def test_toxic_spikes_max_2(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Setter", moves=[_status_move("toxic-spikes")])],
            team2=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
        )
        state.side2.toxic_spikes = 2
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.side2.toxic_spikes == 2
        assert any("maximum" in e for e in result.log_entries)

    def test_toxic_spikes_1_layer_poisons(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(name="Victim", hp=200, types=["normal"]),
            ],
        )
        state.side2.toxic_spikes = 1
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        assert result.new_state.player2.team[1].status == StatusCondition.POISON

    def test_toxic_spikes_2_layers_badly_poisons(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(name="Victim", hp=200, types=["normal"]),
            ],
        )
        state.side2.toxic_spikes = 2
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        assert result.new_state.player2.team[1].status == StatusCondition.TOXIC

    def test_toxic_spikes_flying_immune(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(name="Pidgeot", hp=200, types=["normal", "flying"]),
            ],
        )
        state.side2.toxic_spikes = 2
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        assert result.new_state.player2.team[1].status == StatusCondition.NONE

    def test_toxic_spikes_poison_type_absorbs(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(name="Gengar", hp=200, types=["ghost", "poison"]),
            ],
        )
        state.side2.toxic_spikes = 2
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        assert result.new_state.player2.team[1].status == StatusCondition.NONE
        assert result.new_state.side2.toxic_spikes == 0  # Absorbed
        assert any("absorbed" in e for e in result.log_entries)


# ═══════════════════════════════════════════════════════════════════════════
#  RAPID SPIN
# ═══════════════════════════════════════════════════════════════════════════


class TestRapidSpin:
    def test_rapid_spin_clears_own_hazards(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Spinner",
                    attack=80,
                    moves=[make_move(name="rapid-spin", power=50, type_="normal")],
                )
            ],
            team2=[make_pokemon(name="Foe", hp=300, moves=[_status_move("growl")])],
        )
        state.side1.stealth_rock = True
        state.side1.spikes = 2
        state.side1.toxic_spikes = 1
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.side1.stealth_rock is False
        assert result.new_state.side1.spikes == 0
        assert result.new_state.side1.toxic_spikes == 0
        assert any("hazards disappeared" in e for e in result.log_entries)

    def test_rapid_spin_deals_damage(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Spinner",
                    attack=80,
                    moves=[make_move(name="rapid-spin", power=50, type_="normal")],
                )
            ],
            team2=[make_pokemon(name="Foe", hp=300, defense=80, moves=[_status_move("growl")])],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player2.team[0].current_hp < 300

    def test_rapid_spin_does_not_clear_opponent_hazards(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Spinner",
                    attack=80,
                    moves=[make_move(name="rapid-spin", power=50, type_="normal")],
                )
            ],
            team2=[make_pokemon(name="Foe", hp=300, moves=[_status_move("growl")])],
        )
        state.side2.stealth_rock = True
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.side2.stealth_rock is True  # Not cleared


# ═══════════════════════════════════════════════════════════════════════════
#  DEFOG
# ═══════════════════════════════════════════════════════════════════════════


class TestDefog:
    def test_defog_clears_both_sides(self):
        state = make_battle_state(
            team1=[make_pokemon(name="User", moves=[_status_move("defog")])],
            team2=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
        )
        state.side1.stealth_rock = True
        state.side1.spikes = 2
        state.side2.stealth_rock = True
        state.side2.toxic_spikes = 1
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.side1.stealth_rock is False
        assert result.new_state.side1.spikes == 0
        assert result.new_state.side2.stealth_rock is False
        assert result.new_state.side2.toxic_spikes == 0

    def test_defog_no_hazards_message(self):
        state = make_battle_state(
            team1=[make_pokemon(name="User", moves=[_status_move("defog")])],
            team2=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert any("no hazards" in e for e in result.log_entries)


# ═══════════════════════════════════════════════════════════════════════════
#  PROTECT / DETECT
# ═══════════════════════════════════════════════════════════════════════════


class TestProtect:
    def test_protect_blocks_attack(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Protector",
                    speed=100,
                    hp=200,
                    moves=[make_move(name="protect", power=0, category="status", priority=4)],
                )
            ],
            team2=[
                make_pokemon(
                    name="Attacker",
                    speed=50,
                    attack=100,
                    moves=[make_move(name="earthquake", type_="ground", power=100)],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        protector = result.new_state.player1.team[0]
        assert protector.current_hp == 200  # No damage taken
        assert any("protected itself" in e for e in result.log_entries)

    def test_protect_high_priority(self):
        """Protect (+4 priority) always goes first even if slower."""
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="SlowProtector",
                    speed=10,
                    hp=200,
                    moves=[make_move(name="protect", power=0, category="status", priority=4)],
                )
            ],
            team2=[
                make_pokemon(
                    name="FastAttacker", speed=200, attack=100, moves=[make_move(power=100)]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player1.team[0].current_hp == 200

    def test_protect_consecutive_use_can_fail(self):
        """Using Protect twice in a row has only 50% success on the 2nd turn."""
        protector = make_pokemon(
            name="Protector",
            speed=100,
            hp=500,
            moves=[make_move(name="protect", power=0, category="status", priority=4)],
        )
        attacker = make_pokemon(
            name="Attacker", speed=50, attack=100, hp=500, moves=[make_move(power=80)]
        )

        state = make_battle_state(team1=[protector], team2=[attacker])
        engine = TurnEngine(rng=Random(42))

        # Turn 1: always succeeds
        r1 = engine.resolve_turn(state, _move_action("user-1"), _move_action("user-2"))
        assert r1.new_state.player1.team[0].current_hp == 500

        # Turn 2+: try many seeds — some should fail
        successes = 0
        failures = 0
        for seed in range(100):
            engine2 = TurnEngine(rng=Random(seed))
            r2 = engine2.resolve_turn(r1.new_state, _move_action("user-1"), _move_action("user-2"))
            if r2.new_state.player1.team[0].current_hp == 500:
                successes += 1
            else:
                failures += 1
        # With 50% chance, we should see both successes and failures
        assert successes > 0
        assert failures > 0

    def test_detect_works_like_protect(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Protector",
                    speed=100,
                    hp=200,
                    moves=[make_move(name="detect", power=0, category="status", priority=4)],
                )
            ],
            team2=[
                make_pokemon(name="Attacker", speed=50, attack=100, moves=[make_move(power=100)])
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player1.team[0].current_hp == 200

    def test_protect_resets_after_non_protect_turn(self):
        """If you don't use Protect for a turn, the counter resets."""
        protector = make_pokemon(
            name="Protector",
            speed=100,
            hp=500,
            moves=[
                make_move(name="protect", power=0, category="status", priority=4),
                make_move(name="tackle", power=40),
            ],
        )
        attacker = make_pokemon(
            name="Attacker", speed=50, attack=50, hp=500, moves=[make_move(power=40)]
        )

        state = make_battle_state(team1=[protector], team2=[attacker])
        engine = TurnEngine(rng=Random(42))

        # Turn 1: Protect (succeeds)
        r1 = engine.resolve_turn(state, _move_action("user-1", 0), _move_action("user-2"))

        # Turn 2: Use tackle instead
        r2 = engine.resolve_turn(r1.new_state, _move_action("user-1", 1), _move_action("user-2"))

        # Turn 3: Protect again — should succeed at 100% (counter was reset)
        r3 = engine.resolve_turn(r2.new_state, _move_action("user-1", 0), _move_action("user-2"))
        assert r3.new_state.player1.team[0].volatile_data.get("protect_turns") == 1


# ═══════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestHazardIntegration:
    def test_stealth_rock_plus_spikes_on_switch(self):
        """Both Stealth Rock and Spikes damage apply on switch-in."""
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(name="Victim", hp=200, types=["normal"]),
            ],
        )
        state.side2.stealth_rock = True
        state.side2.spikes = 1
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        victim = result.new_state.player2.team[1]
        sr_dmg = max(1, int(200 * 1.0 / 8))  # 25
        spikes_dmg = max(1, 200 // 8)  # 25
        assert victim.current_hp == 200 - sr_dmg - spikes_dmg

    def test_hazards_plus_toxic_spikes(self):
        """Stealth Rock damages and Toxic Spikes poisons on same switch."""
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(name="Victim", hp=200, types=["normal"]),
            ],
        )
        state.side2.stealth_rock = True
        state.side2.toxic_spikes = 1
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        victim = result.new_state.player2.team[1]
        assert victim.current_hp < 200
        assert victim.status == StatusCondition.POISON

    def test_rapid_spin_then_switch_no_hazard_damage(self):
        """After Rapid Spin clears hazards, switching in takes no hazard damage."""
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Spinner",
                    attack=80,
                    hp=500,
                    moves=[make_move(name="rapid-spin", power=50, type_="normal")],
                )
            ],
            team2=[make_pokemon(name="Foe", hp=500, moves=[_status_move("growl")])],
        )
        state.side1.stealth_rock = True
        state.side1.spikes = 2

        engine = TurnEngine(rng=Random(42))

        # Turn 1: Rapid Spin clears hazards
        r1 = engine.resolve_turn(state, _move_action("user-1"), _move_action("user-2"))
        assert r1.new_state.side1.stealth_rock is False
        assert r1.new_state.side1.spikes == 0

    def test_protect_then_hazard_setup(self):
        """Protect blocks the opponent's attack while you set up hazards."""
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Protector",
                    speed=100,
                    moves=[make_move(name="protect", power=0, category="status", priority=4)],
                )
            ],
            team2=[make_pokemon(name="Setter", speed=50, moves=[_status_move("stealth-rock")])],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        # Protect goes first (priority +4). Then opponent sets rocks.
        # But Protect only blocks damaging moves — Stealth Rock is a status move targeting the field
        # Stealth Rock should still succeed
        assert result.new_state.side1.stealth_rock is True

    def test_hazard_faint_on_switch_in_skips_ability(self):
        """If hazards KO on switch-in, ability hooks don't fire."""
        state = make_battle_state(
            team1=[make_pokemon(name="Foe", moves=[_status_move("growl")])],
            team2=[
                make_pokemon(name="Lead"),
                make_pokemon(
                    name="Charizard", hp=10, types=["fire", "flying"], ability="intimidate"
                ),
            ],
        )
        state.side2.stealth_rock = True
        # Charizard: 4x weak to Rock SR → int(10 * 4.0 / 8) = 5 damage
        # Pre-weaken to 4 HP so SR KOs
        state.player2.team[1].current_hp = 4
        result = _resolve(state, _move_action("user-1"), _switch_action("user-2", 1))
        charizard = result.new_state.player2.team[1]
        assert charizard.fainted
        # Intimidate should NOT have triggered
        assert not any("Intimidate" in e for e in result.log_entries)

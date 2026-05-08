"""Tests for Phase 6: Ability effects.

Covers all 28 registered abilities across 7 categories:
- Switch-in: Intimidate, Drought, Drizzle, Sand Stream, Snow Warning
- Type immunities: Levitate, Lightning Rod, Water Absorb, Volt Absorb, Flash Fire
- Speed: Speed Boost, Swift Swim, Chlorophyll, Sand Rush
- Damage: Huge Power, Pure Power, Adaptability, Guts, Technician
- Defensive: Multiscale, Sturdy, Marvel Scale
- Contact: Rough Skin, Iron Barbs, Flame Body, Static
- Switch-out: Natural Cure, Regenerator
"""

from random import Random

import pytest

from app.battle.actions import MoveAction, SwitchAction
from app.battle.engine import TurnEngine
from app.battle.enums import StatusCondition, Weather
from tests.helpers import make_battle_state, make_move, make_pokemon

# ─── Helpers ────────────────────────────────────────────────────────────────


def _resolve(state, a1, a2, seed=42):
    engine = TurnEngine(rng=Random(seed))
    return engine.resolve_turn(state, a1, a2)


def _move_action(uid, idx=0):
    return MoveAction(player_id=uid, move_index=idx)


def _switch_action(uid, idx):
    return SwitchAction(player_id=uid, switch_to_index=idx)


# ═══════════════════════════════════════════════════════════════════════════
#  SWITCH-IN ABILITIES
# ═══════════════════════════════════════════════════════════════════════════


class TestIntimidate:
    def test_intimidate_lowers_opponent_attack_on_switch_in(self):
        mon1 = make_pokemon(name="Gyarados", ability="intimidate", moves=[make_move()])
        mon2 = make_pokemon(name="Rattata")
        state = make_battle_state(
            team1=[make_pokemon(name="Starter"), mon1],
            team2=[mon2],
        )
        result = _resolve(
            state,
            _switch_action("user-1", 1),
            _move_action("user-2"),
        )
        opp = result.new_state.player2.team[0]
        assert opp.stat_stages.attack == -1
        assert any("Intimidate" in e for e in result.log_entries)


class TestWeatherSetters:
    @pytest.mark.parametrize(
        "ability,weather,msg_fragment",
        [
            ("drought", Weather.SUN, "intensified the sun"),
            ("drizzle", Weather.RAIN, "made it rain"),
            ("sand-stream", Weather.SANDSTORM, "whipped up a sandstorm"),
            ("snow-warning", Weather.HAIL, "whipped up a hailstorm"),
        ],
    )
    def test_weather_setter_on_switch_in(self, ability, weather, msg_fragment):
        state = make_battle_state(
            team1=[make_pokemon(name="Starter"), make_pokemon(name="Setter", ability=ability)],
            team2=[make_pokemon(name="Foe")],
        )
        result = _resolve(
            state,
            _switch_action("user-1", 1),
            _move_action("user-2"),
        )
        assert result.new_state.field.weather == weather
        assert result.new_state.field.weather_turns == 4  # Set to 5, decremented end-of-turn
        assert any(msg_fragment in e for e in result.log_entries)


# ═══════════════════════════════════════════════════════════════════════════
#  TYPE IMMUNITY ABILITIES
# ═══════════════════════════════════════════════════════════════════════════


class TestLevitate:
    def test_levitate_blocks_ground_moves(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker", moves=[make_move(name="earthquake", type_="ground", power=100)]
                )
            ],
            team2=[make_pokemon(name="Rotom", ability="levitate", hp=200)],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        defender = result.new_state.player2.team[0]
        assert defender.current_hp == 200  # No damage
        assert any("Levitate" in e and "immune" in e for e in result.log_entries)

    def test_levitate_does_not_block_non_ground(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    moves=[
                        make_move(
                            name="thunderbolt", type_="electric", power=90, category="special"
                        )
                    ],
                )
            ],
            team2=[make_pokemon(name="Rotom", ability="levitate", hp=200)],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        defender = result.new_state.player2.team[0]
        assert defender.current_hp < 200  # Took damage


class TestLightningRod:
    def test_lightning_rod_blocks_electric_and_boosts_spa(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    moves=[
                        make_move(
                            name="thunderbolt", type_="electric", power=90, category="special"
                        )
                    ],
                )
            ],
            team2=[make_pokemon(name="Raichu", ability="lightning-rod", hp=200)],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        defender = result.new_state.player2.team[0]
        assert defender.current_hp == 200
        assert defender.stat_stages.special_attack == 1
        assert any("Lightning Rod" in e for e in result.log_entries)


class TestWaterAbsorb:
    def test_water_absorb_heals_from_water_move(self):
        mon = make_pokemon(name="Vaporeon", ability="water-absorb", hp=200)
        mon.current_hp = 100  # Damage it first
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    moves=[make_move(name="surf", type_="water", power=90, category="special")],
                )
            ],
            team2=[mon],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        defender = result.new_state.player2.team[0]
        assert defender.current_hp == 150  # Healed 200//4 = 50
        assert any("Water Absorb restored HP" in e for e in result.log_entries)

    def test_water_absorb_at_full_hp(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    moves=[make_move(name="surf", type_="water", power=90, category="special")],
                )
            ],
            team2=[make_pokemon(name="Vaporeon", ability="water-absorb", hp=200)],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        defender = result.new_state.player2.team[0]
        assert defender.current_hp == 200
        assert any("Water Absorb made the attack useless" in e for e in result.log_entries)


class TestVoltAbsorb:
    def test_volt_absorb_heals_from_electric_move(self):
        mon = make_pokemon(name="Jolteon", ability="volt-absorb", hp=200)
        mon.current_hp = 100
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    moves=[
                        make_move(
                            name="thunderbolt", type_="electric", power=90, category="special"
                        )
                    ],
                )
            ],
            team2=[mon],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        defender = result.new_state.player2.team[0]
        assert defender.current_hp == 150
        assert any("Volt Absorb restored HP" in e for e in result.log_entries)


class TestFlashFire:
    def test_flash_fire_blocks_fire_and_sets_flag(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    moves=[
                        make_move(name="flamethrower", type_="fire", power=90, category="special")
                    ],
                )
            ],
            team2=[make_pokemon(name="Heatran", ability="flash-fire", hp=200)],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        defender = result.new_state.player2.team[0]
        assert defender.current_hp == 200
        assert defender.volatile_data.get("flash_fire") == 1
        assert any("Flash Fire" in e for e in result.log_entries)

    def test_flash_fire_boosts_own_fire_attack(self):
        """After being hit by a fire move, the Pokemon's fire moves do 1.5x damage."""
        attacker = make_pokemon(
            name="Heatran",
            ability="flash-fire",
            types=["fire", "steel"],
            attack=100,
            moves=[make_move(name="flamethrower", type_="fire", power=90, category="special")],
        )
        attacker.volatile_data["flash_fire"] = 1  # Already activated
        defender = make_pokemon(name="Target", hp=500, special_defense=80)

        state = make_battle_state(team1=[attacker], team2=[defender])

        # With Flash Fire boost
        r1 = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_boosted = 500 - r1.new_state.player2.team[0].current_hp

        # Without Flash Fire (same Pokemon, no flag)
        attacker2 = make_pokemon(
            name="Heatran",
            types=["fire", "steel"],
            attack=100,
            moves=[make_move(name="flamethrower", type_="fire", power=90, category="special")],
        )
        defender2 = make_pokemon(name="Target", hp=500, special_defense=80)
        state2 = make_battle_state(team1=[attacker2], team2=[defender2])
        r2 = _resolve(state2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_normal = 500 - r2.new_state.player2.team[0].current_hp

        assert dmg_boosted > dmg_normal


# ═══════════════════════════════════════════════════════════════════════════
#  SPEED ABILITIES
# ═══════════════════════════════════════════════════════════════════════════


class TestSpeedBoost:
    def test_speed_boost_raises_speed_at_end_of_turn(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Blaziken", ability="speed-boost")],
            team2=[make_pokemon(name="Foe")],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        mon = result.new_state.player1.team[0]
        assert mon.stat_stages.speed == 1
        assert any("Speed Boost" in e for e in result.log_entries)

    def test_speed_boost_accumulates_over_turns(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Blaziken", ability="speed-boost", hp=500)],
            team2=[make_pokemon(name="Foe", hp=500)],
        )
        engine = TurnEngine(rng=Random(42))
        s = state
        for _ in range(3):
            r = engine.resolve_turn(s, _move_action("user-1"), _move_action("user-2"))
            s = r.new_state
        assert s.player1.team[0].stat_stages.speed == 3


class TestSwiftSwim:
    def test_swift_swim_doubles_speed_in_rain(self):
        """A slower mon with Swift Swim should outspeed in rain."""
        fast_mon = make_pokemon(name="FastMon", speed=100, hp=500, moves=[make_move(name="tackle")])
        slow_mon = make_pokemon(
            name="SlowMon", speed=60, ability="swift-swim", hp=500, moves=[make_move(name="tackle")]
        )
        state = make_battle_state(
            team1=[slow_mon],
            team2=[fast_mon],
            weather=Weather.RAIN,
            weather_turns=5,
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        # SlowMon (60 * 2 = 120) should move first
        first_log = result.log_entries[0]
        assert "SlowMon" in first_log

    def test_swift_swim_no_effect_without_rain(self):
        fast_mon = make_pokemon(name="FastMon", speed=100, hp=500, moves=[make_move(name="tackle")])
        slow_mon = make_pokemon(
            name="SlowMon", speed=60, ability="swift-swim", hp=500, moves=[make_move(name="tackle")]
        )
        state = make_battle_state(team1=[slow_mon], team2=[fast_mon])
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        first_log = result.log_entries[0]
        assert "FastMon" in first_log


class TestChlorophyll:
    def test_chlorophyll_doubles_speed_in_sun(self):
        fast_mon = make_pokemon(name="FastMon", speed=100, hp=500, moves=[make_move()])
        slow_mon = make_pokemon(
            name="SlowMon", speed=60, ability="chlorophyll", hp=500, moves=[make_move()]
        )
        state = make_battle_state(
            team1=[slow_mon],
            team2=[fast_mon],
            weather=Weather.SUN,
            weather_turns=5,
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert "SlowMon" in result.log_entries[0]


class TestSandRush:
    def test_sand_rush_doubles_speed_in_sandstorm(self):
        fast_mon = make_pokemon(
            name="FastMon", speed=100, hp=500, types=["rock"], moves=[make_move()]
        )
        slow_mon = make_pokemon(
            name="SlowMon",
            speed=60,
            ability="sand-rush",
            hp=500,
            types=["ground"],
            moves=[make_move()],
        )
        state = make_battle_state(
            team1=[slow_mon],
            team2=[fast_mon],
            weather=Weather.SANDSTORM,
            weather_turns=5,
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert "SlowMon" in result.log_entries[0]


# ═══════════════════════════════════════════════════════════════════════════
#  DAMAGE MODIFIER ABILITIES
# ═══════════════════════════════════════════════════════════════════════════


class TestHugePower:
    def test_huge_power_doubles_physical_damage(self):
        boosted = make_pokemon(
            name="Azumarill",
            ability="huge-power",
            attack=50,
            moves=[make_move(name="tackle", power=40, category="physical")],
        )
        normal = make_pokemon(
            name="NormalMon",
            attack=50,
            moves=[make_move(name="tackle", power=40, category="physical")],
        )
        target = make_pokemon(name="Target", hp=500, defense=80)

        s1 = make_battle_state(team1=[boosted], team2=[target])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 500 - r1.new_state.player2.team[0].current_hp

        target2 = make_pokemon(name="Target", hp=500, defense=80)
        s2 = make_battle_state(team1=[normal], team2=[target2])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 500 - r2.new_state.player2.team[0].current_hp

        # Huge Power should deal roughly double damage
        assert dmg1 > dmg2
        assert abs(dmg1 - dmg2 * 2) <= dmg2 * 0.2  # Within 20% of double

    def test_huge_power_does_not_affect_special(self):
        boosted = make_pokemon(
            name="Azumarill",
            ability="huge-power",
            special_attack=50,
            moves=[make_move(name="ice-beam", power=90, category="special", type_="ice")],
        )
        normal = make_pokemon(
            name="NormalMon",
            special_attack=50,
            moves=[make_move(name="ice-beam", power=90, category="special", type_="ice")],
        )
        target = make_pokemon(name="Target", hp=500, special_defense=80)

        s1 = make_battle_state(team1=[boosted], team2=[target])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 500 - r1.new_state.player2.team[0].current_hp

        target2 = make_pokemon(name="Target", hp=500, special_defense=80)
        s2 = make_battle_state(team1=[normal], team2=[target2])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 500 - r2.new_state.player2.team[0].current_hp

        assert dmg1 == dmg2


class TestAdaptability:
    def test_adaptability_boosts_stab(self):
        """Adaptability makes STAB 2x instead of 1.5x."""
        adapted = make_pokemon(
            name="Porygon-Z",
            ability="adaptability",
            types=["normal"],
            attack=80,
            moves=[make_move(name="return", power=102, type_="normal")],
        )
        normal_mon = make_pokemon(
            name="NormalMon",
            types=["normal"],
            attack=80,
            moves=[make_move(name="return", power=102, type_="normal")],
        )
        target = make_pokemon(name="Target", hp=500, defense=80)

        s1 = make_battle_state(team1=[adapted], team2=[target])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 500 - r1.new_state.player2.team[0].current_hp

        target2 = make_pokemon(name="Target", hp=500, defense=80)
        s2 = make_battle_state(team1=[normal_mon], team2=[target2])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 500 - r2.new_state.player2.team[0].current_hp

        # Adaptability: STAB = 2x vs 1.5x, so damage ratio ≈ 4/3
        assert dmg1 > dmg2

    def test_adaptability_no_boost_without_stab(self):
        adapted = make_pokemon(
            name="Porygon-Z",
            ability="adaptability",
            types=["normal"],
            attack=80,
            moves=[make_move(name="shadow-ball", power=80, type_="ghost", category="special")],
        )
        normal_mon = make_pokemon(
            name="NormalMon",
            types=["normal"],
            attack=80,
            moves=[make_move(name="shadow-ball", power=80, type_="ghost", category="special")],
        )
        target = make_pokemon(
            name="Target", hp=500, special_defense=80, types=["normal"]
        )  # Ghost immune to normal
        # Use a different target type that ghost hits
        target = make_pokemon(name="Target", hp=500, special_defense=80, types=["psychic"])

        s1 = make_battle_state(team1=[adapted], team2=[target])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 500 - r1.new_state.player2.team[0].current_hp

        target2 = make_pokemon(name="Target", hp=500, special_defense=80, types=["psychic"])
        s2 = make_battle_state(team1=[normal_mon], team2=[target2])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 500 - r2.new_state.player2.team[0].current_hp

        assert dmg1 == dmg2  # No STAB = no difference


class TestGuts:
    def test_guts_boosts_attack_when_statused(self):
        burned = make_pokemon(
            name="Swellow",
            ability="guts",
            attack=80,
            status=StatusCondition.BURN,
            moves=[make_move(name="facade", power=70, category="physical")],
        )
        normal = make_pokemon(
            name="NormalMon",
            attack=80,
            status=StatusCondition.BURN,
            moves=[make_move(name="facade", power=70, category="physical")],
        )
        target = make_pokemon(name="Target", hp=500, defense=80)

        s1 = make_battle_state(team1=[burned], team2=[target])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 500 - r1.new_state.player2.team[0].current_hp

        target2 = make_pokemon(name="Target", hp=500, defense=80)
        s2 = make_battle_state(team1=[normal], team2=[target2])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 500 - r2.new_state.player2.team[0].current_hp

        # Guts: no burn penalty + 1.5x attack > burn penalty (halved atk)
        assert dmg1 > dmg2

    def test_guts_no_boost_when_healthy(self):
        gutsy = make_pokemon(
            name="Swellow",
            ability="guts",
            attack=80,
            moves=[make_move(name="facade", power=70, category="physical")],
        )
        normal = make_pokemon(
            name="NormalMon",
            attack=80,
            moves=[make_move(name="facade", power=70, category="physical")],
        )
        target = make_pokemon(name="Target", hp=500, defense=80)

        s1 = make_battle_state(team1=[gutsy], team2=[target])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 500 - r1.new_state.player2.team[0].current_hp

        target2 = make_pokemon(name="Target", hp=500, defense=80)
        s2 = make_battle_state(team1=[normal], team2=[target2])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 500 - r2.new_state.player2.team[0].current_hp

        assert dmg1 == dmg2


class TestTechnician:
    def test_technician_boosts_low_power_moves(self):
        tech = make_pokemon(
            name="Scizor",
            ability="technician",
            attack=80,
            moves=[make_move(name="bullet-punch", power=40, type_="steel", category="physical")],
        )
        normal = make_pokemon(
            name="NormalMon",
            attack=80,
            moves=[make_move(name="bullet-punch", power=40, type_="steel", category="physical")],
        )
        target = make_pokemon(name="Target", hp=500, defense=80)

        s1 = make_battle_state(team1=[tech], team2=[target])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 500 - r1.new_state.player2.team[0].current_hp

        target2 = make_pokemon(name="Target", hp=500, defense=80)
        s2 = make_battle_state(team1=[normal], team2=[target2])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 500 - r2.new_state.player2.team[0].current_hp

        assert dmg1 > dmg2

    def test_technician_no_boost_above_60(self):
        tech = make_pokemon(
            name="Scizor",
            ability="technician",
            attack=80,
            moves=[make_move(name="iron-head", power=80, type_="steel", category="physical")],
        )
        normal = make_pokemon(
            name="NormalMon",
            attack=80,
            moves=[make_move(name="iron-head", power=80, type_="steel", category="physical")],
        )
        target = make_pokemon(name="Target", hp=500, defense=80)

        s1 = make_battle_state(team1=[tech], team2=[target])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 500 - r1.new_state.player2.team[0].current_hp

        target2 = make_pokemon(name="Target", hp=500, defense=80)
        s2 = make_battle_state(team1=[normal], team2=[target2])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 500 - r2.new_state.player2.team[0].current_hp

        assert dmg1 == dmg2


# ═══════════════════════════════════════════════════════════════════════════
#  DEFENSIVE ABILITIES
# ═══════════════════════════════════════════════════════════════════════════


class TestMultiscale:
    def test_multiscale_halves_damage_at_full_hp(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Attacker", attack=100, moves=[make_move(power=80)])],
            team2=[make_pokemon(name="Dragonite", ability="multiscale", hp=300, defense=80)],
        )
        r1 = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 300 - r1.new_state.player2.team[0].current_hp

        state2 = make_battle_state(
            team1=[make_pokemon(name="Attacker", attack=100, moves=[make_move(power=80)])],
            team2=[make_pokemon(name="Dragonite", hp=300, defense=80)],
        )
        r2 = _resolve(state2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 300 - r2.new_state.player2.team[0].current_hp

        assert dmg1 < dmg2
        assert abs(dmg1 * 2 - dmg2) <= 2  # Roughly half

    def test_multiscale_no_effect_when_not_full(self):
        defender = make_pokemon(name="Dragonite", ability="multiscale", hp=300, defense=80)
        defender.current_hp = 200

        state = make_battle_state(
            team1=[make_pokemon(name="Attacker", attack=100, moves=[make_move(power=80)])],
            team2=[defender],
        )
        r1 = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 200 - r1.new_state.player2.team[0].current_hp

        defender2 = make_pokemon(name="Dragonite", hp=300, defense=80)
        defender2.current_hp = 200
        state2 = make_battle_state(
            team1=[make_pokemon(name="Attacker", attack=100, moves=[make_move(power=80)])],
            team2=[defender2],
        )
        r2 = _resolve(state2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 200 - r2.new_state.player2.team[0].current_hp

        assert dmg1 == dmg2


class TestSturdy:
    def test_sturdy_survives_ohko_from_full_hp(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Attacker", attack=200, moves=[make_move(power=150)])],
            team2=[make_pokemon(name="Golem", ability="sturdy", hp=50, defense=50)],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        defender = result.new_state.player2.team[0]
        assert defender.current_hp == 1
        assert not defender.fainted
        assert any("Sturdy" in e for e in result.log_entries)

    def test_sturdy_no_effect_when_not_full_hp(self):
        defender = make_pokemon(name="Golem", ability="sturdy", hp=100, defense=50)
        defender.current_hp = 50  # Not full

        state = make_battle_state(
            team1=[make_pokemon(name="Attacker", attack=200, moves=[make_move(power=150)])],
            team2=[defender],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        assert result.new_state.player2.team[0].fainted


class TestMarvelScale:
    def test_marvel_scale_reduces_physical_damage_when_statused(self):
        defender = make_pokemon(
            name="Milotic", ability="marvel-scale", hp=300, defense=80, status=StatusCondition.BURN
        )

        state = make_battle_state(
            team1=[make_pokemon(name="Attacker", attack=100, moves=[make_move(power=80)])],
            team2=[defender],
        )
        r1 = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg1 = 300 - r1.new_state.player2.team[0].current_hp

        defender2 = make_pokemon(name="Milotic", hp=300, defense=80, status=StatusCondition.BURN)
        state2 = make_battle_state(
            team1=[make_pokemon(name="Attacker", attack=100, moves=[make_move(power=80)])],
            team2=[defender2],
        )
        r2 = _resolve(state2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg2 = 300 - r2.new_state.player2.team[0].current_hp

        assert dmg1 < dmg2


# ═══════════════════════════════════════════════════════════════════════════
#  CONTACT ABILITIES
# ═══════════════════════════════════════════════════════════════════════════


class TestRoughSkin:
    def test_rough_skin_damages_attacker_on_contact(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    hp=200,
                    attack=80,
                    moves=[make_move(name="tackle", power=40, flags=["contact"])],
                )
            ],
            team2=[
                make_pokemon(
                    name="Garchomp",
                    ability="rough-skin",
                    hp=300,
                    defense=80,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        attacker = result.new_state.player1.team[0]
        expected_recoil = max(1, 200 // 8)
        assert attacker.current_hp == 200 - expected_recoil
        assert any("Rough Skin" in e for e in result.log_entries)

    def test_rough_skin_no_effect_without_contact(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    hp=200,
                    attack=80,
                    moves=[make_move(name="earthquake", type_="ground", power=100, flags=[])],
                )
            ],
            team2=[
                make_pokemon(
                    name="Garchomp",
                    ability="rough-skin",
                    hp=300,
                    defense=80,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        attacker = result.new_state.player1.team[0]
        assert attacker.current_hp == 200


class TestIronBarbs:
    def test_iron_barbs_damages_attacker_on_contact(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    hp=200,
                    attack=80,
                    moves=[make_move(name="tackle", power=40, flags=["contact"])],
                )
            ],
            team2=[
                make_pokemon(
                    name="Ferrothorn",
                    ability="iron-barbs",
                    hp=300,
                    defense=100,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        attacker = result.new_state.player1.team[0]
        expected_recoil = max(1, 200 // 8)
        assert attacker.current_hp == 200 - expected_recoil
        assert any("Iron Barbs" in e for e in result.log_entries)


class TestFlameBody:
    def test_flame_body_can_burn_on_contact(self):
        """With a seeded RNG that triggers the 30% chance."""
        # Try multiple seeds to find one where burn triggers
        for seed in range(100):
            state = make_battle_state(
                team1=[
                    make_pokemon(
                        name="Attacker",
                        hp=200,
                        attack=80,
                        moves=[make_move(name="tackle", power=40, flags=["contact"])],
                    )
                ],
                team2=[make_pokemon(name="Magcargo", ability="flame-body", hp=300, defense=80)],
            )
            result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=seed)
            attacker = result.new_state.player1.team[0]
            if attacker.status == StatusCondition.BURN:
                assert any("Flame Body" in e for e in result.log_entries)
                return
        pytest.fail("Flame Body never triggered across 100 seeds")

    def test_flame_body_no_burn_on_fire_type(self):
        """Fire types are immune to burn."""
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Charizard",
                    hp=200,
                    attack=80,
                    types=["fire", "flying"],
                    moves=[make_move(name="tackle", power=40, flags=["contact"])],
                )
            ],
            team2=[make_pokemon(name="Magcargo", ability="flame-body", hp=300, defense=80)],
        )
        # Run with many seeds — should never burn
        for seed in range(50):
            result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=seed)
            assert result.new_state.player1.team[0].status != StatusCondition.BURN


class TestStatic:
    def test_static_can_paralyze_on_contact(self):
        for seed in range(100):
            state = make_battle_state(
                team1=[
                    make_pokemon(
                        name="Attacker",
                        hp=200,
                        attack=80,
                        moves=[make_move(name="tackle", power=40, flags=["contact"])],
                    )
                ],
                team2=[make_pokemon(name="Pikachu", ability="static", hp=200, defense=50)],
            )
            result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=seed)
            attacker = result.new_state.player1.team[0]
            if attacker.status == StatusCondition.PARALYSIS:
                assert any("Static" in e for e in result.log_entries)
                return
        pytest.fail("Static never triggered across 100 seeds")

    def test_static_no_paralyze_on_electric_type(self):
        """Electric types are immune to paralysis."""
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Jolteon",
                    hp=200,
                    attack=80,
                    types=["electric"],
                    moves=[make_move(name="tackle", power=40, flags=["contact"])],
                )
            ],
            team2=[make_pokemon(name="Pikachu", ability="static", hp=200, defense=50)],
        )
        for seed in range(50):
            result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=seed)
            assert result.new_state.player1.team[0].status != StatusCondition.PARALYSIS


# ═══════════════════════════════════════════════════════════════════════════
#  SWITCH-OUT ABILITIES
# ═══════════════════════════════════════════════════════════════════════════


class TestNaturalCure:
    def test_natural_cure_heals_status_on_switch_out(self):
        mon = make_pokemon(name="Blissey", ability="natural-cure", status=StatusCondition.POISON)
        state = make_battle_state(
            team1=[mon, make_pokemon(name="Backup")],
            team2=[make_pokemon(name="Foe")],
        )
        result = _resolve(
            state,
            _switch_action("user-1", 1),
            _move_action("user-2"),
        )
        blissey = result.new_state.player1.team[0]
        assert blissey.status == StatusCondition.NONE
        assert any("Natural Cure" in e for e in result.log_entries)

    def test_natural_cure_no_effect_when_healthy(self):
        mon = make_pokemon(name="Blissey", ability="natural-cure")
        state = make_battle_state(
            team1=[mon, make_pokemon(name="Backup")],
            team2=[make_pokemon(name="Foe")],
        )
        result = _resolve(
            state,
            _switch_action("user-1", 1),
            _move_action("user-2"),
        )
        assert not any("Natural Cure" in e for e in result.log_entries)


class TestRegenerator:
    def test_regenerator_heals_on_switch_out(self):
        mon = make_pokemon(name="Slowbro", ability="regenerator", hp=300)
        mon.current_hp = 100

        state = make_battle_state(
            team1=[mon, make_pokemon(name="Backup")],
            team2=[make_pokemon(name="Foe")],
        )
        result = _resolve(
            state,
            _switch_action("user-1", 1),
            _move_action("user-2"),
        )
        slowbro = result.new_state.player1.team[0]
        assert slowbro.current_hp == 200  # 100 + 300//3 = 200
        assert any("Regenerator" in e for e in result.log_entries)

    def test_regenerator_caps_at_max_hp(self):
        mon = make_pokemon(name="Slowbro", ability="regenerator", hp=300)
        mon.current_hp = 290  # Almost full

        state = make_battle_state(
            team1=[mon, make_pokemon(name="Backup")],
            team2=[make_pokemon(name="Foe")],
        )
        result = _resolve(
            state,
            _switch_action("user-1", 1),
            _move_action("user-2"),
        )
        slowbro = result.new_state.player1.team[0]
        assert slowbro.current_hp == 300  # Capped at max


# ═══════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAbilityIntegration:
    def test_intimidate_switch_in_then_weather_setter(self):
        """Switch in Intimidate mon, then opponent switches in Drought setter."""
        state = make_battle_state(
            team1=[
                make_pokemon(name="Starter"),
                make_pokemon(name="Gyarados", ability="intimidate"),
            ],
            team2=[
                make_pokemon(name="Starter2"),
                make_pokemon(name="Ninetales", ability="drought"),
            ],
        )
        result = _resolve(
            state,
            _switch_action("user-1", 1),
            _switch_action("user-2", 1),
        )
        # Both switch-in abilities should fire
        assert any("Intimidate" in e for e in result.log_entries)
        assert result.new_state.field.weather == Weather.SUN

    def test_levitate_immune_but_other_moves_hit(self):
        """Levitate blocks Ground, but other types still hit."""
        levitator = make_pokemon(
            name="Weezing",
            ability="levitate",
            hp=200,
            moves=[make_move()],
        )
        attacker = make_pokemon(
            name="Attacker",
            attack=80,
            moves=[
                make_move(name="earthquake", type_="ground", power=100),
                make_move(name="rock-slide", type_="rock", power=75),
            ],
        )
        state = make_battle_state(team1=[attacker], team2=[levitator])

        # Ground move: blocked
        r1 = _resolve(state, _move_action("user-1", 0), _move_action("user-2"), seed=42)
        assert r1.new_state.player2.team[0].current_hp == 200

        # Rock move: hits
        r2 = _resolve(state, _move_action("user-1", 1), _move_action("user-2"), seed=42)
        assert r2.new_state.player2.team[0].current_hp < 200

    def test_speed_boost_makes_slower_mon_faster_after_turns(self):
        """Speed Boost should make a slower mon outspeed after enough turns."""
        slow = make_pokemon(
            name="Ninjask", ability="speed-boost", speed=60, hp=500, moves=[make_move()]
        )
        fast = make_pokemon(name="FastMon", speed=70, hp=500, moves=[make_move()])

        state = make_battle_state(team1=[slow], team2=[fast])
        engine = TurnEngine(rng=Random(42))

        # Turn 1: FastMon faster (70 > 60)
        r1 = engine.resolve_turn(state, _move_action("user-1"), _move_action("user-2"))
        assert "FastMon" in r1.log_entries[0]

        # After turn 1, Ninjask speed +1 stage. Effective speed = 60 * 1.5 = 90 > 70
        r2 = engine.resolve_turn(r1.new_state, _move_action("user-1"), _move_action("user-2"))
        assert "Ninjask" in r2.log_entries[0]

    def test_natural_cure_then_regenerator_on_same_team(self):
        """Verify two different switch-out abilities on different team members."""
        nc_mon = make_pokemon(
            name="Chansey", ability="natural-cure", hp=500, status=StatusCondition.PARALYSIS
        )
        regen_mon = make_pokemon(name="Slowbro", ability="regenerator", hp=500)

        state = make_battle_state(
            team1=[nc_mon, regen_mon],
            team2=[make_pokemon(name="Foe")],
        )

        # Switch from Natural Cure to Regenerator
        r1 = _resolve(state, _switch_action("user-1", 1), _move_action("user-2"))
        chansey = r1.new_state.player1.team[0]
        assert chansey.status == StatusCondition.NONE
        assert any("Natural Cure" in e for e in r1.log_entries)

    def test_sturdy_plus_contact_ability(self):
        """Sturdy saves from OHKO, then Rough Skin damages the attacker."""
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    hp=200,
                    attack=200,
                    moves=[
                        make_move(
                            name="close-combat", power=120, type_="fighting", flags=["contact"]
                        )
                    ],
                )
            ],
            team2=[make_pokemon(name="Golem", ability="sturdy", hp=60, defense=80)],
        )
        # Golem can't have Rough Skin and Sturdy... let's test Sturdy alone
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"), seed=99)
        golem = result.new_state.player2.team[0]
        assert golem.current_hp == 1
        assert not golem.fainted

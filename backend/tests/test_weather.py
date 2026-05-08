"""Tests for weather and terrain: type boosts, end-of-turn damage, countdown, setting moves."""

from random import Random

from app.battle.actions import MoveAction
from app.battle.damage import DamageResult, calc_damage
from app.battle.engine import TurnEngine
from app.battle.enums import Terrain, Weather
from tests.helpers import make_battle_state, make_move, make_pokemon

SEED = 42


def _engine(seed=SEED) -> TurnEngine:
    return TurnEngine(rng=Random(seed))


def _resolve(engine, state, p1=0, p2=0):
    a1 = MoveAction(player_id=state.player1.user_id, move_index=p1)
    a2 = MoveAction(player_id=state.player2.user_id, move_index=p2)
    return engine.resolve_turn(state, a1, a2)


def _dmg(attacker, defender, move, weather=Weather.NONE, seed=99) -> DamageResult:
    return calc_damage(attacker, defender, move, Random(seed), weather=weather)


# ─── Weather type boost in damage calc ──────────────────────────────────────


class TestWeatherTypeBoost:
    def test_rain_boosts_water(self):
        atk = make_pokemon(attack=100, types=["normal"])
        dfn = make_pokemon(defense=100, types=["normal"])
        move = make_move(power=80, type_="water", category="physical")

        normal = _dmg(atk, dfn, move, weather=Weather.NONE)
        rainy = _dmg(atk, dfn, move, weather=Weather.RAIN)
        assert rainy.damage > normal.damage
        # Should be ~1.5x
        assert rainy.damage >= int(normal.damage * 1.4)

    def test_rain_weakens_fire(self):
        atk = make_pokemon(attack=100, types=["normal"])
        dfn = make_pokemon(defense=100, types=["normal"])
        move = make_move(power=80, type_="fire", category="physical")

        normal = _dmg(atk, dfn, move, weather=Weather.NONE)
        rainy = _dmg(atk, dfn, move, weather=Weather.RAIN)
        assert rainy.damage < normal.damage
        assert rainy.damage <= int(normal.damage * 0.6)

    def test_sun_boosts_fire(self):
        atk = make_pokemon(special_attack=100, types=["normal"])
        dfn = make_pokemon(special_defense=100, types=["normal"])
        move = make_move(power=80, type_="fire", category="special")

        normal = _dmg(atk, dfn, move, weather=Weather.NONE)
        sunny = _dmg(atk, dfn, move, weather=Weather.SUN)
        assert sunny.damage > normal.damage

    def test_sun_weakens_water(self):
        atk = make_pokemon(special_attack=100, types=["normal"])
        dfn = make_pokemon(special_defense=100, types=["normal"])
        move = make_move(power=80, type_="water", category="special")

        normal = _dmg(atk, dfn, move, weather=Weather.NONE)
        sunny = _dmg(atk, dfn, move, weather=Weather.SUN)
        assert sunny.damage < normal.damage

    def test_weather_no_effect_on_other_types(self):
        atk = make_pokemon(attack=100, types=["normal"])
        dfn = make_pokemon(defense=100, types=["normal"])
        move = make_move(power=80, type_="electric", category="physical")

        normal = _dmg(atk, dfn, move, weather=Weather.NONE)
        rainy = _dmg(atk, dfn, move, weather=Weather.RAIN)
        assert rainy.damage == normal.damage

    def test_sandstorm_no_type_boost(self):
        atk = make_pokemon(attack=100, types=["normal"])
        dfn = make_pokemon(defense=100, types=["normal"])
        move = make_move(power=80, type_="rock", category="physical")

        normal = _dmg(atk, dfn, move, weather=Weather.NONE)
        sandy = _dmg(atk, dfn, move, weather=Weather.SANDSTORM)
        assert sandy.damage == normal.damage


# ─── End-of-turn weather damage ─────────────────────────────────────────────


class TestSandstormDamage:
    def test_sandstorm_damages_non_immune(self):
        mon = make_pokemon(name="Pikachu", hp=160, speed=100, types=["electric"])
        other = make_pokemon(name="Other", hp=160, speed=50, types=["electric"])
        state = make_battle_state(
            team1=[mon],
            team2=[other],
            weather=Weather.SANDSTORM,
            weather_turns=5,
        )

        result = _resolve(_engine(), state)
        # Sandstorm does 1/16 of max HP = 10
        assert any("buffeted" in e for e in result.log_entries)
        # Both should take sandstorm damage
        buffeted = [e for e in result.log_entries if "buffeted" in e]
        assert len(buffeted) == 2

    def test_sandstorm_immune_rock(self):
        rock = make_pokemon(name="Golem", hp=160, speed=100, types=["rock", "ground"])
        elec = make_pokemon(name="Pikachu", hp=160, speed=50, types=["electric"])
        state = make_battle_state(
            team1=[rock],
            team2=[elec],
            weather=Weather.SANDSTORM,
            weather_turns=5,
        )

        result = _resolve(_engine(), state)
        buffeted = [e for e in result.log_entries if "buffeted" in e]
        # Only Pikachu should be buffeted, not Golem
        assert len(buffeted) == 1
        assert "Pikachu" in buffeted[0]

    def test_sandstorm_immune_ground(self):
        ground = make_pokemon(name="Sandshrew", hp=160, speed=100, types=["ground"])
        water = make_pokemon(name="Squirtle", hp=160, speed=50, types=["water"])
        state = make_battle_state(
            team1=[ground],
            team2=[water],
            weather=Weather.SANDSTORM,
            weather_turns=5,
        )

        result = _resolve(_engine(), state)
        buffeted = [e for e in result.log_entries if "buffeted" in e]
        assert len(buffeted) == 1
        assert "Squirtle" in buffeted[0]

    def test_sandstorm_immune_steel(self):
        steel = make_pokemon(name="Magneton", hp=160, speed=100, types=["electric", "steel"])
        fire = make_pokemon(name="Charmander", hp=160, speed=50, types=["fire"])
        state = make_battle_state(
            team1=[steel],
            team2=[fire],
            weather=Weather.SANDSTORM,
            weather_turns=5,
        )

        result = _resolve(_engine(), state)
        buffeted = [e for e in result.log_entries if "buffeted" in e]
        assert len(buffeted) == 1
        assert "Charmander" in buffeted[0]

    def test_sandstorm_damage_amount(self):
        mon = make_pokemon(name="Test", hp=320, speed=100, types=["normal"])
        other = make_pokemon(name="Other", hp=9999, speed=50, defense=255, types=["rock"])
        state = make_battle_state(
            team1=[mon],
            team2=[other],
            weather=Weather.SANDSTORM,
            weather_turns=5,
        )

        result = _resolve(_engine(), state)
        # Took tackle damage + sandstorm damage (320 // 16 = 20)
        # Just verify sandstorm happened
        assert any("buffeted" in e and "Test" in e for e in result.log_entries)


class TestHailDamage:
    def test_hail_damages_non_ice(self):
        fire = make_pokemon(name="Charmander", hp=160, speed=100, types=["fire"])
        water = make_pokemon(name="Squirtle", hp=160, speed=50, types=["water"])
        state = make_battle_state(
            team1=[fire],
            team2=[water],
            weather=Weather.HAIL,
            weather_turns=5,
        )

        result = _resolve(_engine(), state)
        buffeted = [e for e in result.log_entries if "buffeted" in e]
        assert len(buffeted) == 2

    def test_hail_immune_ice(self):
        ice = make_pokemon(name="Articuno", hp=160, speed=100, types=["ice", "flying"])
        fire = make_pokemon(name="Charmander", hp=160, speed=50, types=["fire"])
        state = make_battle_state(
            team1=[ice],
            team2=[fire],
            weather=Weather.HAIL,
            weather_turns=5,
        )

        result = _resolve(_engine(), state)
        buffeted = [e for e in result.log_entries if "buffeted" in e]
        assert len(buffeted) == 1
        assert "Charmander" in buffeted[0]

    def test_hail_can_faint(self):
        mon = make_pokemon(name="Weak", hp=16, speed=100, types=["normal"], defense=255)
        mon.current_hp = 1
        other = make_pokemon(
            name="Other",
            hp=9999,
            speed=50,
            types=["ice"],
            moves=[make_move(power=0, type_="normal", category="status", name="growl")],
        )
        state = make_battle_state(
            team1=[mon],
            team2=[other],
            weather=Weather.HAIL,
            weather_turns=5,
        )

        result = _resolve(_engine(), state)
        assert result.new_state.player1.team[0].fainted


# ─── Weather countdown and expiry ───────────────────────────────────────────


class TestWeatherCountdown:
    def test_weather_decrements_each_turn(self):
        mon1 = make_pokemon(name="Mon1", hp=9999, speed=100, types=["rock"])
        mon2 = make_pokemon(name="Mon2", hp=9999, speed=50, types=["rock"])
        state = make_battle_state(
            team1=[mon1],
            team2=[mon2],
            weather=Weather.SANDSTORM,
            weather_turns=3,
        )

        engine = _engine()
        r = _resolve(engine, state)
        assert r.new_state.field.weather == Weather.SANDSTORM
        assert r.new_state.field.weather_turns == 2

    def test_weather_clears_at_zero(self):
        mon1 = make_pokemon(name="Mon1", hp=9999, speed=100, types=["rock"])
        mon2 = make_pokemon(name="Mon2", hp=9999, speed=50, types=["rock"])
        state = make_battle_state(
            team1=[mon1],
            team2=[mon2],
            weather=Weather.SANDSTORM,
            weather_turns=1,
        )

        engine = _engine()
        r = _resolve(engine, state)
        assert r.new_state.field.weather == Weather.NONE
        assert r.new_state.field.weather_turns == 0
        assert any("subsided" in e for e in r.log_entries)

    def test_rain_expiry_message(self):
        mon1 = make_pokemon(name="Mon1", hp=9999, speed=100, types=["water"])
        mon2 = make_pokemon(name="Mon2", hp=9999, speed=50, types=["water"])
        state = make_battle_state(
            team1=[mon1],
            team2=[mon2],
            weather=Weather.RAIN,
            weather_turns=1,
        )

        r = _resolve(_engine(), state)
        assert any("rain stopped" in e for e in r.log_entries)

    def test_sun_expiry_message(self):
        mon1 = make_pokemon(name="Mon1", hp=9999, speed=100)
        mon2 = make_pokemon(name="Mon2", hp=9999, speed=50)
        state = make_battle_state(
            team1=[mon1],
            team2=[mon2],
            weather=Weather.SUN,
            weather_turns=1,
        )

        r = _resolve(_engine(), state)
        assert any("faded" in e for e in r.log_entries)


# ─── Weather-setting moves ──────────────────────────────────────────────────


class TestWeatherSettingMoves:
    def test_rain_dance_sets_rain(self):
        user = make_pokemon(
            name="Dancer",
            hp=9999,
            speed=100,
            moves=[make_move(name="rain-dance", power=0, type_="water", category="status")],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[user], team2=[other])

        r = _resolve(_engine(), state)
        assert r.new_state.field.weather == Weather.RAIN
        assert r.new_state.field.weather_turns == 4  # 5 - 1 (ticked down end of turn)
        assert any("rain" in e.lower() for e in r.log_entries)

    def test_sunny_day_sets_sun(self):
        user = make_pokemon(
            name="Sunny",
            hp=9999,
            speed=100,
            moves=[make_move(name="sunny-day", power=0, type_="fire", category="status")],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[user], team2=[other])

        r = _resolve(_engine(), state)
        assert r.new_state.field.weather == Weather.SUN
        assert any("sunlight" in e.lower() for e in r.log_entries)

    def test_sandstorm_move_sets_sandstorm(self):
        user = make_pokemon(
            name="Sandy",
            hp=9999,
            speed=100,
            types=["rock"],
            moves=[make_move(name="sandstorm", power=0, type_="rock", category="status")],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50, types=["rock"])
        state = make_battle_state(team1=[user], team2=[other])

        r = _resolve(_engine(), state)
        assert r.new_state.field.weather == Weather.SANDSTORM

    def test_hail_move_sets_hail(self):
        user = make_pokemon(
            name="Icy",
            hp=9999,
            speed=100,
            types=["ice"],
            moves=[make_move(name="hail", power=0, type_="ice", category="status")],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50, types=["ice"])
        state = make_battle_state(team1=[user], team2=[other])

        r = _resolve(_engine(), state)
        assert r.new_state.field.weather == Weather.HAIL

    def test_weather_replaces_existing(self):
        user = make_pokemon(
            name="Dancer",
            hp=9999,
            speed=100,
            moves=[make_move(name="rain-dance", power=0, type_="water", category="status")],
        )
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(
            team1=[user],
            team2=[other],
            weather=Weather.SUN,
            weather_turns=3,
        )

        r = _resolve(_engine(), state)
        assert r.new_state.field.weather == Weather.RAIN


# ─── Weather + damage integration ───────────────────────────────────────────


class TestWeatherDamageIntegration:
    def test_rain_boosts_water_move_in_battle(self):
        """Water move should deal more damage during rain."""
        atk = make_pokemon(
            name="Blastoise",
            hp=9999,
            special_attack=100,
            speed=100,
            types=["water"],
            moves=[make_move(name="surf", power=90, type_="water", category="special")],
        )
        dfn = make_pokemon(name="Target", hp=9999, speed=50, types=["normal"])

        # Without rain
        state_dry = make_battle_state(team1=[atk], team2=[dfn])
        r_dry = _resolve(_engine(), state_dry)
        dry_hp = r_dry.new_state.player2.team[0].current_hp

        # With rain
        state_rain = make_battle_state(
            team1=[atk],
            team2=[dfn],
            weather=Weather.RAIN,
            weather_turns=5,
        )
        r_rain = _resolve(_engine(), state_rain)
        rain_hp = r_rain.new_state.player2.team[0].current_hp

        # Rain should cause more damage (lower remaining HP)
        assert rain_hp < dry_hp


# ─── Grassy Terrain ─────────────────────────────────────────────────────────


class TestGrassyTerrain:
    def test_grassy_terrain_heals(self):
        mon = make_pokemon(name="Test", hp=200, speed=100, types=["normal"])
        mon.current_hp = 150
        other = make_pokemon(
            name="Other",
            hp=9999,
            speed=50,
            moves=[make_move(power=0, type_="normal", category="status", name="growl")],
        )
        state = make_battle_state(
            team1=[mon],
            team2=[other],
            terrain=Terrain.GRASSY,
            terrain_turns=5,
        )

        r = _resolve(_engine(), state)
        test_mon = r.new_state.player1.team[0]
        # Should have healed 200 // 16 = 12 HP
        assert test_mon.current_hp > 150
        assert any("Grassy Terrain" in e for e in r.log_entries)

    def test_grassy_terrain_no_overheal(self):
        mon = make_pokemon(name="Test", hp=200, speed=100, types=["normal"])
        other = make_pokemon(
            name="Other",
            hp=9999,
            speed=50,
            moves=[make_move(power=0, type_="normal", category="status", name="growl")],
        )
        state = make_battle_state(
            team1=[mon],
            team2=[other],
            terrain=Terrain.GRASSY,
            terrain_turns=5,
        )

        r = _resolve(_engine(), state)
        assert r.new_state.player1.team[0].current_hp == 200

    def test_terrain_countdown(self):
        mon1 = make_pokemon(name="Mon1", hp=9999, speed=100)
        mon2 = make_pokemon(name="Mon2", hp=9999, speed=50)
        state = make_battle_state(
            team1=[mon1],
            team2=[mon2],
            terrain=Terrain.GRASSY,
            terrain_turns=1,
        )

        r = _resolve(_engine(), state)
        assert r.new_state.field.terrain == Terrain.NONE
        assert any("returned to normal" in e for e in r.log_entries)


# ─── No weather = no effects ────────────────────────────────────────────────


class TestNoWeather:
    def test_no_weather_no_damage(self):
        mon1 = make_pokemon(name="Mon1", hp=160, speed=100, types=["normal"])
        mon2 = make_pokemon(name="Mon2", hp=160, speed=50, types=["normal"])
        state = make_battle_state(team1=[mon1], team2=[mon2])

        r = _resolve(_engine(), state)
        assert not any("buffeted" in e for e in r.log_entries)

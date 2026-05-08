"""Tests for Phase 7: Held item effects.

Covers all 12 registered items:
- Choice Band, Choice Specs, Choice Scarf
- Leftovers, Black Sludge
- Life Orb
- Focus Sash
- Rocky Helmet
- Assault Vest
- Sitrus Berry, Lum Berry
- Eviolite
"""

from random import Random

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


def _compare_damage(item_holder, no_item, target_hp=500, target_def=80, seed=99):
    """Run two battles and return (damage_with_item, damage_without_item)."""
    t1 = make_pokemon(
        name="Target",
        hp=target_hp,
        defense=target_def,
        special_defense=target_def,
        moves=[make_move(name="growl", power=0, category="status")],
    )
    t2 = make_pokemon(
        name="Target",
        hp=target_hp,
        defense=target_def,
        special_defense=target_def,
        moves=[make_move(name="growl", power=0, category="status")],
    )

    s1 = make_battle_state(team1=[item_holder], team2=[t1])
    r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=seed)
    dmg1 = target_hp - r1.new_state.player2.team[0].current_hp

    s2 = make_battle_state(team1=[no_item], team2=[t2])
    r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=seed)
    dmg2 = target_hp - r2.new_state.player2.team[0].current_hp

    return dmg1, dmg2


# ═══════════════════════════════════════════════════════════════════════════
#  CHOICE ITEMS
# ═══════════════════════════════════════════════════════════════════════════


class TestChoiceBand:
    def test_choice_band_boosts_physical_damage(self):
        banded = make_pokemon(
            name="Attacker",
            item="choice-band",
            attack=100,
            moves=[make_move(power=80, category="physical")],
        )
        normal = make_pokemon(
            name="Attacker", attack=100, moves=[make_move(power=80, category="physical")]
        )
        dmg_band, dmg_norm = _compare_damage(banded, normal)
        assert dmg_band > dmg_norm

    def test_choice_band_no_boost_on_special(self):
        banded = make_pokemon(
            name="Attacker",
            item="choice-band",
            special_attack=100,
            moves=[make_move(power=80, category="special", type_="fire")],
        )
        normal = make_pokemon(
            name="Attacker",
            special_attack=100,
            moves=[make_move(power=80, category="special", type_="fire")],
        )
        dmg_band, dmg_norm = _compare_damage(banded, normal)
        assert dmg_band == dmg_norm


class TestChoiceSpecs:
    def test_choice_specs_boosts_special_damage(self):
        specced = make_pokemon(
            name="Attacker",
            item="choice-specs",
            special_attack=100,
            moves=[make_move(power=80, category="special", type_="fire")],
        )
        normal = make_pokemon(
            name="Attacker",
            special_attack=100,
            moves=[make_move(power=80, category="special", type_="fire")],
        )
        dmg_spec, dmg_norm = _compare_damage(specced, normal)
        assert dmg_spec > dmg_norm

    def test_choice_specs_no_boost_on_physical(self):
        specced = make_pokemon(
            name="Attacker",
            item="choice-specs",
            attack=100,
            moves=[make_move(power=80, category="physical")],
        )
        normal = make_pokemon(
            name="Attacker", attack=100, moves=[make_move(power=80, category="physical")]
        )
        dmg_spec, dmg_norm = _compare_damage(specced, normal)
        assert dmg_spec == dmg_norm


class TestChoiceScarf:
    def test_choice_scarf_outspeeds(self):
        """A slower mon with Choice Scarf should outspeed a faster mon."""
        slow = make_pokemon(
            name="SlowMon", speed=70, item="choice-scarf", hp=500, moves=[make_move()]
        )
        fast = make_pokemon(name="FastMon", speed=100, hp=500, moves=[make_move()])
        state = make_battle_state(team1=[slow], team2=[fast])
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        # 70 * 1.5 = 105 > 100
        assert "SlowMon" in result.log_entries[0]

    def test_no_scarf_is_slower(self):
        slow = make_pokemon(name="SlowMon", speed=70, hp=500, moves=[make_move()])
        fast = make_pokemon(name="FastMon", speed=100, hp=500, moves=[make_move()])
        state = make_battle_state(team1=[slow], team2=[fast])
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert "FastMon" in result.log_entries[0]


# ═══════════════════════════════════════════════════════════════════════════
#  LEFTOVERS / BLACK SLUDGE
# ═══════════════════════════════════════════════════════════════════════════


class TestLeftovers:
    def test_leftovers_heals_end_of_turn(self):
        mon = make_pokemon(name="Tank", item="leftovers", hp=160)
        mon.current_hp = 100
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        tank = result.new_state.player1.team[0]
        assert tank.current_hp == 110  # 100 + 160//16 = 110
        assert any("Leftovers" in e for e in result.log_entries)

    def test_leftovers_caps_at_max(self):
        mon = make_pokemon(name="Tank", item="leftovers", hp=160)
        mon.current_hp = 155
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player1.team[0].current_hp == 160


class TestBlackSludge:
    def test_black_sludge_heals_poison_types(self):
        mon = make_pokemon(name="Gengar", item="black-sludge", hp=160, types=["ghost", "poison"])
        mon.current_hp = 100
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player1.team[0].current_hp == 110
        assert any("Black Sludge" in e and "restored" in e for e in result.log_entries)

    def test_black_sludge_hurts_non_poison_types(self):
        mon = make_pokemon(name="Pikachu", item="black-sludge", hp=160, types=["electric"])
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        pika = result.new_state.player1.team[0]
        assert pika.current_hp == 160 - max(1, 160 // 8)
        assert any("Black Sludge" in e and "hurt" in e for e in result.log_entries)


# ═══════════════════════════════════════════════════════════════════════════
#  LIFE ORB
# ═══════════════════════════════════════════════════════════════════════════


class TestLifeOrb:
    def test_life_orb_boosts_damage(self):
        orbed = make_pokemon(
            name="Attacker", item="life-orb", attack=100, hp=200, moves=[make_move(power=80)]
        )
        normal = make_pokemon(name="Attacker", attack=100, hp=200, moves=[make_move(power=80)])
        dmg_orb, dmg_norm = _compare_damage(orbed, normal)
        assert dmg_orb > dmg_norm

    def test_life_orb_recoil(self):
        orbed = make_pokemon(
            name="Attacker", item="life-orb", attack=100, hp=200, moves=[make_move(power=80)]
        )
        target = make_pokemon(
            name="Target",
            hp=500,
            defense=80,
            moves=[make_move(name="growl", power=0, category="status")],
        )
        state = make_battle_state(team1=[orbed], team2=[target])
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        attacker = result.new_state.player1.team[0]
        # Should have taken 200//10 = 20 recoil
        assert attacker.current_hp == 200 - 20
        assert any("Life Orb" in e for e in result.log_entries)


# ═══════════════════════════════════════════════════════════════════════════
#  FOCUS SASH
# ═══════════════════════════════════════════════════════════════════════════


class TestFocusSash:
    def test_focus_sash_survives_ohko(self):
        state = make_battle_state(
            team1=[make_pokemon(name="Nuke", attack=200, moves=[make_move(power=150)])],
            team2=[
                make_pokemon(
                    name="Frail",
                    item="focus-sash",
                    hp=50,
                    defense=50,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        frail = result.new_state.player2.team[0]
        assert frail.current_hp == 1
        assert not frail.fainted
        assert frail.item_consumed
        assert any("Focus Sash" in e for e in result.log_entries)

    def test_focus_sash_consumed_only_once(self):
        """After consuming Focus Sash, a second hit KOs."""
        frail = make_pokemon(
            name="Frail",
            item="focus-sash",
            hp=50,
            defense=50,
            moves=[make_move(name="growl", power=0, category="status")],
        )
        state = make_battle_state(
            team1=[make_pokemon(name="Nuke", attack=200, hp=500, moves=[make_move(power=150)])],
            team2=[frail],
        )
        engine = TurnEngine(rng=Random(42))
        r1 = engine.resolve_turn(state, _move_action("user-1"), _move_action("user-2"))
        assert r1.new_state.player2.team[0].current_hp == 1

        r2 = engine.resolve_turn(r1.new_state, _move_action("user-1"), _move_action("user-2"))
        assert r2.new_state.player2.team[0].fainted

    def test_focus_sash_no_effect_when_not_full_hp(self):
        frail = make_pokemon(
            name="Frail",
            item="focus-sash",
            hp=100,
            defense=50,
            moves=[make_move(name="growl", power=0, category="status")],
        )
        frail.current_hp = 50
        state = make_battle_state(
            team1=[make_pokemon(name="Nuke", attack=200, moves=[make_move(power=150)])],
            team2=[frail],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player2.team[0].fainted


# ═══════════════════════════════════════════════════════════════════════════
#  ROCKY HELMET
# ═══════════════════════════════════════════════════════════════════════════


class TestRockyHelmet:
    def test_rocky_helmet_damages_attacker_on_contact(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    hp=240,
                    attack=80,
                    moves=[make_move(name="tackle", power=40, flags=["contact"])],
                )
            ],
            team2=[
                make_pokemon(
                    name="Tank",
                    item="rocky-helmet",
                    hp=300,
                    defense=100,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        attacker = result.new_state.player1.team[0]
        expected_recoil = max(1, 240 // 6)
        assert attacker.current_hp == 240 - expected_recoil
        assert any("Rocky Helmet" in e for e in result.log_entries)

    def test_rocky_helmet_no_effect_without_contact(self):
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    hp=240,
                    attack=80,
                    moves=[make_move(name="earthquake", type_="ground", power=100)],
                )
            ],
            team2=[
                make_pokemon(
                    name="Tank",
                    item="rocky-helmet",
                    hp=300,
                    defense=100,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player1.team[0].current_hp == 240


# ═══════════════════════════════════════════════════════════════════════════
#  ASSAULT VEST
# ═══════════════════════════════════════════════════════════════════════════


class TestAssaultVest:
    def test_assault_vest_reduces_special_damage(self):
        vested = make_pokemon(
            name="Defender", item="assault-vest", hp=300, special_defense=80, moves=[make_move()]
        )
        normal = make_pokemon(name="Defender", hp=300, special_defense=80, moves=[make_move()])
        attacker = make_pokemon(
            name="Attacker",
            special_attack=100,
            moves=[make_move(power=80, category="special", type_="fire")],
        )

        s1 = make_battle_state(team1=[attacker], team2=[vested])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_vest = 300 - r1.new_state.player2.team[0].current_hp

        attacker2 = make_pokemon(
            name="Attacker",
            special_attack=100,
            moves=[make_move(power=80, category="special", type_="fire")],
        )
        s2 = make_battle_state(team1=[attacker2], team2=[normal])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_norm = 300 - r2.new_state.player2.team[0].current_hp

        assert dmg_vest < dmg_norm

    def test_assault_vest_no_effect_on_physical(self):
        vested = make_pokemon(
            name="Defender", item="assault-vest", hp=300, defense=80, moves=[make_move()]
        )
        normal = make_pokemon(name="Defender", hp=300, defense=80, moves=[make_move()])
        attacker = make_pokemon(
            name="Attacker", attack=100, moves=[make_move(power=80, category="physical")]
        )

        s1 = make_battle_state(team1=[attacker], team2=[vested])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_vest = 300 - r1.new_state.player2.team[0].current_hp

        attacker2 = make_pokemon(
            name="Attacker", attack=100, moves=[make_move(power=80, category="physical")]
        )
        s2 = make_battle_state(team1=[attacker2], team2=[normal])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_norm = 300 - r2.new_state.player2.team[0].current_hp

        assert dmg_vest == dmg_norm


# ═══════════════════════════════════════════════════════════════════════════
#  EVIOLITE
# ═══════════════════════════════════════════════════════════════════════════


class TestEviolite:
    def test_eviolite_reduces_physical_damage(self):
        evo = make_pokemon(name="Chansey", item="eviolite", hp=300, defense=50, moves=[make_move()])
        normal = make_pokemon(name="Chansey", hp=300, defense=50, moves=[make_move()])
        attacker = make_pokemon(
            name="Attacker", attack=100, moves=[make_move(power=80, category="physical")]
        )

        s1 = make_battle_state(team1=[attacker], team2=[evo])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_evo = 300 - r1.new_state.player2.team[0].current_hp

        attacker2 = make_pokemon(
            name="Attacker", attack=100, moves=[make_move(power=80, category="physical")]
        )
        s2 = make_battle_state(team1=[attacker2], team2=[normal])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_norm = 300 - r2.new_state.player2.team[0].current_hp

        assert dmg_evo < dmg_norm

    def test_eviolite_reduces_special_damage(self):
        evo = make_pokemon(
            name="Chansey", item="eviolite", hp=300, special_defense=50, moves=[make_move()]
        )
        normal = make_pokemon(name="Chansey", hp=300, special_defense=50, moves=[make_move()])
        attacker = make_pokemon(
            name="Attacker",
            special_attack=100,
            moves=[make_move(power=80, category="special", type_="fire")],
        )

        s1 = make_battle_state(team1=[attacker], team2=[evo])
        r1 = _resolve(s1, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_evo = 300 - r1.new_state.player2.team[0].current_hp

        attacker2 = make_pokemon(
            name="Attacker",
            special_attack=100,
            moves=[make_move(power=80, category="special", type_="fire")],
        )
        s2 = make_battle_state(team1=[attacker2], team2=[normal])
        r2 = _resolve(s2, _move_action("user-1"), _move_action("user-2"), seed=99)
        dmg_norm = 300 - r2.new_state.player2.team[0].current_hp

        assert dmg_evo < dmg_norm


# ═══════════════════════════════════════════════════════════════════════════
#  BERRIES
# ═══════════════════════════════════════════════════════════════════════════


class TestSitrusBerry:
    def test_sitrus_berry_heals_when_hp_drops_below_50(self):
        """Sitrus Berry triggers at end of turn when HP <= 50%."""
        mon = make_pokemon(
            name="Mon",
            item="sitrus-berry",
            hp=200,
            moves=[make_move(name="growl", power=0, category="status")],
        )
        mon.current_hp = 90  # Below 50%

        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        tank = result.new_state.player1.team[0]
        assert tank.current_hp == 90 + 50  # 200//4 = 50
        assert tank.item_consumed
        assert any("Sitrus Berry" in e for e in result.log_entries)

    def test_sitrus_berry_no_trigger_above_50(self):
        mon = make_pokemon(
            name="Mon",
            item="sitrus-berry",
            hp=200,
            moves=[make_move(name="growl", power=0, category="status")],
        )
        mon.current_hp = 110  # Above 50%

        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player1.team[0].current_hp == 110
        assert not result.new_state.player1.team[0].item_consumed

    def test_sitrus_berry_consumed_once(self):
        mon = make_pokemon(
            name="Mon",
            item="sitrus-berry",
            hp=200,
            moves=[make_move(name="growl", power=0, category="status")],
        )
        mon.current_hp = 90
        mon.item_consumed = True  # Already consumed

        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player1.team[0].current_hp == 90


class TestLumBerry:
    def test_lum_berry_cures_status(self):
        mon = make_pokemon(
            name="Mon",
            item="lum-berry",
            hp=200,
            status=StatusCondition.PARALYSIS,
            moves=[make_move()],
        )
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        healed = result.new_state.player1.team[0]
        assert healed.status == StatusCondition.NONE
        assert healed.item_consumed
        assert any("Lum Berry" in e for e in result.log_entries)

    def test_lum_berry_no_trigger_when_healthy(self):
        mon = make_pokemon(name="Mon", item="lum-berry", hp=200, moves=[make_move()])
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert not result.new_state.player1.team[0].item_consumed


# ═══════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestItemIntegration:
    def test_rocky_helmet_plus_rough_skin_stacks(self):
        """Both Rough Skin ability and Rocky Helmet trigger on contact."""
        state = make_battle_state(
            team1=[
                make_pokemon(
                    name="Attacker",
                    hp=240,
                    attack=80,
                    moves=[make_move(name="tackle", power=40, flags=["contact"])],
                )
            ],
            team2=[
                make_pokemon(
                    name="Garchomp",
                    ability="rough-skin",
                    item="rocky-helmet",
                    hp=300,
                    defense=100,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        attacker = result.new_state.player1.team[0]
        rough_skin_dmg = max(1, 240 // 8)  # 30
        helmet_dmg = max(1, 240 // 6)  # 40
        assert attacker.current_hp == 240 - rough_skin_dmg - helmet_dmg
        assert any("Rough Skin" in e for e in result.log_entries)
        assert any("Rocky Helmet" in e for e in result.log_entries)

    def test_focus_sash_and_sturdy_both_save(self):
        """Only one triggers — Sturdy (ability) takes priority since it's checked first."""
        state = make_battle_state(
            team1=[make_pokemon(name="Nuke", attack=200, moves=[make_move(power=150)])],
            team2=[
                make_pokemon(
                    name="Golem",
                    ability="sturdy",
                    item="focus-sash",
                    hp=50,
                    defense=50,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        golem = result.new_state.player2.team[0]
        assert golem.current_hp == 1
        assert not golem.fainted
        # Sturdy should trigger, Focus Sash should NOT be consumed
        assert any("Sturdy" in e for e in result.log_entries)
        assert not golem.item_consumed

    def test_life_orb_recoil_can_faint(self):
        """Life Orb recoil can KO the attacker."""
        mon = make_pokemon(
            name="Attacker", item="life-orb", hp=100, attack=100, moves=[make_move(power=80)]
        )
        mon.current_hp = 5  # Very low HP
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Target",
                    hp=500,
                    defense=80,
                    moves=[make_move(name="growl", power=0, category="status")],
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        attacker = result.new_state.player1.team[0]
        assert attacker.fainted
        assert any("Life Orb" in e for e in result.log_entries)

    def test_leftovers_heals_after_burn_damage(self):
        """Leftovers heal at end of turn, after burn damage."""
        mon = make_pokemon(
            name="Tank",
            item="leftovers",
            hp=320,
            status=StatusCondition.BURN,
            moves=[make_move(name="growl", power=0, category="status")],
        )
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        tank = result.new_state.player1.team[0]
        burn_dmg = max(1, 320 // 16)  # 20
        leftovers_heal = max(1, 320 // 16)  # 20
        assert tank.current_hp == 320 - burn_dmg + leftovers_heal

    def test_choice_scarf_plus_swift_swim_stacks(self):
        """Choice Scarf and Swift Swim both boost speed."""
        slow = make_pokemon(
            name="SlowMon",
            speed=40,
            ability="swift-swim",
            item="choice-scarf",
            hp=500,
            moves=[make_move()],
        )
        fast = make_pokemon(name="FastMon", speed=100, hp=500, moves=[make_move()])
        state = make_battle_state(
            team1=[slow],
            team2=[fast],
            weather=Weather.RAIN,
            weather_turns=5,
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        # 40 * 2 (Swift Swim) * 1.5 (Scarf) = 120 > 100
        assert "SlowMon" in result.log_entries[0]

    def test_lum_berry_cures_burn_after_status_damage(self):
        """Lum Berry triggers after burn damage at end of turn."""
        mon = make_pokemon(
            name="Mon",
            item="lum-berry",
            hp=200,
            status=StatusCondition.BURN,
            moves=[make_move(name="growl", power=0, category="status")],
        )
        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        healed = result.new_state.player1.team[0]
        assert healed.status == StatusCondition.NONE
        assert healed.item_consumed
        # Should have taken burn damage first, then been cured
        burn_dmg = max(1, 200 // 16)
        assert healed.current_hp == 200 - burn_dmg

    def test_item_consumed_flag_persists_across_turns(self):
        """Once item_consumed is set, the item no longer activates."""
        mon = make_pokemon(name="Mon", item="sitrus-berry", hp=200)
        mon.current_hp = 80
        mon.item_consumed = True

        state = make_battle_state(
            team1=[mon],
            team2=[
                make_pokemon(
                    name="Foe", moves=[make_move(name="growl", power=0, category="status")]
                )
            ],
        )
        result = _resolve(state, _move_action("user-1"), _move_action("user-2"))
        assert result.new_state.player1.team[0].current_hp == 80  # No heal

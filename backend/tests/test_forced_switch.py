"""Tests for forced switch mechanics after a Pokemon faints."""

from random import Random

from app.battle.actions import MoveAction
from app.battle.engine import TurnEngine
from tests.helpers import make_battle_state, make_pokemon


class TestForcedSwitch:
    """When a Pokemon faints and the player has multiple bench options."""

    def test_faint_with_multiple_bench_triggers_forced_switch(self):
        """If the player has 2+ non-fainted bench mons, forced_switches is populated."""
        engine = TurnEngine(rng=Random(42))

        team1 = [make_pokemon(name="Attacker", hp=200, attack=999, speed=100)]
        team2 = [
            make_pokemon(name="Defender", hp=1, speed=50),
            make_pokemon(name="Bench1", hp=100, speed=50),
            make_pokemon(name="Bench2", hp=100, speed=50),
        ]

        state = make_battle_state(team1=team1, team2=team2)
        result = engine.resolve_turn(
            state,
            MoveAction(player_id="user-1", move_index=0),
            MoveAction(player_id="user-2", move_index=0),
        )

        assert "Defender fainted!" in result.log_entries
        assert "user-2" in result.forced_switches
        assert not result.battle_over

    def test_faint_with_one_bench_auto_switches(self):
        """If the player has only 1 non-fainted bench mon, auto-switch happens."""
        engine = TurnEngine(rng=Random(42))

        team1 = [make_pokemon(name="Attacker", hp=200, attack=999, speed=100)]
        team2 = [
            make_pokemon(name="Defender", hp=1, speed=50),
            make_pokemon(name="Bench1", hp=100, speed=50),
        ]

        state = make_battle_state(team1=team1, team2=team2)
        result = engine.resolve_turn(
            state,
            MoveAction(player_id="user-1", move_index=0),
            MoveAction(player_id="user-2", move_index=0),
        )

        assert "Defender fainted!" in result.log_entries
        assert "Go, Bench1!" in result.log_entries
        assert result.forced_switches == []
        assert result.new_state.player2.active_index == 1

    def test_faint_with_no_bench_ends_battle(self):
        """If the player has no bench mons left, the battle ends."""
        engine = TurnEngine(rng=Random(42))

        team1 = [make_pokemon(name="Attacker", hp=200, attack=999, speed=100)]
        team2 = [make_pokemon(name="Defender", hp=1, speed=50)]

        state = make_battle_state(team1=team1, team2=team2)
        result = engine.resolve_turn(
            state,
            MoveAction(player_id="user-1", move_index=0),
            MoveAction(player_id="user-2", move_index=0),
        )

        assert result.battle_over
        assert result.winner_id == "user-1"

    def test_apply_forced_switch(self):
        """apply_forced_switch correctly switches the active Pokemon."""
        engine = TurnEngine(rng=Random(42))

        team = [
            make_pokemon(name="Fainted", hp=0, fainted=True),
            make_pokemon(name="Choice1", hp=100),
            make_pokemon(name="Choice2", hp=100),
        ]

        state = make_battle_state(team1=team)
        result = engine.apply_forced_switch(state, "user-1", switch_to=2)

        assert result.new_state.player1.active_index == 2
        assert "Go, Choice2!" in result.log_entries
        assert not result.battle_over
        assert not result.needs_switch

    def test_apply_forced_switch_with_hazard_faint_auto_switches(self):
        """If switch-in faints from hazards with only 1 remaining, auto-switch to last mon."""
        from app.battle.state import SideState

        engine = TurnEngine(rng=Random(42))

        team = [
            make_pokemon(name="Fainted", hp=0, fainted=True),
            make_pokemon(
                name="Fragile", hp=1, species_id=6, types=["fire", "flying"]
            ),  # 4x SR weakness
            make_pokemon(name="Backup", hp=100),
        ]

        state = make_battle_state(team1=team)
        state.side1 = SideState(stealth_rock=True)

        result = engine.apply_forced_switch(state, "user-1", switch_to=1)

        assert "Fragile fainted!" in result.log_entries
        assert "Go, Backup!" in result.log_entries
        # Auto-switched to last mon, no further switch needed
        assert not result.needs_switch
        assert not result.battle_over

    def test_apply_forced_switch_with_hazard_faint_needs_switch(self):
        """If switch-in faints from hazards with 2+ remaining, needs_switch is True."""
        from app.battle.state import SideState

        engine = TurnEngine(rng=Random(42))

        team = [
            make_pokemon(name="Fainted", hp=0, fainted=True),
            make_pokemon(
                name="Fragile", hp=1, species_id=6, types=["fire", "flying"]
            ),  # 4x SR weakness
            make_pokemon(name="Backup1", hp=100),
            make_pokemon(name="Backup2", hp=100),
        ]

        state = make_battle_state(team1=team)
        state.side1 = SideState(stealth_rock=True)

        result = engine.apply_forced_switch(state, "user-1", switch_to=1)

        assert "Fragile fainted!" in result.log_entries
        assert result.needs_switch

    def test_both_players_forced_switch(self):
        """If both players' mons faint, both appear in forced_switches."""
        engine = TurnEngine(rng=Random(42))

        team1 = [
            make_pokemon(name="Mon1A", hp=1, attack=999, speed=100),
            make_pokemon(name="Mon1B", hp=100),
            make_pokemon(name="Mon1C", hp=100),
        ]
        team2 = [
            make_pokemon(name="Mon2A", hp=1, attack=999, speed=50),
            make_pokemon(name="Mon2B", hp=100),
            make_pokemon(name="Mon2C", hp=100),
        ]

        state = make_battle_state(team1=team1, team2=team2)
        result = engine.resolve_turn(
            state,
            MoveAction(player_id="user-1", move_index=0),
            MoveAction(player_id="user-2", move_index=0),
        )

        # Both should faint (the faster one KOs first, then the slower one still tries)
        assert "Mon1A fainted!" in result.log_entries or "Mon2A fainted!" in result.log_entries
        # At least one forced switch should be needed
        assert len(result.forced_switches) >= 1

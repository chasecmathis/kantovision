"""Tests for strategic switching: ordering, switch-out cleanup, validation, forced switches."""

from random import Random

from app.battle.actions import MoveAction, SwitchAction
from app.battle.engine import TurnEngine
from app.battle.enums import StatusCondition, VolatileStatus
from app.battle.state import StatStages
from tests.helpers import make_battle_state, make_move, make_pokemon

SEED = 42


def _engine(seed=SEED) -> TurnEngine:
    return TurnEngine(rng=Random(seed))


def _move_action(state, side="p1", move_index=0) -> MoveAction:
    player = state.player1 if side == "p1" else state.player2
    return MoveAction(player_id=player.user_id, move_index=move_index)


def _switch_action(state, side="p1", switch_to=1) -> SwitchAction:
    player = state.player1 if side == "p1" else state.player2
    return SwitchAction(player_id=player.user_id, switch_to_index=switch_to)


# ─── Switch ordering ────────────────────────────────────────────────────────


class TestSwitchOrdering:
    def test_switch_happens_before_move(self):
        """A switch action should resolve before a move action regardless of speed."""
        switcher = make_pokemon(name="Switcher", hp=9999, speed=10)
        bench = make_pokemon(name="BenchMon", hp=9999, speed=10)
        attacker = make_pokemon(name="Attacker", hp=9999, speed=200, attack=100)
        state = make_battle_state(team1=[switcher, bench], team2=[attacker])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        # Switch log should appear before the attack log
        switch_idx = next((i for i, e in enumerate(result.log_entries) if "withdrawn" in e), -1)
        attack_idx = next((i for i, e in enumerate(result.log_entries) if "used" in e), -1)
        assert switch_idx >= 0
        assert attack_idx >= 0
        assert switch_idx < attack_idx

    def test_both_switches_before_moves(self):
        """If both players switch, both switches resolve before any moves."""
        mon1 = make_pokemon(name="Mon1", hp=9999, speed=50)
        bench1 = make_pokemon(name="Bench1", hp=9999, speed=50)
        mon2 = make_pokemon(name="Mon2", hp=9999, speed=100)
        bench2 = make_pokemon(name="Bench2", hp=9999, speed=100)
        state = make_battle_state(team1=[mon1, bench1], team2=[mon2, bench2])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _switch_action(state, "p2", switch_to=1),
        )

        # Both switches should be in the log
        switch_logs = [e for e in result.log_entries if "withdrawn" in e]
        assert len(switch_logs) == 2


# ─── Switch-out cleanup ─────────────────────────────────────────────────────


class TestSwitchOutCleanup:
    def test_volatile_statuses_cleared_on_switch(self):
        """Volatile statuses (flinch, confusion, etc.) should be cleared on switch-out."""
        mon = make_pokemon(name="Active", hp=9999, speed=100)
        mon.volatile_statuses.add(VolatileStatus.FLINCH)
        mon.volatile_statuses.add(VolatileStatus.CONFUSION)
        bench = make_pokemon(name="Bench", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, bench], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        # The old active (now at index 0) should have no volatile statuses
        old_active = result.new_state.player1.team[0]
        assert len(old_active.volatile_statuses) == 0

    def test_stat_stages_reset_on_switch(self):
        """All stat stage changes should reset to 0 on switch-out."""
        mon = make_pokemon(
            name="Boosted",
            hp=9999,
            speed=100,
            stat_stages=StatStages(attack=4, defense=-2, speed=2),
        )
        bench = make_pokemon(name="Bench", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, bench], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        old_active = result.new_state.player1.team[0]
        assert old_active.stat_stages.attack == 0
        assert old_active.stat_stages.defense == 0
        assert old_active.stat_stages.speed == 0

    def test_toxic_counter_resets_on_switch(self):
        """Toxic counter should reset to 0 when the Pokemon switches out."""
        mon = make_pokemon(
            name="Toxic",
            hp=9999,
            speed=100,
            status=StatusCondition.TOXIC,
        )
        mon.status_turns = 5
        bench = make_pokemon(name="Bench", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, bench], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        toxic_mon = result.new_state.player1.team[0]
        assert toxic_mon.status == StatusCondition.TOXIC  # status persists
        assert toxic_mon.status_turns == 0  # counter resets

    def test_non_volatile_status_persists_on_switch(self):
        """Burns, paralysis etc. should persist through switches."""
        mon = make_pokemon(
            name="Burned",
            hp=9999,
            speed=100,
            status=StatusCondition.BURN,
        )
        bench = make_pokemon(name="Bench", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, bench], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        old_active = result.new_state.player1.team[0]
        assert old_active.status == StatusCondition.BURN

    def test_last_move_cleared_on_switch(self):
        """Last move used should be cleared on switch-out."""
        mon = make_pokemon(name="Active", hp=9999, speed=100)
        mon.last_move_used = "thunderbolt"
        bench = make_pokemon(name="Bench", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, bench], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        old_active = result.new_state.player1.team[0]
        assert old_active.last_move_used is None


# ─── Switch validation ──────────────────────────────────────────────────────


class TestSwitchValidation:
    def test_cannot_switch_to_fainted_pokemon(self):
        """Switching to a fainted Pokemon should be a no-op."""
        mon = make_pokemon(name="Active", hp=9999, speed=100)
        fainted = make_pokemon(name="Fainted", hp=100, fainted=True)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, fainted], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        # Should not have switched (active_index unchanged)
        assert result.new_state.player1.active_index == 0
        # No "withdrawn" message should appear
        assert not any("withdrawn" in e for e in result.log_entries)

    def test_cannot_switch_to_self(self):
        """Switching to the already-active index should be a no-op."""
        mon = make_pokemon(name="Active", hp=9999, speed=100)
        bench = make_pokemon(name="Bench", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, bench], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=0),  # same as current
            _move_action(state, "p2"),
        )

        assert result.new_state.player1.active_index == 0
        assert not any("withdrawn" in e for e in result.log_entries)

    def test_cannot_switch_out_of_bounds(self):
        """Invalid switch index should be a no-op."""
        mon = make_pokemon(name="Active", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=5),
            _move_action(state, "p2"),
        )

        assert result.new_state.player1.active_index == 0


# ─── Switch + move interaction ───────────────────────────────────────────────


class TestSwitchMoveInteraction:
    def test_attack_hits_new_pokemon(self):
        """When one player switches, the opponent's attack should hit the new Pokemon."""
        active = make_pokemon(name="Active", hp=9999, speed=50)
        bench = make_pokemon(name="Bench", hp=300, speed=50, defense=50, types=["normal"])
        attacker = make_pokemon(name="Attacker", hp=9999, speed=200, attack=150)
        attacker.moves = [make_move(name="tackle", power=80, type_="normal")]
        state = make_battle_state(team1=[active, bench], team2=[attacker])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        # Bench (now active at index 1) should have taken damage
        new_active = result.new_state.player1.team[1]
        assert new_active.current_hp < 300
        # Old active (at index 0) should be untouched (still at 9999)
        old_active = result.new_state.player1.team[0]
        assert old_active.current_hp == 9999

    def test_switch_after_faint_advances_automatically(self):
        """When a Pokemon faints, advance_active should pick the next available."""
        strong = make_pokemon(name="Strong", hp=9999, attack=9999, speed=200)
        weak = make_pokemon(name="Weak", hp=1, speed=10, defense=1, types=["normal"])
        backup = make_pokemon(name="Backup", hp=500, speed=10)
        state = make_battle_state(team1=[strong], team2=[weak, backup])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _move_action(state, "p1"),
            _move_action(state, "p2"),
        )

        # Weak fainted, active_index should advance to Backup
        assert result.new_state.player2.team[0].fainted
        assert result.new_state.player2.active_index == 1
        assert any("fainted" in e for e in result.log_entries)


# ─── Log messages ────────────────────────────────────────────────────────────


class TestSwitchLogMessages:
    def test_switch_logs_withdrawal_and_send_out(self):
        mon = make_pokemon(name="Pikachu", hp=9999, speed=100)
        bench = make_pokemon(name="Charizard", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, bench], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        switch_log = [e for e in result.log_entries if "withdrawn" in e]
        assert len(switch_log) == 1
        assert "Pikachu" in switch_log[0]
        assert "Charizard" in switch_log[0]

    def test_active_index_updated_after_switch(self):
        mon = make_pokemon(name="Mon1", hp=9999, speed=100)
        bench = make_pokemon(name="Mon2", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon, bench], team2=[other])

        engine = _engine()
        result = engine.resolve_turn(
            state,
            _switch_action(state, "p1", switch_to=1),
            _move_action(state, "p2"),
        )

        assert result.new_state.player1.active_index == 1


# ─── Multi-turn switch scenarios ─────────────────────────────────────────────


class TestMultiTurnSwitch:
    def test_switch_back_and_forth(self):
        """Switch out then switch back — stats should reset each time."""
        mon1 = make_pokemon(
            name="Mon1",
            hp=9999,
            speed=100,
            moves=[make_move(name="swords-dance", power=0, type_="normal", category="status")],
        )
        mon2 = make_pokemon(name="Mon2", hp=9999, speed=100)
        other = make_pokemon(name="Other", hp=9999, speed=50)
        state = make_battle_state(team1=[mon1, mon2], team2=[other])
        engine = _engine()

        # Turn 1: Use Swords Dance (+2 attack)
        r1 = engine.resolve_turn(state, _move_action(state, "p1"), _move_action(state, "p2"))
        assert r1.new_state.player1.team[0].stat_stages.attack == 2

        # Turn 2: Switch out — stat stages reset
        r2 = engine.resolve_turn(
            r1.new_state,
            _switch_action(r1.new_state, "p1", switch_to=1),
            _move_action(r1.new_state, "p2"),
        )
        assert r2.new_state.player1.team[0].stat_stages.attack == 0
        assert r2.new_state.player1.active_index == 1

        # Turn 3: Switch back — starts fresh
        r3 = engine.resolve_turn(
            r2.new_state,
            _switch_action(r2.new_state, "p1", switch_to=0),
            _move_action(r2.new_state, "p2"),
        )
        assert r3.new_state.player1.active_index == 0
        assert r3.new_state.player1.team[0].stat_stages.attack == 0

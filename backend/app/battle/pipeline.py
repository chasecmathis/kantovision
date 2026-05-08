"""Turn pipeline context and phase helpers.

TurnContext wraps a deep-copied BattleState and provides helper methods
that the engine and effect hooks use to inspect and mutate battle state.
"""

from __future__ import annotations

from enum import StrEnum
from random import Random
from typing import Literal

# Ensure effects are registered on import
import app.battle.effects.abilities  # noqa: F401
import app.battle.effects.items  # noqa: F401
from app.battle.effects.registry import ABILITY_REGISTRY, ITEM_REGISTRY
from app.battle.enums import StatusCondition
from app.battle.state import (
    BattleState,
    PlayerState,
    PokemonBattleState,
    SideState,
)
from app.battle.stats import get_stat_stage_multiplier


class TurnPhase(StrEnum):
    ACTION_ORDERING = "action_ordering"
    PRE_TURN = "pre_turn"
    ACTION_EXECUTION = "action_execution"
    END_OF_TURN = "end_of_turn"
    FORCED_SWITCHES = "forced_switches"
    BATTLE_END_CHECK = "battle_end_check"


Side = Literal["p1", "p2"]


class TurnContext:
    """Mutable wrapper around a deep-copied BattleState.

    Provides helpers for the engine pipeline and effect hooks to read
    and mutate battle state in a controlled way.
    """

    def __init__(self, state: BattleState, rng: Random) -> None:
        self.state = state
        self.rng = rng
        self.log: list[str] = []
        self.pending_forced_switches: list[str] = []  # player user_ids

    # ─── Player / side helpers ───────────────────────────────────────────

    def get_player(self, side: Side) -> PlayerState:
        return self.state.player1 if side == "p1" else self.state.player2

    def get_side_state(self, side: Side) -> SideState:
        return self.state.side1 if side == "p1" else self.state.side2

    def get_opponent_side(self, side: Side) -> Side:
        return "p2" if side == "p1" else "p1"

    def get_active(self, side: Side) -> PokemonBattleState:
        player = self.get_player(side)
        return player.team[player.active_index]

    def side_for_user(self, user_id: str) -> Side:
        if user_id == self.state.player1.user_id:
            return "p1"
        return "p2"

    # ─── Effect lookups ─────────────────────────────────────────────────

    def get_ability(self, pokemon: PokemonBattleState):
        """Look up the AbilityEffect for a Pokemon's ability, or None."""
        return ABILITY_REGISTRY.get(pokemon.ability)

    def get_item(self, pokemon: PokemonBattleState):
        """Look up the ItemEffect for a Pokemon's held item, or None."""
        if pokemon.item_consumed:
            return None
        return ITEM_REGISTRY.get(pokemon.item)

    # ─── Stat helpers ────────────────────────────────────────────────────

    def get_effective_stat(self, pokemon: PokemonBattleState, stat: str) -> int:
        """Get a Pokemon's effective stat value including stat stage modifiers."""
        base_val = getattr(pokemon, stat)
        stage = getattr(pokemon.stat_stages, stat, 0)
        is_acc_eva = stat in ("accuracy", "evasion")
        multiplier = get_stat_stage_multiplier(stage, is_accuracy_evasion=is_acc_eva)
        return max(1, int(base_val * multiplier))

    def get_effective_speed(self, pokemon: PokemonBattleState) -> int:
        """Get effective speed including stat stages, paralysis, abilities, and items."""
        speed = self.get_effective_stat(pokemon, "speed")
        # Paralysis halves speed (Gen V+)
        if pokemon.status == StatusCondition.PARALYSIS:
            speed = max(1, speed // 2)
        # Ability speed modifier
        ability = self.get_ability(pokemon)
        if ability:
            speed = ability.on_modify_speed(self, pokemon, speed)
        # Item speed modifier (Choice Scarf)
        item = self.get_item(pokemon)
        if item:
            speed = item.on_modify_speed(self, pokemon, speed)
        return speed

    # ─── Stat stage changes ──────────────────────────────────────────────

    def apply_stat_change(
        self,
        pokemon: PokemonBattleState,
        stat: str,
        stages: int,
        *,
        source: str = "",
    ) -> int:
        """Apply a stat stage change. Returns the actual change applied (clamped to -6..+6)."""
        # Let the defender's ability modify the stage change (e.g. Clear Body)
        ability = self.get_ability(pokemon)
        if ability:
            stages = ability.on_stat_change(self, pokemon, stat, stages)
            if stages == 0:
                return 0
        current = getattr(pokemon.stat_stages, stat, 0)
        new_val = max(-6, min(6, current + stages))
        actual_change = new_val - current

        if actual_change == 0:
            self.log.append(
                f"{pokemon.name}'s {stat} won't go any {'higher' if stages > 0 else 'lower'}!"
            )
            return 0

        setattr(pokemon.stat_stages, stat, new_val)

        if actual_change > 0:
            desc = (
                "rose"
                if actual_change == 1
                else "rose sharply"
                if actual_change == 2
                else "rose drastically"
            )
        else:
            desc = (
                "fell"
                if actual_change == -1
                else "fell harshly"
                if actual_change == -2
                else "fell severely"
            )

        msg = f"{pokemon.name}'s {stat} {desc}!"
        if source:
            msg = f"{source}: {msg}"
        self.log.append(msg)
        return actual_change

    # ─── Damage helpers ──────────────────────────────────────────────────

    def apply_damage(self, pokemon: PokemonBattleState, amount: int) -> int:
        """Apply damage to a Pokemon. Returns actual damage dealt."""
        actual = min(amount, pokemon.current_hp)
        pokemon.current_hp = max(0, pokemon.current_hp - actual)
        if pokemon.current_hp == 0:
            pokemon.fainted = True
        return actual

    def heal(self, pokemon: PokemonBattleState, amount: int) -> int:
        """Heal a Pokemon. Returns actual HP restored."""
        if pokemon.fainted:
            return 0
        actual = min(amount, pokemon.max_hp - pokemon.current_hp)
        pokemon.current_hp += actual
        return actual

    # ─── Active advancement ──────────────────────────────────────────────

    def advance_active(self, player: PlayerState) -> None:
        """Move active_index to the next non-fainted Pokemon, if one exists."""
        for i, mon in enumerate(player.team):
            if not mon.fainted:
                player.active_index = i
                return

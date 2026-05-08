"""Base classes for ability, item, and move effects.

Each effect class overrides only the hooks it needs. All hooks are no-ops
by default so subclasses stay minimal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.battle.enums import StatusCondition, Terrain, Weather

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


class AbilityEffect:
    """Base class for ability implementations. Override only the hooks you need."""

    name: str = ""

    def on_switch_in(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        pass

    def on_switch_out(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        pass

    def on_before_move(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
    ) -> MoveSlot | None:
        """Return a modified move, or None to keep the original."""
        return None

    def on_try_hit(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
    ) -> bool:
        """Return False to block the move entirely (type-absorb abilities)."""
        return True

    def on_modify_atk(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        value: int,
    ) -> int:
        return value

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        return damage

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        pass

    def on_modify_speed(self, ctx: TurnContext, pokemon: PokemonBattleState, speed: int) -> int:
        return speed

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        pass

    def on_stat_change(
        self,
        ctx: TurnContext,
        pokemon: PokemonBattleState,
        stat: str,
        stages: int,
    ) -> int:
        """Return modified stage change amount (e.g. Clear Body returns 0)."""
        return stages

    def on_before_faint(self, ctx: TurnContext, pokemon: PokemonBattleState, damage: int) -> int:
        """Return modified damage (e.g. Sturdy reduces to max_hp - 1)."""
        return damage


class ItemEffect:
    """Base class for held item implementations."""

    name: str = ""

    def on_modify_atk(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        value: int,
    ) -> int:
        return value

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        return damage

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        """Called on the defender's item after taking damage."""
        pass

    def on_attacker_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        """Called on the attacker's item after dealing damage (e.g. Life Orb recoil)."""
        pass

    def on_modify_speed(self, ctx: TurnContext, pokemon: PokemonBattleState, speed: int) -> int:
        return speed

    def on_modify_stat(
        self,
        ctx: TurnContext,
        pokemon: PokemonBattleState,
        stat: str,
        value: int,
    ) -> int:
        return value

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        pass

    def on_before_faint(self, ctx: TurnContext, pokemon: PokemonBattleState, damage: int) -> int:
        """Return modified damage (e.g. Focus Sash reduces to max_hp - 1)."""
        return damage

    def on_after_status_damage(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        """Called after end-of-turn status/weather damage — berry trigger point."""
        pass


@dataclass
class StatChange:
    """A single stat stage change."""

    stat: str
    stages: int


@dataclass
class MoveEffectSpec:
    """Data-driven specification for a move's secondary/additional effects.

    Most moves can be described by composing these fields rather than writing
    custom code. For truly unique moves, subclass and override apply().
    """

    status: StatusCondition | None = None
    status_chance: int = 0
    stat_changes: list[StatChange] = field(default_factory=list)
    stat_chance: int = 100
    self_stat_changes: list[StatChange] = field(default_factory=list)
    recoil_fraction: float = 0.0
    drain_fraction: float = 0.0
    flinch_chance: int = 0
    hits: tuple[int, int] = (1, 1)
    weather: Weather | None = None
    terrain: Terrain | None = None

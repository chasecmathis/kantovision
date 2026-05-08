"""Damage-modifying abilities: Huge Power, Adaptability, Guts, Technician."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import AbilityEffect
from app.battle.effects.registry import register_ability
from app.battle.enums import StatusCondition

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


@register_ability
class HugePower(AbilityEffect):
    """Doubles the Pokemon's Attack stat for physical moves."""

    name = "huge-power"

    def on_modify_atk(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        value: int,
    ) -> int:
        if move.category == "physical":
            return value * 2
        return value


@register_ability
class PurePower(AbilityEffect):
    """Functionally identical to Huge Power."""

    name = "pure-power"

    def on_modify_atk(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        value: int,
    ) -> int:
        if move.category == "physical":
            return value * 2
        return value


@register_ability
class Adaptability(AbilityEffect):
    """STAB bonus is 2x instead of 1.5x. Implemented via damage modifier."""

    name = "adaptability"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        # Only applies to STAB moves. The engine already applied 1.5x STAB,
        # so we multiply by 4/3 to get the 2x total: damage * 1.5 * (4/3) = damage * 2
        if move.type in attacker.types:
            return int(damage * 4 / 3)
        return damage


@register_ability
class Guts(AbilityEffect):
    """Attack is 1.5x when the user has a status condition. Also ignores burn penalty."""

    name = "guts"

    def on_modify_atk(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        value: int,
    ) -> int:
        if move.category == "physical" and attacker.status != StatusCondition.NONE:
            return int(value * 1.5)
        return value


@register_ability
class Technician(AbilityEffect):
    """Moves with base power <= 60 get a 1.5x damage boost."""

    name = "technician"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if move.power and move.power <= 60:
            return int(damage * 1.5)
        return damage

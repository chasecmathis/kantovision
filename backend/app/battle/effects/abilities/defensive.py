"""Defensive abilities: Multiscale, Sturdy, Marvel Scale."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import AbilityEffect
from app.battle.effects.registry import register_ability
from app.battle.enums import StatusCondition

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


@register_ability
class Multiscale(AbilityEffect):
    """Damage is halved when the Pokemon is at full HP."""

    name = "multiscale"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if defender.current_hp == defender.max_hp:
            return damage // 2
        return damage


@register_ability
class Sturdy(AbilityEffect):
    """Survives a hit that would KO from full HP with 1 HP remaining."""

    name = "sturdy"

    def on_before_faint(self, ctx: TurnContext, pokemon: PokemonBattleState, damage: int) -> int:
        if pokemon.current_hp == pokemon.max_hp and damage >= pokemon.max_hp:
            ctx.log.append(f"{pokemon.name} endured the hit with Sturdy!")
            return pokemon.max_hp - 1
        return damage


@register_ability
class MarvelScale(AbilityEffect):
    """Defense is 1.5x when the Pokemon has a status condition."""

    name = "marvel-scale"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if move.category == "physical" and defender.status != StatusCondition.NONE:
            return int(damage * 2 / 3)
        return damage

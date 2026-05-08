"""Contact-triggered abilities: Rough Skin, Iron Barbs, Flame Body, Static."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import AbilityEffect
from app.battle.effects.registry import register_ability
from app.battle.enums import StatusCondition
from app.battle.status import apply_status

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


@register_ability
class RoughSkin(AbilityEffect):
    """Attacker takes 1/8 max HP damage when making contact."""

    name = "rough-skin"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if "contact" in move.flags and not attacker.fainted:
            recoil = max(1, attacker.max_hp // 8)
            ctx.apply_damage(attacker, recoil)
            ctx.log.append(f"{attacker.name} was hurt by {defender.name}'s Rough Skin!")


@register_ability
class IronBarbs(AbilityEffect):
    """Attacker takes 1/8 max HP damage when making contact."""

    name = "iron-barbs"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if "contact" in move.flags and not attacker.fainted:
            recoil = max(1, attacker.max_hp // 8)
            ctx.apply_damage(attacker, recoil)
            ctx.log.append(f"{attacker.name} was hurt by {defender.name}'s Iron Barbs!")


@register_ability
class FlameBody(AbilityEffect):
    """30% chance to burn the attacker on contact."""

    name = "flame-body"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if "contact" in move.flags and not attacker.fainted:
            if ctx.rng.randint(1, 100) <= 30:
                if apply_status(attacker, StatusCondition.BURN, ctx.rng):
                    ctx.log.append(f"{attacker.name} was burned by {defender.name}'s Flame Body!")


@register_ability
class Static(AbilityEffect):
    """30% chance to paralyze the attacker on contact."""

    name = "static"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if "contact" in move.flags and not attacker.fainted:
            if ctx.rng.randint(1, 100) <= 30:
                if apply_status(attacker, StatusCondition.PARALYSIS, ctx.rng):
                    ctx.log.append(f"{attacker.name} was paralyzed by {defender.name}'s Static!")

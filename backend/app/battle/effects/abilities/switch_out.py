"""Switch-out abilities: Natural Cure, Regenerator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import AbilityEffect
from app.battle.effects.registry import register_ability
from app.battle.enums import StatusCondition

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


@register_ability
class NaturalCure(AbilityEffect):
    """Cures non-volatile status on switch-out."""

    name = "natural-cure"

    def on_switch_out(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        if pokemon.status != StatusCondition.NONE:
            old_status = pokemon.status
            pokemon.status = StatusCondition.NONE
            pokemon.status_turns = 0
            ctx.log.append(f"{pokemon.name}'s Natural Cure cured its {old_status}!")


@register_ability
class Regenerator(AbilityEffect):
    """Heals 1/3 max HP on switch-out."""

    name = "regenerator"

    def on_switch_out(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        if not pokemon.fainted:
            heal = max(1, pokemon.max_hp // 3)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                ctx.log.append(f"{pokemon.name}'s Regenerator restored HP!")

"""Berry items: Sitrus Berry, Lum Berry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item
from app.battle.enums import StatusCondition

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


@register_item
class SitrusBerry(ItemEffect):
    """Restores 25% max HP when HP drops to 50% or below. Consumed after use."""

    name = "sitrus-berry"

    def on_after_status_damage(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        self._try_activate(ctx, pokemon)

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        self._try_activate(ctx, pokemon)

    def _try_activate(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if pokemon.fainted or pokemon.item_consumed:
            return
        if pokemon.current_hp <= pokemon.max_hp // 2:
            heal = max(1, pokemon.max_hp // 4)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                pokemon.item_consumed = True
                ctx.log.append(f"{pokemon.name} restored HP with its Sitrus Berry!")


@register_item
class LumBerry(ItemEffect):
    """Cures any non-volatile status condition. Consumed after use."""

    name = "lum-berry"

    def on_after_status_damage(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        self._try_activate(ctx, pokemon)

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        self._try_activate(ctx, pokemon)

    def _try_activate(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if pokemon.fainted or pokemon.item_consumed:
            return
        if pokemon.status != StatusCondition.NONE:
            old_status = pokemon.status
            pokemon.status = StatusCondition.NONE
            pokemon.status_turns = 0
            pokemon.item_consumed = True
            ctx.log.append(f"{pokemon.name}'s Lum Berry cured its {old_status}!")

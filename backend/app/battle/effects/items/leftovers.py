"""Leftovers: restores 1/16 max HP at end of turn. Black Sludge: same for Poison types."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


@register_item
class Leftovers(ItemEffect):
    name = "leftovers"

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if not pokemon.fainted:
            heal = max(1, pokemon.max_hp // 16)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                ctx.log.append(f"{pokemon.name} restored HP with Leftovers!")


@register_item
class BlackSludge(ItemEffect):
    """Poison types heal 1/16; non-Poison types take 1/8 damage."""

    name = "black-sludge"

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if pokemon.fainted:
            return
        if "poison" in pokemon.types:
            heal = max(1, pokemon.max_hp // 16)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                ctx.log.append(f"{pokemon.name} restored HP with Black Sludge!")
        else:
            dmg = max(1, pokemon.max_hp // 8)
            ctx.apply_damage(pokemon, dmg)
            ctx.log.append(f"{pokemon.name} was hurt by Black Sludge!")

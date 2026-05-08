"""Focus Sash: survives a hit that would KO from full HP, consumed after use."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


@register_item
class FocusSash(ItemEffect):
    name = "focus-sash"

    def on_before_faint(self, ctx: TurnContext, pokemon: PokemonBattleState, damage: int) -> int:
        if (
            pokemon.current_hp == pokemon.max_hp
            and damage >= pokemon.max_hp
            and not pokemon.item_consumed
        ):
            pokemon.item_consumed = True
            ctx.log.append(f"{pokemon.name} held on with Focus Sash!")
            return pokemon.max_hp - 1
        return damage

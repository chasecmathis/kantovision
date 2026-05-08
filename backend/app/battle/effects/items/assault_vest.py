"""Assault Vest: 1.5x Special Defense, but can only use attacking moves."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


@register_item
class AssaultVest(ItemEffect):
    name = "assault-vest"

    def on_modify_stat(
        self,
        ctx: TurnContext,
        pokemon: PokemonBattleState,
        stat: str,
        value: int,
    ) -> int:
        if stat == "special_defense":
            return int(value * 1.5)
        return value

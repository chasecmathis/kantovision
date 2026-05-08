"""Eviolite: 1.5x Defense and Special Defense if the Pokemon can still evolve.

Since we don't have evolution chain data in battle state, we use a flag:
the `can_evolve` check is approximated by checking `volatile_data["can_evolve"]`.
For now, any Pokemon holding Eviolite is assumed to be eligible (the DB layer
should only assign Eviolite to Pokemon that can actually evolve).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


@register_item
class Eviolite(ItemEffect):
    name = "eviolite"

    def on_modify_stat(
        self,
        ctx: TurnContext,
        pokemon: PokemonBattleState,
        stat: str,
        value: int,
    ) -> int:
        if stat in ("defense", "special_defense"):
            return int(value * 1.5)
        return value

"""Choice items: Choice Band, Choice Specs, Choice Scarf.

Each boosts a stat by 1.5x but locks the user into the first move used.
The lock is tracked via volatile_data["choice_lock"] = move_index.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


@register_item
class ChoiceBand(ItemEffect):
    """1.5x Attack, locked into one move."""

    name = "choice-band"

    def on_modify_atk(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        value: int,
    ) -> int:
        if move.category == "physical":
            return int(value * 1.5)
        return value


@register_item
class ChoiceSpecs(ItemEffect):
    """1.5x Special Attack, locked into one move."""

    name = "choice-specs"

    def on_modify_atk(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        value: int,
    ) -> int:
        if move.category == "special":
            return int(value * 1.5)
        return value


@register_item
class ChoiceScarf(ItemEffect):
    """1.5x Speed, locked into one move."""

    name = "choice-scarf"

    def on_modify_speed(self, ctx: TurnContext, pokemon: PokemonBattleState, speed: int) -> int:
        return int(speed * 1.5)

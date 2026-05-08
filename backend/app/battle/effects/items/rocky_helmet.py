"""Rocky Helmet: attacker takes 1/6 max HP when making contact."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


@register_item
class RockyHelmet(ItemEffect):
    name = "rocky-helmet"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if "contact" in move.flags and not attacker.fainted:
            recoil = max(1, attacker.max_hp // 6)
            ctx.apply_damage(attacker, recoil)
            ctx.log.append(f"{attacker.name} was hurt by {defender.name}'s Rocky Helmet!")

"""Life Orb: 1.3x damage, 10% max HP recoil after each attack."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


@register_item
class LifeOrb(ItemEffect):
    name = "life-orb"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        return int(damage * 1.3)

    def on_attacker_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if not attacker.fainted:
            recoil = max(1, attacker.max_hp // 10)
            ctx.apply_damage(attacker, recoil)
            ctx.log.append(f"{attacker.name} lost HP due to Life Orb!")

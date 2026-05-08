"""Type-immunity abilities: Levitate, Lightning Rod, Water Absorb, Volt Absorb, Flash Fire."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import AbilityEffect
from app.battle.effects.registry import register_ability

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


@register_ability
class Levitate(AbilityEffect):
    name = "levitate"

    def on_try_hit(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
    ) -> bool:
        if move.type == "ground" and move.category != "status":
            ctx.log.append(f"{defender.name}'s Levitate makes it immune to Ground-type moves!")
            return False
        return True


@register_ability
class LightningRod(AbilityEffect):
    name = "lightning-rod"

    def on_try_hit(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
    ) -> bool:
        if move.type == "electric":
            ctx.apply_stat_change(
                defender,
                "special_attack",
                1,
                source=f"{defender.name}'s Lightning Rod",
            )
            return False
        return True


@register_ability
class WaterAbsorb(AbilityEffect):
    name = "water-absorb"

    def on_try_hit(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
    ) -> bool:
        if move.type == "water":
            healed = ctx.heal(defender, defender.max_hp // 4)
            if healed > 0:
                ctx.log.append(f"{defender.name}'s Water Absorb restored HP!")
            else:
                ctx.log.append(f"{defender.name}'s Water Absorb made the attack useless!")
            return False
        return True


@register_ability
class VoltAbsorb(AbilityEffect):
    name = "volt-absorb"

    def on_try_hit(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
    ) -> bool:
        if move.type == "electric":
            healed = ctx.heal(defender, defender.max_hp // 4)
            if healed > 0:
                ctx.log.append(f"{defender.name}'s Volt Absorb restored HP!")
            else:
                ctx.log.append(f"{defender.name}'s Volt Absorb made the attack useless!")
            return False
        return True


@register_ability
class FlashFire(AbilityEffect):
    """Grants immunity to Fire-type moves and boosts Fire-type attacks.

    Uses volatile_data["flash_fire"] as a flag (0 or 1) for the boost.
    """

    name = "flash-fire"

    def on_try_hit(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
    ) -> bool:
        if move.type == "fire":
            defender.volatile_data["flash_fire"] = 1
            ctx.log.append(f"{defender.name}'s Flash Fire raised the power of its Fire-type moves!")
            return False
        return True

    def on_modify_atk(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        value: int,
    ) -> int:
        if move.type == "fire" and attacker.volatile_data.get("flash_fire"):
            return int(value * 1.5)
        return value

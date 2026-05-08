"""Miscellaneous item implementations — batch 2.

Covers: Heavy-Duty Boots, Toxic Orb, Flame Orb, Expert Belt,
Muscle Band, Wise Glasses, Weakness Policy, White Herb,
Light Clay, weather rocks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import ItemEffect
from app.battle.effects.registry import register_item
from app.battle.enums import StatusCondition

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


@register_item
class HeavyDutyBoots(ItemEffect):
    """Immune to entry hazards."""

    name = "heavy-duty-boots"


@register_item
class ToxicOrb(ItemEffect):
    """Poisons the holder at end of turn."""

    name = "toxic-orb"

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if pokemon.status == StatusCondition.NONE:
            pokemon.status = StatusCondition.TOXIC
            pokemon.status_turns = 0
            ctx.log.append(f"{pokemon.name} was badly poisoned by its Toxic Orb!")


@register_item
class FlameOrb(ItemEffect):
    """Burns the holder at end of turn."""

    name = "flame-orb"

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if pokemon.status == StatusCondition.NONE:
            if "fire" not in pokemon.types:
                pokemon.status = StatusCondition.BURN
                ctx.log.append(f"{pokemon.name} was burned by its Flame Orb!")


@register_item
class ExpertBelt(ItemEffect):
    """1.2x damage on super effective moves."""

    name = "expert-belt"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        from app.battle.typechart import get_type_effectiveness

        eff = get_type_effectiveness(move.type, defender.types)
        if eff >= 2:
            return int(damage * 1.2)
        return damage


@register_item
class MuscleBand(ItemEffect):
    """1.1x damage on physical moves."""

    name = "muscle-band"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if move.category == "physical":
            return int(damage * 1.1)
        return damage


@register_item
class WiseGlasses(ItemEffect):
    """1.1x damage on special moves."""

    name = "wise-glasses"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if move.category == "special":
            return int(damage * 1.1)
        return damage


@register_item
class WeaknessPolicy(ItemEffect):
    """When hit by a super effective move, +2 Atk and +2 SpA. Consumed."""

    name = "weakness-policy"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        from app.battle.typechart import get_type_effectiveness

        if defender.item_consumed:
            return
        eff = get_type_effectiveness(move.type, defender.types)
        if eff >= 2:
            defender.item_consumed = True
            ctx.apply_stat_change(
                defender, "attack", 2, source=f"{defender.name}'s Weakness Policy"
            )
            ctx.apply_stat_change(
                defender, "special_attack", 2, source=f"{defender.name}'s Weakness Policy"
            )


@register_item
class WhiteHerb(ItemEffect):
    """Restores any negative stat changes once. Consumed."""

    name = "white-herb"

    def on_after_status_damage(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if pokemon.item_consumed:
            return
        stages = pokemon.stat_stages
        restored = False
        for stat in ("attack", "defense", "special_attack", "special_defense", "speed"):
            val = getattr(stages, stat)
            if val < 0:
                setattr(stages, stat, 0)
                restored = True
        if restored:
            pokemon.item_consumed = True
            ctx.log.append(f"{pokemon.name}'s White Herb restored its stats!")


@register_item
class LightClay(ItemEffect):
    """Screens last 8 turns instead of 5. (Checked by the screen-setting code.)"""

    name = "light-clay"


@register_item
class HeatRock(ItemEffect):
    """Sun lasts 8 turns instead of 5. (Checked by weather-setting code.)"""

    name = "heat-rock"


@register_item
class DampRock(ItemEffect):
    """Rain lasts 8 turns instead of 5."""

    name = "damp-rock"


@register_item
class SmoothRock(ItemEffect):
    """Sandstorm lasts 8 turns instead of 5."""

    name = "smooth-rock"


@register_item
class IcyRock(ItemEffect):
    """Hail lasts 8 turns instead of 5."""

    name = "icy-rock"


@register_item
class ScopeLens(ItemEffect):
    """Boosts critical-hit ratio by 1 stage."""

    name = "scope-lens"


@register_item
class AirBalloon(ItemEffect):
    """Immune to Ground-type moves. Pops when hit by any attack."""

    name = "air-balloon"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if not defender.item_consumed and damage > 0:
            defender.item_consumed = True
            ctx.log.append(f"{defender.name}'s Air Balloon popped!")

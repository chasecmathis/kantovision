"""Speed-modifying abilities: Speed Boost, Swift Swim, Chlorophyll, Sand Rush."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import AbilityEffect
from app.battle.effects.registry import register_ability
from app.battle.enums import Weather

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


@register_ability
class SpeedBoost(AbilityEffect):
    name = "speed-boost"

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if not pokemon.fainted:
            ctx.apply_stat_change(
                pokemon,
                "speed",
                1,
                source=f"{pokemon.name}'s Speed Boost",
            )


@register_ability
class SwiftSwim(AbilityEffect):
    name = "swift-swim"

    def on_modify_speed(self, ctx: TurnContext, pokemon: PokemonBattleState, speed: int) -> int:
        if ctx.state.field.weather == Weather.RAIN:
            return speed * 2
        return speed


@register_ability
class Chlorophyll(AbilityEffect):
    name = "chlorophyll"

    def on_modify_speed(self, ctx: TurnContext, pokemon: PokemonBattleState, speed: int) -> int:
        if ctx.state.field.weather == Weather.SUN:
            return speed * 2
        return speed


@register_ability
class SandRush(AbilityEffect):
    name = "sand-rush"

    def on_modify_speed(self, ctx: TurnContext, pokemon: PokemonBattleState, speed: int) -> int:
        if ctx.state.field.weather == Weather.SANDSTORM:
            return speed * 2
        return speed

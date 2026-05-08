"""Switch-in abilities: Intimidate, Drought, Drizzle, Sand Stream, Snow Warning."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import AbilityEffect
from app.battle.effects.registry import register_ability
from app.battle.enums import Weather

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


@register_ability
class Intimidate(AbilityEffect):
    name = "intimidate"

    def on_switch_in(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        opp_side = ctx.get_opponent_side(side)
        opponent = ctx.get_active(opp_side)
        if not opponent.fainted:
            ctx.apply_stat_change(
                opponent,
                "attack",
                -1,
                source=f"{pokemon.name}'s Intimidate",
            )


@register_ability
class Drought(AbilityEffect):
    name = "drought"

    def on_switch_in(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        ctx.state.field.weather = Weather.SUN
        ctx.state.field.weather_turns = 5
        ctx.log.append(f"{pokemon.name}'s Drought intensified the sun's rays!")


@register_ability
class Drizzle(AbilityEffect):
    name = "drizzle"

    def on_switch_in(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        ctx.state.field.weather = Weather.RAIN
        ctx.state.field.weather_turns = 5
        ctx.log.append(f"{pokemon.name}'s Drizzle made it rain!")


@register_ability
class SandStream(AbilityEffect):
    name = "sand-stream"

    def on_switch_in(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        ctx.state.field.weather = Weather.SANDSTORM
        ctx.state.field.weather_turns = 5
        ctx.log.append(f"{pokemon.name}'s Sand Stream whipped up a sandstorm!")


@register_ability
class SnowWarning(AbilityEffect):
    name = "snow-warning"

    def on_switch_in(self, ctx: TurnContext, pokemon: PokemonBattleState, side: str) -> None:
        ctx.state.field.weather = Weather.HAIL
        ctx.state.field.weather_turns = 5
        ctx.log.append(f"{pokemon.name}'s Snow Warning whipped up a hailstorm!")

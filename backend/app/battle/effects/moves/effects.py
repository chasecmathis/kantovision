"""Move effect interpreter — applies MoveEffectSpec after damage calculation.

Handles: secondary status infliction, stat changes (target and self),
flinch, recoil, drain, and multi-hit. Each field in MoveEffectSpec is
processed independently so effects compose naturally.
"""

from __future__ import annotations

from random import Random
from typing import TYPE_CHECKING

from app.battle.effects.base import MoveEffectSpec
from app.battle.enums import StatusCondition, Terrain, VolatileStatus, Weather
from app.battle.status import apply_status

_WEATHER_NAMES: dict[Weather, str] = {
    Weather.SUN: "The sunlight turned harsh!",
    Weather.RAIN: "It started to rain!",
    Weather.SANDSTORM: "A sandstorm kicked up!",
    Weather.HAIL: "It started to hail!",
}

_TERRAIN_NAMES: dict[Terrain, str] = {
    Terrain.ELECTRIC: "An electric current runs across the battlefield!",
    Terrain.GRASSY: "Grass grew to cover the battlefield!",
    Terrain.PSYCHIC: "The battlefield got weird!",
    Terrain.MISTY: "Mist swirled around the battlefield!",
}

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


def apply_move_effect(
    ctx: TurnContext,
    spec: MoveEffectSpec,
    attacker: PokemonBattleState,
    defender: PokemonBattleState,
    damage_dealt: int,
    rng: Random,
) -> None:
    """Apply a move's secondary/additional effects after damage."""

    # ── Secondary status infliction ──────────────────────────────────
    if spec.status and spec.status_chance > 0 and not defender.fainted:
        if rng.randint(1, 100) <= spec.status_chance:
            if apply_status(defender, spec.status, rng):
                ctx.log.append(f"{defender.name} was {_status_verb(spec.status)}!")
            # If it fails (immunity, already statused), silently skip

    # ── Stat changes on target ───────────────────────────────────────
    if spec.stat_changes and not defender.fainted:
        if rng.randint(1, 100) <= spec.stat_chance:
            for sc in spec.stat_changes:
                ctx.apply_stat_change(defender, sc.stat, sc.stages)

    # ── Stat changes on self ─────────────────────────────────────────
    if spec.self_stat_changes and not attacker.fainted:
        for sc in spec.self_stat_changes:
            ctx.apply_stat_change(attacker, sc.stat, sc.stages)

    # ── Flinch ───────────────────────────────────────────────────────
    if spec.flinch_chance > 0 and not defender.fainted:
        if rng.randint(1, 100) <= spec.flinch_chance:
            defender.volatile_statuses.add(VolatileStatus.FLINCH)

    # ── Recoil ───────────────────────────────────────────────────────
    if spec.recoil_fraction > 0 and damage_dealt > 0 and not attacker.fainted:
        recoil = max(1, int(damage_dealt * spec.recoil_fraction))
        ctx.apply_damage(attacker, recoil)
        ctx.log.append(f"{attacker.name} is damaged by recoil!")

    # ── Drain ────────────────────────────────────────────────────────
    if spec.drain_fraction > 0 and damage_dealt > 0 and not attacker.fainted:
        heal_amount = max(1, int(damage_dealt * spec.drain_fraction))
        healed = ctx.heal(attacker, heal_amount)
        if healed > 0:
            ctx.log.append(f"{attacker.name} restored HP!")

    # ── Weather / Terrain ───────────────────────────────────────────
    _apply_weather_terrain(ctx, spec)


def apply_status_move_effect(
    ctx: TurnContext,
    spec: MoveEffectSpec,
    attacker: PokemonBattleState,
    defender: PokemonBattleState,
    rng: Random,
) -> None:
    """Apply effects for status-category moves (no damage dealt).

    Status moves apply their effects at 100% rate (ignoring stat_chance
    for stat changes, but still respecting status_chance for status infliction).
    """

    # ── Status infliction ────────────────────────────────────────────
    if spec.status and not defender.fainted:
        chance = spec.status_chance if spec.status_chance > 0 else 100
        if rng.randint(1, 100) <= chance:
            if apply_status(defender, spec.status, rng):
                ctx.log.append(f"{defender.name} was {_status_verb(spec.status)}!")
            else:
                ctx.log.append(f"It didn't affect {defender.name}...")

    # ── Stat changes on target ───────────────────────────────────────
    if spec.stat_changes and not defender.fainted:
        for sc in spec.stat_changes:
            ctx.apply_stat_change(defender, sc.stat, sc.stages)

    # ── Stat changes on self ─────────────────────────────────────────
    if spec.self_stat_changes and not attacker.fainted:
        for sc in spec.self_stat_changes:
            ctx.apply_stat_change(attacker, sc.stat, sc.stages)

    # ── Weather setting ─────────────────────────────────────────────
    _apply_weather_terrain(ctx, spec)


def _apply_weather_terrain(ctx: TurnContext, spec: MoveEffectSpec) -> None:
    """Set weather or terrain from a move effect spec."""
    if spec.weather and spec.weather != Weather.NONE:
        ctx.state.field.weather = spec.weather
        ctx.state.field.weather_turns = 5
        ctx.log.append(_WEATHER_NAMES.get(spec.weather, f"{spec.weather} started!"))

    if spec.terrain and spec.terrain != Terrain.NONE:
        ctx.state.field.terrain = spec.terrain
        ctx.state.field.terrain_turns = 5
        ctx.log.append(_TERRAIN_NAMES.get(spec.terrain, f"{spec.terrain} terrain was set!"))


def _status_verb(status: StatusCondition) -> str:
    """Human-readable past-tense verb for status application."""
    return {
        StatusCondition.BURN: "burned",
        StatusCondition.FREEZE: "frozen",
        StatusCondition.PARALYSIS: "paralyzed",
        StatusCondition.POISON: "poisoned",
        StatusCondition.TOXIC: "badly poisoned",
        StatusCondition.SLEEP: "put to sleep",
    }.get(status, "afflicted")

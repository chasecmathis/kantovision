"""Damage calculation (Gen V+ formula at Level 50).

Includes critical hits, random damage factor, stat stage modifiers,
STAB, type effectiveness, and weather type boosts.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

from app.battle.enums import StatusCondition, Weather
from app.battle.state import MoveSlot, PokemonBattleState
from app.battle.stats import get_stat_stage_multiplier
from app.battle.typechart import get_type_effectiveness

if TYPE_CHECKING:
    from app.battle.effects.base import AbilityEffect, ItemEffect

# Critical hit rates by stage (Gen VI+)
_CRIT_CHANCE: dict[int, tuple[int, int]] = {
    0: (1, 24),  # ~4.17%
    1: (1, 8),  # 12.5%
    2: (1, 2),  # 50%
    3: (1, 1),  # 100%
}


@dataclass
class DamageResult:
    """Result of a damage calculation with metadata for logging."""

    damage: int
    effectiveness: float
    is_crit: bool


def _roll_crit(crit_stage: int, rng: Random) -> bool:
    """Return True if this hit is a critical hit."""
    stage = max(0, min(3, crit_stage))
    num, den = _CRIT_CHANCE[stage]
    return rng.randint(1, den) <= num


def _weather_modifier(weather: Weather, move_type: str) -> float:
    """Return the weather damage multiplier for a given move type."""
    if weather == Weather.RAIN:
        if move_type == "water":
            return 1.5
        if move_type == "fire":
            return 0.5
    elif weather == Weather.SUN:
        if move_type == "fire":
            return 1.5
        if move_type == "water":
            return 0.5
    return 1.0


def calc_damage(
    attacker: PokemonBattleState,
    defender: PokemonBattleState,
    move: MoveSlot,
    rng: Random,
    *,
    crit_stage: int = 0,
    weather: Weather = Weather.NONE,
    atk_ability: AbilityEffect | None = None,
    atk_item: ItemEffect | None = None,
    def_item: ItemEffect | None = None,
) -> DamageResult:
    """Calculate damage using the Gen V+ formula at Level 50.

    Formula:
        base = ((2 * level / 5 + 2) * power * A / D) / 50 + 2
        damage = base * crit * random * STAB * type_effectiveness
    """
    if not move.power or move.category == "status":
        effectiveness = get_type_effectiveness(move.type, defender.types)
        return DamageResult(damage=0, effectiveness=effectiveness, is_crit=False)

    level = 50

    # Determine physical/special stats
    if move.category == "physical":
        atk_base = attacker.attack
        atk_stage = attacker.stat_stages.attack
        def_base = defender.defense
        def_stage = defender.stat_stages.defense
    else:
        atk_base = attacker.special_attack
        atk_stage = attacker.stat_stages.special_attack
        def_base = defender.special_defense
        def_stage = defender.stat_stages.special_defense

    # Critical hit check
    is_crit = _roll_crit(crit_stage, rng)

    # Apply stat stages — crits ignore negative atk stages and positive def stages
    if is_crit:
        atk_mult = get_stat_stage_multiplier(max(0, atk_stage))
        def_mult = get_stat_stage_multiplier(min(0, def_stage))
    else:
        atk_mult = get_stat_stage_multiplier(atk_stage)
        def_mult = get_stat_stage_multiplier(def_stage)

    effective_atk = max(1, int(atk_base * atk_mult))
    effective_def = max(1, int(def_base * def_mult))

    # Burn halves physical attack (Gen V+) — unless ability overrides (Guts)
    has_guts = atk_ability and atk_ability.name == "guts"
    if move.category == "physical" and attacker.status == StatusCondition.BURN and not has_guts:
        effective_atk = max(1, effective_atk // 2)

    # Ability attack modifier (Huge Power, Guts, Flash Fire, etc.)
    if atk_ability:
        effective_atk = atk_ability.on_modify_atk(
            None,
            attacker,
            defender,
            move,
            effective_atk,
        )

    # Item attack modifier (Choice Band, Choice Specs)
    if atk_item:
        effective_atk = atk_item.on_modify_atk(
            None,
            attacker,
            defender,
            move,
            effective_atk,
        )

    # Item defense stat modifier (Assault Vest, Eviolite)
    if def_item:
        def_stat_name = "defense" if move.category == "physical" else "special_defense"
        effective_def = def_item.on_modify_stat(None, defender, def_stat_name, effective_def)

    # Base damage
    base = (2 * level / 5 + 2) * move.power * effective_atk / effective_def
    damage = int(base / 50 + 2)

    # Critical hit multiplier (1.5x in Gen VI+)
    if is_crit:
        damage = int(damage * 1.5)

    # Random factor: 85-100 (inclusive), divided by 100
    random_roll = rng.randint(85, 100)
    damage = damage * random_roll // 100

    # STAB
    if move.type in attacker.types:
        damage = int(damage * 1.5)

    # Weather modifier
    w_mod = _weather_modifier(weather, move.type)
    if w_mod != 1.0:
        damage = int(damage * w_mod)

    # Type effectiveness
    effectiveness = get_type_effectiveness(move.type, defender.types)
    damage = int(damage * effectiveness)

    if effectiveness == 0:
        return DamageResult(damage=0, effectiveness=0, is_crit=is_crit)

    return DamageResult(
        damage=max(1, damage),
        effectiveness=effectiveness,
        is_crit=is_crit,
    )

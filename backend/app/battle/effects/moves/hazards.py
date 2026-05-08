"""Hazard-related move effects: setting, clearing, and switch-in damage.

Hazard-setting moves: Stealth Rock, Spikes, Toxic Spikes
Hazard-clearing moves: Rapid Spin, Defog

Switch-in hazard damage is applied by the engine during _execute_switch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.enums import StatusCondition
from app.battle.status import apply_status
from app.battle.typechart import get_type_effectiveness

if TYPE_CHECKING:
    from random import Random

    from app.battle.pipeline import Side, TurnContext
    from app.battle.state import PokemonBattleState


# ─── Hazard-setting ──────────────────────────────────────────────────────────

# Maps move name → handler function
HAZARD_SETTERS: dict[str, object] = {}


def set_stealth_rock(
    ctx: TurnContext,
    attacker: PokemonBattleState,
    target_side: Side,
) -> None:
    side_state = ctx.get_side_state(target_side)
    if side_state.stealth_rock:
        ctx.log.append("But it failed! Stealth Rock is already set!")
        return
    side_state.stealth_rock = True
    ctx.log.append("Pointed stones float in the air around the opposing team!")


def set_spikes(
    ctx: TurnContext,
    attacker: PokemonBattleState,
    target_side: Side,
) -> None:
    side_state = ctx.get_side_state(target_side)
    if side_state.spikes >= 3:
        ctx.log.append("But it failed! Spikes are already at maximum!")
        return
    side_state.spikes += 1
    ctx.log.append("Spikes were scattered on the ground around the opposing team!")


def set_toxic_spikes(
    ctx: TurnContext,
    attacker: PokemonBattleState,
    target_side: Side,
) -> None:
    side_state = ctx.get_side_state(target_side)
    if side_state.toxic_spikes >= 2:
        ctx.log.append("But it failed! Toxic Spikes are already at maximum!")
        return
    side_state.toxic_spikes += 1
    ctx.log.append("Poison spikes were scattered on the ground around the opposing team!")


# ─── Hazard-clearing ─────────────────────────────────────────────────────────


def clear_own_hazards(ctx: TurnContext, user_side: Side) -> bool:
    """Clear hazards on the user's side (Rapid Spin). Returns True if any were cleared."""
    side_state = ctx.get_side_state(user_side)
    cleared = False
    if side_state.stealth_rock:
        side_state.stealth_rock = False
        cleared = True
    if side_state.spikes > 0:
        side_state.spikes = 0
        cleared = True
    if side_state.toxic_spikes > 0:
        side_state.toxic_spikes = 0
        cleared = True
    if side_state.sticky_web:
        side_state.sticky_web = False
        cleared = True
    if cleared:
        ctx.log.append("The hazards disappeared from around the team!")
    return cleared


def clear_all_hazards(ctx: TurnContext, user_side: Side) -> None:
    """Clear hazards on both sides (Defog)."""
    opp_side = ctx.get_opponent_side(user_side)
    any_cleared = False

    for side, label in [(user_side, "your"), (opp_side, "the opposing")]:
        side_state = ctx.get_side_state(side)
        cleared = False
        if side_state.stealth_rock:
            side_state.stealth_rock = False
            cleared = True
        if side_state.spikes > 0:
            side_state.spikes = 0
            cleared = True
        if side_state.toxic_spikes > 0:
            side_state.toxic_spikes = 0
            cleared = True
        if side_state.sticky_web:
            side_state.sticky_web = False
            cleared = True
        if side_state.reflect > 0:
            side_state.reflect = 0
            cleared = True
        if side_state.light_screen > 0:
            side_state.light_screen = 0
            cleared = True
        if cleared:
            ctx.log.append(f"The hazards disappeared from around {label} team!")
            any_cleared = True

    if not any_cleared:
        ctx.log.append("But there were no hazards to clear!")


# ─── Switch-in hazard damage ─────────────────────────────────────────────────


# Stealth Rock type effectiveness multipliers:
# Rock hits: 0.25x → 1/32, 0.5x → 1/16, 1x → 1/8, 2x → 1/4, 4x → 1/2
def apply_switch_in_hazards(
    ctx: TurnContext,
    pokemon: PokemonBattleState,
    side: Side,
    rng: Random,
) -> None:
    """Apply hazard damage/effects to a Pokemon that just switched in."""
    # Heavy-Duty Boots blocks all hazard damage
    if pokemon.item == "heavy-duty-boots" and not pokemon.item_consumed:
        return

    side_state = ctx.get_side_state(side)

    # ── Stealth Rock ─────────────────────────────────────────────────
    if side_state.stealth_rock:
        effectiveness = get_type_effectiveness("rock", pokemon.types)
        dmg = max(1, int(pokemon.max_hp * effectiveness / 8))
        ctx.apply_damage(pokemon, dmg)
        ctx.log.append(f"Pointed stones dug into {pokemon.name}!")
        if pokemon.fainted:
            ctx.log.append(f"{pokemon.name} fainted!")
            return

    # ── Spikes (grounded only — for now, all Pokemon are grounded unless Levitate) ─
    if side_state.spikes > 0:
        # Levitate/Flying-type immune
        is_grounded = "flying" not in pokemon.types
        if is_grounded:
            # 1 layer: 1/8, 2 layers: 1/6, 3 layers: 1/4
            fraction = {1: 8, 2: 6, 3: 4}[side_state.spikes]
            dmg = max(1, pokemon.max_hp // fraction)
            ctx.apply_damage(pokemon, dmg)
            ctx.log.append(f"{pokemon.name} was hurt by Spikes!")
            if pokemon.fainted:
                ctx.log.append(f"{pokemon.name} fainted!")
                return

    # ── Toxic Spikes ─────────────────────────────────────────────────
    if side_state.toxic_spikes > 0:
        is_grounded = "flying" not in pokemon.types
        if is_grounded:
            # Poison types absorb Toxic Spikes
            if "poison" in pokemon.types:
                side_state.toxic_spikes = 0
                ctx.log.append(f"{pokemon.name} absorbed the Toxic Spikes!")
            else:
                if side_state.toxic_spikes == 1:
                    if apply_status(pokemon, StatusCondition.POISON, rng):
                        ctx.log.append(f"{pokemon.name} was poisoned by Toxic Spikes!")
                elif side_state.toxic_spikes >= 2:
                    if apply_status(pokemon, StatusCondition.TOXIC, rng):
                        ctx.log.append(f"{pokemon.name} was badly poisoned by Toxic Spikes!")

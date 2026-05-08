"""Status condition logic — application, immunity, pre-turn checks, end-of-turn damage.

Gen V+ mechanics:
- Only one non-volatile status at a time.
- Type-based immunities:
    Electric can't be paralyzed
    Fire can't be burned
    Poison and Steel can't be poisoned/toxiced
    Ice can't be frozen
- Burn:  1/16 max HP damage end-of-turn, halves physical attack
- Poison: 1/8 max HP damage end-of-turn
- Toxic:  N/16 max HP damage end-of-turn (N increments each turn, starting at 1)
- Paralysis: 25% chance of not moving, halves speed
- Sleep: 1-3 turns (counter set on application), can't move until wake
- Freeze: 20% chance to thaw each turn, can't move while frozen;
          thawed immediately if hit by a Fire-type move
"""

from __future__ import annotations

from random import Random

from app.battle.enums import StatusCondition
from app.battle.state import PokemonBattleState

# Type-based immunities: status -> set of immune types
STATUS_IMMUNITIES: dict[StatusCondition, frozenset[str]] = {
    StatusCondition.BURN: frozenset({"fire"}),
    StatusCondition.PARALYSIS: frozenset({"electric"}),
    StatusCondition.POISON: frozenset({"poison", "steel"}),
    StatusCondition.TOXIC: frozenset({"poison", "steel"}),
    StatusCondition.FREEZE: frozenset({"ice"}),
}


def can_apply_status(
    target: PokemonBattleState,
    status: StatusCondition,
) -> bool:
    """Check whether a status can be applied to the target."""
    if target.fainted:
        return False
    # Already has a non-volatile status
    if target.status != StatusCondition.NONE:
        return False
    # Type-based immunity
    immune_types = STATUS_IMMUNITIES.get(status, frozenset())
    if immune_types & set(target.types):
        return False
    return True


def apply_status(
    target: PokemonBattleState,
    status: StatusCondition,
    rng: Random,
) -> bool:
    """Apply a status condition to the target. Returns True if applied."""
    if not can_apply_status(target, status):
        return False
    target.status = status
    target.status_turns = 0
    if status == StatusCondition.SLEEP:
        # Sleep lasts 1-3 turns (Gen V+)
        target.status_turns = rng.randint(1, 3)
    return True


def check_pre_turn(
    pokemon: PokemonBattleState,
    rng: Random,
) -> tuple[bool, str | None]:
    """Check if a Pokemon can act this turn based on its status.

    Returns (can_act, log_message). If can_act is False, the Pokemon
    skips its action this turn.
    """
    status = pokemon.status

    if status == StatusCondition.SLEEP:
        if pokemon.status_turns <= 0:
            pokemon.status = StatusCondition.NONE
            return True, f"{pokemon.name} woke up!"
        pokemon.status_turns -= 1
        return False, f"{pokemon.name} is fast asleep."

    if status == StatusCondition.FREEZE:
        # 20% chance to thaw each turn
        if rng.randint(1, 5) == 1:
            pokemon.status = StatusCondition.NONE
            return True, f"{pokemon.name} thawed out!"
        return False, f"{pokemon.name} is frozen solid!"

    if status == StatusCondition.PARALYSIS:
        # 25% chance of full paralysis
        if rng.randint(1, 4) == 1:
            return False, f"{pokemon.name} is paralyzed! It can't move!"

    return True, None


def apply_end_of_turn_damage(
    pokemon: PokemonBattleState,
) -> tuple[int, str | None]:
    """Apply end-of-turn status damage. Returns (damage_dealt, log_message)."""
    if pokemon.fainted:
        return 0, None

    status = pokemon.status

    if status == StatusCondition.BURN:
        dmg = max(1, pokemon.max_hp // 16)
        pokemon.current_hp = max(0, pokemon.current_hp - dmg)
        if pokemon.current_hp == 0:
            pokemon.fainted = True
        return dmg, f"{pokemon.name} was hurt by its burn! ({dmg} damage)"

    if status == StatusCondition.POISON:
        dmg = max(1, pokemon.max_hp // 8)
        pokemon.current_hp = max(0, pokemon.current_hp - dmg)
        if pokemon.current_hp == 0:
            pokemon.fainted = True
        return dmg, f"{pokemon.name} was hurt by poison! ({dmg} damage)"

    if status == StatusCondition.TOXIC:
        pokemon.status_turns += 1
        n = pokemon.status_turns
        dmg = max(1, pokemon.max_hp * n // 16)
        pokemon.current_hp = max(0, pokemon.current_hp - dmg)
        if pokemon.current_hp == 0:
            pokemon.fainted = True
        return dmg, f"{pokemon.name} was hurt by poison! ({dmg} damage)"

    return 0, None


def try_thaw_from_fire(pokemon: PokemonBattleState, move_type: str) -> str | None:
    """If a frozen Pokemon is hit by a Fire-type move, it thaws."""
    if pokemon.status == StatusCondition.FREEZE and move_type == "fire":
        pokemon.status = StatusCondition.NONE
        pokemon.status_turns = 0
        return f"{pokemon.name} was thawed out by the attack!"
    return None

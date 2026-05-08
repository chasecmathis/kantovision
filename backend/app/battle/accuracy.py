"""Accuracy check (Gen V+ mechanics).

Determines whether a move hits based on the move's accuracy,
attacker's accuracy stages, and defender's evasion stages.
"""

from __future__ import annotations

from random import Random

from app.battle.state import MoveSlot, PokemonBattleState
from app.battle.stats import get_stat_stage_multiplier


def accuracy_check(
    attacker: PokemonBattleState,
    defender: PokemonBattleState,
    move: MoveSlot,
    rng: Random,
) -> bool:
    """Return True if the move hits, False if it misses.

    Moves with accuracy=0 always hit (e.g. Swift, Aerial Ace).
    Otherwise: hit if random(0,99) < move_accuracy * acc_stage / eva_stage.
    """
    if not move.accuracy:
        return True

    acc_multiplier = get_stat_stage_multiplier(
        attacker.stat_stages.accuracy, is_accuracy_evasion=True
    )
    eva_multiplier = get_stat_stage_multiplier(
        defender.stat_stages.evasion, is_accuracy_evasion=True
    )

    # Effective accuracy: move's base accuracy * (acc_stage / eva_stage)
    effective = move.accuracy * acc_multiplier / eva_multiplier
    threshold = int(effective)

    return rng.randint(1, 100) <= threshold

"""Protect and Detect — blocks all incoming moves for the turn.

+4 priority. Success chance halves on consecutive use:
  1st: 100%, 2nd: 50%, 3rd: 25%, etc.

Tracked via volatile_data["protect_turns"] (consecutive successful uses).
The PROTECT volatile status is added when successful and checked by the engine
before executing the opponent's move.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.enums import VolatileStatus

if TYPE_CHECKING:
    from random import Random

    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState


def try_protect(
    ctx: TurnContext,
    user: PokemonBattleState,
    rng: Random,
) -> bool:
    """Attempt to use Protect/Detect. Returns True if it succeeds."""
    consecutive = user.volatile_data.get("protect_turns", 0)

    # Success chance: 1 / (2^consecutive) — first use always succeeds
    if consecutive > 0:
        chance = max(1, 2**consecutive)  # 2, 4, 8, ...
        if rng.randint(1, chance) != 1:
            user.volatile_data["protect_turns"] = 0
            ctx.log.append("But it failed!")
            return False

    user.volatile_statuses.add(VolatileStatus.PROTECT)
    user.volatile_data["protect_turns"] = consecutive + 1
    ctx.log.append(f"{user.name} protected itself!")
    return True

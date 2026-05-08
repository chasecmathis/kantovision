from __future__ import annotations

import asyncio
import logging

from pydantic import ValidationError

from app.battle.state import BattleState, MoveSlot, PokemonBattleState, StoredSlot
from app.battle.stats import calc_stat
from app.database import get_db
from app.repositories import move_repo

logger = logging.getLogger(__name__)


async def build_pokemon(slot: StoredSlot) -> PokemonBattleState:
    b = slot.base_stats
    iv = slot.ivs
    ev = slot.evs
    nature = (slot.nature or "").lower()

    move_names = [n for n in slot.move_names if n]
    if move_names:
        move_rows = await asyncio.to_thread(move_repo.get_moves_bulk, get_db(), move_names)
        moves = [move_repo.to_move_slot(row) for name in move_names if (row := move_rows.get(name))]
    else:
        moves = []

    if not moves:
        moves = [
            MoveSlot(
                name="struggle",
                power=50,
                accuracy=100,
                max_pp=1,
                current_pp=1,
                type="normal",
                category="physical",
            )
        ]

    hp_stat = calc_stat(b.hp, iv.hp, ev.hp, is_hp=True)
    return PokemonBattleState(
        species_id=slot.pokemon_id,
        name=slot.species_name or f"#{slot.pokemon_id}",
        current_hp=hp_stat,
        max_hp=hp_stat,
        attack=calc_stat(b.attack, iv.attack, ev.attack, nature=nature, stat_name="attack"),
        defense=calc_stat(b.defense, iv.defense, ev.defense, nature=nature, stat_name="defense"),
        special_attack=calc_stat(
            b.special_attack,
            iv.special_attack,
            ev.special_attack,
            nature=nature,
            stat_name="special_attack",
        ),
        special_defense=calc_stat(
            b.special_defense,
            iv.special_defense,
            ev.special_defense,
            nature=nature,
            stat_name="special_defense",
        ),
        speed=calc_stat(b.speed, iv.speed, ev.speed, nature=nature, stat_name="speed"),
        types=slot.types or ["normal"],
        moves=moves,
        ability=(slot.ability or "").lower(),
        item=(slot.item or "").lower(),
        nature=nature,
    )


async def fetch_team(team_id: str, user_id: str) -> list[PokemonBattleState]:
    result = await asyncio.to_thread(
        lambda: (
            get_db()
            .table("teams")
            .select("slots")
            .eq("id", team_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    )
    slots_raw: list = (result.data or {}).get("slots", [])

    mons: list[PokemonBattleState] = []
    for raw in slots_raw:
        if raw is None:
            continue
        try:
            slot = StoredSlot(**raw)
            mons.append(await build_pokemon(slot))
        except (ValidationError, ValueError) as exc:
            logger.warning(
                "Skipping invalid slot in team %s: %s — %r", team_id, type(exc).__name__, exc
            )
            continue

    if not mons:
        raise ValueError(f"No valid Pokémon found in team {team_id}")
    return mons


async def save_result(state: BattleState) -> None:
    try:
        await asyncio.to_thread(
            lambda: (
                get_db()
                .table("battles")
                .insert(
                    {
                        "player1_id": state.player1.user_id,
                        "player2_id": state.player2.user_id,
                        "winner_id": state.winner_id,
                        "turns": state.turn,
                    }
                )
                .execute()
            )
        )
    except Exception:
        logger.exception("Failed to persist battle result for battle_id=%s", state.id)

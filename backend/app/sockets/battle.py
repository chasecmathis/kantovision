from __future__ import annotations

import asyncio
from typing import Annotated

import httpx
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.battle.engine import resolve_turn
from app.battle.manager import (
    create_battle,
    get_battle,
    get_battle_by_user,
    remove_battle,
    submit_move,
    update_battle,
)
from app.battle.matchmaking import dequeue, enqueue, try_match
from app.battle.state import BattleState, MoveSlot, PlayerState, PokemonBattleState, StoredSlot
from app.database import get_db
from app.sockets.connections import manager

router = APIRouter(tags=["battle-ws"])

# ─── HTTP client + move cache ─────────────────────────────────────────────────

_http = httpx.AsyncClient(timeout=10.0)
_move_cache: dict[str, MoveSlot] = {}


async def _fetch_move(name: str) -> MoveSlot:
    if name in _move_cache:
        return _move_cache[name]
    try:
        resp = await _http.get(f"https://pokeapi.co/api/v2/move/{name}")
        if resp.status_code == 200:
            d = resp.json()
            move = MoveSlot(
                name=d["name"],
                power=d.get("power") or 50,
                accuracy=d.get("accuracy") or 100,
                pp=d.get("pp") or 20,
                type=d["type"]["name"],
                category=d["damage_class"]["name"],
            )
            _move_cache[name] = move
            return move
    except Exception:
        pass
    fallback = MoveSlot(name=name, power=50, accuracy=100, pp=20, type="normal", category="physical")
    _move_cache[name] = fallback
    return fallback


# ─── Stat calculation (level 50) ─────────────────────────────────────────────

def _stat(base: int, iv: int, ev: int, *, is_hp: bool = False) -> int:
    inner = (2 * base + iv + ev // 4) * 50 // 100
    return inner + 60 if is_hp else inner + 5


async def _build_pokemon(slot: StoredSlot) -> PokemonBattleState:
    b = slot.base_stats
    iv = slot.ivs
    ev = slot.evs

    moves = [await _fetch_move(n) for n in slot.move_names if n]
    if not moves:
        moves = [MoveSlot(name="struggle", power=50, accuracy=100, pp=1, type="normal", category="physical")]

    return PokemonBattleState(
        species_id=slot.pokemon_id,
        name=slot.species_name or f"#{slot.pokemon_id}",
        current_hp=_stat(b.get("hp", 45), iv.get("hp", 31), ev.get("hp", 0), is_hp=True),
        max_hp=_stat(b.get("hp", 45), iv.get("hp", 31), ev.get("hp", 0), is_hp=True),
        attack=_stat(b.get("attack", 45), iv.get("attack", 31), ev.get("attack", 0)),
        defense=_stat(b.get("defense", 45), iv.get("defense", 31), ev.get("defense", 0)),
        # base_stats uses "special-attack" (PokéAPI hyphen); evs/ivs use "special_attack" (underscore)
        special_attack=_stat(
            b.get("special-attack", 45), iv.get("special_attack", 31), ev.get("special_attack", 0)
        ),
        special_defense=_stat(
            b.get("special-defense", 45), iv.get("special_defense", 31), ev.get("special_defense", 0)
        ),
        speed=_stat(b.get("speed", 45), iv.get("speed", 31), ev.get("speed", 0)),
        types=slot.types or ["normal"],
        moves=moves,
    )


async def _fetch_team(team_id: str, user_id: str) -> list[PokemonBattleState]:
    result = await asyncio.to_thread(
        lambda: get_db()
        .table("teams")
        .select("slots")
        .eq("id", team_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    slots_raw: list = (result.data or {}).get("slots", [])

    mons: list[PokemonBattleState] = []
    for raw in slots_raw:
        if raw is None:
            continue
        try:
            slot = StoredSlot(**raw)
            mons.append(await _build_pokemon(slot))
        except Exception:
            continue

    if not mons:
        raise ValueError(f"No valid Pokémon found in team {team_id}")
    return mons


# ─── State serialization ──────────────────────────────────────────────────────

def _ser_state(state: BattleState) -> dict:
    def ser_move(m: MoveSlot) -> dict:
        return {"name": m.name, "power": m.power, "accuracy": m.accuracy,
                "pp": m.pp, "type": m.type, "category": m.category}

    def ser_mon(m: PokemonBattleState) -> dict:
        return {
            "species_id": m.species_id, "name": m.name,
            "current_hp": m.current_hp, "max_hp": m.max_hp,
            "attack": m.attack, "defense": m.defense,
            "special_attack": m.special_attack, "special_defense": m.special_defense,
            "speed": m.speed, "types": m.types,
            "moves": [ser_move(mv) for mv in m.moves],
            "fainted": m.fainted,
        }

    def ser_player(p: PlayerState) -> dict:
        return {"user_id": p.user_id, "active_index": p.active_index,
                "team": [ser_mon(m) for m in p.team]}

    return {
        "id": state.id,
        "player1": ser_player(state.player1),
        "player2": ser_player(state.player2),
        "turn": state.turn,
        "status": state.status,
        "winner_id": state.winner_id,
        "log": state.log[-30:],
    }


# ─── Battle result persistence ────────────────────────────────────────────────

async def _save_result(state: BattleState) -> None:
    try:
        await asyncio.to_thread(
            lambda: get_db().table("battles").insert({
                "player1_id": state.player1.user_id,
                "player2_id": state.player2.user_id,
                "winner_id": state.winner_id,
                "turns": state.turn,
            }).execute()
        )
    except Exception:
        pass


# ─── Message handlers ─────────────────────────────────────────────────────────

async def _handle_join_queue(user_id: str, data: dict) -> None:
    team_id = data.get("team_id")
    if not team_id:
        await manager.send_to_user(user_id, {"type": "error", "message": "team_id required"})
        return

    enqueue(user_id, team_id)
    match = try_match()

    if match is None:
        await manager.send_to_user(user_id, {"type": "queue_joined"})
        return

    entry1, entry2 = match
    try:
        team1 = await _fetch_team(entry1.team_id, entry1.user_id)
        team2 = await _fetch_team(entry2.team_id, entry2.user_id)
    except Exception:
        # Re-queue both players on failure
        enqueue(entry1.user_id, entry1.team_id)
        enqueue(entry2.user_id, entry2.team_id)
        for uid in [entry1.user_id, entry2.user_id]:
            await manager.send_to_user(uid, {"type": "error", "message": "Failed to load team data"})
        return

    state = create_battle(entry1, entry2, team1, team2)
    await manager.join_room(state.id, entry1.user_id)
    await manager.join_room(state.id, entry2.user_id)

    for uid, opp in [(entry1.user_id, entry2.user_id), (entry2.user_id, entry1.user_id)]:
        await manager.send_to_user(uid, {
            "type": "match_found",
            "battle_id": state.id,
            "opponent_id": opp,
        })

    await manager.broadcast_to_room(state.id, {
        "type": "battle_start",
        "battle_id": state.id,
        "state": _ser_state(state),
    })


async def _handle_leave_queue(user_id: str) -> None:
    dequeue(user_id)
    await manager.send_to_user(user_id, {"type": "queue_left"})


async def _handle_make_move(user_id: str, data: dict) -> None:
    battle_id = data.get("battle_id")
    move_slot = data.get("move_slot")

    if not battle_id or move_slot is None:
        await manager.send_to_user(user_id, {"type": "error", "message": "battle_id and move_slot required"})
        return

    state = get_battle(battle_id)
    if not state or state.status != "active":
        await manager.send_to_user(user_id, {"type": "error", "message": "Battle not found or already ended"})
        return

    # Ignore duplicate moves from the same player
    if user_id in state.pending_moves:
        return

    both_ready = submit_move(battle_id, user_id, int(move_slot))

    if not both_ready:
        await manager.broadcast_to_room(battle_id, {"type": "move_received", "user_id": user_id})
        return

    # Both moves are in — resolve the turn
    state = get_battle(battle_id)  # re-fetch after mutation
    if not state:
        return

    p1_move = state.pending_moves.get(state.player1.user_id, 0)
    p2_move = state.pending_moves.get(state.player2.user_id, 0)

    result = resolve_turn(state, p1_move, p2_move)
    update_battle(result.new_state)

    await manager.broadcast_to_room(battle_id, {
        "type": "turn_result",
        "log": result.log_entries,
        "state": _ser_state(result.new_state),
    })

    if result.battle_over:
        await manager.broadcast_to_room(battle_id, {
            "type": "battle_end",
            "winner_id": result.winner_id,
            "reason": "all_fainted",
        })
        await _save_result(result.new_state)
        await manager.leave_room(battle_id)
        remove_battle(battle_id)


async def _handle_forfeit(user_id: str, data: dict) -> None:
    battle_id = data.get("battle_id")
    if not battle_id:
        return

    state = get_battle(battle_id)
    if not state or state.status != "active":
        return

    winner_id = (
        state.player2.user_id if user_id == state.player1.user_id else state.player1.user_id
    )
    state.status = "ended"
    state.winner_id = winner_id

    await manager.broadcast_to_room(battle_id, {
        "type": "battle_end",
        "winner_id": winner_id,
        "reason": "forfeit",
    })
    await _save_result(state)
    await manager.leave_room(battle_id)
    remove_battle(battle_id)


async def _handle_disconnect_forfeit(user_id: str) -> None:
    state = get_battle_by_user(user_id)
    if state and state.status == "active":
        await _handle_forfeit(user_id, {"battle_id": state.id})


# ─── WebSocket endpoint ───────────────────────────────────────────────────────

@router.websocket("/ws/battle")
async def battle_ws(
    ws: WebSocket,
    token: Annotated[str, Query()],
) -> None:
    # Verify JWT before accepting the connection
    try:
        user_response = await asyncio.to_thread(lambda: get_db().auth.get_user(token))
        if not user_response.user:
            await ws.close(code=4001, reason="Unauthorized")
            return
        user_id: str = user_response.user.id
    except Exception:
        await ws.close(code=4001, reason="Unauthorized")
        return

    await ws.accept()
    await manager.connect(ws, user_id)

    # Automatically rejoin any in-progress battle (e.g. after page refresh)
    existing = get_battle_by_user(user_id)
    if existing:
        await manager.join_room(existing.id, user_id)
        await manager.send_to_user(user_id, {
            "type": "battle_start",
            "battle_id": existing.id,
            "state": _ser_state(existing),
        })

    try:
        while True:
            try:
                data = await ws.receive_json()
            except Exception:
                break

            match data.get("type"):
                case "join_queue":
                    await _handle_join_queue(user_id, data)
                case "leave_queue":
                    await _handle_leave_queue(user_id)
                case "make_move":
                    await _handle_make_move(user_id, data)
                case "forfeit":
                    await _handle_forfeit(user_id, data)
                case unknown:
                    await manager.send_to_user(user_id, {
                        "type": "error",
                        "message": f"Unknown message type: {unknown!r}",
                    })
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user_id)
        await _handle_disconnect_forfeit(user_id)

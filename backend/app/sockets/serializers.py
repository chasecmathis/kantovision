"""Battle state serialization for WebSocket transport."""

from __future__ import annotations

from app.battle.state import BattleState, MoveSlot, PlayerState, PokemonBattleState


def _ser_move(m: MoveSlot) -> dict:
    return {
        "name": m.name,
        "power": m.power,
        "accuracy": m.accuracy,
        "pp": m.pp,
        "type": m.type,
        "category": m.category,
    }


def _ser_mon(m: PokemonBattleState) -> dict:
    return {
        "species_id": m.species_id,
        "name": m.name,
        "current_hp": m.current_hp,
        "max_hp": m.max_hp,
        "attack": m.attack,
        "defense": m.defense,
        "special_attack": m.special_attack,
        "special_defense": m.special_defense,
        "speed": m.speed,
        "types": m.types,
        "moves": [_ser_move(mv) for mv in m.moves],
        "fainted": m.fainted,
    }


def _ser_player(p: PlayerState) -> dict:
    return {
        "user_id": p.user_id,
        "active_index": p.active_index,
        "team": [_ser_mon(m) for m in p.team],
    }


def serialize_battle_state(state: BattleState) -> dict:
    """Serialize a BattleState into a dict suitable for JSON transport."""
    return {
        "id": state.id,
        "player1": _ser_player(state.player1),
        "player2": _ser_player(state.player2),
        "turn": state.turn,
        "status": state.status,
        "winner_id": state.winner_id,
        "log": state.log[-30:],
    }

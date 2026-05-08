"""Battle state serialization for WebSocket transport."""

from __future__ import annotations

from app.battle.state import BattleState, MoveSlot, PlayerState, PokemonBattleState


def _ser_move(m: MoveSlot) -> dict:
    return {
        "name": m.name,
        "power": m.power,
        "accuracy": m.accuracy,
        "max_pp": m.max_pp,
        "current_pp": m.current_pp,
        "type": m.type,
        "category": m.category,
        "priority": m.priority,
        "flags": m.flags,
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
        "ability": m.ability,
        "item": m.item,
        "nature": m.nature,
        "status": m.status,
        "stat_stages": m.stat_stages.model_dump(),
        "volatile_statuses": sorted(m.volatile_statuses),
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
        "field": state.field.model_dump(),
        "side1": state.side1.model_dump(),
        "side2": state.side2.model_dump(),
        "awaiting_switch": sorted(state.awaiting_switch),
    }

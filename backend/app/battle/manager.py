from __future__ import annotations

import uuid

from app.battle.matchmaking import QueueEntry
from app.battle.state import BattleState, PlayerState, PokemonBattleState

_battles: dict[str, BattleState] = {}
_user_battle: dict[str, str] = {}  # user_id → battle_id


def create_battle(
    entry1: QueueEntry,
    entry2: QueueEntry,
    team1: list[PokemonBattleState],
    team2: list[PokemonBattleState],
) -> BattleState:
    battle_id = str(uuid.uuid4())
    state = BattleState(
        id=battle_id,
        player1=PlayerState(user_id=entry1.user_id, team=team1),
        player2=PlayerState(user_id=entry2.user_id, team=team2),
    )
    _battles[battle_id] = state
    _user_battle[entry1.user_id] = battle_id
    _user_battle[entry2.user_id] = battle_id
    return state


def get_battle(battle_id: str) -> BattleState | None:
    return _battles.get(battle_id)


def get_battle_by_user(user_id: str) -> BattleState | None:
    battle_id = _user_battle.get(user_id)
    return _battles.get(battle_id) if battle_id else None


def update_battle(state: BattleState) -> None:
    _battles[state.id] = state


def remove_battle(battle_id: str) -> None:
    state = _battles.pop(battle_id, None)
    if state:
        _user_battle.pop(state.player1.user_id, None)
        _user_battle.pop(state.player2.user_id, None)


def submit_move(battle_id: str, user_id: str, move_slot: int) -> bool:
    """
    Record a player's chosen move slot.
    Returns True when both players have submitted and the turn is ready to resolve.
    """
    state = _battles.get(battle_id)
    if not state or state.status != "active":
        return False
    state.pending_moves[user_id] = move_slot
    return len(state.pending_moves) == 2

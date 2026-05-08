"""Battle action models — what a player can do on their turn."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ActionType(StrEnum):
    MOVE = "move"
    SWITCH = "switch"


class Action(BaseModel):
    type: ActionType
    player_id: str


class MoveAction(Action):
    type: ActionType = ActionType.MOVE
    move_index: int


class SwitchAction(Action):
    type: ActionType = ActionType.SWITCH
    switch_to_index: int

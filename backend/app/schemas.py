from typing import Annotated

from pydantic import BaseModel, Field


class EVSpread(BaseModel):
    hp: int = 0
    attack: int = 0
    defense: int = 0
    special_attack: int = 0
    special_defense: int = 0
    speed: int = 0


class IVSpread(BaseModel):
    hp: Annotated[int, Field(ge=0, le=31)] = 31
    attack: Annotated[int, Field(ge=0, le=31)] = 31
    defense: Annotated[int, Field(ge=0, le=31)] = 31
    special_attack: Annotated[int, Field(ge=0, le=31)] = 31
    special_defense: Annotated[int, Field(ge=0, le=31)] = 31
    speed: Annotated[int, Field(ge=0, le=31)] = 31

class BaseStats(BaseModel):
    hp: Annotated[int, Field(ge=1, le=255)] = 45
    attack: Annotated[int, Field(ge=1, le=255)] = 45
    defense: Annotated[int, Field(ge=1, le=255)] = 45
    special_attack: Annotated[int, Field(ge=1, le=255)] = 45 
    special_defense: Annotated[int, Field(ge=1, le=255)] = 45
    speed: Annotated[int, Field(ge=1, le=255)] = 45


class SerializedSlot(BaseModel):
    pokemon_id: int
    species_name: str = ""
    ability: str
    types: Annotated[list[str], Field(max_length=2)] = []
    nature: str | None = None
    item_name: str | None = None
    move_names: list[str | None]
    base_stats: BaseStats = Field(default_factory=EVSpread) 
    evs: EVSpread
    ivs: IVSpread = Field(default_factory=IVSpread)


class SaveTeamRequest(BaseModel):
    name: str
    slots: Annotated[list[SerializedSlot | None], Field(max_length=6)]


class TeamRow(BaseModel):
    id: str
    name: str
    slots: list[SerializedSlot | None]
    created_at: str
    updated_at: str


# ─── Battles ──────────────────────────────────────────────────────────────────

class BattleRow(BaseModel):
    id: str
    player1_id: str
    player2_id: str
    winner_id: str | None = None
    turns: int
    created_at: str


class BattleHistoryItem(BaseModel):
    id: str
    player1_id: str
    player2_id: str
    player1_username: str | None = None
    player2_username: str | None = None
    winner_id: str | None = None
    turns: int
    created_at: str


# ─── Profiles ─────────────────────────────────────────────────────────────────

class ProfileRow(BaseModel):
    id: str
    username: str
    display_name: str | None = None
    created_at: str


class CreateProfileRequest(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")]
    display_name: str | None = None


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas import BaseStats, EVSpread, IVSpread


class BattleStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class MoveSlot(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    power: int
    accuracy: int
    pp: int
    type: str
    category: str  # "physical" | "special" | "status"


class PokemonBattleState(BaseModel):
    species_id: int
    name: str
    current_hp: int
    max_hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    types: list[str]
    moves: list[MoveSlot]
    fainted: bool = False


class PlayerState(BaseModel):
    user_id: str
    team: list[PokemonBattleState]
    active_index: int = 0

    @property
    def active(self) -> PokemonBattleState:
        return self.team[self.active_index]


class BattleState(BaseModel):
    id: str
    player1: PlayerState
    player2: PlayerState
    turn: int = 1
    status: BattleStatus = BattleStatus.ACTIVE
    pending_moves: dict[str, int] = Field(default_factory=dict)
    winner_id: str | None = None
    log: list[str] = Field(default_factory=list)


# ─── DB-stored team slot format (matches frontend serialization) ───────────────


class StoredSlot(BaseModel):
    """Mirrors what the frontend serializes when saving a team to Supabase."""

    pokemon_id: int
    species_name: str = ""
    types: list[str] = []
    base_stats: BaseStats = Field(default_factory=BaseStats)
    ability: str = ""
    nature: str | None = None
    item: str | None = None
    move_names: list[str | None] = []
    evs: EVSpread = Field(default_factory=EVSpread)
    ivs: IVSpread = Field(default_factory=IVSpread)

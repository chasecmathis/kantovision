"""Battle state data models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.battle.enums import StatusCondition, Terrain, VolatileStatus, Weather
from app.schemas import BaseStats, EVSpread, IVSpread


class BattleStatus(StrEnum):
    TEAM_PREVIEW = "team_preview"
    ACTIVE = "active"
    ENDED = "ended"


# ─── Move ────────────────────────────────────────────────────────────────────


class MoveSlot(BaseModel):
    name: str
    power: int | None
    accuracy: int | None
    max_pp: int
    current_pp: int
    type: str
    category: str  # "physical" | "special" | "status"
    priority: int = 0
    effect_id: str = ""
    effect_chance: int = 0
    flags: list[str] = Field(default_factory=list)


STRUGGLE = MoveSlot(
    name="Struggle",
    power=50,
    accuracy=0,  # never misses
    max_pp=1,
    current_pp=1,
    type="normal",
    category="physical",
)


# ─── Stat stages ─────────────────────────────────────────────────────────────


class StatStages(BaseModel):
    attack: int = 0
    defense: int = 0
    special_attack: int = 0
    special_defense: int = 0
    speed: int = 0
    accuracy: int = 0
    evasion: int = 0


# ─── Pokemon battle state ────────────────────────────────────────────────────


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

    ability: str = ""
    item: str = ""
    nature: str = ""

    status: StatusCondition = StatusCondition.NONE
    status_turns: int = 0
    stat_stages: StatStages = Field(default_factory=StatStages)
    volatile_statuses: set[VolatileStatus] = Field(default_factory=set)
    volatile_data: dict[str, int] = Field(default_factory=dict)
    last_move_used: str | None = None
    item_consumed: bool = False


# ─── Player state ────────────────────────────────────────────────────────────


class PlayerState(BaseModel):
    user_id: str
    team: list[PokemonBattleState]
    active_index: int = 0

    @property
    def active(self) -> PokemonBattleState:
        return self.team[self.active_index]


# ─── Field & side state ─────────────────────────────────────────────────────


class SideState(BaseModel):
    stealth_rock: bool = False
    spikes: int = 0
    toxic_spikes: int = 0
    sticky_web: bool = False
    reflect: int = 0
    light_screen: int = 0
    tailwind: int = 0


class FieldState(BaseModel):
    weather: Weather = Weather.NONE
    weather_turns: int = 0
    terrain: Terrain = Terrain.NONE
    terrain_turns: int = 0
    trick_room: int = 0


# ─── Battle state ────────────────────────────────────────────────────────────


class BattleState(BaseModel):
    id: str
    player1: PlayerState
    player2: PlayerState
    turn: int = 1
    status: BattleStatus = BattleStatus.ACTIVE
    pending_actions: dict[str, dict] = Field(default_factory=dict)
    winner_id: str | None = None
    log: list[str] = Field(default_factory=list)

    field: FieldState = Field(default_factory=FieldState)
    side1: SideState = Field(default_factory=SideState)
    side2: SideState = Field(default_factory=SideState)

    # Forced switch: user_ids of players who need to pick a replacement
    awaiting_switch: set[str] = Field(default_factory=set)
    # Lead selection: user_id → selected lead index
    lead_selections: dict[str, int] = Field(default_factory=dict)


# ─── DB-stored team slot format (matches frontend serialization) ─────────────


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

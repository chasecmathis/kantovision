from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass
class MoveSlot:
    name: str
    power: int
    accuracy: int
    pp: int
    type: str
    category: str  # "physical" | "special" | "status"


@dataclass
class PokemonBattleState:
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


@dataclass
class PlayerState:
    user_id: str
    team: list[PokemonBattleState]
    active_index: int = 0

    @property
    def active(self) -> PokemonBattleState:
        return self.team[self.active_index]


@dataclass
class BattleState:
    id: str
    player1: PlayerState
    player2: PlayerState
    turn: int = 1
    status: str = "active"  # "active" | "ended"
    pending_moves: dict[str, int] = field(default_factory=dict)
    winner_id: str | None = None
    log: list[str] = field(default_factory=list)


# ─── DB-stored team slot format (matches frontend serialization) ───────────────


class StoredSlot(BaseModel):
    """Mirrors what the frontend serializes when saving a team to Supabase."""

    pokemon_id: int
    species_name: str = ""
    types: list[str] = []
    base_stats: dict[str, int] = {}
    ability: str = ""
    nature: str | None = None
    item: str | None = None
    move_names: list[str | None] = []
    evs: dict[str, int] = {}
    ivs: dict[str, int] = {}

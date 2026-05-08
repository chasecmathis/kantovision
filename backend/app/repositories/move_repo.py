from __future__ import annotations

from pydantic import BaseModel
from supabase import Client

from app.battle.state import MoveSlot


class MoveRow(BaseModel):
    id: int
    name: str
    power: int | None = None
    accuracy: int | None = None
    pp: int
    type: str
    damage_class: str
    flavor_text: str | None = None


def to_move_slot(row: MoveRow) -> MoveSlot:
    """Convert a MoveRow to a MoveSlot for use in the battle engine."""
    pp = row.pp
    return MoveSlot(
        name=row.name,
        power=row.power,
        accuracy=row.accuracy,
        max_pp=pp,
        current_pp=pp,
        type=row.type,
        category=row.damage_class,
    )


def get_move(db: Client, name: str) -> MoveRow | None:
    result = db.table("moves").select("*").eq("name", name).maybe_single().execute()
    if not result.data:
        return None
    return MoveRow.model_validate(result.data)


def get_moves_bulk(db: Client, names: list[str]) -> dict[str, MoveRow]:
    """Fetch multiple moves by name in a single query. Returns a dict keyed by name."""
    if not names:
        return {}
    result = db.table("moves").select("*").in_("name", names).execute()
    return {d["name"]: MoveRow.model_validate(d) for d in (result.data or [])}

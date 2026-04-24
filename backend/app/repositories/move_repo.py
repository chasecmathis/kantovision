from __future__ import annotations

from dataclasses import dataclass

from supabase import Client

from app.battle.state import MoveSlot


@dataclass
class MoveRow:
    id: int
    name: str
    power: int | None
    accuracy: int | None
    pp: int
    type: str
    damage_class: str
    flavor_text: str | None


def _row_to_move_row(d: dict) -> MoveRow:
    return MoveRow(
        id=d["id"],
        name=d["name"],
        power=d.get("power"),
        accuracy=d.get("accuracy"),
        pp=d["pp"],
        type=d["type"],
        damage_class=d["damage_class"],
        flavor_text=d.get("flavor_text"),
    )


def to_move_slot(row: MoveRow) -> MoveSlot:
    """Convert a MoveRow to a MoveSlot for use in the battle engine."""
    return MoveSlot(
        name=row.name,
        power=row.power or 50,
        accuracy=row.accuracy or 100,
        pp=row.pp,
        type=row.type,
        category=row.damage_class,
    )


def get_move(db: Client, name: str) -> MoveRow | None:
    result = db.table("moves").select("*").eq("name", name).maybe_single().execute()
    if not result.data:
        return None
    return _row_to_move_row(result.data)


def get_moves_bulk(db: Client, names: list[str]) -> dict[str, MoveRow]:
    """Fetch multiple moves by name in a single query. Returns a dict keyed by name."""
    if not names:
        return {}
    result = db.table("moves").select("*").in_("name", names).execute()
    return {d["name"]: _row_to_move_row(d) for d in (result.data or [])}

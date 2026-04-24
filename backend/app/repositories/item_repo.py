from __future__ import annotations

from dataclasses import dataclass

from supabase import Client


@dataclass
class ItemRow:
    id: int
    name: str
    sprite_url: str | None
    category: str | None
    flavor_text: str | None


def _row_to_item_row(d: dict) -> ItemRow:
    return ItemRow(
        id=d["id"],
        name=d["name"],
        sprite_url=d.get("sprite_url"),
        category=d.get("category"),
        flavor_text=d.get("flavor_text"),
    )


def get_item(db: Client, name: str) -> ItemRow | None:
    result = db.table("items").select("*").eq("name", name).maybe_single().execute()
    if not result.data:
        return None
    return _row_to_item_row(result.data)


def get_item_list(
    db: Client,
    *,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
) -> list[ItemRow]:
    query = db.table("items").select("id, name, sprite_url, category")
    if search:
        query = query.ilike("name", f"%{search}%")
    result = query.order("name").range(offset, offset + limit - 1).execute()
    return [_row_to_item_row(d) for d in (result.data or [])]

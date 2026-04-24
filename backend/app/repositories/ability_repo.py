from __future__ import annotations

from dataclasses import dataclass

from supabase import Client


@dataclass
class AbilityRow:
    name: str
    short_effect: str | None
    effect: str | None


def get_ability(db: Client, name: str) -> AbilityRow | None:
    result = db.table("abilities").select("*").eq("name", name).maybe_single().execute()
    if not result.data:
        return None
    d = result.data
    return AbilityRow(
        name=d["name"],
        short_effect=d.get("short_effect"),
        effect=d.get("effect"),
    )

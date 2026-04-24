from __future__ import annotations

from dataclasses import dataclass

from supabase import Client


@dataclass
class NatureRow:
    name: str
    increased_stat: str | None
    decreased_stat: str | None


def get_all_natures(db: Client) -> list[NatureRow]:
    result = db.table("natures").select("*").order("name").execute()
    return [
        NatureRow(
            name=d["name"],
            increased_stat=d.get("increased_stat"),
            decreased_stat=d.get("decreased_stat"),
        )
        for d in (result.data or [])
    ]

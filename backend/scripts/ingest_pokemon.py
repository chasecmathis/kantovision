"""
Populate the KantoVision Postgres database from PokéAPI.

Run:
    uv run python -m scripts.ingest_pokemon
    uv run python -m scripts.ingest_pokemon --env-file .env.local

Idempotent: uses ON CONFLICT upserts so it's safe to rerun.
Handles partial failures: errors on individual records are logged and skipped.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import sys
from typing import Any

import httpx
from dotenv import load_dotenv
from supabase import create_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

POKEAPI = "https://pokeapi.co/api/v2"
CONCURRENCY = 50  # max simultaneous requests
LOG_EVERY = 50    # log progress every N records

# Generation ID ranges (inclusive) per PokéAPI numbering
_GEN_RANGES = [
    (1, 151),    # Gen 1
    (152, 251),  # Gen 2
    (252, 386),  # Gen 3
    (387, 493),  # Gen 4
    (494, 649),  # Gen 5
    (650, 721),  # Gen 6
    (722, 809),  # Gen 7
    (810, 905),  # Gen 8
    (906, 1025), # Gen 9
]


def _generation(pokemon_id: int) -> int:
    for gen, (lo, hi) in enumerate(_GEN_RANGES, start=1):
        if lo <= pokemon_id <= hi:
            return gen
    return 9


def _clean_text(text: str | None) -> str | None:
    if text is None:
        return None
    return re.sub(r"[\x00-\x1f\x7f]", " ", text).strip()


def _english(entries: list[dict], text_key: str = "flavor_text") -> str | None:
    for e in reversed(entries):
        lang = (e.get("language") or {}).get("name")
        if lang == "en":
            return _clean_text(e.get(text_key))
    return None


def _flatten_chain(link: dict) -> list[dict]:
    """Recursively flatten a PokéAPI evolution chain link into [{id, name}]."""
    result: list[dict] = []

    def walk(node: dict) -> None:
        url = (node.get("species") or {}).get("url", "")
        parts = [p for p in url.split("/") if p]
        if parts:
            try:
                evo_id = int(parts[-1])
                result.append({"id": evo_id, "name": node["species"]["name"]})
            except (ValueError, KeyError):
                pass
        for child in node.get("evolves_to", []):
            walk(child)

    walk(link)
    return result


# ─── Async fetch helpers ──────────────────────────────────────────────────────

async def _get(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str) -> dict | None:
    async with sem:
        try:
            resp = await client.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("GET %s failed: %s", url, exc)
            return None


async def _get_list(client: httpx.AsyncClient, sem: asyncio.Semaphore, endpoint: str, limit: int) -> list[dict]:
    data = await _get(client, sem, f"{POKEAPI}/{endpoint}?limit={limit}&offset=0")
    return (data or {}).get("results", [])


# ─── Domain ingestion functions ───────────────────────────────────────────────

async def ingest_moves(client: httpx.AsyncClient, sem: asyncio.Semaphore, db: Any) -> None:
    logger.info("Fetching move list…")
    items = await _get_list(client, sem, "move", 1000)
    logger.info("Ingesting %d moves…", len(items))

    async def process(item: dict) -> dict | None:
        data = await _get(client, sem, item["url"])
        if not data:
            return None
        flavor = _english(data.get("flavor_text_entries", []))
        return {
            "id": data["id"],
            "name": data["name"],
            "power": data.get("power"),
            "accuracy": data.get("accuracy"),
            "pp": data.get("pp") or 1,
            "type": (data.get("type") or {}).get("name", "normal"),
            "damage_class": (data.get("damage_class") or {}).get("name", "physical"),
            "flavor_text": flavor,
        }

    rows = await _gather(process, items)
    _upsert_batch(db, "moves", rows, LOG_EVERY)
    logger.info("Moves done.")


async def ingest_abilities(client: httpx.AsyncClient, sem: asyncio.Semaphore, db: Any) -> None:
    logger.info("Fetching ability list…")
    items = await _get_list(client, sem, "ability", 400)
    logger.info("Ingesting %d abilities…", len(items))

    async def process(item: dict) -> dict | None:
        data = await _get(client, sem, item["url"])
        if not data:
            return None
        effects = data.get("effect_entries", [])
        short = next((e["short_effect"] for e in effects if (e.get("language") or {}).get("name") == "en"), None)
        long_ = next((e["effect"] for e in effects if (e.get("language") or {}).get("name") == "en"), None)
        return {
            "name": data["name"],
            "short_effect": _clean_text(short),
            "effect": _clean_text(long_),
        }

    rows = await _gather(process, items)
    _upsert_batch(db, "abilities", rows, LOG_EVERY, conflict_col="name")
    logger.info("Abilities done.")


async def ingest_natures(client: httpx.AsyncClient, sem: asyncio.Semaphore, db: Any) -> None:
    logger.info("Ingesting natures…")
    items = await _get_list(client, sem, "nature", 30)

    async def process(item: dict) -> dict | None:
        data = await _get(client, sem, item["url"])
        if not data:
            return None
        return {
            "name": data["name"],
            "increased_stat": (data.get("increased_stat") or {}).get("name"),
            "decreased_stat": (data.get("decreased_stat") or {}).get("name"),
        }

    rows = await _gather(process, items)
    _upsert_batch(db, "natures", rows, LOG_EVERY, conflict_col="name")
    logger.info("Natures done.")


async def ingest_items(client: httpx.AsyncClient, sem: asyncio.Semaphore, db: Any) -> None:
    logger.info("Fetching item list…")
    items = await _get_list(client, sem, "item", 2200)
    logger.info("Ingesting %d items…", len(items))

    async def process(item: dict) -> dict | None:
        data = await _get(client, sem, item["url"])
        if not data:
            return None
        flavor = _english(data.get("flavor_text_entries", []), text_key="text")
        sprite = (data.get("sprites") or {}).get("default")
        return {
            "id": data["id"],
            "name": data["name"],
            "sprite_url": sprite,
            "category": (data.get("category") or {}).get("name"),
            "flavor_text": flavor,
        }

    rows = await _gather(process, items)
    _upsert_batch(db, "items", rows, LOG_EVERY)
    logger.info("Items done.")


async def ingest_pokemon(client: httpx.AsyncClient, sem: asyncio.Semaphore, db: Any) -> None:
    logger.info("Fetching pokemon list…")
    items = await _get_list(client, sem, "pokemon", 1100)
    logger.info("Ingesting %d pokemon…", len(items))

    # Track evolution chains to avoid re-fetching
    seen_chains: dict[int, list[dict]] = {}

    async def process(item: dict) -> dict | None:
        url = item["url"]
        parts = [p for p in url.split("/") if p]
        try:
            poke_id = int(parts[-1])
        except (ValueError, IndexError):
            return None

        poke = await _get(client, sem, url)
        if not poke:
            return None

        # Fetch species for lore + evolution chain
        species_url = (poke.get("species") or {}).get("url")
        species: dict = {}
        if species_url:
            species = await _get(client, sem, species_url) or {}

        # Extract base stats
        stat_map: dict[str, int] = {}
        for s in poke.get("stats", []):
            sname = (s.get("stat") or {}).get("name", "")
            stat_map[sname] = s.get("base_stat", 0)

        # Sprites
        sprites = poke.get("sprites") or {}
        oa = (sprites.get("other") or {}).get("official-artwork") or {}
        home = (sprites.get("other") or {}).get("home") or {}

        # Evolution chain
        evo_url = (species.get("evolution_chain") or {}).get("url")
        evo_id: int | None = None
        if evo_url:
            evo_parts = [p for p in evo_url.split("/") if p]
            try:
                evo_id = int(evo_parts[-1])
            except (ValueError, IndexError):
                pass

        if evo_id and evo_id not in seen_chains:
            evo_data = await _get(client, sem, evo_url)
            if evo_data:
                seen_chains[evo_id] = _flatten_chain(evo_data.get("chain", {}))

        return {
            "pokemon_row": {
                "id": poke_id,
                "name": poke["name"],
                "generation": _generation(poke_id),
                "height": poke.get("height"),
                "weight": poke.get("weight"),
                "base_experience": poke.get("base_experience"),
                "hp": stat_map.get("hp", 45),
                "attack": stat_map.get("attack", 45),
                "defense": stat_map.get("defense", 45),
                "special_attack": stat_map.get("special-attack", 45),
                "special_defense": stat_map.get("special-defense", 45),
                "speed": stat_map.get("speed", 45),
                "is_legendary": species.get("is_legendary", False),
                "is_mythical": species.get("is_mythical", False),
                "color": (species.get("color") or {}).get("name"),
                "capture_rate": species.get("capture_rate"),
                "base_happiness": species.get("base_happiness"),
                "flavor_text": _english(species.get("flavor_text_entries", [])),
                "genus": next(
                    (g["genus"] for g in species.get("genera", [])
                     if (g.get("language") or {}).get("name") == "en"),
                    None,
                ),
                "evolution_chain_id": evo_id,
                "sprite_front": sprites.get("front_default"),
                "sprite_official_artwork": oa.get("front_default"),
                "sprite_shiny": oa.get("front_shiny"),
                "sprite_home": home.get("front_default"),
            },
            "types": [
                {"pokemon_id": poke_id, "type_name": t["type"]["name"], "slot": t["slot"]}
                for t in poke.get("types", [])
            ],
            "abilities": [
                {"pokemon_id": poke_id, "ability_name": a["ability"]["name"],
                 "is_hidden": a["is_hidden"], "slot": a["slot"]}
                for a in poke.get("abilities", [])
            ],
            "moves": [
                {
                    "pokemon_id": poke_id,
                    "move_name": m["move"]["name"],
                    "learn_method": vgd["move_learn_method"]["name"],
                    "min_level": vgd.get("level_learned_at") or None,
                }
                for m in poke.get("moves", [])
                for vgd in m.get("version_group_details", [])[:1]  # take first version group
            ],
        }

    results = await _gather_raw(process, items)

    # Upsert evolution chains first (FK dependency)
    evo_rows = [{"id": eid, "chain": chain} for eid, chain in seen_chains.items()]
    if evo_rows:
        logger.info("Upserting %d evolution chains…", len(evo_rows))
        _upsert_batch(db, "evolution_chains", evo_rows, LOG_EVERY)

    # Upsert pokemon rows
    pokemon_rows = [r["pokemon_row"] for r in results if r]
    logger.info("Upserting %d pokemon rows…", len(pokemon_rows))
    _upsert_batch(db, "pokemon", pokemon_rows, LOG_EVERY)

    # Upsert types and abilities
    type_rows = [t for r in results if r for t in r["types"]]
    ability_rows = [a for r in results if r for a in r["abilities"]]
    logger.info("Upserting %d type slots…", len(type_rows))
    _upsert_batch(db, "pokemon_types", type_rows, LOG_EVERY, conflict_col="pokemon_id,slot")
    logger.info("Upserting %d ability slots…", len(ability_rows))
    _upsert_batch(db, "pokemon_abilities", ability_rows, LOG_EVERY, conflict_col="pokemon_id,slot")

    logger.info("Pokemon done.")
    return results


async def ingest_learnable_moves(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    db: Any,
    pokemon_results: list[dict],
) -> None:
    """Upsert pokemon_learnable_moves. Requires moves table to be populated first."""
    logger.info("Building learnable-move rows…")

    # Fetch all known move names from DB to validate FKs
    known_moves_result = db.table("moves").select("name").execute()
    known_moves = {r["name"] for r in (known_moves_result.data or [])}

    move_rows = []
    skipped = 0
    for r in pokemon_results:
        if not r:
            continue
        poke_id = r["pokemon_row"]["id"]
        seen_pairs: set[tuple] = set()
        for m in r["moves"]:
            move_name = m["move_name"]
            method = m["learn_method"]
            pair = (poke_id, move_name, method)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            if move_name not in known_moves:
                skipped += 1
                continue
            # Resolve move_id
            move_rows.append({
                "pokemon_id": poke_id,
                "move_name": move_name,  # resolved to id in batch below
                "learn_method": method,
                "min_level": m.get("min_level"),
            })

    if skipped:
        logger.warning("Skipped %d learnable moves with unknown names", skipped)

    # Resolve move names → ids
    move_name_result = db.table("moves").select("id, name").execute()
    name_to_id = {r["name"]: r["id"] for r in (move_name_result.data or [])}

    resolved_rows = []
    for r in move_rows:
        move_id = name_to_id.get(r["move_name"])
        if move_id:
            resolved_rows.append({
                "pokemon_id": r["pokemon_id"],
                "move_id": move_id,
                "learn_method": r["learn_method"],
                "min_level": r["min_level"],
            })

    logger.info("Upserting %d learnable-move rows…", len(resolved_rows))
    _upsert_batch(db, "pokemon_learnable_moves", resolved_rows, LOG_EVERY, conflict_col="pokemon_id,move_id,learn_method")
    logger.info("Learnable moves done.")


# ─── Batch helpers ────────────────────────────────────────────────────────────

async def _gather(fn, items: list[dict]) -> list[dict]:
    """Run fn(item) for each item, return non-None results."""
    results = await asyncio.gather(*[fn(item) for item in items], return_exceptions=True)
    out = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning("Item processing error: %s", r)
        elif r is not None:
            out.append(r)
    return out


async def _gather_raw(fn, items: list[dict]) -> list[dict | None]:
    """Like _gather but preserves None results for positional tracking."""
    results = await asyncio.gather(*[fn(item) for item in items], return_exceptions=True)
    out = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning("Item processing error: %s", r)
            out.append(None)
        else:
            out.append(r)
    return out


def _upsert_batch(db: Any, table: str, rows: list[dict], log_every: int, conflict_col: str = "id") -> None:
    """Upsert rows into a table in chunks of 500, logging progress."""
    if not rows:
        return
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        try:
            db.table(table).upsert(chunk, on_conflict=conflict_col).execute()
        except Exception as exc:
            logger.error("Upsert failed for table=%s offset=%d: %s", table, i, exc)
        if (i // chunk_size + 1) % (log_every // chunk_size + 1) == 0:
            logger.info("  %s: %d / %d", table, min(i + chunk_size, len(rows)), len(rows))
    logger.info("  %s: %d rows upserted", table, len(rows))


# ─── Entry point ─────────────────────────────────────────────────────────────

async def main(env_file: str) -> None:
    loaded = load_dotenv(env_file, override=True)
    if loaded:
        logger.info("Loaded env vars from %s", env_file)
    else:
        logger.warning("No .env file found at %s — falling back to existing environment", env_file)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set (checked %s)", env_file)
        sys.exit(1)

    db = create_client(supabase_url, supabase_key)
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=30) as client:
        # Dependency order: moves/abilities/natures/items first, then pokemon
        await ingest_moves(client, sem, db)
        await ingest_abilities(client, sem, db)
        await ingest_natures(client, sem, db)
        await ingest_items(client, sem, db)
        pokemon_results = await ingest_pokemon(client, sem, db)
        await ingest_learnable_moves(client, sem, db, pokemon_results)

    logger.info("Ingestion complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Pokémon data from PokéAPI into Supabase.")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a .env file to load (default: .env in the current directory)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.env_file))

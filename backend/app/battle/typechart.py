"""Type effectiveness chart and lookup (Gen VI+, 18 types including Fairy)."""

from __future__ import annotations

TYPE_CHART: dict[str, dict[str, float]] = {
    "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire": {
        "fire": 0.5,
        "water": 0.5,
        "rock": 0.5,
        "dragon": 0.5,
        "grass": 2.0,
        "ice": 2.0,
        "bug": 2.0,
        "steel": 2.0,
    },
    "water": {"water": 0.5, "grass": 0.5, "dragon": 0.5, "fire": 2.0, "ground": 2.0, "rock": 2.0},
    "electric": {
        "electric": 0.5,
        "grass": 0.5,
        "dragon": 0.5,
        "ground": 0.0,
        "water": 2.0,
        "flying": 2.0,
    },
    "grass": {
        "fire": 0.5,
        "grass": 0.5,
        "poison": 0.5,
        "flying": 0.5,
        "bug": 0.5,
        "dragon": 0.5,
        "steel": 0.5,
        "water": 2.0,
        "ground": 2.0,
        "rock": 2.0,
    },
    "ice": {
        "fire": 0.5,
        "water": 0.5,
        "ice": 0.5,
        "steel": 0.5,
        "grass": 2.0,
        "ground": 2.0,
        "flying": 2.0,
        "dragon": 2.0,
    },
    "fighting": {
        "poison": 0.5,
        "flying": 0.5,
        "psychic": 0.5,
        "bug": 0.5,
        "fairy": 0.5,
        "ghost": 0.0,
        "normal": 2.0,
        "ice": 2.0,
        "rock": 2.0,
        "dark": 2.0,
        "steel": 2.0,
    },
    "poison": {
        "poison": 0.5,
        "ground": 0.5,
        "rock": 0.5,
        "ghost": 0.5,
        "steel": 0.0,
        "grass": 2.0,
        "fairy": 2.0,
    },
    "ground": {
        "grass": 0.5,
        "bug": 0.5,
        "flying": 0.0,
        "fire": 2.0,
        "electric": 2.0,
        "poison": 2.0,
        "rock": 2.0,
        "steel": 2.0,
    },
    "flying": {
        "electric": 0.5,
        "rock": 0.5,
        "steel": 0.5,
        "grass": 2.0,
        "fighting": 2.0,
        "bug": 2.0,
    },
    "psychic": {"psychic": 0.5, "steel": 0.5, "dark": 0.0, "fighting": 2.0, "poison": 2.0},
    "bug": {
        "fire": 0.5,
        "fighting": 0.5,
        "poison": 0.5,
        "flying": 0.5,
        "ghost": 0.5,
        "steel": 0.5,
        "fairy": 0.5,
        "grass": 2.0,
        "psychic": 2.0,
        "dark": 2.0,
    },
    "rock": {
        "fighting": 0.5,
        "ground": 0.5,
        "steel": 0.5,
        "fire": 2.0,
        "ice": 2.0,
        "flying": 2.0,
        "bug": 2.0,
    },
    "ghost": {"normal": 0.0, "dark": 0.5, "psychic": 2.0, "ghost": 2.0},
    "dragon": {"steel": 0.5, "fairy": 0.0, "dragon": 2.0},
    "dark": {"fighting": 0.5, "dark": 0.5, "fairy": 0.5, "psychic": 2.0, "ghost": 2.0},
    "steel": {
        "fire": 0.5,
        "water": 0.5,
        "electric": 0.5,
        "steel": 0.5,
        "ice": 2.0,
        "rock": 2.0,
        "fairy": 2.0,
    },
    "fairy": {
        "fire": 0.5,
        "poison": 0.5,
        "steel": 0.5,
        "fighting": 2.0,
        "dragon": 2.0,
        "dark": 2.0,
    },
}


def get_type_effectiveness(attacking: str, defending_types: list[str]) -> float:
    """Calculate type effectiveness multiplier for an attack against defending types."""
    chart = TYPE_CHART.get(attacking, {})
    mult = 1.0
    for def_type in defending_types:
        mult *= chart.get(def_type, 1.0)
    return mult

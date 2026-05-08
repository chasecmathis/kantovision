"""Stat calculation helpers (Gen V+ formulas at Level 50)."""

from __future__ import annotations

# Nature modifiers: nature_name -> (increased_stat, decreased_stat)
# Neutral natures (e.g. hardy, docile) have no entry here.
NATURE_MODIFIERS: dict[str, tuple[str, str]] = {
    "lonely": ("attack", "defense"),
    "brave": ("attack", "speed"),
    "adamant": ("attack", "special_attack"),
    "naughty": ("attack", "special_defense"),
    "bold": ("defense", "attack"),
    "relaxed": ("defense", "speed"),
    "impish": ("defense", "special_attack"),
    "lax": ("defense", "special_defense"),
    "timid": ("speed", "attack"),
    "hasty": ("speed", "defense"),
    "jolly": ("speed", "special_attack"),
    "naive": ("speed", "special_defense"),
    "modest": ("special_attack", "attack"),
    "mild": ("special_attack", "defense"),
    "quiet": ("special_attack", "speed"),
    "rash": ("special_attack", "special_defense"),
    "calm": ("special_defense", "attack"),
    "gentle": ("special_defense", "defense"),
    "sassy": ("special_defense", "speed"),
    "careful": ("special_defense", "special_attack"),
}

NEUTRAL_NATURES = frozenset({"hardy", "docile", "serious", "bashful", "quirky"})


def get_nature_multiplier(nature: str, stat_name: str) -> float:
    """Return the nature multiplier (0.9, 1.0, or 1.1) for a given stat."""
    mod = NATURE_MODIFIERS.get(nature.lower())
    if mod is None:
        return 1.0
    increased, decreased = mod
    if stat_name == increased:
        return 1.1
    if stat_name == decreased:
        return 0.9
    return 1.0


def calc_stat(
    base: int,
    iv: int,
    ev: int,
    *,
    is_hp: bool = False,
    nature: str = "",
    stat_name: str = "",
) -> int:
    """Level-50 stat formula (Gen V+).

    HP:    floor((2*Base + IV + floor(EV/4)) * 50 / 100 + 50 + 10)
    Other: floor(((2*Base + IV + floor(EV/4)) * 50 / 100 + 5) * NatureMod)
    """
    inner = (2 * base + iv + ev // 4) * 50 // 100
    if is_hp:
        return inner + 50 + 10
    stat = inner + 5
    if nature and stat_name:
        stat = int(stat * get_nature_multiplier(nature, stat_name))
    return stat


# Stat stage multiplier table: stage -> multiplier as (numerator, denominator)
_STAGE_TABLE: dict[int, tuple[int, int]] = {
    -6: (2, 8),
    -5: (2, 7),
    -4: (2, 6),
    -3: (2, 5),
    -2: (2, 4),
    -1: (2, 3),
    0: (2, 2),
    1: (3, 2),
    2: (4, 2),
    3: (5, 2),
    4: (6, 2),
    5: (7, 2),
    6: (8, 2),
}

# Accuracy/evasion use a different table
_ACC_EVA_STAGE_TABLE: dict[int, tuple[int, int]] = {
    -6: (3, 9),
    -5: (3, 8),
    -4: (3, 7),
    -3: (3, 6),
    -2: (3, 5),
    -1: (3, 4),
    0: (3, 3),
    1: (4, 3),
    2: (5, 3),
    3: (6, 3),
    4: (7, 3),
    5: (8, 3),
    6: (9, 3),
}


def get_stat_stage_multiplier(stage: int, *, is_accuracy_evasion: bool = False) -> float:
    """Return the effective multiplier for a stat stage (-6 to +6)."""
    stage = max(-6, min(6, stage))
    table = _ACC_EVA_STAGE_TABLE if is_accuracy_evasion else _STAGE_TABLE
    num, den = table[stage]
    return num / den

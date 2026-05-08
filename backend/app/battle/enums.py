"""Battle-specific enumerations."""

from __future__ import annotations

from enum import StrEnum


class StatusCondition(StrEnum):
    NONE = "none"
    BURN = "burn"
    FREEZE = "freeze"
    PARALYSIS = "paralysis"
    POISON = "poison"
    TOXIC = "toxic"
    SLEEP = "sleep"


class VolatileStatus(StrEnum):
    CONFUSION = "confusion"
    FLINCH = "flinch"
    TAUNT = "taunt"
    ENCORE = "encore"
    PROTECT = "protect"
    SUBSTITUTE = "substitute"
    LEECH_SEED = "leech_seed"


class Weather(StrEnum):
    NONE = "none"
    SUN = "sun"
    RAIN = "rain"
    SANDSTORM = "sandstorm"
    HAIL = "hail"


class Terrain(StrEnum):
    NONE = "none"
    ELECTRIC = "electric"
    GRASSY = "grassy"
    PSYCHIC = "psychic"
    MISTY = "misty"


class StatEnum(StrEnum):
    ATTACK = "attack"
    DEFENSE = "defense"
    SPECIAL_ATTACK = "special_attack"
    SPECIAL_DEFENSE = "special_defense"
    SPEED = "speed"
    ACCURACY = "accuracy"
    EVASION = "evasion"

"""Global registries for battle effects.

Abilities, items, and move effects register themselves here on import.
The engine looks up effects by name at runtime.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from random import Random

    from app.battle.effects.base import AbilityEffect, ItemEffect, MoveEffectSpec
    from app.battle.pipeline import TurnContext
    from app.battle.state import PokemonBattleState

ABILITY_REGISTRY: dict[str, AbilityEffect] = {}
ITEM_REGISTRY: dict[str, ItemEffect] = {}
MOVE_EFFECT_REGISTRY: dict[str, MoveEffectSpec] = {}

# Custom move handlers for moves that need logic beyond MoveEffectSpec
# Signature: (ctx, attacker, defender, rng) -> None
CustomMoveHandler = Callable[
    ["TurnContext", "PokemonBattleState", "PokemonBattleState", "Random"], None
]
CUSTOM_MOVE_REGISTRY: dict[str, CustomMoveHandler] = {}


def register_ability(cls: type[AbilityEffect]) -> type[AbilityEffect]:
    """Class decorator that registers an ability effect."""
    instance = cls()
    ABILITY_REGISTRY[instance.name] = instance
    return cls


def register_item(cls: type[ItemEffect]) -> type[ItemEffect]:
    """Class decorator that registers an item effect."""
    instance = cls()
    ITEM_REGISTRY[instance.name] = instance
    return cls


def register_move_effect(name: str, spec: MoveEffectSpec) -> None:
    """Register a move effect spec by move name."""
    MOVE_EFFECT_REGISTRY[name] = spec


def register_custom_move(name: str, handler: CustomMoveHandler) -> None:
    """Register a custom move handler."""
    CUSTOM_MOVE_REGISTRY[name] = handler

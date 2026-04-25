"""Tests for app.repositories.pokemon_repo."""
from unittest.mock import MagicMock

from app.repositories.pokemon_repo import (
    EvolutionEntry,
    PokemonDetail,
    PokemonListRow,
    get_evolution_chain,
    get_pokemon,
    get_pokemon_list,
)


def _minimal_pokemon_row(pokemon_id: int = 1) -> dict:
    return {
        "id": pokemon_id,
        "name": "bulbasaur",
        "generation": 1,
        "height": 7,
        "weight": 69,
        "base_experience": 64,
        "hp": 45, "attack": 49, "defense": 49,
        "special_attack": 65, "special_defense": 65, "speed": 45,
        "is_legendary": False,
        "is_mythical": False,
        "color": "green",
        "capture_rate": 45,
        "base_happiness": 50,
        "flavor_text": "A strange seed was planted.",
        "genus": "Seed Pokémon",
        "evolution_chain_id": 1,
        "sprite_front": "https://example.com/front.png",
        "sprite_official_artwork": "https://example.com/artwork.png",
        "sprite_shiny": None,
        "sprite_home": None,
        "pokemon_types": [
            {"type_name": "grass", "slot": 1},
            {"type_name": "poison", "slot": 2},
        ],
        "pokemon_abilities": [
            {"ability_name": "overgrow", "is_hidden": False, "slot": 1},
            {"ability_name": "chlorophyll", "is_hidden": True, "slot": 3},
        ],
        "evolution_chains": {
            "chain": [
                {"id": 1, "name": "bulbasaur"},
                {"id": 2, "name": "ivysaur"},
                {"id": 3, "name": "venusaur"},
            ]
        },
        "pokemon_learnable_moves": [
            {"learn_method": "level-up", "min_level": 1, "moves": {"name": "tackle"}},
            {"learn_method": "machine", "min_level": None, "moves": {"name": "hyper-beam"}},
        ],
    }


def _make_single_db(data):
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.maybe_single.return_value = chain
    chain.execute.return_value = MagicMock(data=data)
    db = MagicMock()
    db.table.return_value = chain
    return db


def _make_list_db(data, type_data=None):
    """Mock DB that returns `data` for pokemon queries and `type_data` for pokemon_types queries."""
    type_data = type_data or []

    pokemon_chain = MagicMock()
    pokemon_chain.select.return_value = pokemon_chain
    pokemon_chain.eq.return_value = pokemon_chain
    pokemon_chain.in_.return_value = pokemon_chain
    pokemon_chain.order.return_value = pokemon_chain
    pokemon_chain.range.return_value = pokemon_chain
    pokemon_chain.execute.return_value = MagicMock(data=data)

    type_chain = MagicMock()
    type_chain.select.return_value = type_chain
    type_chain.eq.return_value = type_chain
    type_chain.execute.return_value = MagicMock(data=type_data)

    db = MagicMock()
    def _table(name):
        if name == "pokemon_types":
            return type_chain
        return pokemon_chain
    db.table.side_effect = _table
    return db


class TestGetPokemon:
    def test_returns_pokemon_detail_when_found(self):
        db = _make_single_db(_minimal_pokemon_row())
        result = get_pokemon(db, 1)
        assert result is not None
        assert isinstance(result, PokemonDetail)
        assert result.id == 1
        assert result.name == "bulbasaur"

    def test_returns_none_when_not_found(self):
        db = _make_single_db(None)
        result = get_pokemon(db, 9999)
        assert result is None

    def test_parses_types_sorted_by_slot(self):
        db = _make_single_db(_minimal_pokemon_row())
        result = get_pokemon(db, 1)
        assert result is not None
        assert len(result.types) == 2
        assert result.types[0].name == "grass"
        assert result.types[0].slot == 1
        assert result.types[1].name == "poison"

    def test_parses_stats(self):
        db = _make_single_db(_minimal_pokemon_row())
        result = get_pokemon(db, 1)
        assert result is not None
        assert result.stats.hp == 45
        assert result.stats.special_attack == 65
        assert result.stats.special_defense == 65

    def test_parses_evolution_chain(self):
        db = _make_single_db(_minimal_pokemon_row())
        result = get_pokemon(db, 1)
        assert result is not None
        assert len(result.evolution_chain) == 3
        assert result.evolution_chain[0].name == "bulbasaur"
        assert result.evolution_chain[2].id == 3

    def test_parses_learnable_moves(self):
        db = _make_single_db(_minimal_pokemon_row())
        result = get_pokemon(db, 1)
        assert result is not None
        move_names = {m.name for m in result.moves}
        assert "tackle" in move_names
        assert "hyper-beam" in move_names

    def test_parses_abilities(self):
        db = _make_single_db(_minimal_pokemon_row())
        result = get_pokemon(db, 1)
        assert result is not None
        hidden = [a for a in result.abilities if a.is_hidden]
        visible = [a for a in result.abilities if not a.is_hidden]
        assert len(hidden) == 1
        assert hidden[0].name == "chlorophyll"
        assert len(visible) == 1

    def test_handles_missing_evolution_chain(self):
        row = _minimal_pokemon_row()
        row["evolution_chains"] = None
        db = _make_single_db(row)
        result = get_pokemon(db, 1)
        assert result is not None
        assert result.evolution_chain == []

    def test_queries_pokemon_table(self):
        db = _make_single_db(_minimal_pokemon_row())
        get_pokemon(db, 1)
        db.table.assert_called_with("pokemon")


class TestGetPokemonList:
    def test_returns_list_of_rows(self):
        rows = [
            {
                "id": 1, "name": "bulbasaur", "generation": 1,
                "sprite_official_artwork": "https://example.com/1.png",
                "pokemon_types": [{"type_name": "grass", "slot": 1}],
            },
            {
                "id": 4, "name": "charmander", "generation": 1,
                "sprite_official_artwork": "https://example.com/4.png",
                "pokemon_types": [{"type_name": "fire", "slot": 1}],
            },
        ]
        db = _make_list_db(rows)
        result = get_pokemon_list(db, limit=24, offset=0)
        assert len(result) == 2
        assert all(isinstance(r, PokemonListRow) for r in result)

    def test_type_filter_intersects_pokemon_ids(self):
        type_data = [{"pokemon_id": 1}, {"pokemon_id": 3}]
        db = _make_list_db([], type_data=type_data)
        # Should call pokemon_types table for each requested type
        get_pokemon_list(db, types=["grass"])
        db.table.assert_any_call("pokemon_types")

    def test_type_filter_returns_empty_on_no_intersection(self):
        # Two types with no shared pokemon_ids
        call_count = [0]
        def type_data_for_call():
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"pokemon_id": 1}]
            return [{"pokemon_id": 2}]

        type_chain = MagicMock()
        type_chain.select.return_value = type_chain
        type_chain.eq.return_value = type_chain
        type_chain.execute.side_effect = lambda: MagicMock(data=type_data_for_call())

        pokemon_chain = MagicMock()
        pokemon_chain.select.return_value = pokemon_chain
        pokemon_chain.eq.return_value = pokemon_chain
        pokemon_chain.in_.return_value = pokemon_chain
        pokemon_chain.order.return_value = pokemon_chain
        pokemon_chain.range.return_value = pokemon_chain
        pokemon_chain.execute.return_value = MagicMock(data=[])

        db = MagicMock()
        db.table.side_effect = lambda name: type_chain if name == "pokemon_types" else pokemon_chain

        result = get_pokemon_list(db, types=["fire", "water"])
        assert result == []


class TestGetEvolutionChain:
    def test_returns_entries_when_found(self):
        db = _make_single_db({
            "chain": [{"id": 1, "name": "bulbasaur"}, {"id": 2, "name": "ivysaur"}]
        })
        result = get_evolution_chain(db, 1)
        assert result is not None
        assert len(result) == 2
        assert result[0].name == "bulbasaur"
        assert isinstance(result[0], EvolutionEntry)

    def test_returns_none_when_not_found(self):
        db = _make_single_db(None)
        result = get_evolution_chain(db, 9999)
        assert result is None

    def test_returns_empty_list_for_empty_chain(self):
        db = _make_single_db({"chain": []})
        result = get_evolution_chain(db, 1)
        assert result == []

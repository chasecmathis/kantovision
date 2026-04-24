"""Tests for the /pokemon, /moves, /abilities, /natures, /items endpoints."""
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from app.main import create_app
from app.repositories import ability_repo, item_repo, move_repo, nature_repo, pokemon_repo


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def _mock_pokemon_detail(pokemon_id: int = 1):
    return pokemon_repo.PokemonDetail(
        id=pokemon_id,
        name="bulbasaur",
        generation=1,
        height=7,
        weight=69,
        base_experience=64,
        is_legendary=False,
        is_mythical=False,
        color="green",
        capture_rate=45,
        base_happiness=50,
        flavor_text="A strange seed.",
        genus="Seed Pokémon",
        evolution_chain_id=1,
        evolution_chain=[
            pokemon_repo.EvolutionEntry(id=1, name="bulbasaur"),
            pokemon_repo.EvolutionEntry(id=2, name="ivysaur"),
        ],
        types=[pokemon_repo.TypeSlot(slot=1, name="grass")],
        abilities=[pokemon_repo.AbilitySlot(name="overgrow", is_hidden=False)],
        stats=pokemon_repo.Stats(hp=45, attack=49, defense=49,
                                  special_attack=65, special_defense=65, speed=45),
        sprites=pokemon_repo.Sprites(
            front_default="https://example.com/front.png",
            official_artwork="https://example.com/artwork.png",
            shiny=None,
            home=None,
        ),
        moves=[pokemon_repo.MoveEntry(name="tackle", method="level-up", level=1)],
    )


class TestPokemonListEndpoint:
    def test_returns_200_with_list(self, client):
        list_rows = [
            pokemon_repo.PokemonListRow(
                id=1, name="bulbasaur", generation=1,
                types=[pokemon_repo.TypeSlot(slot=1, name="grass")],
                sprite_official_artwork="https://example.com/1.png",
            )
        ]
        with patch.object(pokemon_repo, "get_pokemon_list", return_value=list_rows):
            resp = client.get("/pokemon")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "bulbasaur"
        assert data[0]["types"][0]["name"] == "grass"

    def test_passes_generation_filter(self, client):
        with patch.object(pokemon_repo, "get_pokemon_list", return_value=[]) as mock_list:
            client.get("/pokemon?generation=1")
        mock_list.assert_called_once()
        _, kwargs = mock_list.call_args
        assert kwargs["generation"] == 1

    def test_passes_type_filter(self, client):
        with patch.object(pokemon_repo, "get_pokemon_list", return_value=[]) as mock_list:
            client.get("/pokemon?types=fire,water")
        _, kwargs = mock_list.call_args
        assert kwargs["types"] == ["fire", "water"]

    def test_invalid_generation_returns_422(self, client):
        resp = client.get("/pokemon?generation=99")
        assert resp.status_code == 422


class TestPokemonDetailEndpoint:
    def test_returns_200_with_detail(self, client):
        with patch.object(pokemon_repo, "get_pokemon", return_value=_mock_pokemon_detail()):
            resp = client.get("/pokemon/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["name"] == "bulbasaur"
        assert data["stats"]["hp"] == 45
        assert data["stats"]["special_attack"] == 65
        assert data["sprites"]["official_artwork"] == "https://example.com/artwork.png"
        assert len(data["evolution_chain"]) == 2
        assert data["moves"][0]["name"] == "tackle"

    def test_returns_404_when_not_found(self, client):
        with patch.object(pokemon_repo, "get_pokemon", return_value=None):
            resp = client.get("/pokemon/9999")
        assert resp.status_code == 404


class TestEvolutionChainEndpoint:
    def test_returns_200_with_chain(self, client):
        entries = [
            pokemon_repo.EvolutionEntry(id=1, name="bulbasaur"),
            pokemon_repo.EvolutionEntry(id=2, name="ivysaur"),
            pokemon_repo.EvolutionEntry(id=3, name="venusaur"),
        ]
        with patch.object(pokemon_repo, "get_evolution_chain", return_value=entries):
            resp = client.get("/evolution-chains/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert len(data["chain"]) == 3

    def test_returns_404_when_not_found(self, client):
        with patch.object(pokemon_repo, "get_evolution_chain", return_value=None):
            resp = client.get("/evolution-chains/9999")
        assert resp.status_code == 404


class TestMoveEndpoint:
    def test_returns_200_with_move(self, client):
        row = move_repo.MoveRow(
            id=1, name="tackle", power=40, accuracy=100,
            pp=35, type="normal", damage_class="physical", flavor_text="A tackle.",
        )
        with patch.object(move_repo, "get_move", return_value=row):
            resp = client.get("/moves/tackle")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "tackle"
        assert data["power"] == 40
        assert data["damage_class"] == "physical"

    def test_returns_404_when_not_found(self, client):
        with patch.object(move_repo, "get_move", return_value=None):
            resp = client.get("/moves/nonexistent")
        assert resp.status_code == 404


class TestAbilityEndpoint:
    def test_returns_200_with_ability(self, client):
        row = ability_repo.AbilityRow(
            name="overgrow",
            short_effect="Boosts Grass moves when HP is low.",
            effect="Full overgrow effect.",
        )
        with patch.object(ability_repo, "get_ability", return_value=row):
            resp = client.get("/abilities/overgrow")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "overgrow"
        assert "Boosts" in data["short_effect"]

    def test_returns_404_when_not_found(self, client):
        with patch.object(ability_repo, "get_ability", return_value=None):
            resp = client.get("/abilities/nonexistent")
        assert resp.status_code == 404


class TestNaturesEndpoint:
    def test_returns_all_natures(self, client):
        rows = [
            nature_repo.NatureRow(name="adamant", increased_stat="attack", decreased_stat="special-attack"),
            nature_repo.NatureRow(name="timid", increased_stat="speed", decreased_stat="attack"),
            nature_repo.NatureRow(name="hardy", increased_stat=None, decreased_stat=None),
        ]
        with patch.object(nature_repo, "get_all_natures", return_value=rows):
            resp = client.get("/natures")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        adamant = next(n for n in data if n["name"] == "adamant")
        assert adamant["increased_stat"] == "attack"
        hardy = next(n for n in data if n["name"] == "hardy")
        assert hardy["increased_stat"] is None


class TestItemsEndpoints:
    def test_list_returns_200(self, client):
        rows = [
            item_repo.ItemRow(id=1, name="potion", sprite_url=None, category="medicine", flavor_text=None),
        ]
        with patch.object(item_repo, "get_item_list", return_value=rows):
            resp = client.get("/items")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["name"] == "potion"

    def test_detail_returns_200(self, client):
        row = item_repo.ItemRow(
            id=1, name="potion", sprite_url="https://example.com/potion.png",
            category="medicine", flavor_text="Restores 20 HP.",
        )
        with patch.object(item_repo, "get_item", return_value=row):
            resp = client.get("/items/potion")
        assert resp.status_code == 200
        data = resp.json()
        assert data["flavor_text"] == "Restores 20 HP."

    def test_detail_returns_404_when_not_found(self, client):
        with patch.object(item_repo, "get_item", return_value=None):
            resp = client.get("/items/nonexistent-item")
        assert resp.status_code == 404

import pytest
from src.schemas.pokemon import PokemonSchema, EvolutionSchema

def test_evolution_schema_defaults():
    """Garante que EvolutionSchema inicia com listas vazias por padrão."""
    evo = EvolutionSchema()
    assert evo.predecessors == []
    assert evo.successors == []

def test_pokemon_schema_validation():
    """Valida se o PokemonSchema aceita dados corretos."""
    data = {
        "name": "Pikachu",
        "pokedex_number": 25,
        "category": "Mouse Pokémon",
        "types": ["Electric"],
        "evolution": {"predecessors": ["Pichu"], "successors": ["Raichu"]},
        "abilities": [{"name": "Static", "is_hidden": False}],
        "hp": 35,
        "attack": 55,
        "defense": 40,
        "sp_atk": 50,
        "sp_def": 50,
        "speed": 90,
        "image_path": "media/images/pikachu.png"
    }
    pokemon = PokemonSchema(**data)
    assert pokemon.name == "Pikachu"
    assert pokemon.pokedex_number == 25

def test_pokemon_schema_invalid_data():
    """Verifica se o Pydantic lança erro para dados malformados."""
    invalid_data = {
        "name": "Pikachu",
        "pokedex_number": "não é um número" 
    }
    with pytest.raises(Exception):
        PokemonSchema(**invalid_data)

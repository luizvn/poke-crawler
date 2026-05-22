import pytest
from src.crawler.parser import parse_pokemon, _is_pokemon_page
from src.core.exceptions import FieldExtractionError

def test_is_pokemon_page_valid(pikachu_html):
    """Testa se _is_pokemon_page retorna True para um HTML válido."""
    from lxml import html
    tree = html.fromstring(pikachu_html)
    assert _is_pokemon_page(tree) is True

def test_is_pokemon_page_invalid():
    """Testa se _is_pokemon_page retorna False para uma página de erro."""
    from lxml import html
    html_error = '<div class="noarticletext">Página não encontrada</div>'
    tree = html.fromstring(html_error)
    assert _is_pokemon_page(tree) is False

def test_parse_pokemon_fail_on_empty_html():
    """Garante que o parser levante erro se o HTML for irreconhecível."""
    with pytest.raises(FieldExtractionError):
        parse_pokemon("<html><body>Nada</body></html>")

def test_parse_pokemon_full_pikachu(pikachu_html):
    """
    Testa o parsing completo com o HTML real do Pikachu.
    """
    data = parse_pokemon(pikachu_html)
    
    assert data["name"] == "Pikachu"
    assert data["pokedex_number"] == "0025"
    assert data["category"] == "Mouse Pokémon"
    assert "Electric" in data["types"]
    
    # Stats
    assert data["hp"] == "35"
    assert data["attack"] == "55"
    assert data["defense"] == "40"
    assert data["sp_atk"] == "50"
    assert data["sp_def"] == "50"
    assert data["speed"] == "90"
    
    # Abilities (Static é a principal)
    ability_names = [a["name"] for a in data["abilities"]]
    assert "Static" in ability_names
    assert "Lightning Rod" in ability_names
    
    # Evolution (Pichu e Raichu)
    assert "Pichu" in data["evolution"]["predecessors"]
    assert "Raichu" in data["evolution"]["successors"]

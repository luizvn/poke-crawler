import pytest
from src.services.crawler_service import CrawlerService
from src.db.models import Pokemon
from src.schemas.pokemon import PokemonSchema
from sqlalchemy import select

@pytest.mark.asyncio
async def test_save_or_update_new_pokemon(db_session):
    """Testa a inserção de um novo Pokémon no banco via service."""
    service = CrawlerService(db_session)
    
    pokemon_dto = PokemonSchema(
        name="Charmander",
        pokedex_number=4,
        category="Lizard",
        types=["Fire"],
        evolution={"predecessors": [], "successors": ["Charmeleon"]},
        hp=39, attack=52, defense=43, sp_atk=60, sp_def=50, speed=65,
        image_path="media/images/charmander.png"
    )
    
    db_pokemon = await service._save_or_update_pokemon(pokemon_dto, force_update=False)
    assert db_pokemon.name == "Charmander"
    
    # Verifica se persistiu
    query = select(Pokemon).where(Pokemon.name == "Charmander")
    result = await db_session.execute(query)
    assert result.scalar_one_or_none() is not None

@pytest.mark.asyncio
async def test_save_or_update_existing_force_update(db_session):
    """Testa se o force_update realmente atualiza os campos."""
    service = CrawlerService(db_session)
    
    # Primeiro insert
    pokemon_v1 = PokemonSchema(
        name="Bulbasaur", pokedex_number=1, category="Seed", types=["Grass"],
        evolution={"predecessors": [], "successors": []},
        hp=45, attack=49, defense=49, sp_atk=65, sp_def=65, speed=45,
        image_path="old_path.png"
    )
    await service._save_or_update_pokemon(pokemon_v1, force_update=False)
    
    # Update com novos dados
    pokemon_v2 = pokemon_v1.model_copy(update={"image_path": "new_path.png", "category": "Updated Seed"})
    await service._save_or_update_pokemon(pokemon_v2, force_update=True)
    
    # Verifica alteração
    query = select(Pokemon).where(Pokemon.pokedex_number == 1)
    result = await db_session.execute(query)
    updated = result.scalar_one()
    assert updated.image_path == "new_path.png"
    assert updated.category == "Updated Seed"

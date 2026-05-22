import asyncio
import logging
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Tuple

from src.core.config import settings
from src.crawler.fetcher import get_browser_session
from src.crawler.parser import parse_pokemon, extract_image_url, _get_base_name
from src.schemas.pokemon import PokemonSchema
from src.db.models import Pokemon
from src.core.exceptions import DuplicatePokemonError
from sqlalchemy.exc import IntegrityError
from lxml import html

logger = logging.getLogger(__name__)


class CrawlerService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def process_pokemon_list(self, names: List[str], force_update: bool = False) -> Tuple[list, list]:
        """
        Usa uma fila para processar e salvar pokémons em tempo real com lógica de duplo check e force_update.
        """
        successful = []
        failed = []
        names_to_fetch = []

        if not force_update:
            normalized_names = {n.strip().replace("_", " ").title() for n in names}

            query = select(Pokemon).where(func.lower(Pokemon.name).in_([n.lower() for n in normalized_names]))
            result = await self.db.execute(query)
            existing_pokemons = result.scalars().all()
            
            existing_names_lower = {p.name.lower() for p in existing_pokemons}
            
            for p in existing_pokemons:
                successful.append(PokemonSchema.model_validate(p))
                logger.info(f"Check 1 Hit: {p.name} carregado do banco.")

            names_to_fetch = [n for n in names if n.strip().replace("_", " ").title().lower() not in existing_names_lower]
        else:
            names_to_fetch = names

        if not names_to_fetch:
            return successful, failed

        queue = asyncio.Queue(maxsize=settings.QUEUE_SIZE)
        consumer_task = asyncio.create_task(self._consumer_worker(queue, successful, failed, force_update))

        loop = asyncio.get_running_loop()
        try:
            await asyncio.to_thread(self._producer_isolated, names_to_fetch, queue, loop)
        finally:
            await queue.put(None)
            await consumer_task

        return successful, failed

    def _producer_isolated(self, names: List[str], queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(self._async_producer_loop(names, queue, loop))

    async def _async_producer_loop(self, names: List[str], queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        async with get_browser_session() as fetcher:
            for name in names:
                try:
                    web_name = name.strip().replace(" ", "_")
                    html_content = await fetcher.fetch_html(web_name)
                    
                    if html_content:
                        img_url = extract_image_url(html_content)
                        image_path = await fetcher.download_image(img_url, name) if img_url else None
                        loop.call_soon_threadsafe(queue.put_nowait, (name, html_content, image_path))
                    else:
                        loop.call_soon_threadsafe(queue.put_nowait, (name, None, None))
                except Exception as e:
                    logger.error(f"Erro no produtor para {name}: {e}")
                    loop.call_soon_threadsafe(queue.put_nowait, (name, None, None))

    async def _consumer_worker(self, queue: asyncio.Queue, successful: list, failed: list, force_update: bool):
        while True:
            item = await queue.get()
            if item is None:
                queue.task_done()
                break
            
            name, html_content, image_path = item
            try:
                if not html_content:
                    raise Exception(f"HTML vazio ou erro de download para {name}")

                tree = html.fromstring(html_content)

                if not force_update:
                    canonical_name = _get_base_name(tree)
                    
                    if canonical_name:
                        query = select(Pokemon).where(func.lower(Pokemon.name) == canonical_name.lower())
                        result = await self.db.execute(query)
                        existing = result.scalar_one_or_none()
                        
                        if existing:
                            successful.append(PokemonSchema.model_validate(existing))
                            logger.info(f"Check 2 Hit: {canonical_name} já existia no banco (Alias/Redirect).")
                            queue.task_done()
                            continue

                raw_data = parse_pokemon(html_content)
                raw_data["image_path"] = image_path
                pokemon_dto = PokemonSchema(**raw_data)

                db_pokemon = await self._save_or_update_pokemon(pokemon_dto, force_update)
                successful.append(PokemonSchema.model_validate(db_pokemon))
                logger.info(f"Processado com sucesso: {pokemon_dto.name}")

            except Exception as e:
                await self.db.rollback()
                error_msg = str(e)
                logger.error(f"Erro ao processar {name}: {error_msg}")
                failed.append({"name": name, "error": error_msg})
            
            queue.task_done()

    async def _save_or_update_pokemon(self, pokemon_dto: PokemonSchema, force_update: bool) -> Pokemon:
        query = select(Pokemon).where(Pokemon.pokedex_number == pokemon_dto.pokedex_number)
        result = await self.db.execute(query)
        db_pokemon = result.scalar_one_or_none()

        if db_pokemon and force_update:
            # UPDATE
            db_pokemon.name = pokemon_dto.name
            db_pokemon.category = pokemon_dto.category
            db_pokemon.hp = pokemon_dto.hp
            db_pokemon.attack = pokemon_dto.attack
            db_pokemon.defense = pokemon_dto.defense
            db_pokemon.sp_atk = pokemon_dto.sp_atk
            db_pokemon.sp_def = pokemon_dto.sp_def
            db_pokemon.speed = pokemon_dto.speed
            db_pokemon.image_path = pokemon_dto.image_path
            db_pokemon.types = pokemon_dto.types
            db_pokemon.abilities = pokemon_dto.abilities
            db_pokemon.evolution = pokemon_dto.evolution.model_dump()
        else:
            db_pokemon = Pokemon(
                pokedex_number=pokemon_dto.pokedex_number,
                name=pokemon_dto.name,
                category=pokemon_dto.category,
                types=pokemon_dto.types,
                abilities=pokemon_dto.abilities,
                evolution=pokemon_dto.evolution.model_dump(),
                hp=pokemon_dto.hp,
                attack=pokemon_dto.attack,
                defense=pokemon_dto.defense,
                sp_atk=pokemon_dto.sp_atk,
                sp_def=pokemon_dto.sp_def,
                speed=pokemon_dto.speed,
                image_path=pokemon_dto.image_path
            )
            self.db.add(db_pokemon)

        try:
            await self.db.commit()
            await self.db.refresh(db_pokemon)
            return db_pokemon
        except IntegrityError:
            await self.db.rollback()
            raise DuplicatePokemonError(f"Conflito de integridade para {pokemon_dto.name}.")
        except Exception as e:
            await self.db.rollback()
            raise e

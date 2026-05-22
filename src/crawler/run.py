import asyncio
import logging
import sys
import time

from src.crawler.fetcher import get_browser_session
from src.crawler.parser import parse_pokemon, extract_image_url
from src.schemas.pokemon import PokemonSchema

# --- SILENCIADOR DE BUGS DO WINDOWS ---
if sys.platform == "win32":
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)


async def main():
    start_time = time.time()

    pokemon_alvo = "Pikachu"

    async with get_browser_session() as fetcher:
        html_content = await fetcher.fetch_html(pokemon_alvo)

        if not html_content:
            print("Abortando processamento, o HTML não pôde ser baixado.")
            return

        img_url = extract_image_url(html_content)
        print(f"\nURL da Imagem Identificada: {img_url}")

        image_path = None
        if img_url:
            image_path = await fetcher.download_image(img_url, pokemon_alvo)
            print(f"Caminho Local da Imagem: {image_path}")

        raw_data = parse_pokemon(html_content)

        raw_data["image_path"] = image_path

        print("\n--- Dados Extraídos ---")
        print(raw_data)

        try:
            pokemon_validado = PokemonSchema(**raw_data)
            print("\n--- Dados Normalizados ---")
            print(pokemon_validado.model_dump())
        except Exception as e:
            print("\nErro de Validação:")
            print(e)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\n Tempo total de execução: {elapsed_time:.2f} segundos")

if __name__ == "__main__":
    asyncio.run(main())
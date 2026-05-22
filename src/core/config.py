import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Caminho raiz do projeto (C:\Users\joker\PycharmProjects\poke-crawler)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Banco de Dados
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite+aiosqlite:///{BASE_DIR}/poke-crawler.db"
    )
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() in ("true", "1", "t", "yes")

    # Crawler Settings
    BASE_URL: str = os.getenv("BASE_URL", "https://bulbapedia.bulbagarden.net/wiki/")
    URL_SUFFIX: str = os.getenv("CRAWLER_URL_SUFFIX", "_(Pokémon)")
    MAX_RETRIES: int = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
    QUEUE_SIZE: int = int(os.getenv("CRAWLER_QUEUE_MAXSIZE", "5"))
    
    # Browser Settings
    BROWSER_HEADLESS: bool = os.getenv("BROWSER_HEADLESS", "False").lower() in ("true", "1")
    
    # Business Rules
    MAX_TYPES: int = int(os.getenv("MAX_TYPES_PER_POKEMON", "2"))
    MAX_ABILITIES: int = int(os.getenv("MAX_ABILITIES_PER_POKEMON", "3"))

    # Arquivos
    IMAGES_PATH: str = os.getenv("IMAGES_PATH", "./media/images")

settings = Settings()
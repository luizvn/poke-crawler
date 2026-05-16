import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./poke-crawler.db")
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() in ("true", "1", "t", "yes")
    BASE_URL: str = os.getenv("BASE_URL", "https://bulbapedia.bulbagarden.net/wiki/")
    IMAGES_PATH: str = os.getenv("IMAGES_PATH", "./media/images")

settings = Settings()
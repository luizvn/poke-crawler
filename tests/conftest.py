import asyncio
import pytest
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.db.base import Base
from src.db.database import get_db
from src.main import app

# Configuração do banco de testes em memória
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, future=True)
AsyncSessionTest = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Cria uma instância do event loop para toda a sessão de testes."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_db():
    """Cria as tabelas no banco de dados de teste."""
    import src.db.models
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão de banco de dados limpa para cada teste."""
    async with AsyncSessionTest() as session:
        yield session
        await session.rollback()

@pytest.fixture(autouse=True)
async def override_get_db(db_session):
    """Sobrescreve a dependência get_db do FastAPI globalmente nos testes."""
    async def _get_test_db():
        yield db_session
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def pikachu_html():
    """Fixture que carrega o conteúdo do arquivo pikachu.html para os testes."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", "pikachu.html")
    if not os.path.exists(path):
        return "<html><body><h1 id='firstHeading'>Pikachu (Pokémon)</h1></body></html>"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

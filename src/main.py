import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.api.routers import pokemon
from src.db.database import init_db
from src.core.exceptions import (
    PokeCrawlerException, 
    FieldExtractionError, 
    DuplicatePokemonError, 
    CrawlerFetchError, 
    BusinessRuleError
)

if sys.platform == "win32":
    if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executa na inicialização (Cria as tabelas se não existirem)
    await init_db()
    yield

app = FastAPI(title="PokéCrawler API", lifespan=lifespan)

# --- HANDLERS DE EXCEÇÕES GLOBAIS ---

@app.exception_handler(FieldExtractionError)
async def field_extraction_exception_handler(request: Request, exc: FieldExtractionError):
    return JSONResponse(
        status_code=422,
        content={"error": "Erro de Extração", "field": exc.field, "message": exc.message},
    )

@app.exception_handler(BusinessRuleError)
async def business_rule_exception_handler(request: Request, exc: BusinessRuleError):
    return JSONResponse(
        status_code=422,
        content={"error": "Violação de Regra de Negócio", "field": exc.field, "message": exc.message},
    )

@app.exception_handler(DuplicatePokemonError)
async def duplicate_pokemon_exception_handler(request: Request, exc: DuplicatePokemonError):
    return JSONResponse(
        status_code=409,
        content={"error": "Conflito de Dados", "message": exc.message},
    )

@app.exception_handler(CrawlerFetchError)
async def crawler_fetch_exception_handler(request: Request, exc: CrawlerFetchError):
    return JSONResponse(
        status_code=502,
        content={"error": "Erro de Conexão Externa", "message": exc.message},
    )

@app.exception_handler(PokeCrawlerException)
async def poke_crawler_exception_handler(request: Request, exc: PokeCrawlerException):
    return JSONResponse(
        status_code=500,
        content={"error": "Erro Interno do Crawler", "message": exc.message},
    )

app.include_router(pokemon.router)

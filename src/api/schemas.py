from pydantic import BaseModel
from typing import List
from src.schemas.pokemon import PokemonSchema

class CrawlRequest(BaseModel):
    names: List[str]
    force_update: bool = False

class CrawlFailure(BaseModel):
    name: str
    error: str

class CrawlResponse(BaseModel):
    successful: List[PokemonSchema]
    failed: List[CrawlFailure]
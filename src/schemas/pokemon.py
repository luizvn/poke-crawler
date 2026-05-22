from pydantic import BaseModel
from typing import List, Dict, Any


class EvolutionSchema(BaseModel):
    predecessors: List[str] = []
    successors: List[str] = []

class PokemonSchema(BaseModel):
    name: str
    pokedex_number: int
    category: str
    types: List[str]
    evolution: EvolutionSchema
    abilities: List[Dict[str, Any]] = []
    hp: int
    attack: int
    defense: int
    sp_atk: int
    sp_def: int
    speed: int
    image_path: str

    model_config = {
        "from_attributes": True
    }
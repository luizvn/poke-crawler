from sqlalchemy import Column, Integer, String, JSON
from src.db.base import Base

class Pokemon(Base):
    __tablename__ = 'pokemon'

    pokedex_number = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    hp = Column(Integer, nullable=False)
    attack = Column(Integer, nullable=False)
    defense = Column(Integer, nullable=False)
    sp_atk = Column(Integer, nullable=False)
    sp_def = Column(Integer, nullable=False)
    speed = Column(Integer, nullable=False)
    image_path = Column(String, nullable=False)
    types = Column(JSON, nullable=False)
    abilities = Column(JSON, nullable=False)
    evolution = Column(JSON, nullable=False)

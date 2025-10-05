from pydantic import BaseModel, Field, validator
from typing import Optional, List

class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1)
    franchise: Optional[str] = Field(default='Sanrio')
    species: Optional[str]
    debut_year: Optional[int]
    tags: Optional[List[str]] = []
    description: Optional[str]

    @validator('debut_year')
    def validate_year(cls, v):
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError('debut_year must be in range 1900-2100')
        return v

class Character(CharacterCreate):
    id: str

class SearchQuery(BaseModel):
    q: Optional[str] = None
    franchise: Optional[str] = None
    species: Optional[str] = None
    tags: Optional[List[str]] = None
    page: int = 1
    size: int = 10
    fuzzy: bool = False

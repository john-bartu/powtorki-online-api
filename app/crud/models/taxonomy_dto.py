from __future__ import annotations
from typing import List

from pydantic import BaseModel

from app.database import models


class TaxonomyOut(BaseModel):
    class Config:
        orm_mode = True

    id: int
    id_parent: int | None
    id_taxonomy_type: int
    name: str
    description: str | None
    path: List[str] = []
    children: List[TaxonomyOut]


class TaxonomyForm(BaseModel):
    class Config:
        orm_mode = True

    id_parent: int | None
    id_taxonomy_type: int
    name: str
    description: str | None

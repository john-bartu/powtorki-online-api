from typing import List

from pydantic import BaseModel


class TaxonomyOut(BaseModel):
    class Config:
        orm_mode = True

    id: int
    id_parent: int | None
    id_taxonomy_type: int
    name: str
    description: str | None
    path: List[str] = []

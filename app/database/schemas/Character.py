from pydantic import BaseModel


class Character(BaseModel):
    id: int
    name: str
    description: str | None = None

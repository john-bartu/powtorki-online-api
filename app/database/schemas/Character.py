from pydantic import BaseModel


class Character(BaseModel):
    id: int
    name: str | None
    description: str | None = None
    note: str | None = None
    image: str | None = None

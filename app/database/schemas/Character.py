from pydantic import BaseModel


class DbCharacter(BaseModel):
    id: int
    name: str | None
    description: str | None
    note: str | None
    image: str | None

    class Config:
        orm_mode = True

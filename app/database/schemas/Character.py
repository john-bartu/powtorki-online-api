from pydantic import BaseModel


class DbCharacter(BaseModel):
    id: int
    name: str | None
    description: str | None
    note: str | None

    class Config:
        orm_mode = True


class UpdateCharacter(BaseModel):
    name: str | None
    description: str | None
    note: str | None


class CreateCharacter(BaseModel):
    name: str | None
    description: str | None
    note: str | None

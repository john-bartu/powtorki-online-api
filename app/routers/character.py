from fastapi import APIRouter
from typing import Optional

from sqlalchemy.testing import db

from app.database.schemas.Character import Character as SchemeCharacter
from app.database.models.Character import Character

router = APIRouter(
    prefix="/character",
    tags=["character"],
)


@router.get("/{item_id}", response_model=SchemeCharacter)
def get_character(item_id: int):
    return db.query(Character).filter(Character.id == item_id).first()

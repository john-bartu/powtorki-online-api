from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.database.schemas.Character import Character as SchemeCharacter
from app.database.models.Character import Character
from app.main import get_db

router = APIRouter(
    prefix="/character",
    tags=["character"],
)


@router.get("/{item_id}", response_model=SchemeCharacter)
def get_character(item_id: int, db: Session = Depends(get_db)):
    return db.query(Character).filter(Character.id == item_id).first()

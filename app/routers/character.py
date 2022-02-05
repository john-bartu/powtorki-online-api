from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import schemas
from app.database.database import get_db
from app.database.models.Character import Character

router = APIRouter(
    prefix="/character",
    tags=["character"],
)


@router.get("/{item_id}", response_model=schemas.DbCharacter)
def get_character(item_id: int, db: Session = Depends(get_db)):
    return db.query(Character).filter(Character.id == item_id).first()


@router.get("/", response_model=List[schemas.DbCharacter])
def get_character(db: Session = Depends(get_db)):
    return db.query(Character).all()

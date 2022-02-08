from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import CharacterCRUD
from app.database import schemas
from app.database.database import get_db

router = APIRouter(
    prefix="/character",
    tags=["character"],
)


@router.get("/")
def get_characters(db: Session = Depends(get_db)):
    return CharacterCRUD.get_characters(db)

#
# @router.get("/{item_id}", response_model=schemas.DbCharacter)
# def get_character(item_id: int, db: Session = Depends(get_db)):
#     return CharacterCRUD.get_character(db, item_id)
#
#
# @router.post("/", response_model=schemas.DbCharacter)
# def create_character(character: schemas.CreateCharacter, db: Session = Depends(get_db)):
#     return CharacterCRUD.create_character(db, character)
#
#
# @router.put("/{item_id}", response_model=schemas.DbCharacter)
# def update_character(item_id: int, character: schemas.UpdateCharacter, db: Session = Depends(get_db)):
#     return CharacterCRUD.update_character(db, item_id, character)

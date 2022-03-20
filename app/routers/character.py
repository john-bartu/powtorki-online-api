from urllib.request import Request

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.item_lister import ItemLister
from app.database import models
from app.database.database import get_db

# router = APIRouter(
#     tags=["character"],
# )

#
# @router.get("/{subject}/character")
# def get_characters(subject: int | str, request=Request, db: Session = Depends(get_db)):
#     paginator = ItemLister(db, models.CharacterPage, subject)
#     return paginator.get_items()

#
# @router.get("/{item_id}", response_model=schemas.DbCharacter)
# def get_character(item_id: int, db: Session = Depends(get_db)):
#     return character_crud.get_character(db, item_id)
#
#
# @router.post("/", response_model=schemas.DbCharacter)
# def create_character(character: schemas.CreateCharacter, db: Session = Depends(get_db)):
#     return character_crud.create_character(db, character)
#
#
# @router.put("/{item_id}", response_model=schemas.DbCharacter)
# def update_character(item_id: int, character: schemas.UpdateCharacter, db: Session = Depends(get_db)):
#     return character_crud.update_character(db, item_id, character)

from typing import List

from sqlalchemy.orm import Session

from app.database import models


def get_character(db: Session, character_id: int) -> models.CharacterPage:
    return db.query(models.CharacterPage).filter(models.CharacterPage.id == character_id).first()


def get_characters(db: Session, skip: int = 0, limit: int = 100) -> List[models.CharacterPage]:
    return db.query(models.CharacterPage).offset(skip).limit(limit).all()

#
# def create_character(db: Session, character: schemas.CreateCharacter) -> models.CharacterPage:
#     db_character = models.CharacterPage(
#         name=character.name,
#         description=character.description,
#         note=character.note
#     )
#     db.add(db_character)
#     db.commit()
#     db.refresh(db_character)
#     return db_character
#
#
# def update_character(db: Session, item_id: int, character: schemas.UpdateCharacter):
#     db_character: models.CharacterPage = db.query(models.CharacterPage).get(item_id)
#
#     if character.name:
#         db_character.name = character.name
#
#     if character.description:
#         db_character.description = character.description
#
#     if character.note:
#         db_character.note = character.note
#
#     db.commit()
#     db.refresh(db_character)
#
#     return db_character

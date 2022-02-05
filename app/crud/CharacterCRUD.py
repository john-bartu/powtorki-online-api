from typing import List

from sqlalchemy.orm import Session

from app.database import models, schemas


def get_character(db: Session, character_id: int) -> models.Character:
    return db.query(models.Character).filter(models.Character.id == character_id).first()


def get_characters(db: Session, skip: int = 0, limit: int = 100) -> List[models.Character]:
    return db.query(models.Character).with_entities.offset(skip).limit(limit).all()


def create_character(db: Session, character: schemas.CreateCharacter) -> models.Character:
    db_character = models.Character(
        name=character.name,
        description=character.description,
        note=character.note
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


def update_character(db: Session, item_id: int, character: schemas.UpdateCharacter):
    db_character: models.Character = db.query(models.Character).get(item_id)

    db_character.name = character.name
    db_character.description = character.description
    db_character.note = character.note

    db.commit()
    db.refresh(db_character)

    return db_character

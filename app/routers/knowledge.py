from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.item_lister import ItemLister
from app.database import models
from app.database.database import get_db

router = APIRouter()


@router.get("/{subject}/document", tags=["document"])
def get_documents(subject: int | str, db: Session = Depends(get_db)):
    paginator = ItemLister(db, models.DocumentPage, subject)
    return paginator.get_items()


@router.get("{subject}/date", tags=["date"])
def get_pages(subject: int | str, db: Session = Depends(get_db)):
    paginator = ItemLister(db, models.CalendarPage, subject)
    return paginator.get_items()


@router.get("/{subject}/character", tags=["character"])
def get_characters(subject: int | str, db: Session = Depends(get_db)):
    paginator = ItemLister(db, models.CharacterPage, subject)
    return paginator.get_items()

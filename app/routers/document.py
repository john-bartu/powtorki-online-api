from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.item_lister import ItemLister
from app.database import models
from app.database.database import get_db

router = APIRouter(
    prefix="",
    tags=["document"],
)


@router.get("{subject}/document")
def get_pages(subject: int | str, db: Session = Depends(get_db)):
    paginator = ItemLister(db, models.DocumentPage, subject)
    return paginator.get_items()

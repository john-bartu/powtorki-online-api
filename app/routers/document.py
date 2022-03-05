from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.item_lister import ItemLister
from app.database import models
from app.database.database import get_db

router = APIRouter(
    prefix="/document",
    tags=["document]"],
)


@router.get("/")
def get_pages(db: Session = Depends(get_db)):
    paginator = ItemLister(db, models.DocumentPage, 1)
    return paginator.get_items()

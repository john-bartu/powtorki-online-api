from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import date_crud
from app.database.database import get_db

router = APIRouter(
    prefix="/date",
    tags=["date]"],
)


@router.get("/")
def get_pages(db: Session = Depends(get_db)):
    return DateCRUD.get_dates(db)

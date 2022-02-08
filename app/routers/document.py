from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import document_crud
from app.database.database import get_db

router = APIRouter(
    prefix="/document",
    tags=["document]"],
)


@router.get("/")
def get_pages(db: Session = Depends(get_db)):
    return DocumentCRUD.get_documents(db)

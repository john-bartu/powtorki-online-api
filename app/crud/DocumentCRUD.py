from sqlalchemy.orm import Session

from app.database import models


def get_document(db: Session, page_id: int):
    return db.query(models.DocumentPage).filter(models.DocumentPage.id == page_id).first()


def get_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DocumentPage).offset(skip).limit(limit).all()

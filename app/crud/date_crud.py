from sqlalchemy.orm import Session

from app.database import models


def get_date(db: Session, page_id: int):
    return db.query(models.CalendarPage).filter(models.CalendarPage.id == page_id).first()


def get_dates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CalendarPage).offset(skip).pagination_limit(limit).all()

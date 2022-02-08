from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class Date(Base):
    __tablename__ = "dates"

    id = Column(Integer, primary_key=True, index=True)
    id_page = Column(Integer, ForeignKey("pages.id"))

    date_number = Column(Integer)
    date_text = Column(String)

    page = relationship("CalendarPage", back_populates="date")

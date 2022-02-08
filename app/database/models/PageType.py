from sqlalchemy import Column, Integer, VARCHAR

from app.database.database import Base


class PageType(Base):
    __tablename__ = "page_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(120))

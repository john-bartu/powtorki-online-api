from sqlalchemy import Column, Integer, String

from app.database.database import Base


class Character(Base):
    __tablename__ = "his_characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    note = Column(String)
    image = Column(String)

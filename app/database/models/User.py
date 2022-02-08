from sqlalchemy import Column, Integer, VARCHAR

from app.database.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(VARCHAR(150))
    password = Column(VARCHAR(255))

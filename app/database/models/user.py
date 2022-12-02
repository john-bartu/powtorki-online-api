from sqlalchemy import Column, Integer, VARCHAR, BOOLEAN, ForeignKey

from app.database.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(VARCHAR(150))
    password = Column(VARCHAR(255))
    disabled = Column(BOOLEAN())
    id_role = Column(Integer, ForeignKey("roles.id"))


class Roles(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(32))

from sqlalchemy import Column, Integer, VARCHAR, ForeignKey

from app.database.database import Base


class PageType(Base):
    __tablename__ = "page_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(120))


class PageSubType(Base):
    __tablename__ = "page_sub_types"
    id = Column(Integer, primary_key=True, index=True)
    id_type = Column(Integer, ForeignKey("page_types.id"))
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(120))
    color = Column(VARCHAR(120))
    icon = Column(VARCHAR(120))

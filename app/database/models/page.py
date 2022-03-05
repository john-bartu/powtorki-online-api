from sqlalchemy import Column, Integer, String, VARCHAR, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    id_author = Column(Integer, ForeignKey("users.id"))
    id_type = Column(Integer, ForeignKey("page_types.id"))
    title = Column(VARCHAR(60))
    document = Column(String)
    description = Column(VARCHAR(150))
    time_creation = Column(String)
    time_edited = Column(String)

    taxonomies = relationship("MapPageTaxonomy", uselist=True)

    __mapper_args__ = {
        'polymorphic_on': id_type,
        'polymorphic_identity': 1
    }


class DocumentPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 2
    }


class CharacterPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 4
    }


class CalendarPage(Page):
    __mapper_args__ = {
        'polymorphic_identity': 5
    }

    date = relationship("Date", back_populates="page", lazy='joined', uselist=False)

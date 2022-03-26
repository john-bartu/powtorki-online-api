import json

from sqlalchemy import Column, Integer, VARCHAR, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class MapPageTaxonomy(Base):
    __tablename__ = "map_page_taxonomy"

    id_page = Column(Integer, ForeignKey("pages.id"))
    id_taxonomy = Column(Integer, ForeignKey("taxonomies.id"))

    taxonomy = relationship('Taxonomy', uselist=False)
    page = relationship('Page', uselist=False)

    __table_args__ = (
        PrimaryKeyConstraint(id_page, id_taxonomy),
    )


class Taxonomy(Base):
    __tablename__ = "taxonomies"

    id = Column(Integer, primary_key=True, index=True)
    id_parent = Column(Integer, ForeignKey("taxonomies.id"), nullable=True)
    id_taxonomy_type = Column(Integer, ForeignKey("taxonomy_types.id"))
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(180))

    children = relationship('Taxonomy', uselist=True)
    map_pages = relationship('MapPageTaxonomy', uselist=True)

    time_creation = Column(String)
    time_edited = Column(String)

    __mapper_args__ = {
        'polymorphic_on': id_taxonomy_type,
        'polymorphic_identity': 1
    }

    def __repr__(self):
        filter_names = ['id', 'id_parent', 'id_taxonomy_type', 'name', 'description']
        return json.dumps({index: str(value) if index in filter_names else "" for index, value in vars(self).items()})


class SubjectTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 2
    }


class ChapterTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 3
    }


class CalendarTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 4
    }


class CharacterTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 5
    }


class DictionaryTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 6
    }


class QuizTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 7
    }


class QATaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 8
    }


class TaxonomyType(Base):
    __tablename__ = "taxonomy_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(150))

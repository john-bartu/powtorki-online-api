from sqlalchemy import Column, Integer, VARCHAR, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from app.database.database import Base


class MapPageTaxonomy(Base):
    __tablename__ = "map_page_taxonomy"

    id_page = Column(Integer, ForeignKey("pages.id"))
    id_taxonomy = Column(Integer, ForeignKey("taxonomies.id"))

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

    __mapper_args__ = {
        'polymorphic_on': id_taxonomy_type,
        'polymorphic_identity': 1
    }


class SubjectTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 2
    }


class ChapterTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': 3
    }


class TaxonomyType(Base):
    __tablename__ = "taxonomy_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(150))

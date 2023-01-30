import json

from sqlalchemy import Column, Integer, VARCHAR, ForeignKey, String, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, Session, backref

from app.constants import TaxonomyTypes
from app.database.database import Base
from app.helpers import get_descendants, get_ancestors, get_whole_branch, get_subjects


class MapPageTaxonomy(Base):
    __tablename__ = "map_page_taxonomy"

    id_page = Column(Integer, ForeignKey("pages.id"))
    id_taxonomy = Column(Integer, ForeignKey("taxonomies.id"))
    order_no = Column(Integer)

    taxonomy = relationship('Taxonomy', uselist=False, back_populates="map_pages")
    page = relationship('Page', uselist=False, back_populates="taxonomies")

    __table_args__ = (
        PrimaryKeyConstraint(id_page, id_taxonomy),
        UniqueConstraint(id_taxonomy, order_no)
    )


class Taxonomy(Base):
    __tablename__ = "taxonomies"

    id = Column(Integer, primary_key=True, index=True)
    id_parent = Column(Integer, ForeignKey("taxonomies.id"), nullable=True)
    id_taxonomy_type = Column(Integer, ForeignKey("taxonomy_types.id"))
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(180))

    children = relationship('Taxonomy', uselist=True, backref=backref('parent', uselist=False, remote_side=[id]))
    map_pages = relationship('MapPageTaxonomy', uselist=True, back_populates="taxonomy")

    time_creation = Column(String)
    time_edited = Column(String)

    __mapper_args__ = {
        'polymorphic_on': id_taxonomy_type,
        'polymorphic_identity': 1
    }

    def __repr__(self):
        filter_names = ['id', 'id_parent', 'id_taxonomy_type', 'name', 'description']
        return json.dumps({index: str(value) if index in filter_names else "" for index, value in vars(self).items()})

    def get_descendants(self, db: Session):
        return [tax[0] for tax in get_descendants(db, [self.id])]

    def get_ancestors(self, db: Session):
        return [tax[0] for tax in get_ancestors(db, [self.id])]

    def get_whole_branch(self, db: Session):
        return get_whole_branch(db, [self.id])

    def get_subject(self, db: Session):
        subjects = get_subjects(db, [self.id])
        if len(subjects) > 1:
            raise Exception("This subject belongs to multiple subjects")
        elif len(subjects) == 0:
            raise Exception("This subject does not belong to any subject")
        else:
            return subjects[0]


class SubjectTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': TaxonomyTypes.SubjectTaxonomy
    }


class ChapterTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': TaxonomyTypes.ChapterTaxonomy
    }


class SetTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': TaxonomyTypes.SetTaxonomy
    }


class KindTaxonomy(Taxonomy):
    __mapper_args__ = {
        'polymorphic_identity': TaxonomyTypes.KindTaxonomy
    }


class TaxonomyType(Base):
    __tablename__ = "taxonomy_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(150))

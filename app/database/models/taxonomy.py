import json

from sqlalchemy import Column, Integer, VARCHAR, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.orm import relationship, Session, backref

from app.database.database import Base


class MapPageTaxonomy(Base):
    __tablename__ = "map_page_taxonomy"

    id_page = Column(Integer, ForeignKey("pages.id"))
    id_taxonomy = Column(Integer, ForeignKey("taxonomies.id"))

    taxonomy = relationship('Taxonomy', uselist=False, back_populates="map_pages")
    page = relationship('Page', uselist=False, back_populates="taxonomies")

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

    def get_all_sub_taxonomies(self, db: Session):
        taxonomy_selected = db.query(Taxonomy).with_entities(Taxonomy.id, Taxonomy.id_parent)
        taxonomy_selected = taxonomy_selected.filter(Taxonomy.id == self.id)
        taxonomy_selected = taxonomy_selected.cte('cte', recursive=True)

        taxonomy_child = db.query(Taxonomy).with_entities(Taxonomy.id, Taxonomy.id_parent)
        taxonomy_child = taxonomy_child.join(taxonomy_selected, Taxonomy.id_parent == taxonomy_selected.c.id)

        recursive_q = taxonomy_selected.union(taxonomy_child)

        return [tax[0] for tax in db.query(recursive_q).all()]

    def get_subject(self, db: Session):
        taxonomy_selected = db.query(Taxonomy).with_entities(Taxonomy.id, Taxonomy.id_parent, Taxonomy.id_taxonomy_type)
        taxonomy_selected = taxonomy_selected.filter(Taxonomy.id == self.id)
        taxonomy_selected = taxonomy_selected.cte('cte', recursive=True)

        taxonomy_child = db.query(Taxonomy).with_entities(Taxonomy.id, Taxonomy.id_parent, Taxonomy.id_taxonomy_type)
        taxonomy_child = taxonomy_child.join(taxonomy_selected, Taxonomy.id == taxonomy_selected.c.id_parent)

        recursive_q = taxonomy_selected.union(taxonomy_child)

        return db.query(recursive_q).all()[-1]


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

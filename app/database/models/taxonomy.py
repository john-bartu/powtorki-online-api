from sqlalchemy import Column, Integer, VARCHAR, ForeignKey, PrimaryKeyConstraint

from app.database.database import Base


class MapPageTaxonomy(Base):
    __tablename__ = "map_page_taxonomy"

    id_page = Column(Integer, ForeignKey("pages.id"))
    id_taxonomy = Column(Integer, ForeignKey("taxonomies.id"))

    __table_args__ = (
        PrimaryKeyConstraint(id_page, id_taxonomy),
        {},
    )


class Taxonomy(Base):
    __tablename__ = "taxonomies"

    id = Column(Integer, primary_key=True, index=True)
    id_type = Column(Integer, ForeignKey("taxonomy_types.id"))
    name = Column(VARCHAR(60))


class TaxonomyType(Base):
    __tablename__ = "taxonomy_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(60))
    description = Column(VARCHAR(150))

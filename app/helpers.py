from sqlalchemy.orm import Session

from app.constants import TaxonomyTypes
from app.database import models


# noinspection DuplicatedCode
def get_descendants(db: Session, chapter_ids: list[int]):
    taxonomy_selected = (db.query(models.Taxonomy)
                         .with_entities(models.Taxonomy.id, models.Taxonomy.id_parent, models.Taxonomy.id_taxonomy_type)
                         .filter(models.Taxonomy.id.in_(chapter_ids))
                         .cte('cte', recursive=True))

    taxonomy_child = (db.query(models.Taxonomy)
                      .with_entities(models.Taxonomy.id, models.Taxonomy.id_parent, models.Taxonomy.id_taxonomy_type)
                      .join(taxonomy_selected, models.Taxonomy.id_parent == taxonomy_selected.c.id))

    recursive_q = taxonomy_selected.union(taxonomy_child)
    return [tax[0] for tax in db.query(recursive_q).all()]


# noinspection DuplicatedCode
def get_ancestors(db: Session, chapter_ids: list[int]):
    taxonomy_selected = (db.query(models.Taxonomy)
                         .with_entities(models.Taxonomy.id, models.Taxonomy.id_parent, models.Taxonomy.id_taxonomy_type)
                         .filter(models.Taxonomy.id.in_(chapter_ids))
                         .cte('cte', recursive=True))

    taxonomy_child = (db.query(models.Taxonomy)
                      .with_entities(models.Taxonomy.id, models.Taxonomy.id_parent, models.Taxonomy.id_taxonomy_type)
                      .join(taxonomy_selected, models.Taxonomy.id == taxonomy_selected.c.id_parent))

    recursive_q = taxonomy_selected.union(taxonomy_child)
    return [tax[0] for tax in db.query(recursive_q).all()]


def get_whole_branch(db: Session, chapter_ids: list[int]):
    return {*get_descendants(db, chapter_ids), *get_ancestors(db, chapter_ids)}


def get_subjects(db: Session, chapter_ids: list[int]):
    return set([chapter for chapter in get_ancestors(db, chapter_ids) if chapter[2] == TaxonomyTypes.SubjectTaxonomy])

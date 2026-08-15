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

    taxonomy_parent = (db.query(models.Taxonomy)
                       .with_entities(models.Taxonomy.id, models.Taxonomy.id_parent, models.Taxonomy.id_taxonomy_type)
                       .join(taxonomy_selected, models.Taxonomy.id == taxonomy_selected.c.id_parent))

    recursive_q = taxonomy_selected.union(taxonomy_parent)
    return [tax[0] for tax in db.query(recursive_q).all()]


def get_whole_branch(db: Session, chapter_ids: list[int]):
    return {*get_descendants(db, chapter_ids), *get_ancestors(db, chapter_ids)}


def find_branch_conflict(db: Session, taxonomy_ids: list[int]) -> tuple[int, int] | None:
    """Returns a pair of ids from taxonomy_ids that share an ancestor/descendant branch (or are equal), or None."""
    for taxonomy_id in taxonomy_ids:
        branch = get_whole_branch(db, [taxonomy_id])
        for other_id in taxonomy_ids:
            if other_id != taxonomy_id and other_id in branch:
                return taxonomy_id, other_id
    return None


def get_subjects(db: Session, chapter_ids: list[int]):
    return set([chapter for chapter in get_ancestors(db, chapter_ids) if chapter[2] == TaxonomyTypes.SubjectTaxonomy])

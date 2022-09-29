from sqlalchemy.orm import Session

from app.database import models


def get_whole_taxonomy(db: Session, chapter_id: int):
    taxonomy_selected = db.query(models.Taxonomy).with_entities(models.Taxonomy.id, models.Taxonomy.id_parent)
    taxonomy_selected = taxonomy_selected.filter(models.Taxonomy.id == chapter_id)
    taxonomy_selected = taxonomy_selected.cte('cte', recursive=True)

    taxonomy_child = db.query(models.Taxonomy).with_entities(models.Taxonomy.id, models.Taxonomy.id_parent)
    taxonomy_child = taxonomy_child.join(taxonomy_selected, models.Taxonomy.id_parent == taxonomy_selected.c.id)

    recursive_q = taxonomy_selected.union(taxonomy_child)

    return [tax[0] for tax in db.query(recursive_q).all()]

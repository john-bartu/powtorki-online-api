from sqlalchemy.orm import Session

from app.database import models


def get_whole_taxonomy(db: Session, chapter_ids: list[int]):
    taxonomy_selected = (db.query(models.Taxonomy)
                         .with_entities(models.Taxonomy.id, models.Taxonomy.id_parent)
                         .filter(models.Taxonomy.id.in_(chapter_ids))
                         .cte('cte', recursive=True))

    taxonomy_child = (db.query(models.Taxonomy)
                      .with_entities(models.Taxonomy.id, models.Taxonomy.id_parent)
                      .join(taxonomy_selected, models.Taxonomy.id_parent == taxonomy_selected.c.id))

    recursive_q = taxonomy_selected.union(taxonomy_child)
    print(db.query(recursive_q).all())
    return [tax[0] for tax in db.query(recursive_q).all()]

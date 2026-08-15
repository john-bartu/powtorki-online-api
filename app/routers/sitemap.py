from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import TaxonomyTypes
from app.database import models
from app.database.database import get_db

router = APIRouter(prefix="/sitemap", tags=["sitemap"])


@router.get("/subjects")
def get_sitemap_subjects(db: Session = Depends(get_db)):
    """
    Returns list of subjects (Taxonomy with id_taxonomy_type == 2)
    """
    subjects = (
        db.query(models.Taxonomy.id.label("subjectId"))
        .filter(models.Taxonomy.id_taxonomy_type == TaxonomyTypes.SubjectTaxonomy)
        .all()
    )
    return [dict(row._mapping) for row in subjects]


@router.get("/taxonomies")
def get_sitemap_taxonomies(db: Session = Depends(get_db)):
    """
    Returns list of taxonomies per subject nested too
    """
    # Base case: all subjects
    base_query = (
        db.query(
            models.Taxonomy.id.label("taxonomy_id"),
            models.Taxonomy.id.label("subject_id")
        )
        .filter(models.Taxonomy.id_taxonomy_type == TaxonomyTypes.SubjectTaxonomy)
        .cte(name="taxonomy_tree", recursive=True)
    )

    # Recursive part: children of the current nodes in the tree
    child_alias = db.query(
        models.Taxonomy.id.label("taxonomy_id"),
        base_query.c.subject_id.label("subject_id")
    ).join(base_query, models.Taxonomy.id_parent == base_query.c.taxonomy_id)

    taxonomy_tree = base_query.union_all(child_alias)

    results = db.query(
        taxonomy_tree.c.subject_id.label("subjectId"),
        taxonomy_tree.c.taxonomy_id.label("taxonomyId")
    ).all()

    return [dict(row._mapping) for row in results]


@router.get("/pages")
def get_sitemap_pages(db: Session = Depends(get_db)):
    """
    Returns list of pages within taxonomy (in subject scope)
    """
    # Base case: all subjects
    base_query = (
        db.query(
            models.Taxonomy.id.label("taxonomy_id"),
            models.Taxonomy.id.label("subject_id")
        )
        .filter(models.Taxonomy.id_taxonomy_type == TaxonomyTypes.SubjectTaxonomy)
        .cte(name="taxonomy_tree", recursive=True)
    )

    # Recursive part: children of the current nodes in the tree
    child_alias = db.query(
        models.Taxonomy.id.label("taxonomy_id"),
        base_query.c.subject_id.label("subject_id")
    ).join(base_query, models.Taxonomy.id_parent == base_query.c.taxonomy_id)

    taxonomy_tree = base_query.union_all(child_alias)

    results = (
        db.query(
            taxonomy_tree.c.subject_id.label("subjectId"),
            taxonomy_tree.c.taxonomy_id.label("taxonomyId"),
            models.Page.id_sub_type.label("pageSubTypeId"),
            models.Page.id.label("pageId")
        )
        .join(models.MapPageTaxonomy, taxonomy_tree.c.taxonomy_id == models.MapPageTaxonomy.id_taxonomy)
        .join(models.Page, models.MapPageTaxonomy.id_page == models.Page.id)
        .all()
    )

    return [dict(row._mapping) for row in results]

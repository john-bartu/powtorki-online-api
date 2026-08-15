from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload

from app.database import models
from app.services.models.taxonomy_dto import TaxonomyForm, TaxonomyOut


class TaxonomyService:

    def __init__(self, db: Session, model: type[models.Taxonomy] = models.Taxonomy) -> None:
        self.db = db
        self.model = model

    def get(self, taxonomy_id: int) -> models.Taxonomy | None:
        item = self.db.query(self.model).filter(self.model.id == taxonomy_id).first()
        if item is None:
            return None

        taxonomy_branch = item.get_whole_branch(self.db)
        page_count_per_type = (self.db.query(models.Page.id_sub_type, func.count(models.Page.id_sub_type))
                               .join(models.MapPageTaxonomy)
                               .filter(models.MapPageTaxonomy.id_taxonomy.in_(taxonomy_branch))
                               .group_by(models.Page.id_sub_type)
                               .all())
        item.pages = {page_type[0]: {'count': page_type[1]} for page_type in page_count_per_type}
        return item

    def get_items(self, parent_id: int | None) -> list[TaxonomyOut]:
        items = (self.db.query(self.model).
                 options(joinedload(self.model.children))
                 .filter(self.model.id_parent == parent_id)
                 .all())
        return [TaxonomyOut.model_validate(item) for item in items]

    def post(self, form: TaxonomyForm) -> TaxonomyOut:
        item = models.Taxonomy()

        item.id_parent = form.id_parent
        item.id_taxonomy_type = form.id_taxonomy_type
        item.name = form.name
        item.description = form.description

        self.db.add(item)
        self.db.commit()
        return TaxonomyOut.model_validate(item)

    def delete(self, taxonomy_id: int) -> bool:
        item = (self.db.query(models.Taxonomy)
                .options(joinedload(self.model.children))
                .filter(models.Taxonomy.id == taxonomy_id)
                .first())

        if (len(item.children)) > 0:
            raise Exception("Cannot remove taxonomy which has related children")

        self.db.delete(item)
        self.db.commit()
        return True

    def put(self, taxonomy_id: int, form: TaxonomyForm) -> TaxonomyOut | None:
        item = self.db.query(models.Taxonomy).filter(models.Taxonomy.id == taxonomy_id).first()

        if item is None:
            return None

        item.id_parent = form.id_parent
        item.id_taxonomy_type = form.id_taxonomy_type
        item.name = form.name
        item.description = form.description

        self.db.commit()

        return TaxonomyOut.model_validate(item)

    def get_taxonomy_tree(self, taxonomy: models.Taxonomy, tax_names=None) -> list[str]:
        if tax_names is None:
            tax_names = []
        if taxonomy.id_parent is None:
            return tax_names + [taxonomy.name]
        else:
            return self.get_taxonomy_tree(taxonomy.parent, tax_names + [taxonomy.name])

    def search(self, name_filter: str | None = None, filter_types: list[int] | None = None) -> list[TaxonomyOut]:
        query = (self.db.query(self.model))

        if name_filter and len(name_filter) > 0:
            query = query.filter(or_(self.model.name.match(name_filter), self.model.name.like(f'%{name_filter}%')))

        if filter_types and len(filter_types) > 0:
            query = query.filter(self.model.id_taxonomy_type.in_(filter_types))

        taxonomies = query.limit(30).all()
        for tax in taxonomies:
            tax_tree = self.get_taxonomy_tree(tax)[1:]
            tax.path = tax_tree if len(tax_tree) > 0 else []

        return [TaxonomyOut.model_validate(tax) for tax in taxonomies]

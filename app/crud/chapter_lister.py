from typing import List, Type

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.crud.models.taxonomy_dto import TaxonomyForm
from app.database import models


class TaxonomyLister:

    def __init__(self, db: Session, model: Type[models.Taxonomy] = models.Taxonomy) -> None:
        self.db = db
        self.model = model
        super().__init__()

    def get_item(self, taxonomy_id: int) -> models.Taxonomy:
        item = (self.db.query(self.model)
                .options(joinedload(self.model.children).subqueryload(self.model.children))
                .filter(self.model.id == taxonomy_id)
                .first())

        # tax_tree = self.get_taxonomy_tree(item)[1:]
        # item.path = tax_tree if len(tax_tree) > 0 else []
        return item

    def post(self, form: TaxonomyForm) -> models.Taxonomy:
        item = models.Taxonomy()

        item.id_parent = form.id_parent
        item.id_taxonomy_type = form.id_taxonomy_type
        item.name = form.name
        item.description = form.description

        self.db.add(item)
        self.db.commit()
        return item

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

    def put(self, taxonomy_id: int, form: TaxonomyForm) -> models.Taxonomy | None:
        item = self.db.query(models.Taxonomy).filter(models.Taxonomy.id == taxonomy_id).first()

        if item is None:
            return None

        item.id_parent = form.id_parent
        item.id_taxonomy_type = form.id_taxonomy_type
        item.name = form.name
        item.description = form.description

        self.db.commit()

        return item

    def get_taxonomy_tree(self, taxonomy: models.Taxonomy, tax_names=None) -> List[str]:
        if tax_names is None:
            tax_names = []
        if taxonomy.id_parent is None:
            return tax_names + [taxonomy.name]
        else:
            return self.get_taxonomy_tree(taxonomy.parent, tax_names + [taxonomy.name])

    def search(self, name_filter: str | None = None, filter_types: List[int] | None = None):
        query = (self.db.query(self.model))

        if name_filter and len(name_filter) > 0:
            query = query.filter(or_(self.model.name.match(name_filter), self.model.name.like(f'%{name_filter}%')))

        if filter_types and len(filter_types) > 0:
            query = query.filter(self.model.id_taxonomy_type.in_(filter_types))

        taxonomies = query.limit(30).all()
        for tax in taxonomies:
            tax_tree = self.get_taxonomy_tree(tax)[1:]
            tax.path = tax_tree if len(tax_tree) > 0 else []

        return taxonomies

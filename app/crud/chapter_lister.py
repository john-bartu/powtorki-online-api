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
        item = (self.db.query(self.model).
                options(joinedload(self.model.children))
                .filter(self.model.id == taxonomy_id)
                .first())

        tax_tree = self.get_taxonomy_tree(item)[1:]
        item.path = tax_tree if len(tax_tree) > 0 else []
        return item

    def get_items(self, parent_id: int) -> List[models.Taxonomy]:
        items = (self.db.query(self.model).
                 options(joinedload(self.model.children))
                 .filter(self.model.id_parent == parent_id)
                 .all())
        return items

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
        item = self.db.query(models.Taxonomy).options(joinedload(self.model.children)).filter(
            models.Taxonomy.id == taxonomy_id).first()

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

    def search(self, query):
        taxonomies = (self.db.query(self.model)
                      .filter(or_(self.model.name.match(query), self.model.name.like(f'%{query}%')))
                      .limit(30)
                      .all())

        for tax in taxonomies:
            tax_tree = self.get_taxonomy_tree(tax)[1:]
            tax.path = tax_tree if len(tax_tree) > 0 else []

        return taxonomies

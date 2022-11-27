from typing import List, Type

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import models


class TaxonomyLister:

    def __init__(self, db: Session, model: Type[models.Taxonomy], subject_id: int, limit: int = 100) -> None:
        self.db = db
        self.model = model
        self.subject_id = subject_id
        self.pagination_limit = limit

        self.taxonomies_list = self.db.query(self.model).all()
        super().__init__()

    def get_item(self, taxonomy_id: int):
        return self.db.query(self.model).filter(self.model.id == taxonomy_id).first()

    def get_items(self, pagination_no: int = 0) -> List[models.Page]:
        return self.db.query(self.model) \
            .options(joinedload(self.model.children)) \
            .filter(self.model.id_parent == self.subject_id) \
            .offset(self.pagination_limit * pagination_no) \
            .limit(self.pagination_limit) \
            .all()

    def get_taxonomy_tree(self, taxonomy: models.Taxonomy, tax_names=None) -> List[str]:
        if tax_names is None:
            tax_names = []
        if taxonomy.id_parent is None:
            return tax_names + [taxonomy.name]
        else:
            return self.get_taxonomy_tree(taxonomy.parent, tax_names + [taxonomy.name])

    def search(self, query):
        taxonomies = self.db.query(self.model) \
            .filter(or_(self.model.name.match(query), self.model.name.like(f'%{query}%'))) \
            .limit(30) \
            .all()

        for tax in taxonomies:
            tax_tree = self.get_taxonomy_tree(tax)[1:]
            tax.path = tax_tree if len(tax_tree) > 0 else []

        return taxonomies

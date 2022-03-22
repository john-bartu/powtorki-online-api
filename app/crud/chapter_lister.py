from typing import List, Type

from sqlalchemy.orm import Session, joinedload

from app.database import models


class TaxonomyLister:

    def __init__(self, db: Session, model: Type[models.Taxonomy], subject_id: int, limit: int = 100) -> None:
        self.db = db
        self.model = model
        self.subject_id = subject_id
        self.pagination_limit = limit

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

from typing import List, Type

from sqlalchemy.orm import Session, joinedload

from app.database import models
from app.database.models import Page


class ItemLister:
    subject_mapper = {
        'history': 1,
        'civics': 2
    }

    def __init__(self, db: Session, model: Type[models.Page], subject_name, limit: int = 100) -> None:
        self.db = db
        self.model = model
        self.subject_id = self.subject_mapper.get(subject_name)
        self.pagination_limit = limit

        super().__init__()

    def get_item(self, page_id: int):
        return self.db.query(self.model).filter(getattr(self.model, 'id') == page_id).first()

    def get_items(self, pagination_no: int = 0) -> List[Page]:
        print(getattr(self.model, 'taxonomies'))
        return self.db.query(self.model) \
            .join(models.MapPageTaxonomy) \
            .options(joinedload(getattr(self.model, 'taxonomies'))) \
            .filter(models.MapPageTaxonomy.id_taxonomy == self.subject_id) \
            .offset(self.pagination_limit * pagination_no) \
            .limit(self.pagination_limit) \
            .all()

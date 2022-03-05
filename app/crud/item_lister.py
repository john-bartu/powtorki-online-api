from typing import List, Type

from sqlalchemy.orm import Session, joinedload

from app.database import models
from app.database.models import Page


class ItemLister:

    def __init__(self, db: Session, model: Type[models.Page], subject, limit: int = 100) -> None:
        self.db = db
        self.model = model
        self.subject = subject
        self.pagination_limit = limit

        super().__init__()

    def get_item(self, page_id: int):
        return self.db.query(self.model).filter(getattr(self.model, 'id') == page_id).first()

    def get_items(self, pagination_no: int = 0) -> List[Page]:
        return self.db.query(self.model) \
            .options(joinedload(getattr(self.model, 'taxonomies'))) \
            .filter(models.MapPageTaxonomy.id_taxonomy == 1) \
            .offset(self.pagination_limit * pagination_no) \
            .limit(self.pagination_limit) \
            .all()

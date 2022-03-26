from typing import List, Type

from sqlalchemy.orm import Session, joinedload, contains_eager

from app.database import models


class ItemLister:

    def __init__(self, db: Session, model: Type[models.Page], subject_id: int, chapter: int = None,
                 limit: int = 100) -> None:
        self.db = db
        self.model = model
        self.subject_id = subject_id
        self.pagination_limit = limit
        self.chapter_id = chapter

        super().__init__()

    def get_item(self, page_id: int):
        return self.db.query(self.model).filter(getattr(self.model, 'id') == page_id).first()

    def get_items(self, pagination_no: int = 0) -> List[models.Page]:
        print(getattr(self.model, 'taxonomies'))

        if self.model is models.QuizPage:
            return self.db.query(self.model) \
                .join(models.MapPageTaxonomy) \
                .join(models.MapPageAnswer) \
                .join(models.Answer) \
                .options(contains_eager(getattr(self.model, 'taxonomies'))) \
                .options(contains_eager(getattr(self.model, 'answers')).contains_eager(models.MapPageAnswer.answer)) \
                .filter(models.MapPageTaxonomy.id_taxonomy == self.chapter_id) \
                .offset(self.pagination_limit * pagination_no) \
                .limit(self.pagination_limit) \
                .all()
        else:
            return self.db.query(self.model) \
                .join(models.MapPageTaxonomy) \
                .options(joinedload(getattr(self.model, 'taxonomies'))) \
                .filter(models.MapPageTaxonomy.id_taxonomy == self.chapter_id) \
                .offset(self.pagination_limit * pagination_no) \
                .limit(self.pagination_limit) \
                .all()

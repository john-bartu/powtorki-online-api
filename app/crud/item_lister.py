from random import shuffle
from typing import List, Type

from sqlalchemy.orm import Session, joinedload

from app.database import models
from app.render.renderer import page_renderer


class ItemLister:

    def __init__(self, db: Session, model: Type[models.Page], subject_id: int, chapter: int = None,
                 limit: int = 150) -> None:
        self.db = db
        self.model = model
        self.subject_id = subject_id
        self.pagination_limit = limit
        self.chapter_id = chapter

        super().__init__()

    def get_item(self, page_id: int):

        if self.model is models.QuizPage:
            item = (self.db.query(models.QuizPage)
                    .options(joinedload(models.QuizPage.answers)
                             .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer))
                    .filter(self.model.id == page_id).first())

            shuffle(item.answers)
        else:
            item = self.db.query(self.model).filter(self.model.id == page_id).first()

        if item.document:
            item.document = page_renderer(item.document).strip()

        return item

    def get_items(self, pagination_no: int = 0) -> List[models.Page]:
        if self.model is models.QuizPage:
            return (
                self.db.query(self.model)
                    .join(models.MapPageTaxonomy)
                    .join(models.QuizTaxonomy)
                    .options(joinedload(self.model.taxonomies))
                    .filter(models.QuizTaxonomy.id_parent == self.chapter_id)
                    .order_by(models.QuizPage.title)
                    .offset(self.pagination_limit * pagination_no)
                    .limit(self.pagination_limit)
            ).all()
        elif self.model is models.CalendarPage:
            return (
                self.db.query(self.model)
                    .join(models.MapPageTaxonomy)
                    .join(models.Date)
                    .options(joinedload(self.model.taxonomies))
                    .options(joinedload(models.CalendarPage.date))
                    .filter(models.MapPageTaxonomy.id_taxonomy == self.chapter_id)
                    .order_by(models.Date.date_number)
                    .offset(self.pagination_limit * pagination_no)
                    .limit(self.pagination_limit)
            ).all()
        else:
            return (
                self.db.query(self.model)
                    .options(joinedload(getattr(self.model, 'taxonomies')))
                    .filter(models.MapPageTaxonomy.id_taxonomy == self.chapter_id)
                    .join(models.MapPageTaxonomy)
                    .order_by(self.model.title)
                    .offset(self.pagination_limit * pagination_no)
                    .limit(self.pagination_limit)
            ).all()

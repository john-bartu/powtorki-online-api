from random import shuffle
from typing import List

from sqlalchemy.orm import Session, joinedload, selectin_polymorphic

from app.constants import PageTypes
from app.database import models
from app.helpers import get_whole_branch
from app.render.renderer import PageRenderer


class ItemLister:

    def __init__(self, db: Session, limit: int = 25) -> None:
        self.db = db
        self.pagination_limit = limit

        self.filter_taxonomies: List[int] = []
        self.filter_page_types: List[int] = []

        super().__init__()

    def get_item(self, page_id: int):
        renderer = PageRenderer()

        item = (self.db.query(models.Page)
                .options(
            selectin_polymorphic(models.Page, [models.QuizPage, models.VideoScriptPage, models.CalendarPage]),
            joinedload(models.QuizPage.answers)
            .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer),
            joinedload(models.VideoScriptPage.media),
            joinedload(models.CalendarPage.date))
                .filter(models.Page.id == page_id).first())

        if item.document:
            item.document = renderer.render(item.document)

        return item

    def get_items(self, pagination_no: int = 1) -> List[models.Page]:
        if not pagination_no > 0:
            raise ValueError("Page cannot be less than 1")
        pagination_no = pagination_no - 1

        query = (self.db.query(models.Page)  # noqa
        .join(models.Page.taxonomies)
        .join(models.CalendarPage.date, isouter=True)
        .join(models.QuizPage.answers, isouter=True)
        .options(
            selectin_polymorphic(models.Page, [models.QuizPage, models.VideoScriptPage, models.CalendarPage]),
            joinedload(models.QuizPage.answers)
            .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer),
            joinedload(models.VideoScriptPage.media),
            joinedload(models.CalendarPage.date),
            joinedload(models.Page.taxonomies)))

        if len(self.filter_taxonomies) > 0:
            taxonomies = [get_whole_branch(self.db, [taxonomy]) for taxonomy in self.filter_taxonomies][0]
            print(taxonomies)
            query = query.filter(models.MapPageTaxonomy.id_taxonomy.in_(taxonomies))

        if len(self.filter_page_types) > 0:
            query = query.filter(models.Page.id_type.in_(self.filter_page_types))

        if len(self.filter_page_types) == 1:
            page_type = self.filter_page_types[0]
            if page_type == PageTypes.CalendarPage:
                query = query.order_by(models.Date.date_number)
            elif page_type in [PageTypes.CharacterPage, PageTypes.DictionaryPage]:
                query = query.order_by(models.Page.title)
            elif page_type in [PageTypes.VideoScriptPage, PageTypes.DocumentPage, PageTypes.ScriptPage]:
                query = query.order_by(models.Page.order_no)
            else:
                query = query.order_by(models.Page.title)
        else:
            query = query.order_by(models.Page.title)

        results = (query.offset(self.pagination_limit * pagination_no).limit(self.pagination_limit).all())

        for page in results:
            if page.id_type == PageTypes.QuizPage:
                shuffle(page.answers)

        return results

from random import shuffle
from typing import List, Type

from sqlalchemy.orm import Session, joinedload, selectin_polymorphic

from app.database import models
from app.render.renderer import page_renderer


class ItemLister:

    def __init__(self, db: Session, model: Type[models.Page], subject_id: int, chapter: int = None,
                 limit: int = 25) -> None:
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
        elif self.model is models.ScriptPage:
            item = (self.db.query(self.model)
                    .options(selectin_polymorphic(models.ScriptPage, [models.VideoScriptPage]),
                             joinedload(models.VideoScriptPage.media))
                    .filter(self.model.id == page_id)).first()
        else:
            item = self.db.query(self.model).filter(self.model.id == page_id).first()

        if item.document:
            item.document = page_renderer(item.document).strip()

        return item

    def get_whole_taxonomy(self, chapter_id: int):
        taxonomy_selected = self.db.query(models.Taxonomy).with_entities(models.Taxonomy.id, models.Taxonomy.id_parent)
        taxonomy_selected = taxonomy_selected.filter(models.Taxonomy.id == chapter_id)
        taxonomy_selected = taxonomy_selected.cte('cte', recursive=True)

        taxonomy_child = self.db.query(models.Taxonomy).with_entities(models.Taxonomy.id, models.Taxonomy.id_parent)
        taxonomy_child = taxonomy_child.join(taxonomy_selected, models.Taxonomy.id_parent == taxonomy_selected.c.id)

        recursive_q = taxonomy_selected.union(taxonomy_child)

        return [tax[0] for tax in self.db.query(recursive_q).all()]

    def get_items(self, pagination_no: int = 0) -> List[models.Page]:
        if self.subject_id == 2 and (
                self.model is models.CharacterPage or
                self.model is models.DictionaryPage or
                self.model is models.CalendarPage
        ):
            # In Civics list all characters and  in this subject for all taxonomies
            taxonomies = self.get_whole_taxonomy(self.subject_id)
        else:
            taxonomies = self.get_whole_taxonomy(self.chapter_id)

        query = (self.db.query(self.model)
                 .join(models.MapPageTaxonomy)
                 .options(joinedload(self.model.taxonomies))
                 .filter(models.MapPageTaxonomy.id_taxonomy.in_(taxonomies)))

        if self.model is models.QuizPage:
            quizzes = (query
                       .options(joinedload(models.QuizPage.answers)
                                .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer))
                       .order_by(models.QuizPage.title)
                       .offset(self.pagination_limit * pagination_no)
                       .limit(self.pagination_limit)
                       ).all()

            for quiz in quizzes:
                shuffle(quiz.answers)

            return quizzes
        else:
            if self.model is models.CalendarPage:
                query = (query.join(models.Date)
                         .options(joinedload(models.CalendarPage.date))
                         .order_by(models.Date.date_number))
            elif self.model is models.CharacterPage or self.model is models.DictionaryPage:
                query = query.order_by(self.model.title)
            else:
                query = query.order_by(self.model.order_no)
            return (query.offset(self.pagination_limit * pagination_no)
                    .limit(self.pagination_limit)).all()

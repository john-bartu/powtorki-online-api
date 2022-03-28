from collections import Counter
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.database import models
from app.render.renderer import page_renderer


def compare(s, t):
    return Counter(s) == Counter(t)


class QuizEndpoint:

    def __init__(self, session: Session, quiz_id: int):
        self.session = session
        self.item = self.get_item(quiz_id)

    def get_item(self, page_id: int) -> models.QuizPage:
        item = (self.session.query(models.QuizPage)
                .options(joinedload(models.QuizPage.answers)
                         .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer))
                .filter(models.QuizPage.id == page_id).first())

        if item.document:
            item.document = page_renderer(item.document).strip()
        return item

    def answer(self, answers_id: List[int]):

        correct = []
        for answer in self.item.answers:
            if answer.is_correct == 1:
                correct.append(answer.id)

        if compare(answers_id, correct):
            pass  # TODO: log user answer

        return correct

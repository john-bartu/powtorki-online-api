from collections import Counter
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.database import models
from app.database.models import UserQuizAnswer
from app.render.renderer import PageRenderer


def compare(s, t):
    return Counter(s) == Counter(t)


class QuizEndpoint:

    def __init__(self, session: Session, quiz_id: int):
        self.session = session
        self.item = self.get_item(quiz_id)

    def get_item(self, page_id: int) -> models.QuizPage:
        renderer = PageRenderer()

        item = (self.session.query(models.QuizPage)
                .options(joinedload(models.QuizPage.answers)
                         .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer))
                .filter(models.QuizPage.id == page_id).first())

        if item.document:
            item.document = renderer.render(item.document)
        return item

    def answer(self, answers_id: List[int]):

        correct = []
        for answer in self.item.answers:
            if answer.is_correct == 1:
                correct.append(answer.id)

        try:
            for answer_id in answers_id:
                log = UserQuizAnswer()
                log.id_answer = answer_id
                # log.id_user = TODO: log user session id
                self.session.add(log)

            self.session.flush()
            self.session.commit()
        except Exception as e:
            print("error:")
            print(str(e))

        if compare(answers_id, correct):
            pass  # TODO: return array of answers, null if not match

        return correct

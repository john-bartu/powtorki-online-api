from collections import Counter
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.constants import ActivitySettings
from app.database import models
from app.database.models import UserQuizAnswer


def compare(s, t):
    return Counter(s) == Counter(t)


class QuizEndpoint:

    def __init__(self, session: Session, quiz_id: int):
        self.session = session
        self.question_page = self.get_item(quiz_id)

    def get_item(self, page_id: int) -> models.QuizPage:
        item = (self.session.query(models.QuizPage)
                .options(joinedload(models.QuizPage.answers)
                         .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer))
                .filter(models.QuizPage.id == page_id).first())
        return item

    def answer(self, answers_id: List[int]):

        correct = []
        wrong = []
        for answer in self.question_page.answers:
            if answer.is_correct == 1:
                correct.append(answer.id)
            else:
                wrong.append(answer.id)

        try:
            for answer_id in answers_id:
                log = UserQuizAnswer()
                log.id_answer = answer_id
                # log.id_user = TODO: log user session id
                self.session.add(log)
        except Exception as e:
            print("error:", str(e))

        user_activity = models.UserActivity()
        user_activity.id_user = 1
        user_activity.id_page = self.question_page.id

        if compare(answers_id, correct):
            user_activity.knowledge = ActivitySettings.correct_answer
            pass  # TODO: return array of answers, null if not match
        else:
            user_activity.knowledge = ActivitySettings.incorrect_answer

        self.session.add(user_activity)
        self.session.commit()

        return correct

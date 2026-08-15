import logging
from collections import Counter

from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import TokenData
from app.constants import ActivitySettings
from app.database import models
from app.database.models import UserQuizAnswer
from app.helpers import get_descendants

logger = logging.getLogger(__name__)


def compare(s, t):
    return Counter(s) == Counter(t)


class QuizService:

    def __init__(self, session: Session, quiz_id: int, current_user: TokenData | None = None):
        self.session = session
        self.current_user = current_user
        self.question_page = self.get_item(quiz_id)

    def get_item(self, page_id: int) -> models.QuizPage:
        item = (self.session.query(models.QuizPage)
                .options(joinedload(models.QuizPage.answers)
                         .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer))
                .filter(models.QuizPage.id == page_id).first())
        return item

    def answer(self, answers_id: list[int], id_test_session: int | None = None):

        correct: list[int] = []
        wrong = []
        for answer in self.question_page.answers:
            if answer.is_correct == 1:
                correct.append(answer.id)
            else:
                wrong.append(answer.id)

        is_correct = compare(answers_id, correct)

        if self.current_user is not None:
            try:
                for answer_id in answers_id:
                    log = UserQuizAnswer()
                    log.id_answer = answer_id
                    log.id_user = self.current_user.id
                    self.session.add(log)
            except Exception:
                logger.exception("Error saving quiz answer")

            user_activity = models.UserActivity()
            user_activity.id_user = self.current_user.id
            user_activity.id_page = self.question_page.id
            user_activity.knowledge = (ActivitySettings.correct_answer if is_correct
                                        else ActivitySettings.incorrect_answer)
            self.session.add(user_activity)

            if id_test_session is not None:
                session = (self.session.query(models.TestSession)
                           .filter(models.TestSession.id == id_test_session,
                                   models.TestSession.id_user == self.current_user.id,
                                   models.TestSession.status == "in_progress").first())
                eligible = False
                if session is not None and self.question_page.id_type in session.included_types:
                    taxonomy_ids = get_descendants(self.session, [session.id_taxonomy])
                    eligible = (self.session.query(models.MapPageTaxonomy)
                               .filter(models.MapPageTaxonomy.id_page == self.question_page.id,
                                       models.MapPageTaxonomy.id_taxonomy.in_(taxonomy_ids)).first() is not None)
                already_graded = (self.session.query(models.TestSessionPage)
                                  .filter(models.TestSessionPage.id_test_session == id_test_session,
                                          models.TestSessionPage.id_page == self.question_page.id).first()
                                  if eligible else None)
                if eligible and already_graded is None:
                    # answers_id holds PageAnswer.id (the map_question_answer row id, see
                    # QuizAnswers.vue/LearningQuizCard.vue) -- translate to the underlying
                    # Answer.id so TestSessionPage.id_answer (FK answers.id) actually resolves
                    # to the given answer's text for session review.
                    given_answer_id = next((a.id_answer for a in self.question_page.answers
                                            if a.id == answers_id[0]), None) if answers_id else None
                    self.session.add(models.TestSessionPage(
                        id_test_session=session.id,
                        id_page=self.question_page.id,
                        is_known=is_correct,
                        id_answer=given_answer_id,
                    ))

            self.session.commit()

        return correct

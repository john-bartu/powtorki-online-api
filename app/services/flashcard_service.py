import logging

from sqlalchemy.orm import Session

from app.auth.dependencies import TokenData
from app.constants import ActivitySettings, LearningSettings
from app.database import models
from app.helpers import get_descendants

logger = logging.getLogger(__name__)


class FlashcardGradeError(ValueError):
    pass


class FlashcardService:
    """Grades Character/Date/QA/Dictionary pages inside Learning Mode.

    Flashcard grading only exists inside a session, and a session can only be
    created by an authenticated user (POST /test-sessions requires login) — so
    unlike quiz answering (which also works standalone, outside any session,
    and stays open to anonymous callers there), grading here always requires
    a real, owned, in-progress session. There is no anonymous/no-op path.
    """

    def __init__(self, db: Session):
        self.db = db

    def grade(self, page_id: int, known: bool, current_user: TokenData, id_test_session: int) -> bool:
        page = self.db.query(models.Page).filter(models.Page.id == page_id).first()
        if page is None:
            raise FlashcardGradeError(f"Page {page_id} not found")
        if page.id_type not in LearningSettings.flashcard_types:
            raise FlashcardGradeError(f"Page {page_id} is not a flashcard-graded type")

        session = (self.db.query(models.TestSession)
                   .filter(models.TestSession.id == id_test_session,
                           models.TestSession.id_user == current_user.id,
                           models.TestSession.status == "in_progress").first())
        if session is None:
            raise FlashcardGradeError(f"Test session {id_test_session} not found or not active")

        if page.id_type not in session.included_types:
            raise FlashcardGradeError(f"Page {page_id} is not part of test session {id_test_session}")
        taxonomy_ids = get_descendants(self.db, [session.id_taxonomy])
        in_branch = (self.db.query(models.MapPageTaxonomy)
                     .filter(models.MapPageTaxonomy.id_page == page_id,
                             models.MapPageTaxonomy.id_taxonomy.in_(taxonomy_ids)).first())
        if in_branch is None:
            raise FlashcardGradeError(f"Page {page_id} is not part of test session {id_test_session}")

        already_graded = (self.db.query(models.TestSessionPage)
                          .filter(models.TestSessionPage.id_test_session == id_test_session,
                                  models.TestSessionPage.id_page == page_id).first())
        if already_graded is None:
            self.db.add(models.TestSessionPage(
                id_test_session=session.id,
                id_page=page_id,
                is_known=known,
            ))

        user_activity = models.UserActivity()
        user_activity.id_user = current_user.id
        user_activity.id_page = page_id
        user_activity.knowledge = ActivitySettings.correct_answer if known else ActivitySettings.incorrect_answer
        self.db.add(user_activity)

        self.db.commit()
        return known

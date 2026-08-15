import logging
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload, selectin_polymorphic

from app.auth.dependencies import TokenData
from app.constants import LearningSettings, PageTypes
from app.database import models
from app.helpers import get_descendants
from app.services.models.page_dto import PageDTO
from app.services.page_service import _strip_correct_answers

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {PageTypes.QuizPage} | LearningSettings.flashcard_types


class TestSessionNotFoundError(ValueError):
    pass


class TestSessionService:

    def __init__(self, db: Session):
        self.db = db

    def get_owned_session(self, id_test_session: int, id_user: int) -> models.TestSession:
        session = (self.db.query(models.TestSession)
                   .filter(models.TestSession.id == id_test_session,
                           models.TestSession.id_user == id_user).first())
        if session is None:
            raise TestSessionNotFoundError(f"Test session {id_test_session} not found")
        return session

    def create(self, current_user: TokenData, id_taxonomy: int, included_types: list[int]) -> models.TestSession:
        # A student starting a fresh session for this taxonomy is implicitly done with
        # whatever they left open there before -- close it out rather than leaving it
        # dangling in_progress forever (which would otherwise make "active session"
        # detection keep surfacing stale, abandoned sessions).
        stale_sessions = (self.db.query(models.TestSession)
                          .filter(models.TestSession.id_user == current_user.id,
                                  models.TestSession.id_taxonomy == id_taxonomy,
                                  models.TestSession.status == "in_progress").all())
        for stale in stale_sessions:
            self.complete(stale)

        session = models.TestSession(
            id_user=current_user.id,
            id_taxonomy=id_taxonomy,
            included_types=[t for t in included_types if t in ALLOWED_TYPES],
            status="in_progress",
        )
        self.db.add(session)
        self.db.commit()
        return session

    def _eligible_page_ids(self, id_taxonomy: int, included_types: list[int], exclude_ids: set[int]) -> list[int]:
        taxonomy_ids = get_descendants(self.db, [id_taxonomy])
        rows = (self.db.query(models.Page.id)
                .join(models.MapPageTaxonomy, models.MapPageTaxonomy.id_page == models.Page.id)
                .filter(models.MapPageTaxonomy.id_taxonomy.in_(taxonomy_ids))
                .filter(models.Page.id_type.in_(included_types))
                .distinct()
                .all())
        return [row[0] for row in rows if row[0] not in exclude_ids]

    def _history_by_page(self, id_user: int, id_page_ids: list[int]) -> dict[int, list]:
        """Per-page grading history for this user, most recent first."""
        by_page: dict[int, list] = {pid: [] for pid in id_page_ids}
        if id_page_ids:
            rows = (self.db.query(models.TestSessionPage.id_page, models.TestSessionPage.is_known,
                                   models.TestSessionPage.time_answered)
                    .join(models.TestSession, models.TestSession.id == models.TestSessionPage.id_test_session)
                    .filter(models.TestSession.id_user == id_user,
                            models.TestSessionPage.id_page.in_(id_page_ids))
                    .order_by(models.TestSessionPage.id_page, models.TestSessionPage.time_answered.desc())
                    .all())
            for id_page, is_known, time_answered in rows:
                by_page[id_page].append((is_known, time_answered))
        return by_page

    def _score_candidates(self, id_user: int, id_page_ids: list[int]) -> dict[int, dict]:
        by_page = self._history_by_page(id_user, id_page_ids)
        scores = {}
        for id_page, history in by_page.items():
            times_seen = len(history)
            times_correct = sum(1 for is_known, _ in history if is_known)
            streak_correct = 0
            for is_known, _ in history:
                if not is_known:
                    break
                streak_correct += 1
                if streak_correct >= LearningSettings.streak_cap:
                    break
            scores[id_page] = {
                "times_seen": times_seen,
                "times_correct": times_correct,
                "last_answered_at": history[0][1] if history else None,
                "streak_correct": streak_correct,
            }
        return scores

    @staticmethod
    def _weighted_sample(ids: list[int], weights: dict[int, float], k: int) -> list[int]:
        if k <= 0 or not ids:
            return []
        pool = list(ids)
        chosen = []
        for _ in range(min(k, len(pool))):
            pick = random.choices(pool, weights=[weights[pid] for pid in pool], k=1)[0]
            chosen.append(pick)
            pool.remove(pick)
        return chosen

    def next_chunk(self, session: models.TestSession, count: int = LearningSettings.chunk_size) -> list[PageDTO]:
        already_shown = {row[0] for row in (self.db.query(models.TestSessionPage.id_page)
                                             .filter(models.TestSessionPage.id_test_session == session.id).all())}
        eligible_ids = self._eligible_page_ids(session.id_taxonomy, session.included_types, already_shown)
        if not eligible_ids:
            return []

        scores = self._score_candidates(session.id_user, eligible_ids)
        now = datetime.utcnow()

        due_ids, not_due_ids, weights = [], [], {}
        for id_page in eligible_ids:
            s = scores[id_page]
            streak = min(s["streak_correct"], LearningSettings.streak_cap)
            last_answered_at = s["last_answered_at"]
            interval = timedelta(days=LearningSettings.interval_days[streak])
            is_due = last_answered_at is None or last_answered_at <= now - interval
            overdue_days = max(0.0, (now - (last_answered_at + interval)).total_seconds() / 86400) \
                if last_answered_at is not None else 0.0
            weights[id_page] = LearningSettings.base_weight[streak] * (1 + overdue_days)
            (due_ids if is_due else not_due_ids).append(id_page)

        selected = self._weighted_sample(due_ids, weights, count)
        if len(selected) < count:
            remainder = [pid for pid in not_due_ids if pid not in selected]
            selected += self._weighted_sample(remainder, weights, count - len(selected))

        return self._dtos_for(selected)

    def _dtos_for(self, page_ids: list[int]) -> list[PageDTO]:
        if not page_ids:
            return []
        pages = (self.db.query(models.Page)
                 .options(selectin_polymorphic(models.Page, [models.QuizPage, models.CalendarPage]),
                          joinedload(models.QuizPage.answers),
                          joinedload(models.CalendarPage.date))
                 .filter(models.Page.id.in_(page_ids)).all())
        pages_by_id = {p.id: p for p in pages}
        ordered = [pages_by_id[pid] for pid in page_ids if pid in pages_by_id]
        dtos = [PageDTO.model_validate(p) for p in ordered]
        for dto in dtos:
            _strip_correct_answers(dto)
        return dtos

    def _stats(self, session: models.TestSession) -> dict:
        rows = (self.db.query(models.TestSessionPage.is_known, models.Page.id_type)
                .join(models.Page, models.Page.id == models.TestSessionPage.id_page)
                .filter(models.TestSessionPage.id_test_session == session.id).all())
        total = len(rows)
        correct = sum(1 for is_known, _ in rows if is_known)
        by_type: dict[int, dict] = {}
        for is_known, id_type in rows:
            entry = by_type.setdefault(id_type, {"total": 0, "correct": 0})
            entry["total"] += 1
            entry["correct"] += 1 if is_known else 0
        for entry in by_type.values():
            entry["percent_correct"] = entry["correct"] / entry["total"] * 100 if entry["total"] else None
        return {
            "total": total,
            "correct": correct,
            "incorrect": total - correct,
            "percent_correct": (correct / total * 100) if total else None,
            "by_type": by_type,
        }

    def get_progress(self, session: models.TestSession) -> dict:
        return self._stats(session)

    def complete(self, session: models.TestSession) -> dict:
        session.status = "completed"
        session.time_completed = datetime.utcnow()
        self.db.commit()
        return self._stats(session)

    def practice(self, id_taxonomy: int, included_types: list[int], exclude_ids: list[int]) -> list[PageDTO]:
        included_types = [t for t in included_types if t in ALLOWED_TYPES]
        eligible_ids = self._eligible_page_ids(id_taxonomy, included_types, set(exclude_ids))
        if not eligible_ids:
            return []
        selected = random.sample(eligible_ids, k=min(LearningSettings.chunk_size, len(eligible_ids)))
        return self._dtos_for(selected)

    @staticmethod
    def _aggregate(entries: list[dict]) -> dict | None:
        if not entries:
            return None
        known_count = sum(1 for e in entries if e["last_correct"])
        return {
            "pages_graded": len(entries),
            "known_count": known_count,
            "pct_last_correct": known_count / len(entries) * 100,
            "pct_last_3": sum(e["pct_last_3"] for e in entries) / len(entries),
        }

    def knowledge_stats(self, id_user: int, id_taxonomy: int) -> dict:
        """Per-`id_type` (and overall) knowledge %, over every page in this taxonomy branch
        the user has graded at least once via Learning Mode."""
        taxonomy_ids = get_descendants(self.db, [id_taxonomy])
        page_rows = (self.db.query(models.Page.id, models.Page.id_type)
                     .join(models.MapPageTaxonomy, models.MapPageTaxonomy.id_page == models.Page.id)
                     .filter(models.MapPageTaxonomy.id_taxonomy.in_(taxonomy_ids))
                     .filter(models.Page.id_type.in_(ALLOWED_TYPES))
                     .distinct().all())
        id_type_by_page = dict(page_rows)
        history = self._history_by_page(id_user, list(id_type_by_page.keys()))

        by_type: dict[int, list[dict]] = {}
        for id_page, rows in history.items():
            if not rows:
                continue
            last_3 = rows[:LearningSettings.streak_cap]
            entry = {
                "last_correct": rows[0][0],
                "pct_last_3": sum(1 for is_known, _ in last_3 if is_known) / len(last_3) * 100,
            }
            by_type.setdefault(id_type_by_page[id_page], []).append(entry)

        return {
            "by_type": {id_type: self._aggregate(entries) for id_type, entries in by_type.items()},
            "overall": self._aggregate([e for entries in by_type.values() for e in entries]),
        }

    def list_sessions(self, id_user: int) -> list[dict]:
        """All of this user's Learning Mode sessions, most recent first, with summary stats."""
        sessions = (self.db.query(models.TestSession)
                   .filter(models.TestSession.id_user == id_user)
                   .order_by(models.TestSession.time_creation.desc())
                   .all())
        if not sessions:
            return []

        taxonomy_names = dict(self.db.query(models.Taxonomy.id, models.Taxonomy.name)
                              .filter(models.Taxonomy.id.in_({s.id_taxonomy for s in sessions})).all())
        return [{
            "id": s.id,
            "id_taxonomy": s.id_taxonomy,
            "taxonomy_name": taxonomy_names.get(s.id_taxonomy),
            "status": s.status,
            "time_creation": s.time_creation,
            "time_completed": s.time_completed,
            "progress": self._stats(s),
        } for s in sessions]

    def get_session_review(self, session: models.TestSession) -> list[dict]:
        """Every graded page in this session, oldest first, with the given/correct answer
        text for quiz pages (flashcard grades only ever carry the known/unknown mark).

        Each item embeds a shallow page representation (title/document/note/date) so the
        frontend can preview it without a separate per-page fetch -- deliberately not the
        full PageDTO (no taxonomies/media/answers), just enough to render the content."""
        rows = (self.db.query(models.TestSessionPage, models.Page, models.Date)
                .join(models.Page, models.Page.id == models.TestSessionPage.id_page)
                .outerjoin(models.Date, models.Date.id_page == models.Page.id)
                .filter(models.TestSessionPage.id_test_session == session.id)
                .order_by(models.TestSessionPage.time_answered)
                .all())

        quiz_page_ids = [tsp.id_page for tsp, page, _ in rows if page.id_type == PageTypes.QuizPage]
        correct_answers: dict[int, str] = {}
        if quiz_page_ids:
            correct_rows = (self.db.query(models.MapPageAnswer.id_question, models.Answer.answer)
                           .join(models.Answer, models.Answer.id == models.MapPageAnswer.id_answer)
                           .filter(models.MapPageAnswer.id_question.in_(quiz_page_ids),
                                   models.MapPageAnswer.is_correct.is_(True))
                           .all())
            correct_answers = dict(correct_rows)

        given_answer_ids = [tsp.id_answer for tsp, _, _ in rows if tsp.id_answer is not None]
        given_answers: dict[int, str] = {}
        if given_answer_ids:
            given_answers = dict(self.db.query(models.Answer.id, models.Answer.answer)
                                 .filter(models.Answer.id.in_(given_answer_ids)).all())

        return [{
            "id_page": tsp.id_page,
            "title": page.title,
            "id_type": page.id_type,
            "is_known": tsp.is_known,
            "time_answered": tsp.time_answered,
            "given_answer": given_answers.get(tsp.id_answer) if tsp.id_answer is not None else None,
            "correct_answer": correct_answers.get(tsp.id_page) if page.id_type == PageTypes.QuizPage else None,
            "page": {
                "id": page.id,
                "id_type": page.id_type,
                "id_sub_type": page.id_sub_type,
                "title": page.title,
                "document": page.document,
                "note": page.note,
                "date": {"date_text": date.date_text, "date_number": date.date_number} if date else None,
            },
        } for tsp, page, date in rows]

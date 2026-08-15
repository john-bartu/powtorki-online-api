"""Learning Mode (TestSession) tests.

These exercise TestSessionService.next_chunk against real taxonomy/page/session
rows, but everything is created inside app_tests.conftest's db_session fixture,
which wraps the whole test in an outer transaction that gets rolled back at
teardown -- nothing here is ever actually persisted to the dev DB.

Exact draw order within a single next_chunk call is intentionally randomized
(weighted sampling, see TestSessionService.next_chunk), so these tests assert
what next_chunk guarantees deterministically instead: no repeats within a
session, full coverage before exhaustion, and that a page which was very
recently mastered (streak_correct capped, so not "due" yet) is excluded from
the very next chunk rather than reappearing immediately.
"""
import uuid
from datetime import datetime, timedelta

import pytest

from app.auth.dependencies import TokenData
from app.constants import LearningSettings, PageSubTypes, PageTypes, TaxonomyTypes
from app.database import models
from app.services.test_session_service import TestSessionService


def make_user(db_session) -> models.User:
    user = models.User(email=f"test-{uuid.uuid4()}@example.invalid", password="x", disabled=False, id_role=2)
    db_session.add(user)
    db_session.commit()
    return user


def make_chapter_with_pages(db_session, count: int, id_type: int = PageTypes.CharacterPage) -> tuple[models.Taxonomy, list[models.Page]]:
    taxonomy = models.Taxonomy(id_taxonomy_type=TaxonomyTypes.ChapterTaxonomy, name=f"Test chapter {uuid.uuid4()}")
    db_session.add(taxonomy)
    db_session.commit()

    pages = []
    for i in range(count):
        page = models.CharacterPage() if id_type == PageTypes.CharacterPage else models.Page()
        page.title = f"Test page {i} {uuid.uuid4()}"
        page.id_sub_type = PageSubTypes.Character if id_type == PageTypes.CharacterPage else PageSubTypes.DocumentPage
        db_session.add(page)
        db_session.flush()
        db_session.add(models.MapPageTaxonomy(id_page=page.id, id_taxonomy=taxonomy.id, order_no=i))
        pages.append(page)
    db_session.commit()
    return taxonomy, pages


def grade(db_session, id_test_session: int, id_page: int, is_known: bool, time_answered: datetime | None = None):
    row = models.TestSessionPage(id_test_session=id_test_session, id_page=id_page, is_known=is_known)
    if time_answered is not None:
        row.time_answered = time_answered
    db_session.add(row)
    db_session.commit()


def grade_in_own_session(db_session, service: TestSessionService, current_user: TokenData, id_taxonomy: int,
                         id_page: int, is_known: bool, time_answered: datetime | None = None):
    """map_test_session_page has a UNIQUE(id_test_session, id_page) constraint -- a page can only
    be graded once per session. To build up multi-event history for the *same* page (as happens
    across separate real Learning Mode sessions on different days), each grade needs its own
    session, same as it would in production."""
    session = service.create(current_user, id_taxonomy, [PageTypes.CharacterPage])
    grade(db_session, session.id, id_page, is_known, time_answered)
    service.complete(session)


def test_next_chunk_never_repeats_and_exhausts_pool(db_session):
    user = make_user(db_session)
    taxonomy, pages = make_chapter_with_pages(db_session, 7)
    page_ids = {p.id for p in pages}

    current_user = TokenData(id=user.id, email=user.email, disabled=False)
    service = TestSessionService(db_session)
    session = service.create(current_user, taxonomy.id, [PageTypes.CharacterPage])

    seen: set[int] = set()
    for _ in range(10):  # generous upper bound; real termination is asserted below
        chunk = service.next_chunk(session, count=3)
        if not chunk:
            break
        chunk_ids = [p.id for p in chunk]
        assert len(chunk_ids) == len(set(chunk_ids)), "a single chunk must not contain duplicates"
        assert not (seen & set(chunk_ids)), "a page must never be shown twice in the same session"
        for page in chunk:
            grade(db_session, session.id, page.id, is_known=True)
            seen.add(page.id)
    else:
        pytest.fail("next_chunk never reported exhaustion")

    assert seen == page_ids, "every eligible page must be shown exactly once before exhaustion"
    assert service.next_chunk(session, count=3) == [], "next_chunk must stay empty once the pool is exhausted"


def test_next_chunk_excludes_a_just_mastered_page(db_session):
    user = make_user(db_session)
    taxonomy, pages = make_chapter_with_pages(db_session, 8)
    mastered_page, unseen_pages = pages[0], pages[1:]

    current_user = TokenData(id=user.id, email=user.email, disabled=False)
    service = TestSessionService(db_session)

    # streak_cap prior (separate, completed) sessions where mastered_page was answered
    # correctly, just now -- streak_correct caps at 3, which carries a multi-day
    # "not due yet" interval, so it should not resurface immediately.
    now = datetime.utcnow()
    for i in range(LearningSettings.streak_cap):
        grade_in_own_session(db_session, service, current_user, taxonomy.id, mastered_page.id, True,
                             time_answered=now - timedelta(seconds=LearningSettings.streak_cap - i))

    new_session = service.create(current_user, taxonomy.id, [PageTypes.CharacterPage])
    # due pool (7 unseen pages) already covers count, so nothing needs to be padded
    # in from the not-yet-due mastered page -- its exclusion here is deterministic.
    chunk = service.next_chunk(new_session, count=len(unseen_pages))

    chunk_ids = {p.id for p in chunk}
    assert mastered_page.id not in chunk_ids
    assert chunk_ids <= {p.id for p in unseen_pages}
    assert len(chunk_ids) == len(unseen_pages)


def test_score_candidates_tracks_recency_and_caps_streak(db_session):
    user = make_user(db_session)
    taxonomy, pages = make_chapter_with_pages(db_session, 2)
    streaky_page, capped_page = pages

    current_user = TokenData(id=user.id, email=user.email, disabled=False)
    service = TestSessionService(db_session)

    # map_test_session_page.time_answered is a MySQL DATETIME (second precision, no
    # fractional seconds) -- strip microseconds so the round-tripped value compares equal.
    base = datetime.utcnow().replace(microsecond=0) - timedelta(hours=1)
    # streaky_page: incorrect, correct, correct, correct (oldest -> newest), one grade per session
    # (map_test_session_page only allows one row per (session, page) pair -- see grade_in_own_session).
    history = [False, True, True, True]
    for i, is_known in enumerate(history):
        grade_in_own_session(db_session, service, current_user, taxonomy.id, streaky_page.id, is_known,
                             time_answered=base + timedelta(minutes=i))

    # capped_page: four corrects in a row -- streak must cap at LearningSettings.streak_cap, not 4
    for i in range(4):
        grade_in_own_session(db_session, service, current_user, taxonomy.id, capped_page.id, True,
                             time_answered=base + timedelta(minutes=i))

    scores = service._score_candidates(user.id, [streaky_page.id, capped_page.id])

    assert scores[streaky_page.id]["times_seen"] == 4
    assert scores[streaky_page.id]["times_correct"] == 3
    assert scores[streaky_page.id]["streak_correct"] == 3
    assert scores[streaky_page.id]["last_answered_at"] == base + timedelta(minutes=3)

    assert scores[capped_page.id]["times_seen"] == 4
    assert scores[capped_page.id]["times_correct"] == 4
    assert scores[capped_page.id]["streak_correct"] == LearningSettings.streak_cap

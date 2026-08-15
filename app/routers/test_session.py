from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import TokenData, get_current_user
from app.database.database import get_db
from app.services.flashcard_service import FlashcardGradeError, FlashcardService
from app.services.test_session_service import TestSessionNotFoundError, TestSessionService

router = APIRouter()


class CreateTestSessionForm(BaseModel):
    id_taxonomy: int
    included_types: list[int]


class FlashcardGradeForm(BaseModel):
    known: bool
    id_test_session: int


def _session_summary(session, progress: dict | None = None) -> dict:
    return {
        "id": session.id,
        "id_taxonomy": session.id_taxonomy,
        "included_types": session.included_types,
        "status": session.status,
        "progress": progress,
    }


@router.post("/test-sessions")
def create_test_session(form: CreateTestSessionForm,
                        current_user: TokenData = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    session = TestSessionService(db).create(current_user, form.id_taxonomy, form.included_types)
    return _session_summary(session)


@router.get("/test-sessions")
def list_test_sessions(current_user: TokenData = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    return TestSessionService(db).list_sessions(current_user.id)


@router.get("/test-sessions/practice")
def practice_chunk(id_taxonomy: int,
                   included_types: list[int] = Query(default=[]),
                   exclude: list[int] = Query(default=[]),
                   db: Session = Depends(get_db)):
    return TestSessionService(db).practice(id_taxonomy, included_types, exclude)


@router.get("/test-sessions/{id_test_session}")
def get_test_session(id_test_session: int,
                     current_user: TokenData = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    service = TestSessionService(db)
    try:
        session = service.get_owned_session(id_test_session, current_user.id)
    except TestSessionNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    return _session_summary(session, service.get_progress(session))


@router.get("/test-sessions/{id_test_session}/pages")
def get_test_session_pages(id_test_session: int,
                           current_user: TokenData = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    service = TestSessionService(db)
    try:
        session = service.get_owned_session(id_test_session, current_user.id)
    except TestSessionNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    return service.get_session_review(session)


@router.post("/test-sessions/{id_test_session}/next-chunk")
def next_chunk(id_test_session: int,
              current_user: TokenData = Depends(get_current_user),
              db: Session = Depends(get_db)):
    service = TestSessionService(db)
    try:
        session = service.get_owned_session(id_test_session, current_user.id)
    except TestSessionNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Test session is not in progress")
    return service.next_chunk(session)


@router.post("/test-sessions/{id_test_session}/complete")
def complete_test_session(id_test_session: int,
                          current_user: TokenData = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    service = TestSessionService(db)
    try:
        session = service.get_owned_session(id_test_session, current_user.id)
    except TestSessionNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    return service.complete(session)


@router.post("/flashcards/{page_id}/grade")
def grade_flashcard(page_id: int, form: FlashcardGradeForm,
                    current_user: TokenData = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    try:
        known = FlashcardService(db).grade(page_id, form.known, current_user, form.id_test_session)
        return {"known": known}
    except FlashcardGradeError as err:
        raise HTTPException(status_code=404, detail=str(err))

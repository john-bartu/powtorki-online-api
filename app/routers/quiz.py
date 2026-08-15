from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import TokenData, get_current_user_optional
from app.database.database import get_db
from app.services.quiz_service import QuizService

router = APIRouter()


class Answer(BaseModel):
    answers: list[int]
    id_test_session: int | None = None


@router.post("/quiz/{page_id}")
def post_quiz_answer(page_id: int, answer_data: Answer,
                     current_user: TokenData | None = Depends(get_current_user_optional),
                     db: Session = Depends(get_db)):
    try:
        quiz = QuizService(db, page_id, current_user=current_user)
        correct = quiz.answer(answer_data.answers, id_test_session=answer_data.id_test_session)
        return correct
    except Exception as err:
        raise HTTPException(status_code=404, detail=str(err))

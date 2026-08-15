from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.quiz_service import QuizService

router = APIRouter()


class Answer(BaseModel):
    answers: list[int]


@router.post("/quiz/{page_id}")
def post_quiz_answer(page_id: int, answer_data: Answer, db: Session = Depends(get_db)):
    try:
        quiz = QuizService(db, page_id)
        correct = quiz.answer(answer_data.answers)
        return correct
    except Exception as err:
        raise HTTPException(status_code=404, detail=str(err))

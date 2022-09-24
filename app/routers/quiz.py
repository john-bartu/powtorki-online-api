import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.crud.quiz_endpoint import QuizEndpoint
from app.database.database import get_db

router = APIRouter()


class Answer(BaseModel):
    answers: List[int]


@router.post("/quiz/{page_id}")
def post_quiz_answer(page_id: int, answer_data: Answer, db: Session = Depends(get_db)):
    try:
        quiz = QuizEndpoint(db, page_id)
        correct = quiz.answer(answer_data.answers)
        return json.dumps(correct)
    except Exception as err:
        raise HTTPException(status_code=404, detail=err)

from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.item_lister import ItemLister
from app.database import models
from app.database.database import get_db

router = APIRouter()

path_to_model = {
    # podstawowa
    'lesson': models.ScriptPage,
    # lesson_video
    'document': models.DocumentPage,
    'mindmap': models.MindmapPage,

    # uzupelnienia
    'character': models.CharacterPage,
    'word': models.DictionaryPage,
    'date': models.CalendarPage,

    # sprawdz wiedze
    'quiz': models.QuizPage,
    'qa': models.QAPage
}

subject_to_subject_id = {
    'history': 1,
    'civics': 2
}


@router.get("/{subject}/{page_type}")
def get_knowledge(subject: Union[int, str], page_type: str, db: Session = Depends(get_db)):
    if type(subject) is str:
        subject = subject_to_subject_id.get(subject)

    if subject not in subject_to_subject_id.values() or subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    model = path_to_model.get(page_type)

    if model is None:
        raise HTTPException(status_code=404, detail="Knowledge type not found")

    paginator = ItemLister(db, model, subject)
    return paginator.get_items()

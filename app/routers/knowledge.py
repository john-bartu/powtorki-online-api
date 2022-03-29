from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.chapter_lister import TaxonomyLister
from app.crud.item_lister import ItemLister
from app.database import models
from app.database.database import get_db

router = APIRouter()

path_to_model = {
    # podstawowa
    'script': models.ScriptPage,
    # lesson_video
    'document': models.DocumentPage,
    'mindmap': models.MindmapPage,

    # uzupelnienia
    'character': models.CharacterPage,
    'dictionary': models.DictionaryPage,
    'date': models.CalendarPage,

    # sprawdz wiedze
    'quiz': models.QuizPage,
    'qa': models.QAPage
}

subject_to_taxonomy_id = {
    'history': 1,
    'civics': 2
}


@router.get("/{subject}")
def get_knowledge_list(subject: Union[int, str], db: Session = Depends(get_db)):
    if type(subject) is str:
        subject = subject_to_taxonomy_id.get(subject)

    if subject not in subject_to_taxonomy_id.values() or subject is None:
        raise HTTPException(status_code=404, detail="Knowledge subject not found")

    # Assume to list only chapter taxonomies
    paginator = TaxonomyLister(db, models.ChapterTaxonomy, subject)
    return paginator.get_items()


@router.get("/{subject}/{page_type}")
def get_knowledge_list(subject: Union[int, str], page_type: str, chapter: int = None, page_no: int = 0, db: Session = Depends(get_db)):
    if type(subject) is str:
        subject = subject_to_taxonomy_id.get(subject)

    if subject not in subject_to_taxonomy_id.values() or subject is None:
        raise HTTPException(status_code=404, detail="Knowledge subject not found")

    model = path_to_model.get(page_type)

    if model is None:
        raise HTTPException(status_code=404, detail="Knowledge type not found")

    paginator = ItemLister(db, model, subject, chapter)
    return paginator.get_items(page_no)


@router.get("/{subject}/{page_type}/{page_id}")
def get_knowledge_item(subject: Union[int, str], page_type: str, page_id: int, db: Session = Depends(get_db)):
    if type(subject) is str:
        subject = subject_to_taxonomy_id.get(subject)

    if subject not in subject_to_taxonomy_id.values() or subject is None:
        raise HTTPException(status_code=404, detail="Knowledge subject not found")

    model = path_to_model.get(page_type)

    if model is None:
        raise HTTPException(status_code=404, detail="Knowledge type not found")

    page = ItemLister(db, model, subject).get_item(page_id)

    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page

# @router.post("/", response_model=schemas.DbCharacter)
# def create_character(character: schemas.CreateCharacter, db: Session = Depends(get_db)):
#     return character_crud.create_character(db, character)
#
#
# @router.put("/{item_id}", response_model=schemas.DbCharacter)
# def update_character(item_id: int, character: schemas.UpdateCharacter, db: Session = Depends(get_db)):
#     return character_crud.update_character(db, item_id, character)

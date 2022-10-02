from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from app.constants import PageTypes
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


@router.get("/chapter/{chapter_id}")
def get_knowledge_chapter(chapter_id: int = None, db: Session = Depends(get_db)):
    chapter = db.query(models.Taxonomy).filter(models.Taxonomy.id == chapter_id).first()
    subject_id = chapter.get_subject(db)
    whole_taxonomy = chapter.get_all_sub_taxonomies(db)
    query = db.query(models.Page.id_type, func.count(models.Page.id_type)).join(models.MapPageTaxonomy)

    if subject_id == 2:
        civics_common_pages = [PageTypes.CharacterPage, PageTypes.DictionaryPage, PageTypes.CalendarPage]
        subject_taxonomies = (db.query(models.Taxonomy)
                              .filter(models.Taxonomy.id == subject_id).first()
                              ).get_all_sub_taxonomies(db)
        query = (
            query.filter(
                or_(
                    and_(
                        models.MapPageTaxonomy.id_taxonomy.in_(subject_taxonomies),
                        models.Page.id_type.in_(civics_common_pages)
                    ),
                    and_(
                        models.MapPageTaxonomy.id_taxonomy.in_(whole_taxonomy),
                        models.Page.id_type.notin_(civics_common_pages)
                    )
                )))
    else:
        query = query.filter(models.MapPageTaxonomy.id_taxonomy.in_(whole_taxonomy))

    page_count_per_type = query.group_by(models.Page.id_type).all()
    chapter.pages = {page_type[0]: {'count': page_type[1]} for page_type in page_count_per_type}
    return chapter


@router.get("/{subject}/{page_type}")
def get_knowledge_list(subject: Union[int, str], page_type: str, chapter: int = None, page_no: int = 0,
                       db: Session = Depends(get_db)):
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

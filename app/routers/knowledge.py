from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants import PageTypes
from app.crud.chapter_lister import TaxonomyLister
from app.crud.item_lister import ItemLister
from app.crud.models.taxonomy_dto import TaxonomyOut
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

path_to_type = {
    # podstawowa
    'script': PageTypes.ScriptPage,

    # lesson_video
    'document': PageTypes.DocumentPage,
    'mindmap': PageTypes.MindmapPage,

    # uzupelnienia
    'character': PageTypes.CharacterPage,
    'dictionary': PageTypes.DictionaryPage,
    'date': PageTypes.CalendarPage,

    # sprawdz wiedze
    'quiz': PageTypes.QuizPage,
    'qa': PageTypes.QAPage
}

subject_to_taxonomy_id = {
    'history': 1,
    'civics': 2
}


@router.get(
    "/taxonomy/search",
    response_model=list[TaxonomyOut],
)
def get_knowledge_taxonomy(query: str = "", db: Session = Depends(get_db)):
    taxonomy = TaxonomyLister(db, models.Taxonomy, 1)

    search = taxonomy.search(query)
    return search


@router.get(
    "/taxonomy/get/{taxonomy_id}",
    response_model=TaxonomyOut,
)
def get_knowledge_taxonomy(taxonomy_id: int, db: Session = Depends(get_db)):
    taxonomy = TaxonomyLister(db, models.Taxonomy, 1)

    search = taxonomy.get_item(taxonomy_id)
    return search


@router.get("/taxonomy/{subject}")
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
    taxonomy_branch = chapter.get_whole_branch(db)
    page_count_per_type = (db.query(models.Page.id_type, func.count(models.Page.id_type))
                           .join(models.MapPageTaxonomy)
                           .filter(models.MapPageTaxonomy.id_taxonomy.in_(taxonomy_branch))
                           .group_by(models.Page.id_type)
                           .all())

    chapter.pages = {page_type[0]: {'count': page_type[1]} for page_type in page_count_per_type}
    return chapter


@router.get("/pages")
def get_knowledge_list(types: List[str] = Query(default=[]),
                       chapters: List[int] = Query(default=[]),
                       page_no: int = 1,
                       db: Session = Depends(get_db)):
    paginator = ItemLister(db)

    if types is not None:
        types = [path_to_type.get(page_str) for page_str in types]
        paginator.filter_page_types = types

    print('types', types)
    if chapters is not None:
        paginator.filter_taxonomies = [subject_to_taxonomy_id.get(subject_str)
                                       if isinstance(subject_str, str)
                                       else subject_str
                                       for subject_str in chapters]
    print('chapters', chapters)

    return paginator.get_items(page_no)


@router.get("/page/{page_id}")
def get_knowledge_item(page_id: int, db: Session = Depends(get_db)):
    page = ItemLister(db).get_item(page_id)
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

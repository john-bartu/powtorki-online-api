from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_permissions import Allow, Authenticated, All
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.permissions import Permission
from app.constants import PageTypes
from app.crud.chapter_lister import TaxonomyLister
from app.crud.item_lister import ItemLister
from app.crud.models.page_dto import PageForm
from app.crud.models.taxonomy_dto import TaxonomyOut, TaxonomyForm
from app.database import models
from app.database.database import get_db

router = APIRouter()

path_to_model = {
    # podstawowa

    # lesson_video
    'document': models.DocumentPage,

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
    "/types"
)
def get_knowledge_taxonomy(db: Session = Depends(get_db)):
    return db.query(models.PageSubType).all()


@router.get(
    "/taxonomy/search",
    response_model=list[TaxonomyOut],
)
def get_knowledge_taxonomy(query: str = "", db: Session = Depends(get_db)):
    taxonomy = TaxonomyLister(db, models.Taxonomy)

    search = taxonomy.search(query)
    return search


@router.put(
    "/taxonomy/{id_taxonomy}",
    response_model=TaxonomyOut,
    dependencies=[Permission("put", [(Allow, Authenticated, All)])]
)
def get_knowledge_taxonomy(id_taxonomy: int, tax_content: TaxonomyForm, db: Session = Depends(get_db)):
    crud = TaxonomyLister(db, models.Taxonomy)
    tax = crud.put(id_taxonomy, tax_content)
    return tax


@router.delete(
    "/taxonomy/{id_taxonomy}",
    dependencies=[Permission("delete", [(Allow, Authenticated, All)])]

)
def get_knowledge_taxonomy(id_taxonomy: int, db: Session = Depends(get_db)):
    crud = TaxonomyLister(db, models.Taxonomy)
    tax = crud.delete(id_taxonomy)
    return tax


@router.post(
    "/taxonomy",
    response_model=TaxonomyOut,
    dependencies=[Permission("add", [(Allow, Authenticated, All)])]
)
def get_knowledge_taxonomy(tax_content: TaxonomyForm, db: Session = Depends(get_db)):
    crud = TaxonomyLister(db, models.Taxonomy)
    tax = crud.post(tax_content)
    return tax


@router.get(
    "/taxonomy/get/{taxonomy_id}",
    response_model=TaxonomyOut,
)
def get_knowledge_taxonomy(taxonomy_id: int, db: Session = Depends(get_db)):
    taxonomy = TaxonomyLister(db, models.Taxonomy)

    search = taxonomy.get_item(taxonomy_id)
    return search


@router.get("/taxonomy/{subject}")
def get_knowledge_list(subject: Union[int, str, None], db: Session = Depends(get_db)):
    if type(subject) is str:
        subject = subject_to_taxonomy_id.get(subject)

    # Assume to list only chapter taxonomies
    paginator = TaxonomyLister(db, models.Taxonomy)
    return paginator.get_items(subject)


@router.get("/taxonomy")
def get_knowledge_list(types: List[int] = Query(default=[]), db: Session = Depends(get_db)):
    crud = TaxonomyLister(db, models.Taxonomy)
    return crud.search(filter_types=types)


@router.get("/chapter/{chapter_id}")
def get_knowledge_chapter(chapter_id: int = None, db: Session = Depends(get_db)):
    chapter = db.query(models.Taxonomy).filter(models.Taxonomy.id == chapter_id).first()
    taxonomy_branch = chapter.get_whole_branch(db)
    page_count_per_type = (db.query(models.Page.id_sub_type, func.count(models.Page.id_sub_type))
                           .join(models.MapPageTaxonomy)
                           .filter(models.MapPageTaxonomy.id_taxonomy.in_(taxonomy_branch))
                           .group_by(models.Page.id_sub_type)
                           .all())
    chapter.pages = {page_type[0]: {'count': page_type[1]} for page_type in page_count_per_type}
    return chapter


@router.get("/pages")
def get_knowledge_list(types: List[int | str] = Query(default=[]),
                       chapters: List[int] = Query(default=[]),
                       sub_types: List[int] = Query(default=[]),
                       query: str = Query(default=""),
                       page_no: int = 1,
                       db: Session = Depends(get_db)):
    paginator = ItemLister(db)

    if types is not None:
        types_list = []
        for type_str_or_int in types:
            try:
                parsed = int(type_str_or_int)
                types_list.append(parsed)
            except ValueError:
                types_list.append(path_to_type.get(type_str_or_int))

        paginator.filter_page_types = types_list

    if query != "":
        paginator.filter_name = query

    if sub_types is not None:
        paginator.filter_sub_types = sub_types

    if chapters is not None:
        paginator.filter_taxonomies = [subject_to_taxonomy_id.get(subject_str)
                                       if isinstance(subject_str, str)
                                       else subject_str
                                       for subject_str in chapters]

    return paginator.get_items(page_no)


@router.get("/page/{page_id}")
def get_knowledge_item(page_id: int, db: Session = Depends(get_db)):
    page = ItemLister(db).get_item(page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page


@router.get(
    "/page/{page_id}/raw",
    dependencies=[Permission("add", [(Allow, Authenticated, All)])]
)
def get_knowledge_item(page_id: int, db: Session = Depends(get_db)):
    lister = ItemLister(db)
    lister.render_enabled = False
    page = lister.get_item(page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page


@router.put(
    "/page/{page_id}",
    dependencies=[Permission("put", [(Allow, Authenticated, All)])]
)
def put_knowledge_item(page_id: int, page_content: PageForm, db: Session = Depends(get_db)):
    page = ItemLister(db).put_item(page_id, page_content)
    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page


@router.post(
    "/page",
    dependencies=[Permission("post", [(Allow, Authenticated, All)])]
)
def put_knowledge_item(page_content: PageForm, db: Session = Depends(get_db)):
    page = ItemLister(db).post_item(page_content)
    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page

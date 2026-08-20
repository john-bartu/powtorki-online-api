import logging
import shutil
import uuid
from pathlib import Path

from PIL import Image
from PIL.Image import Resampling
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi_permissions import Allow, All
from sqlalchemy.orm import Session

from app.auth.dependencies import TokenData, get_current_user, get_current_user_optional, is_admin
from app.auth.permissions import Permission
from app.constants import Roles
from app.database import models
from app.database.database import get_db
from app.services.models.page_dto import PageForm, PageTaxonomyMoveForm
from app.services.models.taxonomy_dto import TaxonomyOut, TaxonomyForm
from app.services.page_service import PageService, TaxonomyBranchConflictError
from app.services.taxonomy_service import TaxonomyService
from app.services.test_session_service import TestSessionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/types"
)
def get_knowledge_types(db: Session = Depends(get_db)):
    return db.query(models.PageSubType).all()


@router.get(
    "/taxonomy/search",
    response_model=list[TaxonomyOut],
)
def search_knowledge_taxonomy(query: str = "", db: Session = Depends(get_db)):
    taxonomy = TaxonomyService(db, models.Taxonomy)

    search = taxonomy.search(query)
    return search


@router.put(
    "/taxonomy/{taxonomy_id}",
    response_model=TaxonomyOut,
    dependencies=[Permission("put", [(Allow, Roles.AdminPrincipal, All)])]
)
def update_knowledge_taxonomy(taxonomy_id: int, tax_content: TaxonomyForm, db: Session = Depends(get_db)):
    crud = TaxonomyService(db, models.Taxonomy)
    tax = crud.put(taxonomy_id, tax_content)
    return tax


@router.delete(
    "/taxonomy/{taxonomy_id}",
    dependencies=[Permission("delete", [(Allow, Roles.AdminPrincipal, All)])]

)
def delete_knowledge_taxonomy(taxonomy_id: int, db: Session = Depends(get_db)):
    crud = TaxonomyService(db, models.Taxonomy)
    tax = crud.delete(taxonomy_id)
    return tax


@router.post(
    "/taxonomy",
    response_model=TaxonomyOut,
    dependencies=[Permission("add", [(Allow, Roles.AdminPrincipal, All)])]
)
def create_knowledge_taxonomy(tax_content: TaxonomyForm, db: Session = Depends(get_db)):
    crud = TaxonomyService(db, models.Taxonomy)
    tax = crud.post(tax_content)
    return tax


@router.get("/taxonomy/{taxonomy_id}/children")
def get_knowledge_taxonomy_children(taxonomy_id: int, db: Session = Depends(get_db)):
    paginator = TaxonomyService(db, models.Taxonomy)
    return paginator.get_items(taxonomy_id)


@router.get("/taxonomy")
def get_knowledge_taxonomy_list(types: list[int] = Query(default=[]), db: Session = Depends(get_db)):
    crud = TaxonomyService(db, models.Taxonomy)
    return crud.search(filter_types=types)


@router.get("/taxonomy/{taxonomy_id}/knowledge-stats")
def get_taxonomy_knowledge_stats(taxonomy_id: int,
                                 current_user: TokenData = Depends(get_current_user),
                                 db: Session = Depends(get_db)):
    return TestSessionService(db).knowledge_stats(current_user.id, taxonomy_id)


@router.get("/taxonomy/{taxonomy_id}")
def get_knowledge_taxonomy_detail(taxonomy_id: int, db: Session = Depends(get_db)):
    taxonomy = TaxonomyService(db, models.Taxonomy).get(taxonomy_id)
    if taxonomy is None:
        raise HTTPException(status_code=404, detail="Taxonomy not found")
    return taxonomy


@router.put(
    "/taxonomy/{taxonomy_id}/pages/{page_id}",
    dependencies=[Permission("put", [(Allow, Roles.AdminPrincipal, All)])]
)
def move_taxonomy_page(taxonomy_id: int, page_id: int, form: PageTaxonomyMoveForm, db: Session = Depends(get_db)):
    try:
        return PageService(db).move_page_taxonomy(page_id, taxonomy_id, form.id_taxonomy_from)
    except TaxonomyBranchConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete(
    "/taxonomy/{taxonomy_id}/pages/{page_id}",
    dependencies=[Permission("put", [(Allow, Roles.AdminPrincipal, All)])]
)
def remove_taxonomy_page(taxonomy_id: int, page_id: int, db: Session = Depends(get_db)):
    return PageService(db).remove_page_taxonomy(page_id, taxonomy_id)


@router.get("/pages")
def get_knowledge_pages_list(taxonomies: list[int] = Query(default=[]),
                             sub_types: list[int] = Query(default=[]),
                             query: str = Query(default=""),
                             page_no: int = 1,
                             limit: int = 20,
                             current_user: TokenData | None = Depends(get_current_user_optional),
                             db: Session = Depends(get_db)):
    paginator = PageService(db, limit=limit)

    if query != "":
        paginator.filter_name = query

    paginator.filter_sub_types = sub_types
    paginator.filter_taxonomies = taxonomies

    return paginator.get_items(page_no, include_correct_answers=is_admin(current_user))


@router.get("/page/{page_id}")
def get_knowledge_item(page_id: int,
                       current_user: TokenData | None = Depends(get_current_user_optional),
                       db: Session = Depends(get_db)):
    page = PageService(db, current_user=current_user).get_item(page_id, include_correct_answers=is_admin(current_user))
    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page


@router.get(
    "/page/{page_id}/raw",
    dependencies=[Permission("add", [(Allow, Roles.AdminPrincipal, All)])]
)
def get_knowledge_item(page_id: int,
                       current_user: TokenData | None = Depends(get_current_user_optional),
                       db: Session = Depends(get_db)):
    lister = PageService(db)
    lister.render_enabled = False
    page = lister.get_item(page_id, include_correct_answers=is_admin(current_user))
    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page


@router.put(
    "/page/{page_id}",
    dependencies=[Permission("put", [(Allow, Roles.AdminPrincipal, All)])]
)
def put_knowledge_item(page_id: int, page_content: PageForm, db: Session = Depends(get_db)):
    lister = PageService(db)
    lister.render_enabled = False
    try:
        page = lister.put_item(page_id, page_content)
    except TaxonomyBranchConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page


@router.delete(
    "/page/{page_id}",
    dependencies=[Permission("put", [(Allow, Roles.AdminPrincipal, All)])]
)
def delete_knowledge_item(page_id: int, db: Session = Depends(get_db)):
    lister = PageService(db)
    lister.render_enabled = False
    page = lister.delete_item(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page


@router.post(
    "/page",
    dependencies=[Permission("post", [(Allow, Roles.AdminPrincipal, All)])]
)
def post_knowledge_item(page_content: PageForm, db: Session = Depends(get_db)):
    try:
        page = PageService(db).post_item(page_content)
    except TaxonomyBranchConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if page is None:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    else:
        return page


@router.post(
    "/file",
    dependencies=[Permission("post", [(Allow, Roles.AdminPrincipal, All)])]
)
async def post_file(file: UploadFile):
    file_path = Path(file.filename)
    extension = file_path.suffix
    new_name = uuid.uuid4()

    file_hq_dir = Path("file-upload/original")
    file_hq_dir.mkdir(parents=True, exist_ok=True)
    file_hq_location = file_hq_dir / f"{new_name}{extension}"

    file_compressed_dir = Path("file-upload")
    file_compressed_dir.mkdir(parents=True, exist_ok=True)
    file_compressed_location = file_compressed_dir / f"{new_name}.webp"

    file_shadow_location = f"media-upload/{new_name}{extension}"

    with file_hq_location.open("wb+") as file_object:
        # noinspection PyTypeChecker
        shutil.copyfileobj(file.file, file_object)

    img = Image.open(file_hq_location)
    img.thumbnail((2048, 2048), resample=Resampling.LANCZOS)
    img.save(file_compressed_location, format="WEBP")
    return {"imageUrl": f"https://media.powtorkionline.pl/{file_shadow_location}"}

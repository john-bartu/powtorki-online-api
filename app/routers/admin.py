from fastapi import APIRouter, UploadFile, Form, Depends
from fastapi_permissions import Allow, All
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from app.auth.permissions import Permission
from app.constants import PageTypes
from app.database import models
from app.database.database import get_db
from app.routers import Admin
from app.tools.importing import process_documents, process_pdf, process_qa, process_dates, process_characters, \
    process_dictionary, process_quiz

router = APIRouter()

page_type_to_model = {
    PageTypes.ScriptPage: models.ScriptPage,
    PageTypes.DocumentPage: models.DocumentPage,
    PageTypes.CharacterPage: models.CharacterPage,
    PageTypes.DictionaryPage: models.DictionaryPage,
    PageTypes.CalendarPage: models.CalendarPage,
    PageTypes.QuizPage: models.QuizPage,
    PageTypes.QAPage: models.QAPage,
    PageTypes.MindmapPage: models.MindmapPage
}


@router.post("/import_from_file/", dependencies=[Permission("view", [(Allow, Admin, All)])])
def import_from_file(files: list[UploadFile], taxonomy: int = Form(), page_type: int = Form(),
                     db: Session = Depends(get_db)):
    new_pages = []

    tax = db.query(models.ChapterTaxonomy).filter(models.ChapterTaxonomy.id == taxonomy).first()

    if page_type in [PageTypes.DocumentPage, PageTypes.ScriptPage, PageTypes]:
        new_pages += process_documents(page_type_to_model[page_type], files)
    elif page_type in [PageTypes.MindmapPage]:
        new_pages += process_pdf(page_type_to_model[page_type], files)
    elif page_type in [PageTypes.QAPage]:
        for file in files:

            qa_tax = models.QATaxonomy(name=file.filename, id_parent=tax.id)
            db.add(qa_tax)
            for quiz_page in process_qa(file):
                map_page_tax = models.MapPageTaxonomy()
                map_page_tax.taxonomy = qa_tax
                quiz_page.taxonomies.append(map_page_tax)
                db.add(map_page_tax)
                db.add(quiz_page)
    elif page_type in [PageTypes.CalendarPage]:
        for file in files:
            new_pages += process_dates(file, db)
    elif page_type in [PageTypes.CharacterPage]:
        for file in files:
            new_pages += process_characters(file)
    elif page_type in [PageTypes.DictionaryPage]:
        for file in files:
            new_pages += process_dictionary(file)
    elif page_type in [PageTypes.QuizPage]:
        for file in files:
            process_quiz(file, db, tax)
    else:
        raise Exception(f"Unhandled typeId: {page_type}")

    for page in new_pages:
        map_page_tax = models.MapPageTaxonomy()
        map_page_tax.taxonomy = tax
        page.taxonomies.append(map_page_tax)
        db.add(page)
        db.add(map_page_tax)

    print(f"Flushing")
    db.flush()

    return {"filenames": (file.filename for file in files), "taxonomy": taxonomy, "page_type": page_type}


@router.get("/admin/", dependencies=[Permission("view", [(Allow, Admin, All)])])
async def main():
    content = """
<!DOCTYPE html>
<html>
<body>
<form action="/import_from_file/" enctype="multipart/form-data" method="post">
<label>Files: <input name="files" type="file" multiple></label><br>
<label>Type: <select name="page_type" required>
  <option value="2">Materiały do nauki</option>
  <option value="3">Lekcje</option>
  <option value="4">Postacie</option>
  <option value="5">Kalendarz</option>
  <option value="6">Pojęcia</option>
  <option value="7">Pytania i odpowiedzi</option>
  <option value="8">Quiz</option>
  <option value="9">Mapa mysli</option>
</select></label><br>
<label>Taxonomy: <select name="taxonomy" required>
  <option value="228">XVIII Wiek - Historia Polski</option>
  <option value="229">XVIII Wiek - Historia Powszechna</option>
</select></label></br>
<input type="submit">
</form>
</body>
</html>
    """
    return HTMLResponse(content=content)

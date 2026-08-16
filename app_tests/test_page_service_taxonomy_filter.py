"""Verifies GET /pages' taxonomy filter (app.routers.knowledge.get_knowledge_pages_list,
backed by PageService.get_items(filter_taxonomies=...)) at the PageService level -- no
HTTP client needed, mirrors app_tests/test_learning_mode.py's style of exercising
services directly against the real (rolled-back) DB.

This is the mechanism app.components.prosemirror.PoTaxonomyBlock (po-nuxt) relies on to
resolve a `po-taxonomy` block's member pages: any SetTaxonomy id, not just chapters --
renamed from `chapters` to `taxonomies` for exactly that reason.
"""
import uuid

from app.constants import PageSubTypes
from app.database import models
from app.services.page_service import PageService
from app.tools.quiz_extraction import extract_quiz_blocks
from app.tools.quiz_import import make_quiz_set_id_factory


def make_document_page(db_session, title: str) -> models.DocumentPage:
    chapter = models.ChapterTaxonomy(name=f"Test chapter {uuid.uuid4()}")
    db_session.add(chapter)
    db_session.flush()

    page = models.DocumentPage()
    page.title = title
    page.id_sub_type = PageSubTypes.DocumentPage
    db_session.add(page)
    db_session.flush()

    db_session.add(models.MapPageTaxonomy(id_page=page.id, id_taxonomy=chapter.id, order_no=0))
    db_session.flush()
    db_session.refresh(page)

    return page


def test_get_items_filtered_by_a_set_taxonomy_returns_its_quiz_pages_with_answers(db_session):
    document_page = make_document_page(db_session, f"Lekcja {uuid.uuid4()}")
    id_factory = make_quiz_set_id_factory(db_session, document_page)

    html = """
    <p><strong>SPRAWDZ SWOJA WIEDZE:</strong></p>
    <table>
    <tr><td>L.P</td><td></td><td>PRAWDA</td><td>FALSZ</td></tr>
    <tr><td>1.</td><td>First statement</td><td></td><td></td></tr>
    <tr><td>2.</td><td>Second statement</td><td></td><td></td></tr>
    </table>
    <p>Poprawne odpowiedzi: 1/P, 2/F</p>
    """
    _, blocks = extract_quiz_blocks(html, id_factory=id_factory)
    db_session.flush()
    quiz_taxonomy_id = int(blocks[0].placeholder_id)

    service = PageService(db_session, limit=20)
    service.filter_taxonomies = [quiz_taxonomy_id]
    result = service.get_items(1, include_correct_answers=True)

    assert result.total_number == 2
    titles = {dto.title for dto in result.items}
    assert titles == {"First statement", "Second statement"}

    for dto in result.items:
        assert len(dto.answers) == 2
        correct = [a for a in dto.answers if a.is_correct]
        assert len(correct) == 1


def test_get_items_strips_is_correct_when_not_admin(db_session):
    document_page = make_document_page(db_session, f"Lekcja {uuid.uuid4()}")
    id_factory = make_quiz_set_id_factory(db_session, document_page)

    html = """
    <p><strong>SPRAWDZ SWOJA WIEDZE:</strong></p>
    <table>
    <tr><td>L.P</td><td></td><td>PRAWDA</td><td>FALSZ</td></tr>
    <tr><td>1.</td><td>Statement</td><td></td><td></td></tr>
    </table>
    <p>Poprawne odpowiedzi: 1/P</p>
    """
    _, blocks = extract_quiz_blocks(html, id_factory=id_factory)
    db_session.flush()
    quiz_taxonomy_id = int(blocks[0].placeholder_id)

    service = PageService(db_session, limit=20)
    service.filter_taxonomies = [quiz_taxonomy_id]
    result = service.get_items(1, include_correct_answers=False)

    assert all(a.is_correct is None for dto in result.items for a in dto.answers)

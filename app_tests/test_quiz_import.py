"""Verifies app.tools.quiz_import against a real (rolled-back) DB -- see
app_tests.conftest.db_session. Complements app_tests/test_document_conversion.py,
which only checks the extracted QuizAnswerRow/QuizBlock shape without touching
the DB; this checks what actually gets persisted once an id_factory backed by
make_quiz_set_id_factory is plugged into extraction.
"""
import uuid
from pathlib import Path

import pytest

from app.constants import PageSubTypes
from app.database import models
from app.tools.document_conversion import convert_document
from app.tools.quiz_extraction import FALSZ, PRAWDA, extract_quiz_blocks
from app.tools.quiz_import import make_quiz_set_id_factory

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def load_example(name: str) -> str:
    return (EXAMPLES_DIR / name).read_text(encoding="utf-8")


def iter_nodes(node):
    yield node
    for child in node.get("content", []):
        yield from iter_nodes(child)


def make_document_page(db_session, title: str) -> tuple[models.DocumentPage, models.ChapterTaxonomy]:
    chapter = models.ChapterTaxonomy(name=f"Test chapter {uuid.uuid4()}")
    db_session.add(chapter)
    db_session.flush()

    page = models.DocumentPage()
    page.title = title
    page.id_sub_type = PageSubTypes.DocumentPage
    db_session.add(page)
    db_session.flush()

    mapping = models.MapPageTaxonomy(id_page=page.id, id_taxonomy=chapter.id, order_no=0)
    db_session.add(mapping)
    db_session.flush()
    db_session.refresh(page)

    return page, chapter


def test_quiz_import_creates_set_taxonomy_named_after_document_under_its_chapter(db_session):
    document_page, chapter = make_document_page(db_session, f"Lekcja {uuid.uuid4()}")
    id_factory = make_quiz_set_id_factory(db_session, document_page)

    _, blocks = extract_quiz_blocks(load_example("page_25712.html"), id_factory=id_factory)
    db_session.flush()

    assert len(blocks) == 1
    quiz_taxonomy = db_session.get(models.SetTaxonomy, int(blocks[0].placeholder_id))
    assert quiz_taxonomy.name == document_page.title
    assert quiz_taxonomy.id_parent == chapter.id


def test_quiz_import_creates_one_quiz_page_per_row_with_correct_answers(db_session):
    document_page, _ = make_document_page(db_session, f"Lekcja {uuid.uuid4()}")
    id_factory = make_quiz_set_id_factory(db_session, document_page)

    _, blocks = extract_quiz_blocks(load_example("page_25712.html"), id_factory=id_factory)
    db_session.flush()

    quiz_taxonomy_id = int(blocks[0].placeholder_id)
    mappings = (
        db_session.query(models.MapPageTaxonomy)
        .filter_by(id_taxonomy=quiz_taxonomy_id)
        .order_by(models.MapPageTaxonomy.order_no)
        .all()
    )
    assert [m.order_no for m in mappings] == [1, 2, 3, 4, 5, 6]

    expected_correct = {1: FALSZ, 2: FALSZ, 3: PRAWDA, 4: PRAWDA, 5: FALSZ, 6: PRAWDA}
    for mapping in mappings:
        page = mapping.page
        assert isinstance(page, models.QuizPage)
        assert page.id_sub_type == PageSubTypes.Quiz

        answers = {a.answer.answer: a.is_correct for a in page.map_answers}
        assert set(answers) == {PRAWDA, FALSZ}
        assert answers[PRAWDA] != answers[FALSZ]  # exactly one correct choice
        correct_text = PRAWDA if answers[PRAWDA] else FALSZ
        assert correct_text == expected_correct[mapping.order_no]


def test_full_pipeline_embeds_real_persisted_taxonomy_id_in_po_taxonomy_node(db_session):
    document_page, _ = make_document_page(db_session, f"Lekcja {uuid.uuid4()}")
    id_factory = make_quiz_set_id_factory(db_session, document_page)

    result = convert_document(load_example("page_25712.html"), id_factory=id_factory)
    db_session.flush()

    po_taxonomy = next(n for n in iter_nodes(result.document_json) if n["type"] == "po-taxonomy")
    assert po_taxonomy["attrs"]["taxonomy_id"] == result.quiz_blocks[0].placeholder_id
    assert db_session.get(models.SetTaxonomy, int(po_taxonomy["attrs"]["taxonomy_id"])) is not None


def test_second_quiz_block_in_same_document_gets_a_disambiguated_name(db_session):
    document_page, _ = make_document_page(db_session, f"Lekcja {uuid.uuid4()}")
    id_factory = make_quiz_set_id_factory(db_session, document_page)

    snippet = """
    <p><strong>SPRAWDZ SWOJA WIEDZE:</strong></p>
    <table>
    <tr><td>L.P</td><td></td><td>PRAWDA</td><td>FALSZ</td></tr>
    <tr><td>1.</td><td>Statement</td><td></td><td></td></tr>
    </table>
    <p>Poprawne odpowiedzi: 1/P</p>
    """
    html = snippet + snippet

    _, blocks = extract_quiz_blocks(html, id_factory=id_factory)
    db_session.flush()

    assert len(blocks) == 2
    first = db_session.get(models.SetTaxonomy, int(blocks[0].placeholder_id))
    second = db_session.get(models.SetTaxonomy, int(blocks[1].placeholder_id))
    assert first.name == document_page.title
    assert second.name == f"{document_page.title} (2)"


def test_document_without_a_taxonomy_raises_before_touching_the_db(db_session):
    orphan_page = models.DocumentPage()
    orphan_page.title = "Orphan"
    db_session.add(orphan_page)
    db_session.flush()

    with pytest.raises(ValueError):
        make_quiz_set_id_factory(db_session, orphan_page)

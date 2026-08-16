"""Verifies the HTML -> ProseMirror conversion pipeline (app.tools.document_conversion)
against real DocumentPage exports in examples/. Pure/offline: no DB, no fixtures from
conftest.py -- just page.document HTML in, page.document_json + QuizPage rows out.

Requires `node` and tools/html_to_prosemirror's node_modules (npm install there once).
"""
from pathlib import Path

from app.tools.document_conversion import convert_document
from app.tools.quiz_extraction import FALSZ, PRAWDA, extract_quiz_blocks

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def load_example(name: str) -> str:
    return (EXAMPLES_DIR / name).read_text(encoding="utf-8")


def iter_nodes(node):
    """Recursively walks a ProseMirror JSON doc, yielding every node (including itself)."""
    yield node
    for child in node.get("content", []):
        yield from iter_nodes(child)


def node_types(doc: dict) -> list[str]:
    return [node["type"] for node in iter_nodes(doc)]


def marks(doc: dict) -> set[str]:
    result = set()
    for node in iter_nodes(doc):
        for mark in node.get("marks", []):
            result.add(mark["type"])
    return result


# -- plain documents: no quiz table, just prose/lists/images -----------------


def test_plain_document_preserves_marks_lists_and_images():
    result = convert_document(load_example("page_11.html"))

    assert result.document_json["type"] == "doc"
    assert not result.quiz_blocks
    assert "po-taxonomy" not in node_types(result.document_json)

    types = node_types(result.document_json)
    assert "heading" in types
    assert "bulletList" in types
    assert "listItem" in types
    assert "image" in types
    assert "bold" in marks(result.document_json)


def test_non_quiz_table_is_preserved_as_a_table_node():
    """page_21477 has a <table> used for plain layout (no SPRAWDZ SWOJA WIEDZE
    marker, no PRAWDA/FALSZ header) -- it must survive as an ordinary table,
    not get mistaken for a quiz block."""
    result = convert_document(load_example("page_21477.html"))

    assert not result.quiz_blocks
    types = node_types(result.document_json)
    assert "table" in types
    assert "po-taxonomy" not in types


# -- quiz-table documents -----------------------------------------------------


def test_quiz_table_extracted_with_comma_slash_answer_key():
    """page_25712: 'Poprawne odpowiedzi: 1/F, 2/F, 3/P, 4/P, 5/F, 6/P'."""
    result = convert_document(load_example("page_25712.html"))

    assert len(result.quiz_blocks) == 1
    block = result.quiz_blocks[0]
    assert [row.order_no for row in block.rows] == [1, 2, 3, 4, 5, 6]

    expected = {1: FALSZ, 2: FALSZ, 3: PRAWDA, 4: PRAWDA, 5: FALSZ, 6: PRAWDA}
    assert {row.order_no: row.correct_answer for row in block.rows} == expected

    types = node_types(result.document_json)
    assert types.count("po-taxonomy") == 1
    assert "table" not in types

    po_taxonomy = next(n for n in iter_nodes(result.document_json) if n["type"] == "po-taxonomy")
    assert po_taxonomy["attrs"]["taxonomy_id"] == block.placeholder_id


def test_quiz_table_extracted_across_blank_paragraph_before_answer_key():
    """page_15 has a stray '<p>&nbsp;</p>' between the table and the answer-key
    paragraph -- must still find and consume the answer key, and not leave a
    dangling table/paragraph behind."""
    result = convert_document(load_example("page_15.html"))

    assert len(result.quiz_blocks) == 1
    block = result.quiz_blocks[0]
    assert [row.order_no for row in block.rows] == [1, 2, 3, 4, 5, 6, 7]

    expected = {1: FALSZ, 2: PRAWDA, 3: PRAWDA, 4: FALSZ, 5: FALSZ, 6: FALSZ, 7: FALSZ}
    assert {row.order_no: row.correct_answer for row in block.rows} == expected

    types = node_types(result.document_json)
    assert types.count("po-taxonomy") == 1
    assert "table" not in types


def test_quiz_table_extracted_with_label_then_compact_answer_key():
    """page_13's answer key is split across two paragraphs: 'Odpowiedzi:' then
    '1F/2F/3P/4F/5F/6P/7P/8P/9F/10P' (no separating slash before the letter)."""
    result = convert_document(load_example("page_13.html"))

    assert len(result.quiz_blocks) == 1
    block = result.quiz_blocks[0]
    assert [row.order_no for row in block.rows] == list(range(1, 11))

    expected_letters = "F F P F F P P P F P".split()
    expected = {
        i + 1: (PRAWDA if letter == "P" else FALSZ) for i, letter in enumerate(expected_letters)
    }
    assert {row.order_no: row.correct_answer for row in block.rows} == expected

    types = node_types(result.document_json)
    assert types.count("po-taxonomy") == 1
    assert "table" not in types


def test_quiz_answer_row_produces_prawda_falsz_choice_pair():
    _, blocks = extract_quiz_blocks(load_example("page_25712.html"))
    row = blocks[0].rows[0]

    assert row.answers == [
        {"answer": PRAWDA, "is_correct": False},
        {"answer": FALSZ, "is_correct": True},
    ]


def _quiz_snippet(marker_text: str, statement: str, correct_letter: str) -> str:
    return f"""
    <p><strong>{marker_text}</strong></p>
    <table>
    <tr><td>L.P</td><td></td><td>PRAWDA</td><td>FALSZ</td></tr>
    <tr><td>1.</td><td>{statement}</td><td></td><td></td></tr>
    </table>
    <p>Poprawne odpowiedzi: 1/{correct_letter}</p>
    """


def test_placeholder_ids_are_distinct_across_multiple_quiz_blocks_in_one_document():
    html = _quiz_snippet("SPRAWDZ SWOJA WIEDZE:", "First statement", "P") + _quiz_snippet(
        "SPRAWDZ SWOJA WIEDZE:", "Second statement", "F"
    )

    _, blocks = extract_quiz_blocks(html)

    assert len(blocks) == 2
    assert blocks[0].placeholder_id != blocks[1].placeholder_id
    assert blocks[0].rows[0].correct_answer == PRAWDA
    assert blocks[1].rows[0].correct_answer == FALSZ


def test_placeholder_ids_are_deterministic_across_independent_calls():
    html = load_example("page_25712.html")
    _, first = extract_quiz_blocks(html)
    _, second = extract_quiz_blocks(html)
    assert first[0].placeholder_id == second[0].placeholder_id == "1"


def test_quiz_marker_without_answer_key_is_left_as_a_plain_table():
    """The corpus has real documents like this (e.g. page 8226: marker + PRAWDA/
    FALSZ header, 32 rows, no answer key found anywhere nearby) -- these must not
    blow up the whole document's conversion. The table is left untouched instead
    of being turned into a po-taxonomy block."""
    broken = """
    <p><strong>SPRAWDZ SWOJA WIEDZE:</strong></p>
    <table>
    <tr><td>L.P</td><td></td><td>PRAWDA</td><td>FALSZ</td></tr>
    <tr><td>1.</td><td>Some statement</td><td></td><td></td></tr>
    </table>
    <p>No answer key here.</p>
    """
    html, blocks = extract_quiz_blocks(broken)

    assert blocks == []
    assert "po-taxonomy" not in html
    assert "Some statement" in html


def test_quiz_row_missing_from_answer_key_is_left_as_a_plain_table():
    """Mirrors real documents like page 61: the answer key skips a row number
    (jumps 12 -> 14). Rather than guessing or importing an incomplete quiz, the
    whole table is left alone for manual review."""
    broken = """
    <p><strong>SPRAWDZ SWOJA WIEDZE:</strong></p>
    <table>
    <tr><td>L.P</td><td></td><td>PRAWDA</td><td>FALSZ</td></tr>
    <tr><td>1.</td><td>First statement</td><td></td><td></td></tr>
    <tr><td>2.</td><td>Second statement</td><td></td><td></td></tr>
    </table>
    <p>Poprawne odpowiedzi: 1/P</p>
    """
    html, blocks = extract_quiz_blocks(broken)

    assert blocks == []
    assert "po-taxonomy" not in html
    assert "Second statement" in html


def test_unresolvable_quiz_table_does_not_block_the_rest_of_the_document():
    """Answers the "does a broken quiz table sink the whole document?" question
    directly: a document with one good quiz table and one broken one still
    produces a document_json for everything else -- the good table becomes a
    po-taxonomy block, the broken one round-trips as an ordinary ProseMirror table."""
    good = """
    <p><strong>SPRAWDZ SWOJA WIEDZE:</strong></p>
    <table>
    <tr><td>L.P</td><td></td><td>PRAWDA</td><td>FALSZ</td></tr>
    <tr><td>1.</td><td>Good statement</td><td></td><td></td></tr>
    </table>
    <p>Poprawne odpowiedzi: 1/P</p>
    """
    broken = """
    <p><strong>SPRAWDZ SWOJA WIEDZE:</strong></p>
    <table>
    <tr><td>L.P</td><td></td><td>PRAWDA</td><td>FALSZ</td></tr>
    <tr><td>1.</td><td>Broken statement</td><td></td><td></td></tr>
    </table>
    <p>No answer key here.</p>
    """
    html = f"<h1>Lekcja</h1>{good}<p>Some unrelated prose in between.</p>{broken}<p>Trailing prose.</p>"

    result = convert_document(html)

    assert len(result.quiz_blocks) == 1
    assert result.quiz_blocks[0].rows[0].question == "Good statement"

    types = node_types(result.document_json)
    assert types.count("po-taxonomy") == 1
    assert "table" in types  # the broken one survived as a plain table
    assert "Some unrelated prose in between." in str(result.document_json)
    assert "Trailing prose." in str(result.document_json)

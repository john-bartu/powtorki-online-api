"""Extracts embedded "sprawdz swoja wiedze" true/false quiz tables out of legacy
DocumentPage HTML (see app.tools.importing.process_documents) so they can be
converted into standalone QuizPage rows, grouped under a SetTaxonomy the same
way app.tools.importing.process_quiz already groups spreadsheet-imported quizzes.

The matched <table> (plus its "SPRAWDZ SWOJA WIEDZE" marker paragraph and its
trailing answer-key paragraph(s)) is replaced in-place with a
`<div data-type="po-taxonomy" data-taxonomy-id="...">` marker, which
app.tools.prosemirror's TipTap schema round-trips into a
`{"type": "po-taxonomy", "attrs": {"taxonomy_id": ...}}` node. It's named after the
SetTaxonomy it points at, not a Page -- a quiz table becomes several individual
QuizPages, not one.
"""
import itertools
import logging
import re
from dataclasses import dataclass
from typing import Callable, Optional

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

QUIZ_MARKER_RE = re.compile(r"sprawd[zź]\s+swoj[ąa]\s+wiedz[eę]", re.IGNORECASE)
ANSWER_PAIR_RE = re.compile(r"(\d+)\s*/?\s*([PF])", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")

PRAWDA = "Prawda"
FALSZ = "Fałsz"

# How many siblings after the table we're willing to scan for the answer key
# before giving up (real examples need at most 2: an "Odpowiedzi:" label plus
# the key itself).
_MAX_TRAILING_SIBLINGS = 6


@dataclass
class QuizAnswerRow:
    order_no: int
    question: str
    correct_answer: str  # PRAWDA or FALSZ

    @property
    def answers(self) -> list[dict]:
        return [
            {"answer": PRAWDA, "is_correct": self.correct_answer == PRAWDA},
            {"answer": FALSZ, "is_correct": self.correct_answer == FALSZ},
        ]


@dataclass
class QuizBlock:
    placeholder_id: str
    rows: list[QuizAnswerRow]


def _default_id_factory() -> Callable[[list[QuizAnswerRow]], str]:
    counter = itertools.count(1)
    return lambda rows: str(next(counter))


def _normalize(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def _preceding_marker(table: Tag) -> Optional[Tag]:
    node = table.previous_sibling
    while node is not None:
        if isinstance(node, Tag):
            if QUIZ_MARKER_RE.search(node.get_text()):
                return node
            return None
        if str(node).strip():
            return None
        node = node.previous_sibling
    return None


def _is_quiz_header_row(row: Tag) -> bool:
    text = row.get_text(" ", strip=True).upper()
    return "PRAWDA" in text and ("FAŁSZ" in text or "FALSZ" in text)


def _parse_rows(table: Tag) -> list[tuple[int, str]]:
    trs = table.find_all("tr")
    if not trs or not _is_quiz_header_row(trs[0]):
        return []

    rows = []
    for tr in trs[1:]:
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        order_match = re.search(r"\d+", tds[0].get_text())
        if not order_match:
            continue
        question = _normalize(tds[1].get_text(" "))
        if not question:
            continue
        rows.append((int(order_match.group()), question))
    return rows


def _collect_answer_key(table: Tag) -> tuple[dict[int, str], list[Tag]]:
    trailing_tags: list[Tag] = []
    accumulated = ""
    node = table.next_sibling
    scanned = 0

    while node is not None and scanned < _MAX_TRAILING_SIBLINGS:
        if isinstance(node, Tag):
            trailing_tags.append(node)
            accumulated += " " + node.get_text(" ")
            scanned += 1
            pairs = ANSWER_PAIR_RE.findall(accumulated)
            if pairs:
                answer_map = {int(num): letter.upper() for num, letter in pairs}
                return answer_map, trailing_tags
        node = node.next_sibling

    return {}, []


def extract_quiz_blocks(
    html: str, id_factory: Optional[Callable[[list[QuizAnswerRow]], str]] = None
) -> tuple[str, list[QuizBlock]]:
    """Returns (html_with_po_taxonomy_placeholders, extracted_quiz_blocks).

    `id_factory` is called once per matched quiz block, with that block's
    parsed rows, and must return the taxonomy id embedded as `data-taxonomy-id`
    on the `po-taxonomy` marker. It defaults to a simple 1, 2, 3... sequence. Real
    imports pass app.tools.quiz_import.make_quiz_set_id_factory(...), which
    persists a SetTaxonomy + one QuizPage per row for the given rows and hands
    back that SetTaxonomy's real id -- the rows are only known once parsing
    reaches this point, hence the callback rather than a plain id generator.
    """
    id_factory = id_factory or _default_id_factory()
    soup = BeautifulSoup(html, "html.parser")
    quiz_blocks: list[QuizBlock] = []

    for table in list(soup.find_all("table")):
        marker = _preceding_marker(table)
        if marker is None:
            continue

        parsed_rows = _parse_rows(table)
        if not parsed_rows:
            continue

        answer_map, trailing_tags = _collect_answer_key(table)
        if not answer_map:
            logger.warning(
                "Quiz table matched marker %r but no answer key (e.g. 'Poprawne "
                "odpowiedzi: 1/F, 2/P') was found within %d elements after the "
                "table -- leaving it as a plain <table>, not converting it.",
                marker.get_text(strip=True), _MAX_TRAILING_SIBLINGS,
            )
            continue

        missing = [order_no for order_no, _ in parsed_rows if order_no not in answer_map]
        if missing:
            logger.warning(
                "Quiz table matched marker %r but rows %r have no matching entry "
                "in the parsed answer key %r -- leaving it as a plain <table>, "
                "not converting it.",
                marker.get_text(strip=True), missing, answer_map,
            )
            continue

        rows = [
            QuizAnswerRow(
                order_no=order_no,
                question=question,
                correct_answer=PRAWDA if answer_map[order_no] == "P" else FALSZ,
            )
            for order_no, question in parsed_rows
        ]

        placeholder_id = id_factory(rows)
        placeholder = soup.new_tag(
            "div", attrs={"data-type": "po-taxonomy", "data-taxonomy-id": placeholder_id}
        )
        marker.insert_before(placeholder)

        marker.decompose()
        table.decompose()
        for tag in trailing_tags:
            tag.decompose()

        quiz_blocks.append(QuizBlock(placeholder_id=placeholder_id, rows=rows))

    return str(soup), quiz_blocks

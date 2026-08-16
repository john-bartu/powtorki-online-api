"""Persists the QuizAnswerRow groups extracted by app.tools.quiz_extraction as
real QuizPage rows (one per statement) grouped under a SetTaxonomy, mirroring
how app.tools.importing.process_quiz groups a spreadsheet-imported quiz.

Meant to be plugged in as extract_quiz_blocks's/convert_document's id_factory:
each call gets that block's parsed rows and must hand back the taxonomy_id
embedded on the `po-taxonomy` node, which here is the real, flushed SetTaxonomy id.
"""
from typing import Callable

from sqlalchemy.orm import Session

from app.constants import PageSubTypes
from app.database import models
from app.tools.quiz_extraction import QuizAnswerRow


def make_quiz_set_id_factory(
    db: Session, document_page: models.DocumentPage
) -> Callable[[list[QuizAnswerRow]], str]:
    """Builds an id_factory bound to `document_page`. The SetTaxonomy created
    for the first quiz block in the document is named after the document
    itself and parented under the document's own first taxonomy; a document
    with more than one quiz block gets " (2)", " (3)", ... appended so names
    stay unique.
    """
    parent_taxonomy = _first_taxonomy(document_page)
    block_index = 0

    def factory(rows: list[QuizAnswerRow]) -> str:
        nonlocal block_index
        block_index += 1
        name = document_page.title if block_index == 1 else f"{document_page.title} ({block_index})"

        quiz_taxonomy = models.SetTaxonomy(id_parent=parent_taxonomy.id, name=name)
        db.add(quiz_taxonomy)
        db.flush()  # need quiz_taxonomy.id now, to both link rows and return it

        for row in rows:
            quiz_page = models.QuizPage()
            quiz_page.id_sub_type = PageSubTypes.Quiz
            quiz_page.title = row.question

            for choice in row.answers:
                answer = models.Answer(answer=choice["answer"])
                map_answer = models.MapPageAnswer(answer=answer, is_correct=choice["is_correct"])
                quiz_page.map_answers.append(map_answer)
                db.add(answer)
                db.add(map_answer)

            map_page_tax = models.MapPageTaxonomy(order_no=row.order_no)
            map_page_tax.taxonomy = quiz_taxonomy
            quiz_page.taxonomies.append(map_page_tax)

            db.add(quiz_page)
            db.add(map_page_tax)

        return str(quiz_taxonomy.id)

    return factory


def _first_taxonomy(document_page: models.DocumentPage) -> models.Taxonomy:
    ordered = sorted(
        document_page.taxonomies,
        key=lambda mapping: (mapping.order_no is None, mapping.order_no),
    )
    if not ordered:
        raise ValueError(
            f"DocumentPage {document_page.id!r} ({document_page.title!r}) has no "
            "taxonomy to parent the quiz SetTaxonomy under."
        )
    return ordered[0].taxonomy

"""Glues quiz extraction and ProseMirror conversion into the single operation
needed to migrate a DocumentPage: page.document (HTML) -> page.document_json
(ProseMirror JSON, with embedded quiz tables lifted out as `po-taxonomy` blocks)
plus the QuizPage rows those blocks should be backed by.

No `document_json` column exists yet -- this is the verification step for
that migration, exercised directly against app_tests/../examples/*.html.
"""
from dataclasses import dataclass
from typing import Callable, Optional

from app.tools.prosemirror import html_to_prosemirror
from app.tools.quiz_extraction import QuizAnswerRow, QuizBlock, extract_quiz_blocks


@dataclass
class DocumentConversionResult:
    document_json: dict
    quiz_blocks: list[QuizBlock]


def convert_document(
    html: str, id_factory: Optional[Callable[[list[QuizAnswerRow]], str]] = None
) -> DocumentConversionResult:
    prepared_html, quiz_blocks = extract_quiz_blocks(html, id_factory=id_factory)
    document_json = html_to_prosemirror(prepared_html)
    return DocumentConversionResult(document_json=document_json, quiz_blocks=quiz_blocks)

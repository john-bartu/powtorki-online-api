"""Real, DB-writing pass that populates pages.document_json for every DocumentPage.

For each DocumentPage with document set and document_json still null (so this is
safely resumable/idempotent -- re-running only picks up rows that failed or were
added since the last run), this:
  1. runs app.tools.document_conversion.convert_document on page.document, with
     an id_factory backed by app.tools.quiz_import.make_quiz_set_id_factory --
     which persists one QuizPage per extracted row plus a SetTaxonomy grouping
     them, named after the document and parented under its own first taxonomy;
  2. stores the resulting ProseMirror JSON on page.document_json;
  3. commits per page, so one page's failure doesn't roll back everything before it.

app.tools.document_scan already covers the read-only, nothing-persisted survey of
the corpus (table-classification and HTML-tag-coverage counts) -- this script is
the write pass that actually acts on it, run once real content is what's wanted.

Run as: python -m app.tools.import_documents
"""
import logging

from app.constants import PageTypes
from app.database import models
from app.database.database import SessionLocal
from app.tools.document_conversion import convert_document
from app.tools.quiz_import import make_quiz_set_id_factory

logger = logging.getLogger(__name__)


def main() -> None:
    db = SessionLocal()
    try:
        pages = (
            db.query(models.Page)
            .filter(
                models.Page.id_type == PageTypes.DocumentPage,
                models.Page.document.isnot(None),
                models.Page.document_json.is_(None),
            )
            .all()
        )

        print(f"Found {len(pages)} DocumentPage rows to convert.")

        converted = 0
        failures: list[tuple[int, str, str]] = []

        for page in pages:
            try:
                id_factory = make_quiz_set_id_factory(db, page)
                result = convert_document(page.document, id_factory=id_factory)
                page.document_json = result.document_json
                db.commit()
                converted += 1
            except Exception as exc:
                db.rollback()
                logger.exception("Failed to convert page %s (%r)", page.id, page.title)
                failures.append((page.id, page.title, repr(exc)))

            if (converted + len(failures)) % 100 == 0:
                print(f"...{converted + len(failures)}/{len(pages)}")

        print(f"\nConverted {converted}/{len(pages)} documents.")
        print(f"Failures: {len(failures)}")
        for page_id, title, error in failures:
            print(f"  page {page_id} ({title!r}): {error}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

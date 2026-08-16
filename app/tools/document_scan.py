"""Read-only, dry-run scan across every DocumentPage.document row in the DB
(id_type=2). Never calls db.add/db.flush/db.commit -- SELECT + in-process HTML
analysis only, nothing is persisted. Meant to run ahead of the real "convert
every document" pass, to surface two kinds of gaps:

1. <table>s that smell like an embedded "sprawdz swoja wiedze" quiz but that
   app.tools.quiz_extraction.extract_quiz_blocks either can't fully parse or
   never attempts to match at all (different marker wording, missing/garbled
   answer key, or a differently-shaped table under the same marker).
2. HTML tags used somewhere in the corpus that have no node/mark registered
   in tools/html_to_prosemirror/convert.mjs. TipTap's HTML parser silently
   unwraps unmatched elements -- their text survives, the tag's own
   semantics/attributes don't -- so this is a visibility list, not
   automatically a list of bugs; <a> bookmarks with no text are harmless,
   a real <a href> with link text is not.

Run as: python -m app.tools.document_scan
"""
import re
from collections import Counter
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, NavigableString, Tag

from app.constants import PageTypes
from app.database import models
from app.database.database import SessionLocal
from app.tools.quiz_extraction import (
    _collect_answer_key,
    _is_quiz_header_row,
    _parse_rows,
    _preceding_marker,
)

# Tags with a direct TipTap node/mark registered in convert.mjs (see
# tools/html_to_prosemirror/convert.mjs's `extensions` list).
SUPPORTED_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "b", "em", "i", "u",
    "ul", "ol", "li",
    "img", "table", "tr", "td", "th",
    "br", "a", "sup", "sub",
}
# Not schema nodes, but ProseMirror's HTML parser walks through them
# transparently (their children still get matched normally) -- not content loss.
TRANSPARENT_TAGS = {"tbody", "thead", "tfoot", "html", "body", "head"}

MARKER_HINT_RE = re.compile(r"sprawd|quiz|test\s+wiedz|pytania\s+kontroln", re.IGNORECASE)
TRUE_FALSE_HINT_RE = re.compile(r"prawda|fa[lł]sz", re.IGNORECASE)


@dataclass
class TableFinding:
    page_id: int
    title: str
    classification: str
    detail: str


@dataclass
class TagUsage:
    count_pages: int = 0
    count_occurrences: int = 0
    sample_page_ids: list = field(default_factory=list)


def _preceding_text(table: Tag) -> str:
    node = table.previous_sibling
    while isinstance(node, NavigableString) and not str(node).strip():
        node = node.previous_sibling
    return node.get_text(" ", strip=True) if isinstance(node, Tag) else ""


def classify_tables(page_id: int, title: str, html: str) -> list[TableFinding]:
    soup = BeautifulSoup(html, "html.parser")
    findings = []

    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        header_ok = bool(trs) and _is_quiz_header_row(trs[0])
        marker = _preceding_marker(table)
        header_text = trs[0].get_text(" ", strip=True)[:100] if trs else ""
        preceding_text = _preceding_text(table)

        if marker and header_ok:
            parsed_rows = _parse_rows(table)
            answer_map, _ = _collect_answer_key(table)
            missing = [n for n, _ in parsed_rows if n not in answer_map]
            if not parsed_rows:
                cls, detail = "MARKER_AND_HEADER_BUT_NO_ROWS", f"header={header_text!r}"
            elif not answer_map:
                cls, detail = (
                    "MARKER_AND_HEADER_BUT_NO_ANSWER_KEY",
                    f"rows={len(parsed_rows)} header={header_text!r}",
                )
            elif missing:
                cls, detail = (
                    "ANSWER_KEY_ROW_MISMATCH",
                    f"missing_rows={missing} answer_map={answer_map} header={header_text!r}",
                )
            else:
                cls, detail = "MATCHED", f"rows={len(parsed_rows)}"
        elif header_ok and not marker:
            cls, detail = "PF_TABLE_WITHOUT_MARKER", f"preceding={preceding_text!r} header={header_text!r}"
        elif marker and not header_ok:
            cls, detail = "MARKER_WITHOUT_PF_HEADER", f"marker={preceding_text!r} header={header_text!r}"
        elif TRUE_FALSE_HINT_RE.search(table.get_text(" ")) or MARKER_HINT_RE.search(preceding_text):
            cls, detail = "LOOSE_CANDIDATE", f"preceding={preceding_text!r} header={header_text!r}"
        else:
            cls, detail = "IGNORED", ""

        findings.append(TableFinding(page_id, title, cls, detail))

    return findings


def scan_tags(page_id: int, html: str, usage: dict[str, TagUsage]) -> None:
    soup = BeautifulSoup(html, "html.parser")
    seen_in_page = set()
    for tag in soup.find_all(True):
        name = tag.name.lower()
        if name in SUPPORTED_TAGS or name in TRANSPARENT_TAGS:
            continue
        entry = usage.setdefault(name, TagUsage())
        entry.count_occurrences += 1
        if name not in seen_in_page:
            entry.count_pages += 1
            if len(entry.sample_page_ids) < 5:
                entry.sample_page_ids.append(page_id)
        seen_in_page.add(name)


def scan_real_links(page_id: int, title: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    findings = []
    for a in soup.find_all("a"):
        href = (a.get("href") or "").strip()
        text = a.get_text(strip=True)
        if href and text:
            findings.append(f"page {page_id} ({title!r}): <a href={href!r}>{text[:60]!r}</a>")
    return findings


def main() -> None:
    db = SessionLocal()
    try:
        pages = (
            db.query(models.Page)
            .filter(models.Page.id_type == PageTypes.DocumentPage, models.Page.document.isnot(None))
            .all()
        )

        all_findings: list[TableFinding] = []
        tag_usage: dict[str, TagUsage] = {}
        link_findings: list[str] = []

        for page in pages:
            html = page.document
            all_findings.extend(classify_tables(page.id, page.title, html))
            scan_tags(page.id, html, tag_usage)
            link_findings.extend(scan_real_links(page.id, page.title, html))

        print(f"Scanned {len(pages)} DocumentPage rows (id_type=2), read-only -- nothing persisted.\n")

        by_class = Counter(f.classification for f in all_findings)
        print("=== <table> classification across the corpus ===")
        for cls in ["MATCHED", "MARKER_AND_HEADER_BUT_NO_ROWS", "MARKER_AND_HEADER_BUT_NO_ANSWER_KEY",
                    "ANSWER_KEY_ROW_MISMATCH", "PF_TABLE_WITHOUT_MARKER", "MARKER_WITHOUT_PF_HEADER",
                    "LOOSE_CANDIDATE", "IGNORED"]:
            if by_class.get(cls):
                print(f"  {cls}: {by_class[cls]}")

        gaps = [f for f in all_findings if f.classification not in ("MATCHED", "IGNORED")]
        print(f"\n=== Quiz-table gaps needing review ({len(gaps)}) ===")
        if not gaps:
            print("None -- every <table> that looks like a quiz matches the current parser cleanly.")
        else:
            for g in gaps:
                print(f"  [{g.classification}] page {g.page_id} ({g.title!r}): {g.detail}")

        print("\n=== HTML tags with no registered TipTap node/mark ===")
        if not tag_usage:
            print("None -- every tag used across the corpus is covered by a registered extension.")
        else:
            for name, usage in sorted(tag_usage.items(), key=lambda kv: -kv[1].count_pages):
                print(
                    f"  <{name}>: {usage.count_pages} pages, {usage.count_occurrences} occurrences, "
                    f"e.g. page ids {usage.sample_page_ids}"
                )

        print("\n=== Real <a href> links (lose href/link semantics on conversion) ===")
        if not link_findings:
            print("None -- every <a> found across the corpus is an empty anchor/bookmark, safe to drop.")
        else:
            for line in link_findings[:50]:
                print(f"  {line}")
            if len(link_findings) > 50:
                print(f"  ... and {len(link_findings) - 50} more")
    finally:
        db.close()


if __name__ == "__main__":
    main()

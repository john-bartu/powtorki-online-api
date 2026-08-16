"""Converts HTML (as stored in page.document) to ProseMirror JSON, using the
same TipTap schema the po-admin editor will render, via the Node CLI in
tools/html_to_prosemirror. Kept as a subprocess boundary rather than embedding
a JS engine, since TipTap/ProseMirror have no maintained Python port.
"""
import json
import subprocess
from pathlib import Path

_CONVERTER_DIR = Path(__file__).resolve().parents[2] / "tools" / "html_to_prosemirror"
_CONVERTER_SCRIPT = _CONVERTER_DIR / "convert.mjs"


class ProseMirrorConversionError(RuntimeError):
    pass


def html_to_prosemirror(html: str) -> dict:
    try:
        result = subprocess.run(
            ["node", str(_CONVERTER_SCRIPT)],
            input=html,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=_CONVERTER_DIR,
        )
    except FileNotFoundError as exc:
        raise ProseMirrorConversionError(
            "node executable not found -- required to run the TipTap HTML->JSON converter"
        ) from exc

    if result.returncode != 0:
        raise ProseMirrorConversionError(result.stderr.strip() or "node conversion failed")

    return json.loads(result.stdout)

"""Re-copy the parking and TOD master sections into docs/MODEL_AND_ASSUMPTIONS.md.

Parts B (parking) and C (TOD) of the shared Model & Assumptions Overview are
word-for-word copies of each session's master file. This script replaces each
part's body with the current master, demotes headings by two levels and
rewrites relative links so they resolve from docs/. Part A, the introduction
and each part's "Maintained by" note are left untouched.

Run: uv run python scripts/sync_model_doc.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "MODEL_AND_ASSUMPTIONS.md"
PARTS = [
    ("## Part B. Parking requirement reduction", ROOT / "docs" / "parking" / "MODEL_AND_ASSUMPTIONS_PARKING.md", "parking"),
    ("## Part C. Transit-oriented density (TOD)", ROOT / "docs" / "tod" / "MODEL_AND_ASSUMPTIONS_TOD.md", "tod"),
]
LINK = re.compile(r"\]\((?!https?://|#|mailto:)([^)]+)\)")


def relink(text: str, subdir: str) -> str:
    """Rewrite links relative to docs/<subdir>/ so they resolve from docs/."""
    def fix(m: re.Match) -> str:
        target = m.group(1)
        path, _, frag = target.partition("#")
        resolved = (ROOT / "docs" / subdir / path).resolve()
        new = Path(*Path(resolved).relative_to((ROOT / "docs").resolve()).parts) if resolved.is_relative_to((ROOT / "docs").resolve()) else None
        if new is None:
            new = Path("..") / resolved.relative_to(ROOT.resolve())
        return f"]({new.as_posix()}{'#' + frag if frag else ''})"
    return LINK.sub(fix, text)


def demote(text: str) -> str:
    return re.sub(r"^(#+) ", lambda m: "#" * (len(m.group(1)) + 2) + " ", text, flags=re.M)


def main() -> None:
    doc = DOC.read_text()
    for i, (heading, master, subdir) in enumerate(PARTS):
        start = doc.index(heading)
        note_end = doc.index("\n\n", doc.index("> **Maintained by", start)) + 2
        nxt = doc.find("\n## Part ", note_end)
        end = nxt + 1 if nxt != -1 else len(doc)
        body = relink(demote(master.read_text().strip()), subdir)
        doc = doc[:note_end] + body + "\n\n" + doc[end:].lstrip("\n") if nxt != -1 else doc[:note_end] + body + "\n"
    doc = doc.replace("Its relative links point from `docs/parking/`; follow the master copy for working links.", "Its links are rewritten to resolve from `docs/` by `scripts/sync_model_doc.py`.")
    doc = doc.replace("Its relative links point from `docs/tod/`; follow the master copy for working links.", "Its links are rewritten to resolve from `docs/` by `scripts/sync_model_doc.py`.")
    DOC.write_text(doc)
    print(f"synced {DOC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

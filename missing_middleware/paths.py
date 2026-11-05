"""Standard locations. Raw and processed data stay out of git (see .gitignore)."""
import os as _os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"            # downloaded source files, one folder per source_id
PROCESSED = ROOT / "data" / "processed"  # contract tables, one folder per run or build
REFERENCE = ROOT / "reference"          # small hand-coded, committed tables (e.g. local ADU rules)
if _os.environ.get("MM_REFERENCE_DIR"):  # batch reruns read and write a working copy (e.g. parking batch 2026-11-05)
    REFERENCE = Path(_os.environ["MM_REFERENCE_DIR"])


def raw_dir(source_id: str) -> Path:
    path = RAW / source_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed_dir(name: str = "current") -> Path:
    path = PROCESSED / name
    path.mkdir(parents=True, exist_ok=True)
    return path

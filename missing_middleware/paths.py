"""Standard locations. Raw and processed data stay out of git (see .gitignore)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"            # downloaded source files, one folder per source_id
PROCESSED = ROOT / "data" / "processed"  # contract tables, one folder per run or build
REFERENCE = ROOT / "reference"          # small hand-coded, committed tables (e.g. local ADU rules)


def raw_dir(source_id: str) -> Path:
    path = RAW / source_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed_dir(name: str = "current") -> Path:
    path = PROCESSED / name
    path.mkdir(parents=True, exist_ok=True)
    return path

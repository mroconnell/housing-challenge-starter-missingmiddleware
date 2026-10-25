"""Single source for engine parameters that several scripts share (reference/adu_model_params.json).

The Madison floor (AQ-024) is stored once, under `madison_floor`, with named variants and an
`in_use` selector. Every path in the engine scenario, the pooled and California regressions'
engine checks, and the engine's rural sensitivity read it from here.
Units: second-home permits on single-family lots per 1,000 one-unit detached homes per year.
"""
from __future__ import annotations

import json
from pathlib import Path

from missing_middleware.paths import REFERENCE

PARAMS = REFERENCE / "adu_model_params.json"


def madison_floor(variant: str | None = None, path: Path = PARAMS) -> float:
    """Madison floor rate. variant=None returns the variant named by `in_use`."""
    spec = json.loads(Path(path).read_text())["madison_floor"]
    return float(spec["variants"][variant or spec["in_use"]]["rate"])


def madison_floor_variants(path: Path = PARAMS) -> dict[str, float]:
    spec = json.loads(Path(path).read_text())["madison_floor"]
    return {k: float(v["rate"]) for k, v in spec["variants"].items()}

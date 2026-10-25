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


def area_paths(path: Path = PARAMS) -> "pd.DataFrame":
    """Explicit per-area with-law paths (AQ-042) as a long table area_id, year, rate, override.

    Read from `area_paths` in the params file. Each entry lists area_ids, one rate per forecast
    year 1..5 (already ramped: the engine applies no ramp on top), and the source. Every entry
    applies to all scenario paths (lower, central, upper). Empty if there are none.
    """
    import pandas as pd

    spec = json.loads(Path(path).read_text()).get("area_paths", {})
    rows = []
    for name, ov in spec.items():
        rates = ov["rates"]
        if len(rates) != 5:
            raise ValueError(f"area path {name} needs 5 yearly rates")
        for a in ov["area_ids"]:
            for t, r in enumerate(rates, start=1):
                rows.append({"override": name, "area_id": a, "year": t, "rate": float(r)})
    return pd.DataFrame(rows, columns=["override", "area_id", "year", "rate"])


def area_levels_spec(path: Path = PARAMS) -> dict:
    """Which per-area level file (and option x configuration) the engine uses."""
    return json.loads(Path(path).read_text())["area_levels"]

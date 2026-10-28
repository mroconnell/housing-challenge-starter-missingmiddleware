"""Light sanity checks for parking model runs. They flag problems and never stop a run (owner, 2026-10-28).

Use:
    flags = checks.trait_range(df, group="city", cols=UNITS)        # cities far outside the others' range
    flags += checks.unit_ranges(df, UNITS)                          # values that don't fit the column's unit
    flags += checks.definition(df, rule_name, mask_violating)       # rows breaking the policy's own definition
    checks.report(flags, path)                                      # print at the top of results and save
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# column -> (unit, plausible minimum, plausible maximum)
UNITS = {
    "acres": ("acres", 0.0, 50.0),
    "width_m": ("metres", 0.5, 500.0),
    "dist_station_m": ("metres", 0.0, 100_000.0),
    "before_py": ("net homes permitted per lot per year", -50.0, 500.0),
    "after_py": ("net homes permitted per lot per year", -50.0, 500.0),
    "near_before": ("net homes permitted within 250 m per year", -500.0, 5_000.0),
    "pinched": ("0 or 1", 0.0, 1.0),
}


def trait_range(df: pd.DataFrame, group: str, cols, far: float = 3.0) -> list[dict]:
    """Flag a group whose median is outside the other groups' 5th-95th percentile range widened by `far` x its width."""
    out = []
    for c in cols:
        if c not in df:
            continue
        for g, sub in df.groupby(group):
            rest = df.loc[df[group] != g, c].dropna()
            if rest.empty or sub[c].dropna().empty:
                continue
            lo, hi = np.nanpercentile(rest, [5, 95])
            w = max(hi - lo, 1e-9)
            m = float(sub[c].median())
            if m < lo - far * w or m > hi + far * w:
                out.append(dict(check="trait outside others' range", where=str(g), column=c, value=m,
                                note=f"others' 5th-95th: {lo:.3g} to {hi:.3g}"))
    return out


def unit_ranges(df: pd.DataFrame, units: dict = UNITS) -> list[dict]:
    out = []
    for c, (unit, lo, hi) in units.items():
        if c not in df:
            continue
        v = pd.to_numeric(df[c], errors="coerce")
        bad = ((v < lo) | (v > hi)).sum()
        if bad:
            out.append(dict(check="value outside unit range", where="all rows", column=c, value=int(bad),
                            note=f"{unit}: expected {lo} to {hi}; {bad} of {v.notna().sum()} rows outside"))
    return out


def definition(df: pd.DataFrame, rule: str, violating: pd.Series) -> list[dict]:
    n = int(violating.sum())
    return [dict(check="breaks policy definition", where=rule, column="", value=n, note=f"{n} rows")] if n else []


def worst_miss(pred: pd.DataFrame, key: str, actual: str, model: str, traits: pd.DataFrame | None = None) -> list[dict]:
    """Name the worst-missed held-out unit, for tracing after each run."""
    if pred.empty:
        return []
    p = pred.assign(miss=(pred[model] - pred[actual]).abs()).sort_values("miss", ascending=False).iloc[0]
    return [dict(check="worst miss (trace it)", where=str(p[key]), column=model, value=float(p["miss"]),
                 note=f"actual {p[actual]:.3g}, predicted {p[model]:.3g}")]


def report(flags: list[dict], path: Path | None = None) -> pd.DataFrame:
    f = pd.DataFrame(flags, columns=["check", "where", "column", "value", "note"])
    print("=== CHECKS (flags only; the run continues) ===")
    print(f.to_string(index=False) if len(f) else "no flags")
    print("=== END CHECKS ===")
    if path is not None:
        f.to_csv(path, index=False)
    return f

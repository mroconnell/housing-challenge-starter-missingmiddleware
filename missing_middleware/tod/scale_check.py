"""TOD scale check (docs/tod/GATE3_MODEL_SPEC.md section 9; docs/tod/MODEL.md section 10).

Pure functions only (no file or network access): the per-1,000-homes rate, the benchmark
statistics over a metro-year panel, and the conversion of a scenario's yearly addition into
extra 5+ unit permits per 1,000 existing homes, with flags against the benchmarks.

It is a check shown to the owner, not a cap: nothing here changes a model number.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def per_1000(units: float, housing_units: float) -> float:
    """Units per 1,000 existing housing units (a yearly rate when `units` is one year's permits)."""
    if housing_units is None or not housing_units > 0:
        raise ValueError("housing_units must be positive")
    return 1000.0 * float(units) / float(housing_units)


@dataclass(frozen=True)
class Benchmarks:
    """Peer-metro benchmarks of 5+ unit permits per 1,000 existing homes per year."""
    observed_max: float
    observed_max_metro: str
    observed_max_year: int
    p95: float
    n_metro_years: int
    n_metros: int


def benchmarks(panel: pd.DataFrame, q: float = 0.95) -> Benchmarks:
    """Highest metro-year and the q-th percentile (linear interpolation) of `rate_5plus_per_1000`.

    `panel` has one row per metro-year with columns cbsa_name, year, rate_5plus_per_1000."""
    p = panel.dropna(subset=["rate_5plus_per_1000"])
    top = p.loc[p["rate_5plus_per_1000"].idxmax()]
    return Benchmarks(
        observed_max=float(top["rate_5plus_per_1000"]),
        observed_max_metro=str(top["cbsa_name"]),
        observed_max_year=int(top["year"]),
        p95=float(np.percentile(p["rate_5plus_per_1000"], 100 * q)),
        n_metro_years=int(len(p)),
        n_metros=int(p["cbsa_name"].nunique()),
    )


def own_history(series: pd.DataFrame, recent_years: tuple[int, ...]) -> dict:
    """A metro's own maximum yearly rate (and year) and its mean yearly rate over `recent_years`.

    The recent average is the mean of the yearly rates (each year weighted equally)."""
    s = series.dropna(subset=["rate_5plus_per_1000"])
    top = s.loc[s["rate_5plus_per_1000"].idxmax()]
    recent = s[s["year"].isin(recent_years)]
    if len(recent) != len(recent_years):
        raise ValueError(f"missing recent years: have {sorted(recent['year'])}, need {list(recent_years)}")
    return {
        "own_max": float(top["rate_5plus_per_1000"]),
        "own_max_year": int(top["year"]),
        "recent_mean": float(recent["rate_5plus_per_1000"].mean()),
    }


def scenario_check(addition: float, housing_units: float, baseline_per_1000: float,
                   observed_max: float, p95: float, own_max: float) -> dict:
    """Convert one year's statewide-model addition in a metro (homes, treated as 5+ unit
    apartment permits) into extra permits per 1,000 existing homes, add it to the metro's
    baseline rate and flag the total against the benchmarks."""
    if addition < 0:
        raise ValueError("addition must not be negative")
    extra = per_1000(addition, housing_units)
    total = baseline_per_1000 + extra
    return {
        "extra_per_1000": extra,
        "baseline_per_1000": baseline_per_1000,
        "total_per_1000": total,
        "exceeds_observed_max": bool(total > observed_max),
        "exceeds_p95": bool(total > p95),
        "exceeds_own_max": bool(total > own_max),
    }

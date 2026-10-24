"""ADU scenario engine (Gate 3).

Implements the outcome model from docs/gate1/SCOPE_AND_MODEL.md (revision 3):

    baseline   B[a,t]   = H[a] * x[a] * g[a,t] / 1000
    additional A[a,t,p] = H[a] * max(y[a,p] - x[a] * g[a,t], 0) * ramp[p][t] / 1000

g[a,t] is 1 except in places still ramping after a recent local reform (for
example Milwaukee after August 2025), where the current-law rate is still
rising; the law's addition is measured against that year's current-law rate.

where H is one-unit detached homes (ACS), x the current-law rate of second homes
on single-family lots per 1,000 homes per year (observed or estimated), y the
rate with the statewide law for path p, and ramp the share of the plateau reached
in forecast year t (1..5). Rates are per 1,000 homes per year.

y for each area and path:
    y = max(floor_rate[p], x * (1 + spillover[p]))   if the area is at benchmark
    y = max(floor_rate[p], level[p])                  otherwise
so the Madison floor applies everywhere (AQ-024), benchmark places rise by the
statewide spillover (AQ-027), and no area is forecast below its current rate.

Parameters are supplied by the caller (from the California study and the
Wisconsin baseline); nothing here is calibrated. All paths share the same H and x,
so the baseline is identical across paths and only y and the ramp differ.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

YEARS = (1, 2, 3, 4, 5)
PATHS = ("lower", "central", "upper")


@dataclass(frozen=True)
class PathParams:
    level: float          # with-law rate for places not at benchmark (per 1,000 homes/yr)
    floor_rate: float     # Madison floor: observed 2022-2025 rate / 0.8
    spillover: float      # proportional rise for places already at benchmark
    ramp: tuple[float, ...]  # share of plateau reached in forecast years 1..5

    def __post_init__(self):
        if len(self.ramp) != len(YEARS):
            raise ValueError("ramp needs one value per forecast year")
        if any(r < 0 or r > 1 for r in self.ramp) or list(self.ramp) != sorted(self.ramp):
            raise ValueError("ramp must be non-decreasing shares between 0 and 1")
        if min(self.level, self.floor_rate, self.spillover) < 0:
            raise ValueError("rates and spillover must be non-negative")


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    paths: dict[str, PathParams]
    labels: dict[str, str] = field(default_factory=dict)  # y_basis per path, for display


def y_rate(x: float, at_benchmark: bool, p: PathParams) -> float:
    target = x * (1 + p.spillover) if at_benchmark else p.level
    return max(p.floor_rate, target, x)


def run(areas: pd.DataFrame, scenario: Scenario, baseline_growth: pd.DataFrame | None = None) -> pd.DataFrame:
    """Compute baseline and additional units by area, forecast year, and path.

    areas needs columns: area_id, homes (H), x_rate, at_benchmark (bool),
    x_basis, rights_basis. baseline_growth (optional) has area_id, year, g
    for places still ramping after a recent local reform; g defaults to 1.
    """
    need = {"area_id", "homes", "x_rate", "at_benchmark"}
    missing = need - set(areas.columns)
    if missing:
        raise ValueError(f"areas missing columns {sorted(missing)}")
    g = {}
    if baseline_growth is not None:
        g = {(r.area_id, int(r.year)): float(r.g) for r in baseline_growth.itertuples()}
    rows = []
    for a in areas.itertuples(index=False):
        for path, p in scenario.paths.items():
            y = y_rate(a.x_rate, bool(a.at_benchmark), p)
            for i, t in enumerate(YEARS):
                gt = g.get((a.area_id, t), 1.0)
                x_t = a.x_rate * gt
                base = a.homes * x_t / 1000
                add = a.homes * max(y - x_t, 0.0) * p.ramp[i] / 1000
                rows.append({
                    "scenario_id": scenario.scenario_id, "area_id": a.area_id, "path": path,
                    "year": t, "homes": a.homes, "x_rate": a.x_rate, "y_rate": y,
                    "baseline_units": base, "additional_units": add,
                    "y_basis": scenario.labels.get(path, ""),
                    "x_basis": getattr(a, "x_basis", ""), "rights_basis": getattr(a, "rights_basis", ""),
                })
    return pd.DataFrame(rows)


def check_invariants(out: pd.DataFrame) -> list[str]:
    """Analytical checks the owner can rely on; returns problems, empty if none."""
    problems = []
    if (out.additional_units < -1e-9).any():
        problems.append("negative additional units")
    piv = out.pivot_table(index=["area_id", "year"], columns="path", values="additional_units", aggfunc="sum")
    if {"lower", "central", "upper"} <= set(piv.columns):
        if ((piv["lower"] > piv["central"] + 1e-9) | (piv["central"] > piv["upper"] + 1e-9)).any():
            problems.append("paths out of order (lower <= central <= upper violated)")
    base = out.groupby(["area_id", "year"]).baseline_units.nunique()
    if (base > 1).any():
        problems.append("baseline differs across paths")
    cum = out.sort_values("year").groupby(["area_id", "path"]).additional_units.cumsum()
    if (cum.groupby([out.area_id, out.path]).diff().dropna() < -1e-9).any():
        problems.append("cumulative additional units decrease")
    return problems


def five_year_totals(out: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    keys = (by or []) + ["path"]
    return out.groupby(keys)[["baseline_units", "additional_units"]].sum().reset_index()

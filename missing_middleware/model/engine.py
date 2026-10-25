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
    y = max(floor_rate[p], level[p], x * (1 + spillover[p]))   if the area is at benchmark
    y = max(floor_rate[p], level[p], x)                         otherwise
so the Madison floor and the statewide level apply everywhere (AQ-024), places
already at benchmark also get the statewide spillover on their own rate if that is
higher (AQ-027), and no area is forecast below its current rate.

Explicit per-area paths (AQ-042). An area may instead be given an observed year-by-year
with-law path r[a,t] (for example Madison on the median path of Madison-like cities under
statewide laws, docs/gate3/MADISON_LIKE_CITIES.md). Such a path already contains its own
ramp-up, so the path's ramp is not applied:
    y[a,t]     = max(floor_rate[p], r[a,t], x[a])
    additional = H[a] * max(y[a,t] - x[a] * g[a,t], 0) / 1000
The area-level and uniform levels are ignored for that area; the floor and the
never-below-current-rate rules still apply. A path given without a `path` column applies
to every scenario path (lower, central, upper alike).

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
    spill = x * (1 + p.spillover) if at_benchmark else 0.0
    return max(p.floor_rate, p.level, spill, x)


def area_path_lookup(area_paths: pd.DataFrame | None, path_names) -> dict:
    """{(area_id, path): (r_1..r_5)} from a long table area_id, year (1..5), rate[, path]."""
    if area_paths is None or len(area_paths) == 0:
        return {}
    need = {"area_id", "year", "rate"}
    if need - set(area_paths.columns):
        raise ValueError(f"area_paths needs columns {sorted(need)}")
    out = {}
    for keys, g in area_paths.groupby(["area_id"] + (["path"] if "path" in area_paths.columns else [])):
        keys = keys if isinstance(keys, tuple) else (keys,)
        g = g.set_index(g["year"].astype(int))["rate"]
        if sorted(g.index) != list(YEARS) or g.isna().any() or (g < 0).any():
            raise ValueError(f"area path for {keys} needs a non-negative rate for each year {YEARS}")
        rates = tuple(float(g[t]) for t in YEARS)
        for path in ([keys[1]] if len(keys) > 1 else path_names):
            out[(keys[0], path)] = rates
    return out


def run(areas: pd.DataFrame, scenario: Scenario, baseline_growth: pd.DataFrame | None = None,
        area_levels: pd.DataFrame | None = None, area_paths: pd.DataFrame | None = None) -> pd.DataFrame:
    """Compute baseline and additional units by area, forecast year, and path.

    areas needs columns: area_id, homes (H), x_rate, at_benchmark (bool),
    x_basis, rights_basis. baseline_growth (optional) has area_id, year, g
    for places still ramping after a recent local reform; g defaults to 1.
    area_levels (optional) has area_id plus one column per path (e.g. y_lower,
    y_central, y_upper) giving an area-specific with-law level that replaces the
    path's uniform level for that area (for example from the market-adjusted
    regression); the floor and spillover rules still apply.
    area_paths (optional) has area_id, year (1..5), rate, and optionally path: an explicit
    with-law rate path per year that replaces the level and the ramp for that area (see the
    module docstring); without a path column it applies to every path.
    """
    need = {"area_id", "homes", "x_rate", "at_benchmark"}
    missing = need - set(areas.columns)
    if missing:
        raise ValueError(f"areas missing columns {sorted(missing)}")
    g = {}
    if baseline_growth is not None:
        g = {(r.area_id, int(r.year)): float(r.g) for r in baseline_growth.itertuples()}
    lv = {}
    if area_levels is not None:
        for r in area_levels.to_dict("records"):
            for path in scenario.paths:
                v = r.get(f"y_{path}")
                if v is not None and pd.notna(v):
                    lv[(r["area_id"], path)] = float(v)
    ap = area_path_lookup(area_paths, tuple(scenario.paths))
    rows = []
    for a in areas.itertuples(index=False):
        for path, p in scenario.paths.items():
            if (a.area_id, path) in lv:
                p = PathParams(level=lv[(a.area_id, path)], floor_rate=p.floor_rate,
                               spillover=p.spillover, ramp=p.ramp)
            fixed = ap.get((a.area_id, path))
            y = y_rate(a.x_rate, bool(a.at_benchmark), p)
            for i, t in enumerate(YEARS):
                gt = g.get((a.area_id, t), 1.0)
                x_t = a.x_rate * gt
                base = a.homes * x_t / 1000
                if fixed is None:
                    y_t, ramp_t = y, p.ramp[i]
                else:   # explicit observed path: its own ramp-up, so no ramp on top
                    y_t, ramp_t = max(p.floor_rate, fixed[i], a.x_rate), 1.0
                add = a.homes * max(y_t - x_t, 0.0) * ramp_t / 1000
                rows.append({
                    "scenario_id": scenario.scenario_id, "area_id": a.area_id, "path": path,
                    "year": t, "homes": a.homes, "x_rate": a.x_rate, "y_rate": y_t,
                    "y_source": "area_path" if fixed is not None else ("area_level" if (a.area_id, path) in lv else "uniform_level"),
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

"""TOD Gate 3 model: pure functions (no file paths, no network).

Implements docs/tod/GATE3_MODEL_SPEC.md:

Method A (section 2), per area a and year k since the law (2027 = year 1):
    addition(a, k) = eligible acres(a) x added FAR(a) x r x ramp(k)
                   = added floor area (sq ft) / 43,560 x r x ramp(k)
  r is extra homes permitted per eligible acre per year per 1.0 of added FAR, measured from the
  comparison cases; ramp(k) is the New York pooled set's gap per added FAR in year k divided by its
  mean over years 1 to 5 (so the ramp averages 1 and r x ramp(k) is the measured gap in year k).

Method B (section 3):
    addition(a, k) = feasible new capacity(a) x take-up x ramp(k)
  feasible new capacity = capacity gain on lots where a new mid-rise apartment at the law's density
  earns its cost (capitalised net rent >= building cost + assessed land value); take-up = Milwaukee's
  new homes per year in 5+ home buildings on land zoned for 30+ homes per acre / that land's feasible
  capacity under current zoning.

Baseline near stops (section 6): each municipality's all-housing baseline x its share of homes near
stops. Additions sit on top and are never negative.

Nothing here is calibrated: every parameter is passed in by the caller with its source.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

SQFT_PER_ACRE = 43_560.0
YEARS = (1, 2, 3, 4, 5)
CALENDAR = {k: 2026 + k for k in YEARS}  # year 1 = 2027

# --------------------------------------------------------------------------- ramp


def ramp_from_gaps(gaps: Sequence[float]) -> tuple[float, ...]:
    """Ramp(k) = gap(k) / mean(gap(1..5)). No smoothing, no assumed shape (spec section 2)."""
    g = np.asarray(gaps, dtype=float)
    if len(g) != len(YEARS):
        raise ValueError("need one gap per year 1..5")
    m = g.mean()
    if m <= 0:
        raise ValueError("mean gap must be positive")
    return tuple(float(x) for x in g / m)


def ramp_year5_alternative(gaps: Sequence[float]) -> tuple[float, ...]:
    """Sensitivity (spec section 2): year 5 takes the mean of years 3 to 5. The other years and the
    divisor (the measured mean of years 1 to 5, which is what r is) are unchanged, so r x ramp(k)
    stays the measured gap in years 1 to 4 and the year-5 drop is replaced."""
    g = np.asarray(gaps, dtype=float)
    alt = g.copy()
    alt[4] = g[2:5].mean()
    return tuple(float(x) for x in alt / g.mean())


# --------------------------------------------------------------------------- method A


def method_a_addition(added_floor_area_sqft: float, r: float, ramp: Sequence[float]) -> np.ndarray:
    """Extra homes permitted per year (years 1..5) for one area. added_floor_area_sqft is
    sum over eligible lots of max(law FAR - current FAR, 0) x lot area, so / 43,560 it is eligible
    acres x added FAR. Never negative."""
    dose = max(float(added_floor_area_sqft), 0.0) / SQFT_PER_ACRE
    return np.maximum(dose * float(r) * np.asarray(ramp, dtype=float), 0.0)


def fallback_added_floor_area(capacity_gain: float, sqft_per_home: float) -> float:
    """Added floor area for a place whose zoning is not coded. There the current allowance is the
    existing homes and the law's homes per acre are FAR-bound at the pooled floor area per home, so
    lot by lot max(law FAR x area - existing homes x sq ft per home, 0) = capacity gain x sq ft per
    home. (The station-area table stores 0 in added_floor_area_sqft for these places because no
    current FAR is coded, not because density does not rise.)"""
    return max(float(capacity_gain), 0.0) * float(sqft_per_home)


# --------------------------------------------------------------------------- method B: feasibility


@dataclass(frozen=True)
class FeasibilityParams:
    cap_rate: float            # going-in capitalisation rate (share)
    opex_ratio: float          # operating expenses incl. property taxes / gross rents collected
    cost_per_sqft: float       # hard construction cost per sq ft (HUD HCC, elevator)
    sqft_per_home: float       # gross floor area per home (measured)
    rent_ratio_new: float = 1.0  # new-building rent / all-building rent (1.0 when not available)


def value_per_home(monthly_rent: float, p: FeasibilityParams) -> float:
    """Capitalised net rent per home: 12 x rent x new-building ratio x (1 - opex) / cap rate."""
    return 12.0 * monthly_rent * p.rent_ratio_new * (1.0 - p.opex_ratio) / p.cap_rate


def cost_per_home(p: FeasibilityParams) -> float:
    return p.cost_per_sqft * p.sqft_per_home


def break_even_rent(p: FeasibilityParams) -> float:
    """Monthly (unscaled ACS) rent at which value per home equals building cost per home, with free land."""
    return cost_per_home(p) * p.cap_rate / (12.0 * p.rent_ratio_new * (1.0 - p.opex_ratio))


def is_feasible(homes: np.ndarray, monthly_rent: np.ndarray, land_value: np.ndarray,
                p: FeasibilityParams) -> np.ndarray:
    """A new building of `homes` homes earns its cost when homes x (value - cost) >= land value.
    Lots with no homes allowed, or no rent, are not feasible."""
    homes = np.asarray(homes, dtype=float)
    rent = np.asarray(monthly_rent, dtype=float)
    land = np.nan_to_num(np.asarray(land_value, dtype=float), nan=0.0)
    margin = homes * (value_per_home(1.0, p) * rent - cost_per_home(p))
    ok = (homes > 0) & np.isfinite(rent) & (rent > 0)
    return ok & (margin >= land)


def take_up_rate(new_homes: float, years: int, feasible_capacity: float) -> float:
    """Share of feasible capacity permitted per year. NaN when there is no feasible capacity."""
    if feasible_capacity <= 0:
        return float("nan")
    return float(new_homes) / float(years) / float(feasible_capacity)


def bootstrap_take_up(building_homes: Sequence[float], years: int, feasible_capacity: float,
                      draws: int = 2000, seed: int = 20261026) -> tuple[float, float]:
    """90% interval for take-up by redrawing whole buildings (projects) with replacement."""
    h = np.asarray(building_homes, dtype=float)
    if feasible_capacity <= 0 or len(h) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    sums = h[rng.integers(0, len(h), size=(draws, len(h)))].sum(axis=1)
    t = sums / years / feasible_capacity
    return float(np.quantile(t, 0.05)), float(np.quantile(t, 0.95))


def method_b_addition(feasible_capacity: float, take_up: float, ramp: Sequence[float]) -> np.ndarray:
    if not np.isfinite(take_up):
        return np.full(len(ramp), np.nan)
    return np.maximum(max(float(feasible_capacity), 0.0) * float(take_up) * np.asarray(ramp, dtype=float), 0.0)


# --------------------------------------------------------------------------- Madison test predictions


def method_a_madison_prediction(r: float, r_low: float, r_high: float, dose_far: float) -> dict:
    """Predicted DiD (extra homes per eligible acre per year) = r x Madison's added FAR (spec 4.1)."""
    return {"prediction": r * dose_far, "interval90_low": r_low * dose_far, "interval90_high": r_high * dose_far}


def method_b_madison_prediction(take_up: float, take_up_low: float, take_up_high: float,
                                delta_feasible_capacity: float, eligible_acres: float) -> dict:
    """Predicted DiD = take-up x change in feasible capacity from the overlay / eligible overlay acres."""
    per_acre = delta_feasible_capacity / eligible_acres if eligible_acres > 0 else float("nan")
    return {"prediction": take_up * per_acre, "interval90_low": take_up_low * per_acre,
            "interval90_high": take_up_high * per_acre}


# --------------------------------------------------------------------------- baseline near stops


def baseline_near_stops(baseline_by_area: pd.DataFrame, shares: pd.DataFrame, share_col: str) -> pd.DataFrame:
    """Per municipality piece: five-year and annual low/central/high baseline (all building sizes)
    x share of homes near stops. baseline_by_area has area_id, annual_*, five_year_*; shares has
    area_id and share_col."""
    cols = ["annual_low", "annual_central", "annual_high", "five_year_low", "five_year_central", "five_year_high"]
    b = baseline_by_area.groupby("area_id")[cols].sum().reset_index()
    b = b.merge(shares[["area_id", share_col]], on="area_id", how="left")
    s = b[share_col].fillna(0.0)
    out = b[["area_id"]].copy()
    out["share_near"] = s
    for c in cols:
        out[f"baseline_near_{c}"] = b[c] * s
    return out


# --------------------------------------------------------------------------- aggregation


def to_years(area_add: pd.DataFrame, value_cols: Iterable[str] | None = None) -> pd.DataFrame:
    """Long per-year table: area_add has area_id, method, scenario and add_y1..add_y5."""
    ycols = [f"add_y{k}" for k in YEARS]
    keys = [c for c in area_add.columns if c not in ycols]
    long = area_add.melt(id_vars=keys, value_vars=ycols, var_name="k", value_name="addition")
    long["year"] = long.k.str[-1].astype(int).map(CALENDAR)
    return long.drop(columns="k")


def aggregate(df: pd.DataFrame, keys: Sequence[str], value_cols: Sequence[str]) -> pd.DataFrame:
    return df.groupby(list(keys), dropna=False)[list(value_cols)].sum(min_count=1).reset_index()


def to_districts(df: pd.DataFrame, crosswalk: pd.DataFrame, district_col: str, keys: Sequence[str],
                 value_cols: Sequence[str]) -> pd.DataFrame:
    """Share each municipality piece's values out to districts by the crosswalk's share column
    (shares sum to 1 per area_id), then sum by district."""
    cw = crosswalk.groupby(["area_id", district_col], as_index=False)["share"].sum()
    x = df.merge(cw, on="area_id", how="inner")
    for c in value_cols:
        x[c] = x[c] * x["share"]
    return aggregate(x, [district_col, *keys], value_cols)


def check_no_negative(values: Iterable[float]) -> bool:
    v = np.asarray(list(values), dtype=float)
    return bool(np.all(np.nan_to_num(v, nan=0.0) >= -1e-9))


def case_reference_line(per_far_cases: Mapping[str, float]) -> float:
    """Median of every measured per-FAR case (spec section 5), named members counted through the pooled set."""
    return float(np.median(list(per_far_cases.values())))

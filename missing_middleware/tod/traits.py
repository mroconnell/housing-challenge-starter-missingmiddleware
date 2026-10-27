"""TOD trait test: why did upzoning near transit add many homes in some places and few in others?

Implements docs/tod/TRAITS_PLAN.md (written before any trait was compared with any effect). Results and every
departure are in docs/tod/TRAITS_RESULTS.md; departures are also in the plan's section 8.

- Units (plan section 2): separate rezonings or station areas inside each measured case. Each unit's own
  difference-in-differences uses its case's rules (cases.did, cases.bootstrap_did): the unit's treatment lots against
  the case's comparison lots within 1/4 mile of the unit's treatment lots. A unit is kept with at least 5 eligible
  acres in each of treatment and comparison (MIN_ACRES). The unit list is fixed before any trait is joined.
- Outcome (section 3): extra homes permitted per eligible acre per year (the unit's DiD), weighted by the unit's
  eligible treatment acres.
- Held-out test (section 5): baseline = weighted mean effect of the fitting units; one trait at a time = weighted
  linear model of the effect on the trait (logs for rent, home value, income, density and land area);
  leave-one-city-out; error = acre-weighted mean absolute error in homes per acre per year; a trait passes if it lowers
  the held-out error against the baseline both on average across cities and in at least half of the cities. Chicago and
  Madison units are always predicted and never fitted. A trait that lowers the error in only one held-out city is a
  near-miss, not a finding. Two-trait models use passing traits only.

The arithmetic here takes plain pandas tables so it can be tested without geography; geometry helpers take
GeoDataFrames in a projected CRS in metres.
"""
from __future__ import annotations

import itertools
import math
import re

import numpy as np
import pandas as pd

from missing_middleware.tod import cases as C

MIN_ACRES = 5.0
FIT_CITIES = ("New York", "Philadelphia", "Charlotte", "Saint Paul")
TEST_CITIES = ("Chicago", "Madison")
CITY_ORDER = FIT_CITIES + TEST_CITIES
STATION_CLUSTER_M = 150.0   # stops (platforms, directions) within this distance of each other are one station

# Traits (plan section 4). log=True: entered as natural logarithms (plan section 5.2).
TRAITS = {
    "t01_home_value": {"label": "Median home value", "log": True, "unit": "2024 dollars", "owner": "owner"},
    "t02_lot_size": {"label": "Average lot size of treatment parcels", "log": False, "unit": "acres per lot", "owner": "owner"},
    "t03_existing_density": {"label": "Existing density (homes per eligible acre before)", "log": True, "unit": "homes per eligible acre", "owner": "owner"},
    "t04_income": {"label": "Median household income", "log": True, "unit": "2024 dollars", "owner": "owner"},
    "t05_city_land_area": {"label": "Land area of the city", "log": True, "unit": "square miles", "owner": "owner"},
    "t06_rent": {"label": "Median gross rent", "log": True, "unit": "2024 dollars per month", "owner": "conductor"},
    "t07_added_far": {"label": "Size of the upzoning (added floor area ratio)", "log": False, "unit": "added FAR", "owner": "conductor"},
    "t08_rate_before": {"label": "Building rate before the change", "log": False, "unit": "homes permitted per eligible acre per year", "owner": "conductor"},
    "t09_vacant_parking_industrial_share": {"label": "Share of treatment land vacant, parking or industrial", "log": False, "unit": "share of acres", "owner": "conductor"},
    "t10_km_to_downtown": {"label": "Distance to the city's downtown", "log": False, "unit": "km", "owner": "conductor"},
    "t11_transit_jobs_access": {"label": "Jobs reachable by transit (EPA D5BR, 45 minutes, weighted)", "log": False, "unit": "jobs", "owner": "conductor"},
    "t12_parking_cut": {"label": "Reform also cut parking minimums (city level)", "log": False, "unit": "1 = yes, 0 = no", "owner": "conductor"},
}
# Density can be zero; its logarithm is taken of (homes per acre + LOG_DENSITY_OFFSET). Recorded in plan section 8.
LOG_DENSITY_OFFSET = 1.0


# --------------------------------------------------------------------------- units

def keep_unit(treat_acres: float, comp_acres: float, min_acres: float = MIN_ACRES) -> tuple[bool, str]:
    """Plan section 2: at least min_acres eligible acres in each of treatment and comparison."""
    t = 0.0 if treat_acres is None or (isinstance(treat_acres, float) and math.isnan(treat_acres)) else float(treat_acres)
    c = 0.0 if comp_acres is None or (isinstance(comp_acres, float) and math.isnan(comp_acres)) else float(comp_acres)
    if t < min_acres and c < min_acres:
        return False, f"treatment {t:.1f} and comparison {c:.1f} eligible acres, both under {min_acres:g}"
    if t < min_acres:
        return False, f"treatment {t:.1f} eligible acres, under {min_acres:g}"
    if c < min_acres:
        return False, f"comparison {c:.1f} eligible acres, under {min_acres:g}"
    return True, "kept"


def unit_estimate(permits: pd.DataFrame, acres: dict, before: list[int], after: list[int], draws: int = C.N_DRAWS,
                  seed: int = C.SEED) -> dict:
    """The unit's DiD (homes permitted per eligible acre per year) and 90% project-bootstrap interval (cases rules)."""
    out = {"did": np.nan, "low": np.nan, "high": np.nan, "treat_before": np.nan, "treat_after": np.nan,
           "comp_before": np.nan, "comp_after": np.nan}
    if not before or not after or not acres.get(C.TREAT) or not acres.get(C.COMP):
        return out
    e = C.did(permits, acres, before, after)
    lo, hi, _ = C.bootstrap_did(permits, acres, before, after, draws=draws, seed=seed)
    out.update({k: e[k] for k in ("did", "treat_before", "treat_after", "comp_before", "comp_after")}, low=lo, high=hi)
    return out


def units_in(permits: pd.DataFrame, area: str, years: list[int]) -> float:
    return float(permits[(permits["area"] == area) & permits["year"].isin(years)]["units"].sum())


def cluster_stations(stops, names: pd.Series | None = None, within_m: float = STATION_CLUSTER_M):
    """One point per station: stops within within_m of each other (platforms, directions) are merged. Returns a
    GeoDataFrame with columns station (name of the first stop, or 'station N') and geometry (mean point)."""
    import geopandas as gpd
    from shapely.geometry import Point
    pts = list(stops.geometry) if hasattr(stops, "geometry") else list(stops)
    n = len(pts)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if pts[i].distance(pts[j]) <= within_m:
                parent[find(i)] = find(j)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    rows = []
    for k, (_, ix) in enumerate(sorted(groups.items(), key=lambda kv: min(kv[1]))):
        nm = None
        if names is not None:
            vals = [str(names.iloc[i]) for i in ix if isinstance(names.iloc[i], str)]
            nm = sorted(vals, key=len)[0] if vals else None
        rows.append({"station": clean_station_name(nm) if nm else f"station {k + 1}",
                     "geometry": Point(np.mean([pts[i].x for i in ix]), np.mean([pts[i].y for i in ix]))})
    crs = getattr(stops, "crs", None)
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=crs)
    # distinct stations sharing a name (e.g. two 'Western' stops on different lines) get a number
    dup = g["station"].duplicated(keep=False)
    if dup.any():
        g.loc[dup, "station"] = [f"{s} ({i + 1})" for i, s in zip(g.loc[dup].groupby("station").cumcount(), g.loc[dup, "station"])]
    return g


def clean_station_name(s: str) -> str:
    s = re.sub(r"\s+(Station|Platform\s*\d+|Stop)\b.*$", "", str(s).strip(), flags=re.I)
    return s.strip(" -")


def nearest_station(points, stations) -> pd.Series:
    """Name of the nearest station for each point (GeoSeries in the same CRS)."""
    import geopandas as gpd
    j = gpd.sjoin_nearest(gpd.GeoDataFrame(geometry=points, crs=stations.crs), stations[["station", "geometry"]], how="left")
    j = j[~j.index.duplicated()]
    return j["station"].reindex(points.index)


SECTORS = ("north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest")


def sector_label(dx: float, dy: float, core_m: float) -> str:
    """Corridor segment by position relative to a centre: 'core' within core_m, else one of eight 45-degree sectors
    (north = bearing 337.5 to 22.5 degrees)."""
    if math.hypot(dx, dy) <= core_m:
        return "core"
    bearing = (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0
    return SECTORS[int(((bearing + 22.5) % 360.0) // 45.0)]


def comparison_for_unit(parcels, treat_ix, comp_ix, ring_m: float = C.QUARTER_MILE_M) -> pd.Index:
    """The case's comparison lots whose representative point lies within ring_m of the unit's treatment lots
    (the rule of cases.assign_areas applied to the unit)."""
    tu = parcels.loc[treat_ix].geometry.union_all().buffer(ring_m)
    pts = parcels.loc[comp_ix].geometry.representative_point()
    return pts.index[pts.within(tu)]


# --------------------------------------------------------------------------- trait arithmetic

def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    d = pd.DataFrame({"v": values, "w": weights}).dropna()
    d = d[d["w"] > 0]
    if d.empty:
        return float("nan")
    return float((d["v"] * d["w"]).sum() / d["w"].sum())


def transform(df: pd.DataFrame, trait: str) -> pd.Series:
    """The trait as entered in the model (plan section 5.2: logs for rent, home value, income, density, land area)."""
    x = pd.to_numeric(df[trait], errors="coerce").astype(float)
    if not TRAITS[trait]["log"]:
        return x
    if trait == "t03_existing_density":
        x = x + LOG_DENSITY_OFFSET
    return np.log(x.where(x > 0))


def cpi_to_2024(value: float, year: int) -> float:
    """Dollars of `year` in 2024 dollars (CPI-U, U.S. city average, annual average, BLS series CUUR0000SA0)."""
    return value * CPI_U[2024] / CPI_U[year]


CPI_U = {2010: 218.056, 2022: 292.655, 2024: 313.689}


# --------------------------------------------------------------------------- held-out test

def wls(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return beta


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str], y: str = "effect", w: str = "weight") -> np.ndarray:
    """Weighted linear model of y on cols (with intercept) fitted on train, predicted on test. With no cols, the
    weighted mean of train (the baseline)."""
    Xtr = np.column_stack([np.ones(len(train))] + [train[c].values.astype(float) for c in cols])
    Xte = np.column_stack([np.ones(len(test))] + [test[c].values.astype(float) for c in cols])
    b = wls(Xtr, train[y].values.astype(float), train[w].values.astype(float))
    return Xte @ b


def weighted_mae(pred: np.ndarray, obs: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum(np.abs(pred - obs) * w) / np.sum(w))


def heldout_errors(df: pd.DataFrame, cols: list[str], fit_cities=FIT_CITIES, test_cities=TEST_CITIES,
                   y: str = "effect", w: str = "weight", city: str = "city") -> pd.DataFrame:
    """Leave-one-city-out errors of a model (cols) and of the baseline (weighted mean), on the same units.

    Units with a missing value of any col are left out of both (so model and baseline are judged on the same
    units). Fit cities: each is predicted from the other fit cities only. Test cities (Chicago, Madison): predicted
    from all fit cities, never fitted. Returns one row per city with acre-weighted mean absolute errors."""
    d = df.dropna(subset=[y, w] + cols)
    d = d[d[w] > 0]
    rows = []
    for c in list(fit_cities) + list(test_cities):
        test = d[d[city] == c]
        train = d[d[city].isin([f for f in fit_cities if f != c])]
        if test.empty or train.empty or train[city].nunique() < 1:
            continue
        if cols and any(np.ptp(train[k].values.astype(float)) == 0 for k in cols):
            # a trait with no spread among the fitting units cannot be fitted: its prediction is the baseline
            pm = fit_predict(train, test, [], y, w)
            note = "no spread in the fitting units"
        else:
            pm = fit_predict(train, test, cols, y, w)
            note = ""
        pb = fit_predict(train, test, [], y, w)
        ob, ww = test[y].values.astype(float), test[w].values.astype(float)
        rows.append({"city": c, "role": "fold" if c in fit_cities else "always held out", "units": len(test),
                     "treatment_acres": float(ww.sum()), "fit_units": len(train), "fit_cities": int(train[city].nunique()),
                     "error_baseline": weighted_mae(pb, ob, ww), "error_model": weighted_mae(pm, ob, ww),
                     "measured_mean": float(np.sum(ob * ww) / ww.sum()), "predicted_mean_model": float(np.sum(pm * ww) / ww.sum()),
                     "predicted_mean_baseline": float(np.sum(pb * ww) / ww.sum()), "note": note})
    return pd.DataFrame(rows)


def judge(errors: pd.DataFrame) -> dict:
    """Plan section 5.3 and 5.6, on the leave-one-city-out folds (the fitting cities).

    pass: the model's error is lower than the baseline's on average across the fold cities (simple mean of the
    cities' acre-weighted errors) and in at least half of the fold cities, and in more than one city. near-miss: lower
    in exactly one fold city (section 5.6 overrides 5.3 when only two folds exist and one is half). fail: otherwise."""
    f = errors[errors["role"] == "fold"]
    if f.empty:
        return {"verdict": "not testable", "cities_better": 0, "cities": 0, "mean_error_baseline": np.nan, "mean_error_model": np.nan}
    better = int((f["error_model"] < f["error_baseline"] - 1e-12).sum())
    mb, mm = float(f["error_baseline"].mean()), float(f["error_model"].mean())
    n = len(f)
    if better == 1:
        v = "near-miss"
    elif mm < mb and better >= math.ceil(n / 2):
        v = "pass"
    else:
        v = "fail"
    return {"verdict": v, "cities_better": better, "cities": n, "mean_error_baseline": mb, "mean_error_model": mm}


def two_trait_sets(passing: list[str]) -> list[tuple[str, str]]:
    return list(itertools.combinations(passing, 2))


# --------------------------------------------------------------------------- privacy

ID_LIKE = re.compile(r"(^|_)(parcel|pin|bbl|block|lot|permit|project|address|owner|job|bill)s?(_?id|_?num(ber)?|_?no|$)", re.I)


def check_private(df: pd.DataFrame, allowed: set[str] = frozenset()) -> list[str]:
    """Column names that look like identifiers of parcels, permits, projects or people (must be empty for outputs)."""
    return [c for c in df.columns if ID_LIKE.search(c) and c not in allowed]

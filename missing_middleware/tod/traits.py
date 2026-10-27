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


# --------------------------------------------------------------------------- exploratory combinations
# Owner-approved exploration (plan section 8, entry "exploratory combinations", 2026-10-27): all 66 trait pairs and one
# regression tree (depth <= 2, >= 8 units per leaf), same folds, error and transforms; stricter pass rule.

TREE_MAX_DEPTH = 2
TREE_MIN_LEAF = 8
CHANCE_WARNING = ("Exploratory: about 3 of 66 pairs would be expected to look good by chance; shown as a sensitivity "
                  "only, never used for the main estimate.")


def judge_strict(errors: pd.DataFrame) -> dict:
    """Pass only if the model beats the baseline in at least 3 of the 4 fitted cities, on average across them, and
    in Chicago and in Madison, each by itself."""
    f = errors[errors["role"] == "fold"]
    h = errors[errors["role"] == "always held out"].set_index("city")
    better = int((f["error_model"] < f["error_baseline"] - 1e-12).sum())
    mb, mm = float(f["error_baseline"].mean()), float(f["error_model"].mean())
    held = {c: bool(c in h.index and h.loc[c, "error_model"] < h.loc[c, "error_baseline"] - 1e-12) for c in TEST_CITIES}
    ok = len(f) == len(FIT_CITIES) and better >= 3 and mm < mb and all(held.values())
    return {"verdict": "pass (exploratory)" if ok else "fail", "fold_cities_better": better, "fold_cities": len(f),
            "mean_error_baseline": mb, "mean_error_model": mm,
            **{f"beats_baseline_{c.lower()}": v for c, v in held.items()}}


def _wsse(y: np.ndarray, w: np.ndarray) -> float:
    if len(y) == 0:
        return 0.0
    m = np.sum(w * y) / np.sum(w)
    return float(np.sum(w * (y - m) ** 2))


def fit_tree(df: pd.DataFrame, cols: list[str], y: str = "effect", w: str = "weight", depth: int = TREE_MAX_DEPTH,
             min_leaf: int = TREE_MIN_LEAF) -> dict:
    """Weighted regression tree (least squares). A split is 'col <= threshold'; units with a missing value of the
    split's trait follow the child with more acres. Leaves predict the acre-weighted mean effect."""
    yy, ww = df[y].values.astype(float), df[w].values.astype(float)
    node = {"n": len(df), "acres": float(ww.sum()), "value": float(np.sum(yy * ww) / ww.sum())}
    if depth == 0 or len(df) < 2 * min_leaf:
        return node
    best, base = None, _wsse(yy, ww)
    for c in cols:
        x = df[c].values.astype(float)
        ok = ~np.isnan(x)
        vals = np.unique(x[ok])
        for lo, hi in zip(vals[:-1], vals[1:]):
            t = (lo + hi) / 2
            left = ok & (x <= t)
            right = ok & (x > t)
            if ww[left].sum() >= ww[right].sum():
                left = left | ~ok
            else:
                right = right | ~ok
            if left.sum() < min_leaf or right.sum() < min_leaf:
                continue
            gain = base - _wsse(yy[left], ww[left]) - _wsse(yy[right], ww[right])
            if gain > 1e-12 and (best is None or gain > best[0]):
                best = (gain, c, t, bool(ww[left & ok].sum() >= ww[right & ok].sum()))
    if best is None:
        return node
    _, c, t, miss_left = best
    x = df[c].values.astype(float)
    go_left = np.where(np.isnan(x), miss_left, x <= t)
    node.update(col=c, threshold=float(t), missing_left=miss_left,
                left=fit_tree(df[go_left], cols, y, w, depth - 1, min_leaf),
                right=fit_tree(df[~go_left], cols, y, w, depth - 1, min_leaf))
    return node


def predict_tree(node: dict, df: pd.DataFrame) -> np.ndarray:
    out = np.empty(len(df))
    for i, (_, r) in enumerate(df.iterrows()):
        n = node
        while "col" in n:
            v = r[n["col"]]
            n = n["left"] if (n["missing_left"] if pd.isna(v) else v <= n["threshold"]) else n["right"]
        out[i] = n["value"]
    return out


def tree_rows(node: dict, path: str = "all units") -> list[dict]:
    """The tree as rows: one per node, with its rule, units, acres and value."""
    rows = [{"node": path, "units": node["n"], "acres": node["acres"], "mean_effect": node["value"],
             "split_trait": node.get("col", ""), "split_threshold": node.get("threshold", np.nan),
             "missing_values_go": ("left (<=)" if node.get("missing_left") else "right (>)") if "col" in node else ""}]
    if "col" in node:
        rows += tree_rows(node["left"], f"{path} / {node['col']} <= {node['threshold']:.4g}")
        rows += tree_rows(node["right"], f"{path} / {node['col']} > {node['threshold']:.4g}")
    return rows


def heldout_tree_errors(df: pd.DataFrame, cols: list[str], y: str = "effect", w: str = "weight",
                        city: str = "city") -> pd.DataFrame:
    """Leave-one-city-out errors of the tree against the baseline, on every unit (missing trait values are routed)."""
    d = df.dropna(subset=[y, w])
    d = d[d[w] > 0]
    rows = []
    for c in list(FIT_CITIES) + list(TEST_CITIES):
        test = d[d[city] == c]
        train = d[d[city].isin([f for f in FIT_CITIES if f != c])]
        if test.empty or train.empty:
            continue
        tree = fit_tree(train, cols, y, w)
        pm, pb = predict_tree(tree, test), fit_predict(train, test, [], y, w)
        ob, ww = test[y].values.astype(float), test[w].values.astype(float)
        rows.append({"city": c, "role": "fold" if c in FIT_CITIES else "always held out", "units": len(test),
                     "treatment_acres": float(ww.sum()), "fit_units": len(train), "fit_cities": int(train[city].nunique()),
                     "error_baseline": weighted_mae(pb, ob, ww), "error_model": weighted_mae(pm, ob, ww),
                     "measured_mean": float(np.sum(ob * ww) / ww.sum()), "predicted_mean_model": float(np.sum(pm * ww) / ww.sum()),
                     "predicted_mean_baseline": float(np.sum(pb * ww) / ww.sum()),
                     "splits": "; ".join(f"{r['node']}" for r in tree_rows(tree) if r["split_trait"] == "" and r["node"] != "all units")})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- wider set, several tools
# Plan section 8, entries "rerun on the wider case set with several tools" and "details of the several-tools rerun"
# (2026-10-27, written before the run). Same leave-one-city-out test against the plain average on more cities, with
# eight tools; a stricter pass rule because many tools are tried.

WIDE_FIT_CITIES = ("New York", "Philadelphia", "Charlotte", "Saint Paul", "Los Angeles", "Seattle")
WIDE_CONTEXT_CITIES = ("Bellevue", "Toronto")   # units built and predicted, never fitted or judged
WIDE_CITY_ORDER = WIDE_FIT_CITIES + TEST_CITIES + WIDE_CONTEXT_CITIES
TOOL_SEED = 20261027
CF_TREES = 500
CF_MIN_LEAF = 5
KNN_K = 5


def role_of(city: str) -> str:
    if city in WIDE_FIT_CITIES:
        return "fold"
    if city in TEST_CITIES:
        return "always held out"
    return "context"


def judge_tools(errors: pd.DataFrame, fit_cities=WIDE_FIT_CITIES) -> dict:
    """Pass only if the tool beats the plain average in at least two-thirds of the fold cities, on the simple mean of
    the fold cities' errors, and in Chicago and in Madison, each by itself."""
    f = errors[errors["role"] == "fold"]
    h = errors[errors["role"] == "always held out"].set_index("city")
    better = int((f["error_model"] < f["error_baseline"] - 1e-12).sum())
    need = math.ceil(2 * len(fit_cities) / 3)
    mb, mm = float(f["error_baseline"].mean()), float(f["error_model"].mean())
    held = {c: bool(c in h.index and h.loc[c, "error_model"] < h.loc[c, "error_baseline"] - 1e-12) for c in TEST_CITIES}
    ok = len(f) == len(fit_cities) and better >= need and mm < mb - 1e-12 and all(held.values())
    return {"verdict": "pass" if ok else "fail", "fold_cities_better": better, "fold_cities": len(f), "fold_cities_needed": need,
            "mean_error_baseline": mb, "mean_error_model": mm, **{f"beats_baseline_{c.lower()}": v for c, v in held.items()}}


def weighted_fill(train: pd.DataFrame, test: pd.DataFrame, cols: list[str], w: str = "weight"):
    """Missing trait values filled with the acre-weighted mean of the training units (worked out inside the fold).
    A trait with no value in the training fold is dropped."""
    keep = [c for c in cols if train[c].notna().any()]
    means = {c: weighted_mean(train[c], train[w]) for c in keep}
    return train[keep].fillna(means).values.astype(float), test[keep].fillna(means).values.astype(float), keep


def standardize(Xtr: np.ndarray, Xte: np.ndarray):
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (Xtr - mu) / sd, (Xte - mu) / sd


def knn_predict(Xtr: np.ndarray, ytr: np.ndarray, wtr: np.ndarray, Xte: np.ndarray, k: int = KNN_K) -> np.ndarray:
    """Acre-weighted mean effect of the k nearest training units (Euclidean distance on standardized traits)."""
    out = np.empty(len(Xte))
    for i, x in enumerate(Xte):
        dist = np.sqrt(((Xtr - x) ** 2).sum(axis=1))
        nn = np.argsort(dist, kind="stable")[:k]
        out[i] = float(np.sum(ytr[nn] * wtr[nn]) / np.sum(wtr[nn]))
    return out


# honest causal forest ------------------------------------------------------------------------------------------------
# Each unit is a pair: a treated observation (treatment-area change, after minus before, weight = treatment acres) and a
# control observation (comparison-area change, weight = comparison acres). A leaf's effect is the weighted mean treated
# change minus the weighted mean control change of its units; for one unit this is exactly the unit's DiD.

def _leaf_tau(yt, wt, yc, wc) -> float:
    st, sc = wt.sum(), wc.sum()
    if st <= 0 or sc <= 0:
        return float("nan")
    return float(np.sum(yt * wt) / st - np.sum(yc * wc) / sc)


def _cf_best_split(X, yt, wt, yc, wc, min_leaf):
    """Split maximizing sum over children of (treatment acres x child effect squared), i.e. the acre-weighted spread
    of the effect between children (the causal-tree criterion for a fixed parent)."""
    n, p = X.shape
    best = None
    i = np.arange(min_leaf - 1, n - min_leaf)
    if len(i) == 0:
        return None
    for j in range(p):
        order = np.argsort(X[:, j], kind="stable")
        x = X[order, j]
        cs = [np.cumsum(a[order]) for a in (yt * wt, wt, yc * wc, wc)]
        L = [c[i] for c in cs]
        R = [c[-1] - l for c, l in zip(cs, L)]
        ok = (x[i] != x[i + 1]) & (L[1] > 0) & (L[3] > 0) & (R[1] > 0) & (R[3] > 0)
        if not ok.any():
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            tl = L[0] / L[1] - L[2] / L[3]
            tr = R[0] / R[1] - R[2] / R[3]
            crit = np.where(ok, L[1] * tl * tl + R[1] * tr * tr, -np.inf)
        k = int(np.argmax(crit))
        if best is None or crit[k] > best[0] + 1e-12:
            best = (float(crit[k]), j, float((x[i[k]] + x[i[k] + 1]) / 2.0))
    return best


def _cf_grow(Xs, ys, Xe, ye, min_leaf, rng):
    """Honest tree: splits chosen on the split half (Xs, ys), leaf effects estimated on the estimation half (Xe, ye).
    ys/ye are tuples (yt, wt, yc, wc). A split must leave at least min_leaf units of each half in each child."""
    est = _leaf_tau(*(a for a in ye)) if len(Xe) else float("nan")
    node = {"value": est}
    if len(Xs) < 2 * min_leaf or len(Xe) < 2 * min_leaf:
        return node
    b = _cf_best_split(Xs, *ys, min_leaf)
    if b is None:
        return node
    _, j, t = b
    ls, le = Xs[:, j] <= t, Xe[:, j] <= t
    if le.sum() < min_leaf or (~le).sum() < min_leaf:
        return node
    node.update(col=j, threshold=t,
                left=_cf_grow(Xs[ls], tuple(a[ls] for a in ys), Xe[le], tuple(a[le] for a in ye), min_leaf, rng),
                right=_cf_grow(Xs[~ls], tuple(a[~ls] for a in ys), Xe[~le], tuple(a[~le] for a in ye), min_leaf, rng))
    return node


def _cf_predict_one(node, x) -> float:
    while "col" in node:
        node = node["left"] if x[node["col"]] <= node["threshold"] else node["right"]
    return node["value"]


def causal_forest_predict(Xtr, yt, wt, yc, wc, Xte, n_trees: int = CF_TREES, min_leaf: int = CF_MIN_LEAF,
                          seed: int = TOOL_SEED) -> np.ndarray:
    """Mean over honest trees of the leaf effect (homes per acre per year) for each test row."""
    rng = np.random.default_rng(seed)
    n = len(Xtr)
    preds = np.zeros(len(Xte))
    used = 0
    for _ in range(n_trees):
        sub = rng.permutation(n)[: n // 2]
        half = len(sub) // 2
        s, e = sub[:half], sub[half:]
        tree = _cf_grow(Xtr[s], (yt[s], wt[s], yc[s], wc[s]), Xtr[e], (yt[e], wt[e], yc[e], wc[e]), min_leaf, rng)
        p = np.array([_cf_predict_one(tree, x) for x in Xte])
        if np.isnan(p).any():
            continue
        preds += p
        used += 1
    return preds / used if used else np.full(len(Xte), np.nan)


# multilevel model (random intercept per city), for uncertainty --------------------------------------------------------

def random_intercept_fit(df: pd.DataFrame, y: str = "effect", w: str = "weight", city: str = "city") -> dict:
    """effect = mu + city intercept (variance tau2) + unit noise. Fitted by maximum likelihood on the cities'
    acre-weighted means, each with sampling variance s_c^2 = sigma2 * sum(w^2) / (sum w)^2, where sigma2 is the pooled
    acre-weighted within-city variance. Returns mu, its standard error, tau (between-city sd) and sigma (within)."""
    from scipy.optimize import minimize_scalar
    g = []
    num = den = 0.0
    for _, d in df.groupby(city):
        yy, ww = d[y].values.astype(float), d[w].values.astype(float)
        m = float(np.sum(yy * ww) / ww.sum())
        num += float(np.sum(ww * (yy - m) ** 2))
        den += float(ww.sum()) * (1 - float(np.sum(ww ** 2)) / float(ww.sum()) ** 2)
        g.append((m, float(np.sum(ww ** 2)) / float(ww.sum()) ** 2))
    sigma2 = num / den if den > 0 else 0.0
    m = np.array([a for a, _ in g])
    s2 = sigma2 * np.array([b for _, b in g])

    def mu_of(t2):
        v = t2 + s2
        return float(np.sum(m / v) / np.sum(1 / v)), float(1 / np.sum(1 / v))

    def nll(lt):
        t2 = math.exp(lt)
        v = t2 + s2
        mu, _ = mu_of(t2)
        return 0.5 * float(np.sum(np.log(v) + (m - mu) ** 2 / v))
    r = minimize_scalar(nll, bounds=(-20, 8), method="bounded")
    t2 = math.exp(r.x)
    mu, vmu = mu_of(t2)
    return {"mu": mu, "mu_se": math.sqrt(vmu), "tau": math.sqrt(t2), "sigma": math.sqrt(sigma2), "cities": len(g)}


def new_city_interval(fit: dict, z: float = 1.6449) -> tuple[float, float]:
    """90% interval for a new city's acre-weighted mean effect (between-city spread plus uncertainty in mu)."""
    h = z * math.sqrt(fit["tau"] ** 2 + fit["mu_se"] ** 2)
    return fit["mu"] - h, fit["mu"] + h

"""Pooled up- and downzonings with building pressure (docs/tod/UPDOWN_PLAN.md, written before fitting).

    uv run --all-extras python scripts/run_tod_updown.py --stage collect   # rebuild cases, measure up and down units
    uv run --all-extras python scripts/run_tod_updown.py --stage fit       # 8 methods, leave-one-city-out, Chicago held out

Writes reference/tod_updown_units.csv and reference/tod_updown_models.csv (aggregates only).
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import cases as C  # noqa: E402
from missing_middleware.tod import traits as T  # noqa: E402
from scripts.run_tod_net_effect import _permits_from_points, capture, widen  # noqa: E402

OUT = PROCESSED / "tod_updown"
UNITS = REFERENCE / "tod_updown_units.csv"
MODELS = REFERENCE / "tod_updown_models.csv"
FOLD = ("New York", "Philadelphia", "Saint Paul", "Seattle")
HOLD = ("Chicago",)
MIN_ACRES = 3.0
INVENTORY = {"New York": "nyc_bloomberg_rezonings_2003_2013", "Philadelphia": "philadelphia_2012_code",
             "Saint Paul": "stpaul_green_line_2011", "Seattle": "seattle_nbh_othello_2012", "Chicago": "chicago_tod_2013_2015"}


def rail(crs):
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    return gpd.GeoDataFrame(geometry=gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(crs).geometry.union_all()


def rate(q: pd.DataFrame, lab: str, years: list[int], acres: float) -> float:
    return q.loc[(q["area"] == lab) & q["year"].isin(years), "units"].sum() / len(years) / acres if acres > 0 else np.nan


def measure(city: str, unit_id: str, args: dict, area: pd.Series, q: pd.DataFrame, per: dict, stops) -> list[dict]:
    """Up and down units of one case or member. q: permits with pix and calendar year."""
    L = args["parcels"]
    acres = L.geometry.area / C.SQM_PER_ACRE
    elig = args["eligible"].astype(bool)
    lb, la = args["level_before"].astype(float), args["level_after"].astype(float)
    near = L.geometry.representative_point().distance(stops) <= C.HALF_MILE_M
    in_reform = args["in_reform"].astype(bool)
    outside = args["changed_outside"].astype(bool)
    fell = (la < lb - 1e-9) & np.isfinite(lb) & np.isfinite(la) & elig & near
    lab = pd.Series(None, index=L.index, dtype=object)
    lab[area == C.COMP] = "comp"
    lab[area == C.TREAT] = "up"
    lab[fell & in_reform] = "down_in"
    lab[fell & outside & ~in_reform] = "down_out"
    p = q.dropna(subset=["pix"]).copy()
    p["area"] = lab.reindex(p["pix"].astype(int)).values
    p = p[p["area"].notna()]
    b, a = per["before"], per["after"]
    ca = float(acres[lab == "comp"].sum())
    cb, cr = rate(p, "comp", b, ca), rate(p, "comp", a, ca)
    rows = []
    for kind in ("up", "down_in", "down_out"):
        m = lab == kind
        ac = float(acres[m].sum())
        if ac < MIN_ACRES or ca <= 0:
            continue
        dfar = float(((la - lb)[m].replace([np.inf, -np.inf], np.nan) * acres[m]).sum() / acres[m].sum())
        if not np.isfinite(dfar) or abs(dfar) < 1e-6:
            continue
        ub, ua = rate(p, kind, b, ac), rate(p, kind, a, ac)
        did = (ua - ub) - (cr - cb)
        fb = float((lb[m].replace(np.inf, np.nan) * acres[m]).sum() / acres[m].sum())
        rows.append({"unit": f"{unit_id}:{kind}", "city": city, "kind": kind, "direction_up": float(kind == "up"),
                     "acres": ac, "comparison_acres": ca, "far_change": dfar, "far_before": fb,
                     "pressure_before": ub, "comp_pressure_before": cb, "did_per_acre_year": did,
                     "response_per_far": did / dfar, "d_treat": (ua - ub) / dfar, "d_comp": (cr - cb) / dfar})
    return rows


def collect() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, stops = [], None
    # New York members
    from missing_middleware.tod import case_nyc as N
    for ulurp, (name, boro) in N.POOLED.items():
        with capture(nyc=N) as cap:
            try:
                m = N.build_member(ulurp, boro)
            except Exception as e:  # noqa: BLE001
                print(f"  {name}: {type(e).__name__}: {e}")
                continue
        args, area = cap["uniform"][-1]
        stops = stops or {}
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        jg, ix = cap["jobs"][-1]
        rows += measure("New York", f"nyc_{ulurp}", args, area, _permits_from_points(jg, ix), m["per"], stops[crs])
        print(f"New York {name}: {len(rows)} units so far", flush=True)
    # Philadelphia members (including members with no upzoned land)
    from missing_middleware.tod import case_philadelphia as P
    d = P._load()
    rm = d["rm"]
    dp = rm[(rm["Origination"] == "DistrictPlan") & rm["changes"] & rm["enacted"].dt.year.between(*P.MEMBER_YEARS)]
    q = _permits_from_points(d["permits"], d["permits"]["pix"])
    for bill in sorted(dp["Bill_Number_TXT"].astype(str).unique()):
        with capture() as cap:
            try:
                m = P.build_member(bill)
            except Exception as e:  # noqa: BLE001
                print(f"  {bill}: {type(e).__name__}: {e}")
                continue
        args, area = cap["uniform"][-1]
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        rows += measure("Philadelphia", f"phl_{bill}", args, area, q, m["per"], stops[crs])
    print(f"Philadelphia: {len(rows)} units so far", flush=True)
    # Chicago and Saint Paul
    for key, city in (("chicago", "Chicago"), ("stpaul", "Saint Paul")):
        mod = importlib.import_module(f"missing_middleware.tod.case_{key}")
        with capture() as cap:
            ci, _ = mod.build()
        args, area = cap["uniform"][0]
        pts, pix = cap["locate"][-1]
        per = C.period_years(ci.effective_year, ci.first_year, ci.last_full_year)
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        rows += measure(city, key, args, area, _permits_from_points(pts, pix), per, stops[crs])
        print(f"{city}: {len(rows)} units so far", flush=True)
    # Seattle cases
    from missing_middleware.tod import case_seattle as K
    for case in ("seattle_nbh_othello_2012", "seattle_mount_baker_2014"):
        with capture() as cap:
            f = K._frame(case)
        args, area = cap["uniform"][-1]
        pg = K._load()["permits"]
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        rows += measure("Seattle", case, args, area, _permits_from_points(pg, pg["pix"]), f["per"], stops[crs])
    print(f"Seattle: {len(rows)} units so far", flush=True)
    U = pd.DataFrame(rows)
    inv = pd.read_csv(REFERENCE / "tod_cases.csv").set_index("case_id")
    U["rent"] = [pd.to_numeric(inv.loc[INVENTORY[c], "median_gross_rent_usd_per_month"], errors="coerce") for c in U["city"]]
    U["home_value"] = [pd.to_numeric(inv.loc[INVENTORY[c], "median_home_value_usd"], errors="coerce") for c in U["city"]]
    assert not T.check_private(U.drop(columns=["unit"]))
    U.round(5).to_csv(UNITS, index=False)
    print(U.groupby(["city", "kind"]).agg(n=("unit", "size"), acres=("acres", "sum")).round(1).to_string())


# --------------------------------------------------------------------------- fit
def frame(drop_outside: bool = False) -> tuple[pd.DataFrame, list[str]]:
    d = pd.read_csv(UNITS)
    if drop_outside:
        d = d[d["kind"] != "down_out"]
    d = d.assign(effect=d["response_per_far"], weight=d["acres"])
    d["x_pressure"] = np.log1p(d["pressure_before"].clip(lower=0))
    d["x_comp_pressure"] = np.log1p(d["comp_pressure_before"].clip(lower=0))
    d["x_up"] = d["direction_up"]
    d["x_abs_far_change"] = d["far_change"].abs()
    d["x_far_before"] = d["far_before"]
    d["x_log_acres"] = np.log(d["acres"])
    d["x_rent"] = d["rent"]
    d["x_home_value"] = np.log(d["home_value"])
    return d, [c for c in d.columns if c.startswith("x_")]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=["collect", "fit"], required=True)
    a = ap.parse_args(argv)
    if a.stage == "collect":
        collect()
        return
    import run_tod_census_predict as P2
    P2.FOLD, P2.HOLD = FOLD, HOLD
    rows = []
    for variant, drop in (("all units", False), ("down units changed outside the reform left out", True)):
        d, cols = frame(drop)
        for tool, cc, label in [("baseline", [], P2.LABELS["baseline"])] + [(t, cols, P2.LABELS[t]) for t in P2.TOOLS] + \
                               [("wls", ["x_pressure"], "building pressure alone (weighted regression)")]:
            e = P2.errors(d, tool, cc)
            j = P2.judge(e) if tool != "baseline" else {"verdict": "baseline"}
            j["fold_cities_needed"] = math.ceil(2 * len(FOLD) / 3)
            row = {"variant": variant, "method": label, "units": len(d), **j}
            for r in e.itertuples():
                row[f"err_base_{r.city}"], row[f"err_model_{r.city}"] = r.error_baseline, r.error_model
            rows.append(row)
            print(variant, "|", label, j.get("verdict"), j.get("fold_cities_better"), flush=True)
        full = T.random_intercept_fit(d[d["city"].isin(FOLD)])
        lo, hi = T.new_city_interval(full)
        rows.append({"variant": variant, "method": P2.LABELS["multilevel"], "verdict": "uncertainty only",
                     "detail": f"overall mean {full['mu']:+.3f} homes per acre per year per 1.0 FAR; new city {lo:+.3f} to {hi:+.3f}"})
        def wcorr(x, y):
            w = d.loc[x.index, "weight"]
            mx, my = np.average(x, weights=w), np.average(y, weights=w)
            return float(np.average((x - mx) * (y - my), weights=w) / math.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w)))
        rows.append({"variant": variant, "method": "weighted correlation: pressure before vs response (shown, not judged)",
                     "verdict": "context", "detail": f"all {wcorr(d.x_pressure, d.effect):+.3f}; up {wcorr(d[d.x_up == 1].x_pressure, d[d.x_up == 1].effect):+.3f}; down {wcorr(d[d.x_up == 0].x_pressure, d[d.x_up == 0].effect):+.3f}"})
    out = pd.DataFrame(rows)
    out.round(4).to_csv(MODELS, index=False)
    pd.set_option("display.width", 250)
    print(out[["variant", "method", "verdict", "fold_cities_better", "mean_error_baseline", "mean_error_model", "beats_baseline_chicago", "detail"]].round(3).to_string())


if __name__ == "__main__":
    main()

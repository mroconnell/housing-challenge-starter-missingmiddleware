"""Parking causal test E1: AB 2097 triple difference (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, section E1, locked).

    .venv/bin/python scripts/run_parking_causal_e1.py

Decisions the locked plan does not fix, written 2026-11-02 BEFORE any E1 permit was counted by zone or class
(only column formats and fill rates were looked at):

 D1 Jurisdictions: the 185 of TOD's AB 2097 test group P (full reporters 2018-2025, minus the 12 "already no
    minimums" places, minus San Jose and Sacramento), rebuilt with missing_middleware.tod.ab2097.define_groups from
    TOD's cached denominators and permit table (data/processed/ab2097/), and checked to be 185.
 D2 Zones: inside = under 1/2 mile of an existing major transit stop (TOD's stop filter: blank plan_name); outside =
    TOD's comparison ring, 1/2 to 1 1/2 miles, same jurisdiction. Land and permits inside Los Angeles's 2017 TOC tier
    areas are left out of both (they are TOD's T+P land, not group P). Land beyond 1 1/2 miles is not used.
 D3 Denominators: TOD's 2020-census existing homes per jurisdiction x zone (cells.parquet, spec "zone").
 D4 Geometry: missing_middleware.geom only (transform to EPSG:3310, nearest via KD-tree, point in polygon).
 D5 Permit records: TOD's cleaning rules reused (geocoded = coordinates plus an HCD standardized street address;
    exact duplicates on jurisdiction, address, report year, unit category and units dropped). Added because permits are
    re-dated by issue date: the same permit re-reported in a later report year (same jurisdiction, address, unit
    category, units and BP_ISSUE_DT1) is kept once. Sensitivity: TOD's rule only.
 D6 Permit year = year of BP_ISSUE_DT1, else YEAR. Records whose permit year falls outside 2018-2025 are dropped and
    counted. Homes = NO_BUILDING_PERMITS.
 D7 Size class from the record's UNIT_CAT: "2 to 4" = mid-sized, "5+" = large. Other categories are not used.
 D8 5+ without density bonus = 5+ records with DENSITY_BONUS_TOTAL == 0 (the field is filled on every record).
 D9 Pooling, main = homes-weighted: rate = summed homes permitted / summed existing homes in the zone (ratio of sums,
    as TOD's test). Equal-weight = mean over jurisdictions of each jurisdiction's own DiD (jurisdictions with existing
    homes in both zones).
 D10 Interval: 2,000 resamples of whole jurisdictions, seed 20261103, the same resamples for every class (so the
    triple difference is paired), 90% percentile interval. SE = SD of the draws. MDE = 1.645 x SE.
 D11 Pre-trend: same contrasts with before = 2018-2020 and after = 2021-2022; "balanced" if the 90% interval
    includes 0.
 D12 Leave-one-jurisdiction-out: homes-weighted point estimate with each jurisdiction left out; min, max and the
    jurisdiction whose removal moves the estimate most.
 D13 Data checks (counted on all statewide records with permits, 2018-2025 report years, and in the E1 sample):
    missing coordinates, coordinates outside California (lat 32.5-42.1, lon -124.5 to -114.1), more than 1,000 homes
    on one record, duplicates (D5). Records over 1,000 homes are kept in the main estimate; a sensitivity drops them.
 POST HOC (after the first results): a report-year dating case and its pre-trend; see main().
 D14 Lot size: no city parcel layer is used in E1 (the plan uses lot breaks only where a parcel layer is on disk;
    none is joined here).

Outputs (aggregates only; no addresses, APNs or ids): reference/parking_causal_e1_estimates.csv,
reference/parking_causal_e1_rates.csv, reference/parking_causal_e1_by_jurisdiction.csv,
reference/parking_causal_e1_data_checks.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import geom as G  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

CRS = 3310
SEED = 20261103
DRAWS = 2000
BEFORE, AFTER = [2018, 2019, 2020, 2021, 2022], [2023, 2024, 2025]
PRE_B, PRE_A = [2018, 2019, 2020], [2021, 2022]
YEARS = list(range(2018, 2026))
BIG = 1000
CA_LAT, CA_LON = (32.5, 42.1), (-124.5, -114.1)
COLS = ["JURIS_NAME", "YEAR", "UNIT_CAT", "NO_BUILDING_PERMITS", "BP_ISSUE_DT1", "DENSITY_BONUS_TOTAL",
        "LATITUDE", "LONGITUDE", "STD_ADDRESS", "STREET_ADDRESS"]
CLASSES = {"2to4": "units_2to4", "5plus": "units_5plus", "5plus_no_db": "units_5plus_nodb"}


# ------------------------------------------------------------------ inputs

def jurisdictions() -> tuple[list[str], pd.DataFrame]:
    cells = pd.read_parquet(PROCESSED / "ab2097" / "cells.parquet")
    cells = cells[cells.spec == "zone"].drop(columns="spec")
    tod_p = pd.read_parquet(PROCESSED / "ab2097" / "permits.parquet", columns=["juris", "year"])
    g = ab.define_groups(cells, ab.full_reporters(tod_p))["P"]
    assert len(g.juris) == 185, len(g.juris)
    return list(g.juris), cells


def load_permits() -> tuple[pd.DataFrame, list[dict]]:
    a = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=COLS, low_memory=False)
    a["units"] = pd.to_numeric(a["NO_BUILDING_PERMITS"], errors="coerce").fillna(0.0)
    a = a[(a.units > 0) & a.YEAR.isin(YEARS)].copy()
    lat, lon = pd.to_numeric(a.LATITUDE, errors="coerce"), pd.to_numeric(a.LONGITUDE, errors="coerce")
    checks = []

    def chk(name, mask, scope="statewide records with permits, report years 2018-2025"):
        checks.append({"check": name, "scope": scope, "records": int(mask.sum()), "homes": float(a.loc[mask, "units"].sum()),
                       "records_in_scope": int(len(a)), "homes_in_scope": float(a.units.sum())})
    miss = lat.isna() | lon.isna()
    chk("missing coordinates", miss)
    outside = ~miss & ~(lat.between(*CA_LAT) & lon.between(*CA_LON))
    chk("coordinates outside California box", outside)
    chk("more than 1,000 homes on one record", a.units > BIG)
    geo = ab.is_geocoded(lat, lon, a.STD_ADDRESS)
    chk("not geocoded to a street address (TOD rule; includes missing coordinates)", ~geo)
    bp = pd.to_datetime(a.BP_ISSUE_DT1, errors="coerce")
    chk("BP_ISSUE_DT1 missing or unreadable (report year used)", bp.isna())
    a["permit_year"] = bp.dt.year.fillna(a.YEAR).astype(int)
    chk("permit year differs from report year", a.permit_year != a.YEAR)
    a = a[geo].copy()
    a["addr"] = ab._norm(a.STREET_ADDRESS).where(ab._norm(a.STREET_ADDRESS) != "", ab._norm(a.STD_ADDRESS))
    a["juris"] = a.JURIS_NAME.astype(str).str.upper().str.strip()
    a["bp_date"] = bp.reindex(a.index).dt.strftime("%Y-%m-%d").fillna("")
    d1 = a.duplicated(["JURIS_NAME", "addr", "YEAR", "UNIT_CAT", "units"])
    a["dup_tod"] = d1
    # D5: re-reported in another report year (needs an issue date to match on)
    a["dup_cross_year"] = ~d1 & (a.bp_date != "") & a[~d1].duplicated(["JURIS_NAME", "addr", "UNIT_CAT", "units", "bp_date"]).reindex(a.index, fill_value=False)
    sc = "geocoded records"
    for name, m in (("exact duplicate (TOD rule)", a.dup_tod), ("same permit re-reported in a later report year (D5)", a.dup_cross_year)):
        checks.append({"check": name, "scope": sc, "records": int(m.sum()), "homes": float(a.loc[m, "units"].sum()),
                       "records_in_scope": int(len(a)), "homes_in_scope": float(a.units.sum())})
    out_yr = ~a.permit_year.isin(YEARS)
    checks.append({"check": "permit year outside 2018-2025 (dropped)", "scope": sc, "records": int(out_yr.sum()),
                   "homes": float(a.loc[out_yr, "units"].sum()), "records_in_scope": int(len(a)), "homes_in_scope": float(a.units.sum())})
    p = pd.DataFrame({"juris": a.juris.values, "year": a.permit_year.values, "report_year": a.YEAR.astype(int).values,
                      "in_window": ~out_yr.values, "unit_cat": a.UNIT_CAT.astype(str).values,
                      "units": a.units.values, "db": pd.to_numeric(a.DENSITY_BONUS_TOTAL, errors="coerce").fillna(0).values,
                      "dup_tod": a.dup_tod.values, "dup_cross_year": a.dup_cross_year.values,
                      "lat": pd.to_numeric(a.LATITUDE).values, "lon": pd.to_numeric(a.LONGITUDE).values})
    return p, checks


def place(p: pd.DataFrame) -> pd.DataFrame:
    """Zone (near / ring / beyond) and LA TOC flag for each record, with missing_middleware.geom only."""
    s = G.read_geojson(RAW / "ab2097" / "major_transit_stops.geojson", columns=["plan_name", "hqta_type"])
    s = s.subset(s.attrs["plan_name"].fillna("").str.strip().eq("").values).to_crs(CRS)
    print(f"existing major transit stops: {len(s):,}")
    x, y = G.transform(p.lon.values, p.lat.values, 4326, CRS)
    _, d = G.nearest(x, y, s.x, s.y)
    p = p.copy()
    p["zone"] = ab.zone_of(d)
    t = G.read_geojson(RAW / "ab2097" / "la_toc_tiers_2017.geojson").to_crs(CRS)
    parts = [[part] for f in t.polys for part in (f or [])]   # parts one by one, as TOD (exploded layer)
    la = np.flatnonzero((p.juris == ab.LA).values)
    upz = np.zeros(len(p), bool)
    upz[la] = G.points_in_any(x[la], y[la], parts)
    p["upz"] = upz
    return p.drop(columns=["lat", "lon"])


# ------------------------------------------------------------------ arithmetic

def matrices(p, cells, J, col, years):
    """units[zone] (J x years) and homes[zone] (J) for zone in near/ring, TOC land excluded."""
    ix = {j: i for i, j in enumerate(J)}
    yx = {y: k for k, y in enumerate(years)}
    out = {}
    for z in ("near", "ring"):
        c = cells[(cells.zone == z) & (~cells.upz) & cells.juris.isin(J)].groupby("juris").homes.sum()
        h = np.array([c.get(j, 0.0) for j in J])
        q = p[(p.zone == z) & (~p.upz) & p.juris.isin(J) & p.year.isin(years)]
        m = np.zeros((len(J), len(years)))
        for (j, yv), v in q.groupby(["juris", "year"])[col].sum().items():
            m[ix[j], yx[yv]] += v
        out[z] = (m, h)
    return out


def did_pooled(mats, w, nb):
    """Homes-weighted DiD for weight rows w (draws x J; counts of each jurisdiction)."""
    def ch(m, h):
        u = w @ m                      # draws x years
        hh = w @ h
        r = u / hh[:, None] * 1000.0
        return r[:, nb:].mean(1) - r[:, :nb].mean(1)
    return ch(*mats["near"]) - ch(*mats["ring"])


def did_by_juris(mats, nb):
    def ch(m, h):
        with np.errstate(invalid="ignore", divide="ignore"):
            r = m / h[:, None] * 1000.0
        return r[:, nb:].mean(1) - r[:, :nb].mean(1)
    return ch(*mats["near"]) - ch(*mats["ring"])


def rates(mats, nb):
    out = {}
    for z, (m, h) in mats.items():
        u = m.sum(0)
        out[f"{z}_rate_before"] = u[:nb].mean() / h.sum() * 1000
        out[f"{z}_rate_after"] = u[nb:].mean() / h.sum() * 1000
        out[f"{z}_homes_before"] = u[:nb].sum()
        out[f"{z}_homes_after"] = u[nb:].sum()
        out[f"{z}_existing_homes"] = h.sum()
    return out


def run_case(p, cells, J, before, after, case, W, Wloo):
    years = list(before) + list(after)
    nb = len(before)
    mats = {k: matrices(p, cells, J, col, years) for k, col in CLASSES.items()}
    ones = np.ones((1, len(J)))
    pt = {k: did_pooled(m, ones, nb)[0] for k, m in mats.items()}
    dr = {k: did_pooled(m, W, nb) for k, m in mats.items()}
    loo = {k: did_pooled(m, Wloo, nb) for k, m in mats.items()}
    jd = {k: did_by_juris(m, nb) for k, m in mats.items()}
    okj = (mats["2to4"]["near"][1] > 0) & (mats["2to4"]["ring"][1] > 0)
    combos = {"DiD 2-4": ("2to4", None), "DiD 5+": ("5plus", None), "DiD 5+ no density bonus": ("5plus_no_db", None),
              "Triple difference (2-4 minus 5+)": ("2to4", "5plus"),
              "Triple difference (2-4 minus 5+ no density bonus)": ("2to4", "5plus_no_db")}
    rows = []
    rng = np.random.default_rng(SEED)
    Wj = np.stack([np.bincount(rng.integers(0, okj.sum(), okj.sum()), minlength=okj.sum()) for _ in range(DRAWS)])
    for name, (a, b) in combos.items():
        est = pt[a] - (pt[b] if b else 0)
        d = dr[a] - (dr[b] if b else 0)
        lo_ = loo[a] - (loo[b] if b else 0)
        ej = jd[a][okj] - (jd[b][okj] if b else 0)
        eq_draws = (Wj @ ej) / okj.sum()
        k = int(np.nanargmax(np.abs(lo_ - est)))
        for wname, e, dd in (("homes-weighted (main)", est, d), ("equal-weight", float(ej.mean()), eq_draws)):
            lo, hi = np.nanquantile(dd, [0.05, 0.95])
            se = float(np.nanstd(dd, ddof=1))
            r = {"case": case, "estimand": name, "weighting": wname, "estimate": e, "interval90_low": lo,
                 "interval90_high": hi, "se": se, "mde_1645se": 1.645 * se,
                 "interval_includes_0": bool(lo <= 0 <= hi),
                 "n_jurisdictions": int(len(J) if wname.startswith("homes") else okj.sum())}
            if wname.startswith("homes"):
                r.update({"loo_min": float(np.nanmin(lo_)), "loo_max": float(np.nanmax(lo_)),
                          "loo_most_influential": J[k], "loo_estimate_without_it": float(lo_[k])})
                if b is None:
                    r.update(rates(mats[a], nb))
                    m = mats[a]["near"][0]
                    r["n_juris_near_permits_both_periods"] = int(((m[:, :nb].sum(1) > 0) & (m[:, nb:].sum(1) > 0)).sum())
            rows.append(r)
    byj = pd.DataFrame({"juris": J, "near_existing_homes": mats["2to4"]["near"][1], "ring_existing_homes": mats["2to4"]["ring"][1]})
    for k in CLASSES:
        byj[f"did_{k}"] = jd[k]
        for z in ("near", "ring"):
            m = mats[k][z][0]
            byj[f"{z}_{k}_homes_before"] = m[:, :nb].sum(1)
            byj[f"{z}_{k}_homes_after"] = m[:, nb:].sum(1)
    byj["case"] = case
    return rows, byj, mats


def main() -> None:
    J, cells = jurisdictions()
    p, checks = load_permits()
    p = place(p)
    p["units_2to4"] = np.where(p.unit_cat == "2 to 4", p.units, 0.0)
    p["units_5plus"] = np.where(p.unit_cat == "5+", p.units, 0.0)
    p["units_5plus_nodb"] = np.where((p.unit_cat == "5+") & (p.db == 0), p.units, 0.0)
    ins = p.juris.isin(J) & p.zone.isin(["near", "ring"]) & ~p.upz
    for name, m in (("more than 1,000 homes on one record", p.units > BIG), ("exact duplicate (TOD rule)", p.dup_tod),
                    ("same permit re-reported in a later report year (D5)", p.dup_cross_year)):
        s = ins & p.unit_cat.isin(["2 to 4", "5+"])
        checks.append({"check": name, "scope": "E1 sample: 185 jurisdictions, inside or ring, 2-4 and 5+ records",
                       "records": int((s & m).sum()), "homes": float(p.loc[s & m, "units"].sum()),
                       "records_in_scope": int(s.sum()), "homes_in_scope": float(p.loc[s, "units"].sum())})
    main_p = p[~p.dup_tod & ~p.dup_cross_year & p.in_window]
    # POST HOC (added 2026-11-02 after seeing the main results): permits re-dated by issue date are missing late
    # reports in the after years (homes permitted in 2018-2022 that first appear in a later report year: about a fifth;
    # 2024: 7%; 2025: ~0%). This case dates permits by report year (TOD's rule) with TOD's duplicate rule, so the
    # before and after years are filled alike.
    by_report = p[~p.dup_tod].assign(year=lambda d: d.report_year)
    rng = np.random.default_rng(SEED)
    W = np.stack([np.bincount(rng.integers(0, len(J), len(J)), minlength=len(J)) for _ in range(DRAWS)]).astype(float)
    Wloo = 1.0 - np.eye(len(J))
    rows, byjs = [], []
    cases = [("main", main_p, BEFORE, AFTER), ("pre-trend 2018-2020 vs 2021-2022", main_p, PRE_B, PRE_A),
             ("sensitivity: TOD duplicate rule only", p[~p.dup_tod & p.in_window], BEFORE, AFTER),
             ("POST HOC sensitivity: report-year dating, TOD duplicate rule", by_report, BEFORE, AFTER),
             ("POST HOC pre-trend, report-year dating", by_report, PRE_B, PRE_A),
             ("sensitivity: records over 1,000 homes dropped", main_p[main_p.units <= BIG], BEFORE, AFTER)]
    for case, pp, b, a in cases:
        r, byj, _ = run_case(pp, cells, J, b, a, case, W, Wloo)
        rows += r
        byjs.append(byj)
    res = pd.DataFrame(rows)
    num = res.select_dtypes("number").columns
    res[num] = res[num].round(4)
    res.to_csv(REFERENCE / "parking_causal_e1_estimates.csv", index=False)
    pd.concat(byjs).round(4).to_csv(REFERENCE / "parking_causal_e1_by_jurisdiction.csv", index=False)
    # rates by class, zone and year (main sample)
    rr = []
    mp = main_p[main_p.juris.isin(J) & ~main_p.upz]
    for z in ("near", "ring"):
        h = cells[(cells.zone == z) & (~cells.upz) & cells.juris.isin(J)].homes.sum()
        for k, col in CLASSES.items():
            for y in YEARS:
                q = mp[(mp.zone == z) & (mp.year == y) & (mp[col] > 0)]
                rr.append({"zone": "inside 1/2 mile" if z == "near" else "ring 1/2-1 1/2 mile", "class": k, "year": y,
                           "homes_permitted": float(q[col].sum()), "records": int(len(q)),
                           "jurisdictions_with_permits": int(q.juris.nunique()), "existing_homes_2020": float(h),
                           "per_1000_existing_homes": float(q[col].sum() / h * 1000)})
    pd.DataFrame(rr).round(4).to_csv(REFERENCE / "parking_causal_e1_rates.csv", index=False)
    pd.DataFrame(checks).to_csv(REFERENCE / "parking_causal_e1_data_checks.csv", index=False)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(checks).to_string())
    print(res.drop(columns=[c for c in res.columns if c.startswith(("near_", "ring_"))]).to_string())
    print(res[res.weighting.str.startswith("homes") & res.near_rate_before.notna()][
        ["case", "estimand"] + [c for c in res.columns if c.startswith(("near_", "ring_"))]].to_string())


if __name__ == "__main__":
    main()

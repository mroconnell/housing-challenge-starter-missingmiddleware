"""Run the pre-registered Madison TOD overlay test (docs/tod/MADISON_TEST_PREREG.md).

    uv run --all-extras python scripts/run_tod_madison_test.py --fetch   # first run: rezonings + 2016 city boundary
    uv run --all-extras python scripts/run_tod_madison_test.py           # offline afterwards

In:  data/raw/madison_permits/construction_summary_*.csv (Construction Summary; owner fields dropped at load)
     data/raw/madison_parcels/{tax_parcels,address_points}.geojson (address matching, as in the ADU pipeline)
     data/raw/madison_tod/tod_boundary.geojson, data/raw/tod_capacity/mad_zoning.geojson,
     reference/tod_zoning_rules_madison.csv (lots, eligibility and the overlay's added floor area, exactly as in
     scripts/build_tod_station_areas.py and the blind prediction in scripts/run_tod_model.py)
     data/raw/madison_rezonings/legistar_28022_matters.json (zoning map amendments, Legistar web API)
     data/raw/madison_rezonings/tl_2016_55_place.zip (City of Madison boundary on 1 January 2016)
     reference/tod_madison_test_predictions.csv (method A's committed prediction)
Out: reference/tod_madison_test_results.csv       estimate, interval, judgment, sensitivities, match rate
     reference/tod_madison_test_rates_by_year.csv  units, acres and rates by area and year, 2017-2026
     reference/tod_madison_test_unmatched.csv      unmatched permits with 10+ units: street name and year only
Privacy: no permit numbers, parcel ids, house numbers or names are written.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.permits import fetch_util as fu  # noqa: E402
from missing_middleware.permits import madison  # noqa: E402
from missing_middleware.permits.address import parse  # noqa: E402
from missing_middleware.permits.match import AddressIndex, match_addresses  # noqa: E402
from missing_middleware.tod import capacity as C  # noqa: E402
from missing_middleware.tod import cases as K  # noqa: E402
from missing_middleware.tod import madison_test as T  # noqa: E402

_spec = importlib.util.spec_from_file_location("build_tod_station_areas", ROOT / "scripts" / "build_tod_station_areas.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

CRS_M = B.CRS_M
RZ = RAW / "madison_rezonings"
LEGISTAR = "https://webapi.legistar.com/v1/madison/matters"
PLACE_2016 = "https://www2.census.gov/geo/tiger/TIGER2016/PLACE/tl_2016_55_place.zip"
MADISON_PLACEFP = "48000"
OUT_RES = REFERENCE / "tod_madison_test_results.csv"
OUT_RATES = REFERENCE / "tod_madison_test_rates_by_year.csv"
OUT_UNM = REFERENCE / "tod_madison_test_unmatched.csv"
YEARS = T.BEFORE + T.AFTER + T.SHOWN
LIT = {"overlay": K.TREAT, "ring_quarter_mile_outside": K.COMP, "rest_of_city": K.COMP2}


# ----------------------------------------------------------------------------- fetch

def fetch() -> None:
    RZ.mkdir(parents=True, exist_ok=True)
    log_path = RZ / "_downloads.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    out = RZ / "legistar_28022_matters.json"
    rows, skip = [], 0
    filt = "substringof('28.022',MatterTitle) and MatterIntroDate ge datetime'2015-01-01'"
    while True:
        b = fu.get(LEGISTAR, {"$filter": filt, "$top": 1000, "$skip": skip, "$orderby": "MatterId"}, timeout=180)
        page = json.loads(b)
        rows += page
        if len(page) < 1000:
            break
        skip += 1000
    keep = ["MatterId", "MatterFile", "MatterName", "MatterTitle", "MatterTypeName", "MatterStatusName",
            "MatterIntroDate", "MatterPassedDate", "MatterEnactmentDate", "MatterEnactmentNumber"]
    out.write_text(json.dumps([{k: r.get(k) for k in keep} for r in rows], indent=1))
    log[out.name] = {"url": LEGISTAR, "query": f"$filter={filt}", "accessed": fu.now_iso()[:10],
                     "records": len(rows), "bytes": out.stat().st_size, "sha256": fu.sha256_file(out),
                     "terms": "City of Madison Legistar public records (web API); fields kept: ids, titles, dates, status"}
    z = RZ / "tl_2016_55_place.zip"
    if not z.exists():
        z.write_bytes(fu.get(PLACE_2016, timeout=600))
    log[z.name] = {"url": PLACE_2016, "accessed": fu.now_iso()[:10], "bytes": z.stat().st_size,
                   "sha256": fu.sha256_file(z), "terms": "Public domain (U.S. Census Bureau TIGER/Line 2016)"}
    log_path.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n")
    print(f"fetched {len(rows)} Legistar matters and the 2016 place boundary")


# ----------------------------------------------------------------------------- lots

def lots():
    """Madison lots (identical outlines collapsed) with eligibility, area labels and the overlay's added FAR."""
    import geopandas as gpd

    rows = B.read_rules("madison")
    p = B.load_madison({r["district"] for r in rows})
    sq = C.MEASURED_SQFT_PER_HOME["Madison city"]
    base, ovl = C.rule_table(rows, False, sq), C.rule_table(rows, True, sq)
    elig, fb, fo, uncapped = [], [], [], []
    for r in p.itertuples(index=False):
        rb, ro = base.get(r.district), ovl.get(r.district)
        e = rb is not None and rb.rule_type != "not_coded" and C.is_eligible(rb.zoning_class, r.use_class, rb.rule_type) \
            and r.use_class != "single_family"
        elig.append(e)
        if rb is not None and rb.rule_type == "assumed_at_or_above_law":
            fb.append(np.inf); fo.append(np.inf)
        else:
            fb.append(rb.far if rb is not None and rb.far is not None else np.nan)
            fo.append(ro.far if ro is not None and ro.far is not None else np.nan)
        uncapped.append(rb is not None and rb.rule_type in {"far", "assumed_at_or_above_law"})
    p["elig"], p["far_base"], p["far_ovl"], p["uncapped"] = elig, fb, fo, uncapped
    p["acres"] = p.geometry.area / B.M2_PER_ACRE
    p["added_far"] = np.where(p.elig & np.isfinite(p.far_base) & np.isfinite(p.far_ovl),
                              (p.far_ovl - p.far_base).clip(lower=0), 0.0)
    p["rose"] = p.in_overlay & p.elig & (p.added_far > 0)
    p["lit_area"] = np.where(p.in_overlay, "overlay", np.where(p.dist_overlay_m <= C.QUARTER_M, "ring_quarter_mile_outside", "rest_of_city"))
    return gpd.GeoDataFrame(p, geometry="geometry", crs=CRS_M)


def ref_points(ref: pd.DataFrame):
    import geopandas as gpd

    return gpd.GeoDataFrame(ref, geometry=gpd.points_from_xy(ref.x, ref.y), crs=4326).to_crs(CRS_M)


def rezoned_lots(L, index: AddressIndex, ref_pts) -> tuple[pd.Series, dict]:
    """Lots in a zoning map amendment enacted 2017-2025, or outside the City on 1 January 2016 (zoning assigned)."""
    import geopandas as gpd

    matters = json.loads((RZ / "legistar_28022_matters.json").read_text())
    w = T.window_rezonings(matters)
    ref = index.ref
    hit_rows, n_parsed, n_placed, unparsed, near = set(), 0, 0, [], 0
    for r in w.itertuples(index=False):
        addrs = T.split_addresses(T.address_text(r.title, r.name))
        if not addrs:
            unparsed.append(r.name)
            continue
        n_parsed += 1
        found = set()
        for a in addrs:
            pa = parse(a, index.street_keys)
            rb = T.range_bounds(a)
            if rb and pa.street_key:
                m = ref[(ref.street_key == pa.street_key) & ref.house_nbr.between(*rb)]
                if rb[0] % 2 == rb[1] % 2:
                    m = m[m.house_nbr % 2 == rb[0] % 2]
                found |= set(m.index)
            res = index.match_one(a)
            cands = [res["parcel_id"]] if res["parcel_id"] else (res["candidate_parcels"] or "").split(";")
            cands = [c for c in cands if c]
            if cands:
                found |= set(ref.index[ref.parcel_id.isin(cands)])
            elif pa.street_key:
                # address retired by redevelopment or not yet in the layers: nearest number on the street
                for n in ([*rb] if rb else [pa.house_nbr]):
                    j = T.nearest_on_street(ref, pa.street_key, n) if n is not None else None
                    if j is not None:
                        found.add(j); near += 1
        if found:
            n_placed += 1
        hit_rows |= found
    pts = ref_pts.loc[sorted(hit_rows)]
    ix = K.locate_points(pts, L[["geometry"]])
    rez = pd.Series(False, index=L.index)
    rez.loc[ix.dropna().astype(int).unique()] = True
    pl = gpd.read_file(f"zip://{RZ / 'tl_2016_55_place.zip'}")
    city16 = pl[pl.PLACEFP == MADISON_PLACEFP].to_crs(CRS_M).geometry.union_all()
    annexed = ~L["pt"].within(city16)
    info = {"rezonings_2017_2025": len(w), "rezonings_with_addresses": n_parsed, "rezonings_placed_on_lots": n_placed,
            "rezonings_without_addresses": len(unparsed), "rezoning_addresses_placed_by_nearest_number": near, "lots_rezoned": int(rez.sum()),
            "eligible_acres_rezoned": round(float(L.acres[rez & L.elig].sum()), 1),
            "lots_outside_city_2016": int(annexed.sum()),
            "eligible_acres_outside_city_2016": round(float(L.acres[annexed & L.elig & ~rez].sum()), 1),
            "unparsed_names": "; ".join(unparsed)}
    return rez | annexed, info


# ----------------------------------------------------------------------------- permits

def permits_on_lots(L, index: AddressIndex, ref_pts, parcels_tbl):
    import geopandas as gpd

    raw = madison.load_raw_permits(RAW / "madison_permits")
    d = T.test_permits(raw)
    m = match_addresses(d, index)
    d = d.join(m)
    pxy = parcels_tbl.set_index("parcel_id")[["x", "y"]]
    xs, ys = [], []
    for r in d.itertuples(index=False):
        x = y = np.nan
        if r.parcel_id and r.parcel_id in pxy.index:
            x, y = pxy.loc[r.parcel_id, ["x", "y"]]
        elif r.match_method == "geocode" and r.geo_x is not None:
            x, y = r.geo_x, r.geo_y
        xs.append(x); ys.append(y)
    d["x"], d["y"] = xs, ys
    pts = gpd.GeoDataFrame(d[["x"]], geometry=gpd.points_from_xy(d.x, d.y), crs=4326).to_crs(CRS_M)
    has = d.x.notna()
    d["lot"] = np.nan
    d.loc[has, "lot"] = K.locate_points(pts[has], L[["geometry"]]).values
    # ambiguous: placed when every candidate parcel lies on the same lot
    amb = d.lot.isna() & d.candidate_parcels.notna()
    for i in d.index[amb]:
        c = [x for x in str(d.at[i, "candidate_parcels"]).split(";") if x in pxy.index]
        if not c:
            continue
        cp = gpd.GeoDataFrame(geometry=gpd.points_from_xy(pxy.loc[c, "x"], pxy.loc[c, "y"]), crs=4326).to_crs(CRS_M)
        lots_c = K.locate_points(cp, L[["geometry"]]).dropna().unique()
        if len(lots_c) == 1:
            d.at[i, "lot"] = lots_c[0]
            d.at[i, "match_method"] = "ambiguous_same_lot"
    key = [f"{int(h)}|{s}" if pd.notna(h) and s else str(a).upper() for h, s, a in
           zip(d.addr_house_nbr, d.addr_street_key, d.address_raw)]
    d["project"] = T.project_ids(pd.Series(key, index=d.index), d.year)
    d["placed"] = d.lot.notna()
    return d


def area_table(d: pd.DataFrame, L, col: str) -> pd.DataFrame:
    """Permits (project, area, year, units) on eligible lots with an area label."""
    x = d[d.placed].copy()
    lot = x.lot.astype(int)
    x["area"] = L[col].reindex(lot).values
    x["elig"] = L.elig.reindex(lot).values
    x = x[x.elig.astype(bool) & x.area.notna()]
    return x[["project", "area", "year", "units"]].reset_index(drop=True)


# ----------------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args(argv)
    if args.fetch or not (RZ / "legistar_28022_matters.json").exists():
        fetch()
    pred = pd.read_csv(REFERENCE / "tod_madison_test_predictions.csv")
    main_pred = pred[(pred.method == "A") & pred.variant.str.startswith("main")].iloc[0]
    assert abs(main_pred.prediction - T.PRED) < 1e-9 and abs(main_pred.dose_added_far - T.DOSE_OVERLAY) < 1e-9

    print("lots ...", flush=True)
    L = lots()
    # check: the prereg's land layer is reproduced
    land = pd.read_csv(REFERENCE / "tod_madison_test_land.csv").set_index("area")
    for a in land.index:
        got = L.acres[(L.lit_area == a) & L.elig].sum()
        assert abs(got - land.loc[a, "eligible_acres"]) < 0.01, (a, got)

    parcels_tbl = madison.parcel_table(madison.load_parcels(RAW / "madison_parcels"))
    ref = madison.address_reference(parcels_tbl, madison.load_address_points(RAW / "madison_parcels"))
    index = AddressIndex(ref)
    ref_pts = ref_points(index.ref)

    print("rezonings ...", flush=True)
    changed, rinfo = rezoned_lots(L, index, ref_pts)
    L["changed"] = changed

    # uniform area rule (CASE_ANALYSIS_PLAN.md section 7)
    area, uinfo = K.uniform_areas(L, in_reform=L.in_overlay, rose=L.rose, level_before=L.far_base,
                                  level_after=L.far_ovl, uncapped_before=L.uncapped, changed_outside=L.changed,
                                  eligible=L.elig)
    med = uinfo["median_new_level_on_rising_land"]
    at_law = L.uncapped & (L.far_base.fillna(-1) >= med)
    excluded = (L.in_overlay & (area != K.TREAT)) | at_law | L.changed
    area = area.where(~excluded, None)
    # second comparison (prereg section 2): all other eligible Madison lots, not excluded
    area[area.isna() & ~excluded & L.elig] = K.COMP2
    L["zone"] = area
    L["lit"] = L.lit_area.map(LIT)

    acres = {a: float(L.acres[(L.zone == a) & L.elig].sum()) for a in K.AREAS}
    homes = {a: float(L.homes[(L.zone == a) & L.elig].sum()) for a in K.AREAS}
    lit_acres = {a: float(L.acres[(L.lit == a) & L.elig].sum()) for a in K.AREAS}
    lit_homes = {a: float(L.homes[(L.lit == a) & L.elig].sum()) for a in K.AREAS}
    t = L[(L.zone == K.TREAT) & L.elig]
    dose_treat = float((t.added_far * t.acres).sum() / t.acres.sum())
    tl = L[(L.lit == K.TREAT) & L.elig]
    dose_lit = float((tl.added_far * tl.acres).sum() / tl.acres.sum())
    print({k: round(v, 1) for k, v in acres.items()}, "dose on treated land", round(dose_treat, 4), "literal dose", round(dose_lit, 4))

    print("permits ...", flush=True)
    d = permits_on_lots(L, index, ref_pts, parcels_tbl)
    win = d[d.year.isin(YEARS)]
    est_yrs = d[d.year.isin(T.BEFORE + T.AFTER)]
    match = {"permits": len(est_yrs), "permits_placed": int(est_yrs.placed.sum()),
             "units": float(est_yrs.units.sum()), "units_placed": float(est_yrs.units[est_yrs.placed].sum())}
    unm = win[~win.placed & (win.units >= T.LARGE_UNITS)]
    pd.DataFrame({"street": [T.street_only(a) for a in unm.address_raw], "year": unm.year.astype(int),
                  "units": unm.units.astype(int), "permit_type": unm.permit_type,
                  "match_result": unm.match_rule}).sort_values(["year", "street"]).to_csv(OUT_UNM, index=False, lineterminator="\n")

    P = area_table(d, L, "zone")
    PL = area_table(d, L, "lit")

    # ---- estimates
    m = T.estimate(P, acres)
    lit = T.estimate(PL, lit_acres)
    s2 = T.estimate(P, acres, comp=K.COMP2)
    drop = T.estimate(K.drop_largest_project(P, T.BEFORE, T.AFTER), acres, interval=False)
    ra = T.estimate(P, acres, after=T.AFTER_ROUTE_A)
    ph = T.estimate(P, homes, scale=1000.0)
    lit_s2 = T.estimate(PL, lit_acres, comp=K.COMP2)
    yr = {y: T.estimate(P, acres, after=[y], interval=False)["did"] for y in T.AFTER + T.SHOWN}

    # judged quantity: per eligible overlay acre at the overlay dose (spec section 4: r x dose 0.374)
    scale = T.DOSE_OVERLAY / dose_treat
    judged = {k: m[k] * scale for k in ("did", "low", "high")}  # rates before/after not rescaled
    verdict = T.judge(T.PRED, judged["low"], judged["high"])
    verdict_lit = T.judge(T.PRED, lit["low"], lit["high"])

    def row(name, e, unit, denom_note, dose=None, note=""):
        out = {"estimate": name, "value": round(e["did"], 4), "interval90_low": round(e["low"], 4) if np.isfinite(e["low"]) else None,
               "interval90_high": round(e["high"], 4) if np.isfinite(e["high"]) else None, "unit": unit,
               **{f"{k.replace('treat_', 'treat_rate_').replace('comp_', 'comp_rate_')}": (round(e[k], 4) if k in e else None)
                  for k in ("treat_before", "treat_after", "comp_before", "comp_after")},
               "denominators": denom_note, "dose_added_far": round(dose, 4) if dose else None,
               "per_added_far": round(e["did"] / dose, 4) if dose else None,
               "per_added_far_low": round(e["low"] / dose, 4) if dose and np.isfinite(e["low"]) else None,
               "per_added_far_high": round(e["high"] / dose, 4) if dose and np.isfinite(e["high"]) else None, "note": note}
        return out

    U = "homes permitted per eligible acre per year (difference-in-differences of mean yearly rates)"
    dn = f"treatment {acres[K.TREAT]:.1f} ac; comparison {acres[K.COMP]:.1f} ac; second comparison {acres[K.COMP2]:.1f} ac"
    dl = f"overlay {lit_acres[K.TREAT]:.1f} ac; ring {lit_acres[K.COMP]:.1f} ac; rest of city {lit_acres[K.COMP2]:.1f} ac"
    rows = [
        row("main: uniform area rule, treatment minus comparison, before 2017-2022, after 2023-2025", m, U, dn, dose_treat,
            "Treatment = eligible overlay lots whose allowed FAR rose; comparison = eligible lots within 1/4 mile of treated land with no zoning change 2017-2025"),
        {**row("judged: main estimate per eligible overlay acre at the overlay dose", judged, "extra homes permitted per eligible acre per year (overlay basis)",
               f"main x overlay dose {T.DOSE_OVERLAY} / treated-land dose {dose_treat:.4f}", T.DOSE_OVERLAY,
               f"Method A predicted {T.PRED} (90% {T.PRED_LOW} to {T.PRED_HIGH}). Verdict: {verdict}"),
         },
        row("sensitivity: prereg areas as written (all eligible overlay land vs 1/4-mile ring of the overlay edge, no rezoning drop)", lit, U, dl, dose_lit,
            f"Judged directly against {T.PRED}: {verdict_lit}"),
        row("sensitivity: second comparison area (all other eligible Madison lots)", s2, U, dn, dose_treat),
        row("sensitivity: prereg areas as written, second comparison (rest of city)", lit_s2, U, dl, dose_lit),
        row("sensitivity: largest project left out in each area and period", drop, U, dn, dose_treat),
        row("sensitivity: after = 2024-2025 only (Rapid Route A opened 2024-09-22)", ra, U, dn, dose_treat),
        row("sensitivity: per 1,000 existing homes instead of per acre", ph, "homes permitted per 1,000 existing homes per year (difference-in-differences)",
            f"treatment {homes[K.TREAT]:.0f} homes; comparison {homes[K.COMP]:.0f} homes", None),
    ]
    for y, v in yr.items():
        rows.append({"estimate": f"ramp check: after = {y} only" + (" (partial year, shown only)" if y in T.SHOWN else ""),
                     "value": round(v, 4), "unit": U, "dose_added_far": round(dose_treat, 4),
                     "per_added_far": round(v / dose_treat, 4), "denominators": dn})
    info = {**rinfo, **{f"uniform_{k}": v for k, v in uinfo.items()},
            "match_rate_permits": round(match["permits_placed"] / match["permits"], 4),
            "match_rate_units": round(match["units_placed"] / match["units"], 4),
            "permits_2017_2025": match["permits"], "permits_placed": match["permits_placed"],
            "units_2017_2025": match["units"], "units_placed": match["units_placed"],
            "unmatched_10plus_permits_2017_2026": len(unm), "unmatched_10plus_units_2017_2026": float(unm.units.sum()),
            "units_on_treatment_2017_2025": float(P[(P.area == K.TREAT) & P.year.isin(T.BEFORE + T.AFTER)].units.sum()),
            "units_on_comparison_2017_2025": float(P[(P.area == K.COMP) & P.year.isin(T.BEFORE + T.AFTER)].units.sum()),
            "dose_treated_land": round(dose_treat, 4), "dose_overlay_literal": round(dose_lit, 4),
            "r_measured": round(m["did"] / dose_treat, 4), "r_measured_low": round(m["low"] / dose_treat, 4),
            "r_measured_high": round(m["high"] / dose_treat, 4), "r_method_a": T.R_TYPICAL,
            "overlay_effective": T.OVERLAY_EFFECTIVE, "draws": K.N_DRAWS, "seed": K.SEED}
    for k, v in info.items():
        rows.append({"estimate": f"info: {k}", "value": v if isinstance(v, (int, float)) else None, "note": "" if isinstance(v, (int, float)) else str(v)})
    res = pd.DataFrame(rows)
    res.to_csv(OUT_RES, index=False, lineterminator="\n")

    rt = []
    for name, PP, den, hom in (("uniform rule", P, acres, homes), ("prereg as written", PL, lit_acres, lit_homes)):
        r = K.rates_by_year(PP, den, YEARS)
        r.insert(0, "areas", name)
        r["period"] = r.year.map(lambda y: "before" if y in T.BEFORE else ("after" if y in T.AFTER else "shown only (partial)"))
        r["projects"] = [PP[(PP.area == a) & (PP.year == y)].project.nunique() for a, y in zip(r.area, r.year)]
        r["existing_homes"] = r.area.map(hom)
        r["rate_per_1000_homes"] = r.units / r.existing_homes * 1000
        rt.append(r.rename(columns={"denominator": "eligible_acres", "rate": "rate_per_acre"}))
    rt = pd.concat(rt, ignore_index=True)
    rt.round(4).to_csv(OUT_RATES, index=False, lineterminator="\n")

    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 120)
    print(res[["estimate", "value", "interval90_low", "interval90_high", "per_added_far", "per_added_far_low", "per_added_far_high"]].to_string())
    print(rt[rt.areas == "uniform rule"].pivot(index="year", columns="area", values=["units", "rate_per_acre"]).round(3).to_string())
    print(pd.read_csv(OUT_UNM).to_string())
    print("verdict:", verdict, "| as written:", verdict_lit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

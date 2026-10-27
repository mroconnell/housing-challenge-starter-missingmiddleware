"""Run the California AB 2097 test (docs/tod/AB2097_TEST_PREREG.md, with its section 8 changes).

    uv run --all-extras python scripts/run_ab2097_test.py [--rebuild]

Inputs (fetch first with scripts/fetch_ab2097_inputs.py):
  data/raw/hcd_apr_a2/tablea2.csv, data/raw/ab2097/{major_transit_stops.geojson, la_toc_tiers_2017.geojson,
  tl_2020_06_tabblock20.zip}, data/raw/census_tiger_2024_ca_place/tl_2024_06_place.zip,
  reference/ca_jurisdiction_crosswalk.csv.
Intermediate (git-ignored): data/processed/ab2097/{cells.parquet, permits.parquet, meta.json}. The permit table there
  holds hashed project ids, coordinates and units only.
Outputs: reference/tod_ab2097_results.csv, reference/tod_ab2097_rates_by_year.csv, and a summary printed for
  docs/tod/AB2097_TEST_RESULTS.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

D = RAW / "ab2097"
OUT = PROCESSED / "ab2097"
CRS = 3310  # California Albers, metres
A2_COLS = ["JURIS_NAME", "YEAR", "UNIT_CAT", "NO_BUILDING_PERMITS", "LATITUDE", "LONGITUDE", "STD_ADDRESS", "STREET_ADDRESS"]


# --------------------------------------------------------------------------- geography

def load_stops(kind: str = "all"):
    import geopandas as gpd
    s = gpd.read_file(D / "major_transit_stops.geojson")
    s = s[s["plan_name"].fillna("").str.strip() == ""]  # existing stops only (section 8 item 6)
    if kind == "rail_brt_ferry":
        s = s[s["hqta_type"].isin(["major_stop_rail", "major_stop_brt", "major_stop_ferry"])]
    return s.to_crs(CRS)


def nearest_m(points, stops) -> np.ndarray:
    from shapely import STRtree
    tree = STRtree(stops.geometry.values)
    idx, dist = tree.query_nearest(points.geometry.values, return_distance=True, all_matches=False)
    out = np.full(len(points), np.inf)
    out[idx[0]] = dist
    return out


def in_toc(points) -> np.ndarray:
    import geopandas as gpd
    t = gpd.read_file(D / "la_toc_tiers_2017.geojson").to_crs(CRS).explode(index_parts=False)
    t = t[["geometry"]].reset_index(drop=True)
    xmin, ymin, xmax, ymax = t.total_bounds
    b = points.geometry
    cand = points[(b.x >= xmin) & (b.x <= xmax) & (b.y >= ymin) & (b.y <= ymax)]
    j = gpd.sjoin(cand[["geometry"]], t, how="inner", predicate="within")
    flag = np.zeros(len(points), dtype=bool)
    flag[points.index.get_indexer(j.index.unique())] = True
    return flag


def block_juris(blocks) -> pd.Series:
    import geopandas as gpd
    pl = gpd.read_file(RAW / "census_tiger_2024_ca_place" / "tl_2024_06_place.zip").to_crs(CRS)[["PLACEFP", "geometry"]]
    j = gpd.sjoin(blocks[["geometry"]], pl, how="left", predicate="within")
    j = j[~j.index.duplicated()]
    cw = pd.read_csv(REFERENCE / "ca_jurisdiction_crosswalk.csv", dtype=str)
    city = cw[cw.juris_type != "county_unincorporated"].dropna(subset=["placefp"]).drop_duplicates("placefp").set_index("placefp")["juris_name"]
    cnty = cw[cw.juris_type == "county_unincorporated"].set_index("county_fips")["juris_name"]
    jur = j["PLACEFP"].map(city)
    jur = jur.fillna(blocks["COUNTYFP20"].map(cnty))
    return jur.reindex(blocks.index)


def build(rebuild: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    import geopandas as gpd
    import pyogrio
    OUT.mkdir(parents=True, exist_ok=True)
    if not rebuild and (OUT / "cells.parquet").exists() and (OUT / "permits.parquet").exists():
        return pd.read_parquet(OUT / "cells.parquet"), pd.read_parquet(OUT / "permits.parquet"), json.loads((OUT / "meta.json").read_text())
    stops = load_stops("all")
    stops_rbf = load_stops("rail_brt_ferry")
    print(f"stops: {len(stops):,} existing major transit stops ({len(stops_rbf):,} rail, BRT or ferry)")

    # blocks
    b = pyogrio.read_dataframe(D / "tl_2020_06_tabblock20.zip", read_geometry=False,
                               columns=["GEOID20", "COUNTYFP20", "ALAND20", "HOUSING20", "INTPTLAT20", "INTPTLON20"])
    b = gpd.GeoDataFrame(b, geometry=gpd.points_from_xy(b.INTPTLON20.astype(float), b.INTPTLAT20.astype(float)), crs=4326).to_crs(CRS)
    b["juris"] = block_juris(b)
    b["dist"] = nearest_m(b, stops)
    b["dist_rbf"] = nearest_m(b, stops_rbf)
    b["upz"] = in_toc(b) & (b["juris"] == ab.LA)
    b["homes"] = b["HOUSING20"].astype(float)
    b["acres"] = b["ALAND20"].astype(float) / 4046.8564224
    print(f"blocks: {len(b):,}; homes {b.homes.sum():,.0f}; no jurisdiction {b.juris.isna().sum():,}")

    # permits
    a2 = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=A2_COLS, low_memory=False)
    p, info = ab.clean_permits(a2)
    del a2
    missing = sorted(set(p.juris) - set(b.juris.dropna()))
    info["permit_jurisdictions_without_blocks"] = missing
    print(f"permit jurisdictions with no matching blocks: {missing}")
    pg = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.lon, p.lat), crs=4326).to_crs(CRS)
    p["dist"] = nearest_m(pg, stops)
    p["dist_rbf"] = nearest_m(pg, stops_rbf)
    p["upz"] = in_toc(pg) & (p["juris"] == ab.LA)

    def zones(df):
        return {"zone": ab.zone_of(df["dist"]),
                "zone_q": ab.zone_of(df["dist"], near_m=ab.QUARTER_M),
                "zone_rbf": ab.zone_of(df["dist_rbf"])}
    for k, v in zones(p).items():
        p[k] = v
    for k, v in zones(b).items():
        b[k] = v
    keys = ["juris", "upz"]
    cells = {}
    for zc in ("zone", "zone_q", "zone_rbf"):
        cells[zc] = b.dropna(subset=["juris"]).groupby(keys + [zc])[["homes", "acres"]].sum().reset_index().rename(columns={zc: "zone"})
        cells[zc]["spec"] = zc
    cells = pd.concat(cells.values(), ignore_index=True)
    p = p.drop(columns=["lat", "lon"])
    cells.to_parquet(OUT / "cells.parquet")
    p.to_parquet(OUT / "permits.parquet")
    meta = {"permit_cleaning": info, "stops_existing": int(len(stops)), "stops_rail_brt_ferry": int(len(stops_rbf)),
            "blocks": int(len(b)), "homes_2020": float(b.homes.sum()),
            "toc_blocks_homes": float(b.loc[b.upz, "homes"].sum())}
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
    return cells, p, meta


# --------------------------------------------------------------------------- estimates

def spec_tables(cells, permits, spec: str):
    c = cells[cells.spec == spec].drop(columns="spec")
    p = permits.copy()
    p["zone"] = p[spec]
    return c, p


def run(cells, permits, meta) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    reporters = ab.full_reporters(permits)
    allu = permits.groupby("year")["all_units"].sum()
    kept = permits[permits.juris.isin(reporters)].groupby("year")["all_units"].sum()
    clean = meta["permit_cleaning"]
    share = {"geocoded_units_kept_by_full_reporters": float(kept.sum() / allu.sum()),
             "statewide_units_with_permits": clean["units_with_permits"],
             "units_kept": float(kept.sum()),
             "share_of_all_statewide_units_kept": float(kept.sum() / clean["units_with_permits"]),
             "full_reporting_jurisdictions": len(reporters),
             "jurisdictions_filing_any_year": int(permits.juris.nunique()),
             "kept_share_by_year": {int(y): float(kept.get(y, 0) / allu[y]) for y in allu.index}}

    c0, p0 = spec_tables(cells, permits, "zone")
    rows = []

    def add(case, gname, g, oc, ms, r, method, cc=None):
        rows.append({"case": case, "group": gname, "outcome": oc, "measure": ms,
                     "estimate": r["estimate"], "interval90_low": r["low"], "interval90_high": r["high"],
                     "interval_method": method,
                     "near_rate_before": r.get("treat_rate_before"), "near_rate_after": r.get("treat_rate_after"),
                     "comparison_rate_before": r.get("comp_rate_before"), "comparison_rate_after": r.get("comp_rate_after"),
                     "near_units_before": r.get("treat_units_before"), "near_units_after": r.get("treat_units_after"),
                     "comparison_units_before": r.get("comp_units_before"), "comparison_units_after": r.get("comp_units_after"),
                     "near_denominator": r.get("treat_denominator"), "comparison_denominator": r.get("comp_denominator"),
                     "n_jurisdictions": len(g.juris) if g else None,
                     "n_jurisdictions_near_permits_both_periods": r.get("n_juris_permits_both_periods"),
                     "status": cc})

    def main_block(case, c, p, groups, before=ab.BEFORE, after=ab.AFTER, project_too=False, comb=True):
        out = {}
        for oc in ab.OUTCOMES:
            for ms in ab.MEASURES:
                res = {}
                for gname, g in groups.items():
                    r = ab.estimate(g, c, p, oc, ms, before, after, keep_draws=True)
                    method = r["interval"]
                    if len(g.juris) < 2:   # section 8 item 15
                        lo, hi, dr = ab.project_interval(g, c, p, oc, ms, before, after)
                        r.update(low=lo, high=hi, draws=dr)
                        method = "projects (one jurisdiction)"
                    res[gname] = r
                    st = ab.usable(r["n_juris_permits_both_periods"]) if gname == "P" else (
                        "one jurisdiction" if len(g.juris) == 1 else ab.usable(r["n_juris_permits_both_periods"]))
                    add(case, gname, g, oc, ms, r, method, st)
                    if project_too:
                        lo, hi, _ = ab.project_interval(g, c, p, oc, ms, before, after)
                        add("project_resampling", gname, g, oc, ms, dict(r, low=lo, high=hi), "projects", st)
                if comb and "P" in res and "T+P" in res:
                    d = res["T+P"]["draws"] - res["P"]["draws"]
                    lo, hi = ab.interval_of(d)
                    est = res["T+P"]["estimate"] - res["P"]["estimate"]
                    add(case, "T+P minus P", None, oc, ms, {"estimate": est, "low": lo, "high": hi},
                        "T+P draw minus P draw, independent" if len(groups["T+P"].juris) < 2 else "jurisdictions")
                    if project_too:
                        _, _, dp = ab.project_interval(groups["P"], c, p, oc, ms, before, after)
                        _, _, dt = ab.project_interval(groups["T+P"], c, p, oc, ms, before, after)
                        lo, hi = ab.interval_of(dt - dp)
                        add("project_resampling", "T+P minus P", None, oc, ms, {"estimate": est, "low": lo, "high": hi}, "projects")
                out[(oc, ms)] = res
        return out

    groups = ab.define_groups(c0, reporters)
    main = main_block("main", c0, p0, groups, project_too=True)
    # each after year on its own (prereg section 4)
    for y in ab.AFTER:
        main_block(f"after_{y}_only", c0, p0, groups, after=[y])
    # sensitivities (prereg section 5 and section 8)
    main_block("drop_2023", c0, p0, groups, after=[2024, 2025])
    main_block("include_san_jose_sacramento", c0, p0, ab.define_groups(c0, reporters, include_repealed=True))
    main_block("los_angeles_only", c0, p0, ab.define_groups(c0, reporters, only=[ab.LA]))
    cq, pq = spec_tables(cells, permits, "zone_q")
    main_block("quarter_mile", cq, pq, ab.define_groups(cq, reporters))
    cr, pr = spec_tables(cells, permits, "zone_rbf")
    main_block("rail_brt_ferry_stops_only (added check)", cr, pr, ab.define_groups(cr, reporters))
    # leaving out the largest project in each group, area and period
    for oc in ab.OUTCOMES:
        for ms in ab.MEASURES:
            res = {}
            for gname, g in groups.items():
                pd_ = ab.drop_largest(g, p0, oc)
                r = ab.estimate(g, c0, pd_, oc, ms, keep_draws=True)
                method = r["interval"]
                if len(g.juris) < 2:
                    lo, hi, dr = ab.project_interval(g, c0, pd_, oc, ms)
                    r.update(low=lo, high=hi, draws=dr)
                    method = "projects (one jurisdiction)"
                res[gname] = r
                add("drop_largest_project", gname, g, oc, ms, r, method)
            lo, hi = ab.interval_of(res["T+P"]["draws"] - res["P"]["draws"])
            add("drop_largest_project", "T+P minus P", None, oc, ms,
                {"estimate": res["T+P"]["estimate"] - res["P"]["estimate"], "low": lo, "high": hi}, "T+P draw minus P draw")
    # displacement check: ring against beyond (section 8 item 4 / 17)
    for gname, g in groups.items():
        for oc in ab.OUTCOMES:
            for ms in ab.MEASURES:
                r = ab.estimate(g, c0, p0, oc, ms, treat=("ring", False), comp=("beyond", False))
                method = r["interval"]
                if len(g.juris) < 2:
                    lo, hi, _ = ab.project_interval(g, c0, p0, oc, ms, treat=("ring", False), comp=("beyond", False))
                    r.update(low=lo, high=hi)
                    method = "projects (one jurisdiction)"
                add("displacement_ring_vs_beyond", gname, g, oc, ms, r, method)
    res = pd.DataFrame(rows)
    rates = ab.rates_by_year(groups, c0, p0)
    # group sizes
    sizes = {}
    for gname, g in groups.items():
        t = p0[p0.juris.isin(g.juris) & (p0.zone == g.treat[0]) & (p0.upz == g.treat[1]) & (p0.all_units > 0)]
        cmp_ = p0[p0.juris.isin(g.juris) & (p0.zone == "ring") & (~p0.upz) & (p0.all_units > 0)]
        sizes[gname] = {"jurisdictions": len(g.juris),
                        "near_projects_before": int(t[t.year.isin(ab.BEFORE)].project.nunique()),
                        "near_projects_after": int(t[t.year.isin(ab.AFTER)].project.nunique()),
                        "ring_projects_before": int(cmp_[cmp_.year.isin(ab.BEFORE)].project.nunique()),
                        "ring_projects_after": int(cmp_[cmp_.year.isin(ab.AFTER)].project.nunique()),
                        "near_2plus_projects_before": int(t[t.year.isin(ab.BEFORE) & (t.units_2plus > 0)].project.nunique()),
                        "near_2plus_projects_after": int(t[t.year.isin(ab.AFTER) & (t.units_2plus > 0)].project.nunique()),
                        "jurisdictions_with_near_permits_both_periods": int(len(set(t[t.year.isin(ab.BEFORE)].juris) & set(t[t.year.isin(ab.AFTER)].juris))),
                        "near_homes_2020": float(c0[c0.juris.isin(g.juris) & (c0.zone == g.treat[0]) & (c0.upz == g.treat[1])].homes.sum()),
                        "ring_homes_2020": float(c0[c0.juris.isin(g.juris) & (c0.zone == "ring") & (~c0.upz)].homes.sum()),
                        "beyond_homes_2020": float(c0[c0.juris.isin(g.juris) & (c0.zone == "beyond") & (~c0.upz)].homes.sum()),
                        "juris_list": g.juris if len(g.juris) <= 300 else []}
    summary = {"reporting": share, "sizes": sizes, "meta": meta,
               "already_in_reporters": sorted(set(ab.ALREADY_NO_MINIMUMS) & set(reporters)),
               "already_not_full_reporters": sorted(set(ab.ALREADY_NO_MINIMUMS) - set(reporters))}
    return res, rates, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    cells, permits, meta = build(a.rebuild)
    res, rates, summary = run(cells, permits, meta)
    num = res.select_dtypes("number").columns
    res[num] = res[num].round(5)
    res.to_csv(REFERENCE / "tod_ab2097_results.csv", index=False)
    rn = rates.select_dtypes("number").columns
    rates[rn] = rates[rn].round(5)
    rates.to_csv(REFERENCE / "tod_ab2097_rates_by_year.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k != "meta"}, indent=1, default=str)[:6000])
    show = res[(res.measure == "per_1000_homes")]
    print(show[["case", "group", "outcome", "estimate", "interval90_low", "interval90_high", "interval_method", "status"]].to_string())


if __name__ == "__main__":
    main()

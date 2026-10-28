"""More TOD reforms measured with census block counts (2010 to 2020), a holdout check, and a census-vs-permit method check.

    uv run --all-extras python scripts/fetch_tod_census_cases.py
    uv run --all-extras python scripts/run_tod_census_cases.py

Plan: docs/tod/CENSUS_CASES_PLAN.md (written before looking). Results: docs/tod/CENSUS_CASES_RESULTS.md.
Writes reference/tod_census_cases.csv, reference/tod_census_holdouts.csv, reference/tod_census_method_check.csv.
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402

D = RAW / "tod_census_cases"
CACHE = PROCESSED / "tod_census_cases"
CRS = 5070                       # USA Albers, metres
HALF, QUARTER, ACRE = 804.672, 402.336, 4046.8564
SEED, DRAWS = 20261030, 2000

NEW_CASES = {  # case: (state, role, label, adopted)
    "jersey_city_journal_square_2010": ("34", "holdout", "Jersey City, Journal Square 2060", "2010"),
    "milpitas_tasp_2008": ("06", "holdout", "Milpitas, Transit Area Specific Plan", "2008"),
    "phoenix_wu_2015_2016": ("04", "fitted", "Phoenix, Walkable Urban Code (2015–2016 rezonings)", "2015–2016"),
    "bellevue_belred_2009": ("53", "fitted", "Bellevue, BelRed", "2009"),
    "austin_tod_station_plans": ("48", "fitted", "Austin, TOD station area plans", "2006–2009"),
    "tysons_2010": ("51", "fitted", "Tysons, plan amendment", "2010"),
}
METHOD_CASES = {  # net-effect areas file -> state
    "stpaul_green_line_2011": "27", "seattle_nbh_othello_2012": "53", "seattle_mount_baker_2014": "53",
    "la_warner_center_2013": "06", "la_cornfield_arroyo_seco_2013": "06", "chicago_tod_2013_2015": "17",
    "philadelphia_2012_remapping": "42", "nyc_pooled_2003_2013": "36", "charlotte_tod_2019": "37",
}


# ------------------------------------------------------------------ census blocks
def block_points(st: str, year: int) -> gpd.GeoDataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"blocks_{st}_{year}.parquet"
    if f.exists():
        return gpd.read_parquet(f)
    if year == 2010:
        b = gpd.read_file(D / f"tabblock2010_{st}_pophu.zip").rename(columns={"HOUSING10": "homes"})
    else:
        b = gpd.read_file(D / f"tl_2020_{st}_tabblock20.zip").rename(columns={"HOUSING20": "homes"})
    b = b.to_crs(CRS)
    out = gpd.GeoDataFrame({"homes": b["homes"].astype(float).values, "land": b.area.values},
                           geometry=b.representative_point().values, crs=CRS)
    out.to_parquet(f)
    return out


def within(pts: gpd.GeoDataFrame, geom) -> pd.Series:
    if geom is None or geom.is_empty:
        return pd.Series(False, index=pts.index)
    idx = pts.sindex.query(geom, predicate="contains")
    m = pd.Series(False, index=pts.index)
    m.iloc[idx] = True
    return m


def per_acre(d10: pd.DataFrame, d20: pd.DataFrame) -> float:
    acres = (d10["land"].sum() + d20["land"].sum()) / 2 / ACRE
    return (d20["homes"].sum() - d10["homes"].sum()) / acres if acres > 0 else np.nan


def diff_with_interval(t10, t20, c10, c20, rng) -> tuple[float, float, float]:
    est = per_acre(t10, t20) - per_acre(c10, c20)
    arrs = [(x["homes"].to_numpy(), x["land"].to_numpy()) for x in (t10, t20, c10, c20)]
    draws = np.empty(DRAWS)
    for i in range(DRAWS):
        s = []
        for h, l in arrs:
            k = rng.integers(0, len(h), len(h)) if len(h) else np.array([], int)
            s.append((h[k].sum(), l[k].sum()))
        ta = (s[0][1] + s[1][1]) / 2 / ACRE
        ca = (s[2][1] + s[3][1]) / 2 / ACRE
        draws[i] = (s[1][0] - s[0][0]) / ta - (s[3][0] - s[2][0]) / ca
    lo, hi = np.nanquantile(draws, [0.05, 0.95])
    return est, lo, hi


# ------------------------------------------------------------------ boundaries
def boundary(case: str):
    if case == "phoenix_wu_2015_2016":
        from missing_middleware.tod import case_phoenix as P
        wu = gpd.read_file(RAW / "tod_cases" / "phoenix" / "wu_zoning.geojson")
        plan = gpd.read_file(RAW / "tod_cases" / "phoenix" / "wu_annual_plan.geojson")
        dates = {str(r.REDEFINE1).strip(): pd.to_datetime(r.DATE_APPRO, errors="coerce") for r in plan.itertuples()}
        wcol = next(c for c in wu.columns if c.upper().endswith("REDEFINE1"))
        case_no = wu[wcol].astype(str).str.strip()
        eff = [dates.get(c).year if pd.notna(dates.get(c)) else P.case_year(c) for c in case_no]
        g = wu[pd.Series(eff, index=wu.index).isin([2015, 2016])]
        return g.to_crs(CRS).geometry.make_valid().union_all(), wu.to_crs(CRS).geometry.make_valid().union_all()
    if case == "bellevue_belred_2009":
        from missing_middleware.tod import case_bellevue as B
        z = gpd.read_file(RAW / "tod_cases" / "bellevue" / "zoning.geojson")
        is_ord = z["ORDNUM"].map(B.ord_number).eq(B.BELRED_ORD) | z["ORDNUM2"].map(B.ord_number).eq(B.BELRED_ORD)
        zn = z["Zoning"].astype(str).str.strip().str.upper()
        g = z[is_ord & zn.isin(B.BR_HOUSING)]
        allbr = z[zn.str.startswith("BR-")]
        return g.to_crs(CRS).geometry.make_valid().union_all(), allbr.to_crs(CRS).geometry.make_valid().union_all()
    g = gpd.read_file(D / f"boundary_{case}.geojson")
    if case == "austin_tod_station_plans":
        g = g[g["TOD_SUB_DISTRICT"].astype(str).str.upper() == "APPROVED STATION AREA PLAN"]
    geom = g.to_crs(CRS).geometry.make_valid().union_all()
    if case == "tysons_2010":  # the county layer is Fairfax County with Tysons as its one hole (plan section 8, item 1)
        from shapely.geometry import Polygon
        geom = Polygon(geom.interiors[0])
    return geom, geom


# ------------------------------------------------------------------ new cases
def run_new_cases(rng) -> pd.DataFrame:
    geoms = {c: boundary(c) for c in NEW_CASES}
    every = unary_union([g[1] for g in geoms.values()])
    rows = []
    for case, (st, role, label, adopted) in NEW_CASES.items():
        treated, exclude = geoms[case]
        p10, p20 = block_points(st, 2010), block_points(st, 2020)
        ring = treated.buffer(HALF).difference(every).difference(exclude)
        ring_q = ring.difference(treated.buffer(QUARTER))
        res = {"case": case, "label": label, "adopted": adopted, "role": role, "state": st}
        for name, cg in (("main", ring), ("comparison_quarter_to_half_mile", ring_q)):
            t10, t20 = p10[within(p10, treated)], p20[within(p20, treated)]
            c10, c20 = p10[within(p10, cg)], p20[within(p20, cg)]
            est, lo, hi = diff_with_interval(t10, t20, c10, c20, rng)
            if name == "main":
                res.update({"treated_homes_2010": t10["homes"].sum(), "treated_homes_2020": t20["homes"].sum(),
                            "treated_acres": (t10["land"].sum() + t20["land"].sum()) / 2 / ACRE,
                            "comparison_homes_2010": c10["homes"].sum(), "comparison_homes_2020": c20["homes"].sum(),
                            "comparison_acres": (c10["land"].sum() + c20["land"].sum()) / 2 / ACRE,
                            "treated_blocks_2010": len(t10), "treated_blocks_2020": len(t20),
                            "treated_per_acre_decade": per_acre(t10, t20), "comparison_per_acre_decade": per_acre(c10, c20),
                            "difference_per_acre_decade": est, "low": lo, "high": hi,
                            "difference_per_acre_year": est / 10, "low_per_year": lo / 10, "high_per_year": hi / 10})
                if len(t20) and len(c20):
                    res["largest_block_left_out_per_acre_decade"] = (
                        per_acre(t10, t20.drop(t20["homes"].idxmax())) - per_acre(c10, c20.drop(c20["homes"].idxmax())))
            else:
                res.update({"quarter_to_half_difference_per_acre_decade": est, "quarter_to_half_low": lo,
                            "quarter_to_half_high": hi})
        rows.append(res)
        print(f"{case}: done", flush=True)
    slc = pd.read_csv(REFERENCE / "tod_slc_census_results.csv").set_index("estimate").loc["main"]
    rows.append({"case": "salt_lake_city_tsa_2010", "label": "Salt Lake City, TSA district", "adopted": "2010",
                 "role": "fitted", "state": "49", "treated_homes_2010": slc["treated_homes_2010"],
                 "treated_homes_2020": slc["treated_homes_2020"], "comparison_homes_2010": slc["comparison_homes_2010"],
                 "comparison_homes_2020": slc["comparison_homes_2020"],
                 "treated_per_acre_decade": slc["treated_net_homes_per_acre_decade"],
                 "comparison_per_acre_decade": slc["comparison_net_homes_per_acre_decade"],
                 "difference_per_acre_decade": slc["difference_per_acre_decade"], "low": slc["low"], "high": slc["high"],
                 "difference_per_acre_year": slc["difference_per_acre_year"], "low_per_year": slc["low_per_year"],
                 "high_per_year": slc["high_per_year"]})
    return pd.DataFrame(rows)


def holdout_check(cases: pd.DataFrame) -> pd.DataFrame:
    fit = cases[(cases.role == "fitted") & cases["difference_per_acre_year"].notna()]
    med, lo, hi = fit["difference_per_acre_year"].median(), fit["difference_per_acre_year"].min(), fit["difference_per_acre_year"].max()
    out = []
    for r in cases[cases.role == "holdout"].itertuples():
        inside = lo <= r.difference_per_acre_year <= hi
        covers = r.low_per_year <= med <= r.high_per_year
        out.append({"holdout": r.case, "estimate_per_acre_year": r.difference_per_acre_year, "low": r.low_per_year,
                    "high": r.high_per_year, "fitted_cases": len(fit), "fitted_median": med, "fitted_lowest": lo,
                    "fitted_highest": hi, "inside_fitted_range": inside, "interval_includes_median": covers,
                    "agrees": inside and covers})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ method check
def run_method_check(rng) -> pd.DataFrame:
    rows = []
    for case, st in METHOD_CASES.items():
        allm = pickle.loads((PROCESSED / "tod_net_effect" / f"areas_{case}.pkl").read_bytes())
        # Only members whose permit table spans the census decade (plan section 8, item 3).
        members = [m for m in allm if len(m["permits"]) and m["permits"]["year"].min() <= 2010 and m["permits"]["year"].max() >= 2019]
        if not members:
            rows.append({"case": case, "members": 0, "note": f"dropped: none of {len(allm)} members' permit tables span 2010-2019"})
            print(f"method {case}: dropped", flush=True)
            continue
        crs = members[0]["crs"]
        to = lambda g: gpd.GeoSeries([g], crs=crs).to_crs(CRS).iloc[0]  # noqa: E731
        treated = unary_union([to(m["treated_union"]) for m in members])
        upz = unary_union([to(m["upzoned_union"]) for m in members])
        ring = upz.buffer(QUARTER).difference(upz)
        p10, p20 = block_points(st, 2010), block_points(st, 2020)
        t10, t20, c10, c20 = p10[within(p10, treated)], p20[within(p20, treated)], p10[within(p10, ring)], p20[within(p20, ring)]
        est, lo, hi = diff_with_interval(t10, t20, c10, c20, rng)
        acres = {k: sum(m["acres"].get(k, 0) for m in members) for k in ("treatment", "comparison")}
        perm = pd.concat([m["permits"] for m in members], ignore_index=True)
        res = {"case": case, "members": len(members), "note": f"{len(members)} of {len(allm)} members",
               "census_treated_net_homes": t20["homes"].sum() - t10["homes"].sum(),
               "census_ring_net_homes": c20["homes"].sum() - c10["homes"].sum(),
               "census_treated_per_acre_decade": per_acre(t10, t20), "census_ring_per_acre_decade": per_acre(c10, c20),
               "census_difference_per_acre_decade": est, "census_low": lo, "census_high": hi,
               "treated_eligible_acres": acres["treatment"], "ring_eligible_acres": acres["comparison"]}
        for tag, yrs in (("2009_2018", range(2009, 2019)), ("2010_2019", range(2010, 2020))):
            q = perm[perm["year"].isin(list(yrs))]
            tu, cu = q.loc[q.area == "treatment", "units"].sum(), q.loc[q.area == "comparison", "units"].sum()
            pd_t = tu / acres["treatment"] if acres["treatment"] else np.nan
            pd_c = cu / acres["comparison"] if acres["comparison"] else np.nan
            res.update({f"permit_treated_homes_{tag}": tu, f"permit_ring_homes_{tag}": cu,
                        f"permit_treated_per_acre_{tag}": pd_t, f"permit_ring_per_acre_{tag}": pd_c,
                        f"permit_difference_per_acre_{tag}": pd_t - pd_c})
        res["census_over_permits_treated"] = res["census_treated_net_homes"] / res["permit_treated_homes_2009_2018"] \
            if res["permit_treated_homes_2009_2018"] else np.nan
        res["census_over_permits_ring"] = res["census_ring_net_homes"] / res["permit_ring_homes_2009_2018"] \
            if res["permit_ring_homes_2009_2018"] else np.nan
        res["gap_census_minus_permit_difference"] = est - res["permit_difference_per_acre_2009_2018"]
        res["methods_agree"] = bool(lo <= res["permit_difference_per_acre_2009_2018"] <= hi)
        res["methods_agree_2010_2019"] = bool(lo <= res["permit_difference_per_acre_2010_2019"] <= hi)
        rows.append(res)
        print(f"method {case}: done", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    cases = run_new_cases(rng)
    hold = holdout_check(cases)
    meth = run_method_check(rng)
    cases.round(4).to_csv(REFERENCE / "tod_census_cases.csv", index=False)
    hold.round(4).to_csv(REFERENCE / "tod_census_holdouts.csv", index=False)
    meth.round(4).to_csv(REFERENCE / "tod_census_method_check.csv", index=False)
    pd.set_option("display.width", 250)
    print(cases[["case", "role", "treated_homes_2010", "treated_homes_2020", "treated_acres", "comparison_per_acre_decade",
                 "treated_per_acre_decade", "difference_per_acre_year", "low_per_year", "high_per_year"]].round(3).to_string())
    print(hold.round(3).to_string())
    print(meth[["case", "census_treated_net_homes", "permit_treated_homes_2009_2018", "census_over_permits_treated",
                "census_over_permits_ring", "census_difference_per_acre_decade", "census_low", "census_high",
                "permit_difference_per_acre_2009_2018", "methods_agree"]].round(3).to_string())


if __name__ == "__main__":
    main()

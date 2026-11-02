"""Citywide net effect of each station-area reform, per 1,000 existing homes in the city (owner question, 2026-11-02:
"if we judged all this by permitted units per 1000 existing units in the city ... have we checked that?").

For each place: extra homes permitted a year attributable to the reform, as the station-area model measures it
(scripts/run_tod_station_model.py, stage 0, dates "permit_est", hand-check corrections, same windows): in each band,

    extra = (reform after/yr - reform before/yr) - reform existing homes x (comparison change per existing home)

i.e. the band's effect per 1,000 existing homes (effect_raw) x the reform band's existing homes / 1,000. Summed over
the bands out to 1 mile (also the 0-1/4 mile band alone), summed over a place's cases (New York's and Philadelphia's
rezonings, Seattle's two), and divided by the city's existing homes (Census). 90% interval: 1,000 bootstrap draws over
stops, stratified by group (reform stops and comparison stops resampled separately, each case on its own; a resampled
stop brings its lots in every band), seed 20261102; a place's draws are summed draw by draw over its cases.

Main places (not in the 2026-10-27 net-effect table): la_toc_2017, san_diego_2021, chicago_2022, honolulu_2017,
portland_2020. Like-for-like places (also in the 2026-10-27 table): New York, Philadelphia, Charlotte, Saint Paul,
Seattle (Othello + Mount Baker), Chicago 2015; these use the 2026-10-27 table's own city stock (2010 Census) so only
the numerator differs.

City existing homes (main places): the last decennial Census at or before the year before the reform (the station
model's rule): 2010 for Los Angeles (2016), Honolulu (2016) and Portland (2019); 2020 for San Diego (2020) and Chicago
(2021). Census block housing units (HOUSING10 / HOUSING20) whose block point lies in the place (Honolulu: the City and
County of Honolulu, county 15003). A linear interpolation of 2010 and 2020 to the year before the reform is given
beside it where both counts are in data/raw (not Honolulu: no 2020 Hawaii blocks on disk).

Overlap: where a place has several cases (New York, Philadelphia, Seattle), a lot in k cases' reform groups is
weighted 1/k in each, so the place total counts each lot once.

Coverage (main places): the share of homes on the reform's own map that the station-area table counts, i.e. block
homes inside the map whose nearest stop is a reform stop within 1 mile (stop points approximated by each stop's
nearest lot, median 40 m off in Los Angeles). Reform land farther out is not in the citywide total, which then
undercounts. Like-for-like places: the share of upzoned lots' existing homes in the lot tables that sit in the reform
group (lots more than 1 mile from every stop are not in the tables, so this is an upper bound).

    .venv/bin/python scripts/run_tod_citywide_per1000.py

Writes reference/tod_citywide_per1000.csv (summaries only; no parcel ids or owner fields). Does not change any output
of run_tod_station_model.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
import run_tod_station_model as M  # noqa: E402

OUT = M.OUT
BANDS = M.BANDS
SEED, DRAWS = 20261102, 1000
CRS = 5070
MILE, QUARTER = 1609.0, 402.0
COLS = ["group", "band", "stop_id", "homes_existing", "homes_before_win", "homes_after_win", "in_reform_area",
        "implausible", "acres", "x", "y"]

MAIN = {"Los Angeles (TOC 2017)": ["la_toc_2017"], "San Diego (2021)": ["san_diego_2021"],
        "Chicago (Connected Communities 2022)": ["chicago_2022"], "Honolulu (2017)": ["honolulu_2017"],
        "Portland (2020)": ["portland_2020"]}


def like_cases() -> dict[str, list[str]]:
    lots = sorted(p.stem.removeprefix("lots_") for p in OUT.glob("lots_*.parquet"))
    return {"New York": [c for c in lots if c.startswith("nyc_")], "Philadelphia": [c for c in lots if c.startswith("phl_")],
            "Charlotte": ["charlotte_2019"], "Saint Paul": ["stpaul_2011"],
            "Seattle": ["seattle_othello_2012", "seattle_mount_baker_2014"], "Chicago": ["chicago_2015"]}


# =========================================================================== numerator

def load(case: str) -> pd.DataFrame:
    D = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=COLS)
    if (OUT / f"events_{case}.parquet").exists():
        D = M.event_windows(case, D, "permit_est")
    return D[~D.implausible.fillna(False).astype(bool)]


def extra_by_band(e, b, a, yb, ya):
    """e, b, a: arrays [..., group(0 reform, 1 comparison), band]. Extra homes a year per band (nan where the model
    skips the band: no existing homes on either side)."""
    re, rb, ra = e[..., 0, :], b[..., 0, :], a[..., 0, :]
    ce, cb, ca = e[..., 1, :], b[..., 1, :], a[..., 1, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        cr = (ca / ya - cb / yb) / ce
        x = (ra / ya - rb / yb) - re * cr
    return np.where((re > 0) & (ce > 0), x, np.nan)


def reform_key_counts(cases: list[str]) -> pd.Series:
    """How many of a place's cases put each lot (by its point) in their reform group. New York's and Philadelphia's
    rezonings (and Seattle's two cases) share stops and lots; each such lot is weighted 1/k in each of its k cases, so
    the place total counts every lot once (each lot's effect is the average over the cases that claim it)."""
    ks = []
    for c in cases:
        L = pd.read_parquet(OUT / f"lots_{c}.parquet", columns=["group", "x", "y"])
        L = L[L.group == "reform"]
        ks.append(pd.Series(1, index=pd.MultiIndex.from_arrays([L.x.round(1), L.y.round(1)])).groupby(level=[0, 1]).size().clip(upper=1))
    return pd.concat(ks).groupby(level=[0, 1]).sum() if ks else pd.Series(dtype=float)


def case_numbers(case: str, idx: int, kcount: pd.Series | None = None) -> dict:
    D = load(case)
    if kcount is not None and len(kcount) and kcount.max() > 1:
        r = D.group == "reform"
        k = kcount.reindex(pd.MultiIndex.from_arrays([D.x[r].round(1), D.y[r].round(1)])).fillna(1).to_numpy()
        D = D.copy()
        for col in ("homes_existing", "homes_before_win", "homes_after_win"):
            D.loc[r, col] = D.loc[r, col].to_numpy() / k
    yb, ya = M.windows(case)
    g = D.groupby(["group", "stop_id", "band"])[["homes_existing", "homes_before_win", "homes_after_win"]].sum()
    out = {"case": case, "years_before": yb, "years_after": ya}
    mats = []
    for grp in ("reform", "comparison"):
        if grp not in g.index.get_level_values(0):
            return {**out, "skip": f"no {grp} stops"}
        t = g.loc[grp].unstack("band").reindex(columns=pd.MultiIndex.from_product(
            [["homes_existing", "homes_before_win", "homes_after_win"], BANDS])).fillna(0.0)
        mats.append(t.to_numpy().reshape(len(t), 3, 3))          # stop x var x band
    point = [m.sum(axis=0) for m in mats]                         # var x band
    e = np.stack([point[0][0], point[1][0]]); b = np.stack([point[0][1], point[1][1]]); a = np.stack([point[0][2], point[1][2]])
    xb = extra_by_band(e, b, a, yb, ya)
    rng = np.random.default_rng([SEED, idx])
    sums = []
    for m in mats:
        n = len(m)
        w = rng.multinomial(n, np.full(n, 1.0 / n), size=DRAWS)  # draws x stops
        sums.append(np.einsum("ds,svb->dvb", w, m))               # draws x var x band
    E = np.stack([sums[0][:, 0], sums[1][:, 0]], axis=1)
    B = np.stack([sums[0][:, 1], sums[1][:, 1]], axis=1)
    A = np.stack([sums[0][:, 2], sums[1][:, 2]], axis=1)
    xd = extra_by_band(E, B, A, yb, ya)                           # draws x band
    rh = D[D.group == "reform"]
    out.update({
        "extra_by_band": xb, "draws_by_band": xd,
        "reform_homes_by_band": point[0][0], "comparison_homes_by_band": point[1][0],
        "effect_raw_by_band": 1000 * xb / point[0][0],
        "reform_stops": len(mats[0]), "comparison_stops": len(mats[1]),
        "upzoned_homes_reform_group": float((rh.homes_existing * rh.in_reform_area.fillna(0).astype(float)).sum()),
        "upzoned_homes_all_groups": float((D.homes_existing * D.in_reform_area.fillna(0).astype(float)).sum()),
        "reform_keys": set(zip(rh.x.round(1), rh.y.round(1))),
        "reform_homes_total": float(rh.homes_existing.sum()),
    })
    return out


def place_summary(cases: list[dict], scope: str) -> dict:
    sel = slice(None) if scope == "all bands, 0-1 mile" else slice(0, 1)
    cs = [c for c in cases if "skip" not in c]

    def tot(v):
        v = np.asarray(v)[..., sel]
        return np.where(np.isnan(v).all(axis=-1), np.nan, np.nansum(v, axis=-1))
    pt = float(np.nansum([tot(c["extra_by_band"]) for c in cs]))
    dr = np.nansum(np.stack([tot(c["draws_by_band"]) for c in cs]), axis=0)
    lo, hi = np.nanpercentile(dr, [5, 95])
    rh = float(sum(np.asarray(c["reform_homes_by_band"])[sel].sum() for c in cs))
    return {"extra_homes_per_year": pt, "extra_low": lo, "extra_high": hi, "reform_band_homes": rh,
            "cases_used": len(cs), "cases_skipped": len(cases) - len(cs),
            "reform_stops": sum(c["reform_stops"] for c in cs), "comparison_stops": sum(c["comparison_stops"] for c in cs),
            "after_years": "/".join(sorted({str(c["years_after"]) for c in cs})),
            "before_years": "/".join(sorted({str(c["years_before"]) for c in cs}))}


# =========================================================================== city homes (Census)

def _place_poly(path, geoid_col, geoid):
    p = X.read_vector(path, columns=[geoid_col])
    p = p[p[geoid_col] == geoid]
    assert len(p) == 1, (path, geoid)
    return p.geometry.iloc[0]


def homes_2020(st: str, geoid: str) -> float:
    blk = next(f for f in (RAW / "tod_census_cases" / f"tl_2020_{st}_tabblock20.zip",
                           RAW / "parking_census_route" / f"tl_2020_{st}_tabblock20.zip") if f.exists())
    poly = _place_poly(next(f for f in (RAW / "tod_census_cases" / f"tl_2020_{st}_place.zip",) if f.exists()), "GEOID", geoid)
    b = X.read_vector(blk, columns=["HOUSING20", "INTPTLON20", "INTPTLAT20"], geometry=False)
    x, y = b.INTPTLON20.astype(float).to_numpy(), b.INTPTLAT20.astype(float).to_numpy()
    bb = X.feature_bounds([poly])[0]
    m = (x >= bb[0]) & (x <= bb[2]) & (y >= bb[1]) & (y <= bb[3])
    inside = X.first_within(x[m], y[m], [poly]) >= 0
    return float(pd.to_numeric(b.HOUSING20[m], errors="coerce").fillna(0).to_numpy()[inside].sum())


def homes_2010(st: str, place_path, geoid_col, geoid) -> float:
    blk = RAW / "tod_census_cases" / f"tabblock2010_{st}_pophu.zip"
    poly = _place_poly(place_path, geoid_col, geoid)
    bb = X.feature_bounds([poly])[0]
    b = X.read_vector(blk, columns=["HOUSING10"], bbox=tuple(bb))
    x, y = X.interior_points(list(b.geometry))
    inside = X.first_within(x, y, [poly]) >= 0
    return float(pd.to_numeric(b.HOUSING10, errors="coerce").fillna(0).to_numpy()[inside].sum())


def honolulu_2010() -> float:
    b = X.read_vector(RAW / "tod_census_cases" / "tabblock2010_15_pophu.zip", columns=["COUNTYFP10", "HOUSING10"], geometry=False)
    return float(pd.to_numeric(b.HOUSING10[b.COUNTYFP10 == "003"], errors="coerce").sum())


def main_stocks() -> dict[str, dict]:
    cov = pd.read_csv(OUT.parent / "tod_net_effect" / "coverage_cities.csv").set_index("city") \
        if (OUT.parent / "tod_net_effect" / "coverage_cities.csv").exists() else None
    t2010 = RAW / "tod_net_coverage" / "tiger2010"
    la10 = float(cov.loc["Los Angeles", "homes"]) if cov is not None else homes_2010("06", t2010 / "tl_2010_06_place10.zip", "GEOID10", "0644000")
    ch10 = float(cov.loc["Chicago", "homes"]) if cov is not None else homes_2010("17", t2010 / "tl_2010_17_place10.zip", "GEOID10", "1714000")
    s = {
        "Los Angeles (TOC 2017)": {"y0": 2016, "h2010": la10, "h2020": homes_2020("06", "0644000")},
        "San Diego (2021)": {"y0": 2020, "h2010": homes_2010("06", t2010 / "tl_2010_06_place10.zip", "GEOID10", "0666000"),
                             "h2020": homes_2020("06", "0666000")},
        "Chicago (Connected Communities 2022)": {"y0": 2021, "h2010": ch10, "h2020": homes_2020("17", "1714000")},
        "Honolulu (2017)": {"y0": 2016, "h2010": honolulu_2010(), "h2020": np.nan},
        # no 2010 Oregon place file on disk: the 2020 Portland boundary is used for the 2010 blocks (flagged)
        "Portland (2020)": {"y0": 2019, "h2010": homes_2010("41", RAW / "tod_census_cases" / "tl_2020_41_place.zip", "GEOID", "4159000"),
                            "h2020": homes_2020("41", "4159000")},
    }
    for k, v in s.items():
        v["main"] = v["h2020"] if v["y0"] >= 2020 else v["h2010"]
        v["main_source"] = ("2020 Census" if v["y0"] >= 2020 else "2010 Census") + " block housing units in the place" \
            + (" (City and County of Honolulu, county 15003)" if k.startswith("Honolulu") else "") \
            + ("; 2010 blocks placed with the 2020 boundary" if k.startswith("Portland") else "")
        v["interp"] = v["h2010"] + (v["h2020"] - v["h2010"]) * min(v["y0"] - 2010, 10) / 10 if pd.notna(v["h2020"]) else np.nan
    return s


# =========================================================================== coverage of the reform's own map

def reform_polys(case: str) -> list:
    if case == "la_toc_2017":
        return list(X.read_vector(RAW / "tod_radius_programs" / "la" / "toc_tiers_oct2017.geojson", dst=CRS).geometry)
    if case == "san_diego_2021":
        return list(X.read_vector(RAW / "tod_radius_programs" / "san_diego" / "transit_priority_areas.geojson", dst=CRS).geometry)
    if case == "honolulu_2017":
        return [g for f in ("tod_zone_change_waipahu_tc.geojson", "tod_zone_change_west_loch.geojson")
                for g in X.read_vector(RAW / "tod_radius_programs" / "honolulu" / f, dst=CRS).geometry]
    if case == "portland_2020":
        from station_cases import cluster_west as W
        return W.reform_area(case)
    return []


def block_points(case: str, year: int):
    st = {"la_toc_2017": "06", "san_diego_2021": "06", "honolulu_2017": "15", "portland_2020": "41", "chicago_2022": "17"}[case]
    D = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=["x", "y"])
    pad = 3000.0
    box = (D.x.min() - pad, D.y.min() - pad, D.x.max() + pad, D.y.max() + pad)
    if year == 2020:
        blk = RAW / "tod_census_cases" / f"tl_2020_{st}_tabblock20.zip"
        b = X.read_vector(blk, columns=["HOUSING20", "INTPTLON20", "INTPTLAT20"], geometry=False)
        x, y = X.transform(b.INTPTLON20.astype(float).to_numpy(), b.INTPTLAT20.astype(float).to_numpy(), 4269, CRS)
        h = pd.to_numeric(b.HOUSING20, errors="coerce").fillna(0).to_numpy()
    else:
        b = X.read_vector(RAW / "tod_census_cases" / f"tabblock2010_{st}_pophu.zip", dst=CRS, columns=["HOUSING10"], bbox=box)
        x, y = X.interior_points(list(b.geometry))
        h = pd.to_numeric(b.HOUSING10, errors="coerce").fillna(0).to_numpy()
    m = (x >= box[0]) & (x <= box[2]) & (y >= box[1]) & (y <= box[3])
    return x[m], y[m], h[m]


def map_coverage(case: str, year: int) -> dict:
    polys = reform_polys(case)
    if not polys:
        return {}
    L = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=["group", "stop_id", "dist_m", "x", "y"])
    S = L.loc[L.groupby(["group", "stop_id"]).dist_m.idxmin(), ["group", "x", "y"]].reset_index(drop=True)
    from scipy.spatial import cKDTree
    x, y, h = block_points(case, year)
    inmap = X.first_within(x, y, polys) >= 0
    d, i = cKDTree(S[["x", "y"]].to_numpy()).query(np.c_[x, y])
    ref = S.group.to_numpy()[i] == "reform"
    tot = h[inmap].sum()
    return {"map_homes": float(tot),
            "map_homes_counted_share": float(h[inmap & ref & (d <= MILE)].sum() / tot) if tot else np.nan,
            "map_homes_quarter_mile_share": float(h[inmap & ref & (d <= QUARTER)].sum() / tot) if tot else np.nan,
            "map_homes_beyond_1_mile": float(h[inmap & ~(ref & (d <= MILE))].sum())}


# =========================================================================== main

def main() -> None:
    oct27 = pd.read_csv(REFERENCE / "tod_net_effect_by_case.csv")
    o_city = {"New York": "nyc_pooled_2003_2013", "Philadelphia": "philadelphia_2012_remapping", "Charlotte": "charlotte_tod_2019",
              "Saint Paul": "stpaul_green_line_2011", "Seattle": "seattle_all_cases", "Chicago": "chicago_tod_2013_2015"}
    stocks = main_stocks()
    print({k: (round(v["h2010"]), v["h2020"], round(v["interp"]) if pd.notna(v["interp"]) else None) for k, v in stocks.items()})
    rows, idx = [], 0
    groups = [("main", MAIN), ("like-for-like", like_cases())]
    for kind, places in groups:
        for place, cases in places.items():
            kc = reform_key_counts(cases) if len(cases) > 1 else None
            res = []
            for c in cases:
                res.append(case_numbers(c, idx, kc)); idx += 1
            used = [r for r in res if "skip" not in r]
            keys = [r["reform_keys"] for r in used]
            allk = set().union(*keys) if keys else set()
            dup = 1 - len(allk) / sum(len(k) for k in keys) if keys else np.nan
            if kind == "main":
                st = stocks[place]
                stock, src = st["main"], st["main_source"]
                cov = map_coverage(cases[0], 2020 if st["y0"] >= 2020 else 2010)
            else:
                o = oct27.set_index("case").loc[o_city[place]]
                stock, src = float(o["city_housing_stock"]), f"{o['city_housing_stock_source']} (as the 2026-10-27 table)"
                cov = {}
            for scope in ("all bands, 0-1 mile", "0-1/4 mile only"):
                s = place_summary(res, scope)
                r = {"comparison_set": kind, "place": place, "scope": scope, "cases": ";".join(cases) if len(cases) <= 2 else f"{len(cases)} rezonings",
                     **s, "city_existing_homes": stock, "city_existing_homes_source": src}
                for k in ("", "_low", "_high"):
                    v = s["extra_homes_per_year" if not k else f"extra{k}"]
                    r[f"per_1000_per_year{k}"] = 1000 * v / stock
                    r[f"per_1000_5yr{k}"] = 5000 * v / stock
                r["reform_band_homes_share_of_city"] = s["reform_band_homes"] / stock
                if kind == "main":
                    r["city_existing_homes_2010"], r["city_existing_homes_2020"] = stocks[place]["h2010"], stocks[place]["h2020"]
                    r["city_existing_homes_interpolated"] = stocks[place]["interp"]
                    r["per_1000_5yr_on_interpolated_stock"] = 5000 * s["extra_homes_per_year"] / stocks[place]["interp"] \
                        if pd.notna(stocks[place]["interp"]) else np.nan
                    r.update(cov)
                up_r = sum(x["upzoned_homes_reform_group"] for x in used)
                up_a = sum(x["upzoned_homes_all_groups"] for x in used)
                if kind == "main":
                    r["upzoned_lot_homes_in_reform_group_share"] = up_r / up_a if up_a else np.nan
                r["reform_lots_in_more_than_one_case_share"] = dup
                if kind == "like-for-like":
                    o = oct27.set_index("case").loc[o_city[place]]
                    r["oct27_net_extra_homes_per_year"] = o["net_extra_homes_per_year"]
                    r["oct27_treated_area_homes"] = o["treated_area_homes_before"]
                    r["upzoned_lot_homes_in_reform_group"] = up_r
                    r["oct27_per_1000_5yr"] = 10 * o["net_share_5yr_pct"]
                    r["oct27_per_1000_5yr_low"] = 10 * o.get("net_share_5yr_low_pct", 5 * o["net_share_low_pct"])
                    r["oct27_per_1000_5yr_high"] = 10 * o.get("net_share_5yr_high_pct", 5 * o["net_share_high_pct"])
                    if pd.isna(r["oct27_per_1000_5yr_low"]):
                        r["oct27_per_1000_5yr_low"], r["oct27_per_1000_5yr_high"] = 50 * o["net_share_low_pct"], 50 * o["net_share_high_pct"]
                rows.append(r)
            print(place, "done")
    R = pd.DataFrame(rows)
    R.to_csv(REFERENCE / "tod_citywide_per1000.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 250)
    print(R[["place", "scope", "extra_homes_per_year", "extra_low", "extra_high", "city_existing_homes", "per_1000_per_year",
             "per_1000_5yr", "per_1000_5yr_low", "per_1000_5yr_high", "reform_band_homes_share_of_city"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()

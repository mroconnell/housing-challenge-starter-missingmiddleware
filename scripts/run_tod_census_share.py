"""Census cases: city share per 1,000 homes, and blocks scored by the share of their land inside the area.

    uv run --all-extras python scripts/run_tod_census_share.py

Plan: docs/tod/CENSUS_CASES_PLAN.md section 9 (written before running). Reads the boundaries and census blocks used by
scripts/run_tod_census_cases.py, plus Salt Lake City's (data/raw/tod_slc). Writes reference/tod_census_share.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.run_tod_slc_census import TSA_STATIONS, stations  # noqa: E402

SEED = 20261031
JURIS = {  # case: (jurisdiction, 2010 homes)
    "jersey_city_journal_square_2010": ("Jersey City", 108720), "milpitas_tasp_2008": ("Milpitas", 19806),
    "austin_tod_station_plans": ("Austin", 354241), "bellevue_belred_2009": ("Bellevue", 55551),
    "tysons_2010": ("Fairfax County", 407998), "salt_lake_city_tsa_2010": ("Salt Lake City", 80724),
    "phoenix_wu_2015_2016": ("Phoenix", None),
}


def slc_boundary():
    z = gpd.read_file(RAW / "tod_slc" / "slc_zoning_2020_jacobs.geojson").to_crs(26912)
    tsa = z[z["ZONING"].str.startswith("TSA")].copy()
    st = stations()
    rp = tsa.copy()
    rp["geometry"] = tsa.representative_point()
    near = gpd.sjoin_nearest(rp, st[["name", "geometry"]])
    near = near[~near.index.duplicated()]
    keep = tsa[near["name"].isin(TSA_STATIONS)]
    return (keep.to_crs(R.CRS).geometry.make_valid().union_all(), tsa.to_crs(R.CRS).geometry.make_valid().union_all())


def block_polys(path: Path, year: int, box) -> gpd.GeoDataFrame:
    b = gpd.read_file(path, bbox=tuple(gpd.GeoSeries([box], crs=R.CRS).to_crs(4269).total_bounds))
    b = b.rename(columns={"HOUSING10": "homes", "HOUSING20": "homes"}).to_crs(R.CRS)
    return gpd.GeoDataFrame({"homes": b["homes"].astype(float).values, "land": b.area.values}, geometry=b.geometry.values, crs=R.CRS)


def shares(b: gpd.GeoDataFrame, geom) -> np.ndarray:
    s = np.zeros(len(b))
    idx = b.sindex.query(geom, predicate="intersects")
    if len(idx):
        s[idx] = b.geometry.iloc[idx].intersection(geom).area.values / b["land"].values[idx]
    return np.clip(s, 0, 1)


def weighted(b10, s10, b20, s20, rng, draws=R.DRAWS):
    def rate(h10, l10, h20, l20):
        a = (l10 + l20) / 2 / R.ACRE
        return (h20 - h10) / a if a > 0 else np.nan
    tv = lambda b, s: (b["homes"].values * s, b["land"].values * s)  # noqa: E731
    return tv(b10, s10), tv(b20, s20)


def run():
    rng = np.random.default_rng(SEED)
    geoms = {c: R.boundary(c) for c in R.NEW_CASES}
    geoms["salt_lake_city_tsa_2010"] = slc_boundary()
    every = unary_union([g[1] for g in geoms.values()])
    cases = pd.read_csv(REFERENCE / "tod_census_cases.csv").set_index("case")
    rows = []
    for case, (treated, exclude) in geoms.items():
        if case == "salt_lake_city_tsa_2010":
            f10, f20 = RAW / "tod_slc" / "tabblock2010_49_pophu.zip", RAW / "tod_slc" / "tl_2020_49_tabblock20.zip"
        else:
            st = R.NEW_CASES[case][0]
            f10, f20 = R.D / f"tabblock2010_{st}_pophu.zip", R.D / f"tl_2020_{st}_tabblock20.zip"
        ring = treated.buffer(R.HALF).difference(every).difference(exclude)
        box = treated.buffer(R.HALF + 500).envelope
        b10, b20 = block_polys(f10, 2010, box), block_polys(f20, 2020, box)
        st10, st20 = shares(b10, treated), shares(b20, treated)
        sc10, sc20 = shares(b10, ring), shares(b20, ring)

        def diff(i10, i20):
            def r(b, s, i):
                h, l = (b["homes"].values[i] * s[i]).sum(), (b["land"].values[i] * s[i]).sum()
                return h, l
            th10, tl10 = r(b10, st10, i10); th20, tl20 = r(b20, st20, i20)
            ch10, cl10 = r(b10, sc10, i10); ch20, cl20 = r(b20, sc20, i20)
            ta, ca = (tl10 + tl20) / 2 / R.ACRE, (cl10 + cl20) / 2 / R.ACRE
            return ((th20 - th10) / ta if ta else np.nan) - ((ch20 - ch10) / ca if ca else np.nan), ta, th10, th20
        a10, a20 = np.where((st10 > 0) | (sc10 > 0))[0], np.where((st20 > 0) | (sc20 > 0))[0]
        est, acres, th10, th20 = diff(a10, a20)
        draws = []
        for _ in range(R.DRAWS):
            draws.append(diff(rng.choice(a10, len(a10)), rng.choice(a20, len(a20)))[0])
        lo, hi = np.nanquantile(draws, [0.05, 0.95])
        juris, homes = JURIS[case]
        cp = cases.loc[case] if case in cases.index else None
        cp_diff = float(cp["difference_per_acre_decade"]) if cp is not None else np.nan
        cp_acres = float(cp["treated_acres"]) if cp is not None and pd.notna(cp.get("treated_acres")) else np.nan
        extra_cp = cp_diff * cp_acres
        extra_aw = est * acres
        rows.append({
            "case": case, "jurisdiction": juris, "jurisdiction_homes_2010": homes,
            "blocks_wholly_inside_2010": int((st10 >= 0.99).sum()), "blocks_partly_inside_2010": int(((st10 > 0) & (st10 < 0.99)).sum()),
            "blocks_wholly_inside_2020": int((st20 >= 0.99).sum()), "blocks_partly_inside_2020": int(((st20 > 0) & (st20 < 0.99)).sum()),
            "share_of_upzoned_homes_2010_in_partial_blocks": (b10["homes"].values * st10 * ((st10 > 0) & (st10 < 0.99))).sum() / max(th10, 1),
            "area_share_upzoned_acres": acres, "area_share_upzoned_homes_2010": th10, "area_share_upzoned_homes_2020": th20,
            "area_share_difference_per_acre_decade": est, "area_share_low": lo, "area_share_high": hi,
            "centre_point_difference_per_acre_decade": cp_diff,
            "extra_homes_decade_centre_point": extra_cp, "extra_homes_decade_area_share": extra_aw,
            "city_share_per_1000_decade_centre_point": 1000 * extra_cp / homes if homes else np.nan,
            "city_share_per_1000_decade_area_share": 1000 * extra_aw / homes if homes else np.nan,
            "city_share_per_1000_decade_area_share_low": 1000 * lo * acres / homes if homes else np.nan,
            "city_share_per_1000_decade_area_share_high": 1000 * hi * acres / homes if homes else np.nan,
            "per_1000_upzoned_homes_decade": 1000 * extra_aw / th10 if th10 >= 500 else np.nan,
        })
        print(f"{case}: done", flush=True)
    out = pd.DataFrame(rows)
    out["city_share_per_1000_five_years_area_share"] = out["city_share_per_1000_decade_area_share"] / 2
    out.round(4).to_csv(REFERENCE / "tod_census_share.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(2).T.to_string())


if __name__ == "__main__":
    run()

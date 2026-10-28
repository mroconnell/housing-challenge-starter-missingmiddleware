"""Salt Lake City's 2010 station-area (TSA) districts: net homes added 2010-2020 from census block counts.

    uv run --all-extras python scripts/fetch_tod_slc.py
    uv run --all-extras python scripts/run_tod_slc_census.py

Plan: docs/tod/SLC_CENSUS_PLAN.md (written before looking). Results: docs/tod/SLC_CENSUS_RESULTS.md.
Writes reference/tod_slc_census_results.csv and reference/tod_slc_census_areas.csv (area totals only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

D = RAW / "tod_slc"
CRS = 26912            # NAD83 / UTM 12N, metres
HALF, QUARTER = 804.672, 402.336
ACRE = 4046.8564
SEED, DRAWS = 20261029, 2000

# Plan section 3. 2200 West is named in the ordinance but has no rail stop in the National Transit Map (plan section 8).
TSA_STATIONS = ["North Temple Station", "Jackson/Euclid Station", "Fairpark Station", "Power Station",
                "1940 W. North Temple Station"]
LATER_TSA = ["Library Station", "Trolley Station", "900 East Station", "Arena Station"]
NEW_2011_2013 = ["Decker Lake Station", "West Valley Central Station", "Redwood Junction Station", "River Trail Station",
                 "Bingham Junction Station", "Historic Gardner Station", "West Jordan City Center Station",
                 "2700 W. Sugar Factory Rd Station", "Jordan Valley Station", "4800 W. Old Bingham Hwy Station",
                 "5600 W. Old Bingham Hwy Station", "South Jordan Parkway Station", "Daybreak Parkway Station",
                 "Kimballs Lane Station", "Draper Town Center Station"]


def stations() -> gpd.GeoDataFrame:
    s = pd.DataFrame(json.load(open(D / "uta_stops.json")))
    s = s[s["stop_type_text"].str.contains("rail", case=False, na=False)]
    s["name"] = s["stop_name"].str.strip()
    s.loc[s["name"].str.upper() == "RIVER TRAIL STATION", "name"] = "River Trail Station"
    s = s.groupby("name", as_index=False)[["stop_lat", "stop_lon"]].mean()
    return gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(CRS)


def blocks(year: int) -> gpd.GeoDataFrame:
    if year == 2010:
        b = gpd.read_file(D / "tabblock2010_49_pophu.zip")
        b = b.rename(columns={"BLOCKID10": "geoid", "HOUSING10": "homes"})
    else:
        b = gpd.read_file(D / "tl_2020_49_tabblock20.zip")
        b = b.rename(columns={"GEOID20": "geoid", "HOUSING20": "homes"})
    b = b.to_crs(CRS)
    b["land"] = b.area   # polygon area for both years (the 2010 file has no land-area field; plan section 8)
    pts = b.copy()
    pts["geometry"] = b.representative_point()
    return pts[["geoid", "homes", "land", "geometry"]]


def assign(pts: gpd.GeoDataFrame, st: gpd.GeoDataFrame, tsa: gpd.GeoDataFrame) -> pd.Series:
    """Group of each block point: treated, comp1 (same line, not TSA), comp2 (new stations elsewhere), or none."""
    tsa_main = tsa[tsa["station"].isin(TSA_STATIONS)]
    in_tsa_main = gpd.sjoin(pts, tsa_main[["geometry"]], predicate="within", how="left")["index_right"].notna()
    in_tsa_main = in_tsa_main.groupby(level=0).any()
    in_any_tsa = gpd.sjoin(pts, tsa[["geometry"]], predicate="within", how="left")["index_right"].notna().groupby(level=0).any()
    s1 = st[st["name"].isin(TSA_STATIONS)]
    s2 = st[st["name"].isin(NEW_2011_2013)]
    d1 = pts.geometry.apply(lambda p: s1.distance(p).min())
    d2 = pts.geometry.apply(lambda p: s2.distance(p).min())
    g = pd.Series("none", index=pts.index)
    g[(d2 <= HALF)] = "comp2"
    g[(d1 <= HALF) & ~in_any_tsa] = "comp1"
    g[in_tsa_main] = "treated"
    return g, d1


def main() -> None:
    st = stations()
    missing = [n for n in TSA_STATIONS + NEW_2011_2013 + LATER_TSA if n not in set(st["name"])]
    print("stations not found:", missing)
    z = gpd.read_file(D / "slc_zoning_2020_jacobs.geojson").to_crs(CRS)
    tsa = z[z["ZONING"].str.startswith("TSA")].copy()
    rp = tsa.copy()
    rp["geometry"] = tsa.representative_point()
    near = gpd.sjoin_nearest(rp, st[["name", "geometry"]], distance_col="d")
    near = near[~near.index.duplicated()]
    tsa["station"] = near["name"]
    tsa["core"] = tsa["ZONING"].str.endswith("-C")

    rows, area_rows = [], []
    data = {}
    for year in (2010, 2020):
        pts = blocks(year)
        bbox = st[st["name"].isin(TSA_STATIONS + NEW_2011_2013)].total_bounds
        pts = pts.cx[bbox[0] - 3000:bbox[2] + 3000, bbox[1] - 3000:bbox[3] + 3000].copy()
        grp, d1 = assign(pts, st, tsa)
        core = gpd.sjoin(pts, tsa[tsa["core"] & tsa["station"].isin(TSA_STATIONS)][["geometry"]], predicate="within",
                         how="left")["index_right"].notna().groupby(level=0).any()
        pts["group"], pts["d1"], pts["core"] = grp, d1, core
        data[year] = pts[pts["group"] != "none"].drop(columns="geometry")
    b10, b20 = data[2010], data[2020]

    def totals(df10, df20):
        return {"homes_2010": df10["homes"].sum(), "homes_2020": df20["homes"].sum(),
                "acres_2010": df10["land"].sum() / ACRE, "acres_2020": df20["land"].sum() / ACRE,
                "blocks_2010": len(df10), "blocks_2020": len(df20)}

    def per_acre(df10, df20):
        acres = (df10["land"].sum() + df20["land"].sum()) / 2 / ACRE
        return (df20["homes"].sum() - df10["homes"].sum()) / acres

    variants = {
        "main": (lambda d: d["group"] == "treated", lambda d: d["group"] == "comp1"),
        "vs_new_stations_elsewhere": (lambda d: d["group"] == "treated", lambda d: d["group"] == "comp2"),
        "core_only": (lambda d: (d["group"] == "treated") & d["core"], lambda d: d["group"] == "comp1"),
        "comparison_quarter_to_half_mile": (lambda d: d["group"] == "treated",
                                            lambda d: (d["group"] == "comp1") & (d["d1"] > QUARTER)),
    }
    rng = np.random.default_rng(SEED)
    for name, (ft, fc) in variants.items():
        t10, t20, c10, c20 = b10[ft(b10)], b20[ft(b20)], b10[fc(b10)], b20[fc(b20)]
        est = per_acre(t10, t20) - per_acre(c10, c20)
        draws = []
        for _ in range(DRAWS):
            s = [x.sample(len(x), replace=True, random_state=rng.integers(1 << 31)) for x in (t10, t20, c10, c20)]
            draws.append(per_acre(s[0], s[1]) - per_acre(s[2], s[3]))
        lo, hi = np.quantile(draws, [0.05, 0.95])
        rows.append({"estimate": name, "treated_net_homes_per_acre_decade": per_acre(t10, t20),
                     "comparison_net_homes_per_acre_decade": per_acre(c10, c20),
                     "difference_per_acre_decade": est, "low": lo, "high": hi,
                     "difference_per_acre_year": est / 10, "low_per_year": lo / 10, "high_per_year": hi / 10,
                     **{f"treated_{k}": v for k, v in totals(t10, t20).items()},
                     **{f"comparison_{k}": v for k, v in totals(c10, c20).items()}})
    # Largest block left out of each group (by 2020 homes), main comparison.
    t10, t20, c10, c20 = b10[b10.group == "treated"], b20[b20.group == "treated"], b10[b10.group == "comp1"], b20[b20.group == "comp1"]
    rows.append({"estimate": "largest_2020_block_left_out",
                 "difference_per_acre_decade": per_acre(t10, t20.drop(t20["homes"].idxmax())) - per_acre(c10, c20.drop(c20["homes"].idxmax()))})
    res = pd.DataFrame(rows)
    # Treated net gain as a share of Salt Lake City's 2010 homes.
    from missing_middleware.tod.control_cities import read_gazetteer
    gaz = read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip")
    slc = float(gaz.loc[gaz["geoid"] == "4967000", "hu10"].iloc[0])
    res["treated_net_homes_2010_2020"] = res["treated_homes_2020"] - res["treated_homes_2010"]
    res["salt_lake_city_homes_2010"] = slc
    res["treated_net_gain_share_of_city_pct"] = 100 * res["treated_net_homes_2010_2020"] / slc
    res.round(4).to_csv(REFERENCE / "tod_slc_census_results.csv", index=False)
    print(res.round(3).T.to_string())


if __name__ == "__main__":
    main()

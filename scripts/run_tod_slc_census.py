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

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import geom_extra_station as S  # noqa: E402
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


# Geometry without geopandas (docs/GEOMETRY.md): stations and block points are frames with x, y in CRS; zoning is a
# frame with "geometry" (polygon features).
def stations() -> pd.DataFrame:
    s = pd.DataFrame(json.load(open(D / "uta_stops.json")))
    s = s[s["stop_type_text"].str.contains("rail", case=False, na=False)]
    s["name"] = s["stop_name"].str.strip()
    s.loc[s["name"].str.upper() == "RIVER TRAIL STATION", "name"] = "River Trail Station"
    s = s.groupby("name", as_index=False)[["stop_lat", "stop_lon"]].mean()
    x, y = S.transform(s["stop_lon"].to_numpy(float), s["stop_lat"].to_numpy(float), 4326, CRS)
    return s.assign(x=x, y=y)


def blocks(year: int) -> pd.DataFrame:
    if year == 2010:
        b = S.read_vector(D / "tabblock2010_49_pophu.zip", CRS, columns=["BLOCKID10", "HOUSING10"])
        b = b.rename(columns={"BLOCKID10": "geoid", "HOUSING10": "homes"})
    else:
        b = S.read_vector(D / "tl_2020_49_tabblock20.zip", CRS, columns=["GEOID20", "HOUSING20"])
        b = b.rename(columns={"GEOID20": "geoid", "HOUSING20": "homes"})
    polys = list(b["geometry"])
    b["land"] = S.areas(polys)   # polygon area for both years (the 2010 file has no land-area field; plan section 8)
    b["x"], b["y"] = S.interior_points(polys)   # representative points (GEOS point on surface)
    return b[["geoid", "homes", "land", "x", "y"]]


def _inside(pts: pd.DataFrame, zones: pd.DataFrame) -> pd.Series:
    """Point within any of the polygons (spatial join 'within')."""
    k = S.first_within(pts["x"].to_numpy(float), pts["y"].to_numpy(float), list(zones["geometry"]))
    return pd.Series(k >= 0, index=pts.index)


def _min_distance(pts: pd.DataFrame, st: pd.DataFrame) -> pd.Series:
    """Distance from each point to the nearest of the stations."""
    if not len(st):
        return pd.Series(np.nan, index=pts.index)
    d, _ = cKDTree(st[["x", "y"]].to_numpy(float)).query(pts[["x", "y"]].to_numpy(float))
    return pd.Series(d, index=pts.index)


def assign(pts: pd.DataFrame, st: pd.DataFrame, tsa: pd.DataFrame) -> pd.Series:
    """Group of each block point: treated, comp1 (same line, not TSA), comp2 (new stations elsewhere), or none."""
    tsa_main = tsa[tsa["station"].isin(TSA_STATIONS)]
    in_tsa_main = _inside(pts, tsa_main)
    in_any_tsa = _inside(pts, tsa)
    s1 = st[st["name"].isin(TSA_STATIONS)]
    s2 = st[st["name"].isin(NEW_2011_2013)]
    d1 = _min_distance(pts, s1)
    d2 = _min_distance(pts, s2)
    g = pd.Series("none", index=pts.index)
    g[(d2 <= HALF)] = "comp2"
    g[(d1 <= HALF) & ~in_any_tsa] = "comp1"
    g[in_tsa_main] = "treated"
    return g, d1


def tsa_zones(st: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """TSA zoning polygons (frame with "geometry" in CRS) and the station nearest each one's representative point
    (sjoin_nearest; exact ties to the first station)."""
    z = S.read_vector(D / "slc_zoning_2020_jacobs.geojson", CRS)
    tsa = z[z["ZONING"].str.startswith("TSA")].copy()
    rx, ry = S.interior_points(list(tsa["geometry"]))
    k, _ = S.nearest_lowest(rx, ry, st["x"].to_numpy(float), st["y"].to_numpy(float))
    return tsa, pd.Series(st["name"].to_numpy()[k], index=tsa.index)


def main() -> None:
    st = stations()
    missing = [n for n in TSA_STATIONS + NEW_2011_2013 + LATER_TSA if n not in set(st["name"])]
    print("stations not found:", missing)
    tsa, near = tsa_zones(st)
    tsa["station"] = near
    tsa["core"] = tsa["ZONING"].str.endswith("-C")

    rows, area_rows = [], []
    data = {}
    for year in (2010, 2020):
        pts = blocks(year)
        sb = st[st["name"].isin(TSA_STATIONS + NEW_2011_2013)]
        bbox = (sb["x"].min(), sb["y"].min(), sb["x"].max(), sb["y"].max())
        pts = pts[pts["x"].between(bbox[0] - 3000, bbox[2] + 3000) & pts["y"].between(bbox[1] - 3000, bbox[3] + 3000)].copy()
        grp, d1 = assign(pts, st, tsa)
        core = _inside(pts, tsa[tsa["core"] & tsa["station"].isin(TSA_STATIONS)])
        pts["group"], pts["d1"], pts["core"] = grp, d1, core
        data[year] = pts[pts["group"] != "none"].drop(columns=["x", "y"])
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

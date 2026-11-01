"""Station-area lot table, step C (docs/tod/STATION_AREA_PLAN.md, LOCKED section and owner answers of 2026-11-01).

One row per lot within 1 mile of a reform stop or a comparison stop, for each case:
    band (0-1/4, 1/4-1/2, 1/2-1 mile) and exact distance to its nearest stop, whether that stop is a reform or a
    comparison stop, coverage of that stop's band (share of the band's existing homes on reform-area lots),
    homes on the lot before the window, new homes in the before and after windows, and lot traits.

New homes come from one source on both sides of each comparison (owner, 15:57): county year built where the county
file has it (LA County, San Diego County), city permits where the reform city's permit file covers the comparison stops
too (Honolulu: the city is the whole island). Lot tables stay local (data/processed/tod_station_area/); only summary
rates are written to reference/.

    uv run --all-extras python scripts/build_tod_station_lot_table.py --case la_toc_2017
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

CRS = 5070
QUARTER, HALF, MILE = 402.0, 805.0, 1609.0
OUT = ROOT / "data" / "processed" / "tod_station_area"
RP = RAW / "tod_radius_programs"

# windows fixed before counting (plan: LOCKED section and auditor fixes of 14:32)
CASES = {
    "la_toc_2017": {"metro": "la", "reform_city": "Los Angeles", "eff": 2017, "before": (2011, 2016), "after": (2018, 2022),
                    "comparison_cities": ["Pasadena", "Long Beach", "Santa Monica", "Culver City", "Glendale", "Burbank",
                                          "Inglewood", "South Pasadena", "Monrovia", "Arcadia", "Azusa", "Duarte", "Irwindale",
                                          "Norwalk", "Lakewood", "Compton", "Downey", "Hawthorne", "El Segundo", "Redondo Beach",
                                          "Lynwood", "Paramount", "Carson", "West Hollywood", "Bell Gardens", "Commerce"]},
    "san_diego_2021": {"metro": "sd", "reform_city": "San Diego", "eff": 2021, "before": (2015, 2020), "after": (2021, 2025),
                       "comparison_cities": ["Chula Vista", "National City", "La Mesa", "El Cajon", "Santee", "Lemon Grove"]},
    "honolulu_2017": {"metro": "hnl", "reform_city": "Urban Honolulu", "eff": 2017, "before": (2011, 2016), "after": (2018, 2022),
                      "after_v2": (2023, 2025), "comparison_cities": []},
}


# --------------------------------------------------------------------------- stops

def ntm_stations(box: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    """National transit map rail stops in a lon/lat box, merged into stations (platforms within 150 m are one station)."""
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    s = s[s.stop_lon.between(box[0], box[2]) & s.stop_lat.between(box[1], box[3])]
    g = gpd.GeoDataFrame(s[["stop_name", "stop_type_text"]], geometry=gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(CRS)
    if box[0] < -118.5:   # LA County: add the G Line (rapid bus on its own way), as in the stations stage
        gl = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_la_g_line.json")))
        gl = gpd.GeoDataFrame(gl[["stop_name"]].assign(stop_type_text="G Line (rapid)"),
                              geometry=gpd.points_from_xy(gl.stop_lon, gl.stop_lat), crs=4326).to_crs(CRS)
        g = pd.concat([g, gl], ignore_index=True)
    blobs = g.buffer(75).union_all()
    parts = list(blobs.geoms) if hasattr(blobs, "geoms") else [blobs]
    st = gpd.GeoDataFrame(geometry=[p.centroid for p in parts], crs=CRS)
    j = gpd.sjoin_nearest(st, g[["stop_name", "stop_type_text", "geometry"]], how="left").drop_duplicates(subset="geometry")
    return j.reset_index(drop=True)[["stop_name", "stop_type_text", "geometry"]]


def place_of(g: gpd.GeoDataFrame, state: str) -> pd.Series:
    p = gpd.read_file(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip")
    p = p[p.STATEFP == state].to_crs(CRS)[["NAME", "geometry"]]
    j = gpd.sjoin(g[["geometry"]], p, how="left", predicate="within")
    return j[~j.index.duplicated()]["NAME"].reindex(g.index)


# --------------------------------------------------------------------------- lots

def la_lots() -> gpd.GeoDataFrame:
    d = pd.read_csv(RP / "la" / "county_parcels.csv", low_memory=False)
    yb = [pd.to_numeric(d[f"YearBuilt{i}"], errors="coerce") for i in range(1, 6)]
    un = [pd.to_numeric(d[f"Units{i}"], errors="coerce").fillna(0) for i in range(1, 6)]
    L = pd.DataFrame({"city_name": d.SitusCity.astype(str).str.title().str.replace(r"\s+Ca$", "", regex=True),
                      "acres": pd.to_numeric(d["Shape.STArea()"], errors="coerce") / 43560.0,
                      "land_value": pd.to_numeric(d.Roll_LandValue, errors="coerce"),
                      "bldg_value": pd.to_numeric(d.Roll_ImpValue, errors="coerce"),
                      "land_base_year": pd.to_numeric(d.Roll_LandBaseYear, errors="coerce"),
                      "use": d.UseType.astype(str), "use_code": d.UseCode.astype(str), "public": d.AgencyType.notna() & (d.AgencyType.astype(str).str.strip() != ""),
                      "year_built": pd.concat(yb, axis=1).where(pd.concat(yb, axis=1) > 0).min(axis=1)})
    hotel = d.UseCode.astype(str).str.startswith("18")   # hotels and motels: the roll's unit count is rooms (hand check)
    L["_yb"] = list(zip(*[y.fillna(0).astype(int) for y in yb]))
    L["_un"] = [tuple(0.0 for _ in u) if h else u for u, h in zip(zip(*un), hotel)]
    return gpd.GeoDataFrame(L, geometry=gpd.points_from_xy(d.CENTER_LON, d.CENTER_LAT), crs=4326).to_crs(CRS)


def sd_lots() -> gpd.GeoDataFrame:
    d = pd.read_csv(RP / "san_diego" / "county_parcels.csv", low_memory=False)
    # the same building can appear on two records (e.g. a possessory-interest record beside the land parcel): keep one
    multi = pd.to_numeric(d.unitqty, errors="coerce").fillna(0) > 1
    dup = d[multi].duplicated(subset=[d.x_coord.round(0).name, d.y_coord.round(0).name, "unitqty", "year_effective"])
    d = d.drop(index=dup[dup].index)
    # condo master records (no land area, several homes) sit at the same point as the condo-unit parcels that also
    # carry those homes: drop the master where unit parcels at its point hold at least as many homes
    xy = d.x_coord.round(0).astype(str) + "_" + d.y_coord.round(0).astype(str)
    q = pd.to_numeric(d.unitqty, errors="coerce").fillna(0)
    singles = q.where(q == 1, 0).groupby(xy).sum()
    master = d.acreage.isna() & (q > 1) & (xy.map(singles) >= q)
    d = d[~master]
    yy = pd.to_numeric(d.year_effective, errors="coerce")
    yr = np.where(yy.between(1, 26), 2000 + yy, np.where(yy.between(27, 99), 1900 + yy, np.nan))   # "00" unknown
    L = pd.DataFrame({"city_name": d.situs_juris.astype(str), "acres": pd.to_numeric(d.acreage, errors="coerce"),
                      "land_value": pd.to_numeric(d.asr_land, errors="coerce"), "bldg_value": pd.to_numeric(d.asr_impr, errors="coerce"),
                      "use": d.asr_landuse.astype(str), "public": d.taxstat.astype(str).str.upper().eq("E"),
                      "year_built": yr})
    u = pd.to_numeric(d.unitqty, errors="coerce").fillna(0)
    u = u.where(~pd.to_numeric(d.asr_landuse, errors="coerce").isin([26, 44]), 0)   # hotels (26), self-storage (44): rooms/units, not homes
    L["_yb"] = [(int(y) if y == y else 0,) for y in yr]
    L["_un"] = [(float(x),) for x in u]
    # SANDAG coordinates are state plane (feet), NAD83 California zone 6
    return gpd.GeoDataFrame(L, geometry=gpd.points_from_xy(d.x_coord, d.y_coord), crs=2230).to_crs(CRS)


def hnl_lots() -> gpd.GeoDataFrame:
    P = gpd.read_file(RP / "honolulu" / "parcels.geojson").to_crs(CRS)
    v = pd.read_csv(RP / "honolulu" / "assessed_values.csv", low_memory=False)
    vv = v.groupby("tmk")[["landvalue", "buildingvalue"]].sum()   # condo units (suffixes) summed to their parcel
    P["k"] = pd.to_numeric(P.tmk8num, errors="coerce")
    P = P.drop_duplicates("k")
    L = gpd.GeoDataFrame({"city_name": "Honolulu", "acres": pd.to_numeric(P.gisacres, errors="coerce"),
                          "land_value": P.k.map(vv.landvalue), "bldg_value": P.k.map(vv.buildingvalue),
                          "use": "", "public": False, "year_built": np.nan, "tmk8": P.k},
                         geometry=P.geometry.representative_point(), crs=CRS)
    L["_yb"] = [()] * len(L)
    L["_un"] = [()] * len(L)
    return L


def homes_between(L: pd.DataFrame, a: int, b: int) -> pd.Series:
    return pd.Series([sum(u for y, u in zip(ys, us) if a <= y <= b) for ys, us in zip(L["_yb"], L["_un"])], index=L.index, dtype=float)


def homes_before(L: pd.DataFrame, a: int) -> pd.Series:
    """Homes standing before the window: all homes on the lot except those built in or after its first year
    (buildings with an unknown year count as existing)."""
    return pd.Series([sum(u for y, u in zip(ys, us) if not (y >= a)) for ys, us in zip(L["_yb"], L["_un"])], index=L.index, dtype=float)


def implausible(D: pd.DataFrame) -> pd.Series:
    """New-home counts that cannot be right on their face: more than 2,000 new homes per acre (twice the densest towers
    in these cities), which catches the LA roll's placeholder counts (999, 1,001, 1,003 on small lots). Building value is
    not used: LA's roll often carries new buildings at a partial (in-construction) value. These lots are left out of the
    rates and listed; every lot with 100 or more new homes is also listed for a hand check."""
    new = D[["homes_before_win", "homes_after_win"]].max(axis=1)
    dense = (new / D.acres.where(D.acres > 0)) > 2000
    return dense.fillna(False) & (new >= 20)


def blocks_to_lots(D: gpd.GeoDataFrame, zip_path: Path) -> pd.Series:
    """2010 census block housing counts spread equally over the lots inside each block (lots outside any block get 0)."""
    b = gpd.read_file(f"zip://{zip_path}", bbox=tuple(D.to_crs(4269).total_bounds)).to_crs(CRS)
    hu = b.columns[b.columns.str.upper() == "HOUSING10"][0]
    j = gpd.sjoin(D[["geometry"]], b[[hu, "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    n = j.groupby("index_right").size()
    return (j[hu] / j.index_right.map(n)).reindex(D.index).fillna(0).astype(float)


# --------------------------------------------------------------------------- build

def build(case: str) -> pd.DataFrame:
    c = CASES[case]
    if c["metro"] == "la":
        box, state = (-118.95, 33.70, -117.65, 34.35), "06"
        reform_area = gpd.read_file(RP / "la" / "toc_tiers_oct2017.geojson").to_crs(CRS)
        L = la_lots()
    elif c["metro"] == "sd":
        box, state = (-117.30, 32.53, -116.90, 32.95), "06"
        reform_area = gpd.read_file(RP / "san_diego" / "transit_priority_areas_sandag_2022.geojson").to_crs(CRS)
        L = sd_lots()
    else:
        box, state = (-158.3, 21.25, -157.6, 21.75), "15"
        reform_area = pd.concat([gpd.read_file(RP / "honolulu" / f) for f in ("tod_zone_change_waipahu_tc.geojson", "tod_zone_change_west_loch.geojson")]).to_crs(CRS)
        L = hnl_lots()
    area = reform_area.union_all()

    if c["metro"] == "hnl":
        r = gpd.read_file(RP / "honolulu" / "rail_stations.geojson").to_crs(CRS)
        S = gpd.GeoDataFrame({"stop_name": r.station_name_FEIS, "stop_type_text": "Rail (opened 2023 or later)"}, geometry=r.geometry, crs=CRS)
        S["group"] = np.where(S.stop_name.str.contains("Waipahu Transit|West Loch"), "reform", "comparison")
        S["place"] = "Urban Honolulu"
    else:
        S = ntm_stations(box)
        S["place"] = place_of(S, state)
        S["group"] = np.where(S.place == c["reform_city"], "reform", np.where(S.place.isin(c["comparison_cities"]), "comparison", "other"))
        S = S[S.group != "other"].reset_index(drop=True)
    S["stop_id"] = np.arange(len(S))

    # lots within 1 mile of any kept stop
    near = gpd.sjoin_nearest(L[["geometry"]], S[["stop_id", "group", "geometry"]], how="inner", max_distance=MILE, distance_col="dist_m")
    near = near[~near.index.duplicated()]
    D = L.loc[near.index].copy()
    D[["stop_id", "group", "dist_m"]] = near[["stop_id", "group", "dist_m"]]
    D["band"] = pd.cut(D.dist_m, [-1, QUARTER, HALF, MILE], labels=["0-1/4", "1/4-1/2", "1/2-1"]).astype(str)
    D["in_reform_area"] = D.within(area) if hasattr(D, "within") else False

    b0, b1 = c["before"]; a0, a1 = c["after"]
    if c["metro"] == "hnl":   # permits on both sides (the permit file is island-wide)
        import run_tod_station_area as SA
        p = SA.hnl_permits()
        pj = gpd.sjoin_nearest(p, D[["geometry"]], how="inner", max_distance=60, distance_col="_d")
        pj = pj[~pj.index.duplicated()]
        for lab, (x, y) in {"homes_before_win": (b0, b1), "homes_after_win": (a0, a1)}.items():
            w = pj[pj.year.between(x, y)]
            D[lab] = w.groupby("index_right").units.sum().reindex(D.index).fillna(0)
        if "after_v2" in c:
            w = pj[pj.year.between(*c["after_v2"])]
            D["homes_after_v2"] = w.groupby("index_right").units.sum().reindex(D.index).fillna(0)
        D["homes_existing"] = blocks_to_lots(D, RAW / "tod_census_cases" / "tabblock2010_15_pophu.zip")
        D["source"] = "city permits (both sides); existing homes from 2010 census blocks spread over each block's lots"
    else:
        D["homes_before_win"] = homes_between(D, b0, b1)
        D["homes_after_win"] = homes_between(D, a0, a1)
        D["homes_existing"] = homes_before(D, b0)
        D["source"] = "county year built (both sides)"
    D["case"] = case
    D["implausible"] = implausible(D)
    apply_hand_check(D, case)
    EVENTS[case] = events(D, c)
    return D, S


EVENTS: dict[str, pd.DataFrame] = {}


def events(D: gpd.GeoDataFrame, c: dict) -> pd.DataFrame:
    """One row per new-building record from 2000 on (owner, 17:33: keep permit and completion dates side by side and
    compute windows later). Completion rows come from county year built (buildings 1-5 on LA lots); permit rows from
    the city permit file where one exists (LA city side, Honolulu). Records are not matched across the two sources:
    each row has one date; `preferred` names the date type used on both sides of the comparison for that case."""
    rows = []
    if "_yb" in D and D["_yb"].map(len).sum():
        for ix, ys, us in zip(D.index, D["_yb"], D["_un"]):
            for y, u in zip(ys, us):
                if y >= 2000 and u > 0:
                    rows.append((ix, float(u), np.nan, float(y), "county year built"))
    pref = "completed"
    if c["metro"] in ("la", "hnl"):
        import run_tod_station_area as SA
        p = SA.permits("Los Angeles") if c["metro"] == "la" else SA.hnl_permits()
        p = p[p.year >= 2000]
        pj = gpd.sjoin_nearest(p, D[["geometry"]], how="inner", max_distance=60, distance_col="_d")
        pj = pj[~pj.index.duplicated()]
        rows += [(ix, float(u), float(y), np.nan, "city permits") for ix, u, y in zip(pj.index_right, pj.units, pj.year)]
        if c["metro"] == "hnl":
            pref = "permit"
    E = pd.DataFrame(rows, columns=["lot_index", "homes", "permit_year", "completed_year", "source"])
    E["preferred"] = pref
    E["hand_check"] = E.lot_index.map(D.get("hand_check", pd.Series(dtype=str)))
    return E


def apply_hand_check(D: pd.DataFrame, case: str) -> None:
    """Corrections from the hand check of every lot with 100+ new homes (data/processed/tod_station_area/
    hand_check_big_lots.csv): 'wrong count' rows take the corrected number, 'duplicate' rows go to 0; 'unverifiable'
    rows are flagged (column hand_check) so the rates can be shown with and without them."""
    f = OUT / "hand_check_big_lots.csv"
    D["hand_check"] = ""
    if not f.exists():
        return
    h = pd.read_csv(f)
    h = h[(h.case == case) & h.lot_index.isin(D.index)]
    for _, r in h.iterrows():
        col = "homes_after_win" if r["window"] == "after" else "homes_before_win"
        D.loc[r["lot_index"], "hand_check"] = r["class"]
        if r["class"] == "duplicate":
            D.loc[r["lot_index"], col] = 0.0
        elif r["class"] == "wrong count" and pd.notna(r["homes_corrected"]):
            D.loc[r["lot_index"], col] = float(r["homes_corrected"])


def rates(D: pd.DataFrame, years_b: int, years_a: int) -> pd.DataFrame:
    D = D[~D.implausible]
    g = D.groupby(["group", "band"]).agg(lots=("band", "size"), homes_existing=("homes_existing", "sum"),
                                          new_before=("homes_before_win", "sum"), new_after=("homes_after_win", "sum"),
                                          coverage=("in_reform_area", "mean"))
    g["rate_before"] = 1000 * g.new_before / years_b / g.homes_existing
    g["rate_after"] = 1000 * g.new_after / years_a / g.homes_existing
    g["change"] = g.rate_after - g.rate_before
    return g


def adapter_cases() -> dict:
    """Cases built by modules in scripts/station_cases/ (one module per group of cities). Each module defines
    CASES = {case: {"before": (y0, y1), "after": (y0, y1), ...}} and build(case) -> (D, S) in this file's schema."""
    import importlib
    out = {}
    for f in sorted((ROOT / "scripts" / "station_cases").glob("*.py")):
        if f.stem.startswith("_"):
            continue
        m = importlib.import_module(f"station_cases.{f.stem}")
        out.update({k: (m, v) for k, v in m.CASES.items()})
    return out


def main(argv=None) -> None:
    ext = adapter_cases()
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=list(CASES) + list(ext), required=True)
    a = ap.parse_args(argv)
    if a.case in ext:
        mod, cfg = ext[a.case]
        D, S = mod.build(a.case)
        CASES[a.case] = cfg
        D["implausible"] = D.get("implausible", False) | implausible(D)
    else:
        D, S = build(a.case)
    OUT.mkdir(parents=True, exist_ok=True)
    D.drop(columns=[c for c in ("_yb", "_un") if c in D]).assign(x=D.geometry.x, y=D.geometry.y).drop(columns="geometry").to_parquet(OUT / f"lots_{a.case}.parquet")
    ev = EVENTS.get(a.case)
    if ev is None and a.case in ext:
        ev = getattr(ext[a.case][0], "EVENTS", {}).get(a.case)
    if ev is not None:
        ev.to_parquet(OUT / f"events_{a.case}.parquet")
        print(f"events: {len(ev):,} rows; homes by date type: permit {ev.loc[ev.permit_year.notna(), 'homes'].sum():,.0f}, "
              f"completed {ev.loc[ev.completed_year.notna(), 'homes'].sum():,.0f}")
    c = CASES[a.case]
    print(S.groupby(["group", "place"]).size().to_string())
    bad = D[D.implausible]
    print(f"implausible lots left out: {len(bad)}; homes after {bad.homes_after_win.sum():.0f}, before {bad.homes_before_win.sum():.0f}")
    print(bad[["city_name", "group", "band", "homes_before_win", "homes_after_win", "acres", "bldg_value"]].head(15).to_string())
    big = D[(D[["homes_before_win", "homes_after_win"]].max(axis=1) >= 100) & ~D.implausible]
    print(f"lots with 100+ new homes (hand-check list): {len(big)}; share of all new homes {big[['homes_before_win','homes_after_win']].sum().sum() / D[['homes_before_win','homes_after_win']].sum().sum():.2f}")
    print(rates(D, c["before"][1] - c["before"][0] + 1, c["after"][1] - c["after"][0] + 1).round(2).to_string())


if __name__ == "__main__":
    main()

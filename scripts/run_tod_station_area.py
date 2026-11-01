"""TOD station-area measure (docs/tod/STATION_AREA_PLAN.md; pre-registration items 1-10).

    uv run --all-extras python scripts/run_tod_station_area.py --stage stations    # fixed and committed first
    uv run --all-extras python scripts/run_tod_station_area.py --stage inventory   # citywide permit sources, committed first
    uv run --all-extras python scripts/run_tod_station_area.py --stage shares      # counts (only after both are committed)

Stations: every rail or rapid stop inside the city (national transit map rail stops, the Los Angeles G Line and
Wisconsin's rapid stops). Reform stations: stops within 1/2 mile of the reform's upzoned land. Control stations:
the city's other stops. Downtown: within 1 mile of city hall.
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
HALF, MILE = 805.0, 1609.0
# city: (census place name, state FIPS, city hall lat, lon)  -- city hall points from each city's official address
CITIES = {
    "New York": ("New York", "36", 40.7128, -74.0060), "Philadelphia": ("Philadelphia", "42", 39.9524, -75.1636),
    "Charlotte": ("Charlotte", "37", 35.2214, -80.8395), "Saint Paul": ("St. Paul", "27", 44.9440, -93.0936),
    "Seattle": ("Seattle", "53", 47.6036, -122.3294), "Los Angeles": ("Los Angeles", "06", 34.0537, -118.2428),
    "Chicago": ("Chicago", "17", 41.8837, -87.6319), "Madison": ("Madison", "55", 43.0731, -89.3841),
    "Bellevue": ("Bellevue", "53", 47.6145, -122.1913), "Denver": ("Denver", "08", 39.7392, -104.9903),
    "Portland": ("Portland", "41", 45.5152, -122.6784), "Austin": ("Austin", "48", 30.2650, -97.7470),
    "Salt Lake City": ("Salt Lake City", "49", 40.7608, -111.8910), "Milwaukee": ("Milwaukee", "55", 43.0417, -87.9090),
}


def stops() -> gpd.GeoDataFrame:
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    s = s.assign(name=s.stop_name, src="national transit map rail stops")[["name", "stop_lat", "stop_lon", "src"]]
    g = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_la_g_line.json")))
    g = g.assign(name=g.stop_name, src="LA Metro G Line (rapid)")[["name", "stop_lat", "stop_lon", "src"]]
    w = pd.read_csv(REFERENCE / "tod_stops.csv")
    w = w[w.flag_a_rapid == 1].rename(columns={"lat": "stop_lat", "lon": "stop_lon"}).assign(name=lambda x: x.stop_id.astype(str), src="Wisconsin rapid stops")
    # the national rail-stop extract holds the case cities only; Denver and Portland come from their cities' layers
    dn = gpd.read_file(RAW / "tod_new_cities" / "denver" / "rail_stations.geojson")
    dn = dn[dn.STATUS == "Existing"]
    dn = pd.DataFrame({"name": dn.STATION_NAME, "stop_lat": dn.geometry.y, "stop_lon": dn.geometry.x, "src": "Denver rail stations (RTD)"})
    pdx = pd.concat([gpd.read_file(RAW / "tod_new_cities" / "portland" / f) for f in ("max_stops.geojson", "streetcar_stops.geojson")], ignore_index=True).to_crs(4326)
    nm = next(c for c in pdx.columns if c.upper() in ("STATION", "NAME", "STOP_NAME", "STOPNAME", "LOCATION"))
    pdx = pd.DataFrame({"name": pdx[nm].astype(str), "stop_lat": pdx.geometry.y, "stop_lon": pdx.geometry.x, "src": "Portland MAX and Streetcar (TriMet)"})
    a = pd.concat([s, g, w[["name", "stop_lat", "stop_lon", "src"]], dn, pdx], ignore_index=True)
    return gpd.GeoDataFrame(a, geometry=gpd.points_from_xy(a.stop_lon, a.stop_lat), crs=4326).to_crs(CRS)


def places() -> gpd.GeoDataFrame:
    p = gpd.read_file(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip")
    out = []
    for city, (name, st, *_ ) in CITIES.items():
        m = p[(p.NAME == name) & (p.STATEFP == st)]
        out.append(m.assign(city=city)[["city", "geometry"]])
    return pd.concat(out).to_crs(CRS)


def upzoned_points() -> dict[str, list[tuple[str, gpd.GeoSeries]]]:
    """Upzoned land by city and case, as points or polygons (CRS 5070)."""
    import run_tod_lot_model as L
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet", columns=["city", "unit", "treated", "x5070", "y5070"])
    D = D[(D.treated == 1) & ~D.city.str.endswith("placebo")]
    out: dict = {}
    for (c, u), g in D.groupby(["city", "unit"]):
        out.setdefault(c, []).append((str(u), gpd.GeoSeries(gpd.points_from_xy(g.x5070, g.y5070), crs=CRS)))
    z = gpd.read_file(RAW / "tod_new_cities" / "denver" / "zone_map_amendments.geojson").to_crs(CRS)
    out["Denver"] = [("denver_2018", z[(z.ORD_YEAR == 2018) & z.ORD_NUM.isin([15, 17])].geometry)]
    import run_tod_new_city_test as N
    b = gpd.read_file(RAW / "tod_new_cities" / "portland" / "bhd_zone_changes.geojson").to_crs(CRS)
    b = b[b.pr_zone.map(N.PDX_HPA) > b.ex_zone.map(N.PDX_HPA)]
    out["Portland"] = [("portland_2020", b.geometry)]
    a = gpd.read_file(REFERENCE / "tod_austin_dayone_regulating_plans.geojson").to_crs(CRS)
    out["Austin"] = [("austin_2009", a[a.SUBDISTRICT_MAP != "TROW"].geometry)]
    sl = gpd.read_file(RAW / "tod_slc" / "slc_zoning_2020_jacobs.geojson").to_crs(CRS)
    out["Salt Lake City"] = [("slc_2010", sl[sl.ZONING.str.startswith("TSA")].geometry)]
    return out


def stage_stations() -> None:
    st, pl = stops(), places()
    up = upzoned_points()
    rows = []
    for city, (_, _, hlat, hlon) in CITIES.items():
        poly = pl[pl.city == city].geometry.union_all()
        s = st[st.within(poly)].drop_duplicates(subset=["name"]).copy()
        hall = gpd.GeoSeries(gpd.points_from_xy([hlon], [hlat]), crs=4326).to_crs(CRS).iloc[0]
        s["downtown"] = s.distance(hall) <= MILE
        cases = up.get(city, [])
        for case, geo in cases or [("none", None)]:
            if geo is None or not len(geo):
                role = pd.Series("control", index=s.index)
            else:
                u = geo.union_all()
                role = np.where(s.distance(u) <= HALF, "reform", "control")
            for (_, r), rl in zip(s.iterrows(), role):
                rows.append({"city": city, "case": case, "stop": r["name"], "source": r["src"], "role": rl,
                             "downtown": bool(r["downtown"]), "lat": round(float(gpd.GeoSeries([r.geometry], crs=CRS).to_crs(4326).y.iloc[0]), 6),
                             "lon": round(float(gpd.GeoSeries([r.geometry], crs=CRS).to_crs(4326).x.iloc[0]), 6)})
    T = pd.DataFrame(rows)
    T.to_csv(REFERENCE / "tod_station_area_stations.csv", index=False)
    print(T.groupby(["city", "role"]).stop.nunique().unstack(fill_value=0).to_string())


# ---------------------------------------------------------------- shares
TC = RAW / "tod_cases"


def _pts(df, x, y, crs=4326):
    df = df.dropna(subset=[x, y, "year"]).copy()
    df = df[(pd.to_numeric(df[x], errors="coerce").notna()) & (pd.to_numeric(df[y], errors="coerce").notna())]
    g = gpd.GeoDataFrame(df[["year", "units"]], geometry=gpd.points_from_xy(df[x].astype(float), df[y].astype(float)), crs=crs)
    return g.to_crs(CRS)


def permits(city: str) -> gpd.GeoDataFrame | None:
    """Citywide new homes by year, as points (CRS 5070): columns year, units. None where no citywide file exists."""
    if city == "New York":
        d = pd.read_csv(TC / "nyc" / "dob_nb_all.csv", low_memory=False)
        d = d[d.job_type == "NB"]
        d["units"] = pd.to_numeric(d.proposed_dwelling_units, errors="coerce").fillna(0)
        d["year"] = pd.to_numeric(d.fully_permitted.astype(str).str[-4:], errors="coerce")
        d = d.drop_duplicates(subset=["job__"])
        return _pts(d[d.units > 0], "gis_longitude", "gis_latitude")
    if city == "Philadelphia":
        d = pd.read_csv(TC / "philadelphia" / "permits_new_construction.csv", low_memory=False)
        d["units"] = pd.to_numeric(d.numberofunits, errors="coerce").fillna(0)
        d["year"] = pd.to_numeric(d.permitissuedate.astype(str).str[:4], errors="coerce")
        return _pts(d[d.units > 0], "lon", "lat")
    if city == "Charlotte":
        from missing_middleware.tod import case_charlotte as CC
        d = CC.load_permits()
        return _pts(d, "X", "Y", crs=2264)
    if city == "Saint Paul":
        g = gpd.read_file(TC / "stpaul" / "housing_production.geojson").to_crs(CRS)
        g["units"] = pd.to_numeric(g.NewDwellingUnits, errors="coerce").fillna(0)
        g["year"] = pd.to_numeric(g.ProjectPermitIssueYear, errors="coerce")
        return g[g.units > 0][["year", "units", "geometry"]]
    if city == "Seattle":
        d = pd.read_csv(TC / "seattle" / "permits_new_units.csv", low_memory=False)
        d["units"] = pd.to_numeric(d.housingunitsadded, errors="coerce").fillna(0)
        d["year"] = pd.to_datetime(d.issueddate, errors="coerce").dt.year
        return _pts(d[d.units > 0], "longitude", "latitude")
    if city == "Chicago":
        from missing_middleware.tod import case_chicago as CH
        d = pd.read_csv(TC / "chicago" / "permits_new_construction.csv", low_memory=False)
        d["units"] = d.work_description.map(CH.parse_units)
        d["year"] = pd.to_datetime(d.issue_date, errors="coerce").dt.year
        return _pts(d[d.units > 0], "longitude", "latitude")
    if city == "Bellevue":
        g = gpd.read_file(TC / "bellevue" / "permits_units.geojson").to_crs(CRS)
        g["units"] = pd.to_numeric(g.DWELLINGUNITSCREATED, errors="coerce").fillna(0)
        g["year"] = pd.to_datetime(g.ISSUEDDATE, errors="coerce", utc=True).dt.year
        return g[g.units > 0][["year", "units", "geometry"]]
    import run_tod_new_city_test as N
    if city == "Denver":
        d = RAW / "tod_new_cities" / "denver"
        g = pd.concat([gpd.read_file(d / "residential_permits.geojson"), gpd.read_file(d / "commercial_permits.geojson")], ignore_index=True)
        g["units"] = pd.to_numeric(g.UNITS, errors="coerce").fillna(0)
        g = g[g.CLASS.str.upper().eq("NEW BUILDING") & (g.units > 0) & g.CANCEL.isna() & g.geometry.notna()].to_crs(CRS)
        g["year"] = pd.to_datetime(g.DATE_ISSUED, unit="ms").dt.year
        return g[["year", "units", "geometry"]]
    if city == "Portland":
        d = RAW / "tod_new_cities" / "portland"
        g = pd.concat([gpd.read_file(d / "residential_permits.geojson"), gpd.read_file(d / "commercial_permits.geojson")], ignore_index=True)
        g["units"] = pd.to_numeric(g.NUMNEWUNITS, errors="coerce").fillna(0)
        g = g[(g.units > 0) & g.geometry.notna()].to_crs(CRS)
        g["year"] = pd.to_datetime(g.ISSUED, unit="ms").dt.year
        return g[["year", "units", "geometry"]]
    if city == "Austin":
        pm = pd.read_json(RAW / "tod_new_cities" / "austin" / "permits.json").dropna(subset=["latitude", "longitude"])
        pm["units"] = pd.to_numeric(pm.housing_units, errors="coerce").fillna(0)
        pm["year"] = pd.to_datetime(pm.issue_date).dt.year
        return _pts(pm[pm.units > 0], "longitude", "latitude")
    if city == "Salt Lake City":
        h = gpd.read_file(RAW / "tod_new_cities" / "slc" / "housing_unit_inventory.geojson").to_crs(CRS)
        h = h[h.geometry.notna()]
        return gpd.GeoDataFrame({"year": pd.to_numeric(h.APX_BLT_YR, errors="coerce"), "units": pd.to_numeric(h.UNIT_COUNT, errors="coerce").fillna(0)},
                                geometry=h.geometry.representative_point(), crs=CRS).query("units > 0")
    if city == "San Diego":
        return sd_permits()
    if city == "Los Angeles":
        # whole-city LADBS new-building permits (step B); 0.2% (2011-16) and 1.3% (2018-22) of homes lack a location
        d = pd.concat([pd.read_csv(RAW / "tod_radius_programs" / "la" / f"permits_citywide_{x}.csv", low_memory=False)
                       for x in ("e67z-kt2n", "dyxf-7hc4", "pi9x-tg5x")]).drop_duplicates("permit_nbr")
        d["units"] = pd.to_numeric(d.du_changed, errors="coerce").fillna(0)
        d["year"] = pd.to_datetime(d.issue_date, errors="coerce").dt.year
        return _pts(d[d.units > 0], "lon", "lat")
    return None   # Los Angeles (reform areas only), Madison (address placement needed): flagged


SD_SKIP_STATUS = "Cancel|Created|Opened|Expired|Void|Withdrawn"
SD_NOT_HOMES = "No Chg|Acc Struct|Pool|Spa"


def sd_permits() -> gpd.GeoDataFrame:
    """San Diego city Housing Element permit layer, cleaned (STATION_AREA_PLAN, step B):
    issued permits only; new-home job codes only; one home per one-family permit, two per two-family,
    four per three-or-four-family (the legacy system sometimes stores the whole subdivision on each permit);
    one row per approval id."""
    d = pd.DataFrame(json.load(open(RAW / "tod_radius_programs" / "san_diego" / "permits.json")))
    d["year"] = pd.to_datetime(d.APPROVAL_ISSUE_DATE, unit="ms").dt.year
    job = d.JOB_BC_CODE_DESCRIPTION.fillna("")
    keep = (~d.APPROVAL_STATUS.str.contains(SD_SKIP_STATUS, case=False, na=False)
            & job.str.contains("Family|Increase DU", case=False) & ~job.str.contains(SD_NOT_HOMES, case=False))
    d = d[keep].drop_duplicates("APPROVAL_ID").copy()
    j = d.JOB_BC_CODE_DESCRIPTION
    cap = np.select([j.str.contains("One Family"), j.str.contains("Two [Ff]amily"), j.str.contains("Three or Four")], [1, 2, 4], np.inf)
    d["units"] = np.minimum(pd.to_numeric(d.TOTAL_DU, errors="coerce").fillna(0), cap)
    return _pts(d[d.units > 0], "LNG_JOB", "LAT_JOB")


def case_windows() -> list[dict]:
    """Reform date and year windows per case (lot-model windows for the 9 cities; NEW_REFORM_CITIES_PLAN for the rest)."""
    import run_tod_lot_model as L
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet", columns=["city", "unit", "eff_year", "window_first", "window_last", "placebo"])
    D = D[D.placebo != 1].drop_duplicates(["city", "unit"])
    rows = [{"city": r.city, "case": str(r.unit), "eff": int(r.eff_year), "b0": int(r.window_first), "b1": int(r.eff_year) - 1,
             "a0": int(r.eff_year) + 1, "a1": int(r.window_last)} for r in D.itertuples()]
    rows += [{"city": "Denver", "case": "denver_2018", "eff": 2018, "b0": 2013, "b1": 2017, "a0": 2019, "a1": 2023},
             {"city": "Portland", "case": "portland_2020", "eff": 2020, "b0": 2014, "b1": 2019, "a0": 2021, "a1": 2025},
             {"city": "Austin", "case": "austin_2009", "eff": 2009, "b0": 2003, "b1": 2008, "a0": 2010, "a1": 2014},
             {"city": "Salt Lake City", "case": "slc_2010", "eff": 2010, "b0": 2004, "b1": 2009, "a0": 2011, "a1": 2015}]
    return rows


def stage_shares() -> None:
    from scipy.spatial import cKDTree
    S = pd.read_csv(REFERENCE / "tod_station_area_stations.csv")
    out = []
    cache: dict = {}
    for w in case_windows():
        c = w["city"]
        if c not in cache:
            cache[c] = permits(c)
            print(c, "permits:", None if cache[c] is None else len(cache[c]), flush=True)
        P = cache[c]
        st = S[(S.city == c) & (S.case == w["case"])]
        row = {**w, "reform_stops": int((st.role == "reform").sum()), "control_stops": int((st.role == "control").sum())}
        if P is None or st.empty:
            out.append({**row, "flag": "no citywide permits" if P is None else "no station list"})
            continue
        g = gpd.GeoSeries(gpd.points_from_xy(st.lon, st.lat), crs=4326).to_crs(CRS)
        tree = cKDTree(np.c_[g.x, g.y])
        dist, idx = tree.query(np.c_[P.geometry.x, P.geometry.y])
        near = dist <= HALF
        role = np.where(near, st.role.values[idx], "none")         # a home within 1/2 mile of both goes to the nearest stop
        dt = np.where(near, st.downtown.values[idx], False)
        for ver, keep in (("with_downtown", np.ones(len(P), bool)), ("without_downtown", ~dt)):
            r = {**row, "version": ver}
            for k, (y0, y1) in (("before", (w["b0"], w["b1"])), ("after", (w["a0"], w["a1"]))):
                m = P.year.between(y0, y1).values
                tot = float(P.units.values[m].sum())     # denominator: the whole city, downtown included in both versions
                r[f"homes_{k}"] = tot
                r[f"years_{k}"] = y1 - y0 + 1
                for rl in ("reform", "control"):
                    h = float(P.units.values[m & (role == rl) & keep].sum())
                    r[f"{rl}_homes_{k}"] = h
                    r[f"S_{rl}_{k}"] = h / tot if tot > 0 else np.nan
            r["dS_reform"] = r["S_reform_after"] - r["S_reform_before"]
            r["dS_control"] = r["S_control_after"] - r["S_control_before"]
            r["effect"] = r["dS_reform"] - r["dS_control"]
            out.append(r)
    T = pd.DataFrame(out)
    T.round(5).to_csv(REFERENCE / "tod_station_area_shares.csv", index=False)
    m = T[T.get("version") == "with_downtown"]
    city = m.groupby("city")[["S_reform_before", "S_reform_after", "dS_reform", "dS_control", "effect"]].mean()
    pd.set_option("display.width", 200)
    print(city.round(3).to_string())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["stations", "inventory", "shares"], required=True)
    a = ap.parse_args(argv)
    {"stations": stage_stations, "shares": stage_shares}[a.stage]()


if __name__ == "__main__":
    main()

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


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["stations", "inventory", "shares"], required=True)
    a = ap.parse_args(argv)
    {"stations": stage_stations}[a.stage]()


if __name__ == "__main__":
    main()

"""City transit coverage for the TOD net-effect work (docs/tod/NET_EFFECT_PLAN.md section 4, "City coverage").

    uv run --all-extras python scripts/build_tod_net_coverage.py --fetch   # downloads (network)
    uv run --all-extras python scripts/build_tod_net_coverage.py           # build from data/raw/tod_net_coverage/

For each comparison city (New York, Philadelphia, Charlotte, Saint Paul, Los Angeles, Seattle, Chicago, Madison) the
covered area is the union of 1/2-mile circles around rail and rapid-transit stops and 1/4-mile circles around stops of
15-minute buses, with the Wisconsin stop rules of missing_middleware/tod/transit.py:

- Rail and rapid: BTS National Transit Map (NTM) stops whose stop type is a rail route type (transit.RAIL_ROUTE_TYPES),
  Amtrak excluded (transit.is_excluded_agency), plus GTFS stops of rail route types in the city's own feeds, plus the
  named rapid bus routes in RAPID (Los Angeles Metro G Line). Madison: the Wisconsin layer's rapid flag (Route A).
- 15-minute bus: a route qualifies when one direction has >= 4 trips starting in each of the 7:00 and 8:00 hours on a
  representative Tuesday to Thursday (transit.representative_weekday, transit.route_peak_trips, transit.qualifies).
  Outside Wisconsin there are no NTM route lines matched to these feeds, so a stop qualifies when a trip of a qualifying
  route serves it on that day (GTFS stop_times), not by the 30 m line rule. Madison: the Wisconsin layer
  (reference/tod_stops.csv, flag_b_15min), which uses Madison's route descriptions (AQ-045).
- Feeds are today's (no scriptable archive of historical GTFS without an account was found; the OpenMobilityData S3
  archive refuses listing). NTM stops are the current compilation. Recorded per city (plan section 7).
- City boundary: TIGER/Line 2010 places (2010 reform era) for the seven cities outside Wisconsin; Madison: TIGER 2024.
  Land = the place less TIGER 2024 area water of its counties.
- Homes: 2010 Census block housing units (HOUSING10); Madison 2020 blocks (HOUSING20). A block counts as covered when
  its representative point (2010) or internal point (2020) lies in the covered area; homes in the city = blocks whose
  point lies in the place.

Outputs (git-ignored, data/processed/tod_net_effect/):
- coverage_<slug>.gpkg: layer "patches" (one row per connected covered patch inside the city, EPSG:4326, with patch
  acres and land acres) and layer "city" (the boundary).
- coverage_cities.csv: one row per city, every share with its numerator and denominator.
Use covered_patches(slug) to read a city's patches in a metre CRS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE, processed_dir  # noqa: E402
from missing_middleware.tod import transit as TR  # noqa: E402

D = RAW / "tod_net_coverage"
OUT = processed_dir("tod_net_effect")
HALF_M, QUARTER_M = 0.5 * TR.MILE_M, 0.25 * TR.MILE_M
SQM_PER_ACRE = 4046.8564224
UA = {"User-Agent": "missing-middleware research (housing policy model)"}
CENSUS = "Public domain (U.S. government work)"
NTM_LICENCE = "CC BY 3.0 US (BTS National Transit Map stops layer)"

CITIES = {
    "new_york": {"city": "New York", "st": "36", "place": "3651000", "counties": ["005", "047", "061", "081", "085"],
                 "feeds": {"bronx_bus": ("https://files.mobilitydatabase.org/mdb-528/latest.zip", "MTA New York City Transit Bronx bus (Mobility Database copy, mdb-528)"),
                           "brooklyn_bus": ("https://files.mobilitydatabase.org/mdb-512/latest.zip", "MTA New York City Transit Brooklyn bus (mdb-512)"),
                           "manhattan_bus": ("https://files.mobilitydatabase.org/mdb-513/latest.zip", "MTA New York City Transit Manhattan bus (mdb-513)"),
                           "queens_bus": ("https://files.mobilitydatabase.org/mdb-520/latest.zip", "MTA New York City Transit Queens bus (mdb-520)"),
                           "staten_island_bus": ("https://files.mobilitydatabase.org/mdb-514/latest.zip", "MTA New York City Transit Staten Island bus (mdb-514)"),
                           "mta_bus_company": ("https://files.mobilitydatabase.org/mdb-510/latest.zip", "MTA Bus Company (mdb-510)")},
                 "terms": "MTA developer data terms (web.mta.info/developers/developer-data-terms.html)"},
    "philadelphia": {"city": "Philadelphia", "st": "42", "place": "4260000", "counties": ["101"],
                     "feeds": {"septa_bus": ("https://files.mobilitydatabase.org/mdb-502/latest.zip", "SEPTA bus, trolley and subway-surface (mdb-502)")},
                     "terms": "SEPTA developer terms; public record"},
    "charlotte": {"city": "Charlotte", "st": "37", "place": "3712000", "counties": ["119"],
                  "feeds": {"cats": ("https://files.mobilitydatabase.org/mdb-2265/latest.zip", "Charlotte Area Transit System (mdb-2265)")},
                  "terms": "None stated (public record, D1)"},
    "saint_paul": {"city": "Saint Paul", "st": "27", "place": "2758000", "counties": ["123"],
                   "feeds": {"metro_transit": ("https://files.mobilitydatabase.org/mdb-205/latest.zip", "Metro Transit, Twin Cities (mdb-205)")},
                   "terms": "Metro Transit GTFS licence (public data, attribution)"},
    "los_angeles": {"city": "Los Angeles", "st": "06", "place": "0644000", "counties": ["037"],
                    "feeds": {"la_metro_bus": ("https://files.mobilitydatabase.org/mdb-29/latest.zip", "LA Metro bus (mdb-29)")},
                    "terms": "LA Metro developer terms (developer.metro.net)"},
    "seattle": {"city": "Seattle", "st": "53", "place": "5363000", "counties": ["033"],
                "feeds": {"king_county_metro": ("https://files.mobilitydatabase.org/mdb-1330/latest.zip", "King County Metro (mdb-1330)")},
                "terms": "King County Metro GTFS terms of use"},
    "chicago": {"city": "Chicago", "st": "17", "place": "1714000", "counties": ["031", "043"],
                "feeds": {"cta": ("https://files.mobilitydatabase.org/mdb-389/latest.zip", "Chicago Transit Authority (mdb-389)")},
                "terms": "CTA developer licence agreement (transitchicago.com/developers/terms)"},
    "madison": {"city": "Madison", "st": "55", "place": "5548000", "counties": ["025"], "feeds": {},
                "terms": "Madison Metro GTFS not used (AQ-045)"},
}
# rapid bus routes counted as rapid transit (1/2 mile), keyed by city and GTFS route short name
RAPID = {"los_angeles": {"901", "Metro G Line (Orange) 901", "METRO G LINE"}}
RAIL_TYPES = TR.RAIL_ROUTE_TYPES


# =========================================================================== fetch

def _get(url: str, timeout: int = 300, retries: int = 3) -> bytes:
    for a in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception:
            if a == retries - 1:
                raise
            time.sleep(5 * (a + 1))
    raise AssertionError


def _save(man: dict, name: str, data: bytes | None, url: str, licence: str, note: str = "") -> None:
    """Write a download and record it in the manifest. data=None records a file already on disk (time = its mtime)."""
    p = D / name
    p.parent.mkdir(parents=True, exist_ok=True)
    when = dt.datetime.now(dt.timezone.utc)
    if data is None:
        data = p.read_bytes()
        when = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
    else:
        p.write_bytes(data)
    man["files"][name] = {"url": url, "accessed_utc": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "licence": licence, "note": note}
    (D / "manifest.json").write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
    print(f"  {name}: {len(data):,} bytes", flush=True)


def fetch(refresh: bool = False) -> None:
    from fetch_tod_transit import NTM_LAYERS, ntm_query
    D.mkdir(parents=True, exist_ok=True)
    mp = D / "manifest.json"
    man = json.loads(mp.read_text()) if mp.exists() else {}
    man.update({"source_id": "tod_net_coverage", "purpose": "City transit coverage for the TOD net-effect plan (scripts/build_tod_net_coverage.py)"})
    man.setdefault("files", {})

    def want(name):
        return refresh or not (D / name).exists()

    def known(name):
        return name in man["files"]
    states = sorted({c["st"] for c in CITIES.values()})
    for st in states:
        if st != "55":
            n = f"tiger2010/tl_2010_{st}_place10.zip"
            u = f"https://www2.census.gov/geo/tiger/TIGER2010/PLACE/2010/tl_2010_{st}_place10.zip"
            if want(n) or not known(n):
                _save(man, n, _get(u) if want(n) else None, u, CENSUS, "TIGER/Line 2010 places")
    for st in ("36", "06"):
        n = f"blocks2010/tabblock2010_{st}_pophu.zip"
        u = f"https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_{st}_pophu.zip"
        if want(n) or not known(n):
            _save(man, n, _get(u, timeout=900) if want(n) else None, u, CENSUS, "2010 Census block polygons with HOUSING10 and POP10")
    for slug, c in CITIES.items():
        for co in c["counties"]:
            n = f"areawater/tl_2024_{c['st']}{co}_areawater.zip"
            u = f"https://www2.census.gov/geo/tiger/TIGER2024/AREAWATER/tl_2024_{c['st']}{co}_areawater.zip"
            if want(n) or not known(n):
                _save(man, n, _get(u) if want(n) else None, u, CENSUS, "TIGER/Line 2024 area water")
        for key, (u, label) in c["feeds"].items():
            n = f"gtfs/{slug}_{key}.zip"
            if want(n) or not known(n):
                data = _get(u, timeout=900) if want(n) else None
                if data is not None and not data.startswith(b"PK"):
                    raise ValueError(f"{u}: not a zip")
                _save(man, n, data, u, c["terms"], label)
        n = f"ntm/{slug}_rail_stops.json"
        if slug != "madison" and not want(n) and not known(n):
            _save(man, n, None, "NTM stops FeatureServer query (where clause in note)", NTM_LICENCE,
                  "NTM stops of rail stop types within the city's bounding box (+0.03 degrees), with their agencies")
        if slug != "madison" and want(n):
            b = city_bbox_4326(slug, pad=0.03)
            types = ",".join(f"'{t}'" for t in sorted(RAIL_TYPES))
            where = (f"stop_type IN ({types}) AND stop_lat BETWEEN {b[1]:.5f} AND {b[3]:.5f} "
                     f"AND stop_lon BETWEEN {b[0]:.5f} AND {b[2]:.5f}")
            for attempt in range(4):
                try:
                    feats, urls = ntm_query(NTM_LAYERS["stops"], where)
                    break
                except RuntimeError:
                    if attempt == 3:
                        raise
                    time.sleep(10 * (attempt + 1))
            ids = sorted({f["attributes"].get("ntd_id") for f in feats if f["attributes"].get("ntd_id")})
            ag = []
            if ids:
                ag, _ = ntm_query(NTM_LAYERS["agencies"], "NTD_ID IN (" + ",".join(f"'{i}'" for i in ids) + ")")
            data = json.dumps({"stops": [f["attributes"] for f in feats], "agencies": [a["attributes"] for a in ag]}).encode()
            _save(man, n, data, urls[0] if urls else "", NTM_LICENCE, "NTM stops of rail stop types within the city's bounding box (+0.03 degrees), with their agencies")
    mp.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")


# =========================================================================== geography

def city_boundary(slug: str):
    """The city's place polygon (GeoDataFrame, EPSG:4326) and the vintage label."""
    import geopandas as gpd
    c = CITIES[slug]
    if c["st"] == "55":
        g = gpd.read_file(RAW / "census_tiger_2024" / "tl_2024_55_place.zip")
        g = g[g["GEOID"] == c["place"]]
        vint = "TIGER/Line 2024 place"
    else:
        g = gpd.read_file(D / "tiger2010" / f"tl_2010_{c['st']}_place10.zip")
        g = g[g["GEOID10"] == c["place"]]
        vint = "TIGER/Line 2010 place"
    if len(g) != 1:
        raise ValueError(f"{slug}: place {c['place']} not found once")
    return g[["geometry"]].to_crs(4326).reset_index(drop=True), vint


def city_bbox_4326(slug: str, pad: float = 0.0) -> tuple:
    g, _ = city_boundary(slug)
    x0, y0, x1, y1 = g.total_bounds
    return (x0 - pad, y0 - pad, x1 + pad, y1 + pad)


def metre_crs(slug: str):
    g, _ = city_boundary(slug)
    return g.estimate_utm_crs()


def covered_patches(slug: str, crs=None):
    """A city's covered patches (GeoDataFrame: patch_id, patch_acres, patch_land_acres) in a metre CRS (the city's UTM
    zone unless crs is given). Built by this script into data/processed/tod_net_effect/coverage_<slug>.gpkg."""
    import geopandas as gpd
    g = gpd.read_file(OUT / f"coverage_{slug}.gpkg", layer="patches")
    return g.to_crs(crs or metre_crs(slug))


def land_polygon(slug: str, crs):
    """The city place less TIGER 2024 area water of its counties (shapely geometry in crs)."""
    import geopandas as gpd
    c = CITIES[slug]
    city, _ = city_boundary(slug)
    city = city.to_crs(crs).geometry.union_all()
    w = [gpd.read_file(D / "areawater" / f"tl_2024_{c['st']}{co}_areawater.zip") for co in c["counties"]
         if (D / "areawater" / f"tl_2024_{c['st']}{co}_areawater.zip").exists()]
    if not w:
        return city, False
    water = pd.concat(w, ignore_index=True).to_crs(crs)
    water = water[water.intersects(city)]
    return city.difference(water.geometry.union_all()), True


def blocks(slug: str, crs):
    """Census blocks with homes and a point (GeoDataFrame in crs: homes, geometry=point) inside the city's bbox."""
    import geopandas as gpd
    c = CITIES[slug]
    b4269 = tuple(gpd.GeoSeries.from_xy([city_bbox_4326(slug)[0], city_bbox_4326(slug)[2]],
                                        [city_bbox_4326(slug)[1], city_bbox_4326(slug)[3]], crs=4326).to_crs(4269).total_bounds)
    if c["st"] == "55":
        b = gpd.read_file(RAW / "census_tiger_2020_tabblock" / "tl_2020_55_tabblock20.zip", bbox=b4269)
        pts = gpd.points_from_xy(b["INTPTLON20"].astype(float), b["INTPTLAT20"].astype(float), crs=4269)
        g = gpd.GeoDataFrame({"homes": pd.to_numeric(b["HOUSING20"], errors="coerce").fillna(0)}, geometry=pts, crs=4269)
        return g.to_crs(crs), "2020 Census blocks (HOUSING20), internal points"
    cand = [RAW / "tod_cases" / "census_2010_blocks" / f"tabblock2010_{c['st']}_pophu.zip",
            RAW / "tod_traits" / "blocks2010" / f"tabblock2010_{c['st']}_pophu.zip",
            D / "blocks2010" / f"tabblock2010_{c['st']}_pophu.zip"]
    f = next(p for p in cand if p.exists())
    b = gpd.read_file(f, bbox=b4269).to_crs(crs)
    g = gpd.GeoDataFrame({"homes": pd.to_numeric(b["HOUSING10"], errors="coerce").fillna(0)},
                         geometry=b.geometry.representative_point(), crs=crs)
    return g, "2010 Census blocks (HOUSING10), representative points"


# =========================================================================== stops

def ntm_rail_stops(slug: str, crs):
    """Rail stops from the NTM extract (Amtrak excluded), GeoDataFrame in crs with agency id and name."""
    import geopandas as gpd
    d = json.loads((D / "ntm" / f"{slug}_rail_stops.json").read_text())
    s = pd.DataFrame(d["stops"])
    if s.empty:
        return gpd.GeoDataFrame({"ntd_id": [], "stop_name": []}, geometry=[], crs=crs), {}
    names = {a.get("NTD_ID") or a.get("NTAD_NTD_ID"): a.get("Agency_Name", "") for a in d["agencies"]}
    s["agency"] = s["ntd_id"].map(names).fillna("")
    s = s[~s["agency"].map(TR.is_excluded_agency)]
    g = gpd.GeoDataFrame(s[["ntd_id", "agency", "stop_name", "stop_type"]],
                         geometry=gpd.points_from_xy(s["stop_lon"].astype(float), s["stop_lat"].astype(float)), crs=4326)
    dates = sorted(set(s.get("download_date", pd.Series(dtype=str)).dropna()))
    return g.to_crs(crs), {"agencies": sorted(set(s["agency"])), "download_dates": dates}


def _table(z: zipfile.ZipFile, name: str, usecols=None) -> pd.DataFrame:
    names = {n.split("/")[-1]: n for n in z.namelist()}
    if name not in names:
        return pd.DataFrame()
    with z.open(names[name]) as f:
        return pd.read_csv(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace"), dtype=str,
                           usecols=(lambda c: c.strip() in usecols) if usecols else None).rename(columns=str.strip)


def gtfs_stops(path: Path, start: dt.date, rapid_names: set[str] = frozenset(), n: int = TR.MAIN_N) -> tuple[pd.DataFrame, dict]:
    """Stops of one GTFS feed with flags: rail (served by a rail route type or a named rapid route on the
    representative day) and frequent (served by a bus route whose best direction has >= n trips starting in each
    of the 7:00 and 8:00 hours on that day). Returns (stops with lat, lon, rail, frequent) and facts."""
    with zipfile.ZipFile(path) as z:
        routes = _table(z, "routes.txt").fillna("")
        trips = _table(z, "trips.txt", {"route_id", "service_id", "trip_id", "direction_id"}).fillna("")
        cal = _table(z, "calendar.txt").fillna("").to_dict("records")
        cd = _table(z, "calendar_dates.txt").fillna("").to_dict("records")
        fi = _table(z, "feed_info.txt").fillna("").to_dict("records")
        stops = _table(z, "stops.txt", {"stop_id", "stop_lat", "stop_lon", "stop_name"})
        trec = trips.to_dict("records")
        day = TR.representative_weekday(trec, cal, cd, start)
        act = TR.active_services(cal, cd, day)
        dt_ = trips[trips["service_id"].isin(act)]
        st = _table(z, "stop_times.txt", {"trip_id", "stop_id", "stop_sequence", "departure_time", "arrival_time"})
    st = st[st["trip_id"].isin(set(dt_["trip_id"]))].copy()
    st["seq"] = pd.to_numeric(st["stop_sequence"], errors="coerce")
    tm = st["departure_time"].fillna("").where(st["departure_time"].fillna("").str.len() > 0, st["arrival_time"].fillna(""))
    st["hour"] = pd.to_numeric(tm.str.split(":").str[0], errors="coerce")
    first = st.dropna(subset=["hour"]).sort_values(["trip_id", "seq"]).drop_duplicates("trip_id")
    hours = dict(zip(first["trip_id"], first["hour"].astype(int)))
    peaks = TR.route_peak_trips(routes.to_dict("records"), dt_.to_dict("records"), hours)
    routes["key"] = [TR.route_key(r) for r in routes.to_dict("records")]
    rtype = routes["route_type"].astype(str).str.strip()
    is_rail = rtype.isin(RAIL_TYPES) | routes["route_short_name"].isin(rapid_names) | routes["key"].isin(rapid_names)
    is_bus = ~is_rail
    freq_ids = set(routes.loc[is_bus & routes["key"].map(lambda k: TR.qualifies(peaks.get(k, 0), n)), "route_id"])
    rail_ids = set(routes.loc[is_rail, "route_id"])
    tr_route = dict(zip(dt_["trip_id"], dt_["route_id"]))
    st["route_id"] = st["trip_id"].map(tr_route)
    served_f = set(st.loc[st["route_id"].isin(freq_ids), "stop_id"])
    served_r = set(st.loc[st["route_id"].isin(rail_ids), "stop_id"])
    s = stops.copy()
    s["rail"] = s["stop_id"].isin(served_r)
    s["frequent"] = s["stop_id"].isin(served_f)
    s = s[s["rail"] | s["frequent"]].copy()
    s["lat"], s["lon"] = pd.to_numeric(s["stop_lat"], errors="coerce"), pd.to_numeric(s["stop_lon"], errors="coerce")
    lo, hi = TR.feed_validity(cal, cd, fi)
    facts = {"service_day": day.isoformat(), "valid_from": lo.isoformat(), "valid_through": hi.isoformat(),
             "bus_routes": int(is_bus.sum()), "frequent_bus_routes": len(freq_ids), "rail_or_rapid_routes": len(rail_ids),
             "trips_on_day": int(len(dt_))}
    return s.dropna(subset=["lat", "lon"])[["stop_id", "stop_name", "lat", "lon", "rail", "frequent"]], facts


def madison_stops(crs, route_a_rapid: bool = True):
    """Madison's qualifying stops from the Wisconsin layer (reference/tod_stops.csv, Madison Metro 50005):
    rapid (flag_a_rapid; Route A) and 15-minute bus (flag_b_15min)."""
    import geopandas as gpd
    s = pd.read_csv(REFERENCE / "tod_stops.csv", dtype=str)
    s = s[s["ntd_id"] == TR.MADISON_NTD_ID]
    rapid = (s["flag_a_rapid"] == "1") & route_a_rapid
    freq = (s["flag_b_15min"] == "1") | ((s["flag_a_rapid"] == "1") & (not route_a_rapid))
    g = gpd.GeoDataFrame({"rail": rapid.values, "frequent": (freq & ~rapid).values, "src": s["frequency_source"].values},
                         geometry=gpd.points_from_xy(s["lon"].astype(float), s["lat"].astype(float)), crs=4326)
    return g[g["rail"] | g["frequent"]].to_crs(crs)


# =========================================================================== coverage

def covered_area(rail_pts, bus_pts):
    """Union of 1/2-mile circles around rail/rapid stops and 1/4-mile circles around frequent-bus stops."""
    import shapely
    parts = [shapely.buffer(np.asarray(list(rail_pts), dtype=object), HALF_M, quad_segs=16),
             shapely.buffer(np.asarray(list(bus_pts), dtype=object), QUARTER_M, quad_segs=16)]
    geoms = np.concatenate([p for p in parts if len(p)]) if any(len(p) for p in parts) else np.array([], dtype=object)
    return shapely.union_all(geoms) if len(geoms) else shapely.Polygon()


def patches_of(covered, city, land, crs):
    """Connected patches of the covered area inside the city: acres (inside the place) and land acres."""
    import geopandas as gpd
    import shapely
    inside = covered.intersection(city)
    parts = [g for g in getattr(inside, "geoms", [inside]) if not g.is_empty and g.area > 0]
    rows = [{"patch_id": i + 1, "patch_acres": g.area / SQM_PER_ACRE,
             "patch_land_acres": shapely.intersection(g, land).area / SQM_PER_ACRE, "geometry": g} for i, g in enumerate(
        sorted(parts, key=lambda g: -g.area))]
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=crs) if rows else gpd.GeoDataFrame(
        {"patch_id": [], "patch_acres": [], "patch_land_acres": []}, geometry=[], crs=crs)


def build_city(slug: str) -> dict:
    import geopandas as gpd
    from missing_middleware.tod import traits as TT
    c = CITIES[slug]
    crs = metre_crs(slug)
    cityg, vint = city_boundary(slug)
    city = cityg.to_crs(crs).geometry.union_all()
    land, water_ok = land_polygon(slug, crs)
    notes = []
    if slug == "madison":
        s = madison_stops(crs)
        rail = s[s["rail"]].geometry
        bus = s[s["frequent"]].geometry
        stop_src, stop_year = "Wisconsin TOD stop layer (reference/tod_stops.csv): NTM stops, Madison route descriptions", "NTM compiled 2026-09-23"
        feed_src = "Madison route descriptions in the NTM routes layer (AQ-045; Madison Metro GTFS not used)"
        feed_date = "NTM compiled 2026-09-23"
        s2 = madison_stops(crs, route_a_rapid=False)
        alt = covered_area(s2[s2["rail"]].geometry, s2[s2["frequent"]].geometry).intersection(land).area / SQM_PER_ACRE
        notes.append(f"Route A (bus rapid transit, opened September 2024, after the 2023 reform) counted as rapid (1/2 mile) "
                     f"by the Wisconsin rule; with its stops at 1/4 mile instead, covered land is {alt:,.0f} acres")
    else:
        ntm, info = ntm_rail_stops(slug, crs)
        rails, buses, facts = [ntm.geometry], [], []
        start = dt.date.today()
        for key in c["feeds"]:
            p = D / "gtfs" / f"{slug}_{key}.zip"
            if not p.exists():
                notes.append(f"feed {key} missing")
                continue
            s, f = gtfs_stops(p, start, RAPID.get(slug, set()))
            g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s["lon"], s["lat"]), crs=4326).to_crs(crs)
            rails.append(g[g["rail"]].geometry)
            buses.append(g[g["frequent"] & ~g["rail"]].geometry)
            facts.append(f"{key}: service day {f['service_day']}, valid {f['valid_from']} to {f['valid_through']}, "
                         f"{f['frequent_bus_routes']} of {f['bus_routes']} bus routes frequent")
        rail = pd.concat(rails, ignore_index=True) if rails else gpd.GeoSeries([], crs=crs)
        bus = pd.concat(buses, ignore_index=True) if buses else gpd.GeoSeries([], crs=crs)
        stop_src = "BTS NTM stops of rail stop types (" + "; ".join(info.get("agencies", [])) + "), plus GTFS rail-type stops"
        if slug in RAPID:
            stop_src += "; LA Metro G Line (route 901) as rapid"
        stop_year = "NTM compiled " + ", ".join(info.get("download_dates", [])) + " (today's layer, not the year before the reform)"
        feed_src = "today's GTFS: " + "; ".join(c["feeds"][k][1] for k in c["feeds"]) + \
            " (a stop qualifies when a trip of a qualifying route serves it, not by the 30 m line rule)"
        feed_date = "; ".join(facts)
        if slug == "chicago":
            notes.append("Pace suburban buses not included (CTA only)")
        if slug == "new_york":
            notes.append("NYC Ferry, NJ Transit and Westchester Bee-Line buses not included")
    rail_s = gpd.GeoSeries(list(rail), crs=crs)
    cov = covered_area(rail_s, gpd.GeoSeries(list(bus), crs=crs))
    patches = patches_of(cov, city, land, crs)
    bl, hv = blocks(slug, crs)
    in_city = bl.geometry.within(city)
    bc = bl[in_city]
    cov_in = cov.intersection(city)
    homes_cov = float(bc.loc[bc.geometry.within(cov_in), "homes"].sum()) if not cov_in.is_empty else 0.0
    land_ac = land.area / SQM_PER_ACRE
    cov_land = cov.intersection(land).area / SQM_PER_ACRE
    rail_in = rail_s[rail_s.within(city.buffer(HALF_M))]
    stations = len(TT.cluster_stations(rail_in.to_frame("geometry").set_geometry("geometry"))) if len(rail_in) else 0
    bus_s = gpd.GeoSeries(list(bus), crs=crs)
    n_bus = int(len(bus_s[bus_s.within(city)].drop_duplicates()))
    out = OUT / f"coverage_{slug}.gpkg"
    if out.exists():
        out.unlink()
    patches.to_crs(4326).to_file(out, layer="patches", driver="GPKG")
    cityg.to_file(out, layer="city", driver="GPKG")
    if not water_ok:
        notes.append("no area-water file: land includes water")
    return {"city": c["city"], "slug": slug, "land_acres": land_ac, "covered_land_acres": cov_land,
            "share_land_covered": cov_land / land_ac, "homes": float(bc["homes"].sum()), "homes_covered": homes_cov,
            "share_homes_covered": homes_cov / float(bc["homes"].sum()), "rail_or_rapid_stations": stations,
            "frequent_bus_stops": n_bus, "patches": len(patches),
            "largest_patch_acres": float(patches["patch_acres"].max()) if len(patches) else 0.0,
            "largest_patch_share_of_covered": float(patches["patch_acres"].max() / patches["patch_acres"].sum()) if len(patches) else np.nan,
            "stop_layer_source": stop_src, "stop_layer_year": stop_year, "bus_feed_source": feed_src, "bus_feed_date": feed_date,
            "boundary_vintage": vint + "; land = place less TIGER 2024 area water", "homes_vintage": hv, "notes": "; ".join(notes)}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--city", nargs="*", default=list(CITIES))
    a = ap.parse_args(argv)
    if a.fetch:
        fetch(a.refresh)
    rows = []
    for slug in a.city:
        print("==", slug, flush=True)
        r = build_city(slug)
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k not in ("stop_layer_source", "bus_feed_source", "bus_feed_date")}, flush=True)
        rows.append(r)
    df = pd.DataFrame(rows)
    p = OUT / "coverage_cities.csv"
    if p.exists() and set(a.city) != set(CITIES):
        old = pd.read_csv(p)
        df = pd.concat([old[~old["slug"].isin(df["slug"])], df], ignore_index=True)
    order = {s: i for i, s in enumerate(CITIES)}
    df = df.sort_values("slug", key=lambda s: s.map(order)).reset_index(drop=True)
    for k in ("land_acres", "covered_land_acres", "homes", "homes_covered", "largest_patch_acres"):
        df[k] = df[k].round(1)
    for k in ("share_land_covered", "share_homes_covered", "largest_patch_share_of_covered"):
        df[k] = df[k].round(4)
    df.to_csv(p, index=False, lineterminator="\n")
    print("wrote", p)


if __name__ == "__main__":
    main()

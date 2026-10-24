#!/usr/bin/env python3
"""Fetch a few sample rows from every data source in docs/data-sources/.

This script is the reproducible way to refresh data/sample/. It uses only
the Python standard library, so it runs anywhere Python 3.10+ is installed.

For each source it writes:
  data/sample/<source_id>.csv        up to 5 sample rows (long values cut short)
  data/sample/<source_id>.meta.json  where the rows came from, field list,
                                     record counts and any errors
and a summary in data/sample/_fetch_report.json.

Usage:
  python3 scripts/fetch_samples.py            # all sources
  python3 scripts/fetch_samples.py acs bps    # only these source ids
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import re
import sys
import traceback
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sample"
N_ROWS = 5
MAX_CELL = 200
UA = (
    "housing-challenge-data-dictionary/0.1 "
    "(+https://github.com/mroconnell/housing-challenge-starter-missingmiddleware)"
)
SOURCES = {}


def source(source_id):
    def wrap(fn):
        SOURCES[source_id] = fn
        return fn

    return wrap


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def _request(url, params=None, data=None, headers=None, timeout=90):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    return urllib.request.urlopen(req, timeout=timeout), url


def get_bytes(url, params=None, **kw):
    resp, full = _request(url, params, **kw)
    with resp:
        return resp.read()


def get_json(url, params=None, **kw):
    raw = get_bytes(url, params, **kw).decode("utf-8", "replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"not JSON ({e}); body starts: {raw[:300]!r}") from None


def get_text(url, params=None, **kw):
    return get_bytes(url, params, **kw).decode("utf-8", "replace")


def head_lines(url, n_lines=6, max_bytes=4_000_000, gz=False):
    """Read only the first lines of a (possibly gzipped) text file."""
    resp, _ = _request(url)
    buf = b""
    dec = zlib.decompressobj(16 + zlib.MAX_WBITS) if gz else None
    with resp:
        read = 0
        while read < max_bytes:
            chunk = resp.read(65536)
            if not chunk:
                break
            read += len(chunk)
            buf += dec.decompress(chunk) if dec else chunk
            if buf.count(b"\n") > n_lines:
                break
    return buf.decode("utf-8", "replace").splitlines()[:n_lines]


def first_ok(candidates, fn):
    """Try fn(url) for each url, return (url, result) for the first that works."""
    errors = []
    for u in candidates:
        try:
            return u, fn(u)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{u}: {type(e).__name__}: {e}")
    raise RuntimeError("all candidate URLs failed: " + " | ".join(errors))


# --------------------------------------------------------------------------- #
# ArcGIS / Hub / Socrata / CKAN helpers
# --------------------------------------------------------------------------- #
def arcgis_layer(url, where="1=1"):
    """Return (rows, meta) for an ArcGIS FeatureServer/MapServer layer."""
    url = url.rstrip("/")
    info = get_json(url, {"f": "json"})
    if "error" in info:
        raise RuntimeError(f"layer metadata error: {info['error']}")
    fields = [
        {
            "name": f.get("name"),
            "type": (f.get("type") or "").replace("esriFieldType", ""),
            "alias": f.get("alias"),
            "length": f.get("length"),
            "has_domain": bool(f.get("domain")),
        }
        for f in info.get("fields") or []
    ]
    count = None
    try:
        count = get_json(
            url + "/query", {"where": where, "returnCountOnly": "true", "f": "json"}
        ).get("count")
    except Exception:  # noqa: BLE001
        pass
    q = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "false",
        "resultRecordCount": N_ROWS,
        "f": "json",
    }
    res = get_json(url + "/query", q)
    if "error" in res:
        q.pop("resultRecordCount")
        oid = info.get("objectIdField") or "OBJECTID"
        q["where"] = f"{oid} <= 50"
        res = get_json(url + "/query", q)
    if "error" in res:
        raise RuntimeError(f"query error: {res['error']}")
    rows = [ft.get("attributes", {}) for ft in res.get("features", [])][:N_ROWS]
    meta = {
        "service_url": url,
        "layer_name": info.get("name"),
        "geometry_type": info.get("geometryType"),
        "spatial_reference": (info.get("extent") or {}).get("spatialReference")
        or info.get("sourceSpatialReference"),
        "record_count": count,
        "max_record_count": info.get("maxRecordCount"),
        "last_edit_date": _epoch((info.get("editingInfo") or {}).get("lastEditDate")),
        "description": _clean(info.get("description"))[:1000],
        "copyright": _clean(info.get("copyrightText"))[:500],
        "fields": fields,
    }
    return rows, meta


def resolve_layer(url):
    """Turn a .../FeatureServer or .../MapServer url into its first layer url."""
    url = url.rstrip("/")
    if not re.search(r"/(Feature|Map)Server$", url):
        return url
    svc = get_json(url, {"f": "json"})
    layers = svc.get("layers") or []
    return f"{url}/{layers[0]['id'] if layers else 0}"


def arcgis_item(item_id, portal="https://www.arcgis.com"):
    item = get_json(f"{portal}/sharing/rest/content/items/{item_id}", {"f": "json"})
    if "error" in item:
        raise RuntimeError(f"item error: {item['error']}")
    return item


def arcgis_item_layer(item_id, layer=0, portal="https://www.arcgis.com"):
    item = arcgis_item(item_id, portal)
    url = (item.get("url") or "").rstrip("/")
    if not url:
        raise RuntimeError(f"item {item_id} has no service url (type={item.get('type')})")
    url = resolve_layer(url)
    rows, meta = arcgis_layer(url)
    meta["item"] = {
        "id": item_id,
        "title": item.get("title"),
        "owner": item.get("owner"),
        "type": item.get("type"),
        "modified": _epoch(item.get("modified")),
        "license": _clean(item.get("licenseInfo"))[:500],
        "access": item.get("access"),
    }
    return rows, meta


def arcgis_search(query, num=10):
    res = get_json(
        "https://www.arcgis.com/sharing/rest/search",
        {"q": query, "num": num, "f": "json", "sortField": "numviews", "sortOrder": "desc"},
    )
    return [
        {
            "id": r.get("id"),
            "title": r.get("title"),
            "owner": r.get("owner"),
            "type": r.get("type"),
            "url": r.get("url"),
            "modified": _epoch(r.get("modified")),
        }
        for r in res.get("results", [])
    ]


def hub_search(hub, query, limit=10):
    """Search an ArcGIS Hub site. Returns a list of dataset summaries."""
    hub = hub.rstrip("/")
    out = []
    try:
        res = get_json(
            f"{hub}/api/search/v1/collections/dataset/items", {"q": query, "limit": limit}
        )
        for f in res.get("features", []):
            p = f.get("properties", {})
            out.append(
                {
                    "id": f.get("id") or p.get("id"),
                    "title": p.get("title"),
                    "type": p.get("type"),
                    "url": p.get("url"),
                    "owner": p.get("owner"),
                    "modified": _epoch(p.get("modified")),
                }
            )
    except Exception:  # noqa: BLE001
        res = get_json(f"{hub}/api/v3/datasets", {"q": query, "page[size]": limit})
        for d in res.get("data", []):
            a = d.get("attributes", {})
            out.append(
                {
                    "id": d.get("id"),
                    "title": a.get("name"),
                    "type": a.get("type"),
                    "url": a.get("url"),
                    "owner": a.get("owner"),
                    "modified": _epoch(a.get("modified")),
                }
            )
    return out


def first_layer_from(results, title_pattern=None):
    """Sample the first search hit that is a queryable feature layer."""
    errors = []
    for r in results:
        url = (r.get("url") or "").rstrip("/")
        if not re.search(r"/(Feature|Map)Server(/\d+)?$", url):
            continue
        if title_pattern and not re.search(title_pattern, r.get("title") or "", re.I):
            continue
        try:
            url = resolve_layer(url)
            rows, meta = arcgis_layer(url)
            meta["chosen_search_hit"] = r
            return rows, meta
        except Exception as e:  # noqa: BLE001
            errors.append(f"{url}: {e}")
    raise RuntimeError("no queryable layer in search results; " + " | ".join(errors[:5]))


def socrata(domain, dataset_id):
    rows = get_json(f"https://{domain}/resource/{dataset_id}.json", {"$limit": N_ROWS})
    view = get_json(f"https://{domain}/api/views/{dataset_id}.json")
    fields = [
        {
            "name": c.get("fieldName"),
            "type": c.get("dataTypeName"),
            "alias": c.get("name"),
            "description": _clean(c.get("description"))[:300],
        }
        for c in view.get("columns", [])
    ]
    count = None
    try:
        count = int(
            get_json(f"https://{domain}/resource/{dataset_id}.json", {"$select": "count(*)"})[0]
            .popitem()[1]
        )
    except Exception:  # noqa: BLE001
        pass
    meta = {
        "dataset_id": dataset_id,
        "name": view.get("name"),
        "description": _clean(view.get("description"))[:1000],
        "attribution": view.get("attribution"),
        "license": (view.get("license") or {}).get("name"),
        "rows_updated_at": _epoch((view.get("rowsUpdatedAt") or 0) * 1000),
        "record_count": count,
        "page_url": f"https://{domain}/d/{dataset_id}",
        "api_url": f"https://{domain}/resource/{dataset_id}.json",
        "fields": fields,
    }
    return rows, meta


def socrata_catalog(domain, query, limit=25):
    res = get_json(
        "https://api.us.socrata.com/api/catalog/v1",
        {"domains": domain, "search_context": domain, "q": query, "limit": limit},
    )
    return [
        {
            "id": r["resource"]["id"],
            "name": r["resource"]["name"],
            "type": r["resource"].get("type"),
            "updated_at": r["resource"].get("data_updated_at"),
        }
        for r in res.get("results", [])
    ]


def _epoch(ms):
    try:
        return dt.datetime.fromtimestamp(int(ms) / 1000, dt.timezone.utc).date().isoformat()
    except Exception:  # noqa: BLE001
        return None


def _clean(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(s))
    return re.sub(r"\s+", " ", s).strip()


def page_links(url, pattern):
    html = get_text(url)
    links = re.findall(r'href=["\']([^"\']+)["\']', html)
    links = [urllib.parse.urljoin(url, l) for l in links]
    return sorted({l for l in links if re.search(pattern, l, re.I)})


def csv_rows(lines):
    return list(csv.DictReader(io.StringIO("\n".join(lines))))


# --------------------------------------------------------------------------- #
# National sources
# --------------------------------------------------------------------------- #
ACS_VARS = {
    "B01003_001E": "Total population",
    "B25001_001E": "Housing units",
    "B25002_003E": "Vacant housing units",
    "B25003_002E": "Owner-occupied units",
    "B25003_003E": "Renter-occupied units",
    "B25024_002E": "Units in structure: 1, detached",
    "B25024_006E": "Units in structure: 5 to 9",
    "B25077_001E": "Median home value (dollars)",
    "B25064_001E": "Median gross rent (dollars)",
    "B19013_001E": "Median household income (dollars)",
}


B25024_LINES = {
    "001": "Total housing units",
    "002": "1, detached",
    "003": "1, attached",
    "004": "2 units",
    "005": "3 or 4 units",
    "006": "5 to 9 units",
    "007": "10 to 19 units",
    "008": "20 to 49 units",
    "009": "50 or more units",
    "010": "Mobile home",
    "011": "Boat, RV, van, etc.",
}


# Other ACS tables the Wisconsin pipeline reads (missing_middleware/foundation/sources.py).
ACS_PIPELINE_TABLES = ("b25002", "b25034", "b01003")
ACS_TABLE_LINES = {
    "B25002": {"001": "Total housing units", "002": "Occupied", "003": "Vacant"},
    "B25034": {"001": "Total", "002": "Built 2020 or later", "003": "Built 2010 to 2019", "004": "Built 2000 to 2009",
               "005": "Built 1990 to 1999", "006": "Built 1980 to 1989", "007": "Built 1970 to 1979",
               "008": "Built 1960 to 1969", "009": "Built 1950 to 1959", "010": "Built 1940 to 1949",
               "011": "Built 1939 or earlier"},
    "B01003": {"001": "Total population"},
}


def fetch_acs_summary_file():
    """ACS table B25024 from the table-based summary file (no key needed)."""
    def sf(year):
        u = (
            f"https://www2.census.gov/programs-surveys/acs/summary_file/{year}/"
            f"table-based-SF/data/5YRData/acsdt5y{year}-b25024.dat"
        )
        return u, head_lines(u, 3000, max_bytes=3_000_000)

    _, (url, lines) = first_ok([2024, 2023], sf)
    rows_all = list(csv.DictReader(io.StringIO("\n".join(lines)), delimiter="|"))
    # State rows (GEO_ID 0400000USxx) make the most readable sample.
    rows = [r for r in rows_all if r.get("GEO_ID", "").startswith("0400000US")][:N_ROWS] or rows_all[:N_ROWS]
    fields = []
    for c in rows[0].keys() if rows else []:
        m = re.match(r"B25024_([EM])(\d{3})", c)
        if m:
            kind = "estimate" if m.group(1) == "E" else "margin of error (90%)"
            fields.append({"name": c, "type": "int", "alias": f"Units in structure: {B25024_LINES.get(m.group(2), '')}, {kind}"})
        elif c == "GEO_ID":
            fields.append({"name": c, "type": "string", "alias": "Census GEO_ID. 0400000US + 2-digit FIPS = state; 0500000US + 5-digit FIPS = county."})
        else:
            fields.append({"name": c, "type": "string"})
    other = {}
    year = re.search(r"acsdt5y(\d{4})", url).group(1)
    for t in ACS_PIPELINE_TABLES:
        u = url.replace("b25024", t)
        try:
            lines = head_lines(u, 3000, max_bytes=3_000_000)
            trows = list(csv.DictReader(io.StringIO("\n".join(lines)), delimiter="|"))
            wi = next((r for r in trows if r.get("GEO_ID") == "0400000US55"), None)
            other[t.upper()] = {"url": u, "columns": list(trows[0].keys()) if trows else [], "wisconsin_row": wi}
        except Exception as e:  # noqa: BLE001
            other[t.upper()] = {"url": u, "error": f"{type(e).__name__}: {e}"[:200]}
    return rows, {
        "vintage": f"ACS 5-year {year}, table B25024 (Units in Structure); other pipeline tables listed below",
        "pipeline_tables": other,
        "api_url": url,
        "note": (
            "The Census Data API now answers 'Missing Key' without a free key "
            "(https://api.census.gov/data/key_signup.html). Without a key our script reads the "
            "table-based summary file, which needs none. Set CENSUS_API_KEY to use the API."
        ),
        "fields": fields,
    }


@source("acs")
def fetch_acs():
    import os

    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        return fetch_acs_summary_file()

    def try_year(year):
        base = f"https://api.census.gov/data/{year}/acs/acs5"
        data = get_json(base, {"get": "NAME," + ",".join(ACS_VARS), "for": "county:*", "in": "state:44", "key": key})
        return base, data

    used, (base, data) = first_ok([2024, 2023, 2022], try_year)
    header, body = data[0], data[1:]
    rows = [dict(zip(header, r)) for r in body[:N_ROWS]]
    fields = [{"name": "NAME", "type": "string", "alias": "Geography name"}]
    for v in ACS_VARS:
        try:
            m = get_json(f"{base}/variables/{v}.json")
            fields.append(
                {"name": v, "type": m.get("predicateType"), "alias": m.get("label"), "concept": m.get("concept")}
            )
        except Exception:  # noqa: BLE001
            fields.append({"name": v, "alias": ACS_VARS[v]})
    fields += [{"name": "state", "type": "string", "alias": "State FIPS"}, {"name": "county", "type": "string", "alias": "County FIPS"}]
    return rows, {
        "vintage": f"ACS 5-year {used}",
        "api_url": f"{base}?get=NAME,{','.join(ACS_VARS)}&for=county:*&in=state:44",
        "note": "Sample is Rhode Island counties. Any of ~20,000 ACS variables can be requested.",
        "record_count": len(body),
        "fields": fields,
    }


BLS_SERIES = {
    "CES2000000001": "All employees, construction, US, seasonally adjusted (thousands)",
    "CES2023610001": "All employees, residential building construction, US, SA (thousands)",
    "WPUSI012011": "PPI: construction materials (index 1982=100)",
    "WPUIP2311001": "PPI: net inputs to residential construction, goods (index)",
}


@source("bls_ces_ppi")
def fetch_bls():
    yr = dt.date.today().year
    body = json.dumps({"seriesid": list(BLS_SERIES), "startyear": str(yr - 1), "endyear": str(yr)}).encode()
    res = get_json(
        "https://api.bls.gov/publicAPI/v2/timeseries/data/",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    if res.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS API: {res.get('status')} {res.get('message')}")
    rows = []
    for s in res["Results"]["series"]:
        for d in s["data"][:2]:
            rows.append(
                {
                    "seriesID": s["seriesID"],
                    "series_title": BLS_SERIES.get(s["seriesID"]),
                    "year": d["year"],
                    "period": d["period"],
                    "periodName": d["periodName"],
                    "value": d["value"],
                    "footnotes": ";".join(f.get("text", "") for f in d.get("footnotes", []) if f),
                }
            )
    return rows[: N_ROWS * 2], {
        "api_url": "https://api.bls.gov/publicAPI/v2/timeseries/data/ (POST)",
        "messages": res.get("message"),
        "series": BLS_SERIES,
    }


@source("bls_qcew")
def fetch_qcew():
    yr = dt.date.today().year
    cands = [f"https://data.bls.gov/cew/data/api/{y}/a/industry/23.csv" for y in (yr - 1, yr - 2, yr - 3)]
    url, lines = first_ok(cands, lambda u: head_lines(u, 400))
    rows = [r for r in csv_rows(lines) if r.get("own_code") == "5" and r.get("area_fips", "").endswith("000")]
    return rows[:N_ROWS], {
        "api_url": url,
        "note": "Annual averages for NAICS 23 (Construction), every area. Other slices: by area, by size.",
        "layout_doc": "https://www.bls.gov/cew/about-data/downloadable-file-layouts/annual/naics-based-annual-layout.htm",
    }


@source("nlcd")
def fetch_nlcd():
    wms_cands = [
        "https://www.mrlc.gov/geoserver/mrlc_display/wms",
        "https://dmsdata.cr.usgs.gov/geoserver/mrlc_Land-Cover-Native_conus_year_data/wms",
    ]

    def caps(u):
        txt = get_text(u, {"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"})
        names = re.findall(r"<Layer[^>]*>\s*<Name>([^<]+)</Name>", txt)
        return names

    url, names = first_ok(wms_cands, caps)
    lc = [n for n in names if re.search(r"(LndCov|Land_Cover)", n, re.I) and re.search(r"L48|CU|conus", n, re.I)]
    layer = sorted(lc)[-1] if lc else names[0]
    points = {
        "Salt Lake City UT": (40.7608, -111.8910),
        "Hartford CT": (41.7658, -72.6734),
        "Madison WI": (43.0731, -89.4012),
        "Providence RI": (41.8240, -71.4128),
        "Rural Lancaster Co PA": (40.0000, -76.2000),
    }
    rows = []
    for name, (lat, lon) in points.items():
        d = 0.0005
        params = {
            "service": "WMS",
            "version": "1.1.1",
            "request": "GetFeatureInfo",
            "layers": layer,
            "query_layers": layer,
            "srs": "EPSG:4326",
            "bbox": f"{lon-d},{lat-d},{lon+d},{lat+d}",
            "width": 3,
            "height": 3,
            "x": 1,
            "y": 1,
            "info_format": "application/json",
        }
        try:
            fi = get_json(url, params)
            props = (fi.get("features") or [{}])[0].get("properties", {})
        except Exception as e:  # noqa: BLE001
            props = {"error": str(e)[:150]}
        rows.append({"point": name, "lat": lat, "lon": lon, "layer": layer, **props})
    return rows, {
        "wms_url": url,
        "layer": layer,
        "land_cover_layers_found": lc[:40],
        "note": "Raster data. Sample rows are pixel values at 5 points via WMS GetFeatureInfo.",
    }


@source("nasa_modis_lc")
def fetch_modis():
    base = "https://modis.ornl.gov/rst/api/v1/MCD12Q1"
    pts = {"Salt Lake City UT": (40.7608, -111.8910), "Madison WI": (43.0731, -89.4012), "Hartford CT": (41.7658, -72.6734)}
    lat, lon = pts["Salt Lake City UT"]
    dates = get_json(f"{base}/dates", {"latitude": lat, "longitude": lon}, headers={"Accept": "application/json"})["dates"]
    last = dates[-1]["modis_date"]
    bands = get_json(f"{base}/bands", headers={"Accept": "application/json"}).get("bands", [])
    rows = []
    for name, (la, lo) in pts.items():
        r = get_json(
            f"{base}/subset",
            {"latitude": la, "longitude": lo, "band": "LC_Type1", "startDate": last, "endDate": last, "kmAboveBelow": 0, "kmLeftRight": 0},
            headers={"Accept": "application/json"},
        )
        for s in r.get("subset", []):
            rows.append(
                {
                    "point": name,
                    "latitude": r.get("latitude"),
                    "longitude": r.get("longitude"),
                    "band": s.get("band"),
                    "modis_date": s.get("modis_date"),
                    "calendar_date": s.get("calendar_date"),
                    "tile": s.get("tile"),
                    "value": (s.get("data") or [None])[0],
                    "cellsize_m": r.get("cellsize"),
                }
            )
    return rows, {
        "api_url": f"{base}/subset",
        "latest_date": last,
        "bands": [{"name": b.get("band"), "alias": b.get("description"), "units": b.get("units")} for b in bands],
        "note": "MODIS MCD12Q1 v061 yearly land cover, 500 m. Point subsets via ORNL DAAC web service (no login). Bulk tiles need a NASA Earthdata login.",
    }


def _quadkey(lat, lon, z):
    import math
    x = (lon + 180) / 360
    s = math.sin(math.radians(lat))
    y = 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)
    n = 2 ** z
    tx, ty = int(x * n), int(y * n)
    q = ""
    for i in range(z, 0, -1):
        d, m = 0, 1 << (i - 1)
        if tx & m:
            d += 1
        if ty & m:
            d += 2
        q += str(d)
    return q


@source("ms_buildings")
def fetch_ms_buildings():
    links = head_lines("https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv", 400000, max_bytes=60_000_000)
    rows = csv_rows(links)
    us = [r for r in rows if r.get("Location") in ("UnitedStates", "United States")]
    if not us:
        raise RuntimeError(f"no US rows; locations seen: {sorted({r.get('Location') for r in rows})[:20]}")
    qk = _quadkey(40.7608, -111.8910, 9)
    tile = next((r for r in us if r.get("QuadKey") == qk), us[0])
    lines = head_lines(tile["Url"], N_ROWS, gz=tile["Url"].endswith(".gz"))
    out, full = [], []
    for ln in lines:
        f = json.loads(ln)
        full.append({"type": "Feature", "properties": f.get("properties", {}), "geometry": f.get("geometry")})
        geom = f.get("geometry", {})
        coords = json.dumps(geom.get("coordinates"))
        out.append({**f.get("properties", {}), "geometry_type": geom.get("type"), "geometry": coords[:MAX_CELL]})
    return out, {
        "index_url": "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv",
        "us_tiles": len(us),
        "sample_tile": tile,
        "index_columns": list(rows[0].keys()) if rows else [],
        "note": "Each tile is a gzipped GeoJSON-lines file keyed by a zoom-9 quadkey.",
        "_geo_features": full[:GEO_FEATURES],
        "_geo_info": {"geometry_type": "Polygon", "native_crs": "EPSG:4326", "supports_pagination": None, "max_record_count": None},
    }


@source("google_open_buildings")
def fetch_google_open_buildings():
    base = "https://storage.googleapis.com/open-buildings-data/v3"
    tile_ids = ["0e9_buildings", "0c3_buildings", "0d1_buildings", "0e5_buildings", "1b9_buildings"]

    def read(tid):
        return head_lines(f"{base}/polygons_s2_level_4_gzip/{tid}.csv.gz", N_ROWS + 1, gz=True)

    url, lines = first_ok(tile_ids, read)
    rows = csv_rows(lines)
    for r in rows:
        if "geometry" in r:
            r["geometry"] = r["geometry"][:MAX_CELL]
    return rows, {
        "sample_file": f"{base}/polygons_s2_level_4_gzip/{url}.csv.gz",
        "note": "v3 polygons. Coverage is Africa, South and Southeast Asia, Latin America and the Caribbean. No United States coverage.",
    }


def bps_header(h1, h2):
    """Join the two BPS header rows into one list of column names.

    The id columns are split across both rows ("Survey" / "Date"). After them
    come 8 groups of (Bldgs, Units, Value): 4 building sizes with imputation,
    then the same 4 "reported only".
    """
    start = [x.strip() for x in h2].index("Bldgs")
    hdr = [f"{a.strip()} {b.strip()}".strip() for a, b in zip(h1[:start], h2[:start])]
    groups = ["1-unit", "2-units", "3-4 units", "5+ units"]
    groups += [g + " rep" for g in groups]
    for i, b in enumerate(h2[start:]):
        hdr.append(f"{groups[i // 3]} {b.strip()}" if i // 3 < len(groups) else b.strip())
    return hdr


@source("census_bps")
def fetch_bps():
    yr = dt.date.today().year
    out_rows, meta = [], {}
    for geo, folder, prefix in (("state", "State", "st"), ("county", "County", "co")):
        cands = [f"https://www2.census.gov/econ/bps/{folder}/{prefix}{y}a.txt" for y in (yr - 1, yr - 2)]
        url, lines = first_ok(cands, lambda u: head_lines(u, N_ROWS + 3))
        h1, h2 = next(csv.reader([lines[0]])), next(csv.reader([lines[1]]))
        hdr = bps_header(h1, h2)
        data = [l for l in lines[2:] if l.strip()]
        for r in csv.reader(data):
            out_rows.append({"geo_level": geo, **dict(zip(hdr, r))})
        meta[geo] = {"url": url, "raw_header_line1": h1, "raw_header_line2": h2}
    return out_rows[: N_ROWS * 2], meta


@source("fhfa_hpi")
def fetch_fhfa():
    links = []
    for p in ("https://www.fhfa.gov/data/hpi/datasets", "https://www.fhfa.gov/data/hpi/datasets?tab=master-hpi-data", "https://www.fhfa.gov/data/hpi/datasets?tab=additional-data"):
        try:
            links += page_links(p, r"\.(csv|xlsx|txt)$")
        except Exception:  # noqa: BLE001
            pass
    links = sorted(set(links))
    master_cands = [l for l in links if re.search(r"hpi_master\.csv$", l, re.I)] + [
        "https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv",
        "https://www.fhfa.gov/DataTools/Downloads/Documents/HPI/HPI_master.csv",
    ]
    url, lines = first_ok(master_cands, lambda u: head_lines(u, N_ROWS + 1))
    rows = csv_rows(lines)
    meta = {"master_url": url, "all_download_links_found": links[:80]}
    county = [l for l in links if re.search(r"county", l, re.I) and l.lower().endswith(".csv")]
    if county:
        try:
            cl = head_lines(county[0], 8)
            meta["county_sample_url"] = county[0]
            meta["county_sample_head"] = cl
        except Exception as e:  # noqa: BLE001
            meta["county_error"] = str(e)
    return rows, meta


@source("usps_vacancy")
def fetch_usps():
    url = "https://www.huduser.gov/portal/datasets/usps.html"
    try:
        txt = _clean(get_text(url))
        idx = txt.lower().find("governmental")
        excerpt = txt[max(0, idx - 400): idx + 600] if idx >= 0 else txt[:1000]
    except Exception as e:  # noqa: BLE001
        excerpt = f"page fetch failed: {e}"
    return [], {
        "status": "restricted",
        "page_url": url,
        "page_excerpt": excerpt,
        "note": "HUD/USPS vacancy data needs a HUD USER login and is limited to governmental entities and registered non-profits. Not fetched.",
    }


@source("ntd")
def fetch_ntd():
    cat = socrata_catalog("data.transportation.gov", "monthly ridership", 25)
    cat += socrata_catalog("data.transportation.gov", "NTD stations and facilities", 25)
    ds = [c for c in cat if c["type"] == "dataset"]
    pick = next((c for c in ds if re.search(r"complete monthly ridership", c["name"], re.I)), None) or next(
        c for c in ds if re.search(r"monthly ridership|monthly module", c["name"], re.I)
    )
    rows, meta = socrata("data.transportation.gov", pick["id"])
    st = next((c for c in ds if re.search(r"stations and facilities", c["name"], re.I)), None)
    if st:
        try:
            st_rows, st_meta = socrata("data.transportation.gov", st["id"])
            meta["stations_dataset"] = {**st_meta, "sample_rows": st_rows[:3]}
        except Exception as e:  # noqa: BLE001
            meta["stations_error"] = str(e)
    meta["catalog_hits"] = cat
    return rows, meta


@source("hcd_apr")
def fetch_hcd_apr():
    res = get_json(
        "https://data.ca.gov/api/3/action/package_search",
        {"q": "housing element annual progress report", "rows": 10},
    )["result"]["results"]
    pkgs = [{"name": p["name"], "title": p["title"], "org": (p.get("organization") or {}).get("title"), "modified": p.get("metadata_modified")} for p in res]
    pkg = next(p for p in res if re.search(r"annual progress report", p["title"], re.I))
    resources = [
        {"id": r["id"], "name": r.get("name"), "format": r.get("format"), "url": r.get("url"), "datastore_active": r.get("datastore_active"), "last_modified": r.get("last_modified")}
        for r in pkg.get("resources", [])
    ]
    tables = {}
    first_rows = None
    for r in resources:
        if not r["datastore_active"]:
            continue
        try:
            ds = get_json("https://data.ca.gov/api/3/action/datastore_search", {"resource_id": r["id"], "limit": N_ROWS})["result"]
            tables[r["name"]] = {
                "resource_id": r["id"],
                "record_count": ds.get("total"),
                "fields": [{"name": f["id"], "type": f.get("type")} for f in ds.get("fields", [])],
                "sample_rows": ds.get("records", []),
            }
            if first_rows is None or re.search(r"table a2\b|\ba2\b", r["name"] or "", re.I):
                first_rows = (r["name"], ds.get("records", []))
        except Exception as e:  # noqa: BLE001
            tables[r["name"]] = {"error": str(e)}
    rows = (first_rows[1] if first_rows else [])[:N_ROWS]
    return rows, {
        "package": {"name": pkg["name"], "title": pkg["title"], "notes": _clean(pkg.get("notes"))[:1500], "license": pkg.get("license_title"), "modified": pkg.get("metadata_modified")},
        "page_url": f"https://data.ca.gov/dataset/{pkg['name']}",
        "sample_table": first_rows[0] if first_rows else None,
        "resources": resources,
        "tables": tables,
        "other_packages_found": pkgs,
    }


# --------------------------------------------------------------------------- #
# State open data portals (from data/DATA_SOURCES.md)
# --------------------------------------------------------------------------- #
@source("az_azgeo")
def fetch_az():
    hits = hub_search("https://azgeo-data-hub-agic.hub.arcgis.com", "parcels")
    meta_extra = {"hub_search_hits": hits}
    try:
        rows, meta = first_layer_from(hits, r"parcel")
    except Exception as e:  # noqa: BLE001
        meta_extra["hub_error"] = str(e)
        rows, meta = arcgis_layer("https://gis.mcassessor.maricopa.gov/arcgis/rest/services/Parcels/MapServer/0")
        meta["note"] = "Fallback: Maricopa County Assessor parcels (AZGeo has no statewide parcel layer)."
    meta.update(meta_extra)
    return rows, meta


@source("ct_cama_parcels")
def fetch_ct():
    return arcgis_item_layer("82a733423a244c43a9d4bf552954cea9", 0)


@source("or_metro_taxlots")
def fetch_or_metro():
    errors = {}
    try:
        return arcgis_item_layer("9d3c396ffad44649bc7451465aa300f0", 0)
    except Exception as e:  # noqa: BLE001
        errors["item"] = str(e)
    for name, finder in (
        ("rlis_hub", lambda: hub_search("https://rlisdiscovery.oregonmetro.gov", "taxlots")),
        ("arcgis_search", lambda: arcgis_search("taxlots Metro Portland")),
    ):
        try:
            hits = finder()
            rows, meta = first_layer_from(hits, r"^tax ?lots \(public\)$")
            meta["lookup_log"] = errors
            meta["search_hits"] = hits
            return rows, meta
        except Exception as e:  # noqa: BLE001
            errors[name] = str(e)
    raise RuntimeError(json.dumps(errors, default=str)[:1500])


@source("or_geohub")
def fetch_or_geohub():
    meta_all = {}
    hits_p = hub_search("https://geohub.oregon.gov", "parcels")
    hits_z = hub_search("https://geohub.oregon.gov", "zoning")
    meta_all["parcel_hits"], meta_all["zoning_hits"] = hits_p, hits_z
    try:
        rows, meta = first_layer_from(hits_z, r"zon")
        meta["sampled"] = "zoning"
    except Exception as e:  # noqa: BLE001
        meta_all["zoning_error"] = str(e)
        rows, meta = first_layer_from(hits_p, r"parcel|taxlot")
        meta["sampled"] = "parcels"
    meta.update(meta_all)
    return rows, meta


@source("hi_parcels")
def fetch_hi():
    hits = hub_search("https://geoportal.hawaii.gov", "parcels")
    zhits = hub_search("https://geoportal.hawaii.gov", "zoning")
    try:
        rows, meta = first_layer_from(hits, r"parcels.*statewide")
    except Exception:  # noqa: BLE001
        rows, meta = first_layer_from(hits, r"parcel")
    meta["hub_search_hits"], meta["zoning_hits"] = hits, zhits
    return rows, meta


@source("pa_pasda")
def fetch_pa():
    url = "https://www.pasda.psu.edu/uci/SearchResults.aspx?Keyword=parcels"
    html = get_text(url)
    best = {}
    for i, t in re.findall(r"DataSummary\.aspx\?dataset=(\d+)[^>]*>(.*?)</a>", html, re.S):
        t = _clean(t)
        if t and not re.match(r"more options", t, re.I) and len(t) > len(best.get(i, "")):
            best[i] = t
    titles = list(best.items())
    rows = [{"dataset_id": i, "title": t, "summary_url": f"https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset={i}"} for i, t in titles[:N_ROWS * 2]]
    if not rows:
        i = html.find("DataSummary")
        raise RuntimeError(f"could not parse titles; html near first link: {html[max(0,i-400):i+600]!r}")
    return rows, {"search_url": url, "note": "PASDA is a catalog of county/municipal datasets (mostly shapefile downloads). Rows are catalog entries, not parcel records.", "hits": len(titles)}


PASDA_SERVICES = "https://mapservices.pasda.psu.edu/server/rest/services/pasda"
# Spread across the state: rural, suburban and urban counties.
PASDA_COUNTIES = [
    "AdamsCounty", "AlleghenyCounty", "BerksCounty", "BucksCounty",
    "CentreCounty", "LancasterCounty",
]
PASDA_ROWS_PER_COUNTY = 2


@source("pa_pasda_parcels")
def fetch_pa_parcels():
    """A few parcel rows from several county datasets in the PASDA catalog."""
    listing = get_json(PASDA_SERVICES, {"f": "json"})
    have = {s["name"].split("/")[-1]: s for s in listing.get("services", []) if s.get("type") == "MapServer"}
    picks = [c for c in PASDA_COUNTIES if c in have]
    rows, counties, union = [], {}, {}
    for svc in picks:
        base = f"{PASDA_SERVICES}/{svc}/MapServer"
        try:
            layers = get_json(base, {"f": "json"}).get("layers") or []
            parcel = [l for l in layers if re.search(r"parcel", l.get("name", ""), re.I)
                      and not re.search(r"owned|preserv|easement|agric", l.get("name", ""), re.I)]
            if not parcel:
                counties[svc] = {"error": "no parcel layer", "layers": [l.get("name") for l in layers]}
                continue
            lrows, lmeta = arcgis_layer(f"{base}/{parcel[0]['id']}")
        except Exception as e:  # noqa: BLE001
            counties[svc] = {"error": f"{type(e).__name__}: {e}"[:300]}
            continue
        names = [f["name"] for f in lmeta["fields"]]
        counties[svc] = {
            "layer_url": lmeta["service_url"],
            "layer_name": lmeta["layer_name"],
            "record_count": lmeta["record_count"],
            "last_edit_date": lmeta["last_edit_date"],
            "field_names": names,
        }
        for f in lmeta["fields"]:
            u = union.setdefault(f["name"], {"name": f["name"], "type": f["type"], "counties": []})
            u["counties"].append(svc)
        for r in lrows[:PASDA_ROWS_PER_COUNTY]:
            rows.append({"pasda_county": svc, **r})
    if not rows:
        raise RuntimeError(f"no county parcel rows; services seen: {sorted(have)[:40]}; details: {counties}")
    ok = [c for c, m in counties.items() if "field_names" in m]
    for u in union.values():
        u["description"] = f"In {len(u['counties'])} of {len(ok)} counties" + (
            "" if len(u["counties"]) == len(ok) else ": " + ", ".join(c.replace("County", "") for c in u["counties"]))
    return rows, {
        "api_url": PASDA_SERVICES,
        "note": "Each county publishes its own parcel layer with its own field names. Rows are 2 per county; columns are the union of all counties' fields, so most cells are blank.",
        "counties": counties,
        "fields": sorted(union.values(), key=lambda u: (-len(u["counties"]), u["name"].lower())),
    }


@source("tn_comptroller")
def fetch_tn():
    url = "https://comptroller.tn.gov/office-functions/pa/gisredistricting/redistricting-and-land-use-maps/parcel-data.html"
    # The form is embedded on the page; the direct Formstack link is broken.
    form = url
    try:
        txt = _clean(get_text(url))[:1500]
    except Exception as e:  # noqa: BLE001
        txt = f"page fetch failed: {e}"
    return [], {
        "status": "request_form",
        "page_url": url,
        "form_url": form,
        "page_excerpt": txt,
        "note": (
            "Free weekly-updated county shapefiles, but each download goes through a Formstack form "
            "that asks for a name, mailing address, the counties wanted, and two signed checkboxes "
            "(an attestation and a disclaimer). 86 counties are offered. Chester, Davidson, Hamilton, "
            "Hickman, Knox, Montgomery, Rutherford, Shelby and Williamson come from county assessors instead. "
            "The page also says there are no automated or recurring downloads. Not fetched automatically."
        ),
    }


@source("ut_housing_unit_inventory")
def fetch_ut_hui():
    return arcgis_layer("https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/HousingUnitInventory/FeatureServer/0")


@source("ut_parcels")
def fetch_ut_parcels():
    svc = get_json("https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services", {"f": "json"})
    names = [s["name"] for s in svc.get("services", []) if re.search(r"parcel", s["name"], re.I)]
    pick = next((n for n in names if re.search(r"SaltLake.*LIR", n, re.I)), None) or next((n for n in names if "LIR" in n), names[0])
    stype = next(s["type"] for s in svc["services"] if s["name"] == pick)
    rows, meta = arcgis_layer(f"https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/{pick}/{stype}/0")
    meta["parcel_services_found"] = names
    return rows, meta


@source("va_parcels")
def fetch_va():
    cands = [
        "https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Parcels/FeatureServer/0",
        "https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Parcels/MapServer/0",
    ]
    try:
        _, (rows, meta) = first_ok(cands, arcgis_layer)
    except Exception as e:  # noqa: BLE001
        rows, meta = first_layer_from(arcgis_search('title:"Virginia Parcels" OR title:"VA Parcels"'), r"parcel")
        meta["direct_error"] = str(e)
    try:
        d = get_json("https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers", {"f": "json"})
        meta["vgin_base_layers"] = [s["name"] for s in d.get("services", [])]
    except Exception:  # noqa: BLE001
        pass
    return rows, meta


@source("wi_parcels")
def fetch_wi():
    try:
        return arcgis_layer("https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels/FeatureServer/0")
    except Exception as e:  # noqa: BLE001
        rows, meta = first_layer_from(arcgis_search('title:"Wisconsin Statewide Parcels"'), r"parcel")
        meta["direct_error"] = str(e)
        return rows, meta


@source("ri_rigis")
def fetch_ri():
    hits = hub_search("https://www.rigis.org", "land use")
    rows, meta = first_layer_from(hits, r"land use|landuse|lulc")
    meta["hub_search_hits"] = hits
    return rows, meta


@source("nh_granit")
def fetch_nh():
    base = "https://nhgeodata.unh.edu/nhgeodata/rest/services"
    found = []
    for folder in ("", "CAD"):
        try:
            d = get_json(f"{base}/{folder}".rstrip("/"), {"f": "json"})
            found += [(s["name"], s["type"]) for s in d.get("services", [])]
            if not folder:
                found += [(f, "folder") for f in d.get("folders", [])]
        except Exception:  # noqa: BLE001
            pass
    par = [(n, t) for n, t in found if re.search(r"parcel", n, re.I) and t != "folder"]
    if not par:
        raise RuntimeError(f"no parcel service found; services seen: {found[:40]}")
    n, t = par[0]
    svc = get_json(f"{base}/{n}/{t}", {"f": "json"})
    layer = next((l["id"] for l in svc.get("layers", []) if re.search(r"parcel", l["name"], re.I)), 0)
    rows, meta = arcgis_layer(f"{base}/{n}/{t}/{layer}")
    meta["services_seen"] = found[:60]
    return rows, meta


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Sources added for the Wisconsin pipeline and California history (Oct 2026)

BUILDINGANADU_SHEET = "10rb8p7DU379vQw9oeS_Z9dwK9F9c5ZBeTw09wQlvwQY"


@source("buildinganadu_ca_adu")
def fetch_buildinganadu():
    yr = re.compile(r"\b20(1[2-9])\b")

    def load(u):
        lines = head_lines(u, 2000, max_bytes=5_000_000)
        rows_ = list(csv.reader(io.StringIO("\n".join(lines))))
        hi_ = next((i for i, r in enumerate(rows_) if sum(bool(yr.search(c)) for c in r) >= 4), None)
        if hi_ is None:
            raise RuntimeError(f"no year header row; start of response: {' | '.join(lines[:3])[:400]!r}")
        return u, rows_, hi_

    base = f"https://docs.google.com/spreadsheets/d/{BUILDINGANADU_SHEET}"
    # gid=0 is Sheet1; the bare export returns only "@dropdown", and gviz drops numbers.
    _, (url, allrows, hi) = first_ok([f"{base}/export?format=csv&gid=0"], load)
    raw = [re.sub(r"\s+", " ", c).strip() for c in allrows[hi]]
    # The sheet has a second, unlabeled side table to the right of a blank column. Keep the main block.
    width = raw.index("") if "" in raw else len(raw)
    header = raw[:width]
    years = [c for c in header if yr.search(c)]
    data = [dict(zip(header, r[:width])) for r in allrows[hi + 1:] if any(c.strip() for c in r[:width])]
    name_col = header[0]
    juris = [r for r in data if r.get(name_col, "").strip() and not re.search(r"total|compiled|source|buildinganadu", r[name_col], re.I)]

    def num(v):
        v = (v or "").replace(",", "").strip()
        return float(v) if re.fullmatch(r"-?\d+(\.\d+)?", v) else 0.0

    sums = {y: int(sum(num(r.get(y)) for r in juris)) for y in years}
    la = [r for r in juris if re.fullmatch(r"los angeles", r[name_col].strip(), re.I)]
    rows = juris[:N_ROWS] + la[:1]
    return rows, {
        "api_url": url,
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{BUILDINGANADU_SHEET}/edit",
        "page_url": "https://www.buildinganadu.com/california-adu-charts",
        "header_row": hi + 1,
        "jurisdiction_rows": len(juris),
        "year_columns": years,
        "statewide_sums": sums,
        "note": "Sums are over jurisdiction rows (our check against docs/ASSUMPTIONS_AND_QUESTIONS.md AQ-017). The last sample row is Los Angeles.",
        "fields": [{"name": c, "type": "int" if c in years else "string"} for c in header],
    }


PEP_HU_URL = "https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx"


def xlsx_rows(blob, sheet=1):
    """Read one worksheet of an .xlsx file into a list of rows (standard library only)."""
    import xml.etree.ElementTree as ET
    import zipfile

    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    z = zipfile.ZipFile(io.BytesIO(blob))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
    out = []
    for row in ET.fromstring(z.read(f"xl/worksheets/sheet{sheet}.xml")).iter(f"{{{ns['m']}}}row"):
        cells = {}
        for c in row.findall("m:c", ns):
            col = re.match(r"[A-Z]+", c.get("r")).group(0)
            v = c.find("m:v", ns)
            if v is None:
                isv = c.find("m:is", ns)
                val = "".join(t.text or "" for t in isv.iter(f"{{{ns['m']}}}t")) if isv is not None else ""
            elif c.get("t") == "s":
                val = shared[int(v.text)]
            else:
                val = v.text
            cells[col] = val
        if cells:
            width = max(_col_index(k) for k in cells) + 1
            out.append([cells.get(_col_letter(i), "") for i in range(width)])
    return out


def _col_index(letters):
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def _col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


@source("census_pep_housing_units")
def fetch_pep_hu():
    grid = xlsx_rows(get_bytes(PEP_HU_URL))
    title = " ".join(c for c in grid[0] if c) if grid else ""
    hi = next(i for i, r in enumerate(grid) if any(re.fullmatch(r"2020", str(c).split(".")[0]) for c in r))
    top = grid[hi - 1] if hi else []
    header = []
    for i, c in enumerate(grid[hi]):
        c = str(c).split(".")[0] if re.fullmatch(r"\d{4}(\.0)?", str(c)) else str(c)
        above = top[i] if i < len(top) else ""
        header.append(re.sub(r"\s+", " ", c or above or ("Geographic Area" if i == 0 else f"col_{i}")).strip())
    rows = []
    for r in grid[hi + 1:]:
        if not r or not str(r[0]).strip():
            continue
        if re.match(r"(note|source|suggested citation|release date)", str(r[0]), re.I):
            break
        rows.append(dict(zip(header, r)))
    return rows[:N_ROWS + 1], {
        "api_url": PEP_HU_URL,
        "title": title,
        "header_row": hi + 1,
        "county_rows": max(len(rows) - 1, 0),
        "note": "Rows are Wisconsin, then its counties. Sub-county PEP files hold population only, not housing units.",
        "fields": [{"name": h, "type": "int" if re.fullmatch(r"\d{4}", h) else "string"} for h in header],
    }


TIGER_COUSUB_URL = "https://www2.census.gov/geo/tiger/TIGER2024/COUSUB/tl_2024_55_cousub.zip"


def dbf_rows(blob, n):
    """First n records and the field list of a dBase (.dbf) file."""
    import struct

    nrec, hlen, rlen = struct.unpack("<IHH", blob[4:12])
    fields, pos = [], 32
    while blob[pos] != 0x0D:
        name = blob[pos:pos + 11].split(b"\0")[0].decode("ascii", "replace")
        ftype, flen = chr(blob[pos + 11]), blob[pos + 16]
        fields.append({"name": name, "type": {"C": "string", "N": "number", "F": "number", "D": "date", "L": "bool"}.get(ftype, ftype), "length": flen})
        pos += 32
    rows = []
    for i in range(min(n, nrec)):
        rec = blob[hlen + i * rlen: hlen + (i + 1) * rlen]
        off, r = 1, {}
        for f in fields:
            r[f["name"]] = rec[off:off + f["length"]].decode("utf-8", "replace").strip()
            off += f["length"]
        rows.append(r)
    return rows, fields, nrec


@source("census_tiger")
def fetch_tiger():
    import zipfile

    z = zipfile.ZipFile(io.BytesIO(get_bytes(TIGER_COUSUB_URL)))
    names = z.namelist()
    dbf = next(n for n in names if n.endswith(".dbf"))
    rows, fields, nrec = dbf_rows(z.read(dbf), N_ROWS)
    prj = next((z.read(n).decode("ascii", "replace") for n in names if n.endswith(".prj")), "")
    return rows, {
        "api_url": TIGER_COUSUB_URL,
        "record_count": nrec,
        "files_in_zip": names,
        "projection": prj[:300],
        "geometry_type": "Polygon (in the .shp file; not sampled)",
        "note": "Sample is Wisconsin county subdivisions (towns, cities, villages), the layer the pipeline uses as its municipality key. The same field pattern applies to the state, county, place, tract and block group files.",
        "fields": fields,
    }


MADISON_PARCELS = "https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA2/FeatureServer/0"
MADISON_ADDRESS_POINTS = "https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/20"
MADISON_ZONING = "https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/9"
WI_ASSEMBLY_2024 = "https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services/WI_Assembly_Districts_2024/FeatureServer/0"


@source("madison_parcels")
def fetch_madison_parcels():
    return arcgis_layer(MADISON_PARCELS)


@source("madison_address_points")
def fetch_madison_address_points():
    return arcgis_layer(MADISON_ADDRESS_POINTS)


@source("madison_zoning")
def fetch_madison_zoning():
    return arcgis_layer(MADISON_ZONING)


@source("wi_assembly_districts")
def fetch_wi_assembly():
    return arcgis_layer(WI_ASSEMBLY_2024)


@source("madison_permits")
def fetch_madison_permits():
    """A short window of the city's Construction Summary report, via the pipeline's own client."""
    sys.path.insert(0, str(ROOT))
    from missing_middleware.permits import madison as mad  # needs the package installed (pandas)

    end = dt.date.today().replace(day=1) - dt.timedelta(days=1)
    start = end - dt.timedelta(days=13)
    data = mad.fetch_report_csv(start, end)
    text = data.decode("utf-8-sig", "replace")
    recs = [r for r in csv.DictReader(io.StringIO(text)) if mad.PERMIT_ID_RE.match((r.get("B1_ALT_ID") or "").strip())]
    drop = set(mad.OWNER_COLUMNS) | {c for c in (recs[0].keys() if recs else []) if c.lower().startswith("contractor")}
    keep = [{k: v for k, v in r.items() if k not in drop} for r in recs]
    nrc = [r for r in keep if r["B1_ALT_ID"].startswith("BLDNRC")]
    rows = (nrc + [r for r in keep if r not in nrc])[:N_ROWS]
    return rows, {
        "api_url": mad.REPORT_URL,
        "window": f"{start} to {end}",
        "records_in_window": len(recs),
        "dropped_columns": sorted(drop),
        "note": "SSRS report, run for a two-week window. Owner and contractor columns are dropped at fetch, as the pipeline does. New residential permits (BLDNRC) are listed first.",
        "fields": [{"name": c, "type": "string"} for c in (rows[0].keys() if rows else [])],
    }


GEO_OUT = OUT / "geo"
GEO_FEATURES = 3
GEO_MAX_BYTES = 150_000


def _esri_to_geojson(g):
    """Convert an Esri JSON geometry (already in WGS84) to GeoJSON."""
    if not g:
        return None
    if "x" in g:
        return {"type": "Point", "coordinates": [g["x"], g["y"]]}
    if "rings" in g:
        return {"type": "Polygon", "coordinates": g["rings"]}
    if "paths" in g:
        return {"type": "MultiLineString", "coordinates": g["paths"]}
    if "points" in g:
        return {"type": "MultiPoint", "coordinates": g["points"]}
    return None


def _count_vertices(c):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return 1
    return sum(_count_vertices(x) for x in c) if isinstance(c, (list, tuple)) else 0


def _thin(c, step):
    """Keep every step-th vertex of each ring or line, plus its last vertex."""
    if c and isinstance(c[0], (int, float)):
        return c
    if c and isinstance(c[0], list) and c[0] and isinstance(c[0][0], (int, float)):
        kept = c[::step]
        if kept[-1] != c[-1]:
            kept.append(c[-1])
        return kept if len(kept) >= 4 or len(c) < 4 else c[:1] + c[len(c) // 3:len(c) // 3 + 1] + c[2 * len(c) // 3:2 * len(c) // 3 + 1] + c[-1:]
    return [_thin(x, step) for x in c]


def arcgis_geo_sample(url, n=GEO_FEATURES):
    """A few complete features (geometry and attributes) from an ArcGIS layer, as GeoJSON in WGS84."""
    url = url.rstrip("/")
    info = get_json(url, {"f": "json"})
    q = {"where": "1=1", "outFields": "*", "returnGeometry": "true", "outSR": "4326", "resultRecordCount": n}
    feats = []
    try:
        res = get_json(url + "/query", {**q, "f": "geojson"})
        feats = res.get("features") or []
    except Exception:  # noqa: BLE001
        feats = []
    if not feats:
        res = get_json(url + "/query", {**q, "f": "json"})
        if "error" in res:
            res = get_json(url + "/query", {**{k: v for k, v in q.items() if k != "resultRecordCount"},
                                            "where": f"{info.get('objectIdField') or 'OBJECTID'} <= 20", "f": "json"})
        if "error" in res:
            raise RuntimeError(f"geometry query error: {res['error']}")
        feats = [{"type": "Feature", "properties": f.get("attributes", {}), "geometry": _esri_to_geojson(f.get("geometry"))}
                 for f in res.get("features", [])]
    feats = feats[:n]
    sr = (info.get("extent") or {}).get("spatialReference") or info.get("sourceSpatialReference") or {}
    adv = info.get("advancedQueryCapabilities") or {}
    return feats, {
        "layer_url": url,
        "geometry_type": (info.get("geometryType") or "").replace("esriGeometry", ""),
        "native_crs": {"wkid": sr.get("wkid"), "latestWkid": sr.get("latestWkid")},
        "supports_pagination": adv.get("supportsPagination"),
        "max_record_count": info.get("maxRecordCount"),
    }


def write_geo(sid, feats, info):
    """Write a small GeoJSON sample with full geometry. Drops features if the file gets too big."""
    GEO_OUT.mkdir(parents=True, exist_ok=True)
    feats = [{**f, "properties": redact([f.get("properties") or {}])[0]} for f in feats]
    while True:
        text = json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"))
        if len(text) <= GEO_MAX_BYTES or len(feats) <= 1:
            break
        feats = feats[:-1]
    simplified = None
    if len(text) > GEO_MAX_BYTES:
        # One feature is still too big (for example a legislative district): keep every n-th vertex.
        orig = feats[0]
        before = _count_vertices((orig.get("geometry") or {}).get("coordinates"))
        step = 2
        while len(text) > GEO_MAX_BYTES and step < 10_000:
            g = dict(orig["geometry"], coordinates=_thin(orig["geometry"]["coordinates"], step))
            feats = [dict(orig, geometry=g)]
            text = json.dumps({"type": "FeatureCollection", "features": [feats[0]]}, separators=(",", ":"))
            step *= 2
        simplified = {"original_vertices": before, "kept_every_nth_vertex": step // 2}
    path = GEO_OUT / f"{sid}.geojson"
    path.write_text(text + "\n")
    verts = [_count_vertices((f.get("geometry") or {}).get("coordinates")) for f in feats]
    return {
        **info,
        "simplified": simplified,
        "file": f"data/sample/geo/{sid}.geojson",
        "features": len(feats),
        "bytes": len(text),
        "vertices_per_feature": verts,
        "output_crs": "EPSG:4326 (GeoJSON)",
    }


def add_geometry(sid, meta):
    """Save full-geometry features next to the attribute sample, when the source has geometry."""
    feats = meta.pop("_geo_features", None)
    info = meta.pop("_geo_info", {})
    if feats is None and meta.get("service_url"):
        feats, info = arcgis_geo_sample(meta["service_url"])
    if feats is None and meta.get("counties"):
        feats = []
        for county, m in meta["counties"].items():
            if not m.get("layer_url"):
                continue
            try:
                f1, i1 = arcgis_geo_sample(m["layer_url"], 1)
            except Exception as e:  # noqa: BLE001
                m["geometry_error"] = f"{type(e).__name__}: {e}"[:200]
                continue
            for f in f1:
                f["properties"] = {"pasda_county": county, **(f.get("properties") or {})}
            feats += f1
            m["native_crs"] = i1["native_crs"]
            m["supports_pagination"] = i1["supports_pagination"]
            m["max_record_count"] = i1["max_record_count"]
            info = info or {k: v for k, v in i1.items() if k != "layer_url"}
        info["native_crs"] = "varies by county; see counties"
    if not feats:
        return
    meta["geometry_sample"] = write_geo(sid, feats, info)


def _cell(v):
    if isinstance(v, (dict, list)):
        v = json.dumps(v)
    s = "" if v is None else str(v)
    return s if len(s) <= MAX_CELL else s[:MAX_CELL] + "..."


PII_FIELDS = re.compile(r"owner|ownernme|mail|pstladress|co_owner|grantee|taxpayer|care_of|^name[0-9]$", re.I)
PII_KEEP = re.compile(r"^(ownertype|owner_type|unitowner|ownername|majorowner|homeowner|owneroccupied|ownerchangedate|mailcode)$", re.I)


def redact(rows):
    """Blank out owner names and mailing addresses. Field names stay."""
    out = []
    for r in rows:
        out.append({k: ("[redacted]" if PII_FIELDS.search(k) and not PII_KEEP.match(k) and r.get(k) not in (None, "") else v) for k, v in r.items()})
    return out


def write_rows(path, rows):
    rows = redact(rows)
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: _cell(r.get(k)) for k in cols})


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    want = argv or list(SOURCES)
    report_path = OUT / "_fetch_report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    for sid in want:
        fn = SOURCES[sid]
        started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        try:
            rows, meta = fn()
            status = meta.get("status") or ("ok" if rows else "no_rows")
            err = None
        except Exception as e:  # noqa: BLE001
            rows, meta, status = [], {}, "error"
            err = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        if status == "ok":
            try:
                add_geometry(sid, meta)
            except Exception as e:  # noqa: BLE001
                meta.pop("_geo_features", None)
                meta["geometry_sample_error"] = f"{type(e).__name__}: {e}"[:300]
        meta = {"source_id": sid, "fetched_at": started, "status": status, "error": err, "sample_rows": len(rows), **meta}
        (OUT / f"{sid}.meta.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
        if rows:
            write_rows(OUT / f"{sid}.csv", rows)
        report[sid] = {"status": status, "rows": len(rows), "fetched_at": started, "error": err}
        print(f"[{status:>12}] {sid} rows={len(rows)} {err or ''}", flush=True)
    report_path.write_text(json.dumps(dict(sorted(report.items())), indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])

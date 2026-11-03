"""Feasibility check: did Los Angeles widen its AB 2097 ("Reduced Parking Area") map, and can the added area be rebuilt?

Feasibility only: dates, maps and rough counts. No outcome comparison.

Step 1 (fetch, --fetch): downloads public files to data/raw/parking_la_ab2097_map/ and records each in _sources.json
(URL, licence, access time, bytes, sha256):
  - HCD technical-assistance letters to Los Angeles (2023-11-17, 2024-03-08, 2024-03-28) and HCD's AB 2097 fact sheet;
  - LA City Planning AB 2097 memos (2022-12-29, 2023-10-23), the 2024-04-16 transit methodology memo, the AB 2097
    web page and the AB 2097 case-filings export;
  - SCAG major transit stop layers: 2016 existing (Connect SoCal 2020 base year), 2045 plan year (Connect SoCal 2020,
    SCAG data re-hosted by LA County Planning), 2022 base and 2050 plan year (Connect SoCal 2024, since re-issued under
    AB 2553's 20-minute rule);
  - LA City Planning's 2026 citywide "AB2097_clip" polygon (ArcGIS Online, source credited to SCAG);
  - LA County parcel centroids (2022 roll) in a box around the City, for rough lot counts.

Step 2 (count, default): rough area, parcel and new-home permit counts in the areas each alternative map adds over a
2016-existing-stops baseline, inside the City of Los Angeles. Geometry with missing_middleware.geom only.
Permits: HCD APR Table A2, the same loading and duplicate rules as scripts/run_parking_causal_e1.py (permit year =
year of BP_ISSUE_DT1, else report year; TOD exact-duplicate rule and the D5 cross-year re-report rule dropped).

Outputs: reference/parking_la_ab2097_map_counts.csv (aggregates only).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import gzip
import hashlib
import io
import json
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from missing_middleware import geom as G  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

OUT = RAW / "parking_la_ab2097_map"
UA = "Mozilla/5.0 (research; housing study; public data)"
HALF_MILE = 804.672
CRS = 3310
CELL = 25.0  # metres, grid for areas

PUBLIC_CA = "California state government public record (HCD website)"
PUBLIC_LA = "City of Los Angeles public record (City Planning website)"
SCAG_LIC = ("SCAG open data, provided 'as is' for general planning and informational purposes (item licenseInfo); "
            "public government data")
LACO_LIC = ("LA County eGIS Hub Terms of Use (https://egis-lacounty.hub.arcgis.com/pages/terms-of-use): licence to copy, "
            "publish, distribute, adapt and exploit the Data")

DOCS = {
    "hcd_la-ta-ab2097-hau485-11172023.pdf": ("https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/HAU/la-ta-ab2097-hau485-11172023.pdf", PUBLIC_CA),
    "hcd_los-angeles-hau631-ta-03082024.pdf": ("https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/HAU/los-angeles-hau631-ta-03082024.pdf", PUBLIC_CA),
    "hcd_losangeles-hau485-ta-03292024.pdf": ("https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/HAU/losangeles-hau485-ta-03292024.pdf", PUBLIC_CA),
    "hcd_min-parking-requirements-ab-2097.pdf": ("https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/min-parking-requirements-ab-2097.pdf", PUBLIC_CA),
    "lacp_Implementation_Memo__AB_2097.pdf": ("https://planning.lacity.gov/odocument/515b047a-7d54-4605-98a3-79177b4074c6/Implementation_Memo__AB_2097.pdf", PUBLIC_LA),
    "lacp_AB2097_Memo_Oct_2023.pdf": ("https://planning.lacity.gov/odocument/ecf69160-4a89-4078-a0b6-15ad6fdfbc33/AB2097_Memo_Oct_2023.pdf", PUBLIC_LA),
    "lacp_Methodology_for_Determining_Bus_Transit_MEMO.pdf": ("https://planning.lacity.gov/odocument/c908cda7-6291-4c0f-834c-4109e920bd5a/Methodology_for_Determining_Bus_Transit_MEMO.pdf", PUBLIC_LA),
    "lacp_ab2097_page.html": ("https://planning.lacity.gov/project-review/assembly-bill-2097", PUBLIC_LA),
    "lacp_ab2097_cases.xlsx": ("https://planning.lacity.gov/dcpapi/general/ab2097cases/excel", PUBLIC_LA),
}

LAYERS = {  # name: (query base url, item id for licence, licence, note)
    "scag_mts_2016_existing": ("https://services5.arcgis.com/YzWImMY4GtDcMxOx/ArcGIS/rest/services/MajorTransitStopsPoint/FeatureServer/0",
                               "541c4409dd5448f1a7df8f87e90f804a", SCAG_LIC,
                               "SCAG Major Transit Stops (Year 2016): existing stops, Connect SoCal 2020 base year, 15-minute rule"),
    "scag_mts_2045_plan": ("https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/MajorStops2045_SCAG/FeatureServer/9",
                           "5408f1c1691c4c08b5aa09edb6824dc4", SCAG_LIC + "; re-hosted by LA County Planning",
                           "SCAG major transit stops for plan year 2045 (Connect SoCal 2020, 'updated as of February 2020'): existing plus planned"),
    "scag_mts_2022_base": ("https://maps.scag.ca.gov/scaggis/rest/services/OpenData/Major_Transit_Stops_Plan_Year_2022/MapServer/0",
                           "7c2ef342de224f06b24baae1a73a2a15", SCAG_LIC,
                           "SCAG major transit stops base year 2022 (Connect SoCal 2024), re-issued under AB 2553 20-minute rule"),
    "scag_mts_2050_plan": ("https://maps.scag.ca.gov/scaggis/rest/services/OpenData/Major_Transit_Stops_Plan_Year_2050/MapServer/0",
                           "8bfbed890c91423cabe9ccc20369cdca", SCAG_LIC,
                           "SCAG major transit stops plan year 2050 (Connect SoCal 2024), re-issued under AB 2553 20-minute rule"),
    "lacp_ab2097_clip_2026": ("https://services1.arcgis.com/tzwalEyxl2rpamKs/arcgis/rest/services/AB_2097_Exempts_parking_minimums_within_a_half_mile_of_major_transit/FeatureServer/56",
                              None, "City of Los Angeles City Planning public ArcGIS Online item (credit: SCAG); public government data",
                              "LA City Planning citywide AB 2097 area polygon (one dissolved feature), data last edited 2026-04-30; 20-minute (AB 2553) definition in item text"),
}
LA_PARCELS = "https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcels_2022Roll/FeatureServer/0"
LA_BOX = (-118.67, 33.70, -118.15, 34.34)


# ------------------------------------------------------------------------------------------------ fetch helpers
def _get(url: str, data: bytes | None = None, tries: int = 4) -> bytes:
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(3 * (k + 1))
    raise RuntimeError(url)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _record(src: dict, name: str, url: str, blob: bytes, licence: str, **extra) -> None:
    src[name] = {"url": url, "licence": licence, "accessed_utc": _now(), "bytes": len(blob),
                 "sha256": hashlib.sha256(blob).hexdigest(), **extra}


def _query_all(base: str, where: str = "1=1", extra: dict | None = None, page: int = 1000) -> dict:
    feats, off = [], 0
    while True:
        q = {"where": where, "outFields": "*", "returnGeometry": "true", "outSR": "4326", "f": "geojson",
             "resultOffset": off, "resultRecordCount": page, "orderByFields": "OBJECTID"}
        q.update(extra or {})
        js = json.loads(_get(base + "/query?" + urllib.parse.urlencode(q)))
        f = js.get("features", [])
        feats += f
        if len(f) < page and not js.get("exceededTransferLimit") and not (js.get("properties") or {}).get("exceededTransferLimit"):
            break
        off += len(f)
        if not f:
            break
    return {"type": "FeatureCollection", "features": feats}


def fetch() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sp = OUT / "_sources.json"
    src = json.loads(sp.read_text()) if sp.exists() else {}
    for name, (url, lic) in DOCS.items():
        blob = _get(url)
        (OUT / name).write_bytes(blob)
        _record(src, name, url, blob, lic)
    for name, (base, item, lic, note) in LAYERS.items():
        page = 1000 if "scag.ca.gov" in base else 2000
        oid = "OBJECTID" if "MajorTransitStopsPoint" not in base else "FID"
        gj = _query_all(base, extra={"orderByFields": oid}, page=page)
        blob = json.dumps(gj).encode()
        (OUT / f"{name}.geojson").write_bytes(blob)
        _record(src, f"{name}.geojson", base + "/query (paged, where=1=1, outSR=4326, f=geojson)", blob, lic,
                features=len(gj["features"]), note=note)
        meta = _get(base + "?f=json")
        (OUT / f"{name}_layer.json").write_bytes(meta)
        _record(src, f"{name}_layer.json", base + "?f=json", meta, "metadata")
        if item:
            im = _get(f"https://www.arcgis.com/sharing/rest/content/items/{item}?f=json")
            (OUT / f"{name}_item.json").write_bytes(im)
            _record(src, f"{name}_item.json", f"https://www.arcgis.com/sharing/rest/content/items/{item}?f=json", im, "metadata")
    for item in ("1409032f895c42c58a4337beadbac7a4", "62a9e15f4fca490490e096faa1705c7e"):
        im = _get(f"https://www.arcgis.com/sharing/rest/content/items/{item}?f=json")
        (OUT / f"lacp_item_{item}.json").write_bytes(im)
        _record(src, f"lacp_item_{item}.json", f"https://www.arcgis.com/sharing/rest/content/items/{item}?f=json", im, "metadata")
    zl = _get("https://zimas.lacity.org/arcgis/rest/services/zma/zimas/MapServer/layers?f=json")
    (OUT / "zimas_mapserver_layers.json").write_bytes(zl)
    _record(src, "zimas_mapserver_layers.json", "https://zimas.lacity.org/arcgis/rest/services/zma/zimas/MapServer/layers?f=json", zl,
            "City of Los Angeles public ArcGIS service metadata", note="group layer 1500 'AB 2097 Entitlement Areas' has no public sublayers")
    sp.write_text(json.dumps(src, indent=1))
    fetch_parcels(src)
    sp.write_text(json.dumps(src, indent=1))


def fetch_parcels(src: dict, step: float = 0.04) -> None:
    """Parcel centroids (no APN, no address) in a box around the City of Los Angeles, fetched in small tiles
    (large offsets on one big envelope time out). Tiles are cached in a hidden folder so a rerun resumes; the
    cache is removed once the combined file is written. A parcel touching two tiles is kept once (by OBJECTID)."""
    cache = OUT / ".parcel_tiles"
    cache.mkdir(exist_ok=True)
    x0, y0, x1, y1 = LA_BOX
    tiles = [(round(x, 4), round(y, 4), round(min(x + step, x1), 4), round(min(y + step, y1), 4))
             for x in np.arange(x0, x1, step) for y in np.arange(y0, y1, step)]

    def tile(t) -> pd.DataFrame:
        f = cache / ("t_%s.csv" % "_".join(map(str, t)))
        if f.exists():
            return pd.read_csv(f)
        rows, off = [], 0
        while True:
            q = {"where": "1=1", "geometry": ",".join(map(str, t)), "geometryType": "esriGeometryEnvelope", "inSR": "4326",
                 "spatialRel": "esriSpatialRelIntersects", "outFields": "OBJECTID_1,UseType", "returnGeometry": "false",
                 "returnCentroid": "true", "outSR": "4326", "orderByFields": "OBJECTID_1", "resultOffset": off,
                 "resultRecordCount": 2000, "f": "json"}
            js = {}
            for k in range(6):
                try:
                    js = json.loads(_get(LA_PARCELS + "/query?" + urllib.parse.urlencode(q)))
                except Exception:  # noqa: BLE001
                    js = {}
                if "features" in js:
                    break
                time.sleep(10 * (k + 1))
            else:
                raise RuntimeError(f"parcel tile {t} offset {off}: {js}")
            feats = js["features"]
            rows += [{"oid": g["attributes"]["OBJECTID_1"], "use": g["attributes"]["UseType"],
                      "lon": (g.get("centroid") or {}).get("x"), "lat": (g.get("centroid") or {}).get("y")} for g in feats]
            if len(feats) < 2000 and not js.get("exceededTransferLimit"):
                break
            off += len(feats)
        d = pd.DataFrame(rows, columns=["oid", "use", "lon", "lat"])
        d.to_csv(f, index=False)
        return d
    with cf.ThreadPoolExecutor(3) as ex:
        parts = list(ex.map(tile, tiles))
    df = pd.concat(parts).drop_duplicates("oid").sort_values("oid").drop(columns="oid")
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(df.to_csv(index=False).encode())
    blob = buf.getvalue()
    (OUT / "la_parcel_centroids_2022roll.csv.gz").write_bytes(blob)
    _record(src, "la_parcel_centroids_2022roll.csv.gz",
            LA_PARCELS + "/query?where=1=1&geometryType=esriGeometryEnvelope&outFields=OBJECTID_1,UseType&returnCentroid=true "
            f"(tiles of {step} degrees over box {LA_BOX}, paged)", blob, LACO_LIC, rows=len(df),
            note="centroid lon/lat and UseType only; OBJECTID used only to de-duplicate tiles")
    for f in cache.glob("t_*.csv"):
        f.unlink()
    cache.rmdir()


# ------------------------------------------------------------------------------------------------ counts
def la_city() -> list:
    z = RAW / "census_tiger_2024_ca_place" / "tl_2024_06_place.zip"
    lay = G.read_shapefile(z, columns=["GEOID", "NAME"])
    lay = lay.subset(lay.attrs.GEOID.astype(str) == "0644000").to_crs(CRS)
    return lay.polys


def stops(name: str, mask_fn=None) -> tuple[np.ndarray, np.ndarray]:
    lay = G.read_geojson(OUT / f"{name}.geojson")
    if mask_fn is not None:
        lay = lay.subset(mask_fn(lay.attrs))
    lay = lay.to_crs(CRS)
    ok = np.isfinite(lay.x) & np.isfinite(lay.y)
    return lay.x[ok], lay.y[ok]


def within(px, py, sx, sy) -> np.ndarray:
    _, d = G.nearest(px, py, sx, sy, max_distance=HALF_MILE)
    return np.isfinite(d) & (d <= HALF_MILE)


def load_permits_la() -> pd.DataFrame:
    import run_parking_causal_e1 as e1
    p, _ = e1.load_permits()
    p = p[(p.juris == "LOS ANGELES") & p.in_window & ~p.dup_tod & ~p.dup_cross_year].copy()
    return p


def count() -> pd.DataFrame:
    city = la_city()
    # grid over the city for areas
    allxy = np.concatenate([r for f in city for part in f for r in part])
    xs = np.arange(allxy[:, 0].min(), allxy[:, 0].max(), CELL) + CELL / 2
    ys = np.arange(allxy[:, 1].min(), allxy[:, 1].max(), CELL) + CELL / 2
    gx, gy = np.meshgrid(xs, ys)
    gx, gy = gx.ravel(), gy.ravel()
    inside = G.points_in_any(gx, gy, city)
    gx, gy = gx[inside], gy[inside]

    caltrans = G.read_geojson(RAW / "ab2097" / "major_transit_stops.geojson")
    ct = caltrans.to_crs(CRS)
    ct_plan = ct.attrs.plan_name.fillna("").str.strip() != ""
    sets = {
        "scag2016_existing": stops("scag_mts_2016_existing"),
        "scag2045_plan": stops("scag_mts_2045_plan"),
        "scag2022_base_ab2553": stops("scag_mts_2022_base"),
        "scag2050_plan_ab2553": stops("scag_mts_2050_plan"),
        "caltrans_existing_now": (ct.x[~ct_plan.values], ct.y[~ct_plan.values]),
        "caltrans_existing_plus_planned_now": (ct.x, ct.y),
    }
    dcp = G.read_geojson(OUT / "lacp_ab2097_clip_2026.geojson").to_crs(CRS).polys

    def flags(px, py) -> dict:
        f = {k: within(px, py, *v) for k, v in sets.items()}
        f["dcp2026_polygon"] = G.points_in_any(px, py, dcp, union=True)
        return f

    # comparisons: (label, base flag, wider flag, what the change is)
    comps = [
        ("A planned stops, Connect SoCal 2020", "scag2016_existing", "scag2045_plan",
         "SCAG 2045 plan-year stops (existing + planned) over SCAG 2016 existing stops"),
        ("B planned stops, Connect SoCal 2024 (AB 2553 version)", "scag2022_base_ab2553", "scag2050_plan_ab2553",
         "SCAG 2050 plan-year over 2022 base-year stops"),
        ("C planned stops, Caltrans current layer", "caltrans_existing_now", "caltrans_existing_plus_planned_now",
         "Caltrans layer: existing (GTFS, 20-min) plus RTP planned over existing only"),
        ("D City 2026 polygon over SCAG 2016 existing", "scag2016_existing", "dcp2026_polygon",
         "LA City Planning 2026 AB2097_clip over SCAG 2016 existing-stop buffers (method, AB 2553, new service and planned stops mixed)"),
        ("E SCAG 2016 existing over nothing (reference)", None, "scag2016_existing", "whole 2016-existing half-mile area"),
        ("F City 2026 polygon (reference)", None, "dcp2026_polygon", "whole City 2026 AB 2097 polygon"),
    ]
    gf = flags(gx, gy)
    cell_mi2 = CELL * CELL / 2.589988e6

    pfile = OUT / "la_parcel_centroids_2022roll.csv.gz"
    par = pd.read_csv(pfile) if pfile.exists() else pd.DataFrame({"use": [], "lon": [], "lat": []})
    par = par.dropna(subset=["lon", "lat"])
    px, py = G.transform(par.lon.values, par.lat.values, 4326, CRS)
    pin = G.points_in_any(px, py, city)
    px, py, puse = px[pin], py[pin], par.use.values[pin]
    pf = flags(px, py)

    pm = load_permits_la()
    mx, my = G.transform(pm.lon.values, pm.lat.values, 4326, CRS)
    min_ = G.points_in_any(mx, my, city)
    mf = flags(mx, my)

    rows = []
    for label, base, wide, what in comps:
        def sel(f):
            w = f[wide]
            return w & ~f[base] if base else w
        g, p, m = sel(gf), sel(pf), sel(mf) & min_
        r = {"comparison": label, "what": what, "area_sq_mi": round(g.sum() * cell_mi2, 2),
             "city_area_sq_mi": round(len(gx) * cell_mi2, 1), "parcels_all": int(p.sum()),
             "parcels_residential": int((p & (puse == "Residential")).sum()), "parcels_in_city": int(len(px))}
        for y in range(2018, 2026):
            k = m & (pm.year.values == y)
            r[f"permit_records_{y}"] = int(k.sum())
            r[f"permit_homes_{y}"] = float(pm.units.values[k].sum())
        rows.append(r)
    tot = {"comparison": "Z all City of LA permits (reference)", "what": "geocoded, in city boundary"}
    for y in range(2018, 2026):
        k = min_ & (pm.year.values == y)
        tot[f"permit_records_{y}"] = int(k.sum())
        tot[f"permit_homes_{y}"] = float(pm.units.values[k].sum())
    rows.append(tot)
    out = pd.DataFrame(rows)
    if not len(px):  # parcel centroids not fetched: leave parcel columns out rather than report zeros
        out = out.drop(columns=["parcels_all", "parcels_residential", "parcels_in_city"])
    out.to_csv(REFERENCE / "parking_la_ab2097_map_counts.csv", index=False)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--fetch-parcels", action="store_true", help="only the parcel centroids")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    elif a.fetch_parcels:
        sp = OUT / "_sources.json"
        src = json.loads(sp.read_text())
        fetch_parcels(src)
        sp.write_text(json.dumps(src, indent=1))
    pd.set_option("display.width", 250)
    print(count().T.to_string())

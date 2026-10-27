"""Download the land and zoning inputs for the TOD station-area tables (TOD Gate 2, WP4).

    uv run --all-extras python scripts/fetch_tod_parcels_zoning.py [--only v12|mke_zoning|mad_zoning|mad_tod|docs] [--counties all]

Needs network and reference/tod_stops.csv (built by scripts/build_tod_stops.py).

Raw (git-ignored), all under data/raw/tod_capacity/:
- v12_<county>.geojson: Wisconsin V12 statewide parcels (SCO / DOA REST service) for Milwaukee and Dane
  counties (default) or every county with a qualifying stop (--counties all: also Eau Claire, Kenosha,
  Ozaukee and Waukesha), only parcels intersecting a 0.6-mile buffer of the qualifying stops in
  reference/tod_stops.csv (every stop there, i.e. the widest major-stop definition (c), so the main case,
  the high case and the all-1/2-mile sensitivities are all covered with a margin). Owner and address
  fields are never requested.
- mke_zoning.geojson: City of Milwaukee zoning districts (planning/zoning MapServer layer 11, CC BY),
  same spatial filter.
- mad_zoning.geojson: City of Madison zoning districts (Public/OPEN_DATA MapServer layer 9), whole city.
- data/raw/madison_tod/tod_boundary.geojson (outside tod_capacity/, where the build scripts read it): the City
  of Madison Transit-Oriented Development Overlay District boundary (Public/OPEN_DATA_PLANNING MapServer
  layer 16; open data item 4d890b70259846ddb626fcf85af69235), one dissolved polygon. Saved as served, with
  its own data/raw/madison_tod/manifest.json (owner decision T5-4, AQ-055).
- docs/: the source documents behind the hand-coded zoning rule tables (reference/tod_zoning_rules_*.csv):
  Madison's Zoning District Summary PDF (live) and Internet Archive copies of Milwaukee Chapter 295
  subchapters 5 to 9 (the city site returns a Cloudflare challenge to scripts; owner decision D2), and
  the adopted text of Common Council file 240997 (RT5 district) from Milwaukee Legistar.
- manifest.json: URL, access time (UTC), bytes, SHA-256, licence or terms, feature counts, and the
  already-present raw files reused (Madison tax parcels, Milwaukee MPROP).

Method and rules: docs/tod/STATION_AREAS.md, docs/tod/research/WI_CAPACITY_DATA.md.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

D = RAW / "tod_capacity"
UA = {"User-Agent": "missing-middleware research (housing policy model)"}
CRS_M = 3071  # Wisconsin Transverse Mercator (NAD83(HARN)), metres
MILE_M = 1609.344
BUFFER_MILES = 0.6
CELL_M = 2000.0

V12_URL = "https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels_DB/FeatureServer/0"
# No owner, mailing-address or site-address fields (privacy rule, LESSONS_FROM_ADU section 4).
V12_FIELDS = ("OBJECTID,STATEID,PARCELID,TAXPARCELID,TAXROLLYEAR,PLACENAME,CONAME,PROPCLASS,AUXCLASS,"
              "LNDVALUE,IMPVALUE,ESTFMKVALUE,ASSDACRES,DEEDACRES,GISACRES,PARCELFIPS")
V12_LICENCE = "Public records (Wis. Stat. 59.72); SCO: 'provided free of charge', no warranty"
MKE_ZONING_URL = "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/planning/zoning/MapServer/11"
MKE_ZONING_LICENCE = "Creative Commons Attribution (data.milwaukee.gov dataset 'zoning'), City of Milwaukee"
MAD_ZONING_URL = "https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/9"
MAD_LICENCE = "City of Madison open data; no licence stated on the service (public record, D1)"
MAD_TOD_URL = "https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA_PLANNING/MapServer/16"
MAD_TOD_ITEM = "https://data-cityofmadison.opendata.arcgis.com/datasets/4d890b70259846ddb626fcf85af69235"
MAD_TOD_LICENCE = "City of Madison Data Policy (https://www.cityofmadison.com/policy/data), as linked from the open data item"
MAD_TOD_DIR = RAW / "madison_tod"
COUNTY_FILE = RAW / "census_cb_2024" / "cb_2024_us_county_500k.zip"

MKE_CODE = "https://city.milwaukee.gov/ImageLibrary/Groups/ccClerk/Ordinances/Volume-2/CH295-sub{n}.pdf"
SOURCE_DOCS = {
    "madison_zoning_district_summary_2026-03-13.pdf": {
        "url": "https://www.cityofmadison.com/development-services-center/documents/ZoningTable.pdf",
        "terms": "Public record (D1); City of Madison Zoning District Summary dated 13 March 2026"},
    "milwaukee_ch295_sub5.pdf": {
        "url": "https://web.archive.org/web/20250324000000id_/" + MKE_CODE.format(n=5), "original": MKE_CODE.format(n=5),
        "terms": "Public law; Internet Archive copy (owner decision D2) because the city site blocks scripts"},
    "milwaukee_ch295_sub6.pdf": {
        "url": "https://web.archive.org/web/20250323000000id_/" + MKE_CODE.format(n=6), "original": MKE_CODE.format(n=6),
        "terms": "Public law; Internet Archive copy (owner decision D2) because the city site blocks scripts"},
    "milwaukee_ch295_sub7.pdf": {
        "url": "https://web.archive.org/web/20250809000000id_/" + MKE_CODE.format(n=7), "original": MKE_CODE.format(n=7),
        "terms": "Public law; Internet Archive copy (owner decision D2) because the city site blocks scripts"},
    "milwaukee_file_240997_rt5_substitute2.rtf": {
        "url": "https://milwaukee.legistar1.com/milwaukee/attachments/e2d566f7-50a4-4565-9c6d-a6e88b7105c9.rtf",
        "original": "https://milwaukee.legistar.com/LegislationDetail.aspx?ID=69285&GUID=58B81356-8159-4F55-877A-36FF148011D8",
        "terms": "Public law; Common Council file 240997 (RT5 district), Substitute 2, passed 2025-04-22"},
    "milwaukee_ch295_sub8.pdf": {
        "url": "https://web.archive.org/web/20250310131106id_/" + MKE_CODE.format(n=8), "original": MKE_CODE.format(n=8),
        "terms": "Public law; Internet Archive copy (owner decision D2) because the city site blocks scripts"},
    "milwaukee_ch295_sub9.pdf": {
        "url": "https://web.archive.org/web/20261011062849id_/" + MKE_CODE.format(n=9), "original": MKE_CODE.format(n=9),
        "terms": "Public law; Internet Archive copy (owner decision D2) because the city site blocks scripts"},
}
REUSED = {  # raw files already in the repo that the build reads; recorded, not refetched
    "madison_parcels/tax_parcels.geojson": "City of Madison tax parcels (see data/raw/madison_parcels/manifest.json)",
    "milwaukee_mprop/mprop.csv": "City of Milwaukee Master Property file (CC BY, data.milwaukee.gov)",
}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(url: str, data: dict | None = None, timeout: int = 180, retries: int = 4, final: list | None = None) -> bytes:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=UA), timeout=timeout) as r:
                if final is not None:
                    final.append(r.geturl())
                return r.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(8 * (attempt + 1))
    raise RuntimeError("unreachable")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stop_buffers(only: set[str] | None = None):
    """{county key: (buffer polygon, county polygon, stops)} in EPSG:3071 for every Wisconsin county with
    a qualifying stop within the buffer distance. Key: lower-case county name, spaces as '_'."""
    import geopandas as gpd
    import pandas as pd

    stops = pd.read_csv(REFERENCE / "tod_stops.csv", dtype={"stop_id": str, "ntd_id": str})
    pts = gpd.GeoDataFrame(stops, geometry=gpd.points_from_xy(stops.lon, stops.lat), crs=4326).to_crs(CRS_M)
    counties = gpd.read_file(f"zip://{COUNTY_FILE}")
    counties = counties[counties.STATEFP == "55"].to_crs(CRS_M)
    out = {}
    for _, c in counties.sort_values("NAME").iterrows():
        key = county_key(c.NAME)
        if only is not None and key not in only:
            continue
        poly = c.geometry
        # stops inside the county or within the buffer distance of it
        near = pts[pts.distance(poly) <= BUFFER_MILES * MILE_M]
        if len(near) == 0:
            continue
        buf = near.buffer(BUFFER_MILES * MILE_M, quad_segs=16).union_all().intersection(poly.buffer(200))
        out[key] = (buf, poly, len(near))
    return out


def county_key(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace(".", "")


def v12_coname(key: str) -> str:
    """V12 CONAME for a county key (upper-case county name; 'St. Croix' keeps its full stop)."""
    return {"st_croix": "ST. CROIX"}.get(key, key.replace("_", " ").upper())


def grid_cells(area, cell: float = CELL_M) -> list[tuple[float, float, float, float]]:
    from shapely.geometry import box

    x0, y0, x1, y1 = area.bounds
    cells = []
    y = y0
    while y < y1:
        x = x0
        while x < x1:
            b = (x, y, x + cell, y + cell)
            if area.intersects(box(*b)):
                cells.append(b)
            x += cell
        y += cell
    return cells


def query_envelope(url: str, env: tuple, fields: str, where: str = "1=1", page: int = 2000) -> list[dict]:
    """All GeoJSON features of an ArcGIS layer intersecting an EPSG:3071 envelope (paged)."""
    feats, off = [], 0
    while True:
        p = dict(where=where, geometry=",".join(f"{v:.1f}" for v in env), geometryType="esriGeometryEnvelope",
                 inSR=CRS_M, spatialRel="esriSpatialRelIntersects", outFields=fields, returnGeometry="true",
                 outSR=4326, geometryPrecision=6, f="geojson", resultOffset=off, resultRecordCount=page,
                 orderByFields="OBJECTID")
        d = json.loads(_get(url + "/query", p))
        if "error" in d:
            raise RuntimeError(f"{url}: {d['error']}")
        f = d.get("features", [])
        feats += f
        more = d.get("exceededTransferLimit") or d.get("properties", {}).get("exceededTransferLimit")
        if not f or (len(f) < page and not more):
            break
        off += len(f)
    return feats


def fetch_layer_in_buffer(url: str, fields: str, where: str, area, label: str, workers: int = 6) -> list[dict]:
    import geopandas as gpd

    cells = grid_cells(area)
    print(f"{label}: {len(cells)} cells of {CELL_M / 1000:.0f} km", flush=True)
    by_id: dict = {}
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(query_envelope, url, c, fields, where): c for c in cells}
        for i, fu in enumerate(cf.as_completed(futs), 1):
            for f in fu.result():
                by_id[f["properties"]["OBJECTID"]] = f
            if i % 50 == 0:
                print(f"  {i}/{len(cells)} cells, {len(by_id)} features", flush=True)
    feats = [f for f in by_id.values() if f.get("geometry")]
    if not feats:
        return []
    g = gpd.GeoDataFrame.from_features(feats, crs=4326).to_crs(CRS_M)
    keep = g.intersects(area).to_numpy()
    out = [f for f, k in zip(feats, keep) if k]
    out.sort(key=lambda f: f["properties"]["OBJECTID"])
    print(f"{label}: {len(by_id)} features in cells, {len(out)} intersect the buffer", flush=True)
    return out


def _write_geojson(path: Path, feats: list[dict]) -> None:
    path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))


def fetch_v12(manifest: dict, bufs: dict) -> None:
    for key, (buf, _, n_stops) in bufs.items():
        coname = v12_coname(key)
        acc = _now()
        feats = fetch_layer_in_buffer(V12_URL, V12_FIELDS, f"CONAME='{coname}'", buf, f"V12 {coname}")
        path = D / f"v12_{key}.geojson"
        _write_geojson(path, feats)
        manifest["files"][path.name] = {
            "url": V12_URL, "layer": "V1200_WisconsinParcels_2026", "where": f"CONAME='{coname}'",
            "spatial_filter": f"parcels intersecting a {BUFFER_MILES}-mile buffer of {n_stops} stops in reference/tod_stops.csv (EPSG:{CRS_M})",
            "fields": V12_FIELDS, "features": len(feats), "accessed_utc": acc, "bytes": path.stat().st_size,
            "sha256": _sha(path), "licence": V12_LICENCE}


def fetch_mke_zoning(manifest: dict, bufs: dict) -> None:
    buf = bufs["milwaukee"][0]
    acc = _now()
    feats = fetch_layer_in_buffer(MKE_ZONING_URL, "OBJECTID,Zoning,ZoningCategory,ZoningType", "1=1", buf, "MKE zoning")
    path = D / "mke_zoning.geojson"
    _write_geojson(path, feats)
    manifest["files"][path.name] = {
        "url": MKE_ZONING_URL, "spatial_filter": f"polygons intersecting the {BUFFER_MILES}-mile stop buffer, Milwaukee County",
        "fields": "OBJECTID,Zoning,ZoningCategory,ZoningType", "features": len(feats), "accessed_utc": acc,
        "bytes": path.stat().st_size, "sha256": _sha(path), "licence": MKE_ZONING_LICENCE}


def fetch_mad_zoning(manifest: dict) -> None:
    acc = _now()
    feats, off = [], 0
    while True:
        p = dict(where="1=1", outFields="OBJECTID,ZONING_CODE,ZON_PREFIX,PD_ID", returnGeometry="true", outSR=4326,
                 geometryPrecision=6, f="geojson", resultOffset=off, resultRecordCount=1000, orderByFields="OBJECTID")
        d = json.loads(_get(MAD_ZONING_URL + "/query", p))
        f = d.get("features", [])
        feats += f
        if len(f) < 1000 and not d.get("exceededTransferLimit") and not d.get("properties", {}).get("exceededTransferLimit"):
            break
        off += len(f)
    path = D / "mad_zoning.geojson"
    _write_geojson(path, feats)
    manifest["files"][path.name] = {
        "url": MAD_ZONING_URL, "fields": "OBJECTID,ZONING_CODE,ZON_PREFIX,PD_ID", "features": len(feats),
        "accessed_utc": acc, "bytes": path.stat().st_size, "sha256": _sha(path), "licence": MAD_LICENCE}
    print(f"Madison zoning: {len(feats)} polygons", flush=True)


def fetch_mad_tod() -> None:
    """Madison TOD overlay boundary, saved byte for byte as the service returns it (one feature; the
    attribute fields are a parcel schema left empty on the dissolved polygon)."""
    MAD_TOD_DIR.mkdir(parents=True, exist_ok=True)
    path = MAD_TOD_DIR / "tod_boundary.geojson"
    old = _sha(path) if path.exists() else None
    acc = _now()
    p = dict(where="1=1", outFields="*", returnGeometry="true", outSR=4326, f="geojson")
    data = _get(MAD_TOD_URL + "/query", p)
    d = json.loads(data)
    if "error" in d or not d.get("features"):
        raise RuntimeError(f"{MAD_TOD_URL}: {d.get('error', 'no features')}")
    path.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    entry = {"url": MAD_TOD_URL + "/query", "query": p, "open_data_item": MAD_TOD_ITEM,
             "layer": "Transit-Oriented Development Overlay District (MGO 28.104)", "features": len(d["features"]),
             "accessed_utc": acc, "bytes": len(data), "sha256": sha, "licence": MAD_TOD_LICENCE}
    mpath = MAD_TOD_DIR / "manifest.json"
    mpath.write_text(json.dumps({"source_id": "madison_tod", "files": {path.name: entry},
                                 "note": "Fetched by scripts/fetch_tod_parcels_zoning.py --only mad_tod."}, indent=2))
    same = "same as the previous file" if old == sha else ("first copy" if old is None else f"CHANGED (previous sha256 {old})")
    print(f"Madison TOD overlay: {len(d['features'])} feature(s), {len(data)} bytes, {same}; manifest: {mpath}", flush=True)


def fetch_docs(manifest: dict) -> None:
    out = D / "docs"
    out.mkdir(parents=True, exist_ok=True)
    for name, meta in SOURCE_DOCS.items():
        acc = _now()
        try:
            final: list = []
            data = _get(meta["url"], timeout=120, retries=5, final=final)
        except Exception as e:  # recorded, not fatal: the rule tables cite the URL and capture date
            manifest["failed"].append({"file": name, "url": meta["url"], "error": str(e), "accessed_utc": acc})
            print(f"FAILED {name}: {e}", flush=True)
            continue
        if not (data.startswith(b"%PDF") or (name.endswith(".rtf") and data.startswith(b"{\\rtf"))):
            manifest["failed"].append({"file": name, "url": meta["url"], "error": "response is not a PDF", "accessed_utc": acc})
            print(f"FAILED {name}: not a PDF", flush=True)
            continue
        (out / name).write_bytes(data)
        manifest["files"][f"docs/{name}"] = {**meta, "final_url": final[-1] if final else meta["url"],
                                             "accessed_utc": acc, "bytes": len(data),
                                             "sha256": hashlib.sha256(data).hexdigest()}
        print(f"{name}: {len(data)} bytes", flush=True)
        time.sleep(3)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["v12", "mke_zoning", "mad_zoning", "mad_tod", "docs"])
    ap.add_argument("--counties", default="milwaukee,dane",
                    help="comma-separated county keys for V12 (e.g. milwaukee,dane), or 'all' for every county with stops")
    a = ap.parse_args()
    D.mkdir(parents=True, exist_ok=True)
    mpath = D / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    manifest.setdefault("source_id", "tod_capacity")
    manifest.setdefault("files", {})
    manifest["failed"] = []
    manifest["note"] = ("Owner, mailing-address and site-address fields are never requested. Raw files are "
                        "git-ignored; committed outputs are aggregated (never parcel-level).")
    if a.only in (None, "v12", "mke_zoning"):
        wanted = None if a.counties == "all" else set(a.counties.split(","))
        if a.only == "mke_zoning" or (a.only is None and wanted is not None):
            wanted = (wanted or set()) | {"milwaukee"}
        bufs = stop_buffers(wanted)
    if a.only in (None, "v12"):
        fetch_v12(manifest, bufs)
    if a.only in (None, "mke_zoning"):
        fetch_mke_zoning(manifest, bufs)
    if a.only in (None, "mad_zoning"):
        fetch_mad_zoning(manifest)
    if a.only in (None, "mad_tod"):
        fetch_mad_tod()
    if a.only in (None, "docs"):
        fetch_docs(manifest)
    manifest["reused"] = {}
    for rel, desc in REUSED.items():
        p = RAW / rel
        if p.exists():
            st = p.stat()
            manifest["reused"][rel] = {"description": desc, "bytes": st.st_size, "sha256": _sha(p),
                                       "modified_utc": dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        else:
            manifest["reused"][rel] = {"description": desc, "missing": True}
    manifest["updated_utc"] = _now()
    mpath.write_text(json.dumps(manifest, indent=2))
    print(f"manifest: {mpath}")


if __name__ == "__main__":
    main()

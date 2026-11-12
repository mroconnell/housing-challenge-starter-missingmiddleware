"""Inputs for the parking lot-fit test (docs/parking/LOT_FIT_PLAN.md, with its Choices and Audit fixes blocks).

    uv run python scripts/fetch_parking_lotfit.py              # all 11 places + TIGER roads
    uv run python scripts/fetch_parking_lotfit.py --only kenosha racine
    uv run python scripts/fetch_parking_lotfit.py --skip-roads

Writes into data/raw/parking_lotfit/ (git-ignored):
- v12_<place>.geojson: WI statewide parcels V12 (SCO / DOA FeatureServer), every parcel in the place whose PROPCLASS
  contains a 1 (residential, alone or mixed). Paged by OBJECTID chunks of 2,000 (the service's page size). No owner,
  mailing or site-address fields are requested (privacy rule).
- tl_2024_<county>_roads.zip: Census TIGER/Line 2024 all-roads files for the counties the places sit in (alleys are
  MTFCC S1730; other roads give the street side of each lot).
- manifest.json: URL, query, licence, accessed time, feature count, bytes and sha256 for every file.

Our own user agent only. A refusal (HTTP 403, bot check) stops that file and is recorded in the manifest as a block;
the script never retries with another identity or a mirror.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402

D = RAW / "parking_lotfit"
UA = {"User-Agent": "missing-middleware research (housing policy model)"}
V12_URL = "https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels_DB/FeatureServer/0"
V12_LAYER = "V1200_WisconsinParcels_2026"
V12_FIELDS = ("OBJECTID,STATEID,PARCELID,TAXPARCELID,TAXROLLYEAR,PLACENAME,CONAME,PROPCLASS,AUXCLASS,"
              "LNDVALUE,IMPVALUE,ESTFMKVALUE,ASSDACRES,DEEDACRES,GISACRES,PARCELFIPS")
V12_LICENCE = ("Public records (Wis. Stat. 59.72); SCO/DOA item: free for public consumption as of 06/30/2026; "
               "no warranty")
TIGER_URL = "https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_{fips}_roads.zip"
TIGER_LICENCE = "Public domain (U.S. Government work), Census TIGER/Line 2024"
PAGE = 2000

# place key -> (V12 PLACENAME, county FIPS codes the place touches, for TIGER roads)
PLACES = {
    "milwaukee": ("CITY OF MILWAUKEE", ["55079", "55131", "55133"]),
    "madison": ("CITY OF MADISON", ["55025"]),
    "appleton": ("CITY OF APPLETON", ["55087", "55015", "55139"]),
    "waukesha": ("CITY OF WAUKESHA", ["55133"]),
    "eau_claire": ("CITY OF EAU CLAIRE", ["55035", "55017"]),
    "oshkosh": ("CITY OF OSHKOSH", ["55139"]),
    "germantown": ("VILLAGE OF GERMANTOWN", ["55131"]),
    "green_bay": ("CITY OF GREEN BAY", ["55009"]),
    "kenosha": ("CITY OF KENOSHA", ["55059"]),
    "racine": ("CITY OF RACINE", ["55101"]),
    "janesville": ("CITY OF JANESVILLE", ["55105"]),
}


class Blocked(RuntimeError):
    """The server refused us (403 or a bot check). Recorded, never worked around."""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(url: str, data: dict | None = None, timeout: int = 180, retries: int = 4) -> bytes:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=UA), timeout=timeout) as r:
                out = r.read()
            if out[:200].lower().lstrip().startswith((b"<!doctype html", b"<html")) and url.endswith(("query", ".zip")):
                raise Blocked(f"{url}: HTML page instead of data (possible bot check)")
            return out
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) or (e.code == 429 and attempt == retries - 1):
                raise Blocked(f"{url}: HTTP {e.code}") from e
            if attempt == retries - 1:
                raise
        except Blocked:
            raise
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


def v12_where(placename: str) -> str:
    return f"PLACENAME='{placename}' AND PROPCLASS LIKE '%1%'"


def object_ids(where: str) -> list[int]:
    d = json.loads(_get(V12_URL + "/query", {"where": where, "returnIdsOnly": "true", "f": "json"}))
    if "error" in d:
        raise RuntimeError(d["error"])
    return sorted(int(i) for i in d.get("objectIds") or [])


def fetch_v12(key: str, manifest: dict) -> None:
    placename = PLACES[key][0]
    where = v12_where(placename)
    acc = _now()
    ids = object_ids(where)
    feats = []
    for i in range(0, len(ids), PAGE):
        chunk = ids[i:i + PAGE]
        p = {"objectIds": ",".join(map(str, chunk)), "outFields": V12_FIELDS, "returnGeometry": "true",
             "outSR": 4326, "geometryPrecision": 7, "f": "geojson"}
        d = json.loads(_get(V12_URL + "/query", p))
        if "error" in d:
            raise RuntimeError(f"{key}: {d['error']}")
        got = d.get("features", [])
        if len(got) != len(chunk):
            raise RuntimeError(f"{key}: asked {len(chunk)} ids, got {len(got)}")
        feats += got
        print(f"  {key}: {len(feats)}/{len(ids)}", flush=True)
    feats.sort(key=lambda f: f["properties"]["OBJECTID"])
    path = D / f"v12_{key}.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
    manifest["files"][path.name] = {
        "url": V12_URL, "layer": V12_LAYER, "where": where, "fields": V12_FIELDS, "paging": f"OBJECTID chunks of {PAGE}",
        "features": len(feats), "accessed_utc": acc, "bytes": path.stat().st_size, "sha256": _sha(path),
        "licence": V12_LICENCE}


def fetch_roads(fips: str, manifest: dict) -> None:
    url = TIGER_URL.format(fips=fips)
    path = D / f"tl_2024_{fips}_roads.zip"
    acc = _now()
    path.write_bytes(_get(url))
    manifest["files"][path.name] = {"url": url, "vintage": "TIGER/Line 2024", "accessed_utc": acc,
                                    "bytes": path.stat().st_size, "sha256": _sha(path), "licence": TIGER_LICENCE}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="*", choices=sorted(PLACES), help="places to fetch (default: all 11)")
    ap.add_argument("--skip-roads", action="store_true")
    ap.add_argument("--skip-parcels", action="store_true")
    a = ap.parse_args(argv)
    D.mkdir(parents=True, exist_ok=True)
    mpath = D / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {
        "source_id": "parking_lotfit", "plan": "docs/parking/LOT_FIT_PLAN.md", "user_agent": UA["User-Agent"],
        "files": {}, "blocks": []}
    keys = a.only or list(PLACES)

    def save():
        mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True))

    if not a.skip_parcels:
        for k in keys:
            try:
                fetch_v12(k, manifest)
            except Blocked as e:
                manifest["blocks"].append({"file": f"v12_{k}.geojson", "error": str(e), "at_utc": _now()})
                print(f"BLOCKED {k}: {e}", flush=True)
            save()
    if not a.skip_roads:
        for fips in sorted({f for k in keys for f in PLACES[k][1]}):
            try:
                fetch_roads(fips, manifest)
            except Blocked as e:
                manifest["blocks"].append({"file": f"tl_2024_{fips}_roads.zip", "error": str(e), "at_utc": _now()})
                print(f"BLOCKED roads {fips}: {e}", flush=True)
            save()
    for name, f in sorted(manifest["files"].items()):
        print(f"{name}: {f.get('features', '')} features, {f['bytes']:,} bytes")


if __name__ == "__main__":
    main()

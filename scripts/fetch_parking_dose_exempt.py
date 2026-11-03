"""Parking dose pilot, pre-repeal exemptions: download one public ArcGIS REST layer as GeoJSON (WGS 84), paged.

    uv run python scripts/fetch_parking_dose_exempt.py LAYER_URL data/raw/parking_dose_exempt/<place>/<name>.geojson \
        ["where clause"] ["xmin,ymin,xmax,ymax"]

Rules: public layers only; honest user agent below; if a host refuses (403, bot wall) cite the URL and stop, never
work around it. Write only under data/raw/parking_dose_exempt/ (git-ignored) and record url, access time (UTC) and
licence (the layer's copyrightText / item licenseInfo, else "no licence stated") in that place's _sources.json.
Layers are not shipped; shipping any layer needs the owner's OK. No OpenStreetMap."""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path
UA = "missing-middleware-research/1.0 (public data)"
def get(url, params):
    q = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(q, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())
def main():
    if "data/raw/parking_dose_exempt/" not in str(Path(sys.argv[2]).resolve()).replace("\\", "/"):
        raise SystemExit("write layers only under data/raw/parking_dose_exempt/ (git-ignored)")
    url, out = sys.argv[1].rstrip("/"), sys.argv[2]
    where = sys.argv[3] if len(sys.argv) > 3 else "1=1"
    bb = sys.argv[4] if len(sys.argv) > 4 else None
    meta = get(url, {"f": "json"})
    page = min(int(meta.get("maxRecordCount", 1000) or 1000), 2000)
    base = {"where": where, "outFields": "*", "outSR": 4326, "f": "geojson", "returnGeometry": "true"}
    if bb:
        base.update({"geometry": bb, "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects"})
    feats, off = [], 0
    while True:
        d = get(url + "/query", {**base, "resultOffset": off, "resultRecordCount": page})
        if "error" in d: raise SystemExit(d)
        f = d.get("features", []); feats += f
        if len(f) < page and not d.get("exceededTransferLimit") and not (d.get("properties") or {}).get("exceededTransferLimit"):
            break
        if not f: break
        off += len(f); time.sleep(0.3)
    json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w"))
    print(out, len(feats), "features; layer:", meta.get("name"), "| copyright:", meta.get("copyrightText"), "| desc:", (meta.get("description") or "")[:200])
main()

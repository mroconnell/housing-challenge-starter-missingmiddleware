"""Parking dose pilot, pre-repeal exemptions: exempt share of apartment-eligible land by regular-grid sampling.

Output feeds reference/parking_dose_exempt_pilot.csv (hand-assembled; see its notes column).

    uv run python scripts/run_parking_dose_exempt_grid.py data/raw/parking_dose_exempt/<place>/<config>.json

Method: lay a square grid of points (default 25 m) over the apartment-eligible zoning polygons in EPSG:5070
(equal-area), keep points inside them (and inside an optional city clip), and flag each point that is in an exempt
zone, an exempt overlay, or within a radius of any transit point (rail stops, or GTFS route shapes densified to
points). Each share is flagged points / kept points, i.e. a share of apartment-eligible land area. Geometry is
missing_middleware.geom only (numpy, pandas, scipy); no shapely, geopandas or pyproj.

Layers stay in data/raw/parking_dose_exempt/ (git-ignored); this script never copies them elsewhere. Their sources
and terms are in each place's _sources.json and docs/DATA_PROVENANCE.md. Shipping any layer needs the owner's OK.
config: {
 "zoning": "path.geojson", "zone_field": "ZONE",
 "apt_zones_regex": "^(R-3|R-4|C|MU).*",   # zones where apartments (3+/5+ units) are allowed
 "exempt_zones_regex": "^(DT|CBD)",        # zones with no/much-lower minimum (optional)
 "exempt_overlays": [{"path": "x.geojson", "where_field": null, "where_regex": null, "label": "downtown overlay"}],
 "transit_buffers": [{"points": "stops.json" or [[lon,lat],...], "radius_m": 804.67, "label": "1/2 mi frequent bus"}],
 "clip": "city_boundary.geojson" (optional), "spacing_m": 25 }
Prints JSON: apt-eligible area (km2), exempt share overall and by source."""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missing_middleware import geom as G
from scipy.spatial import cKDTree

def load(p):
    return G.read_any(p).to_crs(5070)

def pts_from(spec):
    if isinstance(spec, list):
        a = np.array(spec, float); return G.transform(a[:, 0], a[:, 1], 4326, 5070)
    obj = json.load(open(spec))
    if isinstance(obj, list):                       # [[lon, lat], ...] (densified route shapes)
        a = np.array(obj, float).reshape(-1, 2); return G.transform(a[:, 0], a[:, 1], 4326, 5070)
    if "stops" in obj:
        a = np.array([[s["stop_lon"], s["stop_lat"]] for s in obj["stops"]], float)
        return G.transform(a[:, 0], a[:, 1], 4326, 5070)
    L = G.read_any(spec).to_crs(5070); return L.x, L.y

def main():
    c = json.load(open(sys.argv[1])); sp = float(c.get("spacing_m", 25))
    Z = load(c["zoning"]); zf = c["zone_field"]
    z = Z.attrs[zf].astype(str).fillna("")
    apt = z.str.match(c["apt_zones_regex"]).to_numpy()
    ex = z.str.match(c["exempt_zones_regex"]).to_numpy() if c.get("exempt_zones_regex") else np.zeros(len(z), bool)
    ZA = Z.subset(apt)
    x0, y0, x1, y1 = G.bbox(ZA)
    gx, gy = np.meshgrid(np.arange(x0, x1, sp), np.arange(y0, y1, sp))
    px, py = gx.ravel(), gy.ravel()
    idx = G.points_in_polygons(px, py, ZA.polys)
    keep = idx >= 0
    if c.get("clip"):
        C = load(c["clip"]); keep &= G.points_in_any(px, py, C.polys)
    px, py, idx = px[keep], py[keep], idx[keep]
    zone = ZA.attrs[zf].astype(str).to_numpy()[idx]
    flags = {}
    flags["exempt_zone"] = ex[apt][idx]
    for o in c.get("exempt_overlays", []):
        O = load(o["path"])
        if o.get("where_field"):
            O = O.subset(O.attrs[o["where_field"]].astype(str).str.match(o["where_regex"]).to_numpy())
        flags[o["label"]] = G.points_in_any(px, py, O.polys, union=True)
    for t in c.get("transit_buffers", []):
        sx, sy = pts_from(t["points"]); ok = np.isfinite(sx)
        if ok.sum() == 0: flags[t["label"]] = np.zeros(len(px), bool); continue
        d, _ = cKDTree(np.c_[sx[ok], sy[ok]]).query(np.c_[px, py], k=1)
        flags[t["label"]] = d <= float(t["radius_m"])
    anyx = np.zeros(len(px), bool)
    for v in flags.values(): anyx |= v
    n = len(px); cell = sp * sp / 1e6
    out = {"apt_eligible_km2": round(n * cell, 3), "n_points": int(n), "spacing_m": sp,
           "exempt_share_any": round(float(anyx.mean()), 4) if n else None,
           "by_source": {k: round(float(v.mean()), 4) for k, v in flags.items()},
           "apt_km2_by_zone": {k: round(v * cell, 3) for k, v in pd.Series(zone).value_counts().items()},
           "exempt_share_by_zone": pd.Series(anyx).groupby(zone).mean().round(3).to_dict(),
           "all_zones_in_layer": sorted(z.unique().tolist())[:300]}
    print(json.dumps(out, indent=1))
main()

"""Parking block-by-block catalog (docs/parking/BLOCK_CATALOG_PLAN.md).

    uv run --all-extras python scripts/run_parking_block_catalog.py

Reuses TOD's census block points (2000 Summary File 1 headers; 2010 and 2020 TIGER blocks), read from the caches that
scripts/run_tod_census_cases.py and scripts/run_tod_census2000.py write. Output: reference/parking_block_catalog.csv

Geometry uses missing_middleware/geom.py (numpy/scipy only; docs/GEOMETRY.md). The old shapely code only ever asked
which points (block points, rail stops) an area contains, so each area is kept as a point-membership test (`Region`):
unions, intersections and differences become or / and / and-not, and a buffered point is the same 64-sided polygon
that GEOS builds (16 segments per quarter circle).
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware import geom  # noqa: E402
from missing_middleware.dbf import read_dbf_bytes  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402

SEED, DRAWS = 20261028, 2000
MILE = 1609.344
CRS = 5070                       # USA Albers, metres (as scripts/run_tod_census_cases.py)
ACRE = 4046.8564
TOD_DIR = RAW / "tod_census_cases"
OLD = RAW / "parking_older_reforms"
CACHE = PROCESSED / "tod_census_cases"
MPLS_DOWNTOWN = (44.9778, -93.2650)   # downtown already had no minimums; blocks within 1.5 km are left out


# ------------------------------------------------------------------ areas as point-membership tests
class Region:
    """Stands in for a shapely geometry whose only use is 'which of these points lie inside'."""

    def __init__(self, test):
        self._test = test

    def contains(self, x, y) -> np.ndarray:
        x, y = np.asarray(x, float), np.asarray(y, float)
        return self._test(x, y) if len(x) else np.zeros(0, bool)

    def _narrow(self, other, keep_inside: bool):
        def t(x, y):
            m = self.contains(x, y)
            ix = np.flatnonzero(m)
            if len(ix):
                o = other.contains(x[ix], y[ix])
                m[ix] = o if keep_inside else ~o
            return m
        return Region(t)

    def __and__(self, other):          # intersection
        return self._narrow(other, True)

    def __sub__(self, other):          # difference
        return self._narrow(other, False)

    def __or__(self, other):           # union
        return Region(lambda x, y: self.contains(x, y) | other.contains(x, y))

    @staticmethod
    def polygons(feats: list) -> "Region":
        """Inside any of the polygon features (the union of them). The old code took shapely's union_all, where every
        part counts with its own holes; geom.points_in_feature uses GEOS's even-odd rule over all rings (right for a
        spatial join 'within', not for a union), so each part is passed as its own feature."""
        parts = [[part] for f in feats for part in f]
        return Region(lambda x, y: geom.points_in_any(x, y, parts))

    @staticmethod
    def any_of(regions: list) -> "Region":
        def t(x, y):
            m = np.zeros(len(x), bool)
            for r in regions:
                rest = np.flatnonzero(~m)
                if not len(rest):
                    break
                m[rest[r.contains(x[rest], y[rest])]] = True
            return m
        return Region(t)

    @staticmethod
    def circle(cx: float, cy: float, r: float) -> "Region":
        feat = [[circle_ring(cx, cy, r)]]
        return Region(lambda x, y: geom.points_in_feature(x, y, feat))

    @staticmethod
    def nearest_site(sites_x, sites_y, k: int) -> "Region":
        """The Voronoi cell of site k (points nearer to site k than to any other site)."""
        from scipy.spatial import cKDTree
        tree = cKDTree(np.c_[sites_x, sites_y])
        return Region(lambda x, y: tree.query(np.c_[x, y])[1] == k)


def circle_ring(cx: float, cy: float, r: float, quad_segs: int = 16) -> np.ndarray:
    """GEOS's buffer of a point: vertices at angles k * pi / (2 * quad_segs) on the circle (counter-clockwise here)."""
    a = np.arange(4 * quad_segs) * (np.pi / (2 * quad_segs))
    ring = np.c_[cx + r * np.cos(a), cy + r * np.sin(a)]
    return np.vstack([ring, ring[:1]])


def within(pts: pd.DataFrame, region: Region | None) -> pd.Series:
    if region is None:
        return pd.Series(False, index=pts.index)
    return pd.Series(region.contains(pts["x"].to_numpy(), pts["y"].to_numpy()), index=pts.index)


# ------------------------------------------------------------------ readers
def pt(lat, lon) -> tuple[float, float]:
    x, y = geom.transform([lon], [lat], 4326, CRS)
    return float(x[0]), float(y[0])


def _regroup_holes(feature: list) -> list:
    """Give each hole to the outer ring that holds most of its vertices. geom.read_shapefile tests only a hole's first
    vertex, and a hole touching its shell at that vertex can land in the wrong part (Orland Park, IL: a block point
    inside an 11-vertex hole counted as in the city)."""
    if len(feature) < 2:
        return feature
    outers = [p[0] for p in feature]
    holes = [h for p in feature for h in p[1:]]
    if not holes:
        return feature
    parts = [[o] for o in outers]
    for h in holes:
        hx, hy = (h[:, 0] + np.roll(h[:, 0], -1)) / 2, (h[:, 1] + np.roll(h[:, 1], -1)) / 2   # edge midpoints too
        x, y = np.r_[h[:, 0], hx], np.r_[h[:, 1], hy]
        k = int(np.argmax([geom.points_in_feature(x, y, [[o]]).sum() for o in outers]))
        parts[k].append(h)
    return parts


def read_tiger(zip_path) -> geom.Layer:
    """A TIGER shapefile projected to CRS, attributes decoded as UTF-8 (the files' .cpg) like the old reader."""
    lay = geom.read_shapefile(zip_path)
    with zipfile.ZipFile(zip_path) as z:
        dbf = next(n for n in z.namelist() if n.lower().endswith(".dbf"))
        lay.attrs = read_dbf_bytes(z.read(dbf), encoding="utf-8")
    if lay.kind == "polygon":
        lay.polys = [_regroup_holes(f) for f in lay.polys]
    return lay.to_crs(CRS)


def place_layer(st) -> geom.Layer:
    d = TOD_DIR if (TOD_DIR / f"tl_2020_{st}_place.zip").exists() else OLD
    return read_tiger(d / f"tl_2020_{st}_place.zip")


def place(st, geoid) -> Region:
    p = place_layer(st)
    return Region.polygons(p.subset(p.attrs["GEOID"] == geoid).polys)


def stops() -> pd.DataFrame:
    s = pd.DataFrame(json.load(open(TOD_DIR / "ntm_rail_stops.json")))
    s["x"], s["y"] = geom.transform(s["stop_lon"].astype(float), s["stop_lat"].astype(float), 4326, CRS)
    return s


def urban_villages() -> geom.Layer:
    return geom.read_geojson(OLD / "seattle_urban_villages.geojson").to_crs(CRS)


def _read_points(f: Path) -> pd.DataFrame:
    """A GeoParquet cache of block points (homes, land, point geometry as WKB) as homes, land, x, y."""
    import pyarrow.parquet as pq
    t = pq.read_table(f)
    meta = json.loads(t.schema.metadata[b"geo"])["columns"]["geometry"]
    code = ((meta.get("crs") or {}).get("id") or {}).get("code")
    if meta.get("encoding", "WKB").upper() != "WKB" or code != CRS:
        raise ValueError(f"{f}: expected WKB points in EPSG:{CRS}")
    wkb = t.column("geometry").to_pylist()
    rec = np.frombuffer(b"".join(wkb), dtype=[("bo", "u1"), ("t", "<u4"), ("x", "<f8"), ("y", "<f8")])
    if len(rec) != len(wkb) or (rec["bo"] != 1).any() or (rec["t"] != 1).any():
        raise ValueError(f"{f}: geometry is not little-endian 2D points")
    d = t.drop(["geometry"]).to_pandas()
    d["x"], d["y"] = rec["x"], rec["y"]
    return d


def block_points(st: str, year: int) -> pd.DataFrame:
    """Census block points (2000 SF1 internal points; 2010/2020 TIGER block representative points), from the TOD
    caches (scripts/run_tod_census2000.py, scripts/run_tod_census_cases.py build them)."""
    f = CACHE / f"blocks_{st}_{year}.parquet"
    if not f.exists():
        raise FileNotFoundError(f"{f} missing: build it with the TOD census scripts first")
    return _read_points(f)


def three(st: str, treated: Region, comp: Region):
    out = {}
    for y in (2000, 2010, 2020):
        p = block_points(st, y)
        out[y] = (p[within(p, treated)], p[within(p, comp)])
    return out


def per_acre(a, b):
    acres = (a["land"].sum() + b["land"].sum()) / 2 / ACRE
    return (b["homes"].sum() - a["homes"].sum()) / acres if acres > 0 else np.nan


def diffs(g) -> tuple[float, float]:
    """(2000-2010 difference, 2010-2020 difference), treated minus comparison, net homes per acre per decade."""
    (t0, c0), (t1, c1), (t2, c2) = g[2000], g[2010], g[2020]
    return per_acre(t0, t1) - per_acre(c0, c1), per_acre(t1, t2) - per_acre(c1, c2)


# ------------------------------------------------------------------ catalog
def areas() -> list[dict]:
    out = []
    v = urban_villages()
    sea = place("53", "5363000")
    vil = Region.polygons(v.subset(v.attrs["UV_TYPE"].isin(["HUV", "RUV"])).polys)
    other = Region.polygons(v.subset(v.attrs["UV_TYPE"].isin(["UC", "MIC"])).polys)
    out.append(dict(case="Seattle urban villages (2012)", st="53", from_="2012-08-23", treated=vil & sea,
                    comp=sea - vil - other))
    for name, lat, lon, ey, lab in (("South Hayward", 37.634340, -122.057182, "2011-07-01", "Hayward, South Hayward BART (2011)"),
                                    ("Warm Springs", 37.502307, -121.939358, "2015-07-01", "Fremont, Warm Springs (2015)")):
        c = pt(lat, lon)
        out.append(dict(case=lab, st="06", from_=ey, treated=Region.circle(*c, MILE / 2),
                        comp=Region.circle(*c, 1.5 * MILE) - Region.circle(*c, MILE / 2)))
    mpls = place("27", "2743000")
    s = stops()
    s = s[mpls.contains(s["x"], s["y"]) & s["stop_type_text"].astype(str).str.contains("rail|Rail|Tram")]
    dt = Region.circle(*pt(*MPLS_DOWNTOWN), 1500)
    buf = Region.any_of([Region.circle(x, y, MILE / 2) for x, y in zip(s["x"], s["y"])])
    near = (mpls & buf) - dt
    out.append(dict(case="Minneapolis near-rail parking cut (2015)", st="27", from_="2015-07-01", treated=near,
                    comp=mpls - near - dt, stations=int(len(s))))
    return out


def rates(t0, t1, c0, c1):
    gt = (t1["homes"].sum() - t0["homes"].sum()) / t0["homes"].sum() * 100   # per 1,000 homes per year over a decade
    gc = (c1["homes"].sum() - c0["homes"].sum()) / c0["homes"].sum() * 100
    return gt - gc


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for a in areas():
        g = three(a["st"], a["treated"], a["comp"])
        (t0, c0), (t1, c1), (t2, c2) = g[2000], g[2010], g[2020]
        before, after = rates(t0, t1, c0, c1), rates(t1, t2, c1, c2)
        acre_before, acre_after = diffs(g)
        bs = np.empty((DRAWS, 2))
        for i in range(DRAWS):
            gg = {y: tuple(x.iloc[rng.integers(0, len(x), len(x))] for x in g[y]) for y in g}
            (u0, d0), (u1, d1), (u2, d2) = gg[2000], gg[2010], gg[2020]
            bs[i] = rates(u0, u1, d0, d1), rates(u1, u2, d1, d2)
        cic = bs[:, 1] - bs[:, 0]
        share = (pd.Timestamp("2020-04-01") - max(pd.Timestamp(a["from_"]), pd.Timestamp("2010-04-01"))).days / 3653
        rows.append(dict(case=a["case"], reform_from=a["from_"], share_of_2010s_under_reform=round(min(max(share, 0), 1), 2),
                         treated_homes_2000=t0["homes"].sum(), treated_homes_2010=t1["homes"].sum(), treated_homes_2020=t2["homes"].sum(),
                         comparison_homes_2000=c0["homes"].sum(), comparison_homes_2010=c1["homes"].sum(), comparison_homes_2020=c2["homes"].sum(),
                         gap_2000s=before, gap_2010s=after, change_in_change=after - before,
                         cic_p05=np.nanquantile(cic, 0.05), cic_p95=np.nanquantile(cic, 0.95),
                         gap_2000s_p05=np.nanquantile(bs[:, 0], 0.05), gap_2000s_p95=np.nanquantile(bs[:, 0], 0.95),
                         per_acre_gap_2000s=acre_before, per_acre_gap_2010s=acre_after, per_acre_cic=acre_after - acre_before,
                         stations=a.get("stations")))
    out = pd.DataFrame(rows)
    out.round(3).to_csv(REFERENCE / "parking_block_catalog.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

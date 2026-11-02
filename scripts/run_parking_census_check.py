"""Census-count check (docs/parking/SALVAGE_PLAN.md, section 4): does the change in homes between the 2010 and
2020 censuses match the permits a place issued over the same years?

    uv run python scripts/fetch_parking_census_check.py
    uv run python scripts/run_parking_census_check.py

Both years' blocks are placed in 2020 place boundaries by internal point. Permits from the Census permit place
files. Geometry: missing_middleware/geom.py (open licence, docs/GEOMETRY.md); the 2010 blocks' internal points are
GEOS's representative point, ported below (interior_points) so the outputs match the old shapely run.
Outputs: reference/parking_census_check_places.csv, reference/parking_census_check_summary.csv
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware import geom  # noqa: E402
from missing_middleware.dbf import read_shapefile_attributes  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

D = RAW / "parking_census_check"
CHECK_STATES = ("18", "27", "37", "55")
ALL_STATES = ("18", "27", "37", "45", "46", "42", "55")
EQUAL_AREA = 5070


def interior_points(polys: list, src=None, dst=None) -> tuple[np.ndarray, np.ndarray]:
    """shapely's representative_point() for each polygon feature: GEOS InteriorPointArea (GEOS 3.8+), ported.

    Per polygon part: a horizontal scan line halfway between the vertex heights nearest above and at-or-below the
    middle of the part's height; the point is the middle of the widest run of the scan line inside the part (first
    such run on ties; the shell's first vertex when there is none). A multipart feature takes its first part with the
    widest run. If src/dst are given, the vertices are projected first (all at once, which is fast). Same arithmetic
    as GEOS, so the points agree to the last bit given the same vertices.
    """
    rings, ring_part, ext, part_feat = [], [], [], []
    for k, f in enumerate(polys):
        for part in f:
            for j, r in enumerate(part):
                rings.append(r)
                ring_part.append(len(part_feat))
                ext.append(j == 0)
            part_feat.append(k)
    ox, oy = np.full(len(polys), np.nan), np.full(len(polys), np.nan)
    if not part_feat:
        return ox, oy
    lens = np.array([len(r) for r in rings])
    V = np.concatenate(rings)
    x, y = (V[:, 0], V[:, 1]) if src is None else geom.transform(V[:, 0], V[:, 1], src, dst)
    vring = np.repeat(np.arange(len(rings)), lens)
    vpart = np.asarray(ring_part)[vring]
    vext = np.asarray(ext)[vring]
    pstart = np.flatnonzero(np.r_[True, vpart[1:] != vpart[:-1]])            # parts are contiguous
    ys = y[vext]
    sstart = np.flatnonzero(np.r_[True, vpart[vext][1:] != vpart[vext][:-1]])
    lo, hi = np.minimum.reduceat(ys, sstart), np.maximum.reduceat(ys, sstart)  # polygon envelope = shell envelope
    centre = (lo + hi) / 2
    c = centre[vpart]
    loY = np.maximum(lo, np.maximum.reduceat(np.where(y <= c, y, -np.inf), pstart))
    hiY = np.minimum(hi, np.minimum.reduceat(np.where(y > c, y, np.inf), pstart))
    scan = (hiY + loY) / 2
    i = np.flatnonzero(vring[:-1] == vring[1:])                                 # edges p0 -> p1 within a ring
    x0, y0, x1, y1, Y = x[i], y[i], x[i + 1], y[i + 1], scan[vpart[i]]
    keep = ~(((y0 > Y) & (y1 > Y)) | ((y0 < Y) & (y1 < Y)))                    # edge meets the scan line
    keep &= (y0 != y1) & ~((y0 == Y) & (y1 < Y)) & ~((y1 == Y) & (y0 < Y))      # GEOS isEdgeCrossingCounted
    i, x0, y0, x1, y1, Y = i[keep], x0[keep], y0[keep], x1[keep], y1[keep], Y[keep]
    with np.errstate(divide="ignore", invalid="ignore"):
        m = (y1 - y0) / (x1 - x0)
        xi = np.where(x0 == x1, x0, x0 + ((Y - y0) / m))
    cp = vpart[i]
    o = np.lexsort((xi, cp))
    cp, xi = cp[o], xi[o]
    first = np.flatnonzero(np.r_[True, cp[1:] != cp[:-1]])
    rank = np.arange(len(cp)) - np.repeat(first, np.diff(np.r_[first, len(cp)]))
    a = np.flatnonzero((rank % 2 == 0) & (np.arange(len(cp)) + 1 < len(cp)))
    a = a[cp[np.minimum(a + 1, len(cp) - 1)] == cp[a]]
    w = xi[a + 1] - xi[a]
    a, w = a[w > 0], w[w > 0]
    n_parts = len(part_feat)
    sh0 = np.r_[0, np.cumsum(lens)][np.flatnonzero(ext)]                       # first vertex of each shell
    px, py, pw = x[sh0].copy(), y[sh0].copy(), np.zeros(n_parts)
    if len(a):
        o = np.lexsort((rank[a], -w, cp[a]))                                    # widest, then first, per part
        _, f = np.unique(cp[a][o], return_index=True)
        b = a[o][f]
        p = cp[b]
        px[p], py[p], pw[p] = (xi[b] + xi[b + 1]) / 2, scan[p], xi[b + 1] - xi[b]
    pf = np.asarray(part_feat)
    o = np.lexsort((np.arange(n_parts), -pw, pf))                               # first widest part per feature
    _, f = np.unique(pf[o], return_index=True)
    ox[pf[o][f]], oy[pf[o][f]] = px[o][f], py[o][f]
    return ox, oy


def block_points(zip_path, cols: list[str], dst) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """2020 blocks: attributes and internal points (INTPTLON20/INTPTLAT20, NAD83) projected to dst; no polygons read."""
    a = read_shapefile_attributes(zip_path)
    x, y = geom.transform(a["INTPTLON20"].astype(float).values, a["INTPTLAT20"].astype(float).values, 4269, dst)
    return a[cols].reset_index(drop=True), x, y


def block_points_2010(zip_path, cols: list[str], dst, where=None) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """2010 blocks: attributes and the representative point of each block polygon projected to dst."""
    b = geom.read_shapefile(zip_path)
    if where is not None:
        b = b.subset(where(b.attrs))
    x, y = interior_points(b.polys, b.crs, dst)
    return b.attrs[cols].reset_index(drop=True), x, y


def _ring_parity(px, py, ring: np.ndarray) -> np.ndarray:
    """Odd number of crossings of a ray to +x with the ring's edges (vectorised over points, edges in chunks)."""
    x0, y0 = ring[:, 0], ring[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    keep = y0 != y1
    x0, y0, x1, y1 = x0[keep], y0[keep], x1[keep], y1[keep]
    out = np.zeros(len(px), bool)
    step = max(1, 2_000_000 // max(1, len(x0)))
    for s in range(0, len(px), step):
        X, Y = px[s:s + step, None], py[s:s + step, None]
        hit = ((y0 > Y) != (y1 > Y)) & (X < x0 + (Y - y0) * (x1 - x0) / (y1 - y0))
        out[s:s + step] = (np.count_nonzero(hit, axis=1) % 2) == 1
    return out


def points_in_polygons_evenodd(px, py, polys: list) -> np.ndarray:
    """Index of the first feature containing each point, or -1: a spatial join 'within' that counts ray crossings over
    ALL rings of a feature together (even-odd), as GEOS does. geom.points_in_polygons instead takes the union of the
    parts, each with its own holes, which differs when a hole holds an island of the same feature that has its own
    hole (TIGER places: Fresno's county islands, Wichita, O'Fallon...), or when a shell is nested in another shell."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    out = np.full(len(px), -1, dtype=np.int64)
    order = np.argsort(px)
    sx = px[order]
    for k, f in enumerate(polys):
        rings = [r for part in f for r in part]
        if not rings:
            continue
        allr = np.concatenate(rings)
        lo, hi = np.searchsorted(sx, allr[:, 0].min(), "left"), np.searchsorted(sx, allr[:, 0].max(), "right")
        cand = order[lo:hi]
        cand = cand[(py[cand] >= allr[:, 1].min()) & (py[cand] <= allr[:, 1].max()) & (out[cand] < 0)]
        inside = np.zeros(len(cand), bool)
        for r in rings:                       # a point outside a ring's bounding box crosses it an even number of times
            m = np.flatnonzero((px[cand] >= r[:, 0].min()) & (px[cand] <= r[:, 0].max())
                               & (py[cand] >= r[:, 1].min()) & (py[cand] <= r[:, 1].max()))
            if len(m):
                inside[m] ^= _ring_parity(px[cand[m]], py[cand[m]], r)
        out[cand[inside]] = k
    return out


def read_places(zip_path, dst) -> geom.Layer:
    """2020 places (GEOID, NAME) projected to dst. geom reads .dbf text as Latin-1; TIGER 2020 files are UTF-8 (their
    .cpg says so), so text is re-decoded to keep names such as 'La Cañada Flintridge' as the old reader gave them."""
    places = geom.read_shapefile(zip_path, columns=["GEOID", "NAME"])
    with zipfile.ZipFile(zip_path) as z:
        cpg = next((z.read(n).decode("ascii", "ignore") for n in z.namelist() if n.lower().endswith(".cpg")), "")
    if "UTF" in cpg.upper():
        places.attrs = places.attrs.apply(lambda c: c.str.encode("latin-1").str.decode("utf-8"))
    return places.to_crs(dst)


def sum_in_places(attrs: pd.DataFrame, x, y, places: geom.Layer, cols: list[str]) -> pd.DataFrame:
    """Spatial join 'within' (inner) of points to place polygons, summed by place GEOID."""
    k = points_in_polygons_evenodd(x, y, places.polys)
    j = attrs.loc[k >= 0, cols].assign(GEOID=places.attrs["GEOID"].values[k[k >= 0]])
    return j.groupby("GEOID")[cols].sum()


def place_homes(st: str) -> pd.DataFrame:
    places = read_places(D / f"tl_2020_{st}_place.zip", EQUAL_AREA)
    b20 = block_points(D / f"tl_2020_{st}_tabblock20.zip", ["HOUSING20"], EQUAL_AREA)
    b10 = block_points_2010(D / f"tabblock2010_{st}_pophu.zip", ["HOUSING10"], EQUAL_AREA)
    out = []
    for (a, x, y), col in ((b20, "HOUSING20"), (b10, "HOUSING10")):
        out.append(sum_in_places(a, x, y, places, [col]))
    r = pd.concat(out, axis=1).fillna(0)
    r["name"] = places.attrs.set_index("GEOID")["NAME"]
    return r


def permits() -> pd.DataFrame:
    frames = []
    for f in sorted(list(D.glob("*a.txt")) + list(rpc.BPS_DIR.glob("*a.txt"))):
        y = int(f.name[2:6])
        if 2009 <= y <= 2019:
            d = parsers.read_bps(f, "place", state_fips=None)
            d["year"] = y
            frames.append(d)
    p = cmp.panel(pd.concat(frames, ignore_index=True))
    p = p[p["acs_geoid"].str.startswith("160|")]
    p["GEOID"] = p["acs_geoid"].str[4:]
    return p


def main() -> None:
    p = permits()
    rows = []
    for st in ALL_STATES:
        h = place_homes(st)
        s = p[p["state_fips"] == st]
        for lab, yrs in (("2010-2019", range(2010, 2020)), ("2009-2018", range(2009, 2019))):
            g = s[s["year"].isin(yrs)].groupby("GEOID").agg(units=("units_total", "sum"), years=("year", "nunique"))
            h[f"permits_{lab}"] = g["units"]
            h[f"years_{lab}"] = g["years"]
        h["state_fips"] = st
        rows.append(h.reset_index().rename(columns={"index": "GEOID"}))
        print(st, len(h), flush=True)
    d = pd.concat(rows, ignore_index=True)
    d["census_change"] = d["HOUSING20"] - d["HOUSING10"]
    d.to_csv(REFERENCE / "parking_census_check_places.csv", index=False)

    c = d[d["state_fips"].isin(CHECK_STATES) & (d["years_2010-2019"] == 10) & (d["HOUSING10"] >= 100)].copy()
    out = []
    for lab in ("2010-2019", "2009-2018"):
        k = c[c[f"years_{lab}"] == 10] if lab == "2009-2018" else c
        perm = k[f"permits_{lab}"]
        for band, m in (("all", np.ones(len(k), bool)), ("under 2,500 homes", k["HOUSING10"] < 2500),
                        ("2,500-25,000 homes", (k["HOUSING10"] >= 2500) & (k["HOUSING10"] < 25000)),
                        ("over 25,000 homes", k["HOUSING10"] >= 25000)):
            x, y = perm[m], k["census_change"][m]
            ok = x > 0
            gx, gy = x / k["HOUSING10"][m], y / k["HOUSING10"][m]
            out.append(dict(permit_years=lab, band=band, places=int(m.sum()),
                            correlation=float(np.corrcoef(x, y)[0, 1]) if m.sum() > 2 else np.nan,
                            correlation_rates=float(np.corrcoef(gx, gy)[0, 1]) if m.sum() > 2 else np.nan,
                            median_ratio=float((y[ok] / x[ok]).median()), total_ratio=float(y.sum() / x.sum()),
                            share_disagree=float(((y - x).abs() > np.maximum(0.5 * x, 50)).mean()),
                            share_agree_above_median=float(((gx > gx.median()) == (gy > gy.median())).mean())))
    s = pd.DataFrame(out)
    s.round(4).to_csv(REFERENCE / "parking_census_check_summary.csv", index=False)
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

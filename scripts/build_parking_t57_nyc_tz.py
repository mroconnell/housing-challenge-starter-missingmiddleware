"""Test 57 audit addendum 2: the 2016 NYC Transit Zone line, its checks, and pre-period balance across it.

    uv run python scripts/build_parking_t57_nyc_tz.py

READS NO OUTCOMES. No permit, DOB job or HPD unit is read. Housing here is the existing stock in MapPLUTO 16v1
(March 2016 release: residential units and year built of existing buildings), as the plan's balance check asks.

Inputs (git-ignored, from scripts/fetch_parking_t57_gis.py and earlier fetches):
  data/raw/parking_t57/nyctransitzones_201601.zip   DCP Transit Zones 2016 (primary 2016 line)
  data/raw/parking_t57/nyc_transit_zones_appendix_i_current.geojson   current layer (dpnc-b2hd)
  data/raw/parking_t57/appendixi_2016.pdf   Appendix I as adopted (eff. 3/22/16), Key Map and Maps 1-15
  data/raw/parking_t57/nycd_16a.zip, nybb_16a.zip   community districts, boroughs (DCP 16A)
  data/raw/tod_cases/nyc/mappluto_16v1.zip   lots (zoning, lot area, units, year built) as of March 2016
  data/processed/tod_station_area/nyc_phl_cache/pluto_18v1_shapes.parquet   lot shapes (amendment blocks only)

Steps
 1. Rebuild (check): current layer minus the land each later amendment added, taken from the amendments' own
    descriptions (tax blocks / bounding streets; every post-2016 amendment only added land):
      N 180084 ZRX (2019-02-13, Map 1): Bronx block 5087 (E 241 St, Furman Av, E 240 St, White Plains Rd).
      N 220313 ZRK (2022-11-22, Map 12): Brooklyn blocks 4430, 4431, 4434 (Flatlands, Pennsylvania, Vandalia,
        Louisiana Avs).
      N 240016 ZRX (2024-08-15, Key Map, Maps 2-3): Bronx blocks fronting the six pieces the CPC report lists around
        Bronxdale Av (Poplar St, Sacket Av, Pierce Av, Van Nest Av, E Tremont Av): 4042, 4045, 4046, 4058, 4060,
        4061, 4062, 4063, 4091. The report adds partial blocks, so this block-level rebuild over-removes.
      N 230183 ZRK (2024-11-21, Maps 13-14): Brooklyn blocks 5509, 5516, 5523 (59th-62nd St, 15th-16th Av).
    The rebuild is compared with the 2016 DCP file on a 50 ft raster, map by map.
 2. Map-by-map check of the 2016 DCP file against the adopted Appendix I map pages: each page (rendered with
    pdftoppm when available) is fitted to the GIS raster (scale and shift, by correlation), and the share of the
    page's map pixels where shading and GIS agree is reported, for the 2016 file and for the current layer.
 3. Line type: the 2016 line, sampled every 25 ft, is classed by what lies 60 ft either side: water/outside the city,
    a borough line, a community-district line, a zoning-district change (modal ZoneDist1 of 16v1 lots within
    300 ft on each side, lot centroids), or none.
 4. Arms and cells: 500 m cells on the plan's edge bands (50-400 m inside vs outside the land line, 50 m donut);
    a cell crossing the line is split, each part to its arm. Balance per arm from 16v1 lots (by centroid); outside
    lots in Manhattan CDs 101-108 (Manhattan Core, already treated) are left out of the balance (audit 06:28 UTC).
    The cell counts are of land, not lots, and still include that part of the outside band.
Output: reference/parking_t57_nyc_tz_check.csv (long table: section, item, arm, value, unit, note).
"""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage, signal
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

D = RAW / "parking_t57"
NYC = RAW / "tod_cases" / "nyc"
SHAPES18 = ROOT / "data/processed/tod_station_area/nyc_phl_cache/pluto_18v1_shapes.parquet"
OUT = ROOT / "reference/parking_t57_nyc_tz_check.csv"
FT = 0.3048006096012192                      # metres per US survey foot (EPSG:2263 unit)
STEP = 50.0                                  # raster cell, ft
BOX = (970000.0, 140000.0, 1052000.0, 275000.0)   # raster extent, EPSG:2263 ft (covers both layers + 2 km)
CELL = 500 / FT                              # 500 m grid cell in ft
BAND_IN, BAND_OUT = 50 / FT, 400 / FT        # donut and band edge (ft)
AMEND = {  # (borough code, blocks, maps, ULURP, effective date)
    "E 241 St": (2, [5087], "1", "N 180084 ZRX", "2019-02-13"),
    "Innovative Urban Village": (3, [4430, 4431, 4434], "12", "N 220313 ZRK", "2022-11-22"),
    "Bronx Metro-North (Eastchester-East Tremont)": (2, [4042, 4045, 4046, 4058, 4060, 4061, 4062, 4063, 4091],
                                                     "Key, 2, 3", "N 240016 ZRX", "2024-08-15"),
    "Brooklyn Yards": (3, [5509, 5516, 5523], "13, 14", "N 230183 ZRK", "2024-11-21"),
}
# Key Map frames, pixel boxes on the key map rendered at 150 dpi (cols c0-c1, rows r0-r1), read from its frame lines;
# georeferenced by correlating the key map's shading with the 2016 raster (109 ft per pixel; col 354 = x 970000,
# row 672 = y 275000). Used only to bound the page fit search.
KEY = {1: (682, 885, 724, 849), 2: (741, 941, 835, 959), 3: (681, 883, 904, 1027), 4: (572, 772, 1120, 1245),
       5: (584, 783, 1199, 1324), 6: (762, 961, 1183, 1308), 7: (797, 995, 1280, 1405), 8: (880, 1077, 1334, 1460),
       9: (642, 841, 1340, 1466), 10: (857, 1055, 1434, 1560), 11: (688, 889, 1414, 1538), 12: (635, 834, 1499, 1626),
       13: (450, 651, 1553, 1678), 14: (428, 628, 1623, 1748), 15: (451, 651, 1737, 1861)}
rows_out: list[dict] = []


def rec(section, item, value, unit="", arm="", note=""):
    rows_out.append(dict(section=section, item=item, arm=arm, value=value, unit=unit, note=note))


def unzip_shp(zp: Path, tmp: Path) -> Path:
    with zipfile.ZipFile(zp) as z:
        z.extractall(tmp / zp.stem)
    return next((tmp / zp.stem).rglob("*.shp"))


def raster(polys, xs, ys) -> np.ndarray:
    X_, Y_ = np.meshgrid(xs, ys)
    return G.points_in_any(X_.ravel(), Y_.ravel(), polys, union=True).reshape(X_.shape)


def pluto16() -> pd.DataFrame:
    z = NYC / "mappluto_16v1.zip"
    cols = ["Borough", "Block", "Lot", "CD", "ZoneDist1", "LotArea", "UnitsRes", "YearBuilt", "LandUse", "XCoord", "YCoord"]
    out = []
    for n in [n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith("mappluto.shp")]:
        out.append(X.read_vector(f"zip://{z}!{n}", columns=cols, geometry=False))
    d = pd.concat(out, ignore_index=True)
    d["boro"] = d.Borough.map({"MN": 1, "BX": 2, "BK": 3, "QN": 4, "SI": 5})
    return d[(d.XCoord > 0) & (d.YCoord > 0)].reset_index(drop=True)


def amendment_mask(xs, ys) -> tuple[np.ndarray, dict]:
    L = X.read_geoparquet_wkb(SHAPES18, columns=["bbl"])
    bbl = L.attrs.bbl.to_numpy()
    boro, block = (bbl // 1e9).astype(int), ((bbl % 1e9) // 1e4).astype(int)
    total = np.zeros((len(ys), len(xs)), bool)
    per = {}
    for name, (b, blocks, *_r) in AMEND.items():
        idx = np.flatnonzero((boro == b) & np.isin(block, blocks))
        polys = X.polys_to_crs([L.polys[i] for i in idx], L.crs, G.crs(2263))
        fb = X.feature_bounds(polys)
        i0, i1 = np.searchsorted(xs, fb[:, 0].min() - 200), np.searchsorted(xs, fb[:, 2].max() + 200)
        j0, j1 = np.searchsorted(ys, fb[:, 1].min() - 200), np.searchsorted(ys, fb[:, 3].max() + 200)
        m = np.zeros_like(total)
        m[j0:j1, i0:i1] = raster(polys, xs[i0:i1], ys[j0:j1])
        m = ndimage.binary_dilation(m, iterations=1)          # reach the street centre line (~50 ft)
        per[name] = m
        total |= m
    return total, per


def pgm(path: Path) -> np.ndarray:
    d = path.read_bytes()
    m = re.match(rb"P5\s+(\d+)\s+(\d+)\s+(\d+)\s", d)
    return np.frombuffer(d[m.end():], np.uint8).reshape(int(m[2]), int(m[1]))


def page_fit(k: int, page: np.ndarray, A16: np.ndarray, Acur: np.ndarray, ytop: float) -> dict:
    """Fit adopted map page k (north rotated to the left on the page) to the north-up 50 ft rasters."""
    g = np.rot90(page, k=-1)
    dark = g < 200
    rows, cols = np.flatnonzero(dark.mean(1) > 0.12), np.flatnonzero(dark.mean(0) > 0.12)
    g = g[rows.min() + 4:rows.max() - 4, cols.min() + 4:cols.max() - 4]
    P = np.zeros(g.shape, np.float32)
    P[(g >= 150) & (g <= 190)] = 1                         # Transit Zone fill (grey 170)
    P[g >= 240] = -1                                       # outside (white); lines and labels left out (0)
    c0, c1, r0, r1 = KEY[k]
    kx0, kx1 = 970000 + (c0 - 354) * 109.0, 970000 + (c1 - 354) * 109.0
    ky0, ky1 = 275000 - (r1 - 672) * 109.0, 275000 - (r0 - 672) * 109.0
    pad = 12000.0
    i0 = max(int((kx0 - pad - BOX[0]) / STEP), 0)
    i1 = min(int((kx1 + pad - BOX[0]) / STEP), A16.shape[1])
    j0 = max(int((ytop - (ky1 + pad)) / STEP), 0)
    j1 = min(int((ytop - (ky0 - pad)) / STEP), A16.shape[0])
    sub = A16[j0:j1, i0:i1].astype(np.float32)
    best = None
    for s in np.arange(18.0, 26.01, 0.25):
        T = ndimage.zoom(sub, STEP / s, order=0) * 2 - 1
        if T.shape[0] < P.shape[0] or T.shape[1] < P.shape[1]:
            continue
        c = signal.fftconvolve(T, P[::-1, ::-1], mode="valid")
        j, i = np.unravel_index(np.argmax(c), c.shape)
        sc = c[j, i] / np.abs(P).sum()
        if best is None or sc > best[0]:
            best = (sc, s, i, j)
    sc, s, i, j = best
    h, w = P.shape
    xs = BOX[0] + i0 * STEP + (i + np.arange(w) + 0.5) * s
    ys = ytop - j0 * STEP - (j + np.arange(h) + 0.5) * s
    ci, rj = ((xs - BOX[0]) / STEP).astype(int), ((ytop - ys) / STEP).astype(int)
    ok, okr = (ci >= 0) & (ci < A16.shape[1]), (rj >= 0) & (rj < A16.shape[0])
    Gr, W = P == 1, P == -1
    M = 30                                                 # score only the interior: the page box can catch title/legend rows
    interior = np.zeros(P.shape, bool); interior[M:-M, M:-M] = True
    Gr, W = Gr & interior, W & interior
    out = dict(fit_score=float(sc), ft_per_px=float(s), x0=float(xs[0]), x1=float(xs[-1]), y0=float(ys[-1]), y1=float(ys[0]))
    pxha = (s * FT) ** 2 / 1e4
    for nm, A in (("2016", A16), ("current", Acur)):
        R = np.zeros((h, w), bool)
        R[np.ix_(okr, ok)] = A[np.ix_(rj[okr], ci[ok])]
        out[f"agree_{nm}"] = float(((Gr & R) | (W & ~R)).sum() / (Gr | W).sum())
        out[f"adopted_only_ha_{nm}"] = float((Gr & ~R).sum() * pxha)
        out[f"gis_only_ha_{nm}"] = float((W & R).sum() * pxha)
        # substantive differences: wider than ~2 page pixels (~13 m) after an opening
        out[f"adopted_only_ha_{nm}_wide"] = float(ndimage.binary_opening(Gr & ~R, iterations=2).sum() * pxha)
        out[f"gis_only_ha_{nm}_wide"] = float(ndimage.binary_opening(W & R, iterations=2).sum() * pxha)
    return out


def boundary_samples(polys, spacing: float):
    px, py, nx, ny = [], [], [], []
    for f in polys:
        for part in f:
            for r in part:
                r = r if np.allclose(r[0], r[-1]) else np.vstack([r, r[:1]])
                for a, b in zip(r[:-1], r[1:]):
                    L = np.hypot(*(b - a))
                    if L == 0:
                        continue
                    n = max(int(L // spacing), 1)
                    t = (np.arange(n) + 0.5) / n
                    px += list(a[0] + t * (b[0] - a[0])); py += list(a[1] + t * (b[1] - a[1]))
                    nx += [-(b[1] - a[1]) / L] * n; ny += [(b[0] - a[0]) / L] * n
    return np.array(px), np.array(py), np.array(nx), np.array(ny)


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    try:
        run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(tmp: Path) -> None:
    t16 = G.read_shapefile(unzip_shp(D / "nyctransitzones_201601.zip", tmp))
    cur = G.read_geojson(D / "nyc_transit_zones_appendix_i_current.geojson").to_crs(2263)
    cd = X.read_vector(unzip_shp(D / "nycd_16a.zip", tmp), columns=["BoroCD"])
    bb = X.read_vector(unzip_shp(D / "nybb_16a.zip", tmp), columns=["BoroCode"])
    a16 = G.areas(t16.polys).sum() * FT ** 2 / 1e6
    acur = G.areas(cur.polys).sum() * FT ** 2 / 1e6
    rec("layers", "2016 DCP Transit Zone area", round(a16, 3), "km2", note="nyctransitzones_201601 (Bytes archive via Wayback)")
    rec("layers", "current Transit Zone area", round(acur, 3), "km2", note="dpnc-b2hd")

    xs = np.arange(BOX[0], BOX[2], STEP) + STEP / 2
    ys = np.arange(BOX[1], BOX[3], STEP) + STEP / 2
    A16, Acur = raster(t16.polys, xs, ys), raster(cur.polys, xs, ys)
    land = raster(bb.geometry.tolist(), xs, ys)
    pxha = (STEP * FT) ** 2 / 1e4

    # ---- 1. rebuild
    am, per = amendment_mask(xs, ys)
    rebuilt = Acur & ~am
    for name, (b, blocks, maps, ulurp, eff) in AMEND.items():
        m = per[name]
        rec("rebuild", f"{name} ({ulurp}, eff. {eff}, Map {maps}): amendment blocks inside current zone",
            round((m & Acur).sum() * pxha, 2), "ha", note=f"blocks {blocks}")
        rec("rebuild", f"{name}: of which outside the 2016 DCP zone (added land)",
            round((m & Acur & ~A16).sum() * pxha, 2), "ha")
        rec("rebuild", f"{name}: of which inside the 2016 DCP zone (over-removed by block rule)",
            round((m & Acur & A16).sum() * pxha, 2), "ha")
    lab, n = ndimage.label(Acur & ~A16)
    sz = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    expl = ndimage.maximum(am, lab, range(1, n + 1)) if n else np.array([])
    rec("rebuild", "current minus 2016: all added pixels", round((Acur & ~A16).sum() * pxha, 2), "ha",
        note=f"{n} pieces")
    rec("rebuild", "current minus 2016: pieces >= 1 ha", int((sz * pxha >= 1).sum()), "pieces",
        note="; ".join(f"{s * pxha:.1f} ha {'explained' if e else 'NOT explained'}" for s, e in zip(sz, expl) if s * pxha >= 1))
    rec("rebuild", "current minus 2016: unexplained added area (no amendment block)",
        round(((Acur & ~A16) & ~am).sum() * pxha, 2), "ha", note="slivers along the line (re-digitising)")
    rec("rebuild", "2016 minus current: removed area", round((A16 & ~Acur).sum() * pxha, 2), "ha",
        note="no amendment removed land; these are slivers")
    wide = lambda m: ndimage.binary_opening(m, iterations=1)  # noqa: E731  (drop pieces <= ~100 ft wide)
    for nm, m in (("rebuilt not in 2016", rebuilt & ~A16), ("2016 not in rebuilt", A16 & ~rebuilt)):
        rec("rebuild", f"{nm}: all", round(m.sum() * pxha, 2), "ha")
        rec("rebuild", f"{nm}: wider than ~100 ft", round(wide(m).sum() * pxha, 2), "ha")

    # ---- 2. map by map against the adopted pages
    pdf = D / "appendixi_2016.pdf"
    ytop = BOX[1] + len(ys) * STEP
    fits = {}
    if shutil.which("pdftoppm") and pdf.exists():
        subprocess.run(["pdftoppm", "-r", "100", "-gray", "-f", "3", "-l", "17", str(pdf), str(tmp / "p")], check=True)
        for k in range(1, 16):
            f = next(tmp.glob(f"p-{k + 2:02d}.pgm"))
            fits[k] = page_fit(k, pgm(f), A16[::-1], Acur[::-1], ytop)
            print("map", k, {a: round(b, 3) for a, b in fits[k].items()}, flush=True)
    else:
        print("pdftoppm or Appendix I PDF missing: page check skipped")
    for k in range(1, 16):
        amends = [nm for nm, v in AMEND.items() if str(k) in [s.strip() for s in v[2].split(",")]]
        f = fits.get(k)
        if f:
            x0_, x1_, y0_, y1_ = f["x0"], f["x1"], f["y0"], f["y1"]
            ii = (xs >= x0_) & (xs <= x1_); jj = (ys >= y0_) & (ys <= y1_)
            sl = np.ix_(jj, ii)
            rb_extra = wide(rebuilt[sl] & ~A16[sl]).sum() * pxha
            rb_miss = wide(A16[sl] & ~rebuilt[sl]).sum() * pxha
            ok16 = f["agree_2016"] >= f["agree_current"] - 1e-4
            wide16 = f["adopted_only_ha_2016_wide"] + f["gis_only_ha_2016_wide"]
            status = "pass" if rb_extra + rb_miss < 1.0 else "fix"
            note = (f"page fit score {f['fit_score']:.3f} at {f['ft_per_px']:.2f} ft/px; adopted page vs 2016 GIS agree "
                    f"{f['agree_2016']:.2%} of map pixels (vs current GIS {f['agree_current']:.2%}); mismatch wider than "
                    f"~13 m: {wide16:.1f} ha; rebuild vs 2016 GIS (wider than ~100 ft): {rb_extra:.1f} ha extra, "
                    f"{rb_miss:.1f} ha missing; amendments on map: {', '.join(amends) or 'none'}")
            if status == "fix":
                note += "; FIX: the 2016 DCP file is used for this map (it matches the adopted page at least as well as the current layer)"
            if not ok16:
                note += "; WARNING: current GIS matches the adopted 2016 page better than the 2016 file"
            rec("map check", f"Appendix I Map {k}", status, "pass/fix/drop", note=note)
            rec("map check", f"Map {k}: adopted-page agreement, 2016 GIS", round(f["agree_2016"], 4), "share of page map pixels")
            rec("map check", f"Map {k}: adopted-page agreement, current GIS", round(f["agree_current"], 4), "share of page map pixels")
            rec("map check", f"Map {k}: adopted grey not in 2016 GIS, wider than ~13 m", round(f["adopted_only_ha_2016_wide"], 2), "ha")
            rec("map check", f"Map {k}: 2016 GIS not grey on adopted page, wider than ~13 m", round(f["gis_only_ha_2016_wide"], 2), "ha")
        else:
            rec("map check", f"Appendix I Map {k}", "unchecked", "pass/fix/drop", note="page render unavailable")
    # Text check: the "all of" community districts in the adopted text vs the 2016 file
    allof = [101 + i for i in (8, 9, 10, 11)] + [201, 202, 204, 205, 206, 207] + [301, 302, 303, 304, 306, 307, 308, 309, 316]
    cdmask = raster(cd.geometry.tolist(), xs, ys)
    cdid = np.full(A16.shape, -1)
    X_, Y_ = np.meshgrid(xs, ys)
    inside = cdmask.ravel()
    ids = X.first_within(X_.ravel()[inside], Y_.ravel()[inside], cd.geometry.tolist())
    tmpid = cdid.ravel(); tmpid[np.flatnonzero(inside)] = np.where(ids >= 0, cd.BoroCD.to_numpy()[np.clip(ids, 0, None)], -1)
    cdid = tmpid.reshape(A16.shape)
    for c in allof:
        m = cdid == c
        rec("text check", f"CD {c} ('all of' in adopted text): share of land inside 2016 GIS",
            round(float(A16[m].mean()), 4) if m.any() else np.nan, "share of CD land pixels",
            note="Bronx CD 204 is missing from the 4/5/16 web text but hatched on the key map (erratum fixed 3/6/17)" if c == 204 else "")
    removed = {"Bronx CD 203 (Council removed from 'all of'; Morrisania white on Map 3)": 203,
               "Brooklyn CD 312 (Council removed)": 312, "Brooklyn CD 313 (Council removed; Coney Island)": 313}
    for nm, c in removed.items():
        m = cdid == c
        rec("text check", f"{nm}: share of land inside 2016 GIS", round(float(A16[m].mean()), 4), "share of CD land pixels")
    rock = cdid == 414
    rec("text check", "Queens CD 414 (Rockaways; never in zone): share inside 2016 GIS", round(float(A16[rock].mean()), 4),
        "share of CD land pixels")

    # ---- 3. line type of the 2016 line
    px, py, nx, ny = boundary_samples(t16.polys, 25.0)
    off = 60.0
    sides = []
    for sgn in (1, -1):
        qx, qy = px + sgn * off * nx, py + sgn * off * ny
        b = X.first_within(qx, qy, bb.geometry.tolist())
        c = X.first_within(qx, qy, cd.geometry.tolist())
        sides.append((np.where(b >= 0, bb.BoroCode.to_numpy()[np.clip(b, 0, None)], -1),
                      np.where(c >= 0, cd.BoroCD.to_numpy()[np.clip(c, 0, None)], -1)))
    water = (sides[0][0] < 0) | (sides[1][0] < 0)
    boro_line = ~water & (sides[0][0] != sides[1][0])
    cd_line = ~water & (sides[0][1] != sides[1][1])
    lots = pluto16()
    tree = cKDTree(np.c_[lots.XCoord, lots.YCoord])
    zd = lots.ZoneDist1.fillna("").to_numpy()
    zone_change = np.zeros(len(px), bool)
    no_lots = np.zeros(len(px), bool)
    nb = tree.query_ball_point(np.c_[px, py], r=300.0)
    for k, cand in enumerate(nb):
        if water[k] or not cand:
            no_lots[k] = True
            continue
        cand = np.asarray(cand)
        s = (lots.XCoord.to_numpy()[cand] - px[k]) * nx[k] + (lots.YCoord.to_numpy()[cand] - py[k]) * ny[k]
        a_, b_ = zd[cand[s > 20]], zd[cand[s < -20]]
        if not len(a_) or not len(b_):
            no_lots[k] = True
            continue
        zone_change[k] = pd.Series(a_).mode().iloc[0] != pd.Series(b_).mode().iloc[0]
    L = len(px) * 25.0 * FT / 1000
    landL = (~water).sum() * 25.0 * FT / 1000
    rec("line type", "2016 line length, all", round(L, 1), "km")
    rec("line type", "2016 line: water or city edge on one side", round(water.mean(), 4), "share of all line length")
    rec("line type", "2016 land line length (both sides city land)", round(landL, 1), "km")
    lm = ~water
    rec("line type", "land line along a borough line", round(boro_line[lm].mean(), 4), "share of land line length")
    rec("line type", "land line along a community-district line (incl. borough lines)", round(cd_line[lm].mean(), 4), "share of land line length")
    rec("line type", "land line along a zoning-district change (16v1 lots, modal ZoneDist1 each side)",
        round(zone_change[lm].mean(), 4), "share of land line length", note="approximate: lot centroids within 300 ft each side")
    rec("line type", "land line along a zoning change and not a CD line", round((zone_change & ~cd_line)[lm].mean(), 4), "share of land line length")
    rec("line type", "land line along neither a CD line nor a zoning change", round((~zone_change & ~cd_line)[lm].mean(), 4),
        "share of land line length", note="line cuts through a district and its zoning")
    rec("line type", "land line with no lots on one side within 300 ft (parks, rail yards)", round(no_lots[lm].mean(), 4),
        "share of land line length")

    # ---- 4. arms, cells, balance
    lx, ly = px[lm], py[lm]
    dist = np.full(A16.shape, np.inf)
    t2 = cKDTree(np.c_[lx, ly])
    dd, _ = t2.query(np.c_[X_.ravel(), Y_.ravel()], distance_upper_bound=BAND_OUT + 200)
    dist = dd.reshape(A16.shape)
    inb = land & A16 & (dist >= BAND_IN) & (dist <= BAND_OUT)
    outb = land & ~A16 & (dist >= BAND_IN) & (dist <= BAND_OUT)
    cid = (((Y_ - BOX[1]) // CELL).astype(int) * 10000 + ((X_ - BOX[0]) // CELL).astype(int))
    for nm, m in (("inside (Transit Zone)", inb), ("outside", outb)):
        parts = pd.Series(np.ones(m.sum())).groupby(cid[m]).sum() * pxha
        rec("cells", "500 m cell parts in the 50-400 m band", int(len(parts)), "cell parts", nm)
        rec("cells", "500 m cell parts in the band with >= 1 ha of land", int((parts >= 1).sum()), "cell parts", nm)
        rec("cells", "band land area", round(m.sum() * pxha, 1), "ha", nm)
    split = len(set(cid[inb].tolist()) & set(cid[outb].tolist()))
    rec("cells", "cells split by the line (a part in each arm)", split, "cells")
    for nm, m in (("inside (Transit Zone)", land & A16), ("outside", land & ~A16)):
        rec("cells", "500 m cell parts citywide (no band)", int(len(np.unique(cid[m]))), "cell parts", nm)

    # lots by centroid
    ci = ((lots.XCoord - BOX[0]) // STEP).astype(int).clip(0, len(xs) - 1)
    rj = ((lots.YCoord - BOX[1]) // STEP).astype(int).clip(0, len(ys) - 1)
    lots["arm"] = np.where(inb[rj, ci], "inside (Transit Zone)", np.where(outb[rj, ci], "outside", ""))
    lots["cell"] = cid[rj, ci]
    # audit code rulings (06:28 UTC): outside lots in Manhattan CDs 101-108 (Manhattan Core, no residential parking
    # minimum since 1982) are already treated, so they are left out of the outside arm's balance
    core = (pd.to_numeric(lots.CD, errors="coerce").between(101, 108)) & (lots.arm == "outside")
    rec("balance", "outside lots dropped: Manhattan Core (CDs 101-108)", int(core.sum()), "lots", "outside",
        note="already treated (no minimums since 1982); audit code rulings 06:28 UTC")
    lots.loc[core, "arm"] = ""

    def zclass(z: str) -> str:
        if re.match(r"R[1-5]", z):
            return "R1-R5 (low density residence)"
        if re.match(r"R([6-9]|10)", z):
            return "R6-R10 (higher density residence)"
        if z.startswith("C"):
            return "C (commercial)"
        if z.startswith("M"):
            return "M (manufacturing)"
        return "other (park, BPC, blank)"
    lots["zc"] = lots.ZoneDist1.fillna("").map(zclass)
    for arm in ("inside (Transit Zone)", "outside"):
        d = lots[lots.arm == arm]
        acres = d.LotArea.sum() / 43560
        rec("balance", "tax lots (centroid in band)", int(len(d)), "lots", arm)
        rec("balance", "lot area", round(acres, 0), "acres", arm)
        rec("balance", "median lot area", float(d.LotArea.median()), "sq ft", arm)
        rec("balance", "mean lot area", round(float(d.LotArea.mean()), 0), "sq ft", arm)
        for zc, s in (d.groupby("zc").LotArea.sum() / d.LotArea.sum()).items():
            rec("balance", f"zoning mix: {zc}", round(float(s), 4), "share of lot area", arm, note="ZoneDist1, PLUTO 16v1")
        u = d.UnitsRes.sum()
        rec("balance", "existing residential units (March 2016 stock)", int(u), "units", arm)
        rec("balance", "existing units per lot acre", round(u / acres, 1), "units per acre", arm)
        hb = d[(d.UnitsRes > 0) & (d.YearBuilt > 1800)]
        rec("balance", "units in buildings built before 1940", round(float(hb.UnitsRes[hb.YearBuilt < 1940].sum() / hb.UnitsRes.sum()), 4),
            "share of units with a year built", arm)
        rec("balance", "median year built (lots with units, unit-weighted)",
            float(np.median(np.repeat(hb.YearBuilt.to_numpy(), hb.UnitsRes.to_numpy()))), "year", arm)
        rec("balance", "lots with any housing", round(float((d.UnitsRes > 0).mean()), 4), "share of lots", arm)
        pc = d.groupby("cell").agg(acres=("LotArea", lambda v: v.sum() / 43560), units=("UnitsRes", "sum"))
        pc = pc[pc.acres >= 2.5]
        rec("balance", "cell parts with >= 2.5 lot acres: median units per lot acre", round(float((pc.units / pc.acres).median()), 1),
            "units per acre (median over cell parts)", arm, note=f"{len(pc)} cell parts")

    pd.DataFrame(rows_out).to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(rows_out)} rows)")


if __name__ == "__main__":
    main()

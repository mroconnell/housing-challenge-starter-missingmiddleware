"""Inputs for parking test F1b (docs/parking/CAUSAL_FRAMEWORK_PLAN.md): Minneapolis 2015 cut, inside vs outside the
areas it covered. Builds inputs only; prints counts, never parking numbers.

    uv run python scripts/fetch_parking_mpls_zones.py [--refresh]

Steps
1. Download the sources (standard-library HTTP) to data/raw/parking_first_stage/mpls_2015_zones/ and write _sources.json.
2. Zones = the City of Minneapolis's own map of the areas, as published with the proposal in June 2015
   ("Residential Off-Street Parking Requirements", reproduced on streets.mn, courtesy of the City). The city has no
   GIS layer of the 2015 areas online, so the map image is digitised here:
   - colour classes: blue "qualifies for 100% reduction" + yellow "smaller development 100% / larger 50%" = covered;
     dark teal = downtown districts; pale green = UA University Area Overlay (excluded by the ordinance);
   - georeferenced by fitting the map's dashed city boundary to the city's boundary layer (scale, offsets,
     rotation; hill-climb on the share of boundary points that land on the dashed line), checked against the city's
     LRT station points (they should sit on the map's station circles);
   - written as pixel-rectangle polygons (lon/lat GeoJSON) to data/processed/parking_first_stage/.
   Ordinance 2015-Or-061 rule: within 1/4 mile of a bus stop, or 1/2 mile of a rail stop, with midday headways of
   15 minutes or less (plus rail stops of projects in FTA Project Development); UA overlay excluded.
3. Geocode the Planning Commission sheet's addresses (column C) with the US Census batch geocoder
   (benchmark Public_AR_Current), "Minneapolis, MN" appended; write data/processed/parking_first_stage/mpls_geocoded.csv.
4. Tag each project inside/outside with missing_middleware.geom and print the F1b cell counts (F1 rules: 5+ homes,
   rows with a "Later Action" entry dropped, downtown rows (column F = Y) left out, unmatched addresses left out).

Geometry uses missing_middleware.geom, numpy and pandas only (no geopandas/shapely/pyproj). The map PNG is decoded
with zlib + numpy.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import re
import struct
import sys
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware import geom  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW  # noqa: E402

D = RAW / "parking_first_stage" / "mpls_2015_zones"
OUT = PROCESSED / "parking_first_stage"
XLSX = RAW / "parking_first_stage" / "mpls_planning_commission_schieferdecker.xlsx"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
UA = "missingmiddleware-research/1.0 (housing challenge; parking test F1b)"
AGOL = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services"

ORDINANCE = dict(
    citation="City of Minneapolis Ordinance No. 2015-Or-061, amending Title 20, Chapter 541 (Off-Street Parking and "
             "Loading), section 541.200 Transit incentives, new Table 541-4.5 'Transit Incentive for Multiple-Family "
             "Dwellings'; author Council Member Bender (a companion ordinance the same day amended Chapter 551, "
             "section 551.175(5)a, PO overlay parking). Ordinance 2015-Or-110 (adopted 2015-12-11) amended Chapter 541 "
             "again; not reviewed here.",
    adopted="2015-07-10 (City Council; Municode ordinance list 'Adopted 7/10/15'; WCCO/CBS 2015-07-10)",
    effective="2015-07-18 (publication; the city's 2015-05-21 presentation schedule: 'July 18th - Publication. "
              "Ordinance in effect.'; the adopted text PDF on the city site was created 2015-07-17). Not confirmed "
              "from the published Finance & Commerce notice.",
    area_rule="Except in the UA University Area Overlay District, multiple-family dwellings of 3+ units within 1/4 mile "
              "of a bus transit stop with midday service headways of 15 minutes or less, or within 1/2 mile of a rail "
              "transit stop with midday headways of 15 minutes or less: minimum parking reduced 100% (3-50 units) or "
              "50% (51+ units). Footnote: also rail stops 'included in a project that has been approved to enter the "
              "Project Development phase by the Federal Transit Administration' (SWLRT, Bottineau). Within 350 feet "
              "of a stop with 15-30 minute midday headways: 10% (both sizes). Downtown districts already had no "
              "minimum.",
    plan_split_note="The locked F1b plan splits at 2015-05-01 ('adoption dates, approximate' in F1). The adoption "
                    "date found is 2015-07-10 and the effective date 2015-07-18; counts are printed for both splits.",
)

# name -> (url, note, licence). Wayback 'id_' URLs return the archived bytes unchanged.
SOURCES = {
    "city_parking_amendment_wcms1p-141891.pdf": (
        "http://web.archive.org/web/20150906110529id_/http://www.minneapolismn.gov/www/groups/public/@cped/documents/webcontent/wcms1p-141891.pdf",
        "Adopted ordinance text (Chapter 541 and Chapter 551 amendments, 'By Bender'), City of Minneapolis CPED web page "
        "file, PDF created 2015-07-17; Internet Archive copy of 2015-09-06. The city's LIMS copy "
        "(lims.minneapolismn.gov/Download/PriorMetaData/-51885/2015-061.pdf) sits behind a bot challenge.",
        "Public record of the City of Minneapolis; no licence stated."),
    "city_proposal_map_streetsmn_201506.png": (
        "https://media.streets.mn/wp-content/uploads/2015/06/Parking-Minimum-Reduction-Area.png",
        "City of Minneapolis map 'Residential Off-Street Parking Requirements' (proposal, June 2015), reproduced in "
        "N. Magrino, 'Minneapolis Proposes to Eliminate Minimum Parking Requirements Near Transit', streets.mn, "
        "2015-06-11 (caption: 'Source: City of Minneapolis'). Used as the zone source.",
        "City of Minneapolis work reproduced by streets.mn; no licence stated."),
    "city_proposal_chart_streetsmn_201506.png": (
        "https://media.streets.mn/wp-content/uploads/2015/06/Parking-Minimum-Chart.png",
        "Proposal table from the same streets.mn post (draft tiers).", "No licence stated."),
    "hfn_map_metrotransit_20151008.pdf": (
        "http://web.archive.org/web/20151008213043id_/http://www.metrotransit.org/Data/Sites/1/media/pdfs/Hi-FrequencyMap.pdf",
        "Metro Transit Hi-Frequency Service Network map (PDF created 2014-12-15, in use through 2015). Reference only: "
        "the city's map covers more corridors than the branded network.",
        "Metropolitan Council / Metro Transit; no licence stated."),
    "hfn_page_metrotransit_20150729.html": (
        "http://web.archive.org/web/20150729024445id_/http://www.metrotransit.org:80/hi-frequency-network",
        "Metro Transit Hi-Frequency Network page, 2015-07-29 snapshot (route list: parts of 5, 6, 10, 18, 19, 21, 64, "
        "84, 515; all of 54, Blue Line, Green Line).", "No licence stated."),
    "city_boundary.geojson": (
        f"{AGOL}/City_Boundary/FeatureServer/3/query?where=1%3D1&outFields=*&outSR=4326&f=geojson",
        "City of Minneapolis City_Boundary layer (ArcGIS Online), used to georeference the map.",
        "City of Minneapolis Open Data (the city's open-data terms waive copyright to the extent possible)."),
    "transit_stations_city_2015.geojson": (
        f"{AGOL}/Transit_Stations/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson",
        "City of Minneapolis Transit_Stations layer (LRT stations, data last edited 2015-12-02); georeference check.",
        "City of Minneapolis Open Data: 'City of Minneapolis has waived all copyright and related or neighboring "
        "rights to Open Data'."),
}
# Fetched by hand with WebFetch (metrocouncil.org refuses scripted downloads); kept as context, not re-fetched.
MANUAL = {
    "metc_residential_parking_reform_presentation_2015-05-21.pdf": (
        "https://metrocouncil.org/Communities/Planning/TOD/Files/Residential-Parking-Reform-Presentation.aspx",
        "City of Minneapolis 'Residential Parking Reform' presentation, 2015-05-21 (draft Table 541-4.5; schedule "
        "with 2015-07-10 Council and 2015-07-18 publication/effect).", "No licence stated."),
    "metc_case_study_minneapolis_parking_2018.pdf": (
        "https://metrocouncil.org/Communities/Planning/TOD/Files/Case-Study-Minneapolis-Parking-Regulations.aspx",
        "Metropolitan Council TOD Guide case study, July 2018 (final rule table).", "No licence stated."),
}


# ------------------------------------------------------------------------------------------------- downloads
def get(url: str, data: bytes | None = None, headers: dict | None = None, tries: int = 4, timeout: int = 180) -> bytes:
    h = {"User-Agent": UA, **(headers or {})}
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as r:
                b = r.read()
            if b"Internet Archive: Temporarily Offline" in b[:3000]:
                raise IOError("Internet Archive temporarily offline")
            return b
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (k + 1))
    raise IOError(f"{url}: {last}")


def check_bytes(name: str, b: bytes) -> None:
    ok = {".pdf": b[:4] == b"%PDF", ".png": b[:8] == b"\x89PNG\r\n\x1a\n", ".geojson": b[:1] == b"{",
          ".html": b"<html" in b[:3000].lower()}[Path(name).suffix]
    if not ok or (name.endswith(".geojson") and b'"features"' not in b):
        raise IOError(f"{name}: unexpected content ({b[:80]!r})")


def fetch_sources(refresh: bool) -> None:
    D.mkdir(parents=True, exist_ok=True)
    man = {}
    old = json.loads((D / "_sources.json").read_text()) if (D / "_sources.json").exists() else {}
    for name, (url, note, lic) in SOURCES.items():
        p = D / name
        if refresh or not p.exists():
            b = get(url)
            check_bytes(name, b)
            p.write_bytes(b)
            when = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        else:
            when = old.get("files", {}).get(name, {}).get("accessed_utc", "before this run")
        man[name] = dict(url=url, accessed_utc=when, bytes=p.stat().st_size,
                         sha256=hashlib.sha256(p.read_bytes()).hexdigest(), note=note, licence=lic)
    for name, (url, note, lic) in MANUAL.items():
        p = D / name
        if p.exists():
            man[name] = dict(url=url, accessed_utc=old.get("files", {}).get(name, {}).get("accessed_utc", "2026-11-03 (WebFetch)"),
                             bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                             note=note + " Fetched by hand; this script does not re-download it.", licence=lic)
    rec = dict(test="F1b, docs/parking/CAUSAL_FRAMEWORK_PLAN.md", ordinance=ORDINANCE,
               zone_source=dict(
                   chosen="city_proposal_map_streetsmn_201506.png (City of Minneapolis map, June 2015), digitised",
                   why="No City GIS layer of the 2015 transit incentive areas was found on opendata.minneapolismn.gov or "
                       "the city's ArcGIS Online organisation (searched: parking, transit, frequent, station area; "
                       "HighFrequencyNetwork / High_Frequency_Transit_And_Walksheds are undocumented 2019-2024 "
                       "layers). The city's own 2015 map is used rather than rebuilding from Metro Transit's branded "
                       "Hi-Frequency Network, which is narrower than the ordinance's stop-level 15-minute rule.",
                   caveats=["Map is the June 2015 proposal map; the adopted text dropped the draft 350-ft tier but kept "
                            "the 1/4-mile bus / 1/2-mile rail areas, so the covered union is unchanged in wording.",
                            "Map note: portions of the buffers are drawn from the bus line, not the stops; the "
                            "ordinance requires proximity to a stop, so the map can over-cover between stops.",
                            "Raster ~16 m per pixel; georeference error checked against LRT stations.",
                            "Headways changed over 2015-2021; the zones are fixed at the June 2015 map."]),
               geocoder=dict(url=CENSUS, benchmark="Public_AR_Current", licence="US Census Bureau, public domain"),
               files=man)
    (D / "_sources.json").write_text(json.dumps(rec, indent=2))


# ------------------------------------------------------------------------------------------------- PNG decode
def read_png(path: Path) -> np.ndarray:
    b = path.read_bytes()
    i, idat, hdr = 8, b"", None
    while i < len(b):
        n = struct.unpack(">I", b[i:i + 4])[0]
        t, d = b[i + 4:i + 8], b[i + 8:i + 8 + n]
        i += 12 + n
        if t == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", d)
        elif t == b"IDAT":
            idat += d
    w, h, bd, ct, _, _, il = hdr
    assert bd == 8 and il == 0 and ct in (2, 6), "only 8-bit RGB/RGBA non-interlaced PNG"
    ch = 3 if ct == 2 else 4
    raw, stride = __import__("zlib").decompress(idat), w * ch
    out, prev = np.zeros((h, stride), np.int32), np.zeros(stride, np.int32)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = np.frombuffer(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)], np.uint8).astype(np.int32)
        if f == 0:
            cur = line
        elif f == 2:
            cur = (line + prev) & 255
        else:
            cur = np.zeros(stride, np.int32)
            for x in range(stride):
                a = cur[x - ch] if x >= ch else 0
                up, c = prev[x], (prev[x - ch] if x >= ch else 0)
                if f == 1:
                    p = a
                elif f == 3:
                    p = (a + up) >> 1
                else:
                    pa, pb, pc = abs(up - c), abs(a - c), abs(a + up - 2 * c)
                    p = a if (pa <= pb and pa <= pc) else (up if pb <= pc else c)
                cur[x] = (line[x] + p) & 255
        out[y], prev = cur, cur
    return out.reshape(h, w, ch)[:, :, :3]


# ------------------------------------------------------------------------------------------------- zones
LOC = geom._tm(0, -93.27, 1.0, 0, 0, 1.0, "local transverse Mercator, lon_0 -93.27")
MAP_ROWS = 1125  # map frame; legend below


def shift_or(m: np.ndarray, k: int) -> np.ndarray:
    o = m.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


def shift_and(m: np.ndarray, k: int) -> np.ndarray:
    return ~shift_or(~m, k)


def drop_small(m: np.ndarray, min_px: int) -> np.ndarray:
    lab = np.zeros(m.shape, np.int32)
    keep = np.zeros(m.shape, bool)
    H, W = m.shape
    n = 0
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]:
            continue
        n += 1
        stack, comp = [(y0, x0)], []
        lab[y0, x0] = n
        while stack:
            y, x = stack.pop()
            comp.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
        if len(comp) >= min_px:
            ys, xs = zip(*comp)
            keep[list(ys), list(xs)] = True
    return keep


def classify(a: np.ndarray) -> dict[str, np.ndarray]:
    R, G, B = (a[..., k].astype(int) for k in range(3))
    yellow = ((R + G) / 2 - B > 45) & (np.abs(R - G) < 12) & (R > 150)
    blue = (B - R > 60) & (R < 175) & (G > 120) & (G < 215) & (B > 200)
    downtown = (R < 60) & (G > 100) & (G < 160) & (B > 140) & (B < 200)
    ua = (G > 235) & (R > 215) & (R < 245) & (B > 180) & (B < 220)
    # closing (3 px) fills the street lines drawn over the fills; components under 60 px (specks) are dropped
    clean = lambda m: drop_small(shift_and(shift_or(m, 3), 3), 60)  # noqa: E731
    dtm, uam = clean(downtown), clean(ua)
    covered = clean(yellow | blue) & ~dtm & ~uam
    return dict(downtown=dtm, ua=uam, covered=covered)


def boundary_xy() -> tuple[np.ndarray, np.ndarray]:
    g = json.loads((D / "city_boundary.geojson").read_text())["features"][0]["geometry"]
    rings = g["coordinates"] if g["type"] == "Polygon" else [r for p in g["coordinates"] for r in p]
    pts = []
    for r in rings:
        r = np.asarray(r, float)
        for i in range(len(r) - 1):
            n = max(2, int(np.hypot(*(r[i + 1] - r[i])) / 0.0002))
            t = np.linspace(0, 1, n, endpoint=False)[:, None]
            pts.append(r[i] + t * (r[i + 1] - r[i]))
    pts = np.vstack(pts)
    return geom.transform(pts[:, 0], pts[:, 1], 4326, LOC)


def fit_georef(a: np.ndarray) -> dict:
    mx, mn = a.max(2), a.min(2)
    dark = (mx < 90) & (mx - mn < 25)
    dark[MAP_ROWS:] = False
    ys, xs = np.nonzero(dark)
    X, Y = boundary_xy()
    D2 = shift_or(dark, 2)
    H, W = dark.shape

    def to_px(p, X, Y):
        s, tx, ty, rot = p
        c, si = np.cos(rot), np.sin(rot)
        return (c * X - si * Y) / s + tx, -(si * X + c * Y) / s + ty

    def score(p):
        px, py = to_px(p, X, Y)
        ix, iy = np.round(px).astype(int), np.round(py).astype(int)
        ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
        return D2[iy[ok], ix[ok]].sum() / len(X)

    s0 = ((X.max() - X.min()) / (xs.max() - xs.min()) + (Y.max() - Y.min()) / (ys.max() - ys.min())) / 2
    best = (score((s0, xs.min() - X.min() / s0, ys.min() + Y.max() / s0, 0.0)),
            (s0, xs.min() - X.min() / s0, ys.min() + Y.max() / s0, 0.0))
    step = [0.05, 2.0, 2.0, 0.002]
    for _ in range(80):
        improved = False
        for k in range(4):
            for d in (-1, 1):
                p = list(best[1])
                p[k] += d * step[k]
                sc = score(p)
                if sc > best[0]:
                    best, improved = (sc, tuple(p)), True
        if not improved:
            step = [x / 2 for x in step]
    s, tx, ty, rot = best[1]
    # check: LRT stations should sit on the map's dark-blue line / station circles
    st = json.loads((D / "transit_stations_city_2015.geojson").read_text())["features"]
    lon = np.array([f["geometry"]["coordinates"][0] for f in st])
    lat = np.array([f["geometry"]["coordinates"][1] for f in st])
    sx, sy = geom.transform(lon, lat, 4326, LOC)
    px, py = to_px(best[1], sx, sy)
    R, G, B = (a[..., k].astype(int) for k in range(3))
    lrt = (B > 70) & (R < 50) & (B - R > 40) & (B - G > 25)
    lrt[:440] = False  # skip downtown (station marks overlap the teal fill)
    lx, ly = np.nonzero(lrt)[1], np.nonzero(lrt)[0]
    res = [float(np.min(np.hypot(lx - x, ly - y))) * s for x, y in zip(px, py) if y > 560]
    return dict(metres_per_pixel=s, tx=tx, ty=ty, rotation_rad=rot, boundary_hit_share_2px=best[0],
                lrt_station_distance_to_drawn_line_m=dict(n=len(res), median=float(np.median(res)), max=float(np.max(res))))


def pixel_rects(m: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Rectangles (x0, x1, y0, y1) in pixel indices, inclusive, from row runs merged down columns."""
    open_, out = {}, []
    for y in range(m.shape[0]):
        row = np.concatenate([[0], m[y].astype(np.int8), [0]])
        d = np.diff(row)
        runs = set(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1))
        for r in list(open_):
            if r not in runs:
                out.append((r[0], r[1], open_.pop(r), y - 1))
        for r in runs:
            open_.setdefault(r, y)
    out += [(r[0], r[1], y0, m.shape[0] - 1) for r, y0 in open_.items()]
    return out


def px_to_lonlat(px, py, g) -> tuple[np.ndarray, np.ndarray]:
    s, tx, ty, rot = g["metres_per_pixel"], g["tx"], g["ty"], g["rotation_rad"]
    xr, yr = (np.asarray(px, float) - tx) * s, -(np.asarray(py, float) - ty) * s
    c, si = np.cos(-rot), np.sin(-rot)
    X, Y = c * xr - si * yr, si * xr + c * yr
    return geom.transform(X, Y, LOC, 4326)


def build_zones() -> tuple[dict, dict]:
    a = read_png(D / "city_proposal_map_streetsmn_201506.png")
    a = a[:MAP_ROWS]
    masks = classify(a)
    g = fit_georef(a)
    feats = []
    for label in ("downtown", "ua", "covered"):
        polys = []
        for x0, x1, y0, y1 in pixel_rects(masks[label]):
            cx = np.array([x0 - .5, x1 + .5, x1 + .5, x0 - .5, x0 - .5])
            cy = np.array([y0 - .5, y0 - .5, y1 + .5, y1 + .5, y0 - .5])
            lon, lat = px_to_lonlat(cx, cy, g)
            polys.append([np.round(np.c_[lon, lat], 7).tolist()])
        feats.append(dict(type="Feature", properties=dict(zone=label, rectangles=len(polys)),
                          geometry=dict(type="MultiPolygon", coordinates=polys)))
    OUT.mkdir(parents=True, exist_ok=True)
    gj = dict(type="FeatureCollection", features=feats)
    (OUT / "mpls_2015_zones.geojson").write_text(json.dumps(gj))
    g["pixels"] = {k: int(v.sum()) for k, v in masks.items()}
    g["km2"] = {k: round(v * g["metres_per_pixel"] ** 2 / 1e6, 1) for k, v in g["pixels"].items()}
    return gj, dict(georef=g, masks=masks)


# ------------------------------------------------------------------------------------------------- projects
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
COLS = {"A": "date", "B": "name", "C": "address", "D": "neighborhood", "F": "downtown", "G": "homes", "H": "car",
        "J": "later_action"}  # scripts/run_parking_causal_f1.py's COLS plus C = Address


def read_projects() -> pd.DataFrame:
    """Same reader as scripts/run_parking_causal_f1.py, keeping the sheet row number and column C."""
    z = zipfile.ZipFile(XLSX)
    ss = ["".join(t.text or "" for t in si.iter(M + "t"))
          for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si")]
    sheets = re.findall(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="rId(\d+)"', z.read("xl/workbook.xml").decode())
    rows = []
    for name, rid in sheets:
        if not name.isdigit():
            continue
        for r in ET.fromstring(z.read(f"xl/worksheets/sheet{rid}.xml")).iter(M + "row"):
            if int(r.get("r")) == 1:
                continue
            d = {"sheet": int(name), "row": int(r.get("r"))}
            for c in r.findall(M + "c"):
                col = re.match(r"[A-Z]+", c.get("r")).group()
                if col not in COLS:
                    continue
                v = c.find(M + "v")
                d[COLS[col]] = None if v is None else (ss[int(v.text)] if c.get("t") == "s" else v.text)
            rows.append(d)
    df = pd.DataFrame(rows)
    num = pd.to_numeric(df["date"], errors="coerce")
    df = df[num.notna()].copy()
    df["date"] = [pd.Timestamp(date(1899, 12, 30) + timedelta(days=int(x))) for x in num[num.notna()]]
    for c in ("homes", "car"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["later_action"] = df["later_action"].fillna("").astype(str).str.strip()
    df["downtown"] = df["downtown"].fillna("").astype(str).str.strip().str.upper().str[:1]
    df["address"] = df["address"].fillna("").astype(str).str.strip()
    return df.reset_index(drop=True)


def geocode(df: pd.DataFrame, refresh: bool) -> pd.DataFrame:
    resp = D / "census_geocoder_response.csv"
    req = D / "census_geocoder_request.csv"
    ids = df["sheet"].astype(str) + "-" + df["row"].astype(str)
    body = "".join(f'{i},"{a.replace(chr(34), "")}",Minneapolis,MN,\n' for i, a in zip(ids, df["address"]))
    if refresh or not resp.exists() or not req.exists() or req.read_text() != body:
        req.write_text(body)
        bnd = uuid.uuid4().hex
        parts = [f'--{bnd}\r\nContent-Disposition: form-data; name="benchmark"\r\n\r\nPublic_AR_Current\r\n'.encode(),
                 f'--{bnd}\r\nContent-Disposition: form-data; name="addressFile"; filename="addresses.csv"\r\n'
                 f'Content-Type: text/csv\r\n\r\n'.encode() + body.encode() + b"\r\n", f"--{bnd}--\r\n".encode()]
        out = get(CENSUS, data=b"".join(parts), headers={"Content-Type": f"multipart/form-data; boundary={bnd}"},
                  timeout=600)
        resp.write_bytes(out)
        src = json.loads((D / "_sources.json").read_text())
        src["files"]["census_geocoder_response.csv"] = dict(
            url=CENSUS, accessed_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            bytes=len(out), sha256=hashlib.sha256(out).hexdigest(), licence="US Census Bureau, public domain",
            note="Batch response, benchmark Public_AR_Current; request in census_geocoder_request.csv "
                 "(id = sheet-row, street = column C as written, city Minneapolis, state MN).")
        (D / "_sources.json").write_text(json.dumps(src, indent=2))
    r = pd.read_csv(io.StringIO(resp.read_text()), header=None, dtype=str,
                    names=["id", "input", "status", "match_type", "matched_address", "lonlat", "tiger_id", "side"])
    r = r.set_index("id")
    g = df[["sheet", "row", "date", "address"]].copy()
    g["id"] = ids.values
    st = g["id"].map(r["status"])
    g["matched"] = st.eq("Match")
    ll = g["id"].map(r["lonlat"]).where(g["matched"])
    g["lon"] = pd.to_numeric(ll.str.split(",").str[0], errors="coerce")
    g["lat"] = pd.to_numeric(ll.str.split(",").str[1], errors="coerce")
    g["census_status"] = st.fillna("missing")
    g["match_type"] = g["id"].map(r["match_type"])
    g["matched_address"] = g["id"].map(r["matched_address"])
    OUT.mkdir(parents=True, exist_ok=True)
    g.drop(columns="id")[["sheet", "row", "date", "matched", "lat", "lon", "address", "census_status", "match_type",
                          "matched_address"]].to_csv(OUT / "mpls_geocoded.csv", index=False)
    return g


def tag(g: pd.DataFrame, gj: dict, z: dict) -> pd.Series:
    lay = geom.read_geojson(gj)
    lab = pd.Series("unmatched", index=g.index)
    m = g["matched"].to_numpy()
    lon, lat = g.loc[m, "lon"].to_numpy(), g.loc[m, "lat"].to_numpy()
    idx = geom.points_in_polygons(lon, lat, lay.polys, union=True)
    names = lay.attrs["zone"].tolist()
    lab[m] = ["outside" if k < 0 else names[k] for k in idx]
    return lab


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download sources and re-geocode")
    args = ap.parse_args()
    fetch_sources(args.refresh)
    gj, z = build_zones()
    df = read_projects()
    g = geocode(df, args.refresh)
    df["matched"], df["lon"], df["lat"] = g["matched"].values, g["lon"].values, g["lat"].values
    df["zone"] = tag(df, gj, z).values
    # pixel-edge check: matched points within 2 pixels (~33 m) of a covered/not-covered edge
    gr = z["georef"]
    X, Y = geom.transform(df["lon"].fillna(0).to_numpy(), df["lat"].fillna(0).to_numpy(), 4326, LOC)
    c, si = np.cos(gr["rotation_rad"]), np.sin(gr["rotation_rad"])
    px = np.round((c * X - si * Y) / gr["metres_per_pixel"] + gr["tx"]).astype(int)
    py = np.round(-(si * X + c * Y) / gr["metres_per_pixel"] + gr["ty"]).astype(int)
    cov = z["masks"]["covered"]
    H, W = cov.shape
    near = np.zeros(len(df), bool)
    for k in np.flatnonzero(df["matched"].to_numpy()):
        if 2 <= px[k] < W - 2 and 2 <= py[k] < H - 2:
            w = cov[py[k] - 2:py[k] + 3, px[k] - 2:px[k] + 3]
            near[k] = w.any() and not w.all()
    df["near_edge_33m"] = near
    df[["sheet", "row", "date", "zone", "near_edge_33m"]].to_csv(OUT / "mpls_f1b_zone_tags.csv", index=False)
    (OUT / "mpls_2015_zones_diagnostics.json").write_text(json.dumps(gr, indent=2))

    print(f"geocoded addresses: {len(g)} rows; matched {int(g['matched'].sum())}; not matched {int((~g['matched']).sum())} "
          f"(No_Match {int((g['census_status'] == 'No_Match').sum())}, Tie {int((g['census_status'] == 'Tie').sum())}, "
          f"other {int((~g['census_status'].isin(['Match', 'No_Match', 'Tie'])).sum())})")
    print(f"georeference: {gr['metres_per_pixel']:.2f} m per pixel; boundary hit share {gr['boundary_hit_share_2px']:.3f}; "
          f"LRT stations off drawn line: median {gr['lrt_station_distance_to_drawn_line_m']['median']:.0f} m, "
          f"max {gr['lrt_station_distance_to_drawn_line_m']['max']:.0f} m (n={gr['lrt_station_distance_to_drawn_line_m']['n']})")
    # F1 rules
    f = df.dropna(subset=["homes", "car"])
    f = f[(f["homes"] >= 5) & (f["later_action"] == "") & (f["downtown"] != "Y")]
    print(f"F1 rows (5+ homes, no Later Action, outside downtown): {len(f)}; geocode not matched, left out: "
          f"{int((~f['matched']).sum())}")
    f = f[f["matched"]].copy()
    f["side"] = np.where(f["zone"] == "covered", "inside", "outside")
    END = pd.Timestamp("2021-05-14")
    for cut, lab in ((pd.Timestamp("2015-05-01"), "plan split (before <= 2015-04-30; after 2015-05-01..2021-05-13)"),
                     (pd.Timestamp("2015-07-18"), "effective-date split (before <= 2015-07-17; after 2015-07-18..2021-05-13)")):
        f["period"] = np.select([f["date"] < cut, f["date"] < END], ["before", "after"], "later")
        t = pd.crosstab(f.loc[f["period"] != "later", "side"], f.loc[f["period"] != "later", "period"])
        t = t.reindex(index=["inside", "outside"], columns=["before", "after"]).fillna(0).astype(int)
        print(f"\nF1b projects, {lab}:")
        print(t.to_string())
    w = f[f["date"] < END]
    print(f"\nwithin the window: outside includes {int((w['zone'] == 'ua').sum())} in the UA overlay and "
          f"{int((w['zone'] == 'downtown').sum())} in the map's downtown fill (sheet says not downtown); "
          f"{int(w['near_edge_33m'].sum())} projects lie within ~33 m of a zone edge")


if __name__ == "__main__":
    main()

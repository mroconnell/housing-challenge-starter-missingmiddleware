"""Los Angeles Adaptive Reuse Ordinance (1999) descriptive spot check: homes by tract, 1990-2020.

    uv run python scripts/fetch_parking_la_aro_tracts.py

Evidence only (no test, no tool change). Did 2020 tracts in the original 1999 ordinance area (Historic Core / Old Bank
District and the Financial District) go from few homes in 1990/2000 to many by 2010, while nearby non-downtown contrast
tracts did not? The ordinance (Ord. 172571, effective 3 June 1999) froze parking at existing spaces AND waived lot-area
density limits and kept existing floor area/height/yards, so this measures the whole package, not parking alone.

Method (as the TOD project): census blocks of each year are placed by their internal point inside FIXED 2020 tract
outlines (TIGER/Line 2020 tracts), and their counts summed per 2020 tract.
  - 2020: TIGER 2020 block internal points (INTPTLAT20/INTPTLON20); counts from the 2020 PL 94-171 API, H1_001N (total)
          and H1_002N (occupied).
  - 2010: TIGER 2010 block polygons with HOUSING10 (tabblock2010_06_pophu.zip, as TOD reads it) and their interior
          points (missing_middleware.geom_extra_station.interior_points, as build_tod_net_coverage.blocks); occupied
          units from the 2010 SF1 API, H003002 (total H001001 kept as a check against HOUSING10).
  - 2000: TIGER 2000 block internal points (tl_2010_06037_tabblock00, INTPTLAT00/INTPTLON00); counts from the 2000 SF1
          API, H001001 (total) and H003002 (occupied).
  - 1990: STF1B block file (www2.census.gov/census_1990/STF1B_ASCII), which carries each block's internal point in its
          geographic header; H1 (total) and H2 cell 1 (occupied) from the second physical record of each block.
Official Census Bureau files only (no NHGIS, no LTDB). numpy and pandas only for geometry (missing_middleware.geom).
The Census API key is read from the environment / .env at run time and is never printed, logged or saved.

Output: reference/parking_la_aro_tracts.csv; raw files in data/raw/parking_la_aro/ with _sources.json.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware import geom as G  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE, ROOT  # noqa: E402

D = RAW / "parking_la_aro"
OUT = REFERENCE / "parking_la_aro_tracts.csv"
API = "https://api.census.gov/data"

# Chosen from geography only (tract outlines and street landmarks), before any housing count was pulled.
TRACTS = {
    # ARO: original 1999 "Downtown Project Area" = Central City Community Plan Area (+ a strip south of the I-10).
    # The six 2020 tracts 2073.03-.08 together are roughly the old (1990-2010) tract 2073, where Manville (UCTC working
    # paper of the JAPA 2013 study) finds over 6,000 ARO units clustered.
    "06037207306": ("ARO", "Old Bank District: Spring/Main, about 3rd-5th St (Spring & 4th, Main & 3rd fall inside)"),
    "06037207305": ("ARO", "Historic Core: Broadway/Spring, about 4th-6th St (Broadway & 5th, Hill & 6th inside)"),
    "06037207307": ("ARO", "Historic Core: Spring/Main around 5th-6th St"),
    "06037207308": ("ARO", "Historic Core: Spring/Main around 6th-7th St (Spring & 6th inside)"),
    "06037207304": ("ARO", "Historic Core: Broadway/Spring around 5th-6th St, west of 2073.07"),
    "06037207712": ("ARO", "Financial District: Flower/Olive/Grand, about 5th-7th St (Flower & 6th, Olive & 7th inside)"),
    # Contrast: nearby, outside the Central City Community Plan Area and outside the 2003 incentive-area expansion
    # (Chinatown, Lincoln Heights, Hollywood, parts of Wilshire Center/Koreatown, Central Ave south of the I-10).
    "06037206053": ("contrast", "Boyle Heights: 1st St around Mariachi Plaza, east of the LA River"),
    "06037204200": ("contrast", "Boyle Heights: Soto St / Cesar Chavez Ave"),
    "06037208801": ("contrast", "Westlake: MacArthur Park north of Wilshire, west of the 110; not Wilshire Center"),
}

SOURCES = D / "_sources.json"


# --------------------------------------------------------------------------------------------------- helpers
def api_key() -> str:
    k = os.environ.get("CENSUS_API_KEY")
    if not k:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                m = re.match(r"\s*CENSUS_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
                if m:
                    k = m.group(1)
    if not k:
        raise SystemExit("CENSUS_API_KEY not set (environment or .env)")
    return k


def load_sources() -> dict:
    return json.loads(SOURCES.read_text()) if SOURCES.exists() else {}


def record(src: dict, name: str, url: str, note: str, data: bytes | None = None, path: Path | None = None):
    b = data if data is not None else (path.read_bytes() if path and path.exists() else b"")
    src[name] = {"url": url, "publisher": "U.S. Census Bureau", "licence": "U.S. Government work (public domain)",
                 "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                 "retrieved": src.get(name, {}).get("retrieved") or dt.date.today().isoformat(), "note": note}


def download(src: dict, name: str, url: str, note: str) -> Path:
    p = D / name
    if not p.exists():
        with urllib.request.urlopen(url, timeout=900) as r:
            p.write_bytes(r.read())
    record(src, name, url, note, path=p)
    return p


def census_api(src: dict, name: str, path: str, params: dict, note: str) -> pd.DataFrame:
    """One Census API call, cached as raw JSON. The key is added only to the live request, never saved."""
    p = D / "api" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    q = urllib.parse.urlencode(params, safe=":*, ")
    public = f"{API}/{path}?{q}"
    if not p.exists():
        with urllib.request.urlopen(public + "&key=" + urllib.parse.quote(api_key()), timeout=120) as r:
            body = r.read()
        p.write_bytes(body if body.strip() else b"[]")
    record(src, f"api/{name}", public, note, path=p)
    rows = json.loads(p.read_bytes() or b"[]")
    return pd.DataFrame(rows[1:], columns=rows[0]) if rows else pd.DataFrame()


def assign(lon, lat, tracts: G.Layer) -> np.ndarray:
    """2020 tract GEOID holding each point (internal point in fixed 2020 outline), '' outside the chosen tracts."""
    i = G.points_in_polygons(np.asarray(lon, float), np.asarray(lat, float), tracts.polys)
    ids = tracts.attrs["GEOID"].to_numpy()
    return np.where(i >= 0, ids[np.maximum(i, 0)], "")


# --------------------------------------------------------------------------------------------------- years
def year_2020(src, tracts, bbox):
    f = next(p for p in [RAW / "tod_census_cases" / "tl_2020_06_tabblock20.zip",
                         RAW / "census_tiger_2020_tabblock" / "tl_2020_06_tabblock20.zip"] if p.exists())
    record(src, "reused:" + str(f.relative_to(ROOT)),
           "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_06_tabblock20.zip",
           "Reused TOD copy (not re-downloaded): 2020 blocks, internal points INTPTLAT20/INTPTLON20, HOUSING20", path=f)
    L = G.read_shapefile(f, columns=["GEOID20", "COUNTYFP20", "INTPTLAT20", "INTPTLON20", "HOUSING20"])
    a = L.attrs[L.attrs.COUNTYFP20 == "037"].copy()
    a["lon"], a["lat"] = a.INTPTLON20.astype(float), a.INTPTLAT20.astype(float)
    a = a[(a.lon.between(bbox[0], bbox[2])) & (a.lat.between(bbox[1], bbox[3]))].copy()
    a["tract20"] = assign(a.lon, a.lat, tracts)
    a = a[a.tract20 != ""]
    rows = []
    for t in sorted(a.GEOID20.str[5:11].unique()):
        rows.append(census_api(src, f"2020_pl_tract{t}.json", "2020/dec/pl",
                               {"get": "H1_001N,H1_002N", "for": "block:*", "in": f"state:06 county:037 tract:{t}"},
                               "2020 PL 94-171 block H1_001N total, H1_002N occupied"))
    c = pd.concat(rows)
    c["GEOID20"] = c.state + c.county + c.tract + c.block
    m = a.merge(c, on="GEOID20", how="left")
    assert m.H1_001N.notna().all()
    chk = (m.H1_001N.astype(int) != m.HOUSING20.astype(int)).sum()
    m["total"], m["occ"] = m.H1_001N.astype(int), m.H1_002N.astype(int)
    return m, f"2020 PL 94-171 H1 by block; TIGER 2020 internal points (HOUSING20 mismatches: {chk})"


def year_2010(src, tracts, bbox):
    from missing_middleware.geom_extra_station import interior_points, read_vector
    f = RAW / "tod_census_cases" / "tabblock2010_06_pophu.zip"
    record(src, "reused:" + str(f.relative_to(ROOT)),
           "https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_06_pophu.zip",
           "Reused TOD copy (not re-downloaded): 2010 block polygons with HOUSING10", path=f)
    b = read_vector(f, columns=["BLOCKID10", "COUNTYFP10", "HOUSING10"], bbox=bbox)
    b = b[b.COUNTYFP10 == "037"].reset_index(drop=True)
    x, y = interior_points(list(b["geometry"]))
    a = pd.DataFrame({"BLOCKID10": b.BLOCKID10, "HOUSING10": pd.to_numeric(b.HOUSING10), "lon": x, "lat": y})
    a["tract20"] = assign(a.lon, a.lat, tracts)
    a = a[a.tract20 != ""]
    rows = []
    for t in sorted(a.BLOCKID10.str[5:11].unique()):
        rows.append(census_api(src, f"2010_sf1_tract{t}.json", "2010/dec/sf1",
                               {"get": "H001001,H003002", "for": "block:*", "in": f"state:06 county:037 tract:{t}"},
                               "2010 SF1 block H001001 total, H003002 occupied"))
    c = pd.concat(rows)
    c["BLOCKID10"] = c.state + c.county + c.tract + c.block
    m = a.merge(c, on="BLOCKID10", how="left")
    assert m.H001001.notna().all()
    chk = (m.H001001.astype(int) != m.HOUSING10.astype(int)).sum()
    m["total"], m["occ"] = m.HOUSING10.astype(int), m.H003002.astype(int)
    return m, f"2010 HOUSING10 (TIGER pophu) + SF1 H003002 by block; interior points (SF1 H001001 mismatches: {chk})"


def year_2000(src, tracts, bbox):
    f = download(src, "tl_2010_06037_tabblock00.zip",
                 "https://www2.census.gov/geo/tiger/TIGER2010/TABBLOCK/2000/tl_2010_06037_tabblock00.zip",
                 "TIGER/Line 2010 edition of 2000 Census blocks, LA County, internal points INTPTLAT00/INTPTLON00")
    a = G.read_shapefile(f, columns=["BLKIDFP00", "INTPTLAT00", "INTPTLON00"]).attrs
    a["lon"], a["lat"] = a.INTPTLON00.astype(float), a.INTPTLAT00.astype(float)
    a = a[(a.lon.between(bbox[0], bbox[2])) & (a.lat.between(bbox[1], bbox[3]))].copy()
    a["tract20"] = assign(a.lon, a.lat, tracts)
    a = a[a.tract20 != ""]
    rows = []
    for t in sorted(a.BLKIDFP00.str[5:11].unique()):
        rows.append(census_api(src, f"2000_sf1_tract{t}.json", "2000/dec/sf1",
                               {"get": "H001001,H003002", "for": "block:*",
                                "in": f"state:06 county:037 tract:{t[:4] if t.endswith('00') else t}"},
                               "2000 SF1 block H001001 total, H003002 occupied (API drops a '00' tract suffix)"))
    c = pd.concat(rows)
    c["BLKIDFP00"] = c.state + c.county + c.tract.str.ljust(6, "0") + c.block
    m = a.merge(c, on="BLKIDFP00", how="left")
    miss = int(m.H001001.isna().sum())
    assert miss == 0, miss
    m["total"] = pd.to_numeric(m.H001001).fillna(0).astype(int)
    m["occ"] = pd.to_numeric(m.H003002).fillna(0).astype(int)
    return m, f"2000 SF1 H001/H003 by block; TIGER 2000 internal points (blocks without API row: {miss})"


def year_1990(src, tracts, bbox):
    f = download(src, "STF1B-CA.zip", "https://www2.census.gov/census_1990/STF1B_ASCII/STF1B-CA.zip",
                 "1990 STF1B (block) California, fixed width ASCII, 2 physical records per block")
    download(src, "STF1CRDD.ASC", "https://www2.census.gov/census_1990/STF1B_ASCII/TechDoc/STF1CRDD.ASC",
             "1990 STF1 data dictionary: H1 at 6582 (record 2 col 1777), H2 at 6591 (col 1786), 9 wide")
    cache = D / "stf1b_la_downtown_blocks.csv"
    if not cache.exists():
        out = []
        with zipfile.ZipFile(f) as z:
            for n in sorted(z.namelist()):
                with z.open(n) as fh:
                    for raw in io.TextIOWrapper(fh, encoding="latin-1", newline=""):
                        # 1-based dictionary columns -> 0-based slices
                        if raw[10:13] != "100" or raw[71:74] != "037" or raw[24:28] != "0002":
                            continue
                        lat = int(raw[268:277]) / 1e6
                        lon = int(raw[277:287]) / 1e6
                        if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
                            continue
                        out.append({"tract90": raw[51:57], "block90": raw[46:50].strip(), "lat": lat, "lon": lon,
                                    "HU100": int(raw[259:268]), "H1": int(raw[1776:1785]),
                                    "occ": int(raw[1785:1794]), "vac": int(raw[1794:1803])})
        pd.DataFrame(out).to_csv(cache, index=False)
    record(src, cache.name, "derived from STF1B-CA.zip", "Extract: LA County (037) blocks in the study bbox, record 2",
           path=cache)
    a = pd.read_csv(cache, dtype={"tract90": str, "block90": str})
    a["tract20"] = assign(a.lon, a.lat, tracts)
    a = a[a.tract20 != ""].copy()
    chk = int((a.H1 != a.HU100).sum()) + int((a.occ + a.vac != a.H1).sum())
    a["total"] = a.H1
    return a, f"1990 STF1B H1/H2 by block; STF1B header internal points (header/table mismatches: {chk})"


# --------------------------------------------------------------------------------------------------- main
def main():
    D.mkdir(parents=True, exist_ok=True)
    src = load_sources()
    tf = download(src, "tl_2020_06_tract.zip", "https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_06_tract.zip",
                  "TIGER/Line 2020 census tracts, California (fixed 2020 outlines)")
    T = G.read_shapefile(tf, columns=["GEOID", "NAMELSAD"])
    T = T.subset(T.attrs.GEOID.isin(TRACTS))
    assert len(T) == len(TRACTS)
    xy = np.vstack([r for f in T.polys for p in f for r in p])
    bbox = (xy[:, 0].min() - 0.005, xy[:, 1].min() - 0.005, xy[:, 0].max() + 0.005, xy[:, 1].max() + 0.005)
    rows = []
    for yr, fn in [(1990, year_1990), (2000, year_2000), (2010, year_2010), (2020, year_2020)]:
        m, note = fn(src, T, bbox)
        g = m.groupby("tract20").agg(total_units=("total", "sum"), occupied_units=("occ", "sum"),
                                     blocks=("total", "size"))
        for t, (grp, _) in TRACTS.items():
            r = g.loc[t] if t in g.index else None
            rows.append({"tract": t, "tract_name": T.attrs.set_index("GEOID").NAMELSAD[t], "group": grp, "year": yr,
                         "total_units": int(r.total_units) if r is not None else 0,
                         "occupied_units": int(r.occupied_units) if r is not None else 0,
                         "blocks": int(r.blocks) if r is not None else 0, "method_note": note})
        print(yr, note, flush=True)
    SOURCES.write_text(json.dumps(src, indent=1, sort_keys=True))
    out = pd.DataFrame(rows)
    out["reason"] = out.tract.map({k: v[1] for k, v in TRACTS.items()})
    out.to_csv(OUT, index=False)
    print(out.pivot_table(index=["group", "tract"], columns="year", values="total_units").to_string())
    print(out.pivot_table(index=["group", "tract"], columns="year", values="occupied_units").to_string())


if __name__ == "__main__":
    main()

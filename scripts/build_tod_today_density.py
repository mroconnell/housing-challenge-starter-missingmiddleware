"""TOD "today" snapshot: existing homes per acre around Wisconsin's rail and rapid stops and around the stops of six
older TOD upzonings (2020 census blocks, one snapshot, no before/after).

    .venv/bin/python scripts/build_tod_today_density.py           # fetches missing block files first (network)

In:  reference/tod_stops.csv (Wisconsin stops; flag_a_rapid = rail and rapid, the stops behind the 89,528 figure)
     reference/tod_station_area_stations.csv (reform and comparison rail stops of the station-area study)
     data/raw/census_tiger_2020_tabblock/tl_2020_{55,48,53,49,27}_tabblock20.zip (HOUSING20, ALAND20, INTPTLAT20/LON20)
Out: reference/tod_today_density.csv        one row per place and band (aggregates); bands quarter_mile, half_mile and
                                            ring_half_to_one_mile (beyond 1/2 mile and within 1 mile of any stop);
                                            industrial_rezone = 1 for rows that include BelRed's stops (BelRed, the six-place
                                            pool, Bellevue's all-rail row)
     reference/tod_today_density_stops.csv  one row per stop (each stop's own blocks; aggregates)

Method: a block counts if its internal point lies within the radius (1/4 or 1/2 mile, exact distance) of any of the
place's stops (missing_middleware/tod/transit.py blocks_within). Homes = sum of HOUSING20; land = sum of ALAND20
(water excluded) in acres; homes per acre = homes / land acres (pooled). Typical stop = median over the place's stops
of each stop's own homes / land acres within 1/2 mile (a block near two stops counts for both). Distances: Wisconsin
in EPSG:3071 (as build_tod_stops.py); other places in a transverse Mercator centred on the place's stops (scale 1).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import geom as G  # noqa: E402
from missing_middleware.dbf import read_shapefile_attributes  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import transit as T  # noqa: E402

D = RAW / "census_tiger_2020_tabblock"
URL = "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{st}_tabblock20.zip"
ACRE_M2 = 4046.8564224
BANDS = {"quarter_mile": 0.25 * T.MILE_M, "half_mile": 0.5 * T.MILE_M}
# Third band (owner 2026-11-02): the ring beyond 1/2 mile and within 1 mile of the stops, the nearby neighbourhoods the
# near-stop density is compared with. Pooled totals only (no per-stop rows).
RING = "ring_half_to_one_mile"
RING_M = (0.5 * T.MILE_M, 1.0 * T.MILE_M)
OUT, OUT_STOPS = REFERENCE / "tod_today_density.csv", REFERENCE / "tod_today_density_stops.csv"

# The six older reforms (station-area study case ids) and their state FIPS.
REFORMS = [
    ("austin_2009", "Austin", "48"),
    ("bellevue_belred_2009", "Bellevue", "53"),
    ("slc_2010", "Salt Lake City", "49"),
    ("stpaul", "Saint Paul", "27"),  # the 2011 Saint Paul reform (case id "stpaul" in the stations table)
    ("seattle_nbh_othello_2012", "Seattle", "53"),
    ("seattle_mount_baker_2014", "Seattle", "53"),
]
REFORM_LABEL = {"stpaul": "stpaul_2011", "seattle_nbh_othello_2012": "seattle_othello_2012"}
# BelRed (Bellevue) was a light-industrial district rezoned for housing; its stops sat on industrial land, so it is kept
# in the files (flag industrial_rezone = 1) but left out of the five-place comparison (owner 2026-11-02).
INDUSTRIAL = {"bellevue_belred_2009"}
WI_PLACES = {  # Wisconsin rail/rapid stops grouped by operating agency
    "Milwaukee (BRT and streetcar)": ["Milwaukee County", "City of Milwaukee"],
    "Madison (BRT)": ["City of Madison"],
    "Kenosha (streetcar)": ["City of Kenosha"],
}


# ------------------------------------------------------------------------------------------------- fetch
def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_blocks(st: str) -> Path:
    """Census 2020 block file for a state in data/raw/census_tiger_2020_tabblock/, recorded in its manifest.json.
    An identical copy already downloaded by another thread (same file name, same size as the server's) is hard-linked
    instead of downloaded again; otherwise the file is downloaded from the Census TIGER/Line 2020 folder."""
    name = f"tl_2020_{st}_tabblock20.zip"
    dest = D / name
    mpath = D / "manifest.json"
    man = json.loads(mpath.read_text()) if mpath.exists() else {
        "source_id": "census_tiger_2020_tabblock", "license": "Public domain (U.S. government work)", "files": []}
    if dest.exists() and any(f["file"] == name for f in man["files"]):
        return dest
    url = URL.format(st=st)
    D.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        server_bytes = int(r.headers.get("Content-Length", -1))
        last_mod = r.headers.get("Last-Modified")
    entry = {"file": name, "url": url}
    copies = [p for p in sorted(RAW.glob(f"*/{name}")) if p.resolve() != dest.resolve()
              and p.resolve().stat().st_size == server_bytes]
    if not dest.exists() and copies:
        src = copies[0].resolve()
        try:
            os.link(src, dest)
        except OSError:
            shutil.copy2(src, dest)
        entry["copied_from"] = str(src.relative_to(RAW.parent.parent)) if src.is_relative_to(RAW.parent.parent) else str(src)
        entry["note"] = "local copy of the same Census file (size matches the server's Content-Length)"
        entry["accessed"] = dt.datetime.fromtimestamp(src.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")
    elif not dest.exists():
        tmp = dest.with_suffix(".part")
        with urllib.request.urlopen(url, timeout=600) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        tmp.rename(dest)
        entry["accessed"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    entry.update({"bytes": dest.stat().st_size, "sha256": _sha256(dest), "server_last_modified": last_mod,
                  "vintage": "Census 2020 tabulation blocks (TIGER/Line 2020); HOUSING20 = 2020 census housing units (PL 94-171)"})
    if entry["bytes"] != server_bytes:
        raise SystemExit(f"{name}: {entry['bytes']} bytes on disk, server says {server_bytes}")
    man["files"] = [f for f in man["files"] if f["file"] != name] + [entry]
    mpath.write_text(json.dumps(man, indent=2) + "\n")
    return dest


# ------------------------------------------------------------------------------------------------- measure
def read_blocks(st: str) -> pd.DataFrame:
    b = read_shapefile_attributes(fetch_blocks(st))[["GEOID20", "HOUSING20", "ALAND20", "INTPTLAT20", "INTPTLON20"]]
    return pd.DataFrame({"homes": b.HOUSING20.astype(float).values, "land_m2": b.ALAND20.astype(float).values,
                         "lon": b.INTPTLON20.astype(float).values, "lat": b.INTPTLAT20.astype(float).values})


def measure(blocks: pd.DataFrame, stops: pd.DataFrame, proj) -> tuple[dict, pd.DataFrame]:
    """Pooled totals per band (and the 1/2-1 mile ring), and each stop's own 1/2-mile and 1/4-mile totals."""
    lon0, lat0 = stops.lon.mean(), stops.lat.mean()
    # Pre-filter blocks to a box around the stops (5 km margin) before projecting.
    pad_lat, pad_lon = 0.05, 0.05 / max(np.cos(np.radians(lat0)), 0.1)
    box = ((blocks.lat > stops.lat.min() - pad_lat) & (blocks.lat < stops.lat.max() + pad_lat)
           & (blocks.lon > stops.lon.min() - pad_lon) & (blocks.lon < stops.lon.max() + pad_lon))
    b = blocks[box]
    bp = np.c_[G.transform(b.lon.values, b.lat.values, 4269, proj)]
    sp = np.c_[G.transform(stops.lon.values, stops.lat.values, 4326, proj)]
    homes, land = b.homes.values, b.land_m2.values / ACRE_M2
    pooled = {}
    for band, r in BANDS.items():
        m = T.blocks_within(bp, sp, r)
        pooled[band] = (homes[m].sum(), land[m].sum())
    m = T.blocks_within(bp, sp, RING_M[1]) & ~T.blocks_within(bp, sp, RING_M[0])
    pooled[RING] = (homes[m].sum(), land[m].sum())
    per = []
    for i in range(len(sp)):
        row = {}
        for band, r in BANDS.items():
            m = T.blocks_within(bp, sp[i:i + 1], r)
            h, a = homes[m].sum(), land[m].sum()
            row |= {f"homes_{band}": h, f"land_acres_{band}": a, f"homes_per_acre_{band}": h / a if a else np.nan}
        per.append(row)
    return pooled, pd.DataFrame(per, index=stops.index)


def local_tm(stops: pd.DataFrame):
    return G.Projection("tmerc", {"lat_0": 0.0, "lon_0": float(stops.lon.mean()), "k_0": 1.0, "x_0": 0.0, "y_0": 0.0},
                        name="local transverse Mercator")


def main() -> None:
    places = []  # (group, place, description, state, stops frame with stop/lat/lon)
    wi = pd.read_csv(REFERENCE / "tod_stops.csv")
    wi = wi[wi.flag_a_rapid == 1].assign(stop=lambda d: d.agency + " " + d.stop_id.astype(str))
    places.append(("wisconsin", "Wisconsin (all)", "rail and rapid stops (flag_a_rapid), all agencies", "55", wi))
    for p, ags in WI_PLACES.items():
        places.append(("wisconsin", p, "rail and rapid stops of " + " and ".join(ags), "55", wi[wi.agency.isin(ags)]))
    extra = set(wi.agency) - {a for v in WI_PLACES.values() for a in v}
    if extra:
        raise SystemExit(f"unassigned Wisconsin agencies: {extra}")

    st = pd.read_csv(REFERENCE / "tod_station_area_stations.csv")
    for case, city, fips in REFORMS:
        s = st[(st.case == case) & (st.role == "reform")]
        if s.empty:
            raise SystemExit(f"no reform stops for {case}")
        places.append(("reform_stops", REFORM_LABEL.get(case, case), f"{city}: reform-group rail stops", fips, s))
    for city in dict.fromkeys(c for _, c, _ in REFORMS):
        fips = next(f for _, c, f in REFORMS if c == city)
        s = st[(st.city == city) & st.case.isin([c for c, cc, _ in REFORMS if cc == city])]
        s = s.drop_duplicates(["stop", "lat", "lon"])
        places.append(("city_all_rail", city, f"{city}: all rail stops in the study (reform and comparison)", fips, s))

    blocks = {}
    rows, stop_rows = [], []
    for group, place, desc, fips, s in places:
        if fips not in blocks:
            print(f"reading blocks {fips}")
            blocks[fips] = read_blocks(fips)
        proj = 3071 if fips == "55" else local_tm(s)
        pooled, per = measure(blocks[fips], s, proj)
        for band in [*BANDS, RING]:
            h, a = pooled[band]
            rows.append({"group": group, "place": place, "stops": desc, "band": band, "n_stops": len(s),
                         "homes_2020": int(round(h)), "land_acres": round(a, 1),
                         "homes_per_acre": round(h / a, 2) if a else np.nan,
                         "typical_stop_homes_per_acre_half_mile": round(float(per["homes_per_acre_half_mile"].median()), 2)
                         if band == "half_mile" else np.nan})
        if (group, place) != ("wisconsin", "Wisconsin (all)"):
            for (_, r), (_, q) in zip(s.iterrows(), per.iterrows()):
                stop_rows.append({"group": group, "place": place, "stop": r["stop"], "lat": round(r.lat, 5),
                                  "lon": round(r.lon, 5),
                                  **{k: (round(v, 2) if "per_acre" in k else round(v, 1) if "land" in k else int(v))
                                     for k, v in q.items()}})
    # The reforms pooled: each city's reform stops once (Beacon Hill sits in both Seattle cases). Six = all; five = the
    # non-industrial ones (BelRed left out).
    for label, cases, desc in (
            ("six older reforms (pooled)", [c for c, _, _ in REFORMS], "reform-group rail stops of the six reforms, each stop once"),
            ("five older non-industrial reforms (pooled)", [c for c, _, _ in REFORMS if c not in INDUSTRIAL],
             "reform-group rail stops of the five non-industrial reforms (BelRed left out), each stop once")):
        sel = pd.concat([st[(st.case == c) & (st.role == "reform")].assign(state=f) for c, _, f in REFORMS if c in cases])
        sel = sel.drop_duplicates(["city", "stop", "lat", "lon"])
        tot = {b: [0.0, 0.0] for b in [*BANDS, RING]}
        meds = []
        for city, s in sel.groupby("city", sort=False):
            pooled, per = measure(blocks[s.state.iloc[0]], s, local_tm(s))
            for b in tot:
                tot[b][0] += pooled[b][0]
                tot[b][1] += pooled[b][1]
            meds.append(per["homes_per_acre_half_mile"])
        for b, (h, a) in tot.items():
            rows.append({"group": "reform_stops", "place": label, "band": b, "n_stops": len(sel), "stops": desc,
                         "homes_2020": int(round(h)), "land_acres": round(a, 1), "homes_per_acre": round(h / a, 2),
                         "typical_stop_homes_per_acre_half_mile": round(float(pd.concat(meds).median()), 2)
                         if b == "half_mile" else np.nan})
    out = pd.DataFrame(rows)
    ind_places = {REFORM_LABEL.get(c, c) for c in INDUSTRIAL} | {"six older reforms (pooled)", "Bellevue"}
    out.insert(2, "industrial_rezone", out.place.isin(ind_places).astype(int))
    out["source"] = "Census 2020 blocks (TIGER/Line tabblock20 HOUSING20, ALAND20); block counted if its internal point is within the band of any stop; ring_half_to_one_mile: beyond 1/2 mile of every stop and within 1 mile of any"
    out.to_csv(OUT, index=False)
    pd.DataFrame(stop_rows).to_csv(OUT_STOPS, index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(out.drop(columns=["source", "stops"]).to_string(index=False))
    print(f"wrote {OUT} ({len(out)} rows), {OUT_STOPS} ({len(stop_rows)} rows)")


if __name__ == "__main__":
    main()

"""Exploratory pilot: yearly new hard surface (USGS Annual NLCD) in Buffalo vs Rochester, New York.

Buffalo removed parking minimums citywide in its Green Code (in force 2017-01-03; it came with a full zoning rewrite).
Rochester, New York has no citywide parking reform in the Parking Reform Network data. This is a first look at
whether a satellite measure of hard surface is smooth enough to show a change. It is not a test: nothing here is
pre-registered, and nothing here changes the tool.

Data
- Annual NLCD Collection 1, Fractional Impervious Surface (FctImp: percent of each 30 m square that is hard surface,
  0-100; 250 = no data) and Impervious Descriptor (ImpDsc: 0 not developed, 1 road, 2 other hard surface such as
  roofs and lots). Read as small windows from the public, free Open Storage Network copy that the USGS Water Mission
  Area STAC catalog lists (no account, no fee). Only the city windows are read, never the 1 GB national files.
- City outlines: Census 2024 cartographic boundary places (cb_2024_us_place_500k), held fixed for every year.
- Homes permitted: Census Building Permits Survey annual place files (Northeast), 2005 onward.

Outputs (small, city totals only; no raster is stored in the repository)
- reference/nlcd_pilot_buffalo_rochester.csv: one row per city and year.
- data/raw/annual_nlcd_windows/: cached windows (.npy) and _downloads.json (URL, bytes read, SHA-256), git-ignored.

Run on a machine that can reach usgs.osn.mghpcc.org and www2.census.gov:
    uv run --all-extras python scripts/run_nlcd_paved_pilot.py --fetch
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import geom  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tiff_window import GeoTiff  # noqa: E402

COLLECTION = "c1v1"  # Collection 1.1 (1985-2024). Collection 1.2 (adds 2025) is not on the free OSN copy yet.
OSN = "https://usgs.osn.mghpcc.org/hytest/nlcd/annual-nlcd-cu-{c}/mosaic/Annual_NLCD_{p}_{y}_CU_{C}.tif"
YEARS = range(1985, 2025)
PLACES = {"3611000": "Buffalo", "3663000": "Rochester"}  # Census place GEOIDs, New York
PAD_M = 1000.0  # window padding around each city outline, metres
SQM_PER_ACRE = 4046.8564224
SQFT_PER_ACRE = 43560.0
WIN = RAW / "annual_nlcd_windows"
CB = RAW / "census_cb_2024"
CB_FILE = "cb_2024_us_place_500k.zip"
BPS = RAW / "census_bps_place_ne_long"  # separate from census_bps_place_us so the parking comparison is unchanged
BPS_YEARS = range(2005, 2026)
UA = {"User-Agent": "missing-middleware research (public data)"}
OUT = REFERENCE / "nlcd_pilot_buffalo_rochester.csv"


def url(product: str, year: int) -> str:
    return OSN.format(c=COLLECTION, p=product, y=year, C=COLLECTION.upper())


def _log(folder: Path, name: str, entry: dict) -> None:
    lp = folder / "_downloads.json"
    log = json.loads(lp.read_text()) if lp.exists() else {}
    log[name] = entry
    lp.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")


def _get(u: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=300).read()


def fetch_inputs() -> None:
    CB.mkdir(parents=True, exist_ok=True)
    if not (CB / CB_FILE).exists():
        u = f"https://www2.census.gov/geo/tiger/GENZ2024/shp/{CB_FILE}"
        data = _get(u)
        (CB / CB_FILE).write_bytes(data)
        _log(CB, CB_FILE, {"accessed": dt.date.today().isoformat(), "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest(), "url": u})
    BPS.mkdir(parents=True, exist_ok=True)
    for y in BPS_YEARS:
        f = BPS / f"ne{y}a.txt"
        if f.exists() and f.stat().st_size:
            continue
        u = f"https://www2.census.gov/econ/bps/Place/Northeast%20Region/{f.name}"
        data = _get(u)
        f.write_bytes(data)
        _log(BPS, f.name, {"accessed": dt.date.today().isoformat(), "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest(), "url": u})


def city_outlines() -> geom.Layer:
    lay = geom.read_shapefile(CB / CB_FILE, columns=["GEOID", "NAME"])
    lay = lay.subset(lay.attrs["GEOID"].isin(PLACES).to_numpy())
    if len(lay) != len(PLACES):
        raise SystemExit(f"FLAG: expected {len(PLACES)} city outlines, found {len(lay)}")
    # NLCD is Albers equal-area on WGS84 with the EPSG:5070 parameters; NAD83 vs WGS84 differ by about 1-2 m,
    # far below one 30 m square, so EPSG:5070 is used as is.
    return lay.to_crs(5070)


def window(product: str, year: int, key: str, bounds, fetch: bool) -> tuple[np.ndarray, tuple]:
    """Cached window of one product-year around one city: (array, (origin_x, origin_y, col0, row0))."""
    WIN.mkdir(parents=True, exist_ok=True)
    f = WIN / f"{key}_{product}_{year}_{COLLECTION}.npy"
    meta = WIN / f"{key}_{product}_{year}_{COLLECTION}.json"
    if f.exists() and meta.exists():
        m = json.loads(meta.read_text())
        return np.load(f), (m["origin_x"], m["origin_y"], m["col0"], m["row0"], m["pixel"])
    if not fetch:
        raise SystemExit(f"missing cached window {f.name}; run with --fetch")
    u = url(product, year)
    g = GeoTiff.open(u)
    if (g.pixel_w, g.pixel_h) != (30.0, 30.0):
        raise SystemExit(f"FLAG: {u} pixel size {g.pixel_w} x {g.pixel_h}, expected 30 m")
    c0, r0, nc, nr = g.window_for_bounds(*bounds)
    a = g.read_window(c0, r0, nc, nr, fill=250)
    g.close()
    np.save(f, a)
    m = {"origin_x": g.origin_x, "origin_y": g.origin_y, "col0": c0, "row0": r0, "pixel": g.pixel_w,
         "compression": g.compression, "predictor": g.predictor, "block": [g.block_w, g.block_h],
         "raster_size": [g.width, g.height], "nodata": g.nodata, "geokeys": list(g.geokeys)}
    meta.write_text(json.dumps(m, indent=1) + "\n")
    _log(WIN, f.name, {"accessed": dt.date.today().isoformat(), "url": u, "bytes_read": g._src.bytes_read,
                       "window_sha256": hashlib.sha256(a.tobytes()).hexdigest(), "shape": list(a.shape)})
    print(f"  {product} {year} {PLACES[key]}: {a.shape[1]} x {a.shape[0]} squares, {g._src.bytes_read:,} bytes read")
    return a, (m["origin_x"], m["origin_y"], c0, r0, m["pixel"])


def permits() -> pd.DataFrame:
    rows = []
    for y in BPS_YEARS:
        f = BPS / f"ne{y}a.txt"
        if not f.exists():
            continue
        d = parsers.read_bps(f, "place", state_fips="36")
        for key, name in PLACES.items():
            hit = d[(d["fips_place"] == key[2:]) & d["name"].str.contains(name, case=False, na=False)]
            if len(hit) != 1:
                print(f"FLAG: BPS {y} {name}: {len(hit)} rows")
                continue
            h = hit.iloc[0]
            rows.append({"geoid": key, "year": y, "homes_permitted": float(h["units_total"]),
                         "homes_permitted_5plus": float(h["5plus_units"]),
                         "months_reported": h["months_reported"]})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download what is missing (network)")
    args = ap.parse_args()
    if args.fetch:
        fetch_inputs()
    lay = city_outlines()
    rows = []
    for i, key in enumerate(lay.attrs["GEOID"]):
        feat = lay.polys[i]
        xs = np.concatenate([r[:, 0] for p in feat for r in p])
        ys = np.concatenate([r[:, 1] for p in feat for r in p])
        bounds = (xs.min() - PAD_M, ys.min() - PAD_M, xs.max() + PAD_M, ys.max() + PAD_M)
        inside = None
        for y in YEARS:
            fct, (ox, oy, c0, r0, px) = window("FctImp", y, key, bounds, args.fetch)
            dsc, geo2 = window("ImpDsc", y, key, bounds, args.fetch)
            if geo2[2:4] != (c0, r0) or dsc.shape != fct.shape:
                raise SystemExit(f"FLAG: FctImp and ImpDsc windows differ for {PLACES[key]} {y}")
            if inside is None:
                cx = ox + (c0 + np.arange(fct.shape[1]) + 0.5) * px
                cy = oy - (r0 + np.arange(fct.shape[0]) + 0.5) * px
                gx, gy = np.meshgrid(cx, cy)
                inside = geom.points_in_feature(gx.ravel(), gy.ravel(), feat).reshape(fct.shape)
                prev = None
            ok = inside & (fct != 250)
            share = fct.astype(float) / 100.0
            sq_acres = px * px / SQM_PER_ACRE
            rec = {"geoid": key, "city": PLACES[key], "year": y,
                   "squares_in_city": int(inside.sum()), "squares_no_data": int((inside & (fct == 250)).sum()),
                   "land_acres": round(float(ok.sum() * sq_acres), 1),
                   "hard_acres": float((share * ok).sum() * sq_acres),
                   "road_hard_acres": float((share * (ok & (dsc == 1))).sum() * sq_acres),
                   "other_hard_acres": float((share * (ok & (dsc == 2))).sum() * sq_acres)}
            if prev is not None:
                both = ok & (prev != 250)
                diff = (fct.astype(int) - prev.astype(int)) * both
                rec["gross_gain_acres"] = float(np.clip(diff, 0, None).sum() / 100.0 * sq_acres)
                rec["gross_loss_acres"] = float(-np.clip(diff, None, 0).sum() / 100.0 * sq_acres)
                rec["squares_gaining"] = int((diff > 0).sum())
            prev = fct
            rows.append(rec)
    d = pd.DataFrame(rows).sort_values(["city", "year"]).reset_index(drop=True)
    for c in ("hard_acres", "road_hard_acres", "other_hard_acres"):
        d["new_" + c.replace("_acres", "_acres_per_year")] = d.groupby("city")[c].diff()
    d["hard_acres_per_1000_land_acres"] = 1000 * d["hard_acres"] / d["land_acres"]
    p = permits()
    if len(p):
        d = d.merge(p, on=["geoid", "year"], how="left")
        d["homes_permitted_prev_year"] = d.groupby("city")["homes_permitted"].shift(1)
        for lag, col in (("same", "homes_permitted"), ("prev", "homes_permitted_prev_year")):
            d[f"new_other_hard_sqft_per_home_{lag}_year_permits"] = (
                d["new_other_hard_acres_per_year"] * SQFT_PER_ACRE / d[col].where(d[col] > 0))
    num = [c for c in d.columns if d[c].dtype.kind == "f"]
    d[num] = d[num].round(2)
    OUT.write_text(d.to_csv(index=False))
    print(f"wrote {OUT.name} ({len(d)} rows)")
    # sanity flags
    for city, g in d.groupby("city"):
        nd = g["squares_no_data"].max()
        if nd:
            print(f"FLAG: {city}: up to {nd} squares with no data inside the city")
        if g["squares_in_city"].nunique() != 1:
            print(f"FLAG: {city}: square count changes across years")
        neg = (g["new_hard_acres_per_year"] < 0).sum()
        print(f"{city}: {int(g['squares_in_city'].iloc[0]):,} squares; hard surface "
              f"{g['hard_acres'].iloc[0]:,.0f} acres in {g['year'].iloc[0]} -> {g['hard_acres'].iloc[-1]:,.0f} acres "
              f"in {g['year'].iloc[-1]}; years with a net fall: {neg}")


if __name__ == "__main__":
    main()

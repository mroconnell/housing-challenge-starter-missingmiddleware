"""Lot land counted once: adds `acres_land` to every station-area lot table (owner OK 2026-11-02 18:04).

Why: in some county parcel files (Charlotte, Los Angeles, San Diego, Saint Paul, Denver, Chicago, ...) each stacked
condo-unit record carries the whole parcel's land area, so summing `acres` counts that land once per unit (found by
scripts/build_tod_stop_table.py: lot acres within 1/4 mile vs once-counted, Charlotte 2.25x reform / 2.94x comparison,
LA TOC 3.66x / 3.09x).

Rule (the same test build_tod_stop_table.py uses to find stacked records): records of one lot table (and, in
wi_lots_station.parquet, one case) with the same lot point (x and y in EPSG:5070 metres, rounded to 1 m) and the same
recorded acres (rounded to 0.0001) are one parcel. The parcel's land is split equally across its records:

    acres_land = acres / (number of records sharing that point and acres)

so sums over any set that holds the whole parcel count its land once, and each record keeps a sensible lot size (its
share of the parcel). Records with no acres keep acres_land empty; a record alone keeps acres_land = acres. `acres` is
kept as recorded. Rows, row order and the row index (lot_index in the events files and hand_check_big_lots.csv) are
unchanged, so the hand-check rows stay valid.

Missing acres filled (owner OK 2026-11-02): San Diego (san_diego_2021). The county `acreage` field is blank for most
small lots and every condo unit (96% of the records within 1/4 mile). Where it is blank, the parcel's polygon area
from the same SANDAG layer is used (data/raw/tod_radius_programs/san_diego/parcel_area.csv, SHAPE__Area in square
feet, EPSG:2230, / 43,560; fetched by scripts/fetch_tod_radius_programs.py sd_parcel_area; joined on objectid and
kept only where the APN matches). Where both exist the polygon area matches `acreage` closely (median ratio 1.001,
10th-90th percentile 0.94-1.07). Condo units and possessory-interest records carry the whole lot's polygon at the
lot's point, so for this case the stack key is the point and the polygon area (see land_once): a stack's land is its
recorded acreage where any of its records has one, else the polygon area, split equally across its records.
Column acres_land_source says where each record's land came from: "recorded",
"polygon" (SANDAG area), "census_fill_city_share" (fallback below) or "" (none).

Fallback for any table (owner 2026-11-02 19:55): lots still without land after the exact sources get land from
2020 census blocks at the SAME city's lot-to-block share (census_fill; acres_land_source "census_fill_city_share"):
each lot is placed in its census block (point in polygon); a block counts only for its land within 1 mile of the
city's stops (sampled for blocks over 10 acres); a block is complete when every lot point in it has land; per band
(a block's band = its lots' most common band) share = lot land / block land over the complete blocks; in each
incomplete block the missing land = block land x share - the land its lots already have, split equally over its lots
without land (none where the known land already reaches that). The per-city shares, complete-block counts and land
filled are written to reference/tod_station_acres_census_fill.csv. Lots recorded with 0 acres are left as they are
(0 is a value, not a gap). Chicago is the main user: its acres come only from the Assessor's residential, condo and
commercial-valuation land square feet, so 28% of the lots within 1/4 mile (exempt 14,017, vacant 5,545, commercial
and industrial about 8,000, railroad 714; 0.3% of the existing homes, none of the new homes) had none; the Cook
parcel shapes were not fetched (licence only "See Terms of Use"). Known lean: blocks whose lots already exceed the
target are not cut, so filled cities end slightly above their share overall.

Idempotent: acres_land is recomputed from x, y and acres each time and replaces any earlier column.

    .venv/bin/python scripts/fix_tod_station_acres.py            # every lots_*.parquet (incl. candidates/) + wi_lots_station
    .venv/bin/python scripts/fix_tod_station_acres.py --check    # report only, write nothing

The builders (build_tod_station_lot_table.py, build_tod_station_wisconsin.py) call add_acres_land before writing, so a
rebuilt table carries the column too.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))
REFERENCE = ROOT / "reference"
LOTDIR = ROOT / "data" / "processed" / "tod_station_area"


def stack_size(x, y, acres, case=None) -> np.ndarray:
    """Number of records sharing each record's lot point (1 m) and recorded acres (0.0001); 1 where acres is missing."""
    acres = pd.to_numeric(pd.Series(np.asarray(acres)), errors="coerce")
    k = pd.DataFrame({"x": np.round(np.asarray(x, dtype=float), 0), "y": np.round(np.asarray(y, dtype=float), 0),
                      "a": acres.round(4).values})
    if case is not None:
        k["c"] = np.asarray(case)
    n = k.groupby(list(k.columns), dropna=False, sort=False).x.transform("size").values.astype(float)
    return np.where(acres.notna().values, n, 1.0)


SD_RAW = ROOT / "data" / "raw" / "tod_radius_programs" / "san_diego"


def sd_polygon_acres(index) -> np.ndarray:
    """Polygon acres for San Diego lot-table rows (row index = row of county_parcels.csv); NaN where the APN differs."""
    a = pd.read_csv(SD_RAW / "parcel_area.csv", dtype={"apn": str}, usecols=["objectid", "apn", "SHAPE__Area"])
    d = pd.read_csv(SD_RAW / "county_parcels.csv", dtype={"apn": str}, usecols=["objectid", "apn"])
    m = d.merge(a, on="objectid", how="left", suffixes=("", "_a"))
    ac = (m.SHAPE__Area / 43560.0).where(m.apn == m.apn_a)
    return ac.reindex(np.asarray(index)).values


FILLS = {"san_diego_2021": sd_polygon_acres}


def land_once(x, y, acres, case_col=None, case: str | None = None, index=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per record: land counted once (acres_land), its source label, and the stack size.

    Default: stack = same point and same recorded acres; land = recorded acres / stack size.
    Cases with a polygon fill (FILLS): the stack key uses the polygon area (every record has one), so records sharing
    one polygon at one point are one parcel even when only some of them carry `acreage` (e.g. a possessory-interest
    or condo-unit record beside the land record); the stack's land = its recorded acreage where any record has one
    (largest), else the polygon area; split equally."""
    acres = pd.to_numeric(pd.Series(np.asarray(acres)), errors="coerce").values.astype(float)
    if case not in FILLS:
        n = stack_size(x, y, acres, case_col)
        return acres / n, np.where(np.isfinite(acres), "recorded", ""), n
    poly = FILLS[case](index)
    key = np.where(np.isfinite(poly) & (poly > 0), poly, acres)
    n = stack_size(x, y, key, case_col)
    k = pd.DataFrame({"x": np.round(np.asarray(x, float), 0), "y": np.round(np.asarray(y, float), 0),
                      "a": pd.Series(key).round(4).values, "r": acres})
    rec = k.groupby(["x", "y", "a"], dropna=False, sort=False).r.transform("max").values
    land = np.where(np.isfinite(rec), rec, key)
    src = np.where(np.isfinite(rec), "recorded", np.where(np.isfinite(key), "polygon", ""))
    n = np.where(np.isfinite(key), n, 1.0)
    return land / n, src, n


# ------------------------------------------------------------------ fallback: census block land, same city's share
BLK = ROOT / "data" / "raw" / "census_tiger_2020_tabblock"
BLK_CACHE = LOTDIR / "_blocks_cache"
ACRE_M2 = 4046.8564224
STATE = {"nyc": "36", "phl": "42", "la": "06", "san": "06", "honolulu": "15", "chicago": "17", "denver": "08",
         "portland": "41", "austin": "48", "slc": "49", "seattle": "53", "bellevue": "53", "stpaul": "27",
         "charlotte": "37", "wi": "55"}
FEW_BLOCKS = 30          # a band's share resting on fewer complete blocks than this is flagged
CENSUS_SRC = "census_fill_city_share"


def lot_blocks(x, y, state: str, S: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """2020 census block of each lot point (point in polygon, EPSG:5070): (GEOID20 or "", block land acres, share of
    the block within 1 mile of the stops S). The share: blocks of 10 acres or less count whole if their internal point is
    within 1 mile, else not at all; larger blocks are sampled on a grid (about 1,600 points) and the share is that of the
    points inside the block that lie within 1 mile of a stop. Cached by a hash of the points and stops
    (data/processed/tod_station_area/_blocks_cache/)."""
    import hashlib
    from scipy.spatial import cKDTree
    from missing_middleware import geom as GM
    from missing_middleware import geom_extra_station as X
    x, y = np.asarray(x, float), np.asarray(y, float)
    h = hashlib.sha1(np.round(np.c_[x, y], 1).tobytes() + np.round(S, 1).tobytes()).hexdigest()[:16]
    f = BLK_CACHE / f"lotblock_{state}_{h}.parquet"
    if f.exists():
        c = pd.read_parquet(f)
        return c["geoid"].values, c["land_acres"].values, c["cov"].values
    ok = np.isfinite(x) & np.isfinite(y)
    pad = 2000.0
    bb = (x[ok].min() - pad, y[ok].min() - pad, x[ok].max() + pad, y[ok].max() + pad)
    B = X.read_vector(BLK / f"tl_2020_{state}_tabblock20.zip", dst=5070, columns=["GEOID20", "ALAND20", "INTPTLAT20", "INTPTLON20"], bbox=bb)
    k = np.full(len(x), -1, dtype=np.int64)
    k[ok] = X.first_within(x[ok], y[ok], list(B.geometry))
    used = np.unique(k[k >= 0])
    tree = cKDTree(S)
    bix, biy = X.transform(B.INTPTLON20.astype(float).values[used], B.INTPTLAT20.astype(float).values[used], 4326, 5070)
    bl = B.ALAND20.astype(float).values[used] / ACRE_M2
    cov = (tree.query(np.c_[bix, biy])[0] <= 1609.0).astype(float)
    for n, b in enumerate(used):
        if bl[n] <= 10:
            continue
        feat = B.geometry.iloc[b]
        fb = X.feature_bounds([feat])[0]
        step = max(10.0, np.sqrt((fb[2] - fb[0]) * (fb[3] - fb[1]) / 1600.0))
        gx, gy = np.meshgrid(np.arange(fb[0] + step / 2, fb[2], step), np.arange(fb[1] + step / 2, fb[3], step))
        gx, gy = gx.ravel(), gy.ravel()
        inn = GM.points_in_feature(gx, gy, feat)
        if inn.sum() >= 20:
            cov[n] = float((tree.query(np.c_[gx[inn], gy[inn]])[0] <= 1609.0).mean())
    pos = pd.Series(np.arange(len(used)), index=used)
    kk = np.where(k >= 0, pos.reindex(np.maximum(k, 0)).fillna(-1).astype(int).values, -1)
    geoid = np.where(kk >= 0, B.GEOID20.astype(str).values[np.maximum(k, 0)], "")
    land = np.where(kk >= 0, bl[np.maximum(kk, 0)], np.nan)
    cv = np.where(kk >= 0, cov[np.maximum(kk, 0)], np.nan)
    BLK_CACHE.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"geoid": geoid, "land_acres": land, "cov": cv}).to_parquet(f)
    return geoid, land, cv


_STOPS: dict = {}


def stops_xy(cases) -> np.ndarray:
    """The cases' stops (reference/tod_stop_table.csv; Wisconsin: wi_milwaukee / wi_madison), EPSG:5070."""
    from missing_middleware import geom_extra_station as X
    if "T" not in _STOPS:
        _STOPS["T"] = pd.read_csv(REFERENCE / "tod_stop_table.csv", usecols=["case", "lat", "lon"], low_memory=False).dropna()
    T = _STOPS["T"]
    s = T[T["case"].isin(list(cases))]
    x, y = X.transform(s.lon.values.astype(float), s.lat.values.astype(float), 4326, 5070)
    return np.c_[x, y]


def census_fill(land, src, x, y, band, state: str, case_col=None, city_name: str = "") -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Fallback for lots still without land. Within one city (one lot table; in wi_lots_station one case) and band:
    share = lot land / block land over the city's COMPLETE blocks (blocks whose every lot point has land; a block's
    band = the band most of its lots are in). In each incomplete block: missing land = block land x share - the land
    its lots already have, split equally over its lots without land (0 where the known land already reaches the
    target). Block land counts only the part within 1 mile of the city's stops (lot_blocks), since the lot table stops
    at 1 mile; blocks with none of their land within 1 mile are not used. Lots outside every block, or in such a block,
    stay empty. Returns (land, src, report rows)."""
    land, src = land.astype(float).copy(), src.astype(object).copy()
    miss = ~np.isfinite(land)
    rows = []
    if not miss.any():
        return land, src.astype(str), pd.DataFrame(rows)
    city = np.asarray(case_col).astype(str) if case_col is not None else np.full(len(land), city_name)
    S = stops_xy(set(city))
    geoid, bl, cov = lot_blocks(x, y, state, S)
    for c in np.unique(city[miss]):
        m = (city == c) & (geoid != "") & (cov > 0)
        out_lots = int(((city == c) & miss & ~m).sum())
        D = pd.DataFrame({"g": geoid[m], "bl": bl[m] * cov[m], "band": np.asarray(band)[m], "land": land[m],
                          "miss": miss[m]}, index=np.flatnonzero(m))
        G = D.groupby("g").agg(bl=("bl", "first"), known=("land", "sum"), nmiss=("miss", "sum"),
                               band=("band", lambda b: b.value_counts().index[0]))
        comp = G[G.nmiss == 0]
        share = comp.groupby("band").known.sum() / comp.groupby("band").bl.sum()
        ncomp = comp.groupby("band").size()
        inc = G[G.nmiss > 0].copy()
        inc["target"] = inc.bl * inc.band.map(share) - inc.known
        inc["each"] = inc.target.clip(lower=0) / inc.nmiss
        lm = D[D.miss]
        fill = lm.g.map(inc.each).values
        ix = lm.index.values[np.isfinite(fill)]
        land[ix] = fill[np.isfinite(fill)]
        src[ix] = CENSUS_SRC
        for b in sorted(set(inc.band) | set(share.index)):
            ib = inc[inc.band == b]
            fb = lm.g.isin(ib.index)
            rows.append({"city": c, "band": b, "share": round(float(share.get(b, np.nan)), 3),
                         "complete_blocks": int(ncomp.get(b, 0)), "few_blocks": bool(ncomp.get(b, 0) < FEW_BLOCKS),
                         "incomplete_blocks": len(ib), "lots_filled": int(fb.sum()),
                         "acres_filled": round(float(ib.target.clip(lower=0).sum()), 1),
                         "known_lot_acres_band": round(float(D.land[D.band == b].sum()), 1),
                         "blocks_target_below_known": int((ib.target < 0).sum()),
                         "lots_left_empty_city": out_lots})
    return land, src.astype(str), pd.DataFrame(rows)


def state_of(name: str) -> str | None:
    k = name.removeprefix("lots_").split("_")[0]
    return STATE.get(k)


def add_acres_land(D: pd.DataFrame, case: str | None = None) -> pd.DataFrame:
    """Returns D with acres_land and acres_land_source (see module rule). Uses the `case` column as part of the key when
    present; `case` names a lot-table case with a fill (FILLS)."""
    cc = D["case"].values if "case" in D else None
    land, src, _ = land_once(D.x.values, D.y.values, D.acres.values, cc, case, D.index.values)
    st = state_of(case or (str(cc[0]) if cc is not None and len(cc) else ""))
    if st and "band" in D:
        land, src, _ = census_fill(land, src, D.x.values, D.y.values, D.band.values, st, cc, case or "")
    D = D.copy()
    D["acres_land"] = land
    D["acres_land_source"] = src
    return D


def files() -> list[Path]:
    out = sorted(LOTDIR.glob("lots_*.parquet")) + sorted((LOTDIR / "candidates").glob("lots_*.parquet"))
    w = LOTDIR / "wi_lots_station.parquet"
    return out + ([w] if w.exists() else [])


def fix_file(f: Path, write: bool = True) -> dict:
    import pyarrow as pa
    import pyarrow.parquet as pq
    t = pq.read_table(f)
    names = t.schema.names
    case = t.column("case").to_numpy(zero_copy_only=False) if "case" in names else None
    acres = t.column("acres").to_numpy(zero_copy_only=False).astype(float)
    idx = t.column("__index_level_0__").to_numpy(zero_copy_only=False) if "__index_level_0__" in names else np.arange(len(acres))
    land, src, n = land_once(t.column("x").to_numpy(zero_copy_only=False), t.column("y").to_numpy(zero_copy_only=False),
                             acres, case, f.stem.removeprefix("lots_"), idx)
    a = land * n
    st = state_of(f.stem) if f.stem != "wi_lots_station" else "55"
    rep = pd.DataFrame()
    if st and "band" in names:
        land, src, rep = census_fill(land, src, t.column("x").to_numpy(zero_copy_only=False),
                                     t.column("y").to_numpy(zero_copy_only=False),
                                     t.column("band").to_numpy(zero_copy_only=False), st, case, f.stem.removeprefix("lots_"))
        if len(rep):
            rep.insert(0, "file", f.name)
    old = t.column("acres_land").to_numpy(zero_copy_only=False).astype(float) if "acres_land" in names else None
    old_src = t.column("acres_land_source").to_numpy(zero_copy_only=False) if "acres_land_source" in names else None
    same = (old is not None and np.allclose(old, land, equal_nan=True, rtol=0, atol=1e-12)
            and old_src is not None and (old_src == src).all())
    if "acres_land_src" in names:          # earlier name of acres_land_source
        t = t.drop_columns(["acres_land_src"])
        names = t.schema.names
        same = False
    if write and not same:
        for name, col in (("acres_land", pa.array(land, type=pa.float64())), ("acres_land_source", pa.array(src, type=pa.string()))):
            names = t.schema.names
            t = t.set_column(names.index(name), name, col) if name in names else \
                t.add_column(names.index("acres_land") + 1 if name == "acres_land_source" else names.index("acres") + 1, name, col)
        tmp = f.with_suffix(".parquet.tmp")
        pq.write_table(t, tmp)
        os.replace(tmp, f)          # atomic: a reader holding the old file keeps reading it
    band = t.column("band").to_numpy(zero_copy_only=False) if "band" in names else None
    q = band == "0-1/4" if band is not None else np.ones(len(acres), bool)
    return {"file": str(f.relative_to(LOTDIR)), "rows": len(acres), "stacked_records": int((n > 1).sum()),
            "filled_records": int((src == "polygon").sum()), "census_filled": int((src == CENSUS_SRC).sum()),
            "no_land_q1": round(float(np.mean(~np.isfinite(a[q]))), 3),
            "still_no_land": int((~np.isfinite(land)).sum()), "_rep": rep,
            "acres_q1": round(float(np.nansum(acres[q])), 1), "acres_land_q1": round(float(np.nansum(land[q])), 1),
            "ratio_q1": round(float(np.nansum(acres[q]) / np.nansum(land[q])), 3) if np.nansum(land[q]) > 0 else np.nan,
            "status": "unchanged" if same else ("written" if write else "would write")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only")
    a = ap.parse_args()
    rows = []
    for f in files():
        r = fix_file(f, write=not a.check)
        rows.append(r)
        print({k: v for k, v in r.items() if k != "_rep"}, flush=True)
    reps = [r.pop("_rep") for r in rows]
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(R[(R.stacked_records > 0) | (R.census_filled > 0)].to_string(index=False))
    reps = [r for r in reps if len(r)]
    if reps:
        F = pd.concat(reps, ignore_index=True)
        print("\ncensus fill (same city's share of block land on complete blocks):\n" + F.to_string(index=False))
        if not a.check:
            F.to_csv(REFERENCE / "tod_station_acres_census_fill.csv", index=False)


if __name__ == "__main__":
    main()

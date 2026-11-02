"""Independent check of lot land (acres_land, scripts/fix_tod_station_acres.py) against Census 2020 block land.

For each station-area case (and Wisconsin's Milwaukee and Madison table): every 2020 census block whose internal point
lies within 1 mile of the case's stops is given to its nearest stop (the same nearest-stop rule the lot tables use), so
it takes that stop's group (reform / comparison / wisconsin) and a band by distance (0-1/4, 1/4-1/2, 1/2-1 mile, as
scripts/build_tod_today_density.py counts blocks by internal point). Block land = sum of ALAND20 (land only, no water).
Lot land = sum of acres_land of the case's lots in that group and band. Ratio = lot land / block land.

Parcel land leaves out streets, rail and other right of way, so lot land should sit modestly below block land (about
0.7-0.9 in a street grid). Outside 0.7-1.3 is flagged. A second ratio uses only blocks with a lot point within 100 m of
the block's internal point ("blocks the lot table covers"), which takes out land beyond the parcel file's reach (lot
tables built from a city's or county's file stop at its edge; block land does not).

    .venv/bin/python scripts/check_tod_station_acres_blocks.py   -> reference/tod_station_acres_block_check.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.dbf import read_shapefile_attributes  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

LOTDIR = ROOT / "data" / "processed" / "tod_station_area"
BLK = RAW / "census_tiger_2020_tabblock"
CACHE = LOTDIR / "_blocks_cache"
CRS = 5070
ACRE_M2 = 4046.8564224
EDGES = [402.0, 805.0, 1609.0]
BANDS = ["0-1/4", "1/4-1/2", "1/2-1"]
STATE = {"nyc": "36", "phl": "42", "la": "06", "san": "06", "honolulu": "15", "chicago": "17", "denver": "08",
         "portland": "41", "austin": "48", "slc": "49", "seattle": "53", "bellevue": "53", "stpaul": "27",
         "charlotte": "37", "wi": "55"}


def blocks(st: str) -> pd.DataFrame:
    f = CACHE / f"blocks_{st}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    b = read_shapefile_attributes(BLK / f"tl_2020_{st}_tabblock20.zip")[["ALAND20", "INTPTLAT20", "INTPTLON20"]]
    x, y = X.transform(b.INTPTLON20.astype(float).values, b.INTPTLAT20.astype(float).values, 4326, CRS)
    out = pd.DataFrame({"land_m2": b.ALAND20.astype(float).values, "x": x, "y": y})
    CACHE.mkdir(parents=True, exist_ok=True)
    out.to_parquet(f)
    return out


def check(case: str, lot_file: Path, S: pd.DataFrame, B: pd.DataFrame) -> list[dict]:
    sx, sy = X.transform(S.lon.values.astype(float), S.lat.values.astype(float), 4326, CRS)
    tree = cKDTree(np.c_[sx, sy])
    box = (B.x > sx.min() - 2000) & (B.x < sx.max() + 2000) & (B.y > sy.min() - 2000) & (B.y < sy.max() + 2000)
    b = B[box]
    d, i = tree.query(np.c_[b.x.values, b.y.values])
    keep = d <= EDGES[-1]
    b, d, i = b[keep], d[keep], i[keep]
    bband = np.array(BANDS)[np.digitize(d, EDGES[:-1])]
    bgroup = S.role.values[i]
    cols = ["group", "band", "acres", "acres_land", "x", "y"] + (["case"] if case.startswith("wi") else [])
    L = pd.read_parquet(lot_file, columns=cols)
    if case.startswith("wi"):
        L = L[L["case"].isin(["wi_milwaukee", "wi_madison"])]
        L["group"] = "wisconsin"
    lt = cKDTree(np.c_[L.x.values, L.y.values])
    dl, _ = lt.query(np.c_[b.x.values, b.y.values], distance_upper_bound=100.0)
    covered = np.isfinite(dl)
    rows = []
    for g in sorted(set(bgroup)):
        for band in BANDS:
            mb = (bgroup == g) & (bband == band)
            ml = (L.group == g) & (L.band == band)
            blk = b.land_m2.values[mb].sum() / ACRE_M2
            blk_cov = b.land_m2.values[mb & covered].sum() / ACRE_M2
            lot, lot_rec = float(L.acres_land[ml].sum()), float(L.acres[ml].sum())
            rows.append({"case": case, "group": g, "band": band, "stops": int((S.role == g).sum()), "blocks": int(mb.sum()),
                         "block_land_acres": round(blk, 1), "block_land_acres_covered": round(blk_cov, 1),
                         "lot_acres_recorded": round(lot_rec, 1), "lot_acres_land": round(lot, 1),
                         "ratio_recorded": round(lot_rec / blk, 3) if blk > 0 else np.nan,
                         "ratio_land": round(lot / blk, 3) if blk > 0 else np.nan,
                         "ratio_land_covered": round(lot / blk_cov, 3) if blk_cov > 0 else np.nan})
    return rows


def main() -> None:
    T = pd.read_csv(REFERENCE / "tod_stop_table.csv", low_memory=False, usecols=["case", "role", "stop_id", "lat", "lon", "in_lot_table"])
    cases = {p.stem[5:]: p for p in sorted(LOTDIR.glob("lots_*.parquet"))}
    cases["seattle_roosevelt_2012"] = LOTDIR / "candidates" / "lots_seattle_roosevelt_2012.parquet"
    cases["wi"] = LOTDIR / "wi_lots_station.parquet"
    by_state: dict[str, list[str]] = {}
    for c in cases:
        by_state.setdefault(STATE[c.split("_")[0]], []).append(c)
    rows = []
    for st, cs in by_state.items():
        B = blocks(st)
        for c in cs:
            S = T[T["case"].isin(["wi_milwaukee", "wi_madison"])] if c == "wi" else T[T["case"] == c]
            S = S.dropna(subset=["lat", "lon"])
            r = check(c, cases[c], S, B)
            rows += r
            q = [x for x in r if x["band"] == "0-1/4"]
            print(c, "; ".join(f"{x['group']} {x['ratio_recorded']}->{x['ratio_land']} (covered {x['ratio_land_covered']})" for x in q), flush=True)
        del B
    R = pd.DataFrame(rows)
    R["flag"] = np.where(R.ratio_land.between(0.7, 1.3), "", "outside 0.7-1.3")
    R.to_csv(REFERENCE / "tod_station_acres_block_check.csv", index=False)
    print(R[~R["case"].str.startswith(("nyc_", "phl_"))].to_string(index=False))


if __name__ == "__main__":
    main()

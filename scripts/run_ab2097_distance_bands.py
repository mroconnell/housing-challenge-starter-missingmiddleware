"""AB 2097 distance bands (parking round 3, docs/parking/ROUND3_PLAN.md, "Distance from transit, per permit").

Group P jurisdictions (parking alone near transit, docs/tod/AB2097_TEST_PREREG.md), land outside Los Angeles's TOC areas.
For each band 0-1/4, 1/4-1/2 and 1/2-3/4 mile from a major transit stop: permits (all units, from HCD Table A2) per
1,000 existing homes (2020 census blocks) per year, 2023-2025 against 2018-2022, compared with the 1-1 1/2 mile ring
(difference-in-differences). 90% intervals from resampling whole jurisdictions (2,000 draws, seed 20261027). The slope
is the least-squares slope of the three band estimates on band midpoints (miles), with its interval from the same draws.

Reuses the cached permits from scripts/run_ab2097_test.py and recomputes block distances to stops.
Output: reference/tod_ab2097_distance_bands.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import run_ab2097_test as run  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

MILE = ab.MILE_M
BANDS = [("0-1/4 mile", 0.0, 0.25), ("1/4-1/2 mile", 0.25, 0.5), ("1/2-3/4 mile", 0.5, 0.75)]
RING = ("ring 1-1 1/2 mile", 1.0, 1.5)
DRAWS, SEED = 2000, 20261027


def band_of(d_m: np.ndarray) -> np.ndarray:
    d = np.asarray(d_m, float) / MILE
    out = np.full(len(d), "", dtype=object)
    for name, lo, hi in BANDS + [RING]:
        out[(d >= lo) & (d < hi)] = name
    return out


def block_homes() -> pd.DataFrame:
    cache = run.OUT / "blocks_bands.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import geopandas as gpd
    import pyogrio
    stops = run.load_stops("all")
    b = pyogrio.read_dataframe(run.D / "tl_2020_06_tabblock20.zip", read_geometry=False,
                               columns=["GEOID20", "COUNTYFP20", "HOUSING20", "INTPTLAT20", "INTPTLON20"])
    b = gpd.GeoDataFrame(b, geometry=gpd.points_from_xy(b.INTPTLON20.astype(float), b.INTPTLAT20.astype(float)), crs=4326).to_crs(run.CRS)
    b["juris"] = run.block_juris(b)
    b["dist"] = run.nearest_m(b, stops)
    b["upz"] = run.in_toc(b) & (b["juris"] == ab.LA)
    b["homes"] = b["HOUSING20"].astype(float)
    b["band"] = band_of(b["dist"])
    out = b.dropna(subset=["juris"]).groupby(["juris", "upz", "band"])["homes"].sum().reset_index()
    out.to_parquet(cache)
    return out


def main() -> None:
    cells, permits, _ = run.build()
    c, p = run.spec_tables(cells, permits, "zone")
    juris = ab.define_groups(c, ab.full_reporters(p))["P"].juris
    bh = block_homes()
    bh = bh[bh.juris.isin(juris) & ~bh.upz & (bh.band != "")]
    pp = permits[permits.juris.isin(juris) & ~permits.upz].copy()
    pp["band"] = band_of(pp["dist"])
    pp = pp[pp.band != ""]
    names = [b[0] for b in BANDS] + [RING[0]]
    J = sorted(juris)
    ix = {j: i for i, j in enumerate(J)}
    H = np.zeros((len(J), len(names)))
    for r in bh.itertuples():
        H[ix[r.juris], names.index(r.band)] += r.homes
    U = np.zeros((2, len(J), len(names)))  # period x juris x band
    for (j, y, bnd), v in pp.groupby(["juris", "year", "band"])["all_units"].sum().items():
        if y in ab.BEFORE:
            U[0, ix[j], names.index(bnd)] += v
        elif y in ab.AFTER:
            U[1, ix[j], names.index(bnd)] += v
    mids = np.array([(lo + hi) / 2 for _, lo, hi in BANDS])

    def stats(w: np.ndarray) -> tuple[np.ndarray, float]:
        h = (H * w[:, None]).sum(0)
        rb = 1000 * (U[0] * w[:, None]).sum(0) / h / len(ab.BEFORE)
        ra = 1000 * (U[1] * w[:, None]).sum(0) / h / len(ab.AFTER)
        ch = ra - rb
        did = ch[:3] - ch[3]
        slope = float(np.polyfit(mids, did, 1)[0])
        return did, slope, rb, ra

    did, slope, rb, ra = stats(np.ones(len(J)))
    rng = np.random.default_rng(SEED)
    D, S = [], []
    for _ in range(DRAWS):
        w = np.bincount(rng.integers(0, len(J), len(J)), minlength=len(J)).astype(float)
        d, s, _, _ = stats(w)
        D.append(d); S.append(s)
    D, S = np.array(D), np.array(S)
    rows = []
    for k, (name, lo, hi) in enumerate(BANDS):
        rows.append({"band": name, "miles_from": lo, "miles_to": hi, "homes_2020": round(H[:, k].sum(), 1),
                     "rate_before": round(rb[k], 4), "rate_after": round(ra[k], 4),
                     "ring_rate_before": round(rb[3], 4), "ring_rate_after": round(ra[3], 4),
                     "did_per_1000_homes_per_year": round(did[k], 4),
                     "interval90_low": round(float(np.percentile(D[:, k], 5)), 4),
                     "interval90_high": round(float(np.percentile(D[:, k], 95)), 4)})
    rows.append({"band": "slope across bands (per mile)", "did_per_1000_homes_per_year": round(slope, 4),
                 "interval90_low": round(float(np.percentile(S, 5)), 4), "interval90_high": round(float(np.percentile(S, 95)), 4),
                 "homes_2020": round(H[:, 3].sum(), 1)})
    df = pd.DataFrame(rows)
    df["jurisdictions"] = len(J)
    df["units"] = "permits (all units, HCD Table A2) per 1,000 existing homes (2020 census) per year; 2023-2025 vs 2018-2022; vs the 1-1 1/2 mile ring"
    df["interval"] = f"jurisdiction resampling, {DRAWS} draws, seed {SEED}"
    out = ROOT / "reference" / "tod_ab2097_distance_bands.csv"
    df.to_csv(out, index=False)
    print(df[["band", "homes_2020", "did_per_1000_homes_per_year", "interval90_low", "interval90_high"]].to_string(index=False))


if __name__ == "__main__":
    main()

"""Station-area model, step D stage 1: one fast lot model (docs/tod/STATION_AREA_PLAN.md, LOCKED; three-stage trait plan).

Rows: lots of every case (comparison lots sampled with weights so New York does not swamp the rest). Target: new
homes per year on the lot in the after window. Features: the lot's own before-window rate, lot and block traits,
the band and exact distance, whether its nearest stop is a reform stop, whether the lot is in the reform area, the
coverage of its stop's band, and the joined neighborhood traits (EPA block group, LODES job growth, historic register,
the 78 tract variables). The reform effect for a city is the model's prediction with the reform as it was minus the
prediction with the reform switched off (reform stop -> comparison, in_reform_area -> False, coverage -> 0), summed
over the city's reform lots and expressed per 100 lot acres a year by band.

Test (city is the unit): hide one city, fit on the rest, predict its effect per band, and compare with its measured
effect (stage 0, run_tod_station_model.py). Benchmarks: zero, and the other cities' average measured effect.

    uv run --all-extras python scripts/run_tod_station_lotmodel.py [--trait-groups lot,place,tract]
        [--sampling full --seed N]

Sampling (owner 2026-11-02, "near-all lots"): `capped` (default; the original run) keeps at most 60,000 comparison and
60,000 reform lots per case (New York and Philadelphia rezonings: 4,000 and 8,000) drawn at random. `full` keeps every
lot outside New York and Philadelphia and every reform lot in them; their comparison lots (each rezoning lists the
whole city again) are one fixed set per seed, chosen by a hash of the lot's position, so the same lots are kept in
every rezoning (about 4,000 per rezoning, weighted up to the rezoning's count). Seeds only move that set;
scripts/build_tod_station_area_line.py averages the seeds.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_station_model as M  # noqa: E402

OUT = M.OUT
MAX_COMPARISON, MAX_REFORM = 60_000, 60_000
SEED = 20261101

LOT = ["log_acres", "log_land_value_per_acre", "land_value_rank_in_case", "bldg_to_land", "building_age", "log_homes_existing",
       "vacant", "public", "rate_before"]
PLACE = ["log_dist_m", "band_q", "band_h", "sld_transit_freq", "sld_jobs_per_acre", "sld_transit_job_access", "sld_share_no_car",
         "bg_job_growth_5y", "historic"]
REFORM = ["reform_stop", "in_reform_area", "coverage"]


BASE = ["group", "band", "stop_id", "dist_m", "in_reform_area", "acres", "land_value", "bldg_value", "year_built", "public",
        "homes_existing", "homes_before_win", "homes_after_win", "implausible"]


def fixed_share(x, y, seed: int) -> np.ndarray:
    """A number in [0, 1) per lot from its position (metres, rounded) and the seed: the same lot gets the same number in
    every case, so a threshold keeps the same lots across New York or Philadelphia rezonings."""
    k = (np.round(np.nan_to_num(x)).astype(np.int64) * 1_000_003 + np.round(np.nan_to_num(y)).astype(np.int64)
         + np.int64(seed) * 7_919).astype(np.uint64)
    k ^= k >> np.uint64(33); k *= np.uint64(0xFF51AFD7ED558CCD); k ^= k >> np.uint64(33)    # splitmix-style mixing
    k *= np.uint64(0xC4CEB9FE1A85EC53); k ^= k >> np.uint64(33)
    return (k >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def load_case(case: str, mode: str, rng: np.random.Generator, sampling: str = "capped", seed: int = SEED,
              tract: bool = True) -> pd.DataFrame | None:
    import pyarrow.parquet as pq
    f = OUT / f"lots_{case}.parquet"
    have = pq.ParquetFile(f).schema.names
    D = pd.read_parquet(f, columns=[c for c in have if c in BASE or c in PLACE or (tract and c.startswith("v_"))
                                    or c == "historic" or (sampling == "full" and c in ("x", "y"))])
    if (OUT / f"events_{case}.parquet").exists() and mode != "stored":
        D = M.event_windows(case, D, mode)
    D = D[~D.implausible.fillna(False)]
    if not (D.group == "reform").any():
        return None
    # New York and Philadelphia list every lot of the city for each of their many rezonings: smaller caps per case
    many = case.startswith(("nyc_", "phl_"))
    cap_c, cap_r = (4_000, 8_000) if many else (MAX_COMPARISON, MAX_REFORM)
    D = D.copy()
    D["w"] = 1.0
    if sampling == "full":
        if many:
            ix = D.index[D.group == "comparison"]
            if len(ix) > cap_c:
                keep = ix[fixed_share(D.loc[ix, "x"].values, D.loc[ix, "y"].values, seed) < cap_c / len(ix)]
                D = D.drop(index=ix.difference(keep))
                D.loc[keep, "w"] = len(ix) / max(len(keep), 1)
        D = D.drop(columns=["x", "y"])
    for grp, cap in ((("comparison", cap_c), ("reform", cap_r)) if sampling == "capped" else ()):
        ix = D.index[D.group == grp]
        if len(ix) > cap:
            keep = rng.choice(ix, cap, replace=False)
            D = D.drop(index=ix.difference(keep))
            D.loc[keep, "w"] = len(ix) / cap
    yb, ya = M.windows(case)
    D["rate_before"] = D.homes_before_win / yb
    D["y"] = D.homes_after_win / ya
    eff = M_eff(case)
    D["log_acres"] = np.log(D.acres.clip(lower=0.01).fillna(0.1))
    lva = D.land_value / D.acres.where(D.acres > 0)
    D["log_land_value_per_acre"] = np.log(lva.clip(lower=1000))
    D["land_value_rank_in_case"] = lva.rank(pct=True)
    D["bldg_to_land"] = (D.bldg_value / D.land_value.where(D.land_value > 0)).clip(0, 50)
    D["building_age"] = (eff - D.year_built).clip(0, 200)
    D["log_homes_existing"] = np.log1p(D.homes_existing.clip(lower=0))
    D["vacant"] = (D.bldg_value.fillna(0) <= 0).astype(float)
    D["public"] = D.public.astype(float)
    D["log_dist_m"] = np.log1p(D.dist_m)
    D["band_q"] = (D.band == "0-1/4").astype(float)
    D["band_h"] = (D.band == "1/4-1/2").astype(float)
    D["historic"] = D.get("historic", pd.Series(False, index=D.index)).astype(float)
    D["reform_stop"] = (D.group == "reform").astype(float)
    D["in_reform_area"] = D.in_reform_area.astype(float)
    cov = D.groupby(["stop_id", "band"]).in_reform_area.transform("mean")
    D["coverage"] = cov.where(D.group == "reform", 0.0)
    D["case"], D["city"] = case, M.city_of(case)
    D["strings_attached"] = float(case in STRINGS) * D["reform_stop"]
    num = D.select_dtypes("float64").columns
    D[num] = D[num].astype("float32")
    return D


def M_eff(case: str) -> int:
    import build_tod_station_lot_table as B
    cfg = {**B.CASES, **{k: v for k, (_, v) in B.adapter_cases().items()}}[case]
    return int(cfg.get("eff", cfg["after"][0] - 1))


DROP: set[str] = set()
STRINGS = {"la_toc_2017", "san_diego_2021", "chicago_2022"}   # incentive with required affordable homes (city trait)


def features(D: pd.DataFrame, groups: list[str]) -> list[str]:
    cols = [c for c in REFORM if c not in DROP]
    if "strings" in groups:
        cols.append("strings_attached")
    if "lot" in groups:
        cols += LOT
    if "place" in groups:
        cols += [c for c in PLACE if c in D]
    if "tract" in groups:
        cols += [c for c in D.columns if c.startswith("v_")]
    return cols


def effect_by_band(model, D: pd.DataFrame, cols: list[str]) -> pd.Series:
    R = D[D.reform_stop == 1]
    on = model.predict(R[cols].astype(float))
    off_X = R[cols].astype(float).copy()
    off_X[[c for c in ("reform_stop", "in_reform_area", "coverage", "strings_attached") if c in cols]] = 0.0
    off = model.predict(off_X)
    extra = (on - off) * R.w
    acres = (R.acres.fillna(0) * R.w).groupby(R.band).sum()
    return 100 * extra.groupby(R.band).sum() / acres


def wisconsin_rows() -> pd.DataFrame:
    """Wisconsin lots near rail and rapid stops (scripts/build_tod_station_wisconsin.py), with the training features.
    The law applies at every such stop: reform_stop = 1; in_reform_area = lot the law would upzone; coverage = share of
    that stop-band's lots the law would upzone. rate_before = homes built on the lot in the latest 5 years / 5."""
    W = pd.read_parquet(OUT / "wi_lots_station.parquet")
    W["rate_before"] = W.homes_before_win.fillna(0) / 5
    eff = 2027
    W["log_acres"] = np.log(W.acres.clip(lower=0.01).fillna(0.1))
    lva = W.land_value / W.acres.where(W.acres > 0)
    W["log_land_value_per_acre"] = np.log(lva.clip(lower=1000))
    W["land_value_rank_in_case"] = lva.groupby(W["case"]).rank(pct=True)
    W["bldg_to_land"] = (W.bldg_value / W.land_value.where(W.land_value > 0)).clip(0, 50)
    W["building_age"] = (eff - W.year_built).clip(0, 200)
    W["log_homes_existing"] = np.log1p(W.homes_existing.clip(lower=0))
    W["vacant"] = (W.bldg_value.fillna(0) <= 0).astype(float)
    W["public"] = W.public.astype(float)
    W["log_dist_m"] = np.log1p(W.dist_m)
    W["band_q"], W["band_h"] = (W.band == "0-1/4").astype(float), (W.band == "1/4-1/2").astype(float)
    W["historic"] = W.get("historic", pd.Series(False, index=W.index)).astype(float)
    W["reform_stop"] = 1.0
    W["in_reform_area"] = W.in_reform_area.astype(float)
    W["coverage"] = W.groupby([W["case"], W.stop_id, W.band]).in_reform_area.transform("mean")
    W["strings_attached"] = 0.0   # Wisconsin's law: by right, no affordability requirement
    W["w"] = 1.0
    return W


def wisconsin_extra(model, W: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Extra homes a year by band (Milwaukee and Madison lots near rail and rapid stops)."""
    on = model.predict(W[cols].astype(float))
    off_X = W[cols].astype(float).copy()
    off_X[[c for c in ("reform_stop", "in_reform_area", "coverage", "strings_attached") if c in cols]] = 0.0
    return pd.Series(on - model.predict(off_X), index=W.index).groupby(W.band).sum()


def main(argv=None) -> None:
    from sklearn.ensemble import HistGradientBoostingRegressor
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates", default="permit_est", choices=["stored", "permit_est", "completed"])
    ap.add_argument("--trait-groups", default="lot,place,tract")
    ap.add_argument("--drop", default="", help="reform features to leave out, e.g. coverage")
    ap.add_argument("--sampling", default="capped", choices=["capped", "full"])
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--model-seed", type=int, default=None, help="seed for the model fit only (default: --seed)")
    ap.add_argument("--no-early-stop", action="store_true",
                    help="fit all 300 rounds instead of sklearn's default early stopping on a random 10%% hold-out")
    a = ap.parse_args(argv)
    DROP.update(x for x in a.drop.split(",") if x)
    groups = a.trait_groups.split(",") if a.trait_groups else []
    rng = np.random.default_rng(a.seed)
    parts = [load_case(f.stem.removeprefix("lots_"), a.dates, rng, a.sampling, a.seed, tract=("tract" in groups) or a.sampling == "capped")
             for f in sorted(OUT.glob("lots_*.parquet"))]
    D = pd.concat([p for p in parts if p is not None], ignore_index=True)
    cols = features(D, groups)
    print(f"rows {len(D):,}; cities {D.city.nunique()}; features {len(cols)}")
    measured = M.city_level(M.case_effects(a.dates)).set_index(["city", "band"])["effect_per_100_acres"]
    W = wisconsin_rows() if (OUT / "wi_lots_station.parquet").exists() else None
    rows, wi = [], []
    for city in sorted(D.city.unique()):
        tr, te = D[D.city != city], D[D.city == city]
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=200, random_state=a.seed if a.model_seed is None else a.model_seed,
                                          **({'early_stopping': False} if a.no_early_stop else {}))
        m.fit(tr[cols].astype(float), tr.y, sample_weight=tr.w)
        if W is not None:
            wi.append(wisconsin_extra(m, W, cols).rename(f"without {city}"))
        pred = effect_by_band(m, te, cols)
        for band, v in pred.items():
            obs = measured.get((city, band), np.nan)
            others = measured.drop(index=city, level=0, errors="ignore").xs(band, level=1).mean()
            rows.append({"city": city, "band": band, "measured": obs, "model": v, "others_average": others})
    R = pd.DataFrame(rows)
    R["err_model"], R["err_avg"], R["err_zero"] = (R.model - R.measured).abs(), (R.others_average - R.measured).abs(), R.measured.abs()
    pd.set_option("display.width", 200)
    print(R.round(2).to_string(index=False))
    print("\nmedian absolute error by band (per 100 acres a year):")
    print(R.groupby("band")[["err_model", "err_avg", "err_zero"]].median().round(2).to_string())
    tag = (a.trait_groups.replace(",", "_") or "none") + (f"_no_{a.drop.replace(',', '_')}" if a.drop else "")
    if a.sampling == "full":
        tag += f"_full_s{a.seed}" + (f"_m{a.model_seed}" if a.model_seed is not None else "")
    if a.no_early_stop:
        tag += "_nes"
    if W is not None:
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=200, random_state=a.seed if a.model_seed is None else a.model_seed,
                                          **({'early_stopping': False} if a.no_early_stop else {}))
        m.fit(D[cols].astype(float), D.y, sample_weight=D.w)
        full = wisconsin_extra(m, W, cols)
        X = pd.concat(wi, axis=1)
        out = pd.DataFrame({"all_cities": full, "low": X.min(axis=1), "high": X.max(axis=1)})
        out.loc["total"] = out.sum()
        print("\nWisconsin (Milwaukee + Madison lots near rail and rapid stops), extra homes over 5 years:")
        print((5 * out).round(0).to_string())
        (5 * out).round(1).to_csv(REFERENCE / f"tod_station_lotmodel_wisconsin_{tag}.csv")
    R.round(4).to_csv(REFERENCE / f"tod_station_lotmodel_loco_{tag}.csv", index=False)


if __name__ == "__main__":
    main()

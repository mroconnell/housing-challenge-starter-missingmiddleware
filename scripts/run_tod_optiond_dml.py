"""Option D, "remove the noise" test: partialling out and double ML on the lot model (docs/tod/OPTION_D_PLAN.md, log
entry 2026-11-02 after 21:18, pre-registered before any fit).

Owner, 2026-11-02 21:10: "once we remove the noise from all these other variables which make it better or worse to
develop a lot near this stop, here is the difference reform makes". Two versions, so the treatment-model step can be
judged on its own:
  A    outcome only ("partialling out"): cross-fitted m(X) = E[y | X]; effect = weighted least-squares slope of
       y - m(X) on D (with an intercept);
  B    adds a cross-fitted treatment model e(X) = P(D | X):
       B-PLR   Robinson's partialling-out estimator, sum w (D - e)(y - m) / sum w (D - e)^2;
       B-AIPW  doubly robust effect on the treated lots, sum w [D (y - mu0) - (1 - D) e / (1 - e) (y - mu0)] / sum w D,
               mu0(X) = outcome model fitted on untreated lots.
       e trimmed to [0.01, 0.99]; the number of lots (and their land) trimmed is reported.

Rows: lots of the evidence set's places (D-11 or D-B), one band at a time, comparison lots as sampling "full".
Outcome y = 100 x (new homes a year after - before) / land acres (acres_land floored at 0.001 acre so homes on records
with no land stay in the numerator); weight w = lot weight x land acres, each place the same total weight. Weighted
means of y are extra new homes per 100 lot acres a year, the unit of the measured effects.
Treatment: "in_area" = in the reform area of a reform stop (main); "stop" = reform stop (check).
Traits: lot, place (no band flags), tract, and stop-table traits of the lot's stop; no place identifiers.
Cross-fitting: 5 folds of whole places. Interval: place-cluster bootstrap of the final step (nuisances held fixed).
Hidden-place test: hide a place, estimate on the others (folds over those places only), predict its measured band
effect (in_area: effect x its district land share; stop: effect), median absolute miss vs others' average and zero.

    OMP_NUM_THREADS=2 .venv/bin/python scripts/run_tod_optiond_dml.py --sets D-11 --bands 0-1/4 --seeds 1 --hidden
    .venv/bin/python scripts/run_tod_optiond_dml.py --summarize
Writes reference/tod_optiond_dml_full_<tag>.csv, reference/tod_optiond_dml_hidden_<tag>.csv and (--summarize)
reference/tod_optiond_dml_summary.csv. scikit-learn only.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_optiond as O  # noqa: E402
import run_tod_station_lotmodel as L  # noqa: E402
import run_tod_station_model as M  # noqa: E402

SETS = {"D-11": O.TRAIN,
        "D-B": ["New York", "austin_2009", "charlotte_2019", "denver_2018", "seattle_mount_baker_2014",
                "seattle_othello_2012", "slc_2010", "stpaul_2011"]}
BAND_SUFFIX = {"0-1/4": "q1", "1/4-1/2": "q2"}
WI_ACRES_QUARTER = 4874.1     # reference/tod_optiond_line.csv
SCALE = 1.2269                # statewide scale (land), reference/tod_optiond_line.csv
SHARE = 0.15
TRIM = (0.01, 0.99)
NFOLD = 5
ROUNDS = 150          # departure 2026-11-02 (coordinator): 150 rounds at rate 0.1
RATE = 0.1
NFOLD_HIDDEN = 3      # departure: 3 place-folds in the hidden-place loop
CASE_FOLDS = 5        # within-case treatment model: 5 lot folds inside each case
PLACE_X = [c for c in L.PLACE if c not in ("band_q", "band_h")]
STOP_X = ["st_log_upt_pre5", "st_trips_peak", "st_trips_midday", "st_n_systems", "st_transfer_hub",
          "st_log_dev_acres", "st_log_vacant_acres", "st_log_underused_acres",
          "st_share_dev", "st_share_vacant", "st_share_underused"]
KEEP = ["city", "case", "stop_id", "lot_index", "band", "w", "acres_land", "y", "rate_before", "reform_stop", "in_reform_area"]


def stop_traits() -> pd.DataFrame:
    s = pd.read_csv(REFERENCE / "tod_stop_table.csv", low_memory=False)
    s = s.drop_duplicates(["case", "stop_id"])
    rows = []
    for band, k in BAND_SUFFIX.items():
        land = s[f"acres_dedup_{k}"].where(s[f"acres_dedup_{k}"] > 0)
        rows.append(pd.DataFrame({
            "case": s.case, "stop_id": s.stop_id, "band": band,
            "st_log_upt_pre5": np.log1p(s.own_system_upt_pre5_avg),
            "st_trips_peak": s.trips_peak_all_systems, "st_trips_midday": s.trips_midday_all_systems,
            "st_n_systems": s.n_systems_at_node, "st_transfer_hub": s.transfer_hub,
            "st_log_dev_acres": np.log1p(s[f"dev_acres_dedup_{k}"]),
            "st_log_vacant_acres": np.log1p(s[f"vacant_dev_acres_dedup_{k}"]),
            "st_log_underused_acres": np.log1p(s[f"underused_dev_acres_dedup_{k}"]),
            "st_share_dev": s[f"dev_acres_dedup_{k}"] / land, "st_share_vacant": s[f"vacant_dev_acres_dedup_{k}"] / land,
            "st_share_underused": s[f"underused_dev_acres_dedup_{k}"] / land}))
    return pd.concat(rows, ignore_index=True)


def load_cases(cases: list[str], seed: int, bands: list[str], ST: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for case in cases:
        d = L.load_case(case, "permit_est", np.random.default_rng(seed), "full", seed, tract=True)
        if d is None:
            continue
        d = d[d.band.isin(bands)].copy()
        d["lot_index"] = d.index.astype("int64")
        d = d.merge(ST[ST.case == case].drop(columns="case"), on=["stop_id", "band"], how="left")
        cols = KEEP + O.FILL_COLS + [c for c in L.LOT + PLACE_X + STOP_X if c not in KEEP + O.FILL_COLS] \
            + [c for c in d.columns if c.startswith("v_")]
        d = d[[c for c in dict.fromkeys(cols) if c in d]]
        for c in d.columns:
            if d[c].dtype == "float64":
                d[c] = d[c].astype("float32")
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def all_cases() -> list[str]:
    return [f.stem.removeprefix("lots_") for f in sorted(L.OUT.glob("lots_*.parquet"))
            if M.city_of(f.stem.removeprefix("lots_")) in O.TRAIN]


def finish_rows(D: pd.DataFrame) -> pd.DataFrame:
    a = D.acres_land.astype(float).fillna(0).clip(lower=0.001)
    D["yy"] = 100 * (D.y.astype(float) - D.rate_before.astype(float)) / a
    D["om0"] = D.w.astype(float) * a
    D["D_in_area"] = (D.in_reform_area * D.reform_stop).astype(float)
    D["D_stop"] = D.reform_stop.astype(float)
    for c in O.FILL_COLS + STOP_X:          # gaps (whole-place ones: Austin land values, Philadelphia year built,
        if c in D:                           # Madison trips) take the median over the loaded lots, as fix "fill"
            D[c] = D[c].fillna(np.nanmedian(D[c].astype(float)))
    return D


def xcols(D: pd.DataFrame) -> list[str]:
    return [c for c in L.LOT + PLACE_X + STOP_X if c in D] + [c for c in D.columns if c.startswith("v_")]


def gbr(seed):
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(max_iter=ROUNDS, learning_rate=RATE, min_samples_leaf=200, early_stopping=False,
                                         random_state=seed)


def gbc(seed, leaf: int = 200):
    from sklearn.ensemble import HistGradientBoostingClassifier
    return HistGradientBoostingClassifier(max_iter=ROUNDS, learning_rate=RATE, min_samples_leaf=leaf,
                                          early_stopping=False, random_state=seed)


def crossfit(B: pd.DataFrame, X: np.ndarray, places: list[str], seed: int, nfold: int, mu0: bool, log: str = "") -> dict:
    """Out-of-fold outcome predictions over `nfold` folds of whole places: m(X) = E[y | X] and (if mu0) the outcome
    model on lots outside any district, mu0(X) (B-AIPW diagnostic)."""
    om, y = B.om.to_numpy(float), B.yy.to_numpy(float)
    t = B.D_in_area.to_numpy(int)
    out = {"m": np.full(len(B), np.nan), "mu0_in_area": np.full(len(B), np.nan)}
    perm = np.random.default_rng(seed).permutation(len(places))
    fold = B.city.map({p: int(perm[i] % nfold) for i, p in enumerate(places)}).to_numpy()
    for f in range(nfold):
        tr, te = fold != f, fold == f
        if not te.any():
            continue
        t0 = time.time()
        out["m"][te] = gbr(seed).fit(X[tr], y[tr], sample_weight=om[tr]).predict(X[te])
        if mu0:
            c = tr & (t == 0)
            out["mu0_in_area"][te] = gbr(seed).fit(X[c], y[c], sample_weight=om[c]).predict(X[te])
        print(f"   {log} fold {f}: {te.sum():,} rows out, {time.time() - t0:.0f} s", flush=True)
    return out


def case_propensity(B: pd.DataFrame, X: np.ndarray, seed: int) -> np.ndarray:
    """Departure 2 (coordinator, 2026-11-02): P(in the reform area | X) fitted within each case (how a city picks its
    district), cross-fitted over 5 lot folds inside the case; leaf >= 20 lots (small cases). Cases with no district
    lots (or only district lots) get the case share."""
    t = B.D_in_area.to_numpy(int)
    om = B.om.to_numpy(float)
    e = np.full(len(B), np.nan)
    rng = np.random.default_rng(seed + 17)
    t0 = time.time()
    for case, ix in B.groupby("case").indices.items():
        tc = t[ix]
        if tc.min() == tc.max() or min(tc.sum(), (1 - tc).sum()) < CASE_FOLDS:
            e[ix] = np.average(tc, weights=om[ix]) if om[ix].sum() > 0 else tc.mean()
            continue
        fold = rng.permutation(len(ix)) % CASE_FOLDS
        for f in range(CASE_FOLDS):
            tr, te = ix[fold != f], ix[fold == f]
            if t[tr].min() == t[tr].max():
                e[te] = t[tr].mean()
                continue
            e[te] = gbc(seed, 20).fit(X[tr], t[tr], sample_weight=om[tr]).predict_proba(X[te])[:, 1]
    print(f"   within-case treatment model: {B.case.nunique()} cases, {time.time() - t0:.0f} s", flush=True)
    return e


def centre(v: np.ndarray, w: np.ndarray, case: np.ndarray) -> np.ndarray:
    """Departure 1 (coordinator, 2026-11-02): subtract the case's weighted mean (compare lots within a rezoning)."""
    s = pd.DataFrame({"c": case, "wv": w * v, "w": w}).groupby("c")[["wv", "w"]].transform("sum")
    return v - (s.wv / s.w.where(s.w > 0)).fillna(0).to_numpy()


def place_sums(B: pd.DataFrame, m: np.ndarray, e_raw: np.ndarray | None, mu0: np.ndarray | None,
               d: str) -> tuple[pd.DataFrame, dict]:
    """Per-place sums of the final steps, residuals centred within case. A: slope of r~ on D~; B-PLR: sum w (D - e) r~
    / sum w (D - e)^2 (e from the within-case model); B-AIPW (diagnostic, unstable): effect on district lots."""
    om, y, t = B.om.to_numpy(float), B.yy.to_numpy(float), B[f"D_{d}"].to_numpy(float)
    case = B.case.to_numpy()
    r = centre(y - m, om, case)
    tc = centre(t, om, case)
    cols = {"city": B.city.values, "a_num": om * tc * r, "a_den": om * tc * tc, "wd": om * t}
    trim = {"lots": int(len(t)), "lots_trimmed": 0, "land_share_trimmed": 0.0, "treated_lots_trimmed": 0}
    if e_raw is not None:
        e = np.clip(e_raw, *TRIM)
        bad = (e_raw < TRIM[0]) | (e_raw > TRIM[1])
        cols.update({"plr_num": om * (t - e) * r, "plr_den": om * (t - e) ** 2})
        r0 = centre(y - mu0, om, case) if mu0 is not None else None
        if r0 is not None:
            cols["aipw_num"] = om * (t * r0 - (1 - t) * e / (1 - e) * r0)
        trim = {"lots": int(len(t)), "lots_trimmed": int(bad.sum()), "land_share_trimmed": float(om[bad].sum() / om.sum()),
                "treated_lots_trimmed": int((bad & (t == 1)).sum())}
    return pd.DataFrame(cols).groupby("city").sum(), trim


def estimates(S: pd.DataFrame) -> dict:
    s = S.sum()
    out = {"A": s.a_num / s.a_den}
    if "plr_num" in S:
        out["B-PLR"] = s.plr_num / s.plr_den
    if "aipw_num" in S:
        out["B-AIPW (diagnostic)"] = s.aipw_num / s.wd
    return out


def bootstrap(S: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 991)
    arr = S.to_numpy()
    return pd.DataFrame([estimates(pd.DataFrame(arr[rng.integers(0, len(S), len(S))], columns=S.columns))
                         for _ in range(n)])


def district_share(D: pd.DataFrame) -> pd.Series:
    """Per place and band: land share of reform-stop lots in the reform area (NY/PHL: mean over rezonings)."""
    R = D[D.reform_stop == 1]
    wa = R.w.astype(float) * R.acres_land.astype(float).fillna(0)
    g = pd.DataFrame({"city": R.city, "case": R.case, "band": R.band, "wa": wa, "wad": wa * R.in_reform_area})
    c = g.groupby(["city", "case", "band"])[["wa", "wad"]].sum()
    c["share"] = c.wad / c.wa
    return c.groupby(["city", "band"]).share.mean()


def wisconsin(theta: float, d: str) -> float:
    return theta * (SHARE if d == "in_area" else 1.0) * WI_ACRES_QUARTER / 100 * 5 * SCALE


def with_weights(B: pd.DataFrame) -> pd.DataFrame:
    B = B.reset_index(drop=True)
    B["om"] = B.om0 / B.groupby("city").om0.transform("sum") * 1e5
    return B


def run_set(D, set_name, band, seed, hidden, n_boot, measured, share, rows_full, rows_hidden, interim=None):
    places = [p for p in SETS[set_name] if p in set(D.city)]
    B = with_weights(D[(D.band == band) & D.city.isin(places)])
    cols = xcols(B)
    X = B[cols].to_numpy(np.float32)
    print(f"== {set_name} {band} seed {seed}: {len(B):,} lots, {len(places)} places, {B.case.nunique()} cases, "
          f"{len(cols)} traits", flush=True)
    e_in = case_propensity(B, X, seed)
    nu = crossfit(B, X, places, seed, NFOLD, True, f"{set_name} {band} full")
    for d in ("in_area", "stop"):
        S, trim = place_sums(B, nu["m"], e_in if d == "in_area" else None,
                             nu["mu0_in_area"] if d == "in_area" else None, d)
        est = estimates(S)
        bs = bootstrap(S, n_boot, seed)
        for v, th in est.items():
            lo, hi = np.nanpercentile(bs[v], [2.5, 97.5])
            rows_full.append({"set": set_name, "band": band, "seed": seed, "treatment": d, "version": v,
                              "effect": th, "effect_lo": lo, "effect_hi": hi, "boot_draws": n_boot,
                              "wisconsin": wisconsin(th, d), "wisconsin_lo": wisconsin(lo, d),
                              "wisconsin_hi": wisconsin(hi, d), "traits": len(cols), "lots_all": len(B), **trim})
            print(f"   {d:8s} {v:20s} effect {th:8.2f} ({lo:.2f} to {hi:.2f}); Wisconsin {wisconsin(th, d):,.0f}"
                  f"; trimmed {trim['lots_trimmed']:,} lots", flush=True)
    if not hidden:
        return
    for h in places:
        rest = [p for p in places if p != h]
        keep = B.city.isin(rest).to_numpy()
        T = with_weights(B[keep])
        m = crossfit(T, X[keep], rest, seed, NFOLD_HIDDEN, False, f"{set_name} {band} without {h}")["m"]
        meas = measured.get((h, band), np.nan)
        others = np.mean([measured[(p, band)] for p in rest if (p, band) in measured])
        for d in ("in_area", "stop"):
            S, trim = place_sums(T, m, e_in[keep] if d == "in_area" else None, None, d)
            for v, th in estimates(S).items():
                pred = th * (share.get((h, band), np.nan) if d == "in_area" else 1.0)
                rows_hidden.append({"set": set_name, "band": band, "seed": seed, "treatment": d, "version": v,
                                    "hidden": h, "effect_on_others": th, "district_share": share.get((h, band), np.nan),
                                    "predicted": pred, "measured": meas, "others_average": others,
                                    "miss_model": abs(pred - meas), "miss_average": abs(others - meas),
                                    "miss_zero": abs(meas), "lots_trimmed": trim["lots_trimmed"]})
        print(f"   hidden {h} done (measured {meas:.2f})", flush=True)
        if interim:
            interim()


def summarize() -> None:
    F = pd.concat([pd.read_csv(f) for f in sorted(REFERENCE.glob("tod_optiond_dml_full_*.csv"))], ignore_index=True)
    H = [pd.read_csv(f) for f in sorted(REFERENCE.glob("tod_optiond_dml_hidden_*.csv"))]
    H = pd.concat(H, ignore_index=True) if H else pd.DataFrame()
    key = ["set", "band", "treatment", "version"]
    s1 = F[F.seed == 1].set_index(key)[["effect", "effect_lo", "effect_hi", "wisconsin", "wisconsin_lo",
                                        "wisconsin_hi", "lots_trimmed", "land_share_trimmed"]]
    sp = F.groupby(key).agg(seeds=("seed", "nunique"), effect_seed_min=("effect", "min"),
                            effect_seed_max=("effect", "max"), wisconsin_seed_mean=("wisconsin", "mean"),
                            wisconsin_seed_min=("wisconsin", "min"), wisconsin_seed_max=("wisconsin", "max"))
    sp["wisconsin_seed_spread_pct"] = 100 * (sp.wisconsin_seed_max - sp.wisconsin_seed_min) / sp.wisconsin_seed_mean.abs()
    out = s1.join(sp, how="outer")
    if len(H):
        h = H[H.seed == 1].groupby(key).agg(hidden_places=("hidden", "nunique"), miss_model=("miss_model", "median"),
                                             miss_average=("miss_average", "median"), miss_zero=("miss_zero", "median"))
        out = out.join(h, how="left")
    out = out.reset_index()
    out.round(3).to_csv(REFERENCE / "tod_optiond_dml_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(2).to_string(index=False))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", default="D-11,D-B")
    ap.add_argument("--bands", default="0-1/4,1/4-1/2")
    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--hidden", action="store_true", help="hidden-place test on the first seed, 1/4 mile only")
    ap.add_argument("--boot", type=int, default=500)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--summarize", action="store_true")
    a = ap.parse_args(argv)
    if a.summarize:
        return summarize()
    sets, bands, seeds = a.sets.split(","), a.bands.split(","), [int(x) for x in a.seeds.split(",")]
    hc = pd.read_csv(L.OUT / "hand_check_big_lots.csv")
    print(f"hand-check rule rows present: {hc.evidence_short.astype(str).str.startswith('rule ').sum():,}", flush=True)
    measured = M.city_level(M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    measured = measured[measured.index.get_level_values(0).isin(O.TRAIN)].to_dict()
    ST = stop_traits()
    cases = all_cases()
    many = [c for c in cases if c.startswith(("nyc_", "phl_"))]
    t0 = time.time()
    base = load_cases([c for c in cases if c not in many], 1, bands, ST)
    print(f"loaded other places: {len(base):,} lots, {time.time() - t0:.0f} s", flush=True)
    rows_full, rows_hidden = [], []
    tag = a.tag or "_".join(sets)

    def save():
        pd.DataFrame(rows_full).round(4).to_csv(REFERENCE / f"tod_optiond_dml_full_{tag}.csv", index=False)
        if rows_hidden:
            pd.DataFrame(rows_hidden).round(4).to_csv(REFERENCE / f"tod_optiond_dml_hidden_{tag}.csv", index=False)

    for k, seed in enumerate(seeds):
        D = finish_rows(pd.concat([base, load_cases(many, seed, bands, ST)], ignore_index=True))
        share = district_share(D).to_dict()
        # order (coordinator): seed 1 within 1/4 mile and its hidden-place test first, then the other band and seeds
        for band in bands:
            for set_name in sets:
                run_set(D, set_name, band, seed, a.hidden and k == 0 and band == "0-1/4", a.boot, measured, share,
                        rows_full, rows_hidden, save)
                save()
        del D
    if rows_hidden:
        H = pd.DataFrame(rows_hidden)
        print(H.groupby(["set", "band", "treatment", "version"])[["miss_model", "miss_average", "miss_zero"]]
              .median().round(2).to_string())


if __name__ == "__main__":
    main()

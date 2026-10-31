"""Parking no-reform model (docs/parking/NO_REFORM_MODEL_PLAN.md): homes permitted per place per year with no
parking reform, from data every state has (Census permit survey, ACS).

    uv run --all-extras python scripts/run_parking_no_reform.py [--round N]

Outputs: reference/parking_no_reform_scores.csv, _rows.csv (held-out predictions), _wisconsin.csv, _checks.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
import run_parking_improve_r1 as R1  # noqa: E402
from missing_middleware.parking import checks  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

FIT_ORIGINS, TEST_ORIGINS = (2016, 2017, 2018), (2019, 2020)
SEEDS = range(20261031, 20261036)
MIN_HOMES = 1000
WI = "55"
ROUND = int(sys.argv[sys.argv.index("--round") + 1]) if "--round" in sys.argv else 1
TAG = f"_r{ROUND}"


def acs(table: str, col: str, folder: str = "census_acs5_2024_tbsf_allvars") -> pd.Series:
    return rpc.acs_table(RAW / folder / f"acsdt5y2024-{table}.dat", col)


def score(pred: np.ndarray, act: np.ndarray) -> dict:
    lg = np.abs(np.log((pred + 0.5) / (act + 0.5)))
    return dict(median_abs_log=float(np.median(lg)), error_per_unit=float(np.abs(pred - act).sum() / max(act.sum(), 1e-9)),
                total_ratio=float(pred.sum() / max(act.sum(), 1e-9)), n=int(len(act)))


def build_rows(p: pd.DataFrame, homes_acs: pd.Series, reform_year: dict, traits: pd.DataFrame) -> pd.DataFrame:
    tot = p.pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")
    mf = p.pivot_table(index="key", columns="year", values="units_2plus", aggfunc="sum")
    pop = p.pivot_table(index="key", columns="year", values="pop", aggfunc="first")
    info = p.drop_duplicates("key", keep="last").set_index("key")[["state_fips", "division", "name"]]
    years = sorted(tot.columns)
    rows = []
    for t in range(2016, 2026):
        hist = [t - 4, t - 3, t - 2, t - 1, t]
        fut = [y for y in range(t + 1, t + 6) if y in years]
        need = hist + fut
        ok = tot[need].notna().all(axis=1)
        k = tot.index[ok]
        since = tot.loc[k, [y for y in years if t < y <= 2024]].sum(axis=1)
        h = (homes_acs.reindex(k) - since).clip(lower=homes_acs.reindex(k) * 0.5)
        d = pd.DataFrame(index=k)
        d["origin"] = t
        d["homes"] = h
        d["homes_floored"] = (homes_acs.reindex(k) - since) < homes_acs.reindex(k) * 0.5
        for j, y in enumerate(hist):
            d[f"u{j}"] = tot.loc[k, y]
        d["units_3y"] = tot.loc[k, hist[-3:]].mean(axis=1)
        d["units_5y"] = tot.loc[k, hist].mean(axis=1)
        d["rate_1y"] = tot.loc[k, t] / h * 1000
        d["rate_3y"] = d["units_3y"] / h * 1000
        d["rate_5y"] = d["units_5y"] / h * 1000
        d["share_2plus"] = (mf.loc[k, hist].sum(axis=1) / tot.loc[k, hist].sum(axis=1).replace(0, np.nan)).fillna(0)
        x = np.arange(5) - 2.0
        d["trend"] = (tot.loc[k, hist].values / h.values[:, None] * 1000 @ x) / (x @ x)
        d["pop_growth"] = np.log(pop.loc[k, t].clip(lower=1) / pop.loc[k, t - 4].clip(lower=1))
        d["actual"] = tot.loc[k, fut].mean(axis=1) if len(fut) == 5 else np.nan
        d = d.join(info)
        d = d[d["homes"] >= MIN_HOMES]
        ry = d.index.map(lambda q: reform_year.get(q, 9999))
        d["reform_year"] = ry
        # never reformed, or every outcome year before the repeal; undated reforms (-1) never qualify
        d["no_reform"] = (np.asarray(ry) == 9999) | (np.asarray(ry) > t + 5)
        rows.append(d.reset_index())
    r = pd.concat(rows, ignore_index=True)
    # state and division momentum: 3-year over 5-year permits, from all places (data any state has at the origin)
    for g in ("state_fips", "division"):
        s3 = r.groupby([g, "origin"])["units_3y"].transform("sum")
        s5 = r.groupby([g, "origin"])["units_5y"].transform("sum")
        r[f"{g}_momentum"] = s3 / s5.replace(0, np.nan)
    r["size_class"] = pd.cut(r["homes"], [0, 5_000, 20_000, 100_000, np.inf], labels=False)
    r["log_homes"] = np.log(r["homes"])
    r = r.merge(traits, left_on="key", right_index=True, how="left")
    return r


BASE = ["log_homes", "rate_1y", "rate_3y", "rate_5y", "share_2plus", "trend", "pop_growth", "state_fips_momentum",
        "division_momentum", "size_class"]
ACS = ["income", "renter_share", "vacancy", "pre1980"]


def m2_shrunk(fit: pd.DataFrame, new: pd.DataFrame) -> np.ndarray:
    """Empirical Bayes: each place's 3-year rate pulled toward its division x size-class mean at the same origin."""
    rates = new[["u2", "u3", "u4"]].values / new["homes"].values[:, None] * 1000
    s2 = rates.var(axis=1, ddof=1) / 3
    out = np.empty(len(new))
    for (o, dv, sc), idx in new.groupby(["origin", "division", "size_class"]).indices.items():
        pool = fit[(fit["origin"] == o) & (fit["division"] == dv) & (fit["size_class"] == sc)]
        if len(pool) < 5:
            pool = fit[(fit["origin"] == o) & (fit["size_class"] == sc)]
        pr = pool[["u2", "u3", "u4"]].values / pool["homes"].values[:, None] * 1000
        m = np.average(pr.mean(axis=1), weights=pool["homes"])
        tau2 = max(np.var(pr.mean(axis=1)) - np.mean(pr.var(axis=1, ddof=1) / 3), 1e-6)
        r3 = rates[idx].mean(axis=1)
        w = tau2 / (tau2 + s2[idx])
        out[idx] = (w * r3 + (1 - w) * m) * new["homes"].values[idx] / 1000
    return out


def fit_glm(fit, cols, alpha):
    m = make_pipeline(StandardScaler(), PoissonRegressor(alpha=alpha, max_iter=1000))
    y = (fit["actual"] / fit["homes"] * 1000).clip(lower=0)
    m.fit(fit[cols].fillna(fit[cols].median()), y, poissonregressor__sample_weight=fit["homes"] / 1000)
    return m


def fit_hgb(fit, cols, lr, leaves, seed):
    m = HistGradientBoostingRegressor(loss="poisson", learning_rate=lr, max_leaf_nodes=leaves, max_iter=300,
                                      min_samples_leaf=40, random_state=seed)
    y = (fit["actual"] / fit["homes"] * 1000).clip(lower=0)
    m.fit(fit[cols], y, sample_weight=fit["homes"] / 1000)
    return m


def pred_rate(m, df, cols, med=None):
    X = df[cols]
    if med is not None:
        X = X.fillna(med)
    return np.clip(m.predict(X), 0, None) * df["homes"].values / 1000


def choose(fit, cols, kind, seed):
    """5-fold CV over places within the fitting origins; returns the best setting by median |log|."""
    grid = [1e-4, 1e-3, 1e-2, 1e-1] if kind == "glm" else [(0.05, 15), (0.05, 31), (0.1, 15), (0.03, 31)]
    best, bs = None, np.inf
    gkf = GroupKFold(n_splits=5)
    for g in grid:
        s = []
        for a, b in gkf.split(fit, groups=fit["key"]):
            fa, fb = fit.iloc[a], fit.iloc[b]
            if kind == "glm":
                m = fit_glm(fa, cols, g)
                pr = pred_rate(m, fb, cols, fa[cols].median())
            else:
                m = fit_hgb(fa, cols, *g, seed)
                pr = pred_rate(m, fb, cols)
            s.append(score(pr, fb["actual"].values)["median_abs_log"])
        if np.mean(s) < bs:
            best, bs = g, float(np.mean(s))
    return best, bs


def predict_all(fit, new, seed, choices=None, fake=False):
    """Every model's prediction for `new`, fitted on `fit`. Returns dict model -> array, and the choices made."""
    out = {"M0 flat 3-year": new["units_3y"].values,
           "M1 flat 3-year x state momentum": (new["units_3y"] * new["state_fips_momentum"].fillna(1)).values,
           "M2 shrunk 3-year": m2_shrunk(fit, new)}
    choices = choices or {}
    extra = ["fake_reform"] if fake else []
    for name, kind, cols in (("M3a regression", "glm", BASE + extra), ("M3b regression + ACS", "glm", BASE + ACS + extra),
                             ("M4 boosted trees", "hgb", BASE + ACS + extra)):
        if name not in choices:
            choices[name] = choose(fit, cols, kind, seed)[0]
        g = choices[name]
        m = fit_glm(fit, cols, g) if kind == "glm" else fit_hgb(fit, cols, *g, seed)
        med = fit[cols].median() if kind == "glm" else None
        out[name] = pred_rate(m, new, cols, med)
        if fake:  # with the fake reform on, minus off (should be about 0)
            on, off = new.assign(fake_reform=1), new.assign(fake_reform=0)
            out[name + " | fake on-off"] = pred_rate(m, on, cols, med) - pred_rate(m, off, cols, med)
    return out, choices


def main() -> None:
    bps = rpc.read_bps_us()
    p = R1.panel_with(bps, "scaled")
    months = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()) \
        .drop_duplicates(["key", "year"]).set_index(["key", "year"])["months_reported"]
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes_acs = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    vac = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E003"))
    inc = geo["acs_geoid"].map(acs("b19013", "B19013_E001", "census_acs5_2024_tbsf_market"))
    own = geo["acs_geoid"].map(acs("b25003", "B25003_E001", "census_acs5_2024_tbsf_market"))
    rent = geo["acs_geoid"].map(acs("b25003", "B25003_E003", "census_acs5_2024_tbsf_market"))
    yb = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25034.dat", "B25034_E001")
    old = sum(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25034.dat", f"B25034_E{i:03d}") for i in range(7, 12))
    traits = pd.DataFrame({"income": inc, "renter_share": rent / own.replace(0, np.nan), "vacancy": vac / homes_acs,
                           "pre1980": geo["acs_geoid"].map(old / yb.replace(0, np.nan))})
    homes_acs = homes_acs[homes_acs > 0]

    # reform dates: material entries (V7 coding) plus state laws (V7s)
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    mat = set(pd.read_csv(REFERENCE / "parking_reform_material.csv").query("material")["prn_key"])
    reform_year: dict = {}
    for r in tax[tax["prn_key"].isin(mat)].itertuples():
        k = cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if k:
            y = r.adopted_year if pd.notna(r.adopted_year) else -1
            reform_year[k] = min(reform_year.get(k, 9999), y)
    for k in homes_acs.index:
        y = R1.STATE_LAW.get(k.split("|")[0])
        if y is not None:
            reform_year[k] = min(reform_year.get(k, 9999), y)

    R = build_rows(p, homes_acs, reform_year, traits)
    R["estimated_months"] = [sum(1 for y in range(o - 4, o + 6) if months.get((k, y), 12) < 12)
                             for k, o in zip(R["key"], R["origin"])]
    real_years = [y for y in reform_year.values() if 2012 <= y <= 2022]
    train = R[R["no_reform"]].copy()
    flags = checks.unit_ranges(train, {"rate_3y": ("permits per 1,000 existing homes per year", 0.0, 200.0),
                                       "actual": ("permits per place per year", 0.0, 50_000.0)})
    flags += [dict(check="homes floored at half of ACS", row=int(train["homes_floored"].sum()), detail="place-origin rows")]
    flags += [dict(check="estimated permit months in window", row=int((train["estimated_months"] > 0).sum()),
                   detail="place-origin rows with at least one estimated year")]

    places = train.drop_duplicates("key")[["key", "division", "state_fips"]]
    score_rows, kept_rows, choices_log = [], [], []
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        nonwi = places[places["state_fips"] != WI]
        held = set()
        for dv, g in nonwi.groupby("division"):
            held |= set(rng.choice(g["key"].values, size=max(1, int(round(0.2 * len(g)))), replace=False))
        # fake reform for 10% of training places
        tr_keys = sorted(set(nonwi["key"]) - held)
        fake_keys = set(rng.choice(tr_keys, size=int(0.1 * len(tr_keys)), replace=False))
        fake_year = {k: int(rng.choice(real_years)) for k in fake_keys}
        T = train.assign(fake_reform=[int(k in fake_year and o >= fake_year[k]) for k, o in zip(train["key"], train["origin"])])
        fit = T[T["key"].isin(tr_keys) & T["origin"].isin(FIT_ORIGINS) & T["actual"].notna()]
        tests = {
            "held-out places, later years": T[T["key"].isin(held) & T["origin"].isin(TEST_ORIGINS)],
            "training places, later years": T[T["key"].isin(tr_keys) & T["origin"].isin(TEST_ORIGINS)],
            "held-out places, same years": T[T["key"].isin(held) & T["origin"].isin(FIT_ORIGINS)],
            "Wisconsin, later years": T[(T["state_fips"] == WI) & T["origin"].isin(TEST_ORIGINS)],
        }
        choices = None
        for name, te in tests.items():
            te = te[te["actual"].notna()]
            preds, choices = predict_all(fit, te, seed, choices, fake=True)
            for mname, pr in preds.items():
                if "fake on-off" in mname:
                    score_rows.append(dict(seed=seed, test=name, model=mname, median_abs_log=np.nan,
                                           mean_on_minus_off=float(np.mean(pr)), n=len(te)))
                    continue
                score_rows.append(dict(seed=seed, test=name, model=mname, **score(pr, te["actual"].values)))
                if name == "held-out places, later years":
                    # 90% range of the difference from M0 in the summary score, resampling held-out places
                    m0 = preds["M0 flat 3-year"]
                    keys = te["key"].values
                    uk = np.unique(keys)
                    idx = {k: np.where(keys == k)[0] for k in uk}
                    a = np.abs(np.log((pr + 0.5) / (te["actual"].values + 0.5)))
                    b = np.abs(np.log((m0 + 0.5) / (te["actual"].values + 0.5)))
                    diffs = []
                    brng = np.random.default_rng(seed + 100)
                    for _ in range(2000):
                        s = np.concatenate([idx[k] for k in brng.choice(uk, size=len(uk))])
                        diffs.append(np.median(b[s]) - np.median(a[s]))
                    score_rows[-1].update(gain_vs_M0_p5=float(np.percentile(diffs, 5)), gain_vs_M0_p95=float(np.percentile(diffs, 95)))
                    kept_rows.append(te[["key", "name", "state_fips", "origin", "homes", "actual"]].assign(seed=seed, model=mname, pred=pr))
                if name == "training places, later years":
                    # statewide level (owner, 2026-10-31): each state's total over its places, held-out years
                    st = te.assign(pred=pr).groupby(["state_fips", "origin"])[["pred", "actual"]].sum()
                    score_rows.append(dict(seed=seed, test="state totals, later years", model=mname, **score(st["pred"].values, st["actual"].values)))
        choices_log.append(dict(seed=seed, **{k: str(v) for k, v in choices.items()}))
        print("seed", seed, "done", flush=True)

    S = pd.DataFrame(score_rows)
    S.to_csv(REFERENCE / f"parking_no_reform_scores{TAG}.csv", index=False)
    pd.DataFrame(choices_log).to_csv(REFERENCE / f"parking_no_reform_choices{TAG}.csv", index=False)
    K = pd.concat(kept_rows, ignore_index=True)
    K.to_csv(REFERENCE / f"parking_no_reform_rows{TAG}.csv", index=False)

    # Wisconsin: fit on all non-Wisconsin training rows (origins 2016-2020), predict from origin 2020 (scored on 2021-2025)
    # and origin 2025 (forecast 2026-2030, compared with the shared baseline's 2027-2031)
    allfit = train[(train["state_fips"] != WI) & train["actual"].notna()].assign(fake_reform=0)
    wi_rows = []
    for o in (2020, 2025):
        te = R[(R["state_fips"] == WI) & (R["origin"] == o)].assign(fake_reform=0)
        preds, _ = predict_all(allfit, te, SEEDS[0])
        for mname, pr in preds.items():
            row = dict(origin=o, model=mname, places=len(te), five_year_total=float(pr.sum() * 5))
            if o == 2020:
                row.update(actual_five_year=float(te["actual"].sum() * 5), **score(pr, te["actual"].values))
            wi_rows.append(row)
    W = pd.DataFrame(wi_rows)
    W.to_csv(REFERENCE / f"parking_no_reform_wisconsin{TAG}.csv", index=False)

    main_t = S[S["test"] == "held-out places, later years"]
    worst_model = main_t.groupby("model")["median_abs_log"].mean().idxmin()
    k0 = K[(K["model"] == worst_model) & (K["seed"] == SEEDS[0])].assign(miss=lambda d: d["pred"] - d["actual"])
    w = k0.loc[k0["miss"].abs().idxmax()]
    flags += [dict(check="worst miss (units per year)", row=f"{w['name']} {w['key']} origin {w['origin']}",
                   detail=f"{worst_model}: predicted {w['pred']:.0f}, actual {w['actual']:.0f}, homes {w['homes']:.0f}")]
    checks.report(flags, REFERENCE / f"parking_no_reform_checks{TAG}.csv")

    pd.set_option("display.width", 220)
    print(S.groupby(["test", "model"])[["median_abs_log", "error_per_unit", "total_ratio", "mean_on_minus_off"]].agg(["mean", "min", "max"]).round(3).to_string())
    print(main_t.groupby("model")[["gain_vs_M0_p5", "gain_vs_M0_p95"]].agg(["min", "max"]).round(3).to_string())
    print(W.round(3).to_string())
    print("training rows", len(train), "places", train["key"].nunique(), "Wisconsin places", R[R["state_fips"] == WI]["key"].nunique())


if __name__ == "__main__":
    main()

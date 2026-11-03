"""Parking causal follow-up FU4: double machine learning (partialling out) of repeal on the change in permits.
docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Stage 1 follow-ups" (owner OK 2026-11-03; post hoc to Stage 1; locked before counting).

Units: each repeal place, and each of its comparison-pool places (cmp.controls), at the repeal place's windows.
Y = after rate - before rate (permits per 1,000 existing homes a year). D = 1 for the repeal place.
X = before-window share of permitted homes in 5+ unit buildings, county job growth (QCEW, after-window mean / before-window
mean - 1), census division (one-hot), before-window rate, before-window trend (last 2 before years minus first 3), event year.
Cross-fitted, 5 folds grouped by place, random forests (scikit-learn), seed 20261103. theta = sum(rY rD) / sum(rD^2),
standard error clustered by place.

    uv run python scripts/run_parking_causal_fu4_dml.py
Output: reference/parking_causal_fu4_dml.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED = 20261103


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    u5 = b.pivot_table(index="key", columns="year", values="5plus_units", aggfunc="sum")
    ut = p.pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    jobs = pd.read_csv(REFERENCE / "parking_traits_county_jobs.csv", dtype={"county_fips5": str}).pivot_table(
        index="county_fips5", columns="year", values="employment")
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    excluded |= set(real["key"])

    def unit(key, pre, post, e):
        if key not in geo.index or key not in homes.index:
            return dict(Y=np.nan, share5=np.nan, job_growth=np.nan, division="", rate_before=np.nan, trend_before=np.nan,
                        event_year=e, homes=np.nan)
        t0, t1 = cmp._rate(p, [key], pre, "units_total", homes), cmp._rate(p, [key], post, "units_total", homes)
        a5 = np.nansum(u5.reindex(index=[key], columns=pre).values)
        at = np.nansum(ut.reindex(index=[key], columns=pre).values)
        cf = geo.loc[key, "state_fips"] + str(geo.loc[key, "county_fips"]).zfill(3)
        jb = jobs.reindex(index=[cf], columns=pre).mean(axis=1).iloc[0]
        ja = jobs.reindex(index=[cf], columns=post).mean(axis=1).iloc[0]
        yrs = [cmp._rate(p, [key], [y], "units_total", homes) for y in pre]
        trend = np.nanmean(yrs[-2:]) - np.nanmean(yrs[:3]) if len(yrs) >= 4 else np.nan
        return dict(Y=t1 - t0, share5=a5 / at if at > 0 else np.nan, job_growth=ja / jb - 1 if jb and jb > 0 else np.nan,
                    division=geo.loc[key, "division"], rate_before=t0, trend_before=trend, event_year=e, homes=float(homes.get(key, np.nan)))

    rows = []
    for r in real.itertuples():
        e = int(r.event_year)
        pre, post = cmp.windows(e)
        post = post[: int(r.n_post)]
        rows.append(dict(group=r.key, place=r.key, D=1, **unit(r.key, pre, post, e)))
        ctrl, _ = cmp.controls(p, r.key, e, excluded - {r.key}, homes, popn)
        for c in ctrl:
            rows.append(dict(group=r.key, place=c, D=0, **unit(c, pre, post, e)))
    U = pd.DataFrame(rows)
    n0 = len(U)
    need = ["Y", "share5", "job_growth", "rate_before", "trend_before"]
    U0 = U.replace([np.inf, -np.inf], np.nan)
    gone = sorted(set(U0.loc[(U0["D"] == 1) & U0[need].isna().any(axis=1), "place"]))
    names = dict(zip(real["key"], real["place"] + ", " + real["state"]))
    dropped_repeal = "; ".join(names.get(k, k) for k in gone)
    U = U.replace([np.inf, -np.inf], np.nan).dropna(subset=["Y", "share5", "job_growth", "rate_before", "trend_before"])
    X = pd.concat([U[["share5", "job_growth", "rate_before", "trend_before", "event_year"]],
                   pd.get_dummies(U["division"], prefix="div", dtype=float)], axis=1).values
    Y, D = U["Y"].values, U["D"].values.astype(float)
    rY, rD = np.zeros(len(U)), np.zeros(len(U))
    for tr, te in GroupKFold(n_splits=5).split(X, groups=U["place"].values):
        my = RandomForestRegressor(n_estimators=500, min_samples_leaf=5, random_state=SEED, n_jobs=-1).fit(X[tr], Y[tr])
        md = RandomForestRegressor(n_estimators=500, min_samples_leaf=5, random_state=SEED, n_jobs=-1).fit(X[tr], D[tr])
        rY[te], rD[te] = Y[te] - my.predict(X[te]), D[te] - md.predict(X[te])
    out = []
    for lab, w in (("equal-weight", np.ones(len(U))), ("home-weighted", U["homes"].fillna(0).values)):
        theta = np.sum(w * rY * rD) / np.sum(w * rD * rD)
        psi = w * (rY - theta * rD) * rD
        g = pd.Series(psi).groupby(U["place"].values).sum().values
        se = np.sqrt(np.sum(g ** 2)) / np.sum(w * rD * rD)
        out.append(dict(test=f"FU4 DML effect of repeal, {lab}", estimate=theta, p05=theta - 1.645 * se, p95=theta + 1.645 * se,
                        se=se, units=len(U), repeal_places=int(D.sum()), comparison_units=int((D == 0).sum()),
                        note=f"{n0 - len(U)} units dropped for missing X (repeal places: {dropped_repeal}); SE clustered by place"))
    S = pd.DataFrame(out)
    S["unit"] = "permits per 1,000 existing homes a year"
    S.to_csv(REFERENCE / "parking_causal_fu4_dml.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

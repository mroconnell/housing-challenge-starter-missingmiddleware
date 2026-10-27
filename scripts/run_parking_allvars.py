"""Parking all-variables test (docs/parking/ALLVARS_PLAN.md).

    uv run --all-extras python scripts/run_parking_allvars.py

Builds reference/parking_allvars_values.csv (about 70 place-level variables for the 71 repeal places, written
before any model runs), then scores lasso, elastic net, random forest, gradient boosting and an honest causal
forest on left-out places. Output: reference/parking_allvars_models.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_parking_round3_vars as b3  # noqa: E402
import run_parking_expanded as rpe  # noqa: E402
import run_parking_round3 as r3  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

AV = RAW / "census_acs5_2024_tbsf_allvars"
SEED, FOLDS, REPEATS, MIN_GAIN, MIN_REPEATS = 20261027, 10, 20, 0.05, 15


def E(t, *ns):
    return [f"{t}_E{n:03d}" for n in ns]


def share(d, num, den):
    return d[num].sum(axis=1) / d[den]


def acs_vars() -> pd.DataFrame:
    T = lambda f, cols: b3.acs(AV / f"acsdt5y2024-{f}.dat", cols)  # noqa: E731
    r = T("b25017", E("B25017", *range(1, 11)))
    out = pd.DataFrame(index=r.index)
    out["A_rooms_1to3_share"] = share(r, E("B25017", 2, 3, 4), "B25017_E001")
    out["A_rooms_7plus_share"] = share(r, E("B25017", 8, 9, 10), "B25017_E001")
    c = T("b25014", E("B25014", *range(1, 14)))
    out["A_crowded_share"] = share(c, E("B25014", 5, 6, 7, 11, 12, 13), "B25014_E001")
    g = T("b25063", E("B25063", *range(1, 28)))
    out["A_rent_under_1000_share"] = share(g, E("B25063", *range(3, 20)), "B25063_E002")
    out["A_rent_2000plus_share"] = share(g, E("B25063", 23, 24, 25, 26), "B25063_E002")
    b = T("b25070", E("B25070", *range(1, 12)))
    den = b["B25070_E001"] - b["B25070_E011"]
    out["A_rent_burden_30plus"] = b[E("B25070", 7, 8, 9, 10)].sum(axis=1) / den
    out["A_rent_burden_50plus"] = b["B25070_E010"] / den
    v = T("b25075", E("B25075", *range(1, 28)))
    out["A_value_under_200k_share"] = share(v, E("B25075", *range(2, 19)), "B25075_E001")
    out["A_value_500kplus_share"] = share(v, E("B25075", 23, 24, 25, 26, 27), "B25075_E001")
    mo = T("b25081", E("B25081", 1, 2))
    out["A_mortgage_share"] = mo["B25081_E002"] / mo["B25081_E001"]
    out["A_avg_household_size"] = T("b25010", ["B25010_E001"])["B25010_E001"]
    out["A_median_age"] = T("b01002", ["B01002_E001"])["B01002_E001"]
    k = T("b11005", E("B11005", 1, 2))
    out["A_households_with_children"] = k["B11005_E002"] / k["B11005_E001"]
    ed = T("b15003", E("B15003", *range(1, 26)))
    out["A_bachelors_plus"] = share(ed, E("B15003", 22, 23, 24, 25), "B15003_E001")
    inc = T("b19001", E("B19001", *range(1, 18)))
    out["A_income_under_35k"] = share(inc, E("B19001", *range(2, 8)), "B19001_E001")
    out["A_income_100kplus"] = share(inc, E("B19001", 14, 15, 16, 17), "B19001_E001")
    out["A_income_200kplus"] = inc["B19001_E017"] / inc["B19001_E001"]
    pv = T("c17002", E("C17002", *range(1, 9)))
    out["A_below_150pct_poverty"] = share(pv, E("C17002", 2, 3, 4, 5), "C17002_E001")
    lf = T("b23025", E("B23025", *range(1, 8)))
    out["A_labour_force_participation"] = lf["B23025_E002"] / lf["B23025_E001"]
    out["A_unemployment"] = lf["B23025_E005"] / lf["B23025_E003"]
    out["A_median_earnings"] = T("b20002", ["B20002_E001"])["B20002_E001"]
    tl = T("b08302", E("B08302", *range(1, 16)))
    out["A_leave_before_7am"] = share(tl, E("B08302", 2, 3, 4, 5, 6), "B08302_E001")
    out["A_leave_7_to_9am"] = share(tl, E("B08302", 7, 8, 9, 10), "B08302_E001")
    out["A_leave_after_9am"] = share(tl, E("B08302", 11, 12, 13, 14, 15), "B08302_E001")
    own = b3.acs(b3.MKT / "acsdt5y2024-b25003.dat", ["B25003_E001", "B25003_E002"])
    out["A_owner_share"] = own["B25003_E002"] / own["B25003_E001"]
    return out


def main() -> None:
    d = r3.data()
    ids = pd.read_csv(REFERENCE / "parking_round3_vars.csv")[["prn_key", "acs_geoid"]]
    d = d.merge(ids, on="prn_key", how="left", suffixes=("", "_v"))
    gcol = "acs_geoid_v" if "acs_geoid_v" in d.columns else "acs_geoid"
    d = d.merge(acs_vars(), left_on=gcol, right_index=True, how="left")
    pop_den = d["population"] / d["land_sqmi"] if "land_sqmi" in d.columns else np.nan
    d["A_people_per_sqmi_log"] = np.log10(pd.to_numeric(pop_den, errors="coerce").where(lambda s: s > 0))
    feats = sorted(set(rpe.FEATURES_US + r3.SINGLE + [c for c in d.columns if c.startswith("A_")]))
    feats = [f for f in feats if f in d.columns and d[f].notna().sum() >= 15 and d[f].nunique() > 1]
    d[["prn_key", "place", "state"] + feats].round(5).to_csv(REFERENCE / "parking_allvars_values.csv", index=False)
    print(len(feats), "variables;", len(d), "places")

    rng = np.random.default_rng(SEED)
    tools = ["one average", "lasso", "elastic net", "random forest", "gradient boosting", "causal forest (honest)"]
    per_repeat = {t: [] for t in tools}
    d = d.reset_index(drop=True)
    for rep in range(REPEATS):
        perm = rng.permutation(len(d))
        errs = {t: [] for t in tools}
        wts = []
        for f in range(FOLDS):
            te = perm[f::FOLDS]
            tr = np.setdiff1d(np.arange(len(d)), te)
            Xtr, Xte = rpe._impute(d.iloc[tr], d.iloc[te], feats)
            ytr, wtr = d["effect"].values[tr], d["weight"].values[tr]
            yte, wte = d["effect"].values[te], d["weight"].values[te]
            for t in tools:
                pr = predict(t, Xtr, ytr, wtr, Xte, rng)
                errs[t].append((np.abs(pr - yte) * wte).sum())
            wts.append(wte.sum())
        for t in tools:
            per_repeat[t].append(sum(errs[t]) / sum(wts))
    base = np.array(per_repeat["one average"])
    rows = []
    for t in tools:
        e = np.array(per_repeat[t])
        rows.append(dict(model=t, error=e.mean(), gain=1 - e.mean() / base.mean(), repeats_beating_average=int((e < base).sum()),
                         variables=len(feats), places=len(d)))
    res = pd.DataFrame(rows)
    res["passes"] = (res["gain"] >= MIN_GAIN) & (res["repeats_beating_average"] >= MIN_REPEATS) & (res["model"] != "one average")
    res.round(4).to_csv(REFERENCE / "parking_allvars_models.csv", index=False)
    print(res.round(3).to_string(index=False))


def predict(tool, Xtr, ytr, wtr, Xte, rng):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import ElasticNetCV
    from sklearn.preprocessing import StandardScaler
    if tool in ("one average", "lasso", "random forest", "causal forest (honest)"):
        return rpe.predict(tool, Xtr, ytr, wtr, Xte, rng)
    sc = StandardScaler().fit(Xtr)
    A, B = sc.transform(Xtr), sc.transform(Xte)
    if tool == "elastic net":
        m = ElasticNetCV(l1_ratio=[0.2, 0.5, 0.8], cv=5, max_iter=20000, random_state=int(rng.integers(1e9)))
        return m.fit(A, ytr, sample_weight=wtr).predict(B)
    if tool == "gradient boosting":
        m = HistGradientBoostingRegressor(max_depth=2, learning_rate=0.05, max_iter=300, early_stopping=True,
                                          validation_fraction=0.2, n_iter_no_change=20, min_samples_leaf=5,
                                          random_state=int(rng.integers(1e9)))
        return m.fit(A, ytr, sample_weight=wtr).predict(B)
    raise ValueError(tool)


if __name__ == "__main__":
    main()

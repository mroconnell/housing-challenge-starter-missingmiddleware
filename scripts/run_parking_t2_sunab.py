"""Parking T2: Sun and Abraham (2021) interaction-weighted event study on the 76 repeal places, never-treated = the union
of their comparison places. docs/parking/CAUSAL_FRAMEWORK_PLAN.md (T2, locked). Cross-check, not a replacement.

    uv run python scripts/run_parking_t2_sunab.py
Output: reference/parking_t2_sunab.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

LEADS, LAGS = range(-5, -1), range(0, 4)


def demean(M: np.ndarray, g1: np.ndarray, g2: np.ndarray, iters: int = 50) -> np.ndarray:
    M = M.astype(float).copy()
    for _ in range(iters):
        for g in (g1, g2):
            s = np.zeros((g.max() + 1, M.shape[1]))
            np.add.at(s, g, M)
            n = np.bincount(g, minlength=g.max() + 1)[:, None]
            M -= (s / np.maximum(n, 1))[g]
    return M


def main() -> None:
    p = cmp.panel(rpc.read_bps_us())
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")]
    excluded |= set(real["key"])
    cohort = dict(zip(real["key"], real["event_year"].astype(int)))
    never = set()
    for r in real.itertuples():
        ctrl, _ = cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)
        never |= set(ctrl)
    keys = sorted((set(cohort) | never) & set(homes.index))
    d = p[p["key"].isin(keys) & p["year"].between(2012, 2025)][["key", "year", "units_total"]].copy()
    d["rate"] = d["units_total"] / d["key"].map(homes) * 1000
    d["logp"] = np.log(d["units_total"] + 0.5)
    d["cohort"] = d["key"].map(cohort)
    d["rel"] = d["year"] - d["cohort"]
    d["rel_b"] = d["rel"].clip(lower=min(LEADS))
    cells = [(c, k) for c in sorted(set(cohort.values())) for k in list(LEADS) + list(LAGS)]
    X = np.zeros((len(d), len(cells)))
    for j, (c, k) in enumerate(cells):
        X[:, j] = ((d["cohort"] == c) & (d["rel_b"] == k)).values
    keep = X.sum(axis=0) > 0
    cells = [c for c, kk in zip(cells, keep) if kk]
    X = X[:, keep]
    gp = pd.factorize(d["key"])[0]
    gy = pd.factorize(d["year"])[0]
    Xd = demean(X, gp, gy)
    out = []
    w_h = d.assign(h=d["key"].map(homes))
    for ycol in ("rate", "logp"):
        y = demean(d[[ycol]].values, gp, gy)[:, 0]
        b, *_ = np.linalg.lstsq(Xd, y, rcond=None)
        e = y - Xd @ b
        XtXi = np.linalg.pinv(Xd.T @ Xd)
        S = np.zeros((Xd.shape[1], Xd.shape[1]))
        for g in np.unique(gp):
            m = gp == g
            s = Xd[m].T @ e[m]
            S += np.outer(s, s)
        V = XtXi @ S @ XtXi
        for wl in ("place-years", "homes"):
            wv = np.zeros(len(cells))
            for j, (c, k) in enumerate(cells):
                if 1 <= k <= 3:
                    m = (d["cohort"] == c) & (d["rel_b"] == k)
                    wv[j] = m.sum() if wl == "place-years" else w_h.loc[m, "h"].sum()
            wv = wv / wv.sum()
            est, se = float(wv @ b), float(np.sqrt(wv @ V @ wv))
            out.append(dict(outcome=ycol, weighting=wl, estimate=est, se=se, p05=est - 1.645 * se, p95=est + 1.645 * se))
        for k in LEADS:
            wv = np.array([float(((d["cohort"] == c) & (d["rel_b"] == kk)).sum()) if kk == k else 0.0 for c, kk in cells])
            if wv.sum():
                wv /= wv.sum()
                est, se = float(wv @ b), float(np.sqrt(wv @ V @ wv))
                out.append(dict(outcome=ycol, weighting=f"lead {k} (pre-trend)", estimate=est, se=se, p05=est - 1.645 * se, p95=est + 1.645 * se))
    S = pd.DataFrame(out)
    S["places_treated"] = len(set(cohort) & set(keys))
    S["places_never_treated"] = len(never & set(keys))
    S["unit"] = S["outcome"].map({"rate": "permits per 1,000 existing homes a year", "logp": "log(yearly permits + 0.5)"})
    S.to_csv(REFERENCE / "parking_t2_sunab.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

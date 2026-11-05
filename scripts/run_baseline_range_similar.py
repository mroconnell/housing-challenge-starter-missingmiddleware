"""Baseline range, round 3: learned "similar states" (docs/shared/BASELINE_RANGE_SIMILAR_PLAN.md).

    uv run --extra ml python scripts/run_baseline_range_similar.py

Same inputs as scripts/run_baseline_bakeoff.py --part 1. Level: L0 (flat 3-year). Each of the 51 states is a held-out
target; for target j and check year t, training is the other 50 states with start years s <= t - 5, traits from data
up to t. Every method is calibrated to 90% on the training states only (inner leave-one-state-out; for E, grouped
out-of-fold predictions), then scored on the target.

Outputs (committed): reference/baseline_range_similar_checks.csv (every target x check year x method),
reference/baseline_range_similar_summary.csv (coverage, bootstrap range, width; other 50, Wisconsin, challenge
states; the pick), reference/baseline_range_similar_wisconsin.csv (Wisconsin 2027-2031 by method).
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_baseline_bakeoff as P1  # noqa: E402
from missing_middleware import baseline_bakeoff as bb  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

warnings.filterwarnings("ignore")
WI = "55"
CHALLENGE = {"04", "09", "15", "33", "41", "42", "44", "47", "49", "51"}   # AZ CT HI NH OR PA RI TN UT VA
CHECKS = tuple(range(2005, 2021))
MAIN = tuple(range(2009, 2021))
Q_GRID = (0.05, 0.04, 0.03, 0.025, 0.02, 0.015, 0.01, 0.005, 0.0)   # quantile pair (q, 1-q), narrowest first
K_GRID = (5, 10, 15, 20, 30)
H_GRID = (0.5, 1.0, 2.0)
TRAITS = ["swing", "pace", "tilt", "apt_share", "own_miss", "reg1", "reg2", "reg3", "reg4"]
METHODS = ("A", "B", "C", "D", "E")
SEED = 20261105


def wquantile(x: np.ndarray, w: np.ndarray, q: float) -> float:
    o = np.argsort(x)
    x, w = x[o], w[o]
    c = np.cumsum(w) - 0.5 * w
    c /= w.sum()
    return float(np.interp(q, c, x))


def build(u, homes, region):
    """Ratios r (actual / predicted five-year all-sizes total, L0) for start years 1992-2025 where outcomes exist,
    and traits for every state and year 1999-2025 from data up to that year."""
    tot = u.groupby(["state", "year"])["units"].sum().unstack()          # state x year
    apt = u[u["size"] == "5plus"].groupby(["state", "year"])["units"].sum().unstack()
    h = homes.pivot(index="state", columns="year", values="homes")
    R = []
    for s in range(1992, 2021):
        pred = tot.loc[:, s - 2:s].mean(axis=1) * 5
        act = tot.loc[:, s + 1:s + 5].sum(axis=1)
        R.append(pd.DataFrame({"state": tot.index, "start": s, "pred": pred.values, "actual": act.values}))
    R = pd.concat(R, ignore_index=True)
    R["lr"] = np.log(R["actual"] / R["pred"])
    T = []
    for t in range(1999, 2026):
        own = R[R.start <= t - 5].groupby("state")["lr"].apply(lambda v: np.abs(v).mean())
        d = pd.DataFrame({
            "swing": np.log(tot.loc[:, 1990:t].clip(lower=1)).std(axis=1),
            "pace": tot.loc[:, t - 2:t].mean(axis=1) / h[t] * 1000,
            "tilt": np.log(tot.loc[:, t - 2:t].mean(axis=1) / tot.loc[:, t - 9:t].mean(axis=1)),
            "apt_share": apt.loc[:, t - 2:t].sum(axis=1) / tot.loc[:, t - 2:t].sum(axis=1),
            "own_miss": own.reindex(tot.index),
        })
        for k in range(1, 5):
            d[f"reg{k}"] = (region.reindex(tot.index).astype(int) == k).astype(float)
        T.append(d.assign(year=t).reset_index())
    T = pd.concat(T, ignore_index=True)
    return R, T


def zscore(train: pd.DataFrame, rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    m, s = train[TRAITS].mean(), train[TRAITS].std().replace(0, 1)
    return ((train[TRAITS] - m) / s).fillna(0).to_numpy(), ((rows[TRAITS] - m) / s).fillna(0).to_numpy()


def pool_interval(lr: np.ndarray, w: np.ndarray | None, q: float) -> tuple[float, float]:
    if w is None:
        return float(np.quantile(lr, q)), float(np.quantile(lr, 1 - q))
    return wquantile(lr, w, q), wquantile(lr, w, 1 - q)


def calibrate_pool(groups: dict, weights_for, inner_states, q_grid=Q_GRID):
    """Narrowest q whose inner leave-one-state-out coverage on the training states is >= 90%. groups: state -> array
    of that state's training log ratios. weights_for(i) -> (pool log ratios, weights or None) excluding i."""
    pools = {i: weights_for(i) for i in inner_states}
    cov, wid = {}, {}
    for q in q_grid:
        hits = n = 0
        widths = []
        for i in inner_states:
            lr, w = pools[i]
            if len(lr) < 5:
                continue
            lo, hi = pool_interval(lr, w, q)
            v = groups[i]
            hits += int(((v >= lo) & (v <= hi)).sum())
            n += len(v)
            widths.append(hi - lo)
        cov[q], wid[q] = hits / n if n else np.nan, np.mean(widths) if widths else np.inf
    ok = [q for q in q_grid if cov[q] >= 0.90]
    best = max(ok) if ok else min(q_grid)            # largest q = narrowest pair
    return best, wid[best]


def interval_for(method, j, t, R, T, region):
    """(lo, hi) on the log-ratio scale for target j at check year t, from training states != j, starts <= t-5."""
    tr = R[(R.state != j) & (R.start <= t - 5)]
    groups = {i: g["lr"].to_numpy() for i, g in tr.groupby("state")}
    states = sorted(groups)
    Tt = T[T.year == t].set_index("state")
    if method == "A":
        allv = tr[["state", "lr"]]
        q, _ = calibrate_pool(groups, lambda i: (allv.loc[allv.state != i, "lr"].to_numpy(), None), states)
        return pool_interval(tr["lr"].to_numpy(), None, q)
    if method == "B":
        # level: narrowest q giving 90% when each training state's own history (leave that value out) is its range
        best = min(Q_GRID)
        for q in sorted(Q_GRID, reverse=True):
            hits = n = 0
            for i in states:
                v = groups[i]
                for m in range(len(v)):
                    rest = np.delete(v, m)
                    if len(rest) < 5:
                        continue
                    lo, hi = np.quantile(rest, q), np.quantile(rest, 1 - q)
                    hits += int(lo <= v[m] <= hi)
                    n += 1
            if n and hits / n >= 0.90:
                best = q
                break
        own = R[(R.state == j) & (R.start <= t - 5)]["lr"].to_numpy()
        return pool_interval(own, None, best)
    Ztr, Zj = zscore(Tt.loc[states].reset_index(), Tt.loc[[j]].reset_index())
    zi = {s: Ztr[k] for k, s in enumerate(states)}
    if method in ("C", "D"):
        grid = K_GRID if method == "C" else H_GRID
        best = None
        for g in grid:
            def wf(i, g=g, base=None):
                others = [s for s in states if s != i]
                d = np.array([np.linalg.norm(zi[s] - zi[i]) for s in others])
                if method == "C":
                    nb = [others[k] for k in np.argsort(d)[:g]]
                    return np.concatenate([groups[s] for s in nb]), None
                w = np.exp(-d ** 2 / (2 * g ** 2))
                return (np.concatenate([groups[s] for s in others]),
                        np.concatenate([np.full(len(groups[s]), wk) for s, wk in zip(others, w)]))
            q, wid = calibrate_pool(groups, wf, states)
            if best is None or wid < best[2]:
                best = (g, q, wid)
        g, q, _ = best
        d = np.array([np.linalg.norm(zi[s] - Zj[0]) for s in states])
        if method == "C":
            nb = [states[k] for k in np.argsort(d)[:g]]
            return pool_interval(np.concatenate([groups[s] for s in nb]), None, q)
        w = np.exp(-d ** 2 / (2 * g ** 2))
        return pool_interval(np.concatenate([groups[s] for s in states]),
                             np.concatenate([np.full(len(groups[s]), wk) for s, wk in zip(states, w)]), q)
    if method == "E":
        from sklearn.linear_model import LassoCV
        from sklearn.model_selection import GroupKFold
        rows = tr.merge(T, left_on=["state", "start"], right_on=["state", "year"], how="inner")
        Zr, Zt = zscore(rows, Tt.loc[[j]].reset_index())
        y = np.log(np.abs(rows["lr"].to_numpy()) + 1e-3)
        grp = rows["state"].to_numpy()
        oof = np.zeros(len(y))
        def lasso(X, yy, gg):   # inner CV folds grouped by state, passed as precomputed splits
            return LassoCV(alphas=100, cv=list(GroupKFold(5).split(X, yy, gg)), max_iter=10000,
                           random_state=SEED).fit(X, yy)
        for a, b in GroupKFold(5).split(Zr, y, grp):
            oof[b] = lasso(Zr[a], y[a], grp[a]).predict(Zr[b])
        score = np.abs(rows["lr"].to_numpy()) / np.exp(oof)
        c = float(np.quantile(score, 0.90))
        m = lasso(Zr, y, grp)
        sig = float(np.exp(m.predict(Zt)[0]))
        return -c * sig, c * sig
    raise ValueError(method)


def main() -> None:
    u, geo = P1.read_state_permits()
    census = P1.read_census()
    allu = u.groupby(["state", "year"], as_index=False)["units"].sum()
    homes = bb.homes_by_year(census, allu, range(1990, 2026))
    region = geo.set_index("state")["region"]
    R, T = build(u, homes, region)
    rows = []
    for t in CHECKS:
        cur = R[R.start == t].set_index("state")
        for j in sorted(cur.index):
            for mth in METHODS:
                lo, hi = interval_for(mth, j, t, R, T, region)
                lr = cur.loc[j, "lr"]
                rows.append(dict(method=mth, state=j, start=t, lo=lo, hi=hi, lr=lr, hit=lo <= lr <= hi, width=hi - lo,
                                 pred=cur.loc[j, "pred"], low=cur.loc[j, "pred"] * np.exp(lo),
                                 high=cur.loc[j, "pred"] * np.exp(hi), actual=cur.loc[j, "actual"]))
        print("check year done:", t, flush=True)
    C = pd.DataFrame(rows)
    draws = bb.block_bootstrap_starts(MAIN)
    S = []
    for mth, g in C.groupby("method"):
        m = g[g.start.isin(MAIN)]
        o = m[m.state != WI]
        per = o.groupby("start")["hit"].mean()
        boot = np.array([per.loc[d].mean() for d in draws])
        w, ch = m[m.state == WI], m[m.state.isin(CHALLENGE)]
        full = g[g.state != WI]
        S.append(dict(method=mth, coverage_other50=o["hit"].mean(), boot_lo=np.quantile(boot, 0.05),
                      boot_hi=np.quantile(boot, 0.95), width_other50=o["width"].mean(),
                      wi_hits=int(w["hit"].sum()), wi_checks=len(w), wi_width=w["width"].mean(),
                      challenge_coverage=ch["hit"].mean(), challenge_width=ch["width"].mean(),
                      coverage_other50_2005_2020=full["hit"].mean(),
                      wi_hits_2005_2020=int(g[g.state == WI]["hit"].sum())))
    S = pd.DataFrame(S)
    ok = S[S.coverage_other50 >= 0.90]
    if ok.empty:
        winner = "A"
    else:
        best = ok["width_other50"].min()
        winner = min(ok[ok.width_other50 <= best + 0.01]["method"], key=METHODS.index)
    S["winner"] = S["method"] == winner
    # Wisconsin 2027-2031: target WI at t = 2025 (training starts <= 2020)
    l0 = float((bb.predict("L0", u, homes, 2025, geo.set_index("state")["division"]) * bb.HORIZON).loc[WI].sum())
    f = 124_000 / l0
    W = []
    for mth in METHODS:
        lo, hi = interval_for(mth, WI, 2025, R, T, region)
        W.append(dict(method=mth, published_central=l0, v3_low=l0 * np.exp(lo) * f, v3_central=124_000.0,
                      v3_high=l0 * np.exp(hi) * f, winner=mth == winner))
    W = pd.DataFrame(W)
    C.round({"lo": 5, "hi": 5, "lr": 5, "width": 5, "pred": 1, "low": 1, "high": 1, "actual": 1}).to_csv(
        REFERENCE / "baseline_range_similar_checks.csv", index=False)
    S.round(4).to_csv(REFERENCE / "baseline_range_similar_summary.csv", index=False)
    W.round(1).to_csv(REFERENCE / "baseline_range_similar_wisconsin.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))
    print(W.round(0).to_string(index=False))


if __name__ == "__main__":
    main()

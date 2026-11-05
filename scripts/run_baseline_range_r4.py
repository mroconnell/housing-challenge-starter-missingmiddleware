"""Baseline range, round 4: tighter 90% ranges (docs/shared/BASELINE_RANGE_R4_PLAN.md).

    uv run --extra ml python scripts/run_baseline_range_r4.py

Builds on scripts/run_baseline_range_similar.py (round 3): same leave-one-state-out design, traits, calibration and
pick rule. Methods A, AT, AR, AL3, ARL3, E, E2.
Outputs (committed): reference/baseline_range_r4_{checks,summary,wisconsin}.csv

E is not recomputed: its round-3 results (same code, same seed; reference/baseline_range_similar_checks.csv and
_wisconsin.csv) are read back. Check years run in parallel processes; tables are built once and passed to workers.
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
import run_baseline_range_similar as R3  # noqa: E402
from missing_middleware import baseline_bakeoff as bb  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

warnings.filterwarnings("ignore")
WI, CHALLENGE, CHECKS, MAIN, SEED = R3.WI, R3.CHALLENGE, R3.CHECKS, R3.MAIN, R3.SEED
METHODS = ("A", "AT", "AR", "AL3", "ARL3", "E", "E2")
H_GRID = (3.0, 5.0, 10.0, np.inf)
C_GRID = tuple(np.round(np.arange(0.05, 20.0001, 0.05), 2))


def l3_table(u, homes, division) -> pd.DataFrame:
    """L3 ratios for start years 1997-2025 (b fitted per start year, no look-ahead), as R3.build's R."""
    rows = []
    for s in range(1997, 2026):
        b = bb.fit_param("L3", u, homes, s, division)
        p = bb.predict("L3", u, homes, s, division, b).groupby(level="state").sum() * bb.HORIZON
        a = u[(u.year > s) & (u.year <= s + 5)].groupby("state")["units"].sum() if s <= 2020 else None
        rows.append(pd.DataFrame({"state": p.index, "start": s, "pred": p.values, "b": b,
                                  "actual": a.reindex(p.index).values if a is not None else np.nan}))
    R = pd.concat(rows, ignore_index=True)
    R["lr"] = np.log(R["actual"] / R["pred"])
    return R


def calib_pool(tr: pd.DataFrame, weight=None) -> tuple[float, float]:
    """Inner leave-one-state-out: the narrowest q with >= 90% coverage; returns (q, mean inner width)."""
    states = sorted(tr.state.unique())
    lr = tr["lr"].to_numpy()
    w = np.ones(len(tr)) if weight is None else weight
    st = tr["state"].to_numpy()
    cov, wid = {}, {}
    for q in R3.Q_GRID:
        hits = n = 0
        widths = []
        for i in states:
            m = st != i
            lo, hi = R3.wquantile(lr[m], w[m], q), R3.wquantile(lr[m], w[m], 1 - q)
            v = lr[~m]
            hits += int(((v >= lo) & (v <= hi)).sum())
            n += len(v)
            widths.append(hi - lo)
        cov[q], wid[q] = hits / n, float(np.mean(widths))
    ok = [q for q in R3.Q_GRID if cov[q] >= 0.90]
    q = max(ok) if ok else min(R3.Q_GRID)
    return q, wid[q]


def recency(tr: pd.DataFrame, t: int, h: float) -> np.ndarray:
    return np.ones(len(tr)) if np.isinf(h) else 0.5 ** ((t - 5 - tr["start"].to_numpy()) / h)


def pooled_interval(tr: pd.DataFrame, t: int, recent: bool) -> tuple[float, float, float | None]:
    if not recent:
        q, _ = calib_pool(tr)
        return R3.wquantile(tr.lr.to_numpy(), np.ones(len(tr)), q), R3.wquantile(tr.lr.to_numpy(), np.ones(len(tr)), 1 - q), None
    best = None
    for h in H_GRID:
        w = recency(tr, t, h)
        q, wid = calib_pool(tr, w)
        if best is None or wid < best[2] - 1e-12:
            best = (h, q, wid)
    h, q, _ = best
    w = recency(tr, t, h)
    return R3.wquantile(tr.lr.to_numpy(), w, q), R3.wquantile(tr.lr.to_numpy(), w, 1 - q), h


def e2_interval(tr: pd.DataFrame, T: pd.DataFrame, j: str, t: int) -> tuple[float, float]:
    from sklearn.linear_model import LassoCV
    from sklearn.model_selection import GroupKFold
    rows = tr.merge(T, left_on=["state", "start"], right_on=["state", "year"], how="inner")
    Tt = T[T.year == t].set_index("state")
    Zr, Zt = R3.zscore(rows, Tt.loc[[j]].reset_index())
    y = np.log(np.maximum(np.abs(rows["lr"].to_numpy()), 0.02))
    grp = rows["state"].to_numpy()

    def lasso(X, yy, gg):
        return LassoCV(alphas=100, cv=list(GroupKFold(5).split(X, yy, gg)), max_iter=10000, random_state=SEED).fit(X, yy)

    oof = np.zeros(len(y))
    for a, b in GroupKFold(10).split(Zr, y, grp):
        oof[b] = lasso(Zr[a], y[a], grp[a]).predict(Zr[b])
    lo_cap, hi_cap = np.quantile(oof, 0.01), np.quantile(oof, 0.99)
    sig_oof = np.exp(np.clip(oof, lo_cap, hi_cap))
    absr = np.abs(rows["lr"].to_numpy())
    c = next((c for c in C_GRID if np.mean(absr <= c * sig_oof) >= 0.90), C_GRID[-1])
    sig = float(np.exp(np.clip(lasso(Zr, y, grp).predict(Zt)[0], lo_cap, hi_cap)))
    return -c * sig, c * sig


def interval(method: str, j: str, t: int, R0: pd.DataFrame, RL3: pd.DataFrame, T: pd.DataFrame, region):
    R = RL3 if method in ("AL3", "ARL3") else R0
    tr = R[(R.state != j) & (R.start <= t - 5)].dropna(subset=["lr"])
    if method == "A" or method == "AL3":
        lo, hi, _ = pooled_interval(tr, t, recent=False)
        return lo, hi, None
    if method in ("AR", "ARL3"):
        return pooled_interval(tr, t, recent=True)
    if method == "AT":
        sw = T[(T.year == t) & (T.state.isin(tr.state.unique()))].set_index("state")["swing"]
        q1, q3 = sw.quantile([0.25, 0.75])
        keep = sw[sw <= q3 + 3 * (q3 - q1)].index
        lo, hi, _ = pooled_interval(tr[tr.state.isin(keep)], t, recent=False)
        return lo, hi, len(sw) - len(keep)
    if method == "E":
        lo, hi = R3.interval_for("E", j, t, R0, T, region)
        return lo, hi, None
    if method == "E2":
        lo, hi = e2_interval(tr, T, j, t)
        return lo, hi, None
    raise ValueError(method)


_G = {}


def _init(R0, RL3, T, region):
    _G.update(R0=R0, RL3=RL3, T=T, region=region)


def _one_year(t):
    R0, RL3, T, region = _G["R0"], _G["RL3"], _G["T"], _G["region"]
    out = []
    for mth in METHODS:
        if mth == "E":
            continue
        R = RL3 if mth in ("AL3", "ARL3") else R0
        cur = R[R.start == t].set_index("state")
        for j in sorted(cur.index):
            lo, hi, extra = interval(mth, j, t, R0, RL3, T, region)
            lr = cur.loc[j, "lr"]
            out.append(dict(method=mth, state=j, start=t, lo=lo, hi=hi, lr=lr, hit=lo <= lr <= hi, width=hi - lo,
                            extra=extra, pred=cur.loc[j, "pred"], actual=cur.loc[j, "actual"]))
    return out


def main() -> None:
    import concurrent.futures as cf
    u, geo = P1.read_state_permits()
    census = P1.read_census()
    allu = u.groupby(["state", "year"], as_index=False)["units"].sum()
    homes = bb.homes_by_year(census, allu, range(1990, 2026))
    region, division = geo.set_index("state")["region"], geo.set_index("state")["division"]
    R0, T = R3.build(u, homes, region)
    RL3 = l3_table(u, homes, division)
    print("tables built", flush=True)
    rows = []
    with cf.ProcessPoolExecutor(max_workers=8, initializer=_init, initargs=(R0, RL3, T, region)) as ex:
        for t, out in zip(CHECKS, ex.map(_one_year, CHECKS)):
            rows += out
            print("check year done:", t, flush=True)
    e3 = pd.read_csv(REFERENCE / "baseline_range_similar_checks.csv", dtype={"state": str})
    e3 = e3[e3.method == "E"][["method", "state", "start", "lo", "hi", "lr", "hit", "width", "pred", "actual"]]
    C = pd.concat([pd.DataFrame(rows), e3], ignore_index=True)
    draws = bb.block_bootstrap_starts(MAIN)
    S = []
    for mth in METHODS:
        g = C[C.method == mth]
        m = g[g.start.isin(MAIN)]
        o = m[m.state != WI]
        per = o.groupby("start")["hit"].mean()
        boot = np.array([per.loc[d].mean() for d in draws])
        w, ch = m[m.state == WI], m[m.state.isin(CHALLENGE)]
        S.append(dict(method=mth, coverage_other50=o.hit.mean(), boot_lo=np.quantile(boot, 0.05),
                      boot_hi=np.quantile(boot, 0.95), width_other50=o.width.mean(), median_width_other50=o.width.median(),
                      wi_hits=int(w.hit.sum()), wi_checks=len(w), wi_width=w.width.mean(),
                      challenge_coverage=ch.hit.mean(), challenge_checks=len(ch), challenge_width=ch.width.mean(),
                      coverage_other50_2005_2020=g[g.state != WI].hit.mean(), wi_hits_2005_2020=int(g[g.state == WI].hit.sum())))
    S = pd.DataFrame(S)
    ok = S[S.coverage_other50 >= 0.90]
    winner = "A" if ok.empty else min(ok[ok.width_other50 <= ok.width_other50.min() + 0.01]["method"], key=METHODS.index)
    S["winner"] = S.method == winner
    # Wisconsin 2027-2031 (t = 2025; training starts <= 2020)
    l0 = float((bb.predict("L0", u, homes, 2025, division) * bb.HORIZON).loc[WI].sum())
    l3 = float(RL3[(RL3.state == WI) & (RL3.start == 2025)]["pred"].iloc[0])
    f = 124_000 / l0
    W = []
    w3 = pd.read_csv(REFERENCE / "baseline_range_similar_wisconsin.csv").set_index("method")
    for mth in METHODS:
        if mth == "E":
            lo, hi, extra = np.log(w3.loc["E", "v3_low"] / 124_000), np.log(w3.loc["E", "v3_high"] / 124_000), None
        else:
            lo, hi, extra = interval(mth, WI, 2025, R0, RL3, T, region)
        cen = l3 if mth in ("AL3", "ARL3") else l0
        W.append(dict(method=mth, published_central=cen, v3_central=cen * f, v3_low=cen * np.exp(lo) * f,
                      v3_high=cen * np.exp(hi) * f, extra=extra, winner=mth == winner))
    W = pd.DataFrame(W)
    C.round({"lo": 5, "hi": 5, "lr": 5, "width": 5, "pred": 1, "actual": 1}).to_csv(REFERENCE / "baseline_range_r4_checks.csv", index=False)
    S.round(4).to_csv(REFERENCE / "baseline_range_r4_summary.csv", index=False)
    W.round({"published_central": 1, "v3_central": 1, "v3_low": 1, "v3_high": 1}).to_csv(REFERENCE / "baseline_range_r4_wisconsin.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))
    print(W.round(0).to_string(index=False))


if __name__ == "__main__":
    main()

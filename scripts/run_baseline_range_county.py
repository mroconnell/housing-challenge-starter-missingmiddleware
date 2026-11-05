"""County test of the LASSO's tight ranges (docs/shared/BASELINE_RANGE_COUNTY_PLAN.md).

    uv run --extra ml python scripts/run_baseline_range_county.py

Inputs: national Census county permit files 1990-2025 already on disk (see the plan). No homes data.
Outputs (committed): reference/baseline_range_county_checks.csv, reference/baseline_range_county_summary.csv
"""
from __future__ import annotations

import concurrent.futures as cf
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_baseline_range_similar as R3  # noqa: E402
from missing_middleware import baseline_bakeoff as bb  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

warnings.filterwarnings("ignore")
SEED, MAIN, CHECKS = 20261105, tuple(range(2009, 2021)), tuple(range(2005, 2021))
MIN_3YR = 900
TRAITS = ["swing", "loglevel", "tilt", "apt_share", "own_miss", "reg1", "reg2", "reg3", "reg4"]
C_GRID = tuple(np.round(np.arange(0.05, 20.0001, 0.05), 2))
BINS = [(-np.inf, 1.1), (1.1, 1.3), (1.3, 1.5), (1.5, np.inf)]
UNIT_COLS = (7, 10, 13, 16)          # units in 1, 2, 3-4, 5+ unit buildings (estimate columns)
STATES = {f"{i:02d}" for i in range(1, 57)} - {"03", "07", "14", "43", "52"}


def county_file(y: int) -> Path:
    if y < 2000:
        return RAW / "baseline_bakeoff" / "bps_county" / f"co{y}a.txt"
    if y < 2015:
        return RAW / "census_bps_cbsa" / f"co{y}a.txt"
    return RAW / "census_bps_county" / f"co{y}a.txt"


def read_counties() -> pd.DataFrame:
    rows = []
    for y in range(1990, 2026):
        for ln in county_file(y).read_text(errors="ignore").splitlines()[2:]:
            p = [x.strip() for x in ln.split(",")]
            if len(p) < 17 or p[1] not in STATES or not p[2].isdigit():
                continue
            v = [float(p[i]) for i in UNIT_COLS]
            rows.append(dict(county=p[1] + p[2], state=p[1], region=p[3], year=y, total=sum(v), apt=v[3]))
    return pd.DataFrame(rows).drop_duplicates(["county", "year"])


def build(d: pd.DataFrame):
    tot = d.pivot(index="county", columns="year", values="total")
    apt = d.pivot(index="county", columns="year", values="apt")
    st = d.drop_duplicates("county").set_index("county")["state"]
    reg = d.drop_duplicates("county").set_index("county")["region"]
    R = []
    for s in range(1992, 2021):
        w3 = tot.loc[:, s - 2:s]
        ok = w3.notna().all(axis=1) & (w3.sum(axis=1) >= MIN_3YR) & tot.loc[:, s + 1:s + 5].notna().all(axis=1)
        pred = w3.mean(axis=1) * 5
        act = tot.loc[:, s + 1:s + 5].sum(axis=1)
        r = pd.DataFrame({"county": tot.index, "start": s, "pred": pred.values, "actual": act.values})[ok.values]
        R.append(r)
    R = pd.concat(R, ignore_index=True)
    R["lr"] = np.log(R["actual"].clip(lower=1) / R["pred"])
    R["state"] = R["county"].map(st)
    T = []
    for t in range(1999, 2021):
        own = R[R.start <= t - 5].groupby("county")["lr"].apply(lambda v: np.abs(v).mean())
        x = pd.DataFrame({
            "swing": np.log(tot.loc[:, 1990:t].clip(lower=1)).std(axis=1),
            "loglevel": np.log(tot.loc[:, t - 2:t].mean(axis=1).clip(lower=1)),
            "tilt": np.log(tot.loc[:, t - 2:t].mean(axis=1).clip(lower=1) / tot.loc[:, t - 9:t].mean(axis=1).clip(lower=1)),
            "apt_share": apt.loc[:, t - 2:t].sum(axis=1) / tot.loc[:, t - 2:t].sum(axis=1).replace(0, np.nan),
            "own_miss": own.reindex(tot.index),
        })
        for k in range(1, 5):
            x[f"reg{k}"] = (reg.reindex(tot.index).astype(int) == k).astype(float)
        T.append(x.assign(year=t).reset_index())
    return R, pd.concat(T, ignore_index=True)


_G = {}


def _init(R, T):
    _G.update(R=R, T=T)


def zscore(train, rows):
    m, s = train[TRAITS].mean(), train[TRAITS].std().replace(0, 1)
    return ((train[TRAITS] - m) / s).fillna(0).to_numpy(), ((rows[TRAITS] - m) / s).fillna(0).to_numpy()


def e2(tr, tg):
    from sklearn.linear_model import LassoCV
    from sklearn.model_selection import GroupKFold
    Zr, Zt = zscore(tr, tg)
    y = np.log(np.maximum(np.abs(tr["lr"].to_numpy()), 0.02))
    grp = tr["state"].to_numpy()

    def lasso(X, yy, gg):
        return LassoCV(alphas=100, cv=list(GroupKFold(5).split(X, yy, gg)), max_iter=10000, random_state=SEED).fit(X, yy)

    oof = np.zeros(len(y))
    for a, b in GroupKFold(10).split(Zr, y, grp):
        oof[b] = lasso(Zr[a], y[a], grp[a]).predict(Zr[b])
    lo_cap, hi_cap = np.quantile(oof, 0.01), np.quantile(oof, 0.99)
    sig_oof = np.exp(np.clip(oof, lo_cap, hi_cap))
    absr = np.abs(tr["lr"].to_numpy())
    c = next((c for c in C_GRID if np.mean(absr <= c * sig_oof) >= 0.90), C_GRID[-1])
    sig = np.exp(np.clip(lasso(Zr, y, grp).predict(Zt), lo_cap, hi_cap))
    return -c * sig, c * sig


def pooled(tr):
    lr, st = tr["lr"].to_numpy(), tr["state"].to_numpy()
    for q in R3.Q_GRID:            # narrowest first
        hits = n = 0
        for i in np.unique(st):
            m = st != i
            lo, hi = np.quantile(lr[m], q), np.quantile(lr[m], 1 - q)
            v = lr[~m]
            hits += int(((v >= lo) & (v <= hi)).sum())
            n += len(v)
        if hits / n >= 0.90:
            return float(np.quantile(lr, q)), float(np.quantile(lr, 1 - q)), q
    q = min(R3.Q_GRID)
    return float(np.quantile(lr, q)), float(np.quantile(lr, 1 - q)), q


def one(job):
    j, t = job
    R, T = _G["R"], _G["T"]
    tr = R[(R.state != j) & (R.start <= t - 5)].merge(T, left_on=["county", "start"], right_on=["county", "year"])
    cur = R[(R.state == j) & (R.start == t)]
    if cur.empty or tr.empty:
        return []
    tg = cur.merge(T[T.year == t], on="county", how="left")
    elo, ehi = e2(tr, tg)
    alo, ahi, q = pooled(tr)
    out = []
    for k, r in enumerate(tg.itertuples()):
        out.append(dict(method="E2", county=r.county, state=j, start=t, lo=elo[k], hi=ehi[k], lr=r.lr,
                        hit=elo[k] <= r.lr <= ehi[k], width=ehi[k] - elo[k]))
        out.append(dict(method="A", county=r.county, state=j, start=t, lo=alo, hi=ahi, lr=r.lr,
                        hit=alo <= r.lr <= ahi, width=ahi - alo))
    return out


def boot_cov(df, draws_years, n_draws=2000, seed=SEED):
    """Coverage with a bootstrap over states (with all their counties) crossed with 5-year blocks of years."""
    rng = np.random.default_rng(seed)
    g = df.groupby(["state", "start"])["hit"].agg(["sum", "size"])
    states = sorted(df["state"].unique())
    vals = []
    for d in range(n_draws):
        ss = rng.choice(states, size=len(states), replace=True)
        yy = draws_years[d]
        num = den = 0
        for s in ss:
            for y in yy:
                if (s, y) in g.index:
                    num += g.loc[(s, y), "sum"]
                    den += g.loc[(s, y), "size"]
        if den:
            vals.append(num / den)
    return np.quantile(vals, 0.05), np.quantile(vals, 0.95)


def main() -> None:
    d = read_counties()
    R, T = build(d)
    print("rows", len(R), "counties", R.county.nunique(), flush=True)
    jobs = [(j, t) for t in CHECKS for j in sorted(R.state.unique())]
    rows = []
    with cf.ProcessPoolExecutor(max_workers=8, initializer=_init, initargs=(R, T)) as ex:
        for k, out in enumerate(ex.map(one, jobs, chunksize=4)):
            rows += out
            if k % 51 == 50:
                print("jobs done:", k + 1, flush=True)
    C = pd.DataFrame(rows)
    draws = bb.block_bootstrap_starts(MAIN, n_draws=2000)
    S = []
    m = C[C.start.isin(MAIN)]
    for mth in ("E2", "A"):
        g = m[m.method == mth]
        lo, hi = boot_cov(g, draws)
        w = g[g.state == "55"]
        S.append(dict(method=mth, bin="all", checks=len(g), counties=g.county.nunique(), states=g.state.nunique(),
                      coverage=g.hit.mean(), boot_lo=lo, boot_hi=hi, mean_width=g.width.mean(),
                      median_width=g.width.median(), wi_checks=len(w), wi_coverage=w.hit.mean() if len(w) else np.nan,
                      coverage_2005_2020=C[C.method == mth].hit.mean()))
    e = m[m.method == "E2"]
    for a, b in BINS:
        g = e[(e.width > a) & (e.width <= b)]
        lo, hi = boot_cov(g, draws) if len(g) else (np.nan, np.nan)
        label = f"{a}-{b}"
        if a != -np.inf:
            reading = ""
        elif len(g) < 100 or g.state.nunique() < 10:
            reading = "too few"
        elif hi < 0.90:
            reading = "below 90%"
        elif lo > 0.90:
            reading = "above 90%"
        else:
            reading = "consistent with 90%" + (" (weak: range over 20 points)" if hi - lo > 0.20 else "")
        S.append(dict(method="E2", bin=label, checks=len(g), counties=g.county.nunique(), states=g.state.nunique(),
                      coverage=g.hit.mean() if len(g) else np.nan, boot_lo=lo, boot_hi=hi,
                      mean_width=g.width.mean(), median_width=g.width.median(), reading=reading))
    S = pd.DataFrame(S)
    C.round({"lo": 5, "hi": 5, "lr": 5, "width": 5}).to_csv(REFERENCE / "baseline_range_county_checks.csv", index=False)
    S.round(4).to_csv(REFERENCE / "baseline_range_county_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

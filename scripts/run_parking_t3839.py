"""Parking tests 38/39: count models (negative binomial / Poisson) on a place-year panel with place and year fixed effects.
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("C1/C2 final rules" and "lock additions", locked 2026-11-03).

Phase 1 (blind):  uv run python scripts/run_parking_t3839.py blind   -> prints widths, checks, calibration; no centres
Phase 2 (reveal): uv run python scripts/run_parking_t3839.py reveal  -> prints centres of every version
Outputs: reference/parking_t3839_blind.csv (phase 1), reference/parking_t3839_results.csv (phase 2);
fitted centres are kept unprinted in data/processed/parking_t3839/ until phase 2.
"""
from __future__ import annotations

import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402

SEED, DRAWS, CAL_DRAWS, CAL_BOOT = 20261104, 2000, 200, 199
ALPHAS = [0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
WI_BASE = {"5plus_units": 46_905.0, "units_total": 116_600.0, "5plus_bldgs": np.nan, "b24": np.nan}
CUR_WIDTH, BAR = 35_052.0, 26_289.0
OUT = PROCESSED / "parking_t3839"
VERSIONS = [  # (id, outcome column, model, role)
    ("C1-NB-5plus", "5plus_units", "nb", "candidate"), ("C1-P-5plus", "5plus_units", "poisson", "candidate"),
    ("C1-NB-all", "units_total", "nb", "candidate"), ("C1-P-all", "units_total", "poisson", "beside"),
    ("C2-NB-5plus-bldgs", "5plus_bldgs", "nb", "beside (never the lines)"), ("C2-NB-2to4-bldgs", "b24", "nb", "beside (never the lines)")]


# ---------------------------------------------------------------------------------------------- estimator
def unit_fe(y, mu0, unit, n, alpha, a=None, iters=25):
    if a is None:
        a = np.log((np.bincount(unit, y, n) + 1e-9) / (np.bincount(unit, mu0, n) + 1e-12))
    for _ in range(iters):
        mu = mu0 * np.exp(a[unit])
        g = np.bincount(unit, (y - mu) / (1 + alpha * mu), n)
        h = np.bincount(unit, mu * (1 + alpha * y) / (1 + alpha * mu) ** 2, n)
        step = g / np.maximum(h, 1e-12)
        a += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return a


def fit(y, off, unit, X, alpha, init=None, iters=60):
    """Joint ML for place effects (concentrated) and coefficients on X (year dummies + treatment terms)."""
    n = unit.max() + 1
    b = np.zeros(X.shape[1]) if init is None else init.copy()
    a = None
    for _ in range(iters):
        a = unit_fe(y, np.exp(off + X @ b), unit, n, alpha, a)
        eta = off + a[unit] + X @ b
        mu = np.exp(eta)
        w = mu / (1 + alpha * mu)
        z = X @ b + (y - mu) / mu
        sw = np.sqrt(w)
        # within-unit weighted demeaning, so the place effects are partialled out of the step
        wu = np.bincount(unit, w, n)
        Xd = X - (np.vstack([np.bincount(unit, w * X[:, j], n) for j in range(X.shape[1])]).T / np.maximum(wu, 1e-12)[:, None])[unit]
        zd = z - (np.bincount(unit, w * z, n) / np.maximum(wu, 1e-12))[unit]
        nb = np.linalg.lstsq(Xd * sw[:, None], zd * sw, rcond=None)[0]
        if np.max(np.abs(nb - b)) < 1e-7:
            b = nb
            break
        b = nb
    a = unit_fe(y, np.exp(off + X @ b), unit, n, alpha, a)
    mu = np.exp(off + a[unit] + X @ b)
    return b, a, mu


def loglik(y, mu, alpha):
    if alpha <= 0:
        return float(np.sum(y * np.log(np.maximum(mu, 1e-300)) - mu - gammaln(y + 1)))
    r = 1 / alpha
    return float(np.sum(gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(r / (r + mu)) + y * np.log(np.maximum(mu, 1e-300) / (r + mu))))


def cluster_se(y, mu, unit, X, alpha, j):
    """Sandwich SE for coefficient j, clustered by place, on within-demeaned design."""
    n = unit.max() + 1
    w = mu / (1 + alpha * mu)
    wu = np.bincount(unit, w, n)
    Xd = X - (np.vstack([np.bincount(unit, w * X[:, k], n) for k in range(X.shape[1])]).T / np.maximum(wu, 1e-12)[:, None])[unit]
    H = (Xd * w[:, None]).T @ Xd
    s = Xd * ((y - mu) / (1 + alpha * mu))[:, None]
    G = np.vstack([np.bincount(unit, s[:, k], n) for k in range(X.shape[1])]).T
    V = np.linalg.pinv(H) @ (G.T @ G) @ np.linalg.pinv(H)
    return float(np.sqrt(max(V[j, j], 0)))


# ---------------------------------------------------------------------------------------------- data
def load():
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    b["b24"] = b["2units_bldgs"] + b["3_4units_bldgs"]
    keep = b[["key", "year", "5plus_units", "5plus_bldgs", "b24", "1unit_units"]]
    tot = p[["key", "year", "units_total"]].drop_duplicates(["key", "year"])
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    excluded |= set(real["key"])
    t1 = pd.read_csv(REFERENCE / "parking_t1_places.csv")
    excluded_t1 = excluded | set(t1["key"])
    pools, t1pools = set(), set()
    for r in real.itertuples():
        pools |= set(cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)[0])
    for r in t1.itertuples():
        t1pools |= set(cmp.controls(p, r.key, int(r.event_year), excluded_t1 - {r.key}, homes, popn)[0])
    panel = keep.merge(tot, on=["key", "year"], how="left")
    panel = panel[panel["year"].between(2012, 2025)]
    return panel, homes, real, t1, sorted(pools & set(homes.index)), sorted(t1pools & set(homes.index))


def design(panel, homes, treated: pd.DataFrame, controls, col, leads=False):
    """treated: key, event_year, n_post. Returns arrays y, off, unit, X, j (treat column), keys per unit."""
    rows = []
    tset = {}
    for r in treated.itertuples():
        pre, post = cmp.windows(int(r.event_year))
        post = post[: int(r.n_post)]
        tset[r.key] = (int(r.event_year), set(pre), set(post))
    d = panel[panel["key"].isin(set(tset) | set(controls))].copy()
    d = d[d["key"].isin(homes.index)]
    ev = d["key"].map(lambda k: tset[k][0] if k in tset else np.nan)
    inwin = [((y in tset[k][1]) or (y in tset[k][2])) if k in tset else True for k, y in zip(d["key"], d["year"])]
    d = d[np.array(inwin)].copy()
    ev = ev.loc[d.index]
    d["treat"] = [int(k in tset and y in tset[k][2]) for k, y in zip(d["key"], d["year"])]
    d["y"] = d[col].fillna(0).clip(lower=0).astype(float)
    tot = d.groupby("key")["y"].transform("sum")
    dropped = int(d.loc[tot == 0, "key"].nunique())
    d = d[tot > 0]
    ev = ev.loc[d.index]
    years = sorted(d["year"].unique())
    Y = np.column_stack([(d["year"] == yy).values.astype(float) for yy in years[1:]])
    cols = [Y, d["treat"].values[:, None].astype(float)]
    if leads:
        for k in (-5, -4, -3, -2):
            cols.append(((d["year"] - ev) == k).fillna(False).values[:, None].astype(float))
    X = np.hstack(cols)
    unit, keys = pd.factorize(d["key"])
    off = np.log(d["key"].map(homes).values / 1000)
    return dict(y=d["y"].values, off=off, unit=unit, X=X, j=Y.shape[1], keys=np.asarray(keys),
                treated_units=np.array([k in tset for k in keys]), dropped=dropped, n_lead=4 if leads else 0)


def subset(D, idx_units):
    """Bootstrap: rebuild arrays from a list of unit indices (duplicates become new units)."""
    rows = [np.where(D["unit"] == u)[0] for u in idx_units]
    sel = np.concatenate(rows)
    newu = np.concatenate([np.full(len(r), i) for i, r in enumerate(rows)])
    return D["y"][sel], D["off"][sel], newu, D["X"][sel]


def boot_once(args):
    D, alpha, b0, seed, ndraw = args
    rng = np.random.default_rng(seed)
    tu, cu = np.where(D["treated_units"])[0], np.where(~D["treated_units"])[0]
    out = []
    for _ in range(ndraw):
        idx = np.concatenate([rng.choice(tu, len(tu)), rng.choice(cu, len(cu))])
        y, off, unit, X = subset(D, idx)
        b, _, _ = fit(y, off, unit, X, alpha, init=b0, iters=40)
        out.append(b[D["j"]])
    return out


def boot(D, alpha, b0, draws, seed, workers=8):
    chunks = [(D, alpha, b0, seed + i, draws // workers + (1 if i < draws % workers else 0)) for i in range(workers)]
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(boot_once, chunks))
    return np.concatenate([np.array(r) for r in res])


def fit_version(D, model):
    if model == "poisson":
        b, _, mu = fit(D["y"], D["off"], D["unit"], D["X"], 0.0)
        return b, 0.0, mu
    best = None
    for a in ALPHAS:
        b, _, mu = fit(D["y"], D["off"], D["unit"], D["X"], a)
        ll = loglik(D["y"], mu, a)
        if best is None or ll > best[3]:
            best = (b, a, mu, ll)
    return best[0], best[1], best[2]


def check_ci(D, model):
    b, alpha, mu = fit_version(D, model)
    out = []
    for j in ([D["j"]] + [D["j"] + 1 + k for k in range(D["n_lead"])]):
        se = cluster_se(D["y"], mu, D["unit"], D["X"], alpha, j)
        out.append((np.exp(b[j] - 1.645 * se) <= 1 <= np.exp(b[j] + 1.645 * se)))
    return out


def calibrate(panel, homes, real, controls, col, model, alpha):
    rng = np.random.default_rng(SEED + 99)
    cover = 0
    ctrl = np.array(controls)
    for i in range(CAL_DRAWS):
        fake = rng.choice(ctrl, len(real), replace=False)
        ev = rng.choice(real["event_year"].astype(int).values, len(real))
        npost = [len(cmp.windows(int(e))[1][:3]) for e in ev]
        tr = pd.DataFrame({"key": fake, "event_year": ev, "n_post": npost})
        rest = [c for c in ctrl if c not in set(fake)]
        D = design(panel, homes, tr, rest, col)
        b, _, _ = fit(D["y"], D["off"], D["unit"], D["X"], alpha)
        bs = boot(D, alpha, b, CAL_BOOT, SEED + 1000 + i)
        lo, hi = np.percentile(bs, [5, 95])
        cover += int(lo <= 0 <= hi)
        if (i + 1) % 20 == 0:
            print(f"  calibration {model} {col}: {i + 1}/{CAL_DRAWS}", flush=True)
    return cover / CAL_DRAWS


def blind():
    OUT.mkdir(parents=True, exist_ok=True)
    panel, homes, real, t1, pools, t1pools = load()
    rows, hidden = [], {}
    for vid, col, model, role in VERSIONS:
        D = design(panel, homes, real, pools, col)
        b, alpha, _ = fit_version(D, model)
        bs = boot(D, alpha, b, DRAWS, SEED)
        lo, hi = np.percentile(bs, [5, 95])
        hidden[vid] = dict(b=float(b[D["j"]]), lo=float(lo), hi=float(hi), alpha=alpha, p0125=float(np.percentile(bs, 1.25)),
                           p9875=float(np.percentile(bs, 98.75)))
        width = (np.exp(hi) - np.exp(lo)) * WI_BASE[col] if np.isfinite(WI_BASE[col]) else np.nan
        r = dict(version=vid, outcome=col, model=model, role=role, alpha=alpha, places=int(D["treated_units"].sum()),
                 units=int(D["unit"].max() + 1), units_dropped_all_zero=D["dropped"], wi_width_90=width,
                 width_passes_bar=bool(width <= BAR) if np.isfinite(width) else None)
        if role == "candidate":
            Dl = design(panel, homes, real, pools, col, leads=True)
            r["pretrend_leads_include_1"] = all(check_ci(Dl, model)[1:])
            Dp = design(panel, homes, real, pools, "1unit_units")
            r["placebo_single_family_includes_1"] = check_ci(Dp, model)[0]
            Dt = design(panel, homes, t1, t1pools, col)
            r["placebo_t1_includes_1"] = check_ci(Dt, model)[0]
            ok = r["width_passes_bar"] and r["pretrend_leads_include_1"] and r["placebo_single_family_includes_1"] and r["placebo_t1_includes_1"]
            r["calibration_coverage"] = calibrate(panel, homes, real, pools, col, model, alpha) if ok else np.nan
            r["passes_all"] = bool(ok and 0.85 <= r["calibration_coverage"] <= 0.95)
        rows.append(r)
        print(vid, "width", None if not np.isfinite(width) else round(width), flush=True)
    B = pd.DataFrame(rows)
    B.to_csv(REFERENCE / "parking_t3839_blind.csv", index=False)
    (OUT / "hidden_centres.pkl").write_bytes(pickle.dumps(hidden))
    pd.set_option("display.width", 250)
    print(B.round(1).to_string(index=False))


def reveal():
    hidden = pickle.loads((OUT / "hidden_centres.pkl").read_bytes())
    B = pd.read_csv(REFERENCE / "parking_t3839_blind.csv")
    rows = []
    for r in B.itertuples():
        h = hidden[r.version]
        base = WI_BASE[r.outcome]
        rows.append(dict(version=r.version, outcome=r.outcome, model=r.model, role=r.role, rate_ratio=np.exp(h["b"]),
                         p05=np.exp(h["lo"]), p95=np.exp(h["hi"]), p0125=np.exp(h["p0125"]), p9875=np.exp(h["p9875"]),
                         wi_center=(np.exp(h["b"]) - 1) * base if np.isfinite(base) else np.nan,
                         wi_p05=(np.exp(h["lo"]) - 1) * base if np.isfinite(base) else np.nan,
                         wi_p95=(np.exp(h["hi"]) - 1) * base if np.isfinite(base) else np.nan, wi_width_90=r.wi_width_90))
    R = pd.DataFrame(rows)
    R.to_csv(REFERENCE / "parking_t3839_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.round(3).to_string(index=False))


if __name__ == "__main__":
    {"blind": blind, "reveal": reveal}[sys.argv[1]]()

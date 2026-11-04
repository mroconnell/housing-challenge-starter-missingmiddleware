"""Parking method 2 (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Method 2", locked 2026-11-04).

    uv run --all-extras python scripts/run_parking_method2.py --stage 1   # market-heat bake-off on fake repeals only
    git add reference/parking_method2_pick.csv && git commit ...           # the pick must be committed first
    uv run --all-extras python scripts/run_parking_method2.py --stage 2   # real run, switch-backs, backtest, weight test

Stage 1 writes reference/parking_method2_bakeoff.csv and parking_method2_pick.csv and reads no real-repeal outcome
beyond the 76 cases' event years, sizes and after-year counts (used to draw matching fake cases).
Stage 2 refuses to start unless the pick file is committed and unchanged, and the lock names the main-weight rule.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import multiprocessing as mp
import subprocess
import sys
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_parking_comparison as rpc  # noqa: E402
import run_parking_salvage as rps  # noqa: E402
import run_parking_t45_t46 as t46  # noqa: E402
from missing_middleware.dbf import read_shapefile_attributes  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED = 20261104
N_MATCH, MIN_POOL, N_DONORS = 10, 5, 50
BIG = 250_000
SETS, SET_BOOT, BOOT = 200, 500, 2000
FIRST, LAST = 2012, 2025
BANDS = [0, 10_000, 50_000, 250_000, np.inf]
WI_K = 2_668_677 * 5 / 1000
PICK = REFERENCE / "parking_method2_pick.csv"
LOCK = ROOT / "docs" / "parking" / "CAUSAL_FRAMEWORK_PLAN.md"
CANDIDATES = ("A", "B", "C", "D")


# ---------------------------------------------------------------- data ----------------------------------------------
def gaz(path: Path, name: str, lev: str) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        g = pd.read_csv(z.open(name), sep="\t", dtype={"GEOID": str}, encoding="latin-1")
    g.columns = [c.strip() for c in g.columns]
    g.index = lev + "|" + g["GEOID"]
    return g


class Data:
    def __init__(self):
        bps = rpc.read_bps_us()
        p = cmp.panel(bps)
        sj = bps[(bps["state_fips"].astype(str).str.strip() == "18") & (bps["bps_id"].astype(str).str.strip() == "687500")].copy()
        sj["fips_place"] = "00001"
        p = pd.concat([p, cmp.panel(sj)], ignore_index=True)
        self.p = p
        geo = p.drop_duplicates("key", keep="last").set_index("key")
        self.geo = geo
        acs = RAW / "census_acs5_2024_tbsf"
        homes = geo["acs_geoid"].map(rpc.acs_table(acs / "acsdt5y2024-b25002.dat", "B25002_E001"))
        popn = geo["acs_geoid"].map(rpc.acs_table(acs / "acsdt5y2024-b01003.dat", "B01003_E001"))
        # South Bend's combined area, as in the salvage script
        h2 = rps.acs(acs / "acsdt5y2024-b25002.dat", "B25002_E001")
        p2 = rps.acs(acs / "acsdt5y2024-b01003.dat", "B01003_E001")
        others = [k for k in geo.index if k.startswith("18|") and geo.loc[k, "county_fips"] == "141"
                  and geo.loc[k, "name"].replace(" town", "") in rps.SJ_OTHER_PLACES]
        homes[rps.SJ_KEY] = h2[rps.SJ_COUNTY] - homes.reindex(others).sum()
        popn[rps.SJ_KEY] = p2[rps.SJ_COUNTY] - popn.reindex(others).sum()
        self.homes = homes[homes > 0].astype(float)
        self.popn = popn.astype(float)
        P = p[p["year"].between(FIRST, LAST)].pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")
        self.P = P.reindex(columns=range(FIRST, LAST + 1))
        self.keys = self.P.index
        # exclusions
        tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
        ref = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
        self.main_exc = {k for r in ref.drop_duplicates("prn_key").itertuples()
                         if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
        cities = tax[tax["place_type"] == "city"].drop_duplicates(["state", "place"])
        self.strict_exc = {k for r in cities.itertuples()
                           if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))} | self.main_exc
        # traits keyed by acs_geoid, mapped to BPS keys
        ag = geo["acs_geoid"]
        g10 = pd.concat([gaz(RAW / "parking_older_reforms" / "Gaz_places_national.zip", "Gaz_places_national.txt", "160"),
                         gaz(RAW / "census_gazetteer_2010" / "Gaz_cousubs_national.zip", "Gaz_cousubs_national.txt", "060")])
        g24 = pd.concat([gaz(RAW / "census_gazetteer_2024" / "2024_Gaz_place_national.zip", "2024_Gaz_place_national.txt", "160"),
                         gaz(RAW / "census_gazetteer_2024" / "2024_Gaz_cousubs_national.zip", "2024_Gaz_cousubs_national.txt", "060")])
        hu10 = ag.map(g10["HU10"].astype(float))
        al10 = ag.map(g10["ALAND"].astype(float))
        al24 = ag.map(g24["ALAND"].astype(float))
        sq10 = ag.map(g10["ALAND_SQMI"].astype(float))
        self.density = np.log((hu10 / sq10).where((hu10 > 0) & (sq10 > 0)))
        loss = (hu10 >= 1000) & (homes.reindex(hu10.index) <= 0.9 * hu10)
        land = ((al24 / al10) - 1).abs() >= 0.25
        self.shock = set(hu10.index[loss.fillna(False)]) | set(al10.index[land.fillna(False)])
        b = parsers.read_acs_sf(acs / "acsdt5y2024-b25034.dat", state_fips="", sumlevels=("060", "160"))
        b.index = b["sumlevel"] + "|" + b["geoid"]
        pre2010 = b["B25034_E001"] - b["B25034_E002"] - b["B25034_E003"]
        self.age = ag.map(((b["B25034_E004"] + b["B25034_E005"]) / pre2010).where(pre2010 > 0))
        cr = pd.read_csv(REFERENCE / "parking_acs_crowding.csv", dtype={"acs_geoid": str})
        self.crowd = {y: ag.map(g.set_index("acs_geoid")["crowded_share"]) for y, g in cr.groupby("year")}
        cbsa = read_shapefile_attributes(RAW / "census_cbsa_cb_2024" / "cb_2024_us_cbsa_20m.zip").set_index("CBSAFP")["LSAD"]
        bcb = bps.assign(key=lambda d: d["state_fips"].astype(str).str.strip() + "|" + d["bps_id"].astype(str).str.strip()) \
            .drop_duplicates("key", keep="last").set_index("key")["cbsa"].astype(str).str.strip()
        self.metro = pd.Series({k: float(cbsa.get(bcb.get(k, ""), "") == "M1") for k in geo.index})
        self.division = geo["division"]
        self.state = pd.Series(geo.index.str.split("|").str[0], index=geo.index)

    # homes the year before the event: ACS homes minus permits issued from the event year to 2024, floored at half
    @lru_cache(maxsize=None)
    def homes_pre(self, ey: int, fixed: bool = False) -> pd.Series:
        if fixed:
            return self.homes
        since = self.P[[y for y in self.P.columns if ey <= y <= 2024]].sum(axis=1).reindex(self.homes.index).fillna(0)
        return (self.homes - since).clip(lower=self.homes * 0.5)

    @lru_cache(maxsize=None)
    def complete(self, years: tuple) -> frozenset:
        return frozenset(self.P.index[self.P[list(years)].notna().all(axis=1)])

    def crowd_for(self, ey: int) -> pd.Series:
        y = ey - 1  # latest 5-year release ending before the event year
        return self.crowd.get(y, pd.Series(dtype=float))


# ---------------------------------------------------------------- matching ------------------------------------------
def rates(D: Data, keys, years, h: pd.Series) -> pd.DataFrame:
    return D.P.loc[keys, list(years)].div(h.reindex(keys), axis=0) * 1000


def traits(D: Data, keys, pre, ey, h, with_pace: bool, with_pop: bool) -> pd.DataFrame:
    keys = list(keys)
    t = pd.DataFrame({"crowd": D.crowd_for(ey).reindex(keys), "density": D.density.reindex(keys), "age": D.age.reindex(keys)}, index=keys)
    if with_pace:
        r = rates(D, keys, pre, h)
        x = np.array(pre, dtype=float) - np.mean(pre)
        t["rate"] = r.mean(axis=1)
        t["trend"] = (r.values * x).sum(axis=1) / (x ** 2).sum() if len(pre) > 1 else 0.0
    if with_pop:
        t["log_pop"] = np.log(D.popn.reindex(keys) * (h.reindex(keys) / D.homes.reindex(keys)))
    return t


def mahal(T: pd.DataFrame, target: str, cands: list) -> tuple[pd.Series, np.ndarray]:
    """Distance from target to each candidate: Mahalanobis on z-scores (z and covariance over all rows of T),
    over the traits both have, squared distance scaled by total / available traits."""
    Z = (T - T.mean()) / T.std(ddof=0).replace(0, np.nan)
    cov = Z.cov().values
    tz = Z.loc[target].values
    out = {}
    for c in cands:
        cz = Z.loc[c].values
        m = np.isfinite(tz) & np.isfinite(cz) & np.isfinite(np.diag(cov))
        if m.sum() == 0:
            out[c] = np.inf
            continue
        d = (cz - tz)[m]
        S = cov[np.ix_(m, m)]
        d2 = float(d @ np.linalg.pinv(S) @ d) * (len(tz) / m.sum())
        out[c] = np.sqrt(max(d2, 0.0))
    return pd.Series(out), cov


def eligible(D: Data, target, years, mode_exc, shock_on, h) -> list:
    exc = D.strict_exc if mode_exc == "strict" else D.main_exc
    ok = D.complete(tuple(years))
    return [k for k in ok if k != target and k not in exc and (not shock_on or k not in D.shock)
            and k in h.index and np.isfinite(D.popn.get(k, np.nan))]


def select_pool(D: Data, target, ey, pre, post, cand, opt) -> dict:
    """Pool for one case. cand: A/B/D (C uses select_donors). opt: exc, shock, match, homes_fixed."""
    h = D.homes_pre(ey, opt["homes_fixed"])
    pool_pre = pre
    E = eligible(D, target, list(pool_pre) + list(post), opt["exc"], opt["shock"], h)
    pop = D.popn.reindex(E) * (h.reindex(E) / D.homes.reindex(E))
    tpop = D.popn.get(target, np.nan) * h.get(target, np.nan) / D.homes.get(target, np.nan)
    st, dv = D.state.get(target), D.division.get(target, "")
    steps = [("state", 0.5, 2.0), ("division", 0.5, 2.0), ("nation", 0.5, 2.0), ("nation", 1 / 3, 3.0)]
    pace = cand == "B"
    chosen, step = None, None
    for i, (scope, lo, hi) in enumerate(steps, 1):
        inwin = pop[(pop >= lo * tpop) & (pop <= hi * tpop)].index
        if scope == "state":
            inwin = [k for k in inwin if D.state.get(k) == st]
        elif scope == "division":
            inwin = [k for k in inwin if dv not in ("", None) and D.division.get(k) == dv]
        if len(inwin) >= N_MATCH:
            chosen, step = list(inwin), i
            break
    T = traits(D, E + [target], pre, ey, h, pace, chosen is None)
    if chosen is None:  # step 5: nationwide any size, nearest 10 incl. log population
        dist, cov = mahal(T, target, E)
        step = 5
        pick = nearest(dist, pop, tpop, N_MATCH)
    elif not opt["match"]:
        dist, cov = pd.Series(0.0, index=chosen), None
        pick = sorted(chosen)
    else:
        dist, cov = mahal(T, target, chosen)
        pick = nearest(dist, pop, tpop, N_MATCH)
    missing = float(T.loc[pick].isna().any(axis=1).mean()) if pick else np.nan
    return dict(pool=pick, step=step, cov=cov, missing_share=missing, h=h)


def nearest(dist: pd.Series, pop: pd.Series, tpop: float, n: int) -> list:
    d = pd.DataFrame({"d": dist, "pg": (np.log(pop.reindex(dist.index)) - np.log(tpop)).abs()})
    d["k"] = d.index
    return list(d.sort_values(["d", "pg", "k"]).head(n).index)


def select_donors(D: Data, target, ey, pre_long, post, opt) -> dict:
    h = D.homes_pre(ey, opt["homes_fixed"])
    E = eligible(D, target, list(pre_long) + list(post), opt["exc"], opt["shock"], h)
    pop = D.popn.reindex(E) * (h.reindex(E) / D.homes.reindex(E))
    tpop = D.popn.get(target, np.nan) * h.get(target, np.nan) / D.homes.get(target, np.nan)
    inwin = list(pop[(pop >= 0.5 * tpop) & (pop <= 2 * tpop)].index)
    if len(inwin) < N_DONORS:
        inwin = list(pop[(pop >= tpop / 3) & (pop <= 3 * tpop)].index)
    pre5 = [y for y in pre_long if y >= ey - 5]
    T = traits(D, E + [target], pre5, ey, h, True, False)
    dist, cov = mahal(T, target, inwin)
    return dict(pool=nearest(dist, pop, tpop, N_DONORS), step="donors", cov=cov,
                missing_share=float(T.loc[inwin].isna().any(axis=1).mean()) if inwin else np.nan, h=h)


# ---------------------------------------------------------------- effects -------------------------------------------
def winsor_cols(R: pd.DataFrame, on: bool) -> pd.DataFrame:
    if not on or len(R) < 2:
        return R
    lo, hi = R.quantile(0.05), R.quantile(0.95)
    return R.clip(lower=lo, upper=hi, axis=1)


def pool_rate(D, pool, years, h, wins) -> pd.Series:
    R = winsor_cols(rates(D, pool, years, h), wins)
    w = h.reindex(pool).values
    return pd.Series((R.values * w[:, None]).sum(axis=0) / w.sum(), index=list(years))


def did(D, target, pre, post, pool, h, wins, scale=1.0) -> float:
    t = rates(D, [target], list(pre) + list(post), h).iloc[0]
    c = pool_rate(D, pool, list(pre) + list(post), h, wins)
    return float(((t[post].mean() - t[pre].mean()) - (c[post].mean() - c[pre].mean())) / scale)


def synth(D, target, pre_long, post, donors, h, wins, scale=1.0) -> float:
    from scipy.optimize import minimize
    yrs = list(pre_long) + list(post)
    t = rates(D, [target], yrs, h).iloc[0]
    R = winsor_cols(rates(D, donors, yrs, h), wins)
    X = R[list(pre_long)].values.T
    y = t[list(pre_long)].values
    n = X.shape[1]
    res = minimize(lambda w: ((y - X @ w) ** 2).sum(), np.full(n, 1 / n), method="SLSQP",
                   bounds=[(0, 1)] * n, constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
    sc = pd.Series(R.values.T @ res.x, index=yrs)
    return float(((t[post].mean() - t[pre_long].mean()) - (sc[post].mean() - sc[pre_long].mean())) / scale)


def long_pre(ey, pre, trimmed: bool) -> list:
    if trimmed:
        return list(pre)
    return [y for y in range(max(FIRST, ey - 10), ey)]


def case_effect(D, case, cand, opt) -> dict:
    key, ey, pre, post, scale = case["key"], case["event_year"], list(case["pre"]), list(case["post"]), case.get("scale", 1.0)
    tpop = D.popn.get(key, np.nan) * 1.0
    if cand == "C" and case.get("pop", tpop) >= BIG:
        pl = long_pre(ey, pre, case.get("trimmed", False))
        s = select_donors(D, key, ey, pl, post, opt)
        if len(s["pool"]) < MIN_POOL:
            return dict(effect=np.nan, step=s["step"], n_pool=len(s["pool"]), missing_share=s["missing_share"], cov=s["cov"])
        e = synth(D, key, pl, post, s["pool"], s["h"], opt["wins"], scale)
        return dict(effect=e, step=s["step"], n_pool=len(s["pool"]), missing_share=s["missing_share"], cov=s["cov"])
    c2 = "B" if cand == "C" else cand
    if c2 == "E":  # post hoc side check (Ryan 19:46 UTC): B's pace matching with D's 10-year before window
        pl = long_pre(ey, pre, case.get("trimmed", False))
        s = select_pool(D, key, ey, pl, post, "B", opt)
        e = did(D, key, pl, post, s["pool"], s["h"], opt["wins"], scale) if len(s["pool"]) >= MIN_POOL else np.nan
    elif c2 == "D":
        pl = long_pre(ey, pre, case.get("trimmed", False))
        s = select_pool(D, key, ey, pl, post, "A", opt)
        e = did(D, key, pl, post, s["pool"], s["h"], opt["wins"], scale) if len(s["pool"]) >= MIN_POOL else np.nan
    else:
        s = select_pool(D, key, ey, pre, post, c2, opt)
        e = did(D, key, pre, post, s["pool"], s["h"], opt["wins"], scale) if len(s["pool"]) >= MIN_POOL else np.nan
    return dict(effect=e, step=s["step"], n_pool=len(s["pool"]), missing_share=s["missing_share"], cov=s["cov"], pool=s["pool"])


OPT_MAIN = dict(exc="strict", shock=True, match=True, homes_fixed=False, wins=True)


# ---------------------------------------------------------------- weights -------------------------------------------
def band_of(pop) -> np.ndarray:
    return np.digitize(np.asarray(pop, dtype=float), BANDS[1:-1])


def target_cells(D: Data, state_fips: str) -> pd.Series:
    keys = [k for k in D.homes.index if D.state.get(k) == state_fips and k not in D.main_exc]
    h = D.homes.reindex(keys)
    cells = pd.DataFrame({"band": band_of(D.popn.reindex(keys).fillna(0)), "metro": D.metro.reindex(keys).fillna(0).values, "h": h.values})
    return cells.groupby(["metro", "band"])["h"].sum()


def mix_weights(ev: pd.DataFrame, cells: pd.Series) -> tuple[np.ndarray, float]:
    """ev: band, metro, base (homes x after-years). Returns weights and the share of target homes in empty cells."""
    w = np.zeros(len(ev))
    empty = 0.0
    tot = cells.sum()
    for m in (0.0, 1.0):
        groups = [[b] for b in range(4)]
        def count(g):
            return int(((ev["metro"] == m) & ev["band"].isin(g)).sum())
        changed = True
        while changed and len(groups) > 1:
            changed = False
            for i, g in enumerate(groups):
                if count(g) < 2:
                    j = i + 1 if i < len(groups) / 2 - 0.5 or i == 0 else i - 1
                    j = min(max(j, 0), len(groups) - 1)
                    if j == i:
                        continue
                    a, b = sorted((i, j))
                    groups[a] = groups[a] + groups[b]
                    del groups[b]
                    changed = True
                    break
        for g in groups:
            T = sum(cells.get((m, b), 0.0) for b in g)
            idx = ((ev["metro"] == m) & ev["band"].isin(g)).values
            if idx.sum() == 0:
                empty += T
                continue
            base = ev["base"].values[idx]
            w[idx] = base / base.sum() * T
    if w.sum() > 0:
        w = w / w.sum()
    return w, empty / tot if tot else np.nan


def dl_weights(y, v) -> tuple[np.ndarray, float]:
    w0 = 1 / v
    ybar = np.sum(w0 * y) / w0.sum()
    Q = np.sum(w0 * (y - ybar) ** 2)
    denom = w0.sum() - np.sum(w0 ** 2) / w0.sum()
    tau2 = max(0.0, (Q - (len(y) - 1)) / denom) if denom > 0 else 0.0
    return 1 / (v + tau2), tau2


def winsor(y):
    lo, hi = np.percentile(y, 5), np.percentile(y, 95)
    return np.clip(y, lo, hi)


def weighted_avg(kind, y, ev, cells=None, wins=True):
    yy = winsor(y) if wins else y
    if kind == "random effects":
        w, _ = dl_weights(yy, ev["v"].values)
    elif kind == "target-state mix":
        w, _ = mix_weights(ev, cells)
    elif kind == "square root":
        w = np.sqrt(ev["homes"].values) * ev["n_post"].values
    elif kind == "homes":
        w = ev["homes"].values * ev["n_post"].values
    else:
        w = np.ones(len(yy))
    return float(np.sum(w * yy) / np.sum(w)) if np.sum(w) > 0 else np.nan


WEIGHTS = ("random effects", "target-state mix", "square root", "homes", "equal")


def boot_range(kind, y, ev, cells, draws, seed, wins=True):
    rng = np.random.default_rng(seed)
    n = len(y)
    vals = []
    for _ in range(draws):
        i = rng.integers(0, n, n)
        vals.append(weighted_avg(kind, y[i], ev.iloc[i].reset_index(drop=True), cells, wins))
    vals = np.array(vals)
    vals = vals[np.isfinite(vals)]
    return float(np.percentile(vals, 5)), float(np.percentile(vals, 95))


# ---------------------------------------------------------------- cases ---------------------------------------------
def real_cases() -> tuple[pd.DataFrame, list]:
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    m = t46.rebuild(real, t46.collect())
    assert m["found"].all()
    cases = []
    for i, x in m.iterrows():
        c = x["call"]
        cases.append(dict(i=i, key=c["key"], event_year=int(real.loc[i, "event_year"]), pre=tuple(c["pre"]), post=tuple(c["post"]),
                          scale=float(x["scale"]), pop=float(real.loc[i, "population"]) if pd.notna(real.loc[i, "population"]) else np.nan,
                          trimmed=real.loc[i, "source"] == "rescued" and not str(real.loc[i, "place"]).startswith("South Bend"),
                          homes=float(real.loc[i, "homes"]), n_post=int(real.loc[i, "n_post"]), state=real.loc[i, "state"],
                          place=real.loc[i, "place"]))
    return real, cases


def placebo_v(n: int) -> np.ndarray:
    pl = pd.read_csv(REFERENCE / "parking_placebo_full_places.csv")
    v = pl.groupby("real_index")["effect"].var().reindex(range(n))
    return v.fillna(v.median()).values


WORKERS = 7
_G: dict = {}


def _fake_effects(chunk):
    D = _G["D"]
    out = {}
    for (k, ey, pre, post) in chunk:
        case = dict(key=k, event_year=ey, pre=pre, post=post, pop=D.popn.get(k, np.nan))
        for cand in CANDIDATES:
            out[(k, ey, pre, post, cand)] = case_effect(D, case, cand, OPT_MAIN)["effect"]
    return out


def _variant(arg):
    cand, opt = arg
    return [case_effect(_G["D"], c, cand, opt) for c in _G["cases"]]


def _score(job):
    cand, kind = job
    D, eff, sets, v, cells = _G["D"], _G["eff"], _G["sets"], _G["v"], _G["cells"]
    avgs, cover = [], []
    for si, row in enumerate(sets):
        y = np.array([eff[(k, ey, pre, post, cand)] for (k, ey, pre, post, _) in row])
        ev = pd.DataFrame({"v": [v[i] for *_, i in row], "homes": [D.homes_pre(ey)[k] for (k, ey, *_r) in row],
                           "n_post": [len(post) for (_, _, _, post, _) in row],
                           "band": band_of([D.popn.get(k, 0) for (k, *_r) in row]),
                           "metro": [D.metro.get(k, 0.0) for (k, *_r) in row]})
        ev["base"] = ev["homes"] * ev["n_post"]
        ok = np.isfinite(y)
        y, ev = y[ok], ev[ok].reset_index(drop=True)
        a = weighted_avg(kind, y, ev, cells)
        lo, hi = boot_range(kind, y, ev, cells, SET_BOOT, SEED + si)
        avgs.append(a)
        cover.append(lo <= 0 <= hi)
    cov = float(np.mean(cover))
    return dict(candidate=cand, weights=kind, mae=float(np.mean(np.abs(avgs))), coverage=cov,
                coverage_se=float(np.sqrt(cov * (1 - cov) / SETS)), sets=SETS)


# ---------------------------------------------------------------- stage 1 -------------------------------------------
def stage1(D: Data) -> None:
    real, cases = real_cases()
    v = placebo_v(len(real))
    rng = np.random.default_rng(SEED)
    wi_cells = target_cells(D, "55")
    strata, strata_rows = {}, []
    for c in cases:
        pre, post = cmp.windows(c["event_year"])
        post = post[: c["n_post"]]
        band = int(band_of([c["pop"] if np.isfinite(c["pop"]) else D.popn.get(c["key"], 0)])[0])
        sk = (c["event_year"], band, c["n_post"])
        if sk not in strata:
            ok = D.complete(tuple(pre + post))
            def pool_of(exc):
                return sorted(k for k in ok if k not in exc and k not in D.shock and k in D.homes.index
                              and int(band_of([D.popn.get(k, 0)])[0]) == band)
            s = pool_of(D.strict_exc)
            src = "strict"
            if len(s) < 5:
                s, src = [k for k in pool_of(D.main_exc) if k not in {x["key"] for x in cases}], "main list"
            strata[sk] = (s, pre, post)
            strata_rows.append(dict(event_year=sk[0], size_band=band, n_post=sk[2], distinct_places=len(s), source=src))
    sets = []
    for _ in range(SETS):
        row = []
        for c in cases:
            band = int(band_of([c["pop"] if np.isfinite(c["pop"]) else D.popn.get(c["key"], 0)])[0])
            s, pre, post = strata[(c["event_year"], band, c["n_post"])]
            row.append((s[rng.integers(0, len(s))], c["event_year"], tuple(pre), tuple(post), c["i"]))
        sets.append(row)
    uniq = sorted({(k, ey, pre, post) for row in sets for (k, ey, pre, post, _) in row})
    print(len(uniq), "distinct fake cases", flush=True)
    global _G
    _G = dict(D=D, uniq=uniq, sets=sets, v=v, cells=wi_cells)
    ctx = mp.get_context("fork")
    chunks = [uniq[i::WORKERS] for i in range(WORKERS)]
    eff = {}
    with cf.ProcessPoolExecutor(WORKERS, mp_context=ctx) as ex:
        for part in ex.map(_fake_effects, chunks):
            eff.update(part)
    _G["eff"] = eff
    jobs = [(cand, kind) for cand in CANDIDATES for kind in WEIGHTS]
    with cf.ProcessPoolExecutor(WORKERS, mp_context=ctx) as ex:
        rows = list(ex.map(_score, jobs))
    for r in rows:
        print(r, flush=True)
    B = pd.DataFrame(rows)
    B.round(4).to_csv(REFERENCE / "parking_method2_bakeoff.csv", index=False)
    pd.DataFrame(strata_rows).to_csv(REFERENCE / "parking_method2_bakeoff_strata.csv", index=False)
    re = B[B["weights"] == "random effects"]
    ok = re[(re["coverage"] >= 0.85) & (re["coverage"] <= 0.95)]
    if len(ok):
        pick = ok.sort_values("mae").iloc[0]
        rule = "lowest MAE with coverage 85-95%"
    else:
        re = re.assign(gap=(re["coverage"] - 0.90).abs())
        pick = re.sort_values(["gap", "mae"]).iloc[0]
        rule = "no candidate in 85-95%; coverage closest to 90%, then MAE"
    pd.DataFrame([dict(candidate=pick["candidate"], rule=rule, mae=pick["mae"], coverage=pick["coverage"])]).to_csv(PICK, index=False)
    print("PICK", pick["candidate"], rule)


# ---------------------------------------------------------------- stage 2 -------------------------------------------
def require_pick() -> str:
    lock = LOCK.read_text()
    if "Ryan's main-weight choice (19:22 UTC)" not in lock:
        raise SystemExit("lock does not name Ryan's main-weight rule")
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(PICK)], cwd=ROOT, capture_output=True)
    d = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(PICK)], cwd=ROOT)
    if r.returncode or d.returncode:
        raise SystemExit("the bake-off pick is not committed (or changed since): commit reference/parking_method2_pick.csv first")
    return str(pd.read_csv(PICK)["candidate"].iloc[0])


def stage2(D: Data) -> None:
    pick = require_pick()
    real, cases = real_cases()
    v = placebo_v(len(real))
    ev = pd.DataFrame({"v": v, "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = target_cells(D, "55")
    tn = target_cells(D, "47")
    out, detail, covs = [], [], []
    variants = {f"method 2, {c}": (c, OPT_MAIN) for c in CANDIDATES}
    variants.update({
        f"switch back 2 (main exclusion list), {pick}": (pick, {**OPT_MAIN, "exc": "main"}),
        f"switch back 3 (no matching), {pick}": (pick, {**OPT_MAIN, "match": False}),
        f"switch back 4 (no shock rule), {pick}": (pick, {**OPT_MAIN, "shock": False}),
        f"switch back 5 (no winsorising), {pick}": (pick, {**OPT_MAIN, "wins": False}),
        f"switch back 6 (fixed ACS homes), {pick}": (pick, {**OPT_MAIN, "homes_fixed": True}),
    })
    global _G
    _G = dict(D=D, cases=cases)
    effects = {}
    with cf.ProcessPoolExecutor(WORKERS, mp_context=mp.get_context("fork")) as ex:
        results = dict(zip(variants, ex.map(_variant, variants.values())))
    for name, res in results.items():
        ys = []
        for c, r in zip(cases, res):
            ys.append(r["effect"])
            detail.append(dict(variant=name, place=c["place"], state=c["state"], effect=r["effect"], step=r["step"],
                               n_pool=r["n_pool"], missing_share=r["missing_share"]))
            if name == f"method 2, {pick}" and r["cov"] is not None:
                covs.append(dict(place=c["place"], step=r["step"], cov=";".join(f"{x:.4f}" for x in np.asarray(r["cov"]).ravel())))
        effects[name] = np.array(ys)
    shock_real = np.array([c["key"] in D.shock for c in cases])
    for name, y in list(effects.items()) + [(f"shock rule also drops flagged repeal places, {pick}", np.where(shock_real, np.nan, effects[f"method 2, {pick}"]))]:
        ok = np.isfinite(y)
        wins = "no winsorising" not in name
        for kind in WEIGHTS:
            cells = wi
            a = weighted_avg(kind, y[ok], ev[ok].reset_index(drop=True), cells, wins)
            lo, hi = boot_range(kind, y[ok], ev[ok].reset_index(drop=True), cells, BOOT, SEED, wins)
            out.append(dict(variant=name, weights=kind, places=int(ok.sum()), average=a, p05=lo, p95=hi,
                            wi_homes=a * WI_K, wi_p05=lo * WI_K, wi_p95=hi * WI_K))
    # target-state diagnostics
    yb = effects[f"method 2, {pick}"]
    ok = np.isfinite(yb)
    diag = []
    for stf, cells in (("55", wi), ("47", tn)):
        w, empty = mix_weights(ev[ok].reset_index(drop=True), cells)
        diag.append(dict(state=stf, effective_places=float(w.sum() ** 2 / (w ** 2).sum()), empty_cell_share=empty,
                         eligible_homes_bps=float(cells.sum())))
    # backtest (picked candidate): before -5..-3, after -2..-1, re-matched on -5..-3 with the vintage before the pseudo-event
    bt = []
    for c in cases:
        ey = c["event_year"]
        pre = [y for y in c["pre"] if y <= ey - 3]
        post = [y for y in (ey - 2, ey - 1) if y in c["pre"]]
        if len(pre) < 2 or not post:
            bt.append(np.nan)
            continue
        bc = dict(c, event_year=ey - 2, pre=tuple(pre), post=tuple(post))
        bt.append(case_effect(D, bc, pick, OPT_MAIN)["effect"])
    bt = np.array(bt)
    okb = np.isfinite(bt)
    for kind in WEIGHTS:
        a = weighted_avg(kind, bt[okb], ev[okb].reset_index(drop=True), wi)
        lo, hi = boot_range(kind, bt[okb], ev[okb].reset_index(drop=True), wi, BOOT, SEED)
        out.append(dict(variant=f"backtest, {pick}", weights=kind, places=int(okb.sum()), average=a, p05=lo, p95=hi))
    # weight test: leave one state out
    states = real["state"].value_counts()
    states = list(states[states >= 3].index)
    errs = {k: [] for k in WEIGHTS}
    errs_eq = {k: [] for k in WEIGHTS}
    for s in states:
        hold = (real["state"] == s).values & ok
        train = (~(real["state"] == s).values) & ok
        truth = float(np.average(yb[hold], weights=ev["base"].values[hold]))
        truth_eq = float(np.mean(yb[hold]))
        # weight test only: aim the mix at the held-out repeal places' own homes x after-years by cell (audit)
        hc = ev[hold].groupby(["metro", "band"])["base"].sum()
        for kind in WEIGHTS:
            pred = weighted_avg(kind, yb[train], ev[train].reset_index(drop=True), hc)
            errs[kind].append(abs(pred - truth))
            errs_eq[kind].append(abs(pred - truth_eq))
    E = pd.DataFrame(errs, index=states)
    mae = E.mean()
    best = mae.idxmin()
    rng = np.random.default_rng(SEED)
    diffs = []
    for _ in range(BOOT):
        i = rng.integers(0, len(E), len(E))
        diffs.append(E["target-state mix"].values[i].mean() - E[best].values[i].mean())
    lo, hi = np.percentile(diffs, 5), np.percentile(diffs, 95)
    tie = (mae["target-state mix"] <= 1.10 * mae[best]) or (lo <= 0 <= hi)
    winner = "target-state mix" if tie else best
    E.loc["mean absolute error"] = mae
    E.round(4).to_csv(REFERENCE / "parking_method2_weight_test.csv")
    Eq = pd.DataFrame(errs_eq, index=states)
    Eq.loc["mean absolute error"] = Eq.mean()
    Eq.round(4).to_csv(REFERENCE / "parking_method2_weight_test_equal_truth.csv")
    pd.DataFrame([dict(winner=winner, lowest=best, tie_rule_applied=bool(tie and best != "target-state mix"),
                       mix_minus_best_p05=lo, mix_minus_best_p95=hi)]).to_csv(REFERENCE / "parking_method2_weight_pick.csv", index=False)
    pd.DataFrame(out).round(4).to_csv(REFERENCE / "parking_method2_results.csv", index=False)
    pd.DataFrame(detail).round(4).to_csv(REFERENCE / "parking_method2_places.csv", index=False)
    pd.DataFrame(diag).round(4).to_csv(REFERENCE / "parking_method2_state_mix.csv", index=False)
    pd.DataFrame(covs).to_csv(REFERENCE / "parking_method2_covariances.csv", index=False)
    pd.DataFrame({"shock_flagged_places": sorted(D.shock)}).to_csv(REFERENCE / "parking_method2_shock_list.csv", index=False)
    print(pd.DataFrame(out).round(2).to_string())
    print(E.round(3).to_string())
    print("WEIGHT WINNER", winner, "lowest", best, lo, hi)
    print(pd.DataFrame(diag).round(3).to_string())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, required=True, choices=(1, 2))
    a = ap.parse_args()
    D = Data()
    print("strict exclusions", len(D.strict_exc), "| shock-flagged", len(D.shock), flush=True)
    stage1(D) if a.stage == 1 else stage2(D)


if __name__ == "__main__":
    main()

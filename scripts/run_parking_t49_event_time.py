"""Parking test 49 (CAUSAL_FRAMEWORK_PLAN.md, "Test 49"): does the effect build, hold or fade? Method D on corrected
method-2 data; one pool per case held fixed across years; three weightings; neutral slope rule.

    uv run --all-extras python scripts/run_parking_t49_event_time.py
Outputs: reference/parking_t49_by_year.csv, parking_t49_slopes.csv, parking_t49_places.csv
"""
from __future__ import annotations

import concurrent.futures as cf
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_method2 as m  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

SEED = 20261105
WEIGHTS = ("target-state mix", "random effects", "equal")
G: dict = {}


def case_years(c, last_k: int):
    """Effects for after-years 1..last_k (and year 0, and the long set's leads) with one fixed pool."""
    D = G["D"]
    key, ey, scale = c["key"], c["event_year"], c.get("scale", 1.0)
    pl = m.long_pre(ey, list(c["pre"]), c.get("trimmed", False))
    post = [ey + k for k in range(1, last_k + 1)]
    yrs_all = sorted(set(pl) | set(post) | {ey})
    if not set(yrs_all) <= set(D.P.columns):
        return dict(effects=None, n_pool=0, step=None)
    s = m.select_pool(D, key, ey, pl, post + [ey], "A", m.OPT_MAIN)  # D's pool rule, complete over the whole window
    pool, h = s["pool"], s["h"]
    if len(pool) < m.MIN_POOL:
        return dict(effects=None, n_pool=len(pool), step=s["step"])
    t = m.rates(D, [key], yrs_all, h).iloc[0]
    cp = m.pool_rate(D, pool, yrs_all, h, True)
    base = t[pl].mean() - cp[pl].mean()
    out = {k: float(((t[ey + k] - cp[ey + k]) - base) / scale) for k in [0] + list(range(1, last_k + 1))}
    if len(pl) >= 6:  # leads: last 3 before-years against the earlier before-years
        early, late = [y for y in pl if y < ey - 3], [ey - 3, ey - 2, ey - 1]
        b2 = t[early].mean() - cp[early].mean()
        for y in late:
            out[y - ey] = float(((t[y] - cp[y]) - b2) / scale)
    detail = dict(own={int(y): float(t[y]) for y in yrs_all}, comp={int(y): float(cp[y]) for y in yrs_all},
                  own_before=float(t[pl].mean()), comp_before=float(cp[pl].mean()), scale=scale)
    return dict(effects=out, n_pool=len(pool), step=s["step"], detail=detail)


def _run(args):
    i, last_k = args
    return i, case_years(G["cases"][i], last_k)


def wavg(kind, y, ev, cells):
    if len(y) == 0:  # a bootstrap draw with no place observed in that year (years 6+ have few places)
        return np.nan
    return m.weighted_avg(kind, y, ev, cells)


def summarise(label, idx, ks, eff, ev, cells, rng_seed):
    rows, slopes = [], []
    Y = np.array([[eff[i]["effects"].get(k, np.nan) for k in ks] for i in idx])
    E = ev.iloc[idx].reset_index(drop=True)
    for kind in WEIGHTS:
        point = []
        for j, k in enumerate(ks):
            ok = np.isfinite(Y[:, j])
            a = wavg(kind, Y[ok, j], E[ok].reset_index(drop=True), cells)
            point.append(a)
        rng = np.random.default_rng(rng_seed)
        boots = []
        for _ in range(m.BOOT):
            b = rng.integers(0, len(idx), len(idx))
            vals = []
            for j in range(len(ks)):
                ok = np.isfinite(Y[b, j])
                vals.append(wavg(kind, Y[b][ok, j], E.iloc[b][ok].reset_index(drop=True), cells))
            boots.append(vals)
        boots = np.array(boots)
        for j, k in enumerate(ks):
            bj = boots[:, j][np.isfinite(boots[:, j])]
            rows.append(dict(check=label, weights=kind, year=k, places=int(np.isfinite(Y[:, j]).sum()), estimate=point[j],
                             p05=float(np.percentile(bj, 5)), p95=float(np.percentile(bj, 95)),
                             wi_homes=point[j] * m.WI_K))
        bal = [j for j, k in enumerate(ks) if k >= 1 and np.isfinite(Y[:, j]).all()] if "leads" not in label else list(range(len(ks)))
        if len(bal) >= 2:
            x = np.array([ks[j] for j in bal], float)
            sl = lambda v: float(np.polyfit(x, np.asarray(v)[bal], 1)[0])  # noqa: E731
            sb = np.array([sl(r) for r in boots if np.all(np.isfinite(np.asarray(r)[bal]))])
            lo, hi = np.percentile(sb, 5), np.percentile(sb, 95)
            first, last = bal[0], bal[-1]
            dd = boots[:, last] - boots[:, first]
            n_with = int(np.isfinite(Y[:, bal]).all(axis=1).sum())
            slopes.append(dict(check=label, weights=kind, years=f"{ks[first]}-{ks[last]}", places=n_with, slope=sl(point),
                               slope_p05=lo, slope_p95=hi, change_first_to_last=point[last] - point[first],
                               change_p05=float(np.nanpercentile(dd, 5)), change_p95=float(np.nanpercentile(dd, 95)),
                               reading="changes with time" if (lo > 0 or hi < 0) else "no clear change over time"))
    return rows, slopes


def main() -> None:
    m.SUF, m.CORRECTED = "_corrected", True
    D = m.Data()
    real, cases = m.real_cases()
    G.update(D=D, cases=cases)
    last_year = int(D.P.columns.max())
    n_after = {i: last_year - c["event_year"] for i, c in enumerate(cases)}
    set1 = [i for i in range(len(cases)) if int(real.loc[i, "n_post"]) == 3]
    set2 = [i for i in range(len(cases)) if n_after[i] >= 5]
    jobs = [(i, 3) for i in set1] + [(i, n_after[i]) for i in set2]
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=mp.get_context("fork")) as ex:
        res = list(ex.map(_run, jobs))
    eff1 = {i: r for (i, r), (_, k) in zip(res, jobs) if k == 3 and i in set1 and r["effects"] is not None}
    eff2 = {i: r for (i, r), (_, k) in zip(res, jobs) if i in set2 and k == n_after[i] and r["effects"] is not None}
    drop_rows = [dict(check="38-place set" if k == 3 and i in set1 else "long set", place=cases[i]["place"],
                      event_year=cases[i]["event_year"], pool_size=r["n_pool"])
                 for (i, r), (_, k) in zip(res, jobs) if r["effects"] is None]
    pd.DataFrame(drop_rows, columns=["check", "place", "event_year", "pool_size"]).to_csv(REFERENCE / "parking_t49_dropped.csv", index=False)
    dropped = [d["place"] for d in drop_rows]
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": 1,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"]
    cells = m.target_cells(D, "55")
    rows, slopes = [], []
    i1 = sorted(eff1)
    r, s = summarise("38-place set", i1, [0, 1, 2, 3], {**eff1}, ev, cells, SEED)
    rows += r
    slopes += s
    r, s = summarise("38-place set leads", i1, [-3, -2, -1], eff1, ev, cells, SEED)
    rows += r
    slopes += s
    # years 1-3 average per place vs corrected method 2's effect for the same places (target-state mix)
    y13 = np.array([np.nanmean([eff1[i]["effects"][k] for k in (1, 2, 3)]) for i in i1])
    m2 = pd.read_csv(REFERENCE / "parking_method2_corrected_places.csv")
    m2 = m2[m2["variant"] == "method 2, D"].reset_index(drop=True)
    assert (m2["place"].values == np.array([c["place"] for c in cases])).all(), "method-2 rows out of order"
    m2 = m2["effect"].values[i1]
    E1 = ev.iloc[i1].reset_index(drop=True)
    cmp_rows = []
    for lab, yy in (("years 1-3 average, fixed long pool", y13), ("corrected method 2 (D), same places", m2)):
        ok = np.isfinite(yy)
        a = m.weighted_avg("target-state mix", yy[ok], E1[ok].reset_index(drop=True), cells)
        lo, hi = m.boot_range("target-state mix", yy[ok], E1[ok].reset_index(drop=True), cells, m.BOOT, SEED)
        cmp_rows.append(dict(version=lab, places=int(ok.sum()), estimate=a, p05=lo, p95=hi))
    pd.DataFrame(cmp_rows).round(4).to_csv(REFERENCE / "parking_t49_vs_method2.csv", index=False)
    print(pd.DataFrame(cmp_rows).round(3).to_string(index=False))
    i2 = sorted(eff2)
    kmax = max(n_after[i] for i in i2)
    r, s = summarise("long set", i2, [0] + list(range(1, kmax + 1)), eff2, ev, cells, SEED)
    rows += r
    slopes += [x for x in s]
    r, s = summarise("long set leads", i2, [-3, -2, -1], eff2, ev, cells, SEED)
    rows += r
    slopes += s
    out = pd.DataFrame(rows)
    out.round(4).to_csv(REFERENCE / "parking_t49_by_year.csv", index=False)
    pd.DataFrame(slopes).round(4).to_csv(REFERENCE / "parking_t49_slopes.csv", index=False)
    pl = [dict(set="38-place set" if i in eff1 else "", place=cases[i]["place"], event_year=cases[i]["event_year"],
               n_pool=(eff1.get(i) or eff2.get(i))["n_pool"]) for i in sorted(set(eff1) | set(eff2))]
    pd.DataFrame(pl).to_csv(REFERENCE / "parking_t49_places.csv", index=False)
    pd.set_option("display.width", 220)
    print("dropped:", dropped)
    print(out.round(2).to_string(index=False))
    print(pd.DataFrame(slopes).round(3).to_string(index=False))


if __name__ == "__main__":
    main()

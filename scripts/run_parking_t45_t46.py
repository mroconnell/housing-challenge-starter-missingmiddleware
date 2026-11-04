"""Parking tests 45-46 (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, locked 2026-11-04): who the comparison places are.

    uv run --all-extras python scripts/run_parking_t45_t46.py

Test 45: strict pools that leave out every city with any parking-reform record. Test 46: how much single comparison
places drive the 76 effects. Each repeal place is rebuilt with its own script (expanded, salvage, partial) by
recording the comparison pools those scripts choose; their file writes are switched off while they run.
Outputs: reference/parking_t46_pools.csv, parking_t45_strict.csv, parking_t45_summary.csv, parking_t46_by_comparison.csv,
parking_t46_loo_top10.csv, parking_t46_regression.csv
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
import run_parking_expanded as rpe  # noqa: E402
import run_parking_partial as rpp  # noqa: E402
import run_parking_salvage as rps  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

SEED, DRAWS, TAIL = 20261104, 2000, 8
_orig_controls = cmp.controls
CALLS: list[dict] = []
STRICT: set = set()


def recording_controls(p, key, event_year, excluded, homes, population=None):
    c, label = _orig_controls(p, key, event_year, set(excluded) | (STRICT - {key}), homes, population)
    pre, post = cmp.windows(event_year)
    CALLS.append(dict(key=key, event_year=int(event_year), pre=list(pre), post=list(post), pool=list(c), window=label,
                      p=p, homes=homes, first_year=cmp.FIRST_YEAR))
    return c, label


def collect() -> list[dict]:
    """Run the three effect scripts with recording on and writes off; return the recorded calls."""
    CALLS.clear()
    cmp.controls = recording_controls
    to_csv = pd.DataFrame.to_csv
    pd.DataFrame.to_csv = lambda *a, **k: None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rpe.us_effects()
            rps.main()
            rpp.main()
    finally:
        pd.DataFrame.to_csv = to_csv
        cmp.controls = _orig_controls
    return list(CALLS)


def sums(p, keys, years, homes):
    s = p[p["key"].isin(keys) & p["year"].isin(years)].groupby("key")["units_total"].sum()
    return s.reindex(keys).fillna(0.0), homes.reindex(keys)


def ctrl_change(p, pool, pre, post, homes) -> float:
    a0, h = sums(p, pool, pre, homes)
    a1, _ = sums(p, pool, post, homes)
    return float(a1.sum() / len(post) / h.sum() * 1000 - a0.sum() / len(pre) / h.sum() * 1000)


def rebuild(real: pd.DataFrame, calls: list[dict]) -> pd.DataFrame:
    """Match each repeal place to its recorded pool (last call for that key and year)."""
    by = {}
    for c in calls:
        by[(c["key"], c["event_year"])] = c
    out = []
    for r in real.itertuples():
        k = rps.SJ_KEY if r.source == "rescued" and str(r.place).startswith("South Bend") else r.key
        c = by.get((k, int(r.event_year)))
        if c is None:
            out.append(dict(i=r.Index, found=False))
            continue
        scale = 1.0
        if k == rps.SJ_KEY:
            # combined-area effect / city effect = South Bend's share of the combined area's homes (salvage script)
            scale = float((r.rate_after - r.rate_before) - (r.ctrl_after - r.ctrl_before)) / float(r.effect)
        own = float(r.rate_after - r.rate_before)
        cc = ctrl_change(c["p"], c["pool"], c["pre"], c["post"], c["homes"]) if c["pool"] else np.nan
        out.append(dict(i=r.Index, found=True, call=c, scale=scale, own=own, ctrl=cc, effect=(own - cc) / scale,
                        n_pool=len(c["pool"]), window=c["window"]))
    return pd.DataFrame(out)


def wavg(y, w):
    m = np.isfinite(y)
    return float(np.average(y[m], weights=w[m]))


def boot(y, w, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(y)
    v = [wavg(y[i], w[i]) for i in (rng.integers(0, n, n) for _ in range(DRAWS))]
    return float(np.percentile(v, 5)), float(np.percentile(v, 95))


def main() -> None:
    global STRICT
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    w = (real["homes"] * real["n_post"]).values
    calls = collect()
    m = rebuild(real, calls)
    bad = (~m["found"]) | ((m["effect"] - real["effect"]).abs() > 1e-4) \
        | ((m["ctrl"] - (real["ctrl_after"] - real["ctrl_before"])).abs() > 1e-4)
    print("rebuilt", int(m["found"].sum()), "of", len(real), "| mismatches:", int(bad.sum()))
    if bad.any():
        print(real.loc[bad.values, ["place", "source", "effect"]].assign(rebuilt=m.loc[bad.values, "effect"].values).to_string())
        raise SystemExit("rebuild does not match the stored effects; nothing new is read (lock)")

    # ---- test 46: pools, reuse, outliers, leave-one-out ----
    rank = real["effect"].rank(method="first")
    outlier = ((rank <= TAIL) | (rank > len(real) - TAIL)).values
    rows = []
    for i, x in m.iterrows():
        c = x["call"]
        h = c["homes"].reindex(c["pool"])
        for k in c["pool"]:
            rows.append(dict(ri=i, repeal_place=real.loc[i, "place"], repeal_state=real.loc[i, "state"], repeal_key=real.loc[i, "key"],
                             event_year=c["event_year"], comparison_key=k, share_of_pool_homes=float(h[k] / h.sum()),
                             window=c["window"], outlier=bool(outlier[i])))
    pools = pd.DataFrame(rows)
    names = calls[0]["p"].drop_duplicates("key", keep="last").set_index("key")["name"]
    pools["comparison_name"] = pools["comparison_key"].map(names)
    pools.round(5).to_csv(REFERENCE / "parking_t46_pools.csv", index=False)

    base = wavg(m["effect"].values, w)
    pre_cache = {}
    for i, x in m.iterrows():
        c = x["call"]
        a0, h = sums(c["p"], c["pool"], c["pre"], c["homes"])
        a1, _ = sums(c["p"], c["pool"], c["post"], c["homes"])
        pre_cache[i] = (a0, a1, h, len(c["pre"]), len(c["post"]))
    loo = []
    for k, g in pools.groupby("comparison_key"):
        eff = m["effect"].values.copy()
        for i in g["ri"].unique():
            a0, a1, h, n0, n1 = pre_cache[i]
            keep = h.index != k
            cc = a1[keep].sum() / n1 / h[keep].sum() * 1000 - a0[keep].sum() / n0 / h[keep].sum() * 1000
            eff[i] = (m.loc[i, "own"] - cc) / m.loc[i, "scale"]
        loo.append(dict(comparison_key=k, comparison_name=names.get(k, ""), used_by=g["ri"].nunique(),
                        used_by_outliers=int(g.loc[g["outlier"], "ri"].nunique()),
                        mean_share_of_pool_homes=float(g["share_of_pool_homes"].mean()),
                        max_share_of_pool_homes=float(g["share_of_pool_homes"].max()),
                        average_without=wavg(eff, w), change=wavg(eff, w) - base))
    by = pd.DataFrame(loo).sort_values("used_by", ascending=False)
    by.round(4).to_csv(REFERENCE / "parking_t46_by_comparison.csv", index=False)
    top = by.reindex(by["change"].abs().sort_values(ascending=False).index).head(10)
    top.round(4).to_csv(REFERENCE / "parking_t46_loo_top10.csv", index=False)

    import statsmodels.api as sm
    lead = pools.groupby(["repeal_key", "event_year"])["share_of_pool_homes"].max()
    d = pd.DataFrame({"outlier": outlier.astype(float), "abs_effect": real["effect"].abs().values,
                      "log_pool": np.log(m["n_pool"].values.astype(float)),
                      "widened": (~m["window"].str.startswith("state 0.50")).astype(float).values,
                      "largest_share": [lead.get((real.loc[i, "key"], int(real.loc[i, "event_year"])), np.nan) for i in real.index],
                      "abs_ctrl_change": m["ctrl"].abs().values})
    reg = []
    for ycol in ("outlier", "abs_effect"):
        X = sm.add_constant(d[["log_pool", "widened", "largest_share", "abs_ctrl_change"]])
        f = sm.OLS(d[ycol], X, missing="drop").fit(cov_type="HC1")
        ci = f.conf_int(0.10)
        for v in X.columns:
            reg.append(dict(outcome=ycol, term=v, coef=f.params[v], ci90_low=ci.loc[v, 0], ci90_high=ci.loc[v, 1],
                            p=f.pvalues[v], n=int(f.nobs), r2=f.rsquared))
    pd.DataFrame(reg).round(4).to_csv(REFERENCE / "parking_t46_regression.csv", index=False)
    r_own = float(np.corrcoef(real["effect"], m["own"] / m["scale"])[0, 1])
    r_ctrl = float(np.corrcoef(real["effect"], m["ctrl"] / m["scale"])[0, 1])

    # ---- test 45: strict pools ----
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    p0 = calls[0]["p"]
    cities = tax[tax["place_type"] == "city"].drop_duplicates(["state", "place"])
    STRICT = {k for r in cities.itertuples()
              if (k := cmp.match_place(p0, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    s_calls = collect()
    s = rebuild(real, s_calls)
    st = real[["place", "state", "source"]].copy()
    st["main_pool"], st["main_window"], st["main_effect"] = m["n_pool"], m["window"], m["effect"]
    st["strict_pool"], st["strict_window"], st["strict_effect"] = s["n_pool"], s["window"], s["effect"]
    st["dropped_from_main_pool"] = [len(set(a["pool"]) - set(b["pool"])) for a, b in zip(m["call"], s["call"])]
    st["window_widened"] = st["main_window"] != st["strict_window"]
    st.round(4).to_csv(REFERENCE / "parking_t45_strict.csv", index=False)
    ok = np.isfinite(st["strict_effect"].values)
    main_lo, main_hi = boot(m["effect"].values, w)
    s_lo, s_hi = boot(np.where(ok, st["strict_effect"].values, np.nan), w)
    summ = dict(strict_cities_matched=len(STRICT), main_average=base, main_p05=main_lo, main_p95=main_hi,
                strict_average=wavg(st["strict_effect"].values, w), strict_p05=s_lo, strict_p95=s_hi,
                places_with_strict_effect=int(ok.sum()), places_widened=int(st["window_widened"].sum()),
                mean_dropped_per_pool=float(st["dropped_from_main_pool"].mean()),
                share_of_main_pool_dropped=float(st["dropped_from_main_pool"].sum() / st["main_pool"].sum()),
                main_on_same_set=wavg(np.where(ok, m["effect"].values, np.nan), w),
                consistent_with_main=bool(main_lo <= wavg(st["strict_effect"].values, w) <= main_hi),
                r_effect_own_change=r_own, r_effect_comparison_change=r_ctrl, loo_base=base)
    pd.DataFrame([summ]).round(4).to_csv(REFERENCE / "parking_t45_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(pd.Series(summ).to_string())
    print(st[st["window_widened"]][["place", "main_window", "strict_window", "main_pool", "strict_pool", "main_effect", "strict_effect"]].round(2).to_string())
    print(top.round(3).to_string())
    print(by.head(15).round(3).to_string())
    print(pd.DataFrame(reg).round(3).to_string())


if __name__ == "__main__":
    main()

"""Parking test 47 (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, locked 2026-11-04): do big cities match each other better
than same-state cities half to twice their size?

    uv run --all-extras python scripts/run_parking_t47_bigcity.py
Outputs: reference/parking_t47_targets.csv (per target and fake year), reference/parking_t47_summary.csv
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

BIG, SEED, DRAWS = 250_000, 20261104, 2000
FAKE_YEARS = range(2017, 2022)
ALL_YEARS = list(range(2012, 2026))


def bigcity_controls(p, key, event_year, excluded, homes, popn, big_keys) -> tuple[list, str]:
    pre, post = cmp.windows(event_year)
    ok = cmp.complete(p, pre + post) & set(homes.dropna().index)
    pop0 = popn[key]
    for lo, hi in (cmp.POP_WINDOW, cmp.POP_WINDOW_WIDE):
        c = [k for k in big_keys if k != key and k not in excluded and k in ok and lo * pop0 <= popn[k] <= hi * pop0]
        if len(c) >= cmp.MIN_CONTROLS:
            return c, f"nation {lo:.2f}-{hi:.2f}"
    return c, f"nation {lo:.2f}-{hi:.2f} (fewer than {cmp.MIN_CONTROLS})"


def rate(p, keys, years, homes) -> pd.Series:
    """Pooled rate by year over the places that reported that year (inside fake windows all pool places report)."""
    q = p[p["key"].isin(keys) & p["year"].isin(years)]
    s = q.groupby("year")["units_total"].sum()
    h = q.drop_duplicates(["key", "year"]).assign(h=lambda x: x["key"].map(homes)).groupby("year")["h"].sum()
    return (s / h * 1000).reindex(years)


def fake_effect(p, key, pool, pre, post, homes) -> float:
    t = rate(p, [key], pre + post, homes)
    c = rate(p, pool, pre + post, homes)
    return float((t[post].mean() - t[pre].mean()) - (c[post].mean() - c[pre].mean()))


def fit_rmse(p, key, pool, homes) -> float:
    g = rate(p, [key], ALL_YEARS, homes) - rate(p, pool, ALL_YEARS, homes)
    g = g.dropna()
    return float(np.sqrt(((g - g.mean()) ** 2).mean()))


def boot(x, w, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(x)
    v = [np.average(x[i], weights=w[i]) for i in (rng.integers(0, n, n) for _ in range(DRAWS))]
    return float(np.average(x, weights=w)), float(np.percentile(v, 5)), float(np.percentile(v, 95))


def main() -> None:
    p = cmp.panel(rpc.read_bps_us())
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    ref = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
    exc = {k for r in ref.drop_duplicates("prn_key").itertuples()
           if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    big = [k for k in popn[popn >= BIG].index if k in homes.index]
    targets = [k for k in big if k not in exc and k in cmp.complete(p, ALL_YEARS)]
    print(len(big), "big places;", len(targets), "targets", flush=True)
    # the big-city pool may use any place in the US at 0.5-2x (or 1/3-3x) of the target, not only 250,000+
    cand = [k for k in popn.dropna().index if k in homes.index and popn[k] >= BIG * 0.33 * 0.5]
    rows = []
    for k in targets:
        rm_cur = rm_big = None
        for ey in FAKE_YEARS:
            pre, post = cmp.windows(ey)
            cur, wcur = cmp.controls(p, k, ey, exc, homes, popn)
            bc, wbig = bigcity_controls(p, k, ey, exc, homes, popn, cand)
            if not cur or not bc:
                continue
            if rm_cur is None:
                rm_cur, rm_big = fit_rmse(p, k, cur, homes), fit_rmse(p, k, bc, homes)
            rows.append(dict(key=k, name=geo.loc[k, "name"], state=k.split("|")[0], population=float(popn[k]), homes=float(homes[k]),
                             fake_year=ey, current_window=wcur, current_pool=len(cur), big_window=wbig, big_pool=len(bc),
                             current_effect=fake_effect(p, k, cur, pre, post, homes), big_effect=fake_effect(p, k, bc, pre, post, homes),
                             current_rmse=rm_cur, big_rmse=rm_big))
    d = pd.DataFrame(rows)
    d.round(4).to_csv(REFERENCE / "parking_t47_targets.csv", index=False)
    t = d.groupby("key").agg(homes=("homes", "first"), cur_abs=("current_effect", lambda s: s.abs().mean()),
                             big_abs=("big_effect", lambda s: s.abs().mean()), cur_rmse=("current_rmse", "first"),
                             big_rmse=("big_rmse", "first"))
    out = {"targets": len(t), "target_years": len(d)}
    for wlab, w in (("equal", np.ones(len(t))), ("homes", t["homes"].values)):
        for lab, a, b in (("abs_fake_effect", "big_abs", "cur_abs"), ("rmse", "big_rmse", "cur_rmse")):
            m, lo, hi = boot((t[a] - t[b]).values, w)
            out.update({f"{lab}_{wlab}_big_minus_current": m, f"{lab}_{wlab}_p05": lo, f"{lab}_{wlab}_p95": hi,
                        f"{lab}_{wlab}_current_mean": float(np.average(t[b], weights=w)),
                        f"{lab}_{wlab}_big_mean": float(np.average(t[a], weights=w))})
        a_hi, r_hi = out[f"abs_fake_effect_{wlab}_p95"], out[f"rmse_{wlab}_p95"]
        a_lo, r_lo = out[f"abs_fake_effect_{wlab}_p05"], out[f"rmse_{wlab}_p05"]
        out[f"verdict_{wlab}"] = "big-city better" if a_hi < 0 and r_hi < 0 else "big-city worse" if a_lo > 0 and r_lo > 0 else "no clear difference"
    out["sd_fake_effect_current"] = float(d["current_effect"].std())
    out["sd_fake_effect_big"] = float(d["big_effect"].std())
    pd.DataFrame([out]).round(4).to_csv(REFERENCE / "parking_t47_summary.csv", index=False)
    print(pd.Series(out).to_string())


if __name__ == "__main__":
    main()

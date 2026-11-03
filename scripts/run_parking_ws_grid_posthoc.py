"""POST HOC to the work-session grid (learning thread, 2026-11-03): (1) D1 zero-count sensitivity (add 0.5 / add 1 / drop
places with a zero window); (2) place bootstrap of the held-out error difference, D1 minus predict-zero, all 76.
Reads reference/parking_ws_grid_places.csv (no new count of outcomes beyond the grid's inputs).

    uv run python scripts/run_parking_ws_grid_posthoc.py
Output: reference/parking_ws_grid_posthoc.csv
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

SEED, DRAWS = 20261104, 2000


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    u5 = b.pivot_table(index="key", columns="year", values="5plus_units", aggfunc="sum")
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
    G = pd.read_csv(REFERENCE / "parking_ws_grid_places.csv").set_index("key")
    mean5 = lambda keys, yrs: float(np.nansum(u5.reindex(index=list(keys), columns=yrs).values)) / len(yrs)  # noqa: E731
    raw = []
    for r in real.itertuples():
        pre, post = cmp.windows(int(r.event_year))
        post = post[: int(r.n_post)]
        ctrl, _ = cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)
        n = max(len(ctrl), 1)
        raw.append(dict(key=r.key, tb=mean5([r.key], pre), ta=mean5([r.key], post), cb=mean5(ctrl, pre) / n, ca=mean5(ctrl, post) / n))
    R = pd.DataFrame(raw).set_index("key").join(G[["weight", "effect_main", "rate5_before", "d1"]], how="inner").dropna(subset=["effect_main", "rate5_before"])
    rng = np.random.default_rng(SEED)
    out = []
    for lab, c, dropz in (("add 0.5 (locked)", 0.5, False), ("add 1", 1.0, False), ("drop places with a zero window", 0.5, True)):
        D = R[~((R["tb"] == 0) | (R["ta"] == 0))] if dropz else R
        v = ((np.log(D["ta"] + c) - np.log(D["tb"] + c)) - (np.log(D["ca"] + c) - np.log(D["cb"] + c))).values
        w, act, rate = D["weight"].values, D["effect_main"].values, D["rate5_before"].values
        n = len(D)
        pred = np.array([(np.exp(np.average(np.delete(v, i), weights=np.delete(w, i))) - 1) * rate[i] for i in range(n)])
        e1, e0 = np.abs(act - pred), np.abs(act)
        f = lambda i: np.average(e1[i], weights=w[i]) - np.average(e0[i], weights=w[i])  # noqa: E731
        bs = np.array([f(rng.integers(0, n, n)) for _ in range(DRAWS)])
        est = np.average(v, weights=w)
        out.append(dict(version=lab, places=n, d1_estimate=est, pct=100 * (np.exp(est) - 1), heldout_error=np.average(e1, weights=w),
                        error_zero=np.average(e0, weights=w), diff=f(np.arange(n)), diff_p05=np.percentile(bs, 5), diff_p95=np.percentile(bs, 95),
                        share_draws_d1_better=float((bs < 0).mean())))
    S = pd.DataFrame(out)
    S["unit"] = "errors in permits per 1,000 existing homes a year; diff = D1 minus predict-zero (negative = D1 better)"
    S["label"] = "POST HOC"
    S.to_csv(REFERENCE / "parking_ws_grid_posthoc.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns=["unit", "label"]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()

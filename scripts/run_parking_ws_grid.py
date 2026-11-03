"""Parking work session: D1 (log change in 5+ unit permits) and the 6-version grid {all 76, S2} x {per 1,000 homes, D1, D2}.
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Work session", locked 2026-11-03).

    uv run python scripts/run_parking_ws_grid.py
Outputs: reference/parking_ws_grid_places.csv, reference/parking_ws_grid.csv
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
ACS = RAW / "census_acs5_2024_tbsf"


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    u5 = b.pivot_table(index="key", columns="year", values="5plus_units", aggfunc="sum")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(ACS / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    h5 = sum(geo["acs_geoid"].map(rpc.acs_table(ACS / "acsdt5y2024-b25024.dat", f"B25024_E00{i}")).fillna(0) for i in (6, 7, 8, 9))
    popn = geo["acs_geoid"].map(rpc.acs_table(ACS / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    excluded |= set(real["key"])

    def mean5(keys, yrs):  # mean yearly 5+ permits, pooled
        return float(np.nansum(u5.reindex(index=list(keys), columns=yrs).values)) / len(yrs)

    def per1000(keys, yrs, den):
        d = den.reindex(list(keys)).sum()
        return mean5(keys, yrs) / d * 1000 if d > 0 else np.nan

    rows = []
    for r in real.itertuples():
        pre, post = cmp.windows(int(r.event_year))
        post = post[: int(r.n_post)]
        ctrl, _ = cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)
        tb, ta, cb, ca = mean5([r.key], pre), mean5([r.key], post), mean5(ctrl, pre), mean5(ctrl, post)
        d1 = (np.log(ta + 0.5) - np.log(tb + 0.5)) - (np.log(ca / max(len(ctrl), 1) + 0.5) - np.log(cb / max(len(ctrl), 1) + 0.5))
        d2 = (per1000([r.key], post, h5) - per1000([r.key], pre, h5)) - (per1000(ctrl, post, h5) - per1000(ctrl, pre, h5))
        hk = float(homes.get(r.key, np.nan))
        rows.append(dict(place=r.place, state=r.state, key=r.key, n_post=int(r.n_post), weight=r.weight, effect_main=r.effect,
                         d1=d1, d2=d2, zero_before=tb == 0, zero_after=ta == 0,
                         rate5_before=per1000([r.key], pre, homes), share5=float(h5.get(r.key, np.nan)) / hk if hk else np.nan))
    P = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan)
    P.to_csv(REFERENCE / "parking_ws_grid_places.csv", index=False)

    rng = np.random.default_rng(SEED)
    out = []
    for sub, D in (("all 76", P), ("S2 (3 after years)", P[P["n_post"] == 3])):
        D = D.dropna(subset=["effect_main", "d1", "d2", "rate5_before", "share5"]).reset_index(drop=True)
        w, act = D["weight"].values, D["effect_main"].values
        n = len(D)
        err = lambda pred: np.average(np.abs(act - pred), weights=w)  # noqa: E731
        e_zero = err(np.zeros(n))
        for col, lab, conv in (("effect_main", "per 1,000 homes (main)", lambda v, i: v),
                               ("d1", "D1 log change, 5+ permits", lambda v, i: (np.exp(v) - 1) * D["rate5_before"].values[i]),
                               ("d2", "D2 per 1,000 existing 5+ homes", lambda v, i: v * D["share5"].values[i])):
            v = D[col].values
            pred = np.array([conv(np.average(np.delete(v, i), weights=np.delete(w, i)), i) for i in range(n)])
            f = lambda idx: np.sum(v[idx] * w[idx]) / np.sum(w[idx])  # noqa: E731
            bs = np.array([f(rng.integers(0, n, n)) for _ in range(DRAWS)])
            out.append(dict(subset=sub, version=lab, places=n, estimate=f(np.arange(n)), p05=np.percentile(bs, 5), p95=np.percentile(bs, 95),
                            p0125=np.percentile(bs, 1.25), p9875=np.percentile(bs, 98.75), mde=1.645 * bs.std(ddof=1),
                            heldout_error=err(pred), error_predict_zero=e_zero,
                            zero_count_places=int((D["zero_before"] | D["zero_after"]).sum()) if col == "d1" else np.nan))
    S = pd.DataFrame(out)
    for sub in S["subset"].unique():
        m = S["subset"] == sub
        main_err = S.loc[m & S["version"].str.startswith("per 1,000"), "heldout_error"].iloc[0]
        S.loc[m, "beats_zero"] = S.loc[m, "heldout_error"] < S.loc[m, "error_predict_zero"]
        S.loc[m, "beats_main"] = S.loc[m, "heldout_error"] < main_err
    S["unit_estimate"] = S["version"].map({"per 1,000 homes (main)": "permits per 1,000 existing homes a year",
                                           "D1 log change, 5+ permits": "log change in 5+ unit permits (x100 = approx. %)",
                                           "D2 per 1,000 existing 5+ homes": "5+ permits per 1,000 existing 5+ homes a year"})
    S["unit_error"] = "permits per 1,000 existing homes a year (common unit)"
    S.to_csv(REFERENCE / "parking_ws_grid.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns=["unit_estimate", "unit_error"]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()

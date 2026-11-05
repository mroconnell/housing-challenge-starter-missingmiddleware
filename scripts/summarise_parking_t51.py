"""Test 51 (CAUSAL_FRAMEWORK_PLAN.md): compare an LIHTC-adjusted run with the unadjusted run at the same cut-off.

    uv run python scripts/summarise_parking_t51.py <label> <unadjusted run name> <adjusted run name> [...more triples]
Runs live in data/processed/t51/<name>_ref (scripts/run_parking_t51_lihtc.sh). Writes reference/parking_t51_results.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
T51 = ROOT / "data" / "processed" / "t51"
WI_K = 2_668_677 * 5 / 1000
SEED, DRAWS = 20261105, 2000


def load(name):
    w = T51 / f"{name}_ref"
    e = pd.read_csv(w / "parking_expanded_effects.csv")
    e = e[(e["status"] == "included") & (e["outcome"] == "all")].dropna(subset=["effect"]).set_index("prn_key")
    pl = pd.read_csv(w / "parking_placebo_full_summary.csv").iloc[0]
    m2 = pd.read_csv(w / "parking_method2_corrected_results.csv")
    m2 = m2[(m2["variant"] == "method 2, D") & (m2["weights"] == "target-state mix")].iloc[0]
    logs = sorted(w.glob("parking_t51_floor_log_*.csv"))
    fl = pd.concat([pd.read_csv(f) for f in logs], ignore_index=True).drop_duplicates(["key", "year"]) if logs else None
    return e, pl, m2, fl


def main() -> None:
    a = sys.argv[1:]
    rows = []
    for label, un, ad in zip(a[0::3], a[1::3], a[2::3]):
        eu, pu, mu, _ = load(un)
        ea, pa, ma, fl = load(ad)
        both = eu.index.intersection(ea.index)
        yu, ya = eu.loc[both, "effect"].values, ea.loc[both, "effect"].values
        wu, wa = eu.loc[both, "weight"].values, ea.loc[both, "weight"].values
        diff = np.average(ya, weights=wa) - np.average(yu, weights=wu)
        rng = np.random.default_rng(SEED)
        bd = []
        for _ in range(DRAWS):
            i = rng.integers(0, len(both), len(both))
            bd.append(np.average(ya[i], weights=wa[i]) - np.average(yu[i], weights=wu[i]))
        lo, hi = np.percentile(bd, [5, 95])
        r = dict(check=label, places_unadjusted=len(eu), places_adjusted=len(ea), places_paired=len(both),
                 unadj_rate=pu["real_average"], unadj_wi=pu["real_average"] * WI_K, unadj_wi_p05=pu["range_from_placebo_low"] * WI_K,
                 unadj_wi_p95=pu["range_from_placebo_high"] * WI_K,
                 adj_rate=pa["real_average"], adj_wi=pa["real_average"] * WI_K, adj_wi_p05=pa["range_from_placebo_low"] * WI_K,
                 adj_wi_p95=pa["range_from_placebo_high"] * WI_K,
                 paired_diff_rate=diff, paired_p05=lo, paired_p95=hi, paired_diff_wi=diff * WI_K,
                 paired_wi_p05=lo * WI_K, paired_wi_p95=hi * WI_K,
                 reading="subsidy does not drive the result" if lo <= 0 <= hi else "adjustment moves the result",
                 m2_unadj_wi=mu["wi_homes"], m2_unadj_p05=mu["wi_p05"], m2_unadj_p95=mu["wi_p95"],
                 m2_adj_wi=ma["wi_homes"], m2_adj_p05=ma["wi_p05"], m2_adj_p95=ma["wi_p95"])
        # share of permits removed, home-weighted, repeal places (own) and their pools, before and after
        for side, cu, ca in (("own_before", "rate_before", "rate_before"), ("own_after", "rate_after", "rate_after"),
                             ("pool_before", "ctrl_before", "ctrl_before"), ("pool_after", "ctrl_after", "ctrl_after")):
            h = eu.loc[both, "homes"].values
            su, sa = np.sum(eu.loc[both, cu].values * h), np.sum(ea.loc[both, ca].values * h)
            r[f"removed_share_{side}"] = 1 - sa / su if su else np.nan
        if fl is not None and len(fl):
            r["floor_place_years"] = int(fl["floor_total"].sum())
            r["lihtc_place_years"] = len(fl)
            r["floor_units_lost"] = float((fl["lihtc"] - fl["permits"]).clip(lower=0).sum())
            r["lihtc_units"] = float(fl["lihtc"].sum())
            r["timing_check_share_units"] = float(fl.loc[fl["lihtc"] <= fl["permits"], "lihtc"].sum() / fl["lihtc"].sum())
        rows.append(r)
    out = pd.DataFrame(rows)
    out.round(4).to_csv(ROOT / "reference" / "parking_t51_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(3).T.to_string())


if __name__ == "__main__":
    main()

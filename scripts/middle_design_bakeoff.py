"""Middle housing design bake-off: how precise would each candidate primary design be?

Research only (docs/middle/DESIGN_BAKEOFF.md). Same no-peeking limits as middle_power_check.py:
Census place permits for 2012-2018 only; candidate cities and law states are never fake-treated.

Unit: homes permitted per 1,000 single-family homes per year. Windows: before 2012-2014, after 2016-2018.
Each design's "bar" is the smallest effect detectable with 80% power at a two-sided 90% level:
(1.645 + 0.842) x the spread of its statistic across fake law states.

Designs
  A  law state vs places in other untested states of its Census region (log rate ratio, converted to
     per-1,000 terms at the median fake state's before rate); k = number of law states pooled
  B  within one state, by city size, as Oregon's law: cities of 10,000+ (covered) against cities of
     2,500-9,999 (not covered), homes-weighted change in rate, covered minus not covered
  B+ design B pooled over k states (k = 1 is Oregon alone)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import middle_power_check as pc  # noqa: E402

OUT = pc.OUT


def pooled_change(df: pd.DataFrame, m: str) -> float:
    h = df["homes"].sum()
    return 1000 * (df[m + "_a"].sum() - df[m + "_b"].sum()) / (h * 3) if h else np.nan


def design_b_stats(t: pd.DataFrame, m: str) -> pd.Series:
    pool = t[~t["state_fips"].isin(pc.TESTED_STATES) & ~t["candidate"]]
    out = {}
    for st, g in pool.groupby("state_fips"):
        cov, non = g[g["pop"] >= 10000], g[g["pop"].between(2500, 9999)]
        if len(cov) >= 3 and len(non) >= 3:
            out[st] = pooled_change(cov, m) - pooled_change(non, m)
    return pd.Series(out)


def spread_of_mean(stats: pd.Series, k: int, rng) -> float:
    v = [stats.sample(k, random_state=int(rng.integers(1e9))).mean() for _ in range(5000)]
    return float(np.std(v, ddof=1))


def main() -> None:
    homes = pc.sf_homes()
    rows = []
    for reported_only in (False, True):
        d = pc.load_bps(reported_only)
        t = pc.place_table(d, homes, reported_only)
        label = "reported only, 12 months" if reported_only else "with Census fill-ins"
        for m in ("1to4", "2to4", "all"):
            rng = np.random.default_rng(pc.SEED)
            a = pc.test1_state_stats(t, m)
            base = a["rate_before"].median()
            for k in (2, 4):
                sd = spread_of_mean(a["stat"], k, rng)
                rows.append(dict(data=label, measure=m, design="A: law states vs region", states=k,
                                 fake_states=len(a), bar_per_1000=(np.exp(pc.K * sd) - 1) * base,
                                 bar_note=f"+{100 * (np.exp(pc.K * sd) - 1):.0f}% of {base:.2f}", mean_fake=np.nan))
            b = design_b_stats(t, m)
            for k in (1, 2, 4):
                sd = spread_of_mean(b, k, rng) if k > 1 else float(b.std())
                rows.append(dict(data=label, measure=m, design="B: within state, 10,000+ vs 2,500-9,999", states=k,
                                 fake_states=len(b), bar_per_1000=pc.K * sd, bar_note="", mean_fake=float(b.mean())))
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "middle_design_bakeoff.csv", index=False)
    pd.set_option("display.width", 200)
    print(r.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

"""Baseline range, round 2 (docs/shared/BASELINE_RANGE_PLAN.md; audit-cleared, Ryan's go 2026-11-05 18:08 UTC).

    uv run python scripts/run_baseline_range.py

Same inputs as scripts/run_baseline_bakeoff.py --part 1. Outputs (committed):
reference/baseline_range_coverage.csv          every state x check year x level x method x step: range, actual, hit
reference/baseline_range_coverage_summary.csv  coverage on the 50 states other than Wisconsin (with bootstrap range),
                                               on Wisconsin, by volatility tercile; the pick
reference/baseline_range_wisconsin.csv         Wisconsin 2027-2031 low/high for every level, method and step
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_baseline_bakeoff as P1  # noqa: E402
from missing_middleware import baseline_bakeoff as bb  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

WI = "55"
STEPS = ((0.05, 0.95), (0.025, 0.975), (0.0, 1.0))
CHECKS = tuple(range(2005, 2021))
LEVELS = ("L0", "L3")
V3_CENTRAL = 124_000


def ratios_table(u, homes, division, level) -> pd.DataFrame:
    """Per state and start year: predicted and actual five-year totals (all sizes and by size), start years from
    1992 (L0) or 1997 (L3, whose b needs fit start years s <= t - 5 from 1992)."""
    ss = list(range(1992 if level == "L0" else 1997, 2021))
    par = {t: bb.fit_param(level, u, homes, t, division) for t in ss} if level in bb.FITTED else None
    r = bb.score_rows(level, u, homes, ss, division, par)
    r["ratio"] = r["actual"] / r["pred"]
    for z in bb.SIZES:
        r[f"ratio_{z}"] = r[f"actual_{z}"] / r[f"pred_{z}"]
    return r


def q(x: pd.Series, lo: float, hi: float) -> tuple[float, float]:
    x = x[np.isfinite(x) & (x > 0)]
    return float(x.quantile(lo)), float(x.quantile(hi))


def coverage(r: pd.DataFrame, level: str, u: pd.DataFrame) -> pd.DataFrame:
    tot = u.groupby(["state", "year"])["units"].sum()
    out = []
    for t in CHECKS:
        past, cur = r[r.start <= t - bb.HORIZON], r[r.start == t].set_index("state")
        # volatility: sd of log annual all-sizes permits, 1990..t, terciles at t
        vol = tot[tot.index.get_level_values("year") <= t].groupby("state").apply(lambda s: np.log(s.clip(lower=1)).std())
        terc = pd.qcut(vol.rank(method="first"), 3, labels=["calm", "middle", "volatile"])
        for method in ("R0", "R1"):
            for lo, hi in STEPS:
                if method == "R1":
                    mt = {"_all": q(past["ratio"], lo, hi)}
                    ms = {z: q(past[f"ratio_{z}"], lo, hi) for z in bb.SIZES}
                for s, row in cur.iterrows():
                    if method == "R0":
                        ps = past[past.state == s]
                        a, b = q(ps["ratio"], lo, hi)
                        szs = {z: q(ps[f"ratio_{z}"], lo, hi) for z in bb.SIZES}
                    else:
                        a, b = mt["_all"]
                        szs = ms
                    low, high = row["pred"] * a, row["pred"] * b
                    plow = sum(row[f"pred_{z}"] * szs[z][0] for z in bb.SIZES)
                    phigh = sum(row[f"pred_{z}"] * szs[z][1] for z in bb.SIZES)
                    act = row["actual"]
                    out.append(dict(level=level, method=method, lo=lo, hi=hi, start=t, state=s, tercile=terc[s],
                                    pred=row["pred"], low=low, high=high, actual=act, hit=low <= act <= high,
                                    persize_low=plow, persize_high=phigh, persize_hit=plow <= act <= phigh))
    return pd.DataFrame(out)


def main() -> None:
    u, geo = P1.read_state_permits()
    census = P1.read_census()
    allu = u.groupby(["state", "year"], as_index=False)["units"].sum()
    homes = bb.homes_by_year(census, allu, range(1990, 2026))
    division = geo.set_index("state")["division"]

    C, W = [], []
    l0_2025 = float((bb.predict("L0", u, homes, 2025, division) * bb.HORIZON).loc[WI].sum())
    for level in LEVELS:
        r = ratios_table(u, homes, division, level)
        C.append(coverage(r, level, u))
        p25 = bb.fit_param(level, u, homes, 2025, division) if level in bb.FITTED else None
        pr = bb.predict(level, u, homes, 2025, division, p25) * bb.HORIZON
        cen = float(pr.loc[WI].sum())
        f = V3_CENTRAL / l0_2025
        for method in ("R0", "R1"):
            pool = r[r.state == WI] if method == "R0" else r
            for lo, hi in STEPS:
                a, b = q(pool["ratio"], lo, hi)
                ps = {z: q(pool[f"ratio_{z}"], lo, hi) for z in bb.SIZES}
                plow = sum(float(pr.loc[(WI, z)]) * ps[z][0] for z in bb.SIZES)
                phigh = sum(float(pr.loc[(WI, z)]) * ps[z][1] for z in bb.SIZES)
                W.append(dict(level=level, method=method, lo=lo, hi=hi, param=p25, published_central=cen,
                              v3_central=cen * f, v3_low=cen * a * f, v3_high=cen * b * f,
                              v3_persize_low=plow * f, v3_persize_high=phigh * f))
    C, W = pd.concat(C, ignore_index=True), pd.DataFrame(W)

    draws = bb.block_bootstrap_starts(CHECKS)
    rows = []
    for (level, method, lo, hi), g in C.groupby(["level", "method", "lo", "hi"]):
        o = g[g.state != WI]
        per = o.groupby("start")["hit"].mean()
        boot = np.array([per.loc[d].mean() for d in draws])
        w = g[g.state == WI]
        rec = dict(level=level, method=method, lo=lo, hi=hi, coverage_other50=o["hit"].mean(),
                   boot_lo=np.quantile(boot, 0.05), boot_hi=np.quantile(boot, 0.95),
                   wi_hits=int(w["hit"].sum()), wi_checks=len(w),
                   persize_coverage_other50=o["persize_hit"].mean(), wi_persize_hits=int(w["persize_hit"].sum()),
                   wi_tercile=",".join(sorted(set(map(str, w["tercile"])))))
        for tc, gg in o.groupby("tercile", observed=True):
            rec[f"coverage_{tc}"] = gg["hit"].mean()
        rows.append(rec)
    S = pd.DataFrame(rows)
    S = S.merge(W[["level", "method", "lo", "hi", "v3_low", "v3_high"]], on=["level", "method", "lo", "hi"])
    # pick (plan): per level and method, narrowest step with other-50 coverage >= 90%; then R0 vs R1 by narrower WI range
    S["reaches_90"] = S["coverage_other50"] >= 0.90
    S["width"] = S["v3_high"] - S["v3_low"]
    S["chosen_step"] = False
    S["picked"] = False
    for level in LEVELS:
        best = []
        for method in ("R0", "R1"):
            g = S[(S.level == level) & (S.method == method) & S.reaches_90]
            if not g.empty:   # narrowest step = earliest in STEPS
                i = min(g.index, key=lambda j: STEPS.index((S.loc[j, "lo"], S.loc[j, "hi"])))
                S.loc[i, "chosen_step"] = True
                best.append(i)
        if best:
            S.loc[min(best, key=lambda i: S.loc[i, "width"]), "picked"] = True
    C.round({c: 1 for c in ("pred", "low", "high", "actual", "persize_low", "persize_high")}).to_csv(
        REFERENCE / "baseline_range_coverage.csv", index=False)
    S.round(4).to_csv(REFERENCE / "baseline_range_coverage_summary.csv", index=False)
    W.round({c: 1 for c in W.columns if c.startswith(("v3_", "published"))}).to_csv(REFERENCE / "baseline_range_wisconsin.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

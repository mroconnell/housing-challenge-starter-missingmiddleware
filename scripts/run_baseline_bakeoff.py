"""Baseline bake-off (docs/shared/BASELINE_BAKEOFF_PLAN.md, locked 2026-11-05). Part 1: the level.

    uv run python scripts/run_baseline_bakeoff.py --part 1

Inputs: data/raw/census_bps_state/st{1990..2025}a.txt (all states), data/raw/baseline_bakeoff/ (fetch script:
hu_1990/st-98-51.txt, hu_api/dec_{2000,2010,2020}_state.json).
Outputs (committed): reference/baseline_bakeoff_part1_{rows,summary,params,by_group,range,coverage,wisconsin}.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware import baseline_bakeoff as bb  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

BB = RAW / "baseline_bakeoff"
WI = "55"
V3_CENTRAL = 124_000
UNIT_COLS = {"1unit": 6, "2units": 9, "3_4units": 12, "5plus": 15}   # estimate columns (units) in state files
STATES = {f"{i:02d}" for i in range(1, 57)} - {"03", "07", "14", "43", "52"}   # 50 states + DC


def read_state_permits() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, geo = [], {}
    for y in range(1990, 2026):
        for line in (RAW / "census_bps_state" / f"st{y}a.txt").read_text(errors="ignore").splitlines()[2:]:
            p = [x.strip() for x in line.split(",")]
            if len(p) < 16 or p[1] not in STATES:
                continue
            geo[p[1]] = dict(state=p[1], region=p[2], division=p[3], name=p[4])
            for z, c in UNIT_COLS.items():
                rows.append(dict(state=p[1], year=y, size=z, units=float(p[c])))
    u = pd.DataFrame(rows)
    if u.groupby(["state", "year"]).size().ne(4).any() or u["state"].nunique() != 51:
        raise SystemExit("state files: expected 51 states x 36 years x 4 sizes")
    return u, pd.DataFrame(geo.values())


def read_census() -> pd.DataFrame:
    rows = []
    lines = (BB / "hu_1990" / "st-98-51.txt").read_text(errors="ignore").splitlines()
    for ln in lines:
        t = ln.split()
        if len(t) > 12 and t[0] == "14" and t[1] in STATES and not ln.startswith("Block"):
            rows.append(dict(state=t[1], year=1990, homes=float(t[-3])))   # 4/1/90 census column
    for y in (2000, 2010, 2020):
        d = json.loads((BB / "hu_api" / f"dec_{y}_state.json").read_text())
        hdr = d[0]
        for r in d[1:]:
            rec = dict(zip(hdr, r))
            if rec["state"] in STATES:
                rows.append(dict(state=rec["state"], year=y, homes=float(rec[hdr[1]])))
    c = pd.DataFrame(rows).drop_duplicates(["state", "year"])
    if c.groupby("year")["state"].nunique().ne(51).any():
        raise SystemExit(f"census housing units: expected 51 states per year, got {c.groupby('year')['state'].nunique().to_dict()}")
    return c


def main() -> None:
    if "--part" not in sys.argv or sys.argv[sys.argv.index("--part") + 1] != "1":
        raise SystemExit("usage: --part 1 (Part 2 is written after the linking table)")
    u, geo = read_state_permits()
    census = read_census()
    allu = u.groupby(["state", "year"], as_index=False)["units"].sum()
    homes = bb.homes_by_year(census, allu, range(1990, 2026))
    division = geo.set_index("state")["division"]
    region = geo.set_index("state")["region"]

    starts = bb.SCORE_STARTS
    params, rows = {}, []
    for c in bb.CANDIDATES:
        if c in bb.FITTED:
            params[c] = {t: bb.fit_param(c, u, homes, t, division) for t in starts}
        rows.append(bb.score_rows(c, u, homes, starts, division, params.get(c)))
    R = pd.concat(rows, ignore_index=True)
    R["region"], R["division"] = R["state"].map(region), R["state"].map(division)

    draws = bb.block_bootstrap_starts(starts)
    base = R[R.candidate == "L0"]
    summ = []
    for c in bb.CANDIDATES:
        r = R[R.candidate == c]
        d = bb.paired_diff(r, base, draws) if c != "L0" else np.zeros(len(draws))
        point = r["abs_log"].mean() - base["abs_log"].mean()
        summ.append(dict(candidate=c, score=r["abs_log"].mean(), bias=r["log_ratio"].mean(),
                         crash_score=r[r.start.between(2005, 2009)]["abs_log"].mean(),
                         wi_score=r[r.state == WI]["abs_log"].mean(), wi_bias=r[r.state == WI]["log_ratio"].mean(),
                         diff_vs_l0=point, boot_lo=np.quantile(d, 0.05), boot_hi=np.quantile(d, 0.95)))
    S = pd.DataFrame(summ)
    l0 = S.set_index("candidate").loc["L0"]
    S["pass_margin"] = S["score"] <= 0.98 * l0["score"]
    S["pass_boot"] = S["boot_hi"] < 0
    S["pass_wi"] = S["wi_score"] <= 1.05 * l0["wi_score"]
    winner = bb.pick(S)
    S["winner"] = S["candidate"] == winner

    # by size, region and division (reported only)
    size_rows = []
    for c in bb.CANDIDATES:
        r = R[R.candidate == c]
        for z in bb.SIZES:
            size_rows.append(dict(candidate=c, group="size", value=z,
                                  score=np.abs(np.log(r[f"pred_{z}"].clip(lower=1e-9) / r[f"actual_{z}"].clip(lower=1e-9))).mean()))
        for g in ("region", "division"):
            for v, rr in r.groupby(g):
                size_rows.append(dict(candidate=c, group=g, value=v, score=rr["abs_log"].mean()))
    G = pd.DataFrame(size_rows)

    # range and coverage for every candidate (winner's is the one used); Wisconsin, start years 1992..2020
    rng_rows, cov_rows, wis = [], [], []
    wi_u = u[u.state == WI]
    for c in bb.CANDIDATES:
        first = {"L1c": 1999, "L1b": 1996, "L1a": 1994, "L4a": 1999}.get(c, 1992)
        ss = list(range(first, 2021))
        par = None
        if c in bb.FITTED:   # fitted per start year with the same no-look-ahead rule (fit years need s <= t-5)
            par = {t: bb.fit_param(c, u, homes, t, division) if t - 5 >= bb.FIRST_FIT_START else np.nan for t in ss}
            ss = [t for t in ss if not np.isnan(par[t])]
        rr = bb.score_rows(c, u, homes, ss, division, par)
        rr = rr[rr.state == WI]
        long = pd.concat([pd.DataFrame(dict(start=rr["start"], size=z, pred=rr[f"pred_{z}"], actual=rr[f"actual_{z}"]))
                          for z in bb.SIZES], ignore_index=True)
        long["ratio"] = long["actual"] / long["pred"]
        m = bb.range_multipliers(long).reset_index().assign(candidate=c, n_starts=len(ss))
        rng_rows.append(m)
        cov = bb.coverage_check(long[["start", "size", "ratio"]], long).assign(candidate=c)
        cov_rows.append(cov)
        # Wisconsin 2027-2031 at start year 2025 (plan log: ratio to L0 x 124,000)
        p25 = None if c not in bb.FITTED else bb.fit_param(c, u, homes, 2025, division)
        pr = bb.predict(c, u, homes, 2025, division, p25) * bb.HORIZON
        wis.append(dict(candidate=c, param=p25, published_five_year=float(pr.loc[WI].sum()),
                        **{f"published_{z}": float(pr.loc[(WI, z)]) for z in bb.SIZES}))
    W = pd.DataFrame(wis)
    w0 = W.set_index("candidate").loc["L0", "published_five_year"]
    W["ratio_to_l0"] = W["published_five_year"] / w0
    W["v3_scaled_central"] = W["ratio_to_l0"] * V3_CENTRAL
    RG, CV = pd.concat(rng_rows, ignore_index=True), pd.concat(cov_rows, ignore_index=True)
    covs = CV.groupby(["candidate", "lo", "hi"])["inside"].agg(["mean", "size"]).reset_index()

    P = pd.DataFrame([dict(candidate=c, start=t, param=v) for c, d in params.items() for t, v in d.items()])
    R.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_rows.csv", index=False)
    S.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_summary.csv", index=False)
    P.to_csv(REFERENCE / "baseline_bakeoff_part1_params.csv", index=False)
    G.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_by_group.csv", index=False)
    RG.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_range.csv", index=False)
    CV.round(1).to_csv(REFERENCE / "baseline_bakeoff_part1_coverage.csv", index=False)
    covs.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_coverage_summary.csv", index=False)
    W.round(1).to_csv(REFERENCE / "baseline_bakeoff_part1_wisconsin.csv", index=False)
    print(S.round(4).to_string(index=False))
    print("winner:", winner)
    print(W.round(1).to_string(index=False))
    print(covs.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

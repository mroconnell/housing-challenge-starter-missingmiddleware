"""ADU causal framework A2 (docs/adu/CAUSAL_FRAMEWORK_PLAN.md, locked before running).

Within California: did places already active under the 2017 law gain more or less from the 2020 package?
Panel: the Gate 3 study panel (adu_main: BuildinganADU for 2017, HCD APR Table A2 from 2018; adu_comp1819 is the
BuildinganADU check for 2018-2019). Rate = permits / (single-family detached homes x observed years) x 1,000.
Before 2017-2019, after 2023-2025. Groups: rule v1 (Gate 3 study cutoff, 2017-2019).
Main measure per group: pooled log rate ratio after / before. Bootstrap over jurisdictions (2,000, seed 20261103).
No-cutoff check: OLS of (after rate - before rate) on before rate, + log home value + log homes (CA_REGRESSION).
Regression-to-the-mean check: groups and X from 2017 only; Y = rate 2019 - g x rate 2018, g = statewide 2019/2018.

Run: uv run python scripts/run_adu_causal_a2.py [--measure adu_comp1819]
Outputs: reference/adu_causal_a2_groups.csv, reference/adu_causal_a2_slopes.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.comparison import ca_regression as cr  # noqa: E402
from missing_middleware.paths import PROCESSED, REFERENCE  # noqa: E402

SEED, NB = 20261103, 2000
BEFORE, AFTER = (2017, 2018, 2019), (2023, 2024, 2025)


def window(s, years):
    w = s[s.year.isin(years)].dropna(subset=["adu"])
    return w.groupby("census_geoid").agg(permits=("adu", "sum"), n=("adu", "count"), homes=("homes", "first"))


def pooled_lrr(b, a):
    return float(np.log((a.permits.sum() / (a.n * a.homes).sum()) / (b.permits.sum() / (b.n * b.homes).sum())))


def ols(X, y):
    X = np.column_stack([np.ones(len(y)), X])
    return np.linalg.lstsq(X, y, rcond=None)[0][1]


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--measure", default="adu_main")
    measure = ap.parse_args().measure
    panel = pd.read_parquet(PROCESSED / "comparison_ca/study/study_panel.parquet")
    s = cr.panel_series(panel, measure)
    cut = cr.published_cutoff(panel, BEFORE, measure)
    g = cr.jurisdiction_groups(s, BEFORE, cut)
    b, a = window(s, BEFORE), window(s, AFTER)
    keep = g.index[g.group.ne("excluded_missing")].intersection(b.index[b.n.eq(3)]).intersection(a.index[a.n.eq(3)])
    b, a, grp = b.loc[keep], a.loc[keep], g.loc[keep, "group"]
    rng = np.random.default_rng(SEED)
    rows = []
    for name in ("restrictive", "middle", "permissive", "all"):
        ids = keep if name == "all" else grp.index[grp.eq(name)]
        est = pooled_lrr(b.loc[ids], a.loc[ids])
        bs = [pooled_lrr(b.loc[x], a.loc[x]) for x in (rng.choice(ids, len(ids)) for _ in range(NB))]
        tot_b = (b.loc[ids].permits, (b.loc[ids].n * b.loc[ids].homes))
        tot_a = (a.loc[ids].permits, (a.loc[ids].n * a.loc[ids].homes))
        loo = [np.log(((tot_a[0].sum() - tot_a[0][i]) / (tot_a[1].sum() - tot_a[1][i])) /
                      ((tot_b[0].sum() - tot_b[0][i]) / (tot_b[1].sum() - tot_b[1][i]))) for i in ids] if len(ids) > 1 else [est]
        rb = b.loc[ids].permits.sum() / (b.loc[ids].n * b.loc[ids].homes).sum() * 1000
        ra = a.loc[ids].permits.sum() / (a.loc[ids].n * a.loc[ids].homes).sum() * 1000
        rows.append(dict(measure=measure, group=name, n_places=len(ids), rate_before=rb, rate_after=ra,
                         difference=ra - rb, ratio=np.exp(est), ratio_p05=np.exp(np.percentile(bs, 5)),
                         ratio_p95=np.exp(np.percentile(bs, 95)), ratio_loo_min=np.exp(min(loo)),
                         ratio_loo_max=np.exp(max(loo)), cutoff=cut))
    groups = pd.DataFrame(rows)

    # covariates as in CA_REGRESSION
    d = pd.read_parquet(PROCESSED / "ca_regression/ca_dataset.parquet").set_index("census_geoid")
    ok = keep.intersection(d.index[d.value.gt(0) & d.homes.gt(0)])
    rb = (b.permits / (b.n * b.homes) * 1000).loc[ok]
    ra = (a.permits / (a.n * a.homes) * 1000).loc[ok]
    Xc = np.column_stack([np.log(d.loc[ok, "value"]), np.log(d.loc[ok, "homes"])])
    slopes = []

    def fit(x, y, label, n_note):
        X = np.column_stack([x, Xc_sub])
        est = ols(X, y)
        idx = np.arange(len(y))
        bs = []
        for _ in range(NB):
            j = rng.choice(idx, len(idx))
            bs.append(ols(X[j], y[j]))
        slopes.append(dict(measure=measure, check=label, n_places=len(y), slope=est, p05=np.percentile(bs, 5),
                           p95=np.percentile(bs, 95), note=n_note))

    Xc_sub = Xc
    fit(rb.to_numpy(), (ra - rb).to_numpy(), "main: change 2017-19 -> 2023-25 on 2017-19 rate",
        "extra permits per 1,000 homes per year, per 1 unit of before rate")
    # regression to the mean, 2017 groups, 2018 vs 2019 relative to statewide growth
    y = {yr: s[s.year.eq(yr)].dropna(subset=["adu"]).set_index("census_geoid") for yr in (2017, 2018, 2019)}
    ok2 = ok.intersection(y[2017].index).intersection(y[2018].index).intersection(y[2019].index)
    r = {yr: (y[yr].adu / y[yr].homes * 1000).loc[ok2] for yr in y}
    gstate = y[2019].adu.loc[ok2].sum() / y[2018].adu.loc[ok2].sum()
    Xc_sub = np.column_stack([np.log(d.loc[ok2, "value"]), np.log(d.loc[ok2, "homes"])])
    fit(r[2017].to_numpy(), (r[2019] - gstate * r[2018]).to_numpy(), "regression to the mean: 2019 - g x 2018 on 2017 rate",
        f"statewide growth g = {gstate:.4f}")
    # group view of the RTM check: 2017-only rule v1 groups, ratio 2019/2018 over statewide
    g17 = cr.jurisdiction_groups(s, (2017,), cr.published_cutoff(panel, (2017,), measure))["group"].loc[ok2]
    for name in ("restrictive", "middle", "permissive"):
        ids = g17.index[g17.eq(name)]
        r18, r19 = y[2018].adu.loc[ids].sum(), y[2019].adu.loc[ids].sum()
        slopes.append(dict(measure=measure, check=f"RTM groups (2017 only): {name}", n_places=len(ids),
                           slope=(r19 / r18) / gstate if r18 > 0 else np.nan, p05=np.nan, p95=np.nan,
                           note="group 2019/2018 ratio divided by statewide; 1 = no regression to the mean"))
    sl = pd.DataFrame(slopes)
    tag = "" if measure == "adu_main" else f"_{measure}"
    groups.round(4).to_csv(REFERENCE / f"adu_causal_a2_groups{tag}.csv", index=False)
    sl.round(4).to_csv(REFERENCE / f"adu_causal_a2_slopes{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(groups.round(3).to_string(index=False)); print(sl.round(4).to_string(index=False))


if __name__ == "__main__":
    main()

"""ADU market-drift check (docs/adu/MARKET_DRIFT_PLAN.md, written and audited before running).

D1: normal drift of a state's all-units permit rate relative to the nation, learned from states with no statewide ADU
law (drift_h = a_h + b_h x heat, h = 1..6), applied to the law states' post-law ADU rates; pooled refit and Wisconsin
engine rerun. Decision: change in Wisconsin's 2027-2031 addition (typical adoption), chain bootstrap, 200 draws.
D2: ADU pre-law growth (Poisson on counts) in Washington, California, Rhode Island vs the 7.3% no-reform trend; the
log-log slope of Washington ADU permits on all-units permits (elasticity line).
Heat = log(state rate / national rate) over 3 years; rate = all units permitted per 1,000 existing homes (Census BPS
state annual files; ACS 2020-2024 B25024 total, fixed).

Run: uv run python scripts/run_adu_market_drift.py [--draws 200]
Outputs: reference/adu_market_drift_*.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_adu_all_homes_check as ahc  # noqa: E402
import run_adu_vermont_options as vto  # noqa: E402
import run_pooled_revision as rv  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED = 20261106
YEARS = range(2010, 2026)
H = range(1, 7)
LAW_FIPS = {"CA": "06", "OR": "41", "VT": "50", "UT": "49", "ME": "23", "MA": "25", "RI": "44", "WA": "53", "CO": "08"}
FIRST_LAW_YEAR = {"CA": 2020, "OR": 2020, "VT": 2021, "UT": 2022, "ME": 2025, "MA": 2025, "RI": 2025, "WA": 2026,
                  "CO": 2025}
WI = "55"
NO_REFORM_TREND = 0.073


def permits() -> pd.DataFrame:
    out = []
    for y in YEARS:
        for line in (RAW / f"census_bps_state/st{y}a.txt").read_text(encoding="latin-1").splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) < 18 or not p[0].startswith(str(y)) or not p[1].isdigit():
                continue
            out.append(dict(fips=p[1].zfill(2), year=y, units=sum(float(p[i] or 0) for i in (6, 9, 12, 15))))
    return pd.DataFrame(out)


def rate_table():
    p = permits()
    h = ahc.homes()
    p = p[p.fips.isin(h.index) & p.fips.isin(set(ahc.STATE_FIPS.values()))]
    tot = p.pivot(index="year", columns="fips", values="units")
    nat = tot.sum(axis=1) / h[tot.columns].sum() * 1000
    rate = tot / h[tot.columns] * 1000
    return rate, nat, p


def heat(rate, nat, fips, y_end):
    yrs = [y_end - 2, y_end - 1, y_end]
    return float(np.log(rate.loc[yrs, fips].mean() / nat.loc[yrs].mean()))


def drift_rows(rate, nat, laws):
    rows = []
    for h in H:
        for y in range(YEARS[0] + 2, YEARS[-1] - h + 1):
            lawset = ahc.law_fips_by(y + h, laws)
            for f in rate.columns:
                if f in lawset:
                    continue
                ht = heat(rate, nat, f, y)
                d = float(np.log(rate.loc[y + h, f] / nat.loc[y + h])) - ht
                rows.append(dict(h=h, origin=y, fips=f, heat=ht, drift=d))
    return pd.DataFrame(rows)


def fit(dr: pd.DataFrame, states=None) -> dict:
    """OLS per horizon. `states`: list of fips (with repeats) for a cluster bootstrap."""
    if states is not None:
        dr = pd.concat([dr[dr.fips.eq(f)] for f in states])
    out = {}
    for h, g in dr.groupby("h"):
        X = np.column_stack([np.ones(len(g)), g.heat])
        a, b = np.linalg.lstsq(X, g.drift.to_numpy(), rcond=None)[0]
        out[int(h)] = (float(a), float(b))
    return out


def law_drifts(coef, rate, nat):
    rows = []
    for c, ly in FIRST_LAW_YEAR.items():
        ht = heat(rate, nat, LAW_FIPS[c], ly - 1)
        for k in H:
            a, b = coef[k]
            yr = ly + k - 1
            actual = (float(np.log(rate.loc[yr, LAW_FIPS[c]] / nat.loc[yr])) - ht) if yr in rate.index else np.nan
            rows.append(dict(cluster=c, law_year=ly, k=k, year=yr, heat=ht, pred_drift=a + b * ht, actual_drift=actual))
    return pd.DataFrame(rows)


def adjusted(p, ld: pd.DataFrame, elasticity: float = 1.0):
    """Divide each law row's ADU count by exp(elasticity x predicted drift at its k)."""
    import missing_middleware.comparison.pooled_regression as pr
    m = ld.set_index(["cluster", "k"])["pred_drift"]
    r = p.rows.copy()
    law = r["law"].eq(1)
    keys = list(zip(r.loc[law, "cluster"], r.loc[law, "k"].astype(int)))
    dr = np.array([m.get(kk, np.nan) for kk in keys])
    if np.isnan(dr).any():
        raise SystemExit(f"missing drift for {set(k for k, d in zip(keys, dr) if np.isnan(d))}")
    r.loc[law, "count"] = r.loc[law, "count"].to_numpy() * np.exp(-elasticity * dr)
    return pr.Pooled(r, p.members)


def run_engine(p, ctx, ref_dir, tag):
    vto.pooled_for = lambda opt, d_, pan_, _p=p: _p
    o = vto.engine_option(tag, ctx, ref_dir)
    t = o["totals"]
    return dict(lower=t["lower"], central=t["central"], upper=t["upper"], ref_line=float(o["ref_line"].additional_5yr))


def poisson_growth(counts, homes, years):
    """Year slope of a Poisson GLM (log link, log homes offset) by IRLS; returns yearly growth exp(slope) - 1."""
    y, off = np.asarray(counts, float), np.log(np.asarray(homes, float))
    X = np.column_stack([np.ones(len(y)), np.asarray(years, float) - np.mean(years)])
    beta = np.array([np.log(max(y.mean(), 0.5)) - off.mean(), 0.0])
    for _ in range(100):
        mu = np.exp(X @ beta + off)
        step = np.linalg.solve(X.T @ (mu[:, None] * X), X.T @ (y - mu))
        beta += step
        if np.abs(step).max() < 1e-10:
            break
    return float(np.expm1(beta[1]))


def d2(rate, rng):
    a = pd.read_csv(REFERENCE / "statewide_states_annual.csv")
    rows = []
    wa = a[a.series.eq("WA_inc_exSeattle") & a.year.lt(2026)].sort_values("year")
    ca = pd.read_csv(ROOT / "data/processed/comparison_ca/adu_compilation_2012_2019.csv")
    ca = ca[ca.year.le(2016)].groupby("year").adu_permits.sum().reset_index()
    ca_homes = float([ln.split("|")[3] for ln in open(RAW / "census_acs5_2024_tbsf/acsdt5y2024-b25024.dat", encoding="utf-8")
                      if ln.startswith("0400000US06")][0])
    for name, yrs, cnt, hom in (("WA", wa.year.to_numpy(), wa.adu_count.to_numpy(), wa.homes.to_numpy()),
                                ("CA", ca.year.to_numpy(), ca.adu_permits.to_numpy(), np.full(len(ca), ca_homes))):
        g = poisson_growth(cnt, hom, yrs)
        bs = []
        for _ in range(2000):
            j = rng.integers(0, len(yrs), len(yrs))
            if len(set(yrs[j])) < 2:
                continue
            bs.append(poisson_growth(cnt[j], hom[j], yrs[j]))
        lo, hi = np.percentile(bs, [5, 95])
        rows.append(dict(state=name, years=f"{yrs.min()}-{yrs.max()}", growth=g, p05=lo, p95=hi,
                         excludes_7_3=bool(lo > NO_REFORM_TREND or hi < NO_REFORM_TREND), flag=""))
    ri = a[a.series.eq("RI_statewide") & a.year.between(2021, 2023)].sort_values("year")
    gr = float((ri.adu_count.iloc[-1] / ri.adu_count.iloc[0]) ** (1 / (len(ri) - 1)) - 1)
    rows.append(dict(state="RI", years="2021-2023", growth=gr, p05=np.nan, p95=np.nan, excludes_7_3=np.nan,
                     flag="2 year-on-year steps; no interval"))
    # Washington elasticity: log ADU permits on log all-units permits (BPS), by year
    w = wa.set_index("year")
    yrs = np.array([y for y in w.index if y in rate.index])
    lx = np.log(rate.loc[yrs, LAW_FIPS["WA"]].to_numpy())
    ly = np.log(w.loc[yrs, "adu_count"].to_numpy() / w.loc[yrs, "homes"].to_numpy())

    def slope(x, y):
        return float(np.polyfit(x, y, 1)[0])
    el = slope(lx, ly)
    bs = [slope(lx[j], ly[j]) for j in (rng.integers(0, len(yrs), len(yrs)) for _ in range(2000)) if len(set(j)) > 2]
    elas = dict(estimate=el, p05=float(np.percentile(bs, 5)), p95=float(np.percentile(bs, 95)), n_years=len(yrs),
                years=f"{yrs.min()}-{yrs.max()}",
                note="OFM estimate years (April-March) against BPS calendar years; log-log OLS; bootstrap over years")
    return pd.DataFrame(rows), elas


def panel_match(p):
    b = pd.read_csv(REFERENCE / "baseline_bakeoff_part1_rows.csv", dtype={"state": str})
    b = b[b.candidate.eq(b.candidate.iloc[0]) & b.start.between(YEARS[0] - 1, YEARS[-1] - 5)].drop_duplicates(["state", "start"])
    tot = p.pivot(index="year", columns="fips", values="units")
    rows = []
    for x in b.itertuples():
        f = x.state.zfill(2)
        if f not in tot.columns:
            continue
        bps = float(tot.loc[x.start + 1:x.start + 5, f].sum())   # panel: origin year, then the next 5
        if abs(bps - x.actual) > 0.5:
            rows.append(dict(state=f, start=x.start, baseline_panel=x.actual, bps=bps, diff=x.actual - bps))
    return pd.DataFrame(rows), len(b)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    n_draws = ap.parse_args().draws
    rng = np.random.default_rng(SEED)
    rate, nat, p_raw = rate_table()
    laws = pd.read_csv(REFERENCE / "statewide_states_laws.csv")
    dr = drift_rows(rate, nat, laws)
    mism, n_cmp = panel_match(p_raw)
    mism.to_csv(REFERENCE / "adu_market_drift_panel_check.csv", index=False)
    print(f"panel check: {len(mism)} of {n_cmp} state-window totals differ from BPS (BPS wins)")
    coef = fit(dr)
    ld = law_drifts(coef, rate, nat)
    d2t, elas = d2(rate, rng)

    ctx = vto.context()
    base_p = rv.build(ctx["d"], ctx["pan"])
    rows = []
    with vto.temp_reference() as ref_dir:
        adopted = run_engine(base_p, ctx, ref_dir, "drift_adopted")
        main_ = run_engine(adjusted(base_p, ld), ctx, ref_dir, "drift_main")
        el_line = run_engine(adjusted(base_p, ld, elas["estimate"]), ctx, ref_dir, "drift_wa_elasticity")
        # post hoc diagnostic (not in the plan): heat term only, intercepts a_h set to 0
        ld0 = law_drifts({h: (0.0, b) for h, (a, b) in coef.items()}, rate, nat)
        heat_only = run_engine(adjusted(base_p, ld0), ctx, ref_dir, "drift_heat_only")
        # post hoc diagnostic (audit, 2026-11-06): national rate equal-weighted across states, removing the weighting
        # mismatch between equal-weighted states and the home-weighted national rate
        nat_eq = rate.mean(axis=1)
        coef_eq = fit(drift_rows(rate, nat_eq, laws))
        ld_eq = law_drifts(coef_eq, rate, nat_eq)
        eq_line = run_engine(adjusted(base_p, ld_eq), ctx, ref_dir, "drift_equal_weight")
        st = pd.read_csv(REFERENCE / "adu_model_statewide.csv").set_index("path")["additional_units"]
        if abs(adopted["central"] - st["central"]) > 0.5:
            raise SystemExit("adopted run does not reproduce the tool's central")
        nonlaw = sorted(dr.fips.unique())
        for i in range(n_draws):
            pick = rng.choice(nonlaw, len(nonlaw), replace=True)
            cb = fit(dr, pick)
            o = run_engine(adjusted(base_p, law_drifts(cb, rate, nat)), ctx, ref_dir, f"drift_b{i}")
            rows.append(dict(draw=i, central=o["central"], change=o["central"] - adopted["central"],
                             b1=cb[1][1], b4=cb[4][1]))
            if i % 20 == 0:
                print(f"draw {i}: change {rows[-1]['change']:.0f}", flush=True)
    bs = pd.DataFrame(rows)
    lo, hi = np.percentile(bs.change, [5, 95])
    verdict = "no measurable drift effect" if lo <= 0 <= hi else "drift effect measured"

    # Wisconsin's own heat and drift (ADU baseline only, report)
    wi_heat = heat(rate, nat, WI, 2025)
    by = pd.read_csv(REFERENCE / "adu_model_statewide_by_year.csv")
    base_y = by[by.path.eq("central")].sort_values("year").baseline_units.to_numpy()
    wi_base_adj = float(sum(b * np.exp(coef[h][0] + coef[h][1] * wi_heat) for b, h in zip(base_y, range(2, 7))))

    pd.DataFrame([dict(h=h, a=a, b=b, n=int((dr.h == h).sum()), n_states=dr[dr.h == h].fips.nunique())
                  for h, (a, b) in coef.items()]).round(5).to_csv(REFERENCE / "adu_market_drift_fit.csv", index=False)
    ld.round(5).to_csv(REFERENCE / "adu_market_drift_law_states.csv", index=False)
    pd.DataFrame([dict(h=h, a=a, b=b) for h, (a, b) in coef_eq.items()]).round(5).to_csv(
        REFERENCE / "adu_market_drift_fit_equal_weight.csv", index=False)
    d2t.round(5).to_csv(REFERENCE / "adu_market_drift_d2_pretrends.csv", index=False)
    pd.DataFrame([elas]).round(5).to_csv(REFERENCE / "adu_market_drift_d2_wa_elasticity.csv", index=False)
    bs.round(3).to_csv(REFERENCE / "adu_market_drift_bootstrap.csv", index=False)
    summ = pd.DataFrame([
        dict(line="adopted", **adopted),
        dict(line="drift-adjusted, ADUs 1-for-1 with all housing (main)", **main_),
        dict(line=f"drift-adjusted, Washington elasticity {elas['estimate']:.3f}", **el_line),
        dict(line="post hoc diagnostic: heat term only (intercepts set to 0)", **heat_only),
        dict(line="post hoc diagnostic: equal-weighted national rate", **eq_line)])
    summ["change_central"] = summ.central - adopted["central"]
    summ["a3_low"] = summ.central * 8055.144 / 10491.996
    summ["a3_high"] = summ.central * 13666.047 / 10491.996
    summ.round(1).to_csv(REFERENCE / "adu_market_drift_summary.csv", index=False)
    pd.DataFrame([dict(change_p05=lo, change_p50=float(np.median(bs.change)), change_p95=hi, draws=len(bs),
                       verdict=verdict, wi_heat_2023_2025=wi_heat, wi_adu_baseline_adopted=float(base_y.sum()),
                       wi_adu_baseline_drift_scaled=wi_base_adj)]).round(4).to_csv(
        REFERENCE / "adu_market_drift_decision.csv", index=False)
    pd.set_option("display.width", 220)
    print(pd.read_csv(REFERENCE / "adu_market_drift_fit.csv").to_string(index=False))
    print(ld[ld.k.eq(1)].round(3).to_string(index=False))
    print(summ.round(0).to_string(index=False))
    print(d2t.round(3).to_string(index=False)); print(elas)
    print(f"change in WI central: 90% {lo:.0f} to {hi:.0f} -> {verdict}; WI heat {wi_heat:.3f}, "
          f"ADU baseline {base_y.sum():.0f} -> {wi_base_adj:.0f}")


if __name__ == "__main__":
    main()

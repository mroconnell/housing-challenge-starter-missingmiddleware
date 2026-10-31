"""Parking: Wisconsin permits after reform minus without reform, route B (docs/parking/NET_WI_PLAN.md).

    uv run --all-extras python scripts/run_parking_net_wi.py --round N

The no-reform model (scripts/run_parking_no_reform.py, round 3 data) refit with a dated trait for a material
parking repeal; the Wisconsin net is the prediction with the trait on minus off, from origin 2025 (2027-2031).
Outputs: reference/parking_net_wi_{scores,net,places,checks}_rN.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROUND = int(sys.argv[sys.argv.index("--round") + 1]) if "--round" in sys.argv else 1
_argv = sys.argv
sys.argv = [sys.argv[0], "--round", "4"]  # the no-reform model's round 4 data (leak fixed)
import run_parking_no_reform as NR  # noqa: E402
sys.argv = _argv
from missing_middleware.parking import checks  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

TAG = f"_r{ROUND}"
RESAMPLES = 20
CENTRAL, PUBLISHED = 122_619, 118_822
COLS = {"M4 boosted trees": ("hgb", NR.BASE + NR.ACS + ["reform"]),
        "M3b regression + ACS": ("glm", NR.BASE + NR.ACS + ["reform"])}


def fit_model(kind, cols, fit, seed, setting):
    return NR.fit_glm(fit, cols, setting) if kind == "glm" else NR.fit_hgb(fit, cols, *setting, seed)


def on_off(m, kind, cols, df, fit):
    med = fit[cols].median() if kind == "glm" else None
    return NR.pred_rate(m, df.assign(reform=1), cols, med), NR.pred_rate(m, df.assign(reform=0), cols, med)


def main() -> None:
    R, reform_year, months, geo, shared, shared_keys = NR.prepare()
    ry = R["reform_year"].values
    o = R["origin"].values
    treated = (ry >= o - 1) & (ry <= o + 2) & (ry != 9999) & (ry > 0)
    R["reform"] = np.where(treated, 1, 0)
    use = R[R["no_reform"] | treated].copy()
    data = use[use["actual"].notna() & (use["state_fips"] != NR.WI)]
    reform_keys = np.array(sorted(data.loc[data["reform"] == 1, "key"].unique()))
    wi = R[(R["state_fips"] == NR.WI) & (R["origin"] == 2025)].copy()
    wi_open = wi[wi["key"].map(lambda k: reform_year.get(k, 9999) == 9999)]  # places that still have minimums
    m0_sum = float(wi["units_3y"].sum())
    scale = CENTRAL / (5 * m0_sum)  # model places -> whole state, by the baseline's own ratio (round 2 fix: m0_sum is per year)

    flags = [dict(check="reform rows", where="training", value=int(data["reform"].sum()),
                  note=f"{len(reform_keys)} reform places; trait = material repeal from 1 year before to 2 years after the origin")]
    odd = data[(data["reform"] == 1) & (data["actual"] / data["homes"] * 1000 > data["origin"].map(
        (data["actual"] / data["homes"] * 1000).groupby(data["origin"]).quantile(0.99)))]
    flags += [dict(check="reform row outcome above national 99th percentile (per 1,000 homes)", where=f"{r.name} {r.key}",
                   value=round(r.actual / r.homes * 1000, 1), note=f"origin {r.origin}, homes {r.homes:.0f}") for r in odd.itertuples()]

    score_rows, net_rows, place_rows, miss_rows, fake_trace = [], [], [], [], []
    for seed in NR.SEEDS:
        rng = np.random.default_rng(seed)
        held = set(rng.choice(reform_keys, size=max(1, int(round(0.2 * len(reform_keys)))), replace=False))
        fit = data[~data["key"].isin(held)]
        te = data[data["key"].isin(held) & (data["reform"] == 1)]
        for name, (kind, cols) in COLS.items():
            setting = NR.choose(fit, cols, kind, seed)[0]
            m = fit_model(kind, cols, fit, seed, setting)
            on, off = on_off(m, kind, cols, te, fit)
            if name == "M4 boosted trees":  # round 3: trace the held-out reform places' misses
                miss_rows.append(te[["key", "name", "origin", "reform_year", "homes", "units_3y", "actual"]].assign(seed=seed, pred_on=on, pred_off=off))
            for lab, pr in (("trait on (reform)", on), ("trait off (no reform)", off)):
                score_rows.append(dict(seed=seed, model=name, test="held-out reform places", prediction=lab,
                                       **NR.score(pr, te["actual"].values)))
            # Wisconsin net from the full fit (no held-out places), then resamples of reform places
            for b in range(RESAMPLES + 1):
                if b == 0:
                    fb = data
                else:
                    pick = rng.choice(reform_keys, size=len(reform_keys))
                    rows_t = pd.concat([data[data["key"] == k] for k in pick])
                    fb = pd.concat([data[data["reform"] == 0], rows_t])
                mb = fit_model(kind, cols, fb, seed, setting)
                won, woff = on_off(mb, kind, cols, wi_open, fb)
                net5 = float((won - woff).sum() * 5 * scale)
                net_rows.append(dict(seed=seed, model=name, resample=b, net_2027_2031=net5,
                                     net_2027_2031_published=net5 * PUBLISHED / CENTRAL,
                                     net_per_1000_homes_per_year=float((won - woff).sum() / wi_open["homes"].sum() * 1000)))
                if b == 0:
                    place_rows.append(wi_open[["key", "name", "homes", "units_3y"]].assign(seed=seed, model=name, on=won, off=woff,
                                                                                             net_per_year=won - woff))
        # noise floor: a fake reform on no-reform places, same fit, same Wisconsin read-out
        fake_keys = set(rng.choice(data.loc[data["reform"] == 0, "key"].unique(), size=len(reform_keys), replace=False))
        fd = data[data["reform"] == 0].copy()
        # round 2 fix: like a real repeal, the fake one is on only at origins 1 year before to 2 years after a fake year
        real_y = data.loc[data["reform"] == 1, "reform_year"].astype(int).values
        fy = {k: int(rng.choice(real_y)) for k in sorted(fake_keys)}  # sorted: set order changes between runs (round 4 fix)
        fd["reform"] = [int(k in fy and o - 1 <= fy[k] <= o + 2) for k, o in zip(fd["key"], fd["origin"])]
        # round 5 trace: how the fake-reform rows differ from the rest (change in permits per 1,000 homes per year)
        chg = (fd["actual"] - fd["units_3y"]) / fd["homes"] * 1000
        on_rows = fd[fd["reform"] == 1]
        top = on_rows.assign(chg=chg[fd["reform"] == 1]).sort_values("chg", ascending=False).head(3)
        fake_trace.append(dict(seed=seed, fake_rows=len(on_rows), fake_change=float(chg[fd["reform"] == 1].mean()),
                               other_change=float(chg[fd["reform"] == 0].mean()),
                               top=", ".join(f"{r.name} {r.chg:+.0f}" for r in top.itertuples())))
        for name, (kind, cols) in COLS.items():
            setting = NR.choose(fd, cols, kind, seed)[0] if kind == "glm" else (0.05, 15)
            mf = fit_model(kind, cols, fd, seed, setting)
            won, woff = on_off(mf, kind, cols, wi_open, fd)
            net_rows.append(dict(seed=seed, model=name + " | fake reform", resample=0,
                                 net_2027_2031=float((won - woff).sum() * 5 * scale),
                                 net_per_1000_homes_per_year=float((won - woff).sum() / wi_open["homes"].sum() * 1000)))
        print("seed", seed, "done", flush=True)

    S = pd.DataFrame(score_rows)
    N = pd.DataFrame(net_rows)
    P = pd.concat(place_rows, ignore_index=True)
    S.to_csv(REFERENCE / f"parking_net_wi_scores{TAG}.csv", index=False)
    N.to_csv(REFERENCE / f"parking_net_wi_net{TAG}.csv", index=False)
    P.to_csv(REFERENCE / f"parking_net_wi_places{TAG}.csv", index=False)
    top = P[P["model"] == "M4 boosted trees"].groupby(["key", "name"])[["homes", "units_3y", "net_per_year"]].mean() \
        .sort_values("net_per_year", key=abs, ascending=False).head(10).reset_index()
    flags += [dict(check="largest Wisconsin net (M4, mean over seeds)", where=f"{r.name} {r.key}", column="net per year",
                   value=round(r.net_per_year, 1), note=f"homes {r.homes:.0f}, same-pace permits {r.units_3y:.0f} per year")
              for r in top.itertuples()]
    if miss_rows:
        M = pd.concat(miss_rows, ignore_index=True).assign(miss=lambda d: d["pred_on"] - d["actual"])
        M.to_csv(REFERENCE / f"parking_net_wi_heldout_reform{TAG}.csv", index=False)
        for r in M.reindex(M["miss"].abs().sort_values(ascending=False).index).drop_duplicates("key").head(5).itertuples():
            flags.append(dict(check="held-out reform place, largest miss (M4, trait on)", where=f"{r.name} {r.key}",
                              column="homes per year", value=round(r.miss),
                              note=f"origin {r.origin}, repeal {int(r.reform_year)}, actual {r.actual:.0f}, same pace {r.units_3y:.0f}, on {r.pred_on:.0f}, off {r.pred_off:.0f}"))
    for t in fake_trace:
        flags.append(dict(check="fake-reform rows vs the rest (change per 1,000 homes per year)", where=f"seed {t['seed']}",
                          value=round(t["fake_change"] - t["other_change"], 2),
                          note=f"{t['fake_rows']} fake rows: {t['fake_change']:+.2f} vs {t['other_change']:+.2f}; fastest: {t['top']}"))
    fk = N[N["model"].str.contains("fake")]
    for r in fk.itertuples():
        flags.append(dict(check="fake-reform Wisconsin net by seed", where=r.model, column="homes 2027-2031",
                          value=round(r.net_2027_2031), note=f"seed {r.seed}"))
    checks.report(flags, REFERENCE / f"parking_net_wi_checks{TAG}.csv")

    pd.set_option("display.width", 200)
    print(S.groupby(["model", "prediction"])[["median_abs_log", "total_ratio"]].agg(["mean", "min", "max"]).round(3).to_string())
    g = N.groupby("model")
    print(pd.DataFrame({"full fit (mean of seeds)": N[N["resample"] == 0].groupby("model")["net_2027_2031"].mean(),
                        "p05": g["net_2027_2031"].quantile(0.05), "p95": g["net_2027_2031"].quantile(0.95),
                        "per 1,000 homes/yr": N[N["resample"] == 0].groupby("model")["net_per_1000_homes_per_year"].mean()}).round(1).to_string())
    print(f"Wisconsin places {len(wi)}, still with minimums {len(wi_open)}, scale to state {scale:.3f}")


if __name__ == "__main__":
    main()

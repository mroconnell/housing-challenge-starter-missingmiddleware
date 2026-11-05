"""Test 53 (CAUSAL_FRAMEWORK_PLAN.md, "Test 53" and its audit fixes): core city vs non-core metro vs outside metro.

Groups from reference/parking_place_ruca_traits.csv (`area_class`, Feb 2013 principal cities; `area_class_pc2023` as the
check). Main = the batch's per-place main effects (homes x after-years weights); D = the batch's per-place method-2 D
effects (target-state mix aimed at Wisconsin cells). Ranges: place bootstrap, 2,000 draws, seed 20261105; differences
resample places within each group. Class-matched pools: D rerun with each repeal place's eligible pool limited to its
own group (patching run_parking_method2.eligible; no edit), batch ladder unchanged.

    MM_REFERENCE_DIR=<batch working copy> MM_GATE_TIME=15:50 uv run --all-extras python scripts/run_parking_t53_area.py
Outputs: reference/parking_t53_groups.csv, parking_t53_class_matched_places.csv, parking_t53_class_matched.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import run_parking_method2 as m  # noqa: E402
import run_parking_t52_pool_rules as pr  # noqa: E402  (mix_avg, paired)

OUT = ROOT / "reference"
BATCH = OUT / "batch_2026-11-05"
SEED, DRAWS = 20261105, 2000
MIX = "target-state mix"
GROUP = {"core": "core", "suburb": "non-core metro", "exurb": "non-core metro", "rural part of metro": "non-core metro",
         "non-metro": "outside metro"}


def boot(y, w_fn, draws=DRAWS, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(y)
    return np.array([w_fn(rng.integers(0, n, n)) for _ in range(draws)])


def main() -> None:
    m.SUF, m.CORRECTED = "_corrected", True
    D = m.Data()
    real, cases = m.real_cases()
    assert len(cases) == 74
    T = pd.read_csv(OUT / "parking_place_ruca_traits.csv", dtype={"key": str}).set_index("key")
    keys = [c["key"] for c in cases]
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(k, 0.0) for k in keys]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = m.target_cells(D, "55")
    bp = pd.read_csv(BATCH / "parking_method2_corrected_places.csv")
    bp = bp[bp["variant"] == "method 2, D"].reset_index(drop=True)
    assert (bp["place"].values == np.array([c["place"] for c in cases])).all()
    yD = bp["effect"].values.astype(float)
    me = pd.read_csv(BATCH / "parking_expanded_effects.csv", dtype={"key": str})
    me = me[(me["outcome"] == "all") & me["effect"].notna()].set_index("key")
    yM = me["effect"].reindex(keys).values.astype(float)
    wM = me["weight"].reindex(keys).values.astype(float)
    rows = []
    for col, label in (("area_class", "2013 principal cities (main)"), ("area_class_pc2023", "2023 principal cities (check)")):
        g = pd.Series([GROUP.get(T[col].get(k), "unknown") for k in keys])
        est = {}
        for grp in ("core", "non-core metro", "outside metro"):
            idx = np.flatnonzero((g == grp).values)
            okD = idx[np.isfinite(yD[idx])]
            okM = idx[np.isfinite(yM[idx])]
            eD = ev.iloc[okD].reset_index(drop=True)
            aD = m.weighted_avg(MIX, yD[okD], eD, wi)
            bD = boot(yD[okD], lambda i: m.weighted_avg(MIX, yD[okD][i], eD.iloc[i].reset_index(drop=True), wi))
            aM = float(np.average(yM[okM], weights=wM[okM]))
            bM = boot(yM[okM], lambda i: float(np.average(yM[okM][i], weights=wM[okM][i])))
            est[grp] = (bD, bM)
            for est_name, a, b, n in (("D", aD, bD, len(okD)), ("main", aM, bM, len(okM))):
                lo, hi = np.nanpercentile(b, [5, 95])
                rows.append(dict(groups=label, row=grp, estimator=est_name, places=n, rate=a, p05=lo, p95=hi,
                                 wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K,
                                 places_list="; ".join(real["place"].iloc[idx]) if grp == "outside metro" or (g == grp).sum() <= 8 else ""))
        # differences: independent within-group resamples (draw d of each group's bootstrap)
        for other in ("non-core metro", "outside metro"):
            for k, est_name in ((0, "D"), (1, "main")):
                d = est["core"][k] - est[other][k]
                a = next(r["rate"] for r in rows if r["groups"] == label and r["row"] == "core" and r["estimator"] == est_name) - \
                    next(r["rate"] for r in rows if r["groups"] == label and r["row"] == other and r["estimator"] == est_name)
                lo, hi = np.nanpercentile(d, [5, 95])
                rows.append(dict(groups=label, row=f"core minus {other}", estimator=est_name, rate=a, p05=lo, p95=hi,
                                 wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K, excludes_0=bool(lo > 0 or hi < 0)))
    R = pd.DataFrame(rows)
    R.round(4).to_csv(OUT / "parking_t53_groups.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.drop(columns=["places_list"]).round(3).to_string(index=False))
    # exurbs as a list of cases
    ex = [c["place"] for c in cases if T["area_class"].get(c["key"]) == "exurb"]
    print("exurbs:", ex)

    # class-matched pools (D)
    grp_of = {k: GROUP.get(v, "unknown") for k, v in T["area_class"].items()}
    orig = m.eligible
    cur = {}

    def elig(D_, target, years, mode_exc, shock_on, h):
        E = orig(D_, target, years, mode_exc, shock_on, h)
        tg = cur.get("g")
        return [k for k in E if grp_of.get(k) == tg] if tg else E
    m.eligible = elig
    out = []
    try:
        for c, gname in zip(cases, [GROUP.get(T["area_class"].get(k), "unknown") for k in keys]):
            cur["g"] = gname if gname != "unknown" else None
            pl = m.long_pre(c["event_year"], list(c["pre"]), c.get("trimmed", False))
            h = D.homes_pre(c["event_year"], False)
            n_el = len(m.eligible(D, c["key"], list(pl) + list(c["post"]), "strict", True, h))
            r = m.case_effect(D, c, "D", m.OPT_MAIN)
            out.append(dict(place=c["place"], state=c["state"], group=gname, effect=r["effect"], step=r["step"],
                            n_pool=r["n_pool"], n_eligible_in_class=n_el, batch_effect=yD[len(out)]))
    finally:
        m.eligible = orig
    P = pd.DataFrame(out)
    P.round(4).to_csv(OUT / "parking_t53_class_matched_places.csv", index=False)
    y = P["effect"].values.astype(float)
    ok = np.isfinite(y)
    a = pr.mix_avg(y[ok], ev[ok], wi)
    lo, hi = m.boot_range(MIX, y[ok], ev[ok].reset_index(drop=True), wi, m.BOOT, m.SEED)
    s, slo, shi, npair = pr.paired(y, yD, ev, wi)
    S = pd.DataFrame([dict(variant="D, class-matched pools", places=int(ok.sum()), rate=a, p05=lo, p95=hi, wi_homes=a * m.WI_K,
                           wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K, shift=s, shift_p05=slo, shift_p95=shi, shift_wi=s * m.WI_K,
                           shift_wi_p05=slo * m.WI_K, shift_wi_p95=shi * m.WI_K,
                           pools_off_ladder_step1=int((P["step"].astype(str) != P["step"].astype(str).mode()[0]).sum()),
                           median_eligible_in_class=float(P["n_eligible_in_class"].median()))])
    S.round(4).to_csv(OUT / "parking_t53_class_matched.csv", index=False)
    print(S.round(3).T.to_string())
    print(P.groupby("step").size().to_string())


if __name__ == "__main__":
    main()

"""ADU improvement loop, round 1 (docs/adu/IMPROVE_R1_PLAN.md, written before running).

Data variants V0-V4 x models M1 (plain average), M2 (median), M3 (adopted two-stage), scored by leaving each
non-California statewide-law state out in turn. M3 also runs the Wisconsin engine step for each variant.
Units: ADU permits per 1,000 one-unit detached homes per year; log error = log(predicted / observed).

Run: uv run python scripts/run_adu_improve.py   (about 2 minutes)
Outputs: reference/adu_improve_r1_scores.csv, adu_improve_r1_by_state.csv, adu_improve_r1_flags.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_adu_vermont_options as vto  # noqa: E402
import run_pooled_revision as rv  # noqa: E402
from missing_middleware.comparison import homes_by_year as hb  # noqa: E402
from missing_middleware.comparison import pooled_regression as pr  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

STATES = pr.STATEWIDE_STATES                    # the 7 non-California statewide-law states
ME_HOMES_SHARE = 0.62                           # largest towns holding 73% of Maine's people hold 62% of its homes
RI_EARLY_SHARE = 0.8704                         # homes share of the towns reporting in 2023 and 2024
VARIANTS = {
    "V0": "current data",
    "V1": "Vermont by permit year (counts one year earlier)",
    "V2": "Maine homes share 0.62",
    "V3": "Rhode Island 2021-2022 homes share 0.8704",
    "V4": "V1 + V2 + V3",
}


def shift_vermont(rows: pd.DataFrame) -> pd.DataFrame:
    """Year built -> permit year: each Vermont count moves one year earlier; k falls by one; k < 1 dropped."""
    r = rows.copy()
    vt = r["series"].eq("VT_chittenden")
    r.loc[vt, "year"] = r.loc[vt, "year"] - 1
    r.loc[vt, "k"] = r.loc[vt, "k"] - 1
    return r[~(vt & (r["k"] < 1))].reset_index(drop=True)


def build_variant(v: str, d, pan) -> pr.Pooled:
    cov = {}
    if v in ("V2", "V4"):
        cov["ME_statewide"] = {2025: ME_HOMES_SHARE}
    if v in ("V3", "V4"):
        cov["RI_statewide"] = {2021: RI_EARLY_SHARE, 2022: RI_EARLY_SHARE}
    vt = v in ("V1", "V4")
    p = rv.build(d, pan, coverage_override=cov or None, year_homes=not vt)
    if not vt:
        return p
    rows = hb.apply_homes_index(shift_vermont(p.rows), rv.homes_index(), rv.CLUSTER_FIPS)
    return pr.Pooled(rows, p.members)


def state_rates(p: pr.Pooled) -> pd.Series:
    """Observed post-law rate per state: permits / (homes x years) x 1,000 over its law rows."""
    r = p.rows.assign(homes=p.row_homes().values)
    r = r[r["law"].eq(1) & pr.eval_mask(p.rows)]
    g = r.groupby("cluster")
    return g["count"].sum() / (g.apply(lambda x: (x["years"] * x["homes"]).sum(), include_groups=False)) * 1000


def flags(v: str, p: pr.Pooled) -> list[dict]:
    out = []
    r = p.rows.assign(homes=p.row_homes().values)
    r["rate"] = r["count"] / (r["years"] * r["homes"]) * 1000
    for x in r.itertuples():
        if not 0 <= x.rate <= 10:
            out.append(dict(variant=v, flag="rate outside 0-10 per 1,000 homes per year", series=x.series, year=x.year,
                            detail=f"{x.rate:.2f}"))
    for s, note in (("VT_chittenden", "counts by year built or first occupied, not permit year"),
                    ("UT_mih", "MIH report year (Aug-Jul), self-reported, internal ADUs only"),
                    ("WA_inc_exSeattle", "OFM estimate year (Apr-Mar)")):
        if s in set(r["series"]):
            out.append(dict(variant=v, flag="outcome or year basis differs", series=s, year="", detail=note))
    for s, ys in pr.COVERAGE.items():
        for y, sh in ys.items():
            out.append(dict(variant=v, flag="reporting share applied", series=s, year=y, detail=f"{sh:.4f}"))
    for (s, y), f in pr.PARTIAL_YEAR.items():
        out.append(dict(variant=v, flag="partial year", series=s, year=y, detail=f"{f:.4f} of a year"))
    return out


def main():
    ctx = vto.context()
    d, pan = ctx["d"], ctx["pan"]
    scores, by_state, flag_rows = [], [], []
    with vto.temp_reference() as ref_dir:
        for v, label in VARIANTS.items():
            p = build_variant(v, d, pan)
            vto.pooled_for = lambda opt, d_, pan_, _p=p: _p     # engine_option fits this variant's rows
            o = vto.engine_option(v, ctx, ref_dir)
            la = vto.loso(p, vto.CFG_A, STATES)
            rates = state_rates(p)
            for s in STATES:
                others = rates.drop(s)
                obs = float(la.loc[s, "obs_rate"])
                for m, pred in (("M1 plain average", float(others.mean())), ("M2 median", float(others.median())),
                                ("M3 adopted", float(la.loc[s, "pred_rate"]))):
                    by_state.append(dict(variant=v, model=m, state=s, obs_rate=obs, pred_rate=pred,
                                         log_error=float(np.log(pred / obs))))
            b = pd.DataFrame([x for x in by_state if x["variant"] == v])
            rms = b.groupby("model")["log_error"].apply(lambda e: float(np.sqrt(np.mean(e ** 2))))
            m3 = b[b.model.eq("M3 adopted")].set_index("state")["log_error"]
            worst = m3.abs().idxmax()
            scores.append(dict(variant=v, label=label, rms_m1_plain_average=rms["M1 plain average"],
                               rms_m2_median=rms["M2 median"], rms_m3_adopted=rms["M3 adopted"],
                               worst_state_m3=worst, worst_log_error_m3=float(m3[worst]),
                               lower_additional_5yr=o["totals"]["lower"], central_additional_5yr=o["totals"]["central"],
                               upper_additional_5yr=o["totals"]["upper"],
                               reference_line_additional_5yr=float(o["ref_line"].additional_5yr),
                               baseline_5yr=o["baseline_5yr"]))
            flag_rows += flags(v, p)
            print(v, {k: (round(x, 4) if isinstance(x, float) else x) for k, x in scores[-1].items()})
    sc = pd.DataFrame(scores)
    st = pd.read_csv(REFERENCE / "adu_model_statewide.csv").set_index("path")["additional_units"]
    if abs(sc.iloc[0].central_additional_5yr - st["central"]) > 0.5:
        raise SystemExit("V0 does not reproduce the adopted central")
    sc.round(4).to_csv(REFERENCE / "adu_improve_r1_scores.csv", index=False)
    pd.DataFrame(by_state).round(4).to_csv(REFERENCE / "adu_improve_r1_by_state.csv", index=False)
    pd.DataFrame(flag_rows).to_csv(REFERENCE / "adu_improve_r1_flags.csv", index=False)
    pd.set_option("display.width", 250)
    print(sc.round(3).to_string(index=False))
    print(pd.DataFrame(by_state).pivot_table(index=["state"], columns=["variant", "model"], values="log_error").round(3)
          .to_string())


if __name__ == "__main__":
    main()

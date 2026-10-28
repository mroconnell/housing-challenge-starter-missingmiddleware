"""Vermont options for the adopted ADU model (AQ-061 follow-up). See docs/adu/VERMONT_OPTIONS.md.

Three options, each run through the adopted pipeline (scripts/run_pooled_revision.py fit and allocation, then the
scripts/run_adu_model.py engine step: lower = Rhode Island / Oregon mean, upper = 90th percentile of the between-state
spread, Madison on its observed path, 8-state reference line), with reporting-share coverage and Washington from local
compliance as adopted:
  A  as adopted (reproduces reference/adu_model_statewide.csv and adu_model_reference_lines.csv)
  B  Vermont 2024 dropped (fit rows and reference-line point)
  C  Vermont dropped entirely (within-state stage, between-state common level, reference line, lower and upper spread)

Writes only reference/adu_vermont_options.csv. The adopted files are read, never written: the per-option level,
stage-2 and reference-point files the run_adu_model.py functions read are written to a temporary folder and the
module's REFERENCE / ROOT are pointed there for the duration of the run.
Run: uv run python scripts/run_adu_vermont_options.py   (about 1 minute)
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import run_adu_model as ram  # noqa: E402
import run_pooled_regression as rp  # noqa: E402
import run_pooled_revision as rv  # noqa: E402
from missing_middleware.comparison import pooled_regression as pr  # noqa: E402
from missing_middleware.comparison import pooled_revision as R  # noqa: E402
from missing_middleware.model import engine as e  # noqa: E402
from missing_middleware.model.params import area_paths  # noqa: E402
from missing_middleware.paths import PROCESSED, REFERENCE  # noqa: E402

OPT, CFG_A, CFG_B = "cap_a2", "A_ca_in_common_level", "B_ca_out_of_common_level"
STATES = pr.STATEWIDE_STATES                      # WA OR RI MA ME UT VT
COMMON = tuple(s for s in STATES if s != "VT")    # the 6 states every option keeps
OPTIONS = {
    "A_adopted": "as adopted",
    "B_drop_vt_2024": "Vermont 2024 dropped",
    "C_drop_vt": "Vermont dropped entirely",
}


def pooled_for(opt, d, pan):
    if opt == "B_drop_vt_2024":
        return rv.build(d, pan, drop_vt_2024=True)
    p = rv.build(d, pan)
    if opt == "C_drop_vt":
        p = pr.subset(p, p.rows["cluster"].ne("VT").to_numpy())
    return p


def loso(p, cfg, states):
    lo = pr.loso_ts(p, rv.tspec(cfg), clusters=states)
    return lo[lo["series"].isin(pr.STATE_CODING)].set_index("held_out")


def ref_points(p, pan):
    """8-state reference-line points as run_pooled_revision.main() writes them, for this option's rows."""
    pts = pr.adoption_points(p.rows, p.row_homes())[["cluster", "k", "rate", "year"]]
    ctx = rp.ca_context(pan)
    ca = pd.DataFrame({"cluster": "CA", "k": [y - 2019 for y in range(2020, 2026)],
                       "rate": [ctx[y] for y in range(2020, 2026)], "year": list(range(2020, 2026))})
    return pd.concat([pts, ca], ignore_index=True).round(4)


def main():
    d = rp.load()
    wi, growth = d["wi"], d["growth"]
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    G = rv.growth_matrix(wi, growth)
    pan = rv.ca_panels(d["panel"])[OPT]
    mlp = pd.read_csv(REFERENCE / "madison_like_median_path.csv")
    rv.MADISON_LIKE_PATH = mlp[mlp["group"].eq("WA+OR Madison-like (main)")].sort_values("year_since_law")["median_rate"].to_numpy()
    apaths = area_paths(ram.PARAMS)
    adopted_pts = pd.read_csv(REFERENCE / "pooled_revision_reference_points.csv")

    tmp = Path(tempfile.mkdtemp(prefix="vt_options_"))
    (tmp / "reference").mkdir()
    shutil.copy(REFERENCE / "pooled_revision_adoption_line.csv", tmp / "reference")
    ram_ref, ram_root = ram.REFERENCE, ram.ROOT
    rows, err_rows = [], []
    try:
        ram.REFERENCE, ram.ROOT = tmp / "reference", tmp
        for opt, label in OPTIONS.items():
            p = pooled_for(opt, d, pan)
            r, _, f, Y = rv.wi_results(p, CFG_A, d, G, rv.FLOOR_NEW, pan, set(), sens=False)
            lv = rv.level_frame(opt, CFG_A, wi, Y, r["factor80"], p)
            lawc = f.beta[f.within_names.index("law")]
            st2 = pd.DataFrame([dict(option=opt, config=CFG_A, cluster=c, level_with_law_k4=float(np.exp(a + lawc)))
                                for c, a in f.alpha.items()])
            lv.to_csv(tmp / "reference/pooled_revision_wi_y_by_area.csv", index=False)
            st2.to_csv(tmp / "reference/pooled_revision_stage2_levels.csv", index=False)
            pd.DataFrame([{**r, "option": opt, "config": CFG_A}]).to_csv(tmp / "reference/pooled_revision_wi.csv", index=False)
            pts = ref_points(p, pan)
            if opt == "A_adopted":
                chk = adopted_pts.merge(pts, on=["cluster", "k", "year"], how="outer", indicator=True)
                if not (chk["_merge"].eq("both").all() and np.allclose(chk.rate_x, chk.rate_y, atol=1e-4)):
                    raise SystemExit("option A reference points do not reproduce pooled_revision_reference_points.csv")
            pts.to_csv(tmp / "reference/pooled_revision_reference_points.csv", index=False)

            # engine step exactly as run_adu_model.main(): lower = RI/OR mean, pooled ramps per path, Madison path
            fac_low = ram.bottom_states_factor(opt, CFG_A)
            fac_up = float(r["factor80"])
            ramps = {pth: {"ramp": ram.pooled_ramp(opt, CFG_A, fac, areas)}
                     for pth, fac in (("lower", fac_low), ("central", 1.0), ("upper", fac_up))}
            out = e.run(areas, ram.load_scenario(**ramps), growth, ram.load_area_levels(opt, CFG_A), apaths)
            if e.check_invariants(out):
                raise SystemExit(f"{opt}: engine invariant failures")
            tot = ram.path_totals(out)
            base5 = float(e.five_year_totals(out)["baseline_units"].iloc[0])
            by_year = out.groupby(["path", "year"])[["baseline_units", "additional_units"]].sum().reset_index()
            lines, lby = ram.reference_lines(by_year, float(areas["homes"].sum()))
            l8 = lines[lines.line_id.eq("8_state_median")].iloc[0]

            # held-out errors: configuration A (California in the common level) and B (out)
            states = tuple(s for s in STATES if s in set(p.rows["cluster"]))
            la, lb = loso(p, CFG_A, states), loso(p, CFG_B, states)
            for s in states:
                err_rows.append(dict(option=opt, state=s, obs_rate=la.loc[s, "obs_rate"], pred_rate_ca_in=la.loc[s, "pred_rate"],
                                     log_error_ca_in=la.loc[s, "log_error"], log_error_ca_out=lb.loc[s, "log_error"]))
            rms = lambda lo, ss: float(np.sqrt(np.mean(lo.loc[list(ss), "log_error"] ** 2)))  # noqa: E731
            worst = la["log_error"].abs().idxmax()
            rows.append(dict(
                option=opt, label=label, n_states_total=len(states) + 1, n_states_non_ca=len(states), n_stage2_states=len(f.stage2),
                baseline_permits_5yr=base5, lower_additional_5yr=tot["lower"], central_additional_5yr=tot["central"],
                upper_additional_5yr=tot["upper"], reference_line_additional_5yr=float(l8.additional_5yr),
                reference_line_rates_per_1000=l8.rate_years_1_5, reference_line_n_states_by_year=l8.n_states_by_year,
                typical_level_per_1000_k4=float(r["common_level_k4"]), lower_factor=fac_low, upper_factor=fac_up,
                tau_log=float(r["tau"]),
                rms_log_error_ca_in_states_left=rms(la, states), rms_log_error_ca_out_states_left=rms(lb, states),
                rms_log_error_ca_in_common6=rms(la, COMMON), rms_log_error_ca_out_common6=rms(lb, COMMON),
                ca_in_wins_states_left=rms(la, states) < rms(lb, states), ca_in_wins_common6=rms(la, COMMON) < rms(lb, COMMON),
                worst_miss_state=worst, worst_miss_log_error=float(la.loc[worst, "log_error"]),
                **{f"log_error_ca_in_{s}": float(la.loc[s, "log_error"]) if s in la.index else np.nan for s in STATES},
                **{f"log_error_ca_out_{s}": float(lb.loc[s, "log_error"]) if s in lb.index else np.nan for s in STATES}))
            print(opt, {k: round(v, 4) if isinstance(v, float) else v for k, v in rows[-1].items()})
    finally:
        ram.REFERENCE, ram.ROOT = ram_ref, ram_root
        shutil.rmtree(tmp, ignore_errors=True)

    res = pd.DataFrame(rows)
    # check: option A reproduces the adopted outputs
    st = pd.read_csv(REFERENCE / "adu_model_statewide.csv").set_index("path")["additional_units"]
    a = res.iloc[0]
    for pth in ("lower", "central", "upper"):
        if abs(a[f"{pth}_additional_5yr"] - st[pth]) > 0.5:
            raise SystemExit(f"option A {pth} {a[f'{pth}_additional_5yr']:.1f} != adopted {st[pth]:.1f}")
    rl = pd.read_csv(REFERENCE / "adu_model_reference_lines.csv")
    if abs(a.reference_line_additional_5yr - float(rl[rl.line_id.eq("8_state_median")].additional_5yr.iloc[0])) > 0.5:
        raise SystemExit("option A reference line does not reproduce adu_model_reference_lines.csv")
    g3 = pd.read_csv(REFERENCE / "pooled_revision_g3f2.csv")
    g3a = g3[g3.option.eq(OPT) & g3.config.eq(CFG_A)].iloc[0]
    if abs(a.rms_log_error_ca_in_states_left - g3a.rms_log_error) > 5e-4:
        raise SystemExit("option A held-out RMS does not reproduce pooled_revision_g3f2.csv")
    out = res.round(4)
    out.to_csv(REFERENCE / "adu_vermont_options.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.T.to_string())
    print(pd.DataFrame(err_rows).round(4).to_string(index=False))


if __name__ == "__main__":
    main()

"""ADU side line "Like California": Wisconsin at California's own stage-2 level, built the way the Rhode Island and
Oregon line (lower) is built (owner request 2026-11-11, via the TOD thread): factor = California's stage-2 level
(typical place, law in force 4+ years) / the common level (run_adu_model.bottom_states_factor with ["CA"]); every
area's central level x that factor; the pooled ramp recomputed for this level; the adopted engine run.

Run: uv run python scripts/run_adu_like_california.py
Output: reference/adu_model_like_california.csv (path, year 1..5 and 2027-2031, additional_units, baseline_units)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_adu_model as ram  # noqa: E402
import run_adu_vermont_options as vto  # noqa: E402
import run_pooled_revision as rv  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402
from missing_middleware.model import engine as e  # noqa: E402

OPT = "like_california"


def main():
    ctx = vto.context()
    d, wi, areas = ctx["d"], ctx["wi"], ctx["areas"]
    with vto.temp_reference() as ref_dir:
        p = rv.build(d, ctx["pan"])
        r, _, f, Y = rv.wi_results(p, vto.CFG_A, d, ctx["G"], rv.FLOOR_NEW, ctx["pan"], set(), sens=False)
        lv = rv.level_frame(OPT, vto.CFG_A, wi, Y, r["factor80"], p)
        lawc = f.beta[f.within_names.index("law")]
        st2 = pd.DataFrame([dict(option=OPT, config=vto.CFG_A, cluster=c, level_with_law_k4=float(np.exp(a + lawc)))
                            for c, a in f.alpha.items()])
        lv.to_csv(ref_dir / "pooled_revision_wi_y_by_area.csv", index=False)
        st2.to_csv(ref_dir / "pooled_revision_stage2_levels.csv", index=False)
        pd.DataFrame([{**r, "option": OPT, "config": vto.CFG_A}]).to_csv(ref_dir / "pooled_revision_wi.csv", index=False)
        fac_low = ram.bottom_states_factor(OPT, vto.CFG_A)
        fac_ca = ram.bottom_states_factor(OPT, vto.CFG_A, ["CA"])
        ramps = {pth: {"ramp": ram.pooled_ramp(OPT, vto.CFG_A, fac, areas)}
                 for pth, fac in (("lower", fac_low), ("central", 1.0), ("upper", fac_ca))}
        out = e.run(areas, ram.load_scenario(**ramps), ctx["growth"], ram.load_area_levels(OPT, vto.CFG_A), ctx["apaths"])
        if e.check_invariants(out):
            raise SystemExit("engine invariant failures")
    by = out.groupby(["path", "year"])[["baseline_units", "additional_units"]].sum().reset_index()
    adopted = pd.read_csv(REFERENCE / "adu_model_statewide.csv").set_index("path")["additional_units"]
    tot = by.groupby("path")["additional_units"].sum()
    for pth in ("lower", "central"):
        if abs(tot[pth] - adopted[pth]) > 0.5:
            raise SystemExit(f"{pth} does not reproduce the adopted run: {tot[pth]:.1f} vs {adopted[pth]:.1f}")
    ca = by[by.path.eq("upper")].assign(line="like_california", factor=fac_ca)
    five = pd.DataFrame([dict(line="like_california", path="upper", year="2027-2031", factor=fac_ca,
                              baseline_units=ca.baseline_units.sum(), additional_units=ca.additional_units.sum())])
    res = pd.concat([ca.assign(year=ca.year.astype(str)), five], ignore_index=True)
    res[["line", "year", "factor", "baseline_units", "additional_units"]].round(4).to_csv(
        REFERENCE / "adu_model_like_california.csv", index=False)
    print(f"factor {fac_ca:.4f} (lower {fac_low:.4f}); like California: {ca.additional_units.round(1).tolist()} "
          f"= {ca.additional_units.sum():.1f}")


if __name__ == "__main__":
    main()

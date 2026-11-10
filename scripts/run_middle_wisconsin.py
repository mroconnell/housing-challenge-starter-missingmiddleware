"""Middle housing: Wisconsin lines for the tool, by the locked plan (docs/middle/WISCONSIN_PLAN_LOCKED.md,
including its logged post-lock changes). Reads only committed reference files.

Unit: extra homes permitted, 2027-2031, on top of the shared all-housing baseline (v4).

Core (M2, homes in 2-4 unit buildings): Test 1 four-state rate difference per 1,000 single-family homes per year
(reference/middle_test1_summary.csv, reported-only data): lower / central / upper = 90% range low / estimate / high.
Applied to each area's single-family homes (reference/pooled_wi_y_by_area.csv, 1,839,569 in all).
Timing: measured slow start. 2027 at the first-law-year share (Oregon 2022, California 2022, Vermont 2023 mean first-year
effect over mean main-window effect; computed 2026-11-10, about -21%), full size 2028-2031.
Split of the 2-4 core between 2-unit and 3-4 unit buildings by the baseline's 2027-2031 mix.

Side measures (beside the core, "too noisy to include in predicted range"): M1 (1-4 unit homes) and M3 (all homes) by the
locked ratio reading (Test 1 log ratio applied to the baseline's central for that size), with the same timing; 1-6 view =
M1 + 5-6 estimate.
Extra lines: 5-6 unit homes = core x s/(1-s) with s = 0.17 (midpoint of 7.2%-26.6%); stronger reform = core x 1/(1-s);
with add-ons = core x (1 + 1.25 townhouses and split lots, Test 6 middle x2.25 less the core) + 5-6.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
YEARS = [2027, 2028, 2029, 2030, 2031]

# Measured slow start (Wisconsin plan, timing row): first-law-year effect / main-window effect
FIRST_YEAR = {"Oregon": (-0.195, 0.562), "California": (-0.298, 0.047), "Vermont": (0.327, 0.168)}
SHARE_56 = 0.17                 # convention: midpoint of 7.2%-26.6% (audit 2026-11-10)
SHARE_56_BAND = (0.072, 0.266)
SHARE_56_PORTLAND = 0.03
TOWNHOUSE_FACTOR = 2.25         # Test 6 middle of x1.5-x3 (records with townhouses vs Census 2-4)


def ramp() -> dict[int, float]:
    first = np.mean([a for a, _ in FIRST_YEAR.values()]) / np.mean([b for _, b in FIRST_YEAR.values()])
    return {y: (first if y == 2027 else 1.0) for y in YEARS}


def test1(measure: str) -> pd.Series:
    s = pd.read_csv(REF / "middle_test1_summary.csv")
    return s[(s["data"].str.startswith("reported")) & (s["measure"] == measure) & (s["set"] == "four states")].iloc[0]


def main() -> None:
    ra = ramp()
    areas = pd.read_csv(REF / "pooled_wi_y_by_area.csv")[["area_id", "name", "homes"]]
    t = test1("M2")
    rates = {"lower": t["range_diff_low"], "central": t["real_diff_per_1000"], "upper": t["range_diff_high"]}
    base = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
    proj = base[(base["kind"] == "projected") & base["year"].isin(YEARS)]
    bsize = proj.groupby("structure_type")["central"].sum()
    share2 = bsize["2units"] / (bsize["2units"] + bsize["3_4units"])

    rows = []
    for y in YEARS:
        for line, rate in rates.items():
            core = rate * areas["homes"].sum() / 1000 * ra[y]
            rows.append(dict(year=y, line=line, kind="core_2_4", value=core))
            rows.append(dict(year=y, line=line, kind="core_2_unit", value=core * share2))
            rows.append(dict(year=y, line=line, kind="core_3_4_unit", value=core * (1 - share2)))
            rows.append(dict(year=y, line=line, kind="extra_5_6", value=core * SHARE_56 / (1 - SHARE_56)))
            rows.append(dict(year=y, line=line, kind="stronger_reform", value=core / (1 - SHARE_56)))
            rows.append(dict(year=y, line=line, kind="with_addons",
                             value=core * (1 + (TOWNHOUSE_FACTOR - 1) + SHARE_56 / (1 - SHARE_56))))
            rows.append(dict(year=y, line=line, kind="core_flat_timing", value=rate * areas["homes"].sum() / 1000))
        for m, key in (("M1", "side_1_4"), ("M3", "side_all")):
            tm = test1(m)
            if m == "M1":
                b = proj[proj["year"] == y].set_index("structure_type")["central"][["1unit", "2units", "3_4units"]].sum()
            else:
                b = proj[(proj["year"] == y)].set_index("structure_type")["central"]["all"]
            for line, col in (("lower", "range_log_low"), ("central", "real_log"), ("upper", "range_log_high")):
                rows.append(dict(year=y, line=line, kind=key, value=(np.exp(tm[col]) - 1) * b * ra[y]))
    out = pd.DataFrame(rows)
    # 1-6 view = 1-4 + 5-6 estimate
    s14 = out[out["kind"] == "side_1_4"].set_index(["year", "line"])["value"]
    e56 = out[out["kind"] == "extra_5_6"].set_index(["year", "line"])["value"]
    v16 = (s14 + e56).reset_index().assign(kind="side_1_6")
    out = pd.concat([out, v16], ignore_index=True)
    out["value"] = out["value"].round(3)
    out.to_csv(REF / "middle_model_statewide_by_year.csv", index=False)

    tot = out.groupby(["kind", "line"])["value"].sum().unstack("line")[["lower", "central", "upper"]].round(0)
    tot.to_csv(REF / "middle_model_lines_2027_2031.csv")
    # share band for the stronger-reform line (central only) and Portland check
    core_c = out[(out["kind"] == "core_2_4") & (out["line"] == "central")]["value"].sum()
    band = pd.DataFrame([dict(item="stronger_reform_central_share_low", share=SHARE_56_BAND[0], value=core_c / (1 - SHARE_56_BAND[0])),
                         dict(item="stronger_reform_central_share_high", share=SHARE_56_BAND[1], value=core_c / (1 - SHARE_56_BAND[1])),
                         dict(item="stronger_reform_central_portland", share=SHARE_56_PORTLAND, value=core_c / (1 - SHARE_56_PORTLAND))])
    band["value"] = band["value"].round(0)
    band.to_csv(REF / "middle_model_stronger_band.csv", index=False)

    # by area: each line split by single-family homes (same rate everywhere)
    w = areas["homes"] / areas["homes"].sum()
    for line in rates:
        for y in YEARS:
            v = out[(out["kind"] == "core_2_4") & (out["line"] == line) & (out["year"] == y)]["value"].iat[0]
            areas[f"add_{line}_{y}"] = (w * v).round(3)
        areas[f"add_{line}_five_year"] = areas[[f"add_{line}_{y}" for y in YEARS]].sum(axis=1).round(3)
    areas.to_csv(REF / "middle_model_by_area.csv", index=False)
    print(f"ramp 2027 = {ra[2027]:.4f}; share 2-unit = {share2:.4f}")
    print(tot.to_string())
    print(band.to_string(index=False))


if __name__ == "__main__":
    main()

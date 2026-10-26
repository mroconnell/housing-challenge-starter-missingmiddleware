"""Effect of the current-law (baseline-only) sensitivities on the addition and on the total with the law.

reference/wi_baseline_sensitivities.csv (scripts/build_wi_baseline.py) gives each baseline-only case's
current-law baseline, but not what it does to the permits the law adds. This script reruns the adopted
engine (same parameters, area levels, ramps and Madison path as scripts/run_adu_model.py) with only the
current-law rate x (and its ramp g) changed, and records baseline, additional and with-law totals for
2027-2031 in every path. It does not change any adopted output.

Why the addition moves: the engine adds H x max(y - x g, 0) x ramp / 1000, where y (the rate with the
law) comes from the statewide-law states and each place's characteristics, not from its current rules.
A higher current-law rate therefore means a smaller addition, and the total with the law barely moves.

Cases (all central x; lower and upper paths reported too):
- uncoded places behave like prohibited (old AQ-023 default): x = prohibited-group rate where rules are not coded;
- no ramp for recently liberalized places: g = 1 everywhere;
- Madison x = 2026 provisional pace, 2024-2025, or 2022-2025 without the templated programme;
- Milwaukee: whichever of its two treatments the adopted baseline does not use (its measured 2022-2025 rate,
  or the assumed ramp from its pre-reform rate to Madison's rate after its 2025 reform).

Inputs: data/processed/model_baseline/engine_areas.parquet, engine_baseline_growth.parquet,
reference/wi_baseline_rates_by_group.csv, wi_baseline_observed.csv, wi_baseline_sensitivities.csv (check),
plus the adopted parameters read by scripts/run_adu_model.py.
Output: reference/adu_model_baseline_only_effects.csv
Run: uv run python scripts/run_baseline_only_effects.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from missing_middleware.model import baseline as bl  # noqa: E402
from missing_middleware.model import engine as e  # noqa: E402
from missing_middleware.model.params import area_paths  # noqa: E402
from missing_middleware.paths import PROCESSED, REFERENCE  # noqa: E402

MADISON = "muni:5502548000"
MILWAUKEE_PLACE = "5507953000"


def totals(out: pd.DataFrame) -> dict:
    t = e.five_year_totals(out).set_index("path")
    return {p: (float(t.loc[p, "baseline_units"]), float(t.loc[p, "additional_units"])) for p in e.PATHS}


# plain-language description of each case (also written to reference/adu_model_sensitivities.csv)
CASE_TEXT = {
    "uncoded-prohibited": "Places whose ADU rules have not been coded (69% of single-family homes) behave like places "
                          "that prohibit ADUs, instead of like places that restrict them. Changes only the current-law "
                          "baseline; the law's addition moves the other way by about as much.",
    "no-baseline-ramp": "Places that loosened their ADU rules recently are at their new group's rate at once, instead of "
                        "rising to it over a few years. Changes only the current-law baseline.",
    "madison-2026": "Madison's current-law rate is its 2026 pace so far (42 second homes, 1 January to 23 October, "
                    "provisional) instead of its 2022-2025 rate. Changes only the current-law baseline; Madison's "
                    "addition falls by about as much.",
    "madison-2024-2025": "Madison's current-law rate uses 2024-2025 only. Changes only the current-law baseline.",
    "madison-excl-templated": "Madison's 2022-2025 rate leaves out the one builder's programme of second homes. "
                              "Changes only the current-law baseline.",
    "milwaukee-measured": "Milwaukee stays at its own measured 2022-2025 rate, instead of the assumed rise to Madison's "
                          "rate after its August 2025 ADU reform. Changes only the current-law baseline.",
    "milwaukee-ramp": "Milwaukee rises from its pre-reform rate to Madison's rate within about four years of its August "
                      "2025 ADU reform (the assumed ramp used at Gate 3), instead of staying at its measured 2022-2025 "
                      "rate. Changes only the current-law baseline; Milwaukee's addition falls by about as much.",
}


def baseline_only_cases(areas: pd.DataFrame, growth: pd.DataFrame) -> list[tuple]:
    """(case id, label, engine areas, baseline growth, wi_baseline_sensitivities label or None) for each case that
    changes only the current-law rate x (and its ramp g)."""
    groups = pd.read_csv(REFERENCE / "wi_baseline_rates_by_group.csv").set_index("group")
    obs = pd.read_csv(REFERENCE / "wi_baseline_observed.csv").set_index("key")
    # unrounded rates: the CSVs round rates to 4 decimals, so rebuild them from count / thousand home-years
    grate = {g: float(groups.loc[g, "units"] / groups.loc[g, "thousand_home_years"]) for g in ("prohibited", "restricted")}
    orate = {k: float(obs.loc[k, "units"] / obs.loc[k, "thousand_home_years"]) for k in obs.index}
    cases = []
    a = areas.copy()
    a.loc[a.x_basis.eq("uncoded_like_restricted_AQ027"), "x_rate"] = grate["prohibited"]
    cases.append(("uncoded-prohibited", "Places with uncoded rules behave like prohibited places", a, growth,
                  "uncoded places behave like prohibited (old AQ-023 default)"))
    cases.append(("no-baseline-ramp", "No ramp for recently liberalized places (full current-law rate at once)", areas,
                  growth.iloc[0:0], "no ramp: liberalized places at their class rate at once (g = 1)"))
    for key, cid, label, chk in (
            ("madison_2026_provisional", "madison-2026", "Madison's current-law rate = its 2026 pace so far (provisional)",
             "Madison x = 2026 provisional to date"),
            ("madison_2024_2025", "madison-2024-2025", "Madison's current-law rate from 2024-2025 only", "Madison x = 2024-2025"),
            ("madison_2022_2025_excl_templated", "madison-excl-templated",
             "Madison's current-law rate without the templated builder programme", "Madison x excludes templated programme")):
        a = areas.copy()
        a.loc[a.area_id.eq(MADISON), "x_rate"] = orate[key]
        cases.append((cid, label, a, growth, chk))
    # Milwaukee: two treatments, its measured 2022-2025 rate or the assumed ramp from its pre-reform rate to Madison's
    # rate after its 2025-08-02 reform. Whichever the adopted baseline does not use is the sensitivity case.
    meas = pd.read_csv(REFERENCE / "wi_measured_permits_2022_2025.csv", dtype={"GEOID": str}).set_index("GEOID")
    mke_measured = float(meas.loc[MILWAUKEE_PLACE, "permits"] / meas.loc[MILWAUKEE_PLACE, "thousand_home_years"])
    mke = areas.place_id.astype(str).str.replace(r"\.0$", "", regex=True).eq(MILWAUKEE_PLACE) if "place_id" in areas else \
        areas.area_id.isin([f"muni:{MILWAUKEE_PLACE}", "muni:5513153000", "muni:5513353000"])
    mke_ids = set(areas.loc[mke, "area_id"])
    on_ramp = areas.loc[mke, "x_basis"].astype(str).str.startswith("assumed ramp").any()
    a = areas.copy()
    g = growth[~growth.area_id.isin(mke_ids)]
    if on_ramp:
        a.loc[mke, "x_rate"] = mke_measured
        cases.append(("milwaukee-measured", "Milwaukee at its measured 2022–2025 rate (no assumed rise to Madison's rate)",
                      a, g, None))
    else:
        target = orate["madison_2022_2025"]
        pre = orate["milwaukee_pre_central"]
        reform = date(2025, 8, 2)
        rows = [{"area_id": i, "year": k + 1, "g": bl.ramped_rate(2027 + k, pre, target, reform, bl.RAMP_YEARS["central"]) / target}
                for i in mke_ids for k in range(5)]
        a.loc[mke, "x_rate"] = target
        g = pd.concat([g, pd.DataFrame(rows).query("g < 1 - 1e-12")], ignore_index=True)
        cases.append(("milwaukee-ramp", "Milwaukee rises to Madison's rate after its 2025 reform (assumed ramp)", a, g,
                      "Milwaukee x = assumed ramp to Madison's rate after its 2025 reform"))
    return cases


def main():
    from run_adu_model import load_area_levels, load_scenario

    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    check = pd.read_csv(REFERENCE / "wi_baseline_sensitivities.csv").set_index("sensitivity")
    scen, levels, apaths = load_scenario(), load_area_levels(), area_paths()

    def run(a, g):
        return totals(e.run(a, scen, g, levels, apaths))

    main_t = run(areas, growth)
    cases = []

    def case(cid, label, a, g, check_label=None):
        t = run(a, g)
        row = {"case": cid, "label": label, "description": CASE_TEXT.get(cid, "")}
        for p in e.PATHS:
            b, ad = t[p]
            b0, ad0 = main_t[p]
            row.update({f"baseline_{p}": round(b, 2), f"additional_{p}": round(ad, 2), f"with_law_{p}": round(b + ad, 2),
                        f"d_baseline_{p}": round(b - b0, 2), f"d_additional_{p}": round(ad - ad0, 2),
                        f"d_with_law_{p}": round(b + ad - b0 - ad0, 2)})
        if check_label is not None:
            want = float(check.loc[check_label, "b5yr_central"])
            if abs(row["baseline_central"] - want) > 0.05:
                raise SystemExit(f"{cid}: engine baseline {row['baseline_central']:.2f} != wi_baseline_sensitivities {want:.2f}")
        row["check"] = f"baseline equals reference/wi_baseline_sensitivities.csv ({check_label})" if check_label else "no baseline counterpart"
        cases.append(row)

    case("adopted", "Adopted model", areas, growth, "main (central path)")
    for c in baseline_only_cases(areas, growth):
        case(*c)
    out = pd.DataFrame(cases)
    out.to_csv(REFERENCE / "adu_model_baseline_only_effects.csv", index=False)
    pd.set_option("display.width", 250)
    print(out[["case", "baseline_central", "d_baseline_central", "d_additional_central", "d_with_law_central"]].to_string(index=False))


if __name__ == "__main__":
    main()

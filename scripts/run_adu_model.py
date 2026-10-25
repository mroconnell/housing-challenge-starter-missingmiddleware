"""Run the statewide ADU scenario with the parameters in reference/adu_model_params.json.

Inputs: data/processed/model_baseline/engine_areas.parquet and
engine_baseline_growth.parquet (from scripts/build_wi_baseline.py).
Outputs: data/processed/model_run/results_long.parquet, and summary tables in
reference/adu_model_*.csv (statewide, by county, by context group, by rights basis,
sensitivities). Run: uv run python scripts/run_adu_model.py
"""
from __future__ import annotations

import json

import pandas as pd

from missing_middleware.model import engine as e
from missing_middleware.model.params import madison_floor
from missing_middleware.paths import PROCESSED, REFERENCE, processed_dir


def load_scenario(path=REFERENCE / "adu_model_params.json", which="paths", **overrides) -> e.Scenario:
    spec = json.loads(path.read_text())
    floor = madison_floor(path=path)        # one floor for every path (madison_floor in the params file)
    paths = {}
    for name, p in spec[which].items():
        p = {**p, **overrides.get(name, {})}
        paths[name] = e.PathParams(level=p["level"], floor_rate=p.get("floor_rate", floor), spillover=p["spillover"],
                                   ramp=tuple(p["ramp"]))
    return e.Scenario(spec["scenario_id"], paths, {k: v["basis"] for k, v in spec[which].items()})


def load_area_levels() -> pd.DataFrame:
    y = pd.read_csv(REFERENCE / "pooled_wi_y_by_area.csv")
    return y.rename(columns={"y_plateau_lower_80": "y_lower", "y_plateau_central": "y_central",
                             "y_plateau_upper_80": "y_upper"})[["area_id", "y_lower", "y_central", "y_upper"]]


def totals(out, areas):
    m = out.merge(areas[["area_id", "x_status", "rights_basis"]], on="area_id", how="left", suffixes=("", "_a"))
    state = e.five_year_totals(out)
    return m, state


def main():
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id", "context_group"]]
    scen = load_scenario()
    levels = load_area_levels()
    out = e.run(areas, scen, growth, levels)
    problems = e.check_invariants(out)
    if problems:
        raise SystemExit(f"invariant failures: {problems}")
    od = processed_dir("model_run")
    out.to_parquet(od / "results_long.parquet", index=False)
    out = out.merge(geo, on="area_id", how="left")
    state = e.five_year_totals(out)
    state.to_csv(REFERENCE / "adu_model_statewide.csv", index=False)
    by_year = out.groupby(["path", "year"])[["baseline_units", "additional_units"]].sum().reset_index()
    by_year.to_csv(REFERENCE / "adu_model_statewide_by_year.csv", index=False)
    for key, fn in (("parent_county_id", "by_county"), ("context_group", "by_context"), ("rights_basis", "by_rights_basis"),
                    ("x_basis", "by_x_basis")):
        e.five_year_totals(out, [key]).to_csv(REFERENCE / f"adu_model_{fn}.csv", index=False)
    # engine-level sensitivities on the central path (model-level ones are in
    # reference/ca_regression_sensitivities.csv from scripts/run_ca_regression.py)
    base_central = state.loc[state.path == "central", "additional_units"].item()
    sens = []

    def central_total(scn, lv=levels, ar=areas):
        t = e.five_year_totals(e.run(ar, scn, growth, lv))
        return t.loc[t.path == "central", "additional_units"].item()

    for label, ov in {
        "no ramp (full rate from year 1)": {"central": {"ramp": [1, 1, 1, 1, 1]}},
    }.items():
        v = central_total(load_scenario(**ov))
        sens.append({"change": label, "central_additional_5yr": round(v, 1), "difference": round(v - base_central, 1)})
    rural_ids = set(geo.loc[geo.context_group.isin(["rural", "small_community"]), "area_id"])
    lv2 = levels.copy()
    floor = madison_floor()
    lv2.loc[lv2.area_id.isin(rural_ids), "y_central"] = floor
    v = central_total(scen, lv2)
    sens.append({"change": f"rural and small-community places at the Madison floor ({floor:g})",
                 "central_additional_5yr": round(v, 1), "difference": round(v - base_central, 1)})
    adopt = pd.read_csv(REFERENCE / "statewide_adoption_curve.csv")
    psens = pd.read_csv(REFERENCE / "pooled_sensitivities.csv")
    mult = psens[psens.iloc[:, 0].astype(str).str.contains("multiplicative law effect")].iloc[0, -2]
    ca_only = pd.read_csv(REFERENCE / "ca_regression_wi_statewide.csv").query("path == 'central'").additional_units.item()
    lines = pd.DataFrame([
        {"line": "statewide adoption (median observed path of statewide-law states)",
         "additional_5yr": round(adopt.additional_as_reported.sum(), 1)},
        {"line": "sensitivity: law only multiplies Wisconsin's current rate by the pooled statewide-law factor",
         "additional_5yr": round(float(mult), 1)},
        {"line": "sensitivity: California-only market regression (Wisconsin stays near Madison-like response)",
         "additional_5yr": round(float(ca_only), 1)},
    ])
    lines.to_csv(REFERENCE / "adu_model_reference_lines.csv", index=False)
    print(lines.to_string(index=False))
    pd.DataFrame(sens).to_csv(REFERENCE / "adu_model_sensitivities.csv", index=False)
    print(state.round(1).to_string(index=False))
    print(pd.DataFrame(sens).to_string(index=False))


if __name__ == "__main__":
    main()

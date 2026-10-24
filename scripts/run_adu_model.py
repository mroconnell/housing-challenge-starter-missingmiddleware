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
from missing_middleware.paths import PROCESSED, REFERENCE, processed_dir


def load_scenario(path=REFERENCE / "adu_model_params.json", **overrides) -> e.Scenario:
    spec = json.loads(path.read_text())
    paths = {}
    for name, p in spec["paths"].items():
        p = {**p, **overrides.get(name, {})}
        paths[name] = e.PathParams(level=p["level"], floor_rate=p["floor_rate"], spillover=p["spillover"],
                                   ramp=tuple(p["ramp"]))
    return e.Scenario(spec["scenario_id"], paths, {k: v["basis"] for k, v in spec["paths"].items()})


def totals(out, areas):
    m = out.merge(areas[["area_id", "x_status", "rights_basis"]], on="area_id", how="left", suffixes=("", "_a"))
    state = e.five_year_totals(out)
    return m, state


def main():
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id", "context_group"]]
    scen = load_scenario()
    out = e.run(areas, scen, growth)
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
    # sensitivities on the central path: one change at a time
    base_central = state.loc[state.path == "central", "additional_units"].item()
    sens = []
    variants = {
        "central level = California middle group 2.39": {"central": {"level": 2.39}},
        "central level = lower bound of California interval 0.70": {"central": {"level": 0.70}},
        "central level = upper bound of California interval 2.01": {"central": {"level": 2.01}},
        "no statewide spillover (does not bind: statewide level exceeds benchmark places' x x (1+s))": {"central": {"spillover": 0.0}},
        "no ramp (full rate from year 1)": {"central": {"ramp": [1, 1, 1, 1, 1]}},
        "Madison floor without /0.8 (does not bind on the central path)": {"central": {"floor_rate": 0.183}},
    }
    for label, ov in variants.items():
        s = e.five_year_totals(e.run(areas, load_scenario(**ov), growth))
        v = s.loc[s.path == "central", "additional_units"].item()
        sens.append({"change": label, "central_additional_5yr": round(v, 1), "difference": round(v - base_central, 1)})
    for ratio in (0.15, 0.25, 0.5, 0.67):
        s_ = e.five_year_totals(e.run(areas, load_scenario(central={"level": 1.23 * ratio}), growth))
        v = s_.loc[s_.path == "central", "additional_units"].item()
        sens.append({"change": f"market-adjusted: California level x {ratio} (AQ-024 variant)",
                     "central_additional_5yr": round(v, 1), "difference": round(v - base_central, 1)})
    s_ = e.five_year_totals(e.run(areas, load_scenario(central={"level": 0.87}), growth))
    v = s_.loc[s_.path == "central", "additional_units"].item()
    sens.append({"change": "post-hoc: California restrictive plateau without Lancaster (0.87)",
                 "central_additional_5yr": round(v, 1), "difference": round(v - base_central, 1)})
    geo_ctx = areas.merge(geo[["area_id", "context_group"]], on="area_id", how="left")
    rural = geo_ctx.context_group.isin(["rural", "small_community"])
    out_c = e.run(areas, scen, growth)
    floor_sc = load_scenario(central={"level": 0.229})
    out_f = e.run(areas[rural.values], floor_sc, growth)
    v = (out_c[out_c.path == "central"].merge(geo_ctx[["area_id", "context_group"]], on="area_id")
         .query("context_group not in ['rural','small_community']").additional_units.sum()
         + out_f[out_f.path == "central"].additional_units.sum())
    sens.append({"change": "rural and small-community places at the Madison floor (0.229)",
                 "central_additional_5yr": round(v, 1), "difference": round(v - base_central, 1)})
    ar = areas.copy()
    ar.loc[ar.x_basis.str.startswith("uncoded"), "x_rate"] = ar.loc[ar.x_basis.str.startswith("uncoded"), "x_low"]
    s = e.five_year_totals(e.run(ar, scen, growth))
    v = s.loc[s.path == "central", "additional_units"].item()
    sens.append({"change": "uncoded places at the low current rate (raises the increment; not the AQ-023 bias check)", "central_additional_5yr": round(v, 1),
                 "difference": round(v - base_central, 1)})
    pd.DataFrame(sens).to_csv(REFERENCE / "adu_model_sensitivities.csv", index=False)
    print(state.round(1).to_string(index=False))
    print(pd.DataFrame(sens).to_string(index=False))


if __name__ == "__main__":
    main()

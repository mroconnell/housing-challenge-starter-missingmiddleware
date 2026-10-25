"""Run the statewide ADU scenario with the parameters in reference/adu_model_params.json.

Adopted basis (AQ-042): pooled revision option (ii) "cap + A2", configuration A (California in
the between-state common level), per-area levels from reference/pooled_revision_wi_y_by_area.csv
(written by scripts/run_pooled_revision.py), Madison floor 0.2345, and Madison on the observed
Madison-like path (params `area_paths`, applied by engine.run(area_paths=...)).

Inputs: data/processed/model_baseline/engine_areas.parquet and engine_baseline_growth.parquet
(from scripts/build_wi_baseline.py); reference/pooled_revision_wi_y_by_area.csv,
pooled_revision_wi.csv, pooled_revision_adoption_line.csv (scripts/run_pooled_revision.py);
reference/eligible_basis_wi.csv (scripts/run_eligible_basis.py).
Outputs: data/processed/model_run/results_long.parquet, and summary tables in
reference/adu_model_*.csv (statewide, by year, by county, by context group, by rights basis,
by x basis, sensitivities, reference lines). Run: uv run python scripts/run_adu_model.py
"""
from __future__ import annotations

import json

import pandas as pd

from missing_middleware.model import engine as e
from missing_middleware.model.params import area_levels_spec, area_paths, madison_floor
from missing_middleware.paths import PROCESSED, REFERENCE, ROOT, processed_dir

PARAMS = REFERENCE / "adu_model_params.json"
PATH_COLS = {"lower": "engine_lower", "central": "engine_central", "upper": "engine_upper_tau90"}


def load_scenario(path=PARAMS, which="paths", **overrides) -> e.Scenario:
    spec = json.loads(path.read_text())
    floor = madison_floor(path=path)        # one floor for every path (madison_floor in the params file)
    paths = {}
    for name, p in spec[which].items():
        p = {**p, **overrides.get(name, {})}
        paths[name] = e.PathParams(level=p["level"], floor_rate=p.get("floor_rate", floor), spillover=p["spillover"],
                                   ramp=tuple(p["ramp"]))
    return e.Scenario(spec["scenario_id"], paths, {k: v["basis"] for k, v in spec[which].items()})


def load_area_levels(option: str | None = None, config: str | None = None) -> pd.DataFrame:
    """Per-area plateau levels by path; default = the adopted option x configuration in the params file."""
    spec = area_levels_spec(PARAMS)
    y = pd.read_csv(ROOT / spec["file"])
    y = y[y["option"].eq(option or spec["option"]) & y["config"].eq(config or spec["config"])]
    if y.empty:
        raise SystemExit(f"no per-area levels for {option or spec['option']} x {config or spec['config']}")
    return y.rename(columns={"y_plateau_lower_80": "y_lower", "y_plateau_central": "y_central",
                             "y_plateau_upper_80": "y_upper"})[["area_id", "y_lower", "y_central", "y_upper"]]


def revision_ramps(rev: pd.DataFrame, option: str, config: str) -> dict:
    r = rev[rev["option"].eq(option) & rev["config"].eq(config)].iloc[0]
    return {p: {"ramp": [float(v) for v in r[f"ramp_{c.removeprefix('engine_')}"].split("|")]} for p, c in PATH_COLS.items()}


def path_totals(out) -> dict:
    t = e.five_year_totals(out).set_index("path")
    return {p: float(t.loc[p, "additional_units"]) for p in e.PATHS}


def main():
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id", "context_group"]]
    spec = area_levels_spec(PARAMS)
    rev = pd.read_csv(REFERENCE / "pooled_revision_wi.csv")
    scen = load_scenario()
    levels = load_area_levels()
    apaths = area_paths(PARAMS)
    missing = set(apaths["area_id"]) - set(areas["area_id"])
    if missing:
        raise SystemExit(f"area_paths name unknown areas: {sorted(missing)}")
    out = e.run(areas, scen, growth, levels, apaths)
    problems = e.check_invariants(out)
    if problems:
        raise SystemExit(f"invariant failures: {problems}")

    # check: without the Madison path, the engine reproduces the revision runner's totals
    pooled_only = path_totals(e.run(areas, scen, growth, levels))
    ref = rev[rev["option"].eq(spec["option"]) & rev["config"].eq(spec["config"])].iloc[0]
    for p, c in PATH_COLS.items():
        if abs(pooled_only[p] - ref[c]) > 2.0:     # ramps are stored to 4 decimals
            raise SystemExit(f"engine {p} {pooled_only[p]:.1f} does not reproduce pooled_revision_wi.csv {ref[c]:.1f}")

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

    # ---------------- named sensitivities ----------------
    main_t = path_totals(out)
    base5 = float(state["baseline_units"].iloc[0])
    sens = []

    def add(change, kind, madison, t, source, baseline=base5):
        sens.append({"change": change, "kind": kind, "madison": madison,
                     "lower_additional_5yr": round(t["lower"], 1) if t.get("lower") is not None else None,
                     "central_additional_5yr": round(t["central"], 1),
                     "upper_additional_5yr": round(t["upper"], 1) if t.get("upper") is not None else None,
                     "difference_central": round(t["central"] - main_t["central"], 1),
                     "baseline_5yr": round(baseline, 1), "source": source})

    add("adopted: pooled revision (ii) cap+A2, configuration A, Madison on the Madison-like path", "engine", "path",
        main_t, "this run")
    add("Madison at its pooled level (no Madison-like path)", "engine", "pooled level", pooled_only,
        "engine without area_paths")
    for lab, opt, cfg in (("California out of the common level (configuration B)", "cap_a2", "B_ca_out_of_common_level"),
                          ("LA-calibrated multifamily correction (option iii, configuration A)", "cap_la_calibrated",
                           "A_ca_in_common_level")):
        sc = load_scenario(**revision_ramps(rev, opt, cfg))
        add(lab, "engine", "path", path_totals(e.run(areas, sc, growth, load_area_levels(opt, cfg), apaths)),
            f"reference/pooled_revision_wi_y_by_area.csv ({opt} x {cfg})")
    t = path_totals(e.run(areas, load_scenario(central={"ramp": [1, 1, 1, 1, 1]}), growth, levels, apaths))
    add("no ramp (full rate from 2027; Madison's observed path unchanged)", "engine", "path", {"central": t["central"]},
        "engine, central ramp set to 1")
    rural_ids = set(geo.loc[geo.context_group.isin(["rural", "small_community"]), "area_id"])
    lv2 = levels.copy()
    floor = madison_floor()
    lv2.loc[lv2.area_id.isin(rural_ids), "y_central"] = floor
    t = path_totals(e.run(areas, scen, growth, lv2, apaths))
    add(f"rural and small-community places at the Madison floor ({floor:g})", "engine", "path", {"central": t["central"]},
        "engine, rural y_central = floor")
    eb = pd.read_csv(REFERENCE / "eligible_basis_wi.csv")
    r = eb[eb["run"].eq("denominator without one-unit attached homes")].iloc[0]
    add("eligible-property basis without one-unit attached homes: permits per 1,000 properties eligible under each "
        "state's law (detached homes plus multifamily properties)", "model", "path",
        {"lower": r["engine_lower_madison_path"], "central": r["engine_central_madison_path"],
         "upper": r["engine_upper_tau90_madison_path"]},
        "reference/eligible_basis_wi.csv (docs/gate3/ELIGIBLE_BASIS.md)", baseline=float(r["engine_baseline"]))
    add("multiplicative: the law only multiplies each place's current rate by the pooled statewide-law factor", "model",
        "multiplicative like every place", {"central": float(ref["sens_multiplicative"])},
        "reference/pooled_revision_wi.csv (sens_multiplicative)")
    add("California-only market regression (refitted on cap+A2 counts)", "model", "regression like every place",
        {"central": float(ref["sens_ca_only_regression"])}, "reference/pooled_revision_wi.csv (sens_ca_only_regression)")
    sdf = pd.DataFrame(sens)
    sdf.to_csv(REFERENCE / "adu_model_sensitivities.csv", index=False)

    # ---------------- reference lines ----------------
    al = pd.read_csv(REFERENCE / "pooled_revision_adoption_line.csv")
    lines = pd.DataFrame([
        {"line": "statewide adoption (median observed path of statewide-law states, vacant-lot rule x0.951)",
         "rate_years_1_5": "|".join(f"{v:.4f}" for v in al[al.variant.eq("vacant_lot_x0.951")].median_rate),
         "additional_5yr": round(al[al.variant.eq("vacant_lot_x0.951")].additional.sum(), 1)},
        {"line": "statewide adoption, as reported (no vacant-lot rule)",
         "rate_years_1_5": "|".join(f"{v:.4f}" for v in al[al.variant.eq("as_reported")].median_rate),
         "additional_5yr": round(al[al.variant.eq("as_reported")].additional.sum(), 1)},
    ])
    lines.to_csv(REFERENCE / "adu_model_reference_lines.csv", index=False)
    pd.set_option("display.width", 250)
    print(state.round(1).to_string(index=False))
    print(lines.to_string(index=False))
    print(sdf.drop(columns=["source"]).to_string(index=False))


if __name__ == "__main__":
    main()

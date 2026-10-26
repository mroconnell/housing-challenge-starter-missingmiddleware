"""Run the statewide ADU scenario with the parameters in reference/adu_model_params.json.

Adopted basis (AQ-042, revised by AQ-043 on 2026-10-26): pooled revision option (ii) "cap + A2",
configuration A (California in the between-state common level), per-area levels from
reference/pooled_revision_wi_y_by_area.csv (written by scripts/run_pooled_revision.py), Madison floor
0.2345, and Madison on the observed Madison-like path (params `area_paths`, applied by
engine.run(area_paths=...)). AQ-043: the lower is the mean of Rhode Island's and Oregon's levels (every
area's central level x 0.6497, params `paths.lower.level_from`); Milwaukee's current-law rate is its
measured 2022-2025 rate (scripts/build_wi_baseline.py); the reference line is the median of all 8
statewide-law states including California, 2031 carried forward.

Inputs: data/processed/model_baseline/engine_areas.parquet, engine_baseline_growth.parquet and their
*_milwaukee_ramp variants (Gate 3 rates; from scripts/build_wi_baseline.py); reference/pooled_revision_wi_y_by_area.csv,
pooled_revision_wi.csv, pooled_revision_stage2_levels.csv, pooled_revision_adoption_line.csv
(scripts/run_pooled_revision.py); reference/scenario_options_reference_points.csv (scripts/run_scenario_options.py);
reference/eligible_basis_wi.csv (scripts/run_eligible_basis.py). The multiplicative and California-only cases refit
the adopted pooled model (scripts/run_pooled_revision.py functions; about 3 seconds).
Outputs: data/processed/model_run/results_long.parquet, and summary tables in reference/adu_model_*.csv
(statewide, by year, by county, by context group, by rights basis, by x basis, sensitivities, reference lines and
reference line by year). Run: uv run python scripts/run_adu_model.py
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


def lower_rule(path=PARAMS) -> dict:
    """The lower path's level rule (AQ-043): {"relative_to", "states", "factor", ...} from the params file."""
    return json.loads(path.read_text())["paths"]["lower"]["level_from"]


def bottom_states_factor(option: str, config: str, states=None) -> float:
    """Mean of the named states' stage-2 levels (typical place, law in force 4+ years) / the common level, for
    one option x configuration of the pooled revision. Adopted (cap_a2 x A): (0.6214 + 0.6826) / 2 / 1.0035."""
    states = states or lower_rule()["states"]
    st2 = pd.read_csv(REFERENCE / "pooled_revision_stage2_levels.csv")
    st2 = st2[st2.option.eq(option) & st2.config.eq(config) & st2.cluster.isin(states)]
    if len(st2) != len(states):
        raise SystemExit(f"stage-2 levels missing for {states} in {option} x {config}")
    rev = pd.read_csv(REFERENCE / "pooled_revision_wi.csv")
    common = float(rev[rev.option.eq(option) & rev.config.eq(config)]["common_level_k4"].iloc[0])
    return float(st2["level_with_law_k4"].mean()) / common


def _level_rows(option: str, config: str) -> pd.DataFrame:
    y = pd.read_csv(ROOT / area_levels_spec(PARAMS)["file"])
    y = y[y["option"].eq(option) & y["config"].eq(config)]
    if y.empty:
        raise SystemExit(f"no per-area levels for {option} x {config}")
    return y


def load_area_levels(option: str | None = None, config: str | None = None, lower: str = "bottom_states") -> pd.DataFrame:
    """Per-area plateau levels by path; default = the adopted option x configuration in the params file.

    lower="bottom_states" (adopted, AQ-043): y_lower = y_central x bottom_states_factor(option, config), i.e. the mean
    of Rhode Island's and Oregon's levels relative to the common level, with the same within-state differences.
    lower="percentile10": the Gate 3 lower, the 10th percentile of the between-state spread (y_plateau_lower_80).
    """
    spec = area_levels_spec(PARAMS)
    option, config = option or spec["option"], config or spec["config"]
    y = _level_rows(option, config).rename(columns={"y_plateau_lower_80": "y_lower", "y_plateau_central": "y_central",
                                                    "y_plateau_upper_80": "y_upper"})
    if lower == "bottom_states":
        y["y_lower"] = y["y_central"] * bottom_states_factor(option, config)
    elif lower != "percentile10":
        raise ValueError(lower)
    return y[["area_id", "y_lower", "y_central", "y_upper"]]


def pooled_ramp(option: str, config: str, factor: float, ref_areas: pd.DataFrame) -> list[float]:
    """The pooled model's engine-form ramp for a level scaled by `factor`: homes-weighted
    (ybar_t - xbar) / (ybar_year5 - xbar) over the per-area year levels y_k1..y_k5 (pooled_regression.implied_ramp).
    ref_areas supplies homes and current-law rates; the adopted ramps were computed on the Gate 3 rates."""
    y = _level_rows(option, config)
    a = ref_areas[["area_id", "homes", "x_rate"]].merge(y, on="area_id", validate="1:1")
    if len(a) != len(ref_areas):
        raise SystemExit("per-area year levels do not cover every area")
    H, x = a["homes"].to_numpy(float), a["x_rate"].to_numpy(float)
    yb = [(H * a[f"y_k{k}_central"].to_numpy(float) * factor).sum() / H.sum() for k in range(1, 6)]
    xb = (H * x).sum() / H.sum()
    return [round(min(max((v - xb) / (yb[-1] - xb), 0.0), 1.0), 4) for v in yb]


def revision_ramps(rev: pd.DataFrame, option: str, config: str) -> dict:
    r = rev[rev["option"].eq(option) & rev["config"].eq(config)].iloc[0]
    return {p: {"ramp": [float(v) for v in r[f"ramp_{c.removeprefix('engine_')}"].split("|")]} for p, c in PATH_COLS.items()}


def path_totals(out) -> dict:
    t = e.five_year_totals(out).set_index("path")
    return {p: float(t.loc[p, "additional_units"]) for p in e.PATHS}


def refit_model_sensitivities(areas_by_case: dict) -> dict:
    """Multiplicative-law and California-only-regression cases, recomputed on the given current-law rates.

    Both come from the pooled revision's fitted model (scripts/run_pooled_revision.py: multiplicative() and
    ca_only_regression()); they depend on each place's current-law rate, so they are recomputed here whenever the
    baseline changes. areas_by_case: {name: (engine areas, baseline growth)}. Returns {name: {"multiplicative",
    "ca_only"}}. The fit is the adopted option x configuration (about 3 seconds)."""
    import sys

    import numpy as np  # noqa: F401
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_pooled_regression as rp
    import run_pooled_revision as rv
    from missing_middleware.comparison import pooled_regression as pr

    spec = area_levels_spec(PARAMS)
    d = rp.load()
    panels = rv.ca_panels(d["panel"])
    pan = panels[spec["option"]]
    f = pr.fit_two_stage(rv.build(d, pan), rv.tspec(spec["config"]))
    ca_ds = pd.read_parquet(PROCESSED / "ca_regression/ca_dataset.parquet")
    wiy = pd.read_csv(REFERENCE / "wi_y_by_area.csv")
    out = {}
    for name, (a, g) in areas_by_case.items():
        wi = d["wi"].drop(columns=["x_rate"]).merge(a[["area_id", "x_rate"]], on="area_id", validate="1:1")
        if not wi["area_id"].equals(d["wi"]["area_id"]):
            raise SystemExit("area order changed while recomputing the model sensitivities")
        G = rv.growth_matrix(wi, g)
        out[name] = {"multiplicative": rv.multiplicative(f, wi, d["baseline"]),
                     "ca_only": rv.ca_only_regression(pan, ca_ds, wiy, wi, G, madison_floor())[0]}
    return out


def reference_lines(by_year: pd.DataFrame, homes: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Statewide adoption reference lines, applied to Wisconsin: with-law total = homes x rate / 1,000, addition =
    that minus the year's current-law baseline (central engine baseline).

    Adopted (AQ-043): the median observed statewide rate across all 8 statewide-law states, California included,
    by year since the law (reference/scenario_options_reference_points.csv: California cap+A2 with 2020 = year 1;
    the other seven x0.951 for vacant-lot ADUs). A year with fewer than 2 states carries the last median forward
    (flagged carried_forward); only year 5 (2031) does, with California alone.
    Alternative rows: the Gate 3 seven-state line (California out), with and without the vacant-lot factor
    (reference/pooled_revision_adoption_line.csv), recomputed on the current baseline."""
    base = by_year[by_year.path.eq("central")].sort_values("year")["baseline_units"].to_numpy(float)
    pts = pd.read_csv(REFERENCE / "scenario_options_reference_points.csv")
    pts["k"] = pts["k"].astype(int)
    rows, last = [], None
    for k in e.YEARS:
        g = pts[pts.k.eq(k)].sort_values("rate")
        if g.cluster.nunique() >= 2:
            last = (k, float(g.rate.median()))
            basis, cf = "observed median", False
        else:
            basis, cf = (f"carried forward from year {last[0]} ({2026 + last[0]}): only "
                         f"{', '.join(g.cluster) or 'no state'} has a year {k}"), True
        rate = last[1]
        tot = homes * rate / 1000
        rows.append({"line": "8_state_median", "year_since_law": k, "forecast_year": 2026 + k,
                     "n_states": int(g.cluster.nunique()),
                     "states": ", ".join(f"{c} {r:.4f}" for c, r in zip(g.cluster, g.rate)),
                     "median_rate": round(rate, 4), "basis": basis, "carried_forward": cf,
                     "with_law_total": tot, "baseline": base[k - 1], "additional": tot - base[k - 1]})
    al = pd.read_csv(REFERENCE / "pooled_revision_adoption_line.csv")
    for variant, name in (("vacant_lot_x0.951", "7_state_median"), ("as_reported", "7_state_median_as_reported")):
        v = al[al.variant.eq(variant)].sort_values("year")
        n7 = pts[pts.cluster.ne("CA")].groupby("k").cluster.nunique()
        for k, rate in zip(v.year.astype(int), v.median_rate.astype(float)):
            tot = homes * rate / 1000
            n = int(n7.get(k, 0))
            rows.append({"line": name, "year_since_law": k, "forecast_year": 2026 + k, "n_states": n, "states": "",
                         "median_rate": rate, "basis": "observed median" if n else "carried forward from year 4",
                         "carried_forward": n == 0, "with_law_total": tot, "baseline": base[k - 1],
                         "additional": tot - base[k - 1]})
    ly = pd.DataFrame(rows)
    labels = {
        "8_state_median": ("statewide adoption: median observed path of all 8 statewide-law states incl. California "
                           "(California cap+A2, 2020 = year 1; others x0.951 for vacant-lot ADUs); 2031 carried forward "
                           "from 2030", True),
        "7_state_median": ("statewide adoption, 7 states without California (Gate 3 line; vacant-lot rule x0.951)", False),
        "7_state_median_as_reported": ("statewide adoption, 7 states without California, as reported (no vacant-lot "
                                       "rule)", False),
    }
    summ = []
    for name, (lab, adopted) in labels.items():
        g = ly[ly.line.eq(name)].sort_values("year_since_law")
        obs = g[~g.carried_forward]
        summ.append({"line": lab, "line_id": name, "adopted": adopted,
                     "rate_years_1_5": "|".join(f"{v:.4f}" for v in g.median_rate),
                     "additional_5yr": round(g.additional.sum(), 1),
                     "additional_by_year": "|".join(f"{v:.1f}" for v in g.additional),
                     "n_states_by_year": "|".join(str(v) for v in g.n_states),
                     "carried_forward_years": "|".join(str(v) for v in g.loc[g.carried_forward, "forecast_year"]),
                     "additional_observed_years": round(obs.additional.sum(), 1),
                     "observed_years": f"{obs.forecast_year.min()}-{obs.forecast_year.max()}"})
    return pd.DataFrame(summ), ly.round(4)


def main():
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    # Gate 3 current-law rates (Milwaukee on its assumed ramp): a baseline sensitivity case, the reference for the
    # stored ramps, and the check that the engine still reproduces the pooled revision (scripts/build_wi_baseline.py)
    areas_g3 = pd.read_parquet(PROCESSED / "model_baseline/engine_areas_milwaukee_ramp.parquet")
    growth_g3 = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth_milwaukee_ramp.parquet")
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id", "context_group"]]
    spec = area_levels_spec(PARAMS)
    opt0, cfg0 = spec["option"], spec["config"]
    rev = pd.read_csv(REFERENCE / "pooled_revision_wi.csv")
    ref = rev[rev["option"].eq(opt0) & rev["config"].eq(cfg0)].iloc[0]
    params = json.loads(PARAMS.read_text())
    scen = load_scenario()
    levels = load_area_levels()
    apaths = area_paths(PARAMS)
    missing = set(apaths["area_id"]) - set(areas["area_id"])
    if missing:
        raise SystemExit(f"area_paths name unknown areas: {sorted(missing)}")

    # check: the stored lower factor and every stored ramp follow from the files
    fac_low = bottom_states_factor(opt0, cfg0)
    if abs(fac_low - lower_rule()["factor"]) > 1e-4:
        raise SystemExit(f"lower factor {fac_low:.5f} != params {lower_rule()['factor']}")
    for pth, fac in (("lower", fac_low), ("central", 1.0), ("upper", float(ref["factor80"]))):
        want = pooled_ramp(opt0, cfg0, fac, areas_g3)
        got = params["paths"][pth]["ramp"]
        if max(abs(a - b) for a, b in zip(want, got)) > 6e-4:
            raise SystemExit(f"{pth} ramp {got} does not follow from the per-area year levels {want}")

    out = e.run(areas, scen, growth, levels, apaths)
    problems = e.check_invariants(out)
    if problems:
        raise SystemExit(f"invariant failures: {problems}")

    # check: on the Gate 3 rates, with the Gate 3 lower and without the Madison path, the engine reproduces the
    # revision runner's totals
    scen_g3 = load_scenario(**revision_ramps(rev, opt0, cfg0))
    lv_g3 = load_area_levels(lower="percentile10")
    pooled_g3 = path_totals(e.run(areas_g3, scen_g3, growth_g3, lv_g3))
    for p, c in PATH_COLS.items():
        if abs(pooled_g3[p] - ref[c]) > 2.0:     # ramps are stored to 4 decimals
            raise SystemExit(f"engine {p} {pooled_g3[p]:.1f} does not reproduce pooled_revision_wi.csv {ref[c]:.1f}")

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
    # moves: which number the case changes. "statewide addition" = the permits the law adds statewide;
    # "baseline only" = only the current-law rate changes (the addition then moves the other way by about as much);
    # "local distribution only" = where permits land, with the statewide addition unchanged (no current case).
    main_t = path_totals(out)
    base5 = float(state["baseline_units"].iloc[0])
    sens = []

    def add(change, moves, description, kind, madison, t, source, baseline=base5):
        def v(p):
            return round(t[p], 1) if t.get(p) is not None else None
        sens.append({"change": change, "moves": moves, "description": description, "kind": kind, "madison": madison,
                     "lower_additional_5yr": v("lower"), "central_additional_5yr": v("central"),
                     "upper_additional_5yr": v("upper"),
                     "difference_lower": round(t["lower"] - main_t["lower"], 1) if t.get("lower") is not None else None,
                     "difference_central": round(t["central"] - main_t["central"], 1),
                     "difference_upper": round(t["upper"] - main_t["upper"], 1) if t.get("upper") is not None else None,
                     "baseline_5yr": round(baseline, 1), "source": source})

    def run_t(a=areas, g=growth, sc=scen, lv=levels, ap=apaths):
        o = e.run(a, sc, g, lv, ap)
        return path_totals(o), float(e.five_year_totals(o)["baseline_units"].iloc[0])

    add("adopted: pooled revision (ii) cap+A2, configuration A, Madison on the Madison-like path; lower = mean of "
        "Rhode Island and Oregon; Milwaukee at its measured 2022-2025 rate", "none (adopted)",
        "The three scenarios as adopted.", "engine", "path", main_t, "this run")
    t10, _ = run_t(sc=load_scenario(lower={"ramp": revision_ramps(rev, opt0, cfg0)["lower"]["ramp"]}),
                   lv=load_area_levels(lower="percentile10"))
    add("Lower as a statistical 10th percentile of the between-state spread (the Gate 3 lower: central levels / 1.885)",
        "statewide addition",
        "The lower scenario is set at the 10th percentile of how much the eight statewide-law states' levels differ "
        "(every place's central level divided by 1.885), as at Gate 3, instead of the average of the two slowest "
        "states, Rhode Island and Oregon. That level is below every statewide-law state's. Only the lower changes.",
        "engine", "path", {"lower": t10["lower"], "central": main_t["central"], "upper": main_t["upper"]},
        "reference/pooled_revision_wi_y_by_area.csv (y_plateau_lower_80) and pooled_revision_wi.csv (ramp_lower)")
    tm, _ = run_t(ap=None)
    add("Madison at its pooled level (no Madison-like path)", "statewide addition",
        "Madison follows the statewide estimate for places like it instead of the path that similar cities in "
        "Washington and Oregon took. This changes Madison's addition only, and through it the statewide total.",
        "engine", "pooled level", tm, "engine without area_paths")
    for lab, opt, cfg, what in (
            ("California out of the common level (configuration B)", "cap_a2", "B_ca_out_of_common_level",
             "The eight states' typical level is set without California. The central falls, and Strong adoption falls "
             "most, because California is the state that stretches the range upward. This alternative predicted the "
             "held-out states less well."),
            ("LA-calibrated multifamily correction (option iii, configuration A)", "cap_la_calibrated",
             "A_ca_in_common_level",
             "California's counts include ADUs on apartment and other multifamily properties, which the benchmark law "
             "does not allow. This removes more of them, using Los Angeles County parcel records.")):
        rr = revision_ramps(rev, opt, cfg)
        rr["lower"] = {"ramp": pooled_ramp(opt, cfg, bottom_states_factor(opt, cfg), areas_g3)}
        t, _ = run_t(sc=load_scenario(**rr), lv=load_area_levels(opt, cfg))
        add(lab, "statewide addition", what + " The lower is the same Rhode Island and Oregon average, taken from this fit.",
            "engine", "path", t, f"reference/pooled_revision_wi_y_by_area.csv ({opt} x {cfg})")
    t, _ = run_t(sc=load_scenario(central={"ramp": [1, 1, 1, 1, 1]}))
    r_c = params["paths"]["central"]["ramp"]
    add("no ramp (full rate from 2027; Madison's observed path unchanged)", "statewide addition",
        f"In the adopted model the law reaches about {r_c[0]:.0%}, {r_c[1]:.0%} and {r_c[2]:.0%} of its full effect in "
        "2027, 2028 and 2029 (central), as it did in other states. Here it is at full strength from the first year.",
        "engine", "path", {"central": t["central"]}, "engine, central ramp set to 1")
    rural_ids = set(geo.loc[geo.context_group.isin(["rural", "small_community"]), "area_id"])
    lv2 = levels.copy()
    floor = madison_floor()
    lv2.loc[lv2.area_id.isin(rural_ids), "y_central"] = floor
    t, _ = run_t(lv=lv2)
    add(f"rural and small-community places at the Madison floor ({floor:g})", "statewide addition",
        f"Rural areas and small communities, which have no measured activity, get only the minimum rate set from "
        f"Madison's permits ({floor:g} per 1,000 single-family homes per year) instead of their level from the "
        "statewide estimate. Shows how much of the addition comes from those places.",
        "engine", "path", {"central": t["central"]}, "engine, rural y_central = floor")
    eb = pd.read_csv(REFERENCE / "eligible_basis_wi.csv")
    r = eb[eb["run"].eq("denominator without one-unit attached homes")].iloc[0]
    add("eligible-property basis without one-unit attached homes: permits per 1,000 properties eligible under each "
        "state's law (detached homes plus multifamily properties)", "statewide addition",
        "Rates are divided by the properties each state's law makes eligible (houses plus small multifamily "
        "properties) instead of by single-family homes. A separate model with its own baseline "
        f"({float(r['engine_baseline']):,.0f} permits); it was run at Gate 3 (Milwaukee on its assumed ramp) and is not "
        "rerun here, and its 10th-percentile lower is left out because the adopted lower is defined differently.",
        "model", "path", {"central": r["engine_central_madison_path"], "upper": r["engine_upper_tau90_madison_path"]},
        "reference/eligible_basis_wi.csv (docs/gate3/ELIGIBLE_BASIS.md; Gate 3 run, not recomputed)",
        baseline=float(r["engine_baseline"]))
    refit = refit_model_sensitivities({"adopted": (areas, growth), "gate3": (areas_g3, growth_g3)})
    for k, col in (("multiplicative", "sens_multiplicative"), ("ca_only", "sens_ca_only_regression")):
        if abs(refit["gate3"][k] - float(ref[col])) > 0.5:
            raise SystemExit(f"{k}: refit on the Gate 3 rates {refit['gate3'][k]:.1f} != pooled_revision_wi.csv {ref[col]:.1f}")
    add("multiplicative: the law only multiplies each place's current rate by the pooled statewide-law factor",
        "statewide addition",
        "Each place's current rate is multiplied by one statewide factor, instead of rising to the level that similar "
        "places reached in the eight statewide-law states. Places that permit almost nothing today would stay near "
        "zero. Before-and-after counts in other states contradict this, but no Midwest state has data after a "
        "statewide law yet.", "model", "multiplicative like every place",
        {"central": refit["adopted"]["multiplicative"]},
        "scripts/run_pooled_revision.py multiplicative(), refitted on the adopted current-law rates")
    add("California-only market regression (refitted on cap+A2 counts)", "statewide addition",
        "Wisconsin places are predicted from a model fitted on California cities alone, where cities like Madison "
        "responded weakly. A downside case.", "model", "regression like every place",
        {"central": refit["adopted"]["ca_only"]},
        "scripts/run_pooled_revision.py ca_only_regression(), on the adopted current-law rates")

    # baseline-only cases (scripts/run_baseline_only_effects.py builds the same cases and checks each baseline
    # against reference/wi_baseline_sensitivities.csv)
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_baseline_only_effects import CASE_TEXT, baseline_only_cases
    for cid, label, a, g, _chk in baseline_only_cases(areas, growth):
        t, b = run_t(a=a, g=g)
        add(label, "baseline only", CASE_TEXT[cid], "baseline", "path", t, f"engine with only the current-law rate "
            f"changed (reference/adu_model_baseline_only_effects.csv, case {cid})", baseline=b)
    sdf = pd.DataFrame(sens)
    sdf.to_csv(REFERENCE / "adu_model_sensitivities.csv", index=False)

    # ---------------- reference lines ----------------
    homes = float(areas["homes"].sum())
    lines, line_by_year = reference_lines(by_year, homes)
    lines.to_csv(REFERENCE / "adu_model_reference_lines.csv", index=False)
    line_by_year.to_csv(REFERENCE / "adu_model_reference_line_by_year.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(state.round(1).to_string(index=False))
    print(by_year.round(1).to_string(index=False))
    print(lines.drop(columns=["line"]).to_string(index=False))
    print(sdf[["change", "moves", "lower_additional_5yr", "central_additional_5yr", "upper_additional_5yr",
               "difference_central", "baseline_5yr"]].to_string(index=False))


if __name__ == "__main__":
    main()

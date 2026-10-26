"""Unknown-rules variants (Gate 5; Gate 4 recommendation 2): full engine runs for each treatment of places whose
local ADU rules are not coded.

1,882 of 1,925 county-subdivision areas (1,267,433 of 1,839,569 one-unit detached homes, 68.9%) have no coded ADU rules
(x_basis "uncoded_like_restricted_AQ027"). The adopted model (AQ-027, superseding the AQ-023 default) gives them
the restricted group's current-law rate. This script reruns the adopted engine (same parameters, per-area levels,
ramps and Madison path as scripts/run_adu_model.py) three times, changing only the current-law rate x of those
areas:

  unknown_treatment   contract enum (docs/gate1/DATA_CONTRACTS.md)  x for uncoded areas
  like_restricted     (adopted; AQ-027 replaced "sample_mix")        restricted group: 34 / 560.398 = 0.06067
  like_prohibited     all_prohibited                                 prohibited group: 5 / 159.931 = 0.03126
  like_benchmark      all_compliant                                  benchmark group (Madison 2022-2025):
                                                                     40 / 213.168 = 0.18765; at_benchmark = True

Rates are second-home permits per 1,000 one-unit detached homes per year, rebuilt unrounded from the counts and
thousand home-years in reference/wi_baseline_rates_by_group.csv. Setting at_benchmark has no effect on y while
the spillover is 0 in every path (params file), and is set only so the variant is internally consistent.

The rate with the law (y) does not depend on a place's current rules, so changing x moves the baseline one way and
the addition about as far the other way; the total with the law moves only where x crosses y or the floor.

Inputs: as scripts/run_adu_model.py (data/processed/model_baseline/engine_areas.parquet, engine_baseline_growth.parquet,
reference/adu_model_params.json, reference/pooled_revision_*.csv), plus reference/wi_baseline_rates_by_group.csv and
data/processed/foundation/areas.parquet (county and context labels).
Outputs (one run group; each variant has run_id = <run_group_id>-<unknown_treatment>):
  data/processed/model_run/unknown_rules/results_long.parquet   engine rows by variant, area, path, year
  data/processed/model_run/unknown_rules/run_manifest.json      run group, inputs with SHA-256, checks
  reference/adu_model_unknown_rules_statewide.csv               variant x path: 2027-2031 baseline, addition, total, differences
  reference/adu_model_unknown_rules_statewide_by_year.csv       variant x path x year
  reference/adu_model_unknown_rules_by_county.csv               variant x county x path, 2027-2031
  reference/adu_model_unknown_rules_by_context.csv              variant x context group x path, 2027-2031
  reference/adu_model_unknown_rules_by_area.csv                 variant x area, 2027-2031 baseline and the three additions
Run: uv run python scripts/run_unknown_rules_variants.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from missing_middleware.model import engine as e  # noqa: E402
from missing_middleware.model.params import area_paths  # noqa: E402
from missing_middleware.paths import PROCESSED, REFERENCE, ROOT, processed_dir  # noqa: E402

UNCODED = "uncoded_like_restricted_AQ027"
ADOPTED = "like_restricted"
VARIANTS = {   # unknown_treatment: (group whose rate uncoded areas take, contract enum, at_benchmark, label)
    "like_restricted": ("restricted", "like_restricted (adopted, AQ-027; replaces sample_mix)", False,
                        "Uncoded places behave like places that restrict ADUs (adopted)"),
    "like_prohibited": ("prohibited", "all_prohibited", False,
                        "Uncoded places behave like places that prohibit ADUs"),
    "like_benchmark": ("benchmark", "all_compliant", True,
                       "Uncoded places behave like places that already allow ADUs as the bill would (Madison's rate)"),
}
INPUTS = ["reference/adu_model_params.json", "reference/wi_baseline_rates_by_group.csv",
          "reference/pooled_revision_wi_y_by_area.csv", "reference/pooled_revision_stage2_levels.csv",
          "reference/pooled_revision_wi.csv", "data/processed/model_baseline/engine_areas.parquet",
          "data/processed/model_baseline/engine_baseline_growth.parquet", "missing_middleware/model/engine.py",
          "scripts/run_unknown_rules_variants.py"]


def group_rates() -> dict[str, float]:
    g = pd.read_csv(REFERENCE / "wi_baseline_rates_by_group.csv").set_index("group")
    return {k: float(g.loc[k, "units"] / g.loc[k, "thousand_home_years"]) for k in ("prohibited", "restricted", "benchmark")}


def variant_areas(areas: pd.DataFrame, treatment: str, rates: dict | None = None) -> pd.DataFrame:
    """Engine areas with the uncoded areas' current-law rate set by `treatment` (a VARIANTS key)."""
    group, _, at_bm, _ = VARIANTS[treatment]
    rates = rates or group_rates()
    a = areas.copy()
    m = a["x_basis"].eq(UNCODED)
    if treatment != ADOPTED:
        a.loc[m, "x_rate"] = rates[group]
        a.loc[m, "at_benchmark"] = at_bm
    return a


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_group_id() -> str:
    h = hashlib.sha256("".join(sha(ROOT / p) for p in INPUTS).encode()).hexdigest()
    return f"adu-unk-{h[:10]}"


def main():
    from run_adu_model import load_area_levels, load_scenario

    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id", "context_group"]]
    scen, levels, apaths = load_scenario(), load_area_levels(), area_paths()
    rates = group_rates()
    gid = run_group_id()
    uncoded = areas["x_basis"].eq(UNCODED)
    checks = []

    outs = []
    for t in VARIANTS:
        o = e.run(variant_areas(areas, t, rates), scen, growth, levels, apaths)
        probs = e.check_invariants(o)
        if probs:
            raise SystemExit(f"{t}: invariant failures {probs}")
        o.insert(0, "unknown_treatment", t)
        o.insert(0, "run_id", f"{gid}-{t}")
        o.insert(0, "run_group_id", gid)
        outs.append(o)
    out = pd.concat(outs, ignore_index=True)

    # check 1: the adopted variant reproduces the adopted engine run row for row
    adopted = pd.read_parquet(PROCESSED / "model_run/results_long.parquet")
    mine = out[out.unknown_treatment.eq(ADOPTED)].drop(columns=["run_group_id", "run_id", "unknown_treatment"])
    k = ["area_id", "path", "year"]
    cmp = adopted.merge(mine, on=k, suffixes=("", "_v"), validate="1:1")
    gap = max((cmp.baseline_units - cmp.baseline_units_v).abs().max(), (cmp.additional_units - cmp.additional_units_v).abs().max())
    if len(cmp) != len(adopted) or gap > 1e-9:
        raise SystemExit(f"adopted variant differs from data/processed/model_run/results_long.parquet (max gap {gap})")
    checks.append(f"adopted variant equals model_run/results_long.parquet row for row ({len(cmp):,} rows, max gap {gap:.1e} permits)")

    # check 2: each variant's baseline equals the baseline builder's sensitivity where one exists
    bsens = pd.read_csv(REFERENCE / "wi_baseline_sensitivities.csv").set_index("sensitivity")["b5yr_central"]
    for t, lab in ((ADOPTED, "main (central path)"), ("like_prohibited", "uncoded places behave like prohibited (old AQ-023 default)")):
        b = out[out.unknown_treatment.eq(t) & out.path.eq("central")].baseline_units.sum()
        if abs(b - float(bsens[lab])) > 0.05:
            raise SystemExit(f"{t}: baseline {b:.2f} != wi_baseline_sensitivities.csv {bsens[lab]}")
        checks.append(f"{t}: baseline {b:.2f} equals reference/wi_baseline_sensitivities.csv '{lab}'")

    od = processed_dir("model_run/unknown_rules")
    out.to_parquet(od / "results_long.parquet", index=False)
    full = out.merge(geo, on="area_id", how="left")

    # statewide, five-year
    st = full.groupby(["unknown_treatment", "path"])[["baseline_units", "additional_units"]].sum().reset_index()
    st["total_with_law"] = st.baseline_units + st.additional_units
    ref = st[st.unknown_treatment.eq(ADOPTED)].set_index("path")
    for c in ("baseline_units", "additional_units", "total_with_law"):
        st[f"d_{c}"] = st[c] - st.path.map(ref[c])
    st["run_group_id"] = gid
    st["run_id"] = gid + "-" + st.unknown_treatment
    st["adopted"] = st.unknown_treatment.eq(ADOPTED)
    st["contract_enum"] = st.unknown_treatment.map({k: v[1] for k, v in VARIANTS.items()})
    st["label"] = st.unknown_treatment.map({k: v[3] for k, v in VARIANTS.items()})
    st["x_rate_uncoded"] = st.unknown_treatment.map({k: rates[v[0]] for k, v in VARIANTS.items()}).round(5)
    st["uncoded_areas"] = int(uncoded.sum())
    st["uncoded_homes"] = int(areas.loc[uncoded, "homes"].sum())
    st["state_homes"] = int(areas["homes"].sum())
    order = {t: i for i, t in enumerate(VARIANTS)}
    st = st.sort_values(["unknown_treatment", "path"], key=lambda s: s.map(order) if s.name == "unknown_treatment" else s)
    cols = ["run_group_id", "run_id", "unknown_treatment", "adopted", "contract_enum", "label", "path", "baseline_units",
            "additional_units", "total_with_law", "d_baseline_units", "d_additional_units", "d_total_with_law",
            "x_rate_uncoded", "uncoded_areas", "uncoded_homes", "state_homes"]
    st[cols].round(4).to_csv(REFERENCE / "adu_model_unknown_rules_statewide.csv", index=False)

    # check 3: the adopted rows equal reference/adu_model_statewide.csv
    sw = pd.read_csv(REFERENCE / "adu_model_statewide.csv").set_index("path")
    for p in e.PATHS:
        for c in ("baseline_units", "additional_units"):
            if abs(ref.loc[p, c] - sw.loc[p, c]) > 1e-6:
                raise SystemExit(f"adopted {p} {c} {ref.loc[p, c]} != adu_model_statewide.csv {sw.loc[p, c]}")
    checks.append("adopted variant's statewide 2027-2031 totals equal reference/adu_model_statewide.csv in every path")

    by_year = full.groupby(["unknown_treatment", "path", "year"])[["baseline_units", "additional_units"]].sum().reset_index()
    by_year["forecast_year"] = 2026 + by_year.year
    by_year["total_with_law"] = by_year.baseline_units + by_year.additional_units
    by_year.insert(0, "run_group_id", gid)
    by_year.round(4).to_csv(REFERENCE / "adu_model_unknown_rules_statewide_by_year.csv", index=False)

    for key, fn in (("parent_county_id", "by_county"), ("context_group", "by_context")):
        t = full.groupby(["unknown_treatment", key, "path"])[["baseline_units", "additional_units"]].sum().reset_index()
        y1 = full[full.year.eq(1)].assign(uncoded_homes=lambda d: d.homes.where(d.x_basis.eq(UNCODED), 0))
        h = y1.groupby(["unknown_treatment", key, "path"])[["homes", "uncoded_homes"]].sum().reset_index()
        t = h.merge(t, on=["unknown_treatment", key, "path"], validate="1:1")
        t["total_with_law"] = t.baseline_units + t.additional_units
        t.insert(0, "run_group_id", gid)
        t.round(4).to_csv(REFERENCE / f"adu_model_unknown_rules_{fn}.csv", index=False)
        # check 4: every grouping reconciles to the statewide row
        s = t.groupby(["unknown_treatment", "path"])[["baseline_units", "additional_units"]].sum()
        g = st.set_index(["unknown_treatment", "path"])[["baseline_units", "additional_units"]]
        d = float((s - g.loc[s.index]).abs().max().max())
        if d > 1e-6:
            raise SystemExit(f"{fn} does not reconcile to the state (gap {d})")
        checks.append(f"{fn}: sums to the statewide row for every variant and path (max gap {d:.1e} permits)")

    # compact by-area five-year table for the UI (baseline is the same in every path)
    w = full.pivot_table(index=["unknown_treatment", "area_id"], columns="path", values="additional_units", aggfunc="sum")
    w.columns = [f"additional_{c}" for c in w.columns]
    b = full[full.path.eq("central")].groupby(["unknown_treatment", "area_id"]).agg(
        homes=("homes", "first"), x_rate=("x_rate", "first"), uncoded=("x_basis", lambda v: bool(v.iloc[0] == UNCODED)),
        baseline=("baseline_units", "sum"))
    ba = b.join(w).reset_index()
    ba.insert(0, "run_group_id", gid)
    ba["x_rate"] = ba["x_rate"].round(5)
    ba.round({c: 3 for c in ba.columns if c != "x_rate"}).to_csv(REFERENCE / "adu_model_unknown_rules_by_area.csv", index=False)

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = ""
    manifest = {
        "run_group_id": gid, "run_date": date.today().isoformat(), "model_version": commit,
        "scenario_id": scen.scenario_id, "parameter_file": "reference/adu_model_params.json",
        "runs": [{"run_id": f"{gid}-{t}", "unknown_treatment": t, "contract_enum": v[1], "label": v[3],
                  "adopted": t == ADOPTED, "x_rate_uncoded": round(rates[v[0]], 6), "at_benchmark_uncoded": v[2]}
                 for t, v in VARIANTS.items()],
        "uncoded": {"x_basis": UNCODED, "areas": int(uncoded.sum()), "homes": int(areas.loc[uncoded, "homes"].sum()),
                    "state_homes": int(areas["homes"].sum())},
        "analysis_dates": {"last_observed_year": 2025, "forecast_years": "2027-2031", "effective_date": "2026-12-31 (stylized)"},
        "units": "second-home permits on single-family lots at issuance; rates per 1,000 one-unit detached homes per year",
        "inputs": {p: sha(ROOT / p) for p in INPUTS},
        "validation": checks,
    }
    (od / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    pd.set_option("display.width", 250)
    print(gid)
    print(st[["unknown_treatment", "path", "baseline_units", "additional_units", "total_with_law", "d_baseline_units",
              "d_additional_units", "d_total_with_law"]].round(1).to_string(index=False))
    print("\n".join(checks))


if __name__ == "__main__":
    main()

"""Measure 2022-2025 second-home permits in more Wisconsin places and test rules vs activity (Gate 3).

    uv run python scripts/build_wi_more_cities.py           # from local raw caches (data/raw/wimc_*)
    uv run python scripts/build_wi_more_cities.py --fetch   # download the adapter sources first (plain HTTP GET)

Inputs:
    data/raw/wimc_<slug>/            one folder per adapter (missing_middleware/permits/wimc_<slug>.py)
    data/raw/milwaukee_permits, milwaukee_mprop (Gate 3 baseline caches)
    data/raw/census_acs5_2024_tbsf_market (ACS B25077/B19013, from scripts/run_ca_regression.py)
    reference/madison_adu_permits_by_year.csv, pleasant_prairie_*, sun_prairie_*, wi_baseline_observed.csv
    reference/wi_baseline_by_municipality.csv (homes), wi_rights_exposure.csv, wi_adu_rules.csv,
    wi_holdout_coded_places.csv
Outputs:
    reference/wi_measured_permits_2022_2025.csv          one row per measured place
    reference/wi_rules_vs_activity_by_year.csv           place x year counts and coverage
    reference/wi_rules_vs_activity_places.csv            measured places with rules, groups, market
    reference/wi_rules_vs_activity_crosstabs.csv         rule value x activity group (counts of places)
    reference/wi_rules_vs_activity_rates.csv             pooled rates by rule value
    reference/wi_rules_vs_activity_correlations.csv      Spearman rank correlations (permutation p)
    reference/wi_rules_vs_activity_prediction.csv        rules-based group vs measured group
    data/processed/wi_more_cities/record_review.csv      counted and unconfirmed records (house numbers redacted)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE, processed_dir  # noqa: E402
from missing_middleware.permits import wi_more_cities as wm  # noqa: E402

RATE_UNIT = ("second-home permits on single-family lots (numerator) per 1,000 ACS 2020-2024 one-unit detached "
             "homes per year (denominator: homes x complete years observed in 2022-2025 / 1,000)")

RULE_VARS = ("ordinance_status", "rights_group", "current_class", "tier", "n_flags",
             "window_rights_group", "window_tier", "window_n_flags")
RULE_TO_GROUP = {"scenario_benchmark": "active", "restricted": "middle", "prohibited": "restrictive"}


def build(fetch: bool = False, ref_dir: Path = REFERENCE, raw_root: Path = RAW, out_ref: Path = REFERENCE,
          out_proc: Path | None = None, log=print) -> dict:
    py, metas, review = wm.place_years(ref_dir, raw_root, fetch=fetch, log=log)
    homes = wm.homes_by_place(ref_dir, metas)
    meas = wm.measured_table(py, homes)
    mk = wm.market_values(meas["geoid"], raw_root)
    meas = meas.merge(mk.drop_duplicates("geoid"), on="geoid", how="left")

    rules = wm.coded_rules(ref_dir)
    held = wm.holdout_ids(ref_dir)
    by_name = rules.set_index("jurisdiction_name")
    keep = ["ordinance_status", "current_class", "class_basis", "restrictions", "n_flags", "n_tier1", "n_tier2",
            "tier", "rights_group", "strictness", "window_class", "window_flags", "window_n_flags", "window_tier",
            "window_rights_group", "window_strictness", "window_note", "rules_source"]
    for c in keep:
        meas[c] = meas["place"].map(by_name[c]) if c in by_name else np.nan
    meas["coded"] = meas["rules_source"].fillna("").str.startswith("coded")
    meas["holdout"] = meas["geoid"].isin(held)
    meas["measured_2plus_years"] = meas["years_observed"].ge(2)

    # groups: pre-registered sample (whole 2022-2025 window) and the >=2-complete-years sensitivity
    g_full = wm.groups(meas, "measured_full_window")
    g_2 = wm.groups(meas, "measured_2plus_years")
    meas["group_v1"], meas["group_v1_1"] = g_full["group_v1"], g_full["group_v1_1"]
    meas["cutoff_v1"], meas["n_measured_v1"] = g_full["cutoff_v1"], g_full["n_measured_for_rule"]
    meas["group_v1_2yr"], meas["group_v1_1_2yr"] = g_2["group_v1"], g_2["group_v1_1"]
    meas["cutoff_v1_2yr"], meas["n_measured_v1_2yr"] = g_2["cutoff_v1"], g_2["n_measured_for_rule"]

    samples = {
        "coded_full_window": (meas["coded"] & meas["measured_full_window"], "group_v1", "group_v1_1"),
        "coded_2plus_years": (meas["coded"] & meas["measured_2plus_years"], "group_v1_2yr", "group_v1_1_2yr"),
        "coded_2plus_years_excl_holdouts": (meas["coded"] & meas["measured_2plus_years"] & ~meas["holdout"],
                                            "group_v1_2yr", "group_v1_1_2yr"),
        "all_2plus_years_incl_provisional_rules": (meas["measured_2plus_years"] & meas["rules_source"].notna(),
                                                   "group_v1_2yr", "group_v1_1_2yr"),
    }
    xt, rates, cors, pred = [], [], [], []
    for name, (mask, g1, g11) in samples.items():
        d = meas[mask]
        for rv in RULE_VARS:
            for gc in (g1, g11):
                xt.append(wm.crosstab_long(d, rv, gc, name))
            rates.append(wm.rate_by_rule(d, rv, name))
        for xv, label in (("strictness", "rule strictness, current coding (0 benchmark, 1 tier-2 only, 2 tier-1 flag, 3 prohibited)"),
                          ("window_strictness", "rule strictness in force for most of 2022-2025 (same scale)"),
                          ("value", "ACS 2020-2024 median home value, dollars (county subdivision)"),
                          ("income", "ACS 2020-2024 median household income, dollars")):
            for yv, ylabel in (("rate_per_1000_homes_yr", "rate"), ("rate_upper_per_1000_homes_yr", "upper-bound rate")):
                r = wm.spearman(d[xv], d[yv])
                cors.append({"sample": name, "x": xv, "x_meaning": label, "y": yv, "y_meaning": f"{ylabel}: {RATE_UNIT}", **r,
                             "unit": "Spearman rho (rank correlation, -1 to 1) over n places; p = share of 20,000 "
                                     "random permutations with |rho| at least as large"})
        # restricted places only: number of flags vs rate
        dr = d[d["window_rights_group"].eq("restricted")]
        r = wm.spearman(dr["window_n_flags"], dr["rate_per_1000_homes_yr"])
        cors.append({"sample": name + ":restricted_in_window_only", "x": "window_n_flags",
                     "x_meaning": "number of restriction flags in force for most of 2022-2025", "y": "rate_per_1000_homes_yr",
                     "y_meaning": f"rate: {RATE_UNIT}", **r, "unit": "Spearman rho over n restricted places"})
        for basis in ("rights_group", "window_rights_group"):
            p_ = d[basis].map(RULE_TO_GROUP)
            for gc in (g1, g11):
                ok = p_.eq(d[gc])
                pred.append({"sample": name, "rule_basis": basis, "grouping": gc, "places": int(len(d)),
                             "agree": int(ok.sum()), "share_agree": float(ok.mean()) if len(d) else np.nan,
                             "baseline_all_restrictive_agree": int(d[gc].eq("restrictive").sum()),
                             "unit": "places where benchmark->active, restricted->middle, prohibited->restrictive matches the "
                                     "measured group (numerator) out of measured places in the sample (denominator)",
                             "disagreements": "; ".join(f"{pl}: rules {a} vs measured {b}" for pl, a, b, o in
                                                        zip(d["place"], p_, d[gc], ok) if not o)})

    out_ref.mkdir(parents=True, exist_ok=True)
    m_out = meas.assign(GEOID=meas["geoid"], rate_unit=RATE_UNIT)
    cols = ["place", "GEOID", "pieces", "permits", "permits_upper", "years_observed", "complete_years",
            "partial_months_not_used", "homes", "thousand_home_years", "rate_per_1000_homes_yr",
            "rate_poisson95_lo", "rate_poisson95_hi", "rate_upper_per_1000_homes_yr", "stage", "quality",
            "quality_note", "measured_full_window", "rate_unit"]
    m_out.sort_values(["measured_full_window", "rate_per_1000_homes_yr"], ascending=[False, False])[cols].round(4).to_csv(
        out_ref / "wi_measured_permits_2022_2025.csv", index=False)
    py.assign(units_unit="second-home units permitted in the calendar year (count)")[
        ["place", "slug", "year", "units", "upper_units", "months", "complete", "stage", "note", "units_unit"]].to_csv(
        out_ref / "wi_rules_vs_activity_by_year.csv", index=False)
    pcols = ["place", "GEOID", "coded", "holdout", "rules_source", "class_basis", "ordinance_status", "current_class",
             "restrictions", "n_flags", "n_tier1", "n_tier2", "tier", "strictness", "window_class", "window_flags",
             "window_n_flags", "window_tier", "window_strictness", "window_note", "permits", "permits_upper",
             "years_observed", "homes", "rate_per_1000_homes_yr", "rate_upper_per_1000_homes_yr", "stage", "quality",
             "value", "income", "group_v1", "group_v1_1", "cutoff_v1", "n_measured_v1", "group_v1_2yr",
             "group_v1_1_2yr", "cutoff_v1_2yr", "n_measured_v1_2yr"]
    m_out[pcols].round(4).to_csv(out_ref / "wi_rules_vs_activity_places.csv", index=False)
    pd.concat(xt).to_csv(out_ref / "wi_rules_vs_activity_crosstabs.csv", index=False)
    pd.concat(rates).round(4).to_csv(out_ref / "wi_rules_vs_activity_rates.csv", index=False)
    pd.DataFrame(cors).round(4).to_csv(out_ref / "wi_rules_vs_activity_correlations.csv", index=False)
    pd.DataFrame(pred).round(4).to_csv(out_ref / "wi_rules_vs_activity_prediction.csv", index=False)
    if out_proc is None:
        out_proc = processed_dir("wi_more_cities")
    out_proc.mkdir(parents=True, exist_ok=True)
    if len(review):
        review.to_csv(out_proc / "record_review.csv", index=False)
    summary = {"places": len(meas), "measured_full_window": int(meas["measured_full_window"].sum()),
               "measured_2plus_years": int(meas["measured_2plus_years"].sum()),
               "coded_full_window": int((meas["coded"] & meas["measured_full_window"]).sum()),
               "coded_2plus_years": int((meas["coded"] & meas["measured_2plus_years"]).sum())}
    (out_proc / "summary.json").write_text(json.dumps(summary, indent=2))
    log(json.dumps(summary))
    return {"measured": meas, "place_years": py, "correlations": pd.DataFrame(cors), "prediction": pd.DataFrame(pred)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    res = build(fetch=a.fetch)
    m = res["measured"]
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(m[["place", "permits", "permits_upper", "years_observed", "homes", "rate_per_1000_homes_yr", "stage",
                 "quality", "current_class", "window_class", "group_v1", "group_v1_1", "group_v1_2yr", "value"]])
        print(res["correlations"][["sample", "x", "y", "n", "rho", "p_perm"]])
        print(res["prediction"][["sample", "rule_basis", "grouping", "places", "agree"]])


if __name__ == "__main__":
    main()

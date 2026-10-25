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
    data/processed/wi_more_cities/aq039_new_house_adus.csv  AQ-039 check: ADUs permitted with a new house

AQ-039 (2026-10-25): an ADU permitted with a new house counts on a teardown lot and not on a vacant
lot. The pilots apply it in their own builds (reference rows `second_home_sf_lot:adu_teardown_rebuild`
and `second_home_diag:vacant_lot_new_house_adu`). For the `wimc_*` places the same rule
(`second_homes.new_house_adus`) is run on each adapter's classified records here; a teardown-lot ADU
that the adapter has not counted stops the build (it must be judged in the adapter). The by-year table
carries both lines by place and year; they are missing (not zero) where the source cannot show them
(Milwaukee: no descriptions; Fitchburg: text hits only, none).
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
from missing_middleware.permits import classify, second_homes  # noqa: E402
from missing_middleware.permits import wi_more_cities as wm  # noqa: E402

RATE_UNIT = ("second-home permits on single-family lots (numerator) per 1,000 ACS 2020-2024 one-unit detached "
             "homes per year (denominator: homes x complete years observed in 2022-2025 / 1,000)")

RULE_VARS = ("ordinance_status", "rights_group", "current_class", "tier", "n_flags",
             "window_rights_group", "window_tier", "window_n_flags")
RULE_TO_GROUP = {"scenario_benchmark": "active", "restricted": "middle", "prohibited": "restrictive"}


AQ039_TD = "teardown_rebuild_adu_units"
AQ039_VAC = "diag_vacant_lot_new_house_adu_units"
_RAZE_RE = r"\braz(?:e|ing)\b|demoli|wreck"
_ADU_COMPONENTS = ("adu_detached", "adu_attached", "adu_conversion", "adu_two_unit")


def wimc_new_house_adus(c: pd.DataFrame) -> pd.DataFrame:
    """AQ-039 rule on one adapter's classified records (columns of `classify_records`).

    Lot key = parcel number, else house number + street. ADU = a counted ADU component or ADU wording
    (`classify.ADU_RE`, or a Kaukauna 'Additional dwelling unit' work target). New house = permit type or
    text naming a new principal dwelling (`second_homes.NEW_HOUSE_RE`, 'Residential - New', 'New Home').
    Dwelling raze = raze / demolition / wrecking wording in the type or text."""
    txt = c["permit_type"].fillna("").astype(str) + " | " + c["description"].fillna("").astype(str)
    for col in ("target", "work_type"):
        if col in c.columns:
            txt = txt + " | " + c[col].fillna("").astype(str)
    adu = (c["component"].isin(_ADU_COMPONENTS) | c["description"].fillna("").astype(str).str.contains(classify.ADU_RE)
           | txt.str.contains(r"additional\s+dwelling\s+unit", case=False, regex=True))
    adu &= ~txt.str.contains(_RAZE_RE, case=False, regex=True)
    new_house = (txt.str.contains(second_homes.NEW_HOUSE_RE) | txt.str.contains(r"Residential - New|New Home", case=False,
                                                                                 regex=True)) & ~adu
    addr = c["house_nbr"].astype(str).where(c["house_nbr"].notna()) + " " + c["street"].astype(str)
    key = c["parcel_id"].where(c["parcel_id"].notna(), addr)
    df = pd.DataFrame({"permit_id": c["permit_id"], "issue_date": pd.to_datetime(c["date"]),
                       "units_added": c["units"].where(c["component"].notna(), 1)}, index=c.index)
    nh = second_homes.new_house_adus(df, key=key, adu=adu, new_house=new_house,
                                     dwelling_raze=txt.str.contains(_RAZE_RE, case=False, regex=True))
    return nh.join(c[["permit_id", "year", "component", "units"]])


def aq039_by_place_year(py: pd.DataFrame, ref_dir: Path, raw_root: Path, adapters=wm.ADAPTERS,
                        log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Teardown-rebuild ADU units (in the headline) and vacant-lot new-house ADU units (diagnostic,
    excluded) per place and year; NaN where the source cannot show them."""
    import importlib

    vals: dict[tuple[str, int], tuple[float, float]] = {}
    for slug, f, col in (("madison", "madison_adu_permits_by_year.csv", "category"),
                         ("pleasant_prairie", "pleasant_prairie_adu_equivalent_by_year.csv", "series"),
                         ("sun_prairie", "sun_prairie_adu_equivalent_by_year.csv", "series")):
        path = ref_dir / f
        if not path.exists():
            continue
        d = pd.read_csv(path)
        for y in wm.YEARS:
            g = d[d["year"] == y].groupby(col)["units"].sum()
            td, va = f"{second_homes.HEADLINE}:{second_homes.TEARDOWN}", second_homes.VACANT_ROW
            vals[(slug, y)] = (float(g[td]) if td in g.index else np.nan, float(g[va]) if va in g.index else np.nan)
    checks = []
    for slug in adapters:
        if not (raw_root / f"wimc_{slug}").exists():
            continue
        m = importlib.import_module(f"missing_middleware.permits.wimc_{slug}")
        c = m.classify_records(m.load(raw_root / f"wimc_{slug}"))
        nh = wimc_new_house_adus(c).assign(slug=slug)
        bad = nh[(nh["nh_site"] == "teardown_rebuild") & nh["component"].isna()]
        if len(bad):
            raise RuntimeError(f"{slug}: teardown-lot ADU(s) not counted by the adapter (judge them under AQ-039): "
                               f"{list(bad['permit_id'])}")
        cnt = nh[(nh["nh_site"] == "vacant_lot") & nh["component"].notna()]
        if len(cnt):
            raise RuntimeError(f"{slug}: vacant-lot new-house ADU(s) counted by the adapter (AQ-039 excludes them): "
                               f"{list(cnt['permit_id'])}")
        checks.append(nh)
        for y in wm.YEARS:
            ny = nh[nh["year"] == y]
            vals[(slug, y)] = (float(ny.loc[ny["nh_site"] == "teardown_rebuild", "nh_adu_units"].sum()),
                               float(ny.loc[ny["nh_site"] == "vacant_lot", "nh_adu_units"].sum()))
    py = py.copy()
    py[AQ039_TD] = [vals.get((s, y), (np.nan, np.nan))[0] for s, y in zip(py["slug"], py["year"])]
    py[AQ039_VAC] = [vals.get((s, y), (np.nan, np.nan))[1] for s, y in zip(py["slug"], py["year"])]
    chk = pd.concat(checks, ignore_index=True) if checks else pd.DataFrame()
    log(f"AQ-039 check on the measured adapters: {len(chk)} ADU(s) permitted with a new house")
    return py, chk


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
    py, aq039 = aq039_by_place_year(py, ref_dir, raw_root, log=log)
    py.assign(units_unit="second-home units permitted in the calendar year (count)",
              aq039_unit=("ADU units (count, 1 per ADU) permitted with a new house: teardown lot = counted in "
                          "units; vacant lot = diagnostic, not in units; blank = not observable in the source"))[
        ["place", "slug", "year", "units", "upper_units", "months", "complete", "stage", "note", "units_unit",
         AQ039_TD, AQ039_VAC, "aq039_unit"]].to_csv(out_ref / "wi_rules_vs_activity_by_year.csv", index=False)
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
    aq039.to_csv(out_proc / "aq039_new_house_adus.csv", index=False)
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

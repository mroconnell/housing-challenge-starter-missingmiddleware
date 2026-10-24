"""California pre-2020 local ADU rules versus ADU activity (owner idea, 2026-10-24).

Inputs
- reference/ca_regression_ca_jurisdictions.csv: study jurisdictions with the wave-3 activity group
  (pre-period 2017-2019), pre_rate, 2023-2025 plateau permits and rate, ACS homes, value, income.
- reference/ca_holdout_jurisdictions.csv: the pre-registered holdout flag (used only to flag places).
- reference/ca_jurisdiction_crosswalk.csv: HCD names to census_geoid.
- reference/ca_ordinances_2019.csv: the team's AQ-026 hand coding of a stratified sample.
- data/raw/terner_tcrlus_2018/: Terner California Residential Land Use Survey (fetched here if missing).
- data/raw/wayback_ca_adu/: HCD "ADU ordinances received" list, Wayback capture 2019-08-31 (fetched if missing).
- data/raw/ca_adu_scorecard_2020/interim_report_200201_exa_text.md: CCI ADU Scorecard interim report text.
  urbandisplacement.org refuses scripted requests (HTTP 403); the text was read through the Exa fetch
  service on 2026-10-24 and is not re-fetched here.

Outputs (small, non-personal aggregates): reference/ca_rules_vs_activity_*.csv.
Run: uv run python scripts/build_ca_ordinances.py [--n-boot N] [--no-fetch]
The pre-registered study and holdout tests are not touched or recomputed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.request

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_ordinances as co
from missing_middleware.paths import REFERENCE, raw_dir

UA = "missing-middleware-ca-ordinances/0.1 (Wisconsin housing research; plain HTTP)"
TCRLUS_BASE = "https://ternercenter.berkeley.edu/wp-content/uploads/2023/04/"
TCRLUS_FILES = ("TCRLUS_readme.txt", "TCRLUS_codebook_2018-11-12.txt", "TCRLUS_data_2018-11-12.csv",
                "TCRLUS_labeled_2018-11-12.csv")
HCD_XLSX = ("https://web.archive.org/web/20190831103132id_/http://www.hcd.ca.gov/policy-research/docs/"
            "ordinances/jurisdiction-ordinances.xlsx")
HCD_XLSX_NAME = "hcd_jurisdiction_ordinances_20190831.xlsx"
SCORECARD = "interim_report_200201_exa_text.md"
SCORECARD_URL = "https://www.urbandisplacement.org/wp-content/uploads/2021/09/ADU-Scorecard-InterimReport-200201-1.pdf"


def fetch(url: str, path, log=print) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    path.write_bytes(data)
    log(f"fetched {url} ({len(data):,} bytes)")
    return {"url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "accessed": dt.date.today().isoformat()}


def ensure_sources(no_fetch: bool) -> dict:
    manifest = {}
    t = raw_dir("terner_tcrlus_2018")
    for f in TCRLUS_FILES:
        p = t / f
        if not p.exists() and not no_fetch:
            manifest[f] = fetch(TCRLUS_BASE + f, p)
        elif p.exists():
            manifest[f] = {"url": TCRLUS_BASE + f, "bytes": p.stat().st_size,
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    w = raw_dir("wayback_ca_adu")
    p = w / HCD_XLSX_NAME
    if not p.exists() and not no_fetch:
        manifest[HCD_XLSX_NAME] = fetch(HCD_XLSX, p)
    elif p.exists():
        manifest[HCD_XLSX_NAME] = {"url": HCD_XLSX, "bytes": p.stat().st_size,
                                   "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    s = raw_dir("ca_adu_scorecard_2020") / SCORECARD
    manifest[SCORECARD] = {"url": SCORECARD_URL, "via": "Exa web fetch (site returns 403 to scripts)",
                           "accessed": "2026-10-24", "bytes": s.stat().st_size,
                           "sha256": hashlib.sha256(s.read_bytes()).hexdigest()}
    (raw_dir("ca_ordinances_2019_handcoding") / "_sources_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def load_all():
    xw = pd.read_csv(REFERENCE / "ca_jurisdiction_crosswalk.csv", dtype=str)
    juris = pd.read_csv(REFERENCE / "ca_regression_ca_jurisdictions.csv", dtype={"census_geoid": str})
    hold = pd.read_csv(REFERENCE / "ca_holdout_jurisdictions.csv", dtype={"census_geoid": str})
    base = co.study_base(juris, hold)
    sc = co.attach_geoid(co.parse_scorecard_table((raw_dir("ca_adu_scorecard_2020") / SCORECARD).read_text()), xw)
    hcd, as_of = co.parse_hcd_received(co.read_xlsx_rows(raw_dir("wayback_ca_adu") / HCD_XLSX_NAME))
    hcd = co.attach_geoid(hcd, xw)
    tc = co.attach_geoid(co.tcrlus_codes(pd.read_csv(raw_dir("terner_tcrlus_2018") / "TCRLUS_data_2018-11-12.csv")), xw)
    hand = co.read_hand_coding(REFERENCE / "ca_ordinances_2019.csv")
    return base, sc, hcd, as_of, tc, hand


def predictors(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """(column, label, universe filter column) for the cross-tabs and correlations."""
    return [
        ("hcd_received", "HCD had received a post-2017 local ADU ordinance by 2019-05-01", "all"),
        ("cci_graded", "CCI graded an ordinance received by HCD by 2019-09-06", "all"),
        ("cci_grade_points", "CCI letter grade (A=12 ... F=1), graded places only", "cci_graded"),
        ("tcrlus_ordinance", "TCRLUS: local ADU ordinance adopted / in process / none (2017-18)", "in_tcrlus"),
        ("tcrlus_extra_parking", "TCRLUS: ADU off-street parking > 0 spaces", "in_tcrlus"),
        ("tcrlus_lot_minimum", "TCRLUS: ADU minimum lot size > 0", "in_tcrlus"),
        ("tcrlus_size_below_benchmark", "TCRLUS: ADU maximum size < 600 sq ft", "in_tcrlus"),
        ("tcrlus_fees", "TCRLUS: total ADU fees >= $10,000", "in_tcrlus"),
        ("tcrlus_n_flags", "TCRLUS: count of the four flags above (known True)", "in_tcrlus"),
        ("hand_ordinance_status", "Hand: ordinance status", "hand_coded"),
        ("hand_rights_class", "Hand: rights class", "hand_coded"),
        ("hand_n_tier1", "Hand: tier-1 flags (known True)", "hand_coded"),
        ("hand_n_tier2", "Hand: tier-2 flags (known True)", "hand_coded"),
        ("hand_n_flags", "Hand: all flags (known True)", "hand_coded"),
        ("hand_owner_occupancy", "Hand: owner occupancy", "hand_coded"),
        ("hand_extra_parking", "Hand: extra parking", "hand_coded"),
        ("hand_discretionary_review", "Hand: discretionary review", "hand_coded"),
        ("hand_lot_minimum", "Hand: lot minimum", "hand_coded"),
        ("hand_district_limited", "Hand: district limited", "hand_coded"),
        ("value_tercile", "ACS median home value tercile (non-holdout cut points)", "all"),
        ("income_tercile", "ACS median household income tercile (non-holdout cut points)", "all"),
    ]


def sub(df, uni):
    return df if uni == "all" else df[df[uni].fillna(False).astype(bool)]


def to_num(s: pd.Series) -> pd.Series:
    if not pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
        mapped = s.map({True: 1.0, False: 0.0, "adopted": 2.0, "in_process": 1.0, "no_local_ordinance": 0.0})
        if mapped.notna().any():
            return mapped.astype(float)
    return pd.to_numeric(s, errors="coerce")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    ensure_sources(a.no_fetch)
    base, sc, hcd, as_of, tc, hand = load_all()
    print(f"HCD list current as of: {as_of}")

    ref_vals = base.loc[~base["holdout"], "value"]
    ref_inc = base.loc[~base["holdout"], "income"]
    base["value_tercile"] = co.value_terciles(base["value"], ref_vals)
    base["income_tercile"] = co.value_terciles(base["income"], ref_inc)
    drawn = co.draw_hand_sample(base)
    assert set(drawn["census_geoid"]) == set(hand["census_geoid"]), "hand coding does not match the seeded draw"
    df = co.assemble(base, sc, hcd, tc, hand)
    df["in_hand_sample"] = df["census_geoid"].isin(drawn["census_geoid"])
    df["pre_exposure"] = df["homes"] * co.PRE_YEARS / 1000
    df["plateau_exposure"] = df["homes"] * df["n_years"] / 1000
    for f in ("owner_occupancy", "extra_parking", "discretionary_review", "lot_minimum", "district_limited"):
        df[f"hand_{f}_num"] = to_num(df[f"hand_{f}"])

    # ---- jurisdictions table
    jcols = ["census_geoid", "name", "juris_type", "holdout", "group", "pre_rate", "pre_permits", "rate", "adu",
             "n_years", "homes", "value", "income", "value_tercile", "income_tercile", "hcd_received",
             "hcd_ordinance_date", "cci_graded", "cci_grade", "cci_year_adopted", "in_tcrlus", "tcrlus_ordinance",
             "tcrlus_minlot_sqft", "tcrlus_maxsize_sqft", "tcrlus_parking_spaces", "tcrlus_fees_usd",
             "tcrlus_lot_minimum", "tcrlus_size_below_benchmark", "tcrlus_extra_parking", "tcrlus_fees",
             "tcrlus_n_flags", "in_hand_sample", "hand_coded", "hand_ordinance_status", "hand_rights_class",
             *[f"hand_{f}" for f in co.FLAGS], "hand_approval_pathway", "hand_n_tier1", "hand_n_tier2",
             "hand_n_flags", "hand_n_unknown", "hand_confidence", "hand_source_type"]
    jt = df[jcols].rename(columns={"rate": "plateau_rate_2023_2025", "adu": "plateau_permits_2023_2025",
                                   "pre_rate": "pre_rate_2017_2019", "pre_permits": "pre_permits_2017_2019",
                                   "group": "activity_group_2017_2019", "n_years": "plateau_years_observed"})
    jt.to_csv(REFERENCE / "ca_rules_vs_activity_jurisdictions.csv", index=False)

    # ---- source inventory
    n = len(df)
    inv = pd.DataFrame([
        {"source": "Terner California Residential Land Use Survey (Mawhorter and Reid 2018)",
         "coding_date": "planner self-report, 2017-08 to 2018-10", "coverage_total": len(tc),
         "coverage_study_places": int(df["in_tcrlus"].sum()), "study_places": n,
         "variables": "ADU ordinance status (adopted / in process / none); ADU minimum lot size; maximum unit size; "
                      "off-street parking spaces; total fees for a typical ADU; ADU application frequency",
         "aq026_mapping": "ordinance status; lot_minimum; size_below_benchmark; extra_parking; fees (cost proxy). "
                          "No owner occupancy, related occupant, discretionary review, form, siting, district.",
         "url": "https://ternercenter.berkeley.edu/california-land-use-survey-data/"},
        {"source": "CCI ADU Scorecard interim report (Chapple et al., 2020-02-01), Appendix C",
         "coding_date": "ordinances received by HCD by 2019-09-06 (pre-2020 rules)",
         "coverage_total": int(sc["cci_graded"].sum()), "coverage_study_places": int(df["cci_graded"].sum()),
         "study_places": n,
         "variables": "Composite letter grade A-F from 16 criteria (lot size, lot coverage/FAR, ADU parking, "
                      "replacement parking, setbacks x2, max size x2, height, zones, review timeframe, added review "
                      "layers, fees, JADU, owner occupancy, clarity); 2018 ADU permits; ordinance year and link",
         "aq026_mapping": "Composite only; per-criterion scores not published (available from CCI by email only)",
         "url": SCORECARD_URL},
        {"source": "HCD list of ADU ordinances received (jurisdiction-ordinances.xlsx)",
         "coding_date": f"current as of {as_of}; Wayback capture 2019-08-31", "coverage_total": len(hcd),
         "coverage_study_places": int(df["hcd_received"].sum()), "study_places": n,
         "variables": "Received / not received; ordinance file link and date",
         "aq026_mapping": "Proxy for first-pass status (filed a post-2017 local ordinance). Not received does not "
                          "mean no rules: state default standards applied.",
         "url": HCD_XLSX},
        {"source": "Team hand coding, AQ-026 scheme (reference/ca_ordinances_2019.csv)",
         "coding_date": "2026-10-24, rules in force 2017-2019",
         "coverage_total": int(hand["ordinance_status"].ne("could_not_access").sum()),
         "coverage_study_places": int(df["hand_coded"].fillna(False).sum()), "study_places": n,
         "variables": "Ordinance status, rights class, ten AQ-026 flags, approval pathway, max size, parking, "
                      "minimum lot, source URL and date, quoted evidence",
         "aq026_mapping": "Full scheme",
         "url": "reference/ca_ordinances_2019.csv"},
    ])
    inv.to_csv(REFERENCE / "ca_rules_vs_activity_sources.csv", index=False)

    # ---- cross-tabs (non-holdout and all)
    tabs = []
    for col, label, uni in predictors(df):
        for sample, d in (("non_holdout", df[~df["holdout"]]), ("all_incl_holdout", df)):
            dd = sub(d, uni)
            if col == "cci_grade_points":
                dd = dd.assign(cci_grade_band=pd.cut(dd["cci_grade_points"], [0, 5, 7, 9, 12],
                                                     labels=["C- or lower", "C/C+", "B-/B", "B+ or A"]).astype(str))
                t = co.group_crosstab(dd, "cci_grade_band")
            elif col in ("hand_n_tier1", "hand_n_tier2", "hand_n_flags", "tcrlus_n_flags"):
                t = co.group_crosstab(dd.assign(_c=dd[col].clip(upper=4 if "tier" not in col else 3)), "_c")
            else:
                t = co.group_crosstab(dd, col)
            t.insert(0, "label", label)
            t.insert(0, "sample", sample)
            t["predictor"] = col
            tabs.append(t)
    ct = pd.concat(tabs, ignore_index=True)
    ct.to_csv(REFERENCE / "ca_rules_vs_activity_crosstabs.csv", index=False)

    # ---- within home-value terciles (holds the main competing explanation roughly fixed)
    wv = []
    d0 = df[~df["holdout"]].copy()
    d0["hand_tier1_2plus"] = d0["hand_n_tier1"].ge(2).where(d0["hand_coded"].fillna(False).astype(bool))
    d0["tcrlus_flags_2plus"] = d0["tcrlus_n_flags"].ge(2).where(d0["in_tcrlus"])
    for col, uni in (("hcd_received", "all"), ("cci_graded", "all"), ("tcrlus_flags_2plus", "in_tcrlus"),
                     ("hand_tier1_2plus", "hand_coded"), ("hand_owner_occupancy", "hand_coded"),
                     ("hand_discretionary_review", "hand_coded")):
        for vt in ("low", "mid", "high"):
            dd = sub(d0[d0["value_tercile"] == vt], uni)
            t = co.group_crosstab(dd, col)
            t.insert(0, "value_tercile", vt)
            wv.append(t[t["level"] != "missing"])
    pd.concat(wv, ignore_index=True).to_csv(REFERENCE / "ca_rules_vs_activity_within_value.csv", index=False)

    # ---- rank correlations
    rows = []
    outcomes = [("pre_rate", "2017-2019 rate, ADU permits per 1,000 one-unit detached homes per year"),
                ("rate", "2023-2025 plateau rate, ADU permits per 1,000 one-unit detached homes per year"),
                ("active", "Active group 2017-2019 (1) vs not (0)"),
                ("restrictive", "Restrictive group 2017-2019 (zero permits all 3 years) (1) vs not (0)")]
    numeric_preds = [("hcd_received", "all"), ("cci_graded", "all"), ("cci_grade_points", "cci_graded"),
                     ("tcrlus_ordinance", "in_tcrlus"), ("tcrlus_n_flags", "in_tcrlus"),
                     ("tcrlus_extra_parking", "in_tcrlus"), ("tcrlus_lot_minimum", "in_tcrlus"),
                     ("tcrlus_fees", "in_tcrlus"), ("hand_n_tier1", "hand_coded"), ("hand_n_tier2", "hand_coded"),
                     ("hand_n_flags", "hand_coded"), ("hand_owner_occupancy", "hand_coded"),
                     ("hand_extra_parking", "hand_coded"), ("hand_discretionary_review", "hand_coded"),
                     ("hand_lot_minimum", "hand_coded"), ("hand_district_limited", "hand_coded"),
                     ("log_value", "all"), ("log_income", "all")]
    for sample, d in (("non_holdout", df[~df["holdout"]]), ("all_incl_holdout", df)):
        for col, uni in numeric_preds:
            dd = sub(d, uni)
            x = to_num(dd[col])
            for oc, olab in outcomes:
                y = dd[oc].astype(float)
                r, k = co.spearman(x, y)
                lo, hi = co.spearman_ci(x, y, n_boot=a.n_boot)
                # same, within the hand / survey universe, for value: shows the competing explanation on equal footing
                rv, _ = co.spearman(dd["log_value"], y)
                rows.append({"sample": sample, "predictor": col, "universe": uni, "outcome": oc,
                             "outcome_label": olab, "n_places": k, "spearman": r, "lo95": lo, "hi95": hi,
                             "spearman_log_value_same_places": rv})
    cr = pd.DataFrame(rows)
    cr.to_csv(REFERENCE / "ca_rules_vs_activity_correlations.csv", index=False)

    # ---- Poisson rate ratios with value + income controls
    mrows = []
    specs = [("hcd_received", "all"), ("cci_graded", "all"), ("tcrlus_n_flags", "in_tcrlus"),
             ("tcrlus_extra_parking_num", "in_tcrlus"), ("hand_n_tier1", "hand_coded"),
             ("hand_n_flags", "hand_coded"), ("hand_owner_occupancy_num", "hand_coded"),
             ("hand_discretionary_review_num", "hand_coded")]
    df["tcrlus_extra_parking_num"] = to_num(df["tcrlus_extra_parking"])
    for sample, d in (("non_holdout", df[~df["holdout"]]), ("non_holdout_excl_LA", df[~df["holdout"] & (df["census_geoid"] != co.LA_GEOID)])):
        for col, uni in specs:
            dd = sub(d, uni).copy()
            for oc, ex in (("pre_permits", "pre_exposure"), ("adu", "plateau_exposure")):
                for controls in ((), ("log_value", "log_income")):
                    r = co.poisson_rate_ratio(dd, oc, ex, col, controls, n_boot=a.n_boot)
                    r["sample"] = sample
                    mrows.append(r)
    md = pd.DataFrame(mrows)
    md["outcome"] = md["outcome"].map({"pre_permits": "2017-2019 ADU permits", "adu": "2023-2025 ADU permits"})
    md.to_csv(REFERENCE / "ca_rules_vs_activity_models.csv", index=False)

    # ---- classification: can rules assign activity groups? (logistic; in-sample and 5-fold CV AUC)
    crow = []
    for target in ("active", "restrictive"):
        for uni, rule_cols in (("all", ["hcd_received"]), ("all", ["cci_graded"]), ("all", ["hcd_received", "cci_graded"]),
                               ("in_tcrlus", ["tcrlus_ord_num", "tcrlus_n_flags"]),
                               ("hand_coded", ["hand_n_tier1", "hand_n_tier2"]),
                               ("hand_coded", ["hand_owner_occupancy_num", "hand_extra_parking_num",
                                               "hand_discretionary_review_num"])):
            d = df[~df["holdout"]].copy()
            d["tcrlus_ord_num"] = to_num(d["tcrlus_ordinance"])
            d = sub(d, uni)
            full = d[rule_cols + ["log_value", "log_income", target]].copy()
            for c in rule_cols:
                full[c] = to_num(full[c])
            full = full.dropna()          # all three models use the same places
            for label, cols in (("value_income", ["log_value", "log_income"]), ("rules", rule_cols),
                                ("rules_value_income", rule_cols + ["log_value", "log_income"])):
                dd = full
                X = np.column_stack([np.ones(len(dd))] + [dd[c].to_numpy(float) for c in cols])
                Xs = X.copy()
                Xs[:, 1:] = (Xs[:, 1:] - Xs[:, 1:].mean(0)) / np.where(Xs[:, 1:].std(0) > 0, Xs[:, 1:].std(0), 1)
                y = dd[target].to_numpy(float)
                ok = 0 < y.sum() < len(y)
                auc_in = co.insample_auc(Xs, y) if ok else np.nan
                auc_cv = co.cv_auc(Xs, y) if ok else np.nan
                crow.append({"target": target, "universe": uni, "rule_set": "+".join(rule_cols), "model": label,
                             "n_places": len(dd), "n_target": int(y.sum()), "auc_in_sample": auc_in,
                             "auc_cv_5fold_x20": auc_cv})
    pd.DataFrame(crow).to_csv(REFERENCE / "ca_rules_vs_activity_classification.csv", index=False)
    print(f"wrote reference/ca_rules_vs_activity_*.csv; {len(df)} jurisdictions, "
          f"{int(df['hand_coded'].fillna(False).sum())} hand-coded")


if __name__ == "__main__":
    main()

"""Review outputs: reference counts by year, audit sample, source-vs-clean examples."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ADU_TEXT_CATS = ("adu_detached", "adu_attached", "adu_conversion", "adu_legalization")

# City of Madison, Housing Forward / ADU page table of ADU permits by year
# (2025 = January-August). Transcribed in Gate 1 (docs/gate1/DATA_INVENTORY.md context).
CITY_ADU_TABLE = {2013: 1, 2014: 5, 2015: 2, 2016: 2, 2017: 1, 2018: 1, 2019: 2, 2020: 0,
                  2021: 2, 2022: 6, 2023: 11, 2024: 10, 2025: 6}


def reference_by_year(full: pd.DataFrame) -> pd.DataFrame:
    """year, category, count (permits), units, method. Aggregate and non-personal."""
    c = full[full["counted"]]
    rows = []
    years = range(int(full["year"].min()), int(full["year"].max()) + 1)
    for y in years:
        cy = c[c["year"] == y]
        for cat in (*ADU_TEXT_CATS, "adu_equivalent"):
            s = cy[cy["unit_category"] == cat]
            rows.append({"year": y, "category": cat, "count": len(s), "units": int(s["units_added"].sum()),
                         "method": "parcel_rule" if cat == "adu_equivalent" else "text_rule"})
        # ADU-equivalent ("second dwelling / conversion") sub-series; units_from_text marks
        # Dwell-0 single-family -> two-unit conversions whose 1 unit is read from the text
        if "adu_eq_series" in full.columns:
            eq = cy[cy["unit_category"] == "adu_equivalent"]
            uft = eq["units_from_text"].astype(bool) if "units_from_text" in eq.columns else False
            for series, sel, method in (
                ("adu_equivalent:second_dwelling", eq["adu_eq_series"].eq("second_dwelling"), "parcel_rule"),
                ("adu_equivalent:duplex_conversion", eq["adu_eq_series"].eq("duplex_conversion") & ~uft,
                 "parcel_rule"),
                ("adu_equivalent:duplex_conversion_dwell0", eq["adu_eq_series"].eq("duplex_conversion") & uft,
                 "parcel_rule+units_from_text"),
            ):
                s = eq[sel]
                rows.append({"year": y, "category": series, "count": len(s),
                             "units": int(s["units_added"].sum()), "method": method})
        s = full[(full["year"] == y) & full["in_scope"] & full["unit_category"].isin(ADU_TEXT_CATS)
                 & ~full["counted"]]
        rows.append({"year": y, "category": "adu_text_zero_units_or_duplicate", "count": len(s), "units": 0,
                     "method": "text_rule"})
        s = full[(full["year"] == y) & full["text_note"].eq("near_miss:multi_unit_adu_bundle")]
        rows.append({"year": y, "category": "adu_text_multi_unit_bundle_review", "count": len(s),
                     "units": int(s["units_added"].sum()), "method": "text_rule_excluded"})
        if y in CITY_ADU_TABLE:
            rows.append({"year": y, "category": "adu_all_city_published", "count": CITY_ADU_TABLE[y],
                         "units": None, "method": "city_published" + ("_jan_aug" if y == 2025 else "")})
    out = pd.DataFrame(rows)
    out["units"] = out["units"].astype("Int64")
    return out


def _pick(df: pd.DataFrame, n: int, seed: int = 20261023) -> pd.DataFrame:
    return df.sample(min(n, len(df)), random_state=seed) if len(df) > n else df


AUDIT_COLS = ["audit_group", "permit_id", "year", "issue_date", "permit_type", "use_class", "address_raw",
              "units_added", "units_suspect", "description", "text_note", "unit_category", "classification_method",
              "match_method", "match_quality", "match_rule", "parcel_id", "parcel_parcel_address",
              "parcel_property_use", "parcel_dwelling_units", "parcel_year_built", "parcel_more_than_one_building", "host_units_now",
              "earlier_units", "parcel_rule_reason", "tract_geoid", "counted"]


def audit_sample(full: pd.DataFrame, judgments: Path | None = None) -> pd.DataFrame:
    """25 classified ADU/ADU-equivalent + 10 unmatched in-scope + 10 near-miss text hits.

    ADU picks are stratified: up to 13 text-rule ADUs and 12 ADU-equivalents.
    """
    adu_text = full[full["in_scope"] & full["unit_category"].isin(ADU_TEXT_CATS)]
    adu_eq = full[full["in_scope"] & (full["unit_category"] == "adu_equivalent")]
    n_eq = min(12, len(adu_eq))
    a = pd.concat([_pick(adu_text, 25 - n_eq).assign(audit_group="adu_text"),
                   _pick(adu_eq, n_eq).assign(audit_group="adu_equivalent")])
    unm = full[full["in_scope"] & (full["match_method"] == "unmatched")]
    # near misses: ADU-pattern hits that were excluded, plus parcel-rule failures on 1-unit permits
    # at already-developed parcels (the closest calls of the parcel rule)
    nm_text = full[full["text_note"].fillna("").str.startswith("near_miss")
                   | full["text_note"].eq("related_term")]
    nm_rule = full[full["in_scope"] & (full["unit_category"] == "other_residential")
                   & full["parcel_rule_reason"].isin(["raze_nearby", "main_building_from_earlier_permit",
                                                      "host_not_one_unit_residential"])
                   & (full["units_added"] == 1)]
    nm = pd.concat([_pick(nm_text, 10).assign(audit_group="near_miss_text"),
                    _pick(nm_rule, max(0, 10 - min(10, len(nm_text)))).assign(audit_group="near_miss_parcel_rule")])
    out = pd.concat([a, _pick(unm, 10).assign(audit_group="unmatched"), nm])
    out = out[[c for c in AUDIT_COLS if c in out.columns]].copy()
    out["issue_date"] = out["issue_date"].dt.date
    if judgments is not None and judgments.exists():
        j = pd.read_csv(judgments, dtype=str)
        out = out.merge(j, on="permit_id", how="left")
    return out.sort_values(["audit_group", "year", "permit_id"]).reset_index(drop=True)


def source_vs_clean(raw_dir: Path, full: pd.DataFrame, obs: pd.DataFrame, permit_ids=None,
                    extra_ids=()) -> pd.DataFrame:
    """Raw report rows (owner fields redacted) beside their cleaned record and contract row."""
    from .madison import OWNER_COLUMNS, read_report_csv
    from .pipeline import record_key

    if permit_ids is None:
        picks = []
        for cond in (
            full["unit_category"].eq("adu_detached") & full["counted"],
            full["unit_category"].eq("adu_conversion"),
            full["unit_category"].eq("adu_equivalent"),
            full["unit_category"].eq("other_residential") & full["match_method"].eq("address_normalized"),
            full["n_source_rows"].gt(1) & full["in_scope"],
            full["in_scope"] & full["match_method"].eq("unmatched"),
        ):
            s = full[cond].sort_values("issue_date")
            if len(s):
                picks.append(s.iloc[len(s) // 2]["permit_id"])
        permit_ids = list(dict.fromkeys(list(extra_ids) + picks))
    rows = []
    for path in sorted(raw_dir.glob("construction_summary_*.csv")):
        r = read_report_csv(path)
        r = r[r["B1_ALT_ID"].isin(permit_ids)].copy()
        for c in (*OWNER_COLUMNS, "ContractorBusiness", "ContractorAddress_Line"):
            r[c] = "[REDACTED]"
        r["raw_file"] = path.name
        rows.append(r)
    raw = pd.concat(rows).add_prefix("raw_")
    clean_cols = ["permit_id", "issue_date", "n_source_rows", "units_added", "address_raw", "addr_house_nbr",
                  "addr_street_key", "addr_unit", "match_method", "match_quality", "match_rule", "parcel_id",
                  "parcel_property_use", "parcel_dwelling_units", "parcel_year_built", "unit_category",
                  "classification_method", "text_note", "parcel_rule_reason", "tract_geoid", "bg_geoid",
                  "counted"]
    clean = full[full["permit_id"].isin(permit_ids)][clean_cols].add_prefix("clean_")
    out = raw.merge(clean, left_on="raw_B1_ALT_ID", right_on="clean_permit_id", how="left")
    out["record_key"] = [record_key("madison_permits", p) for p in out["raw_B1_ALT_ID"]]
    return out


def reconcile_city(full: pd.DataFrame) -> pd.DataFrame:
    """Text-rule ADU records vs the City's published table ("ADUs Permitted", i.e.
    permits issued, per the City's own label).

    - text_counted_by_issue_year: counted text ADUs (>=1 unit, not duplicate) by issuance
      year (this pipeline's outcome definition, and the City's stated basis).
    - text_all_by_issue_year: every ADU-text record (incl. Dwell-0 conversions,
      finish/repair records and multi-unit ADU bundles) by issuance year.
    - text_all_by_permit_number_year: the same records by the year embedded in the permit
      number (application year). That the City counts this way is OUR HYPOTHESIS, chosen
      because it reproduces 2014-2022; the City does not document its method.
    - text_counted_issued_jan_aug: counted text ADUs issued January-August (for the
      City's partial 2025 figure).
    """
    t = full[full["text_category"].notna()
             | full["text_note"].fillna("").str.contains("repair_or_finish|multi_unit_adu_bundle")].copy()
    t["number_year"] = t["permit_id"].str.extract(r"-(\d{4})-")[0].astype(int)
    counted = t[t["counted"] & t["text_category"].notna()].groupby("year").size()
    by_num = t.groupby("number_year").size()
    all_issue = t.groupby("year").size()
    ct = t[t["counted"] & t["text_category"].notna()]
    jan_aug = ct[ct["issue_date"].dt.month <= 8].groupby("year").size()
    eq = full[full["counted"] & (full["unit_category"] == "adu_equivalent")].groupby("year").size()
    years = sorted(set(CITY_ADU_TABLE) | set(counted.index) | set(by_num.index))
    rows = []
    for y in years:
        rows.append({
            "year": y,
            "city_published": CITY_ADU_TABLE.get(y),
            "text_counted_by_issue_year": int(counted.get(y, 0)),
            "text_all_by_issue_year": int(all_issue.get(y, 0)),
            "text_all_by_permit_number_year": int(by_num.get(y, 0)),
            "text_counted_issued_jan_aug": int(jan_aug.get(y, 0)),
            "adu_equivalent_by_issue_year": int(eq.get(y, 0)),
        })
    return pd.DataFrame(rows)

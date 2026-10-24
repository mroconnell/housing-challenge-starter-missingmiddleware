"""Validate the hand-coded Wisconsin ADU rule tables.

Checks reference/wi_adu_rules.csv against the `policy_rules` contract and
reference/wi_rights_exposure.csv against the `rights_exposure` contract
(missing_middleware.contracts), plus rules specific to the coding:

- provisions use the DATA_CONTRACTS.md vocabulary plus `approval_pathway` and `ordinance_status` (AQ-025,
  AQ-026); coded provisions use their coded values (ORDINANCE_STATUS from contracts)
- dates are ISO (YYYY-MM-DD) or blank, and effective_from <= effective_to
- every rule_ids entry exists in the rules table, and every coded jurisdiction has rules
- every coded jurisdiction has one ordinance_status row and one current approval_pathway row
- restrictions/reform_restrictions use RESTRICTION_FLAGS; restrictions is non-empty exactly when
  current_class is restricted, reform_restrictions exactly when reform_class is restricted
- adu_full: reform_class is scenario_benchmark (no_zoning stays no_zoning); adu_form_only: reform_class is
  restricted only with occupancy flags (owner_occupancy, related_occupant) taken from restrictions
- reform_class equals current_class where the reform adds nothing (scenario_benchmark, no_zoning)
- class_basis not_found goes with current_class undetermined, and coded_verified needs a verified current
  detached/attached rule
- rules_as_of is on or before the 2026-10-31 freeze; rights_added_text is never blank

Usage: uv run python scripts/check_reference_rules.py [rules.csv exposure.csv]
Exit code 0 when clean, 1 when problems are found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from missing_middleware import contracts as c  # noqa: E402

PROVISIONS = {
    "detached_allowed", "attached_allowed", "owner_occupancy", "occupant_restriction",
    "min_lot_size", "max_size_sqft", "parking_required", "approval_type", "other",
    "approval_pathway", "ordinance_status",
}
PATHWAYS = {"ministerial", "discretionary", "unknown"}
OCC_FLAGS = {"owner_occupancy", "related_occupant"}
FORM_VALUES = {"by_right", "conditional", "prohibited", "unknown"}
CODED_VALUES = {
    "detached_allowed": FORM_VALUES,
    "attached_allowed": FORM_VALUES,
    "owner_occupancy": {"none", "at_permit", "ongoing", "unknown"},
    "occupant_restriction": {"none", "related_only", "employee_only", "other", "unknown"},
    "approval_pathway": PATHWAYS,
    "ordinance_status": c.ORDINANCE_STATUS,
}
SCENARIOS = {"adu_full", "adu_form_only"}
FREEZE = "2026-10-31"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MUNI_ID = re.compile(r"^55\d{8}$")


def _blank(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


def check(rules: pd.DataFrame, exposure: pd.DataFrame) -> list[str]:
    problems = c.validate(rules, c.POLICY_RULES) + c.validate(exposure, c.RIGHTS_EXPOSURE)

    for i, r in rules.iterrows():
        tag = f"rules row {i + 2} ({r.get('rule_id')})"
        if r.get("provision") not in PROVISIONS:
            problems.append(f"{tag}: provision {r.get('provision')!r} not in contract vocabulary")
        allowed = CODED_VALUES.get(r.get("provision"))
        if allowed and r.get("value") not in allowed:
            problems.append(f"{tag}: value {r.get('value')!r} not in {sorted(allowed)}")
        for col in ("effective_from", "effective_to", "retrieved"):
            v = r.get(col)
            if not _blank(v) and not DATE.match(str(v)):
                problems.append(f"{tag}: {col} {v!r} is not YYYY-MM-DD")
        f, t = r.get("effective_from"), r.get("effective_to")
        if not _blank(f) and not _blank(t) and str(f) > str(t):
            problems.append(f"{tag}: effective_from after effective_to")
        if _blank(r.get("source_url")) or not str(r.get("source_url")).startswith("http"):
            problems.append(f"{tag}: source_url missing or not a URL")
        if not MUNI_ID.match(str(r.get("jurisdiction_id"))):
            problems.append(f"{tag}: jurisdiction_id is not a 10-digit Wisconsin county subdivision GEOID")

    rule_ids = set(rules.get("rule_id", pd.Series(dtype=str)))
    need = {"verification", "rule_id", "provision", "effective_to"}
    verified_ids = (set(rules.loc[(rules["verification"] == "verified")
                                  & rules["provision"].isin(["detached_allowed", "attached_allowed"])
                                  & (rules["effective_to"] == ""), "rule_id"])
                    if need <= set(rules.columns) else set())
    if {"jurisdiction_id", "provision"} <= set(rules.columns):
        for jid in sorted(set(rules["jurisdiction_id"])):
            sub = rules[rules["jurisdiction_id"] == jid]
            n_os = int((sub["provision"] == "ordinance_status").sum())
            if n_os != 1:
                problems.append(f"rules {jid}: {n_os} ordinance_status rows (need exactly 1)")
            cur = sub[(sub["provision"] == "approval_pathway") & (sub.get("effective_to", "") == "")]
            if len(cur) != 1:
                problems.append(f"rules {jid}: {len(cur)} current approval_pathway rows (need exactly 1)")
    for i, r in exposure.iterrows():
        tag = f"exposure row {i + 2} ({r.get('jurisdiction_id')}, {r.get('scenario_id')})"
        if r.get("scenario_id") not in SCENARIOS:
            problems.append(f"{tag}: scenario_id not in {sorted(SCENARIOS)}")
        if not MUNI_ID.match(str(r.get("jurisdiction_id"))):
            problems.append(f"{tag}: jurisdiction_id is not a 10-digit Wisconsin county subdivision GEOID")
        cur, ref, basis = r.get("current_class"), r.get("reform_class"), r.get("class_basis")
        rest = [] if _blank(r.get("restrictions")) else str(r.get("restrictions")).split(";")
        rest_after = [] if _blank(r.get("reform_restrictions")) else str(r.get("reform_restrictions")).split(";")
        bad = (set(rest) | set(rest_after)) - c.RESTRICTION_FLAGS
        if bad:
            problems.append(f"{tag}: restriction flags not in RESTRICTION_FLAGS: {sorted(bad)}")
        if (cur == "restricted") != bool(rest):
            problems.append(f"{tag}: restrictions must be non-empty exactly when current_class is restricted")
        if (ref == "restricted") != bool(rest_after):
            problems.append(f"{tag}: reform_restrictions must be non-empty exactly when reform_class is restricted")
        if cur in ("scenario_benchmark", "no_zoning") and ref != cur:
            problems.append(f"{tag}: reform_class must equal current_class when current is {cur}")
        scen = r.get("scenario_id")
        if scen == "adu_full" and cur not in ("scenario_benchmark", "no_zoning") and ref != "scenario_benchmark":
            problems.append(f"{tag}: adu_full reform of a {cur} place must be scenario_benchmark")
        if scen == "adu_form_only" and ref == "restricted":
            if not set(rest_after) <= OCC_FLAGS or not set(rest_after) <= set(rest):
                problems.append(f"{tag}: adu_form_only may keep only the place's own occupancy flags")
        if scen == "adu_form_only" and cur == "restricted" and ref == "scenario_benchmark" and set(rest) & OCC_FLAGS:
            problems.append(f"{tag}: adu_form_only must keep occupancy flags {sorted(set(rest) & OCC_FLAGS)}")
        if "approval_pathway" in exposure.columns and r.get("approval_pathway") not in PATHWAYS:
            problems.append(f"{tag}: approval_pathway {r.get('approval_pathway')!r} not in {sorted(PATHWAYS)}")
        if basis == "not_found" and cur != "undetermined":
            problems.append(f"{tag}: class_basis not_found must go with current_class undetermined")
        as_of = r.get("rules_as_of")
        if _blank(as_of) or not DATE.match(str(as_of)) or str(as_of) > FREEZE:
            problems.append(f"{tag}: rules_as_of {as_of!r} missing, malformed, or after {FREEZE}")
        if _blank(r.get("rights_added_text")):
            problems.append(f"{tag}: rights_added_text is blank")
        ids = [] if _blank(r.get("rule_ids")) else str(r.get("rule_ids")).split(";")
        if basis in ("coded_verified", "coded_source_lead") and not ids:
            problems.append(f"{tag}: coded row has no rule_ids")
        missing = [x for x in ids if x not in rule_ids]
        if missing:
            problems.append(f"{tag}: rule_ids not in rules table: {missing[:3]}")
        if basis == "coded_verified" and ids and not any(x in verified_ids for x in ids):
            problems.append(f"{tag}: coded_verified but none of its current detached/attached rules is verified")

    if {"jurisdiction_id", "scenario_id"} <= set(exposure.columns):
        counts = exposure.groupby("jurisdiction_id")["scenario_id"].nunique()
        for jid in counts[counts < len(SCENARIOS)].index:
            problems.append(f"exposure: {jid} lacks a row for every scenario {sorted(SCENARIOS)}")
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    rules_path = Path(argv[0]) if argv else ROOT / "reference" / "wi_adu_rules.csv"
    exp_path = Path(argv[1]) if len(argv) > 1 else ROOT / "reference" / "wi_rights_exposure.csv"
    rules = pd.read_csv(rules_path, dtype=str, keep_default_na=False)
    exposure = pd.read_csv(exp_path, dtype=str, keep_default_na=False)
    problems = check(rules, exposure)
    full = exposure[exposure["scenario_id"] == "adu_full"] if "scenario_id" in exposure else exposure
    print(f"{rules_path.name}: {len(rules)} rules; {exp_path.name}: {len(exposure)} rows, "
          f"{full['jurisdiction_id'].nunique() if 'jurisdiction_id' in full else 0} jurisdictions")
    if "current_class" in full:
        print("current_class (adu_full rows): " + ", ".join(f"{k}={v}" for k, v in full["current_class"].value_counts().items()))
    for p in problems:
        print("PROBLEM:", p)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Shared table definitions from docs/gate1/DATA_CONTRACTS.md.

Each contract lists its required columns and the allowed values of its
enum columns. `validate(df, contract)` returns a list of problems rather
than raising, so build scripts can report every issue at once.

Change these definitions only through the conductor: other stages depend
on them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

VALUE_STATUS = {"observed", "calculated", "assumed"}
CLAIM_STATUS = {"verified", "source_lead", "unknown"}
MISSING_REASON = {"not_reported", "not_collected", "not_matched", "not_yet_audited"}
# First-pass classifier (AQ-026): does the code have an ADU ordinance at all?
ORDINANCE_STATUS = {"mentioned_allowed", "prohibited", "unmentioned", "could_not_access"}

# Second-pass rights classes (AQ-026). Restrictions are recorded as flags, not subclasses.
RIGHTS_CLASS = {
    "scenario_benchmark",   # benchmark rights already granted by right
    "restricted",           # some ADU form allowed, with one or more binding restrictions (see RESTRICTION_FLAGS)
    "prohibited_explicit",  # code says ADUs (or living space in accessory buildings) are not allowed
    "prohibited_implicit",  # code allows only listed uses/forms and ADUs are not listed
    "no_zoning",            # no municipal or county zoning applies
    "undetermined",         # not yet coded, or ordinance not found; MVP models it as no ADU rights (AQ-023)
}
# A flag applies only if the rule prevents a benchmark ADU (detached or attached, >= 600 sq ft,
# by right, no extra parking, no occupancy rule) on at least some single-family lots (AQ-026).
# Tier 1 follows the Mercatus 2025 taxonomy's core barriers ("poison pills" plus attached+detached).
POISON_PILL_FLAGS = {
    "owner_occupancy",        # owner must live on site (ongoing or at application)
    "related_occupant",       # occupants must be family, caregivers, or employees
    "extra_parking",          # more parking for a lot with an ADU than for the house alone, incl. replacement parking
    "discretionary_review",   # conditional or special use, hearing, plan commission
    "form_limited",           # attached-only, detached-only, or interior conversions only
}
# Tier 2: design, siting, and process limits that matter once tier 1 is cleared.
SECONDARY_FLAGS = {
    "size_below_benchmark",   # absolute cap under 600 sq ft, or a percent-of-house/FAR/coverage cap that can fall under 600
    "siting_limits",          # setbacks, height, or separation that prevent a 600 sq ft detached unit on typical lots
    "lot_minimum",            # minimum lot size or width above typical single-family lots
    "district_limited",       # not allowed in some single-family districts
    "fees",                   # ADU-specific impact or connection fees
    "other",
}
RESTRICTION_FLAGS = POISON_PILL_FLAGS | SECONDARY_FLAGS
CLASS_BASIS = {"coded_verified", "coded_source_lead", "assumed_default", "imputed_from_sample", "not_found"}
AREA_LEVEL = {"state", "county", "municipality", "tract", "block_group", "grid_cell"}
CONTEXT_GROUP = {"urban", "suburban", "small_community", "rural"}
PERMIT_STAGE = {"application", "approval", "issued", "finaled", "expired", "withdrawn"}
UNIT_CATEGORY = {
    "adu_detached",
    "adu_attached",
    "adu_conversion",
    "adu_legalization",
    "adu_equivalent",  # new dwelling on a parcel that already has one (AQ-021)
    "other_residential",
}
CLASSIFICATION_METHOD = {"structured_field", "text_rule", "parcel_rule", "manual_review"}
MATCH_METHOD = {"parcel_id", "address_exact", "address_normalized", "geocode", "unmatched"}
MATCH_QUALITY = {"confirmed", "probable", "ambiguous", "none"}
PATH = {"lower", "central", "upper"}


@dataclass(frozen=True)
class Contract:
    name: str
    required: tuple[str, ...]
    enums: dict[str, set[str]] = field(default_factory=dict)
    key: tuple[str, ...] = ()


AREAS = Contract(
    "areas",
    ("area_id", "level", "name", "boundary_source_id", "boundary_vintage"),
    {"level": AREA_LEVEL},
    key=("area_id",),
)

STATE_CONDITIONS = Contract(
    "state_conditions",
    ("area_id", "year", "indicator", "value", "moe", "period_type", "status", "source_id", "source_vintage"),
    {"status": VALUE_STATUS, "period_type": {"annual", "acs_5yr", "point_in_time"}},
    key=("area_id", "year", "indicator"),
)

INVENTORY = Contract(
    "inventory",
    ("area_id", "homes_1unit_detached", "homes_1unit_detached_moe", "status", "source_id", "source_vintage"),
    {"status": VALUE_STATUS},
    key=("area_id",),
)

POLICY_RULES = Contract(
    "policy_rules",
    ("rule_id", "jurisdiction_id", "provision", "value", "effective_from", "source_url", "retrieved", "verification"),
    {"verification": CLAIM_STATUS},
    key=("rule_id",),
)

RIGHTS_EXPOSURE = Contract(
    "rights_exposure",
    ("jurisdiction_id", "scenario_id", "current_class", "reform_class", "class_basis", "rules_as_of", "rights_added_text"),
    {"current_class": RIGHTS_CLASS, "reform_class": RIGHTS_CLASS, "class_basis": CLASS_BASIS},
    key=("jurisdiction_id", "scenario_id"),
)

PERMITS_OBSERVED = Contract(
    "permits_observed",
    (
        "record_key", "jurisdiction_id", "stage", "stage_date", "unit_category",
        "classification_method", "units_added", "match_method", "match_quality", "source_id",
    ),
    {
        "stage": PERMIT_STAGE,
        "unit_category": UNIT_CATEGORY,
        "classification_method": CLASSIFICATION_METHOD,
        "match_method": MATCH_METHOD,
        "match_quality": MATCH_QUALITY,
    },
    key=("record_key", "stage"),
)

PERMITS_BY_AREA_YEAR = Contract(
    "permits_by_area_year",
    ("area_id", "year", "unit_category", "units", "coverage", "suppressed"),
    {"unit_category": UNIT_CATEGORY},
    key=("area_id", "year", "unit_category"),
)

ALL = {c.name: c for c in (
    AREAS, STATE_CONDITIONS, INVENTORY, POLICY_RULES, RIGHTS_EXPOSURE,
    PERMITS_OBSERVED, PERMITS_BY_AREA_YEAR,
)}


def validate(df, contract: Contract) -> list[str]:
    """Return human-readable problems with `df` against `contract`."""
    problems: list[str] = []
    missing = [c for c in contract.required if c not in df.columns]
    if missing:
        problems.append(f"{contract.name}: missing columns {missing}")
    for col, allowed in contract.enums.items():
        if col in df.columns:
            bad = set(df[col].dropna().unique()) - allowed
            if bad:
                problems.append(f"{contract.name}.{col}: values not allowed {sorted(map(str, bad))}")
    if contract.key and all(k in df.columns for k in contract.key):
        dupes = int(df.duplicated(list(contract.key)).sum())
        if dupes:
            problems.append(f"{contract.name}: {dupes} duplicate keys on {list(contract.key)}")
    return problems

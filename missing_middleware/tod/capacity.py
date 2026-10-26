"""TOD station-area capacity: pure functions (no network, no file paths).

Method (docs/tod/STATION_AREAS.md; docs/tod/GATE1_PACKET.md sections 3 and 4.2 B; AQ-047):
- Each parcel near a qualifying stop gets a distance band from its centroid's distance to the nearest
  stop of each kind (rail and rapid, 15-minute bus, 20-minute bus).
- The modelled law sets an allowed density per band (MODELLED_LAW). It is a floor: where current
  zoning already allows as much or more, the law adds nothing.
- Current allowed density per zoning district comes from the hand-coded rule tables
  (reference/tod_zoning_rules_<city>.csv): homes per acre from the minimum lot area per home or the
  printed maximum density, capped by a floor-area estimate (stories x lot coverage), or from FAR alone
  where the code sets no density limit.
- New capacity per parcel = max(area x law - max(area x current, existing homes), 0), then summed by
  area. Existing homes are subtracted only through the max(), never twice.

Every assumption that is not printed in a code is a named constant below, so it can be changed in one
place when the case evidence revises the modelled law (AQ-047 item 1).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping

SQFT_PER_ACRE = 43_560.0
MILE_M = 1609.344
QUARTER_M = 0.25 * MILE_M
HALF_M = 0.5 * MILE_M

# --------------------------------------------------------------------------- modelled law (parameters)

@dataclass(frozen=True)
class LawRule:
    height_ft: float
    far: float
    homes_per_acre: float


# GATE1_PACKET.md section 3. Bus 1/4-1/2 mile rings exist only in the all-1/2-mile sensitivities and get
# the outer-ring rule.
MODELLED_LAW: dict[str, LawRule] = {
    "rapid_quarter": LawRule(65, 3.0, 100),   # rail and rapid stop, within 1/4 mile
    "rapid_half": LawRule(55, 2.5, 80),       # rail and rapid stop, 1/4 to 1/2 mile
    "bus15_quarter": LawRule(55, 2.5, 80),    # 15-minute bus stop, within 1/4 mile (main case)
    "bus20_quarter": LawRule(55, 2.5, 80),    # 20-minute bus stop, within 1/4 mile (high case only)
    "bus15_half": LawRule(55, 2.5, 80),       # 15-minute bus, 1/4 to 1/2 mile (sensitivity b)
    "bus20_half": LawRule(55, 2.5, 80),       # 20-minute bus, 1/4 to 1/2 mile (sensitivity c)
}
BANDS = tuple(MODELLED_LAW)

# Which bands each stop definition covers (keys match reference/tod_definition_summary.csv).
DEFINITION_BANDS: dict[str, frozenset[str]] = {
    "main": frozenset({"rapid_quarter", "rapid_half", "bus15_quarter"}),
    "high": frozenset({"rapid_quarter", "rapid_half", "bus15_quarter", "bus20_quarter"}),
    "b_half": frozenset({"rapid_quarter", "rapid_half", "bus15_quarter", "bus15_half"}),
    "c_half": frozenset(BANDS),
}

# --------------------------------------------------------------------------- assumptions (parameters)

FT_PER_STORY = 11.0            # height limit (ft) -> whole stories
DEFAULT_LOT_COVERAGE = 0.70    # where the code prints no maximum lot coverage
GROSS_SQFT_PER_HOME = 1_000.0  # gross floor area per home (unit plus share of halls, walls, lobby)

# Land that is never eligible, whatever its zoning (owner rule, AQ-047 item 8; MADISON_TEST_PREREG 2).
EXCLUDED_USE_CLASSES = frozenset({"institutional", "park_open_space", "cemetery", "utility_transport", "water"})
ELIGIBLE_ZONING_CLASSES = frozenset({"residential", "mixed_use", "commercial", "downtown_mixed", "planned_development"})


# --------------------------------------------------------------------------- bands

def assign_band(d_rapid: float, d_bus15: float, d_bus20: float) -> str | None:
    """Strongest-law band for a parcel from its distance (m) to the nearest stop of each kind.

    A 15-minute stop is also a 20-minute stop, so callers pass d_bus20 <= d_bus15 (not required).
    Returns None beyond 1/2 mile of every qualifying stop.
    """
    if d_rapid <= QUARTER_M:
        return "rapid_quarter"
    if d_rapid <= HALF_M:
        return "rapid_half"
    if d_bus15 <= QUARTER_M:
        return "bus15_quarter"
    if d_bus20 <= QUARTER_M:
        return "bus20_quarter"
    if d_bus15 <= HALF_M:
        return "bus15_half"
    if d_bus20 <= HALF_M:
        return "bus20_half"
    return None


def law_homes_per_acre(band: str, law: Mapping[str, LawRule] = MODELLED_LAW) -> float:
    """Homes per acre the modelled law allows in a band: its density, capped by its FAR."""
    r = law[band]
    return min(r.homes_per_acre, r.far * SQFT_PER_ACRE / GROSS_SQFT_PER_HOME)


# --------------------------------------------------------------------------- zoning rules

def _num(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return None if (isinstance(v, float) and math.isnan(v)) else float(v)
    s = str(v).strip().replace(",", "")
    return float(s) if s else None


def stories_from_height(height_ft: float | None) -> float | None:
    return None if height_ft is None else float(math.floor(height_ft / FT_PER_STORY))


@dataclass(frozen=True)
class DistrictRule:
    district: str
    zoning_class: str
    rule_type: str               # density | far | existing_is_rule | assumed_at_or_above_law | not_eligible | not_coded
    homes_per_acre: float | None  # current allowance; None when existing homes or the law set it
    far: float | None             # current floor-area estimate (code FAR, or stories x coverage)
    status: str


def district_rule(row: Mapping, tod_overlay: bool = False) -> DistrictRule:
    """Current allowed homes per acre and FAR for one coded district row (rule-table CSV row).

    density: min(43,560 / lot area per home or printed homes per acre, FAR x 43,560 / gross sq ft per home)
    far:     FAR x 43,560 / gross sq ft per home (no density limit in the code)
    FAR is the code's FAR where printed, else stories x lot coverage (code value or the default). Stories
    come from max_stories, else from max_height_ft. Inside Madison's TOD overlay, the overlay's stories
    replace the base district's where higher. A district with no height or FAR limit has no FAR cap.
    """
    rt = (row.get("rule_type") or "").strip()
    lot = _num(row.get("min_lot_area_per_home_sqft"))
    hpa = _num(row.get("max_homes_per_acre"))
    stories = _num(row.get("max_stories"))
    if stories is None:
        stories = stories_from_height(_num(row.get("max_height_ft")))
    tod_st = _num(row.get("tod_overlay_max_stories"))
    if tod_overlay and tod_st is not None:
        stories = max(stories or 0.0, tod_st)
    cov = _num(row.get("max_lot_coverage"))
    cov = DEFAULT_LOT_COVERAGE if cov is None else cov
    far = _num(row.get("max_far"))
    if far is None and stories is not None:
        far = stories * cov
    far_cap = None if far is None else far * SQFT_PER_ACRE / GROSS_SQFT_PER_HOME
    out_hpa: float | None = None
    if rt == "density":
        dens = SQFT_PER_ACRE / lot if lot else hpa
        if dens is None:
            raise ValueError(f"{row.get('district')}: density rule without a density")
        out_hpa = dens if far_cap is None else min(dens, far_cap)
    elif rt == "far":
        if far_cap is None:
            raise ValueError(f"{row.get('district')}: far rule without FAR or stories")
        out_hpa = far_cap
    elif rt not in {"existing_is_rule", "assumed_at_or_above_law", "not_eligible", "not_coded"}:
        raise ValueError(f"{row.get('district')}: unknown rule_type {rt!r}")
    return DistrictRule(str(row.get("district")), (row.get("zoning_class") or "").strip(), rt, out_hpa, far,
                        (row.get("status") or "").strip())


def rule_table(rows: Iterable[Mapping], tod_overlay: bool = False) -> dict[str, DistrictRule]:
    return {str(r["district"]).strip(): district_rule(r, tod_overlay) for r in rows}


def is_eligible(zoning_class: str, use_class: str, rule_type: str) -> bool:
    """Eligible land: residential, mixed-use or commercial zoning (incl. planned development), not an
    excluded use. Single-family parcels count (the law applies to residential parcels)."""
    return (zoning_class in ELIGIBLE_ZONING_CLASSES and use_class not in EXCLUDED_USE_CLASSES
            and rule_type not in {"not_eligible"})


# --------------------------------------------------------------------------- capacity

def capacity_gain(acres: float, law_hpa: float, current_hpa: float | None, existing_homes: float) -> float:
    """New homes the law allows on one parcel: max(area x law - max(area x current, existing), 0).

    current_hpa None means the current allowance is the existing homes (planned development).
    """
    law = acres * law_hpa
    current = existing_homes if current_hpa is None else acres * current_hpa
    return max(law - max(current, existing_homes), 0.0)


@dataclass
class ParcelResult:
    eligible: bool
    current_allowed_homes: float
    law_allowed_homes: float
    capacity_gain: float
    added_floor_area_sqft: float


def parcel_capacity(acres: float, band: str, rule: DistrictRule | None, use_class: str,
                    existing_homes: float, law: Mapping[str, LawRule] = MODELLED_LAW) -> ParcelResult:
    """Capacity numbers for one parcel. Rules:
    - not eligible (excluded use, or zoning that is not residential, mixed-use, commercial or planned
      development), or no coded zoning (rule None or not_coded): all zero; the caller reports such
      land on its own line rather than guessing;
    - existing_is_rule: current allowance = existing homes;
    - assumed_at_or_above_law: current allowance = the law's (no gain);
    - otherwise the coded homes per acre.
    Law allowed homes = max(area x law, current allowance): the law is a floor, never a cut.
    """
    if rule is None or rule.rule_type == "not_coded" or not is_eligible(rule.zoning_class, use_class, rule.rule_type):
        return ParcelResult(False, 0.0, 0.0, 0.0, 0.0)
    rt = rule.rule_type
    lhpa = law_homes_per_acre(band, law)
    if rt == "existing_is_rule":
        cur_hpa = None
        current = existing_homes
        cur_far = None
    elif rt == "assumed_at_or_above_law":
        cur_hpa = lhpa
        current = acres * lhpa
        cur_far = law[band].far
    else:
        cur_hpa = rule.homes_per_acre
        current = acres * cur_hpa
        cur_far = rule.far
    gain = capacity_gain(acres, lhpa, cur_hpa, existing_homes)
    law_allowed = max(acres * lhpa, current)
    added_far = 0.0 if cur_far is None else max(law[band].far - cur_far, 0.0)
    return ParcelResult(True, current, law_allowed, gain, added_far * acres * SQFT_PER_ACRE)

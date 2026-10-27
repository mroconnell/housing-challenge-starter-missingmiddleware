"""Ann Arbor 2021 TC1 transit corridor district: HELD-OUT case adapter. No estimate: no permit source with units.

A probe on 2026-10-26 (CASE_RESULTS.md, section Ann Arbor) found no bulk permit file with unit counts: the public
permit layer lists only active permits without units; older permits sit in search-only systems (A2Trak 2008 to
March 2022, then STREAM); the data.gov archive link returned "Not Found". Current zoning shows 7 TC1 polygons
(rezoned April 2022 to October 2024); zoning before TC1 is only in the ordinance parcel lists. A parcel snapshot
with year built and unit counts (January 2024) would measure completions, not permits, and is not used.
The case is recorded as held out with its rent and the reason; it never enters a fit.
"""
from __future__ import annotations

import pandas as pd

from missing_middleware.tod import cases as C


def build() -> tuple[C.CaseInputs, dict]:
    ci = C.CaseInputs(case="annarbor_tc1_2021", role="heldout", effective_year=2022, first_year=2008, last_full_year=2025,
                      permits=pd.DataFrame(columns=["project", "area", "year", "units"]), acres={}, homes={},
                      dose_table=None, parking_change="removed (no minimum in TC1)", mandate="no", has_units=False,
                      status_override="no_data: no permit source with unit counts (held out; no estimate)",
                      notes="map rezonings 2022-2024 leave at most 3 after years; no permit file with units")
    return ci, {"sources_checked": ["PublicStaffPermits FeatureServer", "A2Trak / STREAM (search only)", "data.gov archive (Not Found)",
                                    "a2maps.a2gov.org (HTTP 403)", "Zoning FeatureServer (current TC1)"]}


def build_counts() -> list:
    """Permit-count measure (plan section 7, 2026-10-27): not possible. A second probe (2026-10-27) found zoning before
    and after TC1 (the Parcels_by_Zoning snapshot of January 2024 has both), but no permit records with locations
    before 2022: the public permit layer holds only active permits (720, issued 2022-2026, 93 new residential); A2Trak
    (2008 to March 2022) is a search screen only; STREAM refuses scripts (HTTP 403); Washtenaw County servers did not
    answer; the Census Building Permits Survey has city totals without locations. With the first map rezoning in April
    2022, there are no before years."""
    ci = C.CaseInputs(case="annarbor_permit_count_all", role="heldout", effective_year=2022, first_year=2022, last_full_year=2025,
                      permits=pd.DataFrame(columns=["project", "area", "year", "units"]), acres={}, homes={}, dose_table=None,
                      parking_change="removed (no minimum in TC1)", mandate="no", measure="permits per eligible acre per year",
                      status_override="no_data: no permit records with locations before 2022 (held out)",
                      notes="zoning before and after TC1 exists (January 2024 parcel snapshot); permits do not")
    return [(ci, {"sources_checked": ["PublicStaffPermits FeatureServer (active permits 2022-2026 only)", "A2Trak (search only)",
                                      "STREAM (HTTP 403)", "Washtenaw County GIS (no answer)", "Census BPS (no locations)"]})]

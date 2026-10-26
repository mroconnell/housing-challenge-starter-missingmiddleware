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

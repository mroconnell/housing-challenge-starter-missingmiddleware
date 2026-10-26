"""Phoenix 2015 Walkable Urban Code: case adapter. Context only: no permit source with unit counts.

A probe on 2026-10-26 (CASE_RESULTS.md, section Phoenix) found:
- the City's permit layer (maps.phoenix.gov Public/Planning_Permit/MapServer/1) covers issue dates from 2015 only and
  has no unit field;
- the open data portal's only housing-permit table is the federal city-level total (no location);
- Walkable Urban Code areas exist (Public/WalkableUrbanCode/MapServer/0), and current WU zoning carries case numbers,
  but no layer gives the zoning before each WU rezoning or its date.
No file is fetched; the case is recorded with its rent and the reason.
"""
from __future__ import annotations

import pandas as pd

from missing_middleware.tod import cases as C


def build() -> tuple[C.CaseInputs, dict]:
    ci = C.CaseInputs(case="phoenix_walkable_urban_code_2015", role="fit", effective_year=2015, first_year=2015,
                      last_full_year=2025, permits=pd.DataFrame(columns=["project", "area", "year", "units"]), acres={},
                      homes={}, dose_table=None, parking_change="unknown", mandate="no", has_units=False,
                      status_override="context_only: no permit source with unit counts or before years (permit layer starts 2015, no unit field)",
                      notes="no estimate; see CASE_RESULTS.md for the sources checked")
    return ci, {"sources_checked": ["maps.phoenix.gov Public/Planning_Permit/MapServer/1", "phoenixopendata.com",
                                    "Public/Planning_Permit/MapServer/2,3,9", "Public/WalkableUrbanCode/MapServer/0"]}

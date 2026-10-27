"""Ottawa transit-oriented development (TD) zone, By-law 2012-406 (14 November 2012): case adapter (batch 2).

Plan: CASE_ANALYSIS_PLAN.md section 7, entry of 2026-10-27 ("more cities for the trait test").

No estimate is made. Reasons (probe of 2026-10-27, docs/tod/CASE_RESULTS.md (section 'Added cities, batch 2')):
- Before years: the City's open permit files (address, dwelling units, issue date) start in July 2011. The TD zone
  was mapped in two steps: By-law 2012-406 (Train, St-Laurent, Cyrville; consolidation date 14 November 2012) and
  By-law 2014-022 (Lees, Hurdman, Blair; 22 January 2014, confirmed by the Ontario Municipal Board, PL140185). The
  2012 step has no full year before it and the 2014 step has two (2012, 2013), fewer than the plan's 3. The same
  holds for the permit-count fallback, which uses the same files. Later TD polygons (2015-2025) are small
  site-specific amendments of existing TD land, not new station areas.
- Zoning before: the zoning layer is the current consolidation; its HISTORY field lists earlier amending by-law
  numbers, not earlier zone codes, so whether density rose cannot be read for any lot.
- Parcels: the City does not publish a parcel fabric under its open licence (Teranet), so eligible acres would have
  to come from zoning polygons.

The adapter reports, as diagnostics, the TD zone acres by the amending by-law and its consolidation date, and the
months the permit files cover. It never enters a fit.

Inputs (data/raw/tod_cases/ottawa/, fetched by scripts/fetch_tod_cases_batch2.py): td_zones.geojson,
otrain_stage1_stations.geojson, permits/permits_<year>.xls[x], manifest.json.
"""
from __future__ import annotations

import json

import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "ottawa"
CRS_M = 32189  # NAD83 / MTM zone 9 (metres)
PERMITS_FIRST_MONTH = "2011-07"
STEPS = {"2012-406": 2012, "2014-022": 2014}  # the two by-laws that mapped TD station areas
EMPTY = pd.DataFrame(columns=["project", "area", "year", "units"])


def bylaw_step(bylaw: str, history: str) -> str | None:
    """Which station-area step created a TD polygon: the first of 2012-406 / 2014-022 named in its by-law or history."""
    s = f"{bylaw or ''} {history or ''}"
    for b in STEPS:
        if b in s:
            return b
    return None


def full_before_years(effective_year: int, first_month: str = PERMITS_FIRST_MONTH) -> int:
    """Full calendar years of permit data before the effective year."""
    y, m = (int(x) for x in first_month.split("-"))
    first_full = y if m == 1 else y + 1
    return max(0, effective_year - max(first_full, effective_year - C.BEFORE_MAX))


def build() -> tuple[C.CaseInputs, dict]:
    diag: dict = {"permit_files_first_month": PERMITS_FIRST_MONTH,
                  "full_before_years": {b: full_before_years(y) for b, y in STEPS.items()}}
    try:
        import geopandas as gpd
        td = gpd.read_file(DIR / "td_zones.geojson").to_crs(CRS_M)
        td["step"] = [bylaw_step(str(b), str(h)) for b, h in zip(td["BYLAW_NUM"], td["HISTORY"])]
        td["acres"] = td.geometry.area / C.SQM_PER_ACRE
        diag["td_acres_by_step"] = td.groupby(td["step"].fillna("later site-specific"))["acres"].sum().round(1).to_dict()
        diag["td_acres_by_zone"] = td.groupby("ZONE_CODE")["acres"].sum().round(1).to_dict()
        man = json.loads((DIR / "manifest.json").read_text())
        diag["permit_files"] = sorted(k for k in man["files"] if k.startswith("permits/"))
    except Exception as e:  # noqa: BLE001
        diag["load_error"] = f"{type(e).__name__}: {e}"
    best = max(diag["full_before_years"].values())
    ci = C.CaseInputs(case="ottawa_td_zone_2012", role="fit", effective_year=2012, first_year=2012, last_full_year=2025,
                      permits=EMPTY.copy(), acres={}, homes={}, dose_table=None,
                      parking_change="parking maximums near stations (minimum change unknown)", mandate="no",
                      status_override=f"context_only: permit files start July 2011, at most {best} full before years (plan needs {C.BEFORE_MIN})",
                      notes="TD1-TD3 zones (20, 60, 90 m; minimum densities); steps 2012-406 and 2014-022; no zoning-before layer; no open parcels")
    return ci, diag


def build_counts() -> list:
    """Permit-count fallback: the same permit files, so the same shortage of before years."""
    ci, diag = build()
    best = max(diag["full_before_years"].values())
    ci = C.CaseInputs(case="ottawa_td_permit_count_all", role="fit", effective_year=2012, first_year=2012, last_full_year=2025,
                      permits=EMPTY.copy(), acres={}, homes={}, dose_table=None, parking_change=ci.parking_change, mandate="no",
                      measure="permits per eligible acre per year",
                      status_override=f"context_only: permit files start July 2011, at most {best} full before years (plan needs {C.BEFORE_MIN})",
                      notes=ci.notes)
    return [(ci, diag)]


"""Raleigh 2021 transit overlay (TC-17A-20) and its map rezonings: case adapter. Context only.

Inputs (data/raw/tod_cases/raleigh/, fetched by scripts/fetch_tod_cases.py): new residential building permits,
rezoning cases, the TOD overlay layer.

The overlay text was adopted in 2021, but it applies only where the map puts it. The rezoning-case layer shows two
kinds of TOD map changes: the City's own overlay mappings ("Various" -> "add TOD": Z-18-2022 and Z-19-2022 in 2022,
then the New Bern Avenue set Z-92A to Z-92E-2022 in 2024), and applicants' conditional site rezonings with TOD
(2021 onward), which pick the sites about to be built and so cannot serve as a treatment. The permit file's
housing-unit field is filled for almost every new residential permit through 2023 and is nearly empty from 2024, so
the City's first mapping (2022) has one after year with unit counts. The case is context only. The adapter computes
these facts from the files, so the status follows the data.
"""
from __future__ import annotations

import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "raleigh"
MIN_FILL = 0.9  # share of new residential permits with a unit count for a year to count as having units


def build() -> tuple[C.CaseInputs, dict]:
    import geopandas as gpd
    p = gpd.read_file(DIR / "permits_new_residential.geojson")
    p["year"] = pd.to_numeric(p["issueddate_yr"], errors="coerce")
    p["has_units"] = pd.to_numeric(p["housingunitstotal"], errors="coerce").fillna(0) > 0
    fill = p.groupby("year")["has_units"].mean()
    rz = gpd.read_file(DIR / "rezoning_cases.geojson")
    rz["date"] = pd.to_datetime(rz["StatusDate"], unit="ms", errors="coerce")
    tod = rz[rz["ZON_REQ"].astype(str).str.contains("TOD", case=False) & rz["STATUS"].astype(str).str.startswith("Approv")]
    # the City's own overlay mappings ("Various" -> "add TOD"): the reform; the others are site-specific conditional
    # rezonings requested by applicants (district code with -CU), which select the sites that are about to be built
    city = tod[tod["PrevZoning"].astype(str).str.strip().eq("Various")]
    eff = int(city["date"].min().year) if len(city) else 2024
    per = C.period_years(eff, int(p["year"].min()), 2025)
    after_with_units = [y for y in per["after"] if fill.get(y, 0) >= MIN_FILL]
    first_wave = city[city["date"].dt.year == eff]
    base_change = first_wave["ZON_REQ"].astype(str).str.contains("Base District|Height", case=False).any()
    status = ("context_only: " + f"{len(after_with_units)} after year(s) with unit counts (overlay first mapped {eff}; "
              "unit field nearly empty from 2024)" + ("" if base_change else "; the first mapping added the overlay without changing base districts"))
    diag = {"city_overlay_mappings": city[["ZONE_CASE", "ZON_REQ"]].astype(str).assign(date=city["date"].dt.date.astype(str)).values.tolist(),
            "applicant_tod_rezonings_approved": int((~tod.index.isin(city.index)).sum()),
            "unit_fill_share_by_year": {int(k): round(float(v), 3) for k, v in fill.items() if k >= 2015},
            "overlay_polygons": int(len(gpd.read_file(DIR / "tod_overlays.geojson")))}
    ci = C.CaseInputs(case="raleigh_tod_2021", role="fit", effective_year=eff, first_year=int(p["year"].min()), last_full_year=2025,
                      permits=pd.DataFrame(columns=["project", "area", "year", "units"]), acres={}, homes={}, dose_table=None,
                      parking_change="unknown", mandate="no", status_override=status,
                      notes="no estimate: no after year with unit counts")
    return ci, diag

"""Minneapolis Hiawatha (Blue Line) station-area rezonings, 2008-2012: case adapter (batch 2, weak design, flagged).

Plan: CASE_ANALYSIS_PLAN.md section 7, entry of 2026-10-27 ("more cities for the trait test"). Minneapolis has a weak
design and is added only to widen the range of traits.

No estimate is made. Reasons (probe of 2026-10-27, docs/tod/CASE_RESULTS.md (section 'Added cities, batch 2')):
- Boundary: the official rezoning boundaries (38th Street west, approved 2008; 46th Street, approved 8 May 2009;
  38th Street east, 2012) exist only as image maps in PDFs the City has since taken down (archived copies only). No
  GIS layer, parcel list or zoning snapshot from 2007-2012 was found: the City's open zoning layers start January
  2017 (msvcCPED_PrimaryZoning_20170126) and June 2023 (PrimaryZoningArchive). The plan's treatment is "parcels inside
  the official upzoning boundary", which cannot be built automatically, and zoning before cannot be read for any lot.
- Units: unit counts start in 2010 (New_Non_SFD_Building_Permits_2010_2015), after the 2008 and 2009 rezonings and
  only 2 years before the 2012 one, so the unit-based measure has fewer than 3 before years for every member.
- Permit counts (the fallback): the yearly permit layers 2000-2014 have locations and permit types but no units. The
  2011 layer holds 2012's records (identical to the 2012 layer), so 2011 is missing.

The adapter loads what exists and reports, as diagnostics only, the yearly count of new residential building permits
within 1/2 mile of the Hiawatha stations whose areas were rezoned (Franklin Avenue, 38th Street, 46th Street) and of
the line's other south Minneapolis stations (Lake Street, 50th Street/Minnehaha Park). These are context, not a
difference-in-differences: no comparison area can be drawn without the boundary.

Inputs (data/raw/tod_cases/minneapolis/, fetched by scripts/fetch_tod_cases_batch2.py): permits/permits_<year>.geojson
(2000-2014), permits_non_sfd_units_2010_2015.geojson, transit_stations.geojson, zoning_2017_01.geojson.
"""
from __future__ import annotations

import glob
import re

import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "minneapolis"
CRS_M = 26915  # NAD83 / UTM zone 15N (metres)
REZONED = {"Franklin Avenue": 2008, "38th Street": 2008, "46th Street": 2009}  # 38th St east followed in 2012
OTHER = ("Lake Street", "50th Street/Minnehaha Park")
NEW_RES_USE = re.compile(r"^(R1|M\d|A1|A2)")  # one-family, multifamily and apartment use codes on new-building permits
EMPTY = pd.DataFrame(columns=["project", "area", "year", "units"])


def station_name(s: str) -> str:
    return re.sub(r"\s+(IB|OB)$", "", str(s).strip())


def new_res_permits(p: pd.DataFrame) -> pd.DataFrame:
    """New residential building permits: type BINB (new building) with a residential use code, one per permit number."""
    q = p[(p["Permit_Type"].astype(str).str.strip() == "BINB") & p["Use_Code"].astype(str).str.match(NEW_RES_USE)]
    return q.drop_duplicates("Permit_Number")


def load_permits():
    import geopandas as gpd
    parts = []
    for f in sorted(glob.glob(str(DIR / "permits" / "permits_*.geojson"))):
        g = gpd.read_file(f)
        g["layer_year"] = int(re.search(r"(\d{4})", f.split("/")[-1]).group(1))
        parts.append(g)
    g = pd.concat(parts, ignore_index=True)
    return gpd.GeoDataFrame(g, geometry="geometry", crs=parts[0].crs)


def station_counts(permits, stations) -> pd.DataFrame:
    """Yearly count of new residential permits within 1/2 mile of each named station (IB/OB platforms merged)."""
    import geopandas as gpd
    st = stations.copy()
    st["station"] = st["STN_NAME"].map(station_name)
    st = st[st["station"].isin(list(REZONED) + list(OTHER))].dissolve("station").reset_index()
    st["geometry"] = st.geometry.centroid.buffer(C.HALF_MILE_M)
    j = gpd.sjoin(permits[["Permit_Number", "layer_year", "geometry"]], st[["station", "geometry"]], predicate="within")
    t = j.groupby(["station", "layer_year"]).size().unstack(fill_value=0)
    return t


def build() -> tuple[C.CaseInputs, dict]:
    diag: dict = {"rezonings": {"38th Street west": "2008-05-02", "46th Street": "2009-05-08", "38th Street east": "2012"},
                  "boundary": "PDF image maps only (City pages removed; Wayback copies); no GIS or parcel list",
                  "zoning_before": "no layer before January 2017"}
    try:
        import geopandas as gpd
        p = load_permits()
        diag["layer_2011_duplicates_2012"] = bool(
            set(p.loc[p["layer_year"] == 2011, "Permit_Number"]) == set(p.loc[p["layer_year"] == 2012, "Permit_Number"]))
        q = new_res_permits(p[p["layer_year"] != 2011]).to_crs(CRS_M)
        st = gpd.read_file(DIR / "transit_stations.geojson").to_crs(CRS_M)
        diag["new_residential_permits_within_half_mile_by_year"] = station_counts(q, st).to_dict(orient="index")
        diag["citywide_new_residential_permits_by_year"] = q.groupby("layer_year").size().to_dict()
    except Exception as e:  # noqa: BLE001  (raw files absent: the case still records why it has no estimate)
        diag["load_error"] = f"{type(e).__name__}: {e}"
    ci = C.CaseInputs(case="minneapolis_hiawatha_2008_2012", role="fit", effective_year=2009, first_year=2010, last_full_year=2014,
                      permits=EMPTY.copy(), acres={}, homes={}, dose_table=None, parking_change="unknown",
                      mandate="no (no city inclusionary rule until 2019)", median_rent=None, has_units=False,
                      status_override="no_data: rezoning boundaries only as PDF image maps; no zoning before 2017; units from 2010 only",
                      notes="weak design, flagged (added only to widen the range of traits); see CASE_RESULTS.md (section 'Added cities, batch 2')")
    return ci, diag


def build_counts() -> list:
    """Permit-count fallback (plan section 7, 2026-10-27): not possible without the rezoning boundary (see module doc)."""
    ci, diag = build()
    ci = C.CaseInputs(case="minneapolis_hiawatha_permit_count_all", role="fit", effective_year=2009, first_year=2000,
                      last_full_year=2014, permits=EMPTY.copy(), acres={}, homes={}, dose_table=None, parking_change="unknown",
                      mandate="no", measure="permits per eligible acre per year",
                      status_override="no_data: permits with locations exist (2000-2014, 2011 missing) but no machine-readable rezoning boundary",
                      notes="weak design, flagged; station-area permit counts by year are in the diagnostics only")
    return [(ci, diag)]

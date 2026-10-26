"""Saint Paul Green Line (Central Corridor) rezoning, 2011: case adapter. Context only under the plan (permits with
unit counts start in 2010, so at most 1 before year; the plan needs 3).

Inputs (data/raw/tod_cases/stpaul/, fetched by scripts/fetch_tod_cases.py):
- housing_production.geojson: the city's Housing Production layer (projects 2010 onward, permit issue year, new
  dwelling units, parcel).
- zoning_2010_11.geojson, zoning_2011_11.geojson, zoning_2012_11.geojson: principal zoning snapshots.
- parcels.geojson: Saint Paul tax parcels with land use.
- rail_stops.geojson: Metro Transit light-rail stops (BTS National Transit Map).
- ../census_2010_blocks/tabblock2010_27_pophu.zip.

Rules:
- Treatment: parcels within 1/2 mile of a Green Line stop in Saint Paul whose zoning went from a non-traditional-
  neighbourhood district (November 2010) to T1-T4 (November 2012). TN1-TN3 were renamed T1-T3 in the same period;
  a rename is not a change.
- Effective year 2011 (City Council adoption, April 2011). The city's own zoning archive first shows the new
  districts in November 2012; with 2012 the case still has only 2 before years.
- Dose: residential FAR before and after (STP_FAR; values from the Saint Paul zoning code as summarised in
  CASE_INVENTORY.md and marked source_lead in CASE_RESULTS.md).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "stpaul"
CRS_M = 26915  # NAD83 / UTM 15N
EFFECTIVE_YEAR = 2011
FIRST_YEAR, LAST_FULL_YEAR = 2010, 2024
RENAME = {"TN1": "T1", "TN2": "T2", "TN3": "T3", "TN3M": "T3M"}
T_DISTRICTS = {"T1", "T2", "T3", "T3M", "T4", "T4M"}
# Allowed residential FAR (source_lead): business districts B1-B3 about 1.0-2.0, multifamily RM2 2.25, industrial 0
# (housing not allowed), traditional neighbourhood T1 1.0, T2 2.0, T3 3.0, T4 no maximum (75 ft -> 3.76 at 0.05 FAR/ft).
STP_FAR = {"R1": 0.3, "R2": 0.3, "R3": 0.4, "R4": 0.5, "RT1": 0.6, "RT2": 1.0, "RM1": 1.5, "RM2": 2.25, "RM3": 3.0,
           "OS": 1.0, "B1": 1.0, "BC": 1.0, "B2": 2.0, "B3": 2.0, "B4": 8.0, "B5": 8.0, "TN1": 1.0, "TN2": 2.0, "TN3": 3.0,
           "TN3M": 3.0, "T1": 1.0, "T2": 2.0, "T3": 3.0, "T3M": 3.0, "T4": 75 * 6.02 / 120, "T4M": 75 * 6.02 / 120,
           "I1": 0.0, "I2": 0.0, "I3": 0.0, "IR": 0.0, "VP": 0.0, "PD": np.nan, "CA": np.nan, "RL": 0.2}
CLASS = {**{k: "res" for k in ("R1", "R2", "R3", "R4", "RT1", "RT2", "RM1", "RM2", "RM3", "RL")},
         **{k: "com" for k in ("OS", "B1", "BC", "B2", "B3", "B4", "B5", "VP")},
         **{k: "mixed" for k in ("TN1", "TN2", "TN3", "TN3M", "T1", "T2", "T3", "T3M", "T4", "T4M", "PD")},
         **{k: "ind" for k in ("I1", "I2", "I3", "IR")}, "CA": "inst"}
NOT_ELIGIBLE_LANDUSE = re.compile(r"park|cemet|church|school|college|univers|hospital|government|public|water|utilit|"
                                  r"railroad|exempt|religious|library|right.of.way|road", re.I)
GREEN_LINE_STP = re.compile(r"Westgate|Raymond|Fairview|Snelling|Hamline|Lexington|Victoria|Dale|Western|Capitol|"
                            r"Robert St|10th St|Central Station|Union Depot", re.I)


def build() -> tuple[C.CaseInputs, dict]:
    import geopandas as gpd
    parcels = gpd.read_file(DIR / "parcels.geojson").to_crs(CRS_M)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].drop_duplicates("ParcelID").reset_index(drop=True)
    parcels["acres"] = parcels.geometry.area / C.SQM_PER_ACRE
    pts = gpd.GeoDataFrame(geometry=parcels.geometry.representative_point(), crs=CRS_M)

    def zone(fn):
        z = gpd.read_file(DIR / fn).to_crs(CRS_M)[["Zoning", "geometry"]]
        j = gpd.sjoin(pts, z, how="left", predicate="within")
        return j[~j.index.duplicated()].reindex(pts.index)["Zoning"].astype(str).str.strip()

    parcels["z_before"] = zone("zoning_2010_11.geojson")
    parcels["z_after"] = zone("zoning_2012_11.geojson")
    stops = gpd.read_file(DIR / "rail_stops.geojson").to_crs(CRS_M)
    gl = stops[stops["stop_name"].astype(str).str.contains(GREEN_LINE_STP)].geometry
    near_gl = pts.geometry.within(gl.buffer(C.HALF_MILE_M).union_all())
    renamed = parcels["z_before"].map(lambda z: RENAME.get(z, z))
    parcels["treated"] = near_gl & parcels["z_after"].isin(T_DISTRICTS) & (renamed != parcels["z_after"])
    city = parcels.union_all()
    stations_in_city = stops[stops.geometry.within(city)].geometry
    parcels["area"] = C.assign_areas(parcels, parcels["treated"], stations=stations_in_city)
    parcels["zclass"] = parcels["z_before"].map(CLASS)
    lu = parcels["LandUseCodeDescription"].astype(str)
    parcels["eligible"] = parcels["zclass"].isin(["res", "com", "mixed"]) & ~lu.str.contains(NOT_ELIGIBLE_LANDUSE)
    el = parcels[parcels["area"].notna() & parcels["eligible"]]
    acres = el.groupby("area")["acres"].sum().to_dict()

    h = gpd.read_file(DIR / "housing_production.geojson").to_crs(CRS_M)
    h = h[(h["TypeOfWork"] == "New")].copy()
    h["units"] = pd.to_numeric(h["NewDwellingUnits"], errors="coerce").fillna(0)
    h["year"] = pd.to_numeric(h["ProjectPermitIssueYear"], errors="coerce")
    h = h[(h["units"] > 0) & (h["year"] >= 2000)]
    h["project"] = h["ParcelID"].astype(str)
    h["pix"] = C.locate_points(h, parcels)
    h["area"] = parcels["area"].reindex(h["pix"]).values
    h["eligible"] = parcels["eligible"].reindex(h["pix"]).fillna(False).astype(bool).values
    permits = h[h["area"].notna() & h["eligible"]][["project", "area", "year", "units"]].copy()
    permits["year"] = permits["year"].astype(int)

    tr = el[el["area"] == C.TREAT]
    dose_table = pd.DataFrame({"acres": tr["acres"], "old_far": tr["z_before"].map(STP_FAR), "new_far": tr["z_after"].map(STP_FAR)})

    homes = {}
    bz = RAW / "tod_cases" / "census_2010_blocks" / "tabblock2010_27_pophu.zip"
    if bz.exists():
        bbox = tuple(gpd.GeoSeries([el.union_all().envelope], crs=CRS_M).to_crs(4269).total_bounds)
        b = gpd.read_file(bz, bbox=bbox).to_crs(CRS_M)
        b = gpd.GeoDataFrame({"homes": b["HOUSING10"]}, geometry=b.geometry.representative_point(), crs=CRS_M)
        homes = C.homes_by_area(b, el[["area", "geometry"]])
    diag = {"treated_parcels": int(parcels["treated"].sum()),
            "zoning_before_treated": parcels.loc[parcels["treated"], "z_before"].value_counts().head(10).to_dict(),
            "zoning_after_treated": parcels.loc[parcels["treated"], "z_after"].value_counts().head(10).to_dict(),
            "green_line_stops_in_saint_paul": int(len(gl)),
            "second_comparison_stations": int(len(C.stations_not_upzoned(stations_in_city, parcels.loc[parcels["treated"]].geometry.union_all()))),
            "permits_located_share": round(float(h["pix"].notna().mean()), 4),
            "treated_parcels_already_T_in_2011_11_snapshot": int(zone("zoning_2011_11.geojson")[parcels["treated"]].isin(T_DISTRICTS).sum()),
            "parcels_changed_2010_11_to_2011_11": int((zone("zoning_2011_11.geojson") != parcels["z_before"]).sum())}
    ci = C.CaseInputs(case="stpaul_green_line_2011", role="fit", effective_year=EFFECTIVE_YEAR, first_year=FIRST_YEAR,
                      last_full_year=LAST_FULL_YEAR, permits=permits, acres=acres, homes=homes, dose_table=dose_table,
                      parking_change="removed within 1/4 mile of stations; residential minimums cut 25% in T3/T4",
                      mandate="no", notes="permits with units only from 2010; dose values source_lead")
    return ci, diag

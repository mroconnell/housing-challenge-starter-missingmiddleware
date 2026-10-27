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

import numpy as np
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


# --------------------------------------------------------------------------- permit counts (plan section 7, 2026-10-27)

SF_TYPES = {"DETACHED SINGLE FAMILY DWELLING", "RESIDENTIAL TOWNHOUSE", "MANUFACTURED HOME"}
MF_TYPES = {"TWO FAMILY BUILDING (DUPLEX)", "THREE OR FOUR FAMILY BUILDING", "FIVE OR MORE FAMILY BUILDING"}
CRS_M = 32119
NOT_ELIGIBLE = r"EXEMPT|GOVERN|PARK|CEMETER|CHURCH|RELIG|SCHOOL|UTILIT|INDUSTR|RAILROAD|RIGHT.OF.WAY|COMMON AREA"


def build_counts() -> list:
    """New residential building permits (count of permits, not homes) per eligible acre per year: all, single-family
    (detached, townhouse, manufactured) and multifamily (2+ unit buildings). Context only.

    Reform land: the City's TOD map changes that also changed base districts and heights (Z-92A to Z-92E-2022,
    approved March to July 2024; effective year 2024). The City's 2022 overlay-only mappings did not raise by-right
    density (the overlay's extra height needs affordable units), so they are rezonings outside the reform. The case
    record gives no lot-level zoning before ("Various"), so every lot in those cases counts as having risen and no
    land can be tested for "already at the law". Lots in any other rezoning approved 2018-2025 are in no area."""
    import geopandas as gpd
    rz = gpd.read_file(DIR / "rezoning_cases.geojson").to_crs(CRS_M)
    rz["geometry"] = rz.geometry.make_valid()
    rz["date"] = pd.to_datetime(rz["StatusDate"], unit="ms", errors="coerce")
    approved = rz[rz["STATUS"].astype(str).str.startswith("Approv")]
    reform = approved[approved["ZON_REQ"].astype(str).str.contains("Base District", case=False) &
                      approved["PrevZoning"].astype(str).str.strip().eq("Various")]
    eff = int(reform["date"].min().year)
    per = C.period_years(eff, 2000, 2025)
    other = approved[~approved.index.isin(reform.index) &
                     approved["date"].between(pd.Timestamp(f"{per['before'][0]}-01-01"), pd.Timestamp(f"{per['after'][-1]}-12-31"))]
    parcels = gpd.read_file(DIR / "parcels.geojson").to_crs(CRS_M)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].drop_duplicates("PIN_NUM").reset_index(drop=True)
    parcels["acres"] = parcels.geometry.area / C.SQM_PER_ACRE
    pts = parcels.geometry.representative_point()
    in_reform = pts.within(reform.geometry.union_all())
    changed = pts.within(other.geometry.union_all()) & ~in_reform
    in_city = parcels["PLANNING_JURISDICTION"].astype(str).str.upper().eq("RA") | \
        parcels["CITY_DECODE"].astype(str).str.upper().str.contains("RALEIGH")
    use = (parcels["LAND_CLASS_DECODE"].astype(str) + " " + parcels["TYPE_USE_DECODE"].astype(str) + " " +
           parcels["BILLING_CLASS_DECODE"].astype(str)).str.upper()
    eligible = ~use.str.contains(NOT_ELIGIBLE)
    one = pd.Series(1.0, index=parcels.index)
    area, rule = C.uniform_areas(parcels, in_reform, in_reform, one * 0, one, pd.Series(False, index=parcels.index), changed,
                                 eligible, in_city=in_city, stations=None)
    parcels["area"], parcels["eligible"] = area, eligible
    el = parcels[parcels["area"].notna() & parcels["eligible"]]
    acres = el.groupby("area")["acres"].sum().to_dict()
    orig = C.assign_areas(parcels, in_reform, in_city=in_city)
    orig_acres = parcels[orig.notna() & eligible].groupby(orig)["acres"].sum().to_dict()

    p = gpd.read_file(DIR / "permits_new_residential.geojson").to_crs(CRS_M)
    p = p.drop_duplicates("permitnum")
    p["kind"] = p["censuslanduse"].astype(str).str.strip().str.upper()
    p["series"] = np.where(p["kind"].isin(SF_TYPES), "sf", np.where(p["kind"].isin(MF_TYPES), "mf", None))
    p = p[p["series"].notna() & p.geometry.notna()].copy()
    p["year"] = pd.to_numeric(p["issueddate_yr"], errors="coerce")
    # coverage check: the layer stops recording detached single-family and 2+ unit buildings after 2018 (everything
    # new is coded townhouse); a window year with neither is a broken year
    by = p.groupby("year")["kind"].agg(lambda k: int(k.isin({"DETACHED SINGLE FAMILY DWELLING"} | MF_TYPES).sum()))
    broken = [int(y) for y in range(per["before"][0], per["after"][-1] + 1) if by.get(y, 0) == 0]
    status = "context_permit_count" if not broken else \
        (f"not_measurable: the permit layer records no detached single-family or multifamily permits in {broken[0]}-{broken[-1]} "
         "(new homes all coded townhouse from 2019; 5+ unit buildings missing, while the Census BPS shows thousands)")
    p = p[p["year"].between(per["before"][0], per["after"][-1])]
    p["pix"] = C.locate_points(p, parcels)
    p["units"] = 1.0
    p["project"] = p["pix"].astype("Int64").astype(str)
    out = []
    for series, label in (("all", "all new residential"), ("sf", "single-family"), ("mf", "multifamily")):
        q = p if series == "all" else p[p["series"] == series]

        def permits_for(a, q=q):
            r = q.assign(area=a.reindex(q["pix"]).values, el=eligible.reindex(q["pix"]).fillna(False).astype(bool).values)
            r = r[r["area"].notna() & r["el"]][["project", "area", "year", "units"]].copy()
            r["year"] = r["year"].astype(int)
            return r

        ci = C.CaseInputs(case=f"raleigh_permit_count_{series}", role="context", effective_year=eff, first_year=2000,
                          last_full_year=2025, permits=permits_for(parcels["area"]), acres=acres, homes={}, dose_table=None,
                          parking_change="overlay removes minimums (source_lead)", mandate="no (height bonus needs affordable units)",
                          dose_unit="none", measure="permits per eligible acre per year", status_override=status,
                          original_spec=(permits_for(orig), orig_acres),
                          notes=f"{label} permits (count, not homes); reform = TOD map changes with base-district changes, approved 2024")
        out.append((ci, {"rule": rule, "reform_cases": reform["ZONE_CASE"].astype(str).tolist(), "effective_year": eff,
                         "other_rezonings_in_window": int(len(other)), "acres": {k: round(v, 1) for k, v in acres.items()},
                         "permits_located_share": round(float(p["pix"].notna().mean()), 4),
                         "broken_years": broken, "detached_sf_or_mf_permits_by_year": {int(k): int(v) for k, v in by.items() if k >= 2010}}))
    return out

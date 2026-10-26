"""New York City 2003-2004 upzonings in Brooklyn (Fourth Avenue in Park Slope, Downtown Brooklyn): case adapter.

Inputs (data/raw/tod_cases/nyc/, fetched by scripts/fetch_tod_cases.py):
- dob_nb_brooklyn.csv: Department of Buildings job filings, new-building jobs in Brooklyn (document 01), with
  proposed dwelling units, the date the job was fully permitted, block and lot, and a geocoded point.
- nyzma.geojson: City Planning zoning map amendments with effective dates (official boundaries).
- bloomberg_rezonings.geojson: City Planning's list of city-initiated rezonings 2002-2013 (to keep other
  city-initiated rezonings out of the comparison areas).
- mappluto_02b.zip (March 2003, before both) and mappluto_04c.zip (late 2004, after both): tax lots with zoning,
  land use, residential units and maximum allowed FAR.
- subway_stations.geojson: subway stations (second comparison).

Rules used here (docs/tod/CASE_RESULTS.md, section New York):
- Treatment: lots (MapPLUTO 02b polygons) whose representative point is inside the rezoning's zoning map amendment
  and whose allowed residential FAR rose between 02b and 04c. In Park Slope this keeps the Fourth Avenue R8A
  blockfronts and drops the contextual downzoning that made up most of the 110 blocks.
- Lots inside the amendment that were not upzoned, and lots inside other city-initiated rezonings adopted in the
  case's window, are in no area (deviation 1 in CASE_RESULTS.md).
- Outcome: proposed dwelling units of new-building jobs, by the year the job was fully permitted, one record per
  job number. Project (for resampling) = block and lot of the job.
- Dose: allowed residential FAR by district (RESID_FAR, from the Zoning Resolution's maximum residential FAR,
  Quality Housing where higher, no inclusionary bonus), new minus old, over eligible treatment land. PLUTO's
  maxAllwFAR (largest of residential, commercial and community-facility FAR) is reported as a check.
- Existing homes: residential units on the lots in MapPLUTO 02b.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "nyc"
CRS_M = 32118  # NAD83 / New York Long Island (metres)
FIRST_YEAR, LAST_FULL_YEAR = 1991, 2025  # DOB BIS job filings; jobs filed in DOB NOW from about 2021 are not in this file

CASES = {
    "nyc_park_slope_fourth_ave_2003": {"ulurp": "030194azmk", "effective": "2003-04-30"},
    "nyc_downtown_brooklyn_2004": {"ulurp": "040171zmk", "effective": "2004-06-28"},
}

# Maximum residential FAR by residence district (Zoning Resolution 23-141/23-145 as in force 2002-2004; the higher of
# the height-factor and Quality Housing wide-street maximums, e.g. R6 3.0, R7 4.0, R8 7.2; no inclusionary bonus).
RESID_FAR = {
    "R1": 0.5, "R2": 0.5, "R2X": 0.85, "R3": 0.6, "R3A": 0.6, "R3X": 0.6, "R4": 0.9, "R4A": 0.9, "R4B": 0.9, "R5": 1.25,
    "R5A": 1.1, "R5B": 1.35, "R5D": 2.0, "R6": 3.0, "R6A": 3.0, "R6B": 2.0, "R7": 4.0, "R7A": 4.0, "R7B": 3.0,
    "R7D": 4.2, "R7X": 5.0, "R8": 7.2, "R8A": 6.02, "R8B": 4.0, "R8X": 6.02, "R9": 7.52, "R9A": 7.52, "R9X": 9.0,
    "R10": 10.0, "R10A": 10.0, "R10X": 10.0,
}
# Commercial districts: residential equivalent (ZR 35-23 / 34-112).
COMMERCIAL_EQUIV = {
    "C1-6": "R7", "C1-6A": "R7A", "C1-7": "R8", "C1-7A": "R8A", "C1-8": "R9", "C1-8A": "R9A", "C1-9": "R10",
    "C2-6": "R7", "C2-6A": "R7A", "C2-7": "R9", "C2-7A": "R9A", "C2-8": "R10",
    "C3": "R3", "C3A": "R3A", "C4-1": "R5", "C4-2": "R6", "C4-2A": "R6A", "C4-3": "R6", "C4-3A": "R6A", "C4-4": "R7",
    "C4-4A": "R7A", "C4-4D": "R8A", "C4-5": "R7", "C4-5A": "R7A", "C4-5X": "R7X", "C4-6": "R10", "C4-6A": "R10A", "C4-7": "R10",
    "C5-1": "R10", "C5-2": "R10", "C5-2A": "R10A", "C5-3": "R10", "C5-4": "R10", "C5-5": "R10",
    "C6-1": "R7", "C6-1A": "R6", "C6-2": "R8", "C6-2A": "R8A", "C6-3": "R9", "C6-3A": "R9A", "C6-3X": "R9X",
    "C6-4": "R10", "C6-4A": "R10A", "C6-4X": "R10X", "C6-4.5": "R10", "C6-5": "R10", "C6-6": "R10", "C6-7": "R10",
}


def zone_class(z: str | None) -> str | None:
    """res / com / mixed (eligible), ind (manufacturing, not eligible), park, or None."""
    if not isinstance(z, str) or not z.strip():
        return None
    s = z.upper().replace(" ", "")
    if s.startswith("PARK") or s in {"BPC", "NZS"}:
        return "park"
    if re.search(r"[/(]R\d", s) or (s.startswith("R") and re.search(r"\(M", s)):
        return "mixed"
    if s.startswith("R"):
        return "res"
    if s.startswith("C8") or s.startswith("C7"):
        return "com"  # commercial, though housing is not allowed (residential FAR 0)
    if s.startswith("C"):
        return "com"
    if s.startswith("M"):
        return "ind"
    return None


def resid_far(z: str | None) -> float:
    """Maximum residential FAR of a district string from PLUTO ('R6', 'C6-1', 'M1-2/R6A', 'R6(M1-2)')."""
    if not isinstance(z, str) or not z.strip():
        return float("nan")
    s = z.upper().replace(" ", "")
    m = re.search(r"(R\d+[A-Z]?)(?:-\d)?", s)
    if m and (s.startswith("R") or "/R" in s or "(R" in s):
        r = m.group(1)
        return RESID_FAR.get(r, RESID_FAR.get(r[:-1], float("nan")) if r[-1].isalpha() else float("nan"))
    if s.startswith("C"):
        base = re.match(r"(C\d(?:-\d(?:\.\d)?[A-Z]?)?)", s).group(1)
        eq = COMMERCIAL_EQUIV.get(base)
        if eq:
            return RESID_FAR[eq]
        return 0.0 if base.startswith(("C7", "C8")) else float("nan")
    if s.startswith("M"):
        return 0.0
    return float("nan")


# --------------------------------------------------------------------------- loading

_lots_cache: dict = {}


def load_lots():
    import geopandas as gpd
    if "lots" in _lots_cache:
        return _lots_cache["lots"]
    a = gpd.read_file(f"zip://{DIR / 'mappluto_02b.zip'}!MapPLUTO_02B/Brooklyn/bkmappluto.shp",
                      columns=["block", "lot", "zoneDist1", "landUse2", "unitsRes", "maxAllwFAR", "lotArea"]).to_crs(CRS_M)
    a = a[a.geometry.notna() & ~a.geometry.is_empty].reset_index(drop=True)
    b = gpd.read_file(f"zip://{DIR / 'mappluto_04c.zip'}!MapPLUTO_04C/Brooklyn/bkmappluto.shp",
                      columns=["ZONEDIST1", "MAXALLWFAR"]).to_crs(CRS_M)
    pts = gpd.GeoDataFrame(geometry=a.geometry.representative_point(), crs=CRS_M)
    j = gpd.sjoin(pts, b, how="left", predicate="within")
    j = j[~j.index.duplicated()].reindex(pts.index)
    a["zone_after"] = j["ZONEDIST1"].values
    a["maxfar_after"] = pd.to_numeric(j["MAXALLWFAR"], errors="coerce").values
    a["acres"] = a.geometry.area / C.SQM_PER_ACRE
    a["far_before"] = a["zoneDist1"].map(resid_far)
    a["far_after"] = a["zone_after"].map(resid_far)
    a["zclass"] = a["zoneDist1"].map(zone_class)
    a["pt"] = pts.geometry
    _lots_cache["lots"] = a
    return a


def load_jobs() -> pd.DataFrame:
    d = pd.read_csv(DIR / "dob_nb_brooklyn.csv", dtype=str)
    d = d.drop_duplicates("job__")
    d["units"] = pd.to_numeric(d["proposed_dwelling_units"], errors="coerce").fillna(0)
    d["year"] = pd.to_numeric(d["fully_permitted"].str[-4:], errors="coerce")
    d = d[(d["units"] > 0) & d["year"].notna()]
    d["lat"] = pd.to_numeric(d["gis_latitude"], errors="coerce")
    d["lon"] = pd.to_numeric(d["gis_longitude"], errors="coerce")
    d["project"] = d["block"].astype(str) + "-" + d["lot"].astype(str)
    return d.dropna(subset=["lat", "lon"])


def locate_jobs(jg, lots, max_m: float = 40.0) -> pd.Series:
    """Index of the 02b lot for each job: same block and lot number first; otherwise the lot containing or nearest
    to the job's geocoded point (DOB points sit on the street frontage), within max_m metres."""
    import geopandas as gpd
    key = lots["block"].astype(int).astype(str) + "-" + lots["lot"].astype(int).astype(str)
    lut = pd.Series(lots.index, index=key)
    lut = lut[~lut.index.duplicated()]
    jk = pd.to_numeric(jg["block"], errors="coerce").fillna(-1).astype(int).astype(str) + "-" + \
        pd.to_numeric(jg["lot"], errors="coerce").fillna(-1).astype(int).astype(str)
    ix = jk.map(lut)
    miss = ix.isna()
    if miss.any():
        ix.loc[miss] = C.locate_points(jg.loc[miss], lots, max_m).values
    return ix


def build(case: str) -> tuple[C.CaseInputs, dict]:
    import geopandas as gpd
    spec = CASES[case]
    eff = pd.Timestamp(spec["effective"])
    eyear = eff.year
    lots = load_lots().copy()
    zma = gpd.read_file(DIR / "nyzma.geojson").to_crs(CRS_M)
    poly = zma[zma["ULURPNO"].astype(str).str.lower() == spec["ulurp"]].geometry.union_all()
    pts = gpd.GeoSeries(lots["pt"], crs=CRS_M)
    in_zma = pts.within(poly)
    up = lots["far_after"] > lots["far_before"] + 1e-9
    treated = in_zma & up
    # other city-initiated rezonings adopted in this case's window (deviation 1)
    bl = gpd.read_file(DIR / "bloomberg_rezonings.geojson").to_crs(CRS_M)
    bl["adopted"] = pd.to_datetime(bl["Adopted"], unit="ms", errors="coerce")
    per = C.period_years(eyear, FIRST_YEAR, LAST_FULL_YEAR)
    lo, hi = pd.Timestamp(f"{per['before'][0]}-01-01"), pd.Timestamp(f"{per['after'][-1]}-12-31")
    other = bl[(bl["ULURPNO"].astype(str).str.lower() != spec["ulurp"]) & bl["adopted"].between(lo, hi)]
    other_poly = other.geometry.union_all() if len(other) else None
    excluded = (in_zma & ~treated) | (pts.within(other_poly) if other_poly is not None else False)
    stations = gpd.read_file(DIR / "subway_stations.geojson").to_crs(CRS_M)
    stations = stations[stations["Borough"].astype(str) == "3"].geometry
    if other_poly is not None:
        stations = stations[stations.distance(other_poly) > C.HALF_MILE_M]
    lots_for_areas = lots.copy()
    area = C.assign_areas(lots_for_areas, treated, in_city=~excluded | treated, stations=stations)
    area[excluded & ~treated] = None
    lots["area"] = area
    lu = lots["landUse2"].astype(str).str.zfill(2)
    lots["eligible"] = lots["zclass"].isin(["res", "com", "mixed"]) & ~lu.isin(["08", "09"])
    el = lots[lots["area"].notna() & lots["eligible"]].copy()
    acres = el.groupby("area")["acres"].sum().to_dict()
    homes = el.groupby("area")["unitsRes"].sum().astype(float).to_dict()

    jobs = load_jobs()
    jg = gpd.GeoDataFrame(jobs, geometry=gpd.points_from_xy(jobs["lon"], jobs["lat"]), crs=4326).to_crs(CRS_M)
    jg["lot_ix"] = locate_jobs(jg, lots)
    jg["area"] = lots["area"].reindex(jg["lot_ix"]).values
    jg["eligible"] = lots["eligible"].reindex(jg["lot_ix"]).fillna(False).values
    permits = jg[jg["area"].notna() & jg["eligible"].astype(bool)][["project", "area", "year", "units"]].copy()
    permits["year"] = permits["year"].astype(int)

    tr = el[el["area"] == C.TREAT]
    dose_table = tr.rename(columns={"far_before": "old_far", "far_after": "new_far"})[["acres", "old_far", "new_far"]]
    pluto_dose = C.dose(tr.assign(o=pd.to_numeric(tr["maxAllwFAR"], errors="coerce"), n=tr["maxfar_after"]), old="o", new="n")

    # literal-plan check: comparison without excluding other rezonings or non-upzoned lots in the amendment
    lit_area = C.assign_areas(lots, treated, stations=None)
    lit = lots.assign(area=lit_area)
    lit_el = lit[lit["area"].isin([C.TREAT, C.COMP]) & lit["eligible"]]
    jl = jg.assign(area=lit["area"].reindex(jg["lot_ix"]).values)
    jl = jl[jl["area"].isin([C.TREAT, C.COMP]) & jg["eligible"].astype(bool)]
    lit_did = C.did(jl[["project", "area", "year", "units"]].astype({"year": int}), lit_el.groupby("area")["acres"].sum().to_dict(),
                    per["before"], per["after"])["did"]

    diag = {
        "treated_lots": int(treated.sum()), "lots_in_amendment": int(in_zma.sum()),
        "eligible_lots_by_area": el.groupby("area").size().to_dict(),
        "zoning_before_treated": lots.loc[treated, "zoneDist1"].value_counts().head(10).to_dict(),
        "zoning_after_treated": lots.loc[treated, "zone_after"].value_counts().head(10).to_dict(),
        "dose_pluto_maxallwfar": round(pluto_dose, 3),
        "other_rezonings_excluded": sorted(other["RezoneArea"].astype(str).unique().tolist()),
        "second_comparison_stations": int(len(C.stations_not_upzoned(stations, lots.loc[treated].geometry.union_all()))),
        "literal_plan_did": round(lit_did, 4),
        "dose_missing_far_lots": int(dose_table[["old_far", "new_far"]].isna().any(axis=1).sum()),
    }
    role = "fit"
    ci = C.CaseInputs(case=case, role=role, effective_year=eyear, first_year=FIRST_YEAR, last_full_year=LAST_FULL_YEAR,
                      permits=permits, acres=acres, homes=homes, dose_table=dose_table,
                      parking_change="none (minimums kept)", mandate="no",
                      notes="dose = residential FAR by district (Zoning Resolution); PLUTO maxAllwFAR dose in CASE_RESULTS.md")
    return ci, diag

"""Chicago transit-served location ordinances, 2013 and 2015: HELD-OUT case adapter.

The case gets its own estimate only. It never enters fit_set(), the pooled ramp or any comparison of designs
(docs/tod/CASE_ANALYSIS_PLAN.md section 1.3; AQ-047 item 4).

Inputs (data/raw/tod_cases/chicago/, fetched by scripts/fetch_tod_cases.py):
- permits_new_construction.csv: City of Chicago building permits of type "PERMIT - NEW CONSTRUCTION", 2006 onward.
  There is no unit field; units are read from the work description (parse_units).
- zoning_nov2012.zip: zoning districts as of November 2012 (before both ordinances).
- parcels.geojson: Cook County 2021 parcel polygons in Chicago, with assessor class.
- rail_stops.geojson: CTA rail and Metra stops (BTS National Transit Map).
- ../census_2010_blocks/tabblock2010_17_pophu.zip.

Rules:
- Effective year 2015 (ordinance of 24 September 2015, which widened the 2013 rules from 600 ft to 1,320 ft and
  added the larger bonuses). The 2013 ordinance falls in the before years; this biases the estimate toward zero.
- Treatment: parcels zoned B or C with a -3 or -5 bulk suffix in November 2012 whose representative point lies
  within 1,320 ft of a CTA or Metra stop in Chicago. The 2,640 ft distance on Pedestrian Streets is not modelled.
- Dose: +0.5 FAR on -3 districts (3.0 to 3.5) and +1.0 on -5 districts (5.0 to 6.0) without affordable units
  (source_lead, CASE_INVENTORY.md "+0.5 to +1.0").
- Staged permits (foundation, partial superstructure, full building) for one building are kept once: same address
  point (within 1 m), same unit count, issued within about 18 months (dedupe_staged). Project (for resampling) =
  the address point.
- Areas: the uniform rule (cases.uniform_areas). Zoning changes in the window are read by comparing the November
  2012 map with today's map (zoning_current.geojson), which also catches changes after 2020.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "chicago"
CRS_M = 26971  # NAD83 / Illinois East (metres)
EFFECTIVE_YEAR = 2015
FIRST_YEAR, LAST_FULL_YEAR = 2006, 2025
TOD_RADIUS_M = 1320 * 0.3048
WORDS = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10,
         "ELEVEN": 11, "TWELVE": 12, "SINGLE": 1}
UNIT_RE = re.compile(r"\b(\d{1,4}|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE)\s*[-]?\s*\(?\s*"
                     r"(?:NEW\s+)?(?:RESIDENTIAL\s+|DWELLING\s+|APARTMENT\s+|APT\.?\s+|CONDO(?:MINIUM)?\s+|RENTAL\s+|FAMILY\s+)?"
                     r"(?:DWELLING\s+UNITS?|UNITS?\b|D\.\s?U\.?|DU'?S\b|DUS?\b)")
SINGLE_RE = re.compile(r"SINGLE[\s-]+FAMILY|\bSFR\b|ONE[\s-]+FAMILY")
TWO_RE = re.compile(r"\bTWO[\s-]+FLAT|\b2[\s-]+FLAT|DUPLEX|TWO[\s-]+FAMILY")
THREE_RE = re.compile(r"\bTHREE[\s-]+FLAT|\b3[\s-]+FLAT")
EXCLUDE_RE = re.compile(r"REVISION|REINST|\bTENT\b|CANOPY|STAGE\b")
UNIT_LETTERS_RE = re.compile(r"\s*\(?\s*(?:[A-Z]|\d{1,2})\s*(?:&|,|AND\b)")  # 'UNITS A & B': an address, not a count
MAX_UNITS = 1500
STAGE_WINDOW_DAYS = 548  # about 18 months: foundation to full-building permits of one building
RES_FAR = {"RS-1": 0.5, "RS-2": 0.65, "RS-3": 0.9, "RT-3.5": 1.05, "RT-4": 1.2, "RT-4A": 1.5, "RM-4.5": 1.7, "RM-5": 2.0,
           "RM-5.5": 2.5, "RM-6": 4.4, "RM-6.5": 6.6}
BC_FAR = {"1": 1.2, "1.5": 1.5, "2": 2.2, "3": 3.0, "5": 5.0}


def parse_units(desc: str | float) -> int:
    """Housing units in a new-construction permit's work description (0 when none can be read)."""
    if not isinstance(desc, str):
        return 0
    s = desc.upper()
    if EXCLUDE_RE.search(s):
        return 0
    for m in UNIT_RE.finditer(s):
        if UNIT_LETTERS_RE.match(s, m.end()):
            continue
        v = m.group(1)
        n = WORDS[v] if v in WORDS else int(v)
        if 0 < n <= MAX_UNITS:
            return n
    if THREE_RE.search(s):
        return 3
    if TWO_RE.search(s):
        return 2
    if SINGLE_RE.search(s):
        return 1
    return 0


def dedupe_staged(p: pd.DataFrame, x: str = "x", y: str = "y") -> pd.DataFrame:
    """One record per building: staged permits (foundation, partial superstructure, full building) for one building
    carry the same unit count at the same geocoded address point. Permits at the same point (within 1 m), with the
    same unit count, issued within STAGE_WINDOW_DAYS of the group's first permit, are one building: the first is kept.
    Separate homes on neighbouring lots have their own address points and are never merged."""
    p = p.copy()
    p["_d"] = pd.to_datetime(p["issue_date"].str[:10], errors="coerce")
    p["_k"] = p[x].round().astype(int).astype(str) + "_" + p[y].round().astype(int).astype(str) + "_" + p["units"].astype(str)
    p = p.sort_values(["_k", "_d"])
    keep, last_key, first_date = [], None, None
    for k, d in zip(p["_k"], p["_d"]):
        if k != last_key or pd.isna(d) or pd.isna(first_date) or (d - first_date).days > STAGE_WINDOW_DAYS:
            keep.append(True)
            last_key, first_date = k, d
        else:
            keep.append(False)
    return p[keep].drop(columns=["_d", "_k"]).sort_values("issue_date")


def resid_far(z: str | None) -> float:
    """Allowed residential FAR by Chicago district (Chicago Zoning Ordinance bulk tables; source_lead)."""
    if not isinstance(z, str):
        return float("nan")
    s = z.upper().strip()
    if s in RES_FAR:
        return RES_FAR[s]
    m = re.match(r"^(B[123]|C[123])-(\d(?:\.5)?)$", s)
    if m:
        return BC_FAR.get(m.group(2), float("nan"))
    m = re.match(r"^(DX|DC|DR)-(\d+)$", s)
    if m:
        return float(m.group(2))
    if s.startswith(("M", "PMD", "DS")):
        return 0.0
    return float("nan")


def zone_class(z: str | None) -> str | None:
    if not isinstance(z, str):
        return None
    s = z.upper().strip()
    if s.startswith(("RS", "RT", "RM")):
        return "res"
    if s.startswith(("B", "C")):
        return "com"
    if s.startswith(("DX", "DC", "DR", "DS")):
        return "mixed"
    if s.startswith(("M", "PMD")):
        return "ind"
    if s.startswith("POS"):
        return "park"
    if s.startswith("PD"):
        return "pd"
    return None


def tod_far_gain(z: str | None) -> float:
    if not isinstance(z, str):
        return float("nan")
    s = z.upper().strip()
    if re.match(r"^[BC]\d-3$", s):
        return 0.5
    if re.match(r"^[BC]\d-5$", s):
        return 1.0
    return float("nan")


def build() -> tuple[C.CaseInputs, dict]:
    import geopandas as gpd
    parcels = gpd.read_file(DIR / "parcels.geojson").to_crs(CRS_M)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].drop_duplicates("pin10").reset_index(drop=True)
    parcels = parcels[parcels["municipality"].astype(str).str.upper().str.contains("CHICAGO")].reset_index(drop=True)
    parcels["acres"] = parcels.geometry.area / C.SQM_PER_ACRE
    pts = gpd.GeoDataFrame(geometry=parcels.geometry.representative_point(), crs=CRS_M)
    z = gpd.read_file(f"zip://{DIR / 'zoning_nov2012.zip'}").to_crs(CRS_M)
    zcol = next(c for c in z.columns if c.upper() in ("ZONE_CLASS", "ZONING", "ZONE_TYPE_CLASS", "ZONING_CLA", "ZONE_CLA"))
    j = gpd.sjoin(pts, z[[zcol, "geometry"]], how="left", predicate="within")
    parcels["zoning_before"] = j[~j.index.duplicated()].reindex(pts.index)[zcol].values
    stops = gpd.read_file(DIR / "rail_stops.geojson").to_crs(CRS_M)
    city = parcels.union_all().convex_hull
    stops = stops[stops.geometry.within(city)]
    near = pts.geometry.within(stops.geometry.buffer(TOD_RADIUS_M).union_all())
    gain = parcels["zoning_before"].map(tod_far_gain)
    in_reform = near & gain.notna()
    parcels["treated"] = in_reform
    zc = gpd.read_file(DIR / "zoning_current.geojson").to_crs(CRS_M)
    k = gpd.sjoin(pts, zc[["zone_class", "geometry"]], how="left", predicate="within")
    parcels["zoning_now"] = k[~k.index.duplicated()].reindex(pts.index)["zone_class"].values
    parcels["far_before"] = parcels["zoning_before"].map(resid_far)
    parcels["far_after"] = parcels["far_before"] + gain.where(in_reform, 0.0)
    f_now = parcels["zoning_now"].map(resid_far)
    known = parcels["far_before"].notna() & f_now.notna()
    missing = parcels["zoning_before"].isna() | parcels["zoning_now"].isna()
    changed = ~missing & ((known & ((parcels["far_before"] - f_now).abs() > 1e-9)) |
                          (~known & (parcels["zoning_before"].astype(str).str.upper() != parcels["zoning_now"].astype(str).str.upper())))
    parcels["zclass"] = parcels["zoning_before"].map(zone_class)
    cls = parcels["assessorbldgclass"].astype(str).str.upper()
    parcels["eligible"] = parcels["zclass"].isin(["res", "com", "mixed"]) & ~cls.str.startswith(("EX", "RR"))
    parcels["area"], rule = C.uniform_areas(parcels, in_reform, in_reform, parcels["far_before"], parcels["far_after"],
                                            pd.Series(True, index=parcels.index), changed, parcels["eligible"],
                                            stations=stops.geometry)
    orig_area = C.assign_areas(parcels, in_reform, stations=stops.geometry)
    el = parcels[parcels["area"].notna() & parcels["eligible"]]
    acres = el.groupby("area")["acres"].sum().to_dict()

    p = pd.read_csv(DIR / "permits_new_construction.csv", dtype=str).drop_duplicates("permit_")
    p["units"] = p["work_description"].map(parse_units)
    p["year"] = pd.to_numeric(p["issue_date"].str[:4], errors="coerce")
    p["lat"] = pd.to_numeric(p["latitude"], errors="coerce")
    p["lon"] = pd.to_numeric(p["longitude"], errors="coerce")
    p = p[(p["units"] > 0) & p["year"].notna()].dropna(subset=["lat", "lon"])
    pg = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p["lon"], p["lat"]), crs=4326).to_crs(CRS_M)
    pg["x"], pg["y"] = pg.geometry.x, pg.geometry.y
    n_before_dedupe = len(pg)
    pg = dedupe_staged(pg)
    pg["project"] = pg["x"].round().astype(int).astype(str) + "_" + pg["y"].round().astype(int).astype(str)
    pg["pix"] = C.locate_points(pg, parcels)
    pg["eligible"] = parcels["eligible"].reindex(pg["pix"]).fillna(False).astype(bool).values

    def permits_for(area: pd.Series) -> pd.DataFrame:
        q = pg.assign(area=area.reindex(pg["pix"]).values)
        q = q[q["area"].notna() & q["eligible"]][["project", "area", "year", "units"]].copy()
        q["year"] = q["year"].astype(int)
        return q

    permits = permits_for(parcels["area"])
    original = (permits_for(orig_area), parcels[orig_area.notna() & parcels["eligible"]].groupby(orig_area)["acres"].sum().to_dict())

    tr = el[el["area"] == C.TREAT]
    dose_table = pd.DataFrame({"acres": tr["acres"], "old_far": tr["far_before"], "new_far": tr["far_after"]})

    homes = {}
    bz = RAW / "tod_cases" / "census_2010_blocks" / "tabblock2010_17_pophu.zip"
    if bz.exists():
        bbox = tuple(gpd.GeoSeries([el.union_all().envelope], crs=CRS_M).to_crs(4269).total_bounds)
        b = gpd.read_file(bz, bbox=bbox).to_crs(CRS_M)
        b = gpd.GeoDataFrame({"homes": b["HOUSING10"]}, geometry=b.geometry.representative_point(), crs=CRS_M)
        homes = C.homes_by_area(b, el[["area", "geometry"]])
    allp = pd.read_csv(DIR / "permits_new_construction.csv", dtype=str).drop_duplicates("permit_")
    allp["units"] = allp["work_description"].map(parse_units)
    allp["year"] = allp["issue_date"].str[:4]
    diag = {"rule": rule, "zoning_column": zcol, "treated_parcels": int((parcels["area"] == C.TREAT).sum()),
            "reform_parcels": int(in_reform.sum()),
            "treated_zoning": tr["zoning_before"].value_counts().head(12).to_dict(),
            "parcels_changed_nov2012_to_now": int(changed.sum()),
            "stops_in_city": int(len(stops)),
            "permits_with_units_share": round(float((allp["units"] > 0).mean()), 4),
            "citywide_units_parsed_by_year": allp.groupby("year")["units"].sum().to_dict(),
            "permits_located_share": round(float(pg["pix"].notna().mean()), 4),
            "staged_permits_dropped": int(n_before_dedupe - len(pg))}
    ci = C.CaseInputs(case="chicago_tod_2013_2015", role="heldout", effective_year=EFFECTIVE_YEAR, first_year=FIRST_YEAR,
                      last_full_year=LAST_FULL_YEAR, permits=permits, acres=acres, homes=homes, dose_table=dose_table,
                      parking_change="reduced (up to 50% in 2013; residential minimums removable in 2015)",
                      mandate="no for the base bonus (affordable units needed for the top FAR)",
                      notes="units parsed from work descriptions; zoning changes read against today's map (to 2026)",
                      original_spec=original)
    return ci, diag

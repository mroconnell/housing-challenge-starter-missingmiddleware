"""Charlotte 2019 transit-oriented districts (Petition 2019-102, approved 18 November 2019): case adapter.

Inputs (data/raw/tod_cases/charlotte/, fetched by scripts/fetch_tod_cases.py):
- permits.csv: Mecklenburg County building permits (1990-2026) with issue date, Census use code, units, point.
- rezoning_history.geojson: City rezoning petitions with ExistingZoning and RequestedZoning.
- pre_udo_zoning.geojson: zoning in force just before the Unified Development Ordinance (June 2023).
- parcels.geojson: parcels near the corridor and rail stops, with assessor land use.
- rail_stops.geojson: CATS LYNX Blue Line and CityLYNX Gold Line stops (BTS National Transit Map).
- ../census_2010_blocks/tabblock2010_37_pophu.zip: 2010 housing units by block.

Rules used here (docs/tod/CASE_RESULTS.md, section Charlotte):
- Treatment: parcels whose representative point lies in a Petition 2019-102 polygon. Zoning before = that
  polygon's ExistingZoning, zoning after = its RequestedZoning.
- Zoning before for other parcels: the Pre-UDO zoning layer, overridden by the ExistingZoning of any rezoning
  petition approved after 18 November 2019 (so later private rezonings do not change "before").
- Outcome: Census use codes 101-105 and 115 (new one-family to 5+ unit buildings, the Building Permits Survey
  classes), units from `numunits`; placeholder 1-unit permits for garages, amenity areas and similar are dropped.
- Project (for resampling): the permit's parcel number (several per-floor permits of one building are one project).
- Areas: the uniform rule of CASE_ANALYSIS_PLAN.md section 7 (cases.uniform_areas), with height limits as the
  level because Charlotte's districts have no FAR. Lots in rezoning petitions approved in the window that changed
  the base district (other than 2019-102) are in no area.
- Dose: added height limit in feet over eligible treatment land. Charlotte's code gives no FAR for these districts
  and no Charlotte-specific conversion was found, so the case has an effect per added foot, not per added FAR, and
  stays out of per-FAR pooling.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "charlotte"
CRS_M = 32119  # NAD83 / North Carolina (metres)
EFFECTIVE = pd.Timestamp("2019-11-18")
EFFECTIVE_YEAR = 2019
UDO_DATE = pd.Timestamp("2023-06-01")  # Unified Development Ordinance in force; the Pre-UDO layer is the map just before
FIRST_YEAR, LAST_FULL_YEAR = 1990, 2025
RES_CODES = ("101", "102", "103", "104", "105", "115")
PLACEHOLDER = re.compile(r"\bS/C\b|garage|amenit|club|leasing|pool|parking|deck|mail|maint|trash|compactor|cabana|fitness|shell|core", re.I)

# Pre-2019 Charlotte base districts: (class, height limit in ft, homes per acre cap or None).
# class: res / mixed / com (eligible) or ind / inst (not eligible). Heights before are about 40 ft in most base
# districts (source_lead in CASE_INVENTORY.md). Residential density in business and office districts follows
# R-22MF. Districts that do not allow housing get cap 0.
DISTRICTS: dict[str, tuple[str, float | None, float | None]] = {
    "R-3": ("res", 40, 3), "R-4": ("res", 40, 4), "R-5": ("res", 40, 5), "R-6": ("res", 40, 6), "R-8": ("res", 40, 8),
    "R-8MF": ("res", 40, 8), "R-9MF": ("res", 40, 9), "R-15MF": ("res", 40, 15), "R-12": ("res", 40, 12), "R-12MF": ("res", 40, 12), "R-17MF": ("res", 40, 17), "R-20MF": ("res", 40, 20),
    "R-22MF": ("res", 40, 22), "R-43MF": ("res", 40, 43), "R-MH": ("res", 40, 6),
    "UR-1": ("res", 40, 8), "UR-2": ("res", 40, 22), "UR-3": ("res", 40, 43), "UR-C": ("mixed", 40, None),
    "MX-1": ("res", 40, 4), "MX-2": ("res", 40, 6), "MX-3": ("res", 40, 8),
    "B-1": ("com", 40, 22), "B-2": ("com", 40, 22), "B-D": ("com", 40, 0), "BP": ("com", 40, 0),
    "O-1": ("com", 40, 22), "O-2": ("com", 40, 22), "O-3": ("com", 40, 22), "O-6": ("com", 40, 6), "O-15": ("com", 40, 15),
    "NS": ("com", 40, None), "CC": ("com", 40, None), "B-29": ("com", 40, 22),
    "RE-1": ("com", 40, 0), "RE-2": ("com", 40, 0), "RE-3": ("com", 40, 0),
    "MUDD": ("mixed", 120, None), "UMUD": ("mixed", None, None),
    "TOD-M": ("mixed", 120, None), "TOD-R": ("mixed", 120, None), "TOD-E": ("mixed", 120, None), "TOD-MO": ("mixed", 120, None),
    "TOD-CC": ("mixed", 90, None), "TOD-UC": ("mixed", 130, None), "TOD-NC": ("mixed", 75, None), "TOD-TR": ("mixed", 50, None),
    "PED": ("mixed", 40, None),
    "I-1": ("ind", 40, 0), "I-2": ("ind", 40, 0), "INST": ("inst", 40, 0),
}
AFTER_HEIGHT = {"TOD-UC": 130, "TOD-NC": 75, "TOD-CC": 90, "TOD-TR": 50, "TOD-R": 50}  # 'TOD-R' in one polygon = TOD-TR
# Assessor land uses that are not developable for housing (parks, cemeteries, institutions, water, utilities, roads).
NOT_ELIGIBLE_LANDUSE = re.compile(r"park|cemet|church|school|college|univers|hospital|government|govt|public|water|"
                                  r"utilit|right.of.way|road|railroad|common area|exempt|religious|library", re.I)


def base_district(code: str | None) -> str | None:
    """Normalise a Charlotte zoning code to its base district: 'B-1(CD)' -> 'B-1', 'MUDD-O' -> 'MUDD'."""
    if code is None or (isinstance(code, float) and np.isnan(code)):
        return None
    s = str(code).upper().strip()
    s = re.sub(r"\(.*?\)", "", s).strip()
    s = re.sub(r"\s+", "", s)
    if s.startswith("TOD-"):
        m = re.match(r"TOD-(UC|NC|CC|TR|MO|M|R|E)", s)
        return f"TOD-{m.group(1)}" if m else s
    s = re.sub(r"^([A-Z]+)(\d)", r"\1-\2", s)  # 'B1' -> 'B-1'
    m = re.match(r"^(R-\d+MF|R-MH|R-\d+|UR-[C\d]|MX-\d|B-D|B-\d+|BP|O-\d+|NS|CC|RE-\d|MUDD|UMUD|I-\d|INST|PED)", s)
    if m:
        return m.group(1)
    return s


def height_before(code: str | None) -> float:
    """Height limit in feet of the district before (inf for no limit, NaN when unknown)."""
    d = DISTRICTS.get(base_district(code) or "")
    if d is None:
        return float("nan")
    return float("inf") if d[1] is None else float(d[1])


def capped_before(code: str | None) -> bool:
    """True when the district before had a homes-per-acre cap (or did not allow housing)."""
    d = DISTRICTS.get(base_district(code) or "")
    return True if d is None else d[2] is not None


def height_after(code: str | None) -> float:
    h = AFTER_HEIGHT.get(base_district(code) or "")
    return float(h) if h else float("nan")


def zoning_class(code: str | None) -> str | None:
    d = DISTRICTS.get(base_district(code) or "")
    return d[0] if d else None


# --------------------------------------------------------------------------- loading

def load_permits() -> pd.DataFrame:
    cols = ["X", "Y", "permitnum", "projname", "projadd", "parcelnum", "numunits", "usdcdesc", "issuedate", "worktype", "typeofbldg"]
    p = pd.read_csv(DIR / "permits.csv", usecols=cols, low_memory=False, dtype={"parcelnum": str, "permitnum": str})
    p = p.drop_duplicates("permitnum")
    p["code"] = p["usdcdesc"].astype(str).str[:3]
    p = p[p["code"].isin(RES_CODES)]
    p = p[p["worktype"].isna() | (p["worktype"] == "New")]
    p = p[~p["typeofbldg"].isin(["Existing Bldg", "Addition to existing Bldg"])]
    p["units"] = pd.to_numeric(p["numunits"], errors="coerce").fillna(0)
    p = p[~(p["projname"].astype(str).str.contains(PLACEHOLDER) & (p["units"] <= 1) & (p["code"].isin(["105", "115"])))]
    p = p[p["units"] > 0]
    p["year"] = pd.to_numeric(p["issuedate"].astype(str).str[:4], errors="coerce")
    p["project"] = p["parcelnum"].fillna(p["projadd"]).astype(str)
    return p.dropna(subset=["X", "Y", "year"])


def build(blocks_zip: Path | None = None) -> tuple[C.CaseInputs, dict]:
    import geopandas as gpd

    rz = gpd.read_file(DIR / "rezoning_history.geojson").to_crs(CRS_M)
    rz["approved"] = pd.to_datetime(rz["Approved"], unit="ms", errors="coerce")
    treat_poly = rz[rz["Petition"].astype(str).str.startswith("2019-102")][["ExistingZoning", "RequestedZoning", "geometry"]]
    later = rz[(rz["approved"] > EFFECTIVE) & (rz["approved"] < UDO_DATE) & (rz["Status"].astype(str).str.startswith("App")) &
               ~rz["Petition"].astype(str).str.startswith("2019-102")][["ExistingZoning", "approved", "geometry"]]
    pre = gpd.read_file(DIR / "pre_udo_zoning.geojson").to_crs(CRS_M)[["ZoneDes", "geometry"]]
    parcels = gpd.read_file(DIR / "parcels.geojson").to_crs(CRS_M)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].copy()
    parcels = parcels.drop_duplicates("parcelid").reset_index(drop=True)
    parcels["acres"] = parcels.geometry.area / C.SQM_PER_ACRE
    pts = gpd.GeoDataFrame(parcels[["parcelid"]], geometry=parcels.geometry.representative_point(), crs=CRS_M)

    def first_hit(polys, cols):
        j = gpd.sjoin(pts, polys, how="left", predicate="within")
        if "approved" in j.columns:
            j = j.sort_values("approved")
        j = j[~j.index.duplicated(keep="first")]
        return j.reindex(pts.index)[cols]

    t = first_hit(treat_poly, ["ExistingZoning", "RequestedZoning"])
    lz = first_hit(later, ["ExistingZoning"])
    pz = first_hit(pre, ["ZoneDes"])
    parcels["treated"] = t["RequestedZoning"].notna().values
    parcels["zoning_before"] = np.where(parcels["treated"], t["ExistingZoning"],
                                        np.where(lz["ExistingZoning"].notna(), lz["ExistingZoning"], pz["ZoneDes"]))
    parcels["zoning_after"] = np.where(parcels["treated"], t["RequestedZoning"], None)
    parcels["zclass"] = parcels["zoning_before"].map(zoning_class)
    city = gpd.read_file(DIR / "council_districts.geojson").to_crs(CRS_M).union_all()
    in_city = parcels.geometry.representative_point().within(city) | parcels["treated"]
    stations = gpd.read_file(DIR / "rail_stops.geojson").to_crs(CRS_M).geometry
    lu = parcels["landuse_description"].astype(str)
    parcels["eligible"] = parcels["zclass"].isin(["res", "mixed", "com"]) & ~lu.str.contains(NOT_ELIGIBLE_LANDUSE)
    per = C.period_years(EFFECTIVE_YEAR, FIRST_YEAR, LAST_FULL_YEAR)

    # uniform rule (CASE_ANALYSIS_PLAN.md section 7): levels are height limits, since Charlotte's districts have no FAR
    parcels["h_before"] = parcels["zoning_before"].map(height_before)
    parcels["h_after"] = parcels["zoning_after"].map(height_after)
    parcels["capped"] = parcels["zoning_before"].map(capped_before)
    rose = parcels["treated"] & ((parcels["h_after"] > parcels["h_before"]) | parcels["capped"])
    win = rz[rz["approved"].between(pd.Timestamp(f"{per['before'][0]}-01-01"), pd.Timestamp(f"{per['after'][-1]}-12-31"))
             & rz["Status"].astype(str).str.startswith("App") & ~rz["Petition"].astype(str).str.startswith("2019-102")]
    win = win[win["ExistingZoning"].map(base_district) != win["RequestedZoning"].map(base_district)]
    changed = pts.geometry.within(win.geometry.union_all()) if len(win) else pd.Series(False, index=parcels.index)
    # lot plan item 29: what each in-window petition rezoned the lot to (TOD district = take-up of the reform)
    if len(win):
        jw = gpd.sjoin(pts, win[["RequestedZoning", "approved", "geometry"]], how="left", predicate="within").sort_values("approved")
        jw = jw[~jw.index.duplicated(keep="first")].reindex(pts.index)
        parcels["changed_to"] = jw["RequestedZoning"].values
    else:
        parcels["changed_to"] = None
    parcels["uptake"] = changed & parcels["changed_to"].map(lambda z: str(base_district(z) or "").startswith("TOD-"))
    parcels["area"], rule = C.uniform_areas(parcels, parcels["treated"], rose, parcels["h_before"], parcels["h_after"],
                                            ~parcels["capped"], changed, parcels["eligible"], in_city=in_city, stations=stations)
    el = parcels[parcels["area"].notna() & parcels["eligible"]].copy()
    acres = el.groupby("area")["acres"].sum().to_dict()

    # permits located to parcels
    pr = load_permits()
    pg = gpd.GeoDataFrame(pr, geometry=gpd.points_from_xy(pr["X"], pr["Y"]), crs=2264).to_crs(CRS_M)
    near = pg[pg.geometry.within(parcels.union_all().buffer(50))].copy()
    near["pix"] = C.locate_points(near, parcels)
    near["eligible"] = parcels["eligible"].reindex(near["pix"]).fillna(False).astype(bool).values

    def permits_for(area: pd.Series) -> pd.DataFrame:
        a = area.reindex(near["pix"]).values
        q = near.assign(area=a)
        q = q[q["area"].notna() & q["eligible"]][["project", "area", "year", "units"]].copy()
        q["year"] = q["year"].astype(int)
        return q

    permits = permits_for(parcels["area"])

    # original area rule (sensitivity): whole petition area against its 1/4-mile ring
    orig_area = C.assign_areas(parcels, parcels["treated"], in_city=in_city, stations=stations)
    orig_acres = parcels[orig_area.notna() & parcels["eligible"]].groupby(orig_area)["acres"].sum().to_dict()
    original = (permits_for(orig_area), orig_acres)

    # dose: added height in feet over eligible treatment land (the removed homes-per-acre caps are not in it)
    tr = el[el["area"] == C.TREAT]
    dose_table = pd.DataFrame({"acres": tr["acres"], "old_far": tr["h_before"], "new_far": tr["h_after"]})

    # existing homes, 2010 census blocks
    homes = {}
    bz = blocks_zip or (RAW / "tod_cases" / "census_2010_blocks" / "tabblock2010_37_pophu.zip")
    if bz.exists():
        bbox = tuple(gpd.GeoSeries([el.union_all().envelope], crs=CRS_M).to_crs(4269).total_bounds)
        b = gpd.read_file(bz, bbox=bbox).to_crs(CRS_M)
        b = gpd.GeoDataFrame({"homes": b["HOUSING10"]}, geometry=b.geometry.representative_point(), crs=CRS_M)
        homes = C.homes_by_area(b, el[["area", "geometry"]])

    tp = permits[permits["area"] == C.TREAT]
    diag = {
        "rule": rule,
        "eligible_parcels_by_area": el.groupby("area").size().to_dict(),
        "petition_acres_all": round(float(parcels.loc[parcels["treated"], "acres"].sum()), 1),
        "treatment_zoning_before": tr["zoning_before"].map(base_district).value_counts().head(12).to_dict(),
        "treatment_zoning_after": tr["zoning_after"].map(base_district).value_counts().to_dict(),
        "comparison_zoning_classes_acres": el[el["area"] == C.COMP].groupby("zclass")["acres"].sum().round(1).to_dict(),
        "permits_located_share": round(float(near["pix"].notna().mean()), 4),
        "treatment_units_before": int(tp[tp["year"].isin(per["before"])]["units"].sum()),
        "original_rule_acres": {k: round(v, 1) for k, v in orig_acres.items()},
        "second_comparison_stations": int(len(C.stations_not_upzoned(stations, parcels.loc[parcels["area"] == C.TREAT].geometry.union_all()))),
        "rezoning_petitions_in_window_changing_district": int(len(win)),
    }
    ci = C.CaseInputs(case="charlotte_tod_2019", role="fit", effective_year=EFFECTIVE_YEAR, first_year=FIRST_YEAR,
                      last_full_year=LAST_FULL_YEAR, permits=permits, acres=acres, homes=homes, dose_table=dose_table,
                      parking_change="removed (no minimums in TOD districts)", mandate="no (voluntary bonus only)",
                      notes="dose is added height in feet (no FAR in Charlotte's districts); homes-per-acre caps also removed",
                      dose_unit="height_ft", original_spec=original)
    return ci, diag

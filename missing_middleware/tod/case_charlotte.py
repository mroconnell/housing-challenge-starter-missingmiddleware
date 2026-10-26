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
- Dose: allowed residential FAR before and after from height limits and homes-per-acre caps, converted with
  FAR_PER_FT and SQFT_PER_UNIT (written down in CASE_RESULTS.md; Charlotte's code has no FAR for these districts).
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

# FAR conversion (see CASE_RESULTS.md): New York's contextual districts give 0.05 FAR per foot of height
# (R7A 4.0 FAR at 80 ft; R8A 6.02 FAR at 120 ft), and New York's dwelling-unit factor is 680 sq ft per unit.
FAR_PER_FT = 6.02 / 120.0
SQFT_PER_UNIT = 680.0

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


def far_before(code: str | None) -> float:
    d = DISTRICTS.get(base_district(code) or "")
    if d is None:
        return float("nan")
    _, h, cap = d
    far_h = C.far_from_height(h, FAR_PER_FT) if h is not None else float("inf")
    far_d = C.far_from_density(cap, SQFT_PER_UNIT) if cap is not None else float("inf")
    v = min(far_h, far_d)
    return float("nan") if np.isinf(v) else v


def far_after(code: str | None) -> float:
    b = base_district(code)
    h = AFTER_HEIGHT.get(b or "")
    return C.far_from_height(h, FAR_PER_FT) if h else float("nan")


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
    parcels["area"] = C.assign_areas(parcels, parcels["treated"], in_city=in_city, stations=stations)
    lu = parcels["landuse_description"].astype(str)
    parcels["eligible"] = parcels["zclass"].isin(["res", "mixed", "com"]) & ~lu.str.contains(NOT_ELIGIBLE_LANDUSE)
    el = parcels[parcels["area"].notna() & parcels["eligible"]].copy()
    acres = el.groupby("area")["acres"].sum().to_dict()

    # permits on eligible parcels
    pr = load_permits()
    pg = gpd.GeoDataFrame(pr, geometry=gpd.points_from_xy(pr["X"], pr["Y"]), crs=2264).to_crs(CRS_M)
    near = pg[pg.geometry.within(parcels.union_all().buffer(50))].copy()
    near["pix"] = C.locate_points(near, parcels)
    near["area"] = parcels["area"].reindex(near["pix"]).values
    near["eligible"] = parcels["eligible"].reindex(near["pix"]).fillna(False).astype(bool).values
    near["zclass"] = parcels["zclass"].reindex(near["pix"]).values
    j = near[near["area"].notna() & near["eligible"]]
    permits = j[["project", "area", "year", "units"]].copy()
    permits["year"] = permits["year"].astype(int)

    # dose over treatment eligible land
    tr = el[el["area"] == C.TREAT].copy()
    tr["old_far"] = tr["zoning_before"].map(far_before)
    tr["new_far"] = tr["zoning_after"].map(far_after)
    dose_table = tr[["acres", "old_far", "new_far"]]

    # existing homes, 2010 census blocks
    homes = {}
    bz = blocks_zip or (RAW / "tod_cases" / "census_2010_blocks" / "tabblock2010_37_pophu.zip")
    if bz.exists():
        bbox = tuple(gpd.GeoSeries([el.union_all().envelope], crs=CRS_M).to_crs(4269).total_bounds)
        b = gpd.read_file(bz, bbox=bbox).to_crs(CRS_M)
        b = gpd.GeoDataFrame({"homes": b["HOUSING10"]}, geometry=b.geometry.representative_point(), crs=CRS_M)
        homes = C.homes_by_area(b, el[["area", "geometry"]])

    diag = {
        "parcels_by_area": parcels.groupby("area").size().to_dict(),
        "eligible_parcels_by_area": el.groupby("area").size().to_dict(),
        "treatment_acres_all": float(parcels.loc[parcels["treated"], "acres"].sum()),
        "treatment_acres_by_class": parcels[parcels["treated"]].groupby(parcels["zclass"].fillna("unknown"))["acres"].sum().round(1).to_dict(),
        "unknown_zoning_before": sorted(set(parcels.loc[parcels["area"].notna() & parcels["zclass"].isna(), "zoning_before"].dropna().astype(str)))[:40],
        "dose_parcels_missing_far": int(dose_table[["old_far", "new_far"]].isna().any(axis=1).sum()),
        "permits_located_share": round(float(near["pix"].notna().mean()), 4),
        "treatment_units_by_class_before": j[j["area"] == C.TREAT].groupby("zclass")["units"].sum().to_dict(),
        "second_comparison_stations": int(len(C.stations_not_upzoned(stations, parcels.loc[parcels["treated"]].geometry.union_all()))),
    }
    # all-land variant (not pre-registered): industrial land in the treatment and comparison counted too
    allland = parcels[parcels["area"].isin([C.TREAT, C.COMP]) & ~lu.str.contains(NOT_ELIGIBLE_LANDUSE) & parcels["zclass"].ne("inst")]
    j2 = near[near["pix"].isin(allland.index)]
    p2 = j2[["project", "area", "year", "units"]].copy()
    per = C.period_years(EFFECTIVE_YEAR, FIRST_YEAR, LAST_FULL_YEAR)
    a2 = allland.groupby("area")["acres"].sum().to_dict()
    diag["unregistered_all_land_did"] = round(C.did(p2, a2, per["before"], per["after"])["did"], 4)
    diag["unregistered_all_land_acres"] = {k: round(v, 1) for k, v in a2.items()}

    ci = C.CaseInputs(case="charlotte_tod_2019", role="fit", effective_year=EFFECTIVE_YEAR, first_year=FIRST_YEAR,
                      last_full_year=LAST_FULL_YEAR, permits=permits, acres=acres, homes=homes, dose_table=dose_table,
                      parking_change="removed (no minimums in TOD districts)", mandate="no (voluntary bonus only)",
                      notes="dose converted from height and homes-per-acre limits (FAR_PER_FT, SQFT_PER_UNIT)")
    return ci, diag

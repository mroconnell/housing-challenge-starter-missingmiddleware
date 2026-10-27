"""Bellevue BelRed 2009 (BelRed Subarea Plan; Land Use Code ch. 20.25D, Ordinance 5875, May 2009): case adapter.

Added for the trait test (CASE_ANALYSIS_PLAN.md section 7, entry of 2026-10-27, "more cities"). Same rules as every
case: one area rule, units in new-construction building permits per eligible acre per year, 90% project bootstrap.

Inputs (data/raw/tod_cases/bellevue/, fetched by fetch()):
- permits_units.geojson: City of Bellevue permits with dwelling units created (point; permit number, type, parcel,
  issue date, units, subarea, project name). Owner, applicant and contractor fields are not requested.
- zoning.geojson: current City zoning with the ordinance number of each zone (and the pre-2017 district name).
- parcels.geojson: City of Bellevue parcels (parcel number, zoning, size; taxpayer fields not requested).
- rail_stops.geojson: Sound Transit Link stops (BTS National Transit Map); East Link opened in 2024.
- tabblock2010_53_pophu.zip: 2010 Census blocks with housing units (per-1,000-homes sensitivity).

What the data allow, and the rules used:
- Zoning before is not published by parcel. The City's zoning layer is current, and the permit file's zoning field is
  filled with today's district even for permits issued in 2000-2009. The City's plan and the inventory say BelRed was
  mostly light industrial and general commercial, where housing was not allowed (source_lead). So:
  * every parcel now in a BelRed district that allows housing (BR-R, BR-RC-1/2/3, BR-OR, BR-OR-1/2, BR-ORT, BR-CR) and
    zoned by the BelRed ordinance counts as having risen, from residential FAR 0 to the BelRed base FAR of 1.0 (the
    City's FAR guidance: "the base limit ... is 1.0 FAR"; more FAR only through the amenity incentive system, which is
    not by right). BR-MO, BR-MO-1 and BR-GC do not allow housing and are not treatment;
  * the plan's eligible-land rule (residential, mixed-use or commercial zoning before) cannot be applied to the
    treatment, and the land the rule would exclude (industrial) is most of it. The case is therefore context only; its
    estimate counts all non-park BelRed land and is labelled as such (not pre-registered).
- Rezonings outside the reform during 2003-2014: zones whose ordinance (dated by the City's own ordinance dates,
  interpolated by ordinance number) falls in the window are in no area.
- Outcome: new-building permits (types BS single-family new, BB/BA/BM/BW commercial building projects, MH middle
  housing) with dwelling units created; one record per permit number; permits for garages, podiums, foundations,
  shells and below-grade work are dropped, and one record is kept per parcel, unit count and 18 months (staged
  permits of one building). Project = parcel number.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW, ROOT
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "bellevue"
CRS_M = 32148  # NAD83 / Washington North (metres)
CASE = "bellevue_belred_2009"
EFFECTIVE_YEAR = 2009
FIRST_YEAR, LAST_FULL_YEAR = 2000, 2025
BELRED_ORD = 5875
AGS = "https://services1.arcgis.com/EYzEZbDhXZjURPbP/arcgis/rest/services"
LICENCE = "City of Bellevue open data (ArcGIS Hub); no licence stated; public record (D1)"
BUILDING_TYPES = {"BS", "BB", "BA", "BM", "BW", "MH"}
STAGED = re.compile(r"garage|below grade|podium|foundation|shell|parking|demolition|site work", re.I)
STAGE_WINDOW_DAYS = 548
BR_HOUSING = {"BR-R", "BR-RC-1", "BR-RC-2", "BR-RC-3", "BR-OR", "BR-OR-1", "BR-OR-2", "BR-ORT", "BR-CR"}
BR_NO_HOUSING = {"BR-MO", "BR-MO-1", "BR-GC"}
BASE_FAR = 1.0
# Current districts: residential (res), commercial/mixed (com), industrial or no housing (ind), institutional (inst).
RES_PREFIX = ("R-", "LDR", "MDR", "HDR")
COM_PREFIX = ("O", "PO", "OLB", "CB", "NB", "GC", "NMU", "DT", "BR-", "EG-", "BEL", "MI", "OLB")


def zclass(z) -> str | None:
    s = str(z).upper().strip()
    if not s or s == "NONE":
        return None
    if s.startswith(("LI", "BR-GC", "BR-MO")):
        return "ind"
    if s.startswith(RES_PREFIX):
        return "res"
    if s.startswith(("P", "MI")) and not s.startswith("PO"):
        return "inst"
    if s.startswith(COM_PREFIX):
        return "com"
    return None


def ord_number(s) -> float:
    m = re.search(r"(\d{3,4})", str(s))
    return float(m.group(1)) if m else np.nan


def ord_year_map(z: pd.DataFrame) -> callable:
    """Ordinance number -> year, interpolated from the City's own ordinance dates (years 1950 on)."""
    d = z.assign(num=z["ORDNUM"].map(ord_number), yr=pd.to_datetime(z["ORDDATE"], unit="ms", errors="coerce").dt.year)
    d = d[(d["yr"] >= 1950) & d["num"].notna()].groupby("num")["yr"].median().sort_index()
    d = d[d.cummax() == d]  # keep a monotone sequence
    xs, ys = d.index.values.astype(float), d.values.astype(float)
    return lambda n: float(np.interp(n, xs, ys)) if not np.isnan(n) else np.nan


def dedupe_staged(p: pd.DataFrame) -> pd.DataFrame:
    p = p.sort_values(["PARCELNUMBER", "units", "date"])
    keep, last, first = [], None, None
    for k, d in zip(zip(p["PARCELNUMBER"], p["units"]), p["date"]):
        if k != last or pd.isna(d) or pd.isna(first) or (d - first).days > STAGE_WINDOW_DAYS:
            keep.append(True)
            last, first = k, d
        else:
            keep.append(False)
    return p[keep]


# --------------------------------------------------------------------------- fetch

def fetch(refresh: bool = False) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import fetch_tod_cases as F
    man = F.Manifest(DIR, "tod_cases_bellevue", "City of Bellevue (permits, zoning, parcels); BTS National Transit Map; Census")
    F.save_layer(man, "permits_units.geojson", f"{AGS}/Bellevue_Permit/FeatureServer/0", refresh, LICENCE,
                 where="DWELLINGUNITSCREATED > 0",
                 out_fields="PERMITNUMBER,PERMITTYPE,PERMITTYPEDESCRIPTION,SUBTYPE,PERMITSTATUS,PARCELNUMBER,ISSUEDDATE,"
                            "DWELLINGUNITSCREATED,SUBAREA,ZONING,PROJECTNAME", page=2000)
    F.save_layer(man, "zoning.geojson", f"{AGS}/Zoning/FeatureServer/7", refresh, LICENCE,
                 out_fields="ORDNUM,ORDNUM2,ORDDATE,Zoning,ZoningDescription,ZONING_PreCodeAmendment2017", page=2000)
    F.save_layer(man, "parcels.geojson", f"{AGS}/City_of_Bellevue_Parcels/FeatureServer/0", refresh, LICENCE,
                 out_fields="ParcelAFN,Zoning,ParcelSize,Jurisdicti", page=2000)
    F.ntm_rail_stops(man, "rail_stops.geojson", ["00040"], refresh)
    F.download_file(man, "tabblock2010_53_pophu.zip", "https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_53_pophu.zip",
                    refresh, F.CENSUS_LICENCE, note="2010 Census blocks with HOUSING10 (Washington)")


# --------------------------------------------------------------------------- build

_cache: dict = {}


def _prepare():
    import geopandas as gpd
    if _cache:
        return _cache
    z = gpd.read_file(DIR / "zoning.geojson").to_crs(CRS_M)
    z["geometry"] = z.geometry.make_valid()
    yr = ord_year_map(z)
    z["ord_year"] = [max([yr(ord_number(a)) for a in (o1, o2) if not np.isnan(ord_number(a))] or [np.nan])
                     for o1, o2 in zip(z["ORDNUM"], z["ORDNUM2"])]
    z["is_belred_ord"] = z["ORDNUM"].map(ord_number).eq(BELRED_ORD) | z["ORDNUM2"].map(ord_number).eq(BELRED_ORD)
    parcels = gpd.read_file(DIR / "parcels.geojson").to_crs(CRS_M)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].drop_duplicates("ParcelAFN").reset_index(drop=True)
    parcels["acres"] = parcels.geometry.area / C.SQM_PER_ACRE
    pts = gpd.GeoDataFrame(geometry=parcels.geometry.representative_point(), crs=CRS_M)
    j = gpd.sjoin(pts, z[["Zoning", "ord_year", "is_belred_ord", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()].reindex(pts.index)
    parcels["zoning_now"] = j["Zoning"].fillna(parcels["Zoning"]).astype(str).str.strip()
    parcels["ord_year"] = j["ord_year"].values
    parcels["is_belred_ord"] = j["is_belred_ord"].fillna(False).astype(bool).values
    parcels["zclass"] = parcels["zoning_now"].map(zclass)
    stops = gpd.read_file(DIR / "rail_stops.geojson").to_crs(CRS_M)
    p = gpd.read_file(DIR / "permits_units.geojson").to_crs(CRS_M)
    p = p.drop_duplicates("PERMITNUMBER")
    p = p[p["PERMITTYPE"].astype(str).str.strip().isin(BUILDING_TYPES) & p["ISSUEDDATE"].notna()].copy()
    p = p[~p["PROJECTNAME"].astype(str).str.contains(STAGED)]
    p["units"] = pd.to_numeric(p["DWELLINGUNITSCREATED"], errors="coerce").fillna(0)
    p["date"] = pd.to_datetime(p["ISSUEDDATE"], unit="ms", errors="coerce")
    p = p[p["units"] > 0]
    n0 = len(p)
    p = dedupe_staged(p)
    p["year"] = p["date"].dt.year
    p["pix"] = C.locate_points(p, parcels)
    p["project"] = p["PARCELNUMBER"].astype(str)
    _cache.update(z=z, parcels=parcels, stops=stops, permits=p, staged_merged=n0 - len(p))
    return _cache


def _areas(parcels, stops, eligible_rule: str):
    """eligible_rule: 'context' = all non-park, non-institutional land counts (treatment zoning before unknown);
    'plan' = treatment land is eligible only if its zoning before is known to be residential, mixed or commercial
    (never, here, since it is not published)."""
    per = C.period_years(EFFECTIVE_YEAR, FIRST_YEAR, LAST_FULL_YEAR)
    zn = parcels["zoning_now"].str.upper()
    in_reform = parcels["is_belred_ord"] & zn.str.startswith("BR-")
    rose = in_reform & zn.isin(BR_HOUSING)
    lo, hi = per["before"][0], per["after"][-1]
    changed = (~in_reform) & parcels["ord_year"].between(lo, hi + 0.99)
    eligible = parcels["zclass"].isin(["res", "com"]) | rose
    if eligible_rule == "plan":
        eligible = eligible & ~in_reform
    one = pd.Series(1.0, index=parcels.index)
    in_city = parcels["Jurisdicti"].astype(str).str.upper().str.contains("BELLEVUE")
    area, rule = C.uniform_areas(parcels, in_reform, rose, one * 0, one, pd.Series(False, index=parcels.index), changed,
                                 eligible, in_city=in_city, stations=stops.geometry)
    return area, eligible, rose, in_reform, rule, per


def build() -> tuple[C.CaseInputs, dict]:
    import geopandas as gpd
    d = _prepare()
    parcels, stops, p = d["parcels"], d["stops"], d["permits"]
    area, eligible, rose, in_reform, rule, per = _areas(parcels, stops, "context")
    area_plan, elig_plan, *_ = _areas(parcels, stops, "plan")
    el = parcels[area.notna() & eligible]
    acres = el.groupby(area[el.index])["acres"].sum().to_dict()

    def permits_for(a, elig):
        q = p.assign(area=a.reindex(p["pix"]).values, el=elig.reindex(p["pix"]).fillna(False).astype(bool).values)
        q = q[q["area"].notna() & q["el"] & q["year"].between(per["before"][0], per["after"][-1])]
        return q[["project", "area", "year", "units"]].astype({"year": int})

    permits = permits_for(area, eligible)
    orig = C.assign_areas(parcels, in_reform, stations=None)
    orig_acres = parcels[orig.notna() & eligible].groupby(orig)["acres"].sum().to_dict()
    tr = el[area[el.index] == C.TREAT]
    dose_table = pd.DataFrame({"acres": tr["acres"], "old_far": 0.0, "new_far": BASE_FAR})
    homes = {}
    bz = DIR / "tabblock2010_53_pophu.zip"
    if bz.exists():
        bbox = tuple(gpd.GeoSeries([el.union_all().envelope], crs=CRS_M).to_crs(4269).total_bounds)
        b = gpd.read_file(bz, bbox=bbox).to_crs(CRS_M)
        b = gpd.GeoDataFrame({"homes": b["HOUSING10"]}, geometry=b.geometry.representative_point(), crs=CRS_M)
        homes = C.homes_by_area(b, el.assign(area=area[el.index])[["area", "geometry"]])
    plan_acres = parcels[area_plan.notna() & elig_plan].groupby(area_plan)["acres"].sum().to_dict()
    # the all-land estimate (not pre-registered): reported in extra columns, since the plan's rule leaves no treatment
    extra = {}
    if acres.get(C.TREAT) and acres.get(C.COMP):
        e = C.did(permits, acres, per["before"], per["after"])
        lo, hi, _ = C.bootstrap_did(permits, acres, per["before"], per["after"])
        extra = {"sens_all_land_did": round(e["did"], 4), "sens_all_land_low": round(lo, 4), "sens_all_land_high": round(hi, 4),
                 "sens_all_land_dose_far": BASE_FAR, "sens_all_land_effect_per_dose": round(e["did"] / BASE_FAR, 4)}
    diag = {
        "rule": rule,
        "reform_parcels": int(in_reform.sum()), "reform_acres_all": round(float(parcels.loc[in_reform, "acres"].sum()), 1),
        "treated_parcels": int((area == C.TREAT).sum()),
        "treatment_zoning_now": parcels.loc[area == C.TREAT, "zoning_now"].value_counts().to_dict(),
        "reform_no_housing_acres": round(float(parcels.loc[in_reform & ~rose, "acres"].sum()), 1),
        "acres_under_plan_eligible_rule": {k: round(v, 1) for k, v in plan_acres.items()},
        "staged_permits_merged": int(d["staged_merged"]),
        "permits_located_share": round(float(p["pix"].notna().mean()), 4),
        "second_comparison_stations": int(len(C.stations_not_upzoned(stops.geometry, parcels.loc[area == C.TREAT].geometry.union_all()))),
    }
    ci = C.CaseInputs(case=CASE, role="medium", effective_year=EFFECTIVE_YEAR, first_year=FIRST_YEAR,
                      last_full_year=LAST_FULL_YEAR, permits=permits, acres=acres, homes=homes, dose_table=dose_table,
                      parking_change="unknown (own parking chapter 20.25D.120)",
                      mandate="no (bonus FAR through affordable units or fee, voluntary)",
                      status_override="context_only: zoning before not published by parcel; BelRed was mostly light industrial "
                                      "(source_lead), which the eligible-land rule excludes; estimate counts all non-park BelRed land",
                      original_spec=(permits_for(orig, eligible), orig_acres),
                      notes="treatment = BelRed districts allowing housing (Ord. 5875); dose = base FAR 1.0 from 0; "
                            "all-land estimate in sens_all_land_* (not pre-registered)", extra=extra)
    return ci, diag


def unit_frame() -> dict:
    """The case at the trait test's unit level: treatment parcels labelled by nearest Link station (traits helpers),
    with what the trait test needs; no identifiers beyond the internal index."""
    from missing_middleware.tod import traits as T
    d = _prepare()
    parcels, stops, p = d["parcels"], d["stops"], d["permits"]
    area, eligible, rose, in_reform, rule, per = _areas(parcels, stops, "context")
    st = T.cluster_stations(stops.reset_index(drop=True), stops["stop_name"].reset_index(drop=True))
    out = parcels[["acres", "zoning_now", "geometry"]].copy()
    out["area"], out["eligible"] = area, eligible
    tr = out.index[(area == C.TREAT) & eligible]
    out["unit_label"] = None
    out.loc[tr, "unit_label"] = T.nearest_station(out.loc[tr].geometry.representative_point(), st).values
    out["old_level"] = np.where(area == C.TREAT, 0.0, np.nan)
    out["new_level"] = np.where(area == C.TREAT, BASE_FAR, np.nan)
    out["vpi"] = np.nan  # vacant/parking/industrial share is not available by parcel here
    q = p[p["year"].between(per["before"][0], per["after"][-1])].copy()
    q["area"] = area.reindex(q["pix"]).values
    q = q[q["area"].notna() & eligible.reindex(q["pix"]).fillna(False).astype(bool).values]
    return {"parcels": out, "permits": q[["project", "area", "year", "units", "pix"]].astype({"year": int}),
            "effective_year": EFFECTIVE_YEAR, "per": per, "dose_unit": "added FAR (base FAR 1.0 from 0; source_lead before)"}

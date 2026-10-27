"""Los Angeles: Warner Center 2035 Specific Plan (Ordinance 182,766, 2013) and Cornfield Arroyo Seco Specific Plan
(Ordinance 182,617, effective 14 August 2013): case adapter (batch 1 of the added cities, plan section 7 entry of
2026-10-27, "more cities for the trait test").

Inputs (data/raw/tod_cases/la/, fetched by fetch() below with the helpers of scripts/fetch_tod_cases.py):
- permits_<dataset>.csv: LADBS building permits of type "Bldg-New" near the two plans, from the City's open data
  portal (e67z-kt2n issued before 2010, dyxf-7hc4 2010-2019, pi9x-tg5x 2020 on): permit number, type, sub-type, issue
  date, dwelling units changed (du_changed), ADUs changed, APN, zoning at permit, point. No owner or applicant field.
- specific_plans.geojson: the City Planning Department's Specific Plan Areas (official boundaries).
- zoning_<year>.geojson: City Planning's Zoning Archive (Chapter 1), one snapshot a year, near the two plans:
  2007 (start of the before years), 2012 (before), 2014 (after), 2019 (end of the after years).
- parcels.geojson: Los Angeles County Assessor parcels near the plans (APN, use code and type, units, year built).
- transit_stops.geojson: Metro rail stops and Metro G Line (Orange Line) bus rapid transit stations (BTS National
  Transit Map, LA Metro, NTD 90154).

Rules (the one area rule, cases.uniform_areas):
- Reform land: parcels whose representative point lies in the specific plan area.
- Cornfield Arroyo Seco: the Zoning Archive shows each parcel's district before (2012: mostly M1, M2, MR2, CM, C2) and
  after (2014: UV, UC, UI, GW with the (CA) suffix). Allowed residential intensity rose where the ordinal level
  (LEVEL, below) rose.
- Warner Center: the parcels are zoned "WC" both before (1993 Warner Center Specific Plan) and after (2013 plan), so
  the Zoning Archive cannot show the change. Every parcel in the plan counts as having risen (the 2013 plan replaced a
  trip-budget cap with district FARs and removed residential density limits, source_lead), and "already at the law"
  cannot be tested.
- Lots whose zoning string changed between 2007 and 2012, outside the plan between 2012 and 2014, or anywhere between
  2014 and 2019, are in no area.
- Eligible: zoning before residential, commercial or mixed (manufacturing, public facilities, open space and parking
  zones are not), less Assessor use types that are institutional, government, parks or cemeteries.
- Outcome: dwelling units in new-building permits (du_changed > 0; accessory dwelling units are not counted), one
  record per permit number; supplemental and revision permits are dropped. Project = APN (or the point).
- Dose: neither plan's district FARs are in an open data layer (the Zoning Archive FAR field is empty for these
  districts), so there is no FAR dose: dose_unit "none" and no effect per dose; both cases stay out of per-FAR pooling.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "la"
CRS_M = 26945  # NAD83 / California zone 5 (metres)
FIRST_YEAR, LAST_FULL_YEAR = 1988, 2025
SOCRATA = "https://data.lacity.org/resource"
DATASETS = {"e67z-kt2n": (1988, 2009), "dyxf-7hc4": (2010, 2019), "pi9x-tg5x": (2020, 2026)}
PLANNING = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services"
ARCHIVE_LAYERS = {2007: 20, 2012: 15, 2014: 13, 2019: 8}
SNAP = {"start": 2007, "before": 2012, "after": 2014, "end": 2019}
PARCELS = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0"
LA_LICENCE = "City of Los Angeles open data (data.lacity.org) terms of use; no licence named on the datasets; public record (D1)"
PLAN_LICENCE = "City of Los Angeles Department of City Planning GIS; no licence stated; public record (D1)"
COUNTY_LICENCE = "Los Angeles County Office of the Assessor GIS; no licence stated; public record (D1)"
NTM_STOPS = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0"

CASES = {
    "la_warner_center_2013": {"plan": "WARNER CENTER", "effective": "2013-12-25", "zone_rule": "whole plan"},
    "la_cornfield_arroyo_seco_2013": {"plan": "CORNFIELD / ARROYO SECO", "effective": "2013-08-14", "zone_rule": "zoning change"},
}

# Ordinal level of allowed residential intensity (an ordering, not a dose; LA Municipal Code zones: one-family zones,
# two-family, restricted density, R3 one home per 800 sq ft of lot, R4 one per 400, R5 one per 200; commercial zones
# allow R4 density (C1, C1.5, C2, C4, CR) or R3 (C1? CM); manufacturing, public facility, open space and parking zones
# allow no housing; the Cornfield Arroyo Seco districts UV and UC have no density limit, UI allows live/work only).
LEVEL = {"A1": 0.5, "A2": 0.5, "RA": 0.8, "RE": 0.8, "RS": 1, "R1": 1, "RU": 1.2, "RZ": 1.2, "RW1": 1.2, "R2": 1.5,
         "RW2": 1.5, "RD": 2, "RMP": 2, "R3": 3, "RAS3": 3, "R4": 4, "RAS4": 4, "R5": 5, "CR": 4, "C1": 4, "C1.5": 4,
         "C2": 4, "C4": 4, "C5": 4, "CW": 4, "CM": 3, "UV": 6, "UC": 6, "UI": 0.5, "WC": 5,
         "M1": 0, "M2": 0, "M3": 0, "MR1": 0, "MR2": 0, "PF": 0, "OS": 0, "P": 0, "PB": 0, "GW": 0, "SL": 0}
ZCLASS = {**{k: "res" for k in ("A1", "A2", "RA", "RE", "RS", "R1", "RU", "RZ", "RW1", "R2", "RW2", "RD", "RMP", "R3",
                                "RAS3", "R4", "RAS4", "R5")},
          **{k: "com" for k in ("CR", "C1", "C1.5", "C2", "C4", "C5", "CW", "CM")},
          **{k: "mixed" for k in ("UV", "UC", "WC")},
          **{k: "ind" for k in ("M1", "M2", "M3", "MR1", "MR2", "UI")},
          "PF": "inst", "OS": "park", "GW": "park", "P": "parking", "PB": "parking", "SL": "park"}
NOT_ELIGIBLE_USE = re.compile(r"INSTITUTION|GOVERN|PARK|CEMETER|CHURCH|SCHOOL|UTILIT|RECREATION|MISCELLANEOUS", re.I)
VPI_USE = re.compile(r"VACANT|PARKING|INDUSTRIAL|WAREHOUSE|MANUFACTUR", re.I)
EXCLUDE_WORK = re.compile(r"SUPPLEMENT|REVISION|REVISED|CHANGE OF ARCHITECT|CHANGE OF ENGINEER", re.I)


def base_zone(z) -> str | None:
    """Base zone class of an LA zoning string: '(T)(Q)C2-1VL-CDO' -> 'C2', 'UV(CA)' -> 'UV', 'RD1.5-1' -> 'RD',
    'WC' -> 'WC'."""
    if not isinstance(z, str) or not z.strip():
        return None
    s = z.upper().strip()
    if s.startswith("(WC)") or s == "WC":
        return "WC"                                          # Warner Center plan districts, e.g. '(WC)PARK-SN'
    s = re.sub(r"^(\[[^\]]*\]|\([^)]*\))+", "", s)          # leading [Q], (T), (Q) conditions
    s = re.sub(r"\(CA\)", "", s)
    m = re.match(r"(RAS3|RAS4|RW1|RW2|RMP|C1\.5|MR1|MR2|RD|RE|RS|RU|RZ|RA|R1|R2|R3|R4|R5|CR|C1|C2|C4|C5|CW|CM|M1|M2|M3|"
                 r"PF|OS|PB|P|A1|A2|UV|UC|UI|GW|WC|SL)", s)
    return m.group(1) if m else None


def level(z) -> float:
    return float(LEVEL.get(base_zone(z) or "", np.nan))


def zclass(z) -> str | None:
    return ZCLASS.get(base_zone(z) or "")


def zone_changed(a: pd.Series, b: pd.Series) -> pd.Series:
    """True where both snapshots have a zoning string and the strings differ (spaces and case ignored)."""
    def norm(v: pd.Series) -> pd.Series:
        v = v.astype(str).str.upper().str.replace(r"\s+", "", regex=True)
        return v.str.replace(r"^\(WC\).*$", "WC", regex=True)  # 2019 archive spells out the 2013 plan's districts
    x, y = norm(a), norm(b)
    return a.notna() & b.notna() & (x != y)


def is_new_housing(permits: pd.DataFrame) -> pd.Series:
    """New-building permits that add dwelling units and are not supplemental or revision permits."""
    units = pd.to_numeric(permits["du_changed"], errors="coerce").fillna(0)
    work = permits.get("work_desc", pd.Series("", index=permits.index)).astype(str)
    return permits["permit_type"].astype(str).eq("Bldg-New") & (units > 0) & ~work.str.contains(EXCLUDE_WORK)


# --------------------------------------------------------------------------- fetch

def _fetch_helpers():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import fetch_tod_cases as F  # noqa: E402
    return F


def fetch(refresh: bool = False) -> None:
    import urllib.parse
    import geopandas as gpd
    F = _fetch_helpers()
    man = F.Manifest(DIR, "tod_cases_la", "City of Los Angeles (LADBS permits, City Planning) and Los Angeles County Assessor")
    F.save_layer(man, "specific_plans.geojson", f"{PLANNING}/Specific_Plan_Areas/FeatureServer/6", refresh, PLAN_LICENCE,
                 where="SPA_NM IN ('WARNER CENTER','CORNFIELD / ARROYO SECO')", out_fields="SPA_NM", page=100)
    spa = gpd.read_file(DIR / "specific_plans.geojson")
    for nm, g in spa.groupby("SPA_NM"):
        tag = "wc" if "WARNER" in nm else "casp"
        aoi = F.aoi_from([(g.geometry, 1800.0)])
        env = gpd.GeoSeries([aoi], crs=F.AOI_CRS).to_crs(4326).total_bounds
        for ds in DATASETS:
            name = f"permits_{tag}_{ds}.csv"
            if man.have(name, refresh):
                continue
            where = (f"permit_type='Bldg-New' AND within_box(geolocation, {env[3]:.5f}, {env[0]:.5f}, {env[1]:.5f}, {env[2]:.5f})")
            params = {"$select": "permit_nbr,permit_type,permit_sub_type,issue_date,du_changed,adu_changed,apn,zone,work_desc,lat,lon",
                      "$where": where, "$limit": 200000, "$order": "permit_nbr"}
            url = f"{SOCRATA}/{ds}.csv?" + urllib.parse.urlencode(params)
            man.record(name, F.http_get(url, timeout=900), url, licence=LA_LICENCE,
                       note=f"LADBS Building Permits ({ds}), type Bldg-New, within the envelope of the plan buffered 1.8 km; "
                            "no owner, applicant or contractor fields requested")
        for yr, lid in ARCHIVE_LAYERS.items():
            F.save_tiled_layer(man, f"zoning_{tag}_{yr}.geojson", f"{PLANNING}/Zoning_Archive/FeatureServer/{lid}", aoi, refresh,
                               PLAN_LICENCE, out_fields="*", id_field="OBJECTID", page=2000)
        F.save_tiled_layer(man, f"parcels_{tag}.geojson", PARCELS, aoi, refresh, COUNTY_LICENCE,
                           out_fields="AIN,APN,UseCode,UseType,UseDescription,Units1,YearBuilt1", id_field="AIN", page=1000)
        env2 = ",".join(f"{v:.5f}" for v in env)
        F.save_layer(man, f"transit_stops_{tag}.geojson", NTM_STOPS, refresh, "CC BY 3.0 US (BTS National Transit Map stops layer)",
                     where="ntd_id='90154' AND (stop_type IN ('0','1','2') OR stop_name LIKE '% Station')",
                     geometry=env2, page=2000)


# --------------------------------------------------------------------------- build

def _zone_col(z) -> str:
    return next(c for c in z.columns if c.upper().endswith("ZONE_CMPLT") and not c.upper().endswith("ZONE_CMPLT_1"))


def _load(tag: str):
    import geopandas as gpd
    parcels = gpd.read_file(DIR / f"parcels_{tag}.geojson").to_crs(CRS_M)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].drop_duplicates("AIN")
    # condominium units are mapped as copies of their lot: keep one parcel per footprint
    key = parcels.geometry.centroid.x.round(0).astype(int).astype(str) + "_" + parcels.geometry.centroid.y.round(0).astype(int).astype(str) \
        + "_" + parcels.geometry.area.round(-1).astype(int).astype(str)
    parcels = parcels.assign(_k=key)
    units = pd.to_numeric(parcels["Units1"], errors="coerce").fillna(0)
    parcels["Units1"] = units.groupby(parcels["_k"]).transform("sum")
    parcels = parcels.drop_duplicates("_k").drop(columns="_k").reset_index(drop=True)
    parcels["acres"] = parcels.geometry.area / C.SQM_PER_ACRE
    pts = gpd.GeoDataFrame(geometry=parcels.geometry.representative_point(), crs=CRS_M)
    for key, yr in SNAP.items():
        z = gpd.read_file(DIR / f"zoning_{tag}_{yr}.geojson").to_crs(CRS_M)
        col = _zone_col(z)
        z = z[[col, "geometry"]].rename(columns={col: "zone"})
        z["geometry"] = z.geometry.make_valid()
        j = gpd.sjoin(pts, z, how="left", predicate="within")
        parcels[f"zone_{key}"] = j[~j.index.duplicated()].reindex(pts.index)["zone"].values
    perms = []
    for ds in DATASETS:
        f = DIR / f"permits_{tag}_{ds}.csv"
        if f.exists() and f.stat().st_size > 0:
            perms.append(pd.read_csv(f, dtype=str))
    p = pd.concat(perms, ignore_index=True).drop_duplicates("permit_nbr")
    stops = gpd.read_file(DIR / f"transit_stops_{tag}.geojson").to_crs(CRS_M)
    return parcels, pts, p, stops


def _areas(case: str):
    import geopandas as gpd
    spec = CASES[case]
    tag = "wc" if "warner" in case else "casp"
    parcels, pts, p, stops = _load(tag)
    spa = gpd.read_file(DIR / "specific_plans.geojson").to_crs(CRS_M)
    poly = spa[spa["SPA_NM"] == spec["plan"]].geometry.make_valid().union_all()
    eff = pd.Timestamp(spec["effective"])
    per = C.period_years(eff.year, FIRST_YEAR, LAST_FULL_YEAR)
    in_plan = pts.geometry.within(poly)
    lb, la_ = parcels["zone_before"].map(level), parcels["zone_after"].map(level)
    if spec["zone_rule"] == "whole plan":
        rose = in_plan.copy()
        level_before, level_after = pd.Series(0.0, index=parcels.index), in_plan.astype(float)
        uncapped = pd.Series(False, index=parcels.index)
    else:
        rose = in_plan & (la_ > lb)
        level_before, level_after = lb, la_
        uncapped = pd.Series(False, index=parcels.index)  # ordinal levels: "already at the law" is not tested
    changed = zone_changed(parcels["zone_start"], parcels["zone_before"]) | \
        (~in_plan & zone_changed(parcels["zone_before"], parcels["zone_after"])) | \
        zone_changed(parcels["zone_after"], parcels["zone_end"])
    use = (parcels["UseType"].astype(str) + " " + parcels["UseDescription"].astype(str)).str.upper()
    eligible = parcels["zone_before"].map(zclass).isin(["res", "com", "mixed"]) & ~use.str.contains(NOT_ELIGIBLE_USE)
    stations = stops.geometry
    area, rule = C.uniform_areas(parcels, in_plan, rose, level_before, level_after, uncapped, changed, eligible, stations=stations)
    parcels["area"], parcels["eligible"], parcels["in_plan"] = area, eligible, in_plan
    parcels["old_level"], parcels["new_level"] = lb, la_
    parcels["vpi"] = use.str.contains(VPI_USE) | parcels["zone_before"].map(zclass).eq("ind")
    yb = pd.to_numeric(parcels["YearBuilt1"], errors="coerce")
    parcels["homes_before"] = np.where(yb < per["before"][0], pd.to_numeric(parcels["Units1"], errors="coerce").fillna(0), 0.0)

    q = p[is_new_housing(p)].copy()
    q["units"] = pd.to_numeric(q["du_changed"], errors="coerce").fillna(0)
    q["year"] = pd.to_datetime(q["issue_date"], errors="coerce").dt.year
    q = q.dropna(subset=["year"])
    q = q[q["year"].between(per["before"][0], per["after"][-1])]
    q["lat"], q["lon"] = pd.to_numeric(q["lat"], errors="coerce"), pd.to_numeric(q["lon"], errors="coerce")
    q = q.dropna(subset=["lat", "lon"])
    qg = gpd.GeoDataFrame(q, geometry=gpd.points_from_xy(q["lon"], q["lat"]), crs=4326).to_crs(CRS_M)
    apn_lut = pd.Series(parcels.index, index=parcels["APN"].astype(str).str.replace(r"\D", "", regex=True))
    apn_lut = apn_lut[~apn_lut.index.duplicated()]
    ix = qg["apn"].astype(str).str.replace(r"\D", "", regex=True).map(apn_lut)  # masked APNs map to nothing
    miss = ix.isna()
    if miss.any():
        ix.loc[miss] = C.locate_points(qg.loc[miss], parcels).values
    qg["pix"] = ix
    apn_ok = qg["apn"].astype(str).str.fullmatch(r"\d{10}")  # some APNs are masked ('**********') in the open data
    qg["project"] = np.where(apn_ok, qg["apn"].astype(str), qg["permit_nbr"].astype(str))
    return parcels, qg, per, eff, rule, stations


def _permits_for(qg, parcels, area: pd.Series) -> pd.DataFrame:
    r = qg.assign(area=area.reindex(qg["pix"]).values,
                  el=parcels["eligible"].reindex(qg["pix"]).fillna(False).astype(bool).values)
    r = r[r["area"].notna() & r["el"]][["project", "area", "year", "units", "pix"]].copy()
    r["year"] = r["year"].astype(int)
    return r


def build(case: str) -> tuple[C.CaseInputs, dict]:
    parcels, qg, per, eff, rule, stations = _areas(case)
    el = parcels[parcels["area"].notna() & parcels["eligible"]]
    acres = el.groupby("area")["acres"].sum().to_dict()
    homes = el.groupby("area")["homes_before"].sum().astype(float).to_dict()
    permits = _permits_for(qg, parcels, parcels["area"]).drop(columns="pix")
    orig = C.assign_areas(parcels, parcels["in_plan"], stations=None)
    orig_p = _permits_for(qg, parcels, orig).drop(columns="pix")
    orig_a = parcels[orig.notna() & parcels["eligible"]].groupby(orig)["acres"].sum().to_dict()
    tr = el[el["area"] == C.TREAT]
    diag = {"rule": rule, "effective": str(eff.date()), "snapshots": SNAP,
            "plan_parcels": int(parcels["in_plan"].sum()),
            "treatment_zoning_before": tr["zone_before"].map(base_zone).value_counts().head(10).to_dict(),
            "treatment_zoning_after": tr["zone_after"].map(base_zone).value_counts().head(10).to_dict(),
            "plan_zoning_before_all": parcels.loc[parcels["in_plan"], "zone_before"].map(base_zone).value_counts().head(10).to_dict(),
            "permits_located_share": round(float(qg["pix"].notna().mean()), 4) if len(qg) else None,
            "acres": {k: round(v, 1) for k, v in acres.items()},
            "original_rule_acres": {k: round(v, 1) for k, v in orig_a.items()},
            "unknown_zones_in_plan": sorted(set(parcels.loc[parcels["in_plan"] & parcels["zone_before"].map(base_zone).isna(), "zone_before"].dropna().astype(str)))[:20]}
    ci = C.CaseInputs(case=case, role="fit", effective_year=eff.year, first_year=FIRST_YEAR, last_full_year=LAST_FULL_YEAR,
                      permits=permits, acres=acres, homes=homes, dose_table=None, dose_unit="none",
                      parking_change="reduced (shared and reduced parking; Cornfield: no minimum)", mandate="no (voluntary bonus)",
                      original_spec=(orig_p, orig_a),
                      notes="no FAR dose (district FARs not in open data); existing homes from the current Assessor roll (built before the window)")
    return ci, diag


def unit_frame(case: str) -> dict:
    """Parcels and permits at the level the trait test uses: each treatment parcel labelled with its unit. Warner
    Center: the 2013 plan's district (subarea), read from the 2019 Zoning Archive. Cornfield Arroyo Seco: the nearest
    Metro station (stops within 150 m merged, traits.cluster_stations)."""
    import geopandas as gpd
    from missing_middleware.tod import traits as T
    parcels, qg, per, eff, rule, stations = _areas(case)
    tag = "wc" if "warner" in case else "casp"
    s = gpd.read_file(DIR / f"transit_stops_{tag}.geojson").to_crs(CRS_M).reset_index(drop=True)
    st = T.cluster_stations(s, s["stop_name"])
    tr = parcels.index[(parcels["area"] == C.TREAT) & parcels["eligible"].astype(bool)]
    parcels["unit_label"] = None
    if len(tr):
        if tag == "wc":
            # the 2013 plan's districts (Downtown, Uptown, Commerce, Park, College, River, ...), read from the 2019 archive
            d = parcels.loc[tr, "zone_end"].astype(str).str.extract(r"^\(WC\)([A-Z ]+)", expand=False).str.strip().str.title()
            parcels.loc[tr, "unit_label"] = ("Warner Center " + d.fillna("unknown district")).values
        else:
            parcels.loc[tr, "unit_label"] = T.nearest_station(parcels.loc[tr].geometry.representative_point(), st).values
    keep = ["area", "eligible", "unit_label", "old_level", "new_level", "vpi", "homes_before", "geometry"]
    return {"parcels": parcels[keep].copy(), "permits": _permits_for(qg, parcels, parcels["area"]),
            "effective_year": eff.year, "per": per, "dose_unit": "none (no FAR in open data; ordinal levels only)"}

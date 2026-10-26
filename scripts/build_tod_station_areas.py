"""Build the TOD station-area land and zoning tables: the City of Milwaukee and the City of Madison with
coded zoning, and every other municipality near a qualifying stop with the existing-density fallback.

    uv run --all-extras python scripts/fetch_tod_parcels_zoning.py   # once, needs network
    uv run --all-extras python scripts/build_tod_station_areas.py   # offline

In:  reference/tod_stops.csv (qualifying stops), reference/tod_zoning_rules_{milwaukee,madison}.csv
     data/raw/tod_capacity/{v12_milwaukee.geojson, mke_zoning.geojson, mad_zoning.geojson}
     data/raw/milwaukee_mprop/mprop.csv (homes, zoning and land use per tax key)
     data/raw/madison_parcels/tax_parcels.geojson (homes, zoning and use per parcel, with outlines)
     data/raw/madison_tod/tod_boundary.geojson (TOD overlay)
     data/raw/tod_capacity/v12_*.geojson (other counties), data/raw/census_tiger_2020_tabblock (2020 homes)
     data/raw/madison_permits (new 5+ home buildings, citywide: floor area per home only)
Out: reference/tod_station_areas.csv  place x band x zoning district x use class (never parcel-level)
     reference/tod_station_area_summary.csv  totals by definition (two cities, fallback places, state)
     reference/tod_floor_area_per_home.csv  measured floor area per new home
     reference/tod_madison_test_land.csv  eligible land for the pre-registered Madison test
                                          (docs/tod/MADISON_TEST_PREREG.md): overlay, 1/4-mile ring
                                          outside it, rest of city. Land only: no permits are read.

Method: docs/tod/STATION_AREAS.md. Formulas: missing_middleware/tod/capacity.py.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import capacity as C  # noqa: E402

D = RAW / "tod_capacity"
CRS_M = 3071
M2_PER_ACRE = 4046.8564224
OUT = REFERENCE / "tod_station_areas.csv"
OUT_TEST = REFERENCE / "tod_madison_test_land.csv"
OUT_SUMMARY = REFERENCE / "tod_station_area_summary.csv"
OUT_FLOOR = REFERENCE / "tod_floor_area_per_home.csv"
BLOCKS = RAW / "census_tiger_2020_tabblock" / "tl_2020_55_tabblock20.zip"

# ----------------------------------------------------------------------------- use classes

# City of Milwaukee MPROP LAND_USE_GP (land-use group) -> use class. Groups read from the codes they
# hold (2026 MPROP): 1 = 8810/8811 single-family, 2 = 8820 duplex, 3 = 8830 multi-family, 4 = 8899
# homes over commercial (median 4 homes, 2 stories), 5 and 6 = retail and services, 7 = other
# commercial (9999, 9911), 8 = manufacturing, 9 = parking (7523, 7525), rail, utilities, 10 =
# agriculture, 11 = institutions (churches, schools, colleges; 6553 cemeteries), 12 = parks and open
# space (mostly zoned PK), 13 = vacant land, 0 = unknown.
MKE_GROUP_USE = {"1": "single_family", "2": "two_family", "3": "multifamily", "4": "mixed_residential_commercial",
                 "5": "commercial", "6": "commercial", "7": "commercial", "8": "industrial", "10": "agricultural",
                 "11": "institutional", "12": "park_open_space", "13": "vacant", "0": "other_unknown"}
MKE_PARKING = {"7523", "7525"}
MKE_CEMETERY = {"6553"}


def mke_use_class(group, land_use) -> str:
    g = str(group).strip() if pd.notna(group) else ""
    lu = str(land_use).strip() if pd.notna(land_use) else ""
    if lu in MKE_CEMETERY:
        return "cemetery"
    if g == "9":
        return "parking" if lu in MKE_PARKING else "utility_transport"
    return MKE_GROUP_USE.get(g, "other_unknown")


MAD_USE = {
    "Single family": "single_family", "2 Unit": "two_family", "3 Unit": "multifamily",
    "Apartments": "multifamily", "Apartment Sec 42": "multifamily", "Apartments & rooms": "multifamily",
    "Rooming house": "multifamily", "Frat & sorority lg.": "multifamily", "Frat & sorority sm.": "multifamily",
    "Dorm. 3+ stories lg.": "multifamily", "Nursing home": "multifamily", "Retirement home": "multifamily",
    "Mobile home park": "multifamily",
    "Apartment & store": "mixed_residential_commercial", "Restaurant & apts.": "mixed_residential_commercial",
    "Tavern & apartment": "mixed_residential_commercial", "Apartment & office": "mixed_residential_commercial",
    "Shop & house": "mixed_residential_commercial",
    "Vacant": "vacant", "Parking ramp": "parking",
    "Commercial exempt": "institutional", "Residential exempt": "institutional", "Agricultural exempt": "institutional",
    "Commercial Exempt Condo": "institutional", "Church": "institutional", "School": "institutional",
    "Hospital": "institutional", "Community center": "institutional",
    "Golf course": "park_open_space", "Golf -mini & drive": "park_open_space", "Conservancy vacant": "park_open_space",
    "Agricultural": "agricultural", "Agriculture vacant": "agricultural",
    "Manufacturing": "industrial", "Gravel quarry": "industrial", "Asphalt plant": "industrial",
    "Lumber company": "industrial", "Tank storage": "industrial", "Terminal, truck": "industrial",
    "Television station": "commercial", "Radio station": "commercial",
}
MAD_CONDO_NOTATION = {"condominium-notation"}


def mad_use_class(use) -> str:
    u = str(use).strip() if pd.notna(use) else ""
    if u in MAD_USE:
        return MAD_USE[u]
    lu = u.lower()
    if "condo" in lu:
        return "condominium"
    if "parking lot" in lu:
        return "parking"
    if "vacant" in lu:
        return "vacant"
    if lu.startswith("warehouse") or lu.startswith("warehse"):
        return "industrial"
    return "commercial" if u else "other_unknown"


# ----------------------------------------------------------------------------- stops and bands

def stop_points():
    import geopandas as gpd

    s = pd.read_csv(REFERENCE / "tod_stops.csv", dtype={"stop_id": str, "ntd_id": str})
    g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs=4326).to_crs(CRS_M)
    return {"rapid": g[g.flag_a_rapid == 1], "bus15": g[g.flag_b_15min == 1], "bus20": g[g.flag_c_20min == 1]}


def nearest_distance(points, stops) -> np.ndarray:
    """Distance (m) from each point to the nearest stop; inf beyond 1 mile."""
    from shapely import STRtree

    if len(stops) == 0:
        return np.full(len(points), np.inf)
    tree = STRtree(stops.geometry.values)
    idx, dist = tree.query_nearest(points.values, max_distance=C.MILE_M, return_distance=True, all_matches=False)
    out = np.full(len(points), np.inf)
    out[idx[0]] = dist
    return out


def assign_bands(points, stops) -> pd.Series:
    dr = nearest_distance(points, stops["rapid"])
    d15 = nearest_distance(points, stops["bus15"])
    d20 = nearest_distance(points, stops["bus20"])
    return pd.Series([C.assign_band(a, b, c) for a, b, c in zip(dr, d15, d20)], index=points.index)


# ----------------------------------------------------------------------------- parcels

def group_by_outline(g, key_cols: dict) -> "pd.DataFrame":
    """Collapse parcels that share an identical outline (condominium units stacked on one lot) so land
    is counted once; homes are summed, other fields come from the record with the most homes."""
    g = g.copy()
    g["_wkb"] = g.geometry.apply(lambda x: x.wkb if x is not None else None)
    g = g[g["_wkb"].notna()]
    g = g.sort_values("homes", ascending=False, kind="stable")
    agg = {"homes": "sum", "geometry": "first", **{c: "first" for c in key_cols}}
    out = g.groupby("_wkb", sort=False).agg(agg).reset_index(drop=True)
    out["records"] = g.groupby("_wkb", sort=False).size().to_numpy()
    return out


def load_milwaukee():
    import geopandas as gpd

    v = gpd.read_file(D / "v12_milwaukee.geojson", columns=["PARCELID", "PLACENAME"])
    v = v[v.PLACENAME == "CITY OF MILWAUKEE"].to_crs(CRS_M)
    m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", dtype=str,
                    usecols=["TAXKEY", "NR_UNITS", "LAND_USE", "LAND_USE_GP", "ZONING"])
    m["units"] = pd.to_numeric(m.NR_UNITS, errors="coerce").fillna(0)
    # Homes: residential land uses (codes 88xx) only. Hotel rooms and units recorded on commercial,
    # parking and other land-use records are not homes (WI_CAPACITY_DATA.md section 4).
    res = m.LAND_USE.fillna("").str.startswith("88") & (m.LAND_USE_GP != "12")
    m["homes"] = np.where(res, m.units, 0.0)
    m = m.drop_duplicates("TAXKEY")
    v = v.merge(m[["TAXKEY", "homes", "LAND_USE", "LAND_USE_GP", "ZONING"]], left_on="PARCELID", right_on="TAXKEY", how="left")
    v["matched"] = v.TAXKEY.notna()
    v["homes"] = v.homes.fillna(0.0)
    v["use_class"] = [mke_use_class(g, lu) if ok else "other_unknown" for g, lu, ok in zip(v.LAND_USE_GP, v.LAND_USE, v.matched)]
    p = group_by_outline(v, {"ZONING": 1, "use_class": 1, "matched": 1})
    p = gpd.GeoDataFrame(p, geometry="geometry", crs=CRS_M)
    p["pt"] = p.geometry.representative_point()
    # Zoning missing from MPROP (or no MPROP match): take the city zoning polygon under the parcel.
    z = gpd.read_file(D / "mke_zoning.geojson", columns=["Zoning"]).to_crs(CRS_M)
    need = p.ZONING.isna() | (p.ZONING.astype(str).str.strip() == "")
    if need.any():
        pts = gpd.GeoDataFrame({"i": p.index[need]}, geometry=p.loc[need, "pt"].values, crs=CRS_M)
        j = gpd.sjoin(pts, z, how="left", predicate="within").drop_duplicates("i").set_index("i")
        p.loc[need, "ZONING"] = j.Zoning.reindex(p.index[need]).values
    p["zoning_source"] = np.where(need, "zoning layer", "MPROP")
    p["district"] = p.ZONING.fillna("").astype(str).str.strip()
    p["in_overlay"] = False
    return p


def mad_base_district(zoning_all, known: set[str]) -> str:
    if zoning_all is None or (isinstance(zoning_all, float) and np.isnan(zoning_all)):
        return ""
    for t in str(zoning_all).split(","):
        t = t.strip()
        if t in known:
            return t
    return ""


def load_madison(known: set[str]):
    import geopandas as gpd

    g = gpd.read_file(RAW / "madison_parcels" / "tax_parcels.geojson",
                      columns=["PropertyUse", "TotalDwellingUnits", "ZoningAll"]).to_crs(CRS_M)
    g["units"] = pd.to_numeric(g.TotalDwellingUnits, errors="coerce").fillna(0)
    # Condominium notation records describe the whole condominium; their homes are already on the unit records.
    notation = g.PropertyUse.fillna("").str.lower().isin(MAD_CONDO_NOTATION)
    g["homes"] = np.where(notation, 0.0, g.units)
    g["use_class"] = [mad_use_class(u) for u in g.PropertyUse]
    g["district"] = [mad_base_district(z, known) for z in g.ZoningAll]
    # A condominium lot carries several records: keep the residential reading when any record has homes.
    p = group_by_outline(g, {"district": 1, "use_class": 1, "PropertyUse": 1})
    p = gpd.GeoDataFrame(p, geometry="geometry", crs=CRS_M)
    condo = p.PropertyUse.fillna("").str.lower().str.contains("condo") | (p.records > 1)
    p.loc[condo & (p.homes > 0) & ~p.use_class.isin(["multifamily", "mixed_residential_commercial"]), "use_class"] = "condominium"
    p["pt"] = p.geometry.representative_point()
    z = gpd.read_file(D / "mad_zoning.geojson", columns=["ZONING_CODE"]).to_crs(CRS_M)
    need = p.district == ""
    if need.any():
        pts = gpd.GeoDataFrame({"i": p.index[need]}, geometry=p.loc[need, "pt"].values, crs=CRS_M)
        j = gpd.sjoin(pts, z, how="left", predicate="within").drop_duplicates("i").set_index("i")
        p.loc[need, "district"] = [mad_base_district(x, known) for x in j.ZONING_CODE.reindex(p.index[need])]
    p["zoning_source"] = np.where(need, "zoning layer", "parcel ZoningAll")
    tod = gpd.read_file(RAW / "madison_tod" / "tod_boundary.geojson").to_crs(CRS_M).geometry.union_all()
    p["in_overlay"] = p["pt"].within(tod)
    p["dist_overlay_m"] = p["pt"].distance(tod)
    return p


def read_rules(name: str) -> list[dict]:
    with open(REFERENCE / f"tod_zoning_rules_{name}.csv", newline="") as f:
        return list(csv.DictReader(f))


# ----------------------------------------------------------------------------- capacity table

def compute(p, city: str, rules_rows: list[dict] | None, stops, sqft_per_home: float | None = None,
            county: str = "") -> pd.DataFrame:
    """Per-lot capacity for one place. rules_rows None = zoning not coded (suburb fallback: current
    allowance = existing homes). Capacity is computed at the measured floor area per home and again at
    the 1,000 sq ft sensitivity."""
    sq = sqft_per_home or C.sqft_per_home_for(city)
    sq_s = C.SENSITIVITY_SQFT_PER_HOME
    p = p.copy()
    p["acres"] = p.geometry.area / M2_PER_ACRE
    p["band"] = assign_bands(p["pt"], stops)
    p = p[p.band.notna()]
    if rules_rows is not None:
        tabs = {(o, q): C.rule_table(rules_rows, tod_overlay=o, sqft_per_home=q) for o in (False, True) for q in (sq, sq_s)}
    rec = []
    for r in p.itertuples(index=False):
        if rules_rows is None:
            res = C.fallback_capacity(r.acres, r.band, r.use_class, r.homes, sqft_per_home=sq)
            res_s = C.fallback_capacity(r.acres, r.band, r.use_class, r.homes, sqft_per_home=sq_s)
            meta = ("not_coded", "existing_density_fallback", "fallback")
        else:
            rule = tabs[(bool(r.in_overlay), sq)].get(r.district)
            rule_s = tabs[(bool(r.in_overlay), sq_s)].get(r.district)
            res = C.parcel_capacity(r.acres, r.band, rule, r.use_class, r.homes, sqft_per_home=sq)
            res_s = C.parcel_capacity(r.acres, r.band, rule_s, r.use_class, r.homes, sqft_per_home=sq_s)
            meta = (rule.zoning_class, rule.rule_type, rule.status) if rule else ("not_coded", "not_coded", "")
        rec.append((*meta, res.eligible, res.current_allowed_homes, res.law_allowed_homes, res.capacity_gain,
                    res.added_floor_area_sqft, res_s.capacity_gain))
    cols = ["zoning_class", "rule_type", "rule_status", "eligible", "current_allowed_homes", "law_allowed_homes",
            "capacity_gain", "added_floor_area_sqft", "capacity_gain_sqft1000"]
    out = pd.concat([p.reset_index(drop=True), pd.DataFrame(rec, columns=cols)], axis=1)
    if "city" not in out:
        out["city"] = city
    if "county" not in out:
        out["county"] = county
    out["zoning_coded"] = int(rules_rows is not None)
    out["sqft_per_home"] = sq
    out["district"] = out.district.replace("", "(none)") if "district" in out else "(not coded)"
    if "in_overlay" not in out:
        out["in_overlay"] = False
    return out


def aggregate(parcels: pd.DataFrame) -> pd.DataFrame:
    x = parcels.copy()
    x["eligible_acres"] = np.where(x.eligible, x.acres, 0.0)
    x["existing_homes_eligible"] = np.where(x.eligible, x.homes, 0.0)
    x["acres_in_overlay"] = np.where(x.in_overlay, x.acres, 0.0)
    x["eligible_acres_in_overlay"] = np.where(x.in_overlay & x.eligible, x.acres, 0.0)
    x["capacity_gain_excl_single_family"] = np.where(x.use_class.isin(SINGLE_FAMILY_USES), 0.0, x.capacity_gain)
    keys = ["city", "county", "zoning_coded", "sqft_per_home", "band", "district", "zoning_class", "rule_type",
            "rule_status", "use_class", "eligible"]
    a = x.groupby(keys, dropna=False).agg(
        lots=("acres", "size"), acres=("acres", "sum"), eligible_acres=("eligible_acres", "sum"),
        existing_homes=("homes", "sum"), existing_homes_eligible=("existing_homes_eligible", "sum"),
        current_allowed_homes=("current_allowed_homes", "sum"), law_allowed_homes=("law_allowed_homes", "sum"),
        capacity_gain=("capacity_gain", "sum"), capacity_gain_sqft1000=("capacity_gain_sqft1000", "sum"),
        capacity_gain_excl_single_family=("capacity_gain_excl_single_family", "sum"),
        added_floor_area_sqft=("added_floor_area_sqft", "sum"),
        acres_in_overlay=("acres_in_overlay", "sum"), eligible_acres_in_overlay=("eligible_acres_in_overlay", "sum"),
    ).reset_index()
    a["eligible"] = a.eligible.astype(int)
    law = C.MODELLED_LAW
    a["law_homes_per_acre"] = [law[b].homes_per_acre for b in a.band]
    a["law_far"] = [law[b].far for b in a.band]
    a["law_height_ft"] = [law[b].height_ft for b in a.band]
    a["law_homes_per_acre_effective"] = [round(C.law_homes_per_acre(b, sqft_per_home=q), 2) for b, q in zip(a.band, a.sqft_per_home)]
    for d, bands in C.DEFINITION_BANDS.items():
        a[f"in_{d}"] = a.band.isin(bands).astype(int)
    a["share_acres_in_tod_overlay"] = np.where(a.acres > 0, a.acres_in_overlay / a.acres, 0.0)
    band_order = {b: i for i, b in enumerate(C.BANDS)}
    a["_coded"] = -a.zoning_coded
    a = a.sort_values(["_coded", "city", "band", "district", "use_class"],
                      key=lambda s: s.map(band_order) if s.name == "band" else s).drop(columns="_coded")
    cols = ["city", "county", "zoning_coded", "band", "in_main", "in_high", "in_b_half", "in_c_half",
            "law_homes_per_acre", "law_far", "law_height_ft", "sqft_per_home", "law_homes_per_acre_effective",
            "district", "zoning_class", "rule_type", "rule_status", "use_class", "eligible", "lots", "acres",
            "eligible_acres", "existing_homes", "existing_homes_eligible", "current_allowed_homes", "law_allowed_homes",
            "capacity_gain", "capacity_gain_sqft1000", "capacity_gain_excl_single_family", "added_floor_area_sqft",
            "acres_in_overlay", "eligible_acres_in_overlay", "share_acres_in_tod_overlay"]
    a = a[cols]
    for c in ["acres", "eligible_acres", "acres_in_overlay", "eligible_acres_in_overlay"]:
        a[c] = a[c].round(3)
    for c in ["existing_homes", "existing_homes_eligible", "current_allowed_homes", "law_allowed_homes", "capacity_gain",
              "capacity_gain_sqft1000", "capacity_gain_excl_single_family"]:
        a[c] = a[c].round(1)
    a["added_floor_area_sqft"] = a.added_floor_area_sqft.round(0)
    a["share_acres_in_tod_overlay"] = a.share_acres_in_tod_overlay.round(4)
    return a


def summary(agg: pd.DataFrame) -> pd.DataFrame:
    """Totals by definition for Milwaukee city, Madison city, the not-coded places, and the state."""
    out = []
    groups = {"Milwaukee city": agg.city == "Milwaukee city", "Madison city": agg.city == "Madison city",
              "Not coded (fallback places)": agg.zoning_coded == 0, "State total": agg.city.notna()}
    cols = ["acres", "eligible_acres", "existing_homes", "existing_homes_eligible", "current_allowed_homes",
            "law_allowed_homes", "capacity_gain", "capacity_gain_sqft1000", "capacity_gain_excl_single_family"]
    for d in C.DEFINITION_BANDS:
        for name, mask in groups.items():
            s = agg[mask & (agg[f"in_{d}"] == 1)]
            row = {"definition": d, "area": name, "places": s.city.nunique()}
            row.update({c: round(float(s[c].sum()), 1) for c in cols})
            out.append(row)
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- not-coded places (suburbs)

def v12_use_class(propclass, auxclass) -> str:
    """V12 class -> use class. PROPCLASS: 1 residential, 2 commercial, 3 manufacturing, 4 agricultural,
    5 undeveloped, 5M agricultural forest, 6 productive forest, 7 other; AUXCLASS X1-X4 exempt."""
    pc = {t.strip().upper() for t in str(propclass or "").split(",") if t.strip()}
    ax = {t.strip().upper() for t in str(auxclass or "").split(",") if t.strip()}
    if "1" in pc and "2" in pc:
        return "mixed_residential_commercial"
    if "1" in pc:
        return "residential"
    if "2" in pc:
        return "commercial"
    if any(t.startswith("X") for t in ax):
        return "institutional"
    if "3" in pc:
        return "industrial"
    if pc & {"4", "5M", "6"}:
        return "agricultural"
    if "5" in pc:
        return "vacant"
    if "7" in pc:
        return "other"
    return "other_unknown"


CODED_PLACES = {"CITY OF MILWAUKEE", "CITY OF MADISON"}
SF_EST_MAX_HOMES = 1.5
SINGLE_FAMILY_USES = {"single_family", "single_family_est"}


def place_label(placename: str) -> str:
    """'CITY OF WEST ALLIS' -> 'West Allis city' (Census naming, as in tod_near_stop_homes_by_muni.csv)."""
    s = "" if placename is None or (isinstance(placename, float) and np.isnan(placename)) else str(placename).strip()
    for kind in ("CITY", "VILLAGE", "TOWN"):
        if s.startswith(f"{kind} OF "):
            return s[len(kind) + 4:].title() + " " + kind.lower()
    return s.title() or "(unknown)"


def load_fallback_places():
    """V12 parcels outside the two coded cities, with 2020 census block homes shared out to lots.

    Each block's HOUSING20 goes to the lots whose representative point lies in the block, in proportion
    to area: residential- or commercial-class lots (apartments of 4+ homes are class 2), else all lots. Homes of
    blocks with no fetched lot are not placed (reported)."""
    import glob

    import geopandas as gpd

    parts = []
    for f in sorted(glob.glob(str(D / "v12_*.geojson"))):
        g = gpd.read_file(f, columns=["PLACENAME", "CONAME", "PROPCLASS", "AUXCLASS"])
        parts.append(g[~g.PLACENAME.isin(CODED_PLACES)])
    v = pd.concat(parts, ignore_index=True)
    v = gpd.GeoDataFrame(v, geometry="geometry", crs=4326).to_crs(CRS_M)
    v["use_class"] = [v12_use_class(a, b) for a, b in zip(v.PROPCLASS, v.AUXCLASS)]
    v["city"] = [place_label(x) for x in v.PLACENAME]
    v["county"] = v.CONAME.fillna("").str.title() + " County"
    v["homes"] = 0.0
    p = group_by_outline(v, {"city": 1, "county": 1, "use_class": 1})
    p = gpd.GeoDataFrame(p, geometry="geometry", crs=CRS_M)
    p["pt"] = p.geometry.representative_point()
    p["acres_m2"] = p.geometry.area
    blocks = gpd.read_file(f"zip://{BLOCKS}", columns=["GEOID20", "HOUSING20"],
                           bbox=tuple(gpd.GeoSeries(p["pt"], crs=CRS_M).to_crs(4269).total_bounds)).to_crs(CRS_M)
    blocks = blocks[blocks.HOUSING20.astype(float) > 0]
    pts = gpd.GeoDataFrame({"i": p.index}, geometry=p["pt"].values, crs=CRS_M)
    j = gpd.sjoin(pts, blocks[["GEOID20", "HOUSING20", "geometry"]], how="inner", predicate="within").drop_duplicates("i")
    j = pd.DataFrame(j.drop(columns="geometry"))
    j["lot_m2"] = p.loc[j.i, "acres_m2"].values
    j["use"] = p.loc[j.i, "use_class"].values
    j["h"] = j.HOUSING20.astype(float)
    homes = pd.Series(0.0, index=p.index)
    # Wisconsin assesses apartment buildings of 4+ homes as commercial (class 2), so residential and
    # commercial lots share a block's homes.
    tiers = [C.FALLBACK_ELIGIBLE_USES, None]
    placed = 0.0
    for geoid, grp in j.groupby("GEOID20"):
        for t in tiers:
            sel = grp if t is None else grp[grp.use.isin(t)]
            if len(sel) and sel.lot_m2.sum() > 0:
                homes.loc[sel.i.values] += sel.h.iloc[0] * sel.lot_m2.values / sel.lot_m2.sum()
                placed += sel.h.iloc[0]
                break
    p["homes"] = homes
    # V12 has no single-family flag. For the single-family-excluded sensitivity (G2-8), a residential-class
    # lot holding less than 1.5 of its block's homes is treated as an estimated single-family lot.
    p.loc[(p.use_class == "residential") & (p.homes < SF_EST_MAX_HOMES), "use_class"] = "single_family_est"
    p["district"] = "(not coded)"
    p["in_overlay"] = False
    p.attrs["block_homes_placed"] = placed
    return p


# ----------------------------------------------------------------------------- Madison test land layer

def madison_test_land(p, rules_rows: list[dict]) -> pd.DataFrame:
    """Eligible land for the pre-registered Madison test (MADISON_TEST_PREREG.md section 2). Whole city,
    not just station areas. Eligible: residential, mixed-use or commercial zoning (incl. planned
    development), not an excluded use, and not a single-family use. Land only: no permits are read."""
    base = C.rule_table(rules_rows)
    rows = []
    for r in p.itertuples(index=False):
        rule = base.get(r.district)
        zc = rule.zoning_class if rule else "not_coded"
        elig = rule is not None and rule.rule_type != "not_coded" and C.is_eligible(zc, r.use_class, rule.rule_type)
        if r.in_overlay:
            area = "overlay"
        elif r.dist_overlay_m <= C.QUARTER_M:
            area = "ring_quarter_mile_outside"
        else:
            area = "rest_of_city"
        rows.append((area, r.geometry.area / M2_PER_ACRE, r.homes, elig, r.use_class == "single_family"))
    x = pd.DataFrame(rows, columns=["area", "acres", "homes", "elig", "sf"])
    x["prereg"] = x.elig & ~x.sf
    out = []
    for area in ["overlay", "ring_quarter_mile_outside", "rest_of_city"]:
        s = x[x.area == area]
        out.append({"area": area, "lots": len(s), "acres": round(s.acres.sum(), 3),
                    "eligible_lots": int(s.prereg.sum()), "eligible_acres": round(s.acres[s.prereg].sum(), 3),
                    "existing_homes_on_eligible": round(s.homes[s.prereg].sum(), 1),
                    "single_family_acres_excluded": round(s.acres[s.elig & s.sf].sum(), 3),
                    "eligible_acres_incl_single_family": round(s.acres[s.elig].sum(), 3)})
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- floor area per home

FLOOR_YEARS = (2018, 2025)
MAD_MF_USES = {"FIVE AND MORE FAMILY", "CONDOMINIUMS"}
MAD_NOT_NEW = r"CONVERT|ALTERATION|ADD KITCHEN|REMODEL|INTERIOR"


def madison_new_multifamily() -> "pd.DataFrame":
    """Madison new-construction permits (BLDNCC, BLDNRC) for 5+ home buildings, issued 2018-2025, citywide.
    Reads only permit number, use, BLDG_SQFT, Dwell (Textbox13), description and issue date: no owner
    or contractor fields. Never split by TOD overlay (that is the pre-registered test)."""
    import glob
    import re

    rows = []
    for f in sorted(glob.glob(str(RAW / "madison_permits" / "construction_summary_20*.csv"))):
        with open(f, encoding="utf-8-sig", newline="") as fh:
            for r in csv.reader(fh):
                if r and re.match(r"^BLD(NCC|NRC)-\d{4}-\d+$", r[0]) and len(r) >= 11:
                    rows.append((r[0], r[1], r[3], r[6], r[9], r[10]))
    d = pd.DataFrame(rows, columns=["permit", "use", "sqft", "homes", "desc", "issued"]).drop_duplicates("permit")
    d["sqft"] = pd.to_numeric(d.sqft.str.replace(",", ""), errors="coerce")
    d["homes"] = pd.to_numeric(d.homes.str.replace(",", ""), errors="coerce")
    d["year"] = pd.to_datetime(d.issued, format="%m/%d/%Y", errors="coerce").dt.year
    keep = (d.homes >= 5) & d.year.between(*FLOOR_YEARS) & d.use.isin(MAD_MF_USES) & (d.sqft > 0) \
        & ~d.desc.str.upper().str.contains(MAD_NOT_NEW, regex=True)
    return d.loc[keep, ["sqft", "homes", "year"]]


def milwaukee_new_multifamily() -> "pd.DataFrame":
    """Milwaukee buildings with 5+ homes built 2018-2025 (MPROP YR_BUILT, BLDG_AREA, NR_UNITS; residential
    land uses 88xx). The city's permit file has no floor area or unit count, so the assessor record of
    the finished building is used instead."""
    m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", dtype=str,
                    usecols=["LAND_USE", "NR_UNITS", "BLDG_AREA", "YR_BUILT"])
    for c in ("NR_UNITS", "BLDG_AREA", "YR_BUILT"):
        m[c] = pd.to_numeric(m[c], errors="coerce")
    keep = m.YR_BUILT.between(*FLOOR_YEARS) & (m.NR_UNITS >= 5) & (m.BLDG_AREA > 0) \
        & m.LAND_USE.fillna("").str.startswith("88")
    return m.loc[keep].rename(columns={"BLDG_AREA": "sqft", "NR_UNITS": "homes", "YR_BUILT": "year"})[["sqft", "homes", "year"]]


def floor_area_per_home() -> pd.DataFrame:
    out = []
    parts = {"Milwaukee city": (milwaukee_new_multifamily(), "MPROP 2026: buildings with 5+ homes built 2018-2025, BLDG_AREA / NR_UNITS"),
             "Madison city": (madison_new_multifamily(), "Construction Summary BLDNCC/BLDNRC permits issued 2018-2025, 5+ homes, new buildings: BLDG_SQFT / Dwell")}
    parts["pooled"] = (pd.concat([p[0] for p in parts.values()]), "Both cities' buildings together")
    for name, (d, src) in parts.items():
        spu = d.sqft / d.homes
        out.append({"area": name, "source": src, "years": f"{FLOOR_YEARS[0]}-{FLOOR_YEARS[1]}", "buildings": len(d),
                    "homes": int(d.homes.sum()), "median_sqft_per_home": round(float(spu.median()), 0),
                    "p25_sqft_per_home": round(float(spu.quantile(0.25)), 0),
                    "p75_sqft_per_home": round(float(spu.quantile(0.75)), 0),
                    "home_weighted_sqft_per_home": round(float(d.sqft.sum() / d.homes.sum()), 0)})
    return pd.DataFrame(out)


def main() -> None:
    floor = floor_area_per_home()
    floor.to_csv(OUT_FLOOR, index=False, lineterminator="\n")
    for r in floor.itertuples(index=False):
        coded = C.MEASURED_SQFT_PER_HOME[r.area]
        if abs(r.median_sqft_per_home - coded) > 1:
            print(f"WARNING: measured {r.area} {r.median_sqft_per_home} sq ft differs from capacity.py {coded}")
    stops = stop_points()
    mke_rules, mad_rules = read_rules("milwaukee"), read_rules("madison")
    print("Milwaukee parcels ...", flush=True)
    mke = load_milwaukee()
    print("Madison parcels ...", flush=True)
    mad = load_madison({r["district"] for r in mad_rules})
    print("Fallback places ...", flush=True)
    sub = load_fallback_places()
    parcels = pd.concat([compute(mke, "Milwaukee city", mke_rules, stops, county="Milwaukee County"),
                         compute(mad, "Madison city", mad_rules, stops, county="Dane County"),
                         compute(sub, "fallback", None, stops, sqft_per_home=C.MEASURED_SQFT_PER_HOME["pooled"])],
                        ignore_index=True)
    agg = aggregate(parcels)
    agg.to_csv(OUT, index=False, lineterminator="\n")
    summ = summary(agg)
    summ.to_csv(OUT_SUMMARY, index=False, lineterminator="\n")
    test = madison_test_land(mad, mad_rules)
    test.to_csv(OUT_TEST, index=False, lineterminator="\n")
    print(f"wrote {OUT} ({len(agg)} rows), {OUT_SUMMARY}, {OUT_TEST}, {OUT_FLOOR}")
    print(floor.to_string(index=False))
    print("fallback block homes placed on lots:", round(sub.attrs.get("block_homes_placed", 0)))
    for city, s in parcels[parcels.zoning_coded == 1].groupby("city"):
        print(city, "lots in bands:", len(s), "zoning source:", s.zoning_source.value_counts().to_dict(),
              "not coded acres:", round(s.acres[s.rule_type == "not_coded"].sum(), 1))
    pd.set_option("display.width", 250)
    print(summ.to_string(index=False))
    print(test.to_string(index=False))


if __name__ == "__main__":
    main()

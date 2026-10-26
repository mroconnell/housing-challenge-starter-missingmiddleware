"""Build the TOD station-area land and zoning tables for the City of Milwaukee and the City of Madison.

    uv run --all-extras python scripts/fetch_tod_parcels_zoning.py   # once, needs network
    uv run --all-extras python scripts/build_tod_station_areas.py   # offline

In:  reference/tod_stops.csv (qualifying stops), reference/tod_zoning_rules_{milwaukee,madison}.csv
     data/raw/tod_capacity/{v12_milwaukee.geojson, mke_zoning.geojson, mad_zoning.geojson}
     data/raw/milwaukee_mprop/mprop.csv (homes, zoning and land use per tax key)
     data/raw/madison_parcels/tax_parcels.geojson (homes, zoning and use per parcel, with outlines)
     data/raw/madison_tod/tod_boundary.geojson (TOD overlay)
Out: reference/tod_station_areas.csv  city x band x zoning district x use class (never parcel-level)
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

def compute(p, city: str, rules_rows: list[dict], stops) -> pd.DataFrame:
    base = C.rule_table(rules_rows, tod_overlay=False)
    over = C.rule_table(rules_rows, tod_overlay=True)
    p = p.copy()
    p["acres"] = p.geometry.area / M2_PER_ACRE
    p["band"] = assign_bands(p["pt"], stops)
    p = p[p.band.notna()]
    rec = []
    for r in p.itertuples(index=False):
        rule = (over if r.in_overlay else base).get(r.district)
        res = C.parcel_capacity(r.acres, r.band, rule, r.use_class, r.homes)
        rec.append((rule.zoning_class if rule else "not_coded", rule.rule_type if rule else "not_coded",
                    rule.status if rule else "", res.eligible, res.current_allowed_homes, res.law_allowed_homes,
                    res.capacity_gain, res.added_floor_area_sqft))
    cols = ["zoning_class", "rule_type", "rule_status", "eligible", "current_allowed_homes", "law_allowed_homes",
            "capacity_gain", "added_floor_area_sqft"]
    out = pd.concat([p.reset_index(drop=True), pd.DataFrame(rec, columns=cols)], axis=1)
    out["city"] = city
    out["district"] = out.district.replace("", "(none)")
    return out


def aggregate(parcels: pd.DataFrame) -> pd.DataFrame:
    x = parcels.copy()
    x["eligible_acres"] = np.where(x.eligible, x.acres, 0.0)
    x["existing_homes_eligible"] = np.where(x.eligible, x.homes, 0.0)
    x["acres_in_overlay"] = np.where(x.in_overlay, x.acres, 0.0)
    x["eligible_acres_in_overlay"] = np.where(x.in_overlay & x.eligible, x.acres, 0.0)
    keys = ["city", "band", "district", "zoning_class", "rule_type", "rule_status", "use_class", "eligible"]
    a = x.groupby(keys, dropna=False).agg(
        lots=("acres", "size"), acres=("acres", "sum"), eligible_acres=("eligible_acres", "sum"),
        existing_homes=("homes", "sum"), existing_homes_eligible=("existing_homes_eligible", "sum"),
        current_allowed_homes=("current_allowed_homes", "sum"), law_allowed_homes=("law_allowed_homes", "sum"),
        capacity_gain=("capacity_gain", "sum"), added_floor_area_sqft=("added_floor_area_sqft", "sum"),
        acres_in_overlay=("acres_in_overlay", "sum"), eligible_acres_in_overlay=("eligible_acres_in_overlay", "sum"),
    ).reset_index()
    a["eligible"] = a.eligible.astype(int)
    law = C.MODELLED_LAW
    a["law_homes_per_acre"] = [law[b].homes_per_acre for b in a.band]
    a["law_far"] = [law[b].far for b in a.band]
    a["law_height_ft"] = [law[b].height_ft for b in a.band]
    for d, bands in C.DEFINITION_BANDS.items():
        a[f"in_{d}"] = a.band.isin(bands).astype(int)
    a["share_acres_in_tod_overlay"] = np.where(a.acres > 0, a.acres_in_overlay / a.acres, 0.0)
    band_order = {b: i for i, b in enumerate(C.BANDS)}
    a = a.sort_values(["city", "band", "district", "use_class"], key=lambda s: s.map(band_order) if s.name == "band" else s)
    cols = ["city", "band", "in_main", "in_high", "in_b_half", "in_c_half", "law_homes_per_acre", "law_far", "law_height_ft",
            "district", "zoning_class", "rule_type", "rule_status", "use_class", "eligible", "lots", "acres",
            "eligible_acres", "existing_homes", "existing_homes_eligible", "current_allowed_homes", "law_allowed_homes",
            "capacity_gain", "added_floor_area_sqft", "acres_in_overlay", "eligible_acres_in_overlay",
            "share_acres_in_tod_overlay"]
    a = a[cols]
    for c in ["acres", "eligible_acres", "acres_in_overlay", "eligible_acres_in_overlay"]:
        a[c] = a[c].round(3)
    for c in ["existing_homes", "existing_homes_eligible", "current_allowed_homes", "law_allowed_homes", "capacity_gain"]:
        a[c] = a[c].round(1)
    a["added_floor_area_sqft"] = a.added_floor_area_sqft.round(0)
    a["share_acres_in_tod_overlay"] = a.share_acres_in_tod_overlay.round(4)
    return a


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


def main() -> None:
    stops = stop_points()
    mke_rules, mad_rules = read_rules("milwaukee"), read_rules("madison")
    print("Milwaukee parcels ...", flush=True)
    mke = load_milwaukee()
    print("Madison parcels ...", flush=True)
    mad = load_madison({r["district"] for r in mad_rules})
    parcels = pd.concat([compute(mke, "Milwaukee city", mke_rules, stops),
                         compute(mad, "Madison city", mad_rules, stops)], ignore_index=True)
    agg = aggregate(parcels)
    agg.to_csv(OUT, index=False, lineterminator="\n")
    test = madison_test_land(mad, mad_rules)
    test.to_csv(OUT_TEST, index=False, lineterminator="\n")
    print(f"wrote {OUT} ({len(agg)} rows) and {OUT_TEST}")
    # Coverage diagnostics (printed only; parcel-level data never written)
    for city, s in parcels.groupby("city"):
        print(city, "lots in bands:", len(s), "zoning source:", s.zoning_source.value_counts().to_dict(),
              "not coded acres:", round(s.acres[s.rule_type == "not_coded"].sum(), 1))
        if "matched" in s:
            print("  MPROP-matched lots:", round(s.matched.astype(float).mean(), 4))
    for d, bands in C.DEFINITION_BANDS.items():
        s = agg[agg.band.isin(bands)].groupby("city")[["eligible_acres", "existing_homes", "existing_homes_eligible",
                                                         "capacity_gain"]].sum().round(0)
        print(d, s.to_dict("index"))
    print(test.to_string(index=False))


if __name__ == "__main__":
    main()

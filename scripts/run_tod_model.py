"""Run the TOD Gate 3 model (docs/tod/GATE3_MODEL_SPEC.md; method and results in docs/tod/MODEL.md).

    uv run --all-extras python scripts/run_tod_model.py            # rebuilds the lot layer (~2 min)
    uv run --all-extras python scripts/run_tod_model.py --cached   # reuses data/processed/tod_model/lots.parquet

In:  reference/tod_station_areas.csv, tod_case_estimates.csv, tod_case_rates_by_year.csv,
     tod_near_stop_homes_by_muni.csv, housing_baseline_by_area.csv, housing_baseline_sensitivity_published.csv,
     adu_model_district_crosswalk.csv, tod_zoning_rules_{milwaukee,madison}.csv
     raw (git-ignored): the station-area parcel inputs (see scripts/build_tod_station_areas.py) plus
     V12 land values, Milwaukee MPROP land values and year built, 2024 TIGER tracts,
     ACS 2020-2024 B25064 and B25111, and data/raw/tod_model/ (HUD 2024 TDC table, CBRE H1 2024 cap
     rate survey, IREM 2024 income/expense summary; hashes in data/raw/tod_model/manifest.json).
Out: reference/tod_madison_test_predictions.csv  both methods' blind predictions for the Madison test
     reference/tod_model_statewide.csv              state x method x scenario x year
     reference/tod_model_by_area.csv                municipality x method x scenario (five-year and by year)
     reference/tod_model_by_county.csv, tod_model_by_assembly_district.csv, tod_model_by_senate_district.csv
     reference/tod_model_sensitivities.csv          section 7 sensitivities, five-year state totals
     reference/tod_model_params.csv                 every parameter with its source
     reference/tod_model_feasibility.csv            method B diagnostics by city

Privacy: no Madison building permit is read by this script (the Madison test is blind). Parcel ids are
used only to join raw files in memory; no committed output holds a parcel id or a lot-level row.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import capacity as C  # noqa: E402
from missing_middleware.tod import model as M  # noqa: E402

_spec = importlib.util.spec_from_file_location("build_tod_station_areas", ROOT / "scripts" / "build_tod_station_areas.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

PROC = ROOT / "data" / "processed" / "tod_model"
LOTS = PROC / "lots.parquet"
MKE_ALL = PROC / "milwaukee_all_lots.parquet"
MAD_ALL = PROC / "madison_all_lots.parquet"
RAWM = RAW / "tod_model"
CRS_M = B.CRS_M
M2_PER_ACRE = B.M2_PER_ACRE

# ----------------------------------------------------------------------------- parameters (sources in tod_model_params.csv)

# HUD 2024 Unit TDC limits (Nov 2024), elevator building, 2-bedroom (900 sq ft) housing construction
# cost (HCC). HCC per sq ft is the same for every bedroom count in the table.
HUD_HCC_2BR_ELEVATOR = {"MILWAUKEE": 206_727, "MADISON": 204_973, "KENOSHA": 209_955, "EAU CLAIRE": 204_096}
HUD_TDC_2BR_ELEVATOR = {"MILWAUKEE": 330_764, "MADISON": 327_957, "KENOSHA": 335_928, "EAU CLAIRE": 326_554}
HUD_SQFT_2BR = 900.0
HUD_HCC_1BR_ELEVATOR = {"MILWAUKEE": 160_788, "MADISON": 159_424, "KENOSHA": 163_298, "EAU CLAIRE": 158_741}
COUNTY_HUD = {"Milwaukee County": "MILWAUKEE", "Waukesha County": "MILWAUKEE", "Ozaukee County": "MILWAUKEE",
              "Dane County": "MADISON", "Kenosha County": "KENOSHA", "Eau Claire County": "EAU CLAIRE"}
# CBRE U.S. Cap Rate Survey H1 2024, Multifamily Infill, Midwest, Milwaukee, Class A stabilized, H1 2024:
# 5.5% - 6%. Midpoint used. Madison is not in the survey; Milwaukee's is the only Wisconsin market.
CAP_RATE = 0.0575
CAP_RATE_RANGE = (0.055, 0.060)
# IREM Income/Expense IQ National Summary 2024 (2024 operating data), multifamily communities:
# total operating expenses $7,981.42 per unit (incl. taxes, insurance, management) / total gross
# rents $20,575 per unit.
IREM_OPEX_PER_UNIT = 7_981.42
IREM_GROSS_RENT_PER_UNIT = 20_575.0
OPEX_RATIO = IREM_OPEX_PER_UNIT / IREM_GROSS_RENT_PER_UNIT
TAKE_UP_MIN_HPA = 30.0
TAKE_UP_YEARS = (2018, 2025)
SEED = 20261026

ACS_RENT = RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b25064.dat"
ACS_RENT_BY_AGE = RAWM / "acsdt5y2024-b25111.dat"
TRACTS = RAW / "census_tiger_2024" / "tl_2024_55_tract.zip"


def hud_cost_per_sqft(county: str, table=HUD_HCC_2BR_ELEVATOR, sqft=HUD_SQFT_2BR) -> float:
    return table[COUNTY_HUD.get(county, "MILWAUKEE")] / sqft


# ----------------------------------------------------------------------------- ACS rents

def read_acs(path: Path, cols: list[str]) -> pd.DataFrame:
    d = pd.read_csv(path, sep="|", dtype=str, usecols=["GEO_ID", *cols])
    d = d[d.GEO_ID.str.startswith(("1400000US55", "0600000US55", "1600000US55", "0500000US55"))]
    for c in cols:
        v = pd.to_numeric(d[c], errors="coerce")
        d[c] = v.where(v > 0)
    return d.set_index("GEO_ID")


def rent_tables():
    r = read_acs(ACS_RENT, ["B25064_E001"])["B25064_E001"]
    a = read_acs(ACS_RENT_BY_AGE, ["B25111_E001", "B25111_E002"])
    tract = {k[9:]: v for k, v in r.items() if k.startswith("1400000US") and pd.notna(v)}
    cousub = {k[9:]: v for k, v in r.items() if k.startswith("0600000US") and pd.notna(v)}
    county = {k[9:]: v for k, v in r.items() if k.startswith("0500000US") and pd.notna(v)}
    ratio = {}
    for k, row in a.iterrows():
        if k.startswith("0600000US") and pd.notna(row.B25111_E001) and pd.notna(row.B25111_E002):
            ratio[k[9:]] = row.B25111_E002 / row.B25111_E001
    return tract, cousub, county, ratio


# ----------------------------------------------------------------------------- lot layer (land value, tract)

def group_lots(g, first_cols: list[str], sum_cols: list[str]):
    """As B.group_by_outline, but land value and new-building homes are summed over stacked records."""
    import geopandas as gpd

    g = g.copy()
    g["_wkb"] = g.geometry.apply(lambda x: x.wkb if x is not None else None)
    g = g[g["_wkb"].notna()].sort_values("homes", ascending=False, kind="stable")
    agg = {"homes": "sum", "geometry": "first", **{c: "first" for c in first_cols}, **{c: "sum" for c in sum_cols}}
    out = g.groupby("_wkb", sort=False).agg(agg).reset_index(drop=True)
    out["records"] = g.groupby("_wkb", sort=False).size().to_numpy()
    return gpd.GeoDataFrame(out, geometry="geometry", crs=CRS_M)


def load_milwaukee_lots():
    """B.load_milwaukee plus land value (MPROP C_A_LAND) and homes in 5+ home buildings built 2018-2025."""
    import geopandas as gpd

    v = gpd.read_file(B.D / "v12_milwaukee.geojson", columns=["PARCELID", "PLACENAME", "LNDVALUE"])
    v = v[v.PLACENAME == "CITY OF MILWAUKEE"].to_crs(CRS_M)
    m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", dtype=str,
                    usecols=["TAXKEY", "NR_UNITS", "LAND_USE", "LAND_USE_GP", "ZONING", "C_A_LAND", "YR_BUILT"])
    m["units"] = pd.to_numeric(m.NR_UNITS, errors="coerce").fillna(0)
    res = m.LAND_USE.fillna("").str.startswith("88") & (m.LAND_USE_GP != "12")
    m["homes"] = np.where(res, m.units, 0.0)
    yb = pd.to_numeric(m.YR_BUILT, errors="coerce")
    m["new5_homes"] = np.where(res & (m.units >= 5) & yb.between(*TAKE_UP_YEARS), m.units, 0.0)
    m["land_value"] = pd.to_numeric(m.C_A_LAND, errors="coerce")
    m = m.drop_duplicates("TAXKEY")
    v = v.merge(m[["TAXKEY", "homes", "new5_homes", "land_value", "LAND_USE", "LAND_USE_GP", "ZONING"]],
                left_on="PARCELID", right_on="TAXKEY", how="left")
    v["matched"] = v.TAXKEY.notna()
    v["homes"] = v.homes.fillna(0.0)
    v["new5_homes"] = v.new5_homes.fillna(0.0)
    v["land_value"] = v.land_value.fillna(pd.to_numeric(v.LNDVALUE, errors="coerce"))
    v["land_known"] = v.land_value.notna().astype(float)
    v["land_value"] = v.land_value.fillna(0.0)
    v["use_class"] = [B.mke_use_class(g, lu) if ok else "other_unknown" for g, lu, ok in zip(v.LAND_USE_GP, v.LAND_USE, v.matched)]
    p = group_lots(v, ["ZONING", "use_class", "matched"], ["land_value", "new5_homes", "land_known"])
    p["land_known"] = p.land_known > 0
    p["pt"] = p.geometry.representative_point()
    z = gpd.read_file(B.D / "mke_zoning.geojson", columns=["Zoning"]).to_crs(CRS_M)
    need = p.ZONING.isna() | (p.ZONING.astype(str).str.strip() == "")
    if need.any():
        pts = gpd.GeoDataFrame({"i": p.index[need]}, geometry=p.loc[need, "pt"].values, crs=CRS_M)
        j = gpd.sjoin(pts, z, how="left", predicate="within").drop_duplicates("i").set_index("i")
        p.loc[need, "ZONING"] = j.Zoning.reindex(p.index[need]).values
    p["district"] = p.ZONING.fillna("").astype(str).str.strip()
    p["in_overlay"] = False
    p["cousub"] = "5507953000"
    return p


def load_madison_lots(known: set[str]):
    """B.load_madison plus land value (V12 LNDVALUE, joined on the parcel number)."""
    import geopandas as gpd

    g = gpd.read_file(RAW / "madison_parcels" / "tax_parcels.geojson",
                      columns=["Parcel", "PropertyUse", "TotalDwellingUnits", "ZoningAll"]).to_crs(CRS_M)
    vd = gpd.read_file(B.D / "v12_dane.geojson", columns=["PARCELID", "LNDVALUE"], ignore_geometry=True)
    lv = pd.to_numeric(vd.LNDVALUE, errors="coerce").groupby(vd.PARCELID.astype(str)).sum()
    g["land_value"] = g.Parcel.astype(str).map(lv)
    g.attrs["land_match"] = float(g.land_value.notna().mean())
    g["land_known"] = g.land_value.notna().astype(float)
    g["land_value"] = g.land_value.fillna(0.0)
    g["units"] = pd.to_numeric(g.TotalDwellingUnits, errors="coerce").fillna(0)
    notation = g.PropertyUse.fillna("").str.lower().isin(B.MAD_CONDO_NOTATION)
    g["homes"] = np.where(notation, 0.0, g.units)
    g["use_class"] = [B.mad_use_class(u) for u in g.PropertyUse]
    g["district"] = [B.mad_base_district(z, known) for z in g.ZoningAll]
    g["new5_homes"] = 0.0
    p = group_lots(g, ["district", "use_class", "PropertyUse"], ["land_value", "new5_homes", "land_known"])
    p["land_known"] = p.land_known > 0
    condo = p.PropertyUse.fillna("").str.lower().str.contains("condo") | (p.records > 1)
    p.loc[condo & (p.homes > 0) & ~p.use_class.isin(["multifamily", "mixed_residential_commercial"]), "use_class"] = "condominium"
    p["pt"] = p.geometry.representative_point()
    z = gpd.read_file(B.D / "mad_zoning.geojson", columns=["ZONING_CODE"]).to_crs(CRS_M)
    need = p.district == ""
    if need.any():
        pts = gpd.GeoDataFrame({"i": p.index[need]}, geometry=p.loc[need, "pt"].values, crs=CRS_M)
        j = gpd.sjoin(pts, z, how="left", predicate="within").drop_duplicates("i").set_index("i")
        p.loc[need, "district"] = [B.mad_base_district(x, known) for x in j.ZONING_CODE.reindex(p.index[need])]
    tod = gpd.read_file(RAW / "madison_tod" / "tod_boundary.geojson").to_crs(CRS_M).geometry.union_all()
    p["in_overlay"] = p["pt"].within(tod)
    p["dist_overlay_m"] = p["pt"].distance(tod)
    p["cousub"] = "5502548000"
    p.attrs["land_match"] = g.attrs["land_match"]
    return p


def load_fallback_lots(muni: pd.DataFrame):
    """B.load_fallback_places with V12 land values summed per lot."""
    import glob

    import geopandas as gpd

    parts = []
    for f in sorted(glob.glob(str(B.D / "v12_*.geojson"))):
        g = gpd.read_file(f, columns=["PLACENAME", "CONAME", "PROPCLASS", "AUXCLASS", "LNDVALUE"])
        parts.append(g[~g.PLACENAME.isin(B.CODED_PLACES)])
    v = pd.concat(parts, ignore_index=True)
    v = gpd.GeoDataFrame(v, geometry="geometry", crs=4326).to_crs(CRS_M)
    v["use_class"] = [B.v12_use_class(a, b) for a, b in zip(v.PROPCLASS, v.AUXCLASS)]
    v["city"] = [B.place_label(x) for x in v.PLACENAME]
    v["county"] = v.CONAME.fillna("").str.title() + " County"
    v["homes"] = 0.0
    v["land_value"] = pd.to_numeric(v.LNDVALUE, errors="coerce")
    v["land_known"] = v.land_value.notna().astype(float)
    v["land_value"] = v.land_value.fillna(0.0)
    v["new5_homes"] = 0.0
    p = group_lots(v, ["city", "county", "use_class"], ["land_value", "new5_homes", "land_known"])
    p["land_known"] = p.land_known > 0
    # Homes from 2020 blocks, exactly as the station-area build: reuse its function on the same lots.
    ref = B.load_fallback_places()
    key = pd.Series(range(len(ref)), index=[g.wkb for g in ref.geometry])
    idx = [key.get(g.wkb) for g in p.geometry]
    ok = pd.notna(pd.Series(idx, dtype="float"))
    p["homes"] = [float(ref.homes.iloc[int(i)]) if pd.notna(i) else 0.0 for i in idx]
    p["use_class"] = [ref.use_class.iloc[int(i)] if pd.notna(i) else u for i, u in zip(idx, p.use_class)]
    p.attrs["matched_to_station_build"] = float(ok.mean())
    p["pt"] = p.geometry.representative_point()
    p["district"] = "(not coded)"
    p["in_overlay"] = False
    names = muni.set_index(["name", "county"]).area_id.str.replace("muni:", "", regex=False)
    p["cousub"] = [names.get((c, k), "") for c, k in zip(p.city, p.county)]
    return p


def attach_tract(p):
    import geopandas as gpd

    t = gpd.read_file(f"zip://{TRACTS}", columns=["GEOID"]).to_crs(CRS_M)
    pts = gpd.GeoDataFrame({"i": np.arange(len(p))}, geometry=p["pt"].values, crs=CRS_M)
    j = gpd.sjoin(pts, t, how="left", predicate="within").drop_duplicates("i").set_index("i")
    p = p.copy()
    p["tract"] = j.GEOID.reindex(np.arange(len(p))).values
    return p


def build_lot_layer() -> None:
    """Station-area lots (all bands) for the three groups, plus all Milwaukee and Madison lots for the
    take-up and the Madison test. Saved without parcel ids (git-ignored)."""
    PROC.mkdir(parents=True, exist_ok=True)
    muni = pd.read_csv(REFERENCE / "tod_near_stop_homes_by_muni.csv", dtype={"area_id": str})
    stops = B.stop_points()
    mke_rules, mad_rules = B.read_rules("milwaukee"), B.read_rules("madison")
    print("Milwaukee lots ...", flush=True)
    mke = attach_tract(load_milwaukee_lots())
    print("Madison lots ...", flush=True)
    mad = attach_tract(load_madison_lots({r["district"] for r in mad_rules}))
    print("  Madison parcel records with a V12 land value:", round(mad.attrs.get("land_match", 0), 4))
    print("Fallback lots ...", flush=True)
    sub = attach_tract(load_fallback_lots(muni))
    print("  fallback lots matched to the station-area build:", round(sub.attrs.get("matched_to_station_build", 0), 4))
    keep = ["city", "county", "zoning_coded", "sqft_per_home", "band", "district", "zoning_class", "rule_type",
            "use_class", "eligible", "acres", "homes", "current_allowed_homes", "law_allowed_homes", "capacity_gain",
            "capacity_gain_sqft1000", "added_floor_area_sqft", "in_overlay", "land_value", "land_known", "new5_homes", "tract", "cousub"]
    lots = pd.concat([B.compute(mke, "Milwaukee city", mke_rules, stops, county="Milwaukee County"),
                      B.compute(mad, "Madison city", mad_rules, stops, county="Dane County"),
                      B.compute(sub, "fallback", None, stops, sqft_per_home=C.MEASURED_SQFT_PER_HOME["pooled"])],
                     ignore_index=True)
    # 1,000 sq ft law homes for the sensitivity: law homes = max(area x law at 1,000 sq ft, current).
    lots["law_homes_sqft1000"] = [max(a * C.law_homes_per_acre(b, sqft_per_home=C.SENSITIVITY_SQFT_PER_HOME), cur)
                                  if e else 0.0 for a, b, cur, e in
                                  zip(lots.acres, lots.band, lots.current_allowed_homes, lots.eligible)]
    pd.DataFrame(lots[keep + ["law_homes_sqft1000"]]).to_parquet(LOTS, index=False)
    for name, p in (("milwaukee", mke), ("madison", mad)):
        q = pd.DataFrame(p.drop(columns=["geometry", "pt"], errors="ignore"))
        q["acres"] = p.geometry.area / M2_PER_ACRE
        cols = [c for c in ["district", "use_class", "acres", "homes", "land_value", "land_known", "new5_homes", "tract", "cousub",
                            "in_overlay", "dist_overlay_m"] if c in q]
        q[cols].to_parquet(MKE_ALL if name == "milwaukee" else MAD_ALL, index=False)
    print("wrote", LOTS, MKE_ALL, MAD_ALL)


# ----------------------------------------------------------------------------- rents per lot

def lot_rent(df: pd.DataFrame, tract: dict, cousub: dict, county: dict) -> tuple[np.ndarray, np.ndarray]:
    """Tract median gross rent; if suppressed, the municipality's; then the county's."""
    rent, src = [], []
    for t, cs in zip(df.tract, df.cousub):
        if isinstance(t, str) and t in tract:
            rent.append(tract[t]); src.append("tract")
        elif isinstance(cs, str) and cs in cousub:
            rent.append(cousub[cs]); src.append("municipality")
        elif isinstance(cs, str) and cs[:5] in county:
            rent.append(county[cs[:5]]); src.append("county")
        else:
            rent.append(np.nan); src.append("none")
    return np.array(rent, dtype=float), np.array(src)


def params_for(county: str, cousub: str, ratio: dict, sqft: float, use_ratio: bool, cost_table=None,
               cost_sqft=HUD_SQFT_2BR) -> M.FeasibilityParams:
    rr = ratio.get(cousub, np.nan) if use_ratio else 1.0
    return M.FeasibilityParams(cap_rate=CAP_RATE, opex_ratio=OPEX_RATIO,
                               cost_per_sqft=hud_cost_per_sqft(county, cost_table or HUD_HCC_2BR_ELEVATOR, cost_sqft),
                               sqft_per_home=sqft, rent_ratio_new=1.0 if not np.isfinite(rr) else rr)


def feasible_flags(df: pd.DataFrame, homes_col: str, rents, ratio: dict, use_ratio: bool, sqft_col="sqft_per_home",
                   sqft_override: float | None = None) -> np.ndarray:
    out = np.zeros(len(df), dtype=bool)
    for (county, cs, sq), idx in df.groupby(["county", "cousub", sqft_col], dropna=False).indices.items():
        p = params_for(county, cs, ratio, sqft_override or sq, use_ratio)
        out[idx] = M.is_feasible(df[homes_col].to_numpy()[idx], rents[idx], df.land_value.to_numpy()[idx], p)
    return out


# ----------------------------------------------------------------------------- case parameters

def case_params() -> dict:
    est = pd.read_csv(REFERENCE / "tod_case_estimates.csv").set_index("case")
    pooled = est.loc["nyc_pooled_2003_2013"]
    rates = pd.read_csv(REFERENCE / "tod_case_rates_by_year.csv")
    r = rates[rates.case == "nyc_pooled_2003_2013"].pivot_table(index="year", columns="area", values="rate")
    gap = r["treatment"] - r["comparison"]
    before = gap[gap.index < 0].mean()
    per_far = (gap - before) / pooled.dose_added_far
    gaps = [float(per_far[k]) for k in M.YEARS]
    ps, db, chi = (float(est.loc[c, "effect_per_dose"]) for c in
                   ("nyc_park_slope_fourth_ave_2003", "nyc_downtown_brooklyn_2004", "chicago_tod_2013_2015"))
    return {
        "r_typical": float(pooled.effect_per_dose), "r_typical_low": float(pooled.effect_per_dose_low),
        "r_typical_high": float(pooled.effect_per_dose_high), "r_little": chi,
        "r_little_low": float(est.loc["chicago_tod_2013_2015", "effect_per_dose_low"]),
        "r_little_high": float(est.loc["chicago_tod_2013_2015", "effect_per_dose_high"]),
        "r_strong": (ps + db) / 2, "r_park_slope": ps, "r_downtown_brooklyn": db,
        "r_reference_line": M.case_reference_line({"nyc_pooled": float(pooled.effect_per_dose), "chicago": chi}),
        "gaps_per_far": gaps, "gap_year0_per_far": float(per_far[0]),
        "ramp": M.ramp_from_gaps(gaps), "ramp_year5_alt": M.ramp_year5_alternative(gaps),
    }


SCENARIOS_A = [("little", "Little response", "r_little"), ("typical", "Typical response", "r_typical"),
               ("strong", "Strong response", "r_strong"), ("reference_line", "Reference line (median of measured per-FAR cases)", "r_reference_line")]


# ----------------------------------------------------------------------------- Milwaukee take-up (method B)

def milwaukee_take_up(rents_tables, use_ratio: bool) -> dict:
    tract, cousub, county, ratio = rents_tables
    m = pd.read_parquet(MKE_ALL)
    sq = C.MEASURED_SQFT_PER_HOME["Milwaukee city"]
    rules = C.rule_table(B.read_rules("milwaukee"), sqft_per_home=sq)
    hpa, elig = [], []
    for d, u in zip(m.district, m.use_class):
        rl = rules.get(d)
        ok = rl is not None and rl.rule_type in {"density", "far"} and C.is_eligible(rl.zoning_class, u, rl.rule_type)
        elig.append(ok)
        hpa.append(rl.homes_per_acre if ok else np.nan)
    m["hpa"] = hpa
    m = m[np.array(elig) & (m.hpa >= TAKE_UP_MIN_HPA)].copy()
    m["county"] = "Milwaukee County"
    m["sqft_per_home"] = sq
    m["allowed"] = m.acres * m.hpa
    m["existing_start"] = (m.homes - m.new5_homes).clip(lower=0)
    m["cap_start"] = (m.allowed - m.existing_start).clip(lower=0)
    rent, _ = lot_rent(m, tract, cousub, county)
    feas = feasible_flags(m.reset_index(drop=True), "allowed", rent, ratio, use_ratio)
    feasible_cap = float(m.cap_start.to_numpy()[feas].sum())
    years = TAKE_UP_YEARS[1] - TAKE_UP_YEARS[0] + 1
    new = float(m.new5_homes.sum())
    buildings = m.new5_homes[m.new5_homes > 0].to_numpy()
    tu = M.take_up_rate(new, years, feasible_cap)
    lo, hi = M.bootstrap_take_up(buildings, years, feasible_cap, seed=SEED)
    return {"lots": len(m), "acres": float(m.acres.sum()), "new_homes": new, "buildings": int(len(buildings)),
            "years": years, "capacity_current": float(m.cap_start.sum()), "feasible_capacity_current": feasible_cap,
            "feasible_lots": int(feas.sum()), "take_up": tu, "take_up_low": lo, "take_up_high": hi,
            "max_tract_rent": float(np.nanmax(rent)) if len(rent) else np.nan}


# ----------------------------------------------------------------------------- Madison test (blind: land and rules only)

def madison_test(rents_tables, take: dict, cp: dict, use_ratio: bool) -> tuple[pd.DataFrame, dict]:
    tract, cousub, county, ratio = rents_tables
    m = pd.read_parquet(MAD_ALL)
    sq = C.MEASURED_SQFT_PER_HOME["Madison city"]
    rows = B.read_rules("madison")
    base, ovl = C.rule_table(rows, False, sq), C.rule_table(rows, True, sq)
    area, elig, d_far, h_base, h_ovl = [], [], [], [], []
    for r in m.itertuples(index=False):
        rb, ro = base.get(r.district), ovl.get(r.district)
        e = rb is not None and rb.rule_type != "not_coded" and C.is_eligible(rb.zoning_class, r.use_class, rb.rule_type) \
            and r.use_class != "single_family"
        elig.append(e)
        area.append("overlay" if r.in_overlay else ("ring_quarter_mile_outside" if r.dist_overlay_m <= C.QUARTER_M else "rest_of_city"))
        d_far.append(max(ro.far - rb.far, 0.0) if e and rb.far is not None and ro.far is not None else 0.0)
        dens = e and rb.rule_type in {"density", "far"}
        h_base.append(r.acres * rb.homes_per_acre if dens else np.nan)
        h_ovl.append(r.acres * ro.homes_per_acre if dens else np.nan)
    m["area"], m["elig"], m["added_far"], m["h_base"], m["h_ovl"] = area, elig, d_far, h_base, h_ovl
    t = m[(m.area == "overlay") & m.elig].copy().reset_index(drop=True)
    acres = float(t.acres.sum())
    dose = float((t.added_far * t.acres).sum() / acres)
    t["county"], t["sqft_per_home"] = "Dane County", sq
    rent, _ = lot_rent(t, tract, cousub, county)
    fb = feasible_flags(t, "h_base", rent, ratio, use_ratio)
    fo = feasible_flags(t, "h_ovl", rent, ratio, use_ratio)
    cap_b = np.where(fb, (t.h_base.fillna(0) - t.homes).clip(lower=0), 0.0)
    cap_o = np.where(fo, (t.h_ovl.fillna(0) - t.homes).clip(lower=0), 0.0)
    delta_feasible = float(cap_o.sum() - cap_b.sum())
    delta_paper = float(((t.h_ovl.fillna(0) - t.homes).clip(lower=0) - (t.h_base.fillna(0) - t.homes).clip(lower=0)).sum())
    a = M.method_a_madison_prediction(cp["r_typical"], cp["r_typical_low"], cp["r_typical_high"], dose)
    ramp03 = (cp["gap_year0_per_far"] + cp["gaps_per_far"][0] + cp["gaps_per_far"][1]) / 3
    b = M.method_b_madison_prediction(take["take_up"], take["take_up_low"], take["take_up_high"], delta_feasible, acres)
    b_ok = np.isfinite(take["take_up"])
    unit = "extra homes permitted per eligible acre per year (difference-in-differences, overlay minus 1/4-mile ring)"
    out = pd.DataFrame([
        {"method": "A", "variant": "main (spec section 4.1)", **{k: round(v, 4) for k, v in a.items()},
         "unit": unit, "formula": f"r {cp['r_typical']:.4f} (90% {cp['r_typical_low']:.4f} to {cp['r_typical_high']:.4f}) x added FAR {dose:.4f}",
         "status": "computed", "dose_added_far": round(dose, 4), "eligible_overlay_acres": round(acres, 1),
         "delta_capacity_homes": round(delta_paper, 1), "delta_feasible_capacity_homes": np.nan, "take_up_per_year": np.nan},
        {"method": "A", "variant": "sensitivity: ramp matched to the test's after years 2023-2025 (event years 0-2)",
         "prediction": round(ramp03 * dose, 4), "interval90_low": round(ramp03 * dose * cp["r_typical_low"] / cp["r_typical"], 4),
         "interval90_high": round(ramp03 * dose * cp["r_typical_high"] / cp["r_typical"], 4), "unit": unit,
         "formula": f"mean pooled gap per FAR in event years 0-2 {ramp03:.4f} x added FAR {dose:.4f}; interval scaled as r's",
         "status": "computed (not the judged prediction)", "dose_added_far": round(dose, 4), "eligible_overlay_acres": round(acres, 1),
         "delta_capacity_homes": round(delta_paper, 1), "delta_feasible_capacity_homes": np.nan, "take_up_per_year": np.nan},
        {"method": "B", "variant": "main (spec section 4.1)" + (" with ACS rents scaled by B25111" if use_ratio else " with ACS rents unscaled"),
         **({k: round(v, 4) for k, v in b.items()} if b_ok else {"prediction": np.nan, "interval90_low": np.nan, "interval90_high": np.nan}),
         "unit": unit, "formula": "Milwaukee take-up x change in feasible capacity from the overlay / eligible overlay acres",
         "status": "computed" if b_ok else ("not computable: Milwaukee land zoned for 30+ homes per acre has "
                                            f"{take['feasible_capacity_current']:.0f} homes of feasible capacity under current zoning, so take-up "
                                            f"({take['new_homes']:.0f} homes built {TAKE_UP_YEARS[0]}-{TAKE_UP_YEARS[1]}) has no denominator; "
                                            f"overlay change in feasible capacity = {delta_feasible:.0f} homes"),
         "dose_added_far": round(dose, 4), "eligible_overlay_acres": round(acres, 1), "delta_capacity_homes": round(delta_paper, 1),
         "delta_feasible_capacity_homes": round(delta_feasible, 1), "take_up_per_year": take["take_up"]},
    ])
    out.insert(0, "written", "2026-10-26, before any Madison permit was counted by overlay")
    info = {"dose": dose, "acres": acres, "delta_feasible": delta_feasible, "delta_paper": delta_paper,
            "dose_by_district": t.assign(fa=t.added_far * t.acres).groupby("district").agg(acres=("acres", "sum"), far_acres=("fa", "sum"))}
    return out, info


# ----------------------------------------------------------------------------- statewide

def area_ids() -> pd.DataFrame:
    m = pd.read_csv(REFERENCE / "tod_near_stop_homes_by_muni.csv", dtype={"area_id": str})
    return m


def lot_inputs(L: pd.DataFrame, definition_bands, rents_tables, use_ratio: bool, fallback_cap_scale: float = 1.0,
               fallback_dose_scale: float = 0.0, drop_sf: bool = False, sqft1000: bool = False) -> pd.DataFrame:
    """Per (city, county): dose (acre x added FAR), capacity gain and feasible capacity gain, from the same
    lots as reference/tod_station_areas.csv.

    Places whose zoning is not coded: the spec takes the dose from added_floor_area_sqft, which the
    station-area table sets to 0 there, so the main case gives them no method A dose
    (fallback_dose_scale 0). Sensitivities give them M.fallback_added_floor_area (capacity gain x sq ft
    per home) x fallback_dose_scale. Their capacity (method B) is x fallback_cap_scale."""
    tract, cousub, county, ratio = rents_tables
    x = L[L.band.isin(definition_bands) & L.eligible].copy().reset_index(drop=True)
    if drop_sf:
        x = x[~x.use_class.isin(B.SINGLE_FAMILY_USES)].reset_index(drop=True)
    cap = x.capacity_gain_sqft1000 if sqft1000 else x.capacity_gain
    sq = np.where(sqft1000, C.SENSITIVITY_SQFT_PER_HOME, x.sqft_per_home)
    fb = x.zoning_coded == 0
    x["dose_sqft"] = np.where(fb, cap * sq * fallback_dose_scale, x.added_floor_area_sqft)
    x["cap"] = np.where(fb, cap * fallback_cap_scale, cap)
    rent, _ = lot_rent(x, tract, cousub, county)
    homes_col = "law_homes_sqft1000" if sqft1000 else "law_allowed_homes"
    feas = feasible_flags(x, homes_col, rent, ratio, use_ratio,
                          sqft_override=C.SENSITIVITY_SQFT_PER_HOME if sqft1000 else None)
    x["feasible_cap"] = np.where(feas, x.cap, 0.0)
    x["eligible_acres"] = x.acres
    return x.groupby(["city", "county"], as_index=False)[["eligible_acres", "dose_sqft", "cap", "feasible_cap"]].sum()


def fallback_ratio(L: pd.DataFrame) -> float:
    """Coded capacity / the fallback rule applied to the same coded lots (Milwaukee and Madison, main case)."""
    x = L[L.band.isin(C.DEFINITION_BANDS["main"]) & L.eligible & (L.zoning_coded == 1)]
    law = np.array([C.law_homes_per_acre(b, sqft_per_home=s) for b, s in zip(x.band, x.sqft_per_home)])
    fb = np.maximum(x.acres.to_numpy() * law - x.homes.to_numpy(), 0.0)
    return float(x.capacity_gain.sum() / fb.sum())


def run_areas(inputs: pd.DataFrame, muni: pd.DataFrame, share_col: str, cp: dict, take_up: float, ramp,
              baseline: pd.DataFrame, scenarios=SCENARIOS_A) -> pd.DataFrame:
    """One row per municipality piece x method x scenario, additions by year (never negative)."""
    keyed = inputs.merge(muni[["area_id", "name", "county"]], left_on=["city", "county"], right_on=["name", "county"], how="left")
    unmatched = keyed[keyed.area_id.isna()]
    if (unmatched[["dose_sqft", "cap"]].sum() > 1e-6).any():
        raise ValueError(f"station-area places with capacity but no municipality id: {unmatched.city.tolist()}")
    keyed = keyed[keyed.area_id.notna()]
    bl = M.baseline_near_stops(baseline, muni, share_col)
    base = muni[["area_id", "name", "county"]].merge(bl, on="area_id").merge(
        keyed[["area_id", "eligible_acres", "dose_sqft", "cap", "feasible_cap"]], on="area_id", how="left").fillna(
        {"eligible_acres": 0.0, "dose_sqft": 0.0, "cap": 0.0, "feasible_cap": 0.0})
    rows = []
    for a in base.itertuples(index=False):
        common = {"area_id": a.area_id, "name": a.name, "county": a.county, "eligible_acres": a.eligible_acres,
                  "added_far_acres": a.dose_sqft / M.SQFT_PER_ACRE, "capacity_gain": a.cap, "feasible_capacity_gain": a.feasible_cap,
                  "share_near_stops": a.share_near,
                  **{f"baseline_near_{s}_2027_2031": getattr(a, f"baseline_near_five_year_{s}") for s in ("low", "central", "high")}}
        for sid, label, key in scenarios:
            add = M.method_a_addition(a.dose_sqft, cp[key], ramp)
            rows.append({**common, "method": "A", "scenario": sid, "scenario_label": label, "parameter": cp[key],
                         **{f"add_y{k}": v for k, v in zip(M.YEARS, add)}})
        add = M.method_b_addition(a.feasible_cap, take_up, ramp)
        rows.append({**common, "method": "B", "scenario": "milwaukee_take_up", "scenario_label": "Milwaukee take-up (only measured take-up)",
                     "parameter": take_up, **{f"add_y{k}": v for k, v in zip(M.YEARS, add)}})
    out = pd.DataFrame(rows)
    out["add_2027_2031"] = out[[f"add_y{k}" for k in M.YEARS]].sum(axis=1, min_count=5)
    return out


def state_total(by_area: pd.DataFrame) -> pd.DataFrame:
    cols = ["eligible_acres", "added_far_acres", "capacity_gain", "feasible_capacity_gain", "baseline_near_low_2027_2031",
            "baseline_near_central_2027_2031", "baseline_near_high_2027_2031"] + [f"add_y{k}" for k in M.YEARS] + ["add_2027_2031"]
    return M.aggregate(by_area, ["method", "scenario", "scenario_label", "parameter"], cols)


def statewide_long(state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s in state.itertuples(index=False):
        for k in [*M.YEARS, None]:
            add = getattr(s, f"add_y{k}") if k else s.add_2027_2031
            div = 1.0 if k is None else 5.0
            rows.append({"method": s.method, "scenario": s.scenario, "scenario_label": s.scenario_label,
                         "parameter": round(s.parameter, 6) if np.isfinite(s.parameter) else np.nan,
                         "parameter_unit": ("extra homes permitted per eligible acre per year per 1.0 added FAR" if s.method == "A"
                                            else "share of feasible capacity permitted per year"),
                         "year": M.CALENDAR[k] if k else "2027-2031",
                         "baseline_near_stops_low": s.baseline_near_low_2027_2031 / div,
                         "baseline_near_stops_central": s.baseline_near_central_2027_2031 / div,
                         "baseline_near_stops_high": s.baseline_near_high_2027_2031 / div,
                         "addition": add, "with_law_central": s.baseline_near_central_2027_2031 / div + add if np.isfinite(add) else np.nan,
                         "eligible_acres": s.eligible_acres, "added_far_acres": s.added_far_acres,
                         "capacity_gain": s.capacity_gain, "feasible_capacity_gain": s.feasible_capacity_gain})
    return pd.DataFrame(rows)


def by_area_out(by_area: pd.DataFrame) -> pd.DataFrame:
    ren = {f"add_y{k}": f"add_{M.CALENDAR[k]}" for k in M.YEARS}
    out = by_area.rename(columns=ren)
    keep = (out.eligible_acres > 0) | (out.baseline_near_central_2027_2031 > 0)
    return out[keep].round(4)


def write(df: pd.DataFrame, name: str) -> None:
    df.to_csv(REFERENCE / name, index=False, lineterminator="\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cached", action="store_true", help="reuse the lot layer in data/processed/tod_model")
    args = ap.parse_args()
    if not (args.cached and LOTS.exists() and MKE_ALL.exists() and MAD_ALL.exists()):
        build_lot_layer()
    cp = case_params()
    rents = rent_tables()
    muni = area_ids()
    baseline = pd.read_csv(REFERENCE / "housing_baseline_by_area.csv", dtype={"area_id": str})
    L = pd.read_parquet(LOTS)
    # Spec 3: new-building rent ratio "if available"; B25111 (2020-or-later buildings / all) is the
    # measured new-building to all-building rent ratio by municipality. It is used as the main reading.
    use_ratio = True
    take = milwaukee_take_up(rents, use_ratio)
    take_unscaled = milwaukee_take_up(rents, False)
    pred, minfo = madison_test(rents, take, cp, use_ratio)
    write(pred, "tod_madison_test_predictions.csv")

    ramp = cp["ramp"]
    main_in = lot_inputs(L, C.DEFINITION_BANDS["main"], rents, use_ratio)
    by_area = run_areas(main_in, muni, "share_near_main", cp, take["take_up"], ramp, baseline)
    state = state_total(by_area)
    write(statewide_long(state).round(4), "tod_model_statewide.csv")
    write(by_area_out(by_area), "tod_model_by_area.csv")
    vals = ["eligible_acres", "added_far_acres", "capacity_gain", "feasible_capacity_gain", "baseline_near_low_2027_2031",
            "baseline_near_central_2027_2031", "baseline_near_high_2027_2031"] + [f"add_y{k}" for k in M.YEARS] + ["add_2027_2031"]
    keys = ["method", "scenario"]
    write(M.aggregate(by_area, ["county", *keys], vals).round(4), "tod_model_by_county.csv")
    cw = pd.read_csv(REFERENCE / "adu_model_district_crosswalk.csv", dtype={"area_id": str})
    write(M.to_districts(by_area, cw, "assembly_district", keys, vals).round(4), "tod_model_by_assembly_district.csv")
    write(M.to_districts(by_area, cw, "senate_district", keys, vals).round(4), "tod_model_by_senate_district.csv")

    # ------------------------------------------------------------------ sensitivities (spec section 7)
    sens = []

    def add_sens(group, sid, label, ba, base_col="baseline_near_central_2027_2031"):
        st = state_total(ba)
        for s in st.itertuples(index=False):
            sens.append({"group": group, "sensitivity": sid, "description": label, "method": s.method, "scenario": s.scenario,
                         "parameter": s.parameter, "baseline_near_stops_2027_2031": getattr(s, base_col),
                         "addition_2027_2031": s.add_2027_2031, "eligible_acres": s.eligible_acres,
                         "added_far_acres": s.added_far_acres, "capacity_gain": s.capacity_gain,
                         "feasible_capacity_gain": s.feasible_capacity_gain})

    add_sens("main", "main", "Main case as specified", by_area)
    # The law's addition
    ext = [("typical_low", "Typical response, low end of r's 90% interval", "r_typical_low"),
           ("typical_high", "Typical response, high end of r's 90% interval", "r_typical_high"),
           ("park_slope", "Park Slope alone", "r_park_slope"), ("downtown_brooklyn", "Downtown Brooklyn alone", "r_downtown_brooklyn")]
    ba = run_areas(main_in, muni, "share_near_main", cp, take["take_up"], ramp, baseline, scenarios=ext)
    add_sens("law_addition", "r_values", "Method A with each other measured r", ba[ba.method == "A"])
    ba = run_areas(main_in, muni, "share_near_main", cp, take["take_up"], cp["ramp_year5_alt"], baseline)
    add_sens("law_addition", "ramp_year5_alt", "Year 5 of the ramp = mean of years 3 to 5 (the year-5 drop replaced)", ba)
    x = lot_inputs(L, C.DEFINITION_BANDS["main"], rents, use_ratio, sqft1000=True)
    add_sens("law_addition", "sqft_1000", "Floor area per home 1,000 sq ft (capacity and building cost; coded added FAR does not depend on it)",
             run_areas(x, muni, "share_near_main", cp, take["take_up"], ramp, baseline))
    x = lot_inputs(L, C.DEFINITION_BANDS["main"], rents, use_ratio, drop_sf=True)
    add_sens("law_addition", "no_single_family", "Single-family lots left out (G2-8)",
             run_areas(x, muni, "share_near_main", cp, take["take_up"], ramp, baseline))
    fr = fallback_ratio(L)
    x = lot_inputs(L, C.DEFINITION_BANDS["main"], rents, use_ratio, fallback_dose_scale=1.0)
    add_sens("law_addition", "fallback_dose_from_capacity",
             "Uncoded places get a method A dose: capacity gain x pooled floor area per home (law FAR minus existing homes' floor area)",
             run_areas(x, muni, "share_near_main", cp, take["take_up"], ramp, baseline))
    x = lot_inputs(L, C.DEFINITION_BANDS["main"], rents, use_ratio, fallback_cap_scale=fr, fallback_dose_scale=fr)
    add_sens("law_addition", "fallback_scaled", f"As above, with uncoded places' capacity and dose x {fr:.4f} (coded / fallback-rule capacity in Milwaukee and Madison)",
             run_areas(x, muni, "share_near_main", cp, take["take_up"], ramp, baseline))
    # Baseline only
    add_sens("baseline_only", "baseline_low", "Low baseline (Wisconsin's 10th-percentile five-year outcome)", by_area, "baseline_near_low_2027_2031")
    add_sens("baseline_only", "baseline_high", "High baseline (90th percentile)", by_area, "baseline_near_high_2027_2031")
    pub = pd.read_csv(REFERENCE / "housing_baseline_sensitivity_published.csv")
    sw = baseline.groupby("structure_type")[["five_year_low", "five_year_central", "five_year_high"]].sum()
    mke = muni.set_index("area_id").loc["muni:5507953000"]
    diff = sw["five_year_central"].sum() - pub[pub.structure_type.isin(sw.index)].central.sum()
    mke_share = float(mke.share_near_main)
    for r0 in [r for r in sens if r["sensitivity"] == "main"]:
        sens.append({**r0, "group": "baseline_only", "sensitivity": "census_as_published",
                     "description": f"Census as published for Milwaukee city ({diff:,.0f} fewer baseline units statewide, all in Milwaukee city, x its near-stop share {mke_share:.4f})",
                     "baseline_near_stops_2027_2031": r0["baseline_near_stops_2027_2031"] - diff * mke_share})
    # Where homes land
    for d, share_col, bands, label in [
            ("rapid_only", "share_near_rapid_half", frozenset({"rapid_quarter", "rapid_half"}), "Rail and rapid stops only (within 1/2 mile)"),
            ("high", "share_near_high", C.DEFINITION_BANDS["high"], "High case: 20-minute buses within 1/4 mile"),
            ("b_half", "share_near_b_half", C.DEFINITION_BANDS["b_half"], "All 15-minute stops within 1/2 mile")]:
        x = lot_inputs(L, bands, rents, use_ratio)
        add_sens("where_homes_land", d, label, run_areas(x, muni, share_col, cp, take["take_up"], ramp, baseline))
    # Method B reading with unscaled ACS rents (the spec's fallback when no new-building ratio exists)
    x = lot_inputs(L, C.DEFINITION_BANDS["main"], rents, False)
    ba = run_areas(x, muni, "share_near_main", cp, take_unscaled["take_up"], ramp, baseline)
    add_sens("law_addition", "rent_unscaled", "Method B with ACS rents not scaled to new buildings", ba[ba.method == "B"])
    sdf = pd.DataFrame(sens)
    write(sdf.round(4), "tod_model_sensitivities.csv")

    # ------------------------------------------------------------------ parameters and diagnostics
    params = param_table(cp, take, minfo, fr)
    write(params, "tod_model_params.csv")
    write(feasibility_diag(rents, L, take, take_unscaled), "tod_model_feasibility.csv")

    run_net_sizing(by_area, L, muni, cp, rents, baseline, take, use_ratio)

    pd.set_option("display.width", 250)
    print(pred.drop(columns=["written", "formula", "unit"]).to_string(index=False))
    print(statewide_long(state)[lambda d: d.year == "2027-2031"].round(1).to_string(index=False))
    print(sdf[["sensitivity", "method", "scenario", "baseline_near_stops_2027_2031", "addition_2027_2031"]].round(0).to_string(index=False))
    print("take-up:", json.dumps({k: v for k, v in take.items()}, default=float))
    print("Madison dose by district:\n", minfo["dose_by_district"].round(1).to_string())


def param_table(cp: dict, take: dict, minfo: dict, fr: float) -> pd.DataFrame:
    hud = "HUD, 2024 Unit Total Development Cost Limits (PIH, Nov 2024), https://hud.gov/sites/dfiles/PIH/documents/2024_Units_TDC_Limits.pdf, Region V Wisconsin, elevator, 2-bedroom (900 sq ft) HCC"
    rows = [
        ("r_typical", cp["r_typical"], "extra homes permitted per eligible acre per year per 1.0 added FAR", "New York pooled set, reference/tod_case_estimates.csv (effect_per_dose)", "measured"),
        ("r_typical_90_low", cp["r_typical_low"], "same", "same, 90% bootstrap interval", "measured"),
        ("r_typical_90_high", cp["r_typical_high"], "same", "same", "measured"),
        ("r_little", cp["r_little"], "same", "Chicago 2015 (held out), reference/tod_case_estimates.csv", "measured"),
        ("r_strong", cp["r_strong"], "same", "mean of Park Slope and Downtown Brooklyn, reference/tod_case_estimates.csv", "measured"),
        ("r_reference_line", cp["r_reference_line"], "same", "median of measured per-FAR cases: New York pooled set (contains Park Slope and Downtown Brooklyn) and Chicago", "measured"),
        *[(f"ramp_year{k}", v, "share of r reached in year k (mean of years 1-5 = 1)", "New York pooled set gap per added FAR by event year, reference/tod_case_rates_by_year.csv", "measured")
          for k, v in zip(M.YEARS, cp["ramp"])],
        *[(f"ramp_year{k}_year5_alt", v, "same", "sensitivity: year 5 = mean of years 3 to 5", "measured")
          for k, v in zip(M.YEARS, cp["ramp_year5_alt"])],
        ("sqft_per_home_milwaukee", C.MEASURED_SQFT_PER_HOME["Milwaukee city"], "gross sq ft per home", "reference/tod_floor_area_per_home.csv (MPROP 2026, 5+ home buildings built 2018-2025)", "measured"),
        ("sqft_per_home_madison", C.MEASURED_SQFT_PER_HOME["Madison city"], "gross sq ft per home", "reference/tod_floor_area_per_home.csv (permits citywide, 2018-2025)", "measured"),
        ("sqft_per_home_pooled", C.MEASURED_SQFT_PER_HOME["pooled"], "gross sq ft per home", "reference/tod_floor_area_per_home.csv", "measured"),
        *[(f"hud_hcc_per_sqft_{k.lower().replace(' ', '_')}", v / HUD_SQFT_2BR, "2024 dollars per sq ft (hard cost)", hud, "published")
          for k, v in HUD_HCC_2BR_ELEVATOR.items()],
        ("cap_rate", CAP_RATE, "share", "CBRE, U.S. Cap Rate Survey H1 2024, Multifamily Infill, Midwest, Milwaukee, Class A stabilized, H1 2024: 5.5%-6% (midpoint); copy at https://taasinvestments.com/wp-content/uploads/2024/08/Cap-Rate-Survey-H1-2024.pdf", "published"),
        ("opex_ratio", OPEX_RATIO, "operating expenses / gross rents collected", f"IREM, Income/Expense IQ National Summary 2024, multifamily: ${IREM_OPEX_PER_UNIT:,.2f} operating expenses / ${IREM_GROSS_RENT_PER_UNIT:,.0f} gross rents per unit, https://www.irem.org/file%20library/globalnavigation/learning/tools/irem-income-expense-iq-national-summary-24.pdf", "published"),
        ("rent", np.nan, "dollars per month", "ACS 2020-2024 5-year B25064 median gross rent by tract (municipality, then county, where suppressed)", "measured"),
        ("rent_ratio_new_milwaukee", rent_tables()[3].get("5507953000"), "ratio", "ACS 2020-2024 B25111: median gross rent in buildings built 2020 or later / all buildings, municipality", "measured"),
        ("rent_ratio_new_madison", rent_tables()[3].get("5502548000"), "ratio", "same", "measured"),
        ("land_value", np.nan, "dollars", "Assessed land value: MPROP C_A_LAND (Milwaukee), V12 LNDVALUE (Madison, other places), tax roll 2025", "measured"),
        ("take_up", take["take_up"], "share of feasible capacity permitted per year", f"Milwaukee: {take['new_homes']:.0f} homes in {take['buildings']} buildings of 5+ homes built {TAKE_UP_YEARS[0]}-{TAKE_UP_YEARS[1]} (MPROP) on land zoned for 30+ homes per acre / {take['years']} years / {take['feasible_capacity_current']:.0f} homes of feasible capacity under current zoning", "measured" if np.isfinite(take["take_up"]) else "not computable"),
        ("madison_overlay_added_far", minfo["dose"], "FAR (acre-weighted over eligible overlay land)", f"Madison overlay stories vs base district (reference/tod_zoning_rules_madison.csv) x lot coverage, {minfo['acres']:.1f} eligible overlay acres", "coded rules"),
        ("fallback_ratio", fr, "ratio", "coded capacity / fallback-rule capacity on the same Milwaukee and Madison main-case lots", "measured"),
    ]
    return pd.DataFrame(rows, columns=["parameter", "value", "unit", "source", "kind"])


def feasibility_diag(rents, L, take, take_unscaled) -> pd.DataFrame:
    tract, cousub, county, ratio = rents
    rows = []
    x = L[L.band.isin(C.DEFINITION_BANDS["main"]) & L.eligible].reset_index(drop=True)
    rent, _ = lot_rent(x, tract, cousub, county)
    grp = np.where(x.zoning_coded == 1, x.city, "Not coded (fallback places)")
    for g in ["Milwaukee city", "Madison city", "Not coded (fallback places)"]:
        sel = grp == g
        xs = x[sel].reset_index(drop=True)
        cty = xs.county.iloc[0]
        cs = xs.cousub.iloc[0]
        sq = float(xs.sqft_per_home.iloc[0])
        for ur in (True, False):
            p = params_for(cty, cs, ratio, sq, ur)
            f = feasible_flags(xs, "law_allowed_homes", rent[sel], ratio, ur)
            rows.append({"area": g, "rent_scaled_to_new_buildings": ur, "rent_ratio_new": p.rent_ratio_new if ur else 1.0,
                         "cost_per_home": round(M.cost_per_home(p)), "value_per_home_at_area_median_rent": round(M.value_per_home(float(np.nanmedian(rent[sel])), p)),
                         "break_even_acs_rent_land_free": round(M.break_even_rent(p)),
                         "tract_rent_median": float(np.nanmedian(rent[sel])), "tract_rent_max": float(np.nanmax(rent[sel])),
                         "capacity_gain": round(float(xs.capacity_gain.sum()), 1),
                         "feasible_capacity_gain": round(float(xs.capacity_gain.to_numpy()[f].sum()), 1)})
    d = pd.DataFrame(rows)
    d["milwaukee_take_up_feasible_capacity_current"] = np.where(d.rent_scaled_to_new_buildings, take["feasible_capacity_current"], take_unscaled["feasible_capacity_current"])
    d["milwaukee_new_homes_2018_2025"] = take["new_homes"]
    d["milwaukee_capacity_current_30plus"] = round(take["capacity_current"], 1)
    return d


# ----------------------------------------------------------------------------- sizing by citywide net effect (spec 9, proposed)

# Citywide net effects after upzoning, as recorded in GATE3_MODEL_SPEC.md section 9 (2026-10-26):
LA_PP_PER_YEAR = 0.0004          # Los Angeles: 0.04 percentage points of stock growth a year
STACY_SHARE = 0.008              # Stacy et al. 2023: +0.8% of housing supply 3-9 years after, 1,136 US cities
AUCKLAND_SHARE = 0.041           # Auckland: 21,808 extra consents 2016-2021 = 4.1% of the 2016 stock
AUCKLAND_UPZONED = 0.75          # about 75% of Auckland's residential land was upzoned
AUCKLAND_PROFILE = {2016: -2.63, 2017: 2.34, 2018: 6.79, 2019: 8.95, 2020: 12.09, 2021: 18.00}  # yearly effect per statistical area
WI_MEASURED_R = (0.215 + 0.240) / 2   # mean of Madison's measured (MADISON_TEST_RESULTS.md) and Chicago's per-FAR effects
MILWAUKEE_METRO = {"Milwaukee County", "Waukesha County", "Ozaukee County", "Washington County"}
MADISON_METRO = {"Dane County", "Columbia County", "Green County", "Iowa County"}
METRO_NAMES = {"Milwaukee": "Milwaukee-Waukesha, WI", "Madison": "Madison, WI"}
CHECK_YEARS = 3                  # the Madison test's after years, 2023-2025


def metro_of(county: str) -> str:
    return "Milwaukee" if county in MILWAUKEE_METRO else ("Madison" if county in MADISON_METRO else "other")


def net_effects(cp: dict) -> dict:
    ny = M.timing_from_ramp(cp["ramp"])
    # Auckland: 2016 (the Unitary Plan became operative in November 2016, effect -2.63) is year 0, as in
    # the cases; 2017-2021 are years 1-5. Its published 4.1% is applied as the five-year total.
    auck = M.timing_from_profile([AUCKLAND_PROFILE[y] for y in range(2017, 2022)])
    return {
        "little": (M.NetEffect(LA_PP_PER_YEAR * 5, ny, "Los Angeles, 0.04 pp of stock a year x 5 years; New York pooled ramp"),
                   "Little response (Los Angeles net effect)"),
        "typical": (M.NetEffect(STACY_SHARE, ny, "Stacy et al. 2023, +0.8% of supply, applied as the 2027-2031 total; New York pooled ramp"),
                    "Typical response (Stacy et al. 2023)"),
        "strong": (M.NetEffect(AUCKLAND_SHARE, auck, "Auckland, 4.1% of stock as published; Auckland's 2017-2021 yearly profile"),
                   "Strong response (Auckland)"),
    }


def metro_scale_params() -> dict:
    sc = pd.read_csv(REFERENCE / "tod_scale_check.csv")
    b = sc[sc.kind == "benchmark"].set_index("statistic").value
    out = {"observed_max": float(b["observed_max_peer_metro_year"]), "p95": float(b["p95_peer_metro_years"])}
    for key, name in METRO_NAMES.items():
        h = sc[(sc.kind == "metro_history") & (sc.metro == name)].set_index("statistic")
        hu = sc[(sc.kind == "scenario") & (sc.metro == name)].housing_units.dropna().iloc[0]
        out[key] = {"own_max": float(h.loc["own_max", "value"]), "recent_mean": float(h.loc["recent_mean_2021_2025", "value"]),
                    "housing_units_2025": float(hu)}
    return out


def scale_rows(add: pd.DataFrame, sizing: str, scenario: str, sp: dict) -> list[dict]:
    from missing_middleware.tod import scale_check as S

    rows = []
    met = add.county.map(metro_of)
    for key in METRO_NAMES:
        m = sp[key]
        for k in M.YEARS:
            a = float(add.loc[(met == key).to_numpy(), f"add_y{k}"].sum())
            r = S.scenario_check(a, m["housing_units_2025"], m["recent_mean"], sp["observed_max"], sp["p95"], m["own_max"])
            rows.append({"check": "scale", "sizing": sizing, "scenario": scenario, "metro": METRO_NAMES[key], "year": M.CALENDAR[k],
                         "addition_homes": round(a, 1), **{x: (round(v, 4) if isinstance(v, float) else v) for x, v in r.items()},
                         "observed_max": round(sp["observed_max"], 4), "p95": round(sp["p95"], 4), "own_max": round(m["own_max"], 4)})
    return rows


def run_net_sizing(by_area: pd.DataFrame, L: pd.DataFrame, muni: pd.DataFrame, cp: dict, rents, baseline,
                   take: dict, use_ratio: bool) -> None:
    ycols = [f"add_y{k}" for k in M.YEARS]
    effects = net_effects(cp)
    stock = float(muni.homes_near_main.sum())
    sp = metro_scale_params()

    def net_rows(base_area: pd.DataFrame, stock_homes: float, eff_map: dict, weights=None) -> pd.DataFrame:
        a = base_area[(base_area.method == "A") & (base_area.scenario == "typical")].reset_index(drop=True)
        w = None if weights is None else a.area_id.map(weights).fillna(0.0)
        parts = []
        for sid, (eff, label) in eff_map.items():
            x = M.size_additions(a, "net_effect", stock_homes, eff, w)
            x["scenario"], x["scenario_label"], x["parameter"] = sid, label, eff.five_year_share
            x["timing"] = ", ".join(f"{t:.4f}" for t in eff.timing)
            x["source"] = eff.source
            parts.append(x)
        out = pd.concat(parts, ignore_index=True)
        out["sizing"], out["method"] = "net_effect", "A_placement"
        out["add_2027_2031"] = out[ycols].sum(axis=1)
        out["stock_homes_station_areas"] = stock_homes
        return out

    net = net_rows(by_area, stock, effects)
    cols_keep = ["sizing", "method", "scenario", "scenario_label", "parameter", "timing", "source", "area_id", "name", "county",
                 "eligible_acres", "added_far_acres", "share_near_stops", "baseline_near_low_2027_2031",
                 "baseline_near_central_2027_2031", "baseline_near_high_2027_2031", *ycols, "add_2027_2031"]
    ren = {f"add_y{k}": f"add_{M.CALENDAR[k]}" for k in M.YEARS}
    write(net[(net.eligible_acres > 0) | (net.baseline_near_central_2027_2031 > 0)][cols_keep].rename(columns=ren).round(4),
          "tod_model_net_by_area.csv")
    vals = ["baseline_near_low_2027_2031", "baseline_near_central_2027_2031", "baseline_near_high_2027_2031", *ycols, "add_2027_2031"]
    keys = ["sizing", "scenario"]
    write(M.aggregate(net, ["county", *keys], vals).rename(columns=ren).round(4), "tod_model_net_by_county.csv")
    cw = pd.read_csv(REFERENCE / "adu_model_district_crosswalk.csv", dtype={"area_id": str})
    write(M.to_districts(net, cw, "assembly_district", keys, vals).rename(columns=ren).round(4), "tod_model_net_by_assembly_district.csv")
    write(M.to_districts(net, cw, "senate_district", keys, vals).rename(columns=ren).round(4), "tod_model_net_by_senate_district.csv")

    # Statewide, both sizings side by side
    rows = []
    pa = by_area[by_area.method == "A"]
    for sizing, df in (("per_acre", pa), ("net_effect", net)):
        for sid, g in df.groupby("scenario", sort=False):
            base = g.drop_duplicates("area_id")
            bl = {s: float(base[f"baseline_near_{s}_2027_2031"].sum()) for s in ("low", "central", "high")}
            for k in [*M.YEARS, None]:
                add = float(g[f"add_y{k}"].sum()) if k else float(g[ycols].sum().sum())
                div = 1.0 if k is None else 5.0
                rows.append({"sizing": sizing, "scenario": sid, "scenario_label": g.scenario_label.iloc[0],
                             "parameter": float(g.parameter.iloc[0]),
                             "parameter_unit": ("extra homes per eligible acre per year per 1.0 added FAR" if sizing == "per_acre"
                                                else "extra homes over 2027-2031 as a share of 2020 homes in main-case station areas"),
                             "year": M.CALENDAR[k] if k else "2027-2031",
                             "stock_homes_station_areas": stock,
                             "baseline_near_stops_low": bl["low"] / div, "baseline_near_stops_central": bl["central"] / div,
                             "baseline_near_stops_high": bl["high"] / div, "addition": add,
                             "addition_share_of_stock": add / stock, "with_law_central": bl["central"] / div + add})
    state = pd.DataFrame(rows)
    write(state.round(6), "tod_model_net_statewide.csv")

    # Sensitivities (five-year state totals)
    sens = []

    def add_s(group, sid, desc, df, sizing="net_effect"):
        for scen, g in df.groupby("scenario", sort=False):
            sens.append({"group": group, "sensitivity": sid, "description": desc, "sizing": sizing, "scenario": scen,
                         "parameter": float(g.parameter.iloc[0]),
                         "baseline_near_stops_2027_2031": float(g.drop_duplicates("area_id").baseline_near_central_2027_2031.sum()),
                         "addition_2027_2031": float(g[ycols].sum().sum()),
                         "milwaukee_metro_2027_2031": float(g.loc[g.county.map(metro_of) == "Milwaukee", ycols].sum().sum()),
                         "madison_metro_2027_2031": float(g.loc[g.county.map(metro_of) == "Madison", ycols].sum().sum())})

    add_s("main", "main", "Net-effect sizing as proposed", net)
    e = effects["strong"][0]
    add_s("law_addition", "strong_per_upzoned_stock", "Strong: Auckland's 4.1% / 0.75 (per upzoned stock)",
          net_rows(by_area, stock, {"strong": (M.NetEffect(AUCKLAND_SHARE / AUCKLAND_UPZONED, e.timing, e.source + "; / 0.75"), "Strong response (Auckland, per upzoned stock)")}))
    add_s("law_addition", "strong_ny_ramp", "Strong: Auckland's 4.1% timed by the New York pooled ramp",
          net_rows(by_area, stock, {"strong": (M.NetEffect(AUCKLAND_SHARE, M.timing_from_ramp(cp["ramp"]), "Auckland, NY ramp"), "Strong response (Auckland, NY ramp)")}))
    x = lot_inputs(L, C.DEFINITION_BANDS["main"], rents, use_ratio, fallback_dose_scale=1.0)
    ba = run_areas(x, muni, "share_near_main", cp, take["take_up"], cp["ramp"], baseline)
    wts = ba[(ba.method == "A") & (ba.scenario == "typical")].set_index("area_id")[ycols].sum(axis=1)
    add_s("where_homes_land", "placement_with_uncoded", "Placement weights give uncoded places a dose from their capacity",
          net_rows(by_area, stock, effects, weights=wts))
    for d, share_col, homes_col, bands, label in [
            ("rapid_only", "share_near_rapid_half", "homes_near_rapid_half", frozenset({"rapid_quarter", "rapid_half"}), "Rail and rapid stops only: stock and placement"),
            ("high", "share_near_high", "homes_near_high", C.DEFINITION_BANDS["high"], "High case: stock and placement"),
            ("b_half", "share_near_b_half", "homes_near_b_half", C.DEFINITION_BANDS["b_half"], "All 15-minute stops within 1/2 mile: stock and placement")]:
        x = lot_inputs(L, bands, rents, use_ratio)
        ba = run_areas(x, muni, share_col, cp, take["take_up"], cp["ramp"], baseline)
        add_s("where_homes_land", d, label, net_rows(ba, float(muni[homes_col].sum()), effects))
    # Method A with the Wisconsin-measured response, uncapped and capped at the peer 95th percentile
    wi = [("wisconsin_measured", f"Method A, r = mean of Madison 0.215 and Chicago 0.240 = {WI_MEASURED_R:.4f}", "r_wi")]
    cp2 = {**cp, "r_wi": WI_MEASURED_R}
    x = lot_inputs(L, C.DEFINITION_BANDS["main"], rents, use_ratio)
    wa = run_areas(x, muni, "share_near_main", cp2, take["take_up"], cp["ramp"], baseline, scenarios=wi)
    wa = wa[wa.method == "A"].reset_index(drop=True)
    add_s("law_addition", "wisconsin_measured_uncapped", "Method A per acre with the Wisconsin-measured r, uncapped", wa, "per_acre")
    caps = {key: max(sp["p95"] - sp[key]["recent_mean"], 0.0) * sp[key]["housing_units_2025"] / 1000.0 for key in METRO_NAMES}
    wc = M.cap_by_group(wa, wa.county.map(metro_of), caps)
    add_s("law_addition", "wisconsin_measured_capped",
          f"As above, each metro capped so its total 5+ permits stay at or below the peer 95th percentile ({sp['p95']:.2f} per 1,000 homes a year): "
          f"Milwaukee cap {caps['Milwaukee']:,.0f} homes a year, Madison {caps['Madison']:,.0f} (its 2021-2025 rate is already above)", wc, "per_acre")
    write(pd.DataFrame(sens).round(4), "tod_model_net_sensitivities.csv")

    # Checks: Madison's measured overlay effect as a share of overlay stock, and the scale check
    checks = []
    res = pd.read_csv(REFERENCE / "tod_madison_test_results.csv").set_index("estimate")
    judged = res[res.index.str.startswith("judged")].iloc[0]
    mainr = res[res.index.str.startswith("main")].iloc[0]
    mad = pd.read_parquet(MAD_ALL)
    overlay_homes = float(mad.loc[mad.in_overlay, "homes"].sum())
    overlay_acres, treated_acres = 2931.7, 614.7
    treated_homes = 4461.0
    for basis, row, acres, stock_h, note in [
            ("judged estimate x all eligible overlay acres / all homes on overlay lots", judged, overlay_acres, overlay_homes,
             "per-FAR effect carried over all overlay land at its dose 0.374"),
            ("main estimate x treated acres / all homes on overlay lots", mainr, treated_acres, overlay_homes,
             "effect only where allowed FAR rose (614.7 acres)"),
            ("main estimate x treated acres / homes on treated land", mainr, treated_acres, treated_homes,
             "share of the upzoned stock itself (4,461 homes in the treatment, per MADISON_TEST_RESULTS.md)")]:
        ex = [float(row[c]) * acres * CHECK_YEARS for c in ("value", "interval90_low", "interval90_high")]
        checks.append({"check": "madison_share", "sizing": "measured", "scenario": "Madison overlay 2023-2025", "basis": basis,
                       "extra_homes_3yr": round(ex[0], 1), "extra_homes_3yr_low": round(ex[1], 1), "extra_homes_3yr_high": round(ex[2], 1),
                       "stock_homes": stock_h, "share_3yr": round(ex[0] / stock_h, 6), "share_3yr_low": round(ex[1] / stock_h, 6),
                       "share_3yr_high": round(ex[2] / stock_h, 6), "note": note})
    for sid, (eff, label) in effects.items():
        sh = eff.five_year_share * sum(eff.timing[:CHECK_YEARS])
        checks.append({"check": "madison_share", "sizing": "net_effect", "scenario": sid, "basis": "scenario share of station-area stock in years 1-3",
                       "share_3yr": round(sh, 6), "stock_homes": stock, "note": eff.source})
    for sid in ("little", "typical", "strong"):
        g = by_area[(by_area.method == "A") & (by_area.scenario == sid)]
        sh = float(g[ycols[:CHECK_YEARS]].sum().sum()) / stock
        checks.append({"check": "madison_share", "sizing": "per_acre", "scenario": sid, "basis": "scenario share of station-area stock in years 1-3",
                       "share_3yr": round(sh, 6), "stock_homes": stock, "note": "method A per acre"})
    for sid, g in net.groupby("scenario", sort=False):
        checks += scale_rows(g, "net_effect", sid, sp)
    for sid, g in pa.groupby("scenario", sort=False):
        checks += scale_rows(g, "per_acre", sid, sp)
    checks += scale_rows(wa, "per_acre", "wisconsin_measured_uncapped", sp)
    checks += scale_rows(wc, "per_acre", "wisconsin_measured_capped", sp)
    write(pd.DataFrame(checks), "tod_model_net_checks.csv")
    print(state[state.year == "2027-2031"][["sizing", "scenario", "addition", "addition_share_of_stock", "baseline_near_stops_central"]].round(4).to_string(index=False))
    print(pd.DataFrame(sens)[["sensitivity", "sizing", "scenario", "addition_2027_2031", "milwaukee_metro_2027_2031", "madison_metro_2027_2031"]].round(0).to_string(index=False))
    ck = pd.DataFrame(checks)
    print(ck[ck.check == "madison_share"][["sizing", "scenario", "basis", "extra_homes_3yr", "share_3yr", "share_3yr_low", "share_3yr_high"]].to_string(index=False))
    sc = ck[ck.check == "scale"]
    print(sc.groupby(["sizing", "scenario", "metro"]).agg(peak=("total_per_1000", "max"), over_max=("exceeds_observed_max", "sum"),
                                                           over_p95=("exceeds_p95", "sum"), over_own=("exceeds_own_max", "sum")).round(2).to_string())


if __name__ == "__main__":
    main()

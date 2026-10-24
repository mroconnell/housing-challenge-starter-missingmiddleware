"""Areas table: Wisconsin state, counties, municipalities (county subdivisions),
tracts and block groups from TIGER/Line 2024, with parents and context groups.

Area identifiers
  state         "55"
  county        5-digit GEOID, e.g. "55025"
  municipality  "muni:" + 10-digit county-subdivision GEOID, e.g. "muni:5502548000"
                (wi_muni_id = the 10-digit GEOID; a multi-county city or village
                has one piece per county, sharing COUSUBFP)
  tract         11-digit GEOID
  block_group   12-digit GEOID

Context group rule (documented in docs/gate2/FOUNDATION.md). Every input is
measured on the WHOLE municipality (all county pieces summed), so the pieces of
a multi-county city or village always share one group:
  hu      = ACS 2020-2024 total housing units (B25024_001)
  density = hu / land square miles (TIGER ALAND)
  main county = the county piece holding most of the municipality's housing units
  1. urban            hu >= 20,000; or hu >= 10,000, density >= 300 and the
                      largest municipality (by hu) in its main county
                      (a regional city such as Wausau, Superior, Manitowoc)
  2. suburban         not urban, main county metropolitan (OMB 2023), and
                      density >= 425 HU per sq mi, or a city or village with
                      hu >= 2,500 (425 is the Census 2020 urban-area
                      housing-density threshold)
  3. small_community  any other city or village (incorporated)
  4. rural            any other town (unincorporated)
  Tracts and block groups take the group of the municipality covering most of
  their land; counties take the group holding most of their housing units.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

SQM_PER_SQMI = 2_589_988.110336
WI_CRS = "EPSG:3071"  # NAD83(HARN) / Wisconsin Transverse Mercator, metres
BOUNDARY_SOURCE_ID = "census_tiger_2024"
BOUNDARY_VINTAGE = "TIGER/Line 2024"

URBAN_MIN_HU = 20_000            # any municipality this large is urban
REGIONAL_CITY_MIN_HU = 10_000    # ... or this large and the largest in its county
REGIONAL_CITY_MIN_DENSITY = 300.0
SUBURBAN_MIN_DENSITY = 425.0     # Census 2020 urban-area housing-density threshold
SUBURBAN_MIN_HU_INCORPORATED = 2_500

CONTEXT_RULE = (
    "Measured on the whole municipality (all county pieces). hu = ACS 2020-2024 housing units; density = hu per "
    "land sq mi. urban: hu >= 20,000, or hu >= 10,000 with density >= 300 and the largest municipality in its main "
    "county; suburban: other municipality whose main county is metropolitan, with density >= 425 or (city/village "
    "with hu >= 2,500); small_community: other city or village; rural: other town. Tracts/block groups inherit "
    "from the municipality with most of their land; counties from the group holding most of their housing units."
)


def read_tiger(raw: Path, name: str, state_fips: str = "55") -> gpd.GeoDataFrame:
    g = gpd.read_file(f"zip://{raw / name}")
    if "STATEFP" in g.columns:
        g = g[g["STATEFP"] == state_fips]
    return g.reset_index(drop=True)


def muni_type(classfp: str, namelsad: str) -> str:
    if classfp == "Z9":
        return "not_defined"
    low = namelsad.lower()
    for t in ("city", "village", "town"):
        if low.endswith(" " + t):
            return t
    return "other"


def metro_counties(county: gpd.GeoDataFrame, cbsa: pd.DataFrame) -> pd.Series:
    """True where the county belongs to a metropolitan (LSAD M1) CBSA."""
    metro_ids = set(cbsa.loc[cbsa["LSAD"] == "M1", "CBSAFP"])
    return county.set_index("GEOID")["CBSAFP"].isin(metro_ids)


def assign_muni_context(munis: pd.DataFrame) -> pd.Series:
    """Apply the context rule to municipality pieces, using whole-municipality inputs.

    Expects columns: muni_type, hu_total_whole, density_whole (whole
    municipality across counties), metro_main (main county is metropolitan),
    largest_in_county (the whole municipality has the most housing units of
    any municipality in its main county).
    """
    hu, dens = munis["hu_total_whole"], munis["density_whole"]
    incorporated = munis["muni_type"].isin(["city", "village"])
    urban = (hu >= URBAN_MIN_HU) | (
        (hu >= REGIONAL_CITY_MIN_HU) & (dens >= REGIONAL_CITY_MIN_DENSITY) & munis["largest_in_county"].astype(bool))
    suburban = ~urban & munis["metro_main"].astype(bool) & (
        (dens >= SUBURBAN_MIN_DENSITY) | (incorporated & (hu >= SUBURBAN_MIN_HU_INCORPORATED)))
    out = np.select(
        [munis["muni_type"] == "not_defined", urban, suburban, incorporated, munis["muni_type"] == "town"],
        [None, "urban", "suburban", "small_community", "rural"],
        default=None,
    )
    return pd.Series(out, index=munis.index, dtype=object)


def majority_parent(child: gpd.GeoDataFrame, parent: gpd.GeoDataFrame, child_id: str, parent_id: str) -> pd.DataFrame:
    """For each child polygon, the parent with the largest land-area overlap and its share."""
    c = child[[child_id, "geometry"]].to_crs(WI_CRS)
    p = parent[[parent_id, "geometry"]].to_crs(WI_CRS)
    inter = gpd.overlay(c, p, how="intersection", keep_geom_type=True)
    inter["a"] = inter.geometry.area
    tot = inter.groupby(child_id)["a"].transform("sum")
    inter["share"] = inter["a"] / tot
    inter["n_parents"] = (inter["share"] > 0.01).groupby(inter[child_id]).transform("sum")
    best = inter.sort_values("a", ascending=False).drop_duplicates(child_id)
    return best[[child_id, parent_id, "share", "n_parents"]].rename(
        columns={parent_id: "parent", "share": "parent_share", "n_parents": "n_parent_overlaps"}
    )


def build_areas(raw_tiger: Path, raw_cbsa: Path, acs_hu: pd.DataFrame, acs_pop: pd.DataFrame, log=print):
    """Return (areas DataFrame, dict level -> GeoDataFrame of full-resolution geometry).

    acs_hu / acs_pop: DataFrames with columns geoid, level, value (ACS total
    housing units B25024_001, total population B01003_001).
    """
    state = read_tiger(raw_tiger, "tl_2024_us_state.zip")
    county = read_tiger(raw_tiger, "tl_2024_us_county.zip")
    cousub = read_tiger(raw_tiger, "tl_2024_55_cousub.zip")
    tract = read_tiger(raw_tiger, "tl_2024_55_tract.zip")
    bg = read_tiger(raw_tiger, "tl_2024_55_bg.zip")
    cbsa = gpd.read_file(f"zip://{raw_cbsa / 'cb_2024_us_cbsa_20m.zip'}", ignore_geometry=True)
    metro = metro_counties(county, cbsa)

    hu = {(r.level, r.geoid): r.value for r in acs_hu.itertuples()}
    pop = {(r.level, r.geoid): r.value for r in acs_pop.itertuples()}

    # --- municipalities
    m = cousub.copy()
    m["muni_type"] = [muni_type(c, n) for c, n in zip(m["CLASSFP"], m["NAMELSAD"])]
    m["county_geoid"] = m["STATEFP"] + m["COUNTYFP"]
    m["hu_total"] = [hu.get(("municipality", g), np.nan) for g in m["GEOID"]]
    m["sqmi"] = m["ALAND"] / SQM_PER_SQMI
    m["density"] = m["hu_total"] / m["sqmi"].where(m["sqmi"] > 0)
    whole = m.groupby("COUSUBFP").agg(hu_total_whole=("hu_total", "sum"), sqmi_whole=("sqmi", "sum"), n_pieces=("GEOID", "size"))
    whole["density_whole"] = whole["hu_total_whole"] / whole["sqmi_whole"].where(whole["sqmi_whole"] > 0)
    m = m.join(whole, on="COUSUBFP")
    m.loc[m["muni_type"] == "not_defined", "n_pieces"] = 1  # water placeholders share code 00000
    m["metro"] = m["county_geoid"].map(metro).fillna(False).astype(bool)
    # whole-municipality context inputs: main county = piece with most housing units
    real = m[m["muni_type"] != "not_defined"]
    main = (real.sort_values("hu_total", ascending=False, na_position="last")
            .drop_duplicates("COUSUBFP").set_index("COUSUBFP"))
    whole_tbl = whole.loc[main.index].assign(main_county=main["county_geoid"], metro_main=main["metro"])
    whole_tbl["largest_in_county"] = (whole_tbl["hu_total_whole"]
                                      == whole_tbl.groupby("main_county")["hu_total_whole"].transform("max"))
    m = m.join(whole_tbl[["main_county", "metro_main", "largest_in_county"]], on="COUSUBFP")
    m.loc[m["muni_type"] == "not_defined", ["metro_main", "largest_in_county"]] = False
    m["context_group"] = assign_muni_context(m)
    m["area_id"] = "muni:" + m["GEOID"]

    # --- tract / block group parents (majority land overlap with a municipality piece)
    land_m = m[m["ALAND"] > 0]
    log("  overlaying tracts and block groups on municipalities")
    tp = majority_parent(tract, land_m, "GEOID", "area_id").rename(columns={"GEOID": "geoid"})
    bp = majority_parent(bg, land_m, "GEOID", "area_id").rename(columns={"GEOID": "geoid"})
    ctx = m.set_index("area_id")["context_group"]

    rows = []
    st = state.iloc[0]
    rows.append(dict(area_id="55", geoid="55", level="state", name="Wisconsin", parent_county_id=None,
                     parent_municipality_id=None, parent_municipality_share=None, parent_tract_id=None,
                     land_area_sqm=float(st.ALAND), water_area_sqm=float(st.AWATER), muni_type=None,
                     cousubfp=None, n_county_pieces=None, metro_county=None))
    for r in county.itertuples():
        rows.append(dict(area_id=r.GEOID, geoid=r.GEOID, level="county", name=r.NAMELSAD, parent_county_id=None,
                         parent_municipality_id=None, parent_municipality_share=None, parent_tract_id=None,
                         land_area_sqm=float(r.ALAND), water_area_sqm=float(r.AWATER), muni_type=None,
                         cousubfp=None, n_county_pieces=None, metro_county=bool(metro.get(r.GEOID, False))))
    for r in m.itertuples():
        rows.append(dict(area_id=r.area_id, geoid=r.GEOID, level="municipality", name=r.NAMELSAD,
                         parent_county_id=r.county_geoid, parent_municipality_id=None, parent_municipality_share=None,
                         parent_tract_id=None, land_area_sqm=float(r.ALAND), water_area_sqm=float(r.AWATER),
                         muni_type=r.muni_type, cousubfp=r.COUSUBFP, n_county_pieces=int(r.n_pieces),
                         metro_county=bool(r.metro), context_group=r.context_group,
                         context_hu_whole=float(r.hu_total_whole) if r.muni_type != "not_defined" else None,
                         context_density_whole=(float(r.density_whole) if r.muni_type != "not_defined"
                                                and pd.notna(r.density_whole) else None),
                         context_main_county=r.main_county if isinstance(r.main_county, str) else None,
                         context_metro_main=bool(r.metro_main), context_largest_in_county=bool(r.largest_in_county)))
    tpi = tp.set_index("geoid")
    for r in tract.itertuples():
        p = tpi.loc[r.GEOID] if r.GEOID in tpi.index else None
        rows.append(dict(area_id=r.GEOID, geoid=r.GEOID, level="tract", name=r.NAMELSAD,
                         parent_county_id=r.STATEFP + r.COUNTYFP,
                         parent_municipality_id=None if p is None else p["parent"],
                         parent_municipality_share=None if p is None else float(p["parent_share"]),
                         n_municipality_overlaps=None if p is None else int(p["n_parent_overlaps"]),
                         parent_tract_id=None, land_area_sqm=float(r.ALAND), water_area_sqm=float(r.AWATER),
                         metro_county=bool(metro.get(r.STATEFP + r.COUNTYFP, False))))
    bpi = bp.set_index("geoid")
    for r in bg.itertuples():
        p = bpi.loc[r.GEOID] if r.GEOID in bpi.index else None
        rows.append(dict(area_id=r.GEOID, geoid=r.GEOID, level="block_group",
                         name=f"{r.NAMELSAD}, Census Tract {r.TRACTCE}",
                         parent_county_id=r.STATEFP + r.COUNTYFP,
                         parent_municipality_id=None if p is None else p["parent"],
                         parent_municipality_share=None if p is None else float(p["parent_share"]),
                         n_municipality_overlaps=None if p is None else int(p["n_parent_overlaps"]),
                         parent_tract_id=r.STATEFP + r.COUNTYFP + r.TRACTCE,
                         land_area_sqm=float(r.ALAND), water_area_sqm=float(r.AWATER),
                         metro_county=bool(metro.get(r.STATEFP + r.COUNTYFP, False))))
    areas = pd.DataFrame(rows)

    # context for tracts / BGs from their majority municipality
    sub = areas["level"].isin(["tract", "block_group"])
    areas.loc[sub, "context_group"] = areas.loc[sub, "parent_municipality_id"].map(ctx)
    # population, housing units, density
    areas["population"] = [pop.get((lv, g), np.nan) for lv, g in zip(areas["level"], areas["geoid"])]
    areas["population_source"] = "ACS 2020-2024 5-year B01003_001 (census_acs5_2024_tbsf)"
    areas["housing_units_acs"] = [hu.get((lv, g), np.nan) for lv, g in zip(areas["level"], areas["geoid"])]
    sqmi = areas["land_area_sqm"] / SQM_PER_SQMI
    areas["hu_density_per_sqmi"] = areas["housing_units_acs"] / sqmi.where(sqmi > 0)
    # counties: group holding most of the county's housing units
    mm = areas[areas["level"] == "municipality"]
    cg = (mm.groupby(["parent_county_id", "context_group"])["housing_units_acs"].sum().reset_index()
          .sort_values("housing_units_acs", ascending=False).drop_duplicates("parent_county_id")
          .set_index("parent_county_id")["context_group"])
    isc = areas["level"] == "county"
    areas.loc[isc, "context_group"] = areas.loc[isc, "area_id"].map(cg)
    areas["context_rule"] = np.where(areas["level"] == "state", None, CONTEXT_RULE)
    areas["parent_ids"] = [
        [x for x in (c, mu, t) if isinstance(x, str)]
        for c, mu, t in zip(areas["parent_county_id"], areas["parent_municipality_id"], areas["parent_tract_id"])
    ]
    areas["boundary_source_id"] = BOUNDARY_SOURCE_ID
    areas["boundary_vintage"] = BOUNDARY_VINTAGE

    geoms = {
        "state": state[["GEOID", "geometry"]].assign(area_id="55"),
        "county": county[["GEOID", "geometry"]].assign(area_id=county["GEOID"]),
        "municipality": m[["GEOID", "geometry"]].assign(area_id=m["area_id"]),
        "tract": tract[["GEOID", "geometry"]].assign(area_id=tract["GEOID"]),
        "block_group": bg[["GEOID", "geometry"]].assign(area_id=bg["GEOID"]),
    }
    return areas, geoms

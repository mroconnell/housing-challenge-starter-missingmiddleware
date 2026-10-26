"""Allocate the adopted area results to Wisconsin State Assembly districts (2024 plan) and Senate districts (Gate 5).

Method (block-weighted shares of each municipality's one-unit detached homes):
1. Each 2020 census block gets an estimated count of one-unit detached homes:
       w_b = HOUSING20_b x (B25024_002 / B25024_001 of its block group, ACS 2020-2024)
   i.e. the block's 2020 census housing units times its block group's detached share. A block group with no
   ACS housing units takes its county's detached share.
2. Each block's internal point (INTPTLAT20/INTPTLON20) is placed in a model area (2024 TIGER county subdivision,
   data/processed/foundation/geo/areas_municipality.parquet) and in an Assembly district (LTSB 2024 layer).
   Points on no polygon (shoreline and boundary slivers) take the nearest polygon.
3. Share of area m in district d: s[m,d] = sum of w_b over blocks in (m, d) / sum of w_b over blocks in m.
   Fallbacks, in order, for areas with model homes but no block weight: (a) shares of the area's land polygon
   by district (area weights); an area that touches no district goes to the explicit "unallocated" row.
4. District value = sum over areas of s[m,d] x the area's value (baseline and additional, every path and year).
   An explicit "unallocated" row carries the state total minus the sum of districts (zero when every area is
   allocated), so every table reconciles to Wisconsin for every path and year.
5. Senate districts aggregate their three Assembly districts (SEN2024 attribute of the Assembly layer; checked
   against the Senate layer by overlap).

For comparison, the same allocation with plain area weights (share of each area's polygon in each district) is
computed and the difference reported (docs/gate5/MODEL_CHECKS.md).

Weaknesses: 2020 blocks against 2024 county-subdivision boundaries (annexations since 2020 put a few blocks in the
wrong area; the area totals still come from the model, only the split moves); 2020 housing counts, not 2024; the
block group's detached share is applied evenly to its blocks, so a block of apartments inside a mostly-detached
block group gets too many homes; the model allocates each area's result in proportion to its homes, not to where
within the area ADUs would be built.

Inputs: data/raw/census_tiger_2020_tabblock/tl_2020_55_tabblock20.zip, data/raw/wi_assembly_districts/assembly_2024.geojson,
data/raw/wi_senate_districts/senate_2024.geojson (scripts/fetch_legislative_districts.py),
data/processed/foundation/inventory.parquet and geo/areas_municipality.parquet (scripts/build_foundation.py),
data/processed/model_run/results_long.parquet (scripts/run_adu_model.py).
Outputs:
  reference/adu_model_by_assembly_district.csv   district x path x year (2027..2031 and 2027-2031)
  reference/adu_model_by_senate_district.csv     the same for Senate districts
  reference/adu_model_district_crosswalk.csv     area x Assembly district shares (with method)
  data/processed/districts/geo_assembly.geojson, geo_senate.geojson   simplified outlines (WGS84) for the UI
  data/processed/districts/allocation_checks.json
Run: uv run python scripts/build_district_allocation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missing_middleware.paths import PROCESSED, RAW, REFERENCE, processed_dir  # noqa: E402

EQUAL_AREA = "EPSG:3071"     # Wisconsin Transverse Mercator (metres)
UNALLOCATED = "unallocated"
PATHS = ("lower", "central", "upper")
SIMPLIFY_M = 150             # outline simplification tolerance for the UI (metres)


def load_blocks() -> pd.DataFrame:
    b = gpd.read_file(f"zip://{RAW / 'census_tiger_2020_tabblock/tl_2020_55_tabblock20.zip'}", ignore_geometry=True,
                      columns=["GEOID20", "HOUSING20", "INTPTLAT20", "INTPTLON20", "ALAND20"])
    b["bg"] = b.GEOID20.str[:12]
    b["county"] = b.GEOID20.str[:5]
    b["lat"] = b.INTPTLAT20.astype(float)
    b["lon"] = b.INTPTLON20.astype(float)
    return b.drop(columns=["INTPTLAT20", "INTPTLON20"])


def detached_weights(blocks: pd.DataFrame, inv: pd.DataFrame) -> pd.Series:
    """w_b = HOUSING20 x the block group's ACS detached share (county share where the block group has no units)."""
    def share(level):
        g = inv[inv.level.eq(level)].set_index("geoid")
        return (g.homes_1unit_detached / g.total_housing_units).where(g.total_housing_units > 0)
    s = blocks.bg.map(share("block_group"))
    s = s.fillna(blocks.county.map(share("county"))).fillna(0.0)
    return blocks.HOUSING20.astype(float) * s


def locate(points: gpd.GeoDataFrame, polys: gpd.GeoDataFrame, key: str) -> pd.Series:
    """Polygon `key` for each point: within, else nearest (both in EQUAL_AREA)."""
    j = gpd.sjoin(points, polys[[key, "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    miss = j[key].isna()
    if miss.any():
        nn = gpd.sjoin_nearest(points[miss], polys[[key, "geometry"]], how="left")
        nn = nn[~nn.index.duplicated(keep="first")]
        j.loc[miss, key] = nn[key]
    return j[key], miss


def area_weight_shares(munis: gpd.GeoDataFrame, dist: gpd.GeoDataFrame) -> pd.DataFrame:
    """Share of each area's polygon in each district (plain area weights)."""
    ov = gpd.overlay(munis[["area_id", "geometry"]], dist[["district", "geometry"]], how="intersection", keep_geom_type=True)
    ov["a"] = ov.geometry.area
    ov = ov.groupby(["area_id", "district"], as_index=False)["a"].sum()
    ov["share"] = ov.a / ov.groupby("area_id").a.transform("sum")
    return ov[ov.share > 1e-9][["area_id", "district", "share"]]


def allocate(values: pd.DataFrame, shares: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """values: area_id + keys + numeric columns; shares: area_id, district, share. Adds the unallocated row."""
    if not keys:
        return allocate(values.assign(_k=0), shares, ["_k"]).drop(columns="_k")
    num = [c for c in values.columns if c not in ["area_id"] + keys]
    m = values.merge(shares.assign(district=shares.district.astype(str)), on="area_id", how="left")
    m["district"] = m["district"].astype(object).where(m["district"].notna(), UNALLOCATED)
    m["share"] = m["share"].fillna(1.0)
    for c in num:
        m[c] = m[c] * m["share"]
    out = m.groupby(["district"] + keys, as_index=False)[num].sum()
    state = values.groupby(keys)[num].sum()
    alloc = out[out.district.ne(UNALLOCATED)].groupby(keys)[num].sum()
    un = (state - alloc.reindex(state.index).fillna(0)).reset_index()
    un.insert(0, "district", UNALLOCATED)
    out = pd.concat([out[out.district.ne(UNALLOCATED)], un], ignore_index=True)
    return out


def main():
    inv = pd.read_parquet(PROCESSED / "foundation/inventory.parquet")
    munis = gpd.read_parquet(PROCESSED / "foundation/geo/areas_municipality.parquet").to_crs(EQUAL_AREA)
    asm = gpd.read_file(RAW / "wi_assembly_districts/assembly_2024.geojson").to_crs(EQUAL_AREA)
    sen = gpd.read_file(RAW / "wi_senate_districts/senate_2024.geojson").to_crs(EQUAL_AREA)
    asm["district"] = asm.ASM2024.astype(int)
    asm["senate"] = asm.SEN2024.astype(int)
    sen_col = [c for c in sen.columns if c.upper().startswith("SEN")][0]
    sen["district"] = sen[sen_col].astype(int)
    res = pd.read_parquet(PROCESSED / "model_run/results_long.parquet")
    homes = res.drop_duplicates("area_id").set_index("area_id")["homes"]
    checks = {}

    # 1-2. blocks: weights, area and district
    blocks = load_blocks()
    blocks["w"] = detached_weights(blocks, inv)
    pts = gpd.GeoDataFrame(blocks, geometry=gpd.points_from_xy(blocks.lon, blocks.lat), crs="EPSG:4269").to_crs(EQUAL_AREA)
    blocks["area_id"], miss_m = locate(pts, munis, "area_id")
    blocks["district"], miss_d = locate(pts, asm, "district")
    blocks["district"] = blocks["district"].astype(int)
    checks["blocks"] = {"n": int(len(blocks)), "housing20": int(blocks.HOUSING20.sum()),
                        "detached_weight": round(float(blocks.w.sum()), 1),
                        "points_nearest_area": int(miss_m.sum()), "points_nearest_district": int(miss_d.sum())}

    # 3. shares, with fallbacks
    bw = blocks.groupby(["area_id", "district"], as_index=False).w.sum()
    tot = bw.groupby("area_id").w.transform("sum")
    bw = bw[tot > 0].assign(share=lambda d: d.w / d.groupby("area_id").w.transform("sum"))
    bw = bw[bw.share > 0][["area_id", "district", "share"]].assign(method="blocks (2020 housing units x ACS detached share)")
    aw = area_weight_shares(munis, asm)
    need = homes[homes > 0].index.difference(bw.area_id.unique())
    fb = aw[aw.area_id.isin(need)].assign(method="area weights (no block weight in this area)")
    shares = pd.concat([bw, fb], ignore_index=True)
    no_share = sorted(set(homes[homes > 0].index) - set(shares.area_id))
    checks["areas"] = {"with_homes": int((homes > 0).sum()), "block_shares": int(bw.area_id.nunique()),
                       "area_weight_fallback": int(fb.area_id.nunique()),
                       "fallback_ids": sorted(fb.area_id.unique().tolist()),
                       "unallocated_areas": no_share,
                       "unallocated_homes": int(homes.loc[no_share].sum()) if no_share else 0,
                       "split_areas": int((shares.groupby("area_id").size() > 1).sum())}
    # block weight vs model homes by area (how well 2020 blocks x ACS share reproduce the ACS area count)
    wa = blocks.groupby("area_id").w.sum().reindex(homes.index).fillna(0)
    big = homes.ge(500)
    ratio = (wa / homes)[big]
    checks["block_weight_vs_acs_homes"] = {
        "state_ratio": round(float(wa.sum() / homes.sum()), 4),
        "areas_500plus_homes": int(big.sum()),
        "areas_500plus_ratio_outside_0.8_1.25": int(((ratio < 0.8) | (ratio > 1.25)).sum()),
        "median_ratio_areas_500plus": round(float(ratio.median()), 4)}

    crosswalk = shares.merge(asm[["district", "senate"]], on="district", how="left")
    crosswalk = crosswalk.merge(homes.rename("area_homes"), left_on="area_id", right_index=True)
    crosswalk["homes_allocated"] = crosswalk.area_homes * crosswalk.share
    names = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id"]]
    crosswalk = crosswalk.merge(names, on="area_id", how="left").rename(columns={"district": "assembly_district",
                                                                                "senate": "senate_district"})
    crosswalk = crosswalk[["area_id", "name", "parent_county_id", "assembly_district", "senate_district", "share",
                           "area_homes", "homes_allocated", "method"]].sort_values(["area_id", "assembly_district"])
    crosswalk.round({"share": 6, "homes_allocated": 2}).to_csv(REFERENCE / "adu_model_district_crosswalk.csv", index=False)

    # 4. allocate every path and year
    vals = res[["area_id", "path", "year", "baseline_units", "additional_units"]].copy()
    vals["forecast_year"] = (2026 + vals.year).astype(str)
    five = vals.groupby(["area_id", "path"], as_index=False)[["baseline_units", "additional_units"]].sum()
    five["forecast_year"] = "2027-2031"
    vals = pd.concat([vals.drop(columns="year"), five], ignore_index=True)
    a = allocate(vals, shares[["area_id", "district", "share"]], ["path", "forecast_year"])
    h = allocate(homes.rename("homes").reset_index(), shares[["area_id", "district", "share"]], [])
    a = a.merge(h, on="district", how="left")

    def finish(t: pd.DataFrame, level: str) -> pd.DataFrame:
        t = t.copy()
        t["total_with_law"] = t.baseline_units + t.additional_units
        yrs = np.where(t.forecast_year.eq("2027-2031"), 5, 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            t["additional_per_1000_homes_per_year"] = np.where(t.homes > 0, t.additional_units / yrs / t.homes * 1000, np.nan)
            t["baseline_per_1000_homes_per_year"] = np.where(t.homes > 0, t.baseline_units / yrs / t.homes * 1000, np.nan)
        t.insert(0, "level", level)
        t["district_label"] = np.where(t.district.astype(str).eq(UNALLOCATED), "Not allocated to a district",
                                       f"{level.title()} District " + t.district.astype(str))
        t["sort"] = pd.to_numeric(t.district, errors="coerce").fillna(999)
        t = t.sort_values(["sort", "path", "forecast_year"]).drop(columns="sort")
        return t[["level", "district", "district_label", "path", "forecast_year", "homes", "baseline_units",
                  "additional_units", "total_with_law", "baseline_per_1000_homes_per_year",
                  "additional_per_1000_homes_per_year"]]

    asm_t = finish(a, "assembly")
    sen_map = asm.set_index(asm.district.astype(str))["senate"].astype(str)
    s = a.copy()
    s["district"] = s.district.map(lambda d: sen_map.get(d, UNALLOCATED) if d != UNALLOCATED else UNALLOCATED)
    s = s.groupby(["district", "path", "forecast_year"], as_index=False)[["baseline_units", "additional_units", "homes"]].sum()
    sen_t = finish(s, "senate")
    asm_t.round(4).to_csv(REFERENCE / "adu_model_by_assembly_district.csv", index=False)
    sen_t.round(4).to_csv(REFERENCE / "adu_model_by_senate_district.csv", index=False)

    # reconciliation: every path x year, both chambers
    state = vals.groupby(["path", "forecast_year"])[["baseline_units", "additional_units"]].sum()
    rec = {}
    for name, t in (("assembly", asm_t), ("senate", sen_t)):
        g = t.groupby(["path", "forecast_year"])[["baseline_units", "additional_units"]].sum()
        gap = float((g - state).abs().max().max())
        un = t[t.district.astype(str).eq(UNALLOCATED)]
        rec[name] = {"districts": int(t.district.astype(str).ne(UNALLOCATED).groupby(t.district).any().sum()),
                     "max_gap_permits": gap, "unallocated_max_abs": float(un[["baseline_units", "additional_units"]].abs().max().max()),
                     "homes_total": float(t[t.path.eq("central") & t.forecast_year.eq("2027-2031")].homes.sum())}
        if gap > 1e-6:
            raise SystemExit(f"{name} districts do not reconcile to the state (gap {gap})")
    checks["reconciliation"] = rec

    # Senate: Assembly-to-Senate nesting checked against the Senate layer by overlap
    ov = gpd.overlay(asm[["district", "senate", "geometry"]], sen[["district", "geometry"]].rename(columns={"district": "sen_layer"}),
                     how="intersection", keep_geom_type=True)
    ov["a"] = ov.geometry.area
    best = ov.sort_values("a").groupby("district").tail(1).set_index("district")
    frac = (best.a / asm.set_index("district").geometry.area).min()
    checks["senate_nesting"] = {"assembly_in_named_senate": bool((best.sen_layer == best.senate).all()),
                                "min_share_of_assembly_area_in_its_senate": round(float(frac), 4),
                                "assembly_per_senate": sorted(set(asm.groupby("senate").size().tolist()))}

    # comparison: plain area weights
    a2 = allocate(vals, aw, ["path", "forecast_year"])
    cmpd = a[a.forecast_year.eq("2027-2031") & a.path.eq("central")].set_index("district")["additional_units"]
    cmp2 = a2[a2.forecast_year.eq("2027-2031") & a2.path.eq("central")].set_index("district")["additional_units"]
    d = (cmp2.reindex(cmpd.index).fillna(0) - cmpd)
    d = d[d.index != UNALLOCATED]
    checks["area_weight_comparison_central_additional_2027_2031"] = {
        "sum_abs_difference_permits": round(float(d.abs().sum()), 1),
        "half_sum_abs_difference_share_of_state": round(float(d.abs().sum() / 2 / cmpd.sum()), 4),
        "max_abs_difference_permits": round(float(d.abs().max()), 1),
        "district_max": int(d.abs().idxmax()),
        "median_abs_difference_permits": round(float(d.abs().median()), 1)}
    pd.DataFrame({"assembly_district": cmpd.index, "additional_blocks": cmpd.values,
                  "additional_area_weights": cmp2.reindex(cmpd.index).fillna(0).values}).to_csv(
        processed_dir("districts") / "area_weight_comparison.csv", index=False)

    # 5. simplified outlines for the UI
    od = processed_dir("districts")
    for name, g, extra in (("assembly", asm, ["senate"]), ("senate", sen, [])):
        out = g[["district"] + extra + ["geometry"]].copy()
        out["geometry"] = out.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
        out = out.to_crs("EPSG:4326")
        out["geometry"] = out.geometry.set_precision(1e-5)
        p = od / f"geo_{name}.geojson"
        p.unlink(missing_ok=True)
        out.to_file(p, driver="GeoJSON")
        checks[f"geo_{name}_bytes"] = p.stat().st_size
    (od / "allocation_checks.json").write_text(json.dumps(checks, indent=2, default=str) + "\n")
    print(json.dumps(checks, indent=2, default=str))


if __name__ == "__main__":
    main()

"""Wisconsin lot table for the station-area lot model (docs/tod/STATION_AREA_PLAN.md, LOCKED; stage 1 notes).

One row per City of Milwaukee and City of Madison lot within 1 mile (1,609 m) of a Wisconsin rail or rapid stop
(reference/tod_stops.csv, flag_a_rapid == 1) that lies in one of the two cities, in the training lot tables' columns
(scripts/build_tod_station_lot_table.py) so scripts/run_tod_station_lotmodel.py's features can be computed:

    case (wi_milwaukee / wi_madison), city_name, group = "reform" (the law applies at every such stop), stop_id,
    dist_m, band (0-1/4, 1/4-1/2, 1/2-1 mile at 402 / 805 / 1,609 m), in_reform_area (lot the proposed law would
    upzone: the `treated` flag of data/processed/tod_lot_model/wi_lots.parquet matched by location; lots outside that
    table get False and reform_flag_source says so), acres, land_value, bldg_value, year_built, public, use,
    homes_existing (homes standing before 2020), homes_before_win (homes built 2020-2024: the 5 years before the
    law's start, eff = 2025), homes_after_win = NaN, implausible = False, x, y (EPSG 5070).

Sources (local; no owner names or addresses are read):
    Milwaukee: MPROP (assessed land and improvements, taxable plus exempt; year built; units; land use; exempt type)
        joined to parcel outlines in data/raw/tod_capacity/v12_milwaukee.geojson by tax key; outlines without an
        MPROP record take the v12 values.
    Madison: City tax parcels (units, year built, property class; no values) with land and improvement values from
        the statewide parcel file V9 (2023 roll) by parcel number.
    Homes: lot unit counts where the lot has an assessor record (residential uses only, as build_tod_station_areas);
        lots with no record take their 2020 census block's homes not already on recorded lots, spread by lot area.
    Stacked condominium outlines are one lot (homes and values summed), as in build_tod_station_areas.

Then the neighborhood traits are joined with the training functions (scripts/enrich_tod_station_lots.py): EPA Smart
Location Database v3 block group, LODES block-group job growth over the 5 years before 2025 (2019 -> 2022, the latest
LODES year held), historic register listed before 2025, and the 78 tract variables from the latest 5-year ACS held
locally (2018-2022; the 2020-2024 release is not in data/raw/tod_allvars).

    .venv/bin/python scripts/build_tod_station_wisconsin.py

Writes data/processed/tod_station_area/wi_lots_station.parquet (local only). The file name does not start with
"lots_", so the training runs (which glob lots_*.parquet) never pick it up.
"""
from __future__ import annotations

import importlib.util as ilu
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import transit as T  # noqa: E402
import enrich_tod_station_lots as E  # noqa: E402

CRS, CRS_M = 5070, 3071
QUARTER, HALF, MILE = 402.0, 805.0, 1609.0
M2_PER_ACRE = 4046.8564224
EFF = 2025                    # law's start for windows: before window 2020-2024 (5 years)
BEFORE = (2020, 2024)
ACS_EFF = 2023                # survey_end_year(2023) = 2022: the latest 5-year ACS held locally
OUT = ROOT / "data" / "processed" / "tod_station_area"
OUT_FILE = OUT / "wi_lots_station.parquet"
WI_LOTS = ROOT / "data" / "processed" / "tod_lot_model" / "wi_lots.parquet"
BLOCKS = RAW / "census_tiger_2020_tabblock" / "tl_2020_55_tabblock20.zip"
COUSUB = RAW / "census_cb_2024" / "cb_2024_55_cousub_500k.zip"
V9 = str(RAW / "tod_land_values" / "wi_parcels_v9_2023.zip") + "/V9.0.1_Wisconsin_Parcels_2023_10.3_Uncompressed.gdb"
MILWAUKEE_CITY, MADISON_CITY = "5507953000", "5502548000"
STATEWIDE_HALF_MILE = 89_528  # docs/tod/TRANSIT_PIPELINE.md section 4, definition (a)


def _load(name: str):
    spec = ilu.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SA = _load("build_tod_station_areas")


def group_outlines(g: pd.DataFrame, sums: list[str], firsts: list[str]) -> pd.DataFrame:
    """Collapse records sharing one outline (stacked condominium units) into one lot, the way
    build_tod_station_areas.group_by_outline does (sorted by homes, so 'first' is the record with most homes, and the
    representative point is the same as wi_lots.parquet's)."""
    g = g.copy()
    g["_wkb"] = X.outline_keys(list(g.geometry))           # equal exactly when the outlines are (as WKB)
    g = g[g["_wkb"].notna()].sort_values("homes", ascending=False, kind="stable")
    agg = {**{c: "sum" for c in sums}, **{c: "first" for c in firsts}, "geometry": "first",
           "year_built": "min", "public": "all", "matched": "any"}
    out = g.groupby("_wkb", sort=False).agg(agg).reset_index(drop=True)
    out["ptx"], out["pty"] = X.interior_points(list(out.geometry))      # GEOS representative point
    out["acres"] = X.areas(list(out.geometry)) / M2_PER_ACRE
    return out


# --------------------------------------------------------------------------- lots

def milwaukee_lots() -> pd.DataFrame:
    cols = ["TAXKEY", "C_A_LAND", "C_A_IMPRV", "C_A_EXM_LAND", "C_A_EXM_IMPRV", "C_A_EXM_TYPE", "YR_BUILT", "NR_UNITS",
            "LAND_USE", "LAND_USE_GP"]
    m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", dtype=str, usecols=cols).drop_duplicates("TAXKEY")
    num = {c: pd.to_numeric(m[c], errors="coerce") for c in cols if c.startswith(("C_A_", "YR_", "NR_")) and c != "C_A_EXM_TYPE"}
    res = m.LAND_USE.fillna("").str.startswith("88") & (m.LAND_USE_GP != "12")   # homes: residential uses only
    m = pd.DataFrame({"TAXKEY": m.TAXKEY, "use": m.LAND_USE.fillna(""),
                      "land_value": num["C_A_LAND"].fillna(0) + num["C_A_EXM_LAND"].fillna(0),
                      "bldg_value": num["C_A_IMPRV"].fillna(0) + num["C_A_EXM_IMPRV"].fillna(0),
                      "public": m.C_A_EXM_TYPE.notna().values,
                      "year_built": num["YR_BUILT"].where(num["YR_BUILT"] > 1800).values,
                      "homes": np.where(res, num["NR_UNITS"].fillna(0), 0.0)})
    v = X.read_vector(RAW / "tod_capacity" / "v12_milwaukee.geojson", dst=CRS_M, columns=["PARCELID", "PLACENAME", "LNDVALUE", "IMPVALUE"])
    v = v[v.PLACENAME == "CITY OF MILWAUKEE"]
    v = v.merge(m, left_on="PARCELID", right_on="TAXKEY", how="left")
    v["matched"] = v.TAXKEY.notna()
    # a tax key on two outlines carries its homes and values once
    again = v.matched & v.duplicated("PARCELID")
    v.loc[again, ["homes", "land_value", "bldg_value"]] = 0.0
    v["land_value"] = v.land_value.where(v.matched, pd.to_numeric(v.LNDVALUE, errors="coerce"))
    v["bldg_value"] = v.bldg_value.where(v.matched, pd.to_numeric(v.IMPVALUE, errors="coerce"))
    v["public"] = v.public.fillna(False).astype(bool)
    v["use"] = v.use.fillna("")
    v["homes"] = v.homes.fillna(0.0)
    yb = v.year_built
    v["homes_before_win"] = np.where(yb.between(*BEFORE), v.homes, 0.0)
    v["homes_existing_rec"] = np.where(~(yb >= BEFORE[0]), v.homes, 0.0)      # unknown year counts as existing
    L = group_outlines(v, ["homes", "homes_before_win", "homes_existing_rec", "land_value", "bldg_value"], ["use"])
    L["city_name"], L["case"] = "Milwaukee", "wi_milwaukee"
    L["value_source"] = np.where(L.matched, "MPROP 2026 (taxable + exempt)", "v12 parcel file")
    return L


def madison_lots() -> pd.DataFrame:
    g = X.read_vector(RAW / "madison_parcels" / "tax_parcels.geojson", dst=CRS_M,
                      columns=["Parcel", "PropertyClass", "PropertyUse", "TotalDwellingUnits", "YearBuilt"])
    units = pd.to_numeric(g.TotalDwellingUnits, errors="coerce").fillna(0)
    notation = g.PropertyUse.fillna("").str.lower().isin(SA.MAD_CONDO_NOTATION)   # whole-condo records: homes are on units
    g["homes"] = np.where(notation, 0.0, units)
    yb = pd.to_numeric(g.YearBuilt, errors="coerce")
    g["year_built"] = yb.where(yb > 1800)
    g["public"] = g.PropertyClass.fillna("").str.strip().eq("Exempt")
    g["use"] = g.PropertyUse.fillna("")
    g["matched"] = True
    v9 = X.read_gdb(V9, ["PARCELID", "PLACENAME", "LNDVALUE", "IMPVALUE"], where={"PLACENAME": "CITY OF MADISON"},
                    geometry=False, contains=b"CITY OF MADISON").drop_duplicates("PARCELID").set_index("PARCELID")
    g["land_value"] = g.Parcel.map(v9.LNDVALUE).astype(float)
    g["bldg_value"] = g.Parcel.map(v9.IMPVALUE).astype(float)
    g["has_value"] = g.land_value.notna().astype(float)
    g["homes_before_win"] = np.where(g.year_built.between(*BEFORE), g.homes, 0.0)
    g["homes_existing_rec"] = np.where(~(g.year_built >= BEFORE[0]), g.homes, 0.0)
    L = group_outlines(g, ["homes", "homes_before_win", "homes_existing_rec", "land_value", "bldg_value", "has_value"], ["use"])
    L.loc[L.has_value == 0, ["land_value", "bldg_value"]] = np.nan   # no V9 record: unknown, not zero
    L["city_name"], L["case"] = "Madison", "wi_madison"
    L["value_source"] = np.where(L.has_value > 0, "statewide parcels V9 (2023 roll)", "none")
    return L.drop(columns="has_value")


def census_fallback(L: pd.DataFrame, blocks: pd.DataFrame) -> pd.Series:
    """Homes for lots with no assessor record: the 2020 block's homes not already on recorded lots, spread over the
    block's unrecorded lots by area."""
    k = X.first_within(L.ptx.values, L.pty.values, list(blocks.geometry))
    blk = pd.Series(np.where(k >= 0, blocks.GEOID20.values[np.maximum(k, 0)], None), index=L.index, dtype=object).where(k >= 0)
    rec = L.homes_existing_rec.where(L.matched, 0).groupby(blk).sum()
    resid = (blocks.set_index("GEOID20").HOUSING20.astype(float) - rec.reindex(blocks.GEOID20).fillna(0).values).clip(lower=0)
    un = ~L.matched
    area = L.acres.where(un, 0).groupby(blk).transform("sum")
    out = (blk.map(resid) * L.acres / area.where(area > 0)).where(un, 0).fillna(0)
    return out


# --------------------------------------------------------------------------- stops

def muni_of(px: np.ndarray, py: np.ndarray, cs: pd.DataFrame) -> np.ndarray:
    """GEOID of the county subdivision holding each point (the nearest one when none does)."""
    polys = list(cs.geometry)
    pi, gi = X.point_poly_pairs(px, py, polys)
    out = np.full(len(px), -1)
    out[pi] = gi                      # several matches: the last one, as numpy assignment did with the STRtree pairs
    miss = np.flatnonzero(out < 0)
    if len(miss):
        out[miss] = X.nearest_polygon(px[miss], py[miss], polys, 1e7)[0]
    return cs.GEOID.values[out]


def stations(cs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rail and rapid stops; platforms within 150 m are one station (as ntm_stations in the training builder)."""
    s = pd.read_csv(REFERENCE / "tod_stops.csv", dtype={"stop_id": str, "ntd_id": str})
    s = s[s.flag_a_rapid == 1]
    g = s[["agency", "stop_id"]].copy()
    g["x"], g["y"] = X.transform(s.lon.values, s.lat.values, 4326, CRS_M)
    g["muni"] = muni_of(g.x.values, g.y.values, cs)
    keep = g[g.muni.isin([MILWAUKEE_CITY, MADISON_CITY])]
    cx, cy, i = X.merge_stops(keep.x.values, keep.y.values, 75.0)
    st = pd.DataFrame({"stop_id": np.arange(len(cx)), "x": cx, "y": cy,
                       "agency": keep.agency.values[i], "muni": keep.muni.values[i]})
    return st, g


# --------------------------------------------------------------------------- enrichment (training functions)

def enrich(D: pd.DataFrame) -> pd.DataFrame:
    """enrich_tod_station_lots.enrich() for a frame, with Wisconsin's years (no edit to that script)."""
    pts = D[["x", "y"]]
    keep = ["sld_transit_freq", "sld_transit_freq_sqmi", "sld_jobs_per_acre", "sld_transit_job_access", "sld_share_no_car", "sld_walk_index"]
    j = E.join_first(pts, E.sld(3, "55"), ["GEOID10", "GEOID20", *keep])
    for c in keep:
        D[c] = j[c].reindex(D.index).values
    D["bg_geoid"] = j.GEOID10.reindex(D.index).values
    D["sld_version"] = 3
    D["sld_transit_freq_v2"] = E.join_first(pts, E.sld(2, "55"), ["sld_transit_freq"]).sld_transit_freq.values
    bg20 = j.GEOID20.reindex(D.index)
    a, b = E.lodes_bg("55", EFF - 1), E.lodes_bg("55", EFF - 6)
    D["bg_job_growth_5y"] = (bg20.map(a) / bg20.map(b).where(lambda v: v > 0) - 1).clip(-0.9, 5).values
    h = E.nrhp()
    h = h[h.listed.fillna(0) < EFF]
    D["historic"] = E.in_any_polygon(pts, h)
    E.tract_vars(D, pts, ACS_EFF, ["55"])
    return D


# --------------------------------------------------------------------------- build

def build() -> pd.DataFrame:
    cs = X.read_vector(COUSUB, dst=CRS_M).reset_index(drop=True)
    st, allstops = stations(cs)
    print(f"rail/rapid stops statewide {len(allstops)}; in Milwaukee or Madison {int(allstops.muni.isin([MILWAUKEE_CITY, MADISON_CITY]).sum())}"
          f" -> {len(st)} stations (platforms within 150 m merged)", flush=True)
    print("  stops outside the two cities by place:", allstops[~allstops.muni.isin([MILWAUKEE_CITY, MADISON_CITY])]
          .muni.map(cs.set_index("GEOID").NAMELSAD).value_counts().to_dict(), flush=True)
    blocks = X.read_vector(BLOCKS, dst=CRS_M, columns=["GEOID20", "HOUSING20"])
    bb_blocks = X.feature_bounds(list(blocks.geometry))
    parts = []
    for name, f in (("Milwaukee", milwaukee_lots), ("Madison", madison_lots)):
        print(f"{name} lots ...", flush=True)
        L = f()
        fbb = X.feature_bounds(list(L.geometry))
        bb = (np.nanmin(fbb[:, 0]), np.nanmin(fbb[:, 1]), np.nanmax(fbb[:, 2]), np.nanmax(fbb[:, 3]))
        cx = ~((bb_blocks[:, 0] > bb[2]) | (bb_blocks[:, 2] < bb[0]) | (bb_blocks[:, 1] > bb[3]) | (bb_blocks[:, 3] < bb[1]))
        fb = census_fallback(L, blocks[cx])
        L["homes_existing"] = L.homes_existing_rec.where(L.matched, fb)
        L["homes_source"] = np.where(L.matched, "assessor units", "2020 census block remainder by area")
        # distance check against every Wisconsin rail/rapid stop (including ones outside the two cities)
        d_all = SA.nearest_distance(L.ptx.values, L.pty.values, allstops)
        ni, nd = X.nearest_lowest(L.ptx.values, L.pty.values, st.x.values, st.y.values, MILE)
        near = pd.DataFrame({"stop_id": st.stop_id.values[ni[ni >= 0]], "dist_m": nd[ni >= 0]}, index=L.index[ni >= 0])
        extra = int(((d_all <= MILE) & ~L.index.isin(near.index)).sum())
        print(f"  {name}: lots {len(L):,}; within 1 mile of a kept station {len(near):,}; "
              f"lots within 1 mile only of stops outside the two cities (left out) {extra:,}", flush=True)
        D = L.loc[near.index].copy()
        D[["stop_id", "dist_m"]] = near[["stop_id", "dist_m"]]
        parts.append(D)
    D = pd.concat(parts, ignore_index=True)
    D["x"], D["y"] = X.transform(D.ptx.values, D.pty.values, CRS_M, CRS)
    D["band"] = pd.cut(D.dist_m, [-1, QUARTER, HALF, MILE], labels=["0-1/4", "1/4-1/2", "1/2-1"]).astype(str)
    D["group"] = "reform"
    # law's upzoned lots: wi_lots.parquet treated flag, matched by location (same outline grouping and point)
    from scipy.spatial import cKDTree
    W = pd.read_parquet(WI_LOTS, columns=["city", "x5070", "y5070", "treated", "in_reform"])
    D["in_reform_area"] = False
    D["reform_flag_source"] = "beyond wi_lots coverage (set False)"
    for city in ("Milwaukee", "Madison"):
        w = W[W.city == city]
        ix = D.index[D.city_name == city]
        dd, ii = cKDTree(w[["x5070", "y5070"]].to_numpy()).query(D.loc[ix, ["x", "y"]].to_numpy())
        ok = dd <= 1.0
        D.loc[ix[ok], "in_reform_area"] = w.treated.to_numpy()[ii[ok]] == 1
        D.loc[ix[ok], "reform_flag_source"] = "wi_lots treated (matched by location)"
    D["homes_after_win"] = np.nan
    D["implausible"] = False
    D["win_before"] = f"{BEFORE[0]}-{BEFORE[1]}"
    D["eff"] = EFF
    D["source"] = np.where(D.city_name == "Milwaukee", "MPROP 2026 year built and units", "Madison tax parcels year built and units")
    D["stop_id"] = D.stop_id.astype("int64")
    D["public"] = D.public.astype(bool)
    cols = ["case", "city_name", "group", "stop_id", "dist_m", "band", "in_reform_area", "reform_flag_source", "acres",
            "land_value", "bldg_value", "year_built", "use", "public", "homes_existing", "homes_source", "homes_before_win",
            "win_before", "homes_after_win", "implausible", "source", "value_source", "eff", "x", "y"]
    return D[cols]


def statewide_check(cs: pd.DataFrame) -> None:
    bl = X.read_vector(BLOCKS, columns=["GEOID20", "HOUSING20", "INTPTLAT20", "INTPTLON20"], geometry=False)
    bx, by = X.transform(bl.INTPTLON20.astype(float).values, bl.INTPTLAT20.astype(float).values, 4269, CRS_M)
    bp = np.c_[bx, by]
    s = pd.read_csv(REFERENCE / "tod_stops.csv")
    s = s[s.flag_a_rapid == 1]
    sx, sy = X.transform(s.lon.values, s.lat.values, 4326, CRS_M)
    m = T.blocks_within(bp, np.c_[sx, sy], 0.5 * T.MILE_M)
    hu = bl.HOUSING20.astype(float).values
    muni = muni_of(bx[m], by[m], cs)
    by = pd.Series(hu[m]).groupby(muni).sum().sort_values(ascending=False)
    tot = by.sum()
    two = by.get(MILWAUKEE_CITY, 0) + by.get(MADISON_CITY, 0)
    print(f"\nStatewide homes within 1/2 mile of rail/rapid stops (2020 blocks, internal points): {tot:,.0f} "
          f"(earlier {STATEWIDE_HALF_MILE:,}); in Milwaukee + Madison cities {two:,.0f}; outside {tot - two:,.0f} "
          f"({(tot - two) / tot:.1%})")
    names = cs.set_index("GEOID").NAMELSAD
    print("  outside the two cities:", {names[k]: int(v) for k, v in by.drop([MILWAUKEE_CITY, MADISON_CITY], errors="ignore").items()})


def checks(D: pd.DataFrame) -> None:
    pd.set_option("display.width", 220)
    print("\nLots and homes by city and band:")
    g = D.groupby(["city_name", "band"]).agg(lots=("acres", "size"), acres=("acres", "sum"), homes_existing=("homes_existing", "sum"),
                                             homes_2020_24=("homes_before_win", "sum"), upzoned_share=("in_reform_area", "mean"),
                                             matched_wi_lots=("reform_flag_source", lambda s: s.str.startswith("wi_lots").mean()),
                                             census_homes_share=("homes_source", lambda s: np.nan))
    g["census_homes_share"] = D.assign(c=D.homes_existing.where(D.homes_source.str.startswith("2020"), 0)).groupby(["city_name", "band"]).c.sum() / g.homes_existing
    print(g.round(3).to_string())
    h = D[D.dist_m <= HALF]
    print(f"Homes within 1/2 mile in the lot table (existing before 2020 + built 2020-24): "
          f"{h.homes_existing.sum():,.0f} + {h.homes_before_win.sum():,.0f}")
    print("Values missing (land value NaN) share by city:", D.land_value.isna().groupby(D.city_name).mean().round(3).to_dict())
    print("Public share by city:", D.public.groupby(D.city_name).mean().round(3).to_dict())


def features(D: pd.DataFrame, eff: int, years_before: int) -> pd.DataFrame:
    """The lot features of run_tod_station_lotmodel.load_case, plus a few place traits."""
    lva = D.land_value / D.acres.where(D.acres > 0)
    f = pd.DataFrame({"log_acres": np.log(D.acres.clip(lower=0.01).fillna(0.1)),
                      "log_land_value_per_acre": np.log(lva.clip(lower=1000)),
                      "bldg_to_land": (D.bldg_value / D.land_value.where(D.land_value > 0)).clip(0, 50),
                      "building_age": (eff - D.year_built).clip(0, 200),
                      "log_homes_existing": np.log1p(D.homes_existing.clip(lower=0)),
                      "vacant": (D.bldg_value.fillna(0) <= 0).astype(float),
                      "public": D.public.astype(float),
                      "rate_before": D.homes_before_win / years_before,
                      "built_before": (D.homes_before_win > 0).astype(float)}, index=D.index)
    for c in ("sld_transit_freq", "sld_jobs_per_acre", "sld_share_no_car", "bg_job_growth_5y", "historic",
              "v_h13_median_building_age", "v_c01_median_rent", "v_h15_owner_share"):
        if c in D:
            f[c] = D[c].astype(float)
    return f


def compare_training(D: pd.DataFrame) -> None:
    import build_tod_station_lot_table as B
    cfgs = {**B.CASES, **{k: v for k, (_, v) in B.adapter_cases().items()}}
    rows, pool = {}, []
    for case in ("denver_2018", "chicago_2015", "stpaul_2011", "charlotte_2019", "portland_2020", "seattle_othello_2012", "la_toc_2017"):
        f = OUT / f"lots_{case}.parquet"
        if not f.exists():
            continue
        T_ = pd.read_parquet(f)
        T_ = T_[~T_.implausible.fillna(False)]
        c = cfgs[case]
        F = features(T_, int(c.get("eff", c["after"][0] - 1)), c["before"][1] - c["before"][0] + 1)
        rows[case] = F.median()
        rows[case]["mean_rate_before"] = F.rate_before.mean()
        rows[case]["built_before_share"] = F.built_before.mean()
        pool.append(F.sample(min(len(F), 50_000), random_state=1))
    for city, w in D.groupby("city_name"):
        F = features(w, EFF, BEFORE[1] - BEFORE[0] + 1)
        rows[f"WI {city}"] = F.median()
        rows[f"WI {city}"]["mean_rate_before"] = F.rate_before.mean()
        rows[f"WI {city}"]["built_before_share"] = F.built_before.mean()
    R = pd.DataFrame(rows).T
    print("\nFeature medians (rate_before: homes a year per lot; mean shown separately):")
    print(R.round(3).to_string())
    tr = R[~R.index.str.startswith("WI")]
    lo, hi = tr.min(), tr.max()
    P = pd.concat(pool)
    q1, q99 = P.quantile(0.01), P.quantile(0.99)
    print("\nFlags (Wisconsin median outside the training cities' range of medians; share of WI lots outside pooled 1st-99th pct):")
    for city, w in D.groupby("city_name"):
        F = features(w, EFF, BEFORE[1] - BEFORE[0] + 1)
        for c in R.columns:
            v = R.at[f"WI {city}", c]
            out_share = float(((F[c] < q1[c]) | (F[c] > q99[c])).mean()) if c in F and c in q1 else np.nan
            if (v < lo[c] or v > hi[c]) or (out_share == out_share and out_share > 0.05):
                print(f"  {city} {c}: median {v:.3f} vs training {lo[c]:.3f}..{hi[c]:.3f}; outside pooled 1-99%: {out_share:.1%}")


def main() -> None:
    D = build()
    print("enriching ...", flush=True)
    D = enrich(D)
    OUT.mkdir(parents=True, exist_ok=True)
    # acres_land: stacked condo-unit records share their parcel's land (scripts/fix_tod_station_acres.py)
    from fix_tod_station_acres import add_acres_land
    D = add_acres_land(D)
    D.to_parquet(OUT_FILE)
    print(f"wrote {OUT_FILE.relative_to(ROOT)}: {len(D):,} rows, {D.shape[1]} columns; block group found "
          f"{D.bg_geoid.notna().mean():.3f}; tract variables {sum(c.startswith('v_') for c in D.columns)}")
    checks(D)
    statewide_check(X.read_vector(COUSUB, dst=CRS_M).reset_index(drop=True))
    compare_training(D)


if __name__ == "__main__":
    main()

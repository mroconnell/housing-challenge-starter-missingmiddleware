"""Build the Wisconsin statewide foundation tables.

Run with:  uv run python scripts/build_foundation.py [--force-download] [--out NAME]

Outputs (data/processed/foundation/ by default; git-ignored):
  areas.parquet, inventory.parquet, state_conditions.parquet      contract tables
  bps_place_annual.parquet                                         BPS place rows 2015-2025 (WI)
  bps_muni_crosswalk.parquet / .csv, bps_unmatched.csv             BPS id -> municipality
  coverage_municipalities.csv / .md                                per-municipality coverage
  inventory_additivity.csv, checks.json, source_register.csv, run_manifest.json
  geo/areas_<level>.parquet (GeoParquet, NAD83 as published), geo/areas_display.parquet (simplified, WGS84)
  *_preview.csv                                                    first rows for quick inspection
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from missing_middleware import contracts
from missing_middleware.paths import ROOT, processed_dir, raw_dir

from . import crosswalk as xwmod
from . import geo, parsers, sources, tables

ACS_2024_1YR_STATE_1U_DETACHED = 1_855_771  # published ACS 2024 1-year B25024_002, Wisconsin (owner-supplied reference)
SPOT_MUNIS = {
    "Madison city": "5502548000",
    "Milwaukee city": "5507953000",
    "Green Bay city": "5500931000",
    "Appleton city (3 counties)": "5508702375",
    "Eau Claire city (2 counties)": "5503522300",
    "Neenah city": "5513955750",
    "Sun Prairie city": "5502578600",
    "Greenville village (BPS still uses the old town code)": "5508731525",
    "Fox Crossing village (2 counties)": "5513926982",
}


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return None


def _write(df: pd.DataFrame, out: Path, name: str, preview: int | None = 200, full_csv: bool = False):
    df.to_parquet(out / f"{name}.parquet", index=False)
    if full_csv:
        _csv(df).to_csv(out / f"{name}.csv", index=False)
    elif preview:
        _csv(df.head(preview)).to_csv(out / f"{name}_preview.csv", index=False)


def _csv(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in d.columns:
        if d[c].map(lambda x: isinstance(x, (list, np.ndarray))).any():
            d[c] = d[c].map(lambda x: ";".join(map(str, x)) if isinstance(x, (list, np.ndarray)) else x)
    return d


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for r in df.itertuples(index=False):
        cells = []
        for v in r:
            if v is None or (isinstance(v, float) and np.isnan(v)):
                cells.append("")
            elif isinstance(v, float):
                cells.append(f"{v:,.0f}" if abs(v) >= 100 or v == int(v) else f"{v:.2f}")
            else:
                cells.append(str(v).replace("|", "/"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def build(out_name: str = "foundation", force_download: bool = False, log=print) -> dict:
    log("1/7 acquiring sources (keyless)")
    sources.fetch_all(force=force_download, log=log)
    out = processed_dir(out_name)
    (out / "geo").mkdir(exist_ok=True)
    R = {sid: raw_dir(sid) for sid in sources.SOURCES}

    log("2/7 parsing ACS table-based summary files")
    acs = {t: parsers.read_acs_sf(R["census_acs5_2024_tbsf"] / f"acsdt5y2024-{t}.dat") for t in sources.ACS_TABLES}
    hu = acs["b25024"][["geoid", "level"]].assign(value=acs["b25024"]["B25024_E001"])
    pop = acs["b01003"][["geoid", "level"]].assign(value=acs["b01003"]["B01003_E001"])

    log("3/7 building areas from TIGER/Line 2024")
    areas, geoms = geo.build_areas(R["census_tiger_2024"], R["census_cbsa_cb_2024"], hu, pop, log=log)

    log("4/7 inventory and additivity")
    inv = tables.build_inventory(acs["b25024"])
    add = tables.check_additivity(inv)
    add.to_csv(out / "inventory_additivity.csv", index=False)
    inv = inv.merge(areas[["area_id", "context_group"]], on="area_id", how="left")

    log("5/7 BPS, PEP and state_conditions")
    bps_state = pd.concat([parsers.read_bps(R["census_bps_state"] / f"st{y}a.txt", "state") for y in sources.BPS_YEARS])
    bps_county = pd.concat([parsers.read_bps(R["census_bps_county"] / f"co{y}a.txt", "county") for y in sources.BPS_YEARS])
    bps_place = pd.concat([parsers.read_bps(R["census_bps_place"] / f"mw{y}a.txt", "place") for y in sources.BPS_YEARS], ignore_index=True)

    munis = areas[areas["level"] == "municipality"][["area_id", "geoid", "cousubfp", "parent_county_id", "muni_type", "name"]]
    munis = munis.rename(columns={"parent_county_id": "county_geoid"}).merge(
        inv[["area_id", "homes_1unit_detached"]], on="area_id", how="left")
    xw = xwmod.build_crosswalk(bps_place, munis)
    _write(xw, out, "bps_muni_crosswalk", full_csv=True)
    unmatched = xw[xw["match_type"] == "unmatched"]
    unmatched.to_csv(out / "bps_unmatched.csv", index=False)

    place_cols = ["year", "bps_id", "name", "county_fips", "fips_mcd", "fips_place", "months_reported", "pop",
                  "units_total", "1unit_units", "units_2_4", "5plus_units", "units_total_rep", "1unit_units_rep",
                  "2units_units", "3_4units_units", "1unit_bldgs", "2units_bldgs", "3_4units_bldgs", "5plus_bldgs"]
    bp = bps_place[place_cols].copy()
    bp["reporting_status"] = np.select([bp["months_reported"] >= 12, bp["months_reported"] > 0],
                                       ["reported_12_months", "partly_imputed"], "imputed")
    bp["status"] = "observed"
    bp["source_id"] = "census_bps_place"
    _write(bp, out, "bps_place_annual")

    # state_conditions
    sc = [tables.acs_conditions(acs["b25024"], acs["b25002"], acs["b25034"])]
    pep = parsers.read_pep_housing_units(R["census_pep_v2025_hu"] / "CO-EST2025-HU-55.xlsx")
    name_to_geoid = areas[areas["level"] == "county"].set_index("name")["area_id"].to_dict()
    pep_sc, pep_unmatched = tables.pep_conditions(pep, name_to_geoid)
    sc.append(pep_sc)
    sc.append(tables.bps_conditions(bps_state, pd.Series(["55"] * len(bps_state)), "census_bps_state",
                                    tables.units_reported_share(bps_state), "share of units from reported (not imputed) data"))
    sc.append(tables.bps_conditions(bps_county, "55" + bps_county["county_fips"], "census_bps_county",
                                    tables.units_reported_share(bps_county), "share of units from reported (not imputed) data"))
    # municipality BPS rows: one row per BPS jurisdiction at its primary piece
    prim = xw[xw["match_type"].isin(xwmod.MATCHED_TYPES) & (xw["is_primary_piece"] == True)]  # noqa: E712
    prim = prim.drop_duplicates(["bps_id", "fips_mcd", "bps_county_fips", "fips_place"])
    bpm = bps_place.merge(prim[["bps_id", "fips_mcd", "bps_county_fips", "fips_place", "area_id", "match_type", "n_pieces"]],
                          left_on=["bps_id", "fips_mcd", "county_fips", "fips_place"],
                          right_on=["bps_id", "fips_mcd", "bps_county_fips", "fips_place"], how="inner")
    note = np.where(bpm["n_pieces"] > 1,
                    "BPS value covers the whole municipality across " + bpm["n_pieces"].astype(str) + " counties; stored at the BPS county piece",
                    "")
    sc.append(tables.bps_conditions(bpm, bpm["area_id"], "census_bps_place", (bpm["months_reported"] / 12).clip(upper=1),
                                    "months reported / 12", pd.Series(note)))
    state_conditions = pd.concat(sc, ignore_index=True)
    # A BPS jurisdiction id can be reported under two place codes in one year (rare);
    # sum those so the key stays unique and record it.
    dup_mask = state_conditions.duplicated(["area_id", "year", "indicator"], keep=False)
    dup_keys = state_conditions[dup_mask][["area_id", "year"]].drop_duplicates()
    if dup_mask.any():
        agg = (state_conditions[dup_mask].groupby(["area_id", "year", "indicator"], as_index=False)
               .agg({"value": "sum", "moe": "first", "period_type": "first", "status": "first", "source_id": "first",
                     "source_vintage": "first", "reporting_coverage": "min", "coverage_basis": "first",
                     "geography_note": lambda s: "; ".join(sorted(set(filter(None, s))) | {"summed over 2+ BPS rows"})}))
        agg["status"] = "calculated"
        state_conditions = pd.concat([state_conditions[~dup_mask], agg], ignore_index=True)
    _write(state_conditions, out, "state_conditions")

    log("6/7 geometry and coverage")
    for level, g in geoms.items():
        g.to_parquet(out / "geo" / f"areas_{level}.parquet")
    disp = []
    for level, tol in (("state", 200), ("county", 100), ("municipality", 30), ("tract", 30), ("block_group", 15)):
        g = geoms[level].to_crs(geo.WI_CRS)
        g["geometry"] = g.geometry.simplify(tol, preserve_topology=True)
        disp.append(g.to_crs("EPSG:4326").assign(level=level))
    gpd.GeoDataFrame(pd.concat(disp, ignore_index=True), crs="EPSG:4326").to_parquet(out / "geo" / "areas_display.parquet")

    cov = coverage_table(areas, inv, xw, bps_place)
    cov.to_csv(out / "coverage_municipalities.csv", index=False)
    (out / "coverage_municipalities.md").write_text(
        "# Municipality coverage (statewide foundation)\n\n"
        "One row per county-subdivision piece (city, village or town in one county). "
        "Generated by scripts/build_foundation.py.\n\n" + _md_table(cov))

    log("7/7 checks")
    checks = run_checks(areas, inv, add, state_conditions, bps_state, bps_county, bps_place, xw, pep_sc, pep_unmatched, cov, R)
    _write(areas, out, "areas")
    _write(inv, out, "inventory")
    (out / "checks.json").write_text(json.dumps(checks, indent=2, default=str))
    reg = pd.DataFrame(sources.register_rows())
    reg.to_csv(out / "source_register.csv", index=False)
    manifest = {
        "run_id": out_name,
        "run_date": dt.datetime.now().isoformat(timespec="seconds"),
        "model_version": _git_commit(),
        "sources": reg[["source_id", "file", "sha256", "accessed"]].to_dict("records"),
        "boundary_vintage": geo.BOUNDARY_VINTAGE,
        "acs_vintage": tables.ACS_VINTAGE,
        "bps_years": [min(sources.BPS_YEARS), max(sources.BPS_YEARS)],
        "context_rule": geo.CONTEXT_RULE,
        "validation": checks.get("contract_validation"),
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    log(f"done: {out}")
    return checks


def coverage_table(areas, inv, xw, bps_place) -> pd.DataFrame:
    m = areas[areas["level"] == "municipality"].merge(
        inv[["area_id", "homes_1unit_detached", "homes_1unit_detached_moe", "total_housing_units", "cv_1unit_detached"]],
        on="area_id", how="left")
    cnames = areas[areas["level"] == "county"].set_index("area_id")["name"]
    m["county"] = m["parent_county_id"].map(cnames)
    own = xw[xw["match_type"].isin(xwmod.MATCHED_TYPES)]
    cty = xw[xw["match_type"] == "county_unincorporated"]
    years_by_key = bps_place.groupby(["bps_id", "fips_mcd", "county_fips", "fips_place"])
    yr = {k: g for k, g in years_by_key}

    def stats(area_id):
        rows = own[own["area_id"] == area_id]
        if rows.empty:
            return dict(bps_ids=None, bps_match_type=None, bps_years_present=0, bps_years_12mo=0,
                        bps_years_partial=0, bps_years_imputed=0, bps_units_2025=np.nan, bps_units_2015_2025=np.nan)
        gs = [yr[k] for k in zip(rows["bps_id"], rows["fips_mcd"], rows["bps_county_fips"], rows["fips_place"]) if k in yr]
        g = pd.concat(gs) if gs else bps_place.iloc[0:0]
        per_year = g.groupby("year").agg(m=("months_reported", "max"), u=("units_total", "sum"))
        return dict(
            bps_ids=";".join(sorted(rows["bps_id"].unique())),
            bps_match_type=";".join(sorted(rows["match_type"].unique())),
            bps_years_present=int(len(per_year)),
            bps_years_12mo=int((per_year["m"] >= 12).sum()),
            bps_years_partial=int(((per_year["m"] > 0) & (per_year["m"] < 12)).sum()),
            bps_years_imputed=int((per_year["m"] == 0).sum()),
            bps_units_2025=float(per_year["u"].get(2025, np.nan)),
            bps_units_2015_2025=float(per_year["u"].sum()),
        )

    st = pd.DataFrame([stats(a) for a in m["area_id"]])
    c = pd.concat([m.reset_index(drop=True), st], axis=1)
    c["county_issued_bps"] = c["area_id"].isin(cty["area_id"])
    flags = []
    for r in c.itertuples(index=False):
        f = []
        if r.muni_type == "not_defined":
            f.append("water_placeholder")
        if r.bps_years_present == 0 and r.muni_type != "not_defined":
            f.append("county_issued_bps" if r.county_issued_bps else "no_bps_row")
        if 0 < r.bps_years_present < 11:
            f.append("bps_years_missing")
        if r.bps_years_partial or r.bps_years_imputed:
            f.append("bps_imputed_years")
        if r.n_county_pieces and r.n_county_pieces > 1:
            f.append("multi_county")
        if isinstance(r.cv_1unit_detached, float) and r.cv_1unit_detached > 0.30:
            f.append("acs_cv_over_30pct")
        if r.homes_1unit_detached == 0:
            f.append("zero_detached_homes")
        flags.append(";".join(f))
    c["flags"] = flags
    c["inventory_status"] = np.where(c["homes_1unit_detached"].notna(), "observed", "missing")
    cols = ["area_id", "name", "county", "muni_type", "context_group", "n_county_pieces", "homes_1unit_detached",
            "homes_1unit_detached_moe", "total_housing_units", "inventory_status", "bps_ids", "bps_match_type",
            "bps_years_present", "bps_years_12mo", "bps_years_partial", "bps_years_imputed",
            "bps_units_2015_2025", "bps_units_2025", "flags"]
    return c[cols].sort_values("homes_1unit_detached", ascending=False).reset_index(drop=True)


def run_checks(areas, inv, add, sc, bps_state, bps_county, bps_place, xw, pep_sc, pep_unmatched, cov, R) -> dict:
    ch: dict = {}
    st = inv[inv["level"] == "state"].iloc[0]
    ch["state_1unit_detached_acs5"] = {
        "estimate": st["homes_1unit_detached"], "moe": st["homes_1unit_detached_moe"],
        "acs_2024_1yr_published": ACS_2024_1YR_STATE_1U_DETACHED,
        "diff_5yr_minus_1yr": st["homes_1unit_detached"] - ACS_2024_1YR_STATE_1U_DETACHED,
        "pct_diff": round(100 * (st["homes_1unit_detached"] / ACS_2024_1YR_STATE_1U_DETACHED - 1), 3),
        "state_1unit_attached": st["homes_1unit_attached"], "state_total_units": st["total_housing_units"],
    }
    ch["additivity"] = (
        add.assign(nonzero=add["diff"].fillna(0) != 0, missing=add["parent_value"].isna() | add["child_sum"].isna())
        .groupby(["check", "column"])
        .agg(parents=("parent_geoid", "size"), parents_with_diff=("nonzero", "sum"), missing=("missing", "sum"),
             total_abs_diff=("diff", lambda s: float(s.abs().sum())))
        .reset_index().to_dict("records")
    )
    ch["counts"] = areas["level"].value_counts().to_dict()
    ch["inventory_counts"] = inv["level"].value_counts().to_dict()
    ch["counties"] = int((areas["level"] == "county").sum())
    ch["municipality_unique_codes"] = int(areas.loc[(areas["level"] == "municipality") & (areas["muni_type"] != "not_defined"), "cousubfp"].nunique())
    ch["municipality_types"] = (areas[areas["level"] == "municipality"].drop_duplicates("cousubfp")["muni_type"].value_counts().to_dict())
    ch["context_groups"] = {
        lv: areas[areas["level"] == lv]["context_group"].value_counts(dropna=False).to_dict()
        for lv in ("county", "municipality", "tract", "block_group")
    }
    ch["context_homes_1unit_detached"] = (inv[inv["level"] == "municipality"].groupby("context_group")["homes_1unit_detached"].sum().to_dict())

    # BPS
    bc = {}
    for y in sorted(bps_state["year"].unique()):
        s = bps_state[bps_state["year"] == y].iloc[0]
        c = bps_county[bps_county["year"] == y]
        p = bps_place[bps_place["year"] == y]
        bc[int(y)] = {
            "state_file_units": float(s["units_total"]), "state_file_1unit": float(s["1unit_units"]),
            "county_sum_units": float(c["units_total"].sum()), "place_sum_units": float(p["units_total"].sum()),
            "state_units_reported_share": round(float(s["units_total_rep"] / s["units_total"]), 4),
            "places": int(len(p)), "places_12mo": int((p["months_reported"] >= 12).sum()),
            "places_0mo": int((p["months_reported"] == 0).sum()),
        }
    ch["bps_reconciliation"] = bc
    ps = bps_place.groupby(["year", "county_fips"])["units_total"].sum()
    cs = bps_county.set_index(["year", "county_fips"])["units_total"]
    gap = (ps - cs).dropna()
    ch["bps_place_minus_county_by_county"] = [
        {"year": int(y), "county_fips": c, "place_sum_minus_county_file": float(v)} for (y, c), v in gap[gap != 0].items()
    ]
    ch["crosswalk_all_years"] = xwmod.match_summary(xw, bps_place)
    ch["crosswalk_2025"] = xwmod.match_summary(xw, bps_place, 2025)
    um = xw[xw["match_type"] == "unmatched"]
    ch["crosswalk_unmatched"] = um[["bps_id", "bps_name", "bps_county_fips", "fips_mcd", "first_year", "last_year", "units_total_all_years"]].to_dict("records")
    ch["municipalities_without_own_bps_row"] = int((cov["bps_years_present"] == 0).sum() - (cov["muni_type"] == "not_defined").sum())
    ch["municipalities_county_issued"] = int(cov["flags"].str.contains("county_issued_bps").sum())

    # PEP
    p = pep_sc
    ch["pep"] = {
        "unmatched_names": pep_unmatched,
        "years": sorted(p["year"].unique().tolist()),
        "state_minus_county_sum": {int(y): float(g.loc[g["area_id"] == "55", "value"].sum() - g.loc[g["area_id"] != "55", "value"].sum())
                                   for y, g in p.groupby("year")},
        "state_2025": float(p[(p["area_id"] == "55") & (p["year"] == 2025)]["value"].iloc[0]),
    }

    # Spot checks
    spots = []
    for label, geoid in geo_spot_ids().items():
        aid = f"muni:{geoid}"
        a = areas[areas["area_id"] == aid]
        i = inv[inv["area_id"] == aid]
        x = xw[xw["area_id"] == aid]
        b25 = sc[(sc["area_id"] == aid) & (sc["year"] == 2025) & (sc["indicator"] == "permitted_units_total")]
        spots.append({
            "label": label, "area_id": aid, "found": not a.empty,
            "name": a["name"].iloc[0] if not a.empty else None,
            "context_group": a["context_group"].iloc[0] if not a.empty else None,
            "homes_1unit_detached": float(i["homes_1unit_detached"].iloc[0]) if not i.empty else None,
            "moe": float(i["homes_1unit_detached_moe"].iloc[0]) if not i.empty else None,
            "total_units": float(i["total_housing_units"].iloc[0]) if not i.empty else None,
            "bps_ids": sorted(x["bps_id"].unique().tolist()), "match_type": sorted(x["match_type"].unique().tolist()),
            "alloc_share": float(x["alloc_share"].iloc[0]) if not x.empty and pd.notna(x["alloc_share"].iloc[0]) else None,
            "bps_2025_units_at_this_piece": float(b25["value"].iloc[0]) if not b25.empty else None,
        })
    ch["spot_checks"] = spots
    # Madison place (sumlevel 160) vs county subdivision
    mp = parsers.read_acs_sf(R["census_acs5_2024_tbsf"] / "acsdt5y2024-b25024.dat", sumlevels=("160",))
    mp = mp[mp["geoid"] == "5548000"]
    ch["madison_place_vs_cousub"] = {
        "place_5548000_1unit_detached": float(mp["B25024_E002"].iloc[0]) if not mp.empty else None,
        "place_5548000_moe": float(mp["B25024_M002"].iloc[0]) if not mp.empty else None,
        "cousub_5502548000_1unit_detached": float(inv.loc[inv["area_id"] == "muni:5502548000", "homes_1unit_detached"].iloc[0]),
    }
    # BPS Madison
    mb = bps_place[bps_place["bps_id"] == "516500"].set_index("year")
    ch["madison_bps_516500"] = {int(y): {"units": float(r["units_total"]), "1unit": float(r["1unit_units"]),
                                         "months": float(r["months_reported"])} for y, r in mb.iterrows()}

    # contract validation
    val = {}
    for name, df in (("areas", areas), ("inventory", inv), ("state_conditions", sc)):
        val[name] = contracts.validate(df, contracts.ALL[name])
    bad_ctx = set(areas["context_group"].dropna()) - contracts.CONTEXT_GROUP
    if bad_ctx:
        val["areas"].append(f"context_group values not allowed {sorted(bad_ctx)}")
    ch["contract_validation"] = val
    return ch


def geo_spot_ids() -> dict:
    return dict(SPOT_MUNIS)

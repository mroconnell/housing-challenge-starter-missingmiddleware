"""Build Madison permits_observed and permits_by_area_year from cached raw files.

    uv run python scripts/build_madison_permits.py            # build from data/raw caches
    uv run python scripts/build_madison_permits.py --fetch    # (re)download permits 2010..this year,
                                                              # parcels/address points, TIGER WI, then build

Raw inputs (git-ignored):
    data/raw/madison_permits/construction_summary_<year>.csv + manifest.json
    data/raw/madison_parcels/tax_parcels.geojson, address_points.geojson + manifest.json
    data/raw/tiger_wi/tl_2024_55_tract.zip, tl_2024_55_bg.zip + manifest.json
Outputs:
    data/processed/permits/permits_observed.parquet         (contract, record level; local only)
    data/processed/permits/permits_records_full.parquet     (all deduped permits + diagnostics; local only)
    data/processed/permits/permits_by_area_year.parquet     (contract; tract + city)
    data/processed/permits/source_vs_clean_examples.csv     (owner fields redacted)
    data/processed/permits/audit_sample.csv                 (with addresses; local only)
    data/processed/permits/build_report.json
    reference/madison_adu_permits_by_year.csv               (aggregate, non-personal)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import contracts  # noqa: E402
from missing_middleware.paths import REFERENCE, processed_dir, raw_dir  # noqa: E402
from missing_middleware.permits import geo, madison, second_homes  # noqa: E402
from missing_middleware.permits.match import AddressIndex  # noqa: E402
from missing_middleware.permits.pipeline import (  # noqa: E402
    build_permits_observed, by_area_year, to_contract,
)
from missing_middleware.permits.report import (  # noqa: E402
    CITY_ADU_TABLE, audit_sample, reconcile_city, reference_by_year, source_vs_clean,
)

ADU_CATS = ["adu_detached", "adu_attached", "adu_conversion", "adu_legalization"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download raw inputs before building")
    ap.add_argument("--refresh", action="store_true", help="with --fetch, re-download cached years")
    ap.add_argument("--first-year", type=int, default=2010)
    args = ap.parse_args(argv)

    a = madison.MadisonAdapter()
    praw, graw, traw = raw_dir(madison.SOURCE_ID), raw_dir(madison.PARCEL_SOURCE_ID), raw_dir("tiger_wi")
    if args.fetch:
        madison.fetch_permits(praw, list(range(args.first_year, date.today().year + 1)), refresh=args.refresh)
        if args.refresh or not (graw / "address_points.geojson").exists():
            madison.fetch_gis(graw)
        geo.fetch_tiger(traw, a.state_fips)

    raw = a.load_permits(praw)
    print(f"raw detail rows: {len(raw):,} ({raw['permit_id'].nunique():,} permit numbers)")
    parcels = madison.parcel_table(madison.load_parcels(graw))
    ref = madison.address_reference(parcels, madison.load_address_points(graw))
    index = AddressIndex(ref)
    tracts = geo.load_tiger(traw, a.state_fips, "tract")
    bgs = geo.load_tiger(traw, a.state_fips, "block_group")

    def areas_fn(xy: pd.DataFrame) -> pd.DataFrame:
        import geopandas as gpd

        pts = gpd.GeoDataFrame(index=xy.index, geometry=gpd.points_from_xy(xy["x"], xy["y"]), crs=4326)
        return geo.attach_areas(pts, tracts, bgs)

    full = build_permits_observed(raw, index, parcels, parcels[["parcel_id", "x", "y"]], areas_fn,
                                  new_residential_types=a.new_residential_types, host_uses=a.host_uses,
                                  dwell0_conversions=a.dwell0_conversions,
                                  exclude_parcel_rule=a.parcel_rule_false_positives)
    # headline outcome (AQ-032): second homes on single-family lots; unit_category is unchanged
    full = second_homes.assign(full, a.second_home_judgments)
    # review S7: flag the templated 2025-26 builder programme (Gate 3 uses 2026 as a sensitivity only)
    full["templated_programme"] = madison.templated_programme(full)
    obs = to_contract(full, a.source_id, a.jurisdiction_id)
    s_in = full.loc[full["in_scope"]]
    for col in ("second_home_component", "second_home_units", "second_home_upper_units", "templated_programme"):
        obs[col] = s_in[col].values
    problems = contracts.validate(obs, contracts.PERMITS_OBSERVED)
    city_area = f"muni:{a.jurisdiction_id}"
    agg = by_area_year(obs, city_area)
    problems += contracts.validate(agg, contracts.PERMITS_BY_AREA_YEAR)

    out = processed_dir("permits")
    obs.to_parquet(out / "permits_observed.parquet", index=False)
    keep_full = [c for c in full.columns if c not in ("geo_x", "geo_y")]
    full[keep_full].to_parquet(out / "permits_records_full.parquet", index=False)
    agg.to_parquet(out / "permits_by_area_year.parquet", index=False)

    ref_tbl = reference_by_year(full)
    data_end_year = int(full["year"].max())
    # 2026 is a partial year (data to the download date) and is dominated by one templated programme:
    # provisional, and for Gate 3 a sensitivity only (never part of the Madison floor)
    ref_tbl["value_status"] = ref_tbl["year"].map(lambda y: "provisional" if y == data_end_year else "final")
    ref_tbl["gate3_use"] = ref_tbl["year"].map(lambda y: "sensitivity_only" if y == data_end_year else "eligible")
    REFERENCE.mkdir(exist_ok=True)
    ref_tbl.to_csv(REFERENCE / "madison_adu_permits_by_year.csv", index=False)
    traced = ["BLDNRC-2024-10200", "BLDNRC-2026-21855"]  # the doc's traced and unmatched examples
    source_vs_clean(praw, full, obs, extra_ids=traced).to_csv(out / "source_vs_clean_examples.csv", index=False)
    judged = second_home_judgment_table(full, madison.load_parcels(graw), a.second_home_judgments)
    judged.to_csv(out / "second_home_judgments.csv", index=False)
    audit = audit_sample(full, out / "audit_judgments.csv")
    extra = full[full["permit_id"].isin(judged["permit_id"])]
    extra = extra[[c for c in audit.columns if c in extra.columns]].assign(
        audit_group="second_home_judged", issue_date=extra["issue_date"].dt.date)
    extra = extra.merge(judged[["permit_id", "judgment", "evidence"]].rename(
        columns={"evidence": "judgment_note"}), on="permit_id", how="left")
    audit = pd.concat([audit[~audit["permit_id"].isin(judged["permit_id"])], extra], ignore_index=True)
    audit.to_csv(out / "audit_sample.csv", index=False)
    sh_years = second_homes.by_year(full, range(2014, int(full["year"].max()) + 1))
    lb = pd.DataFrame([madison.programme_lower_bounds(full, y) for y in sh_years["year"]])
    sh_years["lower_bound_two_unit_as_one"] = lb["two_unit_as_one"].values
    sh_years["lower_bound_pairs_as_one_project"] = lb["pairs_as_one_project"].values
    sh_years["lower_bound_both"] = lb["both"].values
    sh_years["value_status"] = sh_years["year"].map(lambda y: "provisional" if y == int(full["year"].max())
                                                    else "final")
    sh_years.to_csv(out / "second_homes_by_year.csv", index=False)
    recon = reconcile_city(full)
    recon.to_csv(out / "reconcile_city_table.csv", index=False)

    counted = full[full["counted"]]
    report = {
        "built": date.today().isoformat(),
        "raw_rows": int(len(raw)),
        "permits_deduped": int(len(full)),
        "duplicate_rows_collapsed": int(len(raw) - len(full)),
        "permits_in_scope": int(full["in_scope"].sum()),
        "permits_counted": int(len(counted)),
        "contract_problems": problems,
        "match_by_method_quality_in_scope": (
            full[full["in_scope"]].groupby(["match_method", "match_quality"]).size().astype(int)
            .rename("n").reset_index().to_dict("records")),
        "category_by_year_units": {
            str(k): {str(c): int(v) for c, v in d.items()} for k, d in
            counted.pivot_table(index="year", columns="unit_category", values="units_added", aggfunc="sum",
                                fill_value=0).astype(int).to_dict("index").items()},
        "reconciliation": recon.to_dict("records"),
        "second_home_sf_lot_by_year": sh_years.to_dict("records"),
        "second_home_judgments": judged[["permit_id", "judgment", "counts", "units"]].to_dict("records"),
        "templated_programme": {
            "permits_by_year": full[full["templated_programme"]].groupby("year").size().astype(int).to_dict(),
            "headline_units_by_year": full[full["templated_programme"]].groupby("year")["second_home_units"]
            .sum().astype(int).to_dict(),
            "rule": "BLDNRC, issue year >= 2025, (998 sq ft and $80k-$90k) or (2,994 sq ft and $200k)"},
    }
    (out / "build_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps({k: report[k] for k in ("raw_rows", "permits_deduped", "permits_in_scope",
                                             "permits_counted", "contract_problems")}, indent=2))
    return 1 if problems else 0


def second_home_judgment_table(full: pd.DataFrame, parcels_gdf, judgments: dict) -> pd.DataFrame:
    """Local audit table (has parcel ids): each judged record, its host parcel and the evidence.

    Host = matched parcel, else the parcel containing the record's (geocoded) point.
    """
    import geopandas as gpd

    j = full[full["permit_id"].isin(list(judgments))].copy()
    pts = gpd.GeoDataFrame(j[["permit_id"]], geometry=gpd.points_from_xy(j["x"], j["y"]), crs=4326)
    cols = ["Parcel", "YearBuilt", "MaxConstructionYear", "MoreThanOneBuild", "TotalDwellingUnits", "PropertyUse"]
    hit = gpd.sjoin(pts, parcels_gdf[cols + ["geometry"]], predicate="within", how="left")
    hit = hit[~hit.index.duplicated()]
    by_id = parcels_gdf.drop_duplicates("Parcel").set_index("Parcel")[cols[1:]]
    rows = []
    for idx, r in j.iterrows():
        host = r["parcel_id"] if pd.notna(r["parcel_id"]) else hit.at[idx, "Parcel"]
        how = "matched_parcel" if pd.notna(r["parcel_id"]) else ("point_in_parcel" if pd.notna(host) else "none")
        a = by_id.loc[host] if pd.notna(host) and host in by_id.index else pd.Series(dtype=object)
        jd = judgments[r["permit_id"]]
        if jd.get("host_note"):
            how += "; " + jd["host_note"]
        rows.append({"permit_id": r["permit_id"], "issue_date": r["issue_date"].date(), "units_raw": r["units_added"],
                     "description": r["description"], "match_method": r["match_method"], "host_parcel": host,
                     "host_from": how, "host_year_built": a.get("YearBuilt"),
                     "host_max_construction_year": a.get("MaxConstructionYear"),
                     "host_more_than_one_build": a.get("MoreThanOneBuild"),
                     "host_dwelling_units": a.get("TotalDwellingUnits"), "host_use": a.get("PropertyUse"),
                     "judgment": jd["judgment"], "counts": jd["counts"], "units": jd["units"],
                     "component": jd["component"], "evidence": jd["evidence"]})
    return pd.DataFrame(rows).sort_values("permit_id")


if __name__ == "__main__":
    raise SystemExit(main())

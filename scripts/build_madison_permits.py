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
from missing_middleware.permits import geo, madison  # noqa: E402
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
    obs = to_contract(full, a.source_id, a.jurisdiction_id)
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
    REFERENCE.mkdir(exist_ok=True)
    ref_tbl.to_csv(REFERENCE / "madison_adu_permits_by_year.csv", index=False)
    traced = ["BLDNRC-2024-10200", "BLDNRC-2026-21855"]  # the doc's traced and unmatched examples
    source_vs_clean(praw, full, obs, extra_ids=traced).to_csv(out / "source_vs_clean_examples.csv", index=False)
    audit_sample(full, out / "audit_judgments.csv").to_csv(out / "audit_sample.csv", index=False)
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
    }
    (out / "build_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps({k: report[k] for k in ("raw_rows", "permits_deduped", "permits_in_scope",
                                             "permits_counted", "contract_problems")}, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

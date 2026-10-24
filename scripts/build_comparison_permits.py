"""Build comparison-city permits (Pleasant Prairie restrictive pilot, Sun Prairie 2016-2025 check).

    uv run python scripts/build_comparison_permits.py                    # both cities, from raw caches
    uv run python scripts/build_comparison_permits.py --fetch            # download permits + V12 parcels, then build
    uv run python scripts/build_comparison_permits.py --city sun_prairie

Raw inputs (git-ignored):
    data/raw/pleasant_prairie_permits/permits_issued_<year>.rtf.gz + manifest.json   (owner fields inside: local only)
    data/raw/sun_prairie_permits/permits_submitted_<year>.json.gz + manifest.json    (no owner fields requested)
    data/raw/wi_v12_parcels_kenosha_pp/, data/raw/wi_v12_parcels_dane_sp/ v12_parcels.geojson + manifest.json
    data/raw/tiger_wi/ (TIGER 2024 tracts and block groups, from the Madison build)
Outputs per city (data/processed/permits_<city>/, local):
    permits_observed.parquet, permits_records_full.parquet, permits_by_area_year.parquet,
    bps_reconciliation.csv, match_rates.csv, audit_sample.csv, source_vs_clean_examples.csv, build_report.json
Committed aggregate: reference/<city>_adu_equivalent_by_year.csv
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
from missing_middleware.paths import PROCESSED, REFERENCE, processed_dir, raw_dir  # noqa: E402
from missing_middleware.permits import comparison as cmp  # noqa: E402
from missing_middleware.permits import geo, pleasant_prairie, sun_prairie  # noqa: E402
from missing_middleware.permits.match import AddressIndex  # noqa: E402
from missing_middleware.permits.pipeline import build_permits_observed, by_area_year, to_contract  # noqa: E402

CITIES = {
    "pleasant_prairie": (pleasant_prairie, pleasant_prairie.PleasantPrairieAdapter),
    "sun_prairie": (sun_prairie, sun_prairie.SunPrairieAdapter),
}
ADU_TEXT = ["adu_detached", "adu_attached", "adu_conversion", "adu_legalization"]
REF_SERIES = ["adu_text", "adu_equivalent:second_dwelling", "adu_equivalent:duplex_conversion",
              "teardown_rebuild", "manufactured_home_replacement"]


def build_city(name: str, fetch: bool, refresh: bool, log=print) -> dict:
    mod, cls = CITIES[name]
    a = cls()
    praw, graw, traw = raw_dir(a.source_id), raw_dir(a.parcel_source_id), raw_dir("tiger_wi")
    this_year = date.today().year
    if fetch:
        mod.fetch_permits(praw, list(range(a.first_year, this_year + 1)), refresh=refresh, log=log)
    raw = a.load_permits(praw)
    log(f"{name}: raw rows {len(raw):,} ({raw['permit_id'].nunique():,} permit numbers)")
    if fetch or not (graw / "v12_parcels.geojson").exists():
        cmp.fetch_v12_parcels(graw, a.parcel_source_id, a.v12_placename, a.v12_coname,
                              extra_parcel_ids=sorted(raw["parcel_key"].dropna().unique()), log=log)
    if not (traw / "tl_2024_55_tract.zip").exists():
        geo.fetch_tiger(traw, a.state_fips, log=log)
    parcels = cmp.load_v12_parcel_table(graw)
    index = AddressIndex(cmp.address_reference(parcels))
    tracts = geo.load_tiger(traw, a.state_fips, "tract")
    bgs = geo.load_tiger(traw, a.state_fips, "block_group")

    def areas_fn(xy: pd.DataFrame) -> pd.DataFrame:
        import geopandas as gpd

        pts = gpd.GeoDataFrame(index=xy.index, geometry=gpd.points_from_xy(xy["x"], xy["y"]), crs=4326)
        return geo.attach_areas(pts, tracts, bgs)

    full = build_permits_observed(
        raw, index, parcels, parcels[["parcel_id", "x", "y"]], areas_fn, raze_types=a.raze_types,
        match_fn=cmp.parcel_match_fn(set(parcels["parcel_id"]), index=index),
        parcel_rule_fn=cmp.prior_dwelling_rule(a))
    full = cmp.recount(full)
    full["series"] = cmp.series_label(full)
    full["new_dwelling_type"] = a.is_new_dwelling(full) & ~(full.get("withdrawn", False) == True)  # noqa: E712
    full["manufactured"] = a.is_manufactured(full)
    obs = to_contract(full, a.source_id, a.jurisdiction_id)
    obs["stage"] = a.stage
    obs["parcel_stateid"] = obs["parcel_id"].map(parcels.set_index("parcel_id")["stateid"])
    obs["series"] = full.loc[full["in_scope"], "series"].values
    obs["restrictive_period"] = _restrictive(a, obs["year"])
    problems = contracts.validate(obs, contracts.PERMITS_OBSERVED)
    agg = by_area_year(obs, f"muni:{a.jurisdiction_id}")
    problems += contracts.validate(agg, contracts.PERMITS_BY_AREA_YEAR)

    out = processed_dir(f"permits_{name}")
    obs.to_parquet(out / "permits_observed.parquet", index=False)
    keep = [c for c in full.columns if c not in ("geo_x", "geo_y")]
    full[keep].to_parquet(out / "permits_records_full.parquet", index=False)
    agg.to_parquet(out / "permits_by_area_year.parquet", index=False)

    ref = reference_by_year(full, a)
    REFERENCE.mkdir(exist_ok=True)
    ref.to_csv(REFERENCE / f"{name}_adu_equivalent_by_year.csv", index=False)
    recon = bps_reconciliation(full, a)
    recon.to_csv(out / "bps_reconciliation.csv", index=False)
    rates = match_rates(full)
    rates.to_csv(out / "match_rates.csv", index=False)
    audit = audit_sample(full, out / "audit_judgments.csv")
    audit.to_csv(out / "audit_sample.csv", index=False)

    counted = full[full["counted"]]
    report = {
        "city": name, "built": date.today().isoformat(), "stage": a.stage,
        "raw_rows": int(len(raw)), "permits_deduped": int(len(full)),
        "permits_in_scope": int(full["in_scope"].sum()), "permits_counted": int(len(counted)),
        "contract_problems": problems,
        "series_by_year_units": {str(k): {str(c): int(v) for c, v in d.items()} for k, d in counted.pivot_table(
            index="year", columns="series", values="units_added", aggfunc="sum", fill_value=0).astype(int)
            .to_dict("index").items()},
        "parcel_rule_reasons_new_dwellings": full[full["new_dwelling_type"] & (full["units_added"].fillna(0) > 0)]
        ["parcel_rule_reason"].value_counts().astype(int).to_dict(),
        "match_rates": rates.to_dict("records"),
        "bps_reconciliation": recon.to_dict("records"),
    }
    (out / "build_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    log(json.dumps({k: report[k] for k in ("raw_rows", "permits_deduped", "permits_in_scope", "permits_counted",
                                           "contract_problems")}))
    return report


def _restrictive(a, years: pd.Series) -> pd.Series:
    last = getattr(a, "restrictive_last_year", None)
    return years.le(last) if last else pd.Series(True, index=years.index)


def reference_by_year(full: pd.DataFrame, a) -> pd.DataFrame:
    """Aggregate, non-personal: year x series permits/units, plus new 1-2 family totals."""
    c = full[full["counted"]]
    rows = []
    for y in range(max(int(full["year"].min()), a.first_year), int(full["year"].max()) + 1):
        cy = c[c["year"] == y]
        restrictive = bool(_restrictive(a, pd.Series([y])).iloc[0])
        for s in REF_SERIES:
            x = cy[cy["series"] == s]
            rows.append({"year": y, "series": s, "permits": len(x), "units": int(x["units_added"].sum()),
                         "method": {"adu_text": "text_rule"}.get(s, "parcel_rule" if s.startswith("adu_eq")
                                                                 else "parcel_rule_excluded"),
                         "stage": a.stage, "restrictive_period": restrictive})
        nd = cy[cy["new_dwelling_type"] & ~cy["manufactured"]]
        for k, label in ((1, "new_one_family_dwellings"), (2, "new_two_family_dwellings")):
            x = nd[nd["units_added"] == k]
            rows.append({"year": y, "series": label, "permits": len(x), "units": int(x["units_added"].sum()),
                         "method": "structured_field" if a.stage == "issued" else "type_and_text",
                         "stage": a.stage, "restrictive_period": restrictive})
        x = cy[cy["manufactured"] & cy["new_dwelling_type"]]
        rows.append({"year": y, "series": "new_manufactured_homes", "permits": len(x),
                     "units": int(x["units_added"].sum()), "method": "structured_field", "stage": a.stage,
                     "restrictive_period": restrictive})
    out = pd.DataFrame(rows)
    out.insert(0, "jurisdiction_id", a.jurisdiction_id)
    return out


def bps_reconciliation(full: pd.DataFrame, a) -> pd.DataFrame:
    b = pd.read_parquet(PROCESSED / "foundation" / "bps_place_annual.parquet")
    b = b[b["bps_id"] == a.bps_id].set_index("year")
    c = full[full["counted"] & full["new_dwelling_type"] & ~full["manufactured"]]
    rows = []
    for y in range(max(int(full["year"].min()), a.first_year), int(full["year"].max()) + 1):
        cy = c[c["year"] == y]
        one = int((cy["units_added"] == 1).sum())
        two = int((cy["units_added"] == 2).sum())
        r = {"year": y, "permits_new_1family": one, "permits_new_2family_bldgs": two,
             "units_1family_plus_2family": one + 2 * two,
             "bps_1unit_units": None, "bps_2unit_bldgs": None, "bps_1unit_plus_2unit_units": None,
             "bps_months_reported": None, "diff_1unit": None, "ratio_1unit": None, "ratio_1_2unit": None}
        if y in b.index:
            br = b.loc[y]
            r.update({"bps_1unit_units": int(br["1unit_units"]), "bps_2unit_bldgs": int(br["2units_bldgs"]),
                      "bps_months_reported": int(br["months_reported"]),
                      "bps_1unit_plus_2unit_units": int(br["1unit_units"]) + int(br["2units_units"]),
                      "diff_1unit": one - int(br["1unit_units"]),
                      "ratio_1unit": round(one / br["1unit_units"], 3) if br["1unit_units"] else None,
                      "ratio_1_2unit": round((one + 2 * two) / (br["1unit_units"] + br["2units_units"]), 3)
                      if (br["1unit_units"] + br["2units_units"]) else None})
        rows.append(r)
    return pd.DataFrame(rows)


def match_rates(full: pd.DataFrame) -> pd.DataFrame:
    groups = {
        "all_permits": full,
        "in_scope_unit_adding": full[full["in_scope"]],
        "new_dwellings": full[full["new_dwelling_type"] & (full["units_added"].fillna(0) > 0)],
        "adu_equivalent": full[full["unit_category"].eq("adu_equivalent")],
    }
    rows = []
    for g, d in groups.items():
        n = len(d)
        for (mm, mq), k in d.groupby(["match_method", "match_quality"]).size().items():
            rows.append({"group": g, "match_method": mm, "match_quality": mq, "records": int(k),
                         "share": round(k / n, 4) if n else None,
                         "tract_placed_share": round(float(d.loc[(d["match_method"] == mm)
                                                                  & (d["match_quality"] == mq), "tract_geoid"]
                                                           .notna().mean()), 4)})
    return pd.DataFrame(rows)


AUDIT_COLS = ["audit_group", "permit_id", "year", "issue_date", "permit_type", "address_raw", "parcel_key",
              "units_added", "units_basis", "description", "unit_category", "series", "classification_method",
              "match_method", "match_quality", "match_rule", "parcel_id", "parcel_property_class",
              "parcel_rule_reason", "prior_evidence", "prior_evidence_permit", "prior_evidence_date",
              "earlier_units", "tract_geoid", "counted"]


def audit_sample(full: pd.DataFrame, judgments: Path | None = None, seed: int = 20261024) -> pd.DataFrame:
    """Every ADU-equivalent and text-ADU hit, plus samples of teardowns, near misses and unmatched."""
    def pick(d, n):
        return d.sample(min(n, len(d)), random_state=seed) if len(d) > n else d

    eq = full[full["unit_category"].eq("adu_equivalent")].assign(audit_group="adu_equivalent")
    tx = full[full["unit_category"].isin(ADU_TEXT)].assign(audit_group="adu_text")
    td = pick(full[full["series"].eq("teardown_rebuild")], 8).assign(audit_group="teardown_rebuild")
    nm = pick(full[full["new_dwelling_type"] & full["parcel_rule_reason"].isin(
        ["possible_reissue_of_earlier_dwelling_permit", "multi_dwelling_site", "manufactured_home_replacement",
         "host_not_residential"])], 8).assign(audit_group="near_miss_parcel_rule")
    un = pick(full[full["in_scope"] & full["match_method"].eq("unmatched")], 6).assign(audit_group="unmatched")
    out = pd.concat([eq, tx, td, nm, un])
    out = out[[c for c in AUDIT_COLS if c in out.columns]].copy()
    out["issue_date"] = pd.to_datetime(out["issue_date"]).dt.date
    if judgments is not None and judgments.exists():
        out = out.merge(pd.read_csv(judgments, dtype=str), on="permit_id", how="left")
    return out.sort_values(["audit_group", "year", "permit_id"]).reset_index(drop=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=[*CITIES, "all"], default="all")
    ap.add_argument("--fetch", action="store_true", help="download raw inputs before building")
    ap.add_argument("--refresh", action="store_true", help="with --fetch, re-download cached years")
    args = ap.parse_args(argv)
    bad = 0
    for name in (CITIES if args.city == "all" else [args.city]):
        rep = build_city(name, args.fetch, args.refresh)
        bad += bool(rep["contract_problems"])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the California comparison inputs and the step 0 reconciliation (data quality only).

Run:  uv run python scripts/build_ca_comparison_data.py [--force-download] [--skip-fetch]
Needs: data/raw/census_bps_ca (scripts/build_ca_bps.py) and the ACS B25024 national file
       (scripts/build_foundation.py). Wisconsin BPS state rows are read from the national
       BPS state files already in data/raw/census_bps_ca.
Outputs: data/processed/comparison_ca/*.parquet|csv, data/processed/comparison_ca/step0/*.csv,
         reference/ca_jurisdiction_crosswalk.csv, reference/ca_holdout_jurisdictions.csv,
         reference/ca_wi_statewide_bps_per_1000.csv, data/processed/comparison_ca/ca_comparison_manifest.json
See docs/gate2/CA_COMPARISON_DATA.md. This script does NOT compute the pre-registered study
(no permissive/restrictive groups, no before/after comparisons, no ramp or spillover).
"""
from __future__ import annotations

import datetime as dt
import json
import sys

import pandas as pd

from missing_middleware.comparison import ca_crosswalk as X
from missing_middleware.comparison import ca_inputs as I
from missing_middleware.comparison import ca_sources as S
from missing_middleware.comparison import ca_step0 as Z
from missing_middleware.foundation.sources import sha256
from missing_middleware.paths import REFERENCE, processed_dir, raw_dir


def main(argv: list[str]) -> None:
    out = processed_dir("comparison_ca")
    s0 = out / "step0"
    s0.mkdir(exist_ok=True)
    written: dict[str, str] = {}

    def save(df: pd.DataFrame, path, csv: bool = True):
        path = out / path if not str(path).startswith("/") else path
        if str(path).endswith(".parquet"):
            df.to_parquet(path, index=False)
            if csv:
                df.to_csv(str(path).replace(".parquet", ".csv"), index=False)
        else:
            df.to_csv(path, index=False)
        written[str(path)] = sha256(path)
        print(f"  wrote {path} ({len(df)} rows)")

    if "--skip-fetch" not in argv:
        S.fetch_all(force="--force-download" in argv)
        S.fetch_api_queries(force="--force-download" in argv)

    # --- 1. HCD APR Table A2 -------------------------------------------------
    print("HCD APR Table A2")
    rows = I.classify_permit_rows(I.read_apr_a2(raw_dir("hcd_apr_a2") / "tablea2.csv"))
    assert (rows["bp_units"].fillna(0) == rows["bp_income_sum"]).all(), "NO_BUILDING_PERMITS != sum of BP_* columns"
    agg = I.aggregate_apr(rows)
    save(agg, "hcd_apr_a2_juris_year_unitcat.parquet")
    dedup = I.apr_by_issue_year(rows)
    save(dedup, "hcd_apr_a2_issue_year_dedup.parquet")
    dq = Z.apr_date_quality(rows)
    save(dq, s0 / "apr_permit_date_quality.csv")
    api = Z.api_crosscheck(rows, S.read_api_records(raw_dir("hcd_apr_a2") / "api" / "table_a2_year_unitcat.json"))
    save(api, s0 / "apr_csv_vs_api_crosscheck.csv")
    del rows

    # --- 2. Building an ADU compilation ---------------------------------------
    comp, side = I.read_compilation(raw_dir("buildinganadu_ca_2012_2019") / "california-adu-permits-2012-2019.csv")
    save(comp, "adu_compilation_2012_2019.parquet")

    # --- 3. ACS denominators --------------------------------------------------
    places = I.read_tiger_places(raw_dir("census_tiger_2024_ca_place") / "tl_2024_06_place.zip")
    acs = I.read_acs_b25024_ca(S.shared_acs_b25024())
    den = I.ca_denominators(acs, places)
    save(den, "ca_denominators_acs2024.parquet")
    place_county = acs[acs.sumlevel == "155"][["placefp", "county_fips"]].drop_duplicates("placefp")

    # --- 4. Crosswalk -----------------------------------------------------------
    pep20 = pd.read_csv(raw_dir("census_pep_hu_states") / "HU-EST2020_06.csv", dtype=str, encoding="latin-1")
    counties = X.county_lookup(pep20)
    bps_place = pd.read_parquet(out / "bps_ca_place_annual.parquet")
    bps_county = pd.read_parquet(out / "bps_ca_county_annual.parquet")
    names = pd.concat([agg[["juris_name", "cnty_name"]].drop_duplicates(),
                       comp[["juris_name"]].drop_duplicates()]).drop_duplicates("juris_name")
    xw = X.build_crosswalk(names, places, place_county, counties, bps_place)
    xw["in_hcd_apr"] = xw["juris_name"].isin(set(agg["juris_name"]))
    xw["in_compilation"] = xw["juris_name"].isin(set(comp["juris_name"]))
    save(xw, "ca_jurisdiction_crosswalk.parquet")
    save(xw, REFERENCE / "ca_jurisdiction_crosswalk.csv")

    # --- 4b. Pre-registered holdout (identifiers only; drawn before any group rates) ---
    universe = X.holdout_universe(places, place_county, counties)
    hold = X.draw_holdout(universe)
    hold = hold.merge(xw.groupby("census_geoid")["juris_name"].agg(lambda s: ";".join(sorted(s))).rename("hcd_juris_name"),
                      on="census_geoid", how="left")
    hold_path = REFERENCE / "ca_holdout_jurisdictions.csv"
    hold["drawn_on"] = dt.date.today().isoformat()
    if hold_path.exists():
        # Never silently redraw: a rebuild must reproduce the saved draw exactly.
        prev = pd.read_csv(hold_path, dtype={"census_geoid": str, "county_fips": str})
        same = set(prev.loc[prev["holdout"], "census_geoid"]) == set(hold.loc[hold["holdout"], "census_geoid"])
        if not same:
            raise SystemExit(f"holdout draw differs from saved {hold_path}; investigate before overwriting")
        hold["drawn_on"] = prev["drawn_on"].iloc[0]
    save(hold[["census_geoid", "juris_type", "name", "hcd_juris_name", "county_fips", "holdout", "seed",
               "universe_size", "drawn_on", "method"]], REFERENCE / "ca_holdout_jurisdictions.csv")

    # --- 5. Step 0 --------------------------------------------------------------
    print("Step 0")
    filers = Z.filing_status(agg, xw, S.read_api_records(raw_dir("hcd_apr_a2") / "api" / "table_a_juris_years.json"),
                             S.read_api_records(raw_dir("hcd_apr_a2") / "api" / "table_d_juris_years.json"))
    save(filers, "hcd_apr_filing_status.parquet")
    panel = Z.juris_year_panel(agg, xw, bps_place, den, filers, dedup)
    save(panel, "step0_juris_year_panel.parquet")
    for name, df in Z.all_tables(panel, bps_county, counties, comp, agg, xw, filers, bps_place).items():
        save(df, s0 / f"{name}.csv")

    # --- 6. Statewide BPS per 1,000 homes, WI and CA ---------------------------
    sw = Z.statewide_bps_per_1000(
        ca_state=pd.read_parquet(out / "bps_ca_state_annual.parquet"),
        wi_state_dir=raw_dir("census_bps_ca"),
        pep={"06": (raw_dir("census_pep_hu_states") / "HU-EST2020_06.csv", raw_dir("census_pep_hu_states") / "CO-EST2025-HU-06.xlsx"),
             "55": (raw_dir("census_pep_hu_states") / "HU-EST2020_55.csv", raw_dir("census_pep_hu_states") / "CO-EST2025-HU-55.xlsx")})
    save(sw, REFERENCE / "ca_wi_statewide_bps_per_1000.csv")

    manifest = {"built": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "command": "uv run python scripts/build_ca_comparison_data.py",
                "sources": S.register_rows(), "outputs_sha256": written,
                "compilation_side_block": side,
                "apr_dropped_fields": list(I.DROPPED_APR_FIELDS)}
    (out / "ca_comparison_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(f"  wrote {out / 'ca_comparison_manifest.json'}")


if __name__ == "__main__":
    main(sys.argv[1:])

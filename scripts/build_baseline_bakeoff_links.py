"""Baseline bake-off Part 2 link table and coverage check (before any Part 2 score; plan: "Linking").

    uv run python scripts/build_baseline_bakeoff_links.py

Inputs: data/raw/baseline_bakeoff/bps_place/mw{1990..2014}a.txt, the foundation build (bps_place_annual.parquet,
areas.parquet, inventory.parquet), data/raw/census_bps_state/st{y}a.txt.
Outputs: reference/baseline_bakeoff_links.csv (every BPS identity 1990-2025 and how it links),
reference/baseline_bakeoff_link_coverage.csv (per year: linked units / state units, 95% check),
data/interim/baseline_bakeoff/bps_place_1990_2025.parquet, xw.parquet, alloc.parquet (local, for Part 2).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware import baseline_bakeoff_links as L  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE, ROOT  # noqa: E402

F = PROCESSED / "foundation"
OUT = ROOT / "data" / "interim" / "baseline_bakeoff"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    areas = pd.read_parquet(F / "areas.parquet")
    inv = pd.read_parquet(F / "inventory.parquet")
    munis = areas[areas["level"] == "municipality"][["area_id", "geoid", "cousubfp", "parent_county_id", "muni_type", "name"]]
    munis = munis.rename(columns={"parent_county_id": "county_geoid"}).merge(
        inv[["area_id", "homes_1unit_detached"]], on="area_id", how="left")
    fb = pd.read_parquet(F / "bps_place_annual.parquet")
    old = RAW / "baseline_bakeoff" / "bps_place"
    b = L.read_all_places(old, old, fb)
    xw, alloc = L.link(b, munis)
    st = {}
    for y in range(1990, 2026):
        d = parsers.read_bps(RAW / "census_bps_state" / f"st{y}a.txt", "state")
        st[y] = float(d[[f"{g}_units" for g in L.SIZE_GROUPS]].sum(axis=1).sum())
    cov = L.coverage(b, xw, alloc, pd.Series(st))
    b.to_parquet(OUT / "bps_place_1990_2025.parquet", index=False)
    xw.to_parquet(OUT / "xw.parquet", index=False)
    alloc.to_parquet(OUT / "alloc.parquet", index=False)
    cols = ["bps_id", "bps_name", "bps_county_fips", "fips_mcd", "fips_place", "first_year", "last_year",
            "units_total_all_years", "match_type", "area_id", "muni_name", "alloc_share", "n_pieces", "match_note"]
    xw.reindex(columns=cols).sort_values(["bps_county_fips", "bps_name", "first_year"]).to_csv(
        REFERENCE / "baseline_bakeoff_links.csv", index=False)
    cov.round(4).to_csv(REFERENCE / "baseline_bakeoff_link_coverage.csv", index=False)
    print(cov.round(4).to_string(index=False))
    print(xw.drop_duplicates(["bps_id", "bps_county_fips", "fips_mcd", "fips_place"])["match_type"].value_counts())


if __name__ == "__main__":
    main()

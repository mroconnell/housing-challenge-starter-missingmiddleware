# Parking scenario: how to rebuild it

Written 2026-10-27 by the parking conductor. These steps rebuild the parking scenario and the shared all-housing baseline from public sources. Each step fetches its own data automatically, and records URL, date, bytes and SHA-256 in a `_downloads.json` file beside the raw data, which stays out of git.

## Quick check (no downloads)

The committed reference tables are enough to rebuild the tool's parking bundle and run the tests:

```bash
uv run python scripts/build_parking_bundle.py
uv run --all-extras python -m unittest discover -s tests
bash scripts/test_ui.sh
```

The bundle's run id is a hash of its inputs, so the same tables give the same run id.

## Full rebuild from raw data (in this order)

1. **Foundation** (Census permits for Wisconsin places, ACS tables including B01003, B25002 and B25064, boundaries):
   `uv run python scripts/build_foundation.py`
2. **Milwaukee property file** (for the apartment adjustment; owner fields are never read):
   `uv run python scripts/build_wi_baseline.py --fetch`
3. **All-housing baseline** (also fetches the 1990–2014 Census state files):
   `uv run python scripts/build_housing_baseline.py --fetch`
   This step stops if the Milwaukee property file is missing. The `--published` flag builds the "Census as published" sensitivity case instead.
4. **Parking reform classification** (Parking Reform Network data, pinned commit):
   `uv run python scripts/build_parking_taxonomy.py --fetch`
5. **Repeal comparison** (fetches Census permit place files for all four regions, 2012–2025):
   `uv run python scripts/run_parking_comparison.py --fetch`
   It reads the ordinance checks in `reference/parking_repeal_checks.csv`. These are team-coded from each place's code, with source URLs, and are not re-fetched.
6. **Wisconsin scenario:** `uv run python scripts/run_parking_model.py`
7. **Tool bundle:** `uv run python scripts/build_parking_bundle.py`
8. **Run the tool:** `bash scripts/run_tool.sh`, then open `#/parking/` in the browser.

Step 6 also uses TOD's `reference/tod_near_stop_homes_by_muni.csv`, but only to split additions near transit stops for the combined view. That file is rebuilt by `scripts/fetch_tod_transit.py` and `scripts/build_tod_stops.py`.

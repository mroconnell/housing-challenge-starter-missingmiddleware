# All-housing baseline (shared by the parking and TOD scenarios)

Written 2026-10-26 by the parking conductor. Status: version 1, for use by the parking and TOD scenarios and for owner review at Gate 1. Two open decisions are listed at the end.

## What it answers

How many housing units Wisconsin would permit each year in 2027–2031 under current law, by municipality and by building size, with a range. Every reform scenario's addition is measured against it.

**Answer (version 1).** Under current law, Wisconsin would permit about 118,800 housing units over 2027–2031, which is about 23,800 units per year. The range is 62,200 to 169,800 units over the five years. For comparison, Wisconsin permitted 117,405 units over 2021–2025 in the published Census state files.

| Building size | 2027–2031 low | 2027–2031 central | 2027–2031 high | 2021–2025 permitted (published) |
| --- | ---: | ---: | ---: | ---: |
| 1 unit | 30,926 | 63,075 | 81,622 | 62,600 |
| 2 units | 3,023 | 7,786 | 14,850 | 7,768 |
| 3–4 units | 195 | 642 | 768 | 651 |
| 5+ units | 28,100 | 47,318 | 72,574 | 46,386 |
| All | 62,244 | 118,822 | 169,814 | 117,405 |

All figures are housing units authorized by building permits (at permit issuance), the same milestone as the ADU scenario. Source: `reference/housing_baseline_statewide_by_year.csv`.

## Source and unit

- **Census Building Permits Survey (BPS)**, annual place files for Wisconsin, 2015–2025, parsed by the foundation build (`data/processed/foundation/bps_place_annual.parquet`; see [census_bps.md](../data-sources/census_bps.md)). Public domain.
- **BPS state annual files, 1990–2025**, used only for the long-run range (fetched automatically by `scripts/build_housing_baseline.py` from `https://www2.census.gov/econ/bps/State/st{year}a.txt`, with URL, date, bytes and SHA-256 in `data/raw/census_bps_state/_downloads.json`).
- **Unit:** housing units in new buildings authorized by permit, by building size: 1 unit, 2 units, 3–4 units, 5+ units. The BPS "estimate" columns are used (reported values plus Census imputation for months a place did not report), so the places add up to the published state total.
- **Not counted by BPS:** units added inside existing buildings (most conversions and many ADUs), and demolitions. Permits are not completions.

## How it is built

1. **Allocate each BPS row to a municipality piece** (the 1,925 municipality pieces the ADU tool uses, `muni:<geoid>`):
   - a place that matches one municipality piece gets all of its units (observed);
   - a municipality split across counties is split by each piece's share of one-unit detached homes (assumed; the foundation crosswalk);
   - a county row covering towns without their own BPS row is split each year among those towns by one-unit detached homes (assumed; the foundation allocation table).
2. **Reconcile to the state.** An explicit `unallocated` row holds the difference between the published state total and the sum of the municipality pieces, for each year and building size. It is small: between −55 and 0 units per year in 1-unit buildings (the place rows slightly exceed the state file in some years) and 0 in the other sizes. `reference/housing_baseline_reconciliation.csv` shows the check for every year and size.
3. **Missing reports are missing, not zero.** BPS shows Milwaukee city with 0 units in 3–4 and 5+ unit buildings in 2020, 2023 and 2025, despite documented apartment construction (foundation quality finding 1, [FOUNDATION.md](../gate2/FOUNDATION.md)). Those cells are null here. They are skipped when averaging and when scoring the projection tests. Milwaukee's 1-unit and 2-unit counts are kept. The published state total, which contains Milwaukee's zeros, is kept as published.
4. **Choose the projection by a held-out-year test.** Each candidate predicts each municipality's average annual units by building size over the next up to five years, using only data up to an origin year (origins 2019, 2020, 2021 and 2022, scored on 2020–2025). The candidates were a flat average of the last 1, 2, 3, 4 or 5 years, and the same 3- or 5-year level scaled by the state's straight-line trend (fitted over 5 years or over all years). The score is the municipality-level error per unit permitted, over all building sizes. **The flat average of the last three years (2023–2025) predicted best.** Its error was 0.544 units of error per unit permitted, against 0.545 to 0.598 for the other multi-year candidates and 0.625 for the last year alone. The trend candidates did worse because past trends did not persist. Source: `reference/housing_baseline_window_choice.csv` and `reference/housing_baseline_holdout.csv`.
5. **Projection.** Each municipality and building size is held flat at its 2023–2025 average for 2026 (a bridge year, shown but not in five-year totals) and 2027–2031.
6. **Range from Wisconsin's own history.** For every year from 1992 to 2020, the 3-year state average was compared with what Wisconsin actually permitted in the next five years (29 five-year periods per building size). The low and high cases use the 10th and 90th percentile of those outcomes, by building size: 0.49 and 1.29 times the central for 1-unit buildings, 0.39 and 1.91 for 2 units, 0.30 and 1.20 for 3–4 units, and 0.59 and 1.53 for 5+ units. The worst five-year period on record was 2007–2011, when Wisconsin permitted 0.40 times as many units as the 3-year average before it. Source: `reference/housing_baseline_band.csv`, `reference/housing_baseline_long_run_ratios.csv`.
   - The low and high cases apply the same multiplier to every municipality, so building sizes and places move together; the statewide low and high are their sums and are not independent.
   - A narrower range from the recent held-out test alone is kept as a sensitivity (`reference/housing_baseline_band_recent.csv`). In all four recent tests the flat average under-predicted every building size except 3–4 units, because permits rose over 2015–2025, so that range runs almost only upward (1.00 to 1.46 times central for 5+ units).

## Where the baseline sits

Multifamily permits are concentrated. Ten municipalities hold 25,521 of the 47,318 units projected in 5+ unit buildings over 2027–2031 (54%). Madison alone is projected at 13,182 units in 5+ unit buildings over five years. The other large ones are Eau Claire (2,302), DeForest (1,632), Fitchburg (1,603), Glendale (1,415), Middleton (1,248), West Allis (1,108) and Green Bay (1,075). Source: `reference/housing_baseline_by_area.csv`.

## Files

| File | What it holds |
| --- | --- |
| `reference/housing_baseline_history.csv` | Municipality piece × year, 2015–2025: units by building size, all units, how each value was allocated |
| `reference/housing_baseline_by_area.csv` | Municipality piece × building size: name, county, context, ACS housing units, method, annual and five-year low/central/high, flag for no data in the window |
| `reference/housing_baseline_by_county.csv` | County × building size: the same, summed |
| `reference/housing_baseline_statewide_by_year.csv` | State × year × building size (and all): observed 2015–2025, projected 2026–2031 |
| `reference/housing_baseline_reconciliation.csv` | Year × building size: published state, allocated, unallocated, check |
| `reference/housing_baseline_holdout.csv`, `_window_choice.csv` | The held-out test and its summary |
| `reference/housing_baseline_band.csv`, `_band_recent.csv`, `_long_run_ratios.csv` | The range and its evidence |
| `reference/housing_baseline_milwaukee_check.csv` | Milwaukee's BPS units against the city's property file (see open issue 1) |

Columns use `area_id` (`muni:<10-digit county-subdivision GEOID>`, or `unallocated`), `structure_type` (`1unit`, `2units`, `3_4units`, `5plus`) and `year`. Rebuild with `uv run python scripts/build_housing_baseline.py` after the foundation build. Tests: `tests/test_housing_baseline.py`.

**For the TOD scenario:** station-area baselines can be taken as a share of a municipality's row here; the allocation rule within a municipality is TOD's to choose and test.

## Limitations

- **Milwaukee's multifamily permits are badly under-reported in BPS, not only in the three flagged years** (open issue 1).
- **Flat, not cyclical.** The central assumes 2023–2025 conditions continue. The range covers a downturn like 2007–2011 only at its very bottom.
- **Assumed splits.** Units in county rows (towns without their own BPS row) and in municipalities that cross county lines are split by one-unit detached homes. That is an assumption, and it matters most for apartments in towns.
- **24 municipality pieces have no BPS row in 2023–2025** and are projected at 0, flagged `no_data_in_window`.
- **Conversions and ADUs inside existing buildings are not in BPS**, so this is a baseline of new buildings.

## Open issues for the owner

1. **Milwaukee city's apartments.** Milwaukee's city property file (MPROP, year built) records 13,999 units in new 5+ unit buildings built in 2015–2024. BPS records 3,332 units in 5+ unit buildings permitted in Milwaukee over the same years, with 2020 and 2023 not reported. In 2022–2024, MPROP shows 3,178 such units built, and BPS shows 228 permitted in 2022 and 2024 (2023 not reported). The baseline projects Milwaukee at 152 units in 5+ unit buildings per year, from its single reported year in 2023–2025, which is very likely far too low. Year built lags permits by about one to two years and is not the same measure. **Recommendation:** replace Milwaukee's 3–4 and 5+ unit series with an estimate from MPROP year built, shifted one year earlier to approximate the permit year, and add the difference above the published state total as a labelled adjustment row. Keep BPS-as-published as a sensitivity. This matters a lot for parking and TOD, since Milwaukee is a likely pilot for both.
2. **Range.** **Recommendation:** use the long-run 10th–90th percentile range (it includes a recession), with the recent-decade range and the worst period on record (2007–2011) shown as sensitivities.

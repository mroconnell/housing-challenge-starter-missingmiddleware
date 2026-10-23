# Gate 2: Wisconsin Statewide Foundation

Prepared 2026-10-23 by the inventory and geography agent. Status: **built and checked; awaiting owner review.**

This package builds the statewide tables every later stage joins to:

- `areas`: Wisconsin, its 72 counties, 1,925 county-subdivision pieces (1,850 cities, villages and towns), 1,542 tracts and 4,692 block groups.
- `inventory`: one-unit detached homes, the ADU denominator, at every one of those levels.
- `state_conditions`: housing stock, occupancy, mix, age and permits.
- A crosswalk from Census Building Permits Survey (BPS) jurisdictions to municipalities.
- A per-municipality coverage table.

Everything comes from keyless Census bulk files, so a clean checkout rebuilds it without an API key.

## Bottom line

- **Statewide one-unit detached homes (ACS 2020–2024 5-year): 1,839,569 ± 6,502.** The published ACS 2024 1-year figure is 1,855,771. The 5-year figure is 16,202 lower (−0.87%), as expected: it averages 2020–2024, while the 1-year figure describes 2024 alone. Gate 3 uses the 5-year figure, because only the 5-year release reaches municipalities, tracts and block groups.
- **The estimates add up exactly.** Block groups sum to tracts, tracts to counties, municipalities to counties, and counties to the state. The difference is 0 for every parent and every column checked: detached, attached and total units.
- **BPS reconciles.** In 2025, Wisconsin authorized 25,569 units in the published state file (13,405 of them in one-unit buildings), and the 72 county rows sum to exactly 25,569. This holds for every year from 2015 to 2025. The place-level rows sum to 25,624 in 2025, 55 more. That excess comes from two counties (see quality findings).
- **Crosswalk: in 2025, 95.2% of BPS jurisdictions (1,097 of 1,152) match a municipality, and 100% match either a municipality or a county "unincorporated area" row. Nothing is unmatched in 2025.** Over 2015–2025, 3 of 1,339 jurisdiction identities are unmatched (Brokaw and Silver Lake, both dissolved or merged), carrying 7 units in total.
- **The biggest coverage gap: 724 towns, holding 410,783 one-unit detached homes (22% of the state), have no BPS row of their own.** Their permits are reported only inside a county "Part Unincorporated Area" row. Permit baselines for those towns can be observed only at that county-wide aggregate.

## Reproduce

```bash
uv run python scripts/build_foundation.py                  # downloads missing sources (≈270 MB), then builds (≈30 s)
uv run python scripts/build_foundation.py --force-download # re-download and re-checksum everything
bash scripts/test.sh                                       # offline tests (tests/test_foundation.py)
```

Code is in `missing_middleware/foundation/`:

| Module | What it does |
| --- | --- |
| `sources.py` | Source register and downloader |
| `parsers.py` | Parsers for the ACS summary file, BPS text files and a stdlib xlsx reader |
| `geo.py` | Areas, parent links and the context rule |
| `tables.py` | Inventory, `state_conditions`, MOE formulas and the additivity check |
| `crosswalk.py` | BPS-to-municipality crosswalk |
| `build.py` | Orchestration, coverage table and checks |

Raw files go to `data/raw/<source_id>/`, each with a `_downloads.json` recording the URL, size, SHA-256 and access date. Outputs go to `data/processed/foundation/`. Both locations are git-ignored.

## Sources

All of these are U.S. Census Bureau products, accessed 2026-10-23 by keyless HTTPS. License: U.S. Government work, public domain (17 U.S.C. §105), subject to the Census Bureau's terms of service. Full per-file checksums are in `data/processed/foundation/source_register.csv` and `data/raw/*/_downloads.json`.

| source_id | What | Vintage | URL | Files, bytes, SHA-256 (first 16) |
| --- | --- | --- | --- | --- |
| census_acs5_2024_tbsf | ACS table-based summary file, detailed tables B25024, B25002, B25034, B01003 (national pipe-delimited `.dat`; Wisconsin rows kept) | ACS 2020–2024 5-year | https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/ | b25024 47,866,463 `26ff26c645d1abc5`; b25002 23,400,695 `eb98debfe8e8533e`; b25034 50,103,592 `806d6cb18e8e6c08`; b01003 18,313,708 `38d1a992bb058d18` |
| census_tiger_2024 | TIGER/Line state, county, county subdivision, place, tract and block group | TIGER/Line 2024 (boundaries as of 2024-01-01; 2020 tracts and BGs) | https://www2.census.gov/geo/tiger/TIGER2024/ | us_state 9,954,307 `ad00cbe66c717709`; us_county 83,913,260 `04e668d3502757c8`; 55_cousub 8,576,335 `49c925158b488a0f`; 55_place 3,475,028 `062202ffa5ed57ea`; 55_tract 7,642,880 `313c378d7fa173bf`; 55_bg 13,843,348 `3832c7b938ae357e` |
| census_cbsa_cb_2024 | Cartographic CBSA file, used only for metro vs micro (LSAD) | 2024 (July 2023 OMB delineations) | https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_cbsa_20m.zip | 351,825 `8896deb773d07f33` |
| census_pep_v2025_hu | County housing-unit estimates (CO-EST2025-HU-55.xlsx) | PEP Vintage 2025, July 1 2020–2025 | https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx | 17,071 `4df5cedda85fef5d` |
| census_bps_state | BPS annual state files st2015a–st2025a | Annual, 2025 final | https://www2.census.gov/econ/bps/State/ | 11 files; st2025a 10,744 `eab29258ada83898` |
| census_bps_county | BPS annual county files co2015a–co2025a | Annual, 2025 final | https://www2.census.gov/econ/bps/County/ | 11 files; co2025a 375,314 `5d523b1ff172c886` |
| census_bps_place | BPS annual place files, Midwest region, mw2015a–mw2025a | Annual, 2025 final | https://www2.census.gov/econ/bps/Place/Midwest%20Region/ | 11 files; mw2025a 1,198,782 `e4d21352c78155af` |

**What works without a key.** The ACS API (`api.census.gov/data/2024/acs/acs5?...`) still returns HTTP 302 to `missing_key.html` (rechecked 2026-10-23), so the build uses the table-based summary files. These carry every summary level, including block groups (summary level 150) and county subdivisions (060), with MOEs. They contain no geography names, so names come from TIGER. BPS and PEP are flat files. PEP is xlsx only, and is read with a small stdlib reader because `openpyxl` is not a dependency.

**Why TIGER 2024 and not 2026.** ACS 2020–2024 is tabulated on January 1, 2024 boundaries. Wisconsin county subdivisions change every year through annexations and incorporations: for example, the Town of Madison was dissolved in 2022, and Greenville, Lisbon and Rib Mountain became villages with new codes. TIGER 2024 therefore joins to ACS with no unmatched GEOIDs: 1,925 of 1,925 county subdivisions, 1,542 of 1,542 tracts and 4,692 of 4,692 block groups. TIGER 2026 and the V12 2026 parcels will need a documented crosswalk when they are joined later.

## Outputs (`data/processed/foundation/`)

| File | Rows | Contents |
| --- | --- | --- |
| `areas.parquet` | 8,232 | `area_id`, `geoid`, `level`, `name`, `parent_ids` (list), `parent_county_id`, `parent_municipality_id`, `parent_municipality_share`, `parent_tract_id`, `land_area_sqm`, `water_area_sqm`, `muni_type` (city/village/town/not_defined), `cousubfp`, `n_county_pieces`, `metro_county`, `context_group`, `context_rule`, `population` (ACS B01003, labeled), `housing_units_acs`, `hu_density_per_sqmi`, `boundary_source_id`, `boundary_vintage` |
| `inventory.parquet` | 8,232 | `homes_1unit_detached` and `_moe` (B25024_002), `homes_1unit_attached` and `_moe`, `total_housing_units` and `_moe`, `cv_1unit_detached`, `parcel_proxy_count`/`parcel_to_acs_ratio` (null until parcels are added), `method_note`, `missing_reason`, `status`, `source_id`, `source_vintage`, `context_group` |
| `state_conditions.parquet` | 89,748 | Long form, keyed on (`area_id`, `year`, `indicator`), plus `reporting_coverage`, `coverage_basis` and `geography_note`. Indicators are listed below the table. |
| `bps_place_annual.parquet` | 12,649 | Every Wisconsin BPS place row for 2015–2025, with buildings and units by size, reported-only units, `months_reported` and `reporting_status` (reported_12_months / partly_imputed / imputed) |
| `bps_muni_crosswalk.parquet` / `.csv` | 2,139 | One row per BPS identity and municipality piece: `match_type`, `wi_muni_id`, `area_id`, `is_primary_piece`, `alloc_share`, `match_note`, first and last year |
| `bps_unmatched.csv` | 3 | Unmatched BPS identities |
| `coverage_municipalities.csv` / `.md` | 1,925 | Coverage per municipality piece (see below) |
| `inventory_additivity.csv` | — | Every parent's child sum versus its published value |
| `checks.json`, `run_manifest.json`, `source_register.csv` | — | Check results, run metadata with the git commit and checksums, and the source register |
| `geo/areas_<level>.parquet` | — | Full-resolution GeoParquet, NAD83 (EPSG:4269) as published |
| `geo/areas_display.parquet` | 8,232 | Simplified copy for maps, WGS84. Tolerance in EPSG:3071: 15 m for block groups, 30 m for tracts and municipalities, 100 m for counties |
| `*_preview.csv` | 200 | First rows of each Parquet table, for a quick look |

The `state_conditions` indicators, by level and source:

| Indicators | Source | Levels and years | `status` |
| --- | --- | --- | --- |
| `housing_units` | PEP | State and county, 2020–2025 | observed |
| `total_housing_units_acs`, `units_1_detached`, `units_1_attached`, `mobile_home` | ACS B25024 | State, county and municipality; ACS 5-year ending 2024 | observed |
| `units_2_4`, `units_5_plus` | ACS B25024 | Same | calculated (MOE by root-sum-of-squares) |
| `occupied_units`, `vacant_units` | ACS B25002 | Same | observed |
| `vacancy_rate` | ACS B25002 | Same | calculated (Census proportion MOE) |
| `built_2020_or_later` … `built_1939_or_earlier` | ACS B25034 | Same | observed |
| `permitted_units_total`, `permitted_units_1unit`, `permitted_units_2_4`, `permitted_units_5plus` | BPS | State, county and municipality, 2015–2025 | observed |

### Identifiers

| Level | `area_id` | Example |
| --- | --- | --- |
| state | `55` | |
| county | 5-digit GEOID | `55025` (Dane) |
| municipality | `muni:` + 10-digit county-subdivision GEOID (= `wi_muni_id`) | `muni:5502548000` (Madison city) |
| tract | 11-digit GEOID | `55025000100` |
| block group | 12-digit GEOID | `550250001001` |

A city or village that crosses county lines has one piece per county, and the pieces share `cousubfp`. Appleton, for example, is `5508702375` (Outagamie), `5501502375` (Calumet) and `5513902375` (Winnebago). `n_county_pieces` says how many pieces there are. 121 pieces belong to multi-county municipalities. Madison's place GEOID `5548000` and its county subdivision `5502548000` cover the same area: both report 53,292 one-unit detached homes.

**Parents.** Every municipality, tract and block group has a parent county. Tracts and block groups do not nest in municipalities, so `parent_municipality_id` is the piece covering most of their land, and `parent_municipality_share` gives that share.

| Level | Wholly inside one municipality (share ≥ 0.99) | Largest municipality covers < 50% |
| --- | --- | --- |
| Block groups | 52% | 270 |
| Tracts | 38% | 328 |

Twelve water-only tracts and block groups have no parent municipality.

### Context group rule

Housing-unit density = ACS 2020–2024 housing units (B25024_001) per square mile of TIGER land area. The rule is applied in order:

1. **urban**: a municipality with at least 20,000 housing units (whole municipality, all county pieces) and at least 750 per square mile.
2. **suburban**: any other municipality in a metropolitan county (OMB 2023 metro CBSA) with at least 425 housing units per square mile. 425 is the Census 2020 urban-area housing-density threshold.
3. **small_community**: any other city or village.
4. **rural**: any other town.

Tracts and block groups take the group of their majority municipality. Counties take the group holding most of their housing units. The 12 "County subdivisions not defined" water pieces have no group.

| Group | Municipality pieces | One-unit detached homes | Counties |
| --- | --- | --- | --- |
| urban | 20 (15 municipalities) | 384,218 | 10 |
| suburban | 151 | 358,730 | 6 |
| small_community | 502 | 386,551 | 13 |
| rural | 1,240 | 710,070 | 43 |

The 15 urban municipalities are Milwaukee, Madison, Green Bay, Kenosha, Racine, Appleton, Eau Claire, Waukesha, West Allis, Oshkosh, Janesville, La Crosse, Wauwatosa, Sheboygan and Fond du Lac. The rule has known edge cases:

- Wauwatosa and West Allis are dense inner suburbs of Milwaukee and count as urban.
- Wausau (18,718 units) misses the urban threshold and counts as suburban.
- Franklin (420 units per square mile) and Manitowoc (micropolitan county) count as small_community.

A first draft used 1,000 per square mile for urban, which left Eau Claire and Janesville suburban. I lowered it to 750. **The owner should confirm or change the rule.** It is one set of constants in `geo.py`.

## Check results

| Check | Result |
| --- | --- |
| Statewide one-unit detached homes, ACS 5-year vs the published 1-year | 1,839,569 ± 6,502 vs 1,855,771: −16,202 (−0.87%). Explained by the period difference, not an error. State total units 2,778,572 ± 1,533; one-unit attached 120,679 ± 2,636 |
| Block groups → tracts, tracts → counties, municipalities → counties, counties → state | Exact (0 difference) for 1,542 tracts, 72 counties and the state, on detached, attached and total units |
| BPS 2025: state file vs sum of counties | 25,569 vs 25,569 (also equal in every year 2015–2025) |
| BPS 2025: state file vs sum of place rows | 25,569 vs 25,624 (+55: Barron +7, Taylor +48); small gaps in earlier years in Clark (019) and Lafayette (065), at most 9 units |
| BPS reporting, 2025 | 91.4% of state units come from reported data, not Census imputation; 1,014 of 1,152 places reported 12 months and 113 reported 0 |
| PEP: state vs sum of counties | 0 difference in every year 2020–2025; 2025 state = 2,840,960 |
| Crosswalk, all identities 2015–2025 | 1,339 identities: 1,200 exact, 70 multi-county, 7 matched by name within county, 59 county-unincorporated, 3 unmatched. By units: 81.3% municipality, 18.7% county aggregate, 7 units unmatched |
| Crosswalk, 2025 | 1,152 jurisdictions: 1,038 exact, 57 multi-county, 2 by name, 55 county-unincorporated, 0 unmatched. 95.2% match a municipality; 83.2% of units match a municipality and 16.8% sit at a county aggregate |
| Contract validation (`contracts.validate`) | `areas`, `inventory`, `state_conditions`: no problems |
| Offline tests | 21 foundation tests and 48 in the full suite, all pass |

Unmatched BPS identities: Brokaw village (Marathon; MCD 09975, 2015–2020, 0 units; dissolved) and Silver Lake village (Kenosha; MCD 74025, 2015–2018, 7 units; merged into Salem Lakes).

Name-matched identities, where the BPS code is missing from TIGER 2024:

- Greenville town → Greenville village (BPS still uses the old code through 2025).
- Lisbon town → Lisbon village (same).
- Bristol, Fox Crossing (2 counties), Rib Mountain, Salem Lakes and Windsor, using pre-2022 codes.

### Spot checks

| Municipality | `area_id` | Context | One-unit detached (± MOE) | Total units | BPS id, match | BPS 2025 units |
| --- | --- | --- | --- | --- | --- | --- |
| Madison city | muni:5502548000 | urban | 53,292 ± 1,235 | 133,530 | 516500, exact | 3,383 (250 one-unit) |
| Milwaukee city | muni:5507953000 | urban | 101,402 ± 2,023 | 259,101 | 572000, multi-county (3) | 71 |
| Green Bay city | muni:5500931000 | urban | 26,655 ± 811 | 45,701 | 351000, exact | 283 |
| Appleton city | muni:5508702375 | urban | 18,771 ± 472 (Outagamie piece; 86.5% of the city) | 26,862 | 029000, multi-county | 79 (whole city) |
| Eau Claire city | muni:5503522300 | urban | 16,872 ± 714 (97.1%) | 31,005 | 255500, multi-county | 476 |
| Neenah city | muni:5513955750 | suburban | 8,172 ± 362 | 11,941 | 605000, exact | 169 |
| Sun Prairie city | muni:5502578600 | suburban | 8,118 ± 544 | 16,195 | 853000, exact | 100 |
| Greenville village | muni:5508731525 | small_community | 4,219 ± 263 | 4,744 | 358500, name match | 74 |
| Fox Crossing village | muni:5513926982 | suburban | 4,839 ± 400 | 8,935 | 555500, multi-county and name | 201 |

Madison's BPS series, 2015–2025, in total units: 1,665; 2,381; 2,188; 1,443; 1,658; 2,185; 3,626; 2,360; 2,620; 2,812; 3,383. It reported 10 months in 2016 and 11 in 2017, as the Gate 1 inventory found.

## Quality findings

1. **Milwaukee's published BPS totals look implausibly low.** They are 71 units in 2025, 97 in 2023 and 3,966 over 2015–2025, for a city of 259,101 housing units. Milwaukee reported 12 months in each of those years, so these are reported values, not imputation. This is a source-level issue for the permits agent to reconcile against city records before Milwaukee anchors any rate. I have not changed the values.
2. **County "Part Unincorporated Area" rows.** There are 55 such rows in 2025. Counties issue permits for towns that do not report on their own: 724 towns, holding 410,783 detached homes. The crosswalk links each county row to its towns, with allocation shares by detached homes, so the totals can be split. But that split is an **assumption**, not an observation. In Barron (2025, +7) and Taylor (2025, +48), the county row overlaps towns that also report on their own, so place-level sums exceed the county file. Use the county file as the control total.
3. **Twelve municipalities have no BPS row in any year 2015–2025, and no county row covers them.** Together they hold 13,212 detached homes. The largest are Caledonia village (Racine, 8,293 homes), Lake Hallie village (2,216) and Yorkville village (1,049). The rest are Clayton and Wauzeka towns (Crawford), Forest town and Genoa village (Vernon), Westfield village, Fairchild village, Mount Sterling village and Melvina village. Their permits are either missing from BPS or folded into another jurisdiction. Treat them as `not_reported`, never zero.
4. **Imputed years.** 517 municipality pieces have at least one BPS year with fewer than 12 months reported; 647 municipalities reported all 12 months in all 11 years. Place values for months not reported are Census imputations. `reporting_coverage` (months / 12) is kept on every row.
5. **ACS precision.** 27 municipalities have a coefficient of variation above 30% on one-unit detached homes. 37 pieces report zero detached homes, mostly water placeholders and tiny pieces of multi-county cities.
6. **Tracts and block groups straddle municipal lines.** 328 tracts and 270 block groups have less than half their land in any one municipality, so inherited context groups and municipal parents are approximate there.

## Coverage summary: observed, calculated, assumed

| Input (statewide foundation) | State | County | Municipality | Tract / BG | Status |
| --- | --- | --- | --- | --- | --- |
| Boundaries and land area | ✓ | ✓ | ✓ 1,925 pieces | ✓ | observed (TIGER 2024) |
| One-unit detached homes, with MOE | ✓ | ✓ | ✓ | ✓ | observed (ACS 5-year) |
| One-unit attached and total units | ✓ | ✓ | ✓ | ✓ | observed |
| Units 2–4, 5+ | ✓ | ✓ | ✓ | — | calculated (sum, root-sum-of-squares MOE) |
| Occupancy, vacancy | ✓ | ✓ | ✓ | — | observed; rate calculated |
| Year built | ✓ | ✓ | ✓ | — | observed |
| Annual housing units (PEP) | ✓ | ✓ | missing (PEP has none below county) | — | observed |
| Permits authorized by size, 2015–2025 | ✓ | ✓ | own row: 1,177 pieces / 1,415,574 homes (77%); county aggregate only: 724 towns / 410,783 homes (22%); none: 12 / 13,212 (0.7%) | — | observed (imputed months flagged) |
| Split of a multi-county city's BPS total to pieces | — | — | 121 pieces | — | assumed (share of detached homes) |
| Split of county-unincorporated permits to towns | — | — | 724 towns | — | assumed (share of detached homes) |
| Context group | — | ✓ | ✓ | ✓ | calculated (rule above; thresholds assumed) |
| Population | ✓ | ✓ | ✓ | ✓ | observed (ACS B01003; controlled MOE = 0 at state and county) |
| Parcel proxy counts | — | — | — | — | missing (not yet built; `parcel_proxy_count` is null) |

Per-municipality detail is in `coverage_municipalities.csv` and `.md`, one row per piece. Its columns:

- Identity: name, county, type, context.
- Inventory: detached homes and MOE, total units, inventory status.
- BPS: ids, match type, years present, years with 12, partial and 0 months, and units for 2015–2025 and 2025.
- `flags`, from this set: `county_issued_bps`, `no_bps_row`, `bps_years_missing`, `bps_imputed_years`, `multi_county`, `acs_cv_over_30pct`, `zero_detached_homes`, `water_placeholder`.

Flag counts: county_issued_bps 724, bps_imputed_years 517, multi_county 121, bps_years_missing 44, zero_detached_homes 37, acs_cv_over_30pct 27, no_bps_row 12, water_placeholder 12. 579 pieces have no flags.

## Known limitations

- **ACS 5-year values describe 2020–2024 on average.** They are the denominator by owner decision D4. Do not difference them against other ACS releases to infer construction.
- **BPS records authorizations only.** It does not identify ADUs, and it records new buildings, so ADU conversions are likely absent. Imputed months are Census estimates.
- **Permits at the county-unincorporated level** cannot be observed for individual towns. The towns' shares are assumptions.
- **The context rule's thresholds** (20,000 units, 750 and 425 per square mile) are judgment calls, pending owner review.
- **PEP has no municipal housing-unit estimates.** WI DOA municipal estimates were unreachable at Gate 1 and were not retried here.
- **Parcel-based allocation within areas** (`parcel_proxy_count`, `parcel_to_acs_ratio`) is not yet built. The fields exist and are null.
- **Boundaries are frozen at 2024-01-01.** Later annexations and incorporations, and the 2026 TIGER and V12 parcel vintages, need a crosswalk.

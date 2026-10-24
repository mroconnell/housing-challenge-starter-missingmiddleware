# Gate 2: Wisconsin Statewide Foundation

Prepared 2026-10-23 by the inventory and geography agent; revised 2026-10-24 after the independent Gate 2 review (items B1, S2, S8 and the note on integrity checks). Status: **built and checked; awaiting owner review.**

This package builds the statewide tables every later stage joins to:

- `areas`: Wisconsin, its 72 counties, 1,925 county-subdivision pieces (1,850 cities, villages and towns), 1,542 tracts and 4,692 block groups.
- `inventory`: one-unit detached homes, the ADU denominator, at every one of those levels.
- `state_conditions`: housing stock, occupancy, mix, age and permits.
- A crosswalk from Census Building Permits Survey (BPS) jurisdictions to municipalities.
- A per-municipality coverage table.

Everything comes from keyless Census bulk files, so a clean checkout rebuilds it without an API key.

## Bottom line

- **Statewide one-unit detached homes (ACS 2020–2024 5-year): 1,839,569 ± 6,502.** The published ACS 2024 1-year figure is 1,855,771. The 5-year figure is 16,202 lower (−0.87%), as expected: it averages 2020–2024, while the 1-year figure describes 2024 alone. Gate 3 uses the 5-year figure, because only the 5-year release reaches municipalities, tracts and block groups.
- **Integrity checks pass (these confirm the files were read correctly; they do not validate the estimates).** Block groups sum to tracts, tracts to counties, municipalities to counties, and counties to the state, with 0 difference for every parent on detached, attached and total units. The Census Bureau publishes these tables so that they nest, so a non-zero difference would mean a parsing or join error, not a finding about housing.
- **BPS files are internally consistent.** In 2025, Wisconsin authorized 25,569 units in the published state file (13,405 of them in one-unit buildings), and the 72 county rows sum to exactly 25,569, in every year 2015–2025. This is also true by construction of the Census files and is an integrity check. The place-level rows sum to 25,624 in 2025, 55 more; that excess comes from two counties (see quality findings). **Statewide and Milwaukee County totals include Milwaukee city's incomplete multifamily series (quality finding 1).**
- **Crosswalk: in 2025, 95.3% of BPS jurisdictions (1,098 of 1,152) match a municipality, and 100% match either a municipality or a county "unincorporated area" row. Nothing is unmatched in 2025.** Over 2015–2025, 1 of 1,339 jurisdiction identities is unmatched (Brokaw village, dissolved, 0 units). A county row is now recognized only by its name ("… County Part Unincorporated Area"); villages whose BPS row has a blank MCD code in some years are matched by place code or name (review item B1).
- **The biggest coverage gap: 724 towns, holding 410,783 one-unit detached homes (22.3% of the state), have no BPS row of their own in any year 2015–2025.** Their permits are reported only inside a county "Part Unincorporated Area" row, so their permit baselines can be observed only at that county-wide aggregate. A further 28 towns (13,738 homes) have their own row in some years and are inside the county row in the others. The B1 fix did not change the 724 / 410,783 figure: the misread village rows had been spread over towns that were already county-row towns.

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
| `areas.parquet` | 8,232 | `area_id`, `geoid`, `level`, `name`, `parent_ids` (list), `parent_county_id`, `parent_municipality_id`, `parent_municipality_share`, `parent_tract_id`, `land_area_sqm`, `water_area_sqm`, `muni_type` (city/village/town/not_defined), `cousubfp`, `n_county_pieces`, `metro_county`, `context_group`, `context_rule`, and for municipalities the whole-municipality rule inputs `context_hu_whole`, `context_density_whole`, `context_main_county`, `context_metro_main`, `context_largest_in_county`; `population` (ACS B01003, labeled), `housing_units_acs`, `hu_density_per_sqmi`, `boundary_source_id`, `boundary_vintage` |
| `inventory.parquet` | 8,232 | `homes_1unit_detached` and `_moe` (B25024_002), `homes_1unit_attached` and `_moe`, `total_housing_units` and `_moe`, `cv_1unit_detached`, `parcel_proxy_count`/`parcel_to_acs_ratio` (null until parcels are added), `method_note`, `missing_reason`, `status`, `source_id`, `source_vintage`, `context_group` |
| `state_conditions.parquet` | 89,800 | Long form, keyed on (`area_id`, `year`, `indicator`), plus `reporting_coverage`, `coverage_basis`, `geography_note`, `missing_reason` (`not_reported` where `value` is null) and `value_as_published` (the BPS figure kept for rows nulled as known gaps). Indicators are listed below the table. |
| `bps_place_annual.parquet` | 12,649 | Every Wisconsin BPS place row for 2015–2025, with buildings and units by size, reported-only units, `months_reported`, `reporting_status` (reported_12_months / partly_imputed / imputed) and `quality_flag` (`multifamily_series_incomplete` on Milwaukee 2020, 2023, 2025) |
| `bps_muni_crosswalk.parquet` / `.csv` | 2,117 | One row per BPS identity and municipality piece: `match_type`, `wi_muni_id`, `area_id`, `is_primary_piece`, `alloc_share`, `match_note`, first and last year; for county rows also `county_years_covered` and `town_has_own_row_some_years` |
| `bps_county_unincorporated_allocation.parquet` / `.csv` | 8,116 | Per-year split of each county row to the towns without their own BPS row **in that year**: `alloc_share` (ACS detached homes), `allocated_units_total`, `allocated_1unit`; `status` = assumed |
| `bps_unmatched.csv` | 1 | Unmatched BPS identities |
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
| `permitted_units_total`, `permitted_units_1unit`, `permitted_units_2_4`, `permitted_units_5plus` | BPS | State, county and municipality, 2015–2025 | observed; 9 Milwaukee city rows (total, 2–4, 5+ in 2020, 2023, 2025) have a null value with `missing_reason` = not_reported |

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

Revised after review item S8. Every input is measured on the **whole municipality** (all county pieces summed), so the pieces of a multi-county city or village always share one group (before the revision, Fox Crossing's two pieces fell in different groups).

- `hu` = ACS 2020–2024 housing units (B25024_001); `density` = `hu` per square mile of TIGER land area.
- Main county = the county piece holding most of the municipality's housing units; "metro" means that county is in an OMB 2023 metropolitan CBSA.

The rule is applied in order:

1. **urban**: `hu` ≥ 20,000; or `hu` ≥ 10,000, density ≥ 300 and the largest municipality (by `hu`) in its main county. The second route captures regional cities such as Wausau, Superior and Manitowoc.
2. **suburban**: not urban, main county metropolitan, and either density ≥ 425 (the Census 2020 urban-area housing-density threshold) or a city or village with `hu` ≥ 2,500. The size route captures large, low-density metro suburbs such as Caledonia and Franklin.
3. **small_community**: any other city or village.
4. **rural**: any other town.

Towns reach suburban only through density, never through size, so large but sparse metro towns (e.g. Oconomowoc town, 4,049 units, 146 per sq mi) stay rural. Tracts and block groups take the group of their majority municipality. Counties take the group holding most of their housing units. The 12 "County subdivisions not defined" water pieces have no group. I kept the four contract groups (`contracts.CONTEXT_GROUP`); a separate "small city" group would need a contract change.

| Group | Municipalities (pieces) | One-unit detached homes | Counties |
| --- | --- | --- | --- |
| urban | 20 (25) | 427,619 | 11 |
| suburban | 164 (184) | 450,535 | 9 |
| small_community | 426 (464) | 251,345 | 8 |
| rural | 1,240 (1,240) | 710,070 | 44 |

The 20 urban municipalities are Milwaukee, Madison, Green Bay, Kenosha, Racine, Appleton, Eau Claire, Waukesha, West Allis, Oshkosh, Janesville, La Crosse, Wauwatosa, Sheboygan, Fond du Lac (all ≥ 20,000 units), plus Wausau, Manitowoc, West Bend, Superior and Stevens Point (regional cities).

Compared with the first version, 52 pieces changed group:

- 41 moved from small_community to suburban: large metro suburbs (Caledonia, Mount Pleasant, Franklin, Mequon, Muskego, Pewaukee city, Germantown, Pleasant Prairie, Weston, Greenville, Harrison, Salem Lakes and others), plus some free-standing small cities in metro counties (Columbus, Brodhead, Edgerton, Burlington).
- 3 moved from small_community to urban (Manitowoc, Stevens Point, Superior), and 2 from suburban to urban (Wausau, West Bend).
- 6 moved from suburban to small_community: small pieces whose municipality's main county is not metropolitan (Waupun, Blanchardville, Brooklyn, Montfort, Randolph, Rockland).

The places the review named (from `checks.json` → `context_named_places`):

| Municipality | Housing units (whole) | Units per sq mi | Main county metro | Largest in county | Group |
| --- | --- | --- | --- | --- | --- |
| Wausau city | 18,718 | 973 | yes | yes | urban |
| Manitowoc city | 16,506 | 920 | no | yes | urban |
| West Bend city | 14,680 | 943 | yes | yes | urban |
| Franklin city | 14,540 | 421 | yes | no | suburban |
| Beloit city | 14,531 | 837 | yes | no | suburban |
| Superior city | 12,776 | 349 | yes | yes | urban |
| Mount Pleasant village | 12,366 | 365 | yes | no | suburban |
| Stevens Point city | 11,614 | 671 | no | yes | urban |
| Grand Chute town | 11,192 | 501 | yes | no | suburban |
| Caledonia village | 10,499 | 232 | yes | no | suburban |
| Mequon city | 10,078 | 218 | yes | yes | suburban |
| Marshfield city (2 counties) | 9,722 | 704 | no | yes | small_community |
| Fox Crossing village (2 counties) | 8,935 | 707 | yes | no | suburban (both pieces) |
| Pewaukee city | 7,241 | 371 | yes | no | suburban |
| Whitewater city (2 counties) | 5,925 | 670 | no | yes | small_community (both pieces) |
| Greenville village | 4,744 | 133 | yes | no | suburban |
| Brookfield town | 3,496 | 695 | yes | no | suburban |
| Campbell town | 2,067 | 549 | yes | no | suburban |

Known edge cases:

- Wauwatosa and West Allis are dense inner suburbs of Milwaukee and count as urban by size.
- Beloit (14,531 units) is a historic industrial city, but Janesville is larger in Rock County, so Beloit counts as suburban.
- Mequon is the largest municipality in Ozaukee County but is too sparse (218 per sq mi) for the regional-city route, so it counts as suburban.
- Marshfield (9,722 units) is just under the 10,000-unit floor and counts as small_community.
- Towns such as Brookfield, Grand Chute and Campbell are suburban by density. That is intended: they are built-up suburban towns.

**The owner should confirm or change the rule.** It is one set of constants in `geo.py` (`URBAN_MIN_HU`, `REGIONAL_CITY_MIN_HU`, `REGIONAL_CITY_MIN_DENSITY`, `SUBURBAN_MIN_DENSITY`, `SUBURBAN_MIN_HU_INCORPORATED`).

## Check results

The first block below is **integrity checks**. ACS tables nest by design, the BPS state file is the sum of its county rows, and the PEP state row is the sum of its counties. These checks confirm the files were parsed and joined correctly; they cannot detect an error in the Census estimates themselves.

| Integrity check | Result |
| --- | --- |
| Block groups → tracts, tracts → counties, municipalities → counties, counties → state | 0 difference for all 1,542 tracts, 72 counties and the state, on detached, attached and total units |
| BPS: state file vs sum of county rows | 25,569 vs 25,569 in 2025; equal in every year 2015–2025 |
| PEP: state vs sum of counties | 0 difference in every year 2020–2025; 2025 state = 2,840,960 |
| Contract validation (`contracts.validate`) | `areas`, `inventory`, `state_conditions`: no problems |
| Every `county_unincorporated` crosswalk row has "County" or "Unincorporated" in its BPS name | true (`checks.json` → `county_unincorporated_names_all_say_county`) |

| Comparison or coverage check | Result |
| --- | --- |
| Statewide one-unit detached homes, ACS 5-year vs the published 1-year | 1,839,569 ± 6,502 vs 1,855,771: −16,202 (−0.87%). Explained by the period difference, not an error. State total units 2,778,572 ± 1,533; one-unit attached 120,679 ± 2,636 |
| BPS 2025: state file vs sum of place rows | 25,569 vs 25,624 (+55: Barron +7, Taylor +48); small gaps in earlier years in Clark (019) and Lafayette (065), at most 9 units |
| BPS reporting, 2025 | 91.4% of state units come from reported data, not Census imputation; 1,014 of 1,152 places reported 12 months and 113 reported 0 |
| Crosswalk, all identities 2015–2025 | 1,339 identities: 1,200 exact, 70 multi-county, 3 by place code (blank MCD), 8 by name within county, 2 by documented merger alias, 55 county-unincorporated, 1 unmatched. By units (230,921): 81.5% municipality, 18.5% county aggregate, 0 units unmatched |
| Crosswalk, 2025 | 1,152 jurisdictions: 1,038 exact, 57 multi-county, 3 by name, 54 county-unincorporated, 0 unmatched. 95.3% match a municipality; 83.3% of units match a municipality and 16.7% sit at a county aggregate |
| County-row allocation | Per-year shares sum to 1 for every county row and year; allocated units equal the county rows' published units in every year (e.g. 4,285 in 2025). Waukesha County's row (2015–2022, 0 units) has no town to cover, because every Waukesha town reports on its own |
| Offline tests | 28 foundation tests and 77 in the full suite, all pass |

**Crosswalk matches by method other than code** (`checks.json` → `crosswalk_non_code_matches`):

| BPS identity | Years | Units | Method | Matched to |
| --- | --- | --- | --- | --- |
| Harrison village (Calumet), MCD blank | 2015–2019 | 435 | place code 32790 | Harrison village, `muni:5501532790` (+ Winnebago piece `5508732790` by share). Before the fix these units were spread over Charlestown, Woodville, Brillion and New Holstein towns |
| Bloomfield village (Walworth), MCD blank | 2017–2018 | 20 | place code 08265 | Bloomfield village, `muni:5512708265` |
| Somers village (Kenosha), MCD blank | 2017–2018 | 18 | place code 74625 | Somers village, `muni:5505974625`. Before: a county row with no town |
| Rib Mountain village (Marathon), MCD 00000 | 2022–2025 | 51 | name (place code 67325 is the old town code) | Rib Mountain village, `muni:5507367320`. Before: spread over 18 Marathon towns |
| Rib Mountain town, old code 67325 | 2015–2021 | 125 | name, type changed | Rib Mountain village, `muni:5507367320` |
| Greenville town, old code 31550 | 2015–2025 | 793 | name, type changed | Greenville village, `muni:5508731525` (BPS still uses the old code) |
| Lisbon town, old code 44850 | 2015–2025 | 534 | name, type changed | Lisbon village, `muni:5513344847` |
| Bristol, Fox Crossing (2 counties), Salem Lakes, Windsor (pre-2022 codes) | 2015–2021 | 828 | name | the village of the same name |
| Silver Lake village (Kenosha) | 2015–2018 | 7 | merger alias | Salem Lakes village (Silver Lake merged with Salem town in 2017). Its rows are summed with Salem Lakes' rows in those years (`geography_note` = "summed over 2+ BPS rows", status calculated) |

The one unmatched identity is Brokaw village (Marathon; MCD 09975, 2015–2020, 0 units; dissolved).

**Towns with both their own BPS row and a county row.** 28 towns (13,738 detached homes) report on their own in some years and fall inside their county's "Part Unincorporated Area" row in others. Examples: six Dane County towns (Bristol, Westport, Springfield, Sun Prairie, Berry, Blue Mounds) have their own row in one year and the county row in ten; Georgetown, Clam Falls and Lorain towns (Polk) are the reverse. Each county row is now allocated **per year**, only to towns without their own row in that year, so no town gets both its own permits and a county share in the same year. The list, with years, is in `checks.json` → `county_row_towns.towns_both_detail`, and these towns carry the flag `county_issued_bps_some_years`. The review's count of 15 used the old rule, which looked only at each county row's last year.

### Spot checks

| Municipality | `area_id` | Context | One-unit detached (± MOE) | Total units | BPS id, match | BPS 2025 units |
| --- | --- | --- | --- | --- | --- | --- |
| Madison city | muni:5502548000 | urban | 53,292 ± 1,235 | 133,530 | 516500, exact | 3,383 (250 one-unit) |
| Milwaukee city | muni:5507953000 | urban | 101,402 ± 2,023 | 259,101 | 572000, multi-county (3) | null in `state_conditions` (not_reported); BPS publishes 71, of which 63 one-unit |
| Green Bay city | muni:5500931000 | urban | 26,655 ± 811 | 45,701 | 351000, exact | 283 |
| Appleton city | muni:5508702375 | urban | 18,771 ± 472 (Outagamie piece; 86.5% of the city) | 26,862 | 029000, multi-county | 79 (whole city) |
| Eau Claire city | muni:5503522300 | urban | 16,872 ± 714 (97.1%) | 31,005 | 255500, multi-county | 476 |
| Neenah city | muni:5513955750 | suburban | 8,172 ± 362 | 11,941 | 605000, exact | 169 |
| Sun Prairie city | muni:5502578600 | suburban | 8,118 ± 544 | 16,195 | 853000, exact | 100 |
| Greenville village | muni:5508731525 | suburban | 4,219 ± 263 | 4,744 | 358500, name match | 74 |
| Fox Crossing village | muni:5513926982 | suburban | 4,839 ± 400 | 8,935 | 555500, multi-county and name | 201 |

Madison's BPS series, 2015–2025, in total units: 1,665; 2,381; 2,188; 1,443; 1,658; 2,185; 3,626; 2,360; 2,620; 2,812; 3,383. It reported 10 months in 2016 and 11 in 2017, as the Gate 1 inventory found.

## Quality findings

1. **Milwaukee's BPS multifamily series is incomplete; its one-unit series is usable with caution.** BPS shows Milwaukee city with 0 units in 3–4 and 5+ unit buildings in 2020, 2023 and 2025 (totals 112, 97 and 71). The independent review compared the city's own open data (data.milwaukee.gov "buildingpermits"): 2023 had 14 multifamily new-construction permits worth about $113M, while BPS shows 0 units in 5+ unit buildings. In 2025, Milwaukee County's 846 units in 5+ unit buildings all came from other places (Bayside, Glendale, Oak Creek, West Allis, Whitefish Bay). One-unit counts roughly agree with city records (BPS 2023: 61; city file: about 72 one- and two-family new buildings). Milwaukee reported 12 months in 2015 and 2019–2025, but only 10 months in 2016 and 11 in 2017 and 2018.
   - **What the build does:** in `state_conditions`, Milwaukee city's `permitted_units_total`, `permitted_units_2_4` and `permitted_units_5plus` for 2020, 2023 and 2025 have a null `value`, `missing_reason` = not_reported, the published figure in `value_as_published`, and an explanation in `geography_note` and `coverage_basis`. `permitted_units_1unit` is kept. `bps_place_annual` marks those rows `quality_flag` = multifamily_series_incomplete. No replacement value is imputed. The list of gaps is the constant `KNOWN_BPS_GAPS` in `build.py`.
   - Other years with non-zero multifamily (e.g. 2024: 152 units in 5+) are kept as published, but may also be incomplete; only the three zero years are flagged.
   - **Footnote for totals:** the Wisconsin and Milwaukee County (55079) BPS totals for 2020, 2023 and 2025 include Milwaukee city's zeros. Treat them as lower bounds for multifamily and total units. Their `geography_note` says so; the published values are not changed.
2. **County "Part Unincorporated Area" rows.** There are 54 such rows in 2025 (55 identities over 2015–2025). A row is treated as a county row only if its name says "County" or "Unincorporated"; a blank MCD code alone no longer counts (review item B1). Counties issue permits for towns that do not report on their own: 724 towns (410,783 detached homes) have only the county row, and 28 more have it in some years. The per-year allocation file splits each county row among the towns it covers that year, by detached homes. That split is an **assumption**, not an observation. In Barron (2025, +7) and Taylor (2025, +48), the county row overlaps towns that also report on their own, so place-level sums exceed the county file. Use the county file as the control total.
3. **Twelve municipalities have no BPS row in any year 2015–2025, and no county row covers them.** Together they hold 13,212 detached homes. The largest are Caledonia village (Racine, 8,293 homes), Lake Hallie village (2,216) and Yorkville village (1,049). The rest are Clayton and Wauzeka towns (Crawford), Forest town and Genoa village (Vernon), Westfield village, Fairchild village, Mount Sterling village and Melvina village. Their permits are either missing from BPS or folded into another jurisdiction. Treat them as `not_reported`, never zero.
4. **Imputed years.** 521 municipality pieces have at least one BPS year with fewer than 12 months reported; 647 municipalities reported all 12 months in all 11 years. Place values for months not reported are Census imputations. `reporting_coverage` (months / 12) is kept on every row.
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
| Permits authorized by size, 2015–2025 | ✓ (Milwaukee footnote) | ✓ (Milwaukee County footnote) | own row: 1,177 pieces / 1,415,574 homes (77%), of which 28 towns / 13,738 homes also county-row in some years; county aggregate only: 724 towns / 410,783 homes (22.3%); none: 12 / 13,212 (0.7%); Milwaukee multifamily 2020, 2023, 2025: not_reported | — | observed (imputed months flagged) |
| Split of a multi-county city's BPS total to pieces | — | — | 121 pieces | — | assumed (share of detached homes) |
| Split of county-unincorporated permits to towns | — | — | 752 towns, per year | — | assumed (share of detached homes) |
| Context group | — | ✓ | ✓ | ✓ | calculated (rule above; thresholds assumed) |
| Population | ✓ | ✓ | ✓ | ✓ | observed (ACS B01003; controlled MOE = 0 at state and county) |
| Parcel proxy counts | — | — | — | — | missing (not yet built; `parcel_proxy_count` is null) |

Per-municipality detail is in `coverage_municipalities.csv` and `.md`, one row per piece. Its columns:

- Identity: name, county, type, context.
- Inventory: detached homes and MOE, total units, inventory status.
- BPS: ids, match type, years present, years with 12, partial and 0 months, and units for 2015–2025 and 2025.
- BPS: also `bps_years_county_row` (years the piece sits inside a county row).
- `flags`, from this set: `county_issued_bps`, `county_issued_bps_some_years`, `no_bps_row`, `bps_years_missing`, `bps_imputed_years`, `multi_county`, `acs_cv_over_30pct`, `zero_detached_homes`, `water_placeholder`.

Flag counts: county_issued_bps 724, bps_imputed_years 521, multi_county 121, bps_years_missing 41, county_issued_bps_some_years 28, zero_detached_homes 37, acs_cv_over_30pct 27, no_bps_row 12, water_placeholder 12. 579 pieces have no flags.

## Known limitations

- **ACS 5-year values describe 2020–2024 on average.** They are the denominator by owner decision D4. Do not difference them against other ACS releases to infer construction.
- **BPS records authorizations only.** It does not identify ADUs, and it records new buildings, so ADU conversions are likely absent. Imputed months are Census estimates. Milwaukee city's multifamily series is incomplete (quality finding 1); other cities could have similar gaps that have not been checked.
- **Permits at the county-unincorporated level** cannot be observed for individual towns. The towns' shares are assumptions.
- **The context rule's thresholds** (20,000 and 10,000 units, 300 and 425 per square mile, 2,500 units) are judgment calls, pending owner review.
- **PEP has no municipal housing-unit estimates.** WI DOA municipal estimates were unreachable at Gate 1 and were not retried here.
- **Parcel-based allocation within areas** (`parcel_proxy_count`, `parcel_to_acs_ratio`) is not yet built. The fields exist and are null.
- **Boundaries are frozen at 2024-01-01.** Later annexations and incorporations, and the 2026 TIGER and V12 parcel vintages, need a crosswalk.

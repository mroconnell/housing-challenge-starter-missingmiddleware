# California comparison data and step 0 reconciliation

Gate 2 addendum, built 2026-10-24; revised the same day after the independent review of the addenda (items B1, S1, S4, S6, N1–N4). Assembles the inputs for the pre-registered California comparison study ([plan](../gate3/CA_COMPARISON_PLAN.md), AQ-017, AQ-031) and runs **step 0 only**: a data-quality reconciliation of Census BPS against HCD APR. **Nothing here computes the study**: no permissive or restrictive groups, no comparisons around reform waves, no ramp or spillover estimates.

**How the numbers in this document are kept honest.** Every table and figure computed from data sits between `<!-- generated:… -->` markers and is rewritten from the build outputs by `missing_middleware/comparison/ca_doc.py` at the end of every build. `scripts/build_ca_comparison_data.py --check-doc` fails if any block differs from the outputs, and `tests/test_ca_comparison.py` runs the same check when the outputs are present. Outside the markers, the only figures are source metadata from the download manifests (bytes, checksums, dates) and fixed parameters (seed, years, thresholds).

**Holdout rule.** Every step 0 output carries a holdout marker: `in_holdout` on jurisdiction-level rows, `jurisdiction_sample` (`non_holdout` or `all`) on aggregates that could feed the model, or `includes_holdout_jurisdictions` on state- and county-level data-quality aggregates. Holdout jurisdictions appear in descriptive data-quality tables. They are excluded from every estimate that could feed the model: those are shown for non-holdout jurisdictions, with the all-jurisdiction figure beside them for comparison only.

## Sources

| Source id | What | URL | Vintage | Accessed | License / terms | Bytes | SHA-256 |
|---|---|---|---|---|---|---:|---|
| `hcd_apr_a2` | HCD APR Table A2, project level (CSV), found through the CKAN API `resource_show?id=fe505d9b-…` | [tablea2.csv](https://publish.data.ca.gov/dataset/81b0841f-2802-403e-b48e-2ef4b751f77c/resource/fe505d9b-8c36-42ba-ba30-08bc4f34e022/download/tablea2.csv) ([dataset](https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year)) | Reporting years 2018–2025; resource modified 2026-10-23 | 2026-10-24 | data.ca.gov license field says "License not specified"; California open data terms of use | 294,538,874 | `e3c98250…2db1a64a` |
| `hcd_apr_a2` | Table A2 data dictionary (DOCX) | [data dictionary](https://publish.data.ca.gov/dataset/81b0841f-2802-403e-b48e-2ef4b751f77c/resource/354a375a-821d-4d4e-97ab-4d79c2925fce/download/annualprogressreport_tablea2_datadictionary-2.docx) | as posted 2026-10-01 | 2026-10-24 | same | 35,940 | `dfa79f60…c9549efc113` |
| `hcd_apr_a2` (api/) | CKAN `datastore_search_sql` aggregates: Table A and Table D jurisdiction-years (evidence that a report was filed), and A2 year × UNIT_CAT totals (cross-check of the CSV). The SQL is saved in the manifest. | `https://data.ca.gov/api/3/action/datastore_search_sql` | live 2026-10-24 | 2026-10-24 | same | small | in `_downloads.json` |
| `buildinganadu_ca_2012_2019` | Building an ADU, "California ADU Permits by City from 2012–2019", Sheet1, CSV export | [export](https://docs.google.com/spreadsheets/d/10rb8p7DU379vQw9oeS_Z9dwK9F9c5ZBeTw09wQlvwQY/export?format=csv&gid=0) (linked from [buildinganadu.com/california-adu-charts](https://www.buildinganadu.com/california-adu-charts)) | undated compilation, HCD-attributed | 2026-10-24 | No license stated; publicly viewable third-party compilation; attribution to BuildinganADU.com and HCD (AQ-017) | 20,485 | `216b70a2…0c45f473` |
| `census_tiger_2024_ca_place` | TIGER/Line 2024 California places (attributes only: CLASSFP, FUNCSTAT) | [tl_2024_06_place.zip](https://www2.census.gov/geo/tiger/TIGER2024/PLACE/tl_2024_06_place.zip) | geography as of 2024-01-01 | 2026-10-24 | Public domain (17 U.S.C. 105) | 9,792,773 | `81b82712…39656a42` |
| `census_pep_hu_states` | PEP housing units, CA and WI: Vintage 2020 (2010–2020) CSVs, Vintage 2025 (2020–2025) xlsx | [HU-EST2020_6.csv](https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/housing/HU-EST2020_6.csv), [HU-EST2020_55.csv](https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/housing/HU-EST2020_55.csv), [CO-EST2025-HU-06.xlsx](https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-06.xlsx), [CO-EST2025-HU-55.xlsx](https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx) | V2020, V2025 | 2026-10-24 | Public domain | 8,663 / 10,223 / 16,414 / 17,071 | in `_downloads.json` |
| `census_acs5_2024_tbsf` (shared, read only) | ACS 2020–2024 5-year B25024, national table-based summary file; owned by the Wisconsin foundation build and checked against its manifest | [acsdt5y2024-b25024.dat](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b25024.dat) | ACS 2020–2024 | 2026-10-23 | Public domain | 47,866,463 | `26ff26c6…7493add2ef` |
| `census_bps_ca` (existing) | Census BPS 2010–2025: CA state, county and place files; the national state file also supplies the Wisconsin rows | see `scripts/build_ca_bps.py` | annual | 2026-10-24 | Public domain | — | `data/raw/census_bps_ca/manifest.json` |

Every file goes in `data/raw/<source_id>/`, with its URL, bytes, SHA-256 and access date recorded in `_downloads.json`. The build manifest `data/processed/comparison_ca/ca_comparison_manifest.json` repeats the source register and records the SHA-256 of every output. The Google Sheet export worked over plain HTTPS, so the local fallback copy (`…/work/california-adu-permits-2012-2019.csv`) was not needed. That copy matches the export cell for cell: 527 rows, no differences.

**Personal and locational data.** Table A2 includes APN, prior APN, street address, standardized address, project name, tracking id, notes and latitude/longitude. These stay in the raw file in `data/raw` only. At ingestion, the APN, address, tracking id and permit date are combined into a one-way SHA-1 `permit_key`. This key is used in memory to detect repeated listings and is never written to any output. No processed table or reference table carries an address, an APN or a key.

## Commands

```sh
uv run python scripts/build_ca_bps.py                 # existing: BPS 2010-2025 (needed first)
uv run python scripts/build_ca_comparison_data.py     # fetch (skips files present) + build + step 0 + doc tables
uv run python scripts/build_ca_comparison_data.py --skip-fetch      # rebuild offline
uv run python scripts/build_ca_comparison_data.py --doc-only        # rewrite this doc's generated blocks from outputs
uv run python scripts/build_ca_comparison_data.py --check-doc       # fail if this doc differs from the outputs
bash scripts/test.sh                                  # includes tests/test_ca_comparison.py
```

The build runs in about 13 s once the raw files are present. Code: `missing_middleware/comparison/ca_sources.py` (register, downloader, CKAN queries), `ca_inputs.py` (readers), `ca_crosswalk.py` (crosswalk and holdout), `ca_step0.py` (reconciliation and statewide series), `ca_doc.py` (this document's generated tables).

## Outputs

`data/processed/comparison_ca/` (git-ignored; parquet plus a CSV copy). Every jurisdiction-level output has `in_holdout`.

<!-- generated:outputs_rows -->
| File | Grain | Rows |
|---|---|---:|
| `hcd_apr_a2_juris_year_unitcat` | HCD jurisdiction × report year × UNIT_CAT | 13,018 |
| `hcd_apr_a2_issue_year_dedup` | jurisdiction × permit issue year × UNIT_CAT × `issue_year_flag` | 11,603 |
| `hcd_apr_filing_status` | jurisdiction × year 2018–2025 | 4,304 |
| `adu_compilation_2012_2019` | jurisdiction × year | 4,216 |
| `ca_denominators_acs2024` | incorporated places + county remainders | 539 |
| `ca_jurisdiction_crosswalk` | HCD or compilation name | 539 |
| `step0_juris_year_panel` | census_geoid × year 2018–2025 | 4,268 |
<!-- /generated:outputs_rows -->

- `hcd_apr_a2_juris_year_unitcat`: `bp_units_primary`, `bp_units_reported`, and the components between them (`_date_missing`, `_date_earlier_repeat`, `_date_earlier_late_first`, `_date_later`), plus `ent_units`, `co_units`, `dem_units`, `project_rows`.
- `hcd_apr_a2_issue_year_dedup`: each permit counted once, in the year it was issued (alternative measure). `issue_year_flag` marks dates that cannot be right as entered (see below).
- `hcd_apr_filing_status`: `a2_rows` / `filed_no_a2_rows` / `no_record`, with flags for presence in Tables A, A2 and D.
- `adu_compilation_2012_2019`: ADU permits; a blank cell is `missing`, not zero.
- `ca_denominators_acs2024`: ACS total units and one-unit detached homes, with MOEs.
- `ca_jurisdiction_crosswalk`: `census_geoid`, `placefp`, `county_fips`, `bps_ids`, `match_method`, `in_holdout`, `bps_missing_city`, `bps_may_include_cities`.
- `step0_juris_year_panel`: HCD units by category under all three measures, BPS units by size class (estimated and reported-only), months reported, filing status, ACS denominators, `in_holdout`, `bps_missing_city`, `bps_may_include_cities`, and the HCD units of a county's BPS-missing cities on its remainder row (`*_bps_missing_cities`).
- `step0/*.csv`: the reconciliation tables below.

`reference/` (committed; small; no personal data): `ca_jurisdiction_crosswalk.csv`, `ca_holdout_jurisdictions.csv`, `ca_wi_statewide_bps_per_1000.csv`.

The manifest `ca_comparison_manifest.json` records repository-relative paths only, the SHA-256 of every output, and `outputs_in_write_order` with a write time for each file.

### Which APR columns count as "permits issued"

The building-permit measure is `NO_BUILDING_PERMITS` ("Total number of units issued building permits in the project"). On every row it equals the sum of the 11 `BP_*_INCOME_*` columns, which the build asserts. Entitlements use `NO_ENTITLEMENTS` and completions use `NO_OTHER_FORMS_OF_READINESS` (certificates of occupancy or similar). Both are kept as separate fields, summed over all rows of the report.

**Repeated listings, a finding that matters.** Many rows carry a permit date in a year before the report year. Part of these belong to a permit that the same jurisdiction also lists in another report year, typically again when the certificate of occupancy is issued, so summing `NO_BUILDING_PERMITS` by report year double counts. The City of Los Angeles accounts for most of them. Three measures are kept, and the primary measure was chosen before any comparison with BPS:

- **`bp_units_primary`** (primary): units whose permit date falls in the report year, plus units with no date. This matches the APR definition "issued this year".
- **`bp_units_reported`**: everything as published, for example in HCD's dashboard totals.
- **`bp_units_issue_year_dedup`**: each permit key counted once, in its issue year. This also catches permits first reported late, but recent issue years will rise as later reports arrive.

<!-- generated:apr_measures -->
| Figure (Table A2, 2018–2025 reports, all jurisdictions) | Value |
|---|---:|
| Rows in Table A2 | 926,774 |
| Permitted units as reported (`NO_BUILDING_PERMITS`) | 1,214,141 |
| Units whose permit date is before the report year | 210,165 (17% of reported) |
| … of which the same permit is also listed in another report year (repeats) | 107,339 |
| … of which first reported late (kept by the dedup measure, dropped by the primary) | 102,826 |
| … of which City of Los Angeles | 100,612 |
| Units with no permit date (kept in the primary measure) | 46 |
| Units dated after the report year (dropped by the primary measure) | 3,677 |
| Dedup table: units with an issue year after the year first reported | 3,022 |
| … of which dated 2018–2025 (kept, flagged) | 2,860 |
| Dedup table: units with an issue year before 2000 (ignored: outside 2018–2025) | 66 |
| Dedup table: issue-year range as entered | 1916–2109 |
| CSV vs datastore API, year × UNIT_CAT cells matching | 48 of 48 |
<!-- /generated:apr_measures -->

**Impossible issue dates (N2).** Issue years in the dedup table run far outside any plausible range as entered. They are flagged, not corrected: `issue_year_flag` is `after_first_report_year` when the permit is dated after the report year it was first listed in, and `before_2000` for very old dates. Step 0 reads only issue years 2018–2025, so flagged rows outside that window are ignored. Flagged rows dated 2018–2025 are kept in the dedup measure; their size is in the table above.

Statewide HCD permitted units under the primary measure, with as-reported and issue-year totals for ADUs (all jurisdictions, descriptive):

<!-- generated:apr_statewide -->
| Year | SFD | SFA | 2–4 | 5+ | ADU | ADU as reported | ADU, issue-year dedup | MH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 43,047 | 4,448 | 4,360 | 51,666 | 8,913 | 9,006 | 12,154 | 2,331 |
| 2019 | 43,241 | 4,252 | 4,449 | 54,955 | 12,706 | 15,086 | 13,279 | 1,960 |
| 2020 | 41,248 | 3,784 | 3,369 | 49,187 | 12,775 | 16,041 | 13,479 | 2,064 |
| 2021 | 51,669 | 3,725 | 3,931 | 52,596 | 20,622 | 24,640 | 21,963 | 2,419 |
| 2022 | 41,429 | 3,659 | 3,662 | 65,682 | 25,483 | 31,806 | 27,027 | 1,802 |
| 2023 | 38,677 | 4,477 | 3,303 | 57,497 | 28,420 | 35,720 | 29,861 | 1,805 |
| 2024 | 37,190 | 3,750 | 3,712 | 40,340 | 30,601 | 39,073 | 31,592 | 1,292 |
| 2025 | 36,653 | 3,719 | 3,795 | 45,957 | 32,366 | 41,853 | 32,280 | 1,311 |
<!-- /generated:apr_statewide -->

The 2018 issue-year count includes permits issued in 2018 but first reported in 2019 or later.

### Denominators

ACS 2020–2024 B25024 rows: E001 is total units and E002 is one-unit detached. Cities use summary level 160, filtered to incorporated places (TIGER 2024 `CLASSFP` C1, `FUNCSTAT` A, including San Francisco). Each **county remainder** is the county total (050) minus the sum of its incorporated-place parts (155), so it includes every CDP. Its MOE is the root-sum-of-squares approximation, and its status is `calculated`. San Francisco has no remainder. California county subdivisions (summary level 060) are census county divisions, which are not governments and match no HCD jurisdiction, so they are not used. No California city crosses a county line (the 155 parts confirm this). The build checks that places plus remainders equal the state total of one-unit detached homes. Mountain House incorporated on 2024-07-01, after the 2024 geography date. It is a CDP in ACS and TIGER, so it sits inside the San Joaquin remainder.

## Crosswalk

<!-- generated:crosswalk -->
|  | Names | Matched to Census | Matched to BPS place ids |
|---|---:|---:|---:|
| HCD APR Table A2 jurisdictions | 534 | 534 (100.0%) | 519 (97.2%) |
| Compilation rows | 527 | 527 (100.0%) | 512 (97.2%) |
| Union of the two | 539 | 539 (100.0%) | 523 (97.0%) |

- Methods: 474 exact normalized names, 57 counties by name, 1 consolidated city-county (San Francisco), and 7 hand-checked aliases.
- 16 cities never appear in any BPS place file from 2010 to 2025 (15 with HCD Table A2 rows, 1 compilation only): Biggs, Buellton, Calipatria, Clayton, Etna, Exeter, Farmersville, Fort Bragg, Fort Jones, Lafayette, Montague, Moraga, Nevada City, Orinda, Point Arena, Tehama.
- 12 Table A2 names are missing from the compilation; 5 compilation names have no A2 rows: Industry, Laguna Woods, Rancho Santa Margarita Margarita, Tehama, Vernon.
<!-- /generated:crosswalk -->

- The aliases are VENTURA → San Buenaventura (Ventura), PASO ROBLES → El Paso de Robles, CATHEDRAL → Cathedral City, ANGELS CAMP → Angels, AMADOR → Amador City, CARMEL → Carmel-by-the-Sea, and the compilation typo "RANCHO SANTA MARGARITA MARGARITA". Nothing is fuzzy-matched. Presence in each source is in `in_hcd_apr` and `in_compilation`.
- BPS unincorporated rows (`99990`) and whole-county rows (Alpine, `00000`) map to `<county>_UNINC`. Mountain House's BPS rows (2024–2025) are folded into San Joaquin County's remainder and flagged, because HCD has no Mountain House report.
- Loyalton (Sierra County) is in the Census universe but has no row in Table A2 or in the compilation.

### Cities with no BPS place row (S6)

BPS has no place row for these cities in any year. Each BPS county file equals the sum of its place rows in every county-year (`c_bps_county_vs_places.csv`), so BPS publishes nothing for them *separately*. That does not mean BPS misses their permits: where a county issues building permits for a small city under contract, BPS would count them in the county's unincorporated row. The independent review notes that several of them contract building permits to their county (for example Lafayette, Orinda, Moraga and Clayton in Contra Costa; Etna, Fort Jones and Montague in Siskiyou), but contract status was not verified here. This is a hypothesis, tested in `c_bps_missing_cities_fold.csv`: add the cities' HCD units to the county remainder's HCD units in the years the remainder is fully reported, and see whether HCD/BPS moves toward 1.

<!-- generated:fold -->
| County remainder | BPS-missing cities | Full years | Cities' HCD non-ADU units | HCD / BPS total, full years | Same, all years with both | HCD SF / BPS 1-unit, full years | Corr. of BPS excess with cities' HCD | Fold supported |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Butte County | Biggs | 2 | 0 | 0.40 → 0.40 | 0.56 → 0.56 | 0.40 → 0.40 | — | no |
| Contra Costa County (holdout) | Clayton, Lafayette, Moraga, Orinda | 8 | 559 | 0.47 → 0.60 | 0.47 → 0.60 | 0.44 → 0.56 | 0.49 | yes |
| Imperial County | Calipatria | 7 | 12 | 0.96 → 1.02 | 0.96 → 1.02 | 0.59 → 0.66 | -0.38 | yes |
| Mendocino County | Fort Bragg, Point Arena | 3 | 37 | — → — | 1.16 → 1.39 | — → — | — | no |
| Nevada County | Nevada City | 8 | 75 | 0.28 → 0.32 | 0.28 → 0.32 | 0.26 → 0.28 | 0.16 | yes |
| Santa Barbara County | Buellton | 8 | 245 | 0.73 → 0.86 | 0.73 → 0.86 | 0.65 → 0.69 | 0.84 | yes |
| Siskiyou County (holdout) | Etna, Fort Jones, Montague | 5 | 5 | 0.70 → 0.73 | 0.59 → 0.61 | 0.72 → 0.75 | -0.12 | yes |
| Tehama County (holdout) | Tehama | 2 | 0 | 0.61 → 0.61 | 0.39 → 0.39 | 0.62 → 0.62 | — | no |
| Tulare County | Exeter, Farmersville | 8 | 190 | 0.59 → 0.69 | 0.59 → 0.69 | 0.58 → 0.62 | 0.20 | yes |
<!-- /generated:fold -->

"Fold supported" means the folded HCD/BPS ratio is closer to 1 than the unfolded one. Where it is supported, the remainder's BPS numerator probably includes the cities while its ACS denominator (county minus incorporated places) does not, so the numerator and denominator do not match. Butte (Biggs) and Tehama (Tehama city) have no city HCD units to fold. In Mendocino's fully reported years BPS shows no units for the remainder, and over all years folding moves its ratio away from 1, so it is not folded. Every affected remainder carries `bps_may_include_cities = True` in the panel and the crosswalk, whether or not the fold is supported. For Gate 3: for BPS-based measures, either fold these cities into their county remainder (where supported) or exclude the affected remainders. Contra Costa, Siskiyou and Tehama remainders are holdout jurisdictions.

## Pre-registered holdout (plan, "Held-out data")

`reference/ca_holdout_jurisdictions.csv`: jurisdictions held out with seed 20261024. The universe is Census geography, not the set of jurisdictions with data: the TIGER 2024 incorporated places (including San Francisco), Mountain House, and the county remainders, sorted by `census_geoid`. The draw uses `numpy.random.default_rng(20261024).choice` without replacement.

<!-- generated:holdout -->
| Holdout | Count |
|---|---:|
| Universe (Census geography, sorted by `census_geoid`) | 540 |
| Drawn (seed 20261024) | 108 |
| … cities (incl. San Francisco) | 99 |
| … county remainders | 9 |
| … with any HCD or compilation data (effective holdout) | 107 |
| … with HCD Table A2 rows | 106 |
| Held out with no Table A2 rows | Loyalton (no data at all), Vernon |
<!-- /generated:holdout -->

- **What is evidenced:** the draw uses identifiers only and a fixed seed, and it reproduces exactly. A rebuild redraws it and refuses to overwrite the file if membership ever differs; this check runs on every build. The revised build reproduced the saved membership exactly.
- **What is not claimed:** that the draw predates every look at step 0 data. Earlier development builds of step 0 ran before the final build, and file times reflect only the last rebuild. Since the revision, the build writes the holdout file before any other output, and the manifest's `outputs_in_write_order` records that sequence for that build only.
- **Effective holdout (N3).** The effective holdout is the jurisdictions with any data (see table). The file's `method` column is kept as drawn; the added columns `has_hcd_a2_data`, `has_hcd_or_compilation_data` and `method_note` correct the wording "that reports to HCD".
- **Use:** holdout jurisdictions' data were in the pooled step 0 tables before this revision and have been viewed for data quality. From here on they are excluded from every model-feeding estimate (computed on non-holdout only), and they must be dropped from any Gate 3 file before fitting.

## Statewide BPS per 1,000 homes, Wisconsin and California

`reference/ca_wi_statewide_bps_per_1000.csv` gives BPS total units (estimates including imputation) per 1,000 PEP housing units, July 1 of the same year. Denominators come from PEP Vintage 2020 for 2010–2019 and Vintage 2025 for 2020–2025. Each state is indexed to its own 2014–2016 mean (= 100). The file also carries 1-unit, 2–4 and 5+ units and reported-only totals. These are state totals and include holdout jurisdictions (`includes_holdout_jurisdictions`); the plan uses them as a descriptive statewide view. No divergence is attributed or interpreted here (Gate 3).

<!-- generated:statewide_bps -->
| Year | 2010 | 2014 | 2016 | 2018 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CA units / 1,000 homes | 3.19 | 6.02 | 7.29 | 7.99 | 7.36 | 8.22 | 8.25 | 7.57 | 6.82 | 6.93 |
| CA index | 47 | 89 | 108 | 118 | 108 | 121 | 122 | 112 | 101 | 102 |
| WI units / 1,000 homes | 4.14 | 5.50 | 7.19 | 7.05 | 7.77 | 9.23 | 7.58 | 7.67 | 8.45 | 9.00 |
| WI index | 65 | 87 | 114 | 111 | 123 | 146 | 120 | 121 | 133 | 142 |
<!-- /generated:statewide_bps -->

## Step 0 findings

Unless stated otherwise, the tables use jurisdiction-years that are **fully reported in both sources**: HCD filed Table A2 rows, and BPS reported all 12 months for every BPS row of the jurisdiction.

<!-- generated:full_reporting -->
| Sample | Fully reported jurisdictions a year | Jurisdiction-years 2018–2025 |
|---|---:|---:|
| Non-holdout (used for any model-facing figure) | 295–366 | 2,682 |
| All jurisdictions | 369–455 | 3,327 |
<!-- /generated:full_reporting -->

### (a) HCD non-ADU units (SFD+SFA+2–4+5+) vs BPS total units

<!-- generated:table_a -->
| Year | Jurisdictions | HCD primary | HCD as reported | HCD dedup | BPS total | Primary / BPS | Reported / BPS | Dedup / BPS | (Primary+MH) / BPS | Primary / BPS, all juris. | Dedup / BPS, all juris. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 295 | 71,453 | 72,789 | 85,490 | 77,709 | 0.92 | 0.94 | 1.10 | 0.94 | 0.91 | 1.07 |
| 2019 | 351 | 89,879 | 104,255 | 95,314 | 88,224 | 1.02 | 1.18 | 1.08 | 1.04 | 0.99 | 1.05 |
| 2020 | 309 | 67,908 | 86,278 | 74,296 | 73,287 | 0.93 | 1.18 | 1.01 | 0.95 | 0.93 | 1.01 |
| 2021 | 352 | 92,902 | 111,406 | 100,211 | 96,153 | 0.97 | 1.16 | 1.04 | 0.99 | 0.96 | 1.05 |
| 2022 | 366 | 91,322 | 112,559 | 94,894 | 96,395 | 0.95 | 1.17 | 0.98 | 0.96 | 0.96 | 1.01 |
| 2023 | 329 | 71,958 | 86,507 | 77,315 | 78,415 | 0.92 | 1.10 | 0.99 | 0.94 | 0.91 | 0.97 |
| 2024 | 334 | 58,393 | 82,841 | 59,487 | 71,262 | 0.82 | 1.16 | 0.83 | 0.83 | 0.82 | 0.83 |
| 2025 | 346 | 68,602 | 91,469 | 68,181 | 78,415 | 0.87 | 1.17 | 0.87 | 0.89 | 0.89 | 0.89 |

Non-holdout, fully reported in both sources. Using every jurisdiction-year with BPS imputation, primary / BPS is 0.83 to 1.00 (non-holdout) and 0.84 to 0.97 (all jurisdictions) (`a_nonadu_by_year.csv`).
<!-- /generated:table_a -->

- The as-reported HCD totals overstate permitting from 2019 on, because of the repeated listings. Counting each permit once in its issue year brings HCD close to BPS through 2023. The 2024–2025 shortfall fits permits that will only be reported late.

<!-- generated:table_a_top50 -->
- **Top 50 jurisdictions by housing units** (`a_nonadu_top50.csv`, pooled over full-reporting years), primary / BPS: non-holdout median 0.94; 25 of 39 within 0.80–1.25; all 50 median 0.95; 33 of 50 within 0.80–1.25.
- City of Los Angeles: 1.04 under the primary measure, 1.75 as reported. Other large non-holdout jurisdictions: San Diego 0.99, San Jose 0.86, San Francisco 1.30, Fresno 0.99, Irvine 0.95, Oakland 1.17.
- Non-holdout top-50 jurisdictions where HCD runs well below BPS (below 0.70): Torrance 0.29, Sonoma County 0.47, Riverside County 0.63, Santa Cruz County 0.63, San Diego County 0.65.
- Holdout jurisdictions in the top 50 (flagged `in_holdout` in the CSV; their ratios are not summarised here): 11 (Sacramento, Glendale, El Dorado County, Santa Rosa, Contra Costa County, Fresno County, Elk Grove, Ontario, San Joaquin County, Berkeley, Santa Clara).
<!-- /generated:table_a_top50 -->

<!-- generated:table_a_county -->
- County sums of full-reporting jurisdiction-years, primary / BPS (`a_nonadu_by_county.csv`; descriptive, includes holdout jurisdictions): Los Angeles 0.94, Riverside 0.82, San Diego 0.90, Orange 0.92, Santa Clara 0.87, San Francisco 1.30. Los Angeles County as reported: 1.44.
- Mendocino's 11.65 reflects BPS reporting only 31 units in its full-reporting jurisdiction-years.
- With the HCD units of BPS-missing cities folded into the county where the fold test supports it (`ratio_hcd_primary_to_bps_folded`): Contra Costa 0.82 → 0.85, Tulare 0.91 → 0.92, Santa Barbara 0.81 → 0.85, Nevada 0.62 → 0.64, Imperial 0.91 → 0.92, Siskiyou 0.73 → 0.75.
<!-- /generated:table_a_county -->

- **Largest jurisdiction-year mismatches** (`a_nonadu_largest_mismatches.csv`, all jurisdictions, descriptive):

<!-- generated:table_a_mismatches -->
- Los Angeles 2022: HCD 20,461 (31,407 as reported) vs BPS 16,707.
- Santa Clara County 2019: HCD 2,563 (2,563 as reported) vs BPS 50.
- Irvine 2024: HCD 1,456 (1,456 as reported) vs BPS 3,730.
- Riverside County 2023: HCD 901 (905 as reported) vs BPS 3,107.
- San Diego 2023: HCD 7,783 (7,783 as reported) vs BPS 5,765.
- Manteca 2021: HCD 2,695 (2,695 as reported) vs BPS 711.
- San Francisco 2023: HCD 2,765 (2,765 as reported) vs BPS 1,136.
- Riverside County 2022: HCD 788 (806 as reported) vs BPS 2,280.
<!-- /generated:table_a_mismatches -->

  Most of these look like timing (multi-building projects permitted in different years) or one-source reporting gaps rather than definitional differences.

### (b) Where ADUs land in BPS

<!-- generated:table_b -->
| Year | BPS 1-unit | HCD SFD+SFA | HCD ADU | BPS1 / SF | BPS1 / (SF+ADU) | BPS 2–4 / HCD 2–4 | BPS1 / SF, all juris. | BPS1 / (SF+ADU), all juris. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 39,526 | 32,338 | 6,976 | 1.22 | 1.01 | 1.00 | 1.25 | 1.05 |
| 2019 | 43,902 | 36,262 | 11,358 | 1.21 | 0.92 | 0.91 | 1.21 | 0.95 |
| 2020 | 37,200 | 28,722 | 9,592 | 1.30 | 0.97 | 1.10 | 1.28 | 0.99 |
| 2021 | 51,700 | 45,281 | 16,528 | 1.14 | 0.84 | 1.02 | 1.17 | 0.86 |
| 2022 | 49,776 | 36,068 | 21,476 | 1.38 | 0.87 | 1.15 | 1.41 | 0.90 |
| 2023 | 42,532 | 30,441 | 19,676 | 1.40 | 0.85 | 1.18 | 1.36 | 0.84 |
| 2024 | 44,272 | 29,759 | 21,674 | 1.49 | 0.86 | 1.01 | 1.45 | 0.86 |
| 2025 | 42,437 | 29,617 | 26,101 | 1.43 | 0.76 | 1.20 | 1.40 | 0.77 |

Non-holdout, fully reported in both sources.
<!-- /generated:table_b -->

Neither version tracks cleanly. The level comparison is confounded by a single-family gap with no ADUs in it: in fully reported jurisdiction-years with **zero** HCD ADUs, BPS 1-unit still runs above HCD SFD+SFA. Netting out that baseline gives `implied share = (BPS 1-unit − baseline × HCD SF) / HCD ADU`. That share, and the regression coefficients, move a great deal with reasonable choices (`b_adu_share_sensitivity.csv`, `b_one_unit_baseline_adjusted.csv`, `b_adu_placement_regressions.csv`):

<!-- generated:b_sensitivity -->
| Specification (share of HCD ADUs inside BPS 1-unit) | Non-holdout | Baseline jurisdiction-years, baseline ratio | All jurisdictions |
|---|---:|---:|---:|
| Baseline-adjusted, primary measure | 0.24 | 474, 1.19 | 0.23 |
| Baseline-adjusted, issue-year dedup measure | 0.22 | 443, 1.14 | 0.21 |
| Baseline-adjusted, as reported measure | 0.09 | 436, 1.10 | 0.07 |
| Jurisdiction-cluster bootstrap, primary: median [95% interval] | 0.22 [-0.22 to 0.68] |  | 0.20 [-0.17 to 0.56] |
| Jurisdiction-cluster bootstrap, issue-year dedup: median [95% interval] | 0.22 [-0.20 to 0.64] |  | 0.19 [-0.13 to 0.56] |
| Jurisdiction-cluster bootstrap, as reported: median [95% interval] | 0.08 [-0.27 to 0.46] |  | 0.06 [-0.25 to 0.37] |
| Excluding City of Los Angeles, primary | 0.26 |  | 0.24 |
| Excluding City of Los Angeles, issue-year dedup | 0.28 |  | 0.26 |
| Excluding City of Los Angeles, as reported | 0.15 |  | 0.12 |
| Baseline only from places with ≥ 5,000 one-unit detached homes | 0.30 | 188, 1.16 | 0.27 |
| Baseline only from places with ≥ 10,000 one-unit detached homes | 0.42 | 98, 1.10 | 0.38 |
| Baseline only from places with ≥ 20,000 one-unit detached homes | 0.57 | 42, 1.03 | 0.52 |
| (Median one-unit detached homes in the zero-ADU baseline places) | 3,097 |  | 3,078 |
| Baseline and share for 2018 only | -0.14 | 105, 1.25 | 0.07 |
| Baseline and share for 2019 only | 0.11 | 99, 1.18 | 0.08 |
| Baseline and share for 2020 only | 0.45 | 70, 1.15 | 0.11 |
| Baseline and share for 2021 only | 0.76 | 55, 0.86 | 0.74 |
| Baseline and share for 2022 only | -0.10 | 52, 1.44 | -0.03 |
| Baseline and share for 2023 only | 0.45 | 36, 1.11 | 0.42 |
| Baseline and share for 2024 only | -0.67 | 34, 1.98 | -0.19 |
| Baseline and share for 2025 only | -1.07 | 23, 2.38 | -0.93 |
| Regression ADU coefficient, pooled, no intercept; full-reporting (HCD SF coefficient 1.02) | 0.25 [0.24 to 0.27] |  | 0.26 [0.24 to 0.27] |
| Regression ADU coefficient, within-jurisdiction; full-reporting (HCD SF coefficient 0.52) | 0.32 [0.29 to 0.35] |  | 0.31 [0.28 to 0.34] |
| Regression ADU coefficient, jurisdiction + year FE; full-reporting (HCD SF coefficient 0.52) | 0.32 [0.29 to 0.35] |  | 0.31 [0.28 to 0.35] |
| Regression ADU coefficient, pooled, no intercept; excl. City of Los Angeles (HCD SF coefficient 1.02) | 0.33 [0.29 to 0.38] |  | 0.36 [0.31 to 0.40] |
| Regression ADU coefficient, within-jurisdiction; excl. City of Los Angeles (HCD SF coefficient 0.52) | 0.16 [0.10 to 0.22] |  | 0.13 [0.07 to 0.19] |
| Regression ADU coefficient, jurisdiction + year FE; excl. City of Los Angeles (HCD SF coefficient 0.52) | 0.15 [0.08 to 0.21] |  | 0.13 [0.07 to 0.20] |

Across these non-holdout specifications the central values run from 0.09 to 0.57; year-by-year values run from -1.07 to 0.76, with 23–105 baseline jurisdiction-years a year. Regression intervals use classical standard errors and are too narrow for clustered data; the bootstrap interval is the honest one.
<!-- /generated:b_sensitivity -->

**Reading (B1).** The statewide share of HCD-reported ADUs that BPS counts as 1-unit is **not identified**. It is plausibly anywhere from about 0 to about 0.5, and it is heavily jurisdiction-specific. No single value is offered:

- The jurisdiction-cluster bootstrap interval includes 0 and reaches well past 0.5.
- The as-reported measure gives a much lower share than the primary and dedup measures.
- The zero-ADU baseline comes from small places. Taking it only from larger places lowers the baseline and raises the implied share steadily.
- Computed year by year, the share swings from negative to large, and few zero-ADU jurisdiction-years remain in recent years.
- In the regressions, within-jurisdiction BPS 1-unit does not track HCD SF one for one (SF coefficient well below 1), so the ADU coefficient is weakly identified. Excluding Los Angeles moves it in opposite directions in the pooled and fixed-effect versions.

**Carry no point value into Gate 3.** If an ADU-share model is applied to BPS totals, treat inclusion as a range with bounds of 0 and 0.5, or use only jurisdictions whose practice is identified (the three below appear to be about 0).

**Place-specific pattern (descriptive, non-holdout top 50).** These are descriptive associations, not a model of reporting:

<!-- generated:b_place_pattern -->
- **Appear to exclude ADUs from BPS 1-unit:** Los Angeles (BPS1 / SF 1.94, BPS1 / (SF+ADU) 0.40, BPS total / HCD non-ADU 0.96); San Diego (BPS1 / SF 1.37, BPS1 / (SF+ADU) 0.48, BPS total / HCD non-ADU 1.01); San Francisco (BPS1 / SF 0.95, BPS1 / (SF+ADU) 0.08, BPS total / HCD non-ADU 0.77). BPS1 / (SF+ADU) is far below 1, and BPS totals are near HCD non-ADU units alone. Los Angeles holds 30% of HCD ADUs in the full-reporting sample.
- **Appear to include ADUs in BPS 1-unit** (non-holdout top 50, BPS1 / SF ≥ 2.5 while BPS total / HCD non-ADU is within 0.80–1.25): Fremont (BPS1 / SF 2.62, BPS1 / (SF+ADU) 0.82, BPS total / HCD non-ADU 1.11); Oakland (BPS1 / SF 2.66, BPS1 / (SF+ADU) 0.44, BPS total / HCD non-ADU 0.86); San Jose (BPS1 / SF 2.99, BPS1 / (SF+ADU) 0.82, BPS total / HCD non-ADU 1.17); Santa Ana (BPS1 / SF 3.32, BPS1 / (SF+ADU) 0.88, BPS total / HCD non-ADU 0.83); Long Beach (BPS1 / SF 3.62, BPS1 / (SF+ADU) 0.53, BPS total / HCD non-ADU 1.13).
- **BPS1 / SF ≥ 2.5 but more likely an HCD reporting gap** (BPS total also runs far above HCD non-ADU): Santa Cruz County (BPS1 / SF 2.89, BPS1 / (SF+ADU) 1.11, BPS total / HCD non-ADU 1.57); Sonoma County (BPS1 / SF 3.04, BPS1 / (SF+ADU) 1.87, BPS total / HCD non-ADU 2.12); Torrance (BPS1 / SF 4.91, BPS1 / (SF+ADU) 0.83, BPS total / HCD non-ADU 3.50). Torrance in particular reports far fewer non-ADU units to HCD than BPS shows, so its high BPS1 / SF says little about ADUs.
- 5 holdout jurisdictions in the top 50 also have BPS1 / SF ≥ 2.5; they stay in `b_one_unit_top50.csv` (flagged) and are not used.
- Among the 39 non-holdout top-50 jurisdictions, BPS 1-unit is closer in level to SF+ADU in 23 and to SF alone in 16; over time it correlates better with SF+ADU in 22 of 38.
<!-- /generated:b_place_pattern -->

For Wisconsin this means BPS one-unit counts may contain some ADUs, by an unidentified, place-specific fraction that depends on each permit office's practice. How to read this is a Gate 3 decision.

### (c) Coverage

<!-- generated:table_c -->
| Year | Both sources | HCD only (BPS absent or 0 months) | BPS only (no HCD A2 rows) | HCD: A2 rows | HCD: filed, no A2 rows | HCD: no record | BPS places with 12 / 0 / partial months | BPS imputed share of units |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 423 | 58 | 48 | 481 | 37 | 20 | 411 / 51 / 60 | 5.8% |
| 2019 | 436 | 59 | 33 | 495 | 25 | 18 | 469 / 53 / 0 | 3.7% |
| 2020 | 431 | 70 | 26 | 501 | 21 | 16 | 405 / 63 / 52 | 10.5% |
| 2021 | 435 | 66 | 29 | 501 | 23 | 14 | 464 / 55 / 0 | 4.8% |
| 2022 | 455 | 48 | 27 | 503 | 24 | 11 | 482 / 37 / 0 | 3.6% |
| 2023 | 457 | 47 | 22 | 504 | 23 | 11 | 427 / 40 / 52 | 5.9% |
| 2024 | 455 | 49 | 21 | 504 | 16 | 18 | 436 / 43 / 41 | 6.7% |
| 2025 | 458 | 47 | 27 | 505 | 17 | 16 | 456 / 34 / 30 | 7.0% |

All jurisdictions (descriptive). HCD-only jurisdiction-years hold 34,668 non-ADU and 8,776 ADU permits; BPS-only years hold 9,779 BPS units. Imputed BPS units are 3.6%–10.5% of the state total in 2018–2025.
<!-- /generated:table_c -->

- "Filed, no A2 rows" means the jurisdiction has rows in Table A or D but none in A2. That can mean no reportable activity or an incomplete report.
- "No record" means no rows in Tables A, A2 or D: missing or not yet processed. The full list is in `c_apr_not_filed_or_no_a2.csv`.
- **Late filing cannot be observed**, because the open data carry no submission date.
- The largest one-source-only jurisdiction-years are in `c_one_source_only.csv`; most HCD-only years are years where BPS shows 0 months reported.
- In 2019, 2021 and 2022, BPS months reported are coded only as 0 or 12.

### (d) 2012–2019 compilation vs HCD APR, overlap 2018–2019

<!-- generated:table_d -->
| Year (sample) | Compilation rows | Compilation total | APR ADU as reported, same jurisdictions | APR ADU, primary | Rows exactly equal to APR as reported | Within ±10% or ±2 | Correlation | Compilation 0 where APR > 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 (all) | 527 | 8,900 | 8,992 | 8,913 | 491 / 527 | 507 | 0.999 | 14 |
| 2019 (all) | 527 | 14,702 | 15,071 | 12,707 | 485 / 527 | 498 | 1.000 | 19 |
| 2018 (non-holdout) | 420 | 8,049 | 8,058 | 7,981 | 393 / 420 | 404 | 0.999 | 9 |
| 2019 (non-holdout) | 420 | 13,483 | 13,809 | 11,612 | 384 / 420 | 396 | 1.000 | 18 |

Compilation relative to APR (all jurisdictions): 2018: -1.0% against as-reported, -0.1% against primary; 2019: -2.4% against as-reported, 15.7% against primary.
<!-- /generated:table_d -->

The compilation is essentially HCD's own as-reported APR ADU counts from an earlier data vintage. The break at 2018 is therefore small against as-reported APR. Against the primary measure it is large in 2019, almost all from Los Angeles re-listing permits.

- Largest row differences are in `d_compilation_vs_apr_largest_diffs.csv`.
- The compilation has zeros where APR now shows ADUs, and no case the other way (last column above). APR data were revised upward after the compilation was made.
- Pre-2018 compilation years cannot be checked against APR. They inherit the as-reported definition, and possibly the same re-listing behaviour.
- The sheet has a side block (columns K–S) with a second SACRAMENTO COUNTY series and the compiler credit. It is recorded in the manifest and not used.

## Limitations

- "Fully reported in both" is a selected sample. Statewide ratios on it are not statewide totals.
- The primary APR measure drops late first reports of earlier permits, and the dedup measure keeps them. The permit key relies on tracking id, APN, address and date. If a jurisdiction changes its tracking-id format between years, a repeat will look like a new permit, so repeats are undercounted.
- The step 0 ADU-placement evidence is associational and, statewide, does not identify a share (see (b)). ADU growth coincides with other construction trends, and the zero-ADU baseline comes mostly from small places.
- ACS denominators are 2020–2024 averages, with calculated remainder MOEs that ignore covariance. Mountain House and any later incorporation are inside county remainders, and some remainders' BPS counts probably include contract-permitted cities (S6).
- The compilation has no license and an undated vintage. It is used descriptively with attribution (AQ-017).
- Not done here, by design: groups, wave comparisons, rates per 1,000 by group, ramp, spillover.

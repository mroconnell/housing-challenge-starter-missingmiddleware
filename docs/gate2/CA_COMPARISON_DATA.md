# California comparison data and step 0 reconciliation

Gate 2 addendum, built 2026-10-24. Assembles the inputs for the pre-registered California comparison study ([plan](../gate3/CA_COMPARISON_PLAN.md), AQ-017, AQ-031) and runs **step 0 only**: a data-quality reconciliation of Census BPS against HCD APR. **Nothing here computes the study**: no permissive or restrictive groups, no comparisons around reform waves, no ramp or spillover estimates. The 20% holdout was drawn from jurisdiction identifiers alone, before any ADU rate by group was computed.

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
uv run python scripts/build_ca_comparison_data.py     # fetch (skips files present) + build + step 0
uv run python scripts/build_ca_comparison_data.py --skip-fetch      # rebuild offline
bash scripts/test.sh                                  # includes tests/test_ca_comparison.py (13 tests)
```

The whole build runs in about 12 s once the raw files are present. Code: `missing_middleware/comparison/ca_sources.py` (register, downloader, CKAN queries), `ca_inputs.py` (readers), `ca_crosswalk.py` (crosswalk and holdout), `ca_step0.py` (reconciliation and statewide series).

## Outputs

`data/processed/comparison_ca/` (git-ignored; parquet plus a CSV copy):

| File | Grain | Contents |
|---|---|---|
| `hcd_apr_a2_juris_year_unitcat` | HCD jurisdiction × report year × UNIT_CAT (13,018 rows) | `bp_units_primary`, `bp_units_reported`, and the components between them: `_date_missing`, `_date_earlier_repeat`, `_date_earlier_late_first`, `_date_later`. Also `ent_units`, `co_units`, `dem_units`, `project_rows`. |
| `hcd_apr_a2_issue_year_dedup` | jurisdiction × **permit issue year** × UNIT_CAT | Each permit counted once, in the year it was issued (alternative measure) |
| `hcd_apr_filing_status` | jurisdiction × year 2018–2025 (538 × 8) | `a2_rows` / `filed_no_a2_rows` / `no_record`, with flags for presence in Tables A, A2 and D |
| `adu_compilation_2012_2019` | jurisdiction × year (527 × 8) | ADU permits; a blank cell is `missing`, not zero |
| `ca_denominators_acs2024` | 482 incorporated places + 57 county remainders | ACS total units and one-unit detached homes, with MOEs |
| `ca_jurisdiction_crosswalk` | HCD/compilation name (539) | `census_geoid`, `placefp`, `county_fips`, `bps_ids`, `match_method` |
| `step0_juris_year_panel` | census_geoid × year 2018–2025 (4,244 rows) | HCD units by category under all three measures, BPS units by size class (estimated and reported-only), months reported, filing status, ACS denominators |
| `step0/*.csv` | | The reconciliation tables below |

`reference/` (committed; small; no personal data): `ca_jurisdiction_crosswalk.csv`, `ca_holdout_jurisdictions.csv`, `ca_wi_statewide_bps_per_1000.csv`.

### Which APR columns count as "permits issued"

The building-permit measure is `NO_BUILDING_PERMITS` ("Total number of units issued building permits in the project"). On all 926,774 rows it equals the sum of the 11 `BP_*_INCOME_*` columns, which the build asserts. Entitlements use `NO_ENTITLEMENTS` and completions use `NO_OTHER_FORMS_OF_READINESS` (certificates of occupancy or similar). Both are kept as separate fields, summed over all rows of the report.

**Repeated listings, a finding that matters.** In 90,758 rows carrying permits (213,842 units, 18% of all reported permitted units), the `BP_ISSUE_DT1` date falls in a year before the report year. About 98,600 of those units belong to a permit that the same jurisdiction also lists in its permit-year report, typically again when the certificate of occupancy is issued. Summing `NO_BUILDING_PERMITS` by report year therefore double counts. The City of Los Angeles accounts for about 100,600 of the 213,842 units. Three measures are kept, and the primary measure was chosen before any comparison with BPS:

- **`bp_units_primary`** (primary): units whose permit date falls in the report year, plus 46 units with no date. This matches the APR definition "issued this year".
- **`bp_units_reported`**: everything as published, for example in HCD's dashboard totals.
- **`bp_units_issue_year_dedup`**: each permit key counted once, in its issue year. This also catches permits first reported late, but recent issue years will rise as later reports arrive.

The datastore API matches the CSV in all 48 year × UNIT_CAT cells (row counts and permitted units).

Statewide HCD permitted units under the primary measure (with as-reported totals for ADUs):

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

The 2018 issue-year count includes permits issued in 2018 but first reported in 2019 or later.

### Denominators

ACS 2020–2024 B25024 rows: E001 is total units and E002 is one-unit detached. Cities use summary level 160, filtered to incorporated places (TIGER 2024 `CLASSFP` C1, `FUNCSTAT` A, 482 places including San Francisco). Each **county remainder** is the county total (050) minus the sum of its incorporated-place parts (155), so it includes every CDP. Its MOE is the root-sum-of-squares approximation, and its status is `calculated`. San Francisco has no remainder. California county subdivisions (summary level 060) are census county divisions, which are not governments and match no HCD jurisdiction, so they are not used. No California city crosses a county line (the 155 parts confirm this). Check: places plus remainders give 6,515,600 + 1,838,868 = 8,354,468 one-unit detached homes, equal to the state total. Mountain House incorporated on 2024-07-01, after the 2024 geography date. It is a CDP in ACS and TIGER, so it sits inside the San Joaquin remainder.

## Crosswalk

| | Names | Matched to Census | Matched to BPS place ids |
|---|---:|---:|---:|
| HCD APR Table A2 jurisdictions | 534 | 534 (100%) | 518 (97.0%) |
| Compilation rows | 527 | 527 (100%) | 523 |
| Union of the two | 539 | 539 | 523 (97.0%) |

- Methods: 474 exact normalized names, 57 counties by name, 1 consolidated city-county (San Francisco), and 7 hand-checked aliases. The aliases are VENTURA → San Buenaventura (Ventura), PASO ROBLES → El Paso de Robles, CATHEDRAL → Cathedral City, ANGELS CAMP → Angels, AMADOR → Amador City, CARMEL → Carmel-by-the-Sea, and the compilation typo "RANCHO SANTA MARGARITA MARGARITA". Nothing is fuzzy-matched.
- The 12 Table A2 names missing from the compilation and the 5 compilation names with no A2 rows (Industry, Laguna Woods, Tehama, Vernon, plus the typo row) are flagged in `in_hcd_apr` and `in_compilation`.
- **16 cities never appear in any BPS place file from 2010 to 2025:** Biggs, Buellton, Calipatria, Clayton, Etna, Exeter, Farmersville, Fort Bragg, Fort Jones, Lafayette, Montague, Moraga, Nevada City, Orinda, Point Arena, Tehama. Each BPS county file equals the sum of its places in every county-year (0 differences), so BPS does not count these cities' permits anywhere visible. HCD has their reports.
- BPS unincorporated rows (`99990`) and whole-county rows (Alpine, `00000`) map to `<county>_UNINC`. Mountain House's BPS rows (2024–2025) are folded into San Joaquin County's remainder and flagged, because HCD has no Mountain House report.
- Loyalton (Sierra County) is in the Census universe but has no row in Table A2 or in the compilation.

## Pre-registered holdout (plan, "Held-out data")

`reference/ca_holdout_jurisdictions.csv`: **108 of 540** jurisdictions held out, with seed **20261024**. The universe is the 482 TIGER-2024 incorporated places (including San Francisco), Mountain House, and the 57 county remainders, sorted by `census_geoid`. The draw uses `numpy.random.default_rng(20261024).choice` without replacement. It yielded 99 cities and 9 county remainders. It was drawn from identifiers only, in the build step after the crosswalk and before any step 0 table. A rebuild reproduces the same draw and refuses to overwrite the file if the draw ever differs.

## Statewide BPS per 1,000 homes, Wisconsin and California

`reference/ca_wi_statewide_bps_per_1000.csv` gives BPS total units (estimates including imputation) per 1,000 PEP housing units, July 1 of the same year. Denominators come from PEP Vintage 2020 for 2010–2019 and Vintage 2025 for 2020–2025. Each state is indexed to its own 2014–2016 mean (= 100). The file also carries 1-unit, 2–4 and 5+ units and reported-only totals. This is descriptive only: no divergence is attributed or interpreted here (Gate 3).

| Year | 2010 | 2014 | 2016 | 2018 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CA units / 1,000 homes | 3.19 | 6.02 | 7.29 | 7.99 | 7.36 | 8.22 | 8.25 | 7.57 | 6.82 | 6.93 |
| CA index | 47 | 89 | 108 | 118 | 108 | 121 | 122 | 112 | 101 | 102 |
| WI units / 1,000 homes | 4.14 | 5.50 | 7.19 | 7.05 | 7.77 | 9.23 | 7.58 | 7.67 | 8.45 | 9.00 |
| WI index | 65 | 87 | 114 | 111 | 123 | 146 | 120 | 121 | 133 | 142 |

## Step 0 findings

Unless stated otherwise, the tables use jurisdiction-years that are **fully reported in both sources**: HCD filed Table A2 rows, and BPS reported all 12 months for every BPS row of the jurisdiction. This covers 369–455 jurisdictions a year, 3,327 jurisdiction-years in all. "All" rows add BPS imputation and HCD jurisdictions with missing BPS data.

### (a) HCD non-ADU units (SFD+SFA+2–4+5+) vs BPS total units

| Year | Jurisdictions (full) | HCD primary | HCD as reported | HCD issue-year dedup | BPS total | Primary / BPS | Reported / BPS | Dedup / BPS | (Primary+MH) / BPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 368 | 85,037 | 86,473 | 99,902 | 93,305 | 0.91 | 0.93 | 1.07 | 0.93 |
| 2019 | 436 | 104,328 | 120,559 | 110,408 | 105,301 | 0.99 | 1.14 | 1.05 | 1.01 |
| 2020 | 379 | 79,684 | 99,599 | 87,080 | 85,957 | 0.93 | 1.16 | 1.01 | 0.95 |
| 2021 | 435 | 107,916 | 127,180 | 118,143 | 112,746 | 0.96 | 1.13 | 1.05 | 0.98 |
| 2022 | 455 | 110,072 | 135,876 | 115,864 | 115,063 | 0.96 | 1.18 | 1.01 | 0.97 |
| 2023 | 406 | 84,777 | 103,719 | 90,668 | 93,515 | 0.91 | 1.11 | 0.97 | 0.92 |
| 2024 | 417 | 68,297 | 96,759 | 69,488 | 83,352 | 0.82 | 1.16 | 0.83 | 0.83 |
| 2025 | 430 | 80,861 | 105,699 | 80,440 | 90,805 | 0.89 | 1.16 | 0.89 | 0.90 |

Using all jurisdictions, with BPS imputation, the primary/BPS ratios are 0.84–0.97 (`a_nonadu_by_year.csv`).

- The as-reported HCD totals overstate permitting by 11–18% from 2019 on, because of the repeated listings. Counting each permit once in its issue year matches BPS within ±7% in 2018–2023. The 2024–2025 shortfall (0.83–0.89) fits permits that will only be reported late.
- **Top 50 jurisdictions by housing units** (`a_nonadu_top50.csv`, pooled over full-reporting years): median primary/BPS ratio 0.95; 33 of 50 fall within 0.80–1.25. City of Los Angeles: 1.04 under the primary measure, 1.75 as reported. Other large jurisdictions: San Diego 0.99, San Jose 0.86, San Francisco 1.30, Sacramento 1.03, Fresno 0.99, Irvine 0.95, Oakland 1.17. HCD runs well below BPS in several county remainders: Riverside 0.63, San Diego County 0.65, Contra Costa 0.47, Sonoma 0.47. Torrance is at 0.29.
- **Counties** (`a_nonadu_by_county.csv`): Los Angeles County 0.94 (1.44 as reported), Riverside 0.82, San Diego 0.90, Orange 0.92, Santa Clara 0.87, San Francisco 1.30. Mendocino's 11.6 reflects BPS reporting only 31 units in its unincorporated area.
- **Largest jurisdiction-year mismatches** (`a_nonadu_largest_mismatches.csv`):
  - Los Angeles 2022: HCD 20,461 (31,407 as reported) vs BPS 16,707.
  - Santa Clara County 2019: 2,563 vs 50.
  - Irvine 2024: 1,456 vs 3,730.
  - Riverside County 2020, 2022 and 2023: HCD about 1,400–2,200 below BPS each year.
  - Manteca 2021: 2,695 vs 711.
  - San Francisco 2023: 2,765 vs 1,136.

  Most of these look like timing (multi-building projects permitted in different years) or one-source reporting gaps rather than definitional differences.

### (b) Where ADUs land in BPS

| Year | BPS 1-unit | HCD SFD+SFA | HCD ADU | BPS1 / SF | BPS1 / (SF+ADU) | BPS 2–4 / HCD 2–4 |
|---|---:|---:|---:|---:|---:|---:|
| 2018 | 50,238 | 40,371 | 7,642 | 1.24 | 1.05 | 1.01 |
| 2019 | 55,359 | 45,604 | 12,380 | 1.21 | 0.95 | 0.94 |
| 2020 | 45,287 | 35,358 | 10,598 | 1.28 | 0.99 | 1.12 |
| 2021 | 61,964 | 52,792 | 19,093 | 1.17 | 0.86 | 1.03 |
| 2022 | 60,387 | 42,870 | 24,473 | 1.41 | 0.90 | 1.17 |
| 2023 | 49,498 | 36,353 | 22,636 | 1.36 | 0.84 | 1.20 |
| 2024 | 52,107 | 35,965 | 24,593 | 1.45 | 0.86 | 1.05 |
| 2025 | 49,667 | 35,439 | 29,166 | 1.40 | 0.77 | 1.21 |

Neither version tracks cleanly. The level comparison is confounded by a single-family gap with no ADUs in it. In the 606 full-reporting jurisdiction-years with **zero** HCD ADUs, BPS 1-unit still runs 1.20 × HCD SFD+SFA. Netting out that baseline:

| Sample | BPS 1-unit | HCD SF | HCD ADU | Implied share of HCD ADUs inside BPS 1-unit |
|---|---:|---:|---:|---:|
| All, 2018–2025 | 425,101 | 325,199 | 150,710 | **0.23** |
| Excluding City of Los Angeles | 402,500 | 313,557 | 105,171 | **0.24** |
| City of Los Angeles | 22,601 | 11,642 | 45,539 | 0.19 under primary SF; about 0 against LA's as-reported SF (20,124) |

Regressions of BPS categories on HCD categories (`b_adu_placement_regressions.csv`, 3,327 jurisdiction-years; standard errors in the file) show where ADUs go:

| BPS outcome | ADU coefficient, pooled | Within-jurisdiction | Jurisdiction + year FE | Same, excluding LA city |
|---|---:|---:|---:|---:|
| 1-unit (with HCD SF) | 0.26 | 0.31 | 0.32 | 0.13 (pooled 0.36) |
| 2–4 units (with HCD 2–4) | 0.05 | 0.03 | 0.03 | 0.18 |
| Total units (with HCD non-ADU) | 0.20 | 0.04 | 0.04 | 0.67 (pooled 0.64) |

**Reading.** The statewide answer is that BPS 1-unit counts include **roughly a quarter of HCD-reported ADUs**: 0.23–0.24 net of baseline, and 0.13–0.36 across regression specifications. Practice differs a great deal by jurisdiction:

- **Little or no ADU inclusion:** the City of Los Angeles (30% of the state's ADUs), San Francisco and San Diego. Their BPS totals track HCD non-ADU units alone: LA 0.96, San Diego 1.01.
- **ADUs apparently inside BPS 1-unit:** San Jose, Santa Ana, Fremont, Torrance, Berkeley, Glendale and Long Beach, where BPS 1-unit exceeds HCD SF by 2.6–9×.
- Among the top 50, BPS 1-unit is closer in level to SF+ADU in 32 cases and to SF alone in 18. Over time it correlates better with SF+ADU in 25 of 48.

Outside Los Angeles, about 0.6 of HCD ADUs appear somewhere in BPS totals, spread across the 1-unit, 2–4 and (implausibly, probably through shared trends) 5+ categories. These are descriptive associations, not a model of reporting.

For Wisconsin this means BPS one-unit counts may contain some ADUs, and the share depends on each permit office's practice. An ADU-share model applied to BPS totals could double count by a modest, place-specific fraction. How to read this is a Gate 3 decision.

### (c) Coverage

| Year | Both sources | HCD only (BPS absent or 0 months) | BPS only (no HCD A2 rows) | HCD: A2 rows | HCD: filed, no A2 rows | HCD: no record | BPS places with 12 / 0 / partial months | BPS imputed share of units |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| 2018 | 423 | 58 | 48 | 481 | 37 | 20 | 411 / 51 / 60 | 5.8% |
| 2019 | 436 | 59 | 33 | 495 | 25 | 18 | 469 / 53 / 0 | 3.7% |
| 2020 | 431 | 70 | 26 | 501 | 21 | 16 | 405 / 63 / 52 | 10.5% |
| 2021 | 435 | 66 | 29 | 501 | 23 | 14 | 464 / 55 / 0 | 4.8% |
| 2022 | 455 | 48 | 27 | 503 | 24 | 11 | 482 / 37 / 0 | 3.6% |
| 2023 | 457 | 47 | 22 | 504 | 23 | 11 | 427 / 40 / 52 | 5.9% |
| 2024 | 455 | 49 | 21 | 504 | 16 | 18 | 436 / 43 / 41 | 6.7% |
| 2025 | 458 | 47 | 27 | 505 | 17 | 16 | 456 / 34 / 30 | 7.0% |

- "Filed, no A2 rows" means the jurisdiction has rows in Table A or D but none in A2. That can mean no reportable activity or an incomplete report.
- "No record" means no rows in Tables A, A2 or D: missing or not yet processed. Examples:
  - Patterson: 2018–2024.
  - California City: 5 years.
  - Banning: 5 years.
  - Amador City: 2018–2022.
  - Pomona: 2022, 2024, 2025.
  - Full list in `c_apr_not_filed_or_no_a2.csv`.
- **Late filing cannot be observed**, because the open data carry no submission date.
- HCD-only jurisdiction-years hold 34,668 non-ADU and 8,776 ADU permits. The largest are San Joaquin County, Bakersfield, Long Beach, Mountain View and Napa, mostly years where BPS shows 0 months reported.
- BPS-only years hold 9,714 BPS units. The largest are Pomona, Banning, Fontana 2020 and South Gate.
- Inside BPS, imputed units (estimate minus reported) are 3.6–10.5% of the state total from 2018 to 2025. In 2019, 2021 and 2022, months reported are coded only as 0 or 12.

### (d) 2012–2019 compilation vs HCD APR, overlap 2018–2019

| Year | Compilation total (527 rows) | APR ADU as reported, same jurisdictions | APR ADU, primary | Rows exactly equal to APR as reported | Within ±10% or ±2 | Correlation |
|---|---:|---:|---:|---:|---:|---:|
| 2018 | 8,900 | 8,992 | 8,913 | 491 / 527 | 507 | 0.999 |
| 2019 | 14,702 | 15,071 | 12,707 | 485 / 527 | 498 | 1.000 |

The compilation is essentially HCD's own as-reported APR ADU counts from an earlier data vintage. City of Los Angeles 2019: 6,747 in both. The break at 2018 is therefore small against as-reported APR (−1% in 2018, −2.4% in 2019). Against the primary measure it is +16% in 2019, almost all from Los Angeles re-listing permits.

- Largest row differences: San Francisco 2018 (404 vs 272); Carson, Palm Springs and Alhambra 2019 (0 in the compilation vs 30–46 in APR).
- The compilation has 14 (2018) and 19 (2019) zeros where APR now shows ADUs, and no case the other way. APR data were revised upward after the compilation was made.
- Pre-2018 compilation years cannot be checked against APR. They inherit the as-reported definition, and possibly the same re-listing behaviour.
- The sheet has a side block (columns K–S) with a second SACRAMENTO COUNTY series (35 in 2018, 27 in 2019) and the compiler credit. It is recorded in the manifest and not used.

## Limitations

- "Fully reported in both" is a selected sample (369–455 of about 538 jurisdictions a year). Statewide ratios on it are not statewide totals.
- The primary APR measure drops late first reports of earlier permits (about 108,000 units in 2018–2025), and the dedup measure keeps them. The permit key relies on tracking id, APN, address and date. If a jurisdiction changes its tracking-id format between years, a repeat will look like a new permit, so repeats are undercounted.
- The step 0 ADU-placement evidence is associational. ADU growth coincides with other construction trends (the negative and positive 5+ coefficients show this), and the zero-ADU baseline comes mostly from small places.
- ACS denominators are 2020–2024 averages, with calculated remainder MOEs that ignore covariance. Mountain House and any later incorporation are inside county remainders.
- The compilation has no license and an undated vintage. It is used descriptively with attribution (AQ-017).
- Not done here, by design: groups, wave comparisons, rates per 1,000 by group, ramp, spillover.

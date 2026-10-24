# Data Provenance

Document every dataset your tool uses. The code license does **not** relicense data—each dataset carries its own terms, and you are responsible for them. Do not commit raw or large data to the repository; describe how to obtain it here and keep only small samples in `data/sample/`.

# Dataset Inventory

Complete one row per dataset.

| Dataset | Source | Version / vintage | Access date | License / terms | Category |
| ------- | ------ | ----------------- | ----------- | --------------- | -------- |
| ACS 5-year detailed tables B25024, B25002, B25034, B01003 | U.S. Census Bureau, [table-based summary file](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/) | ACS 2020–2024 5-year | 2026-10-23 | Public domain (17 U.S.C. §105); Census terms of service | Public |
| TIGER/Line boundaries: state, county, county subdivision, place, tract, block group | U.S. Census Bureau, [TIGER2024](https://www2.census.gov/geo/tiger/TIGER2024/) | 2024 (boundaries as of 2024-01-01) | 2026-10-23 | Public domain | Public |
| Cartographic CBSA boundaries (metro/micro type only) | U.S. Census Bureau, [cb_2024_us_cbsa_20m.zip](https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_cbsa_20m.zip) | 2024 (July 2023 OMB delineations) | 2026-10-23 | Public domain | Public |
| County housing-unit estimates (CO-EST2025-HU-55) | U.S. Census Bureau, [Population Estimates Program](https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx) | Vintage 2025, July 1 2020–2025 | 2026-10-23 | Public domain | Public |
| Building Permits Survey annual files: state, county, Midwest places | U.S. Census Bureau, [BPS](https://www2.census.gov/econ/bps/) | Annual 2015–2025 (2025 final) | 2026-10-23 | Public domain | Public |
| Building permit Construction Summary report | City of Madison Building Inspection, [report](https://cityreports.cityofmadison.com/CityReports/ReportViewer/ReportViewer/?ReportPath=/Web%20Access/Building/Permits/Construction%20Summary) | Issue dates 2010-01-01 to 2026-10-23 | 2026-10-23 | No open-data license stated; public-records report. Cite the city. Record-level extracts are not redistributed. | Third-party (local government) |
| Tax parcels and address points | City of Madison, [OPEN_DATA2/FeatureServer/0](https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA2/FeatureServer/0) and [OPEN_DATA/MapServer/20](https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/20) | Current snapshot at access | 2026-10-23 | City of Madison open data terms | Third-party (local government) |
| California ADU permits by city, 2012–2019 | [BuildinganADU.com compilation](https://docs.google.com/spreadsheets/d/10rb8p7DU379vQw9oeS_Z9dwK9F9c5ZBeTw09wQlvwQY/edit) of California HCD data, linked from [buildinganadu.com/california-adu-charts](https://www.buildinganadu.com/california-adu-charts) | Static, 2012–2019 | 2026-10-23 | No license stated. Cite BuildinganADU.com as compiler and HCD as upstream source. | Third-party |
| California Housing Element Annual Progress Report (APR) tables | California HCD, [California Open Data Portal](https://data.ca.gov/) | 2018 onward | See [hcd_apr.meta.json](../data/sample/hcd_apr.meta.json) | California open data terms (see dataset page) | Third-party (state government, not a challenge state) |
| California ADU Reform: A Retrospective (report, cited for its compilation choices) | M. Nolan Gray, California YIMBY, [PDF](https://cayimby.org/wp-content/uploads/2024/01/CAY-ADU_Report-2024-v4.pdf) | January 2024 | 2026-10-23 | Cited, not redistributed | Third-party |
| Madison ADU permits by year | Team-created from the Madison permit report: [reference/madison_adu_permits_by_year.csv](../reference/madison_adu_permits_by_year.csv) | Built 2026-10-23 | n/a | Apache-2.0 (repository); upstream terms above | Team-created |

Each source has a data dictionary with fields and sample rows in [docs/data-sources/](data-sources/README.md). That folder also covers candidate sources the tool does not use yet. Exact files, byte counts and SHA-256 checksums are recorded at download time in `data/raw/<source_id>/_downloads.json` (Census) and `data/raw/madison_*/manifest.json` (Madison); see [Gate 2 foundation](gate2/FOUNDATION.md#sources) and [Madison permits](gate2/MADISON_PERMITS.md).

Categories:

- **Public** — nationally available public datasets (e.g., Census/ACS, BLS).
- **State-provided** — datasets supplied by participating states for the challenge.
- **Third-party** — commercial, nonprofit, academic, or online sources.
- **Team-created** — datasets you built or materially modified.

# Cleaning and Preparation

- **Census foundation** ([details](gate2/FOUNDATION.md)): keep Wisconsin rows from the national ACS files; join ACS to TIGER 2024 by GEOID (all 1,925 county subdivisions, 1,542 tracts and 4,692 block groups match); compute margins of error for derived sums; crosswalk BPS jurisdictions to municipalities (95.2% direct match in 2025, the rest to county unincorporated rows).
- **Madison permits** ([details](gate2/MADISON_PERMITS.md)): keep rows whose permit number matches `^BLD[A-Z]{3}-\d{4}-\d+$`; drop owner and contractor columns at ingestion; drop duplicate reissued permits; classify ADUs from description keywords; match street addresses to city address points to reach parcels.
- **California 2012–2019 series** ([AQ-017](ASSUMPTIONS_AND_QUESTIONS.md)): statewide totals are team sums of the 527 published jurisdiction rows. For 2018 onward, prefer HCD APR data and keep both versions.

# Known Limitations

- 724 Wisconsin towns (22% of one-unit detached homes) have no BPS row of their own; their permits appear only in county unincorporated rows.
- ACS 5-year estimates average 2020–2024 and carry margins of error. PEP housing-unit estimates measure net stock change, not new construction.
- Madison permits have no ADU flag, no application or final dates, and free-text unit suffixes, so ADU counts depend on the keyword rules.
- The California 2012–2019 series is a third-party compilation. Early zeros are reported values, and it holds permits only, not completions.
- TIGER 2024 boundaries match the ACS release. Joining 2026 parcels or boundaries will need a documented crosswalk.

# Restricted, Sensitive, or Personal Data

The Madison permit report includes owner names and mailing addresses. The pipeline drops those columns at ingestion and never writes them to disk outside `data/raw/`, which is git-ignored. Street addresses are kept only for internal matching to parcels and are not published; outputs are counts by year and area. The committed samples in `data/sample/` replace owner and mailing fields with `[redacted]`, and a test checks this. No restricted-use data is used: HUD/USPS vacancy data was excluded because access is limited to government and nonprofit users.

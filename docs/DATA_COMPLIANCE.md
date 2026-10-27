# Data Compliance Audit

Prepared 2026-10-25. This audit checks every dataset the project uses or commits a sample of (Gates 1–3) against the challenge's data rules in [CHALLENGE_HANDBOOK.md](CHALLENGE_HANDBOOK.md#data-rules-rules-7biii-handbook) and [CHALLENGE_SPEC.md](CHALLENGE_SPEC.md). Sources, versions and access dates are in [DATA_PROVENANCE.md](DATA_PROVENANCE.md). Licenses are also listed in [DISCLOSURES.md](DISCLOSURES.md#third-party-datasets).

## Criteria

1. **Terms.** The terms were checked and recorded. Datasets with no use restrictions are preferred. Paid or proprietary data is allowed only if access continues and it stays free to end users. ToS that bar scraping or redistribution, share-alike terms (for example ODbL) and Google Sheets compilations are flagged.
2. **Not committed.** Large source data is not in git.
3. **Automatic fetch.** The pipeline fetches the data from the authoritative source with minimal manual steps. Flagged: values that were hand-transcribed or read from a PDF or image, `source_lead` news or vendor figures, and anything behind a login or reached by scraping a report UI (Power BI, SmartGov, SSRS) that may break.
4. **No PII.** No sensitive, confidential, restricted-use or personally identifiable data is committed. Committed files must drop house numbers, owner names and unmasked parcel numbers. This covers `data/sample/`, `reference/`, `tests/fixtures/` and the sample tables in `docs/data-sources/`.
5. **Recorded.** Source, version, access date, license, cleaning steps and limitations are written down.
6. **Disclosed.** The dataset is listed in DISCLOSURES.md as a third-party dataset with its license.

**Status values:**
- **Pass**: meets the criterion.
- **Fix**: a known gap. The numbered fix list below says what to do.
- **Owner**: needs an owner decision. The decision codes (D1–D6) are listed below the table.
- **n/a**: does not apply. For example, a source that is cited but whose data the tool does not use.

## Checks run

- **Git size (criterion 2).**
  - `git ls-files` holds no raw source files: no PDF, XLSX, ZIP, Parquet or shapefile data. The only PDF is `docs/CHALLENGE_HANDBOOK.pdf`.
  - Nothing under `data/` is tracked except `data/README.md`, `data/DATA_SOURCES.md` and `data/sample/`.
  - Over the whole git history, no file outside `data/sample/` was ever committed under `data/`.
  - The largest blobs ever committed are derived tables: `reference/pooled_wi_y_by_area.csv` (690,252 bytes) and `reference/wi_y_by_area.csv` (667,616 bytes). They are model outputs by area, not source data.
  - The biggest raw input, `data/raw/hcd_apr_a2/tablea2.csv` (294,538,874 bytes), is git-ignored.
- **Owner names (criterion 4).**
  - Every owner, co-owner and mailing-address field in the committed samples reads `[redacted]` or is empty: CT CAMA, WI V-series, WI V12, PA PASDA, Madison. A unit test covers this (`tests/test_data_sources.py`).
  - The same holds in every earlier version of those files in git history. **No owner names were found in git history.**
  - The Oregon GEOHub `ownerName` field holds public bodies only (for example "Baker County").
- **House numbers and parcel numbers (criterion 4).**
  - Every committed record-level sample now keeps the street name only, masks parcel and record ids to their first 2 characters plus `***`, and rounds coordinates: Madison, Pleasant Prairie, Sun Prairie, V12, AZ, CT, OR Metro, NH, UT parcels and housing units, PA, VA, HI, WI V-series and HCD APR. Parcel outlines in `data/sample/geo/` are replaced by a coarse box. See fix F1 (done).
  - `tests/test_sample_privacy.py` scans every file in `data/sample/` and `docs/data-sources/` for house-number-plus-street patterns and long parcel ids, and checks id columns, coordinates and parcel geometry.
  - **The unmasked values are still in git history**, from the first sample commits (`50ade76`, `ea91bcd`) up to the commit before the F1 fix. This audit does not rewrite history; that is an owner decision.
- **Reference tables and fixtures (criterion 4).**
  - `reference/*.csv` holds only aggregates by area, jurisdiction or year. No column carries an address, permit number, APN or name of a person.
  - `tests/fixtures/` is synthetic throughout: "TESTOWNER", "FAKE RD", "1 FAKE ST", APNs like `000-000-001` and `111-222`, Milwaukee rows on "MAIN" and "OAK". The new `tests/fixtures/madison_like/` files are synthetic too: places "Midtown city" and "X County", and made-up APNs.
  - A scan of all history of `reference/` and `tests/fixtures/` found one address-like string, `500 E LAKE DR`, in a synthetic Milwaukee fixture.
- **Raw permit files.** These hold owner, applicant or contractor names: Madison, Pleasant Prairie, De Pere, Howard and Watertown. They stay in git-ignored `data/raw/`, and loaders drop those fields.

## Audit table

Statuses are in the order (1) Terms · (2) Not committed · (3) Automatic fetch · (4) No PII · (5) Recorded · (6) Disclosed.

### Gate 1–2 sources used by the pipeline

| Dataset | (1) | (2) | (3) | (4) | (5) | (6) | Notes |
|---|---|---|---|---|---|---|---|
| ACS 5-year tables (B25024, B25002, B25034, B01003; market tables B19013, B25003, B25064, B25077) | Pass | Pass | Pass | Pass | Pass | Pass | Public domain; `scripts/build_foundation.py` downloads them |
| TIGER/Line 2024, CBSA cartographic file | Pass | Pass | Pass | Pass | Pass | Pass | |
| Census PEP housing units (WI, CA; V2020, V2025) | Pass | Pass | Pass | Pass | Pass | Pass | |
| Census BPS state, county, place files (WI and CA) | Pass | Pass | Pass | Pass | Pass | Pass | |
| Madison Construction Summary permit report | Owner (D1) | Pass | Owner (D3) | Pass | Pass | Pass | SSRS report-viewer export, which may break; site ToS not checked. Sample keeps street names only |
| Madison tax parcels and address points | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Terms recorded only as "City of Madison open data terms". Parcel numbers masked in the sample |
| Pleasant Prairie SmartGov issued-permits report | Owner (D1) | Pass | Owner (D3) | Pass | Pass | Pass | Parsed from a SmartGov RTF export |
| Sun Prairie Power BI submitted-permits report | Owner (D1) | Pass | Owner (D3) | Pass | Pass | Pass | Read through the Power BI querydata API; it may break if the report changes |
| V12 statewide parcels (Kenosha and Dane pieces) | Pass | Pass | Pass | Pass | Pass | Pass | Owner fields never requested; sample masked |
| BuildinganADU.com California ADU compilation 2012–2019 | Owner (D4) | Pass | Pass | Pass | Pass | Pass | A Google Sheets compilation with no license stated. Fetched automatically by CSV export |
| HCD APR tables (A, A2, D: aggregates and project rows) | Fix (F5) | Pass | Pass | Pass | Pass | Pass | The data.ca.gov metadata reads "License not specified"; DATA_PROVENANCE now says so. Sample and `hcd_apr.meta.json` masked (F1): street names only, APNs and tracking ids masked, project names dropped, latitude and longitude rounded to 2 decimals. The 294 MB raw file is git-ignored |
| CA YIMBY ADU retrospective (Nolan Gray, 2024) | n/a | Pass | n/a | Pass | Pass | Pass | Cited only |
| Wisconsin ADU rules, 37 municipalities (`wi_adu_rules.csv`, `wi_rights_exposure.csv`) | Owner (D4) | Pass | Owner (D6) | Pass | Pass | Pass | Hand-coded from codes. The 20 rows that cited the commercial Zoneomics mirror now cite official text (D4, done 2026-10-25); rows cite Municode, ecode360, Legistar, Granicus or city sites, whose site terms were not checked |
| Team tables: Madison, Pleasant Prairie, Sun Prairie ADU series | Pass | Pass | Pass | Pass | Pass | n/a | Team-created (Apache-2.0) |

### Gate 1 candidate sources (committed samples only; not used by the pipeline)

| Dataset | (1) | (2) | (3) | (4) | (5) | (6) | Notes |
|---|---|---|---|---|---|---|---|
| BLS CES/PPI, BLS QCEW, FHFA HPI, NTD, USGS NLCD | Pass | Pass | Pass | Pass | Pass | Pass | Public domain; sample rows only |
| NASA MODIS land cover | Pass | Pass | Pass | Pass | Pass | Pass | |
| Microsoft Global ML Building Footprints | Owner (D5) | Pass | Pass | Pass | Pass | Pass | ODbL, which is share-alike for derived databases |
| Google Open Buildings | Owner (D5) | Pass | Pass | Pass | Pass | Pass | CC BY 4.0 or ODbL; covers no U.S. state |
| HUD/USPS vacancy | Pass | Pass | n/a | Pass | Pass | Pass | Restricted-use data; excluded and not fetched |
| Tennessee Comptroller parcels | Pass | Pass | n/a | Pass | Pass | Pass | Manual request only; not fetched |
| Arizona AZGeo parcels | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Sample masked (F1) |
| Connecticut CAMA and parcels | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Owner fields redacted; sample masked (F1) |
| Oregon Metro RLIS taxlots | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Sample masked (F1). RLIS terms not recorded |
| Oregon GEOHub parcels and zoning | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Owner names are public bodies |
| Hawaii statewide parcels | Fix (F5) | Pass | Pass | Pass | Pass | Pass | TMKs masked; plat and parcel fields dropped (F1) |
| Pennsylvania PASDA catalog and county parcels | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Sample masked (F1) |
| Utah Housing Unit Inventory | Fix (F5) | Pass | Pass | Pass | Pass | Pass | |
| Utah statewide parcels (LIR) | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Sample masked (F1) |
| Virginia VGIN parcels | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Sample masked (F1) |
| Wisconsin V-series statewide parcels | Pass | Pass | Pass | Pass | Pass | Pass | Owner fields redacted; sample masked (F1) |
| Rhode Island RIGIS land use | Fix (F5) | Pass | Pass | Pass | Pass | Pass | |
| New Hampshire GRANIT parcels | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Sample masked (F1) |
| Madison zoning districts; WI Assembly districts | Pass | Pass | Pass | Pass | Pass | Pass | |

### Gate 3 sources

| Dataset | (1) | (2) | (3) | (4) | (5) | (6) | Notes |
|---|---|---|---|---|---|---|---|
| Census 2020 place-code files; IPEDS HD2023 | Pass | Pass | Fix (F3) | Pass | Pass | Pass | No fetch step in `build_madison_like.py` or `build_statewide_states.py`; the files were downloaded by hand into `data/raw/` |
| Census BPS, PEP and TIGER inputs for California | Pass | Pass | Pass | Pass | Pass | Pass | `build_ca_comparison_data.py` fetches them |
| Washington OFM permits by structure type | Fix (F5) | Pass | Fix (F2) | Pass | Pass | Pass | Counts transcribed into `SERIES`. `madison_like` reads the XLSX, but nothing fetches it |
| Oregon DLCD HB 4006 summaries | Fix (F5) | Pass | Fix (F2) | Pass | Pass | Pass | PDF tables; `SERIES` transcribed; `madison_like` parses them with pdftotext |
| NH OPD housing supply CSV and report | Fix (F5) | Pass | Fix (F2) | Pass | Pass | Pass | CSV column summed by hand into `SERIES` |
| Rhode Island EOH annual ADU reports | Fix (F5) | Pass | Fix (F2) | Pass | Fix (F4) | Pass | Blocked to scripts (HTTP 403); read through a text-fetch service; hand-transcribed. URL of the 2025 report not recorded |
| Massachusetts EOHLC ADU Tracker; Boston Indicators report | Fix (F5) | Pass | Fix (F2) | Pass | Fix (F4) | Pass | Dashboard; tracker URL not recorded |
| Maine MOCA 2025 housing data summary | Fix (F5) | Pass | Fix (F2) | Pass | Fix (F4) | Pass | PDF; URL not recorded |
| Utah DWS MIH compiled reports | Fix (F5) | Pass | Fix (F2) | Pass | Pass | Pass | Counts parsed from PDF text by a regex parser that lives in a scratchpad, not in the repo |
| Vermont CCRPC Chittenden ADU inventory (and DHCD layer, unused) | Fix (F5) | Pass | Fix (F2) | Pass | Pass | Pass | Aggregate API query not in a build script; transcribed |
| Honolulu permits; Montgomery County permits | Fix (F5) | Pass | Fix (F2) | Pass | Pass | Pass | Socrata aggregate queries not in a build script; transcribed |
| Bozeman ADU applications table | Fix (F5) | Pass | Fix (F2) | Pass | Fix (F4) | Pass | URL not recorded |
| News and vendor figures (`source_lead`: Portland ME, Tucson, Colorado Springs, Phoenix vendor) | Owner (D4) | Pass | Fix (F2) | Pass | Fix (F4) | Pass | Third-party; article URLs not recorded; low weight by design |
| Mercatus 2025 taxonomy; Peterson reform matrix; vendor law trackers | Pass | Pass | n/a | Pass | Pass | Pass | Cited, not redistributed |
| Statute, session-law and ordinance pages (states and cities) | Pass | Pass | Owner (D6) | Pass | Pass | Pass | Public law; hand-coded by design; URL on every row |
| Seattle building permits (Socrata) | Pass | Pass | Pass | Pass | Pass | Pass | Public domain; `build_other_cities.py --fetch` |
| Seattle OPCD 2024 ADU annual report | Owner (D1) | Pass | Fix (F2) | Pass | Pass | Pass | The PDF is fetched, but the Exhibit 10 values are typed into `other_cities.py` |
| Portland BDS residential permits; demolition permits | Owner (D1) | Pass | Pass / Fix (F3) | Pass | Pass | Pass | No license on the item. The permits are fetched; the demolitions (madison_like) have no fetch step |
| Austin issued construction permits | Pass | Pass | Pass | Pass | Pass | Pass | Public domain |
| Denver residential construction and demolition permits | Fix (F5) | Pass | Pass / Fix (F3) | Pass | Pass | Pass | Use constraints "as stated" are not quoted. Demolitions have no fetch step |
| Minneapolis CCS permits | Fix (F5) | Pass | Pass / Fix (F3) | Pass | Pass | Pass | License name not recorded. New and wrecking permits (madison_like) have no fetch step |
| HCD APR Table A2 project-level rows | Fix (F5) | Pass | Pass | Pass | Pass | Pass | "License not specified". APN rows stay in `data/raw/`; outputs are aggregates |
| Terner TCRLUS 2018 | Fix (F5) | Pass | Pass | Pass | Pass | Pass | Fetched by `build_ca_ordinances.py` |
| HCD "ADU ordinances received" list (Wayback) | Owner (D2) | Pass | Pass | Pass | Pass | Pass | From an Internet Archive capture |
| CCI ADU Scorecard interim report; ADU California grades | Fix (F5) | Pass | Fix (F2) | Pass | Pass | Pass | Blocked to scripts (HTTP 403); text read through the Exa fetch service and not re-fetched. The test fixture `scorecard_appendix_c.md` is a short excerpt |
| Archived California ordinances (AQ-026, 73 places) | Owner (D2) | Pass | Owner (D6) | Pass | Pass | Pass | Hand-coded; Wayback and code-host terms not checked |
| Wisconsin DOA Land Regs Inventory; county and town zoning pages | Owner (D1, D2) | Pass | Pass | Pass | Pass | Pass | `build_wi_town_zoning.py --fetch` uses the Wayback copy. County spot checks were made by hand (84 rows verified) |
| Green Bay monthly reports; Brown County 2020 parcels | Owner (D1, D2) | Pass | Owner (D3) | Pass | Pass | Pass | Live site blocks scripts (Cloudflare), so Internet Archive copies are used. Open owner question, WI_RULES_VS_ACTIVITY.md §7 |
| De Pere monthly reports | Owner (D1) | Pass | Pass | Pass | Pass | Pass | Raw PDFs hold names and stay in `data/raw/` |
| Howard monthly reports | Owner (D1) | Pass | Pass | Pass | Pass | Pass | Needs `pdftotext` |
| Kaukauna council-packet inspection reports | Owner (D1) | Pass | Owner (D3), Fix (F6) | Pass | Pass | Pass | City site blocks scripts; reports read from Municode Meetings. Scanned pages need OCR with `tesseract` and the macOS-only `sips` |
| Neenah monthly activity reports | Owner (D1) | Pass | Pass | Pass | Pass | Pass | Through the WordPress media API |
| Verona annual construction reports | Owner (D1) | Pass | Pass | Pass | Pass | Pass | PDF parsed with `pdftotext -bbox` |
| Watertown monthly permit reports | Owner (D1) | Pass | Pass | Pass | Pass | Pass | Raw PDFs hold contractor names |
| Waunakee ArcGIS permits layer | Owner (D1) | Pass | Pass | Pass | Pass | Pass | OWNER field not requested |
| Milwaukee permits and MPROP | Pass | Pass | Pass | Pass | Pass | Pass | CC-BY; owner fields never loaded |
| Fitchburg building permit reports | Owner (D1) | Pass | Pass | Pass | Pass | Pass | Applicant fields never loaded |
| Team tables: `statewide_states_*`, `other_cities_*`, `pooled_*`, `statewide_adoption_curve`, `wi_town_zoning_status`, `wi_measured_permits_2022_2025`, `ca_*`, `wi_baseline_*`, `wi_rules_vs_activity_*`, `madison_like_*` | Pass | Pass | Fix (F2, F3) | Pass | Fix (F7) | n/a | Aggregates only. They inherit the fetch gaps of their inputs |

### Gate 5 sources

Added 2026-10-26. Both are fetched in full by `uv run python scripts/fetch_legislative_districts.py` into git-ignored `data/raw/<source_id>/`, with URL, access time, bytes and SHA-256 in each folder's `manifest.json`; source, vintage and terms are in [DATA_PROVENANCE.md](DATA_PROVENANCE.md).

| Dataset | (1) | (2) | (3) | (4) | (5) | (6) | Notes |
|---|---|---|---|---|---|---|---|
| Wisconsin State Assembly (99) and Senate (33) districts, 2024 plan (2023 Wisconsin Act 94), LTSB ArcGIS layers (`wi_assembly_districts`, `wi_senate_districts`) | Pass | Pass | Pass | Pass | Pass | Pass | Terms: "open and publicly available ... use at your own risk" (D1 applies). Raw layers stay in `data/raw/`. The tool's bundle carries copies simplified to 150 m with coordinates rounded to 4 decimals (`ui/public/runs/<run_id>/geo_assembly.json`, 143 KB; `geo_senate.json`, 95 KB): district outlines and numbers only, no other attributes |
| Census 2020 tabulation blocks for Wisconsin with 2020 housing-unit counts (TIGER2020 TABBLOCK20, `census_tiger_2020_tabblock`, 291 MB) | Pass | Pass | Pass | Pass | Pass | Pass | Public domain. Used only to split each municipality's single-family homes across districts (`scripts/build_district_allocation.py`); not committed. Committed outputs are area × district shares and district totals (`reference/adu_model_district_crosswalk.csv`, `adu_model_by_assembly_district.csv`, `adu_model_by_senate_district.csv`) |

### TOD cost-method reports (owner decision T5-3, AQ-055)

Added 2026-10-27. Two industry reports behind the set-aside cost-based method (method B). Both PDFs were fetched by hand with `curl` on 2026-10-26 into git-ignored `data/raw/tod_model/` (URL, bytes and SHA-256 in its `manifest.json`); no script downloads them. Their figures are typed into `scripts/run_tod_model.py`. They are used only for method B's diagnostics table, `reference/tod_model_feasibility.csv`, and the parameter table cites them; **no adopted number uses them**. The files are optional: without them `run_tod_model.py` skips that table with a printed note and writes every other output unchanged.

| Dataset | (1) | (2) | (3) | (4) | (5) | (6) | Notes |
|---|---|---|---|---|---|---|---|
| CBRE, U.S. Cap Rate Survey H1 2024 (Milwaukee multifamily infill, Class A stabilised: 5.5%–6%; midpoint 5.75% used) | Owner (D4) | Pass | Fix (manual, optional) | Pass | Pass | Pass | © CBRE. Copy hosted by a third party (taasinvestments.com), not by CBRE; one figure cited, file not redistributed |
| IREM, Income/Expense IQ National Summary 2024 (multifamily: $7,981.42 operating expenses and $20,575 gross rents per unit per year) | Owner (D4) | Pass | Fix (manual, optional) | Pass | Pass | Pass | © IREM. Public summary from irem.org; two figures cited, file not redistributed |

## Owner decisions

**Owner decisions (2026-10-25):**
- **Git history:** leave it; the masking holds from now on. Office-hours question 19.
- **D1:** yes, accept government records with no license stated as public records. Office-hours question 20.
- **D2:** yes, accept Internet Archive copies, with care: record the capture date and checksum, and prefer the live file whenever it exists. Office-hours question 21.
- **D3:** yes, keep the report screens, documented as fragile. Office-hours question 22.
- **D4:** yes, keep third-party compilations and figures as long as their terms allow our use. The BuildinganADU compilation is credited to HCD; the owner can ask its author for the original file. The Zoneomics rows (a commercial mirror) should cite the municipal code directly unless Zoneomics's terms allow this use. **Done 2026-10-25:** the terms do not allow it (see F5), so all 20 rows now cite official text; none is kept on Zoneomics. Details below the D4 question.
- **D5:** drop the building-footprint samples. Done: `SAMPLE_DROPPED` in `scripts/fetch_samples.py`.
- **D6:** yes, hand-coded rules are a documented manual step.

- **D1. Government records with no license stated.** Many city, county and state reports state no license (shown as "not stated" or "public record, no license stated"). Accept them as public records, cited with access dates, or ask each publisher?
- **D2. Internet Archive copies.** Accept Wayback copies in place of the live files? This covers Green Bay's reports, the DOA inventory (doa.wi.gov timed out), the HCD 2019 ordinance list and archived California ordinances.
- **D3. Report UIs that may break.** These sources are reached through report interfaces rather than open-data APIs: Madison's SSRS report viewer, Pleasant Prairie's SmartGov, Sun Prairie's Power BI, Kaukauna's Municode Meetings, and Green Bay (a site that blocks scripts). Keep them with a documented fallback (records request), or limit them to the pilot?
- **D4. Third-party compilations and vendor figures.**
  - BuildinganADU.com's Google Sheets compilation (no license).
  - The commercial Zoneomics code mirror cited in 20 rows of `wi_adu_rules.csv`.
  - News and vendor `source_lead` figures.
  - Options: keep them as cited third-party sources, or replace them with primary sources. The Zoneomics rows could cite the municipal code directly. The California compilation could be replaced by HCD APR for 2018 onward.
  - **Zoneomics rows, resolved 2026-10-25.** Zoneomics's terms (Terms of Use, "Last Revised: November 2020", zoneomics.com/terms-of-use, read 2026-10-25) allow personal, non-commercial use only. They bar reproducing, republishing or storing site material; using any robot or other automatic means to access the site; and republishing or redistributing its zoning data to third parties without written permission. They therefore do not cover our citing and coding from it, and the scanner's automated read of the Fond du Lac page breached the robot clause. The 20 rows of `wi_adu_rules.csv` that cited it (source rows in `reference/wi_adu_rules_spec.py`) now cite official text, re-read on 2026-10-25:
    - **New Berlin (8 rows), Beloit (7), Howard (3):** the Municode chapter, read in an ordinary browser (plain HTTP gets 403). Every coded value matches the official text, so the rows are now `verified` and the three places `coded_verified`. The ordinance_status notes for these places and Neenah (whose rows already cited Municode or a city PDF) say the code was re-read; Neenah is also `coded_verified` now.
    - **Fond du Lac (1 row, plus 7 rule rows whose text had been read through the mirror):** ecode360 shows a bot check, so the rules are read from Ord. 3809 in the city's 2025-02-26 council agenda packet on Granicus (§720-11C(29), pp. 37-39), adopted that night per the minutes. Values match; amendments after Ord. 3809 are not checked. The scanner target now points to that packet (`scripts/scan_adu_mentions.py`), and the Zoneomics target is removed.
    - **Waukesha (1 row, old Ch. 22 before 2026-09-01):** the repealed chapter is no longer online, so the row cites the city's Zoning Code Update Preliminary Recommendations Report (2024-12-30, Legistar), which says the current code does not allow ADUs. Section 22.24 itself was not re-read.
    - **Kept on Zoneomics:** none (0 of the 20 rows). The word survives only as provenance in notes: 8 of the 299 rule rows (Madison parking, Waukesha, Fond du Lac, New Berlin, Beloit, Howard and two Neenah rows) and the 4 Fond du Lac and New Berlin rows of `wi_rights_exposure.csv` (of 86) say a value was first read through the mirror. None cites it as a source.
    - **Coding difference found (not changed, owner to decide):** Beloit's official Ch. 19 allows "secondary dwelling units" (up to 800 sq ft) in the optional Traditional Neighborhood Development district (§5-701 to 5-703). That is a scanner term, so under the first-pass rule Beloit's `ordinance_status` would be `mentioned_allowed`, as Manitowoc's TND is, rather than `unmentioned`. The second-pass class (`restricted`) is not affected.
    - **Rebuilt:** `wi_adu_rules.csv` and `wi_rights_exposure.csv` (`scripts/build_reference_rules.py`, checked by `scripts/check_reference_rules.py`); `wi_rules_vs_activity_places.csv` (`class_basis` column only, `scripts/build_wi_more_cities.py`); `wi_baseline_*` rebuilt without change. Labels changed from 198 verified, 81 source lead and 20 unknown rule rows (of 299) to 226, 53 and 20; class basis from 23 to 28 `coded_verified` places (of 37). No value, date, class or flag changed.
- **D5. Share-alike building footprints.** Microsoft ML Building Footprints (ODbL) and Google Open Buildings appear only as samples. Drop the samples, or keep them with an ODbL note?
- **D6. Hand-coded rules.** Wisconsin and California ADU rules and state laws are coded by hand from official text, with a URL on every row. This cannot be automated. Accept it as a documented manual step?

## Fixes needed, ranked by risk

1. **F1: mask house numbers and parcel numbers in committed samples** (criterion 4). **Fixed in the committed files; the old values remain in git history.**
   - **What changed:** `ADDRESS_REDACTION` in `scripts/fetch_samples.py` now covers the AZ, CT, OR Metro, NH, UT parcels, UT housing units, PA, VA, HI and WI V-series samples and HCD APR, as well as Madison, Pleasant Prairie, Sun Prairie and V12. For each source it:
     - strips house and unit numbers from address fields and keeps the street name. An address that is only a house number becomes empty, and ZIP+4 is cut to 5 digits;
     - masks parcel, account and tracking ids to their first 2 characters plus `***`: APN, TMK, TLID, PIN, `PARCELID`, `STATEID`, CAMA links, HCD `JURS_TRACKING_ID` and the like. The earlier Madison, Pleasant Prairie, Sun Prairie and V12 masks hid only the last 4 characters; they now use the same shorter form;
     - empties row keys that a public layer query turns back into a parcel (`OBJECTID`, `FID`, `GlobalID`, HCD `_id`). It also empties deed book and page, the Hawaii plat and parcel parts and `qpub_link`, and HCD `PROJECT_NAME`;
     - rounds latitude and longitude to 2 decimals (about 1 km) and state-plane feet to the nearest 5,000 ft;
     - masks house numbers and parcel-style ids inside free text, such as HCD `NOTES` and `TRANSFERRED_TO`.
   - **Geometry:** a parcel outline locates one property exactly. So in every parcel and housing-unit sample in `data/sample/geo/`, each outline is replaced by its bounding box, widened outward to a 0.01-degree grid (about 1.1 km north to south). The box keeps the geometry type and a rough location. Point samples are rounded to 2 decimals. Zoning, land-use, district and building-footprint samples hold no records about a property and are unchanged. The data dictionaries give the vertex count of the source outline.
   - **How it was applied:** `python3 scripts/fetch_samples.py --remask` re-applied the masking to the files in place, with no network, through the same functions a fresh fetch uses. That includes the HCD APR sample rows for every table in `hcd_apr.meta.json`. `docs/data-sources/*.md` were then rebuilt with `scripts/build_data_dictionaries.py`.
   - **Test:** `tests/test_sample_privacy.py` scans `data/sample/` and `docs/data-sources/` for house-number-plus-street patterns and long parcel ids. The patterns include Utah grid addresses and Wisconsin `N123W456` numbers. It also checks that id columns are masked, coordinates are rounded and parcel geometry is coarsened.
   - **History:** the unmasked values are still in git history, from commits `50ade76` and `ea91bcd` onward until the commit that lands this fix. They are house-numbered addresses, full parcel ids, HCD latitude and longitude, and exact parcel outlines. Owner names are not in history. Whether to rewrite history is an owner decision and is still pending; this fix did not rewrite it.
   - **Left unmasked, for the owner to decide:** some attributes could narrow a sample row to one property when combined with the street name. Examples are exact parcel area (`Shape__Area`), sale date and price, and assessed values. Permit numbers in the Pleasant Prairie, Sun Prairie and Madison samples are also kept, as under the 2026-10-24 decision.
2. **F2: hand-transcribed values** (criterion 3; code change).
   - **Where:** `SERIES` in `missing_middleware/comparison/statewide_states.py` and the Seattle OPCD Exhibit 10 table in `other_cities.py` are typed in.
   - **Fetch and parse:** the OFM workbook (madison_like already parses it), the NH OPD CSV, and the Honolulu, Montgomery and CCRPC aggregate queries all have stable URLs and can be fetched and parsed.
   - **Commit the parser:** the Utah MIH regex parser is in a scratchpad and should be in the repo.
   - **Keep, but label:** the DLCD and Maine PDFs, the RI, MA and CCI pages blocked to scripts, and the news figures. Label them "transcribed" in the tables. Some of this labeling is already in `value_status`.
3. **F3: no fetch step for some raw inputs** (criterion 3; code change).
   - **Where:** `scripts/build_madison_like.py` and `scripts/build_statewide_states.py` read `data/raw/madison_like/` and `data/raw/statewide_states/`, but nothing downloads them. That covers the place codes, IPEDS, the Portland and Denver demolitions, Minneapolis new and wrecking permits, OFM, DLCD, NH, Utah, Vermont, Honolulu and Maryland.
   - **Fix:** add `--fetch` steps that write `_downloads.json`.
4. **F4: missing source URLs** (criterion 5).
   - **Missing:** exact URLs for the RI EOH 2025 report, the MA EOHLC tracker page, the Maine MOCA summary, the Bozeman table, and the news articles (Portland Press Herald 2026-05-07, Tucson Agenda, KOAA). They are not anywhere in the repo.
   - **Fix:** add them to `SERIES[...]["source"]` and to DATA_PROVENANCE.
5. **F5: terms not checked** (criterion 1).
   - **Record:** the license or terms page for each source marked "not stated", "see item page" or "see … terms". That covers OFM, DLCD, NH OPD, Utah DWS, CCRPC, Honolulu, Montgomery, Minneapolis, Portland, data.ca.gov, Terner, CCI, the state parcel portals and Madison open data. For Denver, quote its use constraints.
   - **Check:** Municode and ecode360 terms on automated access.
   - **Zoneomics: checked 2026-10-25.** Its Terms of Use allow personal, non-commercial use only and bar robots and any other automatic access, copying or storing pages, and republishing its data without written permission. The terms do not allow our use, so it is no longer cited (D4).
6. **F6: system tools not documented** (criterion 3; README, not edited here).
   - **The problem:** README.md says `pdftotext` is needed only for Howard. In fact six `wimc_*` adapters and `madison_like` use it. Kaukauna's OCR also needs `pdftoppm`, `tesseract` and macOS `sips`, so it does not run on Linux.
   - **Fix:** document the tools, and replace `sips` with a portable rotation.
7. **F7: no data dictionaries for Gate 3 sources** (criterion 5). Gate 3 sources have no page or sample in `docs/data-sources/`; that README now says so. Cleaning steps and limits are in the Gate 3 method docs.

**Doc-only fixes made with this audit:**
- **DATA_PROVENANCE.md:**
  - Gate 3 inventory rows.
  - Gate 3 cleaning and limitation bullets.
  - A corrected HCD APR license.
  - An honest note in the personal-data section on the unmasked samples.
- **DISCLOSURES.md:** a third-party dataset section with licenses.
- **docs/data-sources/README.md:** a note that Gate 3 sources have no dictionaries yet.

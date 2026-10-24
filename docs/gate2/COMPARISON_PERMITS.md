# Comparison-city permits: acquisition test, adapters, ADU-equivalent series

Gate 2 work package, built 2026-10-24; headline revised the same day after the addenda review (items S3, N6, N7, N10; see section 8). Code: `missing_middleware/permits/pleasant_prairie.py`, `sun_prairie.py`, `comparison.py` (shared parcel-number pieces). Build: `scripts/build_comparison_permits.py`. Tests: `tests/test_permits_comparison.py` (offline, synthetic fixtures in `tests/fixtures/permits/comparison/`). Sources and candidate search: [COMPARISON_CITY_SEARCH.md](COMPARISON_CITY_SEARCH.md). Madison method this follows: [MADISON_PERMITS.md](MADISON_PERMITS.md).

## Decision

**Pleasant Prairie is the restrictive pilot.** Both candidates downloaded by plain, scripted HTTP with no browser, so the owner's rule (2026-10-24: Pleasant Prairie preferred if both work) picks Pleasant Prairie. Howard stays a tested fallback (section 1). **Sun Prairie 2016–2025** is added as the same-market historical restrictive check against Madison.

**Bottom line.**
- Pleasant Prairie: every issued permit from 2003-10-03 to 2026-10-24 was downloaded: 22,390 permits in 24 yearly files. New one- and two-family units match Census BPS within −4% to +9% in every year 2015–2025.
- Sun Prairie: all 26,342 submitted records 2015-07 to 2026-08 were downloaded. They match BPS within ±9% in 2017–2020 and 2023–2025, but come in 14–29% low in 2016, 2021 and 2022.
- ADU-equivalents are close to zero, as expected in a prohibiting place:
  - Pleasant Prairie: 5 parcel-rule hits in 2003–2026 (one a year at most). None could be confirmed: 2 are uncertain and 3 are probably false.
  - Sun Prairie: no second-dwelling hits in 2016–2025.
  - Text-rule ADU candidates: 1 in Pleasant Prairie (2018) and 2 in Sun Prairie (2017, 2024).
  - Teardown-rebuilds are a separate series: 19 in Pleasant Prairie, 0 in Sun Prairie.
- **Headline (AQ-032): second homes on single-family lots**, window 2014–2026: Pleasant Prairie **3 units** (2 second dwellings the audit could neither confirm nor reject, 1 attached in-law ADU), best read as a range **0–3**, with an **unconfirmed upper bound of 6** that restores the 3 parcel-rule hits the audit judged likely false. They are excluded by the same judgment mechanism Madison uses for its exclusions. Sun Prairie 2016–2026 **3 units** (1 ADU conversion 2017, 1 attached ADU 2024, both in the restrictive period; 1 duplex conversion in August 2026, after Ord. 984); upper bound also 3. Sun Prairie 2014–2015 is missing (no permit data). Adding the series changed no existing figure in either city (section 5a).
- No year-built or dwelling-count field is reachable for either place, so "the parcel already had a dwelling" is read from the permit history of the same parcel number. Madison reads it from the assessor's year built instead, so the three cities' headlines rest on different evidence (cross-city table in section 5a). This is the main limit (section 3).

## Coverage at a glance

| Input | Pleasant Prairie | Sun Prairie |
| --- | --- | --- |
| Permits | **observed**: issued, 2003-10 → 2026-10-24 (dense from 2008) | **observed**: submitted, 2015-07 → 2026-08-31 (model refreshed 2026-09-01) |
| Stage | `issued` (Date Issued) | `application` (Date Submitted only; no issue date). Withdrawn/void/denied/stopped records add 0 units |
| Units added | **calculated** from permit type (new single-family 1, two-family 2, manufactured 1, multi-family from text); conversions and in-law wording from text | **calculated** from record type (Munis codes, OpenGov types) plus description |
| Parcel | **observed** on the permit (Kenosha format `91-4-122-000-0000`, digits illustrative), matched to V12 PARCELID | **observed** on the permit (Dane 12-digit), matched to V12 PARCELID |
| Prior dwelling on parcel | **calculated** from the parcel's permit history (no year built anywhere public) | same |
| Tract / block group | **calculated**: point-in-polygon of the V12 parcel point against TIGER/Line 2024 | same |
| BPS place totals | **observed**, reconciliation only | same |
| DSPS UDC permit counts | **not used**: the search is a Salesforce form post; not submitted under the no-forms rule | one figure from the search document only (below) |

## 1. Acquisition test (2026-10-24, plain HTTP, no browser)

| | Pleasant Prairie (SmartGov → Exago report) | Howard (CivicPlus Archive PDFs) |
| --- | --- | --- |
| Result | **Success**, scripted (Python stdlib `urllib`) | **Success**, scripted (`curl`/`urllib`, then `pdftotext`) |
| Test scope | Full year 2025 in one request, plus Sep 2025 as PDF and RTF | All 12 monthly files of 2025 (ADID 2980–2991) |
| Time | About 30 s for the year (server render about 21 s, plus transfer) | 15 s for 12 files |
| Size | 2025: 28.7 MB RTF (Sep 2025 alone: 1.5 MB PDF, 3.9 MB RTF) | 2.06 MB (12 PDFs, about 170 KB each) |
| Rows | 2025: 1,698 permits, all distinct numbers. Includes 23 new single-family, 1 two-family, 14 manufactured, 4 multi-family and 18 razing permits | 2025: 672 detail rows, including 142 "New Single Family Dwelling" (equal to the report's own summary, "In Single Family Buildings" YTD 142) |
| Quick BPS check, 2025 | BPS 1-unit 24 vs 23 new single-family (manufactured homes are outside BPS); BPS 2-unit 1 building vs 1 new two-family | BPS shows only 4 months reported for Howard in 2025, so no clean check |
| PDF tooling | Not needed (the RTF export is a cell table) | `pdftotext -layout` (poppler, `/opt/homebrew/bin`) works. No Python PDF library is installed (pypdf, pdfplumber and PyMuPDF are absent), and none was needed or added |

### How the Pleasant Prairie download works

The Reports page is public. "View report" is an ASP.NET form post that hands the browser to an Exago WebReports session. Everything after that is JSON over HTTP (`pleasant_prairie._ExagoSession`):

1. GET `https://vlg-pleasantprairie-wi.smartgovcommunity.com/Public/ReportsView` to get the form state.
2. POST multipart to `/Public/ReportsView/ViewReport?reportId=361fe732-f57f-4e4c-827c-72b67cc09ca6&reportType=Exago`.
   - The post carries `__VIEWSTATE`, `__VIEWSTATEGENERATOR` and `__submitFormValidator__`. The last is the page's own client-side token: random letters around a millisecond timestamp.
   - The response redirects to `https://reports-new.smartgovcommunity.com/exago/ExagoHome.aspx` with a session cookie and a settings blob.
3. POST `exago/wrajax/Client.BaseExecuteCtrl.LoadCallback.ashx?t=<TempPath>`. This returns the report definition and its three filters:
   - fee code not one of the impact, sewer and erosion-deposit codes;
   - **Permits.Date Issued between** (default: last month);
   - status ≠ VOID.
4. POST `wrajax/Callbacks.Execute.StartExecuteSimple.ashx` with the date filter set and export type `rtf`. Then poll `Callbacks.Execute.GetStatus` until phase 4 (Success).
5. GET `exago/ExecuteExport.aspx?eid=<id>&…` to fetch the file.

Gotchas:
- **CSV and Excel export are disabled** for this report ("Output type Csv not allowed"). PDF and RTF are allowed.
  - RTF is used because it is an explicit cell table, which parses without layout guessing.
  - PDF text (`pdftotext -raw`) interleaves mobile-home lot numbers into addresses.
- **Date format:** ISO dates are silently misread (2025-09-01 became 09/01/2026). The code sends `MM/DD/YYYY`.
- **Fee-code filter:** the report always applies it. Removing it on the client gave a byte-identical file. Permits whose only fees are excluded codes could in principle be missing. The BPS match (section 4) shows no sign of this. **Unknown**, but low risk.
- **File size:** the RTF embeds a logo on every page, so the raw files are stored gzip-compressed (81 MB total). Re-running a year gives a file differing by one byte (render timestamp), so the sha256 changes between runs.
- **Personal data:** the raw files carry owner names, owner mailing addresses, contractors and fees. They stay in `data/raw/pleasant_prairie_permits/` and are dropped at ingestion (section 2).

### How the Sun Prairie download works

- **Source:** the "All Submitted Permits Report", a Power BI publish-to-web report on the US Government cloud, linked from https://cityofsunprairie.com/974/Construction-Reports.
- **Requests:** `sun_prairie.fetch_permits` POSTs anonymous `querydata` requests to `https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/querydata` with header `X-PowerBI-ResourceKey: fb5e5c09-…`. There is one query per `PermitList.Year`, and the compressed DSR answer is decoded locally.
- **Host:** the `-redirect` host named in the embed page resets connections; the `-api` host answers.
- **Personal data:** only non-personal columns are requested. `Owner Name` and `Contractor` are never downloaded.
- **Row counts:** they equal the counts in the search document, for example 2019: 2,400 and 2025: 2,859. Every record has `Record Ct` = 1, and record numbers are unique.

### How the Howard download works (tested; no adapter built)

- **Archive:** `https://www.villageofhoward.com/Archive.aspx?AMID=41` lists 177 items, from ADID 2820 (2012-01) to 2999 (2026-08). `Archive.aspx?ADID=<n>` redirects (302) to `/ArchiveCenter/ViewFile/Item/<n>`, which is a PDF.
- **Summary pages:** each monthly PDF opens with 2–3 summary pages covering permits, projects, costs and dwelling units by building type for the past 10 years.
- **Permit table:** after the summary comes a permit table with permit #, date issued, job address, local parcel number (e.g. `4099`, `747-R-45`, `664 & 664-4`), description, owner name, applicant, permit types, cost and fees.
  - The Brown County parcel ID needs a `VH-` prefix.
  - `pdftotext -layout` keeps the columns aligned, so a fixed-column parser would work.

## 2. Cleaning rules

**Pleasant Prairie** (`pleasant_prairie.load_raw_permits`):
1. **Parse:** RTF rows are turned into one record per permit: type, permit #, cost, issue date, site address, parcel and description.
2. **Drop personal fields:** owner name, owner mailing, contractor, contractor address and fees are removed here.
   - **Owner surnames inside descriptions are also removed.** In 2015–2024 the description reads "SURNAME (CONTRACTOR) work…". A leading name-plus-parentheses prefix is stripped when the prefix has at most 4 words and no work words, and the parentheses hold neither a bare number nor long text. This affected 8,384 descriptions; the flag `description_prefix_removed` records it.
3. **Site address:** split into street and mobile-home lot number. The city and ZIP are removed (the city can be Kenosha or Pleasant Prairie).
4. **Units** are calculated, because the report has no units field:
   - new single-family → 1; new two-family → 2; new manufactured home → 1;
   - new multi-family → the "N UNIT" number in the text;
   - a raze of a principal or unspecified building → −1; a raze of a garage, shed or barn only, or a partial raze → 0;
   - text "convert … to duplex / two-family", "add a second unit", "in-law", "accessory dwelling" or "ADU" → 1.
   - Type-derived counts are not overruled by description words. The Madison deck/porch filter would otherwise reject "NSFR w/ garage and deck".
5. **Dedupe:** by permit number (no duplicates occurred).

**Sun Prairie** (`sun_prairie.load_raw_permits`):
- **Munis codes (2016 to mid-2021):** R001–R150 are new one-family homes (one code per subdivision or builder), R160 is a duplex, R180/R190 are multi-unit, Z900 is a raze. The builder or owner-builder name after " - " in Munis new-home text is replaced by `[name removed]`.
- **OpenGov types (mid-2021 on):** only "OTFD – one or two-family new construction, additions, alterations" can carry a new home.
  - A new home is recognized when the first dwelling phrase ("single family home", "twin home", "new … house") is not preceded by work-on-existing words (deck, addition, remodel, basement, existing, our…).
  - MWOT and MWMC minor-work permits never add units.
- **Status:** W, X and D (Munis) and "Stopped" (OpenGov) are treated as withdrawn and add 0 units.

## 3. Classification and the ADU-equivalent rule

The pipeline is the Madison one (`pipeline.build_permits_observed`). It is called with two new hooks: parcel-number matching (`comparison.parcel_match_fn`) and a permit-history parcel rule (`comparison.prior_dwelling_rule`).

**Why a different parcel rule.**
- Madison's rule needs the assessor's year built.
- For these places, neither V12 nor any public county layer reachable without a login has year built or dwelling counts:
  - Kenosha County's assessor GIS is behind bot protection, and its public tax-parcel layer returns 0 features.
  - Dane County's public layers carry values only.
  - The historical V-series parcels exist only as multi-GB statewide downloads.

**Rule.** It applies to records that add 1–2 units and are a new dwelling or a conversion, and checks in this order:
1. The description must not contradict the units (type-based units always pass).
2. **Parcel matched.** The permit's parcel number equals a V12 PARCELID (confirmed) or does so after removing spaces and dashes (probable).
3. **Host is residential now.** The V12 PROPCLASS includes 1, 4, 5, 5M, 6 or 7. Commercial (2) parcels fail; these are mainly mobile-home parks.
4. **Conversion text → ADU-equivalent, series `duplex_conversion`.**
5. **Replacement wording → teardown_rebuild.** Examples: "rebuild", "replace existing home", "due to fire", "tear down".
6. **Site with 3+ dwelling permits, or any multi-family permit → excluded** (mobile-home parks, condo plats).
7. **Manufactured home after an earlier manufactured home on the parcel → replacement.**
8. **Teardown signal → teardown_rebuild.** The window runs from the first prior-dwelling evidence (or 730 days before) to **1,095 days after** the permit. Signals are:
   - a dwelling raze;
   - raze-related work on another permit, such as "sewer capping for raze";
   - a temporary "two principal structures" permit.

   The long after-window is deliberate: the audit found owners razing the old house up to 20 months after moving into the new one.
9. **Earlier new-dwelling permit less than 3 years before, with no other evidence → possible re-issue** (excluded).
10. **Prior-dwelling evidence → ADU-equivalent, series `second_dwelling`.** Evidence is either:
    - an earlier permit on the same parcel number, at least 365 days before, for work on an existing dwelling (re-roof, HVAC, plumbing, electrical, addition/alteration, deck, pool, solar, legacy "SF residential"); or
    - an earlier new-dwelling permit at least 3 years before.

    Fences, driveways, detached accessory buildings and early-start footings do not count as evidence: they occur on vacant lots.
11. **Otherwise → `no_prior_dwelling_evidence`** (a first dwelling).

Permit history is grouped by the permit's own parcel number, not the V12 match, so razed-and-replatted parcels that are gone from V12 still count. Series per record: `adu_text`, `adu_equivalent:second_dwelling`, `adu_equivalent:duplex_conversion`, `teardown_rebuild`, `manufactured_home_replacement` and `other_residential`.

**Known limits of the rule.**
- **No early history:** a house with no permit activity since the series began is invisible, so a true second dwelling there is missed. This bites more in Sun Prairie (series from 2016) than in Pleasant Prairie (dense from 2008).
- **Parcel splits:** a lot split for a second house creates a new parcel number and is not an ADU-equivalent anyway.

**New-dwelling outcomes** (records adding units through a new-dwelling type):

| Parcel-rule outcome | Pleasant Prairie | Sun Prairie |
| --- | --- | --- |
| No prior-dwelling evidence (first dwelling) | 1,250 | 1,235 |
| Host not residential (mostly parks on class-2 parcels) | 208 | 6 |
| Teardown-rebuild (raze 14, text 5) | 19 | 0 |
| No parcel | 9 | 1 |
| Multi-dwelling site | 2 | 6 |
| Possible re-issue | 2 | 0 |
| **Pass: ADU-equivalent second dwelling** | **5** | **0** |

## 4. Checks

### BPS reconciliation

The comparison is new one-family permits plus two-family units against BPS 1-unit plus 2-unit units. Manufactured homes are excluded because BPS does not count them. Two-family permits are added because the village reports twin homes on separate lots as 1-unit attached; on its own, the 1-unit ratio runs 0.67–1.09.

Source: `data/processed/permits_<city>/bps_reconciliation.csv`.

| Year | PP permits 1-fam / 2-fam | PP BPS 1u+2u | PP ratio | SP permits 1-fam / 2-fam | SP BPS 1u+2u | SP ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 2015 | 55 / 0 | 56 | 0.98 | – | 160 | – (data start 2016) |
| 2016 | 35 / 0 | 32 | 1.09 | 98 / 4 | 149 | 0.71 (partial year in data) |
| 2017 | 37 / 1 | 40 | 0.98 | 131 / 10 | 139 | 1.09 |
| 2018 | 41 / 5 | 49 | 1.04 | 174 / 6 | 175 | 1.06 (BPS 10 months) |
| 2019 | 66 / 6 | 77 | 1.01 | 109 / 11 | 132 | 0.99 |
| 2020 | 35 / 9 | 54 | 0.98 | 159 / 12 | 172 | 1.06 (BPS 8 months) |
| 2021 | 58 / 6 | 67 | 1.04 | 126 / 5 | 159 | 0.86 |
| 2022 | 34 / 5 | 44 | 1.00 | 72 / 8 | 122 | 0.72 |
| 2023 | 23 / 4 | 31 | 1.00 | 91 / 7 | 113 | 0.93 |
| 2024 | 25 / 4 | 34 | 0.97 | 77 / 2 | 86 | 0.94 |
| 2025 | 23 / 1 | 26 | 0.96 | 85 / 5 | 100 | 0.95 |

Notes on the comparison:
- **Pleasant Prairie** is within −4% to +9% every year.
- **Sun Prairie timing:** it compares submission year with BPS issuance year, so some lag is expected.
- **Sun Prairie 2021–2022:** these are low around the Munis→OpenGov switch. Likely causes are OpenGov new homes described in ways the text rule misses, and condo or twin units filed under multi-family types. This is **open**.
- **DSPS UDC search:** not run. It is a Salesforce Visualforce form post, and the shared rules exclude form submissions.
  - The search document quotes one DSPS figure: Sun Prairie, 2018-01-01 to 2026-10-23, 1,065 new one- and two-family dwelling permits.
  - This build has 945 new one-family plus 59 two-family records submitted 2018-01 to 2026-08, 1,004 in all. That is about 94% of the DSPS figure, but the DSPS total covers a longer window (to 2026-10-23) and counts issued permits.

### Parcel match rates

Source: `match_rates.csv`.

| Group | Method / quality | Pleasant Prairie | Sun Prairie |
| --- | --- | --- | --- |
| All permits | parcel_id / confirmed | 93.3% | 98.0% |
| | address fallback (exact, normalized, geocode) | 2.6% / 0.3% / 0.2% | 1.0% / 0.5% / 0.1% |
| | unmatched | 3.7% (mostly legacy rows and retired parcels) | 0.4% |
| Unit-adding records | parcel_id / confirmed | 98.3% | 95.5% |
| | unmatched | 0.8% | 0.4% |
| New dwellings | parcel_id / confirmed | 99.0% | 97.2% |
| ADU-equivalents | parcel_id / confirmed | 5 of 5 | 1 of 1 |
| Counted units placed in a tract | | 96.4% (2,562 units) | 97.5% (4,091 units) |

- **V12 download:** both places, owner fields not requested (Pleasant Prairie 9,838 features; Sun Prairie 12,427). Each includes the parcels that permits cite but that now lie outside the place: 157 and 178 IDs requested.
- **Tract counties:** all tracts fall in Kenosha (55059) and Dane (55025) counties.

### Audit sample and judgments

Files: `data/processed/permits_<city>/audit_sample.csv`, with judgments from `audit_judgments.csv`. Judgments rest on each record's text and the full permit history of its parcel. No portal record was opened.

| Group | Pleasant Prairie | Sun Prairie |
| --- | --- | --- |
| ADU-equivalent hits | 5: **0 confirmed**, 2 uncertain, 3 uncertain and likely false (unrecorded teardown or re-permit of an unbuilt house) | 1 duplex conversion (2026, after the reform, uncertain: prior use not stated) |
| Text-rule ADU candidates | 1: a 2018 "768 sq ft addition (in law)". Correct text hit; legal unit status unknown; counted with calculated units = 1 | 2 counted: a 2017 coach-house conversion of a detached garage (unmatched to V12) and a 2024 "mother-in-law suite, addition". Plus 1 correctly not counted (re-roof of a carriage house) |
| Teardown-rebuild (8 sampled) | 8 of 8 correct. Includes one new-house-first, raze-the-old-house-20-months-later case | – |
| Near misses (parcel rule, 8 each) | 8 of 8 correct exclusions (park homes on class-2 parcels, new lots, condo two-family buildings) | 8 of 8 correct exclusions (duplex-condo plats, new lots) |
| Unmatched (6 each) | 6 of 6 correctly unmatched (legacy 2004–05 rows without parcel; a 33-unit building on a replatted parcel) | 5 correctly unmatched (multi-family on replatted parcels) and 1 true ADU-like record (the coach house) |

**Findings.**
1. **The ADU-equivalent series in a prohibiting village is near zero and mostly noise.** In Pleasant Prairie, the first rule version passed 9 records; the audit showed most were teardowns, which led to the wider raze rules. Of the 5 that remain, none can be confirmed from permits.
   - **Recommendation:** report Pleasant Prairie as "0–1 per year, unverified upper bound", never as a rate with precision.
2. **Teardown-rebuilds outnumber ADU-equivalents about 4 to 1** and must stay a separate series.
3. **Text-rule ADU candidates in restrictive periods exist but are rare:** 1 in Pleasant Prairie (2018), and 1 in Sun Prairie in 2017 plus 1 in 2024. Their legal status (separate unit or not) is unknown.
4. **Shared classifier word boundary:** `classify.ADU_RE` matches `\bin[- ]law\b`, so names such as "Wisconsin Lawn Sprinkler" are not ADU text hits. (An earlier draft of this note said the boundary was missing; the code already had it.)

## 5. Results by year

`reference/pleasant_prairie_adu_equivalent_by_year.csv` and `reference/sun_prairie_adu_equivalent_by_year.csv` hold these figures by year and series, with columns permits, units, method, stage, restrictive_period, period_start, period_end and value_status (`provisional` for 2026, a partial year, else `final`). One row set per year, except Sun Prairie 2026, which is split at Ord. 984 (below). They are aggregate and non-personal.

Counted units:

| Year | PP ADU-eq second dwelling | PP ADU text | PP teardown-rebuild | PP new 1-fam / 2-fam units | SP ADU-eq | SP ADU text | SP new 1-fam / 2-fam units |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2003–2013 | 0 | 0 | 0 | 745 / 40 | – | – | – |
| 2014 | 1 | 0 | 1 | 50 / 0 | – | – | – |
| 2015 | 0 | 0 | 4 | 55 / 0 | – | – | – |
| 2016 | 0 | 0 | 1 | 35 / 0 | 0 | 0 | 98 / 8 |
| 2017 | 1 | 0 | 2 | 37 / 2 | 0 | 1 | 131 / 20 |
| 2018 | 1 | 1 | 0 | 41 / 10 | 0 | 0 | 174 / 12 |
| 2019 | 0 | 0 | 4 | 66 / 12 | 0 | 0 | 109 / 22 |
| 2020 | 0 | 0 | 1 | 35 / 18 | 0 | 0 | 159 / 24 |
| 2021 | 1 | 0 | 0 | 58 / 12 | 0 | 0 | 126 / 10 |
| 2022 | 1 | 0 | 1 | 34 / 10 | 0 | 0 | 72 / 16 |
| 2023 | 0 | 0 | 1 | 23 / 8 | 0 | 0 | 91 / 14 |
| 2024 | 0 | 0 | 2 | 25 / 8 | 0 | 1 | 77 / 4 |
| 2025 | 0 | 0 | 0 | 23 / 2 | 0 | 0 | 85 / 10 |
| 2026 (PP to 10-24, SP to 08-31) | 0 | 0 | 2 | 43 / 2 | 1 (duplex conversion; after Ord. 984) | 0 | 52 / 6 |

- **Teardown-rebuild columns:** they include the 5 text-only teardowns ("rebuild"), so the PP teardown total is 19.
- **Manufactured homes:** they are separate (`new_manufactured_homes`; 163 Pleasant Prairie permits 2008–2026).
- **Stages:** Pleasant Prairie counts are issued; Sun Prairie counts are submitted applications.
- **Sun Prairie restrictive period:** Ord. 984 (adopted 2026-05-05) allows ADUs by special use. `restrictive_period` is set by record date: true before 2026-05-05, false from that date. In the reference CSV, 2026 has two row sets: **2026-01-01 to 2026-05-04** (restrictive: 24 new one-family and 2 two-family records, 0 second homes) and **2026-05-05 to 2026-12-31** (not restrictive; data end 2026-08-31: 28 one-family, 1 two-family, 1 second home, the August duplex conversion). Use 2016–2025 plus January–April 2026 for the restrictive comparison, or 2016–2025 alone for whole years.

## 5a. Headline: second homes on single-family lots (AQ-032)

Same definition and code as Madison ([MADISON_PERMITS.md](MADISON_PERMITS.md) section 5a; `missing_middleware/permits/second_homes.py`): counted text-rule ADUs except legalizations (`adu_detached`, `adu_attached`, `adu_conversion`), ADU-equivalent `second_dwelling`, and `sf_to_duplex` (ADU-equivalent duplex conversions). Teardown-rebuilds and manufactured-home replacements are excluded. Neither city has ADU text bundles (`adu_two_unit` is 0 throughout). The series is added after classification; `series`, `unit_category` and `counted` are unchanged record by record.

**Judgments, applied the same way as in Madison** (review S3). Madison excludes rule hits that a recorded judgment rejects (BLDNRC-2022-06192; BLDNRC-2026-23354 pending). Pleasant Prairie now does the same: `pleasant_prairie.SECOND_HOME_JUDGMENTS` excludes the three parcel-rule hits the audit judged `uncertain_likely_false`, and keeps them in the unconfirmed upper bound (`second_home_sf_lot_upper_bound`, record column `second_home_upper_units`):

| Permit | Audit finding | Headline |
| --- | --- | --- |
| SF1710-020 (2017) | Only prior evidence is a 2014 legacy permit with no text; a new gas service followed the house permit: a first house on the lot | Excluded; upper bound 1 |
| SF2110-077 (2021) | A 10,256 sq ft new house whose only prior evidence is a 2012 legacy alteration: likely a replacement without a raze permit, i.e. a teardown under AQ-032 | Excluded; upper bound 1 |
| SF2203-055 (2022) | An earlier new-dwelling permit 4.5 years before and no raze: the lot was most likely re-permitted | Excluded; upper bound 1 |

The two other PP hits (14-07-017, 2014; SF1803-010, 2018) are `uncertain` and stay in; the 2018 in-law addition (SF1809-018) is a correct text hit whose legal unit status is unknown. Sun Prairie has no hit judged likely false (its 2026 duplex conversion, OTFD-26-212, is `uncertain` and stays in), so no Sun Prairie judgment is needed.

Counted units (permits equal units in every cell):

| Year | PP second homes | PP components | PP upper bound | SP second homes | SP components |
| --- | --- | --- | --- | --- | --- |
| 2014 | 1 | second_dwelling 1 | 1 | missing | – |
| 2015 | 0 | – | 0 | missing | – |
| 2016 | 0 | – | 0 | 0 | – |
| 2017 | 0 | – | 1 | 1 | adu_conversion 1 |
| 2018 | 2 | adu_attached 1, second_dwelling 1 | 2 | 0 | – |
| 2019 | 0 | – | 0 | 0 | – |
| 2020 | 0 | – | 0 | 0 | – |
| 2021 | 0 | – | 1 | 0 | – |
| 2022 | 0 | – | 1 | 0 | – |
| 2023 | 0 | – | 0 | 0 | – |
| 2024 | 0 | – | 0 | 1 | adu_attached 1 |
| 2025 | 0 | – | 0 | 0 | – |
| 2026, provisional (PP to 10-24; SP to 08-31) | 0 | – | 0 | Jan 1–May 4 (restrictive): 0; May 5 on: 1 | sf_to_duplex 1 (August, after Ord. 984) |
| **2014–2026** | **3** (range 0–3) | second_dwelling 2, adu_attached 1 | **6** | **3** (2016–2026; 2 in the restrictive period) | one each |

**Cross-city headline, 2014–2026** (units; window stated per city):

| City | Window | Headline | Unconfirmed upper bound | Without the templated programme | How "the lot already has a home" is determined | Stage |
| --- | --- | --- | --- | --- | --- | --- |
| Madison | 2014–2026-10-23 | 102 (93 permits); 2026 provisional, 42 | 104 | 66 (2026: 13) | Assessor layer: main building's YearBuilt at least 2 years before the issue year, one-unit Residential host, no earlier unit-adding permit explaining the house, no dwelling raze from 730 days before to 180 days after | issued |
| Pleasant Prairie | 2014–2026-10-24 | 3 (range 0–3) | 6 | n/a | Permit history of the same parcel number: an earlier permit for work on an existing dwelling at least 365 days before (or a new-dwelling permit at least 3 years before), no teardown signal from the first evidence to 1,095 days after; no year built is reachable | issued |
| Sun Prairie | 2016–2026-08-31 (2014–2015 missing) | 3 (restrictive period 2016–2026-05-04: 2) | 3 | n/a | Same permit-history rule as Pleasant Prairie | submitted |

The permit-history rule can only see dwellings with permits on record, and cannot see an unrecorded teardown; the assessor rule can miss a second home on a lot whose main house was rebuilt. Neither city's figure should be compared to Madison's as if measured the same way.

- **Caveat:** none of the Pleasant Prairie hits could be confirmed, and the text candidates' legal status is unknown. The PP headline is a ceiling on confirmed legal second homes in the restrictive period; the true value may be near 0.
- **Stage:** Pleasant Prairie counts issued permits; Sun Prairie counts submitted applications.
- **Reference CSVs:** the headline is series `second_home_sf_lot`, with one row per component `second_home_sf_lot:<component>` (method `aq032_rule`) and the upper bound `second_home_sf_lot_upper_bound`. Second-home rows start in 2014 (Pleasant Prairie) and 2016 (Sun Prairie, its first data year), so summing them gives the window above; Pleasant Prairie's other rows cover 2003–2026. Headline and upper-bound rows carry method `aq032_rule+judgment` in Pleasant Prairie and `aq032_rule` in Sun Prairie.

## 6. Traced examples (house numbers redacted)

### Pleasant Prairie, issued permit SF25-07-076

| Stage | Values |
| --- | --- |
| Source record (`permits_issued_2025.rtf.gz`, row 655) | Type `NEW SINGLE FAMILY DWELLING`; Permit `SF25-07-076`; Cost `500,000.00`; Issued `09/05/2025`; Site Address `[####] 93RD CT PLEASANT PRAIRIE WI 53158`; Parcel `91-4-122-084-07**`; Project Description `New Single Family Dwelling`; Owner, owner mailing, contractor, contractor address and fees `[dropped at ingestion]` |
| Cleaned | address_raw `[####] 93RD CT`; units_raw 1 (basis `type`); no name prefix |
| Parcel | match `parcel_id` / `confirmed` (rule `parcel_id_exact`) to V12 PARCELID; PROPCLASS 1 |
| Parcel rule | No earlier permit on the parcel, so `no_prior_dwelling_evidence`: series `other_residential` (a first dwelling) |
| Area | V12 parcel point → tract **55059002605**, block group **550590026052** |
| Contract row (`permits_observed`) | record_key `236026b72534f932`; jurisdiction 5505963300; stage issued; stage_date 2025-09-05; other_residential / structured_field; units 1; parcel_id; parcel_stateid `05991-4-122-084-07**`; restrictive_period true; counted true |

**Unmatched example: MF1809-011 (2018).** "33 UNIT MF BLDG" at `[#####] 116TH AVE CMPLX`.
- **Match:** parcel `92-4-122-302-01**` is not in V12 (replatted), and the address fallback found no matching number.
- **Result:** `unmatched` / `none`. The 33 units count at village level but in no tract, which lowers 2018 coverage for `other_residential`.

### Sun Prairie, application OTFD-24-106 (restrictive period)

| Stage | Values |
| --- | --- |
| Source row (`permits_submitted_2024.json.gz`, row 2532) | Record `OTFD-24-106`; Record Type `OTFD - One or two-family homes new construction, additions, alterations permit`; Project Description `Mother-in-law Suite, addition`; Parcel `0810023212**`; Status `Active`; Street No `[####]`; Street Name `REBEL DR`; Subdivision `Wyndham Hills`; Date Submitted `2024-04-16` (epoch ms 1713304503000). Owner and contractor never requested |
| Cleaned | record_kind `conversion` (text "in-law"), units_raw 1 (basis `conversion_text`) |
| Classification | Text rule: ADU pattern "in-law" + "addition" → `adu_attached` / `text_rule` |
| Parcel | `parcel_id` / `confirmed`; V12 PROPCLASS 1 |
| Area | tract **55025011404**, block group **550250114042** |
| Contract row | record_key `db5efc12d17d3729`; jurisdiction 5502578600; **stage application**; stage_date 2024-04-16; units 1; parcel_stateid `0250810023212**`; series adu_text; restrictive_period true; counted true |

**Unmatched example: 20170400 (2017).** "BUILDING 2. CONVERT DETACHED GARAGE INTO 1-FAMILY 2-STORY DWELLING. (COACH HOUSE)" at `[###] MAIN ST`.
- **Match:** parcel `0811054436**` is not in V12. The address fallback failed because the permit omits the street direction (rule `street_unknown`).
- **Result:** it is counted as a text ADU at city level only.

## 7. Outputs

| File | Content | Shareable? |
| --- | --- | --- |
| `data/processed/permits_<city>/permits_observed.parquet` | Contract table. Contract columns plus year, permit_type, parcel_stateid, parcel_id, area_id, tract/bg, counted, match_rule, text_note, parcel_rule_reason, n_source_rows, **series**, **restrictive_period** (by record date), **second_home_component**, **second_home_units**, **second_home_upper_units**. Validated with no contract problems. Pleasant Prairie 1,543 rows; Sun Prairie 1,352 | Local (record level) |
| `…/permits_records_full.parquet` | All deduplicated permits with diagnostics: 22,390 and 26,342 | Local |
| `…/permits_by_area_year.parquet` | City and tract rows by year and category, with coverage and suppressed flags (same rules as Madison) | Aggregate; mask suppressed cells before publishing |
| `…/bps_reconciliation.csv`, `match_rates.csv`, `build_report.json` | Checks | Aggregate |
| `…/audit_sample.csv`, `audit_judgments.csv` | Audit with judgments | Local (has addresses) |
| `…/second_homes_by_year.csv` | AQ-032 headline by year with component columns and the upper bound (PP 2014–2026, SP 2016–2026) | Aggregate |
| `reference/pleasant_prairie_adu_equivalent_by_year.csv`, `reference/sun_prairie_adu_equivalent_by_year.csv` | year × series: permits, units, method, stage, restrictive_period, period_start, period_end, value_status; includes `second_home_sf_lot*` rows from 2014 (SP 2016); SP 2026 split at 2026-05-05 | Committed |

**Raw files and manifests:**
- `data/raw/pleasant_prairie_permits/`: 24 yearly RTFs. The manifest records request, access time, seconds, bytes, sha256 of stored and uncompressed data, and permit counts.
- `data/raw/sun_prairie_permits/`: 12 yearly response files plus the model refresh time.
- `data/raw/wi_v12_parcels_kenosha_pp/` and `data/raw/wi_v12_parcels_dane_sp/`: V12 parcels, with URL, query, feature count and sha256.
- `data/raw/tiger_wi/`: reused from the Madison build.

**Reproduce:**
- `uv run python scripts/build_comparison_permits.py --fetch` downloads everything and builds. This is a large download: about 81 MB of gzip-compressed RTF for Pleasant Prairie (about 11 minutes; 378 MB of RTF is transferred before compression), the Sun Prairie Power BI responses (under 1 MB, under 1 minute) and the two V12 parcel extracts (12 MB and 22 MB). The Madison build must have been run first (or `--fetch`ed), because the TIGER files in `data/raw/tiger_wi/` come from it.
- Without `--fetch`, it builds from cache in about 30–40 s. A clean clone has no raw data, so it cannot build without `--fetch`.
- **External tools:** none. Both adapters use the Python standard library plus pandas/geopandas. `pdftotext` (poppler) is needed **only for the Howard fallback**, which is not built (it is also used by the separate rules scan, `scripts/scan_adu_mentions.py`, not by this package).

## 8. Shared-module changes and open items

**Shared-module changes:**
- `pipeline.build_permits_observed` gained two optional hooks, `match_fn` and `parcel_rule_fn`. The defaults keep Madison's behaviour.
  - Check at the time: `scripts/build_madison_permits.py` was rerun; `reference/madison_adu_permits_by_year.csv` was byte-identical, with the same row counts (5,752 in scope, 5,705 counted).
- Gate 2 repair round (2026-10-24), review item S3: the pipeline now holds ADU text bundles (ADU wording on a record adding 2+ units) out of every ADU series whichever rule they reach, including a hook-supplied parcel rule. Rerun of this build: no Pleasant Prairie or Sun Prairie record was affected; both `reference/*_adu_equivalent_by_year.csv` files are byte-identical and the row counts are unchanged (PP 1,543 in scope / 1,543 counted; SP 1,352 / 1,351). The other S3 changes (one-unit host, Dwell-0 conversion path, judged false positives) apply only to Madison's default rule. Madison's figures changed; see [MADISON_PERMITS.md](MADISON_PERMITS.md).
- AQ-032 (2026-10-24): new module `missing_middleware/permits/second_homes.py` adds the headline "second homes on single-family lots" after classification, for all three cities. Rerun of this build: in-scope and counted row counts unchanged (PP 1,543 / 1,543; SP 1,352 / 1,351); `series`, `unit_category` and `counted` identical record by record; the reference CSVs only gained `second_home_sf_lot` rows (existing rows byte-identical).
- Addenda review repair (2026-10-24): S3, `pleasant_prairie.SECOND_HOME_JUDGMENTS` excludes the three likely-false parcel-rule hits from the headline, as Madison's judgments do (PP 6 → **3**, upper bound 6; `second_homes.py` gained the `upper_bound` judgment option and `second_home_upper_units`). N6, `restrictive_period` is set by record date and Sun Prairie 2026 is split at 2026-05-05 in the reference CSV (`comparison.restrictive_flag`, `restrictive_periods`; new columns period_start, period_end, value_status). N7, second-home rows start in 2014 (PP rows had covered 2003–2026; totals unchanged because every hit is 2014 or later). N10, the cross-city table in section 5a states how each city determines "the lot already has a home". Rerun: in-scope and counted row counts unchanged (PP 1,543 / 1,543; SP 1,352 / 1,351); every non-headline series total unchanged; SP headline unchanged (3).
- New module `missing_middleware/permits/comparison.py` holds the V12 fetch, parcel-number matching, the permit-history rule, recount and series labels. Both adapters share it.

**Open items:**
- **Stage:** Sun Prairie submission dates are not issuance; a separate issued series is not available from this source.
- **Sun Prairie 2021–2022 shortfall** against BPS is not yet explained.
- **Year built for the host parcel:** Kenosha County assessor data, V-series parcel history and Dane County assessment data would make the rule much stronger. None is reachable without a login, bot-protection bypass or multi-GB download.
- **ADU candidate status:** whether the text-rule candidates (in-law additions, coach house) are legal separate units needs the permit files, which require portal record views or records requests (not done).
- **Howard:** the adapter was not built. A fixed-column `pdftotext -layout` parser plus the `VH-` parcel prefix is the path if Pleasant Prairie ever fails.

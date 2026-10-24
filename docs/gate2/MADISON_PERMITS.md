# Madison ADU permits: extraction, classification, parcel and area match

Gate 2 work package, built 2026-10-23; ADU-equivalent rule, City reconciliation and privacy redactions revised 2026-10-24 in the Gate 2 repair round (review items S1, S3, S4; see "Changes in the repair round" at the end). Code: `missing_middleware/permits/` (city-agnostic pipeline plus a Madison adapter). Build: `scripts/build_madison_permits.py`. Tests: `tests/test_permits.py` (offline, synthetic fixture).

**Bottom line.**
- All issued Madison building permits from 2010-01-01 to 2026-10-23 were downloaded with plain HTTP: 114,224 report rows, 113,890 distinct permits.
- After deduplication and classification, 64 permits (64 units) count as ADU authorizations by text rule. Another 18 permits (19 units) meet the owner's ADU-equivalent rule (AQ-021). We report them as a separate **"second dwelling / conversion"** series, not as ADUs: 13 single-family → two-unit conversions (3 of them recorded with Dwell 0) and 5 second dwellings.
- 99.0% of all counted units are placed in a census tract.
- **City table.** The City's table is labeled "ADUs Permitted", i.e. permits issued; for 2013–2025 (2025 = January–August) it totals 49. Counted by **issue year**, our text-rule series matches it in 2015, 2017–2020, 2024 and January–August 2025, and differs in 2013, 2014, 2016, 2021, 2022 and 2023. Counted by the **year in the permit number**, it matches every year 2014–2022. That the City counts by permit-number year is **our hypothesis**, chosen because it fits 2014–2022; the City does not document it. Section 6 shows both comparisons.

## Coverage at a glance

| Input | Status | Notes |
| --- | --- | --- |
| Issued building permits, 2010–2026-10-23 | **observed** | City "Construction Summary" report, every permit type, one file per issue year |
| Permit stage | **observed: issued only** | The report has no application, final, expired or withdrawn stages, so every row is `stage = issued` |
| ADU flag | **calculated** | No structured flag exists. ADUs are identified by text rules on the description |
| Units added | **observed** (Dwell field), except 3 records | 45 records with 1–2 units are judged implausible from their text (decks, porches, 2→1 conversions), plus 1 audit-judged false positive. All 46 are kept but marked `units_suspect` and not counted. 3 single-family → two-unit conversions recorded with Dwell 0 get 1 unit **calculated** from the text (`units_from_text = true`) |
| Parcel | **calculated** | From an address match to the City's Address Points and Tax Parcels (current layers only) |
| ADU-equivalent ("second dwelling / conversion") | **calculated** | Parcel rule (AQ-021). Uses current assessor data, with timing guards. Reported separately from text ADUs |
| Tract / block group | **calculated** | Point-in-polygon against TIGER/Line 2024 (2020 census geography) |
| City ADU table 2013–2025 | **observed** (published) | Used only for reconciliation |

## 1. Acquisition

### Permits

- **Source:** City of Madison Building Inspection, "Construction Summary" SSRS report.
  - URL: `https://cityreports.cityofmadison.com/CityReports/ReportViewer/ReportViewer/?ReportPath=/Web%20Access/Building/Permits/Construction%20Summary`
- **Terms:** no open-data license is stated; it is a public-records report on the City website.
- **Personal data:** the raw files contain owner names and mailing addresses. They stay in `data/raw` only.
- **How the download works:** plain HTTP from the standard library, with no browser. See `missing_middleware/permits/madison.py::fetch_report_csv`.
  1. GET the ReportViewer page, which gives the ASP.NET form state.
  2. POST the form with `Start Date = 1/1/<year>`, `End Date = 12/31/<year>` (or today), `Permit Type = ALL` and the "View Report" button.
  3. The response contains an `ExportUrlBase`. GET that URL with `CSV` appended.
- **Session expiry:** each year runs in a fresh session, so expiry is no longer a problem. If a full-year request fails, the code falls back to half-years and concatenates them.
- **Command:**
  - `uv run python scripts/build_madison_permits.py --fetch` downloads 2010 through the current year (the current year is always refreshed), then builds.
  - Without `--fetch`, the build runs from the cached files only.
- **Raw output:** `data/raw/madison_permits/construction_summary_<year>.csv` plus `manifest.json`, which records year, request range, access time, bytes, detail-row count and sha256.

| Year | Detail rows | Year | Detail rows | Year | Detail rows |
| --- | --- | --- | --- | --- | --- |
| 2010 | 5,889 | 2016 | 6,244 | 2022 | 6,469 |
| 2011 | 6,996 | 2017 | 7,502 | 2023 | 6,627 |
| 2012 | 5,102 | 2018 | 6,140 | 2024 | 7,931 |
| 2013 | 4,897 | 2019 | 6,871 | 2025 | 8,166 |
| 2014 | 4,543 | 2020 | 6,177 | 2026 (to 10-23) | 13,316 |
| 2015 | 4,833 | 2021 | 6,521 | | |

All files were accessed 2026-10-23 (UTC times are in the manifest). The CSV ends with summary sections. Only rows whose first field matches `^BLD[A-Z]{3}-\d{4}-\d+$` are kept.

### Parcels and address points

- **Files:** `data/raw/madison_parcels/` (`manifest.json` holds URLs, fields, feature counts, access time and sha256). Geometry was requested in EPSG:4326. No owner fields were requested.
- **Tax Parcels:** `Public/OPEN_DATA2/FeatureServer/0`, 82,616 parcel polygons.
  - Fields: Parcel, Address and its parts, PropertyClass/Use, TotalDwellingUnits, YearBuilt, MoreThanOneBuild, ZoningAll and others.
- **Address Points:** `Public/OPEN_DATA/MapServer/20`, 157,222 points, each with its Parcel. Every point's parcel is present in the parcel layer.
- **Terms:** license not stated.
- **Vintage:** both layers are current as of the access date, not historical.

### Tracts and block groups

- **Files:** `data/raw/tiger_wi/` holds `tl_2024_55_tract.zip` (1,542 tracts) and `tl_2024_55_bg.zip` (4,692 block groups), each with sha256 in `manifest.json`.
- **Source:** U.S. Census TIGER/Line 2024, public domain.
- These files were downloaded independently of the statewide foundation build.

## 2. Cleaning rules

1. **Ingestion** (`load_raw_permits`):
   - Owner name, owner address, contractor name, contractor address and fees are dropped. Every later stage starts from this frame.
   - Dollar and comma formatting is stripped; dates are parsed.
   - The permit-type prefix (`BLDNRC`, `BLDNCC`, `BLDRPR`, `BLDRRZ`, `BLDCRZ`) is kept.
2. **Deduplication** (`pipeline.dedupe`):
   - Rows sharing a permit number are one permit.
   - `stage_date` is the earliest issue date; later dates are reissues or reprints.
   - The number of source rows collapsed is kept in `n_source_rows`.
   - Result: 334 duplicate rows in 330 permits. All duplicates have different issue dates (reissues). None disagree on units.
   - Duplicates also occur across year files, when a reissue falls in a later year.
3. **Renewals with new numbers:**
   - Records whose text says RENEW, REINSTATE or REISSUE are excluded from ADU text classification (`near_miss:renewal`). All three such ADU renewals had Dwell 0.
   - A unit-adding renewal on a parcel with a unit-adding permit in the prior three years would be marked `renewal_duplicate` and not counted. None occurred.
4. **Raze permits** carry negative Dwell (units removed). They are used only by the parcel rule and are never counted.
5. **Implausible unit counts** (`units_suspect`):
   - A record with 1–2 units whose description is only non-dwelling work is not counted. Examples are decks, porches, stoops, sheds, sunrooms and additions with no dwelling word.
   - Conversions to fewer units (e.g. "convert two family to single family", which carries Dwell 1) are treated the same way.
   - 45 records (46 units) are affected. The audit found 2 more that slipped through (§7).
   - The audit-judged false positive BLDNRC-2011-05399 (the text says the home stays a single dwelling unit) is also marked suspect: 46 records (47 units) in all.
6. **Dwell-0 conversions** (`units_from_text`): a record with Dwell 0 whose description says a single-family home becomes two units ("convert single family home to 2 unit", "convert single family to two unit") is given 1 unit so the ADU-equivalent rule can judge it. It counts only if it passes that rule, and not if the same parcel has another unit-adding permit within 2 years (that permit already carries the unit). Otherwise it goes back to 0 units and out of scope. 4 records match the text; 3 pass (BLDRPR-2014-04652, BLDRPR-2023-04213, BLDRPR-2023-18661); the fourth is on a commercial (nursing-home) parcel and fails the host check.

## 3. Classification (`unit_category`)

The rules apply in this order:

1. **Text rule** (`classification_method = text_rule`).
   - The ADU pattern matches: accessory dwelling, ADU, accessory unit/apartment, carriage/coach house, granny, in-law, backyard/garden cottage, secondary dwelling unit, or laneway.
   - None of these exclusions matches:
     - coach house converted *to* a single-family home
     - raze/demolish
     - renew/reinstate/reissue
     - permit revision
     - repair/finish of an ADU
     - **ADU text on a record adding 2 or more units** (`near_miss:multi_unit_adu_bundle`: "new duplex w/ ADU", "detached duplex ADU", "twin home ADU"). These cannot be split into ADU units and principal units from this source. **All 10 are held out of every ADU series**, whichever rule they reach: they also never pass the parcel rule (`adu_bundle_held_for_review`) and are counted as `other_residential` (20 units) until the Accela records show the split.
   - Sub-type, first match wins:
     - `adu_legalization`: legalize / as-built / unpermitted
     - `adu_conversion`: "convert", or basement / lower level / interior / within existing, when the work is not "new"
     - `adu_detached`: "detached"
     - `adu_attached`: "attached" / "addition"
     - otherwise `adu_detached`, noted `text_default_detached`. The defaults are mostly "new single family home (ADU)" or "ADU over garage".
2. **Parcel rule: ADU-equivalent** (AQ-021, `classification_method = parcel_rule`). A permit adding a dwelling on a parcel that already had one. The checks, in order:
   1. The description has dwelling evidence and is not a suspect, moved-house or unit-reduction record.
   2. The parcel match is confirmed or probable.
   3. The permit adds 1–2 units, is not an ADU text bundle, and is not an audit-judged false positive (`judged_false_positive`; listed in `MadisonAdapter.parcel_rule_false_positives`, currently BLDNRC-2011-05399).
   4. **The host was a one-unit home before the permit.** The parcel today is Residential, has 1–2 dwelling units (today's count includes the added unit) and is in use "Single family" or "2 Unit". A host that was already multi-unit fails: "3 Unit" parcels, such as the 2 → 3 apartment conversions BLDNCC-2010-15153 and BLDNCC-2016-12120, are now `other_residential`. Exception: when the description itself says a single-family home becomes two units, the text is the evidence of the prior state, so only Residential with 1–3 dwelling units is required (assessor use codes lag conversions; BLDRPR-2023-18661's parcel shows use "3 Unit" but 1 dwelling unit).
   5. **Timing guard:** the assessor's YearBuilt for the main building is valid and at least 2 years before the issue year.
   6. No earlier unit-adding permit on the parcel explains the main building.
   7. No raze permit removing dwellings on the parcel from 730 days before to 180 days after the permit.
3. **`other_residential`** (`structured_field`): every other record that adds units.

### How the parcel rule avoids the vacant-lot false positive

The parcel layer is current, so a house built on an empty lot in 2015 shows one dwelling today.

**Finding:** Madison's assessor counts a single-family parcel with an ADU as **1 dwelling unit**. All 2014–2018 text-rule ADU parcels have `TotalDwellingUnits = 1` and `MoreThanOneBuild = YES`.

**Consequence:** "current units minus permitted units" cannot recover the units that existed before the permit; it would reject real ADUs. The rule therefore uses the main building's YearBuilt as the evidence of a prior dwelling:
- A new house on a vacant lot carries its own YearBuilt, or 0 while unbuilt, and fails check 5.
- A teardown-and-rebuild resets YearBuilt, and is also caught by the raze check.
- The 2-year margin absorbs assessor YearBuilt values set one year early for houses under construction. Several 2015 subdivision homes had YearBuilt 2014.

In-scope records by parcel-rule outcome:

| Outcome | Records |
| --- | --- |
| Main building not older (first dwelling) | 4,201 |
| Host was not a one-unit residential home | 798 |
| Adds more than 2 units | 526 |
| No dwelling evidence in text | 81 |
| No parcel | 81 |
| Pass | 59 (18 are ADU-equivalent; the other 41 are text ADUs, which take precedence) |
| Raze nearby | 3 |
| Main building came from an earlier permit | 2 |
| No units added (Dwell-0 text ADUs, in scope by text) | 2 |
| Audit-judged false positive | 1 |
| ADU text bundle held for review | 1 |

What the 18 ADU-equivalents are (column `adu_eq_series`; same labels as the comparison cities):
- `duplex_conversion`, 13 permits / 13 units: a single-family home converted to two units ("addition to convert single family to duplex", "change 1 unit to 2 unit", "addition to create duplex"). 3 of them are the Dwell-0 conversions (`units_from_text`).
- `second_dwelling`, 5 permits / 6 units: a second house, an upstairs unit over a new garage, a storage building converted to a house, or a duplex on a lot that already had an older house.

They fit the owner's definition but are **not ADUs by name**. Report them as the separate "second dwelling / conversion" series, never added to the text-ADU count.

## 4. Address match and area attachment

### Match tolerances (fixed before evaluation)

These rules were written into `missing_middleware/permits/match.py` and `address.py` before the first match run.

**Address normalization:**
- Upper-case; `.,#;` become spaces.
- Leading house number. A letter suffix (`123A`), a fraction (`1/2`) and a range (`101-103`) are recognized.
- Pre-direction N/S/E/W.
- The street is the longest run of tokens that names a street known to Address Points or Tax Parcels.
- Anything after the street (`2`, `UNIT 2`, `REAR`, `APT B`) is a unit suffix. It is kept for audit and never blocks a match.

| match_method | match_quality | Rule |
| --- | --- | --- |
| address_exact | confirmed | Cleaned permit address equals a cleaned Address Point or parcel `Address` (with or without the word UNIT), and all hits are one parcel |
| address_normalized | confirmed | House number + street key (direction, name, type) equals a reference key and resolves to one parcel, directly or after narrowing by the unit suffix |
| address_normalized | probable | One relaxation reaches one parcel: the other number of a hyphenated range; street type ignored; or direction ignored. The relaxed key must identify a single street |
| address_normalized | ambiguous | Best key resolves to 2+ parcels and the unit does not narrow it. No parcel is assigned. The area is assigned only if every candidate parcel is in the same block group |
| geocode | probable | No key match, but the same street has an address of the same parity within ±10 house numbers. The nearest such Address Point locates the permit for **area only**: no parcel, so no parcel rule |
| unmatched | none | Anything else |

**One change after the first run, disclosed:** a parser case was added so that a spelled-out direction word that is part of a street name ("WEST SHORE DR") can match. It did not change the matched count: the permit it targeted still fails, because a different "W SHORE DR" exists (§6).

**Area attachment:**
- The point used is the matched parcel's representative point (or the geocode point). It is joined to TIGER 2024 tracts and block groups by point-in-polygon.
- `area_id` in `permits_observed` is the tract GEOID. The city row in `permits_by_area_year` uses `muni:5502548000`.

### Match rates

All 5,755 in-scope records (unit-adding, plus every ADU text hit):

| match_method | match_quality | Records | Share |
| --- | --- | --- | --- |
| address_exact | confirmed | 5,531 | 96.1% |
| address_normalized | confirmed | 137 | 2.4% |
| address_normalized | probable | 2 | 0.0% |
| address_normalized | ambiguous | 8 | 0.1% (all 8 placed in a tract: condo buildings) |
| geocode | probable | 54 | 0.9% |
| unmatched | none | 23 | 0.4% |

Counted ADU records only (64 text + 18 ADU-equivalent = 82):

| Group | Exact / confirmed | Normalized / confirmed | Geocode / probable | Unmatched |
| --- | --- | --- | --- | --- |
| Text ADUs (64) | 45 | 2 | 14 | 3 |
| ADU-equivalent (18) | 17 | 1 (BLDNRC-2026-03464) | 0 | 0 |

The rule requires a confirmed or probable parcel match; all 18 are confirmed (17 by exact address, 1 by normalized address). An earlier version of this table said all ADU-equivalents were exact matches; that was wrong (18 exact + 1 normalized before the repair round).

Of counted units (37,334 across all categories), 99.0% are placed in a tract; 372 units are unplaced.

**The misses are systematic, not random:**
- **ADUs with new addresses.** An ADU often gets its own house number that is not yet in Address Points: 14 geocoded and 3 unmatched ADU records. The geocode places them on the right block face for area purposes. It does not give a parcel, so the parcel rule never applies to them.
- **New subdivisions.** Most unmatched multi-unit records are on streets such as Blissful Ave, Wisdom Rd, Eternity Dr and Stones Throw Loop, which do not yet exist in Address Points.
- **Readdressed or redeveloped sites.** Examples are a University Ave site and an E Washington Ave site (house numbers withheld).

**Boundary and vintage:**
- Tracts are 2020 geography, so tracts split in 2020 are not comparable with 2010-based tables.
- All Madison permits fall in Dane County (55025) tracts.
- Parcel and address layers are current: a pre-2026 parcel split or merge is matched to today's parcel.

## 5. Results by year and category

Counted units (issued, deduplicated, ≥1 unit, not suspect), by issue year:

| Year | adu_detached | adu_attached | adu_conversion | ADU text total | adu_equivalent | other_residential |
| --- | --- | --- | --- | --- | --- | --- |
| 2010 | 0 | 0 | 0 | 0 | 1 | 537 |
| 2011 | 0 | 0 | 0 | 0 | 0 | 602 |
| 2012 | 0 | 0 | 0 | 0 | 0 | 1,227 |
| 2013 | 0 | 0 | 0 | 0 | 0 | 2,156 |
| 2014 | 2 | 0 | 1 | 3 | 2 | 2,018 |
| 2015 | 2 | 0 | 0 | 2 | 2 | 1,786 |
| 2016 | 2 | 1 | 0 | 3 | 0 | 2,393 |
| 2017 | 1 | 0 | 0 | 1 | 2 | 2,272 |
| 2018 | 1 | 0 | 0 | 1 | 1 | 1,719 |
| 2019 | 1 | 0 | 1 | 2 | 1 | 1,796 |
| 2020 | 0 | 0 | 0 | 0 | 0 | 2,409 |
| 2021 | 1 | 0 | 0 | 1 | 0 | 3,756 |
| 2022 | 3 | 0 | 2 | 5 | 0 | 2,408 |
| 2023 | 6 | 0 | 1 | 7 | 2 | 2,631 |
| 2024 | 10 | 0 | 0 | 10 | 1 | 3,051 |
| 2025 | 12 | 0 | 1 | 13 | 1 | 3,785 |
| 2026 (to 10-23) | 16 | 0 | 0 | 16 | 6 (5 permits) | 2,705 |
| **Total** | **57** | **1** | **6** | **64** | **19 (18 permits)** | **37,251** |

ADU-equivalent ("second dwelling / conversion") units by sub-series: `duplex_conversion` 2010 1, 2014 2 (1 Dwell-0), 2015 1, 2019 1, 2023 2 (both Dwell-0), 2024 1, 2025 1, 2026 4; `second_dwelling` 2015 1, 2017 2, 2018 1, 2026 2 (one 2-unit duplex behind an older house).

- Every counted text ADU adds exactly 1 unit, so the unit and permit counts are equal.
- No `adu_legalization` records occur.
- **Conversions, for the owner's headline decision.** `adu_conversion` records are ADUs created inside an existing structure, mostly a detached garage or accessory building converted to an ADU. They are coded `adu_conversion` and kept out of the headline under owner decision D5 ("new detached + attached headline; conversions separate"). Counted per year: 2014 1 (garage → ADU), 2019 1 (garage → ADU, BLDNRC-2019-04971), 2022 2 (one accessory building → ADU, one bedroom → attached ADU), 2023 1 (detached garage → ADU with a second floor), 2025 1 (second-story addition converting a garage, BLDNRC-2024-16274); none in other years; 6 in all, 5 of them accessory-building conversions that produce a detached ADU. If the owner decides accessory-building conversions belong in the headline, the headline rises by these counts.
- **Not counted but kept for review:**
  - **2 Dwell-0 ADU conversions:** BLDRPR-2014-13995 ("lower level ADU" in a 2-unit building) and BLDRPR-2026-03870 ("create second dwelling unit in basement").
  - **10 multi-unit ADU bundles (2 units each):**
    - 1 in 2023: BLDNRC-2022-06192, a new duplex with an ADU.
    - 9 in 2026: "detached duplex ADU" or "twin home ADU".

    All 10 are treated the same way: held out of the text-ADU and ADU-equivalent series and counted as `other_residential`. (Before the repair round one of them, BLDNRC-2026-06494, passed the parcel rule and was counted as 2 ADU-equivalent units; that inconsistency is removed.) If each bundle contains one ADU, the 2026 ADU count would be about 9 higher. If both units are ADUs, about 18 higher. This needs the Accela records.
- `reference/madison_adu_permits_by_year.csv` holds these counts by year, category and method: the text-ADU categories, `adu_equivalent` (total) and its sub-series `adu_equivalent:second_dwelling`, `adu_equivalent:duplex_conversion` and `adu_equivalent:duplex_conversion_dwell0` (method `parcel_rule+units_from_text`), the held-out bundles, and a row for the City's published figures.

## 6. Reconciliation with the City's ADU table

**What the City reports.** The City of Madison's Housing Forward ADU page has a table labeled "ADUs Permitted", i.e. **permits issued**, by year: 1, 5, 2, 2, 1, 1, 2, 0, 2, 6, 11, 10 for 2013–2024 and 6 for January–August 2025, **49 in total**. (Transcribed in Gate 1; the independent review re-read the page on 2026-10-24 and got the same values.) The City does not say how a permit is assigned to a year.

**Two ways of assigning our records to years:**
- **Issue year** (the City's stated basis, and this pipeline's outcome definition): the date the permit was issued.
- **Permit-number year** (our hypothesis): the year embedded in the permit number, which is the application or record-creation year, counting every ADU-text record including Dwell-0 records and bundles. **That the City counts this way is an inference, not a documented method.** We adopted it only because it reproduces the City's figures for 2014–2022.

| Year | City ("ADUs Permitted") | Text ADUs, counted, by **issue year** | Same − City | All ADU-text records by issue year | All ADU-text records by **permit-number year** (hypothesis) | Same − City | ADU-equivalent, issue year (not in City table) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2013 | 1 | 0 | **−1** | 0 | 0 | **−1** | 0 |
| 2014 | 5 | 3 | **−2** | 4 | 5 | 0 | 2 |
| 2015 | 2 | 2 | 0 | 2 | 2 | 0 | 2 |
| 2016 | 2 | 3 | **+1** | 3 | 2 | 0 | 0 |
| 2017 | 1 | 1 | 0 | 1 | 1 | 0 | 2 |
| 2018 | 1 | 1 | 0 | 1 | 1 | 0 | 1 |
| 2019 | 2 | 2 | 0 | 2 | 2 | 0 | 1 |
| 2020 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021 | 2 | 1 | **−1** | 1 | 2 | 0 | 0 |
| 2022 | 6 | 5 | **−1** | 5 | 6 | 0 | 0 |
| 2023 | 11 | 7 | **−4** | 9 | 9 | **−2** | 2 |
| 2024 | 10 | 10 | 0 | 10 | 10 | 0 | 1 |
| 2025 (City: Jan–Aug) | 6 | 6 issued Jan–Aug (13 in the full year) | 0 | 6 Jan–Aug | 18 (full year; not comparable) | – | 1 |
| **2013–2024** | **43** | **35** | **−8** | **38** | **40** | **−3** | |
| **2013–Aug 2025** | **49** | **41** | **−8** | **44** | – | – | |

Source: `data/processed/permits/reconcile_city_table.csv` (columns `text_counted_by_issue_year`, `text_all_by_issue_year`, `text_all_by_permit_number_year`, `text_counted_issued_jan_aug`).

**Reading the table.**
- **By issue year** (the City's own basis), the counted text series matches in 2015, 2017–2020, 2024 and January–August 2025, and **differs in 2013 (−1), 2014 (−2), 2016 (+1), 2021 (−1), 2022 (−1) and 2023 (−4)**; it is 8 lower over 2013–2025.
- **By permit-number year**, it matches every year 2014–2022 and differs in 2013 (−1) and 2023 (−2). Say "matches when counted by permit-number year (our hypothesis of the City's method)", **never "an exact match"** without that qualifier.
- Why the hypothesis is plausible: the issue-year differences are timing shifts of the kind the hypothesis predicts. 2016 has 3 by issue year because BLDNRC-2015-06770 was issued in March 2016; two of the City's five 2014 ADUs were issued in early 2015 (BLDNRC-2014-12981) or carried Dwell 0 (BLDRPR-2014-13995); BLDNRC-2021-15572 was issued 2022-02-08.

**Remaining differences (under either basis):**
- **2013 (City 1, ours 0).** No 2013-numbered record uses ADU wording. A manual search of "accessory", "dwelling unit", "dependency", "coach" and "cottage" found none. The likely candidates are a "dependency living arrangement" unit (the pre-ADU form; one 2014 example, BLDRPR-2014-02900, is in the audit) or an approval outside the building-permit system. **Unexplained.**
- **2023 (City 11, ours 9 by permit-number year, 7 counted by issue year).** Two City ADUs are not visible to the text rule. The repair round found two 2023 Dwell-0 single-family → two-unit conversions (now in the ADU-equivalent series); whether the City counted them as ADUs is not known and is not assumed. Other possible causes are records described without ADU wording, or non-BLD records. **Unexplained by 2.**
- **2025 (City 6 for Jan–Aug).** 6 counted text ADUs were issued 2025-01-01 to 2025-08-31, which matches. The 18 by permit-number year include ADUs applied for in 2025 and issued later.
- **Gate 1 keyword counts** (e.g. 2023: 7; 2025: 13) match this build's counted-by-issue-year column. Gate 1 included the 2023 duplex+ADU bundle, which this build excludes. Its 2026 figure of 16 matches; the nine 2026 bundles are held out here.

**Dwell totals vs Gate 1:**
- The deduplicated sum of positive Dwell by issue year (e.g. 2010: 542; 2013: 2,165; 2025: 3,803) is higher than Gate 1's reported sums (521; 1,851; 3,620).
- Gate 1 appears to have netted raze permits, which carry negative Dwell.
- BPS reconciliation by structure type is left to the BPS owner. The inputs are in `permits_records_full.parquet` (`permit_type`, `use_class`, `units_added`).

## 7. Audit sample and findings

`data/processed/permits/audit_sample.csv` is local only and includes addresses. It has 45 rows:
- 13 text ADUs
- 12 ADU-equivalents
- 10 near-miss text hits
- 10 unmatched in-scope records

Judgments are in `audit_judgments.csv`, merged by the build. They rest on the record text and the parcel attributes. **No Accela record was opened.** The sample is drawn with a fixed seed from the current classification, so the repair-round rule change redrew the ADU-equivalent group: 4 records entered it (the 3 Dwell-0 conversions and BLDNRC-2026-03464) and were judged in the repair round, by the same agent that changed the rule, so treat those 4 as a less independent check.

| Group | Correct | Uncertain | Error / limit |
| --- | --- | --- | --- |
| Text ADUs (13) | 11 correct (incl. 5 geocoded to area only) | 0 | 2 correct ADUs unmatched: new addresses (BLDNRC-2026-14548, -21855) |
| ADU-equivalent (12) | 10 (8 SF→two-unit conversions, 3 of them Dwell 0; 1 second-story dwelling over a new garage; 1 addition converting to a two-unit dwelling) | 2 (BLDNRC-2017-16607, -2018-03245: a new house on a lot with an older house; second house or replacement not determinable) | 0 |
| Near-miss text (10) | 4 correct exclusions (renewal, garage raze, guest suite, coach house → SF home); 1 judged false positive now excluded by the rule (BLDNRC-2011-05399) | 4 multi-unit ADU bundles (2026), all held out | 1 possible miss (BLDRPR-2014-02900: garage → "dependency living arrangement unit", Dwell 0) |
| Unmatched (10) | 7 correctly unmatched (new subdivisions, readdressed sites) | 0 | 2 implausible Dwell = 1 on non-dwelling work missed by the suspect filter (BLDNCC-2011-00856, BLDNRC-2016-09142); 1 parser limit (BLDNRC-2024-08399, "WEST SHORE DR" read as "W SHORE DR") |

**Findings:**
1. **Text ADUs are reliable as a lower bound:** 11 of 13 are correct and placed, and the other 2 are correct but unplaced. The main undercount risk is ADU wording that is absent (2013, 2023 gaps) and the 2026 multi-unit bundles.
2. **The ADU-equivalent rule is plausible but noisy.** Before the repair round the sample showed 7 correct, 4 uncertain and 1 false positive out of 12, and the independent review found two more false positives (2 → 3 apartment conversions) and three missed Dwell-0 conversions. After the fixes the redrawn sample shows 10 correct and 2 uncertain. It mostly captures duplex conversions, a broader concept than ADUs. Report it as the separate "second dwelling / conversion" series.
3. **Dwell has data-entry noise.** Decks and porches carry Dwell = 1. The suspect filter removes 45 such records (plus 1 judged false positive); at least 2 more remain. Some real conversions carry Dwell 0; the 3 that state "single family → two unit" are now picked up, but others worded differently are not.
4. **Geocoded ADUs are common,** because new ADU addresses lag Address Points. Their area is reliable to the block face; the parcel is not assigned.

## 8. Traced examples

### Issued permit traced through parcel and tract (BLDNRC-2024-10200)

| Stage | Values |
| --- | --- |
| Source row (`construction_summary_2024.csv`) | B1_ALT_ID `BLDNRC-2024-10200`; Reportable_Data `SINGLE FAMILY RESIDENCES`; Address `[###] CEDAR ST 2`; BLDG_SQFT `1,175`; Textbox9 `$175,000`; Total_Pay `$351`; Textbox13 (Dwell) `1`; Owner_Full_Name / Owner_Address_Line `[REDACTED, dropped at ingestion]`; Detailed_Description `DETACHED GARAGE WITH ADU`; Issuance_Date `08/12/2024`; contractor fields `[dropped]` |
| Cleaned (`permits_records_full`) | permit_type BLDNRC; issue_date 2024-08-12; n_source_rows 1; units_added 1; parsed house number + street key `CEDAR ST`, unit `2` (flag `unit_suffix`); text_category `adu_detached` (rule: "detached" + ADU) |
| Parcel | match_method `address_exact` / `confirmed` (rule `exact_string`: the "… 2" address is in Address Points); parcel `0709264042**`, situs `[###] Cedar St`; Single family, Residential, TR-C2, YearBuilt 2009, TotalDwellingUnits 1, MoreThanOneBuild YES |
| Area | Representative point of the parcel → tract **55025001300**, block group **550250013001** (TIGER 2024) |
| Contract row (`permits_observed`) | record_key `f1f7fe6fbc23ae30`; jurisdiction_id 5502548000; stage issued; stage_date 2024-08-12; unit_category adu_detached; classification_method text_rule; units_added 1; match_method address_exact; match_quality confirmed; source_id madison_permits; area_id 55025001300; counted true |

### Unmatched example (BLDNRC-2026-21855)

- **Source:** Dwell 1, "NEW DETACHED GARAGE WITH ADU ABOVE", issued 10/16/2026, address `[####] NAKOOSA TRL`.
- **Classification:** `adu_detached` by text rule, counted.
- **Match:** the street is known, but neither the house number nor a same-parity neighbor within ±10 numbers exists in the current Address Points. The result is `unmatched` / `none` (rule `number_not_found`), with no parcel, tract or block group.
- **Effect:** the unit counts in the city-level total but in no tract. This lowers that year's `coverage` for `adu_detached` below 1.
- **Likely cause:** a new ADU address that is not yet published.

The full side-by-side table (source columns with owner and contractor fields redacted, beside cleaned columns) for these two and 6 other examples (one of them a Dwell-0 conversion, BLDRPR-2023-04213) is `data/processed/permits/source_vs_clean_examples.csv`.

## 9. Outputs

| File | Content | Shareable? |
| --- | --- | --- |
| `data/processed/permits/permits_observed.parquet` | Contract table, 5,755 in-scope records. Required columns plus year, permit_type, parcel_id, tract/bg, counted, match_rule, text_note, parcel_rule_reason, n_source_rows, units_from_text. Validated: no contract problems | Local only (record level) |
| `data/processed/permits/permits_records_full.parquet` | All 113,890 deduplicated permits with diagnostics | Local only |
| `data/processed/permits/permits_by_area_year.parquet` | City rows (45) and tract rows (638), by year × category. `units`, `coverage` (share of the city's counted units placed in a tract that year and category), `suppressed` (tract count 1–2), `status = observed`. Tract rows exist only where units > 0. A missing row means none observed among placed records, not a confirmed zero | Aggregate; suppressed cells need masking before publishing |
| `data/processed/permits/source_vs_clean_examples.csv` | Source vs cleaned rows for owner review | Local (has addresses) |
| `data/processed/permits/audit_sample.csv`, `audit_judgments.csv` | Audit sample with judgments | Local (has addresses) |
| `data/processed/permits/reconcile_city_table.csv`, `build_report.json` | Reconciliation and run summary | Aggregate |
| `reference/madison_adu_permits_by_year.csv` | year, category, count, units, method (text_rule, parcel_rule, parcel_rule+units_from_text, text_rule_excluded, city_published) | Committed |
| `data/sample/madison_permits.csv` (+ `.meta.json`, and the generated `docs/data-sources/madison_permits.md`) | 5 sample report rows from `scripts/fetch_samples.py` | Committed. House numbers are removed from addresses (street name kept) and embedded addresses in descriptions are masked, at fetch time (`ADDRESS_REDACTION` in `scripts/fetch_samples.py`). Owner and contractor columns are dropped |

**Privacy.** Committed files hold no record-level addresses: the sample above is redacted at fetch; this document gives house numbers as `[###]` and parcel numbers in masked form (`0709264042**`); the test fixtures use made-up addresses. Record-level outputs (with addresses and full parcel numbers) stay in `data/processed/permits/` and `data/raw/`, which are git-ignored.

**Disclosure threshold:** 3 is used provisionally. It should move into the run manifest when that exists.

**`parcel_stateid` is null:** a V12 STATEID crosswalk was not built. Madison parcel numbers are in `parcel_id`.

## 10. Known gaps

- **Stages:** only `issued` is observable. Application, final and withdrawn need Accela.
- **Multi-unit "duplex/twin ADU" records (10):** the ADU unit count cannot be determined from the report. All 10 are held out of the ADU series and counted as `other_residential` pending the Accela records.
- **Dwell-0 conversions:** only those whose text says "single family → two unit / duplex" are picked up (3 counted). Dwell-0 ADU-text records (BLDRPR-2014-13995, BLDRPR-2026-03870) stay uncounted, as before.
- **Accessory-building conversions:** 6 `adu_conversion` units (5 from garages or accessory buildings) are outside the headline under D5; the owner may want to revisit (§5).
- **City table:** 2013 (1) and 2023 (2) are unexplained.
- **Current-vintage parcel and assessor layers:** the rule cannot see historical parcel states; the timing guard is a proxy.
- **Text-rule limits:** ADUs described without ADU words are missed unless the parcel rule catches them. Geocoded and unmatched ADUs never get the parcel rule.
- **Adapter design:** a second city plugs in by subclassing `permits.base.CityAdapter`. It returns `STANDARD_COLUMNS` from `load_permits` and provides a parcel table and address reference. The pipeline, matcher, classifier and aggregation are city-agnostic. `host_uses` and the raze permit types are adapter settings.

## Changes in the repair round (2026-10-24)

Review items from the independent Gate 2 review, and their effect. Rebuilt with `uv run python scripts/build_madison_permits.py` from the cached raw files (no new permit download).

| Item | Change | Effect |
| --- | --- | --- |
| S3, multi-unit hosts | Host must have been a one-unit home: today 1–2 dwelling units and use "Single family" or "2 Unit" (was 1–3 and "3 Unit" allowed), with a text exception for explicit SF → two-unit conversions | BLDNCC-2010-15153 and BLDNCC-2016-12120 (2 → 3 apartments) move to `other_residential` |
| S3, judged false positive | `MadisonAdapter.parcel_rule_false_positives` (BLDNRC-2011-05399) fails the rule and is marked `units_suspect` | Removed from ADU-equivalents; no longer counted at all |
| S3, Dwell-0 conversions | SF → two-unit conversion text with Dwell 0 gets 1 unit from text (`units_from_text`) and is judged by the rule | BLDRPR-2014-04652, BLDRPR-2023-04213, BLDRPR-2023-18661 added |
| S3, bundles | ADU text bundles never pass the parcel rule either | BLDNRC-2026-06494 (2 units) moves to `other_residential`, like the other 9 |
| S3, match table | Corrected to 17 exact + 1 normalized (was stated as all exact; before the fix it was 18 exact + 1 normalized) | Doc only |
| S4 | City table described as permits issued (49); issue-year comparison added; permit-number year labeled our hypothesis | Doc and `reconcile_city_table.csv` (two new columns) |
| S1 | Sample redaction at fetch; addresses removed from this doc; fake addresses in fixtures and docstrings | No effect on counts |

**Before → after, counted units (permits where different):**

| Series | Before | After |
| --- | --- | --- |
| Text ADUs (detached / attached / conversion / legalization) | 57 / 1 / 6 / 0 = 64 units, 64 permits | **unchanged** (57 / 1 / 6 / 0 = 64) |
| ADU-equivalent ("second dwelling / conversion") | 21 units, 19 permits | 19 units, 18 permits (13 duplex conversions incl. 3 Dwell-0; 5 second dwellings / 6 units) |
| ADU-equivalent by year | 2010 1, 2011 2, 2014 1, 2015 2, 2017 3, 2018 1, 2019 1, 2024 1, 2025 1, 2026 8 | 2010 1, 2011 0, 2014 2, 2015 2, 2017 2, 2018 1, 2019 1, 2023 2, 2024 1, 2025 1, 2026 6 |
| other_residential | 37,247 | 37,251 (2011 +1, 2017 +1, 2026 +2) |
| All counted units | 37,332 (5,705 permits) | 37,334 (5,707 permits) |
| In-scope records | 5,752 | 5,755 |
| Units placed in a tract | 99.0% (372 unplaced) | 99.0% (372 unplaced) |
| Comparison cities (shared pipeline) | – | Unchanged: both reference files byte-identical |

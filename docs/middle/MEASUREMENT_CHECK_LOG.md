# Middle housing: measurement check log

Started 2026-11-08 (UTC) on Ryan's go-ahead. The question is how each source records middle housing, before any measure or test is locked. This file logs what was read, and confirms that no result was seen.

## No-peeking rules (fixed before any step)

**Tested places:**
- **States:** Oregon, California, Washington, Maine, Vermont, Montana and Arizona.
- **Cities:** every city on the candidate list: Minneapolis, Austin, Houston, Durham, Raleigh, Charlotte (Mecklenburg County), Walla Walla, Spokane, Sacramento, Arlington and Portland.
- **Treated period:** from each place's reform date (see [CANDIDATES.md](CANDIDATES.md)) onward.

**Allowed:**
1. Documentation: survey forms, instructions, data dictionaries, codebooks, statutes and rules.
2. Field lists and the list of distinct category values, without counts.
3. Records and counts from years before a place's reform.
4. Records and counts from places outside every test (for example, Wisconsin before its baseline window, or a no-law state not used as a comparison).
5. Reading single example records to learn how a type of project is filed, taken from before the reform or from places outside every test.

**Not allowed:**
- Any count, sum, rate or chart of a tested place's records after its reform date.
- Comparing before with after in any tested place.

**If a step breaks a rule by accident:** log it here with what was seen, and tell Ryan and the audit thread.

## Seen before these rules were written (disclosure)

On 2026-11-06, during step 1 ([CANDIDATES.md](CANDIDATES.md)) and before any rule existed, the lead researcher saw some post-reform numbers in tested places. They are listed here so the audit can judge any bias:
- Census permit units by building size, 2012–2025, for Minneapolis, Austin, Houston, Durham, Raleigh, Mecklenburg County, Walla Walla, Spokane, Sacramento, Arlington and Portland (yearly table, read on screen).
- Washington state agency (OFM) yearly permits by structure for Spokane and Walla Walla, 2012–2026.
- Portland city permits, new units by permit type per year, 2012–2026.
- California progress reports: statewide SB 9-flagged permitted units by unit category, 2022–2025.
- Published post-reform counts quoted in CANDIDATES.md (Raleigh, Austin, Durham, Arlington, Spokane, Portland and others), from city reports and studies.
- No before/after comparison or rate was computed from any of these.

The Oregon cutoff power check (2026-11-06) used only 2012–2019, which is before the Oregon law.

## Log

| When (UTC) | Who | Source | What was read | Rule used | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-11-08T00:28Z | lead | ORS 92.031 (oregonlegislature.gov/bills_laws/ors/ors092.html) | Middle housing land division: one unit per new lot; the plat may carry a notation; history 2021 c.103 (SB 458), 2024 c.102, 2025 c.476 | 1 | Lot-split middle housing is filed as one home per lot, so permits may show 1-unit homes |
| 2026-11-08T00:29Z | lead | ORS 197A.110 (ors197A.html) | Cities of 10,000+ report units permitted and produced each year, split into single-unit, ADU, middle housing and other multiunit (2023 c.13 §37) | 1 | State middle-housing count exists for cities of 10,000+ only, so no below-cutoff comparison |
| 2026-11-08T00:30Z | lead | OHCS dashboard methods page (oregon.gov/ohcs) | DLCD Housing Production Survey has data from 2018; to be replaced by a PSU survey (AHUPS) | 1 | Survey files and categories by year not yet found |
| 2026-11-08T00:27–00:35Z | helper: Census and states | Census BPS forms, definitions, methodology, FAQ, file layout; BPS place files 2015 (all US); WA OFM definitions, FAQ, Readme, file header and 3 rows from 1990–92; WA duplex odd-value check, estimate years 2018 and earlier; Maine MOCA instructions and form; Vermont layer field list and distinct values | 1, 2, 3, 5 | Full list: [measurement/CENSUS_AND_STATES.md](measurement/CENSUS_AND_STATES.md) |
| 2026-11-08T00:27–00:31Z | helper: California | APR Table A2 and Table A dictionaries; APR instructions (Jan 2026); distinct values of six A2 fields (no counts); about 17 example rows from 2018–2021 (Sacramento County, not the city); SB 9, SB 684, SB 1123, AB 803 texts; Census BPS definitions | 1, 2, 3, 5 | Full list: [measurement/CALIFORNIA.md](measurement/CALIFORNIA.md). It avoided `api/table_a2_year_unitcat.json`, which holds counts for all years |
| 2026-11-08T00:27–00:35Z | helper: cities | Metadata, distinct values and pre-reform example records for Raleigh, Mecklenburg, Minneapolis, Sacramento, Austin, Portland, Durham; Houston field list only; licence and terms pages | 1, 2, 5 | Every records query had a date filter ending before the reform. Full list: [measurement/CITIES.md](measurement/CITIES.md) |

| 2026-11-09 | lead | Census place permits 2012–2018 (all US), ACS B25024, PSU 2020 city list | Power check ([POWER_CHECK.md](POWER_CHECK.md)); the script never reads permit files after 2018; candidate cities were never read as stand-ins | 3, 4 | Only population and homes were read for the five Test 3 cities, never their permits |
| 2026-11-09 | lead | HCD Table A2, report years 2018–2021 only | Size mix of "5+" rows (5–6 unit share) | 3 | Before SB 9; no 2022+ rows read |

## Edge cases reported by helpers

- **Washington stock file:** a header command saved about 50 data rows (Adams to Clark counties) to a local tool file. Only place names and 1980-era totals were viewed. No row from 2019 on, and no Spokane or Walla Walla row, was shown.
- **Maine 2025 summary (after Maine's 2024 reform):** a keyword search showed two sentences with the digits masked. Most permitted units were single-family, followed by 5+ unit buildings, and ADUs "contributed considerably". One masked figure: "1,## units" in Census-filled towns.
- **Census national quarterly table:** a digit mask missed two-digit numbers. One U.S. row and one regional row of multifamily size groups were shown, with no year. These are not tested places.
- **Raleigh labels:** distinct values of `missing_middle` and `adu_type` were listed across all years, with no counts. They show that "Yes" and "Internal ADU" exist in some year.
- **Sacramento:** the first 2 rows were read with no date filter, to learn the date format. Both were dated 2016-01-01, before the reform.
- **Raleigh Missing Middle Metrics page:** a fetch helper read it with orders to return definitions only. Its summary had no numbers. The linked PDF and dashboards were not opened.
- **Portland:** a script loaded later rows into memory but dropped them by date before printing anything.

None of these is a count of a tested place after its reform, and no before/after comparison was made.

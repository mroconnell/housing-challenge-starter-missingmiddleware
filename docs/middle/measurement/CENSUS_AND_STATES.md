# How Census BPS, WA OFM, Maine MOCA and Vermont record middle housing

Prepared 2026-11-08 (UTC). This covers how each source records projects. No tested-place result after a reform date was counted. Two accidental glimpses are listed in section 6.

V = official document. S = secondary source, or our own inference from official text.

## 1. Census Building Permits Survey (BPS)

| Case | How recorded | Source | V/S |
| --- | --- | --- | --- |
| Townhouse / rowhouse | **1-unit ("single-family attached")** only if all 3 tests pass: (1) a ground-to-roof wall between units; (2) no unit above or below another; (3) separate heating and separate utility meters. Otherwise the whole building goes in 2, 3–4 or 5+ by its unit count. Condo or co-op ownership is ignored. | C-404 form, item 3b and back page; BPS Definitions ("Single-Family House", "Multifamily Housing"); Respondent FAQ, Classification Q3–Q5 | V |
| Lot-split home (e.g. SB 9) | **No lot concept at all.** Each new building is classed by its structure. 2 detached homes = 2 one-unit buildings. An attached pair across the lot line = 2 one-unit buildings if it passes the 3 tests, else 1 two-unit building. A split or subdivision with no new building records nothing. | C-404 3b–3e; Definitions "Structure, Type of" (no lot or parcel field anywhere) | V for the rule; S that splits are invisible |
| Small-lot detached home | 1-unit, same as any detached house. Can't be told apart from a standard-lot house. Lot size exists only in SOC microdata (AREA, by Census Division; see below). | C-404 3b; SOC microdata guide, variable 29 AREA | V |
| Duplex | Side-by-side duplex passing the 3 tests: **2 one-unit buildings**. Stacked, or with shared heating or utilities: **1 two-unit building**. | Respondent FAQ, Classification Q6 "Where do I classify a duplex"; C-404 3c | V |
| Triplex / fourplex | 3–4 unit building (one combined category), unless every unit passes the 3 tests; then each unit is 1-unit. **3 vs 4 can be split exactly:** 4-unit buildings = units − 3 × buildings, and 3-unit buildings = buildings − 4-unit buildings. Methodology says 3–4 units per building must be 3 or 4. | C-404 3d; Methodology, imputation edit rules; arithmetic (S) | V rule; S formula |
| 5–6 unit building | In **5+**, with 5–500 units per building. No 5–6 category in the BPS. You get only buildings and units for 5+, per place and year, so average size = units ÷ buildings. Two exact cases: one 5+ building with 5 or 6 units, or units = 5 × buildings (all buildings have 5 units). Otherwise the bound is: buildings with ≥7 units ≤ (units − 5 × buildings) ÷ 2, rounded down. Imputed 5+ buildings and units are imputed **separately**, so the average size of an imputed record is modelled, not observed. SOC national and regional tables have a 5–9 unit bucket (see below). | Methodology ("Units and buildings for the 5+ structure type are imputed independently"; edit limit "at least 5 and less than 500"); place file layout | V; S bound |
| ADU | **No ADU category.** A detached ADU that is a new building would count as a 1-unit house, if the office reports it. An internal or attached ADU is excluded as a unit "created in an existing residential structure" or as an addition. Maine's report agrees: "ADUs created through additions or conversions are generally excluded" from BPS. | Definitions "Housing Unit" (excludes units created in existing structures); C-404 exclude list ("residential additions, alterations, renovations and conversions"); Maine 2025 summary note (S) | V exclusion rule; S detached-ADU treatment |
| Conversion (house to duplex) | **Excluded.** Not new construction. A total rebuild on an existing foundation counts as new. Moved or relocated buildings are excluded. | C-404 "Permits to exclude"; Definitions; FAQ Classification Q7–Q9; FAQ General Q12 (additions and alterations no longer collected) | V |
| Addition creating a unit | Excluded (same rule as conversions). | Same as above | V |

**Mechanics:**
- **When counted:** at permit issuance, in the month or year issued. Cancelled or abandoned permits are not removed. Reissued expired permits count only if plans changed a lot. (FAQ Classification Q17–Q18.)
- **Unit of count:** buildings and units by structure type. A multifamily building permitted unit by unit is reported once, with the total expected units, when the first units are authorized. For phased permits, units are counted at the shell or superstructure permit. (C-404 back page; FAQ Q10 and Q16.)
- **Imputation:**
  - When a place doesn't report, its data come from the SOC or third-party data (Construction Monitor), or are imputed. Imputed value = the place's prior-year total × a cell ratio (current ÷ prior for reporters).
  - Cells: division or large state × inside/outside a metro area (CBSA) from 2025; region × CBSA before 2025.
  - Item cells: 1-unit; 2–4 units (buildings for 1-unit and 2–4 use the unit factors); 5+ units and 5+ buildings imputed separately.
  - Annual precedence: reported annual total, then the sum of 12 reported months, then the imputed annual figure. (Methodology.)
- **Place annual file columns** (placeasc.pdf, Attachment B): field 16 is "Number of months reported." Fields 18–29 are estimates with imputation; fields 30–41 are reported-only. Each block gives buildings, units and value for 1, 2, 3–4 and 5+ units.
- **Months-reported check, 2015, all U.S. places** (pre-reform for every tested place, rule 3). Unit: place rows; total 20,122.

  | Months reported | Place rows | What the row holds |
  | --- | --- | --- |
  | 0 | 2,868 | Reported-only block is all zero. 1,547 rows have imputed units above zero. |
  | 12 | 16,022 | Estimated block = reported block in every row. Annual reporters show as 12. |
  | 1–11 | 1,232 | 817 rows have estimated ≠ reported. |

  So "months reported = 12 and estimated = reported" marks fully reported rows.
- **Do 2-unit buildings × 2 = units?** Yes, in 2015 for all U.S. places. Unit: place rows with any 2-unit activity.

  | Block | Rows with 2-unit activity | Rows where units ≠ 2 × buildings |
  | --- | --- | --- |
  | Estimated | 1,483 | 0 |
  | Reported-only | 1,337 | 0 |

  There were also 0 exceptions for 1-unit (units = buildings), 0 for 3–4 (units between 3 × and 4 × buildings) and 0 for 5+ (units below 5 × buildings). The imputation edit rules force these identities.
- **How many 2015 place rows can say anything about 5–6?** Estimated block; unit: place rows with 5+ activity, total 1,712.

  | 5+ pattern | Place rows | Share |
  | --- | --- | --- |
  | Average ≤ 6 units per building | 278 | 16% |
  | Exactly one building of 5 or 6 units (exactly known) | 126 | 7% |

  Reported-only block: 204 and 105 of 1,479 rows.
- **Coverage notes that matter for tests:**
  - Montana footnote @1: in some areas the state issues permits only for 5+ buildings, and **no permits are required for 1–4 unit buildings**. So BPS can't see small Montana buildings there.
  - Footnotes @3–@5: some permit systems cover only 1–2 or 1–3 family buildings.
  - Source: placeasc.pdf, part D.
- **Unit response rate in 2024** (Methodology). Unit: share of requested reports received.

  | Measure | Rate |
  | --- | --- |
  | Revised monthly estimates | about 66% |
  | After the annual survey | about 81% |
  | Share of 2024 final annual units based on reported (or equivalent) data | about 90% |

- **Does Census publish townhouses separately?** Yes, but only nationally and by region:
  - NRC "Quarterly Starts and Completions by Purpose and Design" (quarterly_starts_completions.pdf/.xlsx): Tables Q1–Q10 cover the U.S. and the 4 regions. Single-family is split into **Detached / Attached**. Multifamily is split by units per building: **2–4, 5–9, 10–19, 20+**.
  - SOC microdata (socmicro_info.pdf): DET (1 = detached, 2 = attached), DIV (9 Census Divisions only), and AREA (lot square feet, capped at 2,000 at the low end).
  - Neither series has state or place detail. Neither covers places, so neither can measure a tested place.

## 2. Washington OFM (April 1 permits file)

File: `data/raw/statewide_states/wa/ofm_april1_postcensal_permits_1990-present.xlsx`, sheet PermitCompletionDemolition.

Columns: County Name, City Name, Estimate Year. Then Permitted, Completed and Demolished for: Single Family units; Duplexs; 3/4 units; Five+ units; Accessory Dwelling units.

| Case | How recorded | Source | V/S |
| --- | --- | --- | --- |
| Townhouse / rowhouse | **Not 1-unit.** "Single family attached structures such as row homes, townhouses and condominiums should be categorized as multi-unit structures based on the total number of units." So a row of 3 is "3/4" and a row of 6 is "Five+". **This is the opposite of Census.** | ofm_april1_definitions.pdf p.1 | V |
| Lot-split home | No lot field. A detached home is "Single Family" (1-unit detached). | definitions p.1 | V rule; S |
| Small-lot detached home | Single Family; can't be separated. | definitions p.1 | V |
| Duplex | "Duplexs" = a 2-unit structure. Side-by-side or stacked doesn't matter. | definitions p.1 | V |
| Triplex / fourplex | "3/4 units" (combined). | definitions p.1 | V |
| 5–6 unit building | "Five+" ("5-or-more unit structure"). Can't be separated: the file has units only. Form A collects structures too (section A1), but the published file doesn't show them. | definitions p.1; Form A FAQ p.3; xlsx header | V |
| ADU | **Separate column** (collected since 2010). Attached or detached, with its own kitchen, sleeping and bathroom, on a single-family lot. Tiny homes permitted as long-term housing are reported as ADUs. | definitions p.1; Readme sheet; Form A FAQ p.6 | V |
| Conversion (house to duplex) | **Counted as a paired record:** one lost unit (Demolished Single Family) plus a new 2-unit structure permit. Example given: a house converted to 4 units = 1-unit removal + new fourplex. A commercial-to-residential conversion counts as a new structure permit. | Readme sheet; definitions p.1; Form A FAQ p.5–6 (section A3) | V |
| Addition creating a unit | Recorded as a conversion: a change in unit count is a removal plus a new structure. An attached ADU would go in ADU. | definitions p.1 "Conversion" | V; S for the ADU case |

**Mechanics:**
- **Estimate year Y** = April 2 of Y−1 through April 1 of Y. Exception: unincorporated county data for 2011–2019 are by calendar year. (Readme.)
- **Column meanings:**
  - Permitted = issued in that year.
  - Completed = may come from earlier permits (section A2 "carryover").
  - Demolished = demolitions, conversions, or disaster losses. Disaster losses are likely under-reported.
- **Not adjusted:** figures are not adjusted to the Census. OFM "follows federal census classifications … as much as practicable", but its townhouse rule differs.
- **Values are units, not structures.** Check on pre-2019 estimate years only (rule 3). Unit: city-year rows; numerator is rows with an odd duplex value.

  | Column | Rows above zero | Rows with an odd value |
  | --- | --- | --- |
  | Permitted duplex | 2,298 | 89 |
  | Completed duplex | 2,160 | 153 |

  Mostly even values, so the column holds units. The odd rows suggest conversions or reporting quirks.
- **WA housing-stock file** (ofm_april1_postcensal_estimates_housing_1980_1990-present.xlsx): stock by structure type, built from completions and annexations. I read only its Readme.

## 3. Maine MOCA / GPCOG 2025 Statewide Housing Survey

| Case | How recorded | Source | V/S |
| --- | --- | --- | --- |
| Townhouse / rowhouse | "Single-Family Houses: … townhouses, or rowhouses." Census-style test for side-by-side duplexes: own entrance, separate heating and utilities → each unit is single-family. | Jotform "Additional Instructions & FAQs" (form 253523632685057) | V |
| Lot-split home | No lot field. Single-family. | same | V; S |
| Small-lot detached home | Single-family; can't be separated. | same | V |
| Duplex | "2 Unit Buildings": stacked always; side-by-side if heating or utilities are shared. | same, FAQ "duplex split down the middle" | V |
| Triplex / fourplex | "3-4 Unit Buildings" (combined; triple-deckers, 4-unit apartments). | same | V |
| 5–6 unit building | "5 or More Unit Buildings". **Units only** ("report the number of new housing units added, not the number of buildings"), so 5–6 can't be separated. | same | V |
| ADU | **Separate row**, attached or detached. **But** towns that don't track ADUs put them in single-family, and Census-filled towns have no ADU split. | same; 2025 summary notes | V |
| Conversion / addition | **Included** (unlike Census). Only the new units are reported, in the final building type. A house converted to a stacked duplex = 1 new unit in "2-Unit". | same, FAQ "renovation or addition" | V |

**Mechanics:**
- **Measures:** permits and certificates of occupancy (COs) by type, plus demolitions with no type, for calendar 2025.
- **Where permits aren't issued:** units "approved for construction" are reported instead.
- **Who must report:** towns of 4,000 or more people (LD 1184). Gaps are filled with Census BPS and LUPC data.
- **Mixed sources:** survey responses, LUPC and BPS are mixed in one dataset, so the definitions differ by source (ADUs; conversions).
- **Survey years:** survey questions only. Not seen: 2025-edition instructions earlier than calendar 2025, or earlier survey years.
- **Respondents' complaints:** the summary says respondents asked for clearer definitions, including how to classify duplexes.
- **Detailed-report xlsx:** not read (`_downloads.json` says it holds no permit or ADU data).

## 4. Vermont (VCGI "Vermont_New_Housing" layer)

| Case | How recorded | Source | V/S |
| --- | --- | --- | --- |
| All cases | One point per E911 site with UNITCOUNT and YEARBUILT. SITETYPE is the E911 site-use code; Sitetype_General groups it (see below). | Layer metadata FeatureServer/0?f=json (field list, no descriptions); distinct values from on-disk JSON | V field list; S meaning |
| Townhouse | **No townhouse or attached code.** Probably MULTI-FAMILY DWELLING or CONDOMINIUM, or SINGLE FAMILY DWELLING per address point; can't be told apart. | — | S |
| Duplex / triplex / fourplex / 5–6 | **No 2, 3–4 or 5+ codes.** Every multi-unit site is "MULTI-FAMILY …"; size comes only from UNITCOUNT per site. A site may not equal a building. | — | S |
| ADU | SITETYPE "ACCESSORY DWELLING UNIT", grouped under SINGLE FAMILY DWELLING. Also an ADU_VHIP flag, likely the Vermont Housing Improvement Program. | distinct values; field list | V value; S meaning |
| Lot split / small lot | No lot field. PARCELNUM exists, so in principle you can tell when several sites share a parcel. | field list | S |
| Conversion | Not identifiable. YEARBUILT is a site attribute; there's no conversion flag. | — | S |

Sitetype_General groups (distinct values only, no counts):

| Group | SITETYPE values |
| --- | --- |
| SINGLE FAMILY DWELLING | SINGLE FAMILY DWELLING; ACCESSORY DWELLING UNIT; MOBILE HOME |
| MULTI-FAMILY DWELLING | MULTI-FAMILY DWELLING; MULTI-FAMILY RESIDENCE; MULTI-FAMILY COMPLEX; CONDOMINIUM |
| OTHER RESIDENTIAL | OTHER RESIDENTIAL; RESIDENTIAL OTHER; RESIDENTIAL / MIXED USE; COMMERCIAL W/RESIDENCE; CAMP; SEASONAL CAMP; SEASONAL HOME; RESIDENTIAL FARM; GROUP QUARTERS; blank |

Other fields: SOURCEOFDATA (E911 Board, CCRPC, VHFA, some towns), PRE2016, FOOTPRINT_2016, VERIFIED, UTILITYID/UTILITYYEAR/UTILITYCOUNT.

The ArcGIS item (4f37b1d984274ee398bfa9a93c5b8c19, owner User_VCGI) has **no description and no licence text**. VCGI says the newer E911 schema has 114 SITETYPE values, but I found no definitions document. Vermont is a measure of sites by year built, not permits.

## 5. Bottom line for choosing a measure

- **Townhouses are classified in opposite ways.** Census BPS and Maine count them as 1-unit, which mixes them with detached houses. WA OFM counts them as multi-unit by total units in the row.
- **Lot splits and small lots are invisible in every source.** Neither BPS, OFM, Maine nor VT has a lot field. Census SOC has lot size only by Census Division.
- **5–6 units can't be separated anywhere at place level.** Census BPS gives a bound from 5+ buildings and units, plus exact cases. Census national and regional SOC tables have a 5–9 unit bucket.
- **3 vs 4 units is exact in BPS** (units − 3 × buildings).
- **Conversions are out in BPS** but in for OFM (as a removal plus a new structure) and Maine (net new units).
- **Only OFM and Maine have ADU columns.** Vermont has an ADU site type.

## 6. Audit log (UTC, 2026-11-08)

| # | Time | Item read | Rule |
| --- | --- | --- | --- |
| 1 | 00:27:51 | docs/middle/MEASUREMENT_CHECK_LOG.md (rules) | 1 |
| 2 | 00:28 | wa/ofm_april1_definitions.pdf (pdftotext, both pages) | 1 |
| 3 | 00:28 | wa/ofm_april1_formA_faq.pdf (all 12 pages) | 1 |
| 4 | 00:28 | wa/_downloads.json | 1 |
| 5 | 00:28 | OFM permits xlsx: Readme sheet + PermitCompletionDemolition header + 3 example rows (Adams/Hatton 1990–1992) | 1, 2, 5 |
| 6 | 00:28 | OFM housing-stock xlsx: Readme sheet. **Incident:** see note A. | 1 |
| 7 | 00:29 | docs/middle/CANDIDATES.md lines with WA, ME and VT reform dates | 1 |
| 8 | 00:29 | me/_downloads.json; me_summary.txt: table of contents, Background section (digits masked), survey-questions section (masked), feedback section (masked), keyword grep (masked). **Incident:** see note B. | 1 |
| 9 | 00:29 | Maine PDF hyperlink list (found the 2 Jotform URLs) | 1 |
| 10 | 00:29:42–00:29:45 | census.gov/construction/bps definitions.html, methodology.html, index.html, forms.html, pdf/c404.pdf; form.jotform.com/253523632685057 (ME instructions & FAQ); form.jotform.com/251103173721141 (ME survey form; viewed only, **not submitted**) | 1 |
| 11 | 00:30:24–00:31:07 | census.gov/permitsfaq; bps/faqs/gen_faq.html, class_faq.html, def_faq.html, data_faq.html | 1 |
| 12 | 00:31:45–00:31:50 | www2.census.gov/econ/bps/Documentation/ (listing) and placeasc.pdf | 1 |
| 13 | 00:31 | BPS place files mw/ne/so/we 2015a.txt: header plus identity checks (2-unit = 2 × buildings, etc.), months-reported versus estimated/reported | 3 (2015 is before every tested reform) |
| 14 | 00:32 | vt/_downloads.json; distinct SITETYPE, Sitetype_General and SOURCEOFDATA values from the on-disk JSON (no counts read) | 2 |
| 15 | 00:32:21–00:32:27 | VCGI FeatureServer/0?f=json layer metadata; arcgis.com item 4f37b1d9… metadata | 1 |
| 16 | 00:32 | Web searches: VT E911 SITETYPE definitions; Census ADU; Census attached single-family | 1 |
| 17 | 00:32:55–00:33:52 | census.gov/construction/pdf/bps_general_faqs.pdf, bps_2023_faqs.pdf, nrc/index.html, nrc/definitions.html (empty shell), nrc/data.html, nrc/quarterly.html, chars/microdata.html, chars/pdf/socmicro_info.pdf, nrc/pdf/quarterly_starts_completions.pdf (table titles and column labels only, digits masked). **Incident:** see note C. | 1 |
| 18 | 00:34 | OFM permits xlsx: share of odd duplex values, estimate years ≤ 2018 only | 3 |

User agent on every HTTP call: "missing-middleware-research/1.0 (public data)". No email was sent and no forms were submitted. No repository files were edited. Scratch copies were kept in the session scratch folder (subfolders dl/, txt/, scripts/).

**Incident notes:**

- **A (item 6).** A header-printing command also wrote up to about 50 data rows of the "Housing Units" sheet (stock by structure type for Adams through Clark counties) to a local tool-output file (not in the repo).
  - I viewed only the place names and the first 1–2 numbers per row (1980-era stock counts, before any reform).
  - No values from 2019 or later, and no Spokane or Walla Walla rows, were displayed.
  - Those cities are alphabetically outside the printed range.
- **B (item 8).** The keyword grep of the Maine 2025 summary (calendar-2025 data, after Maine's 2024 reform) showed two qualitative result sentences (digits masked):
  - Most permitted units "were single-family homes, followed by larger multifamily developments of five or more units".
  - "ADUs also contributed considerably to housing production".
  - Also one masked figure: BPS-filled towns accounted for "1,## units".
  - This is a statewide, post-reform rank-order statement. Please log it for Maine.
- **C (item 17).** My digit mask on the national Census quarterly table missed 2-digit values. One U.S. annual row and one regional annual row (year not shown) were displayed, with values like 13, 16, 31, 54, 52 in thousands of units, by multifamily size bucket.
  - These are national or regional aggregates, not a tested place.
  - No before/after comparison was made.

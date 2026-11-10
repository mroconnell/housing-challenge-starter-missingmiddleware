# California: how the data record middle housing (measurement check)

Done 2026-11-08 UTC. Documentation, distinct values and 2018–2021 example rows only. **No counts of any California record were read or made, for any year.** V = official page (HCD, data.ca.gov, leginfo, census.gov). S = secondary source. "Inferred" = my reading of V documents, not stated outright.

## Key facts

- **One row = one project, per stage, per report year.** HCD's definition (V, instructions def. 20) is a project or development. In practice, jurisdictions often file **one row per building permit**. Example: Claremont 2021 has three SFA rows on one APN, each with its own permit number and 1 unit (rule 5).
- **One project shows up in several years.** The instructions say to list a project in each year it reaches a stage: entitled, then permitted, then completed (V, A2 intro). For permits, count `NO_BUILDING_PERMITS` and use `BP_ISSUE_DT1` for the year.
- **UNIT_CAT is one code per row.** The definitions are per **structure** ("units per structure"; V). There is no separate building count. A mixed project (for example, a lot split with a house plus an ADU) has to be split into rows, or it gets one code.
- **No SB 684 or SB 1123 flag exists.** It is missing from the A2 data dictionary, the Table A dictionary, the Jan-2026 instructions (Table A field 9 and A2 field 13), and the distinct values in the file. Projects under these laws cannot be found from a flag.
- **SB 9 flags start with the 2023 APR.** The A2 and Table A dictionaries both say "For 2023 APRs and into the future" (V). For 2018–2022 the field was SB 35 yes/no only. So 2022, SB 9's first year, has **no SB 9 flag**: inferred from the dictionary wording, not checked in the data.
- **Lot splits:** Table A (applications) may hold an SB 9 lot-split row with **0 or blank units** (V, Table A field 5). Lot splits are recorded only through this flag. APR has **no general parcel-map or subdivision table**.
- **Data note:** the data.ca.gov A2 CSV was updated 2026-11-06. Our copy on disk is from 2026-10-24. The Table A CSV was also updated 2026-11-06.

## Table 1: case → how it is recorded in APR

| Case | How recorded in APR (Table A2; Table A similar) | Source | V/S |
|---|---|---|---|
| Townhouse (ground-to-roof wall, own heating and plumbing) | **SFA**, defined as "commonly referred to as a townhouse, half-plex, or row house". In practice filing is mixed: 2021 rows show townhome projects filed as SFA, "2 to 4" and even "5+", so coding follows the building or local habit. | APR Instructions def. 24; A2 dictionary; example rows (San Luis Obispo "NG-30 Townhomes" as 2 to 4 and 5+; Sacramento County "Olive Grove Town Homes" as 5+) | V (definition); V-data (examples) |
| SB 9 urban lot split home (house on a new SB 9 parcel) | Unit row coded by building type: **SFD** if detached, SFA if attached. Flag `APPROVE_SB35` = "SB 9 (2021) - Residential Lot Split", possibly combined with "Duplex in SF Zone". The flag is only on 2023+ APRs. The split itself may be a Table A application row with 0 units. | Instructions Table A field 5 and 9, A2 field 13; A2 dictionary | V (fields); inferred (SFD coding) |
| SB 9 two-unit project / "duplex" on one SF lot | Flag "SB 9 (2021) - Duplex in SF Zone". UNIT_CAT follows the building: one 2-unit structure → **2 to 4**; two detached houses → **SFD**; attached with a ground-to-roof wall → SFA. Under 65852.21(i)(1), adding one new unit next to an existing house counts as two units; the APR row would show 1 new unit. | Instructions def. 24 and A2 field 13; Gov. Code 65852.21 | V (fields); inferred (coding) |
| Small-lot subdivision home (SB 684 / SB 1123, Gov. Code 66499.41; also AB 803, 66499.40) | **No flag.** Coded by building type: usually SFD or SFA, or 2 to 4 / 5+ if stacked. Only `APN`, `PRIOR_APN`, `PROJECT_NAME`, `NOTES` and the "SMAP" option might hint at it. SMAP is not defined in the instructions I read; do not assume it means SB 684. | A2 dictionary; instructions field 13 option list (no SB 684 / 1123) | V |
| Ordinary duplex (not SB 9) | **2 to 4** if one 2-unit structure. Two side-by-side units with a ground-to-roof wall and separate systems → SFA ("half-plex"). Errors exist: a Tulare County duplex note was coded **ADU**. | Def. 24; example rows (San Luis Obispo "Issued/Duplex" = 2 to 4; Tulare "SFD (Duplex)" = ADU) | V |
| Triplex / fourplex | **2 to 4** ("structure containing two, three, or four units"). Errors exist: Marysville "Fourplex" 2021 coded **MH**. | Def. 24; examples (San Diego "Tesoro Triplex" = 2 to 4) | V |
| 5–6 unit building | **5+** ("5 or more units per structure"). Cannot be told apart from large apartment buildings except by the unit counts in the row. A row can mix buildings, so row units ≠ building size. | Def. 24 | V |
| ADU / JADU | **ADU**, which covers attached, detached, within the dwelling, efficiency units, and manufactured homes used as ADUs. Counted as new units for RHNA. | Def. 18 and 24 | V |
| Conversion (garage, or non-residential to residential) | Garage/space → ADU: coded **ADU** (examples: Stanislaus County 2020 "CONVERT ... GARAGE TO ... ADU"). Motel, hotel or other non-residential to residential: **Table A2 as net new units**, not Table F. Market-rate to deed-restricted moderate conversions: **Table F2** (2-4 or 5+, not new units). Conversion of a house into 2–4 units has **no conversion flag**; it is coded by structure and possibly a note. | Instructions Table F and F2 text; examples | V |
| Demolition / replacement | All new units are reported in full. Lost units go in `DEM_DES_UNITS`, with `DEM_OR_DES_UNITS` and tenure. No negatives. | A2 "Net new units" | V |
| Mobile home | **MH**: one-unit structure built on its own chassis. New park spaces count. | Def. 24 | V |

## Table 2: other fields that matter

| Field | Content | V/S |
|---|---|---|
| `APPROVE_SB35` (A2) | 2018–2022 APRs: Y/N, meaning approved under SB 35 (65913.4(b)). 2023+ APRs: "streamlining provision(s)", multiple allowed: NONE; SB 9 (2021) – Duplex in SF Zone; SB 9 (2021) – Residential Lot Split; AB 2011 (2022); SB 6 (2022); SMAP; SB 4 (2023). Distinct values in the file (no counts): `0`, `N`, `Y`, `NONE`, `SB 35 (2017)`, `SB 423 (2023)`, `AB 2011 (2022)`, `SB 6 (2022)`, `SB 4 (2023)`, `SMAP`, `SB 9 (2021) - Duplex in SF Zone`, `SB 9 (2021) - Residential Lot Split`, plus the two SB 9 values combined with ", " or ";" in either order. Because separators differ, **parse by substring**. | V |
| `APP_SUBMITTED_SB35` (Table A) | Same 2023+ option list. 2018–2022: No / Yes-But no action taken / Yes-Approved / Yes-Denied. Table A also has `APPLICATION_STATUS`, `TOT_PROPOSED/APPROVED/DISAPPROVED_UNITS`, `DENSITY_BONUS_RECEIVED/APPROVED`, `APP_SUBMIT_DT`. The instructions (Jan-2026) add a ministerial/discretionary field (Table A field 14); I have not checked whether the CSV has it. | V |
| `INFILL_UNITS` | Y/N. Infill = in a Census urbanized area, on land previously used for urban purposes, or vacant with 2+ sides next to urban uses. Distinct values in the file: `0`, `N`, `Y`. | V |
| Density bonus | `DR_TYPE` (DB / INC / Other), `DENSITY_BONUS_TOTAL` (%), `DENSITY_BONUS_NUMBER_OTHER_INCENTIVES`, `DENSITY_BONUS_INCENTIVES`, `DENSITY_BONUS_RECEIVE_REDUCTION` (parking) | V |
| `TENURE` | Owner or Renter in the file (the dictionary says R/O) | V |
| `UNIT_CAT` distinct values | `2 to 4`, `5+`, `ADU`, `MH`, `SFA`, `SFD`. There is no SH value in A2; SH is for Table J only. | V |
| `PRIOR_APN` / `APN` | Optional prior APN. This is the only parcel-change trace and could be used to detect splits or subdivisions, but it is optional and patchy (inferred). | V |
| `YEAR` distinct values | 2018–2025 | V |

**Instructions version:** "Housing Element APR Instructions", PDF of 33 pages, created 2026-01-26 and modified 2026-01-30. It cites the laws behind the APR form, up to AB 3093 and AB 2580 (2024). It does **not** cite SB 9, SB 684 or SB 1123.

## Table 3: laws

| Law | Chapter | Signed | Effective / operative | What it does | Code | V/S |
|---|---|---|---|---|---|---|
| SB 9 (Atkins, 2021) | Stats. 2021, Ch. 162 | 2021-09-16 | 2022-01-01 (non-urgency bill, so it starts Jan 1 of the next year) | Two units allowed by right on a single-family lot (65852.21). Urban lot split into 2 parcels, each at least 1,200 sq ft and at least 40% of the original lot (66411.7). Only one split per lot; no splitting an adjacent lot the same owner already split. 3-year owner-occupancy affidavit. Units at least 800 sq ft. Up to 4 units across the 2 new lots, since 66411.7(j) caps each at 2. Projects decided within 60 days or deemed approved. | 65852.21; 66411.7; amended 66452.6 | V (leginfo status page and code text). The effective date is inferred from the non-urgency label. |
| SB 9 later amendment | Stats. 2026, Ch. 56 (SB 1426) | — | 2026-06-30 | Changes the current text of 65852.21 and 66411.7, including the 60-day deadline and the rule allowing adjacent or connected structures. I have not checked what the changes are. | same | V (history note only) |
| AB 803 "Starter Home Revitalization Act of 2021" | Stats. 2021, Ch. 154 | (not checked) | 2022-01-01 | Small home lot developments: detached single-family homes on fee-simple lots, on multifamily-zoned lots of 5 acres or less. Average home 1,750 sq ft or less. | 66499.40 (Chapter 8 of Map Act) | V |
| SB 684 (Caballero, 2023) | Stats. 2023, Ch. 783 | 2023-10-11 | Statute effective 2024-01-01. Main provisions **operative 2024-07-01**; horsekeeping exemption operative 2024-01-01. | Required ministerial approval of a parcel or tentative map for **10 or fewer parcels and 10 or fewer units** on a **multifamily-zoned** lot of 5 acres or less, substantially surrounded by urban uses. Parcels at least 600 sq ft. Average home 1,750 net sq ft or less. Decision within 60 days. Also allowed building permits before the final map (65913.4.5). | Added 65852.28, 65913.4.5, 66499.41 | V |
| SB 1123 (Caballero, 2024) | Stats. 2024, Ch. 294 | 2024-09-19 | Statute effective 2025-01-01. **Operative 2025-07-01**. | Extended 66499.41 to **vacant single-family-zoned lots of 1.5 acres or less**. Parcels at least 1,200 sq ft on SF-zoned land. Density floor lowered to 66% of maximum. ADUs and JADUs do not count toward the 10. Tenancy-in-common allowed. Height may be capped at the existing zone limit on SF lots. | Amended 65852.28, 66499.41 | V |
| AB 130 (2025 budget trailer) | Stats. 2025, Ch. 22, Sec. 28 | — | 2025-06-30 | Later amendment to 66499.41, including a remainder-parcel rule and a new sale/lease/finance rule (66499.41(e)). I have not checked the details. | 66499.41 | V (history note) |

**Census BPS and SB 9 (V, census.gov definitions, FAQ and C-404 form):** BPS classifies by **building**: 1-unit (detached plus attached with a ground-to-roof wall, no unit above or below, separate heating and utility meters), 2-unit, 3–4, and 5+. Conversions inside existing structures are excluded from housing-unit counts.

- An SB 9 lot split with detached houses → **1-unit** buildings, indistinguishable from any single-family house.
- An SB 9 two-unit project built as two detached houses, or as a townhouse-style pair → **1-unit** (two buildings).
- Only a stacked or shared-system duplex → **2-unit**.
- Detached new-build ADUs also land in 1-unit (S: HyreADU research note).
- So **much SB 9 output is filed in BPS as 1-unit**: inferred from V definitions, not measured.

## Task 4: public permits by lot-split or parcel-map status

- **Statewide:** only the APR flags. Table A ("Residential Lot Split" applications, including 0-unit rows) and Table A2 (units approved under SB 9) carry them, for 2023+ APRs. HCD publishes no separate parcel-map dataset (V).
- **Local examples, identified only, not opened for data:**
  - Encinitas: "SB 9 Project Dashboard", listing SB 9 two-unit, lot-split and combined applications.
  - Costa Mesa GIS: `Parcel_Viewer/Approved_SB9_Subdivisions` MapServer.
  - San Luis Obispo County EnerGov GIS layers: Parcel Maps, Subdivisions, Tract Maps, Residential Construction Permits, plus an "SB-9 Eligible Parcels" layer. This is an eligibility layer, not outcomes.
  - LA City LADBS permit feature service, with a parcel layer.
  - County recorder and Public Works parcel-map and tract-map indexes exist in most counties; not checked.
- None of these were queried. Note that several are 2022+ data for tested places, so reading their contents would break the no-peeking rule unless restricted to pre-2022.

## Read log (rule numbers from docs/middle/MEASUREMENT_CHECK_LOG.md)

| When (UTC) | Item | Rule | Note |
|---|---|---|---|
| 2026-11-08 00:27:51 | docs/middle/MEASUREMENT_CHECK_LOG.md | — | read rules |
| 00:27:56 | data/raw/hcd_apr_a2/tablea2_datadictionary.docx (word/document.xml) | 1 | |
| 00:27:56 | data/raw/hcd_apr_a2/_downloads.json (file metadata) | 1 | It describes `api/table_a2_year_unitcat.json`, which holds **counts by YEAR × UNIT_CAT for all years including 2022+**. I did **not** open that file. |
| 00:28:09 | tablea2.csv header; distinct values of UNIT_CAT, APPROVE_SB35, YEAR, INFILL_UNITS, DR_TYPE, TENURE across all years | 2 | Distinct values only, no counts. Seeing which SB 9 value *combinations* exist reveals only that each combination occurs at least once. |
| 00:28:19 | tablea2.csv: up to 3 example rows each for townhome, duplex, tri/fourplex, lot split/parcel map/subdivision, SFA with permits, conversion; YEAR 2018–2021 only | 3, 5 | About 17 rows printed. Sacramento County (unincorporated, 2021) rows appeared; no Sacramento city rows, nothing from 2024+. The script stopped by reading order, not by any count. |
| 00:28:45 | HCD APR instructions PDF (hcd.ca.gov, Jan-2026 version); hcd.ca.gov APR page | 1 | curl with project user agent |
| 00:29:21 | data.ca.gov package_show for the APR dataset (resource list and modified dates) | 1 | metadata only |
| 00:29:31 | Table A data dictionary DOCX (data.ca.gov) | 1 | |
| 00:29:46–00:30:20 | leginfo: Gov. Code 66499.40, 66499.41, 66411.7, 65852.21; bill status pages for SB 684, SB 1123, SB 9; bill text for SB 684 and SB 1123 | 1 | curl got 403; read via Exa fetch |
| 00:30:30 | census.gov BPS definitions, classification FAQ, C-404 form (search excerpts); HyreADU note (S) | 1 | |
| 00:30:40 | Web search for local SB 9 / parcel-map datasets (Encinitas, Costa Mesa, SLO County, LADBS) | 1 | Only names and layer lists seen. Encinitas page text asks "How many SB 9 projects..." but shows no number. **No counts seen.** |

**Rule breaks:** none. I saw no count, sum, rate or chart of 2022+ California records.

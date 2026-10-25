# Gate 1 Policy and Evidence Map: ADU Reform

Prepared 2026-10-23 for Gate 1 of the [MVP Execution Plan](../MVP_EXECUTION_PLAN.md). All URLs were checked on 2026-10-23 unless a row says otherwise. This is a research map. It does **not** adopt rules or parameters. Section 7 proposes uptake ranges for review at **Gate 3**; nothing here is a calibrated value.

## Status labels

- **Verified:** the team read the primary source, or an official agency data table, on the check date.
- **Source lead:** the claim comes from a secondary source, a code mirror, a search snippet, or a page that refused automated access. It needs primary confirmation before coding.
- **Unknown:** we could not determine it.

Labels apply to the factual claim, not to how we interpret it. Where a figure is our own arithmetic (for example, permits per 1,000 single-family units), the inputs are cited and the calculation is marked *calc*.

## Benchmark reform (from the challenge)

Allow one ADU on parcels with an existing single-family building. Detached and semi-detached ADUs of at least 600 sq ft must be allowed. No additional parking may be required. Outcome: housing units authorized by issued permits over five years, relative to a current-law baseline.

The benchmark does not address owner occupancy, occupant relationship, fees, process, or height. Section 2.3 and Section 3.2 flag where local rules on those points would determine what "allowed" means in practice. Treating them is a **modeling decision for the owner** (see Q-PE-1 in Section 9).

---

## 1. Wisconsin state law, as of October 2026

### 1.1 Finding: no statewide ADU mandate or preemption exists (Verified)

No enacted Wisconsin statute requires municipalities to allow ADUs or limits how they regulate them. All ADU bills in the 2025–26 session failed on 2026-03-23, at the end of session (Senate Joint Resolution 1). We found no ADU bill in the 2023–24 session (source lead; see 1.3).

**Model consequence:** the current-law baseline is the local rules in each jurisdiction. State reform is purely hypothetical. No Wisconsin calibration event exists at the state level.

### 1.2 Bills, 2025–26 session (Verified)

Primary pages read through the Legislature site (docs.legis.wisconsin.gov refused direct connection, so the agent read the live page text through an alternate fetcher):

| Bill | Sponsors (lead) | ADU provisions | Last action | Status |
| --- | --- | --- | --- | --- |
| [2025 AB 449](https://docs.legis.wisconsin.gov/2025/proposals/ab449) / [SB 473](https://docs.legis.wisconsin.gov/2025/proposals/sb473) ([bill text and LRB analysis](https://docs.legis.wisconsin.gov/2025/related/proposals/ab449.pdf)) | Rep. Goeben, Rep. Brooks et al.; Sens. Bradley, Feyen, Roys, Wall, Cabral-Guevara. Bipartisan. | Would create ss. 59.69(16), 60.61(3o), 62.23(7)(j). Counties, towns and cities with zoning must allow **at least one ADU as a permitted use** (no conditional use, variance or special review) on residential or mixed-use parcels with an existing single-family home. Local governments could still: cap size at the floor area of the existing house; cap height at the district maximum; apply existing setbacks and lot coverage; ban short-term rental of new ADUs. **Silent on parking, owner occupancy and fees.** Effective on the first day of the 7th month after publication. [AA1](https://docs.legis.wisconsin.gov/2025/related/amendments/ab449/aa1_ab449.pdf) / [SA1](https://docs.legis.wisconsin.gov/2025/related/amendments/sb473/sa1_sb473.pdf) would require the ADU to be **created by converting an existing structure**, which excludes new construction. | AB 449: introduced 2025-09-25; Assembly committee 2025-10-03 recommended AA1 (8–6) and passage as amended (13–1); placed on the calendar, no floor vote recorded. SB 473: introduced 2025-10-02; Senate committee 2026-02-12 recommended SA1 and passage (5–0). | Failed 2026-03-23 |
| [2025 AB 365](https://docs.legis.wisconsin.gov/2025/proposals/ab365) / [SB 247](https://docs.legis.wisconsin.gov/2025/proposals/sb247) ([text](https://docs.legis.wisconsin.gov/2025/related/proposals/ab365.pdf)) | Rep. Hong et al.; Sen. Roys et al. | One ADU **by right** wherever single-family or multifamily housing is allowed by right. Size cap no lower than 75% of the existing house. No fees beyond standard building-permit fees. No stricter dimensional or design rules than for houses. **No additional parking.** No separate utility connection required. Voids covenants against ADUs and limits HOA restrictions. No owner-occupancy provision. | SB 247 introduced 2025-05-09; AB 365 introduced 2025-07-17. No hearings. | Failed 2026-03-23 |

The 2025 [Subject Index](https://docs.legis.wisconsin.gov/2025/related/subject_index/index) lists only these four ADU bills (Verified).

**Relevance:** AB 449 as introduced is the closest Wisconsin analogue to the benchmark. It is narrower in two ways: it does not address parking, and it lets local governments cap size at the house's floor area, which on very small houses can fall below 600 sq ft. As amended, it was **much** narrower than the benchmark (conversions only). This is the main policy-design lesson for a legislative audience. The bills that advanced in committee did so only after new construction was removed. The benchmark's detached-new-construction right goes beyond anything that has advanced in Wisconsin.

### 1.3 Related enacted law without ADU provisions (Verified unless noted)

| Law | Date | Relevance |
| --- | --- | --- |
| [2023 Wisconsin Act 16](https://docs.legis.wisconsin.gov/2023/related/acts/16) (AB 266), part of the Acts 14–18 housing package ([acts list](https://docs.legis.wisconsin.gov/2023/related/acts)) | Published 2023-06-23 | Creates s. 66.10016: a complete application meeting existing requirements must be approved, with mandamus as the remedy; adds certiorari review. Zoning amendments pass by simple majority. **No ADU text.** It indirectly supports by-right permit certainty where ADUs are already permitted uses. Acts 14, 15, 17 and 18 are WHEDA loan programs. |
| [2025 Wisconsin Act 173](https://docs.legis.wisconsin.gov/2025/related/acts/173) (AB 453) | Enacted 2026-04-02; published 2026-04-03. General effective date **unknown** (the fetch was truncated). | Sets a 90-day rule for granting certain residential rezonings; adds residential-density content to comprehensive plans; TIF changes. No ADU text. |
| [2025 Acts 235](https://docs.legis.wisconsin.gov/2025/related/acts/235), 236, [237](https://docs.legis.wisconsin.gov/2025/related/acts/237), 67, 78 | 2025–26 | Residential TIDs, low-income housing tax credit, WHEDA loans, manufactured housing, workforce housing credit. No ADU text. |
| [Wis. Stat. s. 66.10013](https://docs.legis.wisconsin.gov/statutes/statutes/66/x/10013) (2017 Act 243) | In force | Cities and villages with 10,000 or more residents must post an annual Housing Affordability Analysis by January 31, including approvals and units approved. **No ADU field.** Useful as a statewide source of permit context and approval counts. Whether reports mention ADUs varies (source lead). |
| [Wis. Stat. s. 66.10015](https://docs.legis.wisconsin.gov/statutes/statutes/66/x/10015) | In force | Vesting under existing requirements, substandard lots, no forced lot merger. No ADU language. |
| ss. 62.23, 59.69, 60.61 | In force | Not read in full. The failed bills would have *created* ADU paragraphs, which implies none exist (source lead). |
| 2023–24 session | — | The [2023 Subject Index](https://docs.legis.wisconsin.gov/2023/related/subject_index/index) was only partly checked; no ADU bill was found (source lead). |

---

## 2. Madison: history and what the benchmark would add

Primary sources are adopted ordinance texts, staff memos and action histories from Madison Legistar and its web API (`https://webapi.legistar.com/v1/madison/matters/{id}`). Municode returned HTTP 403, so the codified rendering of the current text comes from a mirror (source lead), while the ordinances that produced it were read directly (Verified).

### 2.1 Ordinance history (Verified unless noted)

| Effective / code date | Legistar file (ordinance) | Change |
| --- | --- | --- |
| 2013 (new zoning code) | File 29995, ORD-13-00098, passed 2013-06-04 (the base code-adoption ordinance number is **unknown**) | ADUs added as a **conditional use**. Staff describe ADUs as allowed "since 2012/2013." Until 2021, every ADU needed conditional use approval. |
| 2017 | — | **No 2017 ADU ordinance.** File 45555 (2017) deals only with accessory buildings. Correct the assumption that ADUs were first allowed in 2017. |
| Passed 2021-12-07; enactment 2021-12-16 | [File 68079](https://madison.legistar.com/LegislationDetail.aspx?ID=5218928&GUID=692C2A7F-1E48-4779-9367-715C9FD31C50), ORD-21-00087 ([substitute text](https://legistar.granicus.com/madison/attachments/9f0d6cb9-2ee7-4986-b4fb-3cd524c4e722.pdf); [ordinance PDF](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/50000/1127114/pdf)) | ADU becomes a **permitted use** in all residential districts, in mixed-use/commercial and downtown districts where single-family homes are allowed, and in Agricultural. Size changes from the lesser of 700 sq ft or 75% of the principal home to **900 sq ft and 2 bedrooms**. Subordination rule removed. **Owner occupancy retained.** Height 25 ft; 3 ft setbacks. |
| 2023-01-25 | File 74703, ORD-23-00013 (TOD overlay) | ADUs allowed with two-family principal buildings in the TOD overlay, owner-occupied. No minimum car parking in the TOD overlay. |
| 2023-03-10 | File 74885, ORD-23-00022 | New definition of "family"; amends 28.151. |
| Adopted 2024-04-16; code date 2024-04-26 | File 81952, ORD-24-00022 ([text](https://webapi.legistar.com/v1/madison/matters/91265/texts/92975); [staff memo](https://legistar.granicus.com/madison/attachments/7a0e7685-0587-4fa0-9578-6601829f35df.pdf); [news](https://www.cityofmadison.com/news/2024-04-17/common-council-votes-to-approve-more-housing-options-for-residents)) | **Owner occupancy removed for all ADUs.** The principal building may have up to 8 units. Repeal date is 2024, not 2023. |
| Adopted 2025-02-25; code date 2025-03-08 | File 86650, ORD-25-00011, "Housing Forward" ([body](https://legistar.granicus.com/madison/attachments/3bd8ec23-5475-486c-a0fa-c052e688c5b8.pdf); [memo](https://legistar.granicus.com/madison/attachments/3263cd96-60e9-41c1-b348-0d4c531bdeec.pdf)) | Internal ADU up to **1,000 sq ft**; detached ADU building footprint up to **1,000 sq ft**; **bedroom cap removed**. Council kept height at **25 ft** after the Plan Commission recommended 30 ft. |
| 2025-09-11 | File 89326, ORD-25-00057 ([memo](https://legistar.granicus.com/madison/attachments/555bb4e5-0713-4ff3-821c-6f3bbd78eefe.pdf)) | Cleanup: "principal dwelling" becomes "principal building." |
| Passed 2025-10-07; code date 2025-10-16 | [File 89918](https://madison.legistar.com/LegislationDetail.aspx?ID=7656026&GUID=F9768184-E06C-4B82-95BE-E43F79D47E7F), ORD-25-00068 ([memo](https://legistar.granicus.com/madison/attachments/a5f8225d-4847-432b-b1d6-de8c0902253a.pdf)) | **One attached ADU, or two detached ADUs in one structure**, not both. A detached ADU no longer counts toward the 1,000 sq ft cap for other accessory buildings; lot coverage still counts it. |
| After 2025-10 | — | An API title search found no further ADU ordinance through October 2026 (Verified as of the API state). |

### 2.2 Current rules, MGO 28.151 and parking

These come from the adopted 2025 texts (Verified). The codified rendering seen at Gate 1 was a third-party mirror (Zoneomics, source lead; no longer cited, owner decision D4).

- **Units:** principal building up to 8 units; one attached ADU, or up to two detached ADUs in one structure.
- **Size and height:** internal ADU up to 1,000 sq ft; detached ADU building footprint up to 1,000 sq ft; height 25 ft; accessory-building setbacks (3 ft).
- **No** owner occupancy, bedroom cap or minimum lot size. The ADU cannot be sold separately.
- **Parking:** ADU car-parking minimum is 0 (source lead: Table 28I-3 via snippet, consistent with File 74703). A single-family principal home still requires 1 space ("location only") outside the TOD overlay and the districts without minimums. Madison did **not** remove parking minimums citywide in 2022 ([Strong Towns, May 2025](https://www.strongtowns.org/journal/2025-5-16-can-loosening-parking-rules-unlock-madisons-missing-middle), source lead).
- **Districts:** ADUs are permitted in residential, downtown DR1/DR2, Agricultural, NMX, TSS and CC-T. They are not listed in LMX, MXC, CC, RMX or THV (source lead: Table 28D-2 via snippet). Planned Development zoning may restrict them.
- City guidance pages ([detached](https://www.cityofmadison.com/development-services-center/1-2-family-residential/new-building-construction/new-detached-accessory), [attached](https://www.cityofmadison.com/development-services-center/1-2-family-residential/additions/attached-accessory-dwelling-unit)) match these rules (Verified). They also mention a Park Impact fee.

### 2.3 What the benchmark would **additionally** allow in Madison

Madison already meets or exceeds the benchmark on almost every parcel with a single-family home: ADUs are by right, at least 600 sq ft is allowed, ADUs need no parking, and there is no owner occupancy. **The change in rights is small and limited to edge cases:**

1. **Single-family parcels in districts where ADUs are not listed:** LMX, MXC, CC, RMX, THV, downtown/urban districts, employment/industrial districts with nonconforming houses, and PD zoning. The benchmark would add a by-right ADU there. Parcel count: **unknown** (needs a join of zoning and land use).
2. **The 600 sq ft floor on constrained lots:** Madison's limits are maximums. On small lots, lot coverage, 3 ft setbacks or other accessory buildings may leave less than a 600 sq ft footprint. A two-story detached ADU within 25 ft might still fit. Effect: **unknown** (parcel geometry test).
3. **Parking for the principal home after a garage conversion:** the ADU itself needs no parking. If a semi-detached ADU or conversion removes the house's only required space, it is **unknown** whether the benchmark's "no additional parking" protects it.
4. **Not new:** owner occupancy, bedroom limits, process. Madison is more permissive than the benchmark in some respects (two units in a detached ADU building; ADUs with principal buildings of 2–8 units). The model must not *reduce* rights by applying the benchmark as a ceiling.

**Model consequence:** for Madison, the benchmark's additional legal opportunity is close to zero on most single-family parcels. The pilot should show this explicitly. Madison's observed permits belong almost entirely in the **baseline**, not in the reform effect.

### 2.4 Observed ADU permits in Madison (Verified)

The City's [Fall 2025 Housing Forward page](https://www.cityofmadison.com/mayor/priorities/housing-forward/fall-2025-housing-forward-proposals) (re-checked directly 2026-10-23) gives Building Inspection Division ADU permit counts:

| 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 (Jan–Aug) | Total |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 5 | 2 | 2 | 1 | 1 | 2 | 0 | 2 | 6 | 11 | 10 | 6 | 49 |

- **Other sources:** older staff memos, "fewer than 25 approved since 2013, about half built" ([2021 memo](https://legistar.granicus.com/madison/attachments/1159934d-b95f-434f-8352-bb587328505e.pdf)) and "about 32 built or under construction since 2012" (2024), measure different stages but are broadly consistent (Verified).
- **Unreconciled:** a Cap Times count and an ADU-vendor claim that about half of all permits came in the 12 months after April 2024 do not match the City table (source leads). Prefer the City table, pending record-level permit data.
- **Rate (calc):** ACS 2024 1-year estimates 54,615 one-unit detached homes in Madison (B25024_002, via the [Census Reporter API](https://api.censusreporter.org/1.0/data/show/latest?table_ids=B25024&geo_ids=16000US5548000)). That gives about **0.02–0.04 permits per 1,000 single-family homes per year** under conditional use (2013–2021). It rose to **about 0.11 (2022), 0.20 (2023) and 0.18 (2024)** after by-right status (Dec 2021) and the removal of owner occupancy (Apr 2024). This is descriptive. The rise also coincides with rising rents, the City's Housing Forward promotion and interest-rate changes.
- **Reconciliation pending (conductor, 2026-10-23):** a keyword search of the City's record-level Construction Summary report ([DATA_INVENTORY.md](DATA_INVENTORY.md)) also totals about 49 but over 2014–2025 and with different years (e.g., 2023: 7 vs 11; 2025 full year: 13), plus 16 permits in 2026 through Oct 23 (about 0.35 per 1,000 annualized, above the proposed central 0.3). The table above and the keyword counts measure different windows and possibly different stages; Gate 2 reconciles them record by record before any rate is adopted.
- This is the only Wisconsin before/after series we found. Madison is the state's strongest housing market, so the series was first proposed as a **ceiling check**; the owner later set it as the statewide **floor** for the reform case (AQ-024), on the reasoning that statewide reform builds a specialized ADU industry that a single city does not.

---

## 3. New Berlin: current rules compared with the benchmark

### 3.1 Code citation and version

- **Version:** Chapter 275 Zoning of the [New Berlin Municipal Code](https://library.municode.com/wi/new_berlin/codes/municipal_code?nodeId=PTIIGELE_CH275ZO_ARTVIIIGEDERE). Adopted 2013-06-17 (Ord. 2489). Municode returned 403. Captures show "Supplement 3, Update 1, codified through Ordinance No. 2717 enacted January 27, 2026." The online-update date differs between captures (2026-04-08 vs 2026-09-21) and is **unknown**. *Version date for model coding: through Ord. 2717 (2026-01-27), source lead.*
- **Code text:** first read from a Zoneomics mirror (source lead). Re-read on Municode in a browser on 2026-10-25 and unchanged, so the coded rules are now verified (`wi_adu_rules.csv`); Zoneomics is no longer cited because its terms of use do not allow our reuse (owner decision D4). The key prohibition is also confirmed by City PDFs (Verified, below).

| Provision | Rule | Status |
| --- | --- | --- |
| §275-42 C(3) "Family dwelling unit" (in-law suite) | Allowed only in **agricultural and single-family residential districts**. Must be **attached** and architecturally integrated; "Detached accessory dwelling units are prohibited." Approved by an administrative zoning permit (§275-24), not conditional use. **Owner** must live on the property. Occupants must be **related** (deed restriction recorded). **At most 2 occupants.** **At most 50% of the principal unit's living area.** No front entrance. At least one interior connection. | Source lead (mirror) |
| §275-42 B(1)(a)[2][b][iii] | "Accessory dwelling units (ADU's) / Living quarters are not permitted within accessory buildings" in single- and two-family districts. | Source lead (mirror); confirmed by City PDFs |
| Table 275-42-1 | Combined accessory-building footprint: 840 sq ft on lots under 2 acres, rising with lot size. One story, 18 ft (waiver to 21 ft). | Verified ([Accessory Buildings guidance](https://www.newberlinwi.gov/DocumentCenter/View/18250/Accessory-Buildings), PDF 2025-04-04) |
| Table 275-57-1 | Single- and two-family homes: 2 spaces per dwelling unit, with at least 400 sq ft in an attached garage. Whether a family dwelling unit counts as a dwelling unit for parking: **unknown**. | Source lead |
| City guidance | [Sheds guidance](https://www.newberlinwi.gov/DocumentCenter/View/502/Sheds) (DID=502 redirect, PDF 2025-04-04) repeats the ADU / living-quarters prohibition in accessory buildings. | Verified |
| [2025 Housing Affordability Report](https://www.newberlinwi.gov/DocumentCenter/View/25878) (PDF dated 2026-01-29) | **No** mention of ADUs, accessory, in-law or family dwelling units (text search). Notes a coming update to the Comprehensive Plan housing chapter. | Verified |
| 2025–26 amendments | No ADU amendment or Plan Commission ADU item found. | Unknown (none found) |

### 3.2 What the benchmark would newly allow in New Berlin

1. **Detached ADUs:** currently prohibited outright. This is the main change in rights. The benchmark would also need to override the 840 sq ft combined accessory footprint cap, which on lots under 2 acres blocks a 600 sq ft ADU wherever a detached accessory building of more than 240 sq ft already exists. The one-story/18 ft limit is compatible with a 600 sq ft one-story ADU.
2. **Semi-detached ADUs** (breezeway or garage connection without an interior connection): currently not allowed.
3. **The 600 sq ft floor:** the 50%-of-living-area cap holds attached units below 600 sq ft for any house under 1,200 sq ft. The share of affected houses is **unknown**; it needs assessor living-area data.
4. **Single-family parcels outside agricultural/single-family districts** (Rd-1, Rm-1, business, office, institutional, PUD; nonconforming homes): no ADU right today.
5. **Parking:** if ADUs trigger 2 additional spaces or a garage requirement, the benchmark removes that requirement. Current treatment is **unknown**.
6. **Owner occupancy, related occupants, 2-person cap:** the benchmark is silent. Whether the reform removes these limits is a modeling decision (Q-PE-1). They are very likely the biggest *practical* barriers. Related-occupant and deed-restriction rules keep units out of the rental market and so suppress uptake regardless of form.
7. **Process:** already administrative. No change.

**Model consequence:** New Berlin is a clean case of *substantial* added opportunity: from no detached right to a detached right on essentially all single-family parcels. The existing attached family-unit right means the baseline is not zero ADU rights. Attached family units may already appear in permit data under other descriptions ("in-law," "addition"), as AQ-014 warns.

---

## 4. Statewide distribution of local ADU rules

### 4.1 What exists

No complete, verified classification of Wisconsin municipalities' ADU rules was found.

| Source | Coverage | Usefulness | Status |
| --- | --- | --- | --- |
| [National Zoning Atlas, Wisconsin](https://www.zoningatlas.org/wisconsin) | Target is all **1,922** jurisdictions (counties, cities, villages, towns). ADU categories: Allowed / Allowed with occupancy restrictions / Public hearing / Public hearing with occupancy restrictions / Prohibited ([methods](https://www.zoningatlas.org/snapshots-methods)). | **Best candidate coding scheme and possible future data.** Completion state unknown (counters did not render). | Source lead |
| [Wisconsin Policy Forum, "Building Blocks"](https://wispolicyforum.org/wp-content/uploads/2023/07/BuildingBlocks_FullReport.pdf) (Jul 2023) | 4 Waukesha County municipalities. None permitted ADUs. | Spot check of suburban restrictiveness | Source lead |
| [Dane County ADU fact sheet](https://rhs.danecounty.gov/documents/pdf/FactSheets/ADU-Fact-Sheet-v3-FINAL.pdf) (undated) | Lists by-right municipalities: Fitchburg, Madison, Middleton, Verona, Waunakee | Regional lead | Source lead |
| ["Enabling Better Places" WI guide](https://lwm-info.org/DocumentCenter/View/5566/WI-Zoning-Guide-Final-2-2022?bidId=) (CNU / League of WI Municipalities et al., Feb 2022) | Model ADU ordinance; 5 case studies | Not a classification | Source lead |
| [DOA comprehensive-plan and land-regulation library](https://doa.wi.gov/Pages/LocalGovtsGrants/Comprehensive-Planning-Library-of-Plans.aspx) | All jurisdictions, with zoning/subdivision flags and ordinance links | **Sampling frame** for coding | Source lead |
| Commercial compilations (e.g., cityrulelookup.com, badgerhomeowner.com) | about 35 jurisdictions; about 10 Dane-area jurisdictions | Discovery only; do not code from these | Source lead (low reliability) |

### 4.2 Recently liberalized municipalities (discovery list)

These show that the statewide baseline is **changing quickly**. Baseline-period rules and current rules will differ for many places.

| Municipality | Action | Status |
| --- | --- | --- |
| Milwaukee | [File 240999](https://milwaukee.legistar.com/LegislationDetail.aspx?FullText=1&GUID=EC37A5E2-E09E-4F45-8CE2-F4EB15571F88&ID=6899532), effective 2025-08-02. One ADU per lot; owner occupancy at time of permit ([city page](https://city.milwaukee.gov/DCD/Planning/PlanningAdministration/ZoningResources/Accessory-Dwelling-Units)). Which substitute passed (4 vs 6) is unresolved. | Verified (Legistar); substitute detail open |
| La Crosse | [File 23-1243](https://cityoflacrosse.legistar.com/LegislationDetail.aspx?GUID=3605DA25-4406-4260-BADB-E936F0E64E7E&ID=6389312&Options=&Search=), adopted 2024-02-08 | Verified |
| Appleton | [ADU and junior-ADU rules](https://cityofappleton.legistar.com/LegislationDetail.aspx?GUID=96A34E37-FF1B-4AE2-B7A9-1E1BF0F8367E&ID=4970068), approved 2021-07-07 | Verified |
| Wauwatosa | [O-19-11](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true), 2019-06-18: 49% of house or 650 sq ft; no parking. Replaced by O-25-25 (2025-11-18, source lead). | Verified / source lead |
| Sturgeon Bay | [Ord. 1458-0225](https://cms9files.revize.com/sturgeonbaywi/Ordinance%202023/2025/1458-0225.pdf), effective 2025-02-22: 800 sq ft; owner occupancy; 1–2 parking spaces | Verified |
| Eau Claire (eff. 2025-10-01), Green Bay (conditional use, Dec 2025), Sheboygan (Dec 2025; owner occupancy; 40% cap), South Milwaukee, Sun Prairie (2026), Dunn County (2024), Town of Dane (2026) | See agent notes; secondary or news sources | Source leads |

### 4.3 Proposed coding scheme for unknown and verified local status (proposal)

> **Conductor note (2026-10-23):** superseded in part by [SCOPE_AND_MODEL.md](SCOPE_AND_MODEL.md) rev 2, which governs class names (prohibited / restricted / compliant / forms_with_occupancy_limits / no_zoning / unknown), status labels (verified / source_lead / unknown), and the unknown-rules treatment (sample mix with all-compliant and all-prohibited bounds).

Each jurisdiction-period record has two parts: a **rights class** and an **evidence status**. Each is coded separately for the benchmark components.

**Rights components** (per jurisdiction, per effective-dated period):

| Field | Values |
| --- | --- |
| `detached_right` | `by_right` / `discretionary` (CUP / public hearing) / `prohibited` / `no_zoning` / `unknown` |
| `attached_right` | same values |
| `owner_occupancy` | `none` / `at_permit` / `ongoing` / `unknown` |
| `occupant_restriction` | `none` / `related_only` / `unknown` |
| `size_allows_600_detached` | `yes` / `conditional_on_house_size` / `no` / `unknown` |
| `adu_parking_min` | integer / `unknown` |
| `districts_covered` | `all_sf` / `some_sf` / `unknown` |

`no_zoning` matters because many towns lack zoning, or are under county zoning. A state mandate applying through ss. 59.69/60.61/62.23 would reach them differently.

**Evidence status:**

| Status | Definition |
| --- | --- |
| `verified_primary` | Codified text or adopted ordinance read, with version date |
| `verified_secondary` | Official city guidance or a reputable tracker such as the National Zoning Atlas, with a date |
| `lead` | News, vendor or commercial compilation |
| `unknown` | Not researched |

**Treatment of unknowns in statewide runs:** do not impute "prohibited." Run the change in rights under three explicit priors and report the spread as an uncertainty driver:

- `unknown → like verified peers in the same population/county stratum` (central)
- `unknown → permissive` (smallest added opportunity)
- `unknown → prohibited` (largest added opportunity)

Show the share of single-family parcels whose status is `unknown`, weighted by parcel count, on the coverage screen. Prioritize verification by single-family parcel count. The roughly 30–60 largest cities and villages, plus counties administering town zoning, likely cover most single-family inventory (to be confirmed with Gate 2 parcel data).

---

## 5. Empirical ADU permit response after legalization or liberalization

**Overall finding:** we found **no peer-reviewed study that causally estimates the effect of ADU legalization on ADU permits** (searched 2026-10-23). The permit evidence is descriptive before/after data. Causal papers address broad upzoning (Auckland) or prices. Every rate below is **descriptive** unless labeled otherwise.

**Denominator (calc):** unless noted, "SF" means one-unit detached housing units from ACS 2024 1-year estimates, table B25024_002, via the [Census Reporter API](https://api.censusreporter.org/1.0/data/show/latest?table_ids=B25024&geo_ids=04000US06) (Verified). This is a proxy for eligible single-family lots. It overstates eligible lots where condos, HOAs or small lots apply, and differs from parcel counts. Values: California 8,444,064; Los Angeles 565,981; Seattle 143,530; Portland 161,773; Minneapolis 85,943; Austin 212,673; Madison 54,615; Wisconsin 1,855,771.

| Place / reform | Annual ADU permits (period) | Per 1,000 SF per year (calc) | Ramp | 5-year cumulative share of lots | Source; status | Key caveats |
| --- | --- | --- | --- | --- | --- | --- |
| **Seattle**: Ord. 125854, effective Aug 2019 (attached plus detached ADU per lot; no owner occupancy or parking; two detached ADUs only from 2025-06-30). *Corrected 2026-10-24: earlier text cited 125984, a parks fee schedule.* | 2016–19: 245–283; 2020: 476; 2021: 762; 2022: 924; 2023: 905; 2024: 913 (detached 2024: 465) | Before: 1.7–2.0. 2020: 3.3. 2021: 5.3. 2022–24: about 6.3. Detached only 2024: 3.2. | Year 1 ×1.7; plateau by year 3 | 3,980 ADUs 2020–24, or 27.7 per 1,000 SF. About 2.1% of lots (0.77 lots per ADU, from the attached+detached pairs share) | [OPCD ADU Annual Report 2024](https://seattle.gov/documents/Departments/OPCD/OngoingInitiatives/EncouragingBackyardCottages/OPCD-ADUAnnualReport2024.pdf); Verified; descriptive | About 57% of 2022–23 ADUs were on condo parcels (redevelopment). Revisions between report vintages. Very strong market. Applications fell 32% in 2025. |
| **Portland OR**: SDC waiver 2010, plus code changes | 2000–09: about 27 per year; 2016–18: about 621 per year; 2019–20: about 250–300 | Before: 0.17; peak: 3.8–4.1; after: 1.5–1.9 | About 6 years to peak, then decline | About 2.1% of SF by 2021 (cumulative over about a decade) | [accessorydwellings.org 2019](https://accessorydwellings.org/2019/01/14/adu-permit-trends-in-portland-in-2017-and-2018/), [2021](https://accessorydwellings.org/2021/07/22/portland-oregons-adu-permit-data-for-2020/); Verified (secondary analysis of city data); descriptive | Fee-driven, not a change in rights. Short-term-rental demand. Peak tied to the waiver's expiry deadline. 39% built with new houses. |
| **Los Angeles city**: state law effective 2017-01-01 | 2018: 4,079; 2019: 6,747; 2020: 6,012; 2021: 7,589; 2022: 10,304; 2023: 10,426; 2024: 11,406; 2025: 12,333 | Before: about 0.34. 2018: 7.2. 2022–25: 18–22. | Applications ×15 in year 1 | 2018–22: about 61 per 1,000 SF (upper bound) | [HCD APR Table A2](https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year), team aggregation; Verified; descriptive. Applications: [LA Planning 2018](https://shou.senate.ca.gov/sites/shou.senate.ca.gov/files/LA%20Dept.%20of%20City%20Planning%20Housing%20Progress%20Report.pdf) | Outlier. Includes JADUs, conversions (about 80% of early applications were conversions or additions), multifamily ADUs and legalizations. **Not transferable** as a rate. |
| **California statewide**: 2017 and 2020 packages, plus later laws | 2018: 9,006; 2019: 15,086; 2020: 16,041; 2021: 24,640; 2022: 31,806; 2023: 35,720; 2024: 39,073; 2025: 41,853 | 1.1 → 1.9 (2020) → 2.9 → 3.8 → 4.2 → 4.6 → 5.0 | Still rising after 8 years (successive reforms) | 2018–22: 11.4 per 1,000 SF (upper bound) | HCD APR Table A2; Verified; descriptive. Reconcile with AQ-017 historical series (2018: 8,900; 2019: 14,702) | 2018 is the first APR year (undercount). Mixed ADU types. Successive reforms prevent isolating the **2020 package**. |
| **California parcel level**: Bay Area + 5 SoCal counties | 7,500–10,654 parcels per year with at least one ADU permit (2018–21) | **2.1–3.0 parcels per 1,000 SF-zoned parcels per year** | — | **0.97% of 3.57M SF parcels over 4 years** | [Marantz, Elmendorf & Kim 2023, Furman Center / Cityscape](https://www.furmancenter.org/files/Evaluating_California%E2%80%99s_Accessory_Dwelling_Unit_Reforms_508.pdf); Verified; descriptive with associational regressions | The cleanest per-parcel denominator. Uptake rises with lot size (+16% odds per SD) and existing structures; falls with HOA intensity (−29%) and in very-low-rent areas. |
| **Austin**: 2015 amendments (lot minimum is "a standard lot", 5,750 sq ft, not a number in the ordinance; see [OTHER_CITIES.md](../gate3/OTHER_CITIES.md) for permit series rebuilt from city data) | About 260 per year 2015–24 vs 37 per year before | Before: about 0.17; after: about 1.2 | — | About 1.3% over 10 years (calc) | [Bloomberg Philanthropies brief, Oct 2026](https://assets.bbhub.io/dotorg/sites/83/2026/10/Unlocking-Housing-Supply-in-the-US-by-Expanding-Accessory-Dwelling-Units.pdf); Verified; descriptive | Austin already allowed ADUs; the reform eased lot size and parking. |
| **Minneapolis**: 2014 ordinance | 92 in first 3 years; peak 38 (2017); about 13–15 per year (2020–22) | About 0.36 → below 0.2 | Peak year 3, then decline | About 0.2–0.3% over 5 years (calc) | [MinnPost 2019](https://www.minnpost.com/metro/2019/05/accessory-dwelling-units-were-supposed-to-help-ease-the-twin-cities-housing-crunch-hows-that-working-out/), [TCB](https://tcbmag.com/what-happened-to-the-push-for-accessory-dwelling-units/); source lead; descriptive | **Closest Midwest climate and market analogue.** Owner occupancy applied in the early years. |
| **New Hampshire**: SB 146, effective June 2017 (attached ADUs by right statewide) | 8 of 29 larger towns reporting | 2017–21: about 0.1 (Claremont) to about 1.5 (Merrimack) | — | About 0.05–0.7% (calc) | [Mercatus 2023 brief](https://www.mercatus.org/research/policy-briefs/new-hampshire-adu); Verified; descriptive | Self-reported, partial data. About 10% legalizations. State-mandate analogue in a cold climate. |
| **Massachusetts**: Affordable Homes Act, by-right ADUs from Feb 2025 | 2025: 1,224 permits (about half detached) | About 0.72 per 1,000 SF homes (undercounted); detached only about 0.36 | Year 1 | State projection 8–10k over 5 years, or about 5–6 per 1,000 SF | [Boston Indicators, "ADUs Turn One" (2026)](https://www.bostonindicators.org/-/media/indicators/boston-indicators-reports/report-files/2026/adus-turn-one.pdf); Verified; descriptive | **Best recent statewide-mandate analogue.** 58 towns did not report; 65 reported only half the year. |
| **Madison WI**: by right Dec 2021; owner occupancy removed Apr 2024; 1,000 sq ft in 2025 | See Section 2.4 | 0.02–0.04 → about 0.2 | Response within 1–2 years of by-right status | 2022–Aug 2025: 33 permits, or 0.6 per 1,000 SF over about 3.7 years (calc) | City of Madison; **Verified**; descriptive | **In-state anchor.** The strongest Wisconsin market still shows rates an order of magnitude below the West Coast. |
| **Pew (346 cities, 2025)** | Permissive-ordinance cities: 81 ADU permits per 100k residents | About 2–3 per 1,000 SF (rough calc) | — | — | [Pew, Oct 2026](https://www.pew.org/en/research-and-analysis/reports/2026/10/accessory-dwelling-units-can-meaningfully-boost-housing-supply); source lead (403); cross-sectional | Selection: permissive cities are often high-demand cities. |
| **Montana SB 528** (eff. 2024-01-01), **Washington HB 1337** (compliance 2025), **Vermont** (2020 and 2023 HOME Act), **Oregon** SB 1051 (2017) / HB 2001 (2019) | No statewide ADU permit series found | — | — | — | Law texts, e.g. [MT SB 528](https://archive.legmt.gov/bills/2023/billhtml/SB0528.htm); source lead | **Data gap.** Recheck as state reporting matures. |

### 5.1 Causal and identification evidence

| Study | Design | Finding | Use for this model |
| --- | --- | --- | --- |
| [Greenaway-McGrevy, Auckland, EPC WP017 (2025)](https://www.auckland.ac.nz/assets/business/our-research/docs/economic-policy-centre/EPC-WP017.pdf) | **Causal** (synthetic control) | Upzoning about ¾ of residential land roughly doubled permits per capita within 5 years | Shows that rights changes can produce permit changes within 5 years. Broad upzoning, not ADUs; low transferability. Verified. |
| [Bhatt, Harvard M-RCBG AWP 203](https://www.hks.harvard.edu/centers/mrcbg/publications/awp/awp203) | Difference-in-differences style (SF vs 2–3-family zones, California) | Small increase in ADUs in SF zones; unit unclear | Not usable as a coefficient. Verified (abstract only). |
| Gold & Tarascina, SSRN 7089658 (Seattle) | **Causal** for property values | Eligible lots +4% in value | Not a permit coefficient. Verified (abstract). |
| [Jo et al., JAPA (San José)](https://www.housingsolutionslab.org/housing-solutions-lab/our-research-and-partnerships/lab-grant-awardees/california-legalized-adus-but-unpermitted-ones-are-still-far-more-common-new-research-finds/) | Measurement | About 3.6 informal detached ADUs per permitted one (2016–20) | Permits ≠ all ADU supply. Some post-reform "new" permits are legalizations. Verified (summary). |
| Freemark (2020, Chicago) | Causal (upzoning) | No short-run construction effect | Shows that rights alone may not move permits. Source lead (not fetched). |

---

> **Correction (2026-10-24):** Denver's 2023 amendment changed design standards only; ADUs became allowed citywide on 2024-12-16. Rebuilt permit series for Seattle, Portland, Austin, Denver, and Minneapolis are in [OTHER_CITIES.md](../gate3/OTHER_CITIES.md).

## 6. Mapping to model mechanisms

Mechanisms: (a) eligible inventory, (b) current local rights, (c) change in rights under reform, (d) uptake rate and ramp, (e) timing, (f) uncertainty drivers.

| Item | (a) Inventory | (b) Current rights | (c) Change in rights | (d) Uptake / ramp | (e) Timing | (f) Uncertainty drivers |
| --- | --- | --- | --- | --- | --- | --- |
| WI state law (no mandate) | — | Baseline = local rules only | Reform is entirely hypothetical | No in-state calibration event | Reform start date is a scenario parameter. If enacted, AB 449-style delayed effect (first day of 7th month after publication). Model a 6–12-month implementation lag before year 1. | Whether a real bill would match the benchmark (AB 449 as amended = conversions only) |
| AB 449 / AB 365 texts | Defines eligible parcels: existing SF home on residential/mixed-use parcel (AB 449); anywhere SF or MF housing is allowed by right (AB 365) | — | Template for what a Wisconsin reform would override (CUP, size, parking, fees) | — | Effective-date convention | Size cap at house floor area could fall below 600 sq ft |
| Act 16 / s. 66.10016 | — | By-right applications must be granted | Strengthens a by-right reform's certainty | Possibly faster approvals | — | Small |
| s. 66.10013 reports | Approval counts for cities/villages ≥10k | Some reports describe rules | — | Statewide baseline permit context | Annual by Jan 31 | Coverage only ≥10k; no ADU field |
| Madison rules | SF parcels; districts where ADUs are not listed; PD | By right, 1,000 sq ft, 0 ADU parking, no owner occupancy | **About zero for most parcels.** Edge cases: non-listed districts, constrained small lots, principal-home parking. | Observed 0.2 per 1,000 SF per year after liberalization = **in-state descriptive anchor** | Response visible 1–2 years after Dec 2021 and Apr 2024 | Unreconciled counts; permit vs completion stage; Housing Forward promotion |
| New Berlin rules | SF parcels in ag/SF districts and elsewhere; houses under 1,200 sq ft | Attached only; owner-occupied; related occupants; 50% cap; detached prohibited; 840 sq ft accessory cap | **Large:** detached + semi-detached newly allowed; 600 sq ft floor; parking; possibly occupancy (Q-PE-1) | Apply transferred rates, scaled for market (Section 7) | — | Code version (municode blocked); parking treatment; whether occupancy rules survive |
| Statewide local rules | Parcel inventory statewide (Gate 2) | Mostly **unknown**; National Zoning Atlas is a candidate | Depends on rights class; unknowns under 3 priors | Rate by rights-change class | Many cities changed rules in 2024–26, so the baseline must be dated | Share of SF parcels with unknown status (likely the largest driver at Gate 5) |
| Seattle, Portland, LA, California | Lot-size, HOA and existing-structure effects (Furman) | — | Seattle and LA = removal of binding constraints; Portland = fee change | Upper-bound comparators only; detached-only rates are lower | Seattle plateau by year 3; Portland 6 years to peak; California still rising | Market strength; mixed ADU types; condos and redevelopment; legalizations |
| Minneapolis, NH, MA, Austin | — | — | MA and NH = state mandates | **Primary transfer comparators** for Wisconsin (climate, market) | MA year 1 ≈ 0.7 (all types) | Weak reporting (NH, MA); owner occupancy in Minneapolis |
| California 2020 package (AQ-013) | Includes conversions, JADUs, multifamily | Varies by jurisdiction | Package, not benchmark-equivalent | 2020 step 15.1k → 16.0k → 24.6k in 2021 | **One-year lag to visible response** (2021), confounded by COVID | Cannot isolate the 66323 exemption pathway without pathway fields |
| Causal literature | — | — | — | No ADU-permit causal coefficient exists. **Use ranges, not a point coefficient.** | Auckland: effects within 5 years | Transfer validity |

---

## 7. Gate 3 proposal: candidate uptake ranges (not adopted)

> **Conductor note (2026-10-23):** SCOPE_AND_MODEL rev 2 uses rates as *levels* per 1,000 one-unit detached homes by rights class, with the reform effect = (reform-class level − current-class level). Read the values below as candidate levels for the `compliant` class. On that basis Madison's recent annual rates (about 0.1–0.35, with 2026 near 0.35) bracket a central 0.3 rather than sit below it, so reasoning points 1–2 will be rewritten at Gate 3. Gate 3 must also decide whether comparator rates that include conversions and legalizations can calibrate new-construction categories.

> **Status:** proposal for Gate 3 review. Not a calibrated parameter. Every input is descriptive. The ranges are a transparent judgment, not an estimate.

**Quantity:** annual **incremental** permitted ADU units per 1,000 single-family parcels that **gain** a detached/semi-detached ADU right under the reform (mechanism c), once the response has ramped up. It applies only to newly enabled parcels. Parcels that are already permissive (most of Madison) continue at their **baseline** observed rate. They receive no reform increment, apart from edge cases such as non-listed districts.

| Path | Plateau rate (per 1,000 newly enabled SF parcels per year) | Ramp (share of plateau in years 1–5) | 5-year cumulative (per 1,000) | Share of eligible parcels in 5 years |
| --- | ---: | --- | ---: | ---: |
| Lower | 0.1 | 0.25, 0.5, 0.75, 1, 1 | 0.35 | 0.035% |
| **Central** | **0.3** | 0.4, 0.7, 1, 1, 1 | **1.23** | **0.12%** |
| Upper | 1.0 | 0.6, 0.9, 1, 1, 1 | 4.5 | 0.45% |

**Reasoning:**

1. **In-state ceiling check.** Madison, Wisconsin's strongest ADU market with rules as permissive as or more permissive than the benchmark, has run about 0.2 per 1,000 SF homes per year since by-right status. A statewide central above Madison's observed rate would need an explicit justification. A rate close to Madison's is generous for weaker markets but reasonable for the urban parcels that dominate inventory. Hence a central of 0.3, slightly above Madison. Reasons:
   - The benchmark guarantees 600 sq ft detached units in places where *no* ADU was previously possible, so there may be some pent-up demand.
   - Madison counts are permits for all ADU types.
2. **Midwest and cold-climate comparators.** Minneapolis (about 0.2–0.4), New Hampshire (0.1–1.5), Massachusetts year 1 (about 0.7 all types; about 0.36 detached) and Austin (about 1.2) bracket the range from 0.1 to 1.0.
3. **West Coast rates excluded from the range.** Seattle at about 6, California at 2–5, and LA at 18–22 reflect much higher rents, longer reform histories, conversions, JADUs and legalizations. They are kept only as stress tests ("what if Wisconsin behaved like Seattle detached-only, 3.2"), not as the upper path.
4. **Ramp.** When a reform removes a binding prohibition, the response appears in year 1 and plateaus by about year 3 (Seattle, LA, MA). Slower, Portland-style ramps apply where barriers are cost or information. The lower path uses a slower ramp because Wisconsin has no fee or financing component in the benchmark.
5. **Owner/occupancy interaction.** If the owner decides (Q-PE-1) that the benchmark does **not** override owner-occupancy or related-occupant rules (as in New Berlin), parcels under those rules should use the lower path or a discount. Those rules keep units out of the rental market.
6. **Illustrative scale only (calc, not a forecast):** if X% of Wisconsin's about 1.86M one-unit detached homes gained a detached right, the central path gives about 1.23 × 1,856 × X% units over 5 years. For example, about 1,140 units at X = 50%. X is **unknown** until the Section 4.3 coding exists. This arithmetic is not a result.

**Back-tests to run at Gate 3:**

- Apply the central path to Madison's 2021 change, using Madison's own pre-2021 baseline, and compare with 2022–2025 permits.
- Apply the central path to Milwaukee after Aug 2025, if Milwaukee permit records (2016+ in LMS) allow.
- Compare against Massachusetts years 1–2 once 2026 data appear.

---

## 8. Uncertainty drivers, ranked by expected influence on statewide totals

1. **Local-rights coverage.** Unknown baseline status for most of the roughly 1,900 jurisdictions changes the size of the added opportunity by more than any uptake assumption.
2. **Uptake rate transfer.** No causal coefficient exists. Comparators span two orders of magnitude (0.1 to 20). Market strength (rents relative to construction cost) is the main moderator.
3. **Benchmark interpretation.** Whether owner-occupancy and occupant restrictions survive; whether accessory-footprint caps and principal-home parking are overridden.
4. **Permit definitions.** Different ADU types are counted together (conversions, JADUs, legalizations). The benchmark concerns detached and semi-detached units, so detached-only comparator rates are about half of all-type rates.
5. **Timing.** Implementation lag after enactment, and a rapidly changing local baseline (many 2024–26 local reforms).
6. **Interest rates and construction cost.** Seattle applications fell 32% in 2025. A 600 sq ft new detached unit is costly relative to Wisconsin rents.

---

## 9. Open questions for the owner and next verification steps

- **Q-PE-1 (owner decision):** does the benchmark "allow" override owner-occupancy, related-occupant, occupant-count and accessory-footprint rules? Recommended default for proposal: model two variants. *Form-only* overrides form, size and parking only. *Full* also removes occupancy restrictions.
- **Q-PE-2:** does "no additional parking" protect the principal home's existing required space when an ADU replaces a garage?
- **Q-PE-3:** should the statewide prior for unknown local status be stratified by population or county (Section 4.3)?
- **Verification to do:**
  - Codified text of MGO 28.151 and Table 28I-3/28D-2, and New Berlin §275-42 and Table 275-57-1, from official municode once access works, or from certified copies.
  - Madison record-level ADU permits, to reconcile with the City table.
  - New Berlin minimum house sizes (Table 275-33-3) and assessor living-area distribution.
  - National Zoning Atlas Wisconsin completion status and data access.
  - Milwaukee File 240999 final substitute.
  - Effective date of 2025 Act 173.
  - The 2023–24 Subject Index, in full.
  - Pew 2026 report text (403).

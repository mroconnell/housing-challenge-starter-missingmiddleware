# Wisconsin ADU Rules: Largest Jurisdictions (current law frozen 2026-10-31)

Prepared 2026-10-23/24 for Gate 2. Tables: [`reference/wi_adu_rules.csv`](../../reference/wi_adu_rules.csv) (`policy_rules`, 247 rows: 210 provision rows plus 37 first-pass `mentions_adu` rows) and [`reference/wi_rights_exposure.csv`](../../reference/wi_rights_exposure.csv) (`rights_exposure`, 86 rows = 43 county-subdivision pieces × 2 scenarios). Validator: `uv run python scripts/check_reference_rules.py` (prints `OK`); first-pass scanner: `uv run python scripts/scan_adu_mentions.py` (writes `data/processed/adu_mention_scan/scan.csv`, git-ignored); tests: `tests/test_reference_rules.py`.

## Headline

- **37 municipalities coded**: the 32 named in the work package plus Mequon, De Pere, Pleasant Prairie, Menomonee Falls and Howard. They hold **572,136 of Wisconsin's 1,839,569 one-unit detached homes (31.1%)** (ACS 2020–2024 5-year B25024_002, county-subdivision rows, from the foundation agent's raw download `data/raw/census_acs5_2024_tbsf/`).
- **Current class (2026-10-31):** 4 compliant (Madison, Appleton, Wauwatosa, Fitchburg), 20 restricted, 13 prohibited. **No coded place came back `unknown` / `not_found`**; every rule has a dated source.
- **Basis:** 32 `coded_verified`, 5 `coded_source_lead` (New Berlin, Beloit, West Bend, Neenah, Howard).
- **AQ-023 bias:** the "uncoded = prohibited" default would have been **wrong for 24 of 37 places (65%) and for 75% of their one-unit detached homes** (430,461 of 572,136). See [Bias findings](#bias-findings-for-the-aq-023-default).

## First pass: does the code mention ADUs? (owner direction, 2026-10-24)

Per the owner's direction, every municipality first gets a yes/no check for ADU terms in its current code: "accessory dwelling", "ADU", in-law unit/suite, mother-in-law, granny flat, coach house, carriage house, secondary dwelling unit/suite, accessory living quarters, backyard cottage, and the defined term "Family dwelling unit" (matched case-sensitively at the start of a heading or sentence so "single-family dwelling unit" does not count). **A mention is not an allowance**: New Berlin mentions ADUs to prohibit detached ones. Results are stored as `provision = other`, `value = mentions_adu: yes|no|could_not_access` rows in `wi_adu_rules.csv`, with host, method, HTTP status, matched terms and file checksum in `notes`.

**Method.** `scripts/scan_adu_mentions.py` fetches the most direct current code text it can (code PDF, adopting ordinance, codepublishing page, archived copy) with a plain HTTP GET, extracts text (`pdftotext`, docx XML, or HTML), and regex-searches the terms; it records the nearest preceding section citation for the first hit (approximate). **Municode, ecode360, codepublishing and several city sites returned HTTP 403 to the scanner (21 of 37 targets).** For those, the first-pass answer comes from the research agents' reading of the same codes on 2026-10-23 through search-engine renderings, a browser, or mirrors, and is labelled accordingly (`verified` for rendered official text, `source_lead` for mirrors and search extracts). No place is left `could_not_access`.

**Result: 22 of 37 mention ADUs; 15 do not.** Ran 2026-10-24; scan output sha256 `52ead9eca449d6eb7cff7fd7271e1dc834428f7477f9266d87a33a610f0983fe` (final run; it changes with page content and run date).

| Municipality | Code host scanned | How | Mentions ADU | First hit (approx.) | Label | Second-pass class |
| --- | --- | --- | --- | --- | --- | --- |
| Milwaukee | city Clerk PDF (Ch. 295 subch. 5) | manual (scanner 403) | yes | Table 295-505-2.5 | verified | restricted |
| Madison | Municode | manual (Legistar texts) | yes | MGO 28.151 | verified | compliant |
| Green Bay | Municode ordinance PDF (G.O. 24-25) | automated | yes | §44-1580(f) | verified | restricted |
| Kenosha | Municode | manual | no | – | verified | restricted (domestic-help quarters) |
| Racine | Municode | manual | no | – | verified | prohibited |
| Appleton | city code PDF (Ch. 23) | manual | yes | §23-55 | verified | compliant |
| Waukesha | Legistar (adopted Ch. 22.03) | automated | yes | 22.03(6)(C)(4) | verified | restricted |
| Eau Claire | city LDO PDF | manual (403) | yes | 17.03.04(B)(2) | verified | restricted |
| Oshkosh | Wayback copy of Ch. 30 | automated | yes | §30-86(X) | verified | restricted |
| Janesville | Municode | manual (search extracts) | no | – | source lead | prohibited |
| West Allis | Legistar (O-2022-0024) | automated | yes | §19.36 | verified | restricted |
| La Crosse | Legistar (Ord. 5280) | automated | yes | §115-405 | verified | restricted |
| Sheboygan | Ch. 105 compiled 2023 (council packet) | automated | no | – | verified | prohibited |
| Wauwatosa | Legistar (O-25-25) | automated | yes | §24.10.075 | verified | compliant |
| Fond du Lac | Zoneomics mirror of Ch. 720 | automated | yes | §720-11C(29) | verified* | restricted |
| New Berlin | Municode | manual (mirror) | yes | §275-42 C(3) | source lead | restricted |
| Wausau | Municode | manual (browser) | yes | §23.03.28(6) | verified | restricted |
| Brookfield | codepublishing | manual | no | – | verified | prohibited |
| Beloit | Municode | manual (mirror) | no | – | source lead | restricted (guest/employee quarters) |
| Greenfield | Municode | manual | no | – | verified | prohibited |
| Franklin | city UDO PDF | automated | yes | §15-4-13 | verified | restricted |
| Oak Creek | ecode360 print (copy) | automated | yes | §17.0414 | verified | restricted |
| Manitowoc | codepublishing | manual | no | – | verified | prohibited |
| West Bend | city Ch. 17 PDF (2022) | automated | no | – | verified | prohibited |
| Sun Prairie | Municode ordinance PDF (Ord. 984) | automated | yes | §17.16.140(33) | verified | restricted |
| Superior | Municode | manual (browser) | no | – | verified | prohibited |
| Stevens Point | city Ch. 23 PDF | automated | yes | §23.01(15) | verified | restricted |
| Neenah | Municode | manual (mirror) | no | – | source lead | prohibited |
| Fitchburg | city (Ord. 2025-O-17) | automated | yes | Sec. 22-230 | verified | compliant |
| Muskego | ecode360 | manual (rendered) | yes (in-law) | §400-165 | verified | restricted |
| Mequon | Municode | manual | yes | §58-248 | verified | restricted |
| De Pere | city Ch. 14 PDF | automated | yes | §14-27 | verified | restricted |
| Mount Pleasant | ecode360 | manual (rendered) | yes (backyard cottage, secondary suite) | §90-110.20(g) | verified | restricted |
| Caledonia | Municode (staff report scanned) | manual | no | – | source lead | prohibited |
| Pleasant Prairie | ecode360 | manual (rendered) | no | – | verified | prohibited |
| Menomonee Falls | Municode | manual | no | – | verified | prohibited |
| Howard | Municode | manual (mirror) | no | – | source lead | prohibited |

First-hit sections in the table are the coded sections; the scanner's own nearest-citation guess (in the CSV `source_section`) is approximate and sometimes points to a cross-reference. *Fond du Lac's automated hit is on a mirror.

**What the first pass tells us.** Mention and allowance line up well: all 22 places that mention ADUs allow some form (20 restricted or compliant, plus New Berlin's attached family unit). Two places allow a second-dwelling form without ADU vocabulary (Kenosha domestic-help quarters, Beloit guest/employee quarters), and every `no` place is otherwise prohibited. So for the uncoded remainder, "no mention" is a cheap, fairly reliable screen for `prohibited`, while "mentions" always needs the second pass because the class can be anything from New Berlin to Madison.

**Extending the scan.** The scanner is cheap only where hosts allow plain GETs; Municode and ecode360, which host most Wisconsin codes, refuse it. Extending beyond the 37 needs either a browser-based reader or the hosts' search pages read by hand; not done in this pass.

## Second pass: method

1. **Frame.** The ~30 largest municipalities by population and one-unit detached homes, plus restrictive-comparison candidates. IDs are 10-digit Census county-subdivision GEOIDs (`wi_muni_id`, from the 2024 Gazetteer `2024_gaz_cousubs_55.txt`, sha256 `543aec3d…ff939`). Places split across counties (Milwaukee, Appleton, Eau Claire, Howard) carry one `rights_exposure` row per piece, all pointing to the same rules; `policy_rules.jurisdiction_id` uses the largest piece.
2. **Sources.** Codified zoning text (Municode, ecode360, codepublishing, city PDFs), adopted ordinances (Legistar and municipal ordinance PDFs), staff reports and minutes, in that order. News and vendor summaries were used only as leads.
3. **Provisions.** `policy_rules.provision` uses the DATA_CONTRACTS vocabulary. Form provisions are coded `by_right` / `conditional` / `prohibited` / `unknown`; `owner_occupancy` is `none` / `at_permit` / `ongoing` / `unknown`; `occupant_restriction` is `none` / `related_only` / `unknown`. History is kept as earlier rows with `effective_to`. Blank `effective_from` means "in the code before any change we could date", not a known date.
4. **Classes** (SCOPE_AND_MODEL rights classes; benchmark = one ADU per single-family parcel, detached and attached by right, ≥600 sq ft allowed, no extra parking, no owner-occupancy or related-occupant rule, AQ-022):
   - `compliant`: all of that by right in essentially all single-family districts.
   - `restricted`: some ADU form allowed, with any binding limit (conditional use, owner occupancy, related or employee occupants, a size cap that can fall below 600 sq ft, extra parking, attached-only or detached-only, or only some single-family districts).
   - `prohibited`: no ADU form on single-family parcels.
5. **Scenarios.** `adu_full` (headline, AQ-022): every restricted or prohibited place → `compliant`. `adu_form_only` (sensitivity): places with a current owner-occupancy or related-occupant rule → `forms_with_occupancy_limits`; others → `compliant`. Compliant places are unchanged in both (reform = current, so additional = 0).
6. **`rules_as_of`** is the latest ordinance or code-supplement date the coding reflects (e.g. code "current through" date or the last adopted ADU ordinance). For two places with no currency date shown (Greenfield, Mount Pleasant) it is the access date. All are ≤ 2026-10-31.
7. **Verification labels.** `verified` = the team read the codified text, adopted ordinance, or official staff document. Where Municode or ecode360 blocked direct fetch (403/Cloudflare), agents read the official page through a search-engine rendering (Exa) or a browser and cross-checked a mirror; those are labelled `verified` and flagged in the source notes. Mirror-only, news, or snippet claims are `source_lead`. A second reader has not yet checked a sample (Gate 2 acceptance check, still to do).

## Second pass: summary table

Ordered by one-unit detached homes. "Extra parking" is spaces required for the ADU. Full sections, URLs and history are in the CSV.

| Municipality | Class | Basis | Rules as of | Detached | Attached | Owner occ. | Extra parking | Main binding limit(s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Milwaukee | restricted | verified | 2025-08-02 | by right | by right | at permit | 0 | Owner must occupy at application (File 240999, eff. 2025-08-02) |
| Madison | compliant | verified | 2025-10-16 | by right | by right | none | 0 | Edge cases only |
| Green Bay | restricted | verified | 2025-12-02 | CUP | CUP | ongoing | 1 | CUP; owner occupancy; parking (G.O. 24-25, 29-25) |
| Kenosha | restricted* | verified | 2026-04-20 | domestic-help quarters, RS-1 only | no | none | unknown | Only "residential quarters for domestic help" (§3.04.A.4) |
| Racine | prohibited | verified | 2026-03-03 | no | no | – | – | §114-691 accessory buildings not for living |
| Janesville | prohibited | verified | 2026-04-27 | no | no | – | – | Draft Ch. 46 (ADUs with owner occupancy) not adopted as of 2026-10-23 |
| Appleton | compliant | verified | 2026-02-01 | by right | by right (+JADU) | none | 0 | – (§23-55/56, 2021) |
| Eau Claire | restricted | verified | 2026-05-04 | by right (limited-use permit) | by right | none | 1 | Parking (LDO eff. 2025-10-01) |
| Oshkosh | restricted | verified | 2026-03-31 | by right | by right | none | 0 | 400 sq ft cap (§30-86(X), 2023) |
| Waukesha | restricted | verified | 2026-09-01 | by right | by right | none | 1 | Parking; 75%-of-house cap (Ord. 2026-4, eff. 2026-09-01) |
| West Allis | restricted | verified | 2026-02-24 | by right | limited (2-unit rules) | none | 0 | Footprint ≤50% of house, 800 sq ft |
| Wauwatosa | compliant | verified | 2025-11-18 | by right | by right | none | 0 | – (O-25-25) |
| Sheboygan | prohibited | verified | 2026-04-08 | no | no | – | – | ADU ordinances 37-25-26 / 39-25-26 not adopted; referred 2026-04-08 |
| Brookfield | prohibited* | verified | 2026-02-17 | no | no | – | – | One-family only; undefined "guest houses" |
| New Berlin | restricted | source lead | 2026-01-27 | no | family unit | ongoing | unknown | Attached only; related occupants; 50% cap |
| Fond du Lac | restricted | verified | 2026-03-25 | by right (special conditions) | by right | ongoing | 1 | Owner occupancy; parking; 800 sq ft (Ord. 3809, 2025-02-26) |
| Wausau | restricted | verified | 2026-07-14 | CUP | CUP | ongoing | unknown | CUP; owner occupancy; 800 sq ft / 75% |
| La Crosse | restricted | verified | 2024-02-17 | by right | no | ongoing | 0 | Detached only; owner occupancy (Ord. 5280) |
| Menomonee Falls | prohibited | verified | 2026-03-02 | no | no | – | – | One principal structure per lot |
| Beloit | restricted* | source lead | 2026-06-01 | guest house / employee quarters | no | none | – | Non-rented; lots ≥12,000 sq ft |
| Manitowoc | prohibited | verified | 2026-09-30 | no | no | – | – | Ch. 35 draft not adopted |
| Franklin | restricted | verified | 2025-06-09 | CUP | CUP (internal by right) | ongoing | 0 | CUP; owner occupancy (Ord. 2025-2675) |
| Oak Creek | restricted | verified | 2026-04-06 | CUP, above/in garage only | CUP | ongoing | ≥1 | CUP; owner occupancy; 800 sq ft/50%; parking |
| Caledonia | prohibited | verified | 2026-09-28 | no | no | – | – | Staff drafting CUP-only ADUs (pending) |
| Neenah | prohibited | source lead | 2025-09-03 | no | no | – | – | One dwelling per R-1 lot; draft ADU ordinance never adopted (as far as found) |
| Muskego | restricted | verified | 2026-03-24 | CUP (employee/relative) | Plan Commission review (relatives) | unknown | – | Related occupants; no rental |
| Sun Prairie | restricted | verified | 2026-05-08 | special use | special use | none | 0 | Not in ER-1/RH-35 (Ord. 984, adopted 2026-05-05) |
| Greenfield | prohibited | verified | 2026-10-23 | no | no | – | – | One principal building per lot |
| Superior | prohibited | verified | 2025-12-02 | no | no | – | – | Rewrite draft not adopted |
| Mount Pleasant | restricted | verified | 2026-10-23 | by right | by right | one rental per lot | 0 / unknown | 40%-of-house cap |
| West Bend | prohibited | source lead | 2022-02-16 | no | no | – | – | Codified text only through 2022-02-16 |
| Mequon | restricted | verified | 2025-12-09 | no | CUP | ongoing | unknown | Attached only; related occupants; 40% cap |
| De Pere | restricted | verified | 2026-07-21 | by right | by right | ongoing | 0 | Owner occupancy (2023 code) |
| Pleasant Prairie | prohibited | verified | 2026-08-24 | no | no | – | – | §420-30B accessory structures not dwellings |
| Fitchburg | compliant | verified | 2025-09-10 | by right | by right | none | unknown | 75% cap binds only under 800 sq ft (Sec. 22-230) |
| Stevens Point | restricted | verified | 2026-05-05 | CUP | no | ongoing | 1 | CUP; detached only; owner occupancy; parking |
| Howard | prohibited | source lead | 2026-07-27 | no | no | – | – | §50-868 no living space in accessory buildings |

\* Borderline. Kenosha (domestic-help quarters) and Beloit (non-rented guest houses, employee quarters) are coded `restricted` because the code names a second-dwelling form with an occupant limit; reclassify `prohibited` if the owner does not count these as ADU forms. Brookfield is coded `prohibited`; it would become `restricted` if its undefined "guest houses" were counted. The choice changes no reform result (all three become `compliant` under `adu_full`), only the baseline class rate.

## Corrections to the Gate 1 discovery list

- **Sheboygan:** Gate 1 listed a December 2025 ADU ordinance. It was never adopted: Gen. Ord. 37-25-26 was laid over (2026-01-05) and the revised 39-25-26 was referred to the next council on 2026-04-08 ([minutes and code](https://mccmeetingspublic.blob.core.usgovcloudapi.net/sheboygnwi-meet-1ab88e5a89ad4af6836be2c56109cdb0/ITEM-Attachment-001-015d62d52b424fc985217ee1b0ae1f13.pdf)). Coded `prohibited`.
- **Green Bay:** adopted 2025-12-02 as conditional use with ongoing owner occupancy and 1 parking space (not just "conditional use").
- **Sun Prairie:** Ord. 984 adopted 2026-05-05 (special use, no owner occupancy, 1,000 sq ft, no parking).
- **Wauwatosa:** O-25-25 confirmed (adopted 2025-11-18; Legistar 25-1940).
- **Milwaukee:** the passed version was Substitute 4 ("Proposed Substitute C"), passed 2025-07-15, effective 2025-08-02; owner occupancy applies only at application.

## Bias findings for the AQ-023 default

AQ-023 treats every uncoded municipality as `prohibited`. Among the coded places, that default would have been:

| Coded class | Places | One-unit detached homes | Default correct? |
| --- | ---: | ---: | --- |
| prohibited | 13 | 141,675 | yes |
| restricted | 20 | 336,548 | no: overstates added rights (some form already allowed) |
| compliant | 4 | 93,913 | no: credits a reform effect where the reform adds ~nothing |
| **Total** | **37** | **572,136** | wrong for 24 places, 430,461 homes (75%) |

- The default errs in one direction: it **overstates** the reform's added rights. For compliant places it would wrongly add a full prohibited → compliant step.
- Large cities are more often liberalized than the rest (Milwaukee, Madison, Green Bay, Appleton, Eau Claire, Oshkosh, Waukesha, Wauwatosa changed rules in 2019–2026), so this 75% is an **upper estimate** for the uncoded remainder; smaller suburbs in this sample were mostly prohibited (Greenfield, Menomonee Falls, Brookfield, Pleasant Prairie, Caledonia, Howard, West Bend). The spot-check sample planned under AQ-023 is needed to size the bias for small places.
- 7 of the 20 restricted places differ from the benchmark **only** on size, parking or process (Eau Claire, Oshkosh, Waukesha, West Allis, Sun Prairie, Kenosha, Beloit); the rest have owner-occupancy or related-occupant rules, which matter for the `adu_form_only` sensitivity (15 places move to `forms_with_occupancy_limits`).

## Pending changes to re-check before the 2026-10-31 freeze

| Place | Pending item | Effect if adopted |
| --- | --- | --- |
| Janesville | New Ch. 46 (draft 2026-04-30) allows ADUs, owner-occupied, 900 sq ft; council target "fall 2026" | prohibited → restricted |
| Caledonia | Staff directed 2026-09-28 to draft CUP ADUs | prohibited → restricted |
| Racine | ZOrd.0007-26 rewrite (introduced 2026-09-11) has no ADU use | no change |
| Superior, Manitowoc, Neenah, La Crosse, Oshkosh | Zoning rewrites in progress | possible later change |
| Eau Claire | August 2026 LDO amendment is a scanned PDF, unread | unknown |

## Open items and known gaps

- Parking unknown: Kenosha, New Berlin, Wausau, Mequon, Fitchburg, Mount Pleasant (cottages). Size cap unknown: Stevens Point (Ch. 30).
- History not found: pre-2020 Wausau, pre-2022 Oak Creek, pre-2023 De Pere and Oshkosh ordinance number, Stevens Point ADU ordinance number/date (~2022), Kenosha domestic-help clause date, pre-2021 Appleton.
- Codified text read only through a mirror: Howard, Beloit, Neenah (current text), New Berlin; West Bend only through 2022.
- `verified` labels on Municode/ecode360 text rest on rendered copies where direct fetch was blocked; downgrade to `source_lead` if the owner requires a direct primary fetch.
- Second-reader check of a sample of codings (Gate 1 acceptance check) is not yet done.

## Sources (accessed 2026-10-23 unless noted)

Each CSV row carries its own `source_url` and `source_section`. Principal documents:

- Milwaukee: [File 240999 Substitute 4](https://milwaukee.legistar1.com/milwaukee/attachments/257d5d3c-c659-463b-8bd3-8d499a6255c2.rtf); [CPC staff report 2025-04-07](https://milwaukee.legistar1.com/milwaukee/attachments/2caab317-6bf8-4cb3-a0c0-19ed63033977.pdf); [DCD ADU page](https://city.milwaukee.gov/DCD/Planning/PlanningAdministration/ZoningResources/Accessory-Dwelling-Units)
- Madison: Gate 1 [Policy Evidence Map §2](../gate1/POLICY_EVIDENCE_MAP.md) and its Legistar sources; 2026 Legistar title search found no new ADU ordinance
- Green Bay: [G.O. 24-25](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400450/pdf), [G.O. 29-25](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400449/pdf)
- Kenosha: [Zoning Ordinance (Municode)](https://library.municode.com/wi/kenosha/codes/zoning_ordinance)
- Racine: [Ch. 114 (Municode)](https://library.municode.com/wi/racine/codes/code_of_ordinances?nodeId=PTIIMUCO_CH114ZO_ARTVDIRE_DIV2REDI); [BZA staff report 1038-24](https://cityofracine.legistar1.com/cityofracine/attachments/0f020bcb-d8cf-494e-8c4a-98cc8c625efb.pdf)
- Janesville: [Code (Municode)](https://library.municode.com/wi/janesville/codes/code_of_ordinances); [draft Ch. 46](https://graef-usa.mysocialpinpoint.com/janesvillezoning)
- Appleton: [Legistar 2021 ADU/JADU item](https://cityofappleton.legistar.com/LegislationDetail.aspx?GUID=96A34E37-FF1B-4AE2-B7A9-1E1BF0F8367E&ID=4970068); Ch. 23 Supp. 100 (Feb 2026)
- Eau Claire: [Land Development Ordinance](https://www.eauclairewi.gov/DocumentCenter/View/1033/Land-Development-Ordinance-PDF); [old zoning ordinance](https://www.eauclairewi.gov/DocumentCenter/View/1036/Zoning-Ordinance-PDF)
- Oshkosh: [Ch. 30 (archived 2025-12-14)](https://web.archive.org/web/20251214231347/https://www.oshkoshwi.gov/WebLink/DocView.aspx?id=1183289&dbid=0&repo=Laserfiche)
- Waukesha: [Ord. 2026-4](https://legistar2.granicus.com/waukesha/attachments/fb763278-f10c-4d54-91b2-240833e68012.pdf), [Ch. 22.03](https://legistar2.granicus.com/waukesha/attachments/c852c290-1ccf-4801-9967-8d87347537fd.pdf), [Ch. 22.06](https://legistar2.granicus.com/waukesha/attachments/8c8662e7-dfc1-4ece-b405-5a0c1116a477.pdf)
- West Allis: [O-2022-0024](https://westalliswi.legistar1.com/westalliswi/attachments/df2ec2d7-5409-4759-a080-5366789281e4.pdf), [O-2023-0031](https://westalliswi.legistar1.com/westalliswi/attachments/c1e7f426-a56f-412e-bac2-b38e83565261.pdf)
- Wauwatosa: [O-25-25](https://wauwatosacitywi.legistar1.com/wauwatosacitywi/attachments/f54c270b-576f-4e05-a954-36755d2e4f9c.pdf); [O-19-11](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true)
- Sheboygan: [Ch. 105 compiled 2023 and minutes](https://mccmeetingspublic.blob.core.usgovcloudapi.net/sheboygnwi-meet-1ab88e5a89ad4af6836be2c56109cdb0/ITEM-Attachment-001-015d62d52b424fc985217ee1b0ae1f13.pdf)
- Brookfield: [Title 17 §17.28](https://www.codepublishing.com/WI/Brookfield/html/Brookfield17/Brookfield1728.html)
- New Berlin: Gate 1 [Policy Evidence Map §3](../gate1/POLICY_EVIDENCE_MAP.md)
- Fond du Lac: Ch. 720 §720-11C(29); Ord. 3809, City Council minutes 2025-02-26 ([city site](https://www.fdl.wi.gov/))
- Wausau: [Title 23 (Municode)](https://library.municode.com/wi/wausau/codes/code_of_ordinances?nodeId=TIT23ZO_ARTIIILAUSRE)
- La Crosse: [Ord. 5280 text](https://legistar.granicus.com/CityofLaCrosse/attachments/239dbc28-943b-4645-9f22-e87475d777da.docx)
- Menomonee Falls: [Ch. 122 (Municode)](https://library.municode.com/wi/menomonee_falls/codes/code_of_ordinances?nodeId=COOR_CH122ZO_ARTIVUS_DIV5ACUSDEUSSPCO)
- Beloit: Ch. 19 via [Zoneomics mirror](https://www.zoneomics.com/code/beloit-WI)
- Manitowoc: [Ch. 15](https://www.codepublishing.com/WI/Manitowoc/html/Manitowoc15/Manitowoc15110.html)
- Franklin: [UDO 2025](https://www.franklinwi.gov/Files/Planning/UDO-Rewrite-2025/2025-UDO-Rewrite-Text.pdf)
- Oak Creek: [ecode360 print 2025-12-03](https://assets.parkingreform.org/assets/7d1088f1-4f0b-4f6a-a368-d7a3b6c4d398/oak-creek-wisconsin-united-states-attachment.pdf)
- Caledonia: [Plan Commission staff report 2026-09-28](https://data.zoninghub.com/viewfile.aspx?fileid=110664)
- Neenah: [Plan Commission 2025-04-29](https://www2.ci.neenah.wi.us/committees.nsf/0/740d7c8b6bbec18886258c6f005576e1/$FILE/A%2020250429PC.pdf)
- Muskego: [ecode360 §§400-165, 400-172](https://ecode360.com/29722805)
- Sun Prairie: [Ord. 984](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1423544/pdf)
- Greenfield: [Ch. 21 (Municode)](https://library.municode.com/wi/greenfield/codes/code_of_ordinances?nodeId=CH21ZOCO_PT4ZODIDIESDIUSRE_DIV21.04.0800ACTEUSSTRE_21.04.0802DESTACUSREDI)
- Superior: [Ch. 122 (Municode)](https://library.municode.com/wi/superior/codes/code_of_ordinances?nodeId=PTIICOOR_CH122ZO)
- Mount Pleasant: [§90-110.20(g)](https://ecode360.com/36325067), [§90-330.110](https://ecode360.com/36325586)
- West Bend: [Ch. 17 (2022)](https://cms9files.revize.com/westbend/17%20Chapter%20Municipal%20Code-%201.pdf)
- Mequon: [Ch. 58 (Municode)](https://library.municode.com/wi/mequon/codes/code_of_ordinances?nodeId=PTIICOOR_CH58PLDERE_ARTIVZO_DIV3REDI_SDIIUSRE)
- De Pere: [Ch. 14 (2023)](https://www.deperewi.gov/egov/documents/1703171468_81245.pdf)
- Pleasant Prairie: [Ch. 420 (ecode360)](https://ecode360.com/36640696)
- Fitchburg: [Ord. 2025-O-17](https://fitchburgwi.gov/DocumentCenter/View/29094/2025-O-17)
- Stevens Point: [Ch. 23](https://www.stevenspoint.com/DocumentCenter/View/769/Chapter-23---Zoning--Floodplain)
- Howard: Ch. 50 via [Zoneomics mirror](https://www.zoneomics.com/code/howard-WI); Village Board President report 2026-07-13 ([DocumentCenter/View/11523](https://www.villageofhoward.com/DocumentCenter/View/11523))

State context: no Wisconsin ADU statute; AB 449 / SB 473 and AB 365 / SB 247 failed 2026-03-23 (Gate 1 [Policy Evidence Map §1](../gate1/POLICY_EVIDENCE_MAP.md)).

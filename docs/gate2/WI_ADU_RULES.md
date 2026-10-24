# Wisconsin ADU Rules: Largest Jurisdictions (current law frozen 2026-10-31)

Prepared 2026-10-23/24 for Gate 2; revised 2026-10-24 after the independent review (items S5–S7, N6, N7) and the owner's AQ-026 decision on rights classes and restriction flags. Tables: [`reference/wi_adu_rules.csv`](../../reference/wi_adu_rules.csv) (`policy_rules`, 295 rows: 220 hand-coded provision rows, 38 derived `approval_pathway` rows and 37 first-pass `ordinance_status` rows) and [`reference/wi_rights_exposure.csv`](../../reference/wi_rights_exposure.csv) (`rights_exposure`, 86 rows = 43 county-subdivision pieces × 2 scenarios). The hand-coded record is [`reference/wi_adu_rules_spec.py`](../../reference/wi_adu_rules_spec.py).

Reproduce: `uv run python scripts/scan_adu_mentions.py` (network; writes `data/processed/adu_mention_scan/scan.csv`, git-ignored; needs `pdftotext` and `curl`), then `uv run python scripts/build_reference_rules.py reference reference data/processed/adu_mention_scan`, then `uv run python scripts/check_reference_rules.py` (prints `OK`). Tests: `tests/test_reference_rules.py`. Source copies read on 2026-10-24 are in `data/raw/wi_adu_rules_sources/2026-10-24/` (git-ignored).

## Headline

- **37 municipalities coded**: the 32 named in the work package plus Mequon, De Pere, Pleasant Prairie, Menomonee Falls and Howard. They hold **572,136 of Wisconsin's 1,839,569 one-unit detached homes (31.1%)** (ACS 2020–2024 5-year B25024_002, from `data/processed/foundation/inventory.parquet`).
- **Current class (2026-10-31), AQ-026 classes:** 2 `scenario_benchmark` (Madison, Wauwatosa), 22 `restricted`, 5 `prohibited_explicit`, 8 `prohibited_implicit`. None is `undetermined` or `no_zoning`.
- **Restriction flags:** 18 of the 22 restricted places have at least one tier-1 ("poison pill" or form) flag; the other 4 (Appleton, Oshkosh, Sun Prairie, Fitchburg) are held back only by tier-2 limits (size or districts). Owner occupancy (12 places, 220,445 homes) and below-benchmark size caps (12 places, 146,825 homes) are the most common.
- **Approval pathway (AQ-025):** of the 24 places that allow some ADU form, 17 approve ministerially and 7 need discretionary review (Green Bay, Wausau, Franklin, Oak Creek, Stevens Point, Muskego, Mequon). The 13 prohibited places have no pathway (`unknown`).
- **Basis:** 23 `coded_verified`, 14 `coded_source_lead`. The increase in source leads (from 5) comes from applying the verification rule consistently (below), not from new doubts about the coding.
- **AQ-023 bias:** treating uncoded places as having no ADU rights would have been **wrong for 24 of 37 places (65%) and 430,461 of 572,136 one-unit detached homes (75%)**. See [Bias findings](#bias-findings-for-the-aq-023-default).

## What changed in the 2026-10-24 revision

| Item | Before | After | Why |
| --- | --- | --- | --- |
| Class vocabulary | compliant / restricted / prohibited (+ `forms_with_occupancy_limits` reform class) | `scenario_benchmark` / `restricted` (+ flags) / `prohibited_explicit` / `prohibited_implicit` / `no_zoning` / `undetermined` | Owner decision AQ-026 |
| Current classes | 4 compliant, 20 restricted, 13 prohibited | 2 benchmark, 22 restricted, 5 explicit + 8 implicit prohibited | AQ-026 flag rule: Appleton (35%-of-house attached cap) and Fitchburg (75%-of-house cap) can fall below 600 sq ft, so both are now `restricted` with only `size_below_benchmark` |
| Sun Prairie approval (S5) | forms `conditional`, counted as discretionary | forms `by_right`, approval `special use, ministerial` | Ord. 984: "Permitted by right: Not applicable" and "Conditional use regulations: Not applicable"; ADUs sit under *special use regulations*, which §17.44.040 (Ord. 922) has the zoning administrator approve after staff review, with no hearing. Districts SR-4, MR-8, UR-12, NC, UC, CC, PD; the single-family districts excluded are **RH-35ac, CR-5ac and ER-1** (Table 17.16.030 has six residential districts: RH-35ac, CR-5ac, ER-1, SR-4, MR-8, UR-12). No extra parking |
| Verification labels (S6) | 216 verified / 24 source lead / 7 unknown rows; renderings labelled `verified` | 192 / 83 / 20 (of 295 rows) | One rule for every row (see [method](#second-pass-method)). Text seen only through a search-engine rendering or a mirror is now `source_lead`. Places whose code text was read only that way became `coded_source_lead`: Kenosha, Janesville, Fond du Lac, Greenfield, Muskego, Mequon, Mount Pleasant, Pleasant Prairie, Menomonee Falls (plus the existing New Berlin, Beloit, West Bend, Neenah, Howard) |
| Kenosha occupant (S6) | `related_only`, detached by right | `employee_only` (domestic help are household employees); form `unknown` (a permitted *principal* use in RS-1, form not stated) | Second reader |
| Beloit occupant | `related_only` | `other` (non-paying guests or employees, no rental) | Same reasoning |
| Racine | all rows from a Municode rendering | the prohibition rests on the BZA staff report 1038-24 (re-read from Legistar) | Keeps a verified basis |
| Sheboygan (S6) | cited the 2023 Ch. 105 compilation | also cites council minutes: 37-25-26 laid over 2026-01-05 and filed 2026-03-16; 39-25-26 referred to the 2026-27 council on 2026-04-08; on pending list | Second reader |
| Mount Pleasant owner occupancy (S6) | table "one rental per lot", CSV `ongoing` | both `ongoing` (de facto: only one of the two units may be rented; cottages need a deed restriction) | Consistency |
| Eau Claire (N7) | one unread August amendment | Ord. 7614 (adopted 2026-04-28, published 2026-05-04) read via rendering: no ADU change; the 2026-08-11 amendment is still unread | Second reader |
| Approval pathway (AQ-025) | free-text `approval_type` | new `approval_pathway` rows and exposure column (ministerial / discretionary / unknown) | Owner direction |
| First pass (S7) | `mentions_adu: yes/no`; 10 terms; 21 of 37 blocked | `ordinance_status` (AQ-026); 15 terms; 19 of 37 blocked (codepublishing now read through a `curl` fallback) | Reviewer and owner |
| First-pass arithmetic | "22 places … (20 restricted or compliant, plus New Berlin)" (sums to 21) | Old list: 22 mentioned, all 22 of them restricted or compliant (New Berlin is one of the 20 restricted) | Arithmetic fix |

## First pass: ordinance status (AQ-026)

The first pass answers one question per municipality: **does the code have an ADU ordinance at all?** It is stored as `provision = ordinance_status` with `value` = `mentioned_allowed` (an ADU term appears and the passage allows that use somewhere), `prohibited` (a term appears only to bar the use, or is defined but listed in no district), `unmentioned` (no term in the text read) or `could_not_access`. **A mention is not an allowance** of benchmark rights: New Berlin mentions ADUs to prohibit detached ones and allows only an attached family unit.

**Terms** (regular expressions in `scripts/scan_adu_mentions.py`): accessory dwelling, ADU, in-law unit/suite/apartment/quarters and mother-in-law, granny flat, coach house, carriage house, secondary dwelling unit/suite, backyard cottage, the defined term "Family dwelling unit" (New Berlin; matched case-sensitively at the start of a heading or sentence so "single-family dwelling unit" does not count), and, **added 2026-10-24 after the review**: accessory living, accessory apartment, guest house, domestic-help/servant/employee/caretaker quarters, and dependency living (Madison's and Fitchburg's historical term). The domestic-help pattern requires the word "quarters", so a family definition that excludes "domestic employees" does not match.

**Method.** The scanner fetches the most direct code text it can with a plain HTTP GET (and a plain `curl` GET when Python's client is refused), extracts text (`pdftotext`, docx XML or HTML; a codepublishing table of contents is expanded to all its section pages), and searches the terms. Each scan row records the host, the **kind of document read**, the HTTP status, the terms, the approximate section of the first hit and a checksum. Final run 2026-10-24, scan output sha256 `a7b0cddf6fc1ed99fa939123b127fe97056575c2dc61596f2d3c963f8c193a92` (it changes with page content and run date).

**Read this before relying on the first pass:**

- **19 of 37 targets refused the scanner** (HTTP 403 from Municode, ecode360 and several city sites; it was 21 before the `curl` fallback reached codepublishing for Brookfield and Manitowoc). For those 19, plus Caledonia (where the scanner could read only a staff report), the first-pass answer comes from the same research agents' manual reading on 2026-10-23, done through renderings, a browser or mirrors. **So 20 of the 37 first-pass answers are manual, and the first pass is not independent of the second pass** for those places.
- **The 17 automated answers are not all from the current code.** 6 come from the adopting ordinance only, where a hit is guaranteed (Green Bay, West Allis, La Crosse, Wauwatosa, Sun Prairie, Fitchburg); 2 from stale compilations (Sheboygan 2023, West Bend 2022); 1 from a mirror (Fond du Lac). Only 8 come from current codified text or an exact copy of it (Waukesha's adopted chapter, Oshkosh's archived chapter, Franklin, Oak Creek's ecode360 print, Stevens Point, De Pere, Brookfield, Manitowoc).
- **The added terms were not re-searched in the 20 manual places**; only hits the readers had noted are used (Kenosha "residential quarters for domestic help", Beloit "private guest houses" and "employee living quarters", Howard "guesthouse").

**Result (2026-10-24):** 26 `mentioned_allowed`, 1 `prohibited` (Howard: "guesthouse" defined but allowed in no district), 10 `unmentioned`, 0 `could_not_access`.

| Municipality | Document read | How | Status | Terms (first hit) | Label | Second-pass class |
| --- | --- | --- | --- | --- | --- | --- |
| Milwaukee | Ch. 295 subch. 5 | manual (rendering) | mentioned_allowed | accessory dwelling (Table 295-505-2.5) | source lead | restricted |
| Madison | Legistar ordinance texts | manual | mentioned_allowed | accessory dwelling (MGO 28.151) | verified | scenario_benchmark |
| Green Bay | adopting ordinance G.O. 24-25 | automated | mentioned_allowed | accessory dwelling, carriage house | verified | restricted |
| Kenosha | zoning ordinance | manual (rendering) | mentioned_allowed | domestic-help quarters (§3.04.A.4) | source lead | restricted |
| Racine | Ch. 114 | manual (rendering) | unmentioned | – | source lead | prohibited_explicit |
| Appleton | Ch. 23 (Supp. 100) | manual | mentioned_allowed | accessory dwelling (§23-55) | verified | restricted |
| Waukesha | adopted Ch. 22.03 | automated | mentioned_allowed | accessory dwelling | verified | restricted |
| Eau Claire | LDO | manual (browser) | mentioned_allowed | accessory dwelling (17.03.04(B)(2)) | verified | restricted |
| Oshkosh | archived Ch. 30 | automated | mentioned_allowed | accessory dwelling (§30-86) | verified | restricted |
| Janesville | Ch. 42 | manual (search extracts) | unmentioned | – | source lead | prohibited_implicit |
| West Allis | adopting ordinance O-2022-0024 | automated | mentioned_allowed | accessory dwelling | verified | restricted |
| La Crosse | adopting ordinance 5280 | automated | mentioned_allowed | accessory dwelling (§115-405) | verified | restricted |
| Sheboygan | Ch. 105 compiled 2023 (stale) | automated | unmentioned | – | verified | prohibited_explicit |
| Wauwatosa | adopting ordinance O-25-25 | automated | mentioned_allowed | accessory dwelling | verified | scenario_benchmark |
| Fond du Lac | Zoneomics mirror of Ch. 720 | automated | mentioned_allowed | accessory dwelling | source lead | restricted |
| New Berlin | Ch. 275 | manual (mirror) | mentioned_allowed | family dwelling unit (§275-42 C(3)) | source lead | restricted |
| Wausau | Title 23 | manual (browser) | mentioned_allowed | accessory dwelling, in-law (§23.03.28(6)) | verified | restricted |
| Brookfield | Title 17 (all 48 pages) | automated | mentioned_allowed | guest house (R-1, inside the house), servants' quarters (UC district only) | verified | prohibited_implicit* |
| Beloit | Ch. 19 | manual (mirror) | mentioned_allowed | guest house, employee quarters (§6.3.3(a)) | source lead | restricted |
| Greenfield | Ch. 21 | manual (rendering) | unmentioned | – | source lead | prohibited_implicit |
| Franklin | UDO 2025 | automated | mentioned_allowed | accessory dwelling | verified | restricted |
| Oak Creek | ecode360 print copy | automated | mentioned_allowed | accessory dwelling | verified | restricted |
| Manitowoc | Ch. 15 (all 40 pages) | automated | mentioned_allowed | secondary dwelling unit (§15.730 TND only) | verified | prohibited_implicit* |
| West Bend | Ch. 17 codified 2022 (stale) | automated | unmentioned | – | verified | prohibited_implicit |
| Sun Prairie | adopting ordinance 984 | automated | mentioned_allowed | accessory dwelling | verified | restricted |
| Superior | Ch. 122 | manual (browser) | unmentioned | – | verified | prohibited_implicit |
| Stevens Point | Ch. 23 | automated | mentioned_allowed | accessory dwelling | verified | restricted |
| Neenah | Ch. 26 | manual (mirror) | unmentioned | – | source lead | prohibited_explicit |
| Fitchburg | adopting ordinance 2025-O-17 | automated | mentioned_allowed | accessory dwelling (Sec. 22-230) | verified | restricted |
| Muskego | Ch. 400 | manual (rendering) | mentioned_allowed | in-law (§400-165) | source lead | restricted |
| Mequon | Ch. 58 | manual (rendering) | mentioned_allowed | accessory dwelling (§58-248) | source lead | restricted |
| De Pere | Ch. 14 | automated | mentioned_allowed | accessory dwelling, backyard cottage | verified | restricted |
| Mount Pleasant | Ch. 90 | manual (rendering) | mentioned_allowed | backyard cottage, secondary suite (§90-110.20(g)) | source lead | restricted |
| Caledonia | Title 16 (staff report scanned) | manual | unmentioned | – | source lead | prohibited_implicit |
| Pleasant Prairie | Ch. 420 | manual (rendering) | unmentioned | – | source lead | prohibited_explicit |
| Menomonee Falls | Ch. 122 | manual (rendering) | unmentioned | – | source lead | prohibited_implicit |
| Howard | Ch. 50 | manual (mirror) | prohibited | guesthouse (§50-6), listed in no district | source lead | prohibited_explicit |

\* The expanded terms turned up two second-dwelling passages the original list missed, neither available on an ordinary single-family lot: Brookfield allows guest space *inside* the house in R-1 and servants' quarters only in the UC Upland Conservancy district; Manitowoc allows secondary dwelling units only inside a Traditional Neighborhood Development (§15.730), a whole-neighborhood plan. Both stay `prohibited_implicit` and are flagged borderline.

**How good is the screen?**

- With the **original term list**, 15 places had no mention and 2 of them (13%) are coded `restricted` (Kenosha's domestic-help quarters and Beloit's guest/employee quarters). "No mention → prohibited" was therefore **right for 13 of 15 (87%)** on these large municipalities.
- With the **expanded list**, all 10 `unmentioned` places and the 1 `prohibited` place are prohibited in the second pass, but 2 `mentioned_allowed` places are prohibited too (Brookfield, Manitowoc). For 8 of the 10 unmentioned places the answer is manual and the new terms were not re-searched, so this agreement is partly built in.
- The screen is **untested on small places**, where codes are older and second-dwelling vocabulary varies more. It is a cheap triage, not a substitute for the second pass: every `mentioned_allowed` place needs reading, because the class ranges from Brookfield (`prohibited_implicit`) to Madison (`scenario_benchmark`).

**Extending the scan.** Municode and ecode360, which host most Wisconsin codes, refuse plain GETs. Extending beyond the 37 needs either their search pages read by hand or a browser-based reader (not done; the repair round forbids browsers).

## Second pass: method

1. **Frame.** The ~30 largest municipalities by population and one-unit detached homes, plus restrictive-comparison candidates. IDs are 10-digit Census county-subdivision GEOIDs (`wi_muni_id`, from the 2024 Gazetteer `2024_gaz_cousubs_55.txt`, sha256 `543aec3d…ff939`). Places split across counties (Milwaukee, Appleton, Eau Claire, Howard) carry one `rights_exposure` row per piece, all pointing to the same rules; `policy_rules.jurisdiction_id` uses the largest piece.
2. **Sources.** Codified zoning text (Municode, ecode360, codepublishing, city PDFs), adopted ordinances (Legistar and municipal ordinance PDFs), staff reports and minutes, in that order. News and vendor summaries are leads only.
3. **Provisions.** `policy_rules.provision` uses the DATA_CONTRACTS vocabulary plus two new coded provisions: `approval_pathway` (AQ-025) and `ordinance_status` (AQ-026). Form provisions are `by_right` / `conditional` / `prohibited` / `unknown`; `owner_occupancy` is `none` / `at_permit` / `ongoing` / `unknown`; `occupant_restriction` is `none` / `related_only` / `employee_only` / `other` / `unknown` (`employee_only` and `other` added 2026-10-24). History is kept as earlier rows with `effective_to`. A blank `effective_from` means "in the code before any change we could date", not a known date. **DATA_CONTRACTS.md still needs the two new provisions and two new occupant values** (owned by the conductor).
4. **Benchmark** (AQ-022, AQ-026): one ADU per single-family parcel, detached and attached, at least 600 sq ft, by right, no extra parking, no owner-occupancy or occupant rule.
5. **Classes** (`missing_middleware.contracts.RIGHTS_CLASS`, AQ-026):
   - `scenario_benchmark`: the benchmark is already granted in essentially all single-family districts.
   - `restricted`: some ADU form is allowed, but at least one restriction flag applies.
   - `prohibited_explicit`: the code says no ADUs, or no living space in accessory buildings (Racine §114-691/§114-292, Sheboygan §105-722, Neenah §21-19, Pleasant Prairie §420-30B, Howard §50-868).
   - `prohibited_implicit`: the code lists the permitted uses and forms and ADUs are not among them, usually with "one principal building per lot" (Janesville, Brookfield, Greenfield, Manitowoc, West Bend, Superior, Caledonia, Menomonee Falls).
   - `no_zoning` and `undetermined`: not used among the 37. **Towns** (not coded yet): in Wisconsin a town is under county general zoning only where the county has adopted general zoning and the town board has approved it (Wis. Stat. s. 59.69); a town with village powers may adopt its own zoning. A town is `no_zoning` only when neither applies.
6. **Restriction flags** (`contracts.RESTRICTION_FLAGS`; column `restrictions` in `wi_rights_exposure.csv`, a semicolon list, non-empty exactly when the class is `restricted`). **A flag applies only if the provision prevents a benchmark ADU on at least some single-family lots.** Tier 1 follows the Mercatus 2025 taxonomy (Hamilton and Peterson) core barriers:
   - Tier 1 (poison pills and form): `owner_occupancy` (ongoing or at application), `related_occupant` (relatives, caregivers, household employees or non-paying guests), `extra_parking` (more parking than the house alone, including replacement parking), `discretionary_review` (conditional or special use with a hearing, plan commission), `form_limited` (attached-only, detached-only or conversions-only).
   - Tier 2: `size_below_benchmark`, `siting_limits`, `lot_minimum`, `district_limited`, `fees`, `other`.
   - **Size rule:** an absolute cap of 600 sq ft or more is not a flag, nor is a cap equal to the house's own size (it binds only for houses under 600 sq ft). A percent-of-house cap below 100%, or a coverage/FAR cap that can fall below 600 sq ft, is `size_below_benchmark`; the house size below which it binds is recorded in the exposure `notes` (e.g. Appleton 600/0.35 ≈ 1,714 sq ft).
   - A size cap that binds only on unusually small lots (Kenosha's 15%-of-lot accessory cap, under 4,000 sq ft lots; Eau Claire's detached 20%-of-lot cap, under 3,000 sq ft lots) is noted but not flagged on its own.
7. **Approval pathway** (AQ-025): `approval_pathway` = `ministerial` (permit, staff or zoning-administrator approval against standards, no hearing) / `discretionary` (conditional use, special use with a hearing, plan commission review) / `unknown`. It is derived from each `approval_type` row by keyword (an explicit "ministerial" wins; then conditional / special use / plan commission → discretionary; then permit / permitted / administrative / staff / limited use / by right → ministerial). Where a place has no `approval_type` row it is derived from its current form rows (any `by_right` → ministerial; else `conditional` → discretionary). Prohibited places get `unknown` ("not applicable: no ADU form is allowed"). The builder fails if a discretionary place lacks the `discretionary_review` flag. Where forms differ (West Allis: detached by right, attached under two-unit rules; Franklin and Mequon: internal or basement units administrative), the pathway follows the main ADU route and the other route is noted.
8. **Scenarios.** `adu_full` (headline, AQ-022): every coded place → `scenario_benchmark` (a `no_zoning` place would stay `no_zoning`). `adu_form_only` (sensitivity): places whose flags include `owner_occupancy` or `related_occupant` → `restricted`, with those flags in `reform_restrictions`; all others → `scenario_benchmark`. Benchmark places are unchanged in both (additional = 0). `restrictions` minus `reform_restrictions` is what the reform removes.
9. **`rules_as_of`** is the latest ordinance or code-supplement date the coding reflects. For Greenfield and Mount Pleasant (no currency date shown) it is the access date. All are ≤ 2026-10-31.
10. **Verification labels** (one rule for every row, revised 2026-10-24):
    - `verified`: the team read the official document itself: on the official host (municipality, its Legistar or agenda site, its ordinance library or code publisher), as an archived capture of the official host (Wayback), or as the official file re-hosted unchanged (Oak Creek's ecode360 print PDF). Reading the official page in a browser counts (Eau Claire, Wausau, Superior).
    - `source_lead`: the text was seen only as a third party's extraction or re-typeset copy: a search-engine rendering of a blocked Municode or ecode360 page, a Zoneomics mirror, a snippet, or news.
    - `class_basis` is `coded_verified` only when at least one *current* detached or attached rule is verified (the checker enforces this); otherwise `coded_source_lead`.
    - The reviewer suggested a separate `verified_rendered` label. The contract's `CLAIM_STATUS` has only `verified` / `source_lead` / `unknown`, so rendered copies are `source_lead` and the row notes say "via search-engine rendering". Adding a value is a contract change for the conductor.

## Second pass: summary table

Ordered by one-unit detached homes. "Extra parking" is spaces required for the ADU. Flags are in the next section; sections, URLs and history are in the CSV.

| Municipality | Class | Basis | Rules as of | Detached | Attached | Owner occ. | Extra parking | Approval | Main binding limit(s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Milwaukee | restricted | verified | 2025-08-02 | by right | by right | at permit | 0 | ministerial | Owner must occupy at application (File 240999, eff. 2025-08-02) |
| Madison | scenario_benchmark | verified | 2025-10-16 | by right | by right | none | 0 | ministerial | Edge cases only |
| Green Bay | restricted | verified | 2025-12-02 | CUP | CUP | ongoing | 1 | discretionary | CUP; owner occupancy; parking (G.O. 24-25, 29-25) |
| Kenosha | restricted* | source lead | 2026-04-20 | domestic-help quarters, RS-1 only (form not stated) | same | none | unknown | ministerial | Occupants must be domestic employees (§3.04.A.4) |
| Racine | prohibited_explicit | verified | 2026-03-03 | no | no | – | – | – | Accessory buildings not for living; BZA 1038-24 |
| Janesville | prohibited_implicit | source lead | 2026-04-27 | no | no | – | – | – | Draft Ch. 46 (ADUs with owner occupancy) not adopted |
| Appleton | restricted* | verified | 2026-02-01 | by right | by right (+JADU) | none | 0 | ministerial | Attached-accessory cap 35% of house incl. basement (binds under ~1,714 sq ft) |
| Eau Claire | restricted | verified | 2026-05-04 | by right (limited-use permit) | by right | none | 1 | ministerial | Parking; attached 40% of building |
| Oshkosh | restricted | verified | 2026-03-31 | by right | by right | none | 0 | ministerial | 400 sq ft cap (§30-86(X), 2023) |
| Waukesha | restricted | verified | 2026-09-01 | by right | by right | none | 1 | ministerial | Parking; attached 40% / detached 75% of house (Ord. 2026-4) |
| West Allis | restricted | verified | 2026-02-24 | by right | two-unit rules only | none | 0 | ministerial | Footprint ≤ 50% of house (max 800); attached limited |
| Wauwatosa | scenario_benchmark | verified | 2025-11-18 | by right | by right | none | 0 | ministerial | – (O-25-25) |
| Sheboygan | prohibited_explicit | verified | 2026-04-08 | no | no | – | – | – | §105-722; rewrites 37-25-26 filed, 39-25-26 referred 2026-04-08 |
| Brookfield | prohibited_implicit* | verified | 2026-02-17 | no | no | – | – | – | One-family only; guest space inside the house; servants' quarters in UC only |
| New Berlin | restricted | source lead | 2026-01-27 | no | family unit | ongoing | unknown | ministerial | Attached only; related occupants; 50% cap |
| Fond du Lac | restricted | source lead | 2026-03-25 | by right (special conditions) | by right | ongoing | 1 | ministerial | Owner occupancy; parking (Ord. 3809, 2025-02-26) |
| Wausau | restricted | verified | 2026-07-14 | CUP | CUP | ongoing | unknown | discretionary | CUP; owner occupancy; 75% cap; not in DR-6 |
| La Crosse | restricted | verified | 2024-02-17 | by right | no | ongoing | 0 | ministerial | Detached only; owner occupancy (Ord. 5280) |
| Menomonee Falls | prohibited_implicit | source lead | 2026-03-02 | no | no | – | – | – | One principal structure per lot |
| Beloit | restricted* | source lead | 2026-06-01 | guest house / employee quarters | no | none | – | ministerial | Non-rented; lots ≥ 12,000 sq ft |
| Manitowoc | prohibited_implicit* | verified | 2026-09-30 | no (TND only) | no (TND only) | – | – | – | Secondary units only in a TND; Ch. 35 draft not adopted |
| Franklin | restricted | verified | 2025-06-09 | CUP | CUP (internal by right) | ongoing | 0 | discretionary | CUP; owner occupancy (Ord. 2025-2675) |
| Oak Creek | restricted | verified | 2026-04-06 | CUP, above/in garage only | CUP | ongoing | ≥ 1 | discretionary | CUP; owner occupancy; 50% cap; parking |
| Caledonia | prohibited_implicit | verified | 2026-09-28 | no | no | – | – | – | Staff drafting CUP-only ADUs (pending) |
| Neenah | prohibited_explicit | source lead | 2025-09-03 | no | no | – | – | – | §21-19 accessory building not a dwelling; draft never adopted (as far as found) |
| Muskego | restricted | source lead | 2026-03-24 | CUP (employee/relative) | Plan Commission review (relatives) | unknown | – | discretionary | Related occupants; no rental |
| Sun Prairie | restricted | verified | 2026-05-08 | by right (special use, staff) | by right (special use, staff) | none | 0 | ministerial | Not in RH-35ac, CR-5ac, ER-1 (Ord. 984, adopted 2026-05-05) |
| Greenfield | prohibited_implicit | source lead | 2026-10-23 | no | no | – | – | – | One principal building per lot |
| Superior | prohibited_implicit | verified | 2025-12-02 | no | no | – | – | – | Rewrite draft not adopted |
| Mount Pleasant | restricted | source lead | 2026-10-23 | by right | by right | ongoing (one unit may be rented) | 0 / unknown | ministerial | Owner occupancy; 40%-of-house cap |
| West Bend | prohibited_implicit | source lead | 2022-02-16 | no | no | – | – | – | Codified text only through 2022-02-16 |
| Mequon | restricted | source lead | 2025-12-09 | no | CUP | ongoing | unknown | discretionary | Attached only; related occupants; 40% cap |
| De Pere | restricted | verified | 2026-07-21 | by right | by right | ongoing | 0 | ministerial | Owner occupancy; suite 30% of house (2023 code) |
| Pleasant Prairie | prohibited_explicit | source lead | 2026-08-24 | no | no | – | – | – | §420-30B accessory structures not dwellings |
| Fitchburg | restricted | verified | 2025-09-10 | by right | by right | none | unknown | ministerial | 75%-of-house cap (binds under 800 sq ft) |
| Stevens Point | restricted | verified | 2026-05-05 | CUP | no | ongoing | 1 | discretionary | CUP; detached only; owner occupancy; parking |
| Howard | prohibited_explicit | source lead | 2026-07-27 | no | no | – | – | – | §50-868 no living space in accessory buildings |

\* Borderline, for the owner to settle:

- **Kenosha and Beloit** are `restricted` because the code names a second dwelling with an occupant limit (Kenosha: domestic-help quarters in RS-1; Beloit: non-rented guest houses and employee quarters); reclassify `prohibited_implicit` if these are not ADU forms.
- **Brookfield and Manitowoc** are `prohibited_implicit` although their codes have second-dwelling passages (R-1 guest space inside the house and UC-only servants' quarters; TND-only secondary units).
- **Appleton** is `restricted` only by `size_below_benchmark`, and only if §23-43(i)'s 35% attached-accessory cap applies to attached ADUs as the city's January 2025 ADU guide applied it. The city's accessory-building worksheet says the cap is "1,600 sq ft or 35% … whichever is greater", which would never bind, and the guide reissued 2026-10-14 no longer states the cap. The codified text was not reachable. If the cap does not bind, Appleton is `scenario_benchmark`.

None of these choices changes an `adu_full` result (all become `scenario_benchmark`); they change only the baseline class counts and, for Kenosha and Beloit, the `adu_form_only` sensitivity.

## Restriction flags by place

OO owner_occupancy, RO related_occupant, XP extra_parking, DR discretionary_review, FL form_limited (tier 1); SZ size_below_benchmark, SI siting_limits, LM lot_minimum, DL district_limited, FE fees, OT other (tier 2). Ordered by one-unit detached homes.

| Municipality | Approval | OO | RO | XP | DR | FL | SZ | SI | LM | DL | FE | OT |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| Milwaukee | ministerial | ● |  |  |  |  |  |  |  |  |  |  |
| Green Bay | discretionary | ● |  | ● | ● |  |  |  |  |  |  |  |
| Kenosha | ministerial |  | ● |  |  |  |  |  |  | ● |  |  |
| Appleton | ministerial |  |  |  |  |  | ● |  |  |  |  |  |
| Eau Claire | ministerial |  |  | ● |  |  | ● |  |  |  |  |  |
| Oshkosh | ministerial |  |  |  |  |  | ● |  |  |  |  |  |
| Waukesha | ministerial |  |  | ● |  |  | ● |  |  |  |  |  |
| West Allis | ministerial |  |  |  |  | ● | ● |  |  |  |  |  |
| New Berlin | ministerial | ● | ● |  |  | ● | ● |  |  |  |  |  |
| Fond du Lac | ministerial | ● |  | ● |  |  |  |  |  |  |  |  |
| Wausau | discretionary | ● |  |  | ● |  | ● |  |  | ● |  |  |
| La Crosse | ministerial | ● |  |  |  | ● |  |  |  |  |  |  |
| Beloit | ministerial |  | ● |  |  | ● |  |  | ● |  |  | ● |
| Franklin | discretionary | ● |  |  | ● |  |  |  |  |  |  |  |
| Oak Creek | discretionary | ● |  | ● | ● | ● | ● |  |  | ● |  |  |
| Muskego | discretionary |  | ● |  | ● |  |  |  |  |  |  | ● |
| Sun Prairie | ministerial |  |  |  |  |  |  |  |  | ● |  |  |
| Mount Pleasant | ministerial | ● |  |  |  |  | ● |  |  |  |  |  |
| Mequon | discretionary | ● | ● |  | ● | ● | ● |  |  | ● |  |  |
| De Pere | ministerial | ● |  |  |  |  | ● |  |  |  |  |  |
| Fitchburg | ministerial |  |  |  |  |  | ● |  |  |  |  |  |
| Stevens Point | discretionary | ● |  | ● | ● | ● |  |  | ● |  |  |  |

Flag notes: Beloit `other` = the 1,000 sq ft minimum dwelling size; Muskego `other` = no rental, and a 1,200 sq ft minimum for detached quarters. Size caps bind on houses under: Appleton ~1,714 sq ft (attached, incl. basement, less any attached garage); Eau Claire 1,500 (attached); Waukesha 1,500 attached / 800 detached; West Allis 1,200 sq ft footprint; New Berlin, Oak Creek 1,200; Mount Pleasant, Mequon 1,500; De Pere 2,000 (suite); Wausau, Fitchburg 800; Oshkosh at every size (400 sq ft cap). No place was flagged for `siting_limits` or `fees`: setbacks and ADU-specific fees were not coded systematically, so a zero there means "not checked", not "none".

**Count of places per flag** (22 restricted places; a place can carry several flags):

| Tier | Flag | Places | One-unit detached homes |
| --- | --- | ---: | ---: |
| 1 | `owner_occupancy` | 12 | 220,445 |
| 1 | `related_occupant` | 5 | 62,286 |
| 1 | `extra_parking` | 6 | 86,279 |
| 1 | `discretionary_review` | 7 | 77,229 |
| 1 | `form_limited` | 7 | 71,378 |
| 2 | `size_below_benchmark` | 12 | 146,825 |
| 2 | `siting_limits` | 0 (not checked) | 0 |
| 2 | `lot_minimum` | 2 | 16,385 |
| 2 | `district_limited` | 5 | 59,954 |
| 2 | `fees` | 0 (not checked) | 0 |
| 2 | `other` | 2 | 18,706 |

18 restricted places (312,026 homes) have at least one tier-1 flag; 4 (Appleton, Oshkosh, Sun Prairie, Fitchburg; 52,211 homes) have only tier-2 flags.

**Form-only sensitivity.** 15 restricted places keep occupancy flags under `adu_form_only` and stay `restricted` (263,312 homes): the 12 owner-occupancy places plus Kenosha, Beloit and Muskego (related-occupant only). The other 7 restricted places (Appleton, Eau Claire, Oshkosh, Waukesha, West Allis, Sun Prairie, Fitchburg) differ from the benchmark only on size, parking, form or districts and become `scenario_benchmark` in both scenarios. (The earlier draft listed Kenosha and Beloit among the "size, parking or process only" places; that was wrong, because both have occupant rules.)

## Approval pathway (AQ-025)

| Pathway | Places | One-unit detached homes | Places |
| --- | ---: | ---: | --- |
| ministerial | 17 | 353,232 | Milwaukee, Madison, Kenosha, Appleton, Eau Claire, Oshkosh, Waukesha, West Allis, Wauwatosa, New Berlin, Fond du Lac, La Crosse, Beloit, Sun Prairie, Mount Pleasant, De Pere, Fitchburg |
| discretionary | 7 | 77,229 | Green Bay, Wausau, Franklin, Oak Creek, Stevens Point, Muskego, Mequon |
| unknown (no ADU form allowed) | 13 | 141,675 | the 13 prohibited places |

Sun Prairie moved from discretionary to ministerial (S5). Madison's history row records discretionary review (every ADU a conditional use) from 2013-06-04 to 2021-12-15. AQ-025's "at least 6" discretionary places becomes **7** (AQ-025 text is owned by the conductor).

## Corrections to the Gate 1 discovery list

- **Sheboygan:** Gate 1 listed a December 2025 ADU ordinance. It was never adopted. Gen. Ord. 37-25-26 laid over on 2026-01-05 and was filed on 2026-03-16 ([minutes 2026-03-16](https://mccmeetings.blob.core.usgovcloudapi.net/sheboygnwi-pubu/MEET-Minutes-d7d70b7e4efe4892ad3bfe1f6a029d4b.pdf)). The revised 39-25-26 (ADUs with 183-day owner occupancy and a 40% size cap) was referred to the 2026-27 council on 2026-04-08 ([minutes 2026-04-08](https://mccmeetings.blob.core.usgovcloudapi.net/sheboygnwi-pubu/MEET-Minutes-aa9ca83a5a024e488fdf0bbbd0b74044.pdf)). A 2026-10-20 news item still describes a proposed rewrite (source lead). Coded `prohibited_explicit`.
- **Green Bay:** adopted 2025-12-02 as a conditional use, with ongoing owner occupancy and 1 parking space (not just "conditional use").
- **Sun Prairie:** Ord. 984 adopted 2026-05-05: a special use approved by staff without a hearing, no owner occupancy, 1,000 sq ft, no parking, not in RH-35ac, CR-5ac or ER-1.
- **Wauwatosa:** O-25-25 confirmed (adopted 2025-11-18; Legistar 25-1940).
- **Milwaukee:** the passed version was Substitute 4 ("Proposed Substitute C"), passed 2025-07-15 and effective 2025-08-02; owner occupancy applies only at application.

## Bias findings for the AQ-023 default

AQ-023 treats every uncoded municipality as `undetermined`, modeled as having no ADU rights. Among the coded places, that default would have been:

| Coded class | Places | One-unit detached homes | Default correct? |
| --- | ---: | ---: | --- |
| prohibited_explicit | 5 | 55,547 | yes |
| prohibited_implicit | 8 | 86,128 | yes |
| restricted | 22 | 364,237 | no: overstates added rights (some form already allowed) |
| scenario_benchmark | 2 | 66,224 | no: credits a reform effect where the reform adds ~nothing |
| **Total** | **37** | **572,136** | wrong for 24 places, 430,461 homes (75%) |

- The default errs in one direction: it **overstates** the reform's added rights. For benchmark places it would wrongly add a full prohibited → benchmark step.
- Large cities are more often liberalized than the rest (Milwaukee, Madison, Green Bay, Appleton, Eau Claire, Oshkosh, Waukesha and Wauwatosa changed their rules in 2019–2026), so this 75% is an **upper estimate** for the uncoded remainder. Smaller suburbs in this sample were mostly prohibited (Greenfield, Menomonee Falls, Brookfield, Pleasant Prairie, Caledonia, Howard, West Bend). The spot-check sample planned under AQ-023 is needed to size the bias for small places.
- The uncoded remainder is 1,882 county-subdivision pieces, or 1,813 municipalities (counting each municipality once).

## Pending changes to re-check before the 2026-10-31 freeze

| Place | Pending item | Effect if adopted |
| --- | --- | --- |
| Sheboygan | Zoning rewrite 39-25-26 (ADUs with 183-day owner occupancy, one-family occupancy, 40% cap) referred to the 2026-27 council on 2026-04-08; community sessions held in October 2026 | prohibited_explicit → restricted (owner_occupancy, related_occupant, size_below_benchmark) |
| Janesville | New Ch. 46 (draft 2026-04-30): ADUs, owner-occupied, 900 sq ft; council target "fall 2026" | prohibited_implicit → restricted |
| Caledonia | Staff directed 2026-09-28 to draft CUP ADUs | prohibited_implicit → restricted |
| Eau Claire | LDO amendment effective 2026-08-11 (scanned PDF, unread; Plan Commission summary lists no ADU change) | probably none |
| Pleasant Prairie (pilot) | Confirm §420-30B from a primary copy (only renderings read) | label only |
| Appleton | Confirm whether §23-43(i)'s 35% attached cap applies to ADUs | restricted → scenario_benchmark if not |
| Racine | ZOrd.0007-26 rewrite (introduced 2026-09-11) has no ADU use | no change |
| Superior, Manitowoc, Neenah, La Crosse, Oshkosh | Zoning rewrites in progress | possible later change |

## Open items and known gaps

- Parking unknown: Kenosha, New Berlin, Wausau, Mequon, Fitchburg, Mount Pleasant (cottages). Size cap unknown: Stevens Point (Ch. 30). Setbacks (`siting_limits`) and ADU-specific fees (`fees`) not coded anywhere.
- History not found: pre-2020 Wausau, pre-2022 Oak Creek, pre-2023 De Pere and Oshkosh ordinance number, Stevens Point ADU ordinance number/date (~2022), Kenosha domestic-help clause date, pre-2021 Appleton.
- Code text seen only through renderings or mirrors (14 `coded_source_lead` places): Kenosha, Janesville, Fond du Lac, Greenfield, Muskego, Mequon, Mount Pleasant, Pleasant Prairie, Menomonee Falls, New Berlin, Beloit, Neenah, Howard; West Bend only through 2022. Municode and ecode360 refuse plain HTTP, so a primary read needs another route.
- Second reader: 8 places plus Sun Prairie were checked (Gate 2 review); the findings are applied above.
- Contract follow-ups for the conductor: add `approval_pathway` and `ordinance_status` to the DATA_CONTRACTS provision vocabulary, and `employee_only` / `other` to `occupant_restriction`; `wi_rights_exposure.csv` adds the columns `restrictions`, `reform_restrictions` and `approval_pathway` (not yet in `RIGHTS_EXPOSURE.required`).

## Sources (accessed 2026-10-23 unless noted; re-read items 2026-10-24)

Each CSV row carries its own `source_url` and `source_section`. Principal documents:

- Milwaukee: [File 240999 Substitute 4](https://milwaukee.legistar1.com/milwaukee/attachments/257d5d3c-c659-463b-8bd3-8d499a6255c2.rtf); [CPC staff report 2025-04-07](https://milwaukee.legistar1.com/milwaukee/attachments/2caab317-6bf8-4cb3-a0c0-19ed63033977.pdf); [DCD ADU page](https://city.milwaukee.gov/DCD/Planning/PlanningAdministration/ZoningResources/Accessory-Dwelling-Units)
- Madison: Gate 1 [Policy Evidence Map §2](../gate1/POLICY_EVIDENCE_MAP.md) and its Legistar sources; 2026 Legistar title search found no new ADU ordinance
- Green Bay: [G.O. 24-25](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400450/pdf), [G.O. 29-25](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400449/pdf)
- Kenosha: [Zoning Ordinance (Municode)](https://library.municode.com/wi/kenosha/codes/zoning_ordinance)
- Racine: [Ch. 114 (Municode)](https://library.municode.com/wi/racine/codes/code_of_ordinances?nodeId=PTIIMUCO_CH114ZO_ARTVDIRE_DIV2REDI); [BZA staff report 1038-24](https://cityofracine.legistar1.com/cityofracine/attachments/0f020bcb-d8cf-494e-8c4a-98cc8c625efb.pdf) (re-read 2026-10-24, sha256 `8aa0e337…ab10`)
- Janesville: [Code (Municode)](https://library.municode.com/wi/janesville/codes/code_of_ordinances); [draft Ch. 46](https://graef-usa.mysocialpinpoint.com/janesvillezoning)
- Appleton: [Legistar 2021 ADU/JADU item](https://cityofappleton.legistar.com/LegislationDetail.aspx?GUID=96A34E37-FF1B-4AE2-B7A9-1E1BF0F8367E&ID=4970068); Ch. 23 Supp. 100 (Feb 2026); [ADU guide, edited 2026-10-14](https://cms2.revize.com/revize/appletonwi/Documents/CommDev/Planning/Plans%20and%20Reports/City%20of%20Appleton%20-%20Accessory%20Dwelling%20Units%20(ADU)%20Guide.pdf) (2026-10-24, sha256 `a238691a…fc93`); [accessory-building worksheet](https://cms2.revize.com/revize/appletonwi/Documents/CommDev/Building%20Inspection/Permits/building/Accessory%20Bldg%20.pdf) (PDF dated 2024-08-05, sha256 `8f68b5dc…9899`); the January 2025 guide edition is known from the second reader's review only
- Eau Claire: [Land Development Ordinance](https://www.eauclairewi.gov/DocumentCenter/View/1033/Land-Development-Ordinance-PDF); [old zoning ordinance](https://www.eauclairewi.gov/DocumentCenter/View/1036/Zoning-Ordinance-PDF); [Ord. 7614](https://www.eauclairewi.gov/DocumentCenter/View/1479/No-7614-PDF) (adopted 2026-04-28, published 2026-05-04; read via search-engine rendering 2026-10-24); [Plan Commission minutes 2026-08-03](https://www.eauclairewi.gov/AgendaCenter/ViewFile/Minutes/_08032026-165) (summary of the 2026-08-11 amendment); [LDO page](https://www.eauclairewi.gov/650/Land-Development-Ordinances) lists both amendments
- Oshkosh: [Ch. 30 (archived 2025-12-14)](https://web.archive.org/web/20251214231347/https://www.oshkoshwi.gov/WebLink/DocView.aspx?id=1183289&dbid=0&repo=Laserfiche)
- Waukesha: [Ord. 2026-4](https://legistar2.granicus.com/waukesha/attachments/fb763278-f10c-4d54-91b2-240833e68012.pdf), [Ch. 22.03](https://legistar2.granicus.com/waukesha/attachments/c852c290-1ccf-4801-9967-8d87347537fd.pdf), [Ch. 22.06](https://legistar2.granicus.com/waukesha/attachments/8c8662e7-dfc1-4ece-b405-5a0c1116a477.pdf)
- West Allis: [O-2022-0024](https://westalliswi.legistar1.com/westalliswi/attachments/df2ec2d7-5409-4759-a080-5366789281e4.pdf), [O-2023-0031](https://westalliswi.legistar1.com/westalliswi/attachments/c1e7f426-a56f-412e-bac2-b38e83565261.pdf)
- Wauwatosa: [O-25-25](https://wauwatosacitywi.legistar1.com/wauwatosacitywi/attachments/f54c270b-576f-4e05-a954-36755d2e4f9c.pdf); [O-19-11](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true)
- Sheboygan: [Ch. 105 compiled 2023](https://mccmeetingspublic.blob.core.usgovcloudapi.net/sheboygnwi-meet-1ab88e5a89ad4af6836be2c56109cdb0/ITEM-Attachment-001-015d62d52b424fc985217ee1b0ae1f13.pdf); Common Council [agenda 2026-01-05](https://mccmeetings.blob.core.usgovcloudapi.net/sheboygnwi-pubu/MEET-Packet-e1d3cb4ec4c5400797b865c76fb7f273.pdf) (37-25-26 lays over), [minutes 2026-03-16](https://mccmeetings.blob.core.usgovcloudapi.net/sheboygnwi-pubu/MEET-Minutes-d7d70b7e4efe4892ad3bfe1f6a029d4b.pdf) (37-25-26 filed; 39-25-26 to Committee of the Whole), [minutes 2026-04-08](https://mccmeetings.blob.core.usgovcloudapi.net/sheboygnwi-pubu/MEET-Minutes-aa9ca83a5a024e488fdf0bbbd0b74044.pdf) (39-25-26 referred to the 2026-27 council), all re-read 2026-10-24; [Seehafer News 2026-10-20](https://www.seehafernews.com/2026/10/20/sheboygan-adds-two-more-zoning-code-engagement-sessions/) (source lead)
- Brookfield: [Title 17 §17.28](https://www.codepublishing.com/WI/Brookfield/html/Brookfield17/Brookfield1728.html); [Ch. 17.24 UC district](https://www.codepublishing.com/WI/Brookfield/html/Brookfield17/Brookfield1724.html) (2026-10-24)
- New Berlin: Gate 1 [Policy Evidence Map §3](../gate1/POLICY_EVIDENCE_MAP.md)
- Fond du Lac: Ch. 720 §720-11C(29); Ord. 3809, City Council minutes 2025-02-26 ([city site](https://www.fdl.wi.gov/))
- Wausau: [Title 23 (Municode)](https://library.municode.com/wi/wausau/codes/code_of_ordinances?nodeId=TIT23ZO_ARTIIILAUSRE)
- La Crosse: [Ord. 5280 text](https://legistar.granicus.com/CityofLaCrosse/attachments/239dbc28-943b-4645-9f22-e87475d777da.docx)
- Menomonee Falls: [Ch. 122 (Municode)](https://library.municode.com/wi/menomonee_falls/codes/code_of_ordinances?nodeId=COOR_CH122ZO_ARTIVUS_DIV5ACUSDEUSSPCO)
- Beloit: Ch. 19 via [Zoneomics mirror](https://www.zoneomics.com/code/beloit-WI)
- Manitowoc: [Ch. 15](https://www.codepublishing.com/WI/Manitowoc/html/Manitowoc15/Manitowoc15110.html); [§15.730 TND](https://www.codepublishing.com/WI/Manitowoc/html/Manitowoc15/Manitowoc15730.html) (2026-10-24)
- Franklin: [UDO 2025](https://www.franklinwi.gov/Files/Planning/UDO-Rewrite-2025/2025-UDO-Rewrite-Text.pdf)
- Oak Creek: [ecode360 print 2025-12-03](https://assets.parkingreform.org/assets/7d1088f1-4f0b-4f6a-a368-d7a3b6c4d398/oak-creek-wisconsin-united-states-attachment.pdf)
- Caledonia: [Plan Commission staff report 2026-09-28](https://data.zoninghub.com/viewfile.aspx?fileid=110664)
- Neenah: [Plan Commission 2025-04-29](https://www2.ci.neenah.wi.us/committees.nsf/0/740d7c8b6bbec18886258c6f005576e1/$FILE/A%2020250429PC.pdf)
- Muskego: [ecode360 §§400-165, 400-172](https://ecode360.com/29722805)
- Sun Prairie: [Ord. 984](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1423544/pdf) (re-read 2026-10-24, sha256 `3b277266…9973`); [Ord. 922](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1245783/pdf?forceDownload=true) (§17.44.040 special-use review, adopted 2023-09-19; sha256 `bf2e5174…4261`); [Ord. 896](https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1162266/pdf) (Table 17.16.030 district columns; sha256 `ce041536…1ae0`); [Table 17.16.030 (Municode)](https://library.municode.com/wi/sun_prairie/codes/code_of_ordinances?nodeId=TIT17ZO_CH17.16LAUSRE_17.16.030TALAUS) (single-family rows via search-engine rendering)
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

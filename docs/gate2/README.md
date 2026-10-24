# Gate 2 Packet: Usable Data and Verified Connections

Prepared 2026-10-24 by the conductor; revised after independent review. **Status: awaiting owner decision.** Gate 2 is not passed until the owner says so.

## What this gate decides

Whether the data we now hold is fit to build the ADU baseline and policy response on (Gate 3): the statewide foundation; permit records for the permissive pilot (Madison), the restrictive pilot (Pleasant Prairie), and the same-market historical check (Sun Prairie 2016–2025); and coded local ADU rules for the 37 largest municipalities under the two-pass scheme (AQ-026).

## Artifacts

| What | Where |
| --- | --- |
| Statewide foundation: areas, ACS homes, housing conditions, BPS crosswalk | [FOUNDATION.md](FOUNDATION.md); build `uv run python scripts/build_foundation.py` |
| Madison permits | [MADISON_PERMITS.md](MADISON_PERMITS.md); build `uv run python scripts/build_madison_permits.py --fetch` |
| Pleasant Prairie and Sun Prairie permits | [COMPARISON_PERMITS.md](COMPARISON_PERMITS.md); build `uv run python scripts/build_comparison_permits.py --fetch` |
| How the comparison city was chosen | [COMPARISON_CITY_SEARCH.md](COMPARISON_CITY_SEARCH.md) |
| Local ADU rules, 37 largest municipalities | [WI_ADU_RULES.md](WI_ADU_RULES.md); `reference/wi_adu_rules.csv`, `reference/wi_rights_exposure.csv` |
| Review map | `uv run python scripts/build_gate2_review_map.py`, then open `data/processed/review/gate2_map.html` |
| Source-vs-cleaned examples | `data/processed/permits/source_vs_clean_examples.csv` (local only, contains addresses) |

All build commands are also in the README command contract. Raw and processed data stay on your Mac (git-ignored); committed files hold code, tests, docs, and aggregate tables.

## Coverage: what is observed, missing, or assumed

| Input | Statewide | Madison | Pleasant Prairie | Sun Prairie |
| --- | --- | --- | --- | --- |
| One-unit detached homes (denominator) | **Observed**, ACS 2020–24 for every county, municipality, tract, block group: 1,839,569 | Observed: 53,292 | Observed | Observed |
| Housing conditions | **Observed**: PEP county 2020–25, ACS stock, vacancy, mix; Census BPS 2015–25 | Observed | Observed | Observed |
| Total permitted units by place | Observed for 1,098 reporting jurisdictions (2025); **assumed** per-year split of county rows to 724 towns that never report separately (22% of homes); **missing** for 12 municipalities (e.g. Caledonia); Milwaukee's multifamily series **not reported** for 2020, 2023, 2025 | Observed, record-level | Observed, record-level | Observed, applications only |
| ADU permits (text rule) | **Missing** (no statewide source) | **Observed** 2014–2026: 64 text-rule ADU permits | Observed: essentially none | Observed: effectively none in 2016–2025 |
| **Second homes on single-family lots** (headline, AQ-032), 2014–2026 | n/a | **102 units** (93 permits); upper bound 104; **66 without the 2025–26 templated programme**; 2026 provisional | **3** (read as 0–3); upper bound 6 | **3** (2016–2026), 2 of them before its May 2026 ordinance |
| Permit-to-parcel-to-area link | n/a | 98.5% confirmed address match; 99% of counted units in a tract | 93% exact parcel match (99% of new dwellings) | 98% (97% of new dwellings) |
| Current-law ADU rules | **Observed** for 37 municipalities (31% of homes); **assumed** no ADU rights for the rest (AQ-023) | `scenario_benchmark`, verified | `prohibited_explicit`, **source lead** (code site blocks automated reading) | `restricted` since 2026-05 (district_limited only); prohibited before |

## Owner review: step by step, with my self-assessment

| Step | What you do | What you should see | My result |
| --- | --- | --- | --- |
| 1 | Read the coverage table above | Each input marked observed, missing, or assumed | **Pass.** Gaps are named. |
| 2 | Open `data/processed/permits/source_vs_clean_examples.csv` | Source rows with owner and contractor fields redacted beside cleaned rows; units, dates, categories carry over | **Pass for Madison.** The comparison cities have traced examples in COMPARISON_PERMITS.md but no side-by-side file. |
| 3 | In MADISON_PERMITS.md, follow the traced permit and the unmatched example | BLDNRC-2024-10200, detached ADU issued 2024-08-12 → exact address match (confirmed) → tract 55025001300; unmatched BLDNRC-2026-21855 counts toward Madison but no tract | **Pass.** Re-checked against the rebuilt table (record `f1f7fe6fbc23ae30`). The reviewer found 0 tract mismatches across all 8,484 parcel-matched records. |
| 4 | In `reference/wi_rights_exposure.csv`, read Pleasant Prairie (and Madison) | Pleasant Prairie: current `prohibited_explicit`, reform `scenario_benchmark`, rules as of 2026-08-24, source ecode360 Ch. 420 §420-30B; Madison: `scenario_benchmark`, ministerial, verified | **Partly.** Dates and citations present, but Pleasant Prairie's text was read only through a rendered copy; ecode360 shows a bot check that I will not bypass. **Please open [ecode360 Ch. 420](https://ecode360.com/36640696) and confirm §420-30B says an accessory structure may not be a dwelling unit.** |
| 5 | Open the review map | Madison ADU permits concentrate in older near-isthmus and near-west neighborhoods; tract lines follow lakes and arterials; statewide layer colors the 37 coded places by class | **Pass.** Pale green in the north is national forest on the basemap (labeled). |
| 6 | Review the quality findings and accept fitness, or choose a workaround | Below | **Your judgment.** |

## Assumptions this gate relies on

- Permit records are counted at issuance (Sun Prairie: application date, the only date available).
- Second homes on single-family lots combine text-identified ADUs, judged two-unit ADUs, and house-to-duplex conversions on lots that already had a home (AQ-032). "Already had a home" uses assessor year built in Madison and the parcel's permit history in Pleasant Prairie and Sun Prairie.
- Madison's floor for `y` is proposed to use 2022–2025, with 2026 (provisional, templated programme) only as a sensitivity (G2-9).
- One-unit detached homes from ACS 2020–2024 are the denominator; parcels only place records in areas.
- Census BPS county-row permits for 724 towns are split by share of homes (assumed).
- Coded rules are as of 2026-10-31; text seen only through a rendering is a source lead.
- Madison is treated as 80% of benchmark (AQ-030).

## Quality findings

1. **ADU activity is small, and the contrast is clean.** Madison: 64 ADU permits 2014–2026 (3, 2, 3, 1, 1, 2, 0, 1, 5, 7, 10, 13 for 2014–2025, then 16 in 2026 to date). Pleasant Prairie and Sun Prairie under prohibition: essentially none.
2. **Madison against the City's own table.** The City reports permits issued: 49 since 2013. By issue year we count 41, differing in six years by 1–4. Counting by the year in the permit number matches 2014–2022 exactly; that is our inference about the City's method, not confirmed.
3. **Second homes on single-family lots (AQ-032).** Madison: 5, 4, 3, 3, 2, 3, 0, 1, 5, 9, 11, 14 units for 2014–2025, then 42 in 2026 to date (provisional). Nine 2026 "twin home ADU" permits were judged to add two units beside existing 1950s–60s homes; one 2022 permit was new construction on a cleared lot and does not count; one provisional 2026 duplex stays out pending a later check. Pleasant Prairie drops from 6 to 3 after applying its own audit, the same rule as Madison.
4. **A templated programme drives Madison's 2026.** 27 permits in 2025–26 share two template designs from two contractors; they supply 29 of 2026's 42 units and 7 of 2025's 14. They are flagged so Gate 3 can leave them out of the Madison floor except as a sensitivity.
5. **Milwaukee's Census multifamily counts are a reporting gap** (zero apartment units in years with known projects), now marked not reported. Single-family counts are kept.
6. **Rules:** 2 of 37 places meet the benchmark (Madison, Wauwatosa); 22 restricted; 5 explicitly and 8 implicitly prohibited. The most common barriers are owner occupancy (12 places) and percent-of-house size caps that can fall below 600 sq ft (12). Seven require discretionary approval. Treating uncoded places as prohibited would have been wrong for 24 of the 37 (75% of their homes), so the default overstates the reform effect where it still applies.
7. **Privacy.** Owner names are dropped at ingestion; sample files no longer show house numbers, parcel numbers are masked, coordinates rounded. Sample files still show permit numbers, which a city portal can turn back into an address.

## Independent review and repairs

The reviewer confirmed the joins and statewide arithmetic and found two blockers and nine fixes. All were repaired and the affected checks re-run:

- **Blocker: Census permits for some villages were credited to the wrong towns** (Harrison, Rib Mountain, Somers, Bloomfield) because of blank codes. Fixed; only one zero-unit record remains unmatched.
- **Blocker: a clean clone could not rebuild the packet or map.** Fixed: the command contract is filled in and all scripts are committed; a fresh clone ran setup and 67 then-current tests successfully.
- ADU-equivalent rule tightened (multi-unit hosts and one false positive excluded; zero-unit duplex conversions included); Madison ADU counts unchanged.
- City-table comparison now states both counting bases.
- Addresses removed from committed samples, with the redaction in the download code.
- Rules labels made consistent (text seen only through a rendering is a source lead), Sun Prairie and Kenosha recoded, Sheboygan's unadopted ordinance documented, first-pass keyword list widened.
- Context groups computed on whole municipalities; Superior, Stevens Point, Manitowoc now urban; Franklin, Caledonia, Mount Pleasant suburban.
- Integrity checks that hold by construction are no longer presented as validation.

## Decisions requested

| ID | Decision | My recommendation |
| --- | --- | --- |
| G2-1 | Accept the data as fit for Gate 3 | **Accept**, with the gaps above stated in the model |
| G2-2 | ~~Your ADU-equivalent rule~~ | **Decided 2026-10-24 (AQ-032):** headline is second homes on single-family lots (ADUs plus house-to-duplex conversions), components shown |
| G2-3 | ~~ADU conversions of existing space~~ | **Decided 2026-10-24 (AQ-030, AQ-032):** garage and accessory-building conversions count; interior conversions are counted where observed but get no reform uplift |
| G2-4 | Context groups (urban: 20,000+ units, or 10,000+ units at 300+/sq mi and largest in county; suburban: metro county and 425+/sq mi or a city/village with 2,500+ units; small community; rural towns) | **Accept for now** |
| G2-5 | Pleasant Prairie rule check | **Please confirm §420-30B in a browser** (link in step 4); it stays a source lead until then |
| G2-6 | Appleton | Its city guides conflict (35% cap in 2025; no cap in the 2026-10-14 guide). **Code it `scenario_benchmark` if the newest guide reflects the code**; we will confirm from the code text in the later rules pass |
| G2-7 | California comparison data (addendum below) | **Accept**, with the limits stated below |
| G2-8 | Approve the [pre-registered California comparison plan](../gate3/CA_COMPARISON_PLAN.md), as amended before results (cross-state outcome mapping, sources by year, holdout rule) | **Approve** |
| G2-9 | Madison floor years | **Use 2022–2025**; 2026 only as a sensitivity because it is provisional and dominated by one templated programme |

Decisions made since this packet was first sent are recorded in AQ-029 to AQ-032: Madison counts as 80% of benchmark; the benchmark covers garage conversions and bars replacement parking; the outcome is second homes on single-family lots; and the California comparison study is pre-registered.

## California comparison data (addendum)

Assembling and checking data belongs in Gate 2; the comparison analysis stays in Gate 3 and has not been run. Details: [CA_COMPARISON_DATA.md](CA_COMPARISON_DATA.md); build `uv run python scripts/build_ca_comparison_data.py`.

- **Assembled:** Census BPS for California 2010–2025; HCD APR Table A2 2018–2025 (926,774 rows); the 2012–2019 ADU compilation (identical to the owner's copy); ACS one-unit detached homes for 482 cities and 57 unincorporated county areas (sum 8,354,468); a crosswalk matching every HCD and compilation name to Census codes (519 of the HCD names match a BPS place; 16 small cities never appear in BPS and may be counted in their county's row).
- **HCD lists some permits again in later years** (mainly Los Angeles, when homes are finished). The main measure counts units whose permit date falls in the report year; a deduplicated issue-year version and the as-published totals are kept. 2018 is undercounted under the main measure, so the plan fixes both versions as sensitivities.
- **Non-ADU units, HCD versus BPS:** 0.82–0.99 of BPS by year under the main measure; within ±7% in 2018–2023 under the issue-year measure.
- **Are ADUs inside BPS one-unit counts? Not pinned down statewide** — plausibly between none and about half, and it differs by permit office (Los Angeles, San Diego, San Francisco appear to leave ADUs out; San Jose, Oakland, Long Beach appear to include them). No single value is carried into Gate 3.
- **Same-definition limits (AQ-032):** HCD cannot separate single-family-to-duplex conversions or SB 9 second homes, so the two states are compared on ADU-type second homes; Wisconsin's duplex conversions are a Wisconsin-only component.
- **Held-out 20%:** 108 of 540 jurisdictions (107 with data), seed 20261024; every output is marked, and any number that could feed the model uses non-holdout jurisdictions only.
- **Statewide view:** BPS units per 1,000 homes, 2010–2025, both states, indexed to 2014–2016; built, not interpreted.

An independent check confirmed the joins, holdout draw, privacy, and that no study results were computed; its findings (an unsupported single "share inside BPS" value, the definition gap, stale numbers, and second-homes consistency) are repaired above.

## Recommendation

**Advance to Gate 3** after G2-1 and G2-4 to G2-9. The data supports a baseline and response specification: an observed permissive series (Madison), an observed near-zero restrictive series (Pleasant Prairie, Sun Prairie before 2026), statewide denominators, coded rules for a third of the state's homes, and assembled, reconciled California data for the pre-registered comparison. The main limitations are the small ADU counts, the assumed rules for uncoded places, and the absence of statewide ADU permit records; Gate 3 handles these through ranges and stated assumptions.

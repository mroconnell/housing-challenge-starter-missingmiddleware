# Gate 5 Packet (draft): Statewide ADU MVP and the "good enough" decision

Prepared 2026-10-26 by the interface agent, on the model side prepared the same day ([MODEL_CHECKS.md](MODEL_CHECKS.md), [UI_CONTRACT.md](UI_CONTRACT.md)) and the rubric check ([RUBRIC_AND_COMPLIANCE.md](RUBRIC_AND_COMPLIANCE.md)). **Status: draft for the owner's decision.** No model output changed in this gate: every number below is the adopted run (AQ-043 in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md)) or one of the precomputed variants named next to it.

**Units.** As in Gates 3 and 4:
- **permits** = second-home permits at issuance (ADUs, plus single-family-to-duplex conversions on lots that already have a home), summed over 2027–2031 unless a year is named;
- **rate** = permits in a year ÷ thousands of one-unit detached ("single-family") homes, written "per 1,000 single-family homes per year". Wisconsin has 1,839,569 such homes (ACS 2020–2024 five-year estimate, B25024_002), the denominator of every statewide ADU rate here.
- The one exception is general housing production on the landing screen: homes of all types permitted per 1,000 housing units of all types. It is labelled as such and never mixed with the ADU rates.

## 1. What this gate decides

Whether the statewide ADU estimate is a good enough foundation to build the next benchmark scenarios on ([MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md#gate-5--statewide-adu-mvp-and-the-good-enough-decision)). The plan unlocks "MVP work on additional benchmark scenarios only after the owner accepts the statewide ADU foundation." Two more scenarios are required for a scored submission (baseline + at least 3 of 5; we have 1).

## 2. The answer

Over 2027–2031, with a statewide ADU law in effect on 1 January 2027 (stylized):
- **Under current law (baseline): 605 permits** (604.6), 0.07 per 1,000 single-family homes per year (604.6 ÷ 1,839.569 thousand homes ÷ 5 years).
- **Added by the law: 8,757 permits** in the central scenario, 5,538 in the lower ("sluggish adoption") scenario and 16,889 in the strong adoption scenario. Central = 0.95 per 1,000 single-family homes per year (8,756.6 ÷ 1,839.569 ÷ 5).
- **Total with the law, central: 9,361 permits.**
- **Reference line:** 8,851 added permits if Wisconsin followed the median path of the eight statewide-law states.

The scenarios show how much the eight statewide-law states differ from one another; they are not statistical confidence intervals.

## 3. What was built in this gate (interface side)

| Part | What changed |
| --- | --- |
| Screen 1 "Wisconsin today" | Two labelled blocks: **All housing in Wisconsin** (stock, vacancy, production, mix) and **ADU forecasts** (baseline and addition), with a sentence on their different denominators. Vacancy is labelled "Vacant homes, including seasonal" (10.8% = 299,092 ÷ 2,778,572 housing units, ACS 2020–2024), "not a for-rent or for-sale vacancy rate". New production rate: **9.0 homes permitted per 1,000 housing units in 2025** (25,569 permitted units, Census Building Permits Survey 2025 final ÷ 2,840,960 housing units on 1 July 2025, Census Population Estimates Vintage 2025). ACS figures say "five-year average"; PEP says "no published margin of error". Every BPS row carries its source and source id (`census_bps_state`). No composite score. |
| Screen 3 "Where" | Two new geographies next to counties and municipalities: **Assembly districts (99)** and **Senate districts (33)**, with district numbers drawn by the same self-hosted glyph and label overlay as the county names ("Show district numbers"). Table with a reconciliation line that includes the explicit "Not allocated to a district" row (0.0 permits, always shown). A plain caveat and a one-click "Method" note under the map. District details list the largest places in the district and the share of each place's homes inside it (Senate: its three Assembly districts). County outlines are hidden in district views so the two are not mixed. |
| Screen 4 "How sure" | New section **"What the law's addition rests on"** (observed / calculated / assumed, with a stacked bar and the table one click away), and the **unknown-rules switch** with three precomputed runs, tiles for baseline / addition / total with the change from the adopted run, a table of all three, and by-year and by-type-of-place tables in a disclosure. |
| Switch on "Where" | The same switch appears in compact form on the map screen. It applies to counties and municipalities (their yearly values come from the variant run). In Assembly and Senate views it is **greyed out and set to the adopted assumption**, with the note "Districts are shown for the adopted assumption only … The other two assumptions were not split by district." The choice is kept in the URL (`?u=like_prohibited`). |
| Bundle builder | `scripts/build_ui_bundle.py` now also reads the unknown-rules tables and variant run, the district tables, crosswalk and `gate5_trace.csv`, and **copies the simplified district outlines from `data/processed/districts/` (git-ignored) into the committed bundle**, rounded to 4 decimal places: `geo_assembly.json` 143 KB, `geo_senate.json` 95 KB, `geo_district_labels.json` 18 KB. New files `unknown_rules.json` (805 KB: per-year values only for the uncoded places that change) and `districts.json` (115 KB). Bundle `adu-0efbefc58d`: 14 files, 3.98 MB (was 9 files, 2.80 MB), a hash of 50 input files. Built twice: byte-identical. 15 of 15 validation checks pass (4 new, below). |
| Madison note | The map-panel note now says the Madison choice "will be looked at again in December 2026, when Madison's 2026 permit count is final" (owner decision), instead of "under review (Gate 5)". |
| Docs | README command contract (Gate 5 rebuild order, screen list, bundle size); [DATA_COMPLIANCE.md](../DATA_COMPLIANCE.md#gate-5-sources) rows for the 2024 legislative districts and the 2020 Census blocks; [DISCLOSURES.md](../DISCLOSURES.md) dataset rows extended to Senate districts and 2020 blocks. |

Screenshots of the changed and key screens, desktop (1280 px) and phone (Pixel 7, 412 px), from run `adu-0efbefc58d`: [screenshots/](screenshots/) (22 files).

| Screen | Files |
| --- | --- |
| Wisconsin today | `1-today-desktop.png`, `1-today-mobile.png` |
| Statewide comparison | `2-compare-*.png` |
| Where: counties (default); Assembly districts; Senate district 26 details (Madison); municipalities with uncoded places "like prohibited" | `3-where-counties-*.png`, `3-where-assembly-*.png`, `3-where-senate-detail-*.png`, `3-where-munis-like-prohibited-*.png` |
| How sure: adopted; "like places that already allow ADUs as the bill would" | `4-how-sure-*.png`, `4-how-sure-like-benchmark-*.png` |
| Why, Madison pilot, Brief | `5-why-*.png`, `6-pilot-madison-*.png`, `7-brief-*.png` |

## 4. Owner review: step by step, with my self-assessment

The steps are the Gate 5 owner review from [MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md#gate-5--statewide-adu-mvp-and-the-good-enough-decision), quoted literally. I walked each one in headless Chromium on the production build (desktop 1280 px and Pixel 7) and checked the screenshots by eye.

| Step | What you do (plan text) | Where to look | My result |
| --- | --- | --- | --- |
| 1 | "Open the landing screen and identify Wisconsin's current housing conditions and baseline projection." | Tab 1. Top block "All housing in Wisconsin": 2,840,960 housing units (1 July 2025); 1,839,569 single-family homes (±6,502, five-year average); 10.8% vacant including seasonal; 25,569 new homes permitted in 2025, 9.0 per 1,000 housing units. Second block "ADU forecasts": 605 permits under current law over 2027–2031 (about 121 a year, 0.07 per 1,000 single-family homes per year). | **Pass.** Each figure has its period, source and status pill; general production and ADU forecasts sit in separate, labelled blocks with different denominators stated. Not done: tenure and affordability indicators (owner/renter share, value or rent to income) are not on the screen; the tables are on disk (gap 5 in MODEL_CHECKS §3e). |
| 2 | "Apply the ADU reform and identify the statewide additional permitted units and lower/upper paths." | Tab 2 (unchanged since Gate 4). | **Pass.** 8,757 added permits central; 5,538 lower; 16,889 strong adoption; the chart keeps all three and the reference line (8,851). Playwright checks each year and scenario against the bundle. |
| 3 | "Follow the explanation of why those results differ across broad areas." | Tab 2 "By type of place"; Tab 3 map and details; Tab 4 "What if places with uncoded rules behave differently?" by type of place. | **Pass, with a gap.** Rates by type of place are on screen. The plain reason (home value relative to income drives the with-law rate; the group label itself plays no part) is in [MODEL_CHECKS §3b](MODEL_CHECKS.md#3b-urban-suburban-small-community-and-rural-contexts) but **not yet written on screen**; a legislator would see the differences without the one-sentence "why". |
| 4 | "Inspect how much of the result depends on verified local evidence versus assumptions or incomplete coverage." | Tab 4, first two sections. | **Pass.** "Of the 8,757 permits the law adds … 5.5% (482 permits) … own permit records, 21.1% (1,847) … calculated from places with the same coded rules, and 73.4% (6,427) … rules we have not coded." Then "Every place's rate *with* the law is transferred from other states." The switch shows the three unknown-rules runs; Playwright checks each tile against the bundle, which the Python tests check against the CSVs. |
| 5 | "Reconcile the displayed geographic breakdown to the statewide result." | Tab 3, the line above the table, for each of the four geographies. | **Pass.** Counties (72), municipalities (1,925), Assembly districts (99) and Senate districts (33), each plus the not-allocated row (0.0 permits) for districts, reconcile to the state for every scenario and "through year". In the bundle the largest gap is 0.005 permits for districts and 0.006 permits for the variant runs; the Python tests check every path and year. |
| 6 | "Read the rubric assessment, strongest sensitivity, and remaining limitations." | This packet §6–§8; [RUBRIC_AND_COMPLIANCE.md](RUBRIC_AND_COMPLIANCE.md); Tab 4 sensitivity and challenges. | **Pass.** The largest sensitivities on screen are the two alternative model forms (multiplicative law −8,091 permits; California-only regression −6,367). |
| 7 | "Choose **good enough to extend**, **iterate on named weaknesses**, or **revisit the model approach**." | §9. | **For you to decide.** My recommendation is in §9. |

## 5. Context contrasts and trace

**Four contexts** ([MODEL_CHECKS §3b](MODEL_CHECKS.md#3b-urban-suburban-small-community-and-rural-contexts), central, 2027–2031):

| | Urban | Suburban | Small community | Rural | Wisconsin |
| --- | --- | --- | --- | --- | --- |
| Single-family homes (share of 1,839,569) | 427,619 (23%) | 450,535 (24%) | 251,345 (14%) | 710,070 (39%) | 1,839,569 |
| Added permits | 1,450 | 2,605 | 901 | 3,801 | 8,757 |
| Added per 1,000 single-family homes per year | 0.68 | 1.16 | 0.72 | 1.07 | 0.95 |

Differences come from home values and incomes, not from the labels: a place with a 10% higher median home value than its state's average gets a 29% higher with-law rate; at the same value, 10% higher income means a 25% lower rate. No Wisconsin rural town or small community has an observed permit series: their current-law rate is assumed and their with-law rate is transferred.

**Trace** ([MODEL_CHECKS §3c](MODEL_CHECKS.md#3c-trace-of-the-state-totals-and-ranges), places with single-family homes, central addition over 2027–2031):

| Current-law rate | Places | Single-family homes | Added permits | Share |
| --- | --- | --- | --- | --- |
| Observed in the place's own permits (Milwaukee, Madison, Pleasant Prairie) | 3 | 161,026 | 482.4 | 5.5% |
| Calculated from a coded rules group | 37 | 411,110 | 1,846.8 | 21.1% |
| Assumed (rules not coded, like restricted) | 1,848 | 1,267,433 | 6,427.5 | 73.4% |
| **Wisconsin** | 1,888 | 1,839,569 | 8,756.6 | 100% |

Every with-law rate, in every place, is transferred from other states (the pooled model of 8 statewide-law states and 5 cities; Madison from 9 Washington and Oregon cities). The statewide estimate does not scale up a pilot: simple pilot multipliers would give anything from 1,632 to 6,232 added permits ([§3a](MODEL_CHECKS.md#3a-the-statewide-method-stands-without-a-pilot-multiplier)).

## 6. Sensitivity: unknown rules, groupings, transferred response rates

Central, permits over 2027–2031; changes from the adopted baseline (604.6), addition (8,756.6) and total with the law (9,361.3). From [MODEL_CHECKS §3d](MODEL_CHECKS.md#3d-sensitivity-unknown-rules-groupings-transferred-response-rates).

| Group | Case | Baseline | Addition | Total with the law |
| --- | --- | --- | --- | --- |
| Unknown rules (on screen) | 1,882 places with 1,267,433 homes (69%) behave like places that prohibit ADUs | −186.4 | +158.6 | −27.8 (−0.3%) |
| Unknown rules (on screen) | … like places that already allow ADUs as the bill would | +804.7 | −684.7 | +120.0 (+1.3%) |
| Groupings | Urban / suburban / small / rural redrawn (any definition) | 0 | 0 | 0 |
| Groupings | Prohibited and restricted evidence pooled into one group | −30.9 | +26.3 | −4.6 |
| Groupings | Rural places and small communities at the Madison minimum | 0 | −3,991.3 | −3,991.3 |
| Transferred response | California out of the common level | 0 | −1,100.0 | −1,100.0 |
| Transferred response | No ramp | 0 | +1,511.3 | +1,511.3 |
| Transferred response | Multiplicative law | 0 | −8,090.7 | −8,090.7 |
| Transferred response | California-only regression | 0 | −6,367.0 | −6,367.0 |

**Reading.** What we don't know about local rules moves the split between baseline and addition, not the total with the law: from 2030 the three unknown-rules totals are equal (2,180 and 2,195 permits in 2030 and 2031). What moves the total is the transferred response: how Wisconsin responds compared with the eight states, and the model form.

## 7. Rubric summary

Full assessment: [RUBRIC_AND_COMPLIANCE.md](RUBRIC_AND_COMPLIANCE.md) (written at commit `af3a5e2`). Internal ratings, not predicted judging scores: Transparency 3, Replicability 3, Usability 4, Methodological soundness 4, Policy insight 2; weighted 3.25 of 5.

Since that assessment:
- **Closed** (commit `8e1a1d5`): the CodeQL high alert, Dependabot for uv and npm, CodeQL for TypeScript, UI tests in CI, a Python licence check (`certifi`, MPL-2.0, flagged as a reviewed exception), the committed SPDX SBOM, NOTICE, README numbers, and the AI-use disclosure.
- **This gate** adds to Transparency (the trace on screen, the unknown-rules switch) and Usability (districts for legislators; separate labels and denominators on the landing screen).
- **Still open** and decisive: **two more benchmark scenarios** (without them the submission "will not be scored"); the Model & Assumptions Overview and the Policy Scenario Comparison are still templates; no deck or video yet; no worked path to a state with less complete data.

## 8. Remaining limitations

1. **73% of the addition rests on assumed current-law rates.** 6,427.5 of 8,756.6 central permits are in places whose local rules are not coded. The switch shows this moves the total with the law by −28 to +120 permits (−0.3% to +1.3%), but the split between baseline and addition moves much more (baseline 418 to 1,409).
2. **Every with-law rate is transferred.** No Midwest state has data after a statewide law. Iowa's first full year (2026) will be the first Midwest test.
3. **Districts are shares, not forecasts.** District figures share each municipality's result by where its single-family homes were in 2020 census blocks. Housing built since 2020 and annexations are not in the split. In 56 of the 775 areas with at least 500 homes, the block estimate differs from the ACS count by more than −20% or +25%. Plain land-area weights would move 237 of 8,757 central permits (2.7%) between districts.
4. **Districts exist for the adopted run only**, so the switch is disabled there. Splitting the two other runs by district means rerunning `build_district_allocation.py` on the variant run.
5. **Screen-reader pass not done.** Keyboard access is tested (skip link, tabs, radios including the new switch and geography choice, sortable headers, district details), but nobody has used the tool with VoiceOver or NVDA. That manual pass is for the owner or a later step.
6. **Context "why" not on screen** (step 3 above) and **no tenure or affordability indicator** on the landing screen.
7. **The brief has no district page.** It shows the state and the top ten counties only.
8. **Phone layout of the Where screen is long.** The control block now has four geography options and the switch; the 99-row district table is long on a phone. It works (no horizontal page scroll; Playwright checks it) but is not compact.
9. **Bundle size.** 3.98 MB (was 2.80 MB); `unknown_rules.json` is 805 KB. Fine locally; not tested on a slow connection.
10. **Madison** stays on its observed path and is re-examined in December 2026 (owner decision); **small, high-value villages** keep their high rates, e.g. Chenequa (271 homes, 5.24 per 1,000 single-family homes per year central; owner decision, no cap).

## 9. Decision options and recommendation

| Option | What it means | When it fits |
| --- | --- | --- |
| **Good enough to extend** | Accept the statewide ADU foundation; start the next two benchmark scenarios, reusing the state profile, provenance, uncertainty conventions, map (including districts) and brief. | If 73% assumed current-law rates is acceptable given that it barely moves the total with the law, and the transferred response is accepted as the main stated uncertainty. |
| **Iterate on named weaknesses** | Before new scenarios: code rules for more large uncoded places, add the context "why" on screen, a district page in the brief, the screen-reader pass. | If the split between baseline and addition (which is what the assumed rates move) matters to how a legislator will read the result. |
| **Revisit the model approach** | Rework how Wisconsin's response is transferred (for example a different model form). | If the gap between model forms (the multiplicative form adds 8,091 fewer permits; the California-only form 6,367 fewer) is not acceptable as a sensitivity and needs resolving now. |

**My recommendation: good enough to extend**, with three small iterations folded into the next cycle rather than blocking it:
- the one-sentence context "why" on screen 2 or 4;
- a district table on the brief;
- the manual screen-reader pass before submission.

Reasons:
- The total with the law, the number a legislator acts on, is stable to what we don't know about local rules: −0.3% to +1.3%.
- Every geography reconciles to the state.
- The weaknesses that remain are about the transferred response. More Wisconsin coding cannot fix them before Iowa reports.
- Meanwhile the submission is not scorable without two more scenarios, with about 7 weeks to the 16 December deadline.

**What the owner should weigh:**
- **73.4% of the central addition** (6,427.5 of 8,756.6 permits) sits in places with **assumed** current-law rates.
- The **screen-reader pass is not done**.
- **Two more benchmark scenarios are required** for a scored submission.

## 10. Checks run

| Check | Result |
| --- | --- |
| `uv run --all-extras python scripts/build_ui_bundle.py` | `adu-0efbefc58d`, 14 files, 3.98 MB, 15 of 15 validation checks passed. New: unknown rules adopted variant = adopted run (largest difference 0.0000 permits); each variant's areas and counties reconcile to its statewide and county rows (largest gap 0.0064 permits); Assembly and Senate districts plus the unallocated row reconcile to the state (0.0050 permits); each Senate district = the sum of its three Assembly districts (0.0003 permits). Built twice: byte-identical. |
| `bash scripts/test.sh` | 345 tests OK (was 340); Python licence check: 13 distributions, 12 permissive, 1 flagged exception (`certifi`), 0 failures |
| `bash scripts/test_ui.sh` | 22 bundle tests OK (5 new: switch values = the unknown-rules CSVs, variant areas and counties reconcile, districts reconcile to the state and equal their CSV rows, district geometry is in the bundle, landing-screen indicators and trace shares); npm licences permissive; type check and build OK; Playwright **32 passed, 2 skipped** (keyboard tests are desktop-only). New Playwright tests: the switch shows each precomputed run and carries to the map; districts reconcile and disable the switch (both chambers), then re-enable it for municipalities; keyboard (arrow keys on the switch and the geography radios, Enter on a district's Details); landing-screen labels. Playwright serves on port 4317 and never reuses a server. |
| Screenshots | 22 regenerated into [screenshots/](screenshots/), with no console errors (the screenshot run fails on any) |

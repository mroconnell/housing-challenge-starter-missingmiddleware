# Gate 4 Packet (draft): Working ADU Tool

Prepared 2026-10-25 by the interface agent. **Status: draft for the owner's review.** The tool implements the Gate 1 screen flow ([INTERFACE_WORKFLOW.md](../gate1/INTERFACE_WORKFLOW.md)) on the adopted Gate 3 model ([Gate 3 packet](../gate3/README.md)). The owner's mockups were design references only; nothing was copied from them.

**Units.** As in Gate 3, every number in the tool and here is either:
- a **count of second-home permits**: ADUs plus single-family-to-duplex conversions on lots that already have a home, at issuance, usually summed over 2027–2031 ("permits over 2027–2031"); or
- a **rate**: second-home permits in a year ÷ thousands of one-unit detached homes ("permits per 1,000 single-family homes per year").

Wisconsin has 1,839,569 single-family homes (ACS 2020–2024, B25024_002).

## How to run it

From the repository root (macOS or Linux, Python 3.12+, Node.js 20+):

```
bash scripts/setup.sh        # Python packages (uv) and the tool's npm packages (ui/)
bash scripts/run_tool.sh     # rebuilds the bundle if data/processed exists, builds ui/, serves http://127.0.0.1:4173/
bash scripts/test_ui.sh      # bundle tests, licence check, type check, build, Playwright smoke tests
bash scripts/test.sh         # all Python tests, including the bundle tests
```

`run_tool.sh` works from a fresh clone without the 1.7 GB of raw data: it then uses the committed bundle in `ui/public/runs/`. With the Gate 2–3 builds on disk, it first runs `uv run --all-extras python scripts/build_ui_bundle.py`.

## What was built

| Part | Files | Notes |
| --- | --- | --- |
| Bundle builder | `scripts/build_ui_bundle.py` | Reads the adopted outputs only: `reference/adu_model_*.csv` and `adu_model_params.json`, the per-area engine run (`data/processed/model_run/results_long.parquet`), the baseline, measured-permit, rule, coverage, sensitivity, robustness and comparison tables, the ACS/PEP/BPS state conditions, and TIGER 2024 boundaries. Writes `ui/public/runs/<run_id>/` and `latest.json`. |
| Bundle | `ui/public/runs/<run_id>/` (8 JSON files, 2.68 MB) | `areas.json` 1.28 MB, `geo_munis.json` 1.32 MB (1,925 simplified polygons), `geo_counties.json` 25 KB, the rest under 20 KB each. The run id is a hash of the 33 input files, including the builder; the same inputs give a byte-identical bundle (checked by building twice). |
| Tool | `ui/` (Vite + plain TypeScript, MapLibre GL JS) | Seven screens, hash routing, no live model in the browser: switches select precomputed values. Charts are dependency-free SVG. |
| Tests | `tests/test_ui_bundle.py`, `ui/tests/smoke.spec.ts` | See "Agent checks" below. |
| Scripts | `scripts/setup.sh` (extended), `scripts/run_tool.sh`, `scripts/test_ui.sh` | Listed in the README command contract. |

The screens, all reached from the tab bar:

1. **Wisconsin today:** housing units (PEP 2020–2025), single-family homes, vacancy, homes permitted (BPS 2015–2025), housing mix, and the ADU baseline and central addition.
2. **Statewide comparison:** the law's text, the three scenarios with their info text, baseline / added / total tiles, a 2026–2031 chart with all three scenarios, the lower-to-Strong-adoption band and the adoption reference line, an annual and five-year table, rates per 1,000 homes, and results by type of place.
3. **Where:** county and municipality choropleth (area fills only, no basemap, no points), layers for existing homes, baseline growth and additional growth, a "through year" slider 2027–2031, a per-1,000-homes or count measure, a details panel, and a sortable, searchable table with a reconciliation line against the state total.
4. **How sure:** current-law rate basis (observed / calculated / assumed), local-rule coding, results by current rules, the sensitivity tornado and table, the robustness checks and the three strongest challenges.
5. **Why:** five evidence cards and six assumption cards (each with type, status, a "challenge this" question where useful, and links to the docs), and both spaghetti charts re-drawn from data with their tables.
6. **Pilot examples:** Madison and Pleasant Prairie (pilots) and Sun Prairie (same-market check), each labelled "Pilot example, not a statewide result": current rules with ordinance sections, retrieval dates and check status, observed second homes by year, baseline and additional permits by scenario and year.
7. **Brief:** a printable two-page summary ("Print or save as PDF") with the headline, scenario table, top ten counties plus the rest reconciled to Wisconsin, coverage, the three biggest sensitivity cases, limitations, sources and run id.

On every screen: a status strip (adopted model, run id, last observed year 2025, forecast 2027–2031, stylized effective date, data vintages dialog with the run's validation checks), Observed / Calculated / Assumed pills, and a footer with the outcome definition. A missing value shows "—" with its reason, never 0.

Screenshots of every screen, desktop (1280 px) and mobile (390 px), are in [screenshots/](screenshots/).

## Owner review: step by step, with my self-assessment

The steps are the Gate 4 owner review from [MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md#gate-4--working-adu-pilot).

| Step | What you do | What you should see | My result |
| --- | --- | --- | --- |
| 1 | Follow the supplied setup/run instructions or open the prepared local demo. | `bash scripts/setup.sh`, then `bash scripts/run_tool.sh`; the tool at http://127.0.0.1:4173/ opens on "Wisconsin housing today". | **Pass.** From a clean copy of the tracked and new files (no `data/`, no `node_modules`), `setup.sh` took 2 seconds with warm caches, `run_tool.sh` built and served the tool using the committed bundle, and `test_ui.sh` passed there (9 bundle tests + 1 skipped because it needs `data/processed`; 15 Playwright tests). In the full checkout, `run_tool.sh` also rebuilds the bundle from the processed model run. |
| 2 | Select each pilot and explain its baseline back in your own words. | Tab 6. **Madison:** 53,292 single-family homes; observed rate 0.19 per 1,000 per year (40 second homes in 2022–2025); baseline 50 permits over 2027–2031. **Pleasant Prairie:** prohibits ADUs; 6,332 homes; observed 0.04 per 1,000 per year (3 second homes in 2014–2025); baseline 1 permit. **Sun Prairie:** legalised ADUs in May 2026 (restricted class, still ramping); 8,118 homes; rate 0.06 calculated from its rules group; baseline 2 permits; its records are applications. | **Pass.** Each tile, table and chart matches the bundle (Playwright checks the baseline and all three additions for every pilot). Madison's additions are 134.9 permits in all three scenarios, the Gate 3 hand calculation. |
| 3 | Apply the benchmark reform and inspect annual and five-year additional permits. | Tab 2. Pick a scenario; all three stay on the chart. Central: 1,297, 1,627, 1,685, 2,049 and 2,063 additional permits in 2027–2031, 8,721 in total (lower 4,407, Strong adoption 16,853), on top of the 645 baseline. Pilots: Pleasant Prairie adds 21 / 41 / 79, Sun Prairie 27 / 53 / 103. | **Pass.** Statewide values equal `reference/adu_model_statewide.csv` and `_by_year.csv` (Python test) and the screen (Playwright, every year and scenario). The adoption reference line shows 8,208. Switching scenario updates every tile, table and the map. |
| 4 | Open the map, change the year, and distinguish inventory, baseline growth, and additional growth. | Tab 3. "Show": existing homes (ACS single-family homes, observed), baseline growth (current law), additional from the law (scenario). "Through year" 2027 to 2031 accumulates the years. The reconciliation line shows that all rows add up to the state for the chosen year, scenario and layer. | **Pass.** Counties and municipalities reconcile to the state in every path and year (largest gap 0.02 permits; counties equal `adu_model_by_county.csv` to 0.012 permits). Playwright moves the slider by keyboard to 2029 and checks the total 4,609 (1,297 + 1,627 + 1,685). "Existing homes" is single-family homes, not existing ADUs, which no source counts. |
| 5 | Open the evidence and uncertainty explanations; identify at least one assumption you can challenge. | Tabs 4 and 5. For example: 69% of single-family homes are in places with uncoded rules, treated as restricted; if they behaved like prohibited places, the baseline would be 459 instead of 645. Or: no Midwest state has post-law data. | **Pass.** Six assumption cards, each with its status, evidence type and a link to the write-up. The sensitivity table and tornado match `adu_model_sensitivities.csv`; the robustness table matches `pooled_revision_g3f2.csv` and `eligible_basis_g3f2.csv` (0.113 / 0.132 for the adopted method). |
| 6 | Review agent checks and decide whether the ADU mechanism is ready for statewide expansion or needs another pilot iteration. | This packet, the run's validation list (status strip → "Data vintages"), and the test results below. | **For you to decide.** My recommendation is below. |

## Agent checks

**Clean run.** Bundle built from the adopted outputs; tool built and served by the documented commands; every screen opened in headless Chromium at 1280 × 900 and as a 390-px phone, with no console errors.

**Consistency.**
- **Bundle builder:** 10 validation checks, all passed, recorded in `manifest.json`. They cover municipalities and counties summing to the state for each scenario, the baseline sum, counties equal to the reference CSV, lower ≤ central ≤ upper in every area and year, and homes summing to 1,839,569.
- **Python (`tests/test_ui_bundle.py`, 10 tests):**
  - the bundle equals the reference CSVs (statewide, by year, by county, sensitivities, reference line);
  - the Gate 3 packet numbers 4,407 / 8,721 / 16,853 and 645;
  - reconciliation for every path and year at both levels;
  - ordering of the scenarios;
  - missing ≠ zero: areas with no homes carry a reason, central-only sensitivity cases stay null where the CSV is blank, and pilot years without records are "missing" with a reason;
  - the pilots equal their area rows, and Madison is 134.9 in every scenario;
  - geometry is polygons only, with no parcel, address or owner fields;
  - a staleness check that the run id matches the current inputs (runs when `data/processed` exists).
  
  The full suite (`bash scripts/test.sh`) passes: 308 tests.
- **Playwright (`ui/tests/smoke.spec.ts`, 8 tests × desktop and mobile, 15 passed, 1 skipped by design):**
  - every screen loads without errors and shows the run id;
  - headline numbers equal the bundle on screens 1, 2 and 7;
  - the scenario switch updates the compare and pilot tiles;
  - the map table reconciles after the year slider moves and after switching to municipalities;
  - missing shows "—" with a reason, and there are no map markers;
  - pilot values for all three places;
  - keyboard: skip link, tab bar, arrow keys on the scenario radios, sortable headers (desktop only);
  - no horizontal scrolling on any screen at either width.

**Pilots, layouts and keyboard.**
- All three pilot pages were checked on desktop and mobile.
- Every control is a native link, button, radio, range or search field with a visible focus outline. The map is mouse and touch only; the table beside it is the keyboard equivalent, and its "Details" buttons open the same panel. Every chart has a text summary in its SVG description and a data table.
- Layouts are single-column under 640 px, with 44-px tap targets for the main controls and 16-px body text.

**No lot-level marks.** The map has area fills only: no basemap, no points, no parcels. The details panel and the pilot pages say that a figure is the area's share of the statewide result, not a forecast for any lot.

**Licences.** `npm run licenses` lists the 113 installed npm packages: all are MIT, ISC, BSD-2-Clause, BSD-3-Clause or Apache-2.0. Two choices were made for licence reasons, recorded in [DISCLOSURES.md](../DISCLOSURES.md#dependency-licenses):
- Observable Plot was dropped because it pulls in robust-predicates (Unlicense); the charts are hand-drawn SVG instead.
- Vite 7 is used because Vite 8 needs lightningcss (MPL-2.0).

## Known gaps and limitations

1. **Small areas can show high rates.** Several small, high-value villages get high per-area levels from the pooled model's within-state home-value term. For example, Chenequa village has 271 homes and a central rate of 6.2 permits per 1,000 single-family homes per year, against 1.19 statewide in 2031. They top the municipal map in the per-1,000 measure. The values are the adopted model's, but they look implausible to a local reader. The table shows them with ranges, and the text says they are rough shares.
2. **No place names on the map, and no basemap.** This follows the Gate 1 rule of no basemap at state level. A reader finds a place through the search box and the table, not by recognising streets. Labels would need a glyph server or a self-hosted font file.
3. **No sub-city pilot map.** The Gate 1 screen 6 proposed tract or cell layers inside each pilot. The adopted model allocates only to municipalities, so a finer map would invent precision. Pilots show the municipality's numbers, rules and permit history instead.
4. **Madison's provisional 2026 count is above its forecast path.** Madison's 2026 records (partial year, provisional) show 42 second homes on 33 permits. That is above both its 2027 baseline (10) and its with-law 2027 path (24 = 53,292 homes × 0.452 ÷ 1,000). Madison's own pilot chart shows the gap. The year is not final, but it is a challenge to the Madison baseline that Gate 5 should look at.
5. **No unknown-rules switch.** The Gate 1 proposal had an unknown-rules switch on screen 4 (sample mix / all compliant / all prohibited). Those variants were not precomputed in Gate 3. Only the baseline sensitivity (uncoded like prohibited: 459) is shown.
6. **Some areas are pieces of cities.** Areas are census county subdivisions, so cities that cross county lines appear as pieces, named with their county (for example "Appleton city (Calumet County)"). There are no legislative districts yet; they are planned for a later cycle.
7. **Accessibility is checked by tests and by hand, not by an audit tool.** axe-core is MPL-2.0, so it was not added. The tool has not been tried with a screen reader (VoiceOver or NVDA).
8. **Evidence links point to GitHub `main`.** Links to files added in this gate (this packet) work only after the commit is pushed.
9. **Large JavaScript bundle.** The JavaScript is 1.1 MB (311 KB gzipped), mostly MapLibre. It has not been tested on a slow connection.
10. **The brief is printable HTML.** There is no generated PDF file; the browser's print dialog saves one.
11. **The browser was the cached Playwright one.** Playwright used the cached Chromium build 1243 in `~/Library/Caches/ms-playwright`; `/opt/pw-browsers` does not exist on this machine. `@playwright/test` is pinned to 1.63.0 to match it. `playwright install` was not run.

## Recommendations

1. **Advance the ADU mechanism to statewide implementation (Gate 5), with two items carried forward:**
   - decide whether small, high-value villages need a cap or pooling before municipal results are shown (gap 1);
   - re-examine Madison's baseline when its 2026 count is final (gap 4).
2. **Precompute the unknown-rules variants** and add the switch to screen 4. Of all inputs, these move the most homes (69%) from assumed to stated alternatives.
3. **Add place labels** (a self-hosted glyph set) and, at Gate 5, legislative districts, built as area-weighted shares with their own reconciliation line.
4. **Run a manual screen-reader pass** with VoiceOver and NVDA before submission, and record it in the accessibility notes.

# Gate 4 Independent Verification

Prepared 2026-10-25 by the independent verification agent. It covers commit `4b9a404` (main, also on GitHub) and bundle run `adu-d06515c846`.

**Method.** I worked in a fresh `git clone` of the repository in a scratch directory, with no `data/` and no `node_modules`. I followed only the README command contract. For the value checks I drove the production build, served by `scripts/run_tool.sh`, with Playwright (`@playwright/test` 1.63.0 from `ui/node_modules`) and the cached Chromium in `~/Library/Caches/ms-playwright` (build 1243). The browser ran at 1280 × 900 for desktop and as a Pixel 7 profile (412 px wide) for mobile. Every number on screen was compared with `reference/adu_model_*.csv`, `docs/gate3/README.md` and the bundle in `ui/public/runs/adu-d06515c846/`.

**Units.** As in the packets, a count is "second-home permits", usually summed over 2027–2031. A rate is "permits per 1,000 single-family homes per year", meaning permits in a year ÷ thousands of one-unit detached homes.

## Summary

| Severity | Count | Short list |
| --- | ---: | --- |
| Blocker | 3 | `scripts/test.sh` fails on a clean clone; the Madison pilot reads as "the law cuts Madison's permits"; the README's opening section says no scenarios exist yet |
| Should fix | 12 | Madison's baseline carries an "Observed" pill; water and lakes on the map; southern Wisconsin cut off on the map; scenario labels and info text; "today 0.07"; broken count legend; the brief prints to 3 pages; mixed rate windows on the pilot pages; Milwaukee's rate basis text is wrong; tab bar on mobile; small villages top the map; packet claims |
| Nice to have | 9 | Scenario missing from the URL; "Madison city city"; inconsistent pills; one-permit rounding differences; minor wording |

**Numbers.** 519 automated checks were run in the browser:
- 512 passed;
- 3 failed only because my script read a closed `<details>` element; read again with `textContent`, all 3 match;
- 4 are genuine rounding differences of one permit (finding N4).

Every statewide, scenario, year, county, sensitivity, robustness, pilot and brief figure equals the model outputs. Counties and municipalities reconcile to the state for every scenario and every slider year.

## 1. Clean reproduction

Times are wall-clock times on this Mac. The uv and npm caches were warm, so `setup.sh` would be slower on a new machine.

| Step | Command | Time | Result |
| --- | --- | ---: | --- |
| Clone | `git clone <repo> verify_g4` | about 1 s | OK |
| Setup | `bash scripts/setup.sh` | 2.2 s | OK: `uv sync --all-extras`, then `npm ci` added 44 packages |
| Test | `bash scripts/test.sh` | 36.1 s | **FAILED: 308 tests, 11 errors, 3 skipped** (see B1) |
| Test the tool | `bash scripts/test_ui.sh` | 14.4 s | OK: 10 bundle tests (1 skipped, `test_bundle_is_current`, which needs `data/processed`), licence check "All licences permissive", type check, build, Playwright 15 passed and 1 skipped (the keyboard test is desktop-only by design) |
| Run the tool | `PORT=4199 bash scripts/run_tool.sh` | about 8 s to serve | OK: "data/processed/model_run not found: using the committed bundle", HTTP 200 |

**Knowledge not in the docs:**
- The Playwright browser must already be cached. The README does say how to install it.
- `run_tool.sh` needs port 4173 to be free, or `PORT=` to be set. `PORT` is mentioned in the script but not in the README.
- An outside reviewer cannot check that the committed bundle is current: `test_bundle_is_current` is skipped without the roughly 1.7 GB of builds. The packet says this, but the README does not.

## 2. Findings

### Blockers

**B1. `scripts/test.sh` fails on a clean clone.** Screen: command contract (README) and the Gate 4 packet's "Agent checks".
- **Evidence:** 11 errors, all `FileNotFoundError`:
  - `tests/fixtures/ca_ordinances/hcd_received_small.xlsx`, used by `test_ca_ordinances.TestSources.test_hcd_xlsx`;
  - `tests/fixtures/wi_town_zoning/doa_inventory_sample.xlsx`, used by all 10 `test_wi_town_zoning` tests.

  Both files exist in the owner's working copy but are ignored by `.gitignore:41 *.xlsx`, so they were never committed, and GitHub does not have them either. The packet's "The full suite (`bash scripts/test.sh`) passes: 308 tests" is true only on the builder's machine. Step 1's "clean copy" was a copy of the working tree, not a clone.
- **Fix:** add `!tests/fixtures/**/*.xlsx` to `.gitignore`, commit the two fixtures (check that they are small and contain no personal data), and re-run `test.sh` from a fresh clone. Correct the packet's sentence.

**B2. Madison, the flagship pilot, reads as "the law lowers Madison's permits", and as the place the law helps least.** Screens: 6 (Madison pilot), 3 (Where, details panel and municipal map) and 2 ("How each scenario is built").
- **Evidence, pilot chart:**
  - The 2026 bar shows 42 second homes (on 33 permits; provisional, partial year).
  - The lines then drop to 10 a year (baseline) and 24 (with the law, 2027) in every scenario. The bundle has 2026 = 42 units, `base` = 10.0 a year, and 2027 addition 14.1.
  - A reader sees the law arriving and permits falling. The only explanation is in the packet (known gap 4) and in a sensitivity line on screen 4 ("Madison x = 2026 provisional to date gives 854 permits over 2027–2031 (+209)"). Nothing on the pilot page explains the drop.
- **Evidence, regional ranking:** Madison's with-law rate for 2027–2029 is 0.53 permits per 1,000 single-family homes per year: (30 baseline + 55 additional permits) ÷ 53.292 thousand homes ÷ 3 years. It is 0.53 in all three scenarios. Every Dane County municipality with more than 2,000 homes is higher in the central scenario:

  | Place | Central, 2027–2029 | Range across scenarios |
  | --- | ---: | --- |
  | Stoughton | 0.97 | 0.52–1.84 |
  | Sun Prairie | 1.21 | 0.63–2.29 |
  | Fitchburg | 1.38 | 0.73–2.62 |
  | Waunakee | 1.71 | 0.90–3.25 |
  | Middleton town | 2.29 | 1.20–4.35 |

  These places have an assumed or calculated current-law rate of 0.06 per 1,000 per year, a third of Madison's observed 0.19. A skeptical aide will ask why the state's most mature ADU market, which already allows ADUs much like the bill, is projected to permit at a quarter to a half of the rate of suburbs that have almost no ADU history. The reason is a modelling choice:
  - Madison alone is held to the observed path of Madison-like cities (about half the model in years 1–3);
  - every other place gets the typical-state level.

  That is stated on screen 2 ("Madison follows the observed path…") and in the second "strongest challenge" on screen 4. The Where details panel and the map show no such caveat, and the scenario switch visibly does nothing to Madison.
- **Fix:**
  1. Add a note box on the Madison pilot and in Madison's details panel. It should say:
     - the 2026 count is provisional and already above the forecast path;
     - Madison is the one place held to the Madison-like cities' path, which is why it does not change with the scenario and why it ranks below its suburbs;
     - the place to look is the challenge card and the +209 baseline sensitivity case.
  2. Draw the 2027 with-law point on the chart with that note.
  3. For Gate 5, decide whether the other Dane County suburbs, or at least the urban and suburban places, should also take the Madison-like path, or whether Madison's path should start from its 2026 level. This is the owner's call, but showing the gap without an explanation is the blocker.

**B3. The README's opening section contradicts the tool.** Screen: `README.md`, the first thing a judge reads.
- **Evidence:**
  - The top-of-file template comment block is still there.
  - "What this tool does" says "The project is in planning" and "No policy scenarios are implemented yet".
  - "Team" still has the "[List team members…]" placeholder.
  - The command contract below is current.
- **Fix:**
  - Rewrite "What this tool does" around the working ADU tool: the seven screens, the outcome definition, 645 baseline and 8,721 central additional permits (4,407–16,853).
  - Delete the template comment.
  - Fill in "Team".
  - Mention `PORT=` and the skipped bundle-currency test.

### Should fix

**S1. Madison's baseline shows an "Observed" pill.** Screen: 3 (Where), details panel.
- **Evidence:** "Baseline, 2027–2029: 30 permits [Observed]". The code is `ui/src/screens/where.ts` line 412: `pill(a ? a.x_status : "calculated")`. It colours the forecast by the basis of the current-law rate:
  - Madison and Pleasant Prairie show "Observed";
  - places with coded rules show "Calculated";
  - the 1,882 uncoded places show "Assumed".

  The pilot pages show the same baseline numbers as "Calculated".
- **Fix:** always show "Calculated" on forecast counts, and give the rate basis on its own line. The panel already has the "Current-law rate" row for that.

**S2. Water on the map.** Screen: 3 (Where).
- **Evidence:**
  - **Rate measure:** Lake Michigan and Lake Superior show as hatched "no single-family homes (no value)". Those areas are the 12 "County subdivisions not defined (… County)" areas.
  - **Permits measure and "Existing homes" layer:** the same lakes are filled in the lowest colour class. `value()` returns 0, not `null`, when there are no homes in those modes.
  - **Water inside other polygons:** TIGER/Line county and county-subdivision polygons include water, so Door County, the Door towns, Manitowoc, Sheboygan and other lakeshore counties extend large coloured shapes into Green Bay and Lake Michigan.
  - **Table:** "County subdivisions not defined (Milwaukee County)" shows a map value of "0" in the Permits measure and an "Assumed" rate-basis pill.

  Screenshots were taken in the browser at 1280 px and 412 px.
- **Fix:**
  - Use Census cartographic boundary files (`cb_2024_55_cousub_500k`, `cb_2024_us_county_500k`) or clip to land.
  - Drop the water-only areas from the map, or fill them with a water colour and the legend item "Lake Michigan / Lake Superior (water)".
  - Treat zero-home areas as `null` in every measure.
  - In the table, give them the reason "water area" and no rate-basis pill.

**S3. The map cuts off southern Wisconsin.** Screen: 3 (Where), desktop and mobile.
- **Evidence:** at 1280 × 900 and on the 412-px phone, the southern tier of counties (Kenosha, Racine, Walworth, Rock, Green, Lafayette) is cut off at the bottom of the map frame. The MapLibre attribution pill covers the south-east corner. `fitBounds` runs on load, apparently before the container reaches its final height.
- **Fix:** call `map.resize(); map.fitBounds(...)` from a `ResizeObserver` or after layout, add bottom padding for the attribution, or make the map taller.

**S4. Scenario names and info text.** Screens: 2 (picker and "How each scenario is built"), 7 (brief table) and 4 (lede).
- **Evidence:**
  - **Central:** its info text is "Like a typical statewide-law state." It only repeats the label, both in the picker and in the brief's "What it means" column.
  - **Lower:** it is labelled "Like the slower statewide-law states", but its info text says "Below every statewide-law state's typical level". The label and the explanation contradict each other.
  - **Naming:** three naming systems are mixed:
    - "lower / central / Strong adoption" (screen 4 lede, tables, legends);
    - the radio labels;
    - "Strong adoption" capitalised mid-sentence ("with the lower scenario and Strong adoption in brackets").
  - **Two "typical" numbers:** "Like a typical statewide-law state" gives 8,721, while "the median path statewide-law states actually reached" gives 8,208. Nothing explains why "typical" is higher than what typical states reached.
- **Fix:**
  - Give the central a real sentence, for example "Wisconsin at the middle of the eight states' levels: about 1.0 permit per 1,000 single-family homes per year at a typical place once the law is in force (Washington 1.19, Utah 1.08, Maine 1.00)".
  - Rename the lower scenario so the label matches its text, for example "Slower than any statewide-law state so far".
  - Use one set of names everywhere.
  - Add one line on why the central (8,721) differs from the reference line (8,208).

**S5. "Today" is used for a forecast.** Screens: 7 (brief), 4 (first challenge) and 5 ("Wisconsin today: measured permits" card, pill "Observed").
- **Evidence:**
  - The brief says "today it permits 0.07 second homes per 1,000 of them per year".
  - Screen 4 says "Wisconsin permits 0.07 per 1,000 single-family homes per year today".
  - The 0.07 is the model's 2027–2031 current-law baseline: 645 permits ÷ 1,839.569 thousand homes ÷ 5 years. It is not an observed statewide rate, and the tool itself says there is no statewide ADU series.
- **Fix:** write "under current law the model expects 0.07 … in 2027–2031". Mark that sentence on the evidence card "Calculated".

**S6. The map legend breaks in the Permits measure.** Screen: 3 (municipalities, Permits).
- **Evidence:** the legend reads "under under 1", "under 1 to under 1", "1 to under 2", "2 to under 5", "5 or more". `fmtVal` turns breaks below 1 into "under 1".
- **Fix:** format legend breaks with one decimal below 1, or round the breaks to whole permits.

**S7. The "two-page" brief prints to 3 pages, and its robustness bullet overstates.** Screen: 7 (brief).
- **Evidence:**
  - `page.pdf({format: "Letter"})` with print media gives 3 pages.
  - The bullet reads "the adopted method had the lowest error (0.113…)". It drops the Gate 3 caveats: the 0.113 is the best of five configurations on the same 7 states, so it is optimistic, and A beats B in only 66% of 5,000 resamples, which is within noise.
  - The 69% uncoded-rules point appears twice ("How sure" and "Limitations").
- **Fix:** tighten the print CSS or drop the duplicate bullet so it fits on 2 pages. Add "(within noise: 66% of 5,000 resamples)" to the robustness bullet.

**S8. The pilot pages mix rate windows, and Madison's "Permits today" is stale.** Screen: 6.
- **Evidence:**
  - **Pleasant Prairie:** the tile reads "Permits today 0.04 [Observed] … observed 2014–2025". The text under the chart reads "In 2022–2025: 0 permits over 25.3 thousand home-years = 0.00 per 1,000". That is two different observed rates on one page.
  - **Sun Prairie:** the tile reads 0.06 (Calculated, rules group); the text reads 0.03 (1 application in 2022–2025).
  - **Madison:** the tile reads "Permits today 0.19", from 2022–2025. The 2026 provisional count is already 42 units on 33 permits in a partial year.
- **Fix:**
  - Rename the tile "Current-law rate used by the model" and give its window.
  - Make the chart text use the same window, or label it "Recent window".
  - On Madison, note the 2026 provisional count next to the 0.19.

**S9. Milwaukee's rate basis is described wrongly.** Screen: 3 (details panel); the same text also feeds screen 4's coverage table.
- **Evidence:**
  - Milwaukee city has 101,402 single-family homes, the largest number of any area.
  - Its current-law rate is 0.19 with status "estimated", so the panel shows "Calculated: the average rate of places with the same coded ADU rules".
  - The bundle's `x_basis` says "assumed ramp from Milwaukee's observed pre-reform candidate rate to a Madison-like level". Milwaukee is coded "restricted", whose group average is 0.06, not 0.19.
  - Appleton (0.19) and Wauwatosa (0.19) take the benchmark-group rate; that is closer to the text but still not "same coded rules".
- **Fix:** show `x_basis` in plain words for every non-observed place. Consider whether Milwaukee's ramp is "Assumed" rather than "Calculated".

**S10. Mobile tab bar.** Screen: every screen at 412 px.
- **Evidence:** the 7 tabs are in one horizontally scrolling row with no scroll cue. Only "1 Wisconsin today" and "2 Statewide comparison" are visible. On screens 3–7 the current tab is off screen on load.
- **Fix:** scroll the active tab into view (`scrollIntoView({inline: "center"})`), add an edge fade, or wrap the tabs to two rows.

**S11. Small, high-value villages top the municipal map.** Screen: 3 (municipalities, rate measure).
- **Evidence:** the summary line under the map reads "Highest: Chenequa village (5.24), Lac La Belle village (Jefferson County) (5.20), Lac La Belle village (Waukesha County) (5.01)". These are additional permits per 1,000 single-family homes per year. The statewide figure is 0.95: 8,721 ÷ 1,839.569 thousand homes ÷ 5 years. This is known gap 1, but the screen advertises it in its one-sentence summary.
- **Fix:**
  - Below a minimum size (for example 1,000 homes), show the range and a "small area" flag, and leave those areas out of the "Highest" sentence.
  - Or decide on the cap or pooling now rather than at Gate 5.

**S12. Packet claims to correct.** Screen: `docs/gate4/README.md`.
- **Evidence:**
  - "The full suite … passes: 308 tests" (see B1).
  - Known gap 8 ("links … work only after the commit is pushed") is out of date: `git ls-remote` shows `4b9a404` on GitHub `main`.
- **Fix:** update both.

### Nice to have

**N1. The scenario is not in the URL.** The router reads `?s=` but `setScenario` never writes it. A link copied from screen 2 or 3 always opens the central scenario. Fix: write `?s=` on change.

**N2. Duplicated words.** The details panel reads "Madison city city in Dane County" (name + type). Small counts read "under 1 permits". Fix: show the type only when the name lacks it, and write "under 1 permit".

**N3. Pills that confuse.** Screen 6 rule tables show "[Observed] checked" for ordinance coding; "Checked" alone is clearer. Screen 5's "What statewide ADU laws did elsewhere" card is pilled "Observed", but its state levels are pooled-model estimates, so it should be "Calculated". Its "about half the earlier model" refers to a model the reader never saw; write "about half the central scenario's rate".

**N4. One-permit rounding differences against `adu_model_by_county.csv`.**
- **Iron County:** its baseline shows 2; the reference is 1.498.
- **Trempealeau County:** its central addition shows 41; the reference is 40.499.

The bundle rounds per-year values to 3 decimals before summing. Fix: sum unrounded values, or round per-year values to 6 decimals.

**N5. Redundant range on screen 2.** "By type of place" with Strong adoption selected shows the range as "2,692 (736–2,692)". Fix: when the selected scenario is an end point, label the range "lower–Strong adoption" explicitly, or show the other two values.

**N6. Wording on screen 4.** "California in (A) beats out (B)" is awkward. Fix: "Keeping California in (A) gave the lower error in 66% of 5,000 resamples".

**N7. Focus after "Details".** The Details buttons move focus up to the panel, above the table. A keyboard user then has to tab back through the controls. Fix: add a "Back to table" link in the panel.

**N8. Mobile layout of screen 3.** On the phone, the controls take about 1.5 screens before the map. Fix: collapse "Areas / Show / Measure" into a summary row on narrow screens.

**N9. Bundle currency in a clean clone.** `test_bundle_is_current` is skipped there. Fix: say in the README that the bundle's run id is a hash of the 33 inputs, and that only a full build can confirm it.

## 3. Value check: what was compared, and the result

| Screen | What was checked | Result |
| --- | --- | --- |
| 1 Today | Baseline 645; central +8,721; lower 4,407; Strong adoption 16,853; 1,839,569 homes; PEP 2,840,960; "about 129 a year" | All equal `adu_model_statewide.csv` and the bundle |
| 2 Compare, all 3 scenarios | Tiles; per-year table (5 years × baseline, 3 additions, with-law); context table; radio state | All equal `adu_model_statewide_by_year.csv` and `adu_model_by_context.csv`. Rates: central 0.77, 0.95, 0.99, 1.19, 1.19; lower 0.41 → 0.65; Strong 1.45 → 2.22; reference 0.75 → 1.18, matching Gate 3 |
| 3 Where, 3 scenarios × 2 geographies × 5 slider years | Reconciliation line, table footer, map title year; slider moved by keyboard (Home, then Arrow) | 30 of 30 reconcile to the cumulative `_by_year` values: for example central through 2029, 4,609 additional and 382 baseline. All 72 county rows checked per scenario: every row equals `adu_model_by_county.csv` except the rounding cases in N4. 1,925 municipality rows after "Show all" |
| 3 Details panel: Madison, Pleasant Prairie, Sun Prairie, and 3 random places (seed 20261025: Grantsburg town, Rolling town, Fairchild village); 3 scenarios × through 2029 and 2031 | Homes, baseline, addition, the three scenarios, with-law rate | 36 of 36 equal the bundle. Madison: 0.53 in 2027–2029 and 0.69 in 2027–2031 in every scenario |
| 4 How sure | Sensitivity table (9 rows × lower/central/upper) and robustness table (4 rows × A/B) against `docs/gate3/README.md`; "66% of 5,000 resamples"; 69% | All equal. Central-only cases show "— central only" (missing, not zero) |
| 6 Pilots × 3 scenarios | Homes, current-law rate, baseline, addition (integer and 1-decimal) | All equal. Madison 134.9 in every scenario; Pleasant Prairie 21 / 41 / 79; Sun Prairie 27 / 53 / 103 |
| 7 Brief | Headline 8,721; by-year 1,297, 1,627, 1,685, 2,049, 2,063; reference 8,208; top-10 counties (homes, baseline, central); 69% | All equal. "Other 62 counties" plus the top 10 sum to 1,839,569 homes, 645 baseline and 8,721 additional |

## 4. Review as a skeptical legislative aide and as a judge

**What works.**
- The outcome definition appears on every screen.
- Missing values are "—" with a reason, never 0.
- The map has area fills only.
- The sensitivity and robustness tables carry exactly the Gate 3 numbers.
- The 69% uncoded-rules caveat is prominent.
- Each pilot's rules table cites ordinance sections and retrieval dates.

**What a skeptic will push on.**
1. Madison (B2).
2. Lakes painted as places, and the cut-off south (S2, S3). Both make the map look unfinished.
3. A central scenario whose explanation is its own name (S4).
4. "Today 0.07", which is a forecast (S5).

**Rubric view.**

| Criterion (weight) | Assessment |
| --- | --- |
| Transparency (30) | Strong: run id, data vintages, pills, links to the docs. Weakened by the pill errors (S1, S9, N3) and the circular central label (S4). |
| Replicability (25) | Weakened by B1 (the documented test command fails from a clone) and by B3 (the README says the tool does not exist). |
| Usability (20) | Good: the scenario picker, slider, table and brief. Weakened by S3, S6, S10 and the 3-page brief. |
| Method (15) | Well documented on screen. The Madison asymmetry (B2) and small-village outliers (S11) are the visible weak points. |
| Policy insight (10) | The rural share (44% of central additional permits on 39% of homes) and the coverage tables are useful. The Madison result undercuts the insight for the one place readers know. |

## 5. Keyboard, mobile and lot-level

- **Keyboard: pass.** Tab order on screen 3:
  1. skip link;
  2. brand link;
  3. "Data vintages";
  4. the 7 tabs;
  5. one stop per radio group (Areas, Show, Measure);
  6. year slider;
  7. scenario radios;
  8. map canvas;
  9. zoom buttons;
  10. search box;
  11. sort buttons;
  12. "Details for …" buttons.

  Focus outlines are 3 px solid on every app control. Enter on Details moves focus to the panel. The Data vintages dialog opens on Enter with focus on "Close", closes on Escape, and returns focus to its button. The map itself is mouse- or touch-only, and the table is the keyboard equivalent. See N7 and S10.
- **Mobile (412 px): partly passes.**
  - Passes: no horizontal page scroll on any screen (also asserted by `test_ui.sh`), single-column layout, large tap targets.
  - Problems: the tab bar (S10), the cropped map (S3), and the long control block (N8).
- **Lot level: pass.**
  - Nothing implies a lot-level prediction: there are no points, parcels or basemap.
  - The details panel and pilot pages say the figure "is not a forecast for any lot".
  - The footer says "Results are for areas, never individual lots".
  - The brief says "for areas, never for individual lots".
  - `test_no_lot_level_data` passes.

## 6. Resolution

Repaired 2026-10-25 by the interface agent, on top of commit `0f8cfa1`. New bundle run `adu-b6427cb775`. No model output or modelling decision changed: statewide, scenario, county and pilot figures are the same (645 baseline; 4,407 / 8,721 / 16,853 additional permits over 2027–2031). Test results are in the [Gate 4 packet](README.md#repairs-after-the-independent-verification).

| Item | Resolution | Status |
| --- | --- | --- |
| B1 | `.gitignore` exceptions for `tests/fixtures/ca_ordinances/hcd_received_small.xlsx` (2.3 KB: title rows and 5 jurisdictions from California HCD's 2019 public ordinance list) and `tests/fixtures/wi_town_zoning/doa_inventory_sample.xlsx` (7.6 KB: 18 rows in the shape of the public Wisconsin DOA land-regulation inventory). Both are small samples of public government lists, with no personal data. A fresh clone with the repaired files then passed `setup.sh`, `test.sh` (311 tests, 3 skipped) and `test_ui.sh`. Packet sentence corrected. | Fixed (files must be committed) |
| B2 | Note on the Madison pilot page, in Madison's details panel and under the map: Madison alone follows the Madison-like path (0.45 rising to 1.08 permits per 1,000 single-family homes per year in 2027–2031), its neighbours are on the statewide model, so its with-law rate is below theirs; under review at Gate 5. The pilot page also gives Madison's 2027–2031 with-law rate (0.69) against the other Dane County places over 2,000 homes (1.10 to 2.59, central). The 2026 bar is labelled "provisional, partial year (1 January to 23 October 2026)", the 2027 with-law point is labelled (24), and a note says the drop is not the law cutting permits, that 2026 so far (42) already exceeds the 2027 forecast with the law, and gives the +209 baseline sensitivity. The model is unchanged. | Fixed on screen; treatment is a Gate 5 owner decision |
| B3 | README opening rewritten around the working tool (seven screens, outcome, 645 and 8,721 with 4,407–16,853); template comment deleted; Team filled with "Missing Middleware" and a TODO for the owner to list members; `PORT=` and the skipped `test_bundle_is_current` documented. | Fixed (owner TODO: names) |
| S1 | Baseline and additional counts always carry "Calculated"; the rate basis has its own line with its own pill. | Fixed |
| S2 | Map outlines from Census cartographic boundary files 2024 (1:500,000, shoreline-clipped; `scripts/fetch_map_outlines.sh`). The 12 water-only areas are not drawn; the map background is a water colour with the legend item "lakes and outside Wisconsin"; zero-home areas are null in every measure; the table shows "water area" and no rate-basis pill. | Fixed |
| S3 | The map refits whenever its frame settles at a new size (ResizeObserver); the boundary credit moved under the map, so no control covers Kenosha. Checked at 1280 px and 412 px. | Fixed |
| S4 | One set of names: Lower, Central, Strong adoption (lower case in running text). Each has a short description and a real explanation: central "the common level of the eight statewide-law states, about 1.00 permit … at a typical place (Washington 1.19, Utah 1.08, Maine 1.00, Vermont 0.90)"; lower relabelled "Slower than any statewide-law state so far" (about 0.53; Rhode Island 0.62, Oregon 0.68). A line explains why the central (8,721) sits above the reference line (8,208): California is in the common level (7,621 without it) and the Madison floor. | Fixed |
| S5 | "Today 0.07" rewritten as the model's 2027–2031 current-law expectation (645 ÷ 1,839.569 thousand homes ÷ 5 years) on screens 1, 4 and 7; the evidence card marks that sentence "Calculated, not observed". | Fixed |
| S6 | Legend breaks below 1 permit use one decimal. | Fixed |
| S7 | Brief prints to 2 Letter pages (Playwright `page.pdf`, print media). The duplicate 69% bullet was removed (kept under Limitations); the robustness bullet keeps "within noise" (66% of 5,000 resamples) and says the error is optimistic. | Fixed |
| S8 | Tile renamed "Current-law rate used by the model" with its basis and window. The chart text uses the model's window (Pleasant Prairie 2014–2025: 3 second homes, 0.04) or is labelled "Recent window … not used by the model" (Sun Prairie). Madison's tile notes the 2026 provisional count. | Fixed |
| S9 | Every place's rate basis is shown in plain words from `x_basis` (Milwaukee: an assumed ramp to Madison's rate, not the restricted-group rate). The status text for "estimated" now reads "a rules-group rate or a stated ramp". Relabelling Milwaukee "Assumed" would move 101,402 homes in the coverage table, so it is left to the owner. | Fixed text; status is an owner decision |
| S10 | The current tab is scrolled into view on load (horizontally only), with a right-edge fade as a scroll cue. | Fixed |
| S11 | Areas under 1,000 single-family homes are flagged "small area" in the table and details panel; the "Highest" line lists only larger areas and gives the statewide figure; it says small villages can reach several times the state rate. Values unchanged. | Fixed on screen; cap or pooling is a Gate 5 owner decision |
| S12 | Packet test counts corrected (311 tests; 13 bundle tests; 19 Playwright passes); known gap 8 updated (`4b9a404` is on GitHub). | Fixed |
| N1 | The scenario is written to the URL (`?s=`). | Fixed |
| N2 | Details panel reads "City in Dane County"; "under 1 permit". | Fixed |
| N3 | Rule tables show a "Checked" pill; the "What statewide ADU laws did elsewhere" card is "Calculated"; "about half the earlier model" replaced by the comparison with the central scenario (0.77, 0.95, 0.99). | Fixed |
| N4 | County values are summed from unrounded engine values, and area values keep 4 decimals; a builder check and a test confirm every county's whole-permit figures equal the reference CSV after rounding (Iron baseline 1, Trempealeau central 40). | Fixed |
| N5 | Range columns are labelled "lower to strong adoption". | Fixed |
| N6 | "Keeping California in (A) gave the lower error in 66% of 5,000 resamples". | Fixed |
| N7 | "Back to the table" button in the details panel. | Fixed |
| N8 | Not changed: the controls still come before the map on phones. | Open |
| N9 | README says that `test_bundle_is_current` is skipped in a clone and that the run id is a hash of the 35 inputs. | Fixed |

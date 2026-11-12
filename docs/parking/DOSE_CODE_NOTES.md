# Parking dose-response: code notes (code step; nothing run on real outcomes)

Date: 2026-11-12 (UTC). Plan: `docs/parking/DOSE_PLAN.md`. The blocks "Ryan's choices", "C11 amended" and "Audit fixes" override the text above them.

**No outcome was read.** No effect was computed for any place, and no pipeline ran on real data. The code was checked on made-up data only. The BPS name match for the new places (names only) has also not been run.

## Files

| File | What it does |
| --- | --- |
| `scripts/parking_dose_common.py` | Dose freeze check, dose table roles, the through-origin estimator, placebo-set and bootstrap ranges |
| `scripts/run_parking_dose_effects.py` | Effects for the new places, from inside a working copy: main, D, stand-ins, leads, placebo dates. Also builds the drop-from-pools taxonomy |
| `scripts/run_parking_dose.py` | `--identity`, `--first`, `--all`: the dose fit, the 88 cells and the reading |
| `scripts/run_parking_dose.sh` | Runner: the 4 pipeline copies, then identity → first → all |
| `tests/test_parking_dose.py` | 8 checks on made-up data |

## Run order (enforced in code)

1. The doses are frozen first (audit fix 6).
   - `reference/parking_doses.csv` must hash to the **first** sha256 written in `docs/parking/DOSES_BUILT.md`, on a line that names the file or says "sha256".
   - Both files must be committed and unchanged.
   - Every script refuses to run otherwise, including the effects script, so no effect can exist before the freeze.
2. Four pipeline copies. They are independent, so run them side by side:
   - `bash scripts/run_parking_dose.sh all_homes main`
   - `bash scripts/run_parking_dose.sh units_2_4 main`
   - `bash scripts/run_parking_dose.sh all_homes droppools`
   - `bash scripts/run_parking_dose.sh units_2_4 droppools`
   - Each copy runs the batch pipeline as Test 56 does: salvage, partial, expanded, placebo `--full --save-draws`, method 2 corrected stage 2.
   - Main copies only: then Test 56 extras `--parts event,placebo_dates`, then the dose effects script.
3. `bash scripts/run_parking_dose.sh identity`. **(a)** All 74 places at dose 100 must reproduce today's averages, or the run stops. This check runs again at the start of `first` and `all`.
4. `bash scripts/run_parking_dose.sh first`. **(b)** Reports the gap's MDE and the counts per dose group. Commit `reference/parking_dose_{identity,counts,mde}.csv`.
5. `bash scripts/run_parking_dose.sh all`. **(c)** The 88 cells and the reading. It refuses to start until the three step (b) files are committed unchanged.

Working copies, as in Test 56:
- `data/processed/dose/<outcome>_ref`, where outcome is `all_homes` (`MM_BPS_OUTCOME` unset) or `units_2_4`;
- `data/processed/dose/<outcome>_droppools_ref` for the drop-from-pools run.

`reference/` is never written by the pipeline. Each run appends one line to `reference/parking_dose_inputs_hash.txt`, with the sha256 of the ACS crowding file and of the dose table.

## Identity check (a): every row must pass

For each outcome, with all 74 places at dose 100 (not the table's C4 increments):

| Check | Target | Tolerance |
| --- | --- | --- |
| Main average | today's figure: all homes −1.1526; 2–4 units −0.0674 | 0.0001 |
| Main average | this copy's placebo summary | 0.0001 |
| Main range ends; rebuilt set draws | this copy's placebo summary; `parking_placebo_full_draws.csv` | 0.002 |
| D average | today's figure: all homes −0.9647 (batch); 2–4 units −0.0068 | 0.0001 |
| D range ends (seed 20261104) | this copy's method 2 results | 0.002 |
| Leads −5…−2, both methods (estimate and range) | this copy's Test 56 event study | 0.0001 / 0.002 |
| Placebo dates −2, −4, both methods (estimate and range) | this copy's Test 56 placebo-date summaries | 0.0001 (D 0.0002) / 0.002 |

The tolerances allow for the 4-place rounding of saved figures. The −0.9647 all-homes D figure is not in the brief: it is the batch's "method 2, D", target-state mix.

## Step (b) outputs (reads no effect of a new place)

- `parking_dose_counts.csv`: places per dose group, for each outcome and role. Columns:
  - places with a main effect, places with a D effect;
  - fallback doses, C3 placeholder 50s;
  - for 2–4 units, places with any 2–4 unit permits in the before window. The new places' before-window rate is read, as Test 56's `--first` did.
- `parking_dose_mde.csv`, for each outcome:
  - gap MDE = 2.486 × SD of the gap's placebo-set draws (main);
  - full-only placebo range width (main), and the "low power" flag for main;
  - pooled placebo width (main), and the 74-place width (main).
- New places' effects are blanked as they are read. A test changes them by +50 and checks that the outputs do not move.

## Cell map (88 cells, asserted)

Cells = 2 outcomes (all homes; 2–4 units) × 2 methods (main; D) × the 22 statistics below.

| # | Statistic | Places | Doses | Main range | D range |
| --- | --- | --- | --- | --- | --- |
| 1 | Pooled β | 74 + 25 pooled, dose > 0 | frozen | placebo sets, doses attached | bootstrap |
| 2 | Full-repeal only | pooled, dose = 100 | frozen | placebo sets (full columns) | bootstrap |
| 3 | Low-dose only | pooled, 0 < dose < 100 | frozen | placebo sets (low columns) | bootstrap |
| 4 | Gap (2 − 3) | both groups | frozen | placebo sets, set by set | independent within-group bootstraps, draw by draw (as Test 56's gap) |
| 5 | Intercept (dose 0) | pooled | frozen | placebo-set line fits | bootstrap |
| 6 | Slope with intercept | pooled | frozen | same | bootstrap |
| 7 | Fallback doses dropped | pooled, minus fallback | frozen | placebo | bootstrap |
| 8 | Fallback doses halved | pooled | fallback × 0.5 | placebo | bootstrap |
| 9 | Fallback doses doubled | pooled | fallback × 2, cap 100 | placebo | bootstrap |
| 10 | Dose-0 places alone | Seabrook, Brainerd, and any new place with frozen dose 0 | average (not a slope) | their stand-ins | bootstrap |
| 11 | Brainerd alone | Brainerd | average | its stand-ins | none (1 place) |
| 12 | Zoned-land share doses | pooled | land share × removal where coded | placebo | bootstrap |
| 13 | 2010-block doses | pooled | 2010 homes share × removal for 2015–2019 mapped reforms | placebo | bootstrap |
| 14 | Partial-reform places dropped from pools | pooled, from the droppools copy | frozen | that copy's placebo sets | bootstrap |
| 15–18 | Leads −5, −4, −3, −2 (reference −1) | pooled | frozen | place bootstrap (Test 56 event study) | bootstrap |
| 19–20 | Placebo dates −2, −4 | pooled | frozen | placebo sets at the shifted date | bootstrap |
| 21 | C6 alternative: 6 discretion places at 15 | pooled | 15 for the 6 | placebo | bootstrap |
| 22 | C4 alternative: citywide repeals at 100 | pooled | 100 for citywide repeals | placebo | bootstrap |

The 74-place line (the comparison for condition 2) is not a cell. It is read from the working copy's placebo summary (main) and method 2 results (D).

## Estimator

- β = Σ *w d e* ÷ Σ *w d²*, with *d* = dose ÷ 100.
- **Main:**
  - *w* = homes × after-years. Effects are not winsorised (as in the batch).
  - Range = real β + (p05 − p50, p95 − p50) of the same fit on 20,000 placebo sets.
  - The set draws are rebuilt as `run_parking_placebo.py --full` makes them: seed 20261028, one draw call per real place, in real-place order.
  - The 74's columns come first, so they are identical to today's draws.
  - Each stand-in takes its real place's dose, and its own homes × after-years.
- **D:**
  - *w* = target-state mix weights (`run_parking_method2.mix_weights`, Wisconsin tool cells, base = homes × after-years), recomputed over the places in each fit and in each draw.
  - Effects are winsorised 5/95 over the same places.
  - Range: 2,000 place resamples, seed 20261105.
  - With all *d* = 1 this is exactly `weighted_avg("target-state mix")`.
- **Leads:** main *w* = homes; D base = homes (as Test 56).
- **Placebo dates:** main *w* = homes × shifted after-years; D base = homes × shifted after-years (as Test 52d).

## Reading (`parking_dose_reading.csv`), applied mechanically per outcome

| Rule | Per | Pass when | Label |
| --- | --- | --- | --- |
| Condition 1 | method | the gap's range includes 0 | "passed, low power" if the gap MDE (main placebo) is wider than that method's full-only range; if it fails: "the pooled estimate is not used and the full-repeal-only estimate stands" |
| Condition 2 | method | pooled range is narrower than the 74-place range (same outcome and method) | "near-automatic (audit fix 2)…" always |
| Condition 3 | outcome (both methods) | no lead (−5…−2) or placebo date (−2, −4) of the dose fit excludes 0 under **both** methods | "pre-trend, not read as an effect" when on |
| Condition 4 | method | with fallback doses dropped, the verdict is the same. Verdict = includes 0 / excludes 0 and positive / excludes 0 and negative | — |
| Headline switch | outcome | all four conditions hold under both methods | "may be offered as the headline: Ryan decides…"; otherwise "stays a sensitivity row" |
| Intercept flag | method | intercept range excludes 0 | "the effect may not vanish at dose 0" |
| C5 label | method | (drop-run verdict shown) | "C5: a place can be both treated and a comparison…" |
| C10 label | method | (2010-block verdict shown) | "C10: … partly post-treatment …" |
| Assumed doses | — | count of fallback places and C3 placeholder 50s | "assumed dose" |
| 2–4 dose source | — | count of places whose 2–4 dose is the all-homes dose | — |

## Choices where the plan is silent (for audit)

1. **Pooled set = 74 + 25.**
   - The 25 are the plan's 24 (section 5) plus Central Falls, which C8 keeps.
   - The brief says 24. The code asserts 25, and stops otherwise.
   - Conditional places (Albany, Bangor, Binghamton, North Canton) and unsure places (Charlottesville, Eureka, Shoreline, Portland 2018, Honolulu) are not pooled. Their effects are still computed, if they have a key.
2. **Central Falls** after-years end in 2024 (plan 11.2). `cmp.LAST_YEAR` is set to 2024 for its own calls, including its stand-ins.
3. **Spokane (C9).**
   - C9 ("the first step that touched housing") points to Spokane 2023 (transit area), not the 2024 row in the plan's list of 24.
   - The code takes whichever row the frozen table marks `event_used = yes`, and stops if both or neither are.
   - Pomona works the same way: 2019 is expected.
   - The dose builder currently writes `event_used = yes` on every row, unless an input file says otherwise. **The table must set one Spokane row and one Pomona row to "no", or the fit stops.**
4. **Pools for the new places' own effects** leave out the taxonomy's benchmark places **and the 74**, as the salvage and partial scripts do. `us_effects` left out the taxonomy list only.
5. **BPS key.** Same state, and the BPS name equals the place name once a trailing city/town/borough/village/township is removed. An incorporated place is preferred. If a pooled place is not found or is ambiguous, the run stops.
   - Not yet run (names only). It is the first step of the effects script.
   - `KEY_OVERRIDE` is the escape hatch.
6. **Stand-ins for the new places.**
   - Same rule as `--full`, with the new place's own key added to the exclusions.
   - Stand-in order comes from rng 20261027, restarted for the new places. Order only maps draws to stand-ins.
7. **Dose 0 is never pooled.**
   - This covers Seabrook, Brainerd, any new place frozen at 0, and any of the 74 whose C4 increment is 0.
   - Through the origin they add nothing. Under D they would still take mix weight.
8. **D winsorising** applies to *e*, not *e / d*, over each fit's places. This keeps the identity exact.
9. **D for the gap:** Test 56's gap rule (independent resamples within each group, each restarted at the seed).
10. **Low-dose group** = 0 < dose < 100. It includes any of the 74 whose C4 increment is below 100.
11. **"Low power"** compares the main placebo MDE with each method's own full-only range width. At `--first` only the main width is known.
12. **Fallback** = `dose_source == "fallback"`, which includes the C3 placeholder 50s. "Doubled" is capped at 100, the plan's 0–100 cap.
13. **Zoned-land and 2010-block doses** = that coverage × `removal_share`, used where it was coded (not fallback places). Other places keep the frozen dose.
    - 2010 blocks are used only for 2015–2019 reforms of type transit area, district or commercial-only.
    - A 2–4 dose that differs from the all-homes dose (a use-type reform) is not replaced.
14. **2–4 dose.**
    - The `dose_units_2_4` column is used if the table has one. Otherwise the all-homes dose is used, and the reading counts those places.
    - `build_parking_doses.py` writes no such column today, so Norman's 2–4 dose (section 7) would equal its all-homes dose. **Flag for the dose builder.**
15. **Dose-0 group and Brainerd** are averages (weights as the method), not slopes. The D range for one place is empty.
16. **Drop-from-pools list.** Every dated reform outside the 74 that touches housing:
    - included: before 2015, after 2024, staged and affordable-only rows;
    - left out: non-residential-only rows and statewide rules;
    - method: each is appended to the copy's taxonomy as a benchmark city under its exact BPS name and population;
    - effect: it leaves the main pools, the stand-in lists, and D's main and strict lists;
    - places with no BPS row are skipped. The list is written to `dose_droppools_list.csv`.
17. **Extra cells from plan section 6 that are not in the brief:** the C6 alternative (6 places at 15) and the C4 alternative (citywide repeals at 100).
18. **The identity check is wider than the brief.** It also requires the ranges, leads and placebo dates to reproduce at dose 100. This tests the draw mapping and the bootstraps.
19. **No "too few to read" rule.** The plan sets none for the dose fit; the counts are reported instead.
20. **`--all` requires the step (b) files to be committed.** The plan says "before any effect"; Test 56 did not enforce this.

## Synthetic test results (`uv run --all-extras python -m unittest tests.test_parking_dose -v`)

Made-up working copies:
- effects = β × dose + noise;
- stand-ins are pure noise;
- the batch and Test 56 summary files are rebuilt with the batch scripts' own formulas, so identity is a true reproduction;
- 200 bootstrap draws and 2,000 placebo sets, for speed.

| Check | Result |
| --- | --- |
| Hash mismatch refused; two Spokane events refused (C9); pooled set = 25 new + 74 | pass |
| Identity: 90 rows, every difference 0.0 | pass |
| Identity stops `--first` when a target is off by 0.01 | pass |
| `--all` refused before `--first`; `--first` unchanged when every new effect moves by +50 | pass |
| Planted β = −1.5 recovered: pooled, full-only, low-only, intercept ≈ 0, slope ≈ −1.5, both methods and outcomes; 88 cells | pass |
| Non-proportional data: gap excludes 0, condition 1 fails with "full-repeal-only estimate stands", outcome "stays a sensitivity row" | pass |

Not testable without real data: `run_parking_dose_effects.py`'s calls into the batch code (`cmp.effects`, `case_effect`, the Test 56 event functions) and the BPS name match. They reuse the batch functions unchanged.

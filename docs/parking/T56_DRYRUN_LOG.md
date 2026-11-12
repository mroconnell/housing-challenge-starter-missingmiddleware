# Test 56 dry run on all homes (2026-11-12 UTC)

**What this is:** a check that the Test 56 code chain runs end to end. It used the all-homes outcome, which has already been seen.
- `MM_BPS_OUTCOME` was unset for every step.
- No 2–4 unit, 1-unit or 5+ run was made.
- No effect number is recorded here. Only cell counts, row counts and checks are.

**Where:**
- Working copy: `data/processed/t56/dryrun_allhomes_ref/`
- Logs: `data/processed/t56/dryrun_allhomes_logs/`
- Summary outputs: `data/processed/t56/dryrun_allhomes_summary/*_dryrun_allhomes.csv`
- All three are git-ignored and not committed. `reference/` was not written.

**Code commits:**

| Commit | What |
| --- | --- |
| 2eca259b | Audit fixes 1–4; the dry-run mode (`run_parking_t56.sh all`, `summarise_parking_t56.py --dryrun`) |
| 9d2870d6 | Crash fix found by this dry run (see below) |

**Input hash:** sha256 of `reference/parking_acs_crowding.csv` = `5bdf5fba86fef4b9f2137d97407b23bf0509781574615105a0508c6f04e53484`, at commit 2eca259b.
- It is recorded in `dryrun_allhomes_logs/inputs_hash.txt`.
- The file is **not tracked in git**.

**Steps:**

| Step | Result | Runtime | Output check |
| --- | --- | --- | --- |
| `run_parking_salvage.py` | pass | 9 s | — |
| `run_parking_partial.py` | pass | 10 s | — |
| `run_parking_expanded.py` | pass | 23 s | — |
| `run_parking_placebo.py --full --save-draws` | pass | 21 min 27 s | 74 real places with stand-ins |
| `run_parking_t56_method2.py --corrected --stage 2` | pass | 2 min 58 s | — |
| extras: event study, long set, Poisson | pass | 3 min 33 s | Event study: 16 rows (8 years × 2 methods). Long set: 2 rows. Poisson: 2 rows, 73 of 74 stacks used, 2,000 of 2,000 draws finite |
| extras: placebo dates −2 and −4 | pass | 26 min 47 s | 74 place rows per shift. Shift −2 D label reads "moved 2 years early" (asserted) |
| extras: pool rules (g_outmetro, h1_dated) | pass | 3 min 22 s | Base rerun matches the working copy's D effects: max difference 0.00005 per 1,000 homes a year (check: under 0.001) |
| `summarise_parking_t56.py --first --dryrun` | pass | 1 s | counts: 5 rows. MDE: 24 rows (4 outcome slots × 3 statistics × 2 weightings). Stand-in draw rebuild max difference 0.000025 (rounding in the saved file) |
| `summarise_parking_t56.py --all --dryrun` | **fail, then pass after fix** | 86 s | 74 cells, 4 headline (assert passed). places: 74 rows. rtm: 74 rows. reading: 9 rows |

**How the run was split:**
- The pipeline ran through `bash scripts/run_parking_t56.sh all`.
- The extras ran as three parallel `run_parking_t56_extras.py --parts …` jobs, with the runner's environment. The parts were event, long and Poisson; placebo dates; and pools.
- Pools started after method 2 finished, because its base check reads method 2's output.
- So the runner's own `extras` argument was not used. It calls the same script with all parts.

**Cell groups (74):**

| Group | Cells |
| --- | --- |
| Headline | 4 |
| Outcome × statistic × method × weighting | 32 |
| Reported-only columns | 4 |
| Flag/drop and no-Oregon | 8 |
| Poisson (stacked two-period) | 2 |
| Long set | 2 |
| Event study | 16 |
| Placebo date | 4 |
| Spillover | 1 |
| Date-aware pools | 1 |

**Crash fixed (9d2870d6):**
- In `reading()`, the D headline lookup (D, target-state mix, overall effect, all 74 places) also matched the spillover and date-aware D cells. That failed the one-row assert.
- The lookups now also match on group (headline, or outcome × statistic for the gaps).
- This would have failed the real run too.

**"Too few to read" check:** all-homes has no thin cells (0 of 74), so this path was also tested on its own.
- The test forced the under-25,000 group down to 5 places with permits before. It wrote to scratch only.
- 18 of 18 size-slope cells and 12 of 12 gap cells were labelled "too few to read".
- 0 overall-effect cells were labelled.
- `reading.csv` showed the label beside the slope and gap "counts" rules, and the size-group row read True.

**Notes for the real run:**
- In the dry run, every outcome slot holds all homes. So "places with any 2–4 permits before" here means any permits, and the labels say "all homes (dry run…)".
- pandas warnings ("divide by zero in log") come from method 2's existing data load. The same warnings are in the Test 51 method-2 logs.

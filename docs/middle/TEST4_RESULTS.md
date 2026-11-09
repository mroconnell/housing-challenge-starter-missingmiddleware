# Test 4 results: fake reform years (pre-trend check)

Locked plan: [TEST_PLAN_LOCKED.md](TEST_PLAN_LOCKED.md). Fake windows: before 2012–2014, after 2016–2018, before any of the laws passed. Code: [`scripts/middle_test1_states.py`](../../scripts/middle_test1_states.py) (`fake` mode) for Test 1, and the Test 2 code with these windows. Outputs:
- `reference/middle_test1_summary_fakeyears.csv`
- `reference/middle_test1_bootstrap_fakeyears.csv`
- `reference/middle_test2_oregon_line_fakeyears.csv`

Run 2026-11-09. The Test 3 part runs with Test 3.

**Pass rule:** with fake years, each test should read "we do not know" (no detectable change). If it does not, that test's real result is read as partly a trend already under way.

## Test 1 with fake years (four states, against fake law-state sets)

| Data | Measure | Fake-year reading | Percentile among fake sets | Pass? |
| --- | --- | --- | ---: | --- |
| Reported only (main) | **M2: 2–4 unit homes** | we do not know | 67th | **Pass** |
| Reported only (main) | M1: 1–4 unit homes | we do not know | 75th | Pass |
| Reported only (main) | M3: all homes | we do not know | 81st | Pass |
| Reported only (main) | M4: 5+ unit homes | rise | 95.4th | **Fail** |
| Reported only (main) | one-unit homes | we do not know | 77th | Pass |
| Filled-in (sensitivity) | M2 | rise | 99.4th | **Fail** |
| Filled-in (sensitivity) | M3 | rise | 96.0th | **Fail** |
| Filled-in (sensitivity) | M4 | rise | 95.7th | **Fail** |
| Filled-in (sensitivity) | M1, one-unit | we do not know | 94th, 92nd | Pass |

Oregon + California only, all measures, both data versions: we do not know (pass).

**Reading:**
- **The primary test's measure and data pass.** That is M2 with reported-only data, four states.
- **The filled-in version of M2 fails.** With Census filled-in counts, the four states were already rising against comparison places before any law. Any filled-in M2 result in Test 1 is read as partly a trend.
- **5+ unit homes fail in both versions.** The Test 7 substitution result for 5+ homes is read as partly a trend.
- **Unmatched share (reported only):** Oregon 29% and California 35% of single-family homes had no comparison place at ½–2× their size in the screened West pool.

## Test 2 (Oregon line) with fake years (Census filled-in, main)

| Band | M2 | M1 | M3 |
| --- | --- | --- | --- |
| 9,000–10,999 | −0.85 (−3.29 to +1.30): do not know, **pass** | −5.94 (−10.99 to −1.30): fall, **fail** | −1.14 (−7.66 to +5.14): pass |
| 5,000–14,999 | −0.85 (−1.98 to +0.18): pass | −4.64 (−8.05 to −1.46): fall, **fail** | −6.65 (−15.37 to +0.46): pass |

**Reading:** Test 2's M2 passes. Its M1 fails: covered cities' 1–4 unit building was already falling relative to left-out cities before the law, so Test 2's M1 result is read as partly that trend.

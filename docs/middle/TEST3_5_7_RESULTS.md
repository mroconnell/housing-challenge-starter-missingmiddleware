# Tests 3, 5 and 7 results (supporting), and Test 4 for Test 3

Locked plan: [TEST_PLAN_LOCKED.md](TEST_PLAN_LOCKED.md). Run 2026-11-10.
- **Code:** [`scripts/middle_test3_cities.py`](../../scripts/middle_test3_cities.py), committed before the run.
- **Outputs:** `reference/middle_test3_cities.csv`, `_fakeyears.csv`, `reference/middle_test5_heldout.csv`.
- **Disclosure (locked):** Census counts for these five cities were seen before the measure was chosen. Test 3 is supporting only.

## Test 3: each city against stand-in cities (homes in 2–4 unit buildings, M2)

Change in homes per 1,000 single-family homes per year, before → after. Reading: above the stand-ins' 95th percentile = rise; below the 5th = fall.

| City | Data | City change | Stand-ins (scope) | Stand-in median | Percentile | Reading | Fake years (Test 4) |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| Minneapolis | reported (main) | +0.23 | 19 (nation) | +0.08 | 63 | we do not know | pass (78th) |
| Raleigh | reported (main) | +0.28 | 24 (nation) | +0.05 | 63 | we do not know | pass (60th) |
| Spokane | filled-in (flagged main) | +1.03 | 85 (nation) | 0.00 | 95.3 | **rise** | pass (72nd) |
| Walla Walla | reported (main) | +1.44 | 638 (nation) | 0.00 | 94.5 | we do not know | not testable on reported data (filled-in: pass, 9th) |
| Portland | reported (main) | — | — | — | — | fails the data rule (2024 not fully reported) | — |
| Portland | filled-in (sensitivity) | −0.70 | 21 (nation) | +0.23 | 0 | fall | pass (79th) |

- **Spokane check against Washington's own permits (OFM):** duplex plus 3–4 unit homes rose from about 46 a year (2019–2021) to about 87 a year (2023–2025). That is about +0.6 per 1,000 single-family homes per year, the same direction as Census. OFM counts townhouses as multi-unit.
- **Rule deviations:** Minneapolis has 19 stand-ins and Portland's sensitivity has 21; the rule asks for at least 20, and the screened national pool is what remains. Portland's middle housing is mostly townhouses (Test 6, measurement check), which Census M2 does not see.
- **M1 and M3:**
  - Raleigh reads a rise in M1 (100th percentile) and M3 (96th). Its fake-year check failed for both, with a fall before any reform, so these are read as partly a trend.
  - Minneapolis M3 reads a fall in the filled-in sensitivity only.
  - All else reads "we do not know".

## Test 5: hide each case in turn

Each case is predicted by the mean of the others, and the miss recorded.

| Cases | Measure | Root-mean-square miss | Misses |
| --- | --- | --- | --- |
| 4 states | M2, log ratio | 0.25 (about ±28%) | Oregon +0.34, California −0.36, Maine −0.05, Vermont +0.08 |
| 4 states | M2, per 1,000 per year | 0.27 | Oregon +0.45, California −0.24, Maine −0.13, Vermont −0.08 |
| 5 cities | M2, per 1,000 per year | 1.02 | Portland −1.64, Walla Walla +1.32, Spokane +0.81, Minneapolis −0.29, Raleigh −0.20 |

**Reading:** for a state the method has not seen, the 2–4 unit estimate is off by about ±0.27 per 1,000 single-family homes per year, roughly the same as Test 1's own range. A single city is off by about ±1.0. The range rests on 4 and 5 cases.

## Test 7: did other building fall? (substitution)

| Test | 5+ unit homes (M4) | One-unit homes | All homes (M3) |
| --- | --- | --- | --- |
| Test 1, four states (reported) | we do not know (61st) | we do not know (81st) | we do not know (80th) |
| Test 3 cities (main) | see CSV; Raleigh and Spokane rises are partly trend | Raleigh rise (fake-year fail) | Raleigh rise (fake-year fail) |

The 5+ unit check failed Test 4 in Test 1, so it is read as partly a trend. No test shows a clear fall in other building.

## Overall (all locked tests run)

- **Primary (Test 1):** we do not know. 2–4 unit homes +33% (−21% to +92%).
- **Supporting:**
  - The Oregon line: we do not know.
  - Cities: one rise (Spokane, on flagged filled-in data); Portland falls on filled-in data only; the rest we do not know.
  - Held-out miss for a new state: about ±0.27 per 1,000 per year.
- **Fake-year checks** pass for every main 2–4 unit result.

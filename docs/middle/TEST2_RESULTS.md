# Test 2 results: Oregon cities just above and below the 10,000 line

Locked plan: [TEST_PLAN_LOCKED.md](TEST_PLAN_LOCKED.md) (commit 8767525c). Code: [`scripts/middle_test2_oregon_line.py`](../../scripts/middle_test2_oregon_line.py), committed before any run (d8faeb36).

## Step 0: zoning check (documents only, before any run)

Source: [measurement/OREGON_LEFTOUT_ZONING.md](measurement/OREGON_LEFTOUT_ZONING.md).

- **Dropped under the locked rule** (already allowed duplexes on most single-family lots before 2021):
  - Molalla (permitted in R-1 since at least 2019);
  - Warrenton (R-10 permits duplexes);
  - Creswell (interior lots permitted from 2020, Ord 538).
- **Unclear, kept in the main run** (the rule drops only confirmed cases): Florence, North Bend, Madras.

## Sensitivities declared after lock, before any run (post hoc)

The zoning check found something the locked plan did not foresee: several left-out cities allowed duplexes during the after window (2022–2024), before the 2025-06-30 deadline. Two sensitivities are declared here, before Test 2 is run, and are labelled post hoc:

| Sensitivity | Also drops | Why |
| --- | --- | --- |
| S1 | Florence, North Bend, Madras | Duplex status before 2021 unclear |
| S2 | Hood River (2021-04), Talent (2021-04), Lincoln City (2022), Madras (2022-06), Sweet Home (2022-09), Astoria (2022-11), Monmouth (2023-05) | Allowed duplexes in single-family zones during or just before the after window, so they are not "left out" in 2022–2024 |

Also noted:
- **Lincoln City:** its 2022 staff report cites a PSU population of 10,067 and treats the city as covered. Under the 2020 certified estimate used by the plan (8,865), it is left out. S2 drops it.
- **Molalla:** it acted as if HB 2001 applied in 2021, and it is dropped anyway.

## Results

(Filled in by the run below.)

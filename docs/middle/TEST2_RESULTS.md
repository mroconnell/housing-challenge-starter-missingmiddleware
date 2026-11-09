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

Run 2026-11-09. Unit: change in homes permitted per 1,000 single-family homes per year, 2016–2018 → 2022–2024. Each result is covered cities' mean change minus left-out cities' mean change, with a 90% bootstrap range over cities. The detection bar comes from the power check: the smallest change caught 4 times in 5. Outputs: `reference/middle_test2_oregon_line_main.csv`, `_s1.csv`, `_s2.csv`.

**Headline (locked main run, Census filled-in columns):** in the main band, Test 2 cannot tell whether the duplex rule changed permits in 2–4 unit buildings. The estimate is +1.10 per 1,000 single-family homes per year, and the 90% range of −1.43 to +4.16 includes 0. **This is not "no effect".** The range still allows effects from a fall of 1.4 to a rise of 4.2 per 1,000 per year.

### Main run (locked)

| Band | Covered | Left out | M2: 2–4 unit homes | M1: 1–4 unit homes | M3: all homes |
| --- | ---: | ---: | --- | --- | --- |
| 9,000–10,999 (main) | 4 | 6 | **+1.10 (−1.43 to +4.16)**: we do not know | +2.71 (−2.19 to +8.13): we do not know | +8.83 (−0.78 to +16.99): we do not know |
| 5,000–14,999 (wider) | 8 | 17 | +0.62 (−0.62 to +1.98): we do not know | −2.06 (−8.43 to +3.61): we do not know | +2.87 (−6.81 to +13.33): we do not know |
| Detection bar (main band) | | | 1.79 | 8.38 | 21.65 |

- **Main band, covered:** Baker City, Cottage Grove, Newport, Silverton.
- **Main band, left out:** Astoria, Eagle Point, Independence, Monmouth, North Bend, Sweet Home.
- **Each group's own change in M2, main band:**
  - covered cities: +0.36;
  - left-out cities: −0.74.

### Sensitivities

| Run | Band | M2 | M1 | M3 |
| --- | --- | --- | --- | --- |
| Reported-only columns (locked sensitivity) | main | −1.23 (−2.09 to −0.37): fall | −4.93 (−6.10 to −3.84): fall | −1.26 (−11.99 to +9.48): do not know |
| Reported-only columns (locked sensitivity) | wider | −0.23 (−1.36 to +0.96): do not know | −7.48 (−15.11 to −1.31): fall | −1.49 (−15.52 to +13.64): do not know |
| S1, unclear cities dropped (post hoc) | main | +1.40 (−1.47 to +4.85): do not know | +3.39 (−1.88 to +9.27): do not know | +9.86 (+0.18 to +18.53): rise |
| S1 | wider | +0.68 (−0.63 to +2.16): do not know | −2.52 (−9.52 to +3.73): do not know | +3.29 (−7.42 to +14.85): do not know |
| S2, early adopters dropped (post hoc) | main | −0.13 (−1.50 to +1.33): do not know | +5.47 (−1.29 to +13.21): do not know | +13.61 (+3.15 to +23.94): rise |
| S2 | wider | +0.32 (−0.63 to +1.32): do not know | −3.65 (−12.45 to +4.08): do not know | +4.13 (−9.54 to +18.98): do not know |

**How to read the sensitivities:**
- **Reported-only, main band:** only 2 covered and 3 left-out cities qualify. A bootstrap over 2 or 3 cities gives ranges that look narrow but cannot be trusted. Its "fall" readings rest on 5 cities and do not hold in the wider band for M2.
- **S1 and S2 show "rise" for all homes (M3) in the main band.** These are post hoc runs on 7 to 9 cities. M3 is not the lead measure, and the locked main run reads "do not know".
- No sensitivity reverses the locked headline for M2.

### Open backdoors and limits (beside the headline)

- Housing production strategies (ORS 197A.100) use the same 10,000 line.
- Seven left-out cities allowed duplexes during or just before the after window (S2).
- Molalla has no usable Census permit rows.
- Few cities: 4 covered against 6 left out in the main band.

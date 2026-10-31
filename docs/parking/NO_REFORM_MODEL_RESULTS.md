# Parking: homes permitted with no parking reform, results (rounds 1–3)

Written 2026-10-31 by the parking conductor. Plan: [NO_REFORM_MODEL_PLAN.md](NO_REFORM_MODEL_PLAN.md). Script: `scripts/run_parking_no_reform.py --round N`. Outputs: `reference/parking_no_reform_{scores,rows,wisconsin,choices,checks}_rN.csv`.

## Answer

- **Main rule:** keep "same pace as before", the flat 3-year average for each place, as the parking baseline. Per place, no model beat it on held-out places in later years. It is also the rule TOD and ADU use.
- **Its past bias:** on held-out places it predicted 0.83 times what was actually permitted, and 0.78 times in Wisconsin's 2021–2025 back-test. The test years include the 2020–2022 boom.
- **Sensitivity for Ryan:** boosted trees predict state totals about twice as well (0.10 against 0.21 on the summary score). For Wisconsin 2027–2031 they give about 110,500 homes, against 118,822 for the flat rule. Both figures use the baseline's "Census as published" sensitivity; scaled to the shared central of 122,619, the trees give about 114,041.

## Data

- **Training rows:** 83,220 place-origin rows in 9,109 places with at least 1,000 homes. They are never-reformed places, and reformed places only in years before their reform (V7 coding plus state laws).
- **Dropped because not every state has it:**
  - Milwaukee's property-file apartment fix (it adds about 3,800 homes to the shared baseline);
  - city permit files;
  - lot and parcel data.
- **Fixed in round 3:**
  - New York City's five boroughs had each been given all 3.7 million of the city's homes. Each now has its own county's homes.
  - Pieces of one town split across counties are summed into one place.
- **Dropped and named in round 3:** rows with no geography of their own. These are Alaska's three balance-of-state parts, six Ohio county "Part" and "Unincorporated" rows, and Cabot village, VT.

## Scores, round 3

The summary score is the median over places of |log((predicted + 0.5) ÷ (actual + 0.5))|. The unit is homes permitted per place per year, averaged over years 2–6 after the origin. Lower is better: 0.52 means the typical place is off by a factor of about 1.69. Each cell is the average over 5 seeds, with the lowest and highest seed in brackets. The total ratio is predicted ÷ actual, summed over places.

| Model | Held-out places, later years | Total ratio | State totals, later years | Wisconsin, later years |
| --- | --- | ---: | --- | --- |
| M0 same pace (flat 3-year) | 0.522 (0.514–0.533) | 0.83 | 0.214 (0.189–0.233) | 0.481 |
| M1 same pace × state trend | 0.527 (0.522–0.535) | 0.87 | 0.192 (0.166–0.204) | 0.491 |
| M2 shrunk 3-year | 0.522 (0.516–0.532) | 0.75 | 0.293 (0.274–0.304) | 0.505 |
| M3a regression | 0.627 (0.603–0.647) | 1.09 | 0.129 (0.119–0.133) | 0.528 |
| M3b regression + ACS traits | 0.585 (0.554–0.610) | 1.07 | 0.122 (0.115–0.127) | 0.460 |
| M4 boosted trees | 0.569 (0.549–0.591) | 1.00 | 0.100 (0.091–0.106) | 0.491 |

- **Later years** are origins 2018–2019, with outcomes 2020–2025.
- **State totals:** for each state, the sum over its places.
- **Wisconsin** is held out whole; the scores shown are over its 317 places.

## Fake-reform placebo

10% of training places were given a fake reform year. The table shows the prediction with the fake reform switched on, minus with it off, in homes per place per year: the average across 5 seeds, with the lowest and highest seed in brackets.

| Model | On minus off |
| --- | --- |
| M3a | 1.4 (−23 to 46) |
| M3b | 0.4 (−31 to 38) |
| M4 boosted trees | 1.8 (−8 to 18) |

On average the fake reform does nothing. The regressions swing widely from seed to seed, so they are not used.

## Wisconsin, 2027–2031 (homes permitted, no reform)

The 331 Wisconsin places with at least 1,000 homes and every year present hold about 70% of the state's permits. So each model is shown as its ratio to M0, times the shared baseline with Census as published (118,822).

| Model | Back-test: predicted ÷ actual, 2021–2025 | 2027–2031, scaled to the as-published sensitivity (118,822) | 2027–2031, scaled to the shared central (122,619) |
| --- | ---: | ---: | ---: |
| M0 same pace | 0.78 | 118,822 | 122,619 |
| M1 same pace × state trend | 0.78 | 119,428 | 123,244 |
| M2 shrunk | 0.70 | 99,123 | 102,291 |
| M4 boosted trees | 0.81 | 110,510 | 114,041 |

**Which baseline:** the shared baseline's central is 122,619 (v2, with Milwaukee's apartments from the city property file). 118,822 is its "Census as published" sensitivity. This model uses only Census permits, which every state has, so it matches 118,822 like for like. The last column applies the same ratios to the central.

All the models under-predicted Wisconsin's 2021–2025, the flat rule by 22%. The trees' lower forecast for 2027–2031 means they expect some of the recent pace to fade.

## Round by round

| Round | Change | Effect |
| --- | --- | --- |
| 1 | First run | Regressions unstable (fake-reform on−off from −62 to +50); NYC boroughs had city-wide homes |
| 2 | Shared-geography keys dropped; log rates and clipped trend in regressions; flag columns fixed | Regressions' state-total score went from 0.33 to 0.12; place scores unchanged |
| 3 | Shared geographies fixed instead of dropped; land-mismatch flag | Scores within seed spread of round 2 |

## Flags (round 3)

- **916 place-origin rows** (233 places) have a 3-year rate outside the national 1st–99th percentile. The 10 largest are fast-growing suburbs, such as Frisco, McKinney and Georgetown (TX), Buckeye and Queen Creek (AZ), and Apex (NC). These are real booms, not land mismatches.
- **Consolidated city-counties** look consistent: Nashville-Davidson 30.7, Lexington-Fayette 9.8 and Jacksonville 12.0 homes permitted per 1,000 homes per year. The name search also caught same-name small places, which are harmless.
- **Worst miss:** Nashville-Davidson, origin 2018. M2 predicted 6,573 homes a year; 12,408 were permitted. It is a real boom, not a data error.
- **Estimated months:** 43,117 of 83,220 training rows have at least one year partly estimated by the Census Bureau.
- **Homes floored:** 280 rows had homes floored at half of the ACS count.

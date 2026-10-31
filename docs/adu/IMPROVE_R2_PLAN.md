# ADU improvement loop, round 2: plan written before running

Written 2026-10-31 by the ADU conductor. It follows [round 1](IMPROVE_R1_RESULTS.md), whose worst-predicted state after the Vermont fix was Oregon (+0.24, about 24% too high). Same test, score and models as round 1 ([IMPROVE_R1_PLAN.md](IMPROVE_R1_PLAN.md)). No result for the variants below had been computed when this file was committed.

## Problem found by tracing Oregon

- **Oregon's law years start before its rules reached the benchmark.** SB 1051 made cities allow ADUs from 2018-07-01. But cities could still require the owner to live on site and an extra parking space until HB 2001's ADU rules applied from 2020-01-01 ([STATEWIDE_STATES.md](../gate3/STATEWIDE_STATES.md), Oregon row). The benchmark law bars both.
- **The model currently counts 2019 as Oregon's first law year.** So year 1 holds a year under the weaker rules.
- **The same rule already applies to Washington** (AQ-061): its law years count from when cities had to comply, not from enactment. Coding Oregon the same way makes the two consistent.

## Variants

| Variant | Change |
| --- | --- |
| V0 | Current data (as round 1). |
| V1 | Vermont by permit year (round 1; awaiting the owner). |
| V5 Oregon from benchmark rules | Oregon's 32-city panel: 2019 is dropped as a transition year; 2020–2022 are law years 1–3. Portland: 2019 counts as local rules only; 2020–2025 are law years 1–6. |
| V6 | V1 + V5. |

## Reported and used

As round 1: held-out log error by state and RMS for the plain average, the median and the adopted model; Wisconsin's lower, central, upper and reference line; flags; the worst miss traced. V5 is a coding correction, judged on whether it matches the benchmark rule, not on the score. Ryan decides any change to the tool's numbers.

## Changes after writing

- **2026-10-31, audit request after the results:** added V6p, V6 with Portland's 2019 dropped instead of coded as local rules only. It moved the central by 721 permits, so it is reported and recommended over V6 (results section 1b).
- **2026-10-31, audit request:** added V6s, V6p with Seattle 2024 coded as local rules only, under the uniform rule that a law year starts only where the state law changed that place's rules. Adopted only after a rules check (Seattle's HB 1337 report; results section 1c).

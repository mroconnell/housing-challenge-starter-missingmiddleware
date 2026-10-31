# ADU improvement loop, round 2: results

Run 2026-10-31 under [IMPROVE_R2_PLAN.md](IMPROVE_R2_PLAN.md), committed before any result was computed. Code: `scripts/run_adu_improve.py --round 2`. Outputs: `reference/adu_improve_r2_scores.csv`, `adu_improve_r2_by_state.csv`, `adu_improve_r2_flags.csv`. Units as in [round 1](IMPROVE_R1_RESULTS.md): rates are ADU permits per 1,000 single-family homes per year; log error = log(predicted ÷ observed); RMS over the 7 held-out states, lower is better; additional permits are Wisconsin, 2027–2031.

## Answer

- **Coding Oregon from its benchmark rules (V5) fixes Oregon's miss:** +0.20 → +0.06. RMS 0.168 → 0.141.
- **With the Vermont fix too (V6), the RMS falls to 0.110,** the best of any version so far. No state misses by more than 0.13 (about 13%).
- **V6 lowers the Wisconsin numbers:** lower 6,804 → 6,100, central 10,679 → 10,000, upper 19,535 → 18,448 additional permits. Oregon's early years now count as weaker rules, so the typical level and the slow-state lower both fall.
- **The adopted model still beats the simple ones on every version** (plain average 0.30–0.32, same-year average without California 0.34–0.35, median 0.21–0.23).
- **But most of that drop comes from one Portland row, not from Oregon's panel (section 1b).** If Portland's 2019 is dropped as a transition year, as the panel's 2019 is, the central is 10,721 and the RMS 0.111.
- **One rule now covers every city:** a law year starts only where the state law changed that place's rules. Portland (2019) and Seattle (2024) already met the benchmark before their state laws, so those years count as local rules only (V6s; sections 1b and 1c).
- **Ryan decides.** Recommended: adopt V6s with the reference-line fix below: lower 6,464, central 10,591, upper 19,536 additional permits; held-out RMS 0.130.

## 0. How the recommendation moved today, step by step

The recommended central changed three times on 2026-10-31. Each step adds one coding correction. The rule behind each was set before its result was read, except where marked.

| Step | What changed | Rule behind it | Lower | Central | Upper | Held-out RMS |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| V0 | Nothing (the tool today) | n/a | 6,804 | 10,679 | 19,535 | 0.168 |
| V1 | Vermont counted by permit year, not year built | Every state's outcome is permits at issuance; ADUs finish about one year after the permit (Austin, median 0.97 years). Planned in round 1 | 6,790 | 10,834 | 19,519 | 0.135 |
| V6 | + Oregon law years from 2020 (panel 2019 dropped; Portland 2019 as local rules only) | Law years start when the benchmark rules bind, as for Washington (AQ-061). Planned in round 2 | 6,100 | 10,000 | 18,448 | 0.110 |
| V6p | + Portland 2019 dropped, not local rules only | Portland met the benchmark before 2019, so its 2019-to-2020 switch marks no real change; both Oregon series treat 2019 alike. Added at the audit's request after V6 was seen | 6,718 | 10,721 | 19,415 | 0.111 |
| **V6s** | + Seattle 2024 as local rules only | One rule for every city: a law year starts only where the state law changed that place's rules. Seattle met HB 1337 before 2024 (city report). Added at the audit's request after V6p was seen; adopted only after the rules check | **6,464** | **10,591** | **19,536** | **0.130** |

Why it moved so much: the law's estimated effect leans on the few cities with years both before and after a state law. V6 created a new before-and-after pair in Portland that did not reflect a real rule change, and that pulled the central down by about 7%. V6p and V6s remove such pairs by one rule. The held-out score was not used to pick any step; V6s scores worse than V6p and is still recommended because the rule decides.

## 1. Held-out test

| Variant | Plain average | Same-year average, no California | Median | Adopted model | Worst state (adopted) | Lower | Central | Upper |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| V0 current data | 0.319 | 0.338 | 0.230 | 0.168 | Vermont +0.33 | 6,804 | 10,679 | 19,535 |
| V1 Vermont by permit year | 0.309 | 0.343 | 0.216 | 0.135 | Oregon +0.24 | 6,790 | 10,834 | 19,519 |
| V5 Oregon from benchmark rules | 0.312 | 0.341 | 0.223 | 0.141 | Vermont +0.26 | 6,180 | 9,945 | 18,464 |
| V6 = V1 + V5 | 0.302 | 0.346 | 0.209 | 0.110 | Utah −0.13 | 6,100 | 10,000 | 18,448 |
| V6p = V6, Portland 2019 dropped | 0.302 | 0.346 | 0.209 | 0.111 | Vermont +0.19 | 6,718 | 10,721 | 19,415 |
| **V6s = V6p, Seattle 2024 local rules only** | 0.302 | 0.346 | 0.209 | **0.130** | Washington +0.20 | **6,464** | **10,591** | **19,536** |

Adopted model's log error by state:

| State | V0 | V6 | V6p |
| --- | ---: | ---: | ---: |
| Washington | +0.07 | +0.12 | +0.11 |
| Oregon | +0.20 | +0.11 | +0.11 |
| Rhode Island | −0.12 | −0.09 | −0.07 |
| Massachusetts | +0.02 | +0.05 | +0.06 |
| Maine | −0.15 | −0.13 | −0.11 |
| Utah | −0.07 | −0.13 | −0.04 |
| Vermont | +0.33 | +0.13 | +0.19 |

**Washington got worse** (+0.07 → +0.11). Its data did not change; the other states' corrections moved the level it is predicted from.

## 1b. Check asked by the audit: Portland 2019

V5 codes Portland's 2019 as "local rules only" (law 0), since the statewide benchmark rules began in 2020. The panel's 2019 is dropped as a transition year instead. The audit asked whether dropping Portland's 2019 too matters. It does: the central moves by 721 permits (10,000 → 10,721), far more than the 100-permit bar.

Why: Portland already had strong local ADU rules. Its 2019 and 2020 rates are about the same. As a law-0 row, Portland 2019 becomes a new before-and-after comparison that says the statewide law adds almost nothing to a permissive city. That lowers the law's estimated effect everywhere, including Wisconsin. Dropping it treats both Oregon series alike and adds no comparison the plan did not intend. The held-out score is the same (0.111 vs 0.110).

So the Oregon panel recode on its own barely moves the central; the drop in V6 came from Portland's row. **One city-year moved the central by about 7%.** That shows how much the law's estimated effect leans on the few cities with years both before and after a state law.

The audit's reading: Portland's own rules met the benchmark before 2019, and HB 2001 did not change them in 2020. So a switch from "no law" to "law" there marks a change that did not happen. It is a coding artifact, not evidence. The uniform rule follows: **a law year starts only where the state law changed that place's rules.**

## 1c. The same rule applied to Seattle

Seattle was coded as local rules only for 2020–2023 and as law plus local rules for 2024, its second year after Washington's HB 1337. Seattle's own ADU ordinance of 2019 already allowed two ADUs per lot, with no owner-on-site rule and no parking. The city's report on HB 1337 says Seattle is "largely compliant with the state requirements now". The changes it needed (two detached ADUs on one lot, height, lot coverage, condo ownership) were proposed in late 2024, so they bind from 2025 at the earliest. So Seattle 2024 is also local rules only under the uniform rule (V6s).

- **Effect:** the central moves 10,721 → 10,591 (−130); the lower 6,718 → 6,464; the upper 19,415 → 19,536.
- **Held-out RMS rises** 0.111 → 0.130, because Washington is now predicted 20% too high. The plan judges coding corrections on the rules, not the score, so V6s is recommended.
- **No law × local-rules interaction is added.** Only Portland and Seattle would identify it. It can be planned in a later round if Ryan wants it.

Source: Seattle Department of Construction and Inspections, Director's Report, "Accessory Dwelling Unit Amendments – Implementing HB 1337" (2024), seattle.gov.

## 2. Flag found: the reference line uses too few states in later years

The reference line is the median of the states' observed rates in each year since the law. The code needs only 2 states in a year. The cross-scenario rule (AQ-054) shows a median line only with at least 4 cases.

| Year since the law | V0 states | V6 states |
| --- | --- | --- |
| 1 | 7 | 7 |
| 2 | 4 | 4 |
| 3 | 4 | 4 |
| 4 | 4 (Oregon, Utah, Vermont, California) | **2 (Utah, California)** |
| 5 | 1 (California; carried forward) | 1 (California; carried forward) |

Under V6, year 4 rests on Utah and California alone, so the line jumps to 14,216 permits. With the 4-case rule, years 4–5 carry year 3's median forward. The line is then about 10,395 under V6, against 10,374 today; the current line is unchanged by the rule. Recommended: apply the 4-case rule to the ADU reference line too.

## 3. Which way the remaining error leans

Both fixes lowered over-predictions (Vermont, Oregon). The biggest remaining under-predictions are Maine (−0.11) and Rhode Island (−0.07), and Utah is −0.04 under V6p. Utah counts internal ADUs only. Its missing detached ADUs would raise its true rate, so the model may be slightly low there. Maine's 0.73 people share probably under-corrects its count too. Both point the same way: the range may sit a little low.

## 3b. Worst miss traced

Under V6 the worst state was Utah, predicted 13% too low; under V6p it is Vermont (+0.19), whose lag may be longer than Austin's. Utah counts self-reported internal ADUs only, by report year (August to July). Detached ADUs are missing, so Utah's true rate is likely higher still. Nothing to fix without detached counts, which Utah's reports do not give.

## 4. Next round

- Trace the worst under-predictions (Maine, Rhode Island, Utah), not only the worst miss.
- Maine's town list (asked of the Maine Office of Community Affairs).
- Wisconsin's current-law rates: 74% of the central addition sits in places with an assumed current rate.

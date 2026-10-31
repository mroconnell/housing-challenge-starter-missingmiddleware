# ADU improvement loop, round 2: results

Run 2026-10-31 under [IMPROVE_R2_PLAN.md](IMPROVE_R2_PLAN.md), committed before any result was computed. Code: `scripts/run_adu_improve.py --round 2`. Outputs: `reference/adu_improve_r2_scores.csv`, `adu_improve_r2_by_state.csv`, `adu_improve_r2_flags.csv`. Units as in [round 1](IMPROVE_R1_RESULTS.md): rates are ADU permits per 1,000 single-family homes per year; log error = log(predicted ÷ observed); RMS over the 7 held-out states, lower is better; additional permits are Wisconsin, 2027–2031.

## Answer

- **Coding Oregon from its benchmark rules (V5) fixes Oregon's miss:** +0.20 → +0.06. RMS 0.168 → 0.141.
- **With the Vermont fix too (V6), the RMS falls to 0.110,** the best of any version so far. No state misses by more than 0.13 (about 13%).
- **V6 lowers the Wisconsin numbers:** lower 6,804 → 6,100, central 10,679 → 10,000, upper 19,535 → 18,448 additional permits. Oregon's early years now count as weaker rules, so the typical level and the slow-state lower both fall.
- **The adopted model still beats the simple ones on every version** (plain average 0.30–0.32, same-year average without California 0.34–0.35, median 0.21–0.23).
- **But most of that drop comes from one Portland row, not from Oregon's panel (section 1b).** If Portland's 2019 is dropped as a transition year, as the panel's 2019 is, the central is 10,721 and the RMS 0.111.
- **Ryan decides.** Recommended: adopt V6p (both corrections, both Oregon series treating 2019 the same way), with the reference-line fix below: lower 6,718, central 10,721, upper 19,415.

## 1. Held-out test

| Variant | Plain average | Same-year average, no California | Median | Adopted model | Worst state (adopted) | Lower | Central | Upper |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| V0 current data | 0.319 | 0.338 | 0.230 | 0.168 | Vermont +0.33 | 6,804 | 10,679 | 19,535 |
| V1 Vermont by permit year | 0.309 | 0.343 | 0.216 | 0.135 | Oregon +0.24 | 6,790 | 10,834 | 19,519 |
| V5 Oregon from benchmark rules | 0.312 | 0.341 | 0.223 | 0.141 | Vermont +0.26 | 6,180 | 9,945 | 18,464 |
| V6 = V1 + V5 | 0.302 | 0.346 | 0.209 | 0.110 | Utah −0.13 | 6,100 | 10,000 | 18,448 |
| **V6p = V6, Portland 2019 dropped** | 0.302 | 0.346 | 0.209 | **0.111** | Vermont +0.19 | **6,718** | **10,721** | **19,415** |

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

So the Oregon panel recode on its own barely moves the central; the drop in V6 came from Portland's row. Recommended: V6p.

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

# Parking causal framework: Stage 1 results

Plan: `docs/parking/CAUSAL_FRAMEWORK_PLAN.md` (locked 2026-11-03 before any count; changes logged at its end).
All intervals are 90%. MDE = minimum detectable effect (1.645 × standard error). Nothing in the tool has changed.

## Summary

| Test | Question | Result (90% interval) | Unit | Reading |
| --- | --- | --- | --- | --- |
| Main | Average effect of repeal on permits (76 places) | −1.14 (−3.43 to +1.38) home-weighted; +0.42 (−1.20 to +1.96) equal-weight | permits per 1,000 existing homes a year | No measurable change |
| F1 | Less parking per new home after reform? (Minneapolis, 5+ home projects outside downtown) | 0.98 before 2015 → 0.73 in 2015–21: −0.24 (−0.34 to −0.15). Against downtown (no minimum either side): −0.17 (−0.38 to +0.02). Inside the 2015 transit areas vs outside them (F1b): −0.06 (−0.20 to +0.08) | car spaces per home | **Not separated from a citywide trend.** Parking per home fell by about a quarter space both inside and outside the areas the 2015 cut covered |
| H1 | Bigger 5+ unit buildings? | +17.0 (+4.9 to +28.4), +37% | homes per new 5+ unit building | Supported (Austin carries 30% of the weight) |
| H2 | More buildings? | 2–4 unit: −0.03 (−0.07 to +0.02); 5+ unit: −0.06 (−0.10 to −0.02), −35% | new buildings per 1,000 existing homes a year | Fewer, bigger 5+ buildings; read with H1 |
| F1c | Seattle, inside reform areas vs the rest of the city | 2012: −0.27 (−0.46 to −0.08), but about −0.11 (−0.32 to +0.11) from a 2009 start; zero-parking projects 0% → 13–45% inside, 0% outside | car spaces per home | Zero-parking projects appear only after reform; the size of the average drop is uncertain |
| E1 | AB 2097 line, 2–4 home projects (no earlier relief) | −0.023 (−0.070 to +0.018); MDE 0.044 | homes permitted per 1,000 existing homes a year | No measurable change; pre-trend balanced |
| E2 | Repeal alone minus repeal inside a rewrite | −0.14 (−4.43 to +4.00) | permits per 1,000 existing homes a year | No difference |
| E2 2×2 | Does repeal add to a rezoning? (repeal + rewrite) − (repeal alone) − (rewrite only) | −3.07 (−7.31 to +1.78) | same | No measurable interaction; weak (9 rewrite-only places) |
| T | Effect with rail or bus rapid transit minus without (24 vs 51 places) | −4.40 (−8.21 to −0.37); rail only −5.96 (−9.63 to −1.95) | permits per 1,000 existing homes a year | Smaller effect in transit cities when weighted by homes; not when each city counts once (+0.35; rail only −1.16) |
| M1 | Higher old minimum (held out) | −2.91 (−7.79 to +2.88) | same | Not material |
| M3 | Larger city (held out) | −3.98 (−8.52 to +1.20) | same | Not material |
| M2, M4 | = E2, = T | see above | | M4 material, M2 not |
| R | Effect by year since repeal | k1 −0.84 (75 places), k2 −1.03 (57), k3 −2.01 (38), k4 −5.14 (26), k5 −4.62 (15) | same | Described only; later years are fewer, earlier repealers. Years 4–5 lean toward the tool's low line |
| H3 | Bunching at the old minimum | Fails feasibility: only Minneapolis has project data with a known minimum | | Not run |

Only 1 of 4 moderators came out material (M4, rail or BRT, home-weighted only). With four tested, one false "material" is plausible, and M4 rests on Austin and Minneapolis (see T sensitivity). M3 and M4 overlap: rail places are mostly the large places.

## Notes by test

**F1 (Minneapolis Planning Commission approvals, compiled by A. Schieferdecker).**
- 553 rows read; 54 later-resubmitted rows dropped; 5+ home projects only.
- Ramp vs floor: spaces per home fell from about 1.0 (2011–2015) to 0.58–0.80 a year from 2016 on, and stayed there. The drop levelled off well above 0. That matches a floor (lenders and renters still want parking), not a long ramp.
- Share of projects with no car spaces: 0% before 2015, 8% in 2015–21, 19% after 2021.
- **Against downtown (audit fix):** rest-of-city change minus downtown change.
  - 2015 cut (split at the effective date 2015-07-18): −0.17 (−0.38 to +0.02). Downtown barely moved, 0.96 → 0.89 (32 → 50 projects).
  - 2021 repeal: +0.28 (+0.03 to +0.63). Downtown went 0.89 → 0.51 on only 9 projects after 2021, so this is noisy.
  - Both reforms together: +0.11 (−0.18 to +0.50).
  - Read: the big downtown fall is after 2021, on only 9 projects. This test cannot say how much of the fall the reforms caused; F1b is the cleaner test for 2015.
- **Row check against city records (audit fix; 20 random rows, seed 20261103):**
  - Homes: 20 of 20 match the city Planning Commission annual reports.
  - Car spaces: 16 of 16 rows with a source match (within 10% or 3 spaces). The other 4 rows have no parking count anywhere.
  - Parking sources: 7 rows from archived city staff reports; 9 from secondary sources (trade press, development trackers). One of the 9 was read from a search-engine copy of a city page that blocked direct access, so it is counted as secondary.
  - Patterns: in mixed-use buildings the sheet sometimes counts total parking, not just homes' parking (Latitude 45). One condo tower's figure looks estimated (Gateway, 2 per home). Home counts are those at approval, and later revisions differ.
  - Read: the sheet is accurate enough to use. The F1 label stays "suggestive, single source" because of the downtown comparison, not data quality.
- Caveats:
  - The 2015 cut covered transit areas only, but the contrast is citywide outside downtown (no geocoding), so it is diluted.
  - Downtown, with no minimum either side, also fell (0.92 → 0.51, only 9 projects after 2021). Some of the drop may be market drift.
  - The sheet is one person's "ballpark" compilation of approvals, not permits.
- Bunching (descriptive, not H3): 12% of projects sat at exactly 1.0 per home before 2015; 7–10% after.

**F1b Minneapolis, inside vs outside the 2015 transit areas.**
- 2015 ordinance: 2015-Or-061, effective 2015-07-18. F1 had used 2015-05-01, and its 2015 figures are now rerun with the effective date (they move by 0.01 or less).
- Zones: the city's June 2015 map of the covered areas, digitised. Addresses were geocoded with the Census geocoder; 23 of 359 projects didn't match and are left out.
- Inside: 0.99 → 0.72 car spaces per home (28 → 109 projects). Outside: 0.90 → 0.69 (41 → 74 projects).
- Difference: −0.06 (−0.20 to +0.08). It includes 0.
- At the locked plan's split date (2015-05-01): −0.07 (−0.20 to +0.08). The move to the effective date was decided before F1b's first mean but committed together with the result, so both are shown.
- Sensitivities:
  - University Area dropped: −0.03 (−0.22 to +0.19).
  - Projects near a zone edge dropped: −0.08 (−0.22 to +0.07).
- Read: parking per home fell by about a quarter space across Minneapolis after 2015, whether or not the cut applied. The rule change itself is not visible in this comparison. Possible reasons:
  - Builders outside the covered areas were already getting variances.
  - The market moved citywide.
  - The covered areas were wide enough that outside projects were often near frequent transit anyway.

**F1c Seattle (second city; SDCI land-use permits, 1,736 projects of 5+ homes).**
- Parser hand-check: 46 of 50 random rows right, which passes the 45 rule. The 4 misses: a light-rail station whose demolished homes were read as new homes; one project with garage plus surface parking where only the garage was read; one project where only one of two home types was read; and one 5-home project whose 4 garage spaces were read without its 1 surface stall.
- 2012 reform, inside urban centers and villages minus the rest of the city: −0.27 car spaces per home (−0.46 to −0.08). **Binding.** Inside went 0.98 → 0.59 spaces per home; outside went 0.94 → 0.82.
- 2018 reform: +0.05 (−0.12 to +0.21). No extra drop beyond 2012.
- Caveats:
  - Descriptions give the whole project's parking, including shops and hotels.
  - Inside spaces per home were already 0.6–0.7 in 2009–2011, so part of the drop may come before the 2012 reform. The before window starts in 2006.
  - Dates are approximate council dates.
- **Pre-trend (audit round 2, *post hoc*):** spaces per home inside the reform areas stepped down from about 1.2 to about 0.7 in 2009, three years before the 2012 reform. With the before window starting in 2009 instead of 2006, the 2012 effect is −0.11 (−0.32 to +0.11), which includes 0. The −0.27 main result leans on the 2006–2008 boom years. A San Diego planning deck dates a Seattle expansion of no-minimum areas to urban villages to 2010. That would explain the step, but it is not confirmed; other sources date the urban-village change to 2012.
- **Cleaner evidence, projects with no car parking (*post hoc*):**
  - Inside the reform areas: 0% every year through 2010, 3% in 2011, 9% in 2012, then 13–45% a year from 2013 to 2024.
  - Outside: 0% every year through 2018, and at most 6% after that.
  - Projects with no parking could not be built before minimums were removed, so this is a direct sign the reform let projects build less parking.
- Read with Minneapolis: two cold-climate cities both show fewer spaces per home after a reform, by about a quarter of a space per home, and neither falls toward zero.

**E2 2×2 (TOD's upzoned places as "rewrite only").**

| Cell | Places | Effect against matched places that did neither (90% interval) |
| --- | --- | --- |
| Repeal alone | 25 | −1.23 (−2.78 to +1.36) |
| Repeal + rewrite | 51 | −1.09 (−4.48 to +2.88) |
| Rewrite only (TOD upzoning, no parking removal) | 9 | +3.21 (+0.88 to +4.17) |
| TOD upzoning with station-area parking removal (apart) | 5 | −4.63 (−5.93 to −2.65) |

Unit: permits per 1,000 existing homes a year.
- Interaction: −3.07 (−7.31 to +1.78). It includes 0, so there is no measurable sign that repeal changes what a rezoning does.
- **Below the pre-set rule.** The plan required 10+ rewrite-only places; 11 were coded but only 9 are usable. Read this cell as below the rule.
- *Post hoc*, equal-weight (audit round 2): Chicago (46% of the weight; 1 comparison place, 1 year before) and Phoenix (23%) carry 69% of the rewrite-only cell. Equal-weight rewrite only: +1.78 (−0.34 to +3.83), median +1.45. Equal-weight interaction: −2.93 (−6.37 to +0.59). Home-weighted stays the main result.
- Weak:
  - 11 rewrite-only places were coded and 9 could be used. Los Angeles had no comparison place of its size, and Indianapolis's balance area has no matching home count.
  - Chicago, Phoenix and San Diego have only 1–2 comparison places each.
- Different kinds of rezoning: TOD's are mostly station-area rezonings measured citywide, while repeal-place rewrites are often citywide.
- The 5 "upzoning + parking removal" places (Denver, Portland, Somerville, San Diego, Madison) are too few to read on their own. Charlotte is missing because Mecklenburg County issues its permits.

**E1.**
- E1 uses the same jurisdictions and zones as the earlier AB 2097 test (`docs/tod/AB2097_TEST_RESULTS.md`), so it is a re-check of that test by size class, not a second vote.
- Main result is issue-date dating (−0.023, −0.070 to +0.018). Late reporting (18–24% of 2018–22 homes first appear in a later report) means the after years are still filling in, which pulls recent years down. The bias runs toward a negative estimate, so the true change is, if anything, less negative. Report-year dating is shown beside it: −0.045 (−0.103 to +0.019).
- Data: 185 California jurisdictions; inside ½ mile vs ½–1½ miles; 2023–25 vs 2018–22.
- 5+ projects without the density bonus fell inside relative to outside, −1.41 (−2.77 to −0.24). The pre-trend was about the same size, and the result does not survive report-year dating (*post hoc*). So it is not read as an AB 2097 effect.
- Late reporting: 18–24% of 2018–22 homes first appear in a later report year. Issue-date dating (main) undercounts the after years; report-year dating is shown beside it. Which is main is Ryan's call.

**T.**
- Rail = an NTM rail stop inside the place's 2024 boundary; BRT is not included.
- South Bend has no computable matched effect and is left out.
- Rail places include Minneapolis (−8.5), Austin (−12.3), San Francisco (−2.6), St. Paul (−2.2).

**M3.**
- The split is the home-weighted median, so "large" is 6 places and "small" 70.
- *Post hoc*, unweighted median split (39 vs 37), held-out method (split point from the other folds, home-weighted means of each group): −2.12 (−5.87 to +1.68). Still not material. The locked weighted split stays the main result.
- A second unweighted figure, +1.05 (−1.99 to +4.14) in `parking_causal_v2_summary.csv`, uses the full sample and equal-weight means of each group. Weighting by homes versus counting each city once flips the sign; neither is material.

**T rerun with corrected stop data and bus rapid transit (2026-11-03).**
- **Data fix:** the first T run used a rail-stop file covering only the 41 agencies TOD needed. Rail cities such as Cambridge MA and Beaverton OR were counted as "no rail". The rerun uses the national National Transit Map layer (72 rail agencies).
- **Bus rapid transit added**, as the locked plan said: Hartford, Richmond, Eugene, Springfield OR and Birmingham, each with a line open before its repeal. Amtrak-only cities count as no rail.
- **Results** (permits per 1,000 existing homes a year):

| Version | Transit places | Others | With minus without (90% interval) |
| --- | --- | --- | --- |
| Rail or BRT (main) | 24 | 51 | −4.40 (−8.21 to −0.37) |
| Rail only | 19 | 56 | −5.96 (−9.63 to −1.95) |
| Rail or BRT, without Austin and Minneapolis | 22 | 51 | −1.58 |
| Rail or BRT, each city counted once | 24 | 51 | +0.35 |
| Rail only, each city counted once | 19 | 56 | −1.16 |

- Leave one place out: −5.50 (without Lexington) to −2.62 (without Austin).
- **Audit fixes (round 4):**
  - Comparison places are coded by rail only, so every repeal place is now matched on its own rail status. BRT cities had been matched to rail comparison places. The fix moves the main result from −4.37 to −4.40.
  - Timing: rail uses today's stops, while BRT uses opening dates (each line opened before its city's repeal). The two rules differ, and this is stated rather than changed.
  - Birmingham Xpress began service on 2022-09-22, before Birmingham's 2024 repeal.
  - Rail edge cases: Portland ME and Anchorage. Counting either as "no rail" moves the estimate by 0.29 or less.
- **Read:** the home-weighted gap comes from a few big transit cities with weak years after repeal (Austin, Minneapolis, Cambridge MA). Counting each city once, transit cities did slightly better. Rail or BRT does not reliably change the effect.

**T sensitivity, first run (*post hoc*; rail file with 41 agencies, superseded).** The rail result rests on two cities.

| Version | Rail minus no rail |
| --- | --- |
| Main (home-weighted) | −4.67 |
| Without Austin | −2.55 |
| Without Minneapolis | −3.95 |
| Without both | −1.24 |
| Unweighted, all places | −1.63 |
| Unweighted, without both | +0.48 |

Dropping one place at a time keeps the estimate between −5.62 (without San Jose) and −2.55 (without Austin); dropping the two largest drivers takes it to −1.24.

Read: rail does not reliably change the effect. "Invest in both" is neither supported nor ruled out.

## Parking × rezoning at the station-area scale (*post hoc*, descriptive)

- **Question:** whether rezoned station areas grew more where parking minimums were removed at the same time.
- **Data and unit:** TOD's station-area effects within ¼ mile, in extra homes per 100 lot acres a year (`reference/tod_causal_line_age.csv`).
- **Parking coding:** TOD's place list.
  - "Removed": Charlotte, Denver, Portland.
  - "Not removed" (kept or only cut): New York, Philadelphia, Chicago, Austin, St. Paul, Salt Lake City.
  - Seattle's coding is unknown, so it is left out.
- **This is post hoc:** the station-area effects were seen before the grouping was made.
- **Result:**
  - Removed: mean +37.0.
  - Not removed: mean +26.8.
  - Difference: +10.2, with a 90% range of −45 to +68.
- **One city decides the sign.** Without Denver the difference is −29; without Portland it is +45.
- **Why this differs from TOD's trait 12:** trait 12 asked whether parking was *cut* (St. Paul and Chicago = yes). This test asks whether minimums were *removed* (St. Paul and Chicago = no). That is why the two point in opposite directions.
- **Earlier TOD trait test** (`docs/tod/TRAITS_RESULTS.md`, trait 12): units in cities that cut parking had smaller effects. That was a weak pass, and it did not survive dropping St. Paul.
- **Read:** at the station-area scale too, the data cannot tell whether removing parking minimums changes what a rezoning does.

## Added mid-sized and large cities (`reference/parking_repeal_checks_v2.csv`)

- Checked: 35 PRN cities with 25,000+ people, rated at or near a full repeal, that had not been checked before.
- Most of PRN's ratings did not hold up: only 8 of the 35 "at or near" ratings were confirmed as a citywide housing repeal.
  - 26 are weaker (district-only exemptions or cuts).
  - 1 does not cover housing.
  - Greensboro and High Point repeal under a North Carolina law that takes effect in 2027.
- Five fall in 2015–2024: Dover NH (2015, low confidence), Jackson TN (2021), Bowling Green OH (2023), Bakersfield CA (2024) and Spokane WA (2024).
  - Bowling Green has no Census permit file of its own, so 4 were added.
  - Hillsboro OR (2025) is too recent.

| Measure | 76 places | 76 + 4 added |
| --- | --- | --- |
| Average effect, home-weighted | −1.14 (−3.43 to +1.38) | −1.04 (−3.27 to +1.48) |
| Average effect, equal-weight | +0.42 (−1.20 to +1.96) | +0.46 (−1.06 to +1.94) |
| E2 repeal alone minus repeal + rewrite | −0.14 (−4.34 to +3.93) | −0.35 (−4.50 to +3.57) |

Unit: permits per 1,000 existing homes a year.

- Adding the four cities does not change any reading.
- Bakersfield and Spokane have only one year after their repeal.
- The tool still uses the 76 places.
- **Not rerun on the added places (deviation from the plan, logged):** H1/H2, T, M1, M2/M4 and R. The 4 added cities are 5% of the places and change the average by 0.10. Two have only one year after repeal (too few for R or a 3-year window). M1 would need old minimums coded for the new cities. Only the averages, E2 and M3 were rerun.

## Follow-ups from Ryan's theory chat (*post hoc* to Stage 1; rules locked before each count)

**FU1, comparison cities also matched on apartment share.**
- Repeal places built more apartments before repeal. The share of homes in 5+ unit buildings was 45% in repeal places against 37% in their comparison places. Narrowing comparisons to ±10 points brings that to 41%; 39 places needed filling to the 5 nearest.
- Results, permits per 1,000 existing homes a year (75 places; South Bend has no computable effect):

| Version | Home-weighted | Equal-weight |
| --- | --- | --- |
| Main comparison | −1.07 (−3.45 to +1.50) | +0.51 (−1.08 to +2.09) |
| Also matched on apartment share | −0.98 (−3.37 to +1.62) | +0.44 (−1.42 to +2.29) |

- Read: matching on apartment share barely moves the result. The 2022–24 apartment slowdown is not what makes the average null.

**FU2, Austin against Sun Belt boom cities.**
- Peers: Dallas, Houston, San Antonio, Fort Worth, Phoenix, Atlanta, Tampa, Orlando, Jacksonville and Las Vegas. Nashville was not found under that name in the permit files.
- Austin went 34.3 → 19.0 permits per 1,000 homes a year. The peers together went 17.3 → 14.5.
- Difference: −12.5, about the same as the main −12.3.
- Read: Austin fell much more than other Sun Belt boom cities. Before repeal it was permitting at twice their rate, so a fall back from an unusual peak is a likely part of it. Austin's repeal also came with the HOME rezoning, and this test cannot separate the two.

## What Stage 1 says for Stage 2 (not yet run)
- Parking per home fell in Minneapolis after 2015, but by the same amount where the cut did and did not apply (F1b). In Seattle, projects with no parking appeared only in reform areas (F1c). Builders put more homes in each larger building (H1).
- No test shows more total homes, and the line test (E1) finds no measurable change at its scale.

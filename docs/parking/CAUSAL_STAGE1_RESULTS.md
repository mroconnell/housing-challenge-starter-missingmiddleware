# Parking causal framework: Stage 1 results

Plan: `docs/parking/CAUSAL_FRAMEWORK_PLAN.md` (locked 2026-11-03 before any count; changes logged at its end).
All intervals are 90%. MDE = minimum detectable effect (1.645 × standard error). Nothing in the tool has changed.

## Summary

| Test | Question | Result (90% interval) | Unit | Reading |
| --- | --- | --- | --- | --- |
| F1 | Less parking per new home after reform? (Minneapolis, 5+ home projects outside downtown) | 0.98 before 2015 → 0.74 in 2015–21: −0.24 (−0.34 to −0.14). Against downtown (no minimum either side): −0.17 (−0.40 to +0.04) | car spaces per home | **Suggestive, single source.** The drop is clear, but downtown fell too, so the reform's share is not separated from market drift |
| H1 | Bigger 5+ unit buildings? | +17.0 (+4.9 to +28.4), +37% | homes per new 5+ unit building | Supported (Austin carries 30% of the weight) |
| H2 | More buildings? | 2–4 unit: −0.03 (−0.07 to +0.02); 5+ unit: −0.06 (−0.10 to −0.02), −35% | new buildings per 1,000 existing homes a year | Fewer, bigger 5+ buildings; read with H1 |
| F1c | Seattle, inside reform areas vs the rest of the city | 2012: −0.27 (−0.46 to −0.08), but about −0.11 (−0.32 to +0.11) from a 2009 start; zero-parking projects 0% → 13–45% inside, 0% outside | car spaces per home | Zero-parking projects appear only after reform; the size of the average drop is uncertain |
| E1 | AB 2097 line, 2–4 home projects (no earlier relief) | −0.023 (−0.070 to +0.018); MDE 0.044 | homes permitted per 1,000 existing homes a year | No measurable change; pre-trend balanced |
| E2 | Repeal alone minus repeal inside a rewrite | −0.14 (−4.43 to +4.00) | permits per 1,000 existing homes a year | No difference |
| E2 2×2 | Does repeal add to a rezoning? (repeal + rewrite) − (repeal alone) − (rewrite only) | −3.07 (−7.31 to +1.78) | same | No measurable interaction; weak (9 rewrite-only places) |
| T | Effect with rail minus without (11 vs 64 places) | −4.67 (−8.51 to −0.42) | permits per 1,000 existing homes a year | Smaller effect in rail cities |
| M1 | Higher old minimum (held out) | −2.91 (−7.79 to +2.88) | same | Not material |
| M3 | Larger city (held out) | −3.98 (−8.52 to +1.20) | same | Not material |
| M2, M4 | = E2, = T | see above | | M4 material, M2 not |
| R | Effect by year since repeal | k1 −0.84 (75 places), k2 −1.03 (57), k3 −2.01 (38), k4 −5.14 (26), k5 −4.62 (15) | same | Described only; later years are fewer, earlier repealers |
| H3 | Bunching at the old minimum | Fails feasibility: only Minneapolis has project data with a known minimum | | Not run |

Only 1 of 4 moderators came out material (M4, rail). With four tested, one false "material" is plausible, and M4 rests on Austin and Minneapolis (see T sensitivity). M3 and M4 overlap: rail places are mostly the large places.

## Notes by test

**F1 (Minneapolis Planning Commission approvals, compiled by A. Schieferdecker).**
- 553 rows read; 54 later-resubmitted rows dropped; 5+ home projects only.
- Ramp vs floor: spaces per home fell from about 1.0 (2011–2015) to 0.58–0.80 a year from 2016 on, and stayed there. The drop levelled off well above 0. That matches a floor (lenders and renters still want parking), not a long ramp.
- Share of projects with no car spaces: 0% before 2015, 8% in 2015–21, 19% after 2021.
- **Against downtown (audit fix):** rest-of-city change minus downtown change.
  - 2015 cut: −0.17 (−0.40 to +0.04). Downtown went 0.96 → 0.70 (30 → 52 projects).
  - 2021 repeal: +0.28 (+0.03 to +0.64). Downtown went 0.90 → 0.51 on only 9 projects after 2021, so this is noisy.
  - Both reforms together: +0.10 (−0.17 to +0.49).
  - Read: parking per home fell across the whole city, downtown included. This test cannot say how much of the fall the reforms caused.
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
- *Post hoc*, unweighted median split (39 vs 37): −2.12 (−5.87 to +1.68). Still not material. The locked weighted split stays the main result.

**T sensitivity (*post hoc*).** The rail result rests on two cities.

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

## What Stage 1 says for Stage 2 (not yet run)
- Parking per home fell in Minneapolis after the reforms (F1, suggestive, single source; downtown fell too), and builders put more homes in each larger building (H1).
- No test shows more total homes, and the line test (E1) finds no measurable change at its scale.

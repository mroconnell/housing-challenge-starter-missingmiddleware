# Parking causal framework: Stage 1 results

Plan: `docs/parking/CAUSAL_FRAMEWORK_PLAN.md` (locked 2026-11-03 before any count; changes logged at its end).
All intervals are 90%. MDE = minimum detectable effect (1.645 × standard error). Nothing in the tool has changed.

## Summary

| Test | Question | Result (90% interval) | Unit | Reading |
| --- | --- | --- | --- | --- |
| F1 | Less parking per new home after reform? (Minneapolis, 5+ home projects outside downtown) | 0.98 before 2015 → 0.74 in 2015–21: −0.24 (−0.34 to −0.14); 2021 repeal: a further −0.11 (−0.22 to +0.01) | car spaces per home | Binding after 2015; 2021 adds a smaller drop |
| H1 | Bigger 5+ unit buildings? | +17.0 (+4.9 to +28.4), +37% | homes per new 5+ unit building | Supported (Austin carries 30% of the weight) |
| H2 | More buildings? | 2–4 unit: −0.03 (−0.07 to +0.02); 5+ unit: −0.06 (−0.10 to −0.02), −35% | new buildings per 1,000 existing homes a year | Fewer, bigger 5+ buildings; read with H1 |
| E1 | AB 2097 line, 2–4 home projects (no earlier relief) | −0.023 (−0.070 to +0.018); MDE 0.044 | homes permitted per 1,000 existing homes a year | No measurable change; pre-trend balanced |
| E2 | Repeal alone minus repeal inside a rewrite | −0.14 (−4.43 to +4.00) | permits per 1,000 existing homes a year | No difference; 2×2 incomplete |
| T | Effect with rail minus without (11 vs 64 places) | −4.67 (−8.51 to −0.42) | permits per 1,000 existing homes a year | Smaller effect in rail cities |
| M1 | Higher old minimum (held out) | −2.91 (−7.79 to +2.88) | same | Not material |
| M3 | Larger city (held out) | −3.98 (−8.52 to +1.20) | same | Not material |
| M2, M4 | = E2, = T | see above | | M4 material, M2 not |
| R | Effect by year since repeal | k1 −0.84 (75 places), k2 −1.03 (57), k3 −2.01 (38), k4 −5.14 (26), k5 −4.62 (15) | same | Described only; later years are fewer, earlier repealers |
| H3 | Bunching at the old minimum | Fails feasibility: only Minneapolis has project data with a known minimum | | Not run |

Four moderators were tested, so one false "material" in four is plausible. M4 (rail) is the only one, and it rests on Austin and Minneapolis (see T sensitivity).

## Notes by test

**F1 (Minneapolis Planning Commission approvals, compiled by A. Schieferdecker).**
- 553 rows read; 54 later-resubmitted rows dropped; 5+ home projects only.
- Ramp vs floor: spaces per home fell from about 1.0 (2011–2015) to 0.58–0.80 a year from 2016 on, and stayed there. The drop levelled off well above 0. That matches a floor (lenders and renters still want parking), not a long ramp.
- Share of projects with no car spaces: 0% before 2015, 8% in 2015–21, 19% after 2021.
- Caveats:
  - The 2015 cut covered transit areas only, but the contrast is citywide outside downtown (no geocoding), so it is diluted.
  - Downtown, with no minimum either side, also fell (0.92 → 0.51, only 9 projects after 2021). Some of the drop may be market drift.
  - The sheet is one person's "ballpark" compilation of approvals, not permits.
- Bunching (descriptive, not H3): 12% of projects sat at exactly 1.0 per home before 2015; 7–10% after.

**E1.**
- Data: 185 California jurisdictions; inside ½ mile vs ½–1½ miles; 2023–25 vs 2018–22.
- 5+ projects without the density bonus fell inside relative to outside, −1.41 (−2.77 to −0.24). The pre-trend was about the same size, and the result does not survive report-year dating (*post hoc*). So it is not read as an AB 2097 effect.
- Late reporting: 18–24% of 2018–22 homes first appear in a later report year. Issue-date dating (main) undercounts the after years; report-year dating is shown beside it. Which is main is Ryan's call.

**T.**
- Rail = an NTM rail stop inside the place's 2024 boundary; BRT is not included.
- South Bend has no computable matched effect and is left out.
- Rail places include Minneapolis (−8.5), Austin (−12.3), San Francisco (−2.6), St. Paul (−2.2).

**M3.**
- The split is the home-weighted median, so "large" is 6 places and "small" 70.
- *Post hoc*, unweighted median split (39 vs 37): −2.12 (−5.87 to +1.68). Still not material.

**T sensitivity (*post hoc*).** The rail result rests on two cities.

| Version | Rail minus no rail |
| --- | --- |
| Main (home-weighted) | −4.67 |
| Without Austin | −2.55 |
| Without Minneapolis | −3.95 |
| Without both | −1.24 |
| Unweighted, all places | −1.63 |
| Unweighted, without both | +0.48 |

Read: rail does not reliably change the effect. "Invest in both" is neither supported nor ruled out.

## What Stage 1 says for Stage 2 (not yet run)
- The reform moves parking (F1), and builders put more homes in each larger building (H1).
- No test shows more total homes, and the line test (E1) finds no measurable change at its scale.

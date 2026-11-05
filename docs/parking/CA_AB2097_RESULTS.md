# CA AB 2097: results (first full run, 2026-11-05)

Plan: [CA_AB2097_PLAN.md](CA_AB2097_PLAN.md) (locked 2026-11-05 16:48 UTC; changes after lock in section 9, all made
before any count unless marked post hoc). Code: `scripts/ca_ab2097_estimate.py` (run at d6d96c2d), post hoc checks
`scripts/ca_ab2097_posthoc.py`. Outputs: `reference/ca_ab2097_results*.csv`, `reference/ca_ab2097_posthoc_*.csv`.
Status: **draft for the audit's review**, then Ryan.

Unless a row says otherwise, every number is **homes in issued building permits per 1,000 existing homes (2020 census)
per year**, 2023–2025 compared with 2018–2022, near transit (within ½ mile) compared with the ring (½ to 1½ miles) in
the same jurisdictions. Ranges are 90%, from 2,000 resamples of whole jurisdictions. "MDE" is the smallest change the
test could detect (1.645 × the spread of the resampled estimates).

## 1. Answer in brief

- **No measurable change.** Near transit, homes permitted (other than ADUs) changed by −0.905 per 1,000 existing
  homes a year relative to the ring, range −2.292 to +0.350. The range includes 0. The test could detect a change of
  about 1.330 either way.
- **The placebo check failed.** The locked rule (plan section 8, audit block item 3) needs the early-reform test
  cities' 90% range to include 0. It does not: −2.291 (−3.926 to −0.284), and those cities were already falling near
  transit before 2023. So near-vs-ring can drift for reasons other than AB 2097, and this design cannot support a
  causal reading in either direction: it cannot show an effect, and it cannot confirm "no effect" either.
- **Before years.** The main group's lead checks include 0, but every before year sits 1.22 to 3.32 below 2022, which
  was a high year near transit.
- **City-level check: no measurable change.** Homes-weighted slope −1.734 (−3.135 to +1.719); equal weight per city
  +12.602 (−0.132 to +33.057). Both include 0, so there is no statewide "extra homes" claim.
- **Affordable homes (descriptive only).** Tax-credit apartments near transit: +0.165 (−0.205 to +0.510), no
  measurable change. Deed-restricted low-income homes and density-bonus homes were already rising near transit before
  2023 (lead checks exclude 0), so they cannot be read.

## 2. Main result and its checks on the before years

Main group: 198 full-reporting jurisdictions with homes near transit, less the 14 early-reform places and Mountain View.

| Measure | Estimate | 90% range | MDE |
| --- | --- | --- | --- |
| **Headline: homes other than ADUs** | **−0.905** | −2.292 to +0.350 | 1.330 |
| All homes | −0.942 | −2.330 to +0.319 | 1.339 |
| Homes in 2+ unit buildings | −0.789 | −2.045 to +0.454 | 1.283 |
| ADU homes | −0.037 | −0.176 to +0.085 | 0.130 |
| Homes other than ADUs, **per acre** (permits per acre per year) | −0.007 | −0.013 to −0.001 | 0.006 |
| Lead check: 2021–2022 vs 2018–2020 (no law yet) | +0.059 | −1.901 to +2.135 | |
| Lead slope, per year, 2018–2021 vs 2022 | −0.648 | −1.679 to +0.165 | |
| Placebo date: 2020–2022 vs 2018–2019 | −0.240 | −2.326 to +1.591 | |
| Anticipation: 2023–2025 vs 2018–2021 | −0.481 | −1.906 to +0.816 | |

Year by year, relative to 2022 (homes other than ADUs; 90% ranges):

| Year | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Estimate | −1.22 | −1.89 | −2.05 | −3.32 | 0 | −3.21 | −3.63 | −0.96 |
| Range | −5.13 to +3.17 | −5.67 to +1.55 | −5.71 to +0.98 | −7.05 to +0.45 | (reference) | −6.80 to +0.51 | −7.53 to −0.35 | −4.68 to +2.51 |

2022 was a high year near transit; every other year sits below it, before and after the law alike.

The per-acre row is the only main-group headline row whose range excludes 0, and only just (−0.001). Under the plan's
symmetric rules, read beside all the checks, it is not a finding on its own.

## 3. Early-reform test cities (placebo group)

12 places that already had no parking minimums near transit (or repealed citywide) and have homes near transit.

| Measure | Estimate | 90% range |
| --- | --- | --- |
| Headline, homes other than ADUs | −2.291 | −3.926 to −0.284 |
| Lead slope, per year, 2018–2021 vs 2022 | −3.133 | −5.664 to −1.390 |
| Lead check: 2021–2022 vs 2018–2020 | −4.103 | −8.630 to −1.445 |

Under the locked rule this check fails (see section 1). These places' near-transit building was already falling relative to their rings before 2023 (lead check −4.103,
range −8.630 to −1.445), so their headline is not a clean placebo. Their range excludes 0, so the plan's placebo
condition fails. This says the near-vs-ring comparison can drift for reasons other than AB 2097
in dense, early-reform cities (San Francisco, San Diego, Oakland and others). The main result stays "no measurable change", but with the placebo
check failed, it cannot be read as evidence of no effect.

## 4. City-level check (Census BPS place totals)

450 California cities (early-reform places left out). Slope of the change in permits per 1,000 existing homes a year
(2023–2025 minus 2018–2022) on the share of a city's 2020 homes within ½ mile of a stop. Read the slope as "all homes
near transit vs none". BPS counts all units, including ADUs, unlike the point-based main outcome.

| Measure | Estimate | 90% range |
| --- | --- | --- |
| **Homes-weighted (headline for this check)** | **−1.734** | −3.135 to +1.719 |
| Equal weight per city | +12.602 | −0.132 to +33.057 |
| Lead placebo, homes-weighted (2021–2022 vs 2018–2020) | −0.658 | −2.265 to +1.804 |
| Lead placebo, equal weight | −1.719 | −4.527 to +0.871 |

As a count for the kept cities: about −11,226 homes over 2023–2025, range −20,300 to +11,129 (slope × homes within
½ mile ÷ 1,000 × 3 years). The range includes 0, so the plan's statewide-claim rule gives **no statewide "extra
homes" claim**. The equal-weight slope is driven by small cities and is very wide.

## 5. Checks on the main result

All homes other than ADUs; main group unless stated.

| Check | Estimate | 90% range | Jurisdictions |
| --- | --- | --- | --- |
| Rail-only map | −0.270 | −4.135 to +3.283 | 150 |
| Without planned stops (SCAG only) | −0.460 | −1.967 to +0.971 | 194 |
| Without land near 2018–2022 rail openings | −0.964 | −2.233 to +0.185 | 198 |
| HCD street-level points only (no Census re-geocodes) | −0.761 | −2.077 to +0.486 | 198 |
| Report-year dating | −0.259 | −1.645 to +0.970 | 198 |
| Entitlement-date dating | −0.562 | −1.169 to −0.028 | 198 |
| Drop 2023 | −0.602 | −2.208 to +0.807 | 198 |
| Drop Los Angeles | −0.998 | −2.526 to +0.484 | 197 |
| Stable-geocode jurisdictions only | −1.006 | −2.608 to +0.500 | 117 |
| Drop the largest project in each area and period | −0.876 | −2.201 to +0.329 | 198 |
| Equal weight per jurisdiction | +0.241 | −4.086 to +5.193 | 198 |
| **POST HOC:** without land within 150 m of the ½-mile line | −1.522 | −3.298 to +0.068 | 194 |

One of 11 planned checks excludes 0 (entitlement-date dating, by 0.028), in the same direction as the headline. Read
under the plan's symmetric rules, beside the other checks, it is not a finding on its own. The street-level-only
check uses its own full-reporter list; it gives the same 198 jurisdictions as the main group.

## 6. Distance bands and edges

| Comparison | Estimate | 90% range | Jurisdictions |
| --- | --- | --- | --- |
| 0–⅓ mile vs 1–1½ miles | −2.083 | −4.320 to −0.008 | 187 |
| ⅓–½ mile vs 1–1½ miles | +0.218 | −1.190 to +1.737 | 197 |
| ½–⅔ mile vs 1–1½ miles | −1.155 | −2.772 to +0.659 | 202 |
| Edge: ⅓–½ vs ½–⅔ mile, 25 m donut | +1.003 | −0.670 to +2.489 | 197 |
| Edge, rail-only map (land near other stops removed) | +2.608 | −1.489 to +6.498 | 132 |
| Edge, Palo Alto (rail-only map; project resampling) | −0.262 | −0.705 to +0.094 | 1 |

Each band and edge keeps only jurisdictions with homes in its own treated band, so the groups differ by row (187 to
202 jurisdictions; the ½–⅔ mile band has 202, more than the main group's 198). No edge shows a jump at the ½-mile line. The 0–⅓ mile band just excludes 0 on the negative side; the bands do not
form a pattern that steps at the line.

## 7. Affordable homes (descriptive only)

The plan reads these as descriptive only: the density-bonus and financing fields are filled unevenly across report
years (plan section 9). Same contrast and units as the headline.

| Outcome | Estimate | 90% range | Lead check (2021–22 vs 2018–20) |
| --- | --- | --- | --- |
| Homes in LIHTC-flagged projects of 5+ homes (D2) | +0.165 | −0.205 to +0.510 | +0.033 (−0.275 to +0.302) |
| Homes in LIHTC-flagged projects (D) | +0.173 | −0.195 to +0.521 | +0.022 (−0.287 to +0.290) |
| Deed-restricted homes, low income and below | +0.185 | −0.385 to +0.712 | +1.062 (+0.350 to +1.884) |
| Deed-restricted homes, moderate income | −0.100 | −0.205 to +0.013 | +0.025 (−0.183 to +0.272) |
| Deed-restricted homes, all | +0.085 | −0.460 to +0.607 | +1.087 (+0.376 to +1.952) |
| Homes in density-bonus projects (B) | +0.621 | −0.203 to +1.512 | +0.873 (+0.127 to +1.821) |
| A: density-bonus share of 5+ projects (share, 0–1) | +0.067 | +0.029 to +0.114 | |
| C: LIHTC share of 5+ projects with financing filled (share, 0–1) | +0.022 | −0.200 to +0.240 | |

- Tax-credit apartments near transit: no measurable change relative to the ring.
- Deed-restricted low-income homes and density-bonus homes were already rising near transit before 2023 (lead checks
  exclude 0), so their after-years are not evidence of cause.
- Share A rose, but the density-bonus field's reporting changed over the same years (share of 5+ rows with a bonus
  above 0: 0.9% in 2018 to 17.2% in 2025), so it is not read as real use.

Plain counts (main group, jurisdictions with land near transit only; the first version of this table also counted
ring land in places with no land near transit and showed ring 3,778 / 66 before and 2,762 / 45 after; homes in LIHTC-flagged projects of 5+ homes; raw totals, 5 before years vs 3 after years;
near and ring hold different numbers of homes, so compare zones only with the rate above):

| Area | 2018–2022 | 2023–2025 |
| --- | --- | --- |
| Near transit | 3,063 homes in 55 projects | 2,770 homes in 36 projects |
| Ring | 3,594 homes in 64 projects | 2,681 homes in 43 projects |

## 8. Data and caveats

- **Permit locations.** Rows without a precise HCD location rose from 2.4%–4.8% (2018–2022) to 8.7%, 17.4% and
  20.7% (2023–2025). The Census re-geocode accepted 11,197 rows; 10,552 of them remain after
  cleaning (the other 645 are duplicates across report years or fall outside 2018–2025 by issue date) and were used (accepted: 46% of rows sent for 2023, 30% for 2024, 7% for 2025). The street-level-only check gives the same reading.
- **POST HOC: where the unlocated homes are.** In 2025, 13.2% of homes in cities with land near transit were
  unlocated, against 26.7% in cities without (2024: 11.9% vs 13.6%). The main group only includes cities with land
  near transit.
- **Bus areas** use today's Caltrans layer (20-minute rule, adopted after 2024), which covers more land than the 2023
  rule; this blurs near and ring and pulls estimates toward 0. The rail-only map gives the same reading.
- **Planned stops** are mapped only for SCAG; elsewhere, land near 2022-era planned stops counts as ring.
- **Three after years** only; projects permitted in 2023 were mostly designed before the law.
- **Group bug in the first run.** The first run (commit ef67e9ca) let jurisdictions with no land near transit add
  ring land to the comparison. The plan (and the earlier test) keeps only jurisdictions with land near transit. The
  fix (d6d96c2d) gives the results above. First-run headline, labelled "first run, group bug": −0.855
  (−2.283 to +0.498), 360 jurisdictions. Same reading.
- **Earlier AB 2097 test** (October, corrected November 3): −0.75 (−2.27 to +0.66), all homes, 185 jurisdictions.
  This study's −0.942 (−2.330 to +0.319) for all homes is similar; the groups differ (198 vs 185 jurisdictions)
  and so do the maps and points.
- Tests for the estimate helpers (`tests/test_ca_ab2097.py`) were run with python directly; pytest is not installed.

## 9. Not yet run (side checks; spec fixed before this run)

City maps (Oakland Spring 2023, Truckee, Palo Alto and Santa Cruz rebuilt from PDFs), MTC 2017 maps, the dated 2022
bus map from web-archive schedules, National Transit Database service hours, and the streetcar check.

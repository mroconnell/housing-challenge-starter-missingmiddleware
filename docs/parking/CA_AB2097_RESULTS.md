# CA AB 2097: results (first full run, 2026-11-05)

Plan: [CA_AB2097_PLAN.md](CA_AB2097_PLAN.md) (locked 2026-11-05 16:48 UTC; changes after lock in section 9, all made
before any count unless marked post hoc). Code: `scripts/ca_ab2097_estimate.py` (run at d6d96c2d), post hoc checks
`scripts/ca_ab2097_posthoc.py`. Outputs: `reference/ca_ab2097_results*.csv`, `reference/ca_ab2097_posthoc_*.csv`.
Status: **audit reviewed 2026-11-05**.

Unless a row says otherwise, every number is **homes in issued building permits per 1,000 existing homes (2020 census)
per year**, 2023–2025 compared with 2018–2022, near transit (within ½ mile) compared with the ring (½ to 1½ miles) in
the same jurisdictions. Ranges are 90%, from 2,000 resamples of whole jurisdictions. The "MDE" column is the half-width
of the 90% range (1.645 × the spread of the resampled estimates), which gives only about 50% power: a true change of
that size would be detected about half the time. The usual MDE at 80% power is (1.645 + 0.842) × the spread at the
plan's two-sided 10% level; for the headline that is 2.01 homes per 1,000 existing homes a year (spread 0.808), or
2.26 at a two-sided 5% level.

## 1. Answer in brief

- **No measurable change.** Near transit, homes permitted (other than ADUs) changed by −0.905 per 1,000 existing
  homes a year relative to the ring, range −2.292 to +0.350. The range includes 0. The 90% range's half-width is 1.330
  (about 50% power); at 80% power the test could reliably detect a change of about 2.01 either way.
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
They hold 1,363,531 existing homes (2020) within ½ mile on the main map, outside LA's 2017 TOC areas; so 1 home per
1,000 existing homes a year near transit is about 1,364 homes a year.

| Measure | Estimate | 90% range | Half-width of 90% range (about 50% power) |
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

12 places that already had no parking minimums near transit (or repealed citywide) and have homes near transit:
Alameda, Berkeley, Culver City, Emeryville, Fremont, Hayward, Oakland, Sacramento, San Diego, San Francisco, San Jose
and Stockton. (Pomona and Eureka, also on the list, are not in the group: not full reporters or no homes near transit.)

| Measure | Estimate | 90% range |
| --- | --- | --- |
| Headline, homes other than ADUs | −2.291 | −3.926 to −0.284 |
| Lead slope, per year, 2018–2021 vs 2022 | −3.133 | −5.664 to −1.390 |
| Lead check: 2021–2022 vs 2018–2020 | −4.103 | −8.630 to −1.445 |

Under the locked rule this check fails (see section 1). These places' near-transit building was already falling relative to their rings before 2023 (lead check −4.103,
range −8.630 to −1.445), so their headline is not a clean placebo. Their range excludes 0, so the plan's placebo
condition fails. This says the near-vs-ring comparison can drift for reasons other than AB 2097
in early-reform cities (San Francisco, San Diego, Oakland and others). The main result stays "no measurable change", but with the placebo
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
  cleaning (of the other 645, 2 have a permit issue date outside 2018–2025 and 643 are removed as the same permit
  reported again in a later report year) and were used (accepted: 46% of rows sent for 2023, 30% for 2024, 7% for 2025). The street-level-only check gives the same reading.
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

## 9. Side checks (written after the main results were seen; they follow the spec fixed before the run)

Script `scripts/ca_ab2097_side_checks.py`; outputs `reference/ca_ab2097_side_city_maps.csv`,
`reference/ca_ab2097_side_ntd_bus_hours.csv`, `reference/ca_ab2097_side_mtc_licence.json`.

**City maps against our main map** (2020 homes; blocks by internal point; agreement = homes in both maps ÷ homes in
either). Edge = homes other than ADUs per 1,000 existing homes a year, 2023–2025 vs 2018–2022, 25–150 m inside vs
25–150 m outside the city's own line, 90% range from 2,000 resamples of projects.

| City | Role | Homes in city map | Homes in our map | Agreement | Edge on the city's line |
| --- | --- | --- | --- | --- | --- |
| Oakland (Spring 2023 layer, 15-minute rule) | placebo city | 126,788 | 148,602 | 82.9% | −1.548 (−15.749 to +14.639) |
| Sacramento (city layer) | placebo city | 104,311 | 58,396 | 53.7% | +0.482 (−6.214 to +7.537) |
| Truckee (Train Depot ½ mile) | main | 351 | 354 | 99.2% | −73.675 (−151.487 to +0.291); too few permits to read |
| Palo Alto (3 Caltrain stations, rebuilt from our station list, not the PDF) | main | 5,526 | 11,772 | 46.9% | −6.008 (−22.833 to +4.557); too few permits to read |
| Santa Cruz | main | pending: PDF stops need matching by hand | | | |

- Oakland's own 2023 map and ours overlap on 83% of the homes either one covers. Ours is a little wider, consistent
  with today's 20-minute bus rule.
- Sacramento's own layer covers far more homes than ours (104,311 vs 58,396); the city drew a wider area.
- In Palo Alto our map covers twice the city's rail circles because it adds today's bus major stops.
- Placebo cities: the plan's rule needs each placebo city's range to include 0. Oakland's (−15.749 to +14.639) and
  Sacramento's (−6.214 to +7.537) do, but the ranges are so wide that passing says little.
- No city-line edge shows a measurable change. Truckee and Palo Alto have only a few dozen permitted homes near their
  lines, so their ranges are very wide.

**Bus service, 2022 vs 2025** (National Transit Database; annual bus vehicle revenue hours, modes MB, RB and CB).
Almost every large California agency ran more bus service in 2025 than in 2022: for example LA Metro 6,114,098 →
6,931,450 hours (×1.13), AC Transit ×1.08, OCTA ×1.08, VTA ×1.08, SamTrans ×1.34, Omnitrans ×1.32, Santa Cruz Metro
×1.37; Muni ×1.04, San Diego MTS ×1.04, SacRT ×1.03. More service since 2022 adds to the 20-minute rule in making
today's bus layer cover more land than the 2023 rule did, which blurs near and ring.

**Dated 2022 bus map** (`scripts/ca_ab2097_bus2022.py`; web-archive schedule copies that run on 2022-12-14; 2023
15-minute rule; routes meeting within one agency's feed only; both peaks in the same direction). Four large agencies
had a qualifying copy; their today's bus major stops were replaced by their 2022 ones (by agency, not county: not in
the spec):

| Agency | Bus major stops, 2022 | Today | Both (within 150 m) | 2020 homes within ½ mile, 2022 | Today |
| --- | --- | --- | --- | --- | --- |
| LA Metro (copy of Feb 2023, schedule from 2022-12-12) | 1,682 | 3,867 | 1,516 | 919,782 | 1,263,141 |
| Muni (Dec 2022) | 759 | 2,419 | 661 | 378,764 | 395,251 |
| San Diego MTS (Nov 2022) | 323 | 826 | 208 | 177,413 | 213,315 |
| LADOT (Mar 2022) | 159 | 972 | 110 | 151,152 | 601,637 |

- These agencies' 2022 bus major stops cover fewer homes than today's layer. The gap mixes three causes that
  cannot be split here: the rule itself (15 vs 20 minutes), service changes since 2022, and this check's within-one-feed
  limit (for example LADOT DASH routes meeting LA Metro routes are not counted, likely a large part of LADOT's gap:
  151,152 vs 601,637 homes).
- **Headline with these 2022 stops:** −1.271 (−2.683 to +0.067), 196 jurisdictions; main headline −0.905
  (−2.292 to +0.350). Same reading.
- San Diego MTS's only qualifying copy uses calendar_dates only; no other MTS copy ran on 2022-12-14, so the copy
  choice does not matter.
- **Kept today's stops (no qualifying copy):** 43 agencies with 6,140 of today's bus major stops, the largest being AC
  Transit (1,503), VTA (747), Long Beach Transit (677), Foothill Transit (359), Santa Monica (291), OCTA (263), SamTrans
  (236), SacRT (164), Golden Gate (129) and Santa Cruz Metro (129); full list in
  `reference/ca_ab2097_side_bus2022_kept_today.csv`. Small rural feeds that qualified had no bus major stops.

**MTC 2017.** MTC's 2017 layers carry a planning-use disclaimer, not a licence (the 2017 major-stop item's metadata
could not be read). They fall under Ryan's 16:42 OK for unlicensed regional layers as research inputs; the Bay Area
comparison is not yet run.

## 10. Side checks that could not run, and what is left

- **Streetcar check:** the National Transit Database lists one California agency with streetcar service (mode SR):
  San Francisco (NTD 90015), which also runs light rail on the same system. No California system is streetcar-only,
  so the check is empty: there is no streetcar-only system to drop. (San Francisco is outside the main group anyway.)
- **MTC 2017 major transit stops:** the 2017 major-stop item linked from MTC's GitHub no longer exists or is not
  public: https://www.arcgis.com/sharing/rest/content/items/561dc5b42fa9451b95faf615a3054260 returned
  "Item does not exist or is inaccessible." (accessed 2026-11-05). MTC's other 2017 layers are corridors
  and priority areas, not major stops, so the spec's comparison cannot be run as written. Not run.
- **Santa Cruz:** its map is a PDF of circles around many bus stops; rebuilding it means matching each circle to a
  stop by hand. Not done (Ryan's call whether it is worth it).

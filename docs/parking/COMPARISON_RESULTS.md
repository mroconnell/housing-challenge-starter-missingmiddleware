# Parking: results of the repeal comparison (Gate 2)

Written 2026-10-26 by the parking conductor and revised the same day after an independent review. Plan: [COMPARISON_PLAN.md](COMPARISON_PLAN.md), with deviations 1–4 in its section 8. Status: for owner review. These are not yet Gate 3 numbers.

**Terms used here**
- *Repeal place*: a US city, village or town that removed minimum parking requirements for all housing.
- *Comparison places*: similar places in the same state that did not.
- *Effect*: how much a repeal place's permit rate changed, minus how much its comparison places' rate changed over the same years. The unit is permits per 1,000 existing homes per year.
- *Likely range*: the 5th to 95th percentile of the average, from re-drawing the sample of places 2,000 times.

## Answer

**In the three years after US places removed parking minimums for all housing, their permit rates did not rise measurably compared with similar places that kept them.**
- **Average:** the effect averaged −1.18 permits per 1,000 existing homes per year across 24 repeal places, weighting each place by its number of homes. The likely range is −3.57 to +2.21, so it includes zero.
- **Direction:** 10 of the 24 places rose faster than their comparison places, and 14 rose slower.
- **Apartments** (units in buildings of 2+ units): −1.67 per 1,000 homes per year, with a likely range of −3.70 to +1.06. 9 of 24 places rose.
- **City types:** no size cut-off (10,000, 20,000, 50,000 or 100,000 people) predicted places left out of the fit better than one average. A smooth model using city size and metro setting predicted 5% better: an average error of 4.65 against 4.90 permits per 1,000 homes per year. But the likely range of each of its two terms includes zero. So we use one average (deviation 3).

## Checks on the average (`reference/parking_comparison_robustness.csv`)

All rows are all units, in permits per 1,000 existing homes per year.

| Check | Places | Effect | Likely range |
| --- | ---: | ---: | --- |
| Main result (weighted by homes) | 24 | −1.18 | −3.57 to +2.21 |
| Unweighted average | 24 | +0.69 | |
| Median place | 24 | −0.50 | |
| Without San Francisco (25% of the weight) | 23 | −0.48 | −3.77 to +3.11 |
| Without the two small Texas places | 22 | −1.28 | −3.61 to +1.74 |
| Only places that did not rewrite their zoning at the same time | 6 | −3.54 | −4.79 to −2.54 |
| Including the 6 "repeal with conditions" places | 30 | −1.00 | −3.28 to +1.84 |
| Leaving out one state at a time | 20–23 | from −2.47 (no North Carolina) to +0.09 (no Minnesota) | |

The answer does not depend on one place or one state. Every version is near zero or below it. The 6 places that repealed without a wider rewrite all fell against their comparison places, mostly because of San Francisco, Lexington and Cambridge MA.

## The sample

| Step | Places |
| --- | ---: |
| Places PRN rates as removing minimums for all housing, adopted 2015–2022 | 46 |
| Not found in the Census permit place files (Wilmington NC, South Bend, Sandusky city and 3 Michigan villages) | −6 |
| Ordinance check: weaker than PRN says (Norman, Maumee, Camden), minimums restored in the after period (Central Falls), or no minimums before either (Chattahoochee Hills) | −5 |
| Too recent once the effective date was used (San Jose, Anchorage), or missing permit years (Gastonia, Avondale Estates, Calumet) | −5 |
| **Included** | **30** |
| of which removed minimums with conditions (reported separately, not pooled) | 6 |
| **Main sample** | **24** |

Wilmington NC was also rated weaker by the ordinance check. It is counted once, as not found. PRN is the Parking Reform Network database the classification starts from.

Files: `reference/parking_comparison_effects.csv` (each place's before and after rates, comparison places and effect), `reference/parking_comparison_models.csv`, `reference/parking_comparison_estimates.csv`, `reference/parking_repeal_checks.csv`. Script: `scripts/run_parking_comparison.py`.

## Points to note

- **West Allis, the in-state case, rose.** It permitted 2.63 units per 1,000 homes per year in 2017–2021 and 7.49 in 2023–2025. Its 21 comparison places in Wisconsin, of 30,000–120,000 people, went from 5.32 to 5.84. So its effect is +4.34, or +3.95 for apartments. The repeal came with a complete new zoning code, so this cannot be credited to parking alone.
- **Big cities mostly fell against their comparison places:**
  - San Francisco −3.28 (repealed 2019);
  - Minneapolis −8.52 (2021);
  - Lexington −5.08 (2022);
  - St. Paul −2.22 (2021).

  Raleigh (2022) rose by +7.04, Bridgeport (2021) by +5.95 and Gainesville (2022) by +5.21. Places of 50,000+ people averaged −1.26 (7 of 16 rose). Places under 50,000 averaged +1.40 (3 of 8 rose).
- **Small places swing widely.** Bastrop TX rose by +30.65 and Ecorse MI fell by −13.05. Each has a few thousand homes, so each carries little weight.
- **Places that removed minimums with conditions:** Buffalo +0.48, Windham +8.39, Cambridge MD −6.68, Branson +3.16, Canandaigua +2.76, Seabrook −1.92.

## A second check: California's AB 2097 (added 2026-10-27)

The TOD thread ran a separate, pre-registered test of California's AB 2097 ([AB2097_TEST_RESULTS.md](../tod/AB2097_TEST_RESULTS.md)), with the parking thread's amendments. AB 2097 removed parking minimums within ½ mile of major transit stops from 1 January 2023.

- **Method:** permits within ½ mile of a stop are compared with permits ½ to 1½ miles away, in 185 jurisdictions that had not already removed minimums or raised density near transit.
- **All units:** +0.13 permits per 1,000 existing homes per year, with a 90% interval from −1.84 to +1.73 (resampling jurisdictions).
- **Units in buildings of 2 or more units:** +0.39 (−1.37 to +1.89).
- **Reading:** this is no measurable change, which agrees with the city-repeal result.
- **Caveats:**
  - the stops come from today's transit map, not one from before 2023;
  - the comparison ring itself rose against land farther away (+2.58, interval +1.58 to +3.61), which could pull the estimate down.
- **Use:** it is reported as supporting evidence, and does not change any parking number.

## Limitations

- **Zoning rewrites:** 18 of the 24 places repealed parking minimums as part of a wider zoning rewrite, so parking's own effect cannot be separated out.
- **Census estimates fill gaps:** some places' permit years are fully estimated by Census, not reported. That covers Hartford's whole after period, Roanoke's whole before period, and some years for Lexington, Gainesville, Cambridge MA and Hudson. In the independent review, run before the population fix (deviation 4), leaving the six out moved the average only from −1.29 to −1.20.
- **State laws overlap:** California's AB 2097 and Oregon's transit-area parking rules (both 2023) also cut parking for some comparison places, in the cases of Alameda, Culver City, Emeryville, Tigard and Corvallis. That pulls those places' effects toward zero.
- **New York towns:** their permit counts cover the town outside its villages, but the home counts include the villages.
- **Short window:** three years after the repeal. Larger projects can take longer to reach a permit.
- **Self-selection:** the places chose to repeal.

## What this means

This fits the other evidence:
- in Buffalo, stand-alone apartment buildings still built more parking than the old minimum;
- Ryan's point (AQ-046): where low-parking development is seen as risky, developers keep building parking.

Over three years, a repeal has not produced a measurable rise in permits.

## Owner decision (2026-10-26)

Option A, accepted "if necessary":
- the central case is no measurable change;
- the upper case is the high end of the likely range;
- there is no case below zero, because a repeal never subtracts.

The numbers it implies are in the [Gate 2 packet](GATE2_PACKET.md).

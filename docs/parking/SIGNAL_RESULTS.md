# Parking: turning noise into signal, results (quick passes)

Written 2026-11-01 by the parking conductor. Plan: [SIGNAL_PLAN.md](SIGNAL_PLAN.md). Scripts: `scripts/run_parking_signal.py` and `scripts/run_parking_increases.py`. Files: `reference/parking_signal_groups.csv` and `reference/parking_increases_effects.csv`.

## 1 and 3: booming vs cooling markets, and project size

There is no clearer signal. The unit is permits per 1,000 existing homes per year, as a home-weighted average with its 90% resampling range.

| Group | Places | Average | 90% range | Median |
| --- | ---: | ---: | --- | ---: |
| All | 76 | −1.14 | −3.42 to 1.45 | −0.12 |
| Booming market | 38 | −1.03 | −3.95 to 2.00 | −1.27 |
| Cooling market | 38 | −1.23 | −4.46 to 2.98 | 0.97 |
| Sunbelt | 20 | −1.20 | −6.72 to 5.48 | 0.55 |
| Rest of the country | 56 | −1.11 | −2.66 to 0.75 | −0.22 |
| Homes in 2+ unit buildings | 76 | −1.17 | −2.89 to 0.83 | −0.03 |
| Homes in 1-unit buildings | 76 | 0.03 | −0.74 to 0.76 | 0.18 |
| Share in 2+ unit buildings (percentage points; 4 places with no homes in a period left out) | 72 | −0.83 | −5.53 to 3.47 | −1.43 |

Booming and cooling are defined from the comparison places' own change, which is part of the effect. That builds in a small bias (correlation −0.15) toward finding a booming-market gain; none appeared. The 2+ unit × booming/cooling rows in the CSV are unplanned.

## Parking increases

Cities that raised minimum parking for multi-family housing, citywide or near transit, with permit data:

| City | Year | What changed | Before | After | Effect (positive = more permits after the increase) | Comparison places |
| --- | --- | --- | --- | --- | ---: | ---: |
| Kirkland, WA | 2015 | Minimums raised for most buildings, plus 15% cushion and 10% guest parking; several projects cancelled by 2017 | 2012–2014 | 2016–2018 | +14.18 | 21 |
| Portland, OR | 2013 | Minimums reinstated near transit for buildings over 30 units; undone from 2018 | – | – | not measurable (permit files start in 2012) | – |
| Lake Havasu City, AZ | 2023 | Multi-family minimums restored to pre-2016 levels, citywide | 2018–2022 | 2024–2025 | −7.77 | 19 |
| North Miami Beach, FL | 2023 | Multi-family minimums raised citywide, plus guest parking | 2018–2022 | 2024–2025 | +12.09 | 81 |

Also found but not counted:
- Denver 2016, a moratorium on no-parking small-lot buildings (partial);
- Olympia 2023, mixed (minimums removed in some areas, raised in others);
- Philadelphia 2016/2018, a bill that was not passed;
- Mankato 1996, before our permit data.

**Reading.** There are fewer than 5 cases, so per the plan this is a list, not an estimate.
- Two of the three measurable increases were followed by more permits, not fewer. Projects already in the pipeline are usually exempt from a new rule, and the market dominates.
- Lake Havasu's drop fits a parking effect, but it rests on 2 years.

This is the same lesson as the repeals: permit counts move with the market more than with parking rules.

**From the literature:**
- Oakland's 1961 increase to one space per unit is the classic case (Bertha, cited by Shoup). It was followed by about 30% fewer units per project and lower densities.
- New York (Manville 2013): 10% higher minimums go with 6% lower housing density.

## 8. California's 2023 law (AB 2097)

This has already been measured, by the TOD thread ([docs/tod/AB2097_TEST_RESULTS.md](../tod/AB2097_TEST_RESULTS.md)), with permits through 2025 (2018–2022 before, 2023–2025 after). It compares permits within ½ mile of major transit with a ½–1½ mile ring, across 185 California jurisdictions that had no earlier local repeal.

**Result: no measurable change.** The effect is +0.13 permits per 1,000 existing homes per year, with a 90% range of −1.84 to +1.73. Per acre it is +0.004 homes per acre per year (−0.006 to +0.011). It is already one of the parking tool's sensitivity cases: combined with the 76 repeal places, the high end becomes 15,138. No new run is needed. When 2026 permits are published (spring 2027), a 4-year after-period can be added.

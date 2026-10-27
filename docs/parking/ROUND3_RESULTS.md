# Parking: third round of variables. Results

Written 2026-10-27 by the parking conductor. Plan: [ROUND3_PLAN.md](ROUND3_PLAN.md), with the additions in its section 7. Scripts:
- `scripts/build_parking_round3_vars.py`
- `scripts/build_parking_transit_share.py`
- `scripts/build_parking_surface_lots.py`
- `scripts/run_parking_round3.py`

Outputs: `reference/parking_round3_*.csv`, `reference/parking_old_minimums.csv`, `reference/parking_transit_share.csv` and `reference/parking_surface_lots.csv`.

## Answer

**Nothing passed.** None of the 21 variables predicted places left out of the fit at least 5% better than one average, and none of the four tools did either. One average stays.

The 21 variables:
- the old parking minimum, for apartments and for houses;
- transit share, island size and surface parking;
- car ownership and commuting;
- 13 more from data in hand.

The old minimum, which was the strongest idea in theory, made predictions worse, not better: 9% worse for apartments and 7% worse for houses.

## What was tested (71 US repeal places)

"Gain" is how much the variable cut the left-out prediction error, against one average for all places. A variable needed 5% or more, and a slope whose 90% interval excludes zero.

| Variable | Places | Gain | Slope (90% interval) |
| --- | ---: | ---: | --- |
| Old minimum, spaces per apartment | 52 | −9% | −2.27 (−10.37 to +5.81) |
| Old minimum, spaces per house | 50 | −7% | −0.09 (−5.56 to +4.75) |
| Renter share | 71 | −3% | |
| Vacancy rate | 71 | −3% | |
| Share of homes built before 1960 | 71 | −6% | |
| Share of homes in buildings of 5+ units | 71 | +3% | −20.0 (−35.8 to −1.8) |
| Share of permits in 5+ unit buildings before repeal | 68 | +2% | −5.4 (−9.8 to −0.2) |
| Construction value per unit | 68 | −1% | |
| Permit volatility before repeal | 68 | −3% | +7.3 (+1.1 to +14.5) |
| Repeal year | 71 | −3% | |
| Earlier partial reform | 71 | +3% | −5.1 (−8.3 to −0.5) |
| Zoning rewrite at the same time | 71 | −5% | |
| Share of the state's large cities already repealed | 70 | 0% | |
| Census region | 71 | −3% | |
| Share of homes within ½ mile of any transit stop | 70 | −3% | |
| Share of land in surface parking (OpenStreetMap) | 71 | −1% | |
| Share of parking in large contiguous sites (2+ acres) | 71 | −8% | |
| Island size (largest continuous transit-covered patch) | 71 | −3% | |
| Households with no car (follow-up) | 71 | −2% | |
| Workers commuting by transit (follow-up) | 71 | +2% | |
| Mean commute time (follow-up) | 71 | −1% | |

**Tools using all 31 variables together**, change in left-out error against one average: weighted regression −101%, lasso +1.4%, random forest −12%, causal forest −3%. Lasso came closest, but its 1.4% gain is well below the 5% threshold.

**California check** (154 cities near transit) for renter share, vacancy, building age and share of homes in 5+ unit buildings: all four made predictions worse, by 1–3%.

## What the near-misses suggest

Four slopes have 90% intervals that exclude zero, and they tell a consistent story. Places that already had many apartments, already permitted apartments, or had already partly cut their minimums gained **less** from a full repeal. That fits the idea that minimums bind least where earlier reforms or existing density had already loosened them.

None of them improves predictions for places left out of the fit, so they are a pattern on average, not a way to set Wisconsin places apart.

**Island size here is wider than TOD's version.** The parking measure counts any transit stop at ½ mile, because service frequency is not available nationally. TOD's version uses ½ mile of rail and rapid-transit stations plus ¼ mile of 15-minute bus stops. Its result will be reported alongside when TOD's run finishes.

## Limits

- **Old minimum:** found for 52 places (apartments) and 50 places (houses). A third of the values are low confidence, and some Oregon places' old codes had already been overridden by the state's 2022 rules.
- **Surface parking:** comes from OpenStreetMap (ODbL), whose coverage varies by place.
- **Transit share and island size:** count any stop, so "near transit" is broad.

## What it means

Across three rounds, more than 30 variables and five tools have been tested. None of them tells apart the places where repeal raised permits from those where it didn't. The parking scenario keeps one average for every place:
- central case: no measurable change;
- high end: +1.54 permits per 1,000 existing homes per year, about 20,672 over 2027–2031.

TOD is running a wider all-variables test with 60–100 Census variables. Its note applies here too: the limit is the number of places, not the number of variables. With 71 places, adding more variables would mostly add chance patterns.

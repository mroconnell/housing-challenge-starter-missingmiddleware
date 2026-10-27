# Parking: expanded comparison and prediction tools. Results

Written 2026-10-27 by the parking conductor. Plan: [EXPANDED_PLAN.md](EXPANDED_PLAN.md), with the change in its section 7 made before any outcome was computed. Script: `scripts/run_parking_expanded.py`. Outputs: `reference/parking_expanded_{match,effects,estimates,tools}.csv`.

## Answer

- **More data narrowed the high end.** The sample grew from 24 to 71 US places. The average effect barely moved: −1.10 permits per 1,000 existing homes per year, against −1.18 before. The 90% range tightened at the top, from +2.21 to +1.54. For Wisconsin, that would lower the "High end of the evidence" from 29,662 to about 20,672 extra permits over 2027–2031.
- **No prediction tool helped.** On places left out of the fit, none of these tools beat one average for all places:
  - a weighted regression on all traits;
  - lasso;
  - a random forest;
  - an honest causal forest.

  All four predicted worse, in both the US places and the California cities. So the evidence still supports one average for every place.

## The sample

177 places were checked against their ordinances (the first 46 and 131 more). 74 had a usable repeal, and 71 had the permit data needed.

| Dropped | Places |
| --- | ---: |
| No repeal date found | 33 |
| Ordinance check: weaker than the benchmark | 27 |
| No minimums before either (no repeal event; listed in the plan) | 20 |
| Repeal year outside 2015–2024 | 15 |
| Not found in the Census permit files | 6 |
| Minimums restored within 3 years | 2 |
| Missing permit years | 3 |

- **After-years:** of the 71 places, 34 have 3 after-years, 19 have 2 and 18 have 1.
- **Direction:** 36 of 71 rose faster than their comparison places.
- **Rating:** 57 removed minimums for all housing; 14 removed them with conditions.

## Estimates (permits per 1,000 existing homes per year; 90% range)

| Case | Places | Effect | Range |
| --- | ---: | ---: | --- |
| **Expanded, all units (headline candidate)** | 71 | −1.10 | −3.50 to +1.54 |
| Expanded, units in buildings of 2+ units | 71 | −1.09 | −2.89 to +0.94 |
| Removed for all housing only | 57 | −1.35 | −4.03 to +1.60 |
| Places with 3 after-years only | 34 | −0.92 | −3.10 to +1.88 |
| Without a zoning rewrite at the same time | 23 | −1.23 | −2.83 to +1.17 |
| Without San Francisco | 70 | −0.78 | −3.48 to +2.08 |
| The first 24 places, recomputed here | 24 | −1.18 | −3.59 to +1.97 |
| California AB 2097 near transit (TOD test) | 185 | +0.13 | −1.84 to +1.73 |
| US and California combined, by precision (sensitivity) | 256 | −0.28 | −1.74 to +1.17 |

The first 24 places give a high end of +1.97 here, against +2.21 in the first run. The point estimate is the same; only the resampling draws differ. So the high end itself carries roughly ±0.2 of resampling noise.

## Prediction tools

Each tool's average error on left-out places is compared with one average. A negative gain means the tool did worse.

| Tool | US places (71) | California cities (154) |
| --- | ---: | ---: |
| One average | 5.08 (benchmark) | 9.15 (benchmark) |
| Weighted regression, all traits | −22% | −5% |
| Lasso | −10% | −2% |
| Random forest | −18% | −4% |
| Causal forest (honest) | −3% | −1% |

Ten traits went in: home value, income, home value relative to income, density, single-family share, land area, population, metro setting, rent, and the permit rate before repeal. California's test used the six traits it shares with the US data, plus the number of homes.

## What this means for the tool (decision for Ryan)

| Option | High end, 2027–2031 | Basis |
| --- | ---: | --- |
| **A (recommended): update to the expanded sample** | about 20,672 | 71 places; +1.54 per 1,000 homes per year |
| B: keep the current figure | 29,662 | 24 places; +2.21 |
| C: combine with California | about 15,740 | 71 US places and 185 California cities; +1.17. A transit-area law mixed with citywide repeals, so not recommended as the headline |

The central case stays at 0 ("No measurable change") under every option.

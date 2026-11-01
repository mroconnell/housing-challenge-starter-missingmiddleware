# Parking: adjusting for local boom and bust, and longer windows, results

Written 2026-11-01 by the parking conductor. Plan: [TRAITS_ADJUST_PLAN.md](TRAITS_ADJUST_PLAN.md). Scripts: `scripts/fetch_parking_traits.py` and `scripts/run_parking_traits_adjust.py`. Files: `reference/parking_traits_*.csv`.

## Answer

- **The local traits explain almost none of the city-to-city swings.** On held-out states, R² was −0.08 for the weighted regression and 0.08 for the random forest. The traits are county job growth, pay growth, the state's change, car ownership, transit commuting, the before-rate and size.
- **Adjusted for them, the repeal average barely moves.** It is −1.22 with the regression and −1.42 with the forest, against the headline −1.14, and both sit inside the noise.
- **Longer windows show no delayed gain.** Years 4–6 after repeal are more negative, but they rest on 11 to 25 places and are dominated by San Francisco and Minneapolis.

## A. Traits-adjusted effect

The unit is permits per 1,000 existing homes per year: the actual change minus the change predicted from traits. Each row is a home-weighted average with its 90% resampling range, and the median.

| Model | Group | Places | Average | 90% range | Median |
| --- | --- | ---: | ---: | --- | ---: |
| Regression | Repeal places | 72 | −1.22 | −3.76 to 1.40 | 0.21 |
| Regression | Without San Francisco | 71 | −0.65 | −3.42 to 2.04 | 0.26 |
| Regression | Without SF and Minneapolis | 70 | −0.23 | −3.14 to 2.55 | 0.28 |
| Forest | Repeal places | 72 | −1.42 | −3.04 to 0.49 | −0.74 |
| Forest | Without San Francisco | 71 | −1.04 | −2.88 to 0.99 | −0.74 |
| Forest | Without SF and Minneapolis | 70 | −0.74 | −2.61 to 1.49 | −0.65 |

**Noise check.** 72 never-reformed places are drawn at random with the real years, over 5 seeds.
- Regression averages: −1.46, +1.22, −1.45, −1.39 and +2.38.
- Forest averages: −0.97, +0.57, −0.94, −2.62 and +1.23.

So the repeal averages are within what random places show.

| City | Change | Predicted from traits (regression / forest) | Adjusted (regression / forest) | Headline |
| --- | ---: | --- | --- | ---: |
| San Francisco | −4.24 | +0.75 / −0.29 | −4.99 / −3.95 | −3.28 |
| Minneapolis | −7.18 | −1.35 / −2.42 | −5.83 / −4.76 | −8.52 |
| Austin | −15.32 | −1.46 / −6.10 | −13.86 / −9.22 | −12.33 |
| San Jose | +2.36 | −2.22 / −0.74 | +4.58 / +3.10 | +2.48 |
| Raleigh | +7.43 | +5.92 / +10.74 | +1.50 / −3.31 | +7.04 |

The traits do not predict San Francisco's or Minneapolis's drops, so the drops remain unexplained.

## B. Effect by year since repeal (headline comparison places)

| Years after repeal | Places | Average | Median |
| ---: | ---: | ---: | ---: |
| 1 | 75 | −0.83 | −0.29 |
| 2 | 57 | −1.12 | 0.02 |
| 3 | 37 | −2.13 | −1.17 |
| 4 | 25 | −5.76 | −1.64 |
| 5 | 15 | −4.46 | −1.69 |
| 6 | 11 | −2.84 | −0.90 |
| 7 | 6 | 0.18 | 0.32 |

- **Years 4–6 are driven by San Francisco** (−7.7, −7.8, −5.4 in 2023–2025) and Minneapolis (−15.9 in 2025).
- The other long-window places (Buffalo, Hartford, Dunwoody, Branson, Windham) range from −4.3 to +8.4.
- There is no sign of a delayed gain. These windows are described only; 6 to 25 places cannot support an estimate.

## Notes

- **Transit:** agency ridership (the National Transit Database) is reported by agency, not city. The ACS share of workers commuting by transit stands in for it.
- **Car ownership and transit share** come from the ACS 2015–2019 release, before most repeals.
- **County job and pay growth** cover the same before and after years as the permits, so they describe what happened at the same time. This explains past changes; it is not a forecast.

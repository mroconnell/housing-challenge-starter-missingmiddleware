# Parking: near-transit areas that never reformed, results

Written 2026-10-28 by the parking conductor. Plan: [NEAR_TRANSIT_PLACEBO_PLAN.md](NEAR_TRANSIT_PLACEBO_PLAN.md), committed before counting. Script: `scripts/run_parking_near_transit_placebo.py`. Outputs: `reference/parking_near_transit_placebo_units.csv`, `reference/parking_near_transit_placebo_results.csv`.

All figures are extra homes per 1,000 existing homes per year, on a permit footing (census counts divided by 0.86). Each area is measured as its change in change: its 2010s gap against the rest of its city, minus its 2000s gap.

## Answer

- **The "fast growers slow down" pattern is the same without a reform.** The weight on prior gap is −0.82 in 1,040 non-reform station areas and −0.69 in the 36 reform areas.
- **Compared with areas like them, the reform areas did better.** Near-transit areas with the same prior gap and size gained +18.8 more in reform cities (90% range +9.3 to +28.2). This is the first parking result in this work whose range excludes zero against a placebo comparison.
- **Seattle drives it,** with 60,039 of the 76,952 reform-area homes. The result rests on Seattle's villages continuing to grow fast instead of slowing down as other fast growers did.

## Areas

1,040 rail station areas in 469 cities in 11 states, with 3,737,951 homes in 2010. New York has 71% of those homes. The reform areas are Seattle's 24 urban villages and Minneapolis's 12 rail station areas.

## Tests

| Test | Result |
| --- | --- |
| 1. Weight on prior gap, non-reform areas | −0.82 |
| 1. Weight on prior gap, reform areas | −0.69 |
| 2. Parking effect, same prior gap and size | **+18.8 (+9.3 to +28.2)** |
| 3. Non-reform model predicting reform areas: average predicted / actual | −18.1 / +0.8 |
| 3. Its prediction error, compared with one average | 25.4 / 25.9 |

## Checks added after the result (not in the plan)

| Check | Parking effect | 90% range |
| --- | ---: | --- |
| Main | +18.8 | +8.9 to +27.3 |
| Without New York | +19.9 | +10.4 to +29.6 |
| Seattle as the only reform city | +19.8 | +9.1 to +29.5 |
| Minneapolis as the only reform city | +15.7 | −2.3 to +43.6 |
| Each area weighted equally | +24.5 | +4.7 to +47.4 |
| Non-reform areas with prior gaps in the reform areas' range only | +18.3 | +9.5 to +27.3 |
| No adjustment for prior gap or size | +3.9 | — |

(These checks used 1,000 draws with seed 1, so the main row's range differs slightly from the table above.)

## Reading

- **The result depends on the prior-gap adjustment.** Reform areas outgrew their cities by +29.0 in the 2000s, against +7.1 for non-reform areas. Unadjusted, the difference is only +3.9.
- **Seattle's villages were the city's planned growth areas.** Light rail, upzoning and a jobs boom came in the same years, so parking cannot be singled out.
- **Applied to Wisconsin, it would raise the high end, not lower it.** +18.8 on 299,570 homes near major transit stops for five years is about 28,000 permits. That is more than the current high end and more than the citywide evidence supports.
- **Not adopted.** It needs Ryan's decision. The parking conductor's recommendation is to report it as the strongest evidence of a near-transit effect and to keep the tool's range.

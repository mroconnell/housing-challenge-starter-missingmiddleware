# Parking: which city traits explain the effect? Results

Written 2026-10-27 by the parking conductor. Plan: [TRAITS_PLAN.md](TRAITS_PLAN.md), written and committed before any trait was joined to an effect. Script: `scripts/run_parking_traits.py`. Results: `reference/parking_traits_results.csv`.

## Answer

**No trait passed.** None of the six traits predicted the effect of removing parking minimums better than one average in both datasets. So the evidence does not support modelling types of city differently, or narrowing the range by city type.

## Data

- **A. US repeal places:** 30 places, all with traits. Effect: permits per 1,000 existing homes per year against comparison places.
- **B. California AB 2097 near transit:** 154 of the 156 city jurisdictions with permits in both periods, matched to Census places by name. Paso Robles and Ventura did not match. County jurisdictions were left out, as recorded in the plan before testing. Effect: each jurisdiction's own near-transit change against its ring.

## Results

"Gain" is how much the trait cut the left-out prediction error compared with one average. A trait needed 5% or more in both datasets, with the same direction in both.

| Trait | Gain A | Gain B | Slope direction A / B | Passes |
| --- | ---: | ---: | --- | --- |
| Median home value (relative to the state) | 0% | −2% | − / − | No |
| Median household income (relative to the state) | −3% | 0% | − / − | No |
| Homes per square mile | +6% | −1% | − / − | No |
| Share of homes that are single-family detached (a stand-in for lot size) | −7% | −3% | + / + | No |
| Land area | −11% | −3% | + / + | No |
| Home value relative to income | +1% | −1% | − / + | No |

Two near-misses, reported so they are not over-read:
- **Density** helped in the US repeal places (+6%), where denser places did slightly worse, but not in California.
- **Income:** in California, higher-income jurisdictions had lower effects. The 90% interval of that slope, −15.6 to −1.5, excludes zero. But it did not improve predictions for left-out jurisdictions, so it is a pattern on average, not a way to tell places apart.

## What it means

The wide range comes from the effect varying from place to place for reasons these traits do not capture: which projects happened to be in the pipeline, local lenders, interest rates, and the zoning rewrites that came with most repeals. The tool keeps one average for every place, and its "How sure" screen can now say the traits were tested.

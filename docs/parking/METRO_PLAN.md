# Parking: compare each repeal city with its own metro neighbours, plan written before running

Written 2026-11-01 by the parking conductor. Ryan approved idea 7 ("Yes"). The question: is the dip seen in San Francisco and Minneapolis a regional market swing? If a repeal city is compared with the other places in its own metro area, a regional swing cancels out. No result below has been computed before this file was committed.

## Method

- **Same as the headline comparison** (76 places, permits per 1,000 existing homes per year, the Census estimate columns, the same before and after years), except for the comparison places.
- **Comparison places:**
  - every other permit-issuing place in the same metro area (the Census CBSA code in the permit file) with at least 1,000 homes and every year present;
  - widened to the combined statistical area (CSA) if there are fewer than 5;
  - if there are still fewer than 5, the place is reported but left out of the metro average.
  - Places with a dated, apartment-scale repeal (V7 coding) on or before the end of the after-window are left out of the comparison, as are undated ones and the other repeal cities.
- **Comparison rate:** permits summed over the comparison places ÷ their homes summed (as now).

## Reported

- The home-weighted average with its 90% range (2,000 resamples), the median, and the number of places, set beside the headline (−1.14).
- The same without San Francisco, and without San Francisco and Minneapolis.
- San Francisco's and Minneapolis's own effect under both comparisons, with their metro comparison rates before and after.
- **Noise check:** the same metro comparison for 76 never-reformed places drawn at random with the real repeal years (5 seeds), giving the spread of the average when nothing happened.

## Use

- If the average moves toward 0 and San Francisco's effect shrinks, the regional theory is supported, and the low line can be narrowed (Ryan's call).
- The tool does not change from this run.

## Changes after writing

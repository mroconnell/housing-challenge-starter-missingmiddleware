# Parking: a census-only route, plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request: explore "a route that is purely based on census counts to see if it tells a clearer or different story", pro-rating "for how many years of the decade were under the effect of the reform". No census count for any repeal or comparison place has been tabulated for this purpose before this file was committed. Changes go in the last section with a date and a reason.

## 1. Question

Measured only with decennial census home counts, did places that removed parking minimums gain more homes over the decade than similar places that did not, in proportion to how long the repeal was in effect?

## 2. Data

All Census Bureau, public domain, fetched by script.
- **Homes:** Census 2010 blocks with housing counts (TIGER/Line 2010 POPHU) and Census 2020 blocks (TIGER/Line 2020, HOUSING20). Both years' blocks are placed in 2020 place boundaries by internal point, as in the census-count check ([SALVAGE_RESULTS.md](SALVAGE_RESULTS.md)) and TOD's Salt Lake City work.
- **Population for matching:** 2010 block population (POP10), summed the same way.

## 3. Places

- **Repeal places:** every citywide repeal at or near the benchmark in the current comparison (76 places, plus the 2008–2013 small towns that were dropped for lack of permit years), whose repeal took effect before 1 April 2020.
- **Comparison places:** places in the same state with ½–2× the repeal place's 2010 population. Places with any citywide parking-minimum removal in the Parking Reform Network data are left out.
- **Size:** the main sample is places with at least 2,500 homes in 2010. The census-count check showed that below that size the census change is mostly demolitions and removed mobile homes, not new building. Smaller places are reported separately.

## 4. Pro-rating and estimate

- **Exposure:** the share of the decade from 1 April 2010 to 1 April 2020 that the repeal was in effect, from the effective date, or the adoption date if there is none (1 July when only a year is known). A repeal before April 2010 has exposure 1.
- **Growth:** (homes 2020 − homes 2010) ÷ homes 2010 × 1,000 ÷ 10, in homes added per 1,000 existing homes per year.
- **Difference:** the repeal place's growth minus the home-weighted growth of its comparison places.
- **Effect per year of repeal:** if a repeal raises growth by δ in each year it is in effect, the difference equals δ × exposure. δ is estimated across repeal places by weighted least squares through the origin, weighted by 2010 homes: δ = Σ w·e·d ÷ Σ w·e².
- **To compare with the permit route:** δ is also shown multiplied by 1 ÷ 0.86, the ratio of census change to permits in the census-count check (all places summed). This gives a rough permit-equivalent.
- **90% range:** 2,000 bootstrap draws of repeal places.
- **Placebo:** 500 sets of never-repealed places, each matched to a real repeal place (same state, ½–2× population) and given its exposure. δ is computed for each set, and the real δ is placed in that distribution.

## 5. Also reported

- δ for the small places on their own.
- δ for the places whose repeal took effect from 2015 on, for which a permit-route effect exists, side by side with that effect.
- **Transit-area reforms with a known area, as a block-level check:**
  - Seattle's 2012 urban villages against the rest of the city, with exposure 0.76;
  - Salt Lake City's 2010 station areas, cited from TOD's results, not rerun.

## 6. Use

This is a second route. If it gives a clearer answer than the permit route (a 90% range that excludes zero, and a placebo share under 5% or over 95%), the result goes to Ryan with a recommendation. It does not change the tool by itself.

## Changes after writing

# Parking: near-transit areas that never reformed, plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request ("sure", answering whether to run this check). The 10%-per-region test found that models predict held-out reform areas well, mainly because areas that outgrew their surroundings before the reform outgrew them by less afterwards ([NEAR_TRANSIT_PREDICT_RESULTS.md](NEAR_TRANSIT_PREDICT_RESULTS.md)). This check asks whether the same happens near transit without a reform. No figure for the areas below has been computed before this file was committed.

## Areas without a reform

- **Where:** the states with TOD's 2000, 2010 and 2020 block counts: AZ, CA, IL, MN, NC, NJ, NY, PA, TX, UT, VA and WA.
- **Which cities:** 2020 census places with at least one National Transit Map rail station.
- **Cities left out:**
  - places in our reform lists (the 76 repeal places, the partial-reform checks, Seattle, Minneapolis, Salt Lake City, Chicago, Hayward and Fremont);
  - places with any Parking Reform Network entry that removed minimums near transit (scope includes "transit-oriented") or at or near the benchmark, whatever its date.
- **Areas:** blocks within ½ mile of a station, each assigned to its nearest station, inside the city. The comparison is the rest of the same city.
- **Kept:** areas with at least 100 homes in 2000 and in 2010, in cities with at least 1,000 homes outside station areas.

## Measures

The same as the reform areas:
- **Outcome:** the change in change, 2010s minus 2000s, against the rest of the city.
- **Prior gap:** the 2000s gap.
- **Rail:** 1 for every area here.
- **Size:** log of 2010 homes.
- **Units:** extra homes per 1,000 existing homes per year, divided by 0.86 to put census counts on a permit footing.

## Tests

1. **Same pattern?** A home-weighted regression of outcome on prior gap and size, in the non-reform areas and in the reform areas (Seattle and Minneapolis, the census-measured ones), side by side.
2. **Parking effect.** Pool reform areas (Seattle and Minneapolis) with non-reform areas. Regress outcome on prior gap, size and a "reformed" indicator, weighted by homes. The indicator's weight is the estimated parking effect for an area with the same prior gap and size. 90% range: 2,000 bootstrap draws of areas.
3. **Prediction.** A model fitted on non-reform areas only predicts the reform areas. If it predicts them as well as the 10%-per-region model did, the reform added nothing the model doesn't already expect.

## Use

A second check. The tool changes only if test 2 shows a parking effect whose 90% range excludes zero, and Ryan approves.

## Changes after writing

# Boom-and-bust placebo cities, and a sliver-sized Wisconsin law: plan written before running

Written 2026-10-28 by the TOD conductor, at the owner's request:
- "can't we test those building booms with placebo cities from the same period?"
- "Why not just model out 3-6% of Madison being upzoned and use the slivers more directly?"

Nothing below has been computed before this file was committed. Changes go in section 4.

## 1. Boom-and-bust placebo cities

**Question:** did Seattle (2019), Minneapolis (2020) and Portland (2021) fall after their reforms more than other cities that had the same 2010s building boom and no reform?

- **Data:** the Census permit survey by city, 2000–2025 (as in [CONTROL_CITIES_PLAN.md](CONTROL_CITIES_PLAN.md)). Homes permitted per 1,000 homes (2010) per year.
- **Boom cities:** eligible cities (same exclusions as the control-city test) whose average rate in the reform city's before years is within ±25% of the reform city's own rate. The size band is one quarter to four times the reform city's homes, widened until at least 10 cities qualify.
- **Placebo reform:** each boom city gets a pretend reform in the same year, with the same before and after years.
- **Effect:** the reform city's change (after minus before) minus the median change of its boom cities.
- **90% interval:** from the 5th and 95th percentiles of the boom cities' changes.
- **Units:** shown as a share of the city's homes over five years.
- **Also shown:** the share of boom cities that fell by at least as much as the reform city.

## 2. A sliver-sized Wisconsin law

**Idea:** instead of stretching sliver results to a law covering two thirds of Milwaukee and Madison, model a law that upzones only a sliver: 3% and 6% of each city's homes.

- **Sliver cities:** the 14 measured cities of [CONVERSION_RESULTS.md](CONVERSION_RESULTS.md) with less than 5% of homes upzoned:
  - 8 measured by permits: New York, Philadelphia, Charlotte, Saint Paul, Los Angeles, Seattle, Chicago, Madison;
  - 6 measured by census: Jersey City, Milpitas, Bellevue, Austin, Fairfax County (Tysons), Salt Lake City.
- **Response per point of coverage:** whole-city gain over five years (% of homes) ÷ share of homes upzoned (%).
  - Reported: the median, and the 25th and 75th percentiles.
  - Shown again without Milpitas and Bellevue, whose upzoned land held few homes. That makes their ratio very large.
- **Wisconsin, sliver law:** extra homes over five years = response × coverage × the city's homes.
  - Coverage: 3% and 6%.
  - Cities: Milwaukee and Madison.
  - Little, typical and strong = 25th percentile, median, 75th percentile.
- **Which station areas make a 3–6% sliver:** the homes within ¼ mile of rail and rapid-bus stations in each city, from the coded station-area file, as a share of the city's homes. Reported to show whether a natural definition lands in the 3–6% range.
- **Holdout check:** Madison's own 2023 overlay is one of the 14. Its own response is shown beside the median from the other 13.

## 3. Use

Both are for the owner to decide on (AQ-059 and the definition question). No number changes without the owner.

## 4. Changes after writing

None yet.

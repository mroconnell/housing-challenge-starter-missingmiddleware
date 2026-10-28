# From measured cities to Wisconsin: share of a city upzoned → whole-city gain. Plan written before measuring

Written 2026-10-28 by the TOD conductor, at the owner's request: "We want to apply that everywhere outside of Wisconsin based on actuals. And then apply it to Wisconsin in the tool." No new city has been measured for this, and no line has been fitted, before this file was committed. Changes go in section 7 with a date and a reason.

## 1. Idea in one paragraph

Each measured reform gives two numbers:

- **Coverage:** the share of the city that was upzoned.
- **Gain:** the extra homes the whole city got over five years, as a share of all its homes, net of building that moved within the city.

A city that upzones a sliver gets a small whole-city gain, even if the sliver itself booms (one new stall at a market). A city that upzones most of itself gets a bigger whole-city gain, but less per upzoned home (stalls on every block share the same shoppers). Fitting gain against coverage across real cities gives the conversion rule. Wisconsin's numbers are then read off the rule, municipality by municipality, at each one's own coverage under the law.

## 2. Units

- **Coverage:** share of the city's land in residential, mixed or commercial use that was upzoned. Land is used rather than homes because some upzoned areas started nearly empty (Bellevue's BelRed had 3 homes in 2010). The share of homes is reported beside it.
- **Gain:** extra homes over five years ÷ the city's homes before the reform, in percent.

## 3. Cities

### Already measured

**Slivers:**
- 8 permit cities: New York, Philadelphia, Charlotte, Saint Paul, Los Angeles, Seattle, Chicago, Madison ([NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md)).
- 6 census cities: Jersey City, Milpitas, Bellevue, Austin, Tysons in Fairfax County, Salt Lake City ([CENSUS_CASES_RESULTS.md](CENSUS_CASES_RESULTS.md), section 5).

**Broad, from published studies:**
- Auckland 2016: about 4.1% gain in a city upzoned on 75.2% of residential land.
- Los Angeles Transit Oriented Communities 2017: about 0.03% gain, on 61% of homes, with incentives only.

### To be measured as whole cities

These are all from the case inventory, with the same methods.

| City | Reform | Measure | Comparison |
| --- | --- | --- | --- |
| New York | Bloomberg program, 2003–2009 rezonings together | census 2000/2010/2020, change in change | 10 matched US cities (CONTROL_CITIES method) |
| Seattle | Mandatory Housing Affordability upzoning, 2017 and 2019 | Census permit survey 2010–2025 | 10 matched cities |
| Minneapolis | 2040 Plan (2020) | permit survey 2014–2025 | 10 matched cities |
| Portland | Residential Infill Project (2021) | permit survey 2015–2025 | 10 matched cities |

**Expected weakness, written now.** Whole-city comparisons carry about ±4–5% of a city's homes of noise over five years (CONTROL_CITIES_RESULTS). Broad reforms whose true gain is 1–3% may not be distinguishable from zero. They are used with their intervals as weights.

## 4. The rule

Two shapes, both fixed now:

- **A. Proportional:** gain = b × coverage. Every upzoned share adds the same.
- **B. Diminishing:** gain = b × √coverage. Each extra share adds less.

**Fitting:**
- Weighted least squares through the origin. Weights are 1 ÷ (interval width)², capped so that no city carries more than 25% of the weight.
- Charlotte's own reform (2019) is included, as its net effect was measured.

**Choice:**
- Leave-one-city-out prediction error decides between A and B.
- **Holdouts, never fitted:** Madison (the Wisconsin test) and Chicago.
- The chosen shape must predict both holdouts within their own 90% intervals to be offered to the owner.

## 5. Applying it to Wisconsin

- For each Wisconsin municipality: coverage = the share of its residential, mixed and commercial land inside the law's station areas.
- Extra homes 2027–2031 = rule(coverage) × the municipality's homes.
- Computed for two definitions:
  - the current one (rail and rapid ½ mile, 15-minute bus ¼ mile);
  - a narrower one (rail and rapid only, ¼ mile).
- These are shown beside the current scenarios (171 / 2,509 / 17,148).

## 6. Use

A candidate for AQ-059 (the typical value) and a candidate narrower definition. Both are the owner's decisions; nothing changes until then.

## 7. Changes after writing

Recorded 2026-10-28 while running, before the fit was examined except where noted.

1. **Coverage is the share of the city's homes** (2010 census blocks), not of its residential land. City-wide land-use maps are not available for every city, and Auckland and Los Angeles TOC are published as shares of land and homes. Upzoned land that was nearly empty (BelRed) therefore counts as low coverage.
2. **Los Angeles's two sliver cases are taken together** (the net-effect city row), as are Seattle's.
3. **New York's whole-program window** is 2000–2004 before and 2006–2010 after, because the place permit files start in 2000.
4. **Portland's coverage** uses Oregon's statewide zoning layer, which carries only state classes. The "Res." class (the single-dwelling zones that the Residential Infill Project changed) is used. Seen after the first run printed 0% coverage, a parsing error; the fit hardly moved.
5. **Points with no published interval** (Auckland, Los Angeles TOC) take the 25% weight cap.
6. **The Wisconsin narrower definition** is rail and rapid only within ½ mile, because the per-municipality file holds that rung; ¼ mile is not computed per municipality.

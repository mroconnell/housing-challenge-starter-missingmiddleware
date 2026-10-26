# TOD Gate 3 model: specification written before the Madison test

Written 2026-10-26 by the TOD conductor, after the comparison cases were measured ([CASE_RESULTS.md](CASE_RESULTS.md)) and before any Madison permit is counted by overlay ([MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md)). The commit that adds this file is the timestamp. Changes go in section 9 with a date and a reason. Owner decisions in force: AQ-044, AQ-045, AQ-047 and AQ-049.

## 1. Outcome and units

- **Outcome:** extra housing units in issued building permits, by year, 2027–2031, compared with the all-housing baseline (v2, with the Milwaukee correction, AQ-048).
- **Areas:** the main-case station areas, by municipality, from `reference/tod_station_areas.csv` (coded for Milwaukee and Madison; fallback elsewhere).
- **Rates:** extra homes permitted per eligible acre per year. For method A, also per 1.0 of added floor area ratio (FAR).

## 2. Method A: response per acre per unit of added density

For each area *a* and year *k* since the law (2027 is year 1):

addition(*a*, *k*) = eligible acres(*a*) × added FAR(*a*) × *r* × ramp(*k*)

- **Added FAR(*a*):** the floor area the modelled law allows minus what current zoning allows, divided by eligible lot area, floored at zero. It comes from `added_floor_area_sqft` in the station-area table.
- **Eligible land:** only land where allowed density rises counts. Land already at the law adds nothing.
- ***r*:** extra homes permitted per eligible acre per year per 1.0 of added FAR, measured from the comparison cases.

  For the Madison test and the method choice, *r* is the New York pooled set's value, 0.671 (90% interval 0.365 to 1.020). It is the only fitted per-FAR value that is not a single neighborhood, and it already contains Park Slope and Downtown Brooklyn. Chicago was not used.
- **Ramp(*k*):** the New York pooled set's gap per added FAR by year since the change (years 1 to 5: 0.33, 0.31, 0.89, 1.61, 0.22), each divided by the mean of years 1 to 5. No smoothing, no assumed shape. Year 5's drop (0.22) is shown as measured, and a sensitivity uses the mean of years 3 to 5 for year 5.

## 3. Method B: capacity, feasibility and take-up

For each area *a*:

addition(*a*, *k*) = feasible new capacity(*a*) × take-up × ramp(*k*)

- **New capacity:** `capacity_gain` in the station-area table, using measured floor area per home: 1,512 sq ft in Madison, 1,192 in Milwaukee and 1,467 pooled elsewhere.
- **Feasible share:** the share of capacity on land where a new mid-rise apartment would earn its cost. The test is whether the capitalised net rent exceeds the building cost plus land.
  - **Rent:** the area's ACS median gross rent, scaled to new-building rent by the ratio of new-building to all-building rents in each city's recent permits, if available. Otherwise ACS rent is used and the gap is flagged.
  - **Building cost:** HUD's 2024 cost table (about $230 per sq ft for Milwaukee elevator buildings).
  - **Land:** assessed land value.
  - **Other parameters:** the capitalisation rate and operating costs come from one published source, cited. No values are tuned to the cases.
- **Take-up:** the share of feasible capacity that turns into permits each year, measured in Milwaukee. It is Milwaukee's 2018–2025 new 5+ unit homes on land zoned for 30 or more homes per acre, divided by that land's feasible capacity under current zoning. Madison is not used, because it is the test case.
- **Ramp:** the same as method A.

## 4. Which method wins (the Madison test)

1. Before any Madison permit is counted by overlay, both methods' predictions of the Madison overlay's difference-in-differences are written to `reference/tod_madison_test_predictions.csv` and committed:
   - method A: *r* × Madison's added FAR from the overlay;
   - method B: Milwaukee's take-up × Madison's change in feasible capacity from the overlay.

   Both come with their intervals.
2. The Madison count then runs exactly as in [MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md).
3. The method whose prediction is closer to the measured Madison estimate (in extra homes per eligible acre per year) becomes the main method.
4. If both predictions fall inside the Madison estimate's 90% interval, the test cannot separate them. Chicago (already measured, never fitted) then judges in the same way. If Chicago cannot separate them either, method A is the main method, because it rests on measured permits rather than a cost model. The brief says neither was confirmed in Wisconsin.
5. Method A's Chicago prediction is 0.671 × 0.50 = 0.34 extra homes per eligible acre per year. Chicago's measured value, +0.12 (−0.02 to +0.26), was seen before this was written, so Chicago is a weaker test than Madison. This is stated.

## 5. Scenarios, labelled by meaning

Each scenario is method A's formula with *r* taken from real cases, set after the test in section 4:

| Scenario | *r* (extra homes per eligible acre per year per 1.0 added FAR) | Meaning |
| --- | --- | --- |
| Little response | Chicago's 0.24 | A Midwestern big city with a modest upzoning |
| Typical response | the New York pooled set's 0.67, or Madison's measured value if the test shows one with a usable dose | Many rezonings of different sizes |
| Strong response | the mean of Park Slope (2.93) and Downtown Brooklyn (2.20), 2.57 | Plain large upzonings in a very strong market |

If method B wins, the three scenarios use method B with take-up and feasibility at the matching measured cases. The same labels apply.

A reference line, as for ADUs, is the median of every measured per-FAR case, with Park Slope and Downtown Brooklyn counted once through the pooled set.

## 6. Baseline and the rule that the law never subtracts

- **Baseline near stops:** each municipality's baseline (all-housing v2) × its share of homes near stops. That is 14,464 homes over 2027–2031 statewide, central case.
- **Additions:** added on top of the baseline. An area already at or above the law adds zero, and no addition is negative.

## 7. Sensitivities, grouped by what they move

- **The law's addition:**
  - each *r* in section 5;
  - the year-5 ramp alternative;
  - floor area per home at 1,000 sq ft;
  - single-family lots left out (G2-8);
  - the uncoded suburbs' fallback, scaled by the ratio of coded to fallback capacity measured in Milwaukee and Madison (the fallback was found to overstate capacity by 41% and 55% there).
- **Baseline only:** the low and high baselines; the Census-as-published Milwaukee series.
- **Where homes land:** stop definitions from narrowest to widest (rail and rapid only; 20-minute high case; all frequent stops within ½ mile).

## 8. Checks before Gate 3 is presented

- No addition is negative, and areas already at the law add zero.
- Areas add up to municipalities, counties, districts and the state.
- The baseline matches the shared baseline's near-stop split.
- The Madison test predictions are committed before the Madison count. The commit order is the proof.
- An independent verifier recomputes the state totals.

## 9. Changes after writing

**2026-10-26, method B (sections 3 and 4).** Made after stage 1 of the build and before any Madison permit was counted.
- **What happened:** method B could not be computed as specified. At HUD building costs, measured floor area per home, a 5.75% cap rate and 38.8% operating costs, a new mid-rise building would need about $2,011 a month in Milwaukee and $2,098 in Madison, even with free land. The highest ACS tract rents near stops are $1,961 and $1,759. So feasible capacity under current zoning is zero in Milwaukee. Yet 2,923 homes in 34 buildings were built there in 2018–2025, so take-up has no denominator. No parameter was tuned to rescue it.
- **Change:** method B is not used for the Madison test or the main estimate. Method A's committed prediction (0.251 extra homes per eligible acre per year, 90% interval 0.136 to 0.382) is judged against the Madison count alone. If the measured Madison estimate's 90% interval contains it, method A is confirmed in Wisconsin. If not, the brief says so, and the scenarios are re-examined at the owner's review.
- **What is kept:** the feasibility finding is kept as context. Census survey rents near stops sit below what new mid-rise building costs, so new buildings depend on rents above the local median. That is why response in Wisconsin may be weaker than in the comparison cases.
- **Owner:** informed the same day.

**2026-10-26, a scale check added (section 8).** Each scenario's statewide addition is compared with the highest yearly apartment permitting per existing home actually observed in a comparable US metro in the Census permit survey. That shows whether the per-acre response, carried over a large area, exceeds what a market of Milwaukee's or Madison's size has ever absorbed. It is a check shown to the owner, not a cap applied by the model.

**2026-10-26, sizing by citywide net effect (sections 2 and 5). Proposed, pending the owner's choice.** Made after the Madison test and the scale check.
- **Why:** carried over all eligible land near stops, the per-acre response exceeds what any comparable US metro has absorbed (MODEL.md, section 10). The local difference-in-differences counts building pulled from nearby blocks as if it were new: Los Angeles tripled proposals, but its citywide net effect was about 0.04 percentage points of stock growth.
- **Change:** the statewide addition is sized as a share of the housing stock in the upzoned areas, using citywide net effects measured after upzoning:
  - little: Los Angeles, 0.04 percentage points of stock growth a year;
  - typical: Stacy et al. 2023, +0.8% of housing supply 3 to 9 years after an upzoning, across 1,136 US cities;
  - strong: Auckland, 21,808 extra consents over 2016 to 2021, 4.1% of its 2016 stock.

  The stock is the 2020 census homes in the main-case station areas. Auckland's figure is a share of the whole city's stock, of which about 75% of residential land was upzoned. It is applied to the station-area stock as published, and the per-upzoned-stock reading (÷ 0.75) is a sensitivity.
- **Timing:** each study's own yearly profile where published (Auckland's yearly effects), otherwise the New York pooled ramp.
- **Placement:** method A's per-acre response is used only to place the total across station areas, as shares.
- **Checks:**
  - Madison's measured overlay effect, as a share of the overlay's housing stock over 2023–2025, is compared with each scenario's share over three years.
  - The scale check is rerun.
- **Sensitivity:** method A with the Wisconsin-measured response (the mean of Madison's 0.215 and Chicago's 0.240 per added floor area ratio), capped at the peer metros' 95th-percentile apartment permitting.

**2026-10-26, corrections to the net-effect values after reading the originals** ([research/NET_EFFECT_SOURCES.md](research/NET_EFFECT_SOURCES.md)):
- **Los Angeles:** 0.04 percentage points is stock growth over six years (2017–2023), not per year. That is about 0.033% of stock over five years, so the little scenario falls from 627 to about 105 homes on the station-area stock.
- **Stacy et al.:** 0.008 (standard error 0.003) is the average effect in years 3 and later after a loosening reform, measured in postal address counts. Only 28 of the 96 reforms changed floor area, density or height. The paper shows no rising ramp, so applying it inside years 1–5 is generous. That is stated.
- **Auckland:** the figures are confirmed, but the paper's year 0 is 2015. The 2017–2021 profile sums to 4.35% while 4.1% includes 2016, so the profile is rescaled to sum to the stated total.
- **Coverage:** LA's program covered about 61% of the city's homes, and Auckland upzoned about 75% of its residential land. If the owner chooses this sizing, the main reading divides each effect by its study's own coverage share (data from the papers), so the effect is per upzoned home. The as-published reading becomes a sensitivity. Stacy et al. did not measure coverage, so it is used as published.

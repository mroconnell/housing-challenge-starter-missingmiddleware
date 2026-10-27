# California AB 2097 test: plan written before counting

Written 2026-10-27 by the TOD conductor, after the owner approved the test (AQ-052). It was written before any California permits were counted for this question; the commit that adds this file is the timestamp. It is shared with the parking conductor, since half the question is parking's. Any later change goes in section 8 with a date and a reason.

## 1. Questions

1. **Parking near transit alone.** Did California's AB 2097, which removed parking minimums within ½ mile of major transit stops from 1 January 2023, raise homes permitted near transit where density had not already been raised?
2. **TOD plus parking.** Was the effect different where density near transit had already been raised before 2023? This is the combination case for the combined view's rule (c).

## 2. Data

- **Permits:** California HCD Annual Progress Report Table A2, 2018–2025. These are project-level building permits with units and HCD's geocoded latitude and longitude, and are already in the repo (`data/raw/hcd_apr_a2`). Only `NO_BUILDING_PERMITS` units in the permit year count. Records are de-duplicated by jurisdiction, address and year.
- **Major transit stops:** the State of California's Major Transit Stops layer, the last version published before 2023. If no pre-2023 version can be fetched, the earliest available version is used and the fact is recorded.
- **Homes:** 2020 census block housing units.
- **Areas already upzoned before 2023:** Los Angeles's Transit Oriented Communities eligibility areas (2017). San Diego's Transit Priority Area incentives and other city programs are added only if their pre-2023 boundaries are openly published. Every area used is listed.
- **Jurisdictions:** only those that filed Table A2 with geocoded permits in every year 2018–2025, so that reporting changes do not look like effects. The share of statewide permits kept is reported.

## 3. Areas

- **Near transit:** within ½ mile of a major transit stop.
- **Comparison ring:** ½ to 1½ miles from a stop, in the same jurisdiction.
- **Group P (parking alone):** near transit, outside any area upzoned before 2023.
- **Group T+P (TOD plus parking):** near transit, inside an area upzoned before 2023.

## 4. Outcome and periods

- **Outcome:** units in issued building permits per 1,000 existing homes (2020 census) per year. Per acre of land is a second measure.
- **Before:** 2018–2022. **After:** 2023–2025, three years, each also shown on its own.

## 5. Estimates

- **Parking alone:** the difference-in-differences of group P against its ring.
- **TOD plus parking:** the same for group T+P against its ring.
- **The combination term:** the T+P estimate minus the P estimate. It shows whether parking relief adds more where density was already raised. This feeds the combined view's rule (c) as a sensitivity only.
- **Uncertainty:** 90% intervals from resampling whole projects, 2,000 draws, fixed seed.
- **Sensitivity cases, fixed now:**
  - a ¼-mile near-transit distance;
  - Los Angeles city only;
  - leaving out the largest project in each group and period;
  - dropping 2023 as a transition year.

## 6. Known threats, stated now

- **Los Angeles's program already cut parking.** It reduced parking requirements before 2023, so group T+P had partial parking relief already. Its estimate is a lower bound on the combination.
- **Other California laws changed in the same years.** The density bonus, SB 9 and SB 35 streamlining, and the 2021 ADU changes also apply. Most of them apply equally near and away from transit, so the ring comparison absorbs them, but not completely.
- **Rates and costs.** Interest rates rose in 2022–2023, slowing apartments everywhere.
- **Reporting quality.** Self-reported Table A2 data vary across jurisdictions, so only full reporters are kept.
- **Short window.** Three years after the law is short.

## 7. How the results are used

- **Parking alone:** reported to the parking thread as California evidence on parking relief near transit.
- **TOD plus parking:** used only as a sensitivity in the combined TOD-and-parking view (rule c). No main number changes unless the owner decides so.

## 8. Changes after writing

None yet.

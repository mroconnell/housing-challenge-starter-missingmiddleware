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

**2026-10-27, before any counting, from the parking conductor's review:**
1. **Places where AB 2097 changed nothing.** Some places already had no parking minimums near transit, or citywide, before 2023. They are coded "already no minimums" and dropped from group P.
   - Listed from `reference/parking_reform_taxonomy.csv`: California records removing minimums rated "at" or "near" the benchmark, and transit-oriented records adopted before 2023. The list will include San Francisco (2019), San Diego transit priority areas (2019), Alameda (2021), Emeryville (2020) and Culver City (2022).
   - The final list is written into the results before any permits are counted.
   - San Jose (in effect April 2023) and Sacramento (2024) repealed citywide, so their rings changed too. They are dropped from the main estimate and kept as a sensitivity case.
2. **Uncertainty.** The main 90% interval resamples whole jurisdictions, since projects in one city are not independent. Resampling projects becomes a sensitivity case.
3. **Second outcome.** Units in buildings of 2 or more units, from Table A2's unit categories, are counted alongside all units, to match the parking scenario.
4. **Added threat: displacement.** Projects may move from the ring into the near-transit area, making the difference look bigger than it is. Check: compare the ring with land more than 1½ miles from any stop in the same jurisdiction.
5. **Group sizes.** Each group's number of jurisdictions and number of projects is reported. If group P has fewer than about 10 jurisdictions with permits in both periods, the result is called too thin to use.

**2026-10-27, by the analysis thread, after fetching the inputs and before any permits were counted by area.** Statewide Table A2 record counts by year were looked at only to set the geocoding rule in item 8; no permit was placed in an area before these were written.
6. **Major transit stops: no pre-2023 version.** The State's layer (Caltrans "High Quality Transit Stops", `CHrailroad/CA_HQ_Transit_Stops`) keeps only its current version, and no archived pre-2023 copy could be fetched. The current version, fetched 2026-10-27, is used, as section 2 allows. Only existing major transit stops count (`hqta_type` starting `major_stop`, blank `plan_name`); planned stops from the 2024–2026 regional plans are left out because they postdate the law. This version uses the 20-minute bus definition (AB 2553), wider than the 15-minute definition in force in 2023, so it marks some bus stops that were not major stops then. Added check, not part of the plan: rail, bus rapid transit and ferry stops only.
7. **Upzoned areas.** Los Angeles's Transit Oriented Communities tiers as of October 2017 (City Planning layer `TOC_Tiers_Oct2017_new`) are used; the only later pre-2023 layer (September 2021) covers Boyle Heights alone. No openly published pre-2023 boundary was found for San Diego's programs or any other city, so Los Angeles's TOC areas are the only upzoned areas. Group T+P is therefore one jurisdiction.
8. **Geocoded permit.** A record counts as geocoded when it has latitude and longitude and an HCD standardized street address (a street and city, not a city name alone). Records placed at a city or county fallback point are dropped, since their location says nothing about distance to a stop.
9. **De-duplication.** Records with the same jurisdiction, address, year, unit category and unit count are one record. One record per jurisdiction, address and year, read literally, would drop an ADU permitted with a house at the same address.
10. **Second outcome.** "Units in buildings of 2 or more units" = Table A2 unit categories "2 to 4" and "5+".
11. **Areas and denominators.** Areas are built from 2020 census blocks, each placed by its internal point: homes = 2020 census housing units, acres = census land area. A block's jurisdiction is the 2024 Census place containing its internal point, otherwise the county's unincorporated area (`reference/ca_jurisdiction_crosswalk.csv`). The ring and the land beyond 1½ miles leave out land inside upzoned areas. Group T+P's ring is the ring in the jurisdictions that have T+P land.
12. **"Already no minimums" places** are dropped from group P whole (near and ring), since the taxonomy gives no boundaries for downtown or transit-area records.
13. **Full reporters.** A jurisdiction is kept when it has at least one geocoded Table A2 record with permitted units in every year 2018–2025.
14. **Project** (for resampling and "largest project") = jurisdiction plus standardized address.
15. **Intervals with one jurisdiction.** Resampling whole jurisdictions gives no interval for a group with one jurisdiction (T+P). For T+P the interval comes from resampling projects, and it is marked as such. The combination term's interval combines a T+P project draw with a P jurisdiction draw, drawn independently.
16. **¼-mile sensitivity.** Near = within ¼ mile; land between ¼ and ½ mile is in no area; the ring is unchanged.
17. **Displacement check.** The difference-in-differences of each group's ring against land more than 1½ miles from any stop in the same jurisdictions. A negative value means the ring fell relative to the land beyond, as displacement would cause.

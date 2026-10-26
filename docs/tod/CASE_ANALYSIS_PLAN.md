# How each comparison case is measured: plan written before counting

Written 2026-10-26 by the TOD conductor, before any permits have been counted for the comparison cases in [reference/tod_cases.csv](../../reference/tod_cases.csv). The commit that adds this file is the timestamp. Any later change goes in section 7 with its date and reason. The Madison overlay follows its own plan ([MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md)), which uses the same rules.

## 1. Cases, in the order they are measured

1. **Fit set:**
   - Charlotte (2019 transit-oriented districts);
   - New York (the 2003–2013 rezonings: Fourth Avenue in Park Slope, Downtown Brooklyn, and the pooled set);
   - Saint Paul (Green Line, 2011).
2. **Medium-design comparison:**
   - Los Angeles Warner Center (2013);
   - Bellevue BelRed (2009);
   - Seattle North Beacon Hill/Othello (2012) and Mount Baker (2014).
3. **Held out, never used in fitting:**
   - Madison (2023);
   - Chicago (2013 and 2015);
   - Ann Arbor, if its permits carry unit counts.
4. **Mandate contrasts, reported but not fitted:**
   - Los Angeles TOC;
   - Seattle MHA;
   - San Francisco Market and Octavia;
   - New York after 2016.

## 2. Areas

- **Treatment:** parcels inside the official upzoning boundary.
- **Comparison:** parcels outside the boundary, within ¼ mile of its edge, in the same city.
- **Second comparison:** parcels elsewhere in the city within ½ mile of a rail or rapid transit station that was not upzoned in the window, where such stations exist.
- **Eligible land:** parcel acres in residential, mixed-use or commercial zoning before the change. Parks, water, streets, institutional campuses and cemeteries are excluded, the same as for Madison.

## 3. Outcome

- **Housing units:** units in new-construction building permits, by issue date, de-duplicated by permit number. Where only completions or certificates of occupancy exist, the case is marked "not permits" and kept as context.
- **Rate:** units per acre of eligible land per year.
- **Dose:** added allowed floor area ratio, the area-weighted average of (new maximum − old maximum) over eligible land. Where the rule is in homes per acre or height, it is converted to floor area with the case's own code rules, and the conversion is written down.
- **Effect per dose:** the difference-in-differences in units per acre per year, divided by the added floor area ratio.

## 4. Periods

- **Before:** up to 6 full years before the effective year. At least 3 are required; with fewer, the case is context only.
- **After:** years 1 to 5 after the effective year, each shown on its own. Year 0 (the effective year) is shown but not used.
- **Ramp:** the year-by-year after values, pooled across the fit set, become the ramp. Nothing is assumed.

## 5. Uncertainty and checks

- **Interval:** a 90% interval from resampling whole projects, 2,000 draws, fixed seed.
- **Sensitivity cases:**
  - the second comparison area;
  - leaving out the largest project in each area and period;
  - permits per 1,000 existing homes instead of per acre.
- **Parking and affordability:** each case is tagged for parking-minimum changes and affordability mandates. The fit is repeated on cases without parking cuts (New York) and on cases with them (Charlotte, Saint Paul). This separates TOD alone from TOD plus parking as far as the cases allow.
- **Market strength:** each case is tagged with its city's median rent (ACS). Whether the effect per dose rises with rent is tested on the fit set, and judged by the held-out cases. No relationship is assumed.

## 6. Choosing the modelled law's design (AQ-047, item 1)

- **Which designs count:** a design (height and floor-area rules, by-right path, no mandate) is "most effective" only if its effect per dose is above the fit-set median and it holds up on the held-out cases.
- **What happens when the held-out cases disagree:** the design is reported but the law falls back to the SB 79 floors from the Gate 1 packet.
- **One case is never enough:** a single case cannot set the law alone.

## 7. Changes after writing

**2026-10-26, areas (sections 2 and 3).** Made after the first count of Charlotte, New York, Saint Paul and Chicago, following an independent check of those results ([CASE_RESULTS.md](CASE_RESULTS.md)).
- **Change.** One rule for every case:
  - treatment = lots inside the reform whose allowed residential density (floor area ratio, or height where a case has no FAR) actually rose with the reform;
  - comparison and second comparison = lots whose allowed density did not change during the before or after years;
  - lots rezoned outside the reform during those years are in no area;
  - land already at the law is in no area. "Already at the law" means zoning before with no separate homes-per-acre cap that already allowed at least the acre-weighted median allowed level of the reform's new zoning on eligible land where density rose.
- **Reason.** This applies the eligible-land definition already decided in AQ-047 item 8: eligible land is land where the law raises allowed density, and land already at the law is excluded. The check showed the original area rule mixed already-dense land into both groups. In Charlotte, 1,856 of the 2,111 before-period treatment units were on 124.8 acres already zoned for transit-oriented development before 2019, and the comparison ring held older dense mixed-use zoning.
- **Original rule kept.** Results under the original rule stay in the results as a sensitivity (`sens_original_spec`).


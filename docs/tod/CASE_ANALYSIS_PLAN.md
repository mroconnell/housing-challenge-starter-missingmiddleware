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

**2026-10-26, added cases (section 1).** Added after the first five cases were counted, on the owner's approval of G2-3 (AQ-049), and before any permits for them are counted:
- **Fit set:** the New York pooled set of city-initiated rezonings, 2003–2013; Philadelphia's 2012 code remapping and transit overlay; Raleigh's 2021 transit overlay; Phoenix's 2015 Walkable Urban Code.
- **Held out:** Ann Arbor's 2021 TC1 transit corridor district.
- **Why these:** they are the inventory's medium- or strong-design cases with open data and median rents of $1,397 to $1,649 a month, closer to Milwaukee ($1,059) and Madison ($1,413) than New York ($1,821). The cases were chosen by rent, design and data, before their outcomes were seen.
- **Rules:** the same as for every other case, including the one area rule above.

**2026-10-26, how the added cases are measured (deviations recorded while counting them).** Details are in [CASE_RESULTS.md](CASE_RESULTS.md).
- **Rezonings at different dates are stacked in event time.** The New York pooled set and Philadelphia's remapping are many rezonings at different dates. Each member is built with the one area rule. Units and acres are then summed by years since that member's effective date: before is years −6 to −1, after is years 1 to 5. Each member's projects stay distinct in the resampling.
  - Only members with 6 before years and 5 after years inside the permit data are used.
  - Reason: section 4's periods are defined relative to one effective year, and stacking keeps that definition for each member.
- **The New York pooled set.** It is Liao's 22 upzonings (2004–2013, his Table 1) plus Park Slope (2003, the plan's named 2003 member).
  - Members whose upzoned land was all manufacturing before drop out under the eligible-land rule; so do members with no treated land.
  - There is no second comparison area for the pooled set.
  - Each member's zoning before, after and at the window's ends comes from yearly MapPLUTO archives. "After" is the first archive that shows the change, because PLUTO lags the map.
- **New York job placement.** A job is no longer placed by its block and lot when that lot is more than 100 m from the job's own geocoded point. It is placed by its point instead.
  - Reason: a Bergen Street job's block and lot pointed to a lot 1,345 m away (GATE2_EXAMPLES.md).
- **Philadelphia.**
  - **Reform:** the City Planning Commission's district-plan remapping bills under the 2012 code, enacted 2013–2020.
  - **Rezoned elsewhere:** applicant, council and other bills count as rezonings outside the reform.
  - **The transit overlay (/TOD, code section 14-513)** has 13 polygons and no enactment dates, so it is not measured separately.
  - **Rising density:** whether allowed density rose is judged from an ordering built from the City's own table of height and FAR by district.
  - **Dose:** most remapped districts have a height limit and no FAR, so there is no FAR dose. Philadelphia stays out of per-FAR pooling, as Charlotte does.
  - **Outcome:** only whole-building new-construction permit types count. Foundation, shell and fit-out permits are left out so a building is not counted twice.
- **Raleigh is context only.**
  - The 2021 overlay text applies only where mapped. The City's first overlay mappings (Z-18-2022 and Z-19-2022) added the overlay without changing base districts.
  - The other TOD map changes before 2024 are applicants' conditional site rezonings, which select sites about to be built.
  - The permit file's unit field is nearly empty from 2024, leaving one after year.
- **Phoenix is context only.** No permit source with unit counts and before years was found.
- **Ann Arbor (held out) has no estimate.** No permit source with unit counts was found.

**2026-10-27, permit counts for cases without unit counts (owner request).** Raleigh 2021, Phoenix 2015 and Ann Arbor 2021 have no usable unit counts. They are measured with **new residential building permits** (count of permits, not homes) per eligible acre per year, using the same areas, periods, area rule and difference-in-differences. If both are available, multifamily permits are counted separately from single-family. These results are context only. They are never pooled with unit-based cases or used to fit, and their units are always labelled "permits, not homes". Ann Arbor stays a test case. This entry was written before any of their permits were counted.

**2026-10-27, how the permit-count cases were measured (deviations recorded while counting them).** Details are in [CASE_RESULTS.md](CASE_RESULTS.md), section "Permit counts".
- **Raleigh is not measurable, even by permit counts.**
  - The City's open permit layer records 497 to 966 detached single-family and multifamily permits a year in 2010–2018. It then records 6 in 2019, 34 in 2020, 1 in 2021 and none in 2022–2025: new homes are coded "townhouse" and buildings of 2 or more units disappear.
  - The Census Building Permits Survey still shows thousands of units a year in 5+ unit buildings for Raleigh.
  - The reform year is taken as 2024: the first City TOD mapping that also changed base districts and heights, Z-92A to Z-92E-2022. The 2022 overlay-only mappings do not raise by-right density, because the overlay's extra height needs affordable units.
  - The 2024 reform's before and after years both fall in the broken period, so the counts are shown by year but no estimate is made.
- **Phoenix.**
  - **Members:** Walkable Urban Code rezonings, stacked in event time.
  - **Effective year:** the approval year where the City's list gives one. Otherwise it is the year in the case number, which is the year the case was filed.
  - **Zoning before** most WU rezonings is not in any layer. Every WU parcel therefore counts as having risen, and "already at the law" cannot be tested.
  - **Single-family permits** move to a new system with no public archive in 2022, so the single-family and all-permit series use members effective by 2016; the multifamily series uses members effective by 2020.
  - **Units are available.** The City's export carries unit counts, so a unit-based Phoenix measure is possible. It is not made here, because the owner asked for counts.
- **Ann Arbor (held out) is not measurable.** No permit records with locations exist before 2022, and the first TC1 map rezoning is April 2022, so there are no before years.

**2026-10-27, more cities for the trait test (owner request: "Add more cities"; written before any of their permits are counted).** The trait test (TRAITS_PLAN.md) found no trait that predicts held-out cities, with only four cities to learn from. These cases from the inventory are added, chosen by data usability (A or B) and policy design (medium or strong; no affordability mandate) before any outcome is seen:
- **Batch 1:** Los Angeles Warner Center 2013; Los Angeles Cornfield Arroyo Seco 2013; Seattle North Beacon Hill and Othello 2012; Seattle Mount Baker 2014; Bellevue BelRed 2009.
- **Batch 2:** Ottawa transit-oriented development zone 2012; Toronto Eglinton Connects 2014; Minneapolis Hiawatha (Blue Line) station-area rezonings 2008–2012. Minneapolis has a weak design, so it is added only to widen the range of traits, and is flagged.
- **New York:** the 6 pooled rezonings dropped for industrial land stay dropped; the rule is unchanged.

Rules: the same as for every other case, including the one area rule and units-per-acre outcome. A case that lacks unit counts or 3 years before falls back to permit counts and is context only. Each new city becomes a fitted city in the trait test, which is rerun with the same pass rule. Chicago and Madison stay held out.

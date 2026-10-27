# TOD comparison cases: what was measured and what it shows

Written 2026-10-26 for TOD Gate 2, work package 5. It was revised the same day after an independent check, and extended with the cases the owner added on approving Gate 2 (AQ-049, recorded in the plan's section 7 before counting): the New York pooled set, Philadelphia, Raleigh, Phoenix and Ann Arbor (held out). The work applies [CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md), which was written before counting.

- **Recorded changes to the plan.** The area rule changed after the check, and the added cases needed a few measurement choices. Both are recorded in the plan's section 7, dated 2026-10-26, and summarised under [Deviations](#deviations). The results under the original area rule are kept as a sensitivity.
- **Other departures** are listed under Deviations.
- **Madison** is not touched here; it has its own pre-registered step.

**Files.**
- **Code:**
  - [missing_middleware/tod/cases.py](../../missing_middleware/tod/cases.py) holds the shared measurement code, including `uniform_areas` for the area rule.
  - Each city has its own adapter: `case_charlotte.py`, `case_nyc.py` (named members and the pooled set), `case_stpaul.py`, `case_philadelphia.py`, `case_raleigh.py`, `case_phoenix.py`, `case_chicago.py` and `case_annarbor.py`.
  - The scripts are [scripts/fetch_tod_cases.py](../../scripts/fetch_tod_cases.py) and [scripts/run_tod_cases.py](../../scripts/run_tod_cases.py).
  - The tests are in [tests/test_tod_cases.py](../../tests/test_tod_cases.py).
- **Results:**
  - [reference/tod_case_estimates.csv](../../reference/tod_case_estimates.csv) has one row per case.
  - [reference/tod_case_units.csv](../../reference/tod_case_units.csv) splits the added cities (Los Angeles, Seattle, Bellevue) into trait-test units.
  - [reference/tod_case_rates_by_year.csv](../../reference/tod_case_rates_by_year.csv) has every area and year: before, year 0 and after. For the two stacked cases (New York pooled, Philadelphia) `year` is the event year, −6 to +5, years since each member's effective date.
  - Neither file holds parcel, permit or project numbers; a test checks this.
- **Raw files** are git-ignored, under `data/raw/tod_cases/<city>/`. Each folder has a `manifest.json` with the URL, access time, bytes, SHA-256 and licence.
- **To run:**
  1. `uv run --all-extras python scripts/fetch_tod_cases.py`
  2. `uv run --all-extras python scripts/run_tod_cases.py`

**How to read the numbers.**
- **Rate:** housing units in new-construction building permits ÷ acres of eligible land in the area ÷ years.
- **Estimate:** a difference-in-differences (DiD) of yearly mean rates, in units per eligible acre per year:
  (treatment after − treatment before) − (comparison after − comparison before).
- **Interval:** a 90% bootstrap interval. Whole projects are redrawn with replacement within each area; 2,000 draws; seed 20261026.
- **Dose:** added allowed floor area ratio (FAR). It is the acre-weighted mean of (new maximum residential FAR − old maximum residential FAR) over the treatment's eligible land.
- **Effect per dose:** the DiD ÷ the dose, in units per eligible acre per year per 1.0 of added FAR.
- **Exceptions.** Charlotte's districts have no FAR, so its dose is added height in feet and its effect is per added foot. Philadelphia's remapped districts mostly have height limits and no FAR, so it has no dose at all. Both stay out of per-FAR pooling.
- **Stacked cases.** The New York pooled set and Philadelphia are many rezonings at different dates. Each member is built with the area rule; units and acres are then summed by years since that member's effective date.

**The area rule** (plan section 7, change of 2026-10-26, applied the same way to every case):
- **Treatment:** lots inside the reform whose allowed residential density actually rose. The measure is FAR, or height in Charlotte.
- **Comparison:** lots within ¼ mile of the treatment whose allowed density did not change during the before or after years.
- **Second comparison:** lots near rail stations, with the same condition. It uses only stations whose ½-mile area has no treated land.
- **Dropped from every area:**
  - lots rezoned outside the reform during those years;
  - land already at the law. That means zoning before with no separate homes-per-acre cap that already allowed at least the acre-weighted median allowed level of the reform's new zoning on land where density rose.

## Results at a glance

| Case | Role | Estimate (units per eligible acre per year) | 90% interval | Dose | Effect per dose (90% interval) | Original area rule (DiD) | Parking minimums | Affordability mandate | City median gross rent (ACS 2020–2024) |
|---|---|---|---|---|---|---|---|---|---|
| Charlotte 2019 | fit | +0.130 | +0.006 to +0.279 | +30.4 ft of height (no FAR) | +0.0043 per added foot (+0.0002 to +0.0092); no per-FAR value | −0.406 | removed | no (voluntary bonus) | $1,612 |
| Saint Paul 2011 | context only (1 before year) | −0.087 | −0.437 to +0.264 | +1.01 FAR (source_lead; T4 land left out) | −0.086 per FAR | +0.038 | removed near stations | no | $1,281 |
| New York, Fourth Avenue (Park Slope) 2003 | fit | +6.987 | +4.385 to +9.664 | +2.38 FAR | +2.934 per FAR (+1.841 to +4.058) | +0.233 | kept | no | $1,821 |
| New York, Downtown Brooklyn 2004 | fit | +13.313 | +7.919 to +19.340 | +6.06 FAR | +2.197 per FAR (+1.307 to +3.191) | +9.040 | kept | no | $1,821 |
| New York pooled set, 2003–2013 (17 of 23 rezonings) | fit | +1.057 | +0.575 to +1.607 | +1.58 FAR | +0.671 per FAR (+0.365 to +1.020) | +0.111 | kept | no | $1,821 |
| Philadelphia remapping, 2013–2019 (83 bills) | fit | +1.022 | +0.522 to +1.658 | none (height-only districts) | no per-dose value | +0.013 | none code-wide | no | $1,397 |
| Raleigh 2021 transit overlay | context only; not measurable even by permit counts | — | — | — | — | — | (overlay cuts minimums) | no | $1,572 |
| Phoenix 2015 Walkable Urban Code | context only; permit counts below | — | — | — | — | — | unknown | no | $1,582 |
| Chicago 2015 (held out) | held out | +0.120 | −0.015 to +0.263 | +0.50 FAR (source_lead) | +0.240 per FAR (−0.029 to +0.525) | +0.528 | reduced | no for the base bonus | $1,440 |
| Ann Arbor 2021 TC1 (held out) | held out, no data (not even permit counts) | — | — | — | — | — | removed | no | $1,649 |

- **Fit set.** It is the cases with role "fit" and status "measured": Charlotte, Park Slope, Downtown Brooklyn, the New York pooled set and Philadelphia.
  - Park Slope and Downtown Brooklyn are also members of the pooled set, so a median over all three New York rows counts them twice.
  - **Per-FAR values in the fit set:** Park Slope 2.93, Downtown Brooklyn 2.20, the pooled set 0.67. The plain median of these three is 2.20; the pooled set alone (which already contains the two named members) is 0.67 per added FAR.
  - Charlotte and Philadelphia have no per-FAR value and stay out of every per-FAR pooling (deviations 2 and 8).
  - Saint Paul, Raleigh and Phoenix are context only; Chicago and Ann Arbor are held out. None enters anything fitted (`cases.fit_set`).
- **With the added cities (2026-10-27).** Los Angeles Warner Center and Cornfield, and Seattle's two cases, join the fit set; Bellevue is context only. Their rows are in the batch 1 section below.
  - The two Seattle cases add per-FAR values of −0.19 and +0.10, both with intervals spanning zero.
  - The fit-set per-FAR values are now Park Slope 2.93, Downtown Brooklyn 2.20, New York pooled 0.67, Mount Baker 0.10 and North Beacon Hill + Othello −0.19. Their median is 0.67, and Park Slope and Downtown Brooklyn are still counted twice through the pooled set.
- **Batch 2 (2026-10-27).** Toronto is context (boundary problem), Ottawa is context only and Minneapolis has no data, so none of the three changes the fit set. See the batch 2 section.
- **Held-out check.** Chicago's effect per added FAR is 0.24 (90% interval −0.03 to +0.53). That is below every New York value, including the pooled set's 0.67 (interval 0.37 to 1.02); the two intervals do not overlap. Ann Arbor, the other held-out case, has no permit data with unit counts.
- **Median rents** are the city values in [reference/tod_cases.csv](../../reference/tod_cases.csv): ACS 2020–2024 5-year, table B25064, observed there. They are 2020–2024 values, not values at each case's start.

## Charlotte, 2019 transit-oriented districts (fit)

**What was measured.**
- **Reform land.** These are the 360 polygons of City Petition 2019-102, approved 18 November 2019, from the City's Rezoning History layer.
  - A parcel is in the reform when its representative point lies in one of the polygons.
  - That gives 1,580.1 acres; the petition states 1,782.83 acres in 1,564 parcels.
  - Zoning before is the polygon's ExistingZoning; zoning after is its RequestedZoning.
- **Level used by the area rule.** It is the height limit, because Charlotte's districts have no FAR.
  - Density "rose" where the height limit went up, or where the district before had a homes-per-acre cap; the TOD districts have none.
  - The acre-weighted median new height on rising land is 90 ft.
  - So land zoned before with no homes-per-acre cap and a limit of at least 90 ft is already at the law: older transit districts, TOD-CC, MUDD and UMUD.
  - That is 1,839.0 eligible acres across all areas, dropped.
- **Treatment.** It is the petition lots whose density rose and that were not already at the law: **817.5 eligible acres** in 670 parcels.
  - **Before:** mostly B-2 (304 parcels), B-1 (208), O-2 (51), R-17MF (32) and R-22MF (20).
  - **After:** TOD-TR (236), TOD-CC (233), TOD-NC (143) and TOD-UC (56).
- **Lots rezoned outside the reform.** Petitions approved 2013–2024 that changed a lot's base district, other than 2019-102, take the lot out of every area. There were 2,031 such petitions, covering 2,221.6 eligible acres.
  - Zoning before for the remaining non-reform lots is the Pre-UDO zoning map, in force until June 2023.
- **Comparison.** It is lots in the City of Charlotte (current council-district outline) within ¼ mile of the treatment: **3,082.2 eligible acres**. That is 2,313.6 acres residential and 768.1 commercial.
- **Second comparison.** It is lots within ½ mile of the 27 LYNX Blue Line and CityLYNX Gold Line stops whose own ½-mile circle has no treated land: **881.2 eligible acres**.
- **Eligible land.** It is residential, commercial or mixed-use zoning before. Industrial (I-1, I-2) and institutional zoning are out, as are parks, cemeteries, churches, schools, government land, utilities and similar assessor land uses.
- **Outcome.** It is Mecklenburg County building permits, one record per permit number.
  - Only Census use codes 101–105 and 115 count: new one-family to 5-or-more-unit buildings, the Building Permits Survey classes.
  - Units come from `numunits`.
  - Large apartment buildings are permitted floor by floor, and each floor permit carries that floor's units.
  - Placeholder one-unit permits for garages, amenity areas and "shell/core" (S/C) are dropped.
  - 95.1% of permits near the areas fall in a parcel or within 30 m of one.
  - A project, for resampling, is the permit's parcel.
- **Periods.** Before is 2013–2018 (6 years), year 0 is 2019, after is 2020–2024 (5 years).
- **Dose.** It is the added height limit in feet over eligible treatment land, **+30.4 ft**.
  - Charlotte's base districts are about 40 ft before (source_lead); TOD-TR is 50 ft, TOD-NC 75, TOD-CC 90 and TOD-UC 130.
  - The removal of homes-per-acre caps (for example 22 homes per acre in B-1 and B-2) is a second part of the dose that this number does not carry.

**Results (units per eligible acre per year).**

| Area | Before 2013–2018 | After 2020–2024 |
|---|---|---|
| Treatment (817.5 acres) | 0.012 (58 units ÷ 817.5 acres ÷ 6 years) | 0.152 (622 units ÷ 817.5 ÷ 5) |
| Comparison (3,082.2 acres) | 0.047 (862 units ÷ 3,082.2 ÷ 6) | 0.057 (871 units ÷ 3,082.2 ÷ 5) |

- **DiD:** **+0.130** (90% interval +0.006 to +0.279).
- **Effect per added foot of height:** +0.0043 (+0.0002 to +0.0092). That is about +0.043 units per eligible acre per year for 10 added feet.
- **Sensitivities** (all DiD, units per eligible acre per year):
  - second comparison: +0.188;
  - largest project in each area and period left out: +0.091;
  - per 1,000 existing homes: +42.6 units per 1,000 homes per year. The homes are from 2010 census blocks: 2,514 in treatment and 10,049 in comparison.
  - **original area rule** (whole petition against its ring): **−0.406** (−0.695 to −0.119).
- **Why the two rules differ.** Under the original rule, 1,856 of the 2,111 before-period treatment units were on 124.8 acres already zoned TOD-CC before 2019, and the comparison ring held older dense zoning (TOD-M, MUDD, UMUD). Both now sit in "already at the law".

**Limitations.**
- **The rule removes development-linked rezonings from the comparison.** In Charlotte most apartment projects outside the TOD districts go through a private conditional rezoning first, so a lot rezoned in 2013–2024 is often a lot that was then built on.
  - Dropping those lots, as the rule requires, leaves the comparison with mostly lots that did not develop. Its after-period rate (0.057) is far below the original ring's (0.411).
  - This pushes the DiD up. The second comparison (+0.188) has the same problem.
  - The true effect probably lies between the original-rule −0.406 and this +0.130. Read Charlotte as weak evidence either way.
- The treatment after-period units are concentrated in a few projects: 231 units in 2021 and 323 in 2023 out of 622.
- **Census BPS check.** This compares units in all new-housing permits in the county permit file with the Census Building Permits Survey (BPS) for Mecklenburg County, as permit file ÷ BPS − 1.
  - **Before years:** +39% in 2013 (11,919 against 8,558; the year of a 903-unit burst on land that is now "already at the law"), −4% in 2014, −12% in 2015, −21% in 2016, −27% in 2017 and +2% in 2018.
  - **After years:** +22% in 2020, −2% in 2021, +6% in 2022, +41% in 2023 and +54% in 2024.
  - Floor-by-floor permits may be counted differently from BPS; the excess and shortfall fall in both areas.
- The county server refuses scripted queries. The file is the City of Charlotte's ArcGIS Hub copy of the same county layer.
- Heights before are source_lead. A per-foot effect cannot be pooled with per-FAR effects (deviation 2).
- **Inconsistency with [capacity.py](../../missing_middleware/tod/capacity.py).** That module converts FAR to homes at 1,000 gross sq ft per home (`GROSS_SQFT_PER_HOME`). The first version of this case used New York's 680 sq ft dwelling-unit factor; that conversion has been removed here.
  - Any later step that turns Charlotte's height dose into FAR must use one stated conversion, and it should come from Charlotte's code or its built projects.

## Saint Paul, Green Line 2011 (context only)

**What was measured.**
- **Reform land.** It is parcels within ½ mile of a Green Line stop in Saint Paul whose zoning changed from another district (November 2010 snapshot) to T1–T4 (November 2012). The TN1–TN3 to T1–T3 renaming does not count.
- **Treatment.** It is reform parcels whose allowed FAR rose: 686 parcels, **210.6 eligible acres**.
  - T4 has no FAR maximum, so the median new level is "no limit" and no land counts as already at the law.
- **Lots dropped.** Zoning changes in the window are read from the November 2010, November 2012 and November 2017 snapshots. 1,677.3 eligible acres changed outside the reform and are dropped.
- **Comparison:** **1,450.2 eligible acres**.
- **Second comparison:** none. Every rail stop in Saint Paul is a Green Line stop with treated land within ½ mile.
- **Outcome.** It is the City's Housing Production layer: type of work "New", new dwelling units, by permit issue year. 92.4% of projects locate to a parcel.
- **Effective year: 2011.** That is the City Council adoption, April 2011. The City's own zoning archive does not show the change in November 2011 and does show it in November 2012.
- **Dose.** It is +1.01 FAR, from district values that are source_lead: B3 2.0, I1 0, T2 2.0 and T3 3.0. T4 (130.4 acres, no limit) is left out of the dose.

**Results.**
- **Status: context only.** Permits with unit counts start in 2010, so the case has 1 before year; the plan needs 3. With 2012 as the effective year it would still have only 2.
- **Treatment:** 0.237 units per eligible acre per year in 2010 (50 units ÷ 210.6 acres ÷ 1 year), and 0.155 in 2012–2016 (163 units ÷ 210.6 ÷ 5).
- **Comparison:** 0.000 (0 units), then 0.004 (30 units ÷ 1,450.2 ÷ 5).
- **DiD:** −0.087 (90% interval −0.437 to +0.264). The original rule gives +0.038.
- Shown for context only; not used.

## New York, Fourth Avenue in Park Slope, 2003 (fit)

**What was measured.**
- **Reform land.** It is lots (MapPLUTO 02b, March 2003) whose representative point is inside zoning map amendment 030194A ZMK, effective 30 April 2003.
- **Treatment.** It is reform lots whose allowed residential FAR rose between MapPLUTO 02b and 04c: **19.1 eligible acres** in 300 lots.
  - **Before:** 240 lots R6 and 70 lots R7A.
  - **After:** 245 lots R8A and 66 lots R7A.
  - The contextual downzoning that covered most of the amendment's 5,640 lots is not treatment.
  - The median new level on rising land is 6.02 FAR. Lots already at 6.02 or more before are already at the law: 106.6 eligible acres.
- **Lots dropped.** Lots whose allowed FAR changed outside the amendment between 02b and 04c, or anywhere between 04c and 09v1 (mid 2009, the first archive after the window), are in no area: 2,287.6 eligible acres.
  - That includes South Park Slope (2005) along Fourth Avenue south of the treatment, and the many contextual rezonings of 2005–2009.
  - Changes in 1997–2002 cannot be seen, because 02b is the first archive.
- **Comparison:** **88.4 eligible acres**.
- **Second comparison:** lots within ½ mile of the 154 Brooklyn subway stations whose ½-mile circle has no treated land: **10,978.9 eligible acres**.
- **Eligible land.** It is residential, commercial or mixed (M1/R) zoning in 2002. PLUTO land use 08 (public facilities and institutions), land use 09 (open space, which includes cemeteries) and PARK are out.
- **Outcome.** It is Department of Buildings job filings for new-building jobs in Brooklyn, using proposed dwelling units.
  - There is one record per job number, counted in the year the job was fully permitted.
  - A job goes on the 02b lot with the same block and lot, unless that lot is more than 100 m from the job's own geocoded point (37 Brooklyn jobs in the Park Slope window; deviation 9). Otherwise it goes on the lot containing its point, or the nearest lot within 40 m.
  - A project is the job's block and lot.
- **Dose.** It uses maximum residential FAR by district under the Zoning Resolution as in force 2002–2004: the higher of the height-factor and Quality Housing wide-street maximums, with no inclusionary bonus.
  - Values used: R6 3.0, R7A 4.0, R8A 6.02, M1-2 0.
  - Dose: **+2.38**.
  - As a check, PLUTO's own maximum allowed FAR gives +2.84. That field is the largest of residential, commercial and community-facility FAR.
- **Periods.** Before is 1997–2002 (6 years; the file has jobs fully permitted from 1991), year 0 is 2003, after is 2004–2008.

**Results.**

| Area | Before 1997–2002 | After 2004–2008 |
|---|---|---|
| Treatment (19.1 acres) | 0.026 (3 units ÷ 19.1 ÷ 6) | 7.198 (686 units ÷ 19.1 ÷ 5) |
| Comparison (88.4 acres) | 0.232 (123 units ÷ 88.4 ÷ 6) | 0.416 (184 units ÷ 88.4 ÷ 5) |

- **DiD:** **+6.987** (90% interval +4.385 to +9.664).
- **Effect per added FAR:** **+2.934** (+1.841 to +4.058).
- **Sensitivities:**
  - second comparison: +6.843;
  - largest project left out: +5.307;
  - per 1,000 existing homes: +87.6 units per 1,000 homes per year. The homes are 2002 PLUTO residential units: 1,512 in treatment and 5,844 in comparison.
  - **original area rule:** **+0.233**. Here every lot in the 2003 amendment (276.2 eligible acres, mostly the downzoned brownstone blocks) is set against its ¼-mile ring (219.9 acres).
- **The two records flagged in [GATE2_EXAMPLES.md](GATE2_EXAMPLES.md) were checked.**
  - *The Bergen Street comparison job* (3 units, 2005) had a block and lot pointing to a lot 1,345 m from its own point. Such id matches are no longer trusted beyond 100 m; the job is now placed by its point and leaves the Park Slope comparison. The comparison's after-period total falls from 187 to 184 units.
  - *The possible duplicate behind Job E* is not a duplicate. The DOB records show two jobs on 2nd Street: number 306, a 5-storey, 46-unit building filed in March 2001 and fully permitted on 30 April 2003 (lot 6), and number 302, a 12-storey, 69-unit building filed in November 2004 and fully permitted later that month (new lot 106). Both are signed off, so both were completed. The 5-storey one fits the old R6/R7A rules and the 12-storey one the new R8A height of 120 ft. Both counts stay.
- **Note on the first version.** The first version reported "literal plan" figures of +6.883 and +11.457. Those already limited treatment to upzoned lots, so they were an alternative comparison, not the plan read literally. The whole-amendment figures above replace them.

## New York, Downtown Brooklyn, 2004 (fit)

**What was measured.**
- **Rules:** the same as Park Slope.
- **Amendment:** 040171 ZMK, adopted 28 June 2004.
- **Treatment:** 227 of the amendment's 292 lots had a higher residential FAR after, giving **27.7 eligible acres**.
  - **Before:** 181 lots C6-1, 24 lots R6 and 14 lots M1-1.
  - **After:** 144 lots C6-4, 77 lots C6-4.5 and 6 lots C6-2.
  - The median new level is 10.0. Lots already at 10.0 or more before are already at the law: 53.0 acres.
  - Snapshots: before 03c, after 04c, end 10v1.
- **Lots dropped.**
  - Lots whose FAR changed outside the amendment are dropped. This includes the 18 lots (4.58 acres) just outside the amendment whose residential FAR rose from 4 to 10 between 02b and 04c.
  - Lots that changed again by mid 2010 are also dropped: 3,792.6 eligible acres in all.
- **Comparison:** **146.3 eligible acres**.
- **Second comparison:** 151 stations, **10,042.2 eligible acres**.
- **Dose.** C6-1 is R7-equivalent at 4.0; C6-4 and C6-4.5 are R10-equivalent at 10.0. Dose: **+6.06**. PLUTO's maximum allowed FAR gives +4.90.
- **Periods.** Before is 1998–2003, year 0 is 2004, after is 2005–2009.

**Results.**

| Area | Before 1998–2003 | After 2005–2009 |
|---|---|---|
| Treatment (27.7 acres) | 0.000 (0 units) | 14.700 (2,036 units ÷ 27.7 ÷ 5) |
| Comparison (146.3 acres) | 0.263 (231 units ÷ 146.3 ÷ 6) | 1.650 (1,207 units ÷ 146.3 ÷ 5) |

- **DiD:** **+13.313** (90% interval +7.919 to +19.340).
- **Effect per added FAR:** **+2.197** (+1.307 to +3.191).
- **Sensitivities:**
  - second comparison: +14.523;
  - largest project left out: +9.055;
  - per 1,000 existing homes: +1,481.1 units per 1,000 homes per year. The figure is very large because the treated blocks held only 271 homes before; the comparison held 9,451.
  - original area rule (whole amendment against its ring): +9.040.

**New York limitations (both cases).**
- **Census BPS check.** This compares proposed units in Brooklyn new-building jobs, by year fully permitted, with BPS units for Kings County, as job file ÷ BPS − 1.
  - **Before years:** −31% in 1997, −28% in 1998, −33% in 1999, −34% in 2000, +11% in 2001, −27% in 2002 and +28% in 2003.
  - **After years:** −14% in 2004, −10% in 2005, +4% in 2006, −6% in 2007, −7% in 2008 and +234% in 2009. The 2009 excess is jobs authorized in 2008 and fully permitted later.
  - So the before years are undercounted by about a quarter in both treatment and comparison. The DiD compares like with like, but the before rates are low by that much.
- "Fully permitted" is when all of a job's work types are permitted. It can trail the first new-building permit.
- Downtown Brooklyn was also a city investment programme, with an office-to-housing shift and public projects; the inventory flags it as confounded.
- The treatment areas are small (19.1 and 27.8 eligible acres), so a few buildings move the rate. The interval reflects this.
- New York's market and building types are far from Wisconsin's.
- The job file now covers all five boroughs (`dob_nb_all.csv`); the Brooklyn records are the same as before.

## New York pooled set, 2003–2013 (fit)

**What was measured.**
- **Members.** The 22 upzonings in Liao (2026, Table 1: city-initiated rezonings of 2004–2013 that raised a district's aggregate residential capacity by 20% or more), plus Park Slope (2003), the plan's named 2003 member. That is 23 rezonings. Effective dates and boundaries come from City Planning's zoning map amendment layer (125th Street Corridor, 080099A ZMM, is only in that layer).
- **Each member is built like Park Slope**, within 1.5 km of its amendment, with the one area rule:
  - zoning before, after and at both ends of its window comes from yearly MapPLUTO archives (02b to 18v1). "After" is the first archive that shows the change, because PLUTO lags the map;
  - treatment is lots whose residential FAR rose and that were not already at the law;
  - lots whose FAR changed outside the member in its window are dropped;
  - jobs are the citywide DOB new-building file, placed as for Park Slope.
- **Members used: 17 of 23.** Six have no eligible treated land: Ladies Mile, Port Morris/Bruckner Boulevard, New Stapleton Waterfront, DUMBO, North Tribeca and West Clinton. Their upzoned lots were manufacturing (or otherwise not residential, commercial or mixed) before, and plan section 2 counts only residential, mixed-use or commercial land as eligible. Several large members (Greenpoint-Williamsburg 3.8 treated acres, West Chelsea 0.1, Hunters Point 4.7) keep only their small non-industrial parts for the same reason.
- **Stacking.** Units and acres are summed by event year (years since each member's effective date). Each member has 6 before years and 5 after years inside the job file (1991–2025). Each member's projects stay distinct in the resampling.
- **Totals:** treatment **574.1 eligible acres**, comparison **2,343.5 eligible acres** (summed over members). No second comparison is built for the pooled set.
- **Dose:** **+1.58 FAR**, acre-weighted over all members' treated land (the same district table as Park Slope).

**Results (units per eligible acre per year, stacked).**

| Area | Before (event years −6 to −1) | After (event years 1 to 5) |
|---|---|---|
| Treatment (574.1 acres) | 0.114 (393 units ÷ 574.1 ÷ 6) | 1.135 (3,258 units ÷ 574.1 ÷ 5) |
| Comparison (2,343.5 acres) | 0.335 (4,715 units ÷ 2,343.5 ÷ 6) | 0.299 (3,508 units ÷ 2,343.5 ÷ 5) |

- **DiD:** **+1.057** (90% interval +0.575 to +1.607).
- **Effect per added FAR:** **+0.671** (+0.365 to +1.020).
- **Sensitivities:**
  - largest project left out: +0.878;
  - per 1,000 existing homes: +35.5 units per 1,000 homes per year (PLUTO residential units before: 16,862 in treatment, 120,628 in comparison);
  - original area rule (each whole amendment against its ring): +0.111.
- **Year by year** (treatment minus comparison, less the before mean, units per eligible acre per year): event year −6 to −1: +0.07, −0.21, −0.02, +0.01, +0.08, +0.08 (no pre-trend); year 0 +0.14; years 1 to 5: +0.52, +0.49, +1.40, +2.53, +0.35.
- **Members' own estimates** (DiD, units per eligible acre per year; most have small areas and wide uncertainty): Park Slope +6.99, Downtown Brooklyn +13.31, Hunters Point +12.22, 161st Street +1.69, 125th Street +1.12, Coney Island +0.10, Hudson Yards +0.09, Jamaica +0.06, East Flushing +0.04, Kew Gardens–Richmond Hill +0.03, Pelham Parkway +0.02, Greenpoint-Williamsburg 0.00, Third Avenue–Tremont −0.09, Lower Concourse −0.23, West Chelsea −0.66, Special Forest Hills −0.94; East Fordham Road has 0.1 treated acres and no comparison.

**Limitations.**
- The eligible-land rule removes the industrial-to-residential conversions that made the biggest of these rezonings (Greenpoint-Williamsburg, West Chelsea, DUMBO, Hudson Yards' rail-yard edge). The pooled estimate describes upzoning of land that already allowed housing.
- Most members are contextual "hybrid" rezonings with modest FAR increases on residential streets (East Flushing, Kew Gardens, Pelham Parkway, Jamaica). They pull the per-FAR effect down from the two named members.
- Members from 2007–2009 have after years in the 2008–2012 slump; stacking in event time mixes calendar years.
- Comparison rings of nearby members can overlap; an overlapping lot counts once per member.
- PLUTO lag: "before" and "after" archives are chosen with margins and then checked for the change; changes before March 2003 cannot be seen.

## Philadelphia, remapping under the 2012 zoning code, 2013–2019 (fit)

**What was measured.**
- **Reform.** The City's zoning-change layer (ProposedZoning_Implementation_Public_View) lists every map change with its existing and new district, bill number, enactment date, status and origination. The reform is the City Planning Commission's district-plan remapping: bills of origination "DistrictPlan" that changed a district, enacted 2013–2020. 112 bills; **83** have eligible treated land, all enacted 2013–2019.
- **The transit overlay** (/TOD, code section 14-513) has 13 mapped polygons around Market-Frankford Line stations and no enactment dates in any layer, so it is not measured separately (deviation 8).
- **Rising density.** The remapping mostly lowered intensity (RM-1 to RSA-5 and CMX-2 to CMX-1 are the most common changes). Rising is judged from an ordering built from the City's own table of maximum height and FAR by district (`PHL_LEVEL`): for example RSA-5 (38 ft, single-family attached) < RM-1 (38 ft, multi-family) < CMX-2 (38 ft) < CMX-2.5 (55 ft) < RM-4 (FAR 3.5) < CMX-3 (FAR 5.0) < CMX-5 (FAR 12).
- **Each member (bill)** is built with the one area rule within 2 km:
  - treatment is parcels (Water Department parcels) inside the bill's enacted polygons whose level rose and that were not already at the law;
  - lots in any other enacted zoning change in the member's window (applicant, council or other district-plan bills), or whose base district differs between the March 2015 snapshot and the first snapshot after the window, are dropped;
  - comparison is the ¼-mile ring; second comparison is lots within ½ mile of SEPTA rail, subway and trolley stops whose ½-mile circle holds no treated land.
- **Outcome.** L&I new-construction permits, whole-building types only (ENTIRE, NEWCON, New Construction, New Construction (Stand Alone)); foundation, shell, fit-out and site permits are left out. One record per permit number, and one per address point, unit count and 18 months, because the 2019–2020 change of permit system left some buildings in both systems (3,565 records merged). Project = parcel id.
- **Stacking.** As for the New York pooled set: permits from 2007, so members need enactment in 2013 or later; 5 after years to 2025 need 2020 or earlier.
- **Totals:** treatment **642.2 eligible acres**, comparison **11,345.3**, second comparison **49,454.9** (summed over members; rings of neighbouring bills overlap heavily).
- **Dose: none.** Only 7.1% of treated acres are in districts with a code FAR both before and after; the rest are height-only districts. Philadelphia stays out of per-FAR pooling.

**Results (units per eligible acre per year, stacked).**

| Area | Before (event years −6 to −1) | After (event years 1 to 5) |
|---|---|---|
| Treatment (642.2 acres) | 0.154 (593 units ÷ 642.2 ÷ 6) | 1.260 (4,046 units ÷ 642.2 ÷ 5) |
| Comparison (11,345.3 acres) | 0.136 (9,246 units ÷ 11,345.3 ÷ 6) | 0.220 (12,457 units ÷ 11,345.3 ÷ 5) |

- **DiD:** **+1.022** (90% interval +0.522 to +1.658). No effect per dose.
- **Sensitivities:**
  - second comparison: +1.008;
  - largest project left out: +0.798;
  - original area rule (each bill's whole area against its ring): +0.013;
  - per 1,000 existing homes: not computed (2010 blocks for Pennsylvania are fetched; the stacked comparison areas overlap too much for a homes count to mean much).
- **Year by year** (gap less the before mean): event years −6 to −1: +0.17, 0.00, −0.10, −0.05, −0.13, +0.12; year 0 +0.32; years 1 to 5: +0.63, +0.16, +0.95, +1.29, +2.08.

**Limitations.**
- **Census BPS check** (permit-file units ÷ BPS for Philadelphia County − 1): within −7% to +23% in 2007–2015 and 2021–2024 except −21% in 2023; +38% in 2016, +40% in 2017, +24% in 2018, +78% in 2019 and +43% in 2020. The 2016–2020 excess falls in the after years of most members, in both areas. 2021 has 25,121 units (BPS 25,257), a rush before the City's tax abatement was cut, also in the after years of 2016–2020 members.
- The original area rule gives +0.01: most remapped land was lowered, and the whole bills set downzoned blocks against their rings.
- Rings of neighbouring bills overlap, so the same comparison project can be drawn in several members; the bootstrap treats them as separate, which makes the interval somewhat too narrow.
- The intensity ordering mixes height-only and FAR districts (source: the City's table; the ordering itself is a judgment, written down in `PHL_LEVEL`).
- Treated lots that are industrial before (I-2 to IRMX, CMX-3 and others) are not eligible under plan section 2.

## Raleigh, 2021 transit overlay (context only)

- **What the files show** (rezoning-case and permit layers, computed by `case_raleigh.py`):
  - The overlay text (TC-17A-20) was adopted in 2021 but applies only where mapped.
  - The City's own overlay mappings are Z-19-2022 (5 July 2022) and Z-18-2022 (16 August 2022), both "add TOD" with no base-district change, then the New Bern Avenue set Z-92A to Z-92E-2022 (March to July 2024; Z-92F denied), which also changed base districts and heights.
  - The other 19 approved TOD rezonings are applicants' conditional site rezonings ("-CU"), which select the sites about to be built and cannot serve as a treatment.
  - The housing-unit field is filled on 89–100% of new residential permits each year from 2015 to 2023 (79% in 2020), then on 7.6% in 2024, 0.1% in 2025 and none in 2026.
- **Status: context only.** The first City mapping (2022) has one after year with unit counts (2023), and it did not raise base-district density; the 2024 mappings have none.
- **Rent:** $1,572.

## Phoenix, 2015 Walkable Urban Code (context only)

- **No unit-based estimate.** The first probe (26 October 2026) found only the City's current permit map layer, which starts in 2015 and has no unit field.
- A second probe (27 October 2026) found the City's Issued Permit Data export, the old KIVA system, with permits from 1995 onward and unit counts.
- The case is measured by permit counts, as the owner asked: see the next section.
- **Rent:** $1,582.

## Permit counts for Raleigh, Phoenix and Ann Arbor (context only)

Added 2026-10-27 at the owner's request ([plan section 7](CASE_ANALYSIS_PLAN.md), entry of 2026-10-27, written before counting). These three cases have no usable unit counts, so they are measured by the **count of new residential building permits** per eligible acre per year: permits, not homes. Areas, periods, the area rule and the difference-in-differences are the same as for every other case. Single-family and multifamily permits are counted separately where the type is recorded. The rows are in `tod_case_estimates.csv` with `measure` = "permits per eligible acre per year" and status `context_permit_count`; the `estimate_units_per_acre_yr` and `*_units_*` columns hold permits for these rows. They are never pooled with unit-based cases or used to fit.

| Case | Status | Estimate (permits per eligible acre per year) | 90% interval | Permits before (treatment / comparison) | Permits after (treatment / comparison) | Eligible acres (treatment / comparison) |
|---|---|---|---|---|---|---|
| Phoenix WU, multifamily (31 rezonings effective 2016–2020) | context_permit_count | +0.0186 | +0.0098 to +0.0285 | 0 / 23 | 13 / 27 | 136.4 / 3,234.1 |
| Phoenix WU, single-family (5 rezonings effective 2016) | context_permit_count | +0.0082 | +0.0082 to +0.0082 | 0 / 23 | 0 / 0 | 10.8 / 466.7 |
| Phoenix WU, all new residential (5 rezonings effective 2016) | context_permit_count | +0.0443 | +0.0428 to +0.0459 | 0 / 23 | 2 / 2 | 10.8 / 466.7 |
| Raleigh 2024 TOD mapping (all, single-family, multifamily) | not measurable | — | — | 1 / 101 (all) | 0 / 3 (all) | 639.5 / 1,410.3 |
| Ann Arbor TC1 (held out) | no data | — | — | — | — | — |

Before and after are 6 and 5 years (Phoenix in event years, stacked). Original area rule (every WU parcel against its ring): multifamily +0.0179, single-family +0.0075, all +0.0421. Largest project left out: multifamily +0.0111, single-family +0.0079, all +0.0259. No second comparison is available: within 1.5 km of each member, no light-rail stop has a ½-mile area free of WU treatment.

**Phoenix (context, permit counts).**
- **Permits.** The City's Issued Permit Data export (the old KIVA system) for residential permits by Census structure class: 001 one unit, 002 two, 003 three–four, 004 five–nine, 007 ten or more. It covers 1995–2025, fetched by year and class (155 files).
  - New-building rows only: type RSF/RSFC (new single-family) and BLD (new multifamily building), one per permit number. Temporary certificates of occupancy and shell rows are dropped.
  - Permits are placed on Maricopa County Assessor parcels by parcel number.
  - **Check against the Census Building Permits Survey for Phoenix:** single-family 2,331 permits in 2016 against 2,479 one-unit buildings; multifamily 136 against 126 two-or-more-unit buildings.
  - The single-family series stops at 2021: from 2022 the City moved to a new system with no public archive (2022 has 1,458 single-family permits, 2023 has 9).
- **Reform land.** Current WU zoning polygons with their case numbers. The approval date comes from the City's WU list where given (20 cases); otherwise the year in the case number.
  - No layer gives the zoning before most WU rezonings, so every WU parcel counts as having risen and "already at the law" cannot be tested.
  - Parcels in other approved rezonings with a case year in the window, and parcels in other WU cases, are in no area.
  - Eligible land excludes Assessor use codes 9xxx (exempt and government).
- **Results.**
  - The multifamily series is the most informative. Treatment WU land had 0 multifamily permits in the 6 years before and 13 in the 5 years after, on 136.4 acres; the ¼-mile rings had 23 before and 27 after on 3,234.1 acres.
  - The single-family and all-permit series rest on five 2016 rezonings with 10.8 treated acres and a handful of permits; their intervals are not meaningful.
- **Caveats.**
  - Counts of permits, not homes: one multifamily permit can be 5 or 300 units. **The KIVA export does carry unit counts**, so a unit-based Phoenix measure is possible (multifamily through 2025, single-family through 2021); it was not made because the owner asked for counts.
  - Effective years from case numbers are filing years and may be a year early.
  - Many members are small: WU rezonings were mostly site-by-site, applicant-initiated, so they select sites about to be built (as in Charlotte and Raleigh), which pushes the estimate up.
- **Rent:** $1,582.

**Raleigh (not measurable, even by permit counts).**
- **Reform year.** The City's 2022 overlay-only mappings (Z-18-2022, Z-19-2022) did not raise by-right density: the overlay's extra height needs affordable units, and base districts were unchanged. The first City mapping that also changed base districts and heights is Z-92A to Z-92E-2022, approved March to July 2024. That puts the before years at 2018–2023 and the after year at 2025.
- **Why it cannot be measured.** The City's open permit layer (Building_Permits) records 497 to 966 detached single-family and multifamily permits a year in 2010–2018. It then records 6 in 2019, 34 in 2020, 1 in 2021 and none in 2022–2025: new homes are coded "townhouse" (775 in 2025), and buildings of 2 or more units vanish. Meanwhile the Census Building Permits Survey shows Raleigh authorizing 2,295 to 6,710 units a year in 5+ unit buildings (2020–2024).
  - So the layer misses most new homes in every year of the window except 2018. The counts by year are in `tod_case_rates_by_year.csv`: the comparison ring falls from 35 permits in 2018 to between 1 and 52 a year after, the kind of break a coding change produces.
- **Areas, for the record:** 639.5 eligible treated acres; 1,410.3 comparison acres; 451 other rezonings in the window are dropped.
- **Rent:** $1,572.

**Ann Arbor (held out; not measurable, even by permit counts).**
- A second probe (27 October 2026) found zoning before and after TC1: a January 2024 parcel snapshot has both, and 316 parcels went to TC1 from O, C3, C2B and other districts.
- **No permit records with locations exist before 2022:**
  - the public permit layer holds only active permits (720, issued 2022–2026; 93 new residential);
  - A2Trak (2008 to March 2022) is a search screen only;
  - STREAM refuses scripts (HTTP 403);
  - Washtenaw County's servers did not answer;
  - the Census Building Permits Survey has city totals without locations.
- The first TC1 map rezoning is April 2022, so there are no before years. A parcel year-built proxy exists but measures completions, not permits.

## Added cities, batch 1: Los Angeles, Seattle, Bellevue (2026-10-27)

Added at the owner's request ([plan section 7](CASE_ANALYSIS_PLAN.md), entries of 2026-10-27, chosen before counting) to widen the trait test. The rules, the one area rule and the outputs are the same as for every other case. The adapters are `case_la.py`, `case_seattle.py` and `case_bellevue.py`. Each city is also split into trait-test units in [reference/tod_case_units.csv](../../reference/tod_case_units.csv): station areas, or plan districts in Warner Center. Each unit's treatment lots are set against the case's comparison lots within ¼ mile, and a unit is kept with at least 5 eligible acres in each, as in `traits.py`. Batch 2 (Ottawa, Toronto, Minneapolis) is built by another work package; `run_tod_cases.py` picks up those adapters when their files exist.

All values are units per eligible acre per year, with 90% project-bootstrap intervals.

| Case | Role / status | Estimate (90% interval) | Dose | Effect per dose (90% interval) | Original area rule | Rent |
|---|---|---|---|---|---|---|
| Los Angeles Warner Center 2013 | fit, measured | +0.100 (−0.271 to +0.446) | none (no FAR in open data) | — | +0.037 | $1,933 |
| Los Angeles Cornfield Arroyo Seco 2013 | fit, measured | −0.383 (−0.939 to −0.020) | none | — | −0.228 | $1,933 |
| Seattle North Beacon Hill + Othello 2012 | fit, measured | −0.757 (−4.420 to +1.997) | +3.97 FAR (on 63% of treated acres) | −0.190 per FAR (−1.112 to +0.503) | −0.122 | $2,030 |
| Seattle Mount Baker 2014 | fit, measured | +0.449 (−0.294 to +1.315) | +4.62 FAR (on 77%) | +0.097 per FAR (−0.064 to +0.285) | +0.168 | $2,030 |
| Bellevue BelRed 2009 | context only | — (zoning before unknown) | +1.0 FAR (base, source_lead) | all-land sensitivity: +0.133 (+0.044 to +0.222) | +0.092 | $2,572 |

| Case | Years (before; after) | Eligible acres: treatment / comparison / second comparison | Units before → after: treatment; comparison |
|---|---|---|---|
| Warner Center | 2007–2012; 2014–2018 | 784.8 / 301.4 / 57.6 | 1,399 → 1,552; 4 → 1 |
| Cornfield Arroyo Seco | 2007–2012; 2014–2018 | 13.1 / 154.3 / 450.6 | 0 → 0; 4 → 299 |
| North Beacon Hill + Othello | 2006–2011; 2013–2017 | 32.4 / 343.9 / 2,472.8 | 353 → 172; 207 → 176 |
| Mount Baker | 2008–2013; 2015–2019 | 35.3 / 248.2 / 2,629.7 | 1 → 143; 185 → 596 |
| BelRed (all-land sensitivity) | 2003–2008; 2010–2014 | 504.4 / 296.5 / 235.5 | 0 → 385; 4 → 33 |

Sensitivities, as DiD in units per eligible acre per year:

| Case | Second comparison | Largest project left out | Per 1,000 existing homes |
|---|---|---|---|
| Warner Center | +0.098 | +0.096 | +14.6 |
| Cornfield | −0.599 | −0.080 | −30.4 |
| North Beacon Hill + Othello | −0.918 | +0.363 | −132.3 |
| Mount Baker | +0.607 | +0.025 | +119.0 |
| BelRed | −0.103 | +0.035 | +736.4 |

**Trait-test units (14; 13 kept).** All are DiD in units per eligible acre per year; doses are in added FAR.
- **Warner Center:** 7 plan districts. College +0.90, Commerce +0.004, Downtown +0.003, Park −0.000, Topanga +2.56, Uptown 0.00. Northvillage is dropped (no comparison land). There is no dose.
- **Cornfield:** Lincoln Heights / Cypress Park, 0.00.
- **North Beacon Hill:** +2.80 (dose +3.31).
- **Othello:** −2.79 (dose +4.13). This is one 351-unit project permitted in 2010, before the rezone.
- **Mount Baker:** +0.45 (dose +4.20).
- **BelRed, all-land, dose +1.0:** BelRed −0.02, Overlake Village +0.98, Spring District −0.06.

**Data problems and judgement calls.**
- **Los Angeles:**
  - Neither case has a FAR dose: plan-district FARs are not in open data.
  - Warner Center was zoned "WC" both before and after, so every lot counts as having risen. Its pre-period was already active (1,399 units in 2007–2012) because the 1993 plan allowed housing.
  - Cornfield was mostly manufacturing before, so only 13.1 acres are eligible treatment. Its estimate comes entirely from its comparison area, which got 237 units in 2014.
  - Some APNs are masked in the open permit data; those permits are placed by their point.
  - About 1,070 and 2,142 acres are dropped as rezoned during the window. These are site rezonings and condition edits, which in Los Angeles often come with the development being counted, so this pushes the estimates up (as noted for Charlotte).
- **Seattle:**
  - The permit file is reliable from 2006.
  - The dose covers only the non-single-family part of the treated land.
  - One 351-unit Othello project, permitted in 2010, drives the negative North Beacon Hill + Othello estimate. With it left out the estimate is +0.36.
  - The 2011 Lowrise rename and the 2019 Mandatory Housing Affordability change are not counted as local rezonings (plan section 7).
- **Bellevue:**
  - Zoning before 2009 is not published by parcel; the permit file shows today's districts even on 2000–2009 permits.
  - BelRed was mostly light industrial before (source_lead), which the eligible-land rule excludes, so the pre-registered estimate cannot be made.
  - The base FAR of 1.0 comes from the City's FAR guidance; the code site refused automated fetches.
  - Light rail opened in 2024, after the window.

## Added cities, batch 2: Toronto, Ottawa, Minneapolis (2026-10-27)

Built by a separate work package and merged here. The cases were added by the plan's entry of 2026-10-27, chosen before any permits were counted, and use every rule of the plan, including the one area rule. The adapters are `case_toronto.py`, `case_ottawa.py` and `case_minneapolis.py`. The inputs are fetched by `scripts/fetch_tod_cases_batch2.py` into `data/raw/tod_cases/<city>/` with manifests, and the tests are in `tests/test_tod_cases_batch2.py`. The rows are in `reference/tod_case_estimates.csv`; Toronto's station-area units are in `reference/tod_case_units.csv`.

| Case | Role / status | Estimate (units per eligible acre per year; 90% interval) | Dose | Trait-test units |
|---|---|---|---|---|
| Toronto, Eglinton Connects 2014 | context (boundary problem; plan section 7) | as built −0.102 (−0.336 to +0.042); with the 15 adjacent lots rezoned later +0.906 (+0.383 to +1.431) | +14.3 ft of height (no FAR dose); −0.0071 per added foot | 6 kept of 10, all flagged out of the trait fit |
| Ottawa, TD zone 2012 | context only (too few before years) | — | — | none |
| Minneapolis, Hiawatha 2008–2012 (weak design, flagged) | no data (boundaries only as PDF images) | — | — | none |

### Toronto, Eglinton Connects mid-rise rezoning, By-law 1030-2014

**Reform.** City Council enacted By-law 1030-2014 on 28 August 2014. It rezoned lots fronting Eglinton Avenue between Jane Street and Kennedy Road to CR (commercial residential) labels with no floor space index (FSI) limit, and set heights of 13.5 to 25.5 metres through 28 site-specific exceptions, numbered 2621 to 2648. The staff report describes the change as +1 to +3 storeys on 5.0 km of frontage. The case uses 2014 as the effective year. The parent Official Plan Amendment 253 was appealed and settled on 28 September 2018, so 2018 is shown as a diagnostic.

**Data (Open Government Licence – Toronto).**
- **Permits.** The City's three building-permit files are combined: cleared permits 2000–2016, cleared permits since 2017, and active permits.
  - Kept: new-construction permits with `DWELLING_UNITS_CREATED` > 0 and an issue date, one per permit number. Revision 00 carries the permit's units; later revisions are dropped. Cancelled and refused permits are dropped.
  - New construction means type New Building or New Houses, or a Residential, Multiple Use or Non-Residential Building Permit whose work is "New Building…".
  - 50,211 such permits citywide. Their units total 12,494 in 2012, 20,097 in 2013, 13,727 in 2014 and 20,759 in 2018 (units authorized citywide per year, all issue years in the files).
- **Locations.** The permit's `GEO_ID` is the City's address point id.
  - Within the case area, 13,052 permits were placed by `GEO_ID`, 408 by the same address, and 292 by the nearest house number on the same street side within 20 numbers. Big sites are re-addressed after construction, which is why the fallbacks are needed.
  - 93.2% of the permits placed within the case area fall inside a parcel.
- **Zoning.** Zoning By-law 569-2013 zone areas and height overlay (current consolidation only).
- **Parcels.** The City's property boundaries (`RESERVE` parcels excluded).
- **Stations.** TTC merged GTFS (parent stations of the subway and the Line 5 and Line 6 LRT lines).

**Areas.**
- **Treatment.** Treatment lots are parcels whose representative point lies in a zone polygon labelled with exception 2621–2648. The by-law's own diagrams are images, but every lot it rezoned received one of these exceptions.
  - The current layer has 81.2 acres of such polygons, carrying 25 of the 28 exceptions. Exceptions 2623, 2626 and 2640 no longer appear, so their lots have been rezoned again since 2014.
  - Treatment is 604 eligible parcels on 49.5 eligible acres.
- **Did density rise:** yes on every treatment lot, because the FSI caps were removed. "Already at the law" cannot be tested: no published layer keeps the labels from before 2014, so no lot is excluded for it (as for Phoenix).
- **Comparison:** 10,839 eligible parcels on 981.0 acres within ¼ mile of the treatment.
- **Second comparison:** 11,079.4 eligible acres within ½ mile of 102 TTC stations with no treated land in their own ½ mile.
- **Eligible land:** zones R, RD, RS, RT, RM, RA and RAC (residential), CR and CRE (mixed use), and CL (commercial). Open space, utility, institutional and employment zones are excluded.

**Result (2014 effective year; before 2008–2013, after 2015–2019).**
- **Treatment:** 0 units in the 6 before years and 0 in the 5 after years, on 49.5 eligible acres. Both rates are 0 units per eligible acre per year.
- **Comparison:** 282 units in the 6 before years on 981.0 acres, 0.0479 units per acre per year. After: 735 units in 5 years, 0.1498 per acre per year.
- **Difference-in-differences:** −0.1019 units per eligible acre per year (90% interval −0.3362 to +0.0417).
- **Dose.**
  - On 69.9% of the treatment acres, the exception's height exceeds the height overlay it overrides. The other lots have no recorded before height: either the exception sets no height, or the by-law itself added them to the overlay.
  - The acre-weighted added height is +4.36 metres (+14.3 ft) over that land. The FSI caps that were removed are not in the dose.
  - The effect per added foot is −0.00713 units per acre per year (90% interval −0.02352 to +0.00292).
  - There is no FAR dose, so the case stays out of per-FAR pooling, like Charlotte.
- **Sensitivities:**
  - second comparison: −0.0121;
  - largest project in each area and period left out: −0.0091;
  - original area rule: −0.1019 (the same, because no lot is excluded as already at the law);
  - 2018 effective year: −0.5595 (after years 2019–2023, driven by a comparison spike);
  - per 1,000 homes: not computed (no census dwelling counts by block were fetched).
- **Boundary sensitivity (not the plan's rule):** −0.10 becomes +0.91.
  - Add 15 lots (12.9 acres) that left By-law 569-2013 through a later site-specific rezoning, front on Eglinton, and lie within 100 metres of the by-law's lands.
  - With them, treatment goes from 0 to 312 units in the after years. The estimate becomes +0.9059 units per eligible acre per year (90% interval +0.3831 to +1.4313).

**Why the boundary matters.** In Toronto, nearly every building of any size gets a site-specific rezoning. A lot rezoned that way after 2014 loses its 1030-2014 exception, or leaves the 569-2013 layer altogether (no zone polygon). So the strict treatment holds only lots that were *not* redeveloped by rezoning. The largest Eglinton projects of the period stand on lots with no 569-2013 zone today. Examples are 1185 Eglinton Avenue East (2019, 325 + 310 units), 939 Eglinton Avenue East (2021–2025) and 1603 Eglinton Avenue West (2019, 221 units).
- The strict estimate therefore measures development that used the by-law's by-right permissions only. It is biased toward zero.
- The sensitivity measures all development on the frontage, including projects that needed their own rezoning. It is biased up, and some of the added lots may never have been in the by-law.
- Open data cannot settle which lots were in the by-law in 2014: no 2014 zoning snapshot is published, and the diagrams are images.
- **Toronto is context, not fit (plan section 7, 2026-10-27).** It stays out of any fit until the 2014 lot list is rebuilt from the by-law's diagrams (a manual step). Its 6 kept trait-test units are flagged in `tod_case_units.csv` (`trait_fit` = False) and kept out of the trait-test fit.

**Other limits.**
- Zoning before for the comparison lots is today's layer. Site-specific rezonings in the window cannot be dated from it. Lots outside 569-2013 (153.3 acres in the ¼-mile ring) are excluded from every area as rezoned outside the reform. They carried 0 units before and 2,154 after.
- Parking: Policy Area 4 to 3 (lower apartment minimums) on the corridor.
- Rent: Toronto's rent is in Canadian dollars and is not in `reference/tod_cases.csv`.

**Units for the trait test (station areas, nearest Line 5 station; plan rule ≥ 5 eligible acres in treatment and comparison).**
- **Kept (6):** Caledonia (5.66 treatment acres), Cedarvale (6.16), Fairbank (9.96), Forest Hill (5.73), Keelesdale (8.06) and Oakwood (6.91).
- **Dropped (4):** Chaplin (0.10 acres), Eglinton (1.40), Laird (2.77) and Mount Pleasant (2.79), each with under 5 treatment acres.
- Every kept unit has 0 treatment units before and after. Their effects (−0.0048 to −0.0373 units per acre per year) reflect only growth in the comparison rings. The boundary problem above applies to each unit.
- The parcels carry `h_before` and `h_after` in feet, for the unit dose. No land-use field is published with Toronto parcels, so the vacant, parking or industrial share (trait t09) is not available.

### Ottawa, transit-oriented development (TD) zone, By-law 2012-406

**Status: context only; no estimate.**
- **Permits (Open Government Licence – City of Ottawa, version 2.0).** The City's monthly construction-permit workbooks give address, dwelling units ("D.U.") and issue date, but no coordinates. They **start in July 2011**.
  - 14 files cover July 2011 to 2025.
  - Five of them (2014, 2015, 2020–2022) are old-format Excel files despite the hub's `.xlsx` name, so they are saved as `.xls`. They need `xlrd`, which is not a project dependency.
- **Reform land.** The TD zone was mapped in two steps:
  - By-law 2012-406 (Train, St-Laurent and Cyrville; consolidation date 14 November 2012): 311.6 acres of current TD polygons;
  - By-law 2014-022 (Lees, Hurdman and Blair; 22 January 2014, confirmed by the Ontario Municipal Board, PL140185): 167.3 acres;
  - 21.6 acres of later site-specific amendments.
- **Why no estimate.**
  - **Before years.** The 2012 step has 0 full years of permits before it, and the 2014 step has 2 (2012 and 2013). The plan needs 3. The permit-count fallback uses the same files, so it fails the same rule.
  - **Zoning before.** The zoning layer's `HISTORY` field lists earlier amending by-law numbers, not earlier zone codes, so whether density rose cannot be read for any lot.
  - **Parcels.** The City does not publish a parcel fabric under its open licence.
- **Trait-test units: none.**

### Minneapolis, Hiawatha (Blue Line) station-area rezonings, 2008–2012 (weak design, flagged)

**Status: no data; no estimate.**
- **Boundary.** The official rezoning maps exist only as PDF images on City pages that have since been removed (Wayback copies only):
  - 38th Street west, approved 2 May 2008;
  - 46th Street, approved 8 May 2009;
  - 38th Street east, 2012.

  No GIS layer, parcel list or zoning snapshot from 2007–2012 was found. The City's zoning layers start in January 2017 (`msvcCPED_PrimaryZoning_20170126`) and June 2023 (`PrimaryZoningArchive`). The plan's treatment is "parcels inside the official upzoning boundary", which cannot be built automatically.
- **Units.** Unit counts start in 2010 (`New_Non_SFD_Building_Permits_2010_2015`, 164 permits citywide). That is after the 2008 and 2009 rezonings and 2 years before the 2012 one, so there are too few before years for a unit-based measure.
- **Permit counts (fallback; CC0 1.0).** The yearly permit layers for 2000–2014 have points and use codes but no units.
  - **The 2011 layer holds 2012's records** (the same permit numbers), so 2011 is missing.
  - New residential building permits (type BINB with a one-family, multifamily or apartment use code) number 28 to 123 a year citywide.
  - Within ½ mile of the rezoned stations there are 0 to 4 a year (by station and year, in the adapter's diagnostics). That is too few for a rate even with a boundary.
- **What would make it measurable:** digitizing the three PDF maps (a manual, non-automated step) and accepting permit counts for 2000–2014 without 2011.
- **Trait-test units: none.**

### Data and licence notes

- **Toronto.**
  - The portal's records say "License not specified". The portal's terms page (https://open.toronto.ca/open-data-license/) puts all its datasets under the Open Government Licence – Toronto, which allows reuse with attribution ("Contains information licensed under the Open Government Licence – Toronto").
  - The older TTC GTFS package (`ttc-routes-and-schedules`) returns an empty 22-byte zip, so the merged GTFS package is used instead.
  - The portal returns 502 and 504 errors intermittently, so the fetcher retries.
- **Ottawa.** Open Government Licence – City of Ottawa, version 2.0. Attribution is required.
- **Minneapolis.** CC0 1.0 (City of Minneapolis open data), with the City's GIS accuracy disclaimer.
- Raw files are git-ignored; nothing with addresses or permit numbers is committed.

## Chicago, 2015 transit-served location ordinance (held out)

**What was measured.** This case gets its own estimate only. It is never fitted, never in a fit-set median and never in the pooled ramp.
- **Effective year: 2015.** The ordinance of 24 September 2015 widened the 2013 rules from 600 ft to 1,320 ft of a station. The 2013 ordinance falls in the before years.
- **Reform land.** It is Chicago parcels (Cook County 2021 parcels) zoned B or C with a -3 or -5 bulk suffix in the City's November 2012 zoning map, whose representative point is within 1,320 ft of a CTA or Metra stop (521 stops in the city).
  - That is 3,211 parcels. The 2,640 ft distance on Pedestrian Streets is not modelled.
- **Levels.** Allowed residential FAR by district (source_lead):
  - RS, RT and RM: 0.5 to 6.6;
  - B and C: 1.2 for -1, 2.2 for -2, 3.0 for -3 and 5.0 for -5;
  - D districts: by suffix;
  - M and PMD: 0.
  - The reform adds +0.5 to -3 districts and +1.0 to -5 districts without affordable units.
- **Already at the law.** The median new level on rising land is 3.5. Land already at 3.5 or more before is dropped: -5 districts, RM-6 and up, and D districts, 1,532.9 eligible acres.
- **Treatment:** 2,041 parcels, all -3 districts, **258.8 eligible acres**.
- **Lots dropped.** Zoning changes are read by comparing the November 2012 map with today's map. 1,753.1 eligible acres changed and are dropped. Changes after 2020 are caught too, which drops a little more than the rule needs.
- **Comparison:** **6,601.0 eligible acres**.
- **Second comparison:** **8,570.4 eligible acres**.
- **Outcome.** It is City building permits of type "new construction".
  - There is no unit field, so units are read from the work description ("41 UNIT", "8 D.U.", "SINGLE FAMILY", "TWO FLAT"). 52.4% of new-construction permits carry a readable count; the rest are garages, tents, commercial buildings and the like.
  - Permits that revise or reinstate another permit are dropped.
  - Staged permits for one building (foundation, partial superstructure, full building) are kept once when they share the same address point (within 1 m) and the same unit count and were issued within about 18 months. 340 permits were merged (deviation 4).
  - The first version merged within 50 m cells with no time limit, which also merged separate single-family homes; that is fixed.
  - **Census BPS check** (parsed citywide units ÷ BPS for the City of Chicago − 1):
    - before years: +26% in 2012, +54% in 2013 and +3% in 2014;
    - after years: +19% in 2016, +2% in 2017, +1% in 2018, −7% in 2019 and +8% in 2020;
    - in 2015 it is +19%.
    - The 2013 excess is probably staged permits at slightly different address points.
- **Dose:** **+0.50 FAR**.
- **Periods.** Before is 2009–2014, year 0 is 2015, after is 2016–2020.

**Results.**

| Area | Before 2009–2014 | After 2016–2020 |
|---|---|---|
| Treatment (258.8 acres) | 0.083 (129 units ÷ 258.8 ÷ 6) | 0.247 (320 units ÷ 258.8 ÷ 5) |
| Comparison (6,601.0 acres) | 0.045 (1,785 units ÷ 6,601.0 ÷ 6) | 0.089 (2,950 units ÷ 6,601.0 ÷ 5) |

- **DiD:** **+0.120** (90% interval −0.015 to +0.263).
- **Effect per added FAR:** **+0.240** (−0.029 to +0.525).
- **Sensitivities:**
  - second comparison: +0.161;
  - largest project left out: +0.108;
  - per 1,000 existing homes: +5.5 units per 1,000 homes per year. The homes are from 2010 census blocks: 6,030 in treatment and 193,354 in comparison.
  - original area rule: +0.528.
- Freemark (2020) found no effect on permitted dwellings over 5 years with his own difference-in-differences design (inventory note).

**Limitations.**
- Unit counts are parsed from text.
- Zoning before is the November 2012 map, and parcels are the 2021 layer.
- Stops are today's stops; a few opened after 2015.
- The 2013 ordinance is in the before years.
- Parking minimums were cut at the same time.
- Chicago, like Charlotte, often rezones lots for larger projects, so dropping rezoned lots removes some development from the comparison.

## Ann Arbor, 2021 TC1 transit corridor district (held out, no data)

- **No bulk permit file with unit counts was found** (probe of 26 October 2026, `case_annarbor.py`):
  - the public permit layer lists only about 700 active permits, with no unit field;
  - older permits sit in search-only systems (A2Trak, 2008 to March 2022; then STREAM);
  - the data.gov archive link returned "Not Found", and the City's map server returned HTTP 403.
- **Zoning:** current zoning shows 7 TC1 polygons, modified April 2022 to October 2024. Zoning before TC1 is only in the ordinance parcel lists.
- A January 2024 parcel snapshot with year built and unit counts exists. It would measure completions, not permits, and is not used.
- **Status:** held out, no estimate. It never enters a fit. **Rent:** $1,649.

## Across cases (plan sections 4 to 6)

- **Ramp (plan section 4).**
  - **Method:** the year-by-year treatment-minus-comparison gap, less its before-period mean, in units per eligible acre per year; ÷ the FAR dose where there is one.
  - **The New York pooled set is the best ramp so far**, because it already contains the two named members and 15 more rezonings. Its gap per added FAR (÷ 1.58) is: year 0 +0.09, year 1 +0.33, year 2 +0.31, year 3 +0.89, year 4 +1.61, year 5 +0.22.
  - **Philadelphia** (no dose; gap in units per eligible acre per year): year 0 +0.32, year 1 +0.63, year 2 +0.16, year 3 +0.95, year 4 +1.29, year 5 +2.08.
  - Both build over 3 to 5 years rather than arriving at once. Neither is smoothed; nothing is assumed.
  - The run script's fit-set average over Park Slope, Downtown Brooklyn and the pooled set (`_pooled_ramp_per_dose_fit_set` in the diagnostics) counts the two named members twice and should not be used.
  - Charlotte and Philadelphia do not feed a per-FAR ramp.
- **Parking (plan section 5).**
  - **Without parking cuts:** the New York cases (Park Slope 2.93, Downtown Brooklyn 2.20, pooled 0.67 per added FAR) and Philadelphia (no per-FAR value; code-wide minimums unchanged).
  - **With parking cuts:** Charlotte (no per-FAR value). Saint Paul and Raleigh are context only; Chicago is held out.
  - The cases still cannot separate TOD alone from TOD plus parking. No reading is drawn.
- **Market strength (plan section 5).** The only per-FAR values in the fit set are New York's, all at one rent ($1,821), so whether the effect rises with rent cannot be tested. The two new fit cases at lower rent have no per-FAR value: Philadelphia ($1,397) shows +1.02 units per eligible acre per year, about the same as the New York pooled set (+1.06) at a higher rent.
- **Design choice (plan section 6, AQ-047 item 1).**
  - Park Slope's design is a plain by-right FAR increase from about 3 to 6, with no mandate and parking minimums kept. It is the strongest per-FAR result (2.93), but it is one rezoning of 19 acres.
  - The pooled set, which includes Park Slope and Downtown Brooklyn, comes in at 0.67 per added FAR. The held-out Chicago case (a small +0.5 FAR bonus with parking cuts) comes in at 0.24, with intervals that do not overlap the pooled set's.
  - One case cannot set the law, and the held-out case does not confirm Park Slope's response. Under the plan's rule no design is "most effective" on this evidence, so the law falls back to the SB 79 floors unless the Madison test says otherwise. A response near the pooled set's (about 0.4 to 1.0 units per eligible acre per year per added FAR) is the better-supported range. This is reported for the owner's decision.

## Deviations

1. **Area rule changed (plan section 7, 2026-10-26).** The rule is set out in [The area rule](#how-to-read-the-numbers) above and in the plan's section 7.
   - **Reason:** it applies the eligible-land definition already decided in AQ-047 item 8, and the check showed the original rule mixed already-dense land into both groups.
   - The original-rule DiD is in every row (`sens_original_spec`).
   - **Caution:** where large projects need a site-specific rezoning (Charlotte, Chicago), dropping rezoned lots also drops development from the comparison and pushes the DiD up. The two rules bracket the answer.
   - The first version's separate New York exclusion is now covered by the uniform rule: lots in other city-initiated rezonings and non-upzoned lots in the amendment.
2. **Charlotte has no FAR dose.**
   - The plan asks for heights or densities to be converted to FAR "with the case's own code rules". Charlotte's code has no FAR for these districts.
   - The first version borrowed New York's 0.05 FAR per foot and 680 sq ft per home. Those were arbitrary for Charlotte and have been removed.
   - Charlotte reports an effect per added foot of height and stays out of per-FAR pooling.
   - A Charlotte conversion could be derived from built floor area ÷ lot area in completed TOD projects. That has not been done.
3. **New York's outcome date.**
   - Units are counted in the year the job was fully permitted, from the job-filings file, with one record per job number; the job number plays the role of the permit number.
   - The separate permit-issuance file has no unit counts.
   - The inventory listed the file as starting in 2000. It has jobs fully permitted from 1991, so the before period uses the plan's full 6 years.
4. **Chicago de-duplication beyond permit number.** Staged permits for one building have different permit numbers. They are merged only when they share the same address point (within 1 m), the same unit count and an issue date within about 18 months.
5. **Chicago effective year 2015.** The plan lists "Chicago (2013 and 2015)", but one year is needed to split before and after. 2015 is used because its distance and bonus are larger, and the 2013 rules sit in the before years.
6. **Land base vintages.**
   - Treatment and comparison are built on today's parcels in Charlotte and Saint Paul (2026) and on 2021 parcels in Chicago, not on parcels at the start. New York uses 2002 lots.
   - Charlotte's "same city" is today's city outline.
   - Zoning changes are read from the snapshots each city has: Charlotte petitions; New York yearly MapPLUTO archives; Saint Paul 2010, 2012 and 2017; Chicago 2012 and today; Philadelphia the City's zoning-change layer and base-district snapshots from 2015.
7. **Stacked cases (plan section 7, 2026-10-26).** The New York pooled set and Philadelphia are many rezonings at different dates. Each member is built with the one area rule; units and acres are summed by years since each member's effective date. Only members with 6 before and 5 after years in the data are used. The pooled set has no second comparison.
8. **Philadelphia's reform and dose.** The reform is the City Planning Commission's district-plan remapping bills of 2013–2020; the /TOD overlay has no dates and is not measured separately. Rising density is judged from an ordering built from the City's own height and FAR table. There is no FAR dose, so Philadelphia stays out of per-FAR pooling. Only whole-building permit types count, and buildings that appear in both permit systems are counted once.
9. **New York job placement.** A job's block-and-lot match is not used when the matched lot is more than 100 m from the job's own point; the job is placed by its point. This affects 37 Brooklyn jobs in the Park Slope window and 46 in Downtown Brooklyn's, and moves the Bergen Street job out of the Park Slope comparison.
10. **The New York pooled set's membership.** Liao's 22 upzonings plus Park Slope; the plan's "2003–2013" covers Park Slope, which Liao's 2004–2013 list does not.
11. **Raleigh and Phoenix are context only; Ann Arbor has no estimate.** The reasons are data, not results: see their sections.
12. **Permit counts (plan section 7, 2026-10-27).**
    - Raleigh's reform year is 2024 (the first density-raising mapping), and every lot in those cases counts as risen. The permit layer breaks in 2019, so there is no estimate.
    - Phoenix's effective years come from case numbers where no approval date exists. Every WU parcel counts as risen, and single-family data stop in 2021.
    - Ann Arbor has no permit data before 2022.

## Data problems

- **Charlotte:**
  - The county server blocks scripts, so the City's Hub copy is used.
  - Permit-file units differ from BPS by −27% to +54% across years, including +39% in before year 2013.
  - About 5% of nearby permits do not locate to a parcel.
  - Heights before are source_lead.
- **Saint Paul:**
  - Unit-level permits exist only from 2010, so the case is context only.
  - The zoning archive and the adoption date disagree on the year (2011 against 2012).
- **New York:**
  - Job-file units are about a quarter below BPS in the before years.
  - The treatment areas are small.
- **New York pooled set:**
  - Six of 23 members have no eligible treated land (upzoned land was manufacturing before).
  - MapPLUTO lags the map; snapshots are chosen with margins and checked for the change. There is no 2019 archive, so 2013's East Fordham Road ends at 18v1.
  - 14 lots in Park Slope's amendment and up to 56 in other members' have district names missing from the FAR table (`RESID_FAR`, `COMMERCIAL_EQUIV`); they are not treated.
- **Philadelphia:**
  - Permit-file units run 24–78% above BPS in 2016–2020; the permit system changed in 2019–2020.
  - 2021 is a one-year rush of 25,121 units before the tax abatement was cut.
  - The /TOD overlay has no enactment dates.
  - No FAR dose.
- **Raleigh:**
  - The housing-unit field is nearly empty from 2024.
  - From 2019 the permit layer no longer records detached single-family or multifamily permits, so permit counts fail too.
- **Phoenix:**
  - Single-family permits stop in 2021 (system change).
  - Zoning before WU rezonings is not published.
  - Effective years are partly from case numbers.
  - The old export does carry units, contrary to the first probe.
- **Ann Arbor:** no permit records with locations before 2022.
- **Chicago:**
  - There is no unit field, so units come from text parsing; about half the new-construction permits have a readable count.
  - Staged permits remain: parsed units are +54% against BPS in 2013.
  - Dose values are source_lead.
  - The zoning-change check uses today's map.

## What remains

- **New York pooled set:** a version that counts industrial-before land as eligible would show how much of these rezonings' effect came from conversions; it would need an owner decision, because plan section 2 excludes that land.
- **Philadelphia:** a per-dose figure needs a defensible FAR for the height-only districts, from the City's code or from built projects; the /TOD overlay needs its bill dates.
- **Raleigh** becomes measurable only if the City restores unit counts to permits from 2024 (or another source with units appears).
- **A FAR conversion for Charlotte** from its own code or its built TOD projects, so that Charlotte can join the per-FAR pooling.
- **Saint Paul** could become measurable only with permit unit counts before 2010. None were found in the City's open data.
- **The medium-design cases** (Los Angeles Warner Center, Bellevue BelRed, Seattle) and the Madison pre-registered test.
- **Charlotte's pre-2019 height table** should be checked against the 2018 zoning ordinance text; it is source_lead now.

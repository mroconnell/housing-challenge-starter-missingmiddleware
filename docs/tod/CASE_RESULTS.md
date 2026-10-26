# TOD comparison cases: what was measured and what it shows

Written 2026-10-26 for TOD Gate 2, work package 5, and revised the same day after an independent check. The work applies [CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md), which was written before counting, to the first four cities in its order.

- **One recorded change to the plan.** The area rule changed after the check. It is recorded in the plan's section 7, dated 2026-10-26, and summarised under [Deviations](#deviations). The results under the original rule are kept as a sensitivity.
- **Other departures** are listed under Deviations.
- **Madison** is not touched here; it has its own pre-registered step.

**Files.**
- **Code:**
  - [missing_middleware/tod/cases.py](../../missing_middleware/tod/cases.py) holds the shared measurement code, including `uniform_areas` for the area rule.
  - Each city has its own adapter: `case_charlotte.py`, `case_nyc.py`, `case_stpaul.py` and `case_chicago.py`.
  - The scripts are [scripts/fetch_tod_cases.py](../../scripts/fetch_tod_cases.py) and [scripts/run_tod_cases.py](../../scripts/run_tod_cases.py).
  - The tests are in [tests/test_tod_cases.py](../../tests/test_tod_cases.py).
- **Results:**
  - [reference/tod_case_estimates.csv](../../reference/tod_case_estimates.csv) has one row per case.
  - [reference/tod_case_rates_by_year.csv](../../reference/tod_case_rates_by_year.csv) has every area and year: before, year 0 and after.
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
- **Charlotte is the exception.** Its districts have no FAR, so its dose is added height in feet and its effect is per added foot.

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
| New York, Fourth Avenue (Park Slope) 2003 | fit | +6.980 | +4.382 to +9.732 | +2.38 FAR | +2.931 per FAR (+1.840 to +4.087) | +0.230 | kept | no | $1,821 |
| New York, Downtown Brooklyn 2004 | fit | +13.282 | +8.028 to +19.244 | +6.06 FAR | +2.192 per FAR (+1.325 to +3.175) | +9.097 | kept | no | $1,821 |
| Chicago 2015 (held out) | held out | +0.120 | −0.015 to +0.263 | +0.50 FAR (source_lead) | +0.240 per FAR (−0.029 to +0.525) | +0.528 | reduced | no for the base bonus | $1,440 |

- **Fit set.** It is the cases with role "fit" and status "measured": Charlotte, Park Slope and Downtown Brooklyn.
  - Only the two New York cases have an effect per added FAR. Their median is **2.56** units per eligible acre per year per added FAR.
  - Charlotte stays out of every per-FAR pooling (deviation 2).
  - Saint Paul is context only and Chicago is held out. Neither enters anything fitted (`cases.fit_set`).
- **Held-out check.** Chicago's effect per added FAR is 0.24 (90% interval −0.03 to +0.53). That is far below the New York median of 2.56, and the interval does not reach it.
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
- **Lots dropped.** Lots whose allowed FAR changed outside the amendment between 02b and 04c, or anywhere between 04c and 09v2 (mid 2009), are in no area: 3,166.4 eligible acres.
  - That includes South Park Slope (2005) along Fourth Avenue south of the treatment, and the many contextual rezonings of 2005–2009.
  - Changes in 1997–2002 cannot be seen, because 02b is the first archive.
- **Comparison:** **88.1 eligible acres**.
- **Second comparison:** lots within ½ mile of the 153 Brooklyn subway stations whose ½-mile circle has no treated land: **10,468.5 eligible acres**.
- **Eligible land.** It is residential, commercial or mixed (M1/R) zoning in 2002. PLUTO land use 08 (public facilities and institutions), land use 09 (open space, which includes cemeteries) and PARK are out.
- **Outcome.** It is Department of Buildings job filings for new-building jobs in Brooklyn, using proposed dwelling units.
  - There is one record per job number, counted in the year the job was fully permitted.
  - A job goes on the 02b lot with the same block and lot. If there is none, it goes on the lot containing its geocoded point, or the nearest lot within 40 m.
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
| Comparison (88.1 acres) | 0.233 (123 units ÷ 88.1 ÷ 6) | 0.425 (187 units ÷ 88.1 ÷ 5) |

- **DiD:** **+6.980** (90% interval +4.382 to +9.732).
- **Effect per added FAR:** **+2.931** (+1.840 to +4.087).
- **Sensitivities:**
  - second comparison: +6.856;
  - largest project left out: +5.299;
  - per 1,000 existing homes: +87.5 units per 1,000 homes per year. The homes are 2002 PLUTO residential units: 1,512 in treatment and 5,844 in comparison.
  - **original area rule:** **+0.230**. Here every lot in the 2003 amendment (276.2 eligible acres, mostly the downzoned brownstone blocks) is set against its ¼-mile ring (219.9 acres).
- **Note on the first version.** The first version reported "literal plan" figures of +6.883 and +11.457. Those already limited treatment to upzoned lots, so they were an alternative comparison, not the plan read literally. The whole-amendment figures above replace them.

## New York, Downtown Brooklyn, 2004 (fit)

**What was measured.**
- **Rules:** the same as Park Slope.
- **Amendment:** 040171 ZMK, adopted 28 June 2004.
- **Treatment:** 228 of the amendment's 291 lots had a higher residential FAR after, giving **27.8 eligible acres**.
  - **Before:** 182 lots C6-1, 24 lots R6 and 14 lots M1-1.
  - **After:** 144 lots C6-4, 78 lots C6-4.5 and 6 lots C6-2.
  - The median new level is 10.0. Lots already at 10.0 or more before are already at the law: 51.6 acres.
- **Lots dropped.**
  - Lots whose FAR changed outside the amendment are dropped. This includes the 18 lots (4.58 acres) just outside the amendment whose residential FAR rose from 4 to 10 between 02b and 04c.
  - Lots that changed again by 2009 are also dropped.
- **Comparison:** **145.2 eligible acres**.
- **Second comparison:** 151 stations, **10,471.4 eligible acres**.
- **Dose.** C6-1 is R7-equivalent at 4.0; C6-4 and C6-4.5 are R10-equivalent at 10.0. Dose: **+6.06**. PLUTO's maximum allowed FAR gives +4.90.
- **Periods.** Before is 1998–2003, year 0 is 2004, after is 2005–2009.

**Results.**

| Area | Before 1998–2003 | After 2005–2009 |
|---|---|---|
| Treatment (27.8 acres) | 0.000 (0 units) | 14.671 (2,036 units ÷ 27.8 ÷ 5) |
| Comparison (145.2 acres) | 0.274 (239 units ÷ 145.2 ÷ 6) | 1.663 (1,207 units ÷ 145.2 ÷ 5) |

- **DiD:** **+13.282** (90% interval +8.028 to +19.244).
- **Effect per added FAR:** **+2.192** (+1.325 to +3.175).
- **Sensitivities:**
  - second comparison: +14.485;
  - largest project left out: +9.035;
  - per 1,000 existing homes: +1,479.9 units per 1,000 homes per year. The figure is very large because the treated blocks held only 271 homes before; the comparison held 8,875.
  - original area rule (whole amendment against its ring): +9.097.

**New York limitations (both cases).**
- **Census BPS check.** This compares proposed units in Brooklyn new-building jobs, by year fully permitted, with BPS units for Kings County, as job file ÷ BPS − 1.
  - **Before years:** −31% in 1997, −28% in 1998, −33% in 1999, −34% in 2000, +11% in 2001, −27% in 2002 and +28% in 2003.
  - **After years:** −14% in 2004, −10% in 2005, +4% in 2006, −6% in 2007, −7% in 2008 and +234% in 2009. The 2009 excess is jobs authorized in 2008 and fully permitted later.
  - So the before years are undercounted by about a quarter in both treatment and comparison. The DiD compares like with like, but the before rates are low by that much.
- "Fully permitted" is when all of a job's work types are permitted. It can trail the first new-building permit.
- Downtown Brooklyn was also a city investment programme, with an office-to-housing shift and public projects; the inventory flags it as confounded.
- The treatment areas are small (19.1 and 27.8 eligible acres), so a few buildings move the rate. The interval reflects this.
- New York's market and building types are far from Wisconsin's.
- The pooled set of 23 rezonings (Liao) was not built (see [What remains](#what-remains)).

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

## Across cases (plan sections 4 to 6)

- **Ramp (plan section 4).**
  - **Method:** the year-by-year treatment-minus-comparison gap, less its before-period mean, ÷ each case's FAR dose, averaged over the fit cases that have a FAR dose (the two New York cases), in units per eligible acre per year per added FAR.
  - **Values:** year 0 +0.09, year 1 +0.84, year 2 +1.75, year 3 +1.67, year 4 +6.48, year 5 +2.07.
  - **Year 4** is driven by Downtown Brooklyn in 2008 (1,157 units on 27.8 acres).
  - **Charlotte does not feed this ramp.** It has no FAR dose, and its after-period gap rests on two projects.
  - With 2 cases from one city the ramp is not a usable shape yet. Nothing is smoothed or assumed.
  - Each case's own series is in `tod_case_rates_by_year.csv`.
- **Parking (plan section 5).**
  - The plan asks for the fit to be repeated on cases with and without parking cuts. That cannot be done yet.
  - **Without parking cuts:** the two New York cases (median 2.56 per added FAR).
  - **With parking cuts:** the one measured fit case is Charlotte, which has no per-FAR value. Saint Paul is context only.
  - The cases cannot separate TOD alone from TOD plus parking. No reading is drawn.
- **Market strength (plan section 5).** Only New York has a per-FAR effect in the fit set, so whether the effect rises with rent cannot be tested. The held-out Chicago case (rent $1,440, +0.24 per added FAR) sits well below New York (rent $1,821).
- **Design choice (plan section 6, AQ-047 item 1).**
  - Park Slope's design is a plain by-right FAR increase from about 3 to 6, with no mandate and parking minimums kept. It is above the New York median of 2.56; Downtown Brooklyn is below it.
  - The held-out case is a small bonus (+0.5 FAR) with parking cuts. It comes in at 0.24, with an interval (−0.03 to +0.53) far below.
  - The held-out case therefore does not confirm a high response. Under the plan's rule no design is "most effective" on this evidence, and the law falls back to the SB 79 floors unless the Madison test says otherwise. This is reported for the owner's decision.

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
   - Zoning changes are read from the snapshots each city has: Charlotte petitions; New York 02b, 04c and 09v2; Saint Paul 2010, 2012 and 2017; Chicago 2012 and today.

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
- **Chicago:**
  - There is no unit field, so units come from text parsing; about half the new-construction permits have a readable count.
  - Staged permits remain: parsed units are +54% against BPS in 2013.
  - Dose values are source_lead.
  - The zoning-change check uses today's map.

## What remains

- **The New York pooled set**, the 23 rezonings in Liao (2026). It needs job filings and MapPLUTO for all five boroughs. The code already takes one amendment at a time (`case_nyc.CASES`), so this is mostly a data step.
- **A FAR conversion for Charlotte** from its own code or its built TOD projects, so that Charlotte can join the per-FAR pooling.
- **Saint Paul** could become measurable only with permit unit counts before 2010. None were found in the City's open data.
- **The medium-design cases** (Los Angeles Warner Center, Bellevue BelRed, Seattle) and the Madison pre-registered test.
- **Charlotte's pre-2019 height table** should be checked against the 2018 zoning ordinance text; it is source_lead now.

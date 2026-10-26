# TOD comparison cases: what was measured and what it shows

Written 2026-10-26 for TOD Gate 2, work package 5. It applies the plan written before counting, [CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md), to the first four cities in its order. Where the work departs from the plan, the departure and its reason are in [Deviations](#deviations); the plan file itself is unchanged. Madison is not touched here (separate pre-registered step).

**Files.**
- Code: [missing_middleware/tod/cases.py](../../missing_middleware/tod/cases.py) (shared measurement), one adapter per city (`case_charlotte.py`, `case_nyc.py`, `case_stpaul.py`, `case_chicago.py`), [scripts/fetch_tod_cases.py](../../scripts/fetch_tod_cases.py), [scripts/run_tod_cases.py](../../scripts/run_tod_cases.py), tests in [tests/test_tod_cases.py](../../tests/test_tod_cases.py).
- Results: [reference/tod_case_estimates.csv](../../reference/tod_case_estimates.csv) (one row per case) and [reference/tod_case_rates_by_year.csv](../../reference/tod_case_rates_by_year.csv) (every area and year, before, year 0 and after). Neither holds parcel, permit or project numbers; a test checks this.
- Raw files (git-ignored) are under `data/raw/tod_cases/<city>/`, each folder with a `manifest.json` (URL, access time, bytes, SHA-256, licence). Run: `uv run --all-extras python scripts/fetch_tod_cases.py`, then `uv run --all-extras python scripts/run_tod_cases.py`.

**How to read the numbers.** Every rate is a *rate*: housing units in new-construction building permits, divided by acres of eligible land in the area, divided by years. The estimate is a *difference-in-differences* (DiD) of yearly mean rates: (treatment after − treatment before) − (comparison after − comparison before), in units per eligible acre per year. The interval is a *90% bootstrap interval*: whole projects are redrawn with replacement within each area, 2,000 draws, seed 20261026. The dose is *added allowed floor area ratio* (FAR): the acre-weighted mean of new maximum residential FAR minus old maximum residential FAR over the treatment's eligible land. Effect per dose is the DiD divided by the dose, in units per eligible acre per year per 1.0 of added FAR.

## Results at a glance

| Case | Role | Estimate (units per eligible acre per year) | 90% interval | Dose (added FAR) | Effect per added FAR (90% interval) | Parking minimums | Affordability mandate | City median gross rent (ACS 2020–2024) |
|---|---|---|---|---|---|---|---|---|
| Charlotte 2019 | fit | −0.406 | −0.695 to −0.119 | +2.87 (converted from height, see below) | −0.142 (−0.243 to −0.041) | removed | no (voluntary bonus) | $1,612 |
| Saint Paul 2011 | context only (1 before year) | +0.038 | −0.390 to +0.349 | +1.05 (source_lead) | +0.036 (−0.370 to +0.331) | removed near stations | no | $1,281 |
| New York, Fourth Avenue (Park Slope) 2003 | fit | +7.057 | +4.466 to +9.714 | +2.38 | +2.966 (+1.877 to +4.082) | kept | no | $1,821 |
| New York, Downtown Brooklyn 2004 | fit | +11.258 | +6.556 to +16.492 | +6.15 | +1.831 (+1.066 to +2.682) | kept | no | $1,821 |
| Chicago 2015 (held out) | held out | +0.542 | +0.117 to +0.968 | +0.65 (source_lead) | +0.831 (+0.179 to +1.484) | reduced | no for the base bonus | $1,440 |

- **Fit set** (role "fit" and status "measured"): Charlotte, Park Slope, Downtown Brooklyn. Median effect per added FAR: **1.83** units per eligible acre per year (median of 3 cases; Downtown Brooklyn is the middle value). Saint Paul is context only and Chicago is held out; neither enters this median or anything else fitted (`cases.fit_set`).
- **Held-out check.** Chicago's effect per added FAR, 0.83 (90% interval 0.18 to 1.48), is below the fit-set median of 1.83, and its interval does not reach it. It is above Charlotte's and below both New York cases.
- Median rents are the city values in [reference/tod_cases.csv](../../reference/tod_cases.csv) (ACS 2020–2024 5-year, table B25064, observed there). They are 2020–2024 values, not values at each case's start.

## Charlotte, 2019 transit-oriented districts (fit)

**What was measured.**
- *Treatment*: the 360 polygons of City Petition 2019-102 (approved 18 November 2019) from the City's Rezoning History layer; a parcel is treated when its representative point lies in one. 1,780 parcels on 1,580.1 acres (the petition states 1,782.83 acres in 1,564 parcels; the difference is mostly street and parcel-edit area). Zoning before = the polygon's ExistingZoning; zoning after = its RequestedZoning (TOD-UC, TOD-NC, TOD-CC, TOD-TR).
- *Eligible land*: of the treated 1,580.1 acres, 587.2 acres were industrial (I-1, I-2) before and are not eligible under plan section 2 (residential, mixed-use or commercial before); land uses that are parks, cemeteries, churches, schools, government, utilities or similar are also out. Eligible treatment land: **961.2 acres** (974 parcels).
- *Comparison*: parcels in the City of Charlotte (current council-district outline), not treated, whose representative point is within ¼ mile of treated land: **4,093.9 eligible acres**. Their zoning before is the Pre-UDO zoning map (in force until June 2023), replaced by the ExistingZoning of any rezoning petition approved between 18 November 2019 and 1 June 2023, so that later private rezonings do not change "before".
- *Second comparison*: parcels within ½ mile of the 27 LYNX Blue Line and CityLYNX Gold Line stops whose own ½-mile circle has no treated land (mostly uptown and Gold Line stops): **1,430.8 eligible acres**.
- *Outcome*: Mecklenburg County building permits with Census use codes 101–105 and 115 (new one-family to 5-or-more-unit buildings, the Building Permits Survey classes), units from `numunits`, one record per permit number. Large apartment buildings are permitted floor by floor; each floor permit carries that floor's units. Placeholder one-unit permits for garages, amenity areas and "shell/core" (S/C) permits in apartment projects are dropped. 95.1% of permits near the areas fall in a parcel or within 30 m of one; the rest are not counted. A project, for resampling, is the permit's parcel.
- *Periods*: before 2013–2018 (6 years), year 0 2019, after 2020–2024 (5 years).
- *Dose*: allowed residential FAR before and after from height limits and homes-per-acre caps, because Charlotte's code has no FAR for these districts (deviation 2). FAR from height = 0.0502 per foot (New York's contextual districts: R8A 6.02 FAR at 120 ft); FAR from a homes-per-acre cap = homes per acre × 680 sq ft (New York's dwelling-unit factor) ÷ 43,560. Before = the smaller of the two; after = height only (no homes-per-acre cap in TOD districts). Examples: B-2 before (40 ft, 22 homes per acre) = 0.34; TOD-UC after (130 ft) = 6.52; TOD-NC (75 ft) = 3.76; TOD-TR (50 ft) = 2.51. Heights before (about 40 ft in most base districts) are source_lead. Acre-weighted dose over eligible treatment land: **+2.87**.

**Results (units per eligible acre per year).**

| Area | Before 2013–2018 | After 2020–2024 |
|---|---|---|
| Treatment (961.2 acres) | 0.366 (2,111 units ÷ 961.2 acres ÷ 6 years) | 0.212 (1,020 units ÷ 961.2 ÷ 5) |
| Comparison (4,093.9 acres) | 0.159 (3,910 units ÷ 4,093.9 ÷ 6) | 0.411 (8,413 units ÷ 4,093.9 ÷ 5) |

- DiD **−0.406** (90% interval −0.695 to −0.119). Effect per added FAR **−0.142** (−0.243 to −0.041).
- Sensitivities (all DiD, units per eligible acre per year): second comparison −0.027; largest project in each area and period left out −0.398; per 1,000 existing homes (2010 census blocks: 3,953 homes in treatment, 12,763 in comparison) −118.2 units per 1,000 homes per year.
- Year by year, treatment land had bursts before the rezoning (903 units in 2013, 677 in 2018) on parcels already zoned for dense mixed use (MUDD or the older transit districts); after 2019 the growth moved to the ring around it (comparison: 1,848 units in 2020, 2,613 in 2023).
- Not pre-registered, shown only for context: counting industrial land too (1,538.3 treatment acres, 5,339.4 comparison acres), the DiD is −0.051.

**Limitations.**
- The comparison ring is the area most likely to receive spillover from the rezoning (the same stations, the same market). A negative DiD can mean development moved to the ring, not that the rezoning lowered building.
- The rezoning mostly re-mapped land that was already dense mixed-use or older transit zoning near the most active stations; the eligible treatment land was not a blank slate.
- County permit-file totals against the Census Building Permits Survey (BPS) for Mecklenburg County (units in all new-housing permits, permit file ÷ BPS − 1): within ±10% in 2018, 2019, 2021 and 2022; +22% in 2020; +41% in 2023 and +54% in 2024; −12% to −27% in 2015–2017. The 2023–2024 excess is in both areas; it is a known risk that floor-by-floor permits are counted differently from BPS.
- The county server refuses scripted queries; the file is the City of Charlotte's ArcGIS Hub copy of the same county layer.
- Pre-2019 heights are source_lead and the FAR conversion borrows New York's code rules (deviation 2).

## Saint Paul, Green Line 2011 (context only)

**What was measured.**
- *Treatment*: parcels within ½ mile of a Green Line stop in Saint Paul whose zoning went from a non-traditional-neighbourhood district in the November 2010 snapshot to T1–T4 in the November 2012 snapshot (the TN1–TN3 to T1–T3 renaming is not counted as a change). 941 parcels; eligible (not industrial before, not institutional land use) **271.0 acres**. Before: mostly B3 (389 parcels) and I1 (324); after: T3 (425), T4 (264), T2 (249).
- *Comparison*: parcels within ¼ mile of treated land: **1,556.2 eligible acres**. *Second comparison*: none (every rail stop in Saint Paul is a Green Line stop with treated land within ½ mile).
- *Outcome*: the City's Housing Production layer, type of work "New", new dwelling units, permit issue year. 92.4% of projects locate to a parcel.
- *Effective year*: 2011 (City Council adoption, April 2011). The City's own zoning archive does not show the change in November 2011 (0 treated parcels in T districts) and does show it in November 2012.
- *Dose*: +1.05 FAR, from district FAR values that are source_lead (B3 2.0, I1 0, T3 3.0, T4 75 ft × 0.0502 = 3.76).

**Results.** Status **context only**: permits with unit counts start in 2010, so the case has 1 before year (2010); the plan needs 3. With 2012 as the effective year it would still have only 2. Treatment 0.185 units per eligible acre per year in 2010 (50 units ÷ 271.0 acres ÷ 1 year), 0.226 in 2012–2016 (306 units ÷ 271.0 ÷ 5); comparison 0.000 (0 units) then 0.004 (30 units ÷ 1,556.2 ÷ 5). DiD +0.038 (90% interval −0.390 to +0.349); effect per added FAR +0.036. These are shown for context and are not used.

## New York, Fourth Avenue in Park Slope, 2003 (fit)

**What was measured.**
- *Treatment*: lots (MapPLUTO 02b, March 2003) whose representative point is inside the zoning map amendment 030194A ZMK (effective 30 April 2003) and whose allowed residential FAR rose between MapPLUTO 02b and 04c. This keeps the Fourth Avenue blockfronts (240 lots from R6, 70 from R7A, 6 from M1-2; 245 to R8A, 66 to R7A) and leaves out the contextual downzoning that covered most of the 5,640 lots in the amendment. Eligible: **19.2 acres** (302 lots).
- *Comparison*: lots within ¼ mile of treated land, outside the amendment's other lots and outside other city-initiated rezonings adopted in 1997–2008 (South Park Slope 2005 and Downtown Brooklyn 2004 are the nearby ones) (deviation 1): **92.0 eligible acres**.
- *Second comparison*: lots within ½ mile of the 82 Brooklyn subway stations whose ½-mile circle has no treated land and lies more than ½ mile from any other city-initiated rezoning of the window: **7,926.7 eligible acres**.
- *Eligible land*: residential, commercial or mixed (M1/R) zoning in 2002, not PLUTO land use 08 (public facilities and institutions) or 09 (open space, which includes cemeteries); parks (PARK) are out.
- *Outcome*: Department of Buildings job filings, new-building jobs in Brooklyn, proposed dwelling units, one record per job number, by the year the job was fully permitted. Jobs are placed on the 02b lot with the same block and lot, or else the lot containing or nearest (within 40 m) their geocoded point. A project is the job's block and lot.
- *Dose*: maximum residential FAR by district under the Zoning Resolution as in force 2002–2004 (the higher of the height-factor and Quality Housing wide-street maximums, no inclusionary bonus): R6 3.0, R7A 4.0, R8A 6.02, M1-2 0. Dose **+2.38**. As a check, PLUTO's own maximum allowed FAR (the largest of residential, commercial and community-facility FAR) gives +2.84.
- *Periods*: before 1997–2002 (6 years; the file has jobs fully permitted from 1991), year 0 2003, after 2004–2008.

**Results.**

| Area | Before 1997–2002 | After 2004–2008 |
|---|---|---|
| Treatment (19.2 acres) | 0.026 (3 units ÷ 19.2 ÷ 6) | 7.160 (686 units ÷ 19.2 ÷ 5) |
| Comparison (92.0 acres) | 0.223 (123 units ÷ 92.0 ÷ 6) | 0.300 (138 units ÷ 92.0 ÷ 5) |

- DiD **+7.057** (90% interval +4.466 to +9.714). Effect per added FAR **+2.966** (+1.877 to +4.082).
- Sensitivities: second comparison +6.795; largest project left out +5.366; per 1,000 existing homes (2002 PLUTO residential units: 1,522 in treatment, 6,086 in comparison) +88.6 units per 1,000 homes per year. Plan read literally (no exclusions in the comparison, deviation 1): +6.883.

## New York, Downtown Brooklyn, 2004 (fit)

**What was measured.** Same rules as Park Slope. Amendment 040171 ZMK, adopted 28 June 2004. Treatment: 229 of the amendment's 291 lots had higher residential FAR after (182 from C6-1, 25 from R6, 14 from M1-1; after: 145 C6-4, 78 C6-4.5, 6 C6-2); eligible **30.7 acres** (203 lots). Comparison: **203.6 eligible acres**; second comparison: 54 stations, **5,526.7 eligible acres**. Dose: C6-1 (R7 equivalent, 4.0) to C6-4 and C6-4.5 (R10 equivalent, 10.0): **+6.15**; PLUTO maximum allowed FAR gives +5.15. Periods: before 1998–2003, year 0 2004, after 2005–2009.

**Results.**

| Area | Before 1998–2003 | After 2005–2009 |
|---|---|---|
| Treatment (30.7 acres) | 0.000 (0 units) | 13.276 (2,036 units ÷ 30.7 ÷ 5) |
| Comparison (203.6 acres) | 0.348 (425 units ÷ 203.6 ÷ 6) | 2.366 (2,409 units ÷ 203.6 ÷ 5) |

- DiD **+11.258** (90% interval +6.556 to +16.492). Effect per added FAR **+1.831** (+1.066 to +2.682).
- Sensitivities: second comparison +13.077; largest project left out +7.473; per 1,000 existing homes (271 homes in treatment, 10,616 in comparison) +1,463.9 units per 1,000 homes per year (very large because the treated blocks held almost no homes before). Plan read literally: +11.457.

**New York limitations (both cases).**
- Brooklyn job-file totals against BPS for Kings County (proposed units in new-building jobs by year fully permitted ÷ BPS units − 1): −28% to −34% in 1997–2000, −27% in 2002, +28% in 2003, −14% to +4% in 2004–2008, +234% in 2009 (jobs authorized in 2008 and fully permitted later). The before years are undercounted relative to BPS by about a quarter in both treatment and comparison; the DiD compares like with like, but the rates are low by that much.
- "Fully permitted" is when all of a job's work types are permitted; it can trail the first new-building permit.
- Downtown Brooklyn was also a city investment programme (office-to-housing shift, public projects); the inventory flags it as confounded.
- The treatment areas are small (19.2 and 30.7 eligible acres), so a few buildings move the rate. The interval reflects this.
- New York's market and building types are far from Wisconsin's.
- The pooled set of 23 rezonings (Liao) was not built (see [What remains](#what-remains)).

## Chicago, 2015 transit-served location ordinance (held out)

**What was measured.** This case gets its own estimate only; it is never fitted, never in the fit-set median and never in the pooled ramp.
- *Effective year*: 2015 (ordinance of 24 September 2015, which widened the 2013 rules from 600 ft to 1,320 ft of a station). The 2013 ordinance falls in the before years, which pulls the estimate toward zero.
- *Treatment*: Chicago parcels (Cook County 2021 parcels) zoned B or C with a -3 or -5 bulk suffix in the City's November 2012 zoning map, whose representative point is within 1,320 ft of a CTA or Metra stop (521 stops in the city). 3,211 parcels (1,207 B3-3, 687 C1-3, 384 B1-3, 289 B3-5, others); eligible (not exempt or railroad assessor class) **485.4 acres**. The 2,640 ft distance on Pedestrian Streets is not modelled.
- *Comparison*: **8,092.1 eligible acres** within ¼ mile. *Second comparison*: parcels within ½ mile of stops whose own ½-mile circle holds no treated land (station areas with no B or C -3/-5 land near the stop): **8,869.4 eligible acres**.
- *Outcome*: City building permits of type "new construction". There is no unit field: units are read from the work description ("41 UNIT", "8 D.U.", "SINGLE FAMILY", "TWO FLAT"); 52.4% of new-construction permits carry a readable count (the rest are garages, tents, commercial buildings and the like). Permits that revise or reinstate another permit are dropped, and staged permits for one building (foundation, partial superstructure, full building) are kept once (5,437 dropped; deviation 4). Parsed citywide units against BPS for the City of Chicago (parsed ÷ BPS − 1): −13% to +14% in 2012 and 2014–2023, +39% in 2013, −34% in 2024.
- *Dose*: +0.5 FAR for -3 districts (3.0 to 3.5) and +1.0 for -5 districts (5.0 to 6.0) without affordable units (source_lead, CASE_INVENTORY.md). Acre-weighted dose **+0.65**.
- *Periods*: before 2009–2014, year 0 2015, after 2016–2020.

**Results.**

| Area | Before 2009–2014 | After 2016–2020 |
|---|---|---|
| Treatment (485.4 acres) | 0.204 (594 units ÷ 485.4 ÷ 6) | 0.982 (2,384 units ÷ 485.4 ÷ 5) |
| Comparison (8,092.1 acres) | 0.046 (2,212 units ÷ 8,092.1 ÷ 6) | 0.282 (11,401 units ÷ 8,092.1 ÷ 5) |

- DiD **+0.542** (90% interval +0.117 to +0.968). Effect per added FAR **+0.831** (+0.179 to +1.484).
- Sensitivities: second comparison +0.704; largest project left out +0.558; per 1,000 existing homes (2010 census blocks: 10,936 homes in treatment, 252,385 in comparison) +27.0 units per 1,000 homes per year.
- Freemark (2020) found no effect on permitted dwellings over 5 years with his own difference-in-differences design (inventory note). This estimate differs: it uses units on the parcels that received the bonus, against their ¼-mile ring.

**Limitations.** Unit counts are parsed from text; zoning is the November 2012 map and parcels are the 2021 layer; stops are today's stops (a few opened after 2015); the 2013 ordinance is in the before years; parking minimums were cut at the same time.

## Across cases (plan sections 4 to 6)

- **Ramp** (plan section 4): year-by-year treatment-minus-comparison gap, less its before-period mean, divided by each case's dose, averaged over the 3 fit cases (units per eligible acre per year per added FAR): year 0 +0.10, year 1 +0.51, year 2 +1.09, year 3 +0.85, year 4 +3.89, year 5 +1.43. Year 4 is driven by Downtown Brooklyn in 2008 (1,157 units on 30.7 acres). With 3 cases from 2 cities the ramp is noisy; nothing is smoothed or assumed. Each case's own series is in `tod_case_rates_by_year.csv`.
- **Parking** (plan section 5): fit cases without parking cuts (the two New York cases) have a median effect per added FAR of 2.40; the one measured fit case with parking cuts (Charlotte) has −0.14 (Saint Paul, also with cuts, is context only). This is the opposite of a parking boost, but the two groups also differ by city, market, decade and building type, so the comparison cannot separate parking from those.
- **Market strength** (plan section 5): in the fit set, effect per added FAR is higher where rent is higher (Charlotte $1,612: −0.14; New York $1,821: +2.97 and +1.83). The held-out case does not follow that order: Chicago's rent ($1,440) is the lowest of the four, yet its effect per added FAR (+0.83) is above Charlotte's. With 3 fit cases from 2 cities no rent relationship is supported.
- **Design choice** (plan section 6, AQ-047 item 1): only Park Slope's design (plain by-right FAR increase from about 3 to 6, no mandate, parking minimums kept) is above the fit-set median of 1.83. The held-out case, a small bonus (+0.5 to +1.0 FAR) with parking cuts, comes in at 0.83, with an interval (0.18 to 1.48) below the fit median. One case cannot set the law, and the Madison test is still to come. Under the plan's rule this result does not, by itself, confirm a "most effective" design; it is reported for the owner's decision.

## Deviations

1. **New York comparison areas leave out other rezonings.** The plan defines comparison as lots outside the boundary within ¼ mile. Here, lots inside the case's own amendment that were not upzoned (Park Slope's contextual downzoning) and lots inside other city-initiated rezonings adopted in the case's window (City Planning's list) are in no area, and second-comparison stations must be more than ½ mile from those rezonings. Reason: South Park Slope (2005) upzoned Fourth Avenue just south of the treatment, inside the ¼-mile ring, during the after years, and the 2003 amendment downzoned most of the ring; both would contaminate the comparison. The literal-plan estimates are reported (Park Slope +6.883, Downtown Brooklyn +11.457, against +7.057 and +11.258). Charlotte's later rezonings are *not* excluded, because there they are mostly private petitions that come with the development being counted.
2. **Charlotte's dose uses New York's code rules.** The plan asks for a conversion "with the case's own code rules". Charlotte's districts have no FAR, so FAR per foot of height (0.0502, from R8A) and floor area per home (680 sq ft, New York's dwelling-unit factor) come from New York's Zoning Resolution. The constants are in `case_charlotte.py` (`FAR_PER_FT`, `SQFT_PER_UNIT`) and apply to the Saint Paul T4 value too.
3. **New York's outcome date.** Units are counted in the year the job was fully permitted, from the job-filings file, with one record per job number (the job number plays the role of the permit number). The separate permit-issuance file has no unit counts. The inventory listed the file as starting in 2000; it has jobs fully permitted from 1991, so the before period uses the plan's full 6 years.
4. **Chicago de-duplication beyond permit number.** Staged permits for one building have different permit numbers; counting each would double or triple large buildings (parsed units ran 30–110% above BPS before this step, within about ±15% after). Kept: the first issued per 50 m cell and unit count.
5. **Chicago effective year 2015.** The plan lists "Chicago (2013 and 2015)". One year is needed for before and after; 2015 is used because its distance and bonus are larger. The 2013 rules sit in the before years.
6. **Land base vintages.** Treatment and comparison are built on today's parcels in Charlotte, Saint Paul and Chicago (2026, 2026 and 2021), not on parcels at the start; New York uses 2002 lots. Charlotte's "same city" is today's city outline.

## Data problems

- Charlotte: county server blocks scripts (Hub copy used); 2023–2024 permit-file units 41–54% above BPS; about 5% of nearby permits do not locate to a parcel; pre-2019 heights source_lead.
- Saint Paul: unit-level permits only from 2010, so context only; zoning archive and adoption date disagree on the year (2011 against 2012).
- New York: job-file units about a quarter below BPS in the before years; small treatment areas.
- Chicago: no unit field (text parsing; about half the new-construction permits have a readable count); staged permits; dose values source_lead.

## What remains

- The New York pooled set (the 23 rezonings in Liao 2026): needs job filings and MapPLUTO for all five boroughs; the code takes one amendment at a time (`case_nyc.CASES`), so it is mostly a data step.
- Saint Paul could become measurable only with permit unit counts before 2010 (none found in the City's open data).
- The medium-design cases (Los Angeles Warner Center, Bellevue BelRed, Seattle) and the Madison pre-registered test.
- The Charlotte pre-2019 height table should be checked against the 2018 zoning ordinance text (source_lead now).

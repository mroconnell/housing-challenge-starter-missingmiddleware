# Control cities with no TOD reform: plan written before looking

Written 2026-10-27 by the TOD conductor, at the owner's request ("could we add a bunch of control cities with no Tod reform so we can get a clean read of how development stayed the same or not in similar geographies and time spans to each city reform studied?"). No control-city permit series has been tabulated against any reform city before this file was committed; the commit is the timestamp. Any later change goes in section 9 with a date and a reason.

## 1. Question

For each city whose transit-area upzoning we measured, did the **whole city's** home building change after the reform differently from similar US cities that made no such reform over the same years?

Each case so far compares upzoned lots with unchanged lots inside the same city ([NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md)). That cancels the city's own market swings, but it assumes the unchanged land was itself unaffected. A comparison with other cities does not need that assumption. It checks two things:

1. **Agreement.** Is each city's own net estimate consistent with what the whole-city comparison shows?
2. **Narrowing.** Is the whole-city comparison precise enough to narrow Wisconsin's range (171 to 17,148 extra homes, 2027–2031)?

## 2. Data

- **Homes permitted:** Census Building Permits Survey, annual place files for all four regions, 2000–2025 (public domain). Total units in all structure sizes, including the Census's imputed figures for places that did not report every month. Fetched by script with a manifest; raw files are not committed.
- **Existing homes:** 2010 Census housing units by place (2010 Gazetteer place file, HU10). One count for every city, so the denominator does not move with the reform.
- **Linking:** each permit place is linked to its 2010 Census place by state and the FIPS place code printed in the 2012–2025 permit files, then carried back to earlier years by the permit file's own 6-digit place id. Places that cannot be linked are left out.

## 3. Reform cities and years

The before and after years are each city's own net-effect windows, so the two comparisons cover the same years.

| City | Reform year | Before | After | Note |
| --- | --- | --- | --- | --- |
| Charlotte | 2019 | 2013–2018 | 2020–2024 | |
| Saint Paul | 2011 | 2005–2010 | 2012–2016 | The within-city case had only 2010 as a before year; the permit survey reaches back further, so 6 years are used here |
| Los Angeles | 2013 | 2007–2012 | 2014–2018 | Two plans, same year: one test |
| Seattle | 2012 | 2006–2011 | 2013–2017 | North Beacon Hill and Othello |
| Seattle | 2014 | 2008–2013 | 2015–2019 | Mount Baker; reported separately |
| Chicago | 2015 | 2009–2014 | 2016–2020 | Held out |
| Madison | 2023 | 2017–2022 | 2023–2025 | Held out; 3 after years |

**Left out: New York and Philadelphia.** Their cases stack many rezonings with different dates (New York 2003–2013; Philadelphia's remapping in waves), so there is no single before and after for the whole city. New York also has no US city of similar size.

## 4. Control cities

A place is eligible as a control for a reform city if all of these hold:

- it is linked to a 2010 Census place and reported permits for all 12 months in every before and after year (or was imputed by the Census for all 12 months);
- its 2010 homes are between one quarter and four times the reform city's;
- it is not in the reform city's metro area (CBSA), because building can move across a city line;
- it is not one of the 58 cities in our TOD case inventory ([reference/tod_cases.csv](../../reference/tod_cases.csv));
- its state had no statewide transit-area density law in force by the last after year: Massachusetts from 2021, Oregon and Utah from 2022, Maryland and Colorado from 2024, Washington from 2025, California and Connecticut from 2026 ([research/STATE_LAWS_WEST.md](research/STATE_LAWS_WEST.md), [research/STATE_LAWS_EAST.md](research/STATE_LAWS_EAST.md));
- it is not itself one of the reform cities in section 3.

If fewer than 10 places pass the size rule, the size band widens by a factor of 1.5 on each side, repeatedly, until 10 pass.

Controls may have made local reforms we do not know about. If they did, that would make the reform cities look less different from them, so the comparison leans toward finding no effect.

## 5. Outcome and estimates

**Outcome:** homes permitted per 1,000 existing homes (2010) per year.

**Effect:** the change in the reform city's average rate, after minus before, less the same change for its controls. Each estimate is also shown as a **share of the city's homes over five years** (yearly effect × 5 ÷ 10), the unit used for the cities' own net estimates.

Two ways of choosing and weighting controls, both fixed now:

- **A. Ten matched cities.** The 10 eligible places closest to the reform city on two things measured over the before years: the average rate, and its straight-line yearly trend. Each is divided by its standard deviation across eligible places, and closeness is the ordinary distance. Controls are weighted equally.
- **B. Weighted blend (synthetic control).** From the 50 eligible places closest by the same measure (all, if fewer), non-negative weights summing to 1 are chosen to match the reform city's yearly rate in each before year as closely as possible (least squares). The effect is the average after-year gap less the average before-year gap.

**A is the main estimate.** B is reported beside it.

## 6. Uncertainty: fake reforms in cities that made none

The 90% interval comes from fake reforms. Each eligible control place is treated as if it had reformed in the same year, and the same estimate is computed with its own controls drawn from the other eligible places (never the reform city). The 5th and 95th percentiles of those fake effects give the noise band. The reform city's 90% interval is its estimate minus the 95th and 5th percentiles.

The same fake-reform spread gives a **smallest detectable effect**: the half-width of the noise band, as a share of city homes over five years.

**All reform cities together:** the average of the per-city estimates (Seattle's two tests averaged first, so each city counts once; six cities). Its interval comes from 2,000 draws, each averaging one randomly chosen fake effect per city. Seed 20261028.

## 7. Decision rules, fixed now

1. **Agreement, per city.** The city's own five-year net share ([NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md), section 2) is inside the whole-city 90% interval. The cities agree overall if at least 4 of the 6 do.
2. **Narrowing.** Each whole-city estimate is converted to a share per upzoned home by dividing by the treated area's share of the city's homes (NET_EFFECT_RESULTS section 7). The comparison can narrow Wisconsin's range only if the pooled 90% interval on that basis is narrower than the gap between the little and strong scenarios (0.055% to 5.5% of station-area homes over five years) **and** leaves out at least one of the three scenario values. Otherwise it is reported as too noisy to narrow, with the smallest detectable effect.
3. **Nothing changes without the owner.** The finalized TOD numbers (AQ-055) stay unless the owner approves a change.

**Expectation, written down now.** Most reforms upzoned under 3% of their city's homes. Even the strong scenario applied to that slice is a small share of the whole city, while whole-city permit rates swing by much more from year to year. So rule 2 will probably fail and rule 1 will probably pass because the intervals are wide. The test is still worth running, because it measures how much noise the city-to-city comparison carries, which no earlier test did.

## 8. Fixed checks

- 5 and 20 matched cities instead of 10.
- Buildings of 5 or more homes only, instead of all homes.
- Controls allowed inside the reform city's metro area.
- A fake date: each reform city's estimate with a pretend reform 4 years before the real one. Before = the 6 years before the pretend year; after = the 3 years between it and the real reform. An effect there would mean the method picks up differences that are not the reform.

## 9. Changes after writing

None yet.

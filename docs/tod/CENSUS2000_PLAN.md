# Adding the 2000 census: Old City's 2006 height cap, and before-trends for every census case. Plan written before counting

Written 2026-10-28 by the TOD conductor, after the owner pointed out that the 2000 census is available ("you know you can look at the 2000 census"). No 2000 count has been tabulated for any area here before this file was committed. Changes go in section 6 with a date and a reason.

## 1. Data

- **2000 Census Summary File 1, by block** (public domain), fetched by script from census.gov. The Census API now requires a key, so it is not used.
- **Homes:** table H1 (housing units), file segment 37.
- **Location:** each block's internal point, from the geographic header (INTPTLAT, INTPTLON).
- **Land:** AREALAND (square metres).
- **2010 and 2020 blocks:** as in [CENSUS_CASES_PLAN.md](CENSUS_CASES_PLAN.md).
- **Placement:** each year's blocks are placed by their own internal point (centre point), so no block crosswalk is needed.

## 2. Old City, Philadelphia: the 2006 height cap (Stacy et al. tightening entry)

- **Treated land:** the City's current "/CTR Center City Overlay District – Old City Residential" polygons (Area, Core, Central and Bridge Approach), from the City's zoning overlay layer. The 2006 bill extended this district north to Wood Street and set its height controls. The current boundary may include later edits; this is recorded as a limit.
- **Comparison land:** blocks within ½ mile of the overlay, outside it.
- **Estimate:** change in change, per acre. That is, net homes per acre added 2010→2020 minus 2000→2010 on the treated land, less the same for the comparison land.
  - A binding cap shows as a negative value.
  - The 2000→2010 decade includes 4 years after the 2006 cap, so the "before" decade is partly treated. This leans toward finding no effect.
- **Uncertainty:** blocks resampled within each group and year, 2,000 draws, seed 20261034.

## 3. Before-trends for every census case

For each reform in the census set ([CENSUS_CASES_RESULTS.md](CENSUS_CASES_RESULTS.md) section 6), with the same treated and comparison areas:

- **2000–2010 difference:** net homes per acre, treated minus comparison.
- **For reforms adopted in 2010 or later**, this is a check on parallel trends: values near zero support the 2010–2020 result. Values far from zero mean the land was already diverging before the reform.
- **For reforms adopted 2003–2009** (New York's 2008–2009 rezonings, Milpitas 2008, Austin 2006–2009, Bellevue 2009), the change in change (2010–2020 difference minus 2000–2010 difference) is also reported. It is labelled "before decade partly after adoption".
- **Reported, not judged:** the share of reforms whose 2000–2010 difference is within ±1 net home per acre over the decade.

## 4. How it is used

Context for the census results. No finalized TOD number (AQ-055) changes without the owner.

## 5. Outputs

- `reference/tod_census2000_trends.csv`
- `reference/tod_old_city_2006.csv`
- `docs/tod/CENSUS2000_RESULTS.md`

## 6. Changes after writing

None yet.

## 7. Addition requested by the owner: Pasadena and Culver City (written 2026-10-28, before counting them)

The owner asked not to disregard two single-family size caps from Stacy et al.'s list of tightening reforms. Both are measured with the same 2000/2010/2020 change in change as Old City (section 2).

- **Pasadena, Lower Hastings Ranch (2016).**
  - The single-storey rules apply through the neighbourhood overlay ("ND"). The 1991 overlay was revised after the 2015 moratorium and the 2016 council action.
  - **Treated land:** the City zoning layer's RS-6 ND polygon.
  - **Comparison land:** the City's single-family-zoned polygons within ½ mile, outside it.
  - The 2010–2020 decade includes about 4 years after the change.
- **Culver City, house-size limits (first council step December 2015; ordinance 2016).**
  - The rules apply to single-family lots citywide.
  - **Treated land:** parcels with a single-family use code (01xx) in Culver City, from the Los Angeles County Assessor parcel layer (geometry and use code only; no parcel numbers or addresses are kept).
  - **Comparison land:** single-family parcels in other jurisdictions within ½ mile of the Culver City line (mostly the City of Los Angeles). Los Angeles tightened its own single-family size rules in 2008 and 2017, which leans the comparison toward finding no effect.
- **Expectation, written now:** close to zero for both. These caps limit the size of houses, not the number of homes, except through second units and lot splits.

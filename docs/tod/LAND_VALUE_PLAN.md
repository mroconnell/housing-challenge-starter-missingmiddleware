# Does a project pay for itself? Land values on every lot. Plan written before fetching

Written 2026-10-29 by the TOD conductor, at the owner's request (the Terner Center's SB 9 approach, "that's smart"; "run land value plan concurrently"). No land value beyond New York's and Chicago's has been fetched, and no feasibility number computed, before this file was committed. Changes go in section 8 with a date and a reason.

## 1. Question

For each lot, under the rules before and after the reform: would a new apartment building be worth more than it costs to build, including buying the lot? An upzoning should matter most where it turns "doesn't pay" into "pays". This adds a lot trait to the lot model ([LOT_MODEL_PLAN.md](LOT_MODEL_PLAN.md)), and the same trait for Milwaukee and Madison lots when the model is applied to Wisconsin.

## 2. The calculation (per lot, old rules and new rules)

| Item | Formula | Unit |
| --- | --- | --- |
| Homes allowed | allowed floor area ÷ 1,000 sq ft per home (floor-area-ratio cities); elsewhere lot acres × the training cities' 99th-percentile homes per acre (as the lot ceiling, item 12) | homes |
| Value when built | homes allowed × tract median gross rent × 12 months ÷ 5% cap rate | dollars |
| Cost to build | homes allowed × Census permit-survey construction value per home in 5+ home buildings, that city, year before the reform | dollars |
| Cost to buy the lot | the lot's market value before the reform (section 3) | dollars |
| **Margin** | value − cost to build − cost to buy | dollars |
| **Pays** | margin > 0 | yes / no |

**Traits added to the model:**
- pays under old rules (yes/no), pays under new rules (yes/no), and "flips" (no → yes);
- margin per acre, old and new, and the change, in dollars per acre (log-scaled with sign);
- lot market value per acre before (dollars per acre).

## 3. Lot market value before each reform

Only values dated before each case's window are used (lot plan item 1). Assessed values are turned into market values with each assessor's published level of assessment.

| City | Source | Snapshot | Assessed → market |
| --- | --- | --- | --- |
| New York | MapPLUTO archive (already in the lot table) | before each rezoning | Department of Finance market value where present; else assessed ÷ class ratio (6% class 1, 45% classes 2 and 4) |
| Chicago | Cook County assessed values 2012 (already in the lot table) | 2012 | ÷ 10% residential, ÷ 25% commercial |
| Philadelphia | Office of Property Assessment certified values history | year before each member's bill (2014 on; earlier members get the missing flag) | market value as published (assessed at 100%) |
| Seattle, Bellevue | King County Assessor value history extract | year before each reform | appraised value as published (100%) |
| Saint Paul | Metropolitan Council regional parcel archive (Ramsey County) | 2010 | estimated market value as published |
| Charlotte | Mecklenburg County assessor | 2018 or the nearest earlier public snapshot | as published (100%); missing flag if no pre-2019 snapshot is public |
| Los Angeles | Los Angeles County Assessor parcel data, roll 2012 | 2012 | **flagged:** Proposition 13 keeps assessed values far below market for long-held lots, so the value is kept but marked "assessed, not market" |
| Madison | Wisconsin statewide parcels (V8, 2022 values) | 2022 | ÷ the city's published ratio of assessed to equalized value |
| Milwaukee (application only) | Wisconsin statewide parcels, latest version | latest | ÷ the city's ratio of assessed to equalized value |

Lots without a usable value get the city median per acre and a missing flag, as for other traits. No owner names are kept; no parcel ids are committed.

## 4. Data rules

- Raw files go under `data/raw/` and are never committed.
- Only public downloads; no account creation; no bot-protection bypass. If a source needs either, that city gets the missing flag and it is reported.
- Licences are recorded in each raw folder's manifest.

## 5. Checks before use (standing checks, [CHECKS.md](CHECKS.md))

- **Units:** market value per acre within $1,000 to $500 million; margin computed in dollars, not thousands.
- **Two sources:** each city's median lot value per acre against the tract median home value × homes per acre, as a rough cross-check.
- **Ask why:** the 10 lots with the largest margin change in each city, by group.

## 6. How it is judged

- The lot model is rerun with these traits (causal forest and boosting, rebuilt table, same holdouts, old and new rules, plus the two robustness checks of lot plan item 19).
- Reported beside the run without them. It counts as helping only if the pass holds and the fold mean error falls.
- Also reported, as context: the share of upzoned lots that flip from "doesn't pay" to "pays", by city, and whether flipping lots built more often than others.

## 7. Limits stated up front

- Rents and construction costs are tract- or city-level, not project-level.
- One cap rate (5%) for every city and year; a 4% and 6% sensitivity is reported.
- Assessed values lag markets and differ by assessor; Los Angeles is the weakest.
- This is a rough "is the limit likely to bind" test, not a developer pro forma.

## 8. Changes after writing

1. **2026-10-29, after checking sources, before any value was read: what each source actually offers.**
   - **King County:** the value-history extract (land and improvement values by tax year). Tax year N holds values as of 1 January of year N−1, so the snapshot used is tax year = reform year (values from the year before).
   - **Philadelphia:** certified values exist from 2015 only (2013 and 2014 hold a few dozen rows). Members whose bill came before 2016 get the missing flag.
   - **Saint Paul:** the 2010 regional parcel archive is no longer published (old link gone, new hub starts 2021). Missing flag.
   - **Charlotte:** no public pre-2019 snapshot found. Missing flag.
   - **Los Angeles:** County Assessor roll 2012 from its public table (land, improvement, centre point), queried for the two plan areas only. Still flagged "assessed, not market" (Proposition 13).
   - **Madison:** Wisconsin statewide parcels V9 (2022 tax roll), not V8 (which holds 2021). Market value = the release's estimated fair market value field, which already divides assessed value by the state's assessment ratio.
   - **Milwaukee:** the latest statewide release (V12), same market value field.
   - **New York:** MapPLUTO archives carry assessed values only. Market value = assessed ÷ the Department of Finance class ratio (6% class 1; 45% classes 2 to 4). Where the Finance market-value roll covers the year (fiscal 2010/11 on), its full value is used instead.
   - **Chicago:** Cook County 2012 levels of assessment: 10% residential (classes 1 to 3), 25% commercial and industrial (class 5).
2. **2026-10-29, written while coding, before any value was read.**
   - **Cities without floor area ratios** (Charlotte, Philadelphia, Los Angeles, Bellevue): homes allowed come from the per-acre ceiling under both rules, so their margin does not change with the reform; "flips" can only happen in floor-area-ratio cities. Their lot value per acre and margin level still enter as traits.
   - **New York class:** class 1 (6%) is taken as residential lots with 3 or fewer homes; all other lots use 45%.
   - **Matching values to lots:** by the lot's point inside the source parcel polygon (King County, Wisconsin), or the nearest source point within 30 m (Philadelphia) or 40 m (Los Angeles). Unmatched lots get the missing flag.
3. **2026-10-29, after checking the Terner Center's method, before any land-value result was read.** The Terner SB 9 report (July 2021, page 6) estimated existing property values with MapCraft Labs' model "in combination with tax assessor data", drawing on CoStar, Zillow, assessors, Census and sales records; it does not say how Proposition 13 was handled, and the model is not public. To stay open and repeatable, **Los Angeles lot values are scaled to market by tract**: factor = the tract's census median home value (5-year ACS before the reform, already on each lot) ÷ the tract median of assessed value per home on lots with at least one census home (LA lots carry no use class), assessed value ÷ the lot's census homes; a tract is identified by its ACS rent and home-value pair. The factor is bounded to 1–10 and applied to every Los Angeles lot in the tract; tracts without enough residential lots (fewer than 5) take the plan area's median factor. The "assessed, not market" flag stays on as a record. Other cities are unchanged (their sources are market or near-market values). The land-value runs started before this change were stopped before finishing and are not reported.

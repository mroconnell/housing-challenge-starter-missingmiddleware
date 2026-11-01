# TOD station-area measure: plan (logged before any count, 2026-11-01)

Owner, 13:06: "try the station-area measure - go for it concurrently and retrain one fast fit and fix model to check for errors and iterate/improve quickly before we do a big run all the models." This runs beside the map-based test in [NEW_REFORM_CITIES_PLAN.md](NEW_REFORM_CITIES_PLAN.md). The tool's central line (1,196) does not change from this work until the owner decides.

## The measure

For each reform, the **station-area share** S is the share of the **whole city's** new homes, in permits, built within ½ mile of a rail or bus rapid transit stop. Stops count if they were open, or planned with a dated source, on the reform date (owner rule of 2026-11-01). Lots are counted whether or not they were upzoned.

- **Windows:** as the lot model: before = the 6 years before the reform; after = the 5 years after. A second version starts the after window at line opening.
- **Change:** ΔS = S after − S before.
- **No zoning maps.** Maps are used only later, to place homes within station areas.

**Why:** it counts spillover onto nearby lots that were not upzoned. It is the unit of the tool's Wisconsin baseline ("homes near stops"). And it needs only stop locations and dates.

## Cases

- **The 9 lot-model cities:** New York, Philadelphia, Charlotte, Saint Paul, Seattle, Los Angeles, Chicago, Madison, Bellevue.
- **The new cities:** Denver 2018, Portland 2018 and 2020, Austin (the regulating plans), Salt Lake City 2010.
- **No-reform cities as placebo:** Milwaukee, Columbus, Kansas City, Madison outside the overlay. Each gets a fake reform date, as in the lot model.
- **The city is the unit:** a city's cases are averaged.

## Comparison and noise controls (fixed now)

- **Placebo station areas:** station areas in the no-reform cities, and new stations that had no reform, such as Salt Lake City's 15 TRAX stations outside the city. These measure how much S moves with no reform.
- **Downtown:** every result is shown with and without stops within 1 mile of the city hall point.
- **New lines:** each case records whether its stops opened within 3 years of the reform. Opening years may differ in the comparison.

## Fast fit-and-fix model (one, iterated)

- **First:** the city-level rule ΔS = a + b × (S before − 0.5), fitted leaving one reform city out (the drift form, on the new measure).
- **Then:** the same rule plus "reform coverage", the share of station-area land the reform upzoned. It is filled only where a map exists; otherwise it is left blank and flagged.
- **Score:** median |log(predicted S after ÷ actual S after)| over held-out cities, against same share and average change.
- **After each run:** check for errors and outliers, fix, rerun, as in the earlier loops. No numbers go into the tool from this step.

## Data needed

Citywide permit files with home counts and locations for each city, and dated stop lists. A first inventory of what the existing case downloads already hold is the first step. Gaps are logged before any share is computed.

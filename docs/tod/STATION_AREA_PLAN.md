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

## Pre-registration (audit list, 2026-11-01 13:07; adopted before any count, and it overrides the sections above where they differ)

1. **Outcome per city:** the change in the share of citywide new homes within ½ mile of the reform's stations, in share points.
2. **Station lists are fixed and committed first.** Planned stops count, with `stop_open_at_reform` recorded and the source for each list.
3. **Controls:** rapid stops in the same city with no reform. Effect = change in reform station areas − change in control station areas. A lot within ½ mile of both goes to the nearest stop. Cities with no control stops are flagged. No-reform cities are kept as a separate placebo check.
4. **Downtown:** stops within 1 mile of city hall count as downtown. The main version includes downtown, because that is where Wisconsin's near-stop homes are. A version without downtown is the second.
5. **Denominator:** citywide permits from one source per city. The 9 cities' lot tables cover only their study areas, so citywide counts come from each city's full permit download where it holds the whole city. Where it does not, the Census permit survey place total is used, and the case is flagged "mixed sources". The source is listed for every city.
6. **Windows:** as the lot model, with a second version starting at line opening.
7. **Wisconsin formula (fixed now).** For each Wisconsin place with main-case stops:
   - extra homes = predicted change in share points × that place's citywide all-housing baseline for 2027–2031 (shared baseline v3);
   - summed over places.
   - The station definition is the one behind the 14,654 baseline (rail and rapid ½ mile, 15-minute bus ¼ mile).
   - The share before is each place's 2019–2024 share of new homes in its near-stop area: Milwaukee and Madison from the lot data, other places from the state's near-stop share × 1.24, as in the re-base.
8. **Training and holdout:** train on the 9 cities. Denver, Portland, Austin and Salt Lake City are held out and scored the same way, with the city as the unit.
9. **The fast fit-and-fix model:** "ΔS rule": change = a + b × (share before − 0.5) + c × reform effect from controls, fitted leaving one city out. Its score is median |log(predicted S after ÷ actual)|. The number is for finding errors only; it is not a tool line. After each run the sanity flags are run and the worst miss is traced.
10. **Framing (as in AQ-068):** like the lot share, this measure cannot tell homes that moved from new homes.

The central line (1,196) stays until this is tested. The Austin and Salt Lake City conditions in NEW_REFORM_CITIES_PLAN.md still apply.

## Committed before any count (2026-11-01)

- **Station lists** (`reference/tod_station_area_stations.csv`, built by `scripts/run_tod_station_area.py --stage stations`). Every rail or rapid stop inside each city's 2024 Census place boundary, from the national transit map's rail stops, LA's G Line, Wisconsin's rapid stops, Denver's RTD stations and Portland's MAX and Streetcar.
  - Reform stations are within ½ mile of the case's upzoned land; control stations are the city's others. Downtown means within 1 mile of city hall.
  - Counts, control / reform: New York 425/122, Philadelphia 335/229, Charlotte 21/23, Chicago 96/182, Los Angeles 212/17, Seattle 31/3, Saint Paul 4/10, Madison 27/105, Bellevue 3/3, Denver 30/5, Portland 19/116, Austin 4/5, Salt Lake City 13/16. Milwaukee has 83 control stations (no reform; placebo).
  - `stop_open_at_reform`: known for Austin and Salt Lake City (no), Denver and Portland (yes). For the 9 cities it is filled from the lot model's case notes when the shares are run.
- **Citywide permit inventory** (`reference/tod_station_area_permit_inventory.csv`). Every city has a whole-city file except Los Angeles, whose downloads hold the reform areas only. Los Angeles uses the Census permit survey place total as its denominator and is flagged "mixed sources; no control stations". Chicago's units are parsed from text, as in its case adapter. Salt Lake City's homes are completions.

# Parking: lot-level test with five reform cities, plan written before counting

Written 2026-10-28 by the parking conductor. Ryan approved collecting more parking-repeal cities ("sure"). No permit outcome for the new cities has been computed before this file was committed. Changes go in the last section with a date and a reason.

## 1. Cities and lots

Each city has "pinched" lots, where the old parking rule most likely limited building, and "comparison" lots, where it rarely did.

| City | Reform in effect | Pinched lots | Comparison lots | Before | After |
| --- | --- | --- | --- | --- | --- |
| San Francisco | 2019 (citywide removal) | Parcels zoned RH-2, RH-3, RM-1 to RM-4, NC-1 to NC-3, NC-S, RC-3, RC-4 | Parcels zoned RH-1 and RH-1(D) (one home per lot) | 2014–2018 | 2020–2024 |
| Buffalo | 2017 (Green Code, citywide) | Assessment property classes 220–289 (2+ family) and 400–499 (commercial) | Class 210 (one-family homes) | 2012–2016 | 2018–2022 |
| Minneapolis | 2015 (near transit) | Parcels within ½ mile of a light-rail station, outside downtown (1.5 km) | Parcels ½ to 1 mile from a station | 2010–2014 | 2016–2019; 2020 on is left out because of the citywide 2040 rezoning |
| Seattle | 2012 | From the parking lot test: inside urban villages | Outside villages, same TOD units | as in [LOT_TEST_PLAN.md](LOT_TEST_PLAN.md) | |
| Chicago | 2015 | Within 402 m of a station | 402–805 m | 2009–2012 | 2016–2020 |

**San Francisco:** parcels in districts that already had no minimums before 2019 are left out: C-3, the neighborhood commercial transit (NCT) districts, residential transit-oriented (RTO), urban mixed use (UMU), mixed-use residential (MUR) and the other Eastern Neighborhoods districts.

**Known confounds:**
- **Buffalo:** the parking repeal was part of a full rezoning (the Green Code).
- **Minneapolis:** the 2015 change also halved minimums for larger buildings.

Both are reported.

## 2. Data (all public domain or CC0, fetched by script)

| City | Permits | Lots |
| --- | --- | --- |
| San Francisco | DataSF Building Permits (`i98e-djp9`, PDDL): issued date, existing and proposed units, block and lot | DataSF Parcels – Active and Retired (`acdm-wktn`, PDDL), with zoning |
| Buffalo | OpenData Buffalo Permits (`9p2d-f3yt`, public domain): issued date, units added and lost, parcel id (SBL), location | Assessment roll 2025 (`mn64-uxt6`, public domain): SBL, front, depth, acres, property class, units |
| Minneapolis | CCS Permits (MapIT Minneapolis, CC0): issued date, new and eliminated dwelling units, APN, location | Hennepin County parcels (licence to be checked before use) |

Station locations come from the National Transit Map rail stops (TOD's file).

## 3. Outcome

Net new homes permitted on a lot in a year: new units minus units lost. A lot is "built" in a year if any permit adds units to it.

## 4. Tests

1. **Effect in each city:** (after − before) for pinched lots minus (after − before) for comparison lots, per 1,000 lots per year, for lots built and for homes. 90% range: 2,000 bootstrap draws of 500 m grid cells.
2. **Prediction with five cities:**
   - **Method:** TOD's run-E way. For each method there are separate models for pinched and comparison lots, each in two parts (the chance of building, then homes if built).
   - **Inputs common to all five cities:** log lot area, lot width (or front), distance to the nearest rail station, and new homes permitted within 250 m in the before period.
   - **Methods:** the same 8 as before.
   - **Held out:** each city in turn. Its "extra homes" is the pinched-lot model's prediction minus the comparison-lot model's prediction, summed over its pinched lots.
   - **Plain average:** the other four cities' actual extra homes per pinched lot.
   - **Pass rule:** beat the plain average and "guess zero" on mean miss, and beat the plain average in at least 3 of 5 cities.

## 5. Use

- **If a method passes:** it goes to Ryan as a candidate for predicting Wisconsin lots. That would need Wisconsin parcels in the same form.
- **If none passes:** the result is reported, and the tool keeps its range.

## Changes after writing
- **2026-10-28, while collecting data (before any outcome was computed):**
  - **Minneapolis dropped.** Its permit files before 2017 do not record home counts, so it has no before-period outcome. That leaves four reform cities, and the pass rule becomes "beat the plain average in at least 3 of 4 cities".
  - **San Francisco:** the main outcome counts new-construction and demolition permits. Alteration permits that add units, mostly accessory dwelling units under the city's 2014 program, are reported separately, because that program reached the comparison lots too.
  - **Buffalo:** lots are classed by their previous assessment class where it differs from the current one, because the 2025 roll shows classes after any construction.
  - **Prediction outcome:** the change in a lot's homes permitted per year (after minus before), with one model for pinched lots and one for comparison lots. This replaces the two-part model, because the parking effect is a change over time.
- **2026-10-28, added after the results, at Ryan's request ("can we reduce the number of lots by only looking at lots near transit"):** a second run keeps only lots within 805 m (½ mile) of a rail station in every city. Chicago and Seattle are already inside that distance. It is reported beside the main run, with the same rules. Script option: `--near-transit`.

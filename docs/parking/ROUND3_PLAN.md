# Parking: third round of variables. Plan written before testing

Written 2026-10-27 by the parking conductor, after Ryan approved one more round. Its purpose is to code the old minimum, test it with the untested variables, and make a best attempt at transit distance and contiguous eligible sites. It builds on [EXPANDED_PLAN.md](EXPANDED_PLAN.md) and [EXPANDED_RESULTS.md](EXPANDED_RESULTS.md). Everything below is fixed before any new variable is joined to an effect. Changes go in section 7 with a date and a reason.

## 1. Question

Does any of these variables predict the effect of removing parking minimums better than one average, on places left out of the fit?
- how much the old minimum required;
- transit access;
- land in surface parking;
- the variables already in hand but untested.

## 2. Sample

The 71 US places in `reference/parking_expanded_effects.csv` (all units; weight = homes × after-years). The sample is unchanged.

## 3. Variables (fixed now)

**V1–V3. Old minimum, coded from each place's ordinance in force just before repeal:**
- **V1:** spaces required per apartment, for a typical 2-bedroom unit in a multifamily building;
- **V2:** spaces required per single-family home;
- **V3:** V1 relative to the typical minimum of the time, 1.5 spaces per apartment. This only rescales V1, so it is reported but not counted as a separate test.

The coding is in `reference/parking_old_minimums.csv`, with sources and confidence. Places whose old minimum cannot be found get no value and drop out of that test only.

**V4–V7. From ACS 2020–2024:**
- **V4:** renter share (B25003);
- **V5:** vacancy rate (B25002);
- **V6:** share of homes built before 1960 (B25034);
- **V7:** share of homes in buildings of 5 or more units (B25024).

**V8–V10. From Census permits before repeal:**
- **V8:** share of permitted units in 5+ unit buildings;
- **V9:** construction value per permitted unit, relative to the state;
- **V10:** year-to-year volatility of the permit rate (coefficient of variation).

**V11–V15. From our own records:**
- **V11:** repeal year;
- **V12:** an earlier partial reform recorded in the ordinance check;
- **V13:** zoning rewrite at the same time;
- **V14:** share of the state's population in large cities that had already repealed;
- **V15:** Census region.

**V16. Transit access.** The share of the place's homes in census block groups whose centre lies within ½ mile of a fixed-route transit stop in the federal National Transit Map. This is a place-level stand-in for distance from transit: Census permits have no locations. "Frequent" service cannot be measured nationally from that map, so any stop counts. That limitation is stated.

**V17–V18. Surface parking, from OpenStreetMap parking areas inside the place:**
- **V17:** share of land in surface parking;
- **V18:** share of that parking in large contiguous sites (2 acres or more after joining lots within 30 metres).

These are a stand-in for "contiguous eligible sites": a national parcel and zoning file does not exist. OpenStreetMap is under the ODbL, so the derived per-place table is published under the ODbL with attribution, and this is recorded in DISCLOSURES.

**Distance from transit, per permit (California).** Using the AB 2097 geocoded permits (TOD's pipeline, group P jurisdictions), the effect is estimated separately for permits 0–¼, ¼–½ and ½–¾ mile from a major transit stop. Each band is compared with the 1–1½ mile ring, 2023–2025 against 2018–2022, permits per 1,000 existing homes per year, with jurisdiction resampling. The question is whether the effect falls with distance: the slope across bands, with a 90% interval.

## 4. Test

- **Single-variable models:** each of V1, V2 and V4–V18 on its own, in a weighted straight-line model. The score is the left-out error (10-fold cross-validation, 20 repeats, seed 20261027), compared with one average. A variable passes if it cuts that error by at least 5% and its slope's 90% interval excludes zero.
- **All variables together:** the tools from the expanded plan (weighted regression, lasso, random forest, honest causal forest), now with all variables, scored the same way. A tool passes at a 5% gain.
- **Checks:** V4–V7 and V16 are also tested on the California cities where they exist, as in the trait plan. The old minimum and permit-history variables have no California counterpart.
- **Reporting:** every variable and tool is reported, pass or fail.

## 5. Use

- **If the old minimum (V1) passes:** I propose to Ryan coding Wisconsin places' current minimums, so the effect can vary by place. That goes to him as a decision.
- **If any other variable passes:** it goes to Ryan as a decision before the tool changes.
- **If nothing passes:** one average stays.

## 6. Interim decision on the high end

Ryan accepted the recommendations ("I take your recommendations"). I read that as including option A. So the tool's high end updates now to the 71-place estimate (+1.54 per 1,000 homes per year, about 20,672 permits over 2027–2031), and this round can only refine it.

## 7. Changes after writing

- **2026-10-27, before any variable was joined to an effect (owner's request):** V19 "island size" is added, following the TOD work. It is the area in acres (log) of the largest continuous patch of the place's land within ½ mile of a transit stop, from the union of ½-mile circles around the National Transit Map stops. A long connected network gives a large island; scattered stops give small ones. It is tested like the others.
- **2026-10-27, after V1–V19 had been tested, before these three were joined to any effect (owner's question in the TOD thread):**
  - V20: share of households with no car (ACS B08201);
  - V21: share of workers commuting by public transit (ACS B08301);
  - V22: mean commute time in minutes (ACS B08013 ÷ workers not working at home).

  Each is tested by the same single-variable rule. Because the first 19 results were already known when these were added, they are reported as a follow-up set. Driver's licences are published only by state, so they are left out.

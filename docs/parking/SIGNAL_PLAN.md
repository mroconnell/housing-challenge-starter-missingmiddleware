# Parking: turning noise into signal, plan written before running

Written 2026-11-01 by the parking conductor. Ryan: "Do the parking increase research. Take a quick pass at our existing data for 1 and 3 … 8 makes a lot of sense to me." These are quick, exploratory passes on the existing 76-place comparison (`reference/parking_expanded_effects.csv`); they do not change the tool. No result below has been computed before this file was committed.

## 1. Booming vs cooling markets

The 76 repeal places are split two ways:
- **Market direction:** whether the place's own comparison places permitted more after the repeal than before (`ctrl_after > ctrl_before`, booming) or less (cooling).
- **Sunbelt:** the Census South region plus the Mountain division, against the rest.

For each group, reported:
- the number of places;
- the home-weighted average effect (permits per 1,000 existing homes per year) and its 90% range from 2,000 resamples;
- the median;
- the weighted average without San Francisco.

If parking minimums bind where builders want to build, the effect should be larger in booming markets.

## 3. Project size

- The same comparison on homes in buildings of 2 or more units (`outcome == "2plus"`), against 1-unit homes (all minus 2+).
- The change in the share of permitted homes in 2+ unit buildings: the place's change minus its comparison places' change, in percentage points.
- Each reported as a weighted average, a median and a 90% range.

## Parking increases (search)

Cities that raised minimum parking requirements for housing between 2010 and 2022, from the Parking Reform Network map and from news and city records. A case counts if it covers multi-family housing citywide and has a date. Each found case goes through the same comparison, with the sign reversed. If fewer than 5 cases are found, the result is reported as a list, not an estimate.

## 8. California's 2023 law (AB 2097)

A separate plan will be written before it runs.

## Changes after writing
- **2026-11-01, audit wording fixes (after the run; no rerun):**
  - **Increase search:** it took in 2023 cases (Lake Havasu City, North Miami Beach), where the plan said 2010–2022, and a near-transit rule (Portland 2013), where the plan said citywide. Both are departures from the plan.
  - **Unplanned rows:** the two rows crossing 2+ unit homes with booming and cooling markets were not in the plan.
  - **The share row has 72 places, not 76.** The share of homes in 2+ unit buildings is undefined where a place or its comparison permitted no homes in a period (4 places).
  - **Booming vs cooling** is defined from the comparison places' change, which is also part of the effect. That builds in a small bias (correlation −0.15) toward finding a larger effect in booming markets. None appeared.

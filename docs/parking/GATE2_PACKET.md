# Parking scenario: Gate 2 packet (usable data)

Written 2026-10-26 by the parking conductor for Ryan, and revised the same day after an independent review. Status: ready for review. Owner decisions so far: AQ-046 (model city types by regression; places left out of the fit decide), and option A (accepted 2026-10-26, "if necessary").

## 1. What this gate decides, and the answer

Gate 2 settles whether the data are good enough to build the scenario, and which comparison the scenario rests on.

- **Data assembled:**
  - Census building permits for every US permit-issuing place, 2012–2025;
  - ACS homes, population and rent for every place;
  - the ordinance text of all 46 candidate repeal places, checked before any outcome was read (`reference/parking_repeal_checks.csv`).
- **The comparison was registered in advance** ([COMPARISON_PLAN.md](COMPARISON_PLAN.md)). Four deviations are recorded there with reasons:
  1. a wider pool of comparison places for the biggest cities;
  2. dates from the ordinance check;
  3. one average instead of the slightly better size-and-metro model;
  4. ACS population instead of the Census permit file's population field, which is wrong for some places.
- **Result** ([COMPARISON_RESULTS.md](COMPARISON_RESULTS.md)):
  - In the three years after 24 US places removed parking minimums for all housing, their permit rate changed by 1.18 permits per 1,000 existing homes per year less than at similar places that kept them. The likely range is −3.57 to +2.21, which includes zero.
  - 10 of the 24 places rose faster than their comparison places.
  - No size cut-off predicted places left out of the fit better than one average.
  - The answer holds without San Francisco, without any single state, and without the two small Texas places.
- **Wisconsin inputs:** the all-housing baseline by municipality and building size ([HOUSING_BASELINE.md](../shared/HOUSING_BASELINE.md)). 9 places are already at the benchmark and get no addition.

## 2. What option A would show (preview of Gate 3; not final)

- **Central:** no measurable change from current law, so 0 additional permits over 2027–2031.
- **Upper, "the high end of the likely range":** +2.21 permits per 1,000 existing homes per year.
  - Wisconsin has 2,684,793 existing homes outside the 9 places already at the benchmark (2,778,572 statewide minus 93,779).
  - So the upper case is about 5,933 more permits per year, or about 29,700 over 2027–2031. That is 25% more than the baseline's 118,822 permits.
  - It depends on San Francisco, which carries a quarter of the weight. Without it, the high end is +3.11, or about 41,700 over five years.
  - The apartments-only high end (+1.06 per 1,000 homes, counting only units in buildings of 2+ units) gives about 14,200.
- **No case below zero:** a repeal never subtracts.
- **Years 4–5:** the effect is measured over years 1–3 only. Holding the same level in years 4–5 is an assumption, and is labelled as one.
- **Where:** the upper case applies to every home outside the 9 places, including rural towns, many of which have few or no parking minimums today. That spreads it more widely than a minimum that binds would. Gate 3 will propose how to treat towns.

## 3. Owner review steps

1. Read "Answer" and "Checks on the average" in [COMPARISON_RESULTS.md](COMPARISON_RESULTS.md).
2. Open `reference/parking_comparison_effects.csv` and filter `outcome` = all and `status` = included. Check whether the places and their before and after rates look plausible. West Allis is the Wisconsin row.
3. Open `reference/parking_repeal_checks.csv` and skim the `evidence` column for any place you know.
4. Decide G2-1 to G2-5 below.

**Self-assessment.** I walked steps 1 to 3 myself.
- Every included place has 5 or more comparison places.
- Minneapolis, Lexington, St. Paul and Raleigh needed comparison places from neighbouring states (deviation 1).
- Each of the 5 places dropped by the ordinance check has a stated reason.
- The independent review rebuilt every effect from the raw Census files and got the same numbers. It found the population-field problem, now fixed (deviation 4).

The weakest points are the sample size (24 places), and the zoning rewrites that came with 18 of the 24 repeals.

## 4. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| G2-1 | Upper case | All units, at the high end of the likely range: +2.21 per 1,000 homes per year, about 29,700 over five years. Show the apartments-only bound (about 14,200) and the without-San Francisco bound (about 41,700) as sensitivities. |
| G2-2 | Years 4–5 | Hold the year 1–3 level flat, labelled as an assumption. |
| G2-3 | One average or size and metro (deviation 3) | One average. Show the size-and-metro model as a sensitivity. |
| G2-4 | Cost-based line (option B) | Not now. Revisit only if office-hours feedback asks for a modelled mechanism. |
| G2-5 | Milwaukee apartment fix (P8) and baseline range (P9) | As recommended at Gate 1. These change the baseline, not the parking addition under option A. |

## 5. Limitations

- **Sample:** 24 places, most of which repealed as part of a wider zoning rewrite. Parking's own effect cannot be isolated.
- **Window:** three years after the repeal. Permits for larger projects can take longer.
- **Self-selection:** the places chose to repeal, so they may differ from places that did not in ways the comparison misses.
- **Census reporting:** some places' permit years are fully estimated by Census, not reported. Five places were dropped for missing years, and Milwaukee's apartments are under-counted.
- **State parking laws overlap:** they affect some comparison places in California and Oregon, which pulls those effects toward zero.
- **Ordinance checks:** done from secondary copies of the code where city sites blocked access. Confidence is recorded for each place.

## 6. Independent review

Done on 2026-10-26.
- **Rebuild:** every effect was rebuilt independently from the raw Census files, with the same numbers. The option A arithmetic was confirmed.
- **Found and fixed:**
  - wrong populations in the Census permit file (deviation 4);
  - the size-and-metro model winning under the plan's rule, now recorded as deviation 3;
  - wording: "units" where the number is a rate, and labels for ranges;
  - two missing checks: one state left out at a time, and places without a zoning rewrite.
- **Added:** the robustness table and the limitations above.

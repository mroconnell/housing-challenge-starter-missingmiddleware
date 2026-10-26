# Parking scenario: Gate 2 packet (usable data)

Written 2026-10-26 by the parking conductor, for Ryan. Status: ready for review. Owner decisions so far: AQ-046 (model city types by regression; held-out places decide) and option A (accepted 2026-10-26, "if necessary").

## 1. What this gate decides, and the answer

Gate 2 settles whether the data are good enough to build the scenario, and which comparison the scenario rests on.

- **Comparison data are assembled:**
  - Census permits for every US permit-issuing place, 2012–2025, all four Census regions;
  - ACS homes and rent for every place;
  - the ordinance text of all 46 candidate repeal places, each checked before the outcomes were read (`reference/parking_repeal_checks.csv`).
- **The comparison was registered in advance** ([COMPARISON_PLAN.md](COMPARISON_PLAN.md)). Two deviations are recorded there with reasons: a wider comparison pool for the biggest cities, and the dates from the ordinance check.
- **Result** ([COMPARISON_RESULTS.md](COMPARISON_RESULTS.md)): 24 US places removed parking minimums for all housing. In the three years after, they permitted −1.29 units per 1,000 existing homes per year compared with similar places that kept them. The range is −3.68 to +2.33, which includes zero. No split by size, metro setting, rent or earlier permit rate predicted held-out places better than one average.
- **Wisconsin inputs for "where it binds":** the all-housing baseline by municipality and building size ([HOUSING_BASELINE.md](../shared/HOUSING_BASELINE.md)), and 9 places already at the benchmark, which get no addition.

## 2. What option A would show (preview of Gate 3)

These are shown so you can see what A means in numbers; they are not final.

- **Central:** no measurable change from current law: 0 additional permits over 2027–2031.
- **Upper**, "if the effect is at the top of what the evidence allows": +2.33 permits per 1,000 existing homes per year. Wisconsin's existing homes outside the 9 places already at the benchmark number 2,684,793 (2,778,572 statewide minus 93,779). So the upper case is about 6,256 more permits per year, or about 31,300 over 2027–2031, which is 26% above the baseline's 118,822. The apartments-only upper bound (+1.20 per 1,000 homes) gives about 16,100.
- **No lower case below zero:** a repeal never subtracts.
- **Ramp:** the effect is measured over years 1–3 only. Applying the same level in years 4–5 is an assumption, and is labelled as one.

## 3. Owner review steps

1. Read section 1 of [COMPARISON_RESULTS.md](COMPARISON_RESULTS.md).
2. Open `reference/parking_comparison_effects.csv`, filter `outcome` = all and `status` = included. Check that the places and their before/after rates look plausible to you (West Allis is the Wisconsin row).
3. Open `reference/parking_repeal_checks.csv` and skim the `evidence` column for any place you know.
4. Decide G2-1 to G2-4 below.

**Self-assessment.** I walked steps 1 to 3 myself.
- Every included place has 5 or more comparison places.
- Minneapolis, Lexington, St. Paul and Raleigh needed the division-wide pool (deviation 1).
- The six ordinance-check exclusions each have a stated reason.
- Effects for small places swing widely (Bastrop +27.8, Bandera −25.9), but they carry little weight because the average is weighted by homes.

The weakest points are the sample size (24 places) and the zoning rewrites that came with most repeals (18 of 24).

## 4. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| G2-1 | Upper case basis | All units (+2.33 per 1,000 homes per year, about 31,300 over five years), with the apartments-only bound (+1.20, about 16,100) as a sensitivity. Or the reverse, if you'd rather headline the narrower one |
| G2-2 | Years 4–5 | Hold the year 1–3 level flat, labelled as an assumption |
| G2-3 | Cost-based line (option B) | Not now; revisit only if office-hours feedback asks for a modelled mechanism |
| G2-4 | Milwaukee apartment fix (P8) and baseline range (P9) | As recommended at Gate 1. These matter for the baseline, not the parking addition under option A |

## 5. Limitations

- 24 places, most of which repealed as part of a wider zoning rewrite. The effect of parking alone cannot be isolated from the rewrite.
- Three years after the repeal. Permits for larger projects can take longer.
- The places chose to repeal, so they may differ from places that did not, in ways the comparison does not capture.
- Census permit data have reporting gaps. Five places were dropped for missing years, and Milwaukee's apartments are under-counted.
- The ordinance checks were done from secondary copies of the code where city sites blocked access. Confidence is recorded for each place.

## 6. Independent review

Not yet run; this packet will be updated with the reviewer's findings before you rely on it.

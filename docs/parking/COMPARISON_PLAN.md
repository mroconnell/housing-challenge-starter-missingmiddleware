# Parking: pre-registered comparison plan (Gate 2)

Written 2026-10-26 by the parking conductor, before the full comparison was run. Owner direction: AQ-046 (model places of different sizes differently; a multi-variable regression finds the cut-offs and the effect by city type; held-out cities decide). Any later change to this plan is recorded in section 8 with its date and reason.

## 1. Question

When a US city or village removed minimum parking requirements for all housing, how many more homes per 1,000 existing homes per year did it permit in the following years than similar places that did not? How does that answer depend on the place's size, density, metro setting and market strength?

## 2. Repeal places (the treated sample)

- **Source:** `reference/parking_reform_cases.csv` (Parking Reform Network data, rated by `missing_middleware/parking/taxonomy.py`).
- **Included:** US places with an adopted removal record rated **at** the benchmark, adopted in 2015–2022.
  - Census permit data start in 2012, so every case has at least 3 years before repeal.
  - The data end in 2025, so every case has at least 3 full years after.
- **Repeal year:** the PRN adoption year, unless the ordinance check (section 6) finds a later effective date, in which case the effective year is used. The repeal year itself is left out of both periods.
- **Excluded, with the reason recorded:**
  - not found in the Census permit place files;
  - the ordinance check finds the repeal was not in force, was reversed, or covered less than PRN says;
  - fewer than 3 years of data before the repeal.
- **Places rated "near"** (repeal with conditions) are a separate arm, reported but not pooled.

## 3. Comparison places

For each repeal place, the comparison places are Census permit places in the **same state** with:
- a population of half to twice the repeal place's, in the last year before repeal;
- no PRN record of removing residential minimums citywide (rated at or near, any status);
- data in every year of both periods.

Places with weaker reforms only (for example, downtown-only exemptions) stay in, because nearly every city has one. If a state has fewer than 5 comparison places, the population window widens to one-third to three times.

## 4. Outcome and effect

- **Outcome:** housing units permitted per 1,000 existing homes per year, from Census permit estimates. Existing homes are housing units from ACS 2020–2024, table B25002, matched to the place or county subdivision the permit file uses. The outcome is computed for all units and for units in buildings of 2+ units.
- **Periods:** before = up to 5 years before the repeal year (at least 3); after = years 1–3 after it. Years 4–5 are reported as an event-study path where available, but are not used to fit.
- **Effect for each repeal place:** (its after rate − its before rate) − (the comparison places' after rate − their before rate). The comparison rates are permits summed over all comparison places divided by their homes summed. The unit is additional permits per 1,000 existing homes per year. A difference, not a ratio, is used because many small places permitted zero homes in one period.

## 5. Which variables, and where the size cut-offs fall

Candidate models for the effect, compared by **leave-one-place-out prediction**. Each repeal place is predicted from all the others, and the error is weighted by its homes. The model with the lowest weighted mean absolute error wins; ties go to the simpler model.

| Model | Explains the effect with |
| --- | --- |
| M0 | one average for all places |
| M1 | size bands, with one or two cut-offs chosen from 10,000, 20,000, 50,000 and 100,000 people (each combination is a separate candidate) |
| M2 | log population (a straight line) |
| M3 | M2 plus market strength: median gross rent (ACS B25064) relative to the state's median |
| M4 | M2 plus metro setting: in a metropolitan area or not (2024 CBSA type) |
| M5 | M2 plus the place's before-repeal permit rate |
| M6 | M2 plus market strength and metro setting |

- **Fit:** least squares weighted by homes.
- **Checks:**
  - the winner refitted with each state's places left out;
  - a bootstrap over repeal places (2,000 draws, seed 20261026) for its uncertainty.
- **Market strength:** ACS 2020–2024 is measured partly after the repeals. ACS 2015–2019 rent is a sensitivity check (fetched if the main model uses rent).

## 6. Ordinance check (before outcomes are read)

For every repeal place in the sample, the code or ordinance is read and recorded in `reference/parking_repeal_checks.csv`:
- in force: yes or no;
- adoption date and effective date;
- what it covers (all housing, or with exceptions);
- other zoning changes adopted within one year (for example, an upzoning or a new form-based code);
- the source URL.

A place with a simultaneous upzoning stays in the main sample. The main model is refitted without such places as a sensitivity check.

## 7. Use for Wisconsin (outline; settled at Gate 3)

The chosen model predicts an effect for each Wisconsin municipality from its own variables, and that is converted to permits using the place's existing homes. A repeal never subtracts: a predicted effect below zero counts as zero. Places already at the benchmark get zero. Scenario levels and the ramp are Gate 3 decisions.

## 8. Deviations and things already seen

- **2026-10-26, before this plan:** a quick look at 16 repeal places of 5,000–50,000 people, with permits per 1,000 residents and a 0.5–2× population window (`scripts/parking_small_places_quicklook.py`), found 7 above their comparison places and 8 below. That result was seen before this plan was written. The formal run repeats those places under the rules above.
- **Deviation 1 (2026-10-26, after the first run):** the largest repeal cities had too few comparison places in their own state, even at one-third to three times their population. Minneapolis and Lexington had none; St. Paul and Raleigh had 1 and 2. When the state gives fewer than 5, the window now widens to the same Census division (for example, the West North Central states for Minneapolis), first at half to twice the population and then at one-third to three times. This was decided after the per-place effects of the first run had been seen, but before any model was compared.
- **Deviation 2 (2026-10-26):** the ordinance check changed some repeal years (effective date, or a corrected adoption date: Ecorse 2020, Hudson 2019, Emeryville 2020). It also excluded places where minimums were restored inside the after period (Central Falls, 2025). Places rated "near" by the check form the separate arm, as planned.

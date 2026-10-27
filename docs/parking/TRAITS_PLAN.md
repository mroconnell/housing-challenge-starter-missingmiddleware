# Parking: which city traits explain the effect? Plan written before testing

Written 2026-10-27 by the parking conductor, after Ryan asked whether traits such as home value, lot size, density, income or land area explain why the reform worked in some places and not in others. The plan is committed before any of the traits below is matched to an effect, and later changes go in section 6 with a date and a reason.

## 1. Question

Does any city trait predict the size of the effect of removing parking minimums, well enough to narrow the range or to model types of city differently?

## 2. Two datasets

- **A. US repeal places.** The 30 places in `reference/parking_comparison_effects.csv`: the 24 in the main sample plus the 6 that removed minimums with conditions, each with an effect from the before/after comparison (all units, permits per 1,000 existing homes per year). Weight: each place's existing homes.
- **B. California AB 2097, near transit.** One effect per jurisdiction in TOD's group P: near transit against the ½–1½ mile ring, 2023–2025 against 2018–2022, permits per 1,000 existing homes per year. Only jurisdictions with permits near transit in both periods count. Weight: homes near transit. These come from TOD's AB 2097 pipeline (docs/tod/AB2097_TEST_PREREG.md).

## 3. Traits (fixed now)

Each trait is measured for the whole place, in ACS 2020–2024 unless stated, and divided by the state's value where that makes it comparable across states.

| # | Trait | Source |
| --- | --- | --- |
| T1 | Median home value, relative to the state | ACS B25077 |
| T2 | Median household income, relative to the state | ACS B19013 |
| T3 | Density: housing units per square mile of land, log | ACS B25002 and Census Gazetteer land area |
| T4 | Share of homes that are single-family detached (a stand-in for lot size, which has no national source) | ACS B25024 |
| T5 | Land area, log square miles | Census Gazetteer |
| T6 | Median home value relative to income (T1 ÷ T2) | from T1 and T2 |

Already tested in the first comparison, and reported again here for completeness: population, metro setting, rent, and the permit rate before repeal.

## 4. Test

- **Models:** each trait on its own, in a straight-line model of the effect weighted as in section 2. With 30 and about 169 places, only one trait at a time is tested; no model with several traits is fitted.
- **Score:** the weighted mean absolute error in predicting each place from all the others (leave one place out), against one average for all places.
- **A trait passes only if all three hold:**
  1. it lowers the left-out error by at least 5% in dataset A;
  2. it lowers it by at least 5% in dataset B;
  3. its slope has the same sign in both.
- **Uncertainty:** a 90% interval for each slope, from 2,000 resamples of places (A) or jurisdictions (B), with seed 20261027.
- **Reporting:** every trait is reported, including those that fail, with its error, slope and interval.

## 5. Use

- **If a trait passes:** I propose to Ryan a version of the scenario in which the upper case (and the central, if the slope moves it above zero) varies with that trait for each Wisconsin place. It goes in front of him as a decision, not straight into the tool.
- **If none passes:** the tool says the effect could not be predicted from these traits in either dataset, which supports one average for every place.

## 6. Changes after writing

- **2026-10-27, before any trait was joined to an effect:** dataset B's jurisdictions are named in HCD's Table A2 style, with no Census code. They are matched to Census places by name: Table A2 name = Gazetteer place name without " city" or " town", California only. The 17 county jurisdictions (unincorporated areas) have no place-level traits, so they are left out of dataset B. Unmatched jurisdictions are listed in the output.

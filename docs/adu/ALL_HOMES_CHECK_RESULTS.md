# ADU all-homes cross-check: results

Run 2026-10-31 under [ALL_HOMES_CHECK_PLAN.md](ALL_HOMES_CHECK_PLAN.md), committed before running. Code: [`scripts/run_adu_all_homes_check.py`](../../scripts/run_adu_all_homes_check.py). Outputs: `reference/adu_all_homes_check_cases.csv`, `adu_all_homes_check_summary.csv`.

**Units.** Permits per 1,000 existing homes per year (Census permit survey ÷ ACS 2020–2024 homes). An **effect** is a law state's change from before to after its law, minus the median change of states without a law over the same years.

## Answer

- **This check cannot see the ADU law's effect, either way.** The states' total permits swing with the building cycle by more than the ADU model predicts.
- **The model's central** (10,349 ADU permits over 2027–2031) is 0.73 more homes per 1,000 existing homes per year in Wisconsin.
- **The placebo spread is wider than that:** −1.20 to +1.02 (5th to 95th percentile of averages for states with no law, given the same dates).
- **The real average effect is −0.97 for all units,** inside the placebo spread: 91% of placebo averages are at or above it. The median of the 7 states is −0.45.
- **Utah drives the negative average.** Its permits fell from 27.1 to 22.1 per 1,000 homes after its 2021 boom: an effect of −5.28. Without Utah, the other six average −0.26.
- **Units in 1–4 unit buildings:** average −0.58, median −0.22, just below the placebo spread (−0.41 to +0.72), again driven by Utah (−3.83).
- **Why it can't see ADUs:** the survey counts new buildings. ADUs in existing houses and garages are often not counted at all. So this check leans toward zero by design.
- **Nothing changes in the tool.** This is a cross-check only.
- **What the check could see.** The placebo spread is about ±1.1 permits per 1,000 homes per year. In Wisconsin that is about 15,600 homes over 2027–2031 (1.1 × 2,840,960 × 5 ÷ 1,000). So only an effect near the upper scenario (19,294) would show. A result of about zero is not evidence against the central.
- **Other limits.** Maine, Massachusetts and Rhode Island have only one after-year (2025). Comparing with every no-law state ignores Utah's own boom and bust; a comparison with states that grew like Utah before 2022 would be fairer, and could be added later.

## By state (all units)

| State | Law year | Before | After | Rate before | Rate after | Change | No-law states' median change | Effect |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| California | 2020 | 2017–19 | 2020–22 | 7.70 | 7.88 | +0.18 | +1.56 | −1.39 |
| Oregon | 2020 | 2017–19 | 2020–22 | 11.16 | 10.93 | −0.24 | +1.56 | −1.80 |
| Vermont | 2021 | 2018–20 | 2021–23 | 5.86 | 7.06 | +1.20 | +1.10 | +0.10 |
| Utah | 2022 | 2019–21 | 2022–24 | 27.14 | 22.07 | −5.07 | +0.21 | −5.28 |
| Maine | 2025 | 2022–24 | 2025 | 8.56 | 9.28 | +0.72 | −0.32 | +1.04 |
| Massachusetts | 2025 | 2022–24 | 2025 | 4.88 | 4.12 | −0.77 | −0.32 | −0.45 |
| Rhode Island | 2025 | 2022–24 | 2025 | 2.95 | 3.58 | +0.63 | −0.32 | +0.95 |

Washington is left out: its law binds from 2025–2026, so the permit files (to 2025) have no full after-year. Comparison states: 37–46, depending on which states had a law by the end of each window.

## What it would take

A state-level total cannot isolate a change of 0.7 per 1,000 homes when the cycle moves states by ±1 or more. The ADU-specific counts the model uses (ADU permits per single-family home) remain the right measure. A city-level version of this check, built like parking's, would need city permit files that separate ADUs, which only a few cities publish.

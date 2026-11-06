# ADU market-drift check: plan written before running

Written 2026-11-06 by the ADU thread, from Ryan's point about regression to the mean (Baseline thread, 19:22 UTC): a slow market drifts back up toward average and a hot one drifts back down, with or without a reform, so a reform's effect should be measured net of that drift. Ryan OK'd checking it with the ADU thread (19:33 UTC). No count below has been run. The audit reviews this plan before anything runs. Nothing in the tool changes without Ryan's OK.

**No expected direction.** Drift could raise or lower the ADU effect, depending on whether the law states' markets were hot or cold before their laws.

## What can and cannot be done

- **Matched non-law states, on ADU counts: not feasible.**
  - No source counts ADUs statewide in states without a law. The Census Building Permits Survey does not count ADUs separately.
  - The only non-law ADU series in the repo are 8 city and county series (NO_REFORM_R1). They are not states, and most have their own local reforms.
- **Market heat for every state: feasible.**
  - Source: Census Building Permits Survey state annual files, 2010–2025, already in `data/raw/census_bps_state/`.
  - Measure: all units permitted per 1,000 existing homes (ACS 2020–2024 B25024 total).
  - This measures how hot each state's whole housing market was. It cannot measure ADUs.
- **ADU pre-trends: feasible in 3 law states only.** These are the only ones with ADU counts from before their law:
  - Washington: OFM, 2011–2025.
  - California: BuildinganADU, 2012–2016, before the 2017 law.
  - Rhode Island: 2021–2023.

## Test D1. Did the law states' markets drift after their laws, and does that change Wisconsin's ADU addition?

**Step 1. Measure normal drift, from states with no ADU law.**
- For every state and every year Y from 2012 to 2020, in states with no statewide ADU law by Y+5:
  - **heat** = log(the state's all-units permit rate over Y−2..Y ÷ the national rate over the same years);
  - **drift** = the change in that log ratio from Y−2..Y to Y+1..Y+4.
- Fit drift = a + b × heat by ordinary least squares, pooled over states and years.
- b between −1 and 0 means partial regression to the mean; b = 0 means none.
- Interval: bootstrap over states, 2,000 draws, seed 20261106.

**Step 2. Predict each law state's drift from its pre-law heat.**
- For each of the 8 law states:
  - heat is measured over the 3 years before its law year (the AQ-065 coding);
  - its predicted drift = a + b × heat;
  - its actual drift is measured too, as a check.

**Step 3. Refit the ADU level net of drift.**
- Divide each law state's post-law ADU rates by exp(its predicted drift).
- Rationale: if its whole market cooled, its ADUs would have cooled with it, so the ADU rate it reached understates the law.
- Refit the adopted pooled model on those rates, then rerun the Wisconsin engine.
- Report the Wisconsin addition over 2027–2031: the A3 range and the 4 side lines, adopted and drift-adjusted, side by side.

**Step 4. Wisconsin's own drift (baseline side only).**
- Measure Wisconsin's own heat over 2023–2025 and its predicted drift.
- Report only: the effect if the ADU baseline (786) were scaled by it. The Baseline thread owns the all-housing drift.

**Assumption stated beside every result:** ADU activity moves with the whole market. This is not tested here. A check against Washington's OFM series is in D2.

**Pass rule (fixed now).**
- If the drift slope's 90% interval includes 0, report "no measurable market drift" and no change.
- Otherwise, report the drift-adjusted lines as a sensitivity case for Ryan to decide on.
- Either way, no line moves in the tool without his OK.

## Test D2. ADU pre-trends in the 3 law states with pre-law counts

- For Washington, California and Rhode Island, compare each pre-law ADU growth rate with the no-reform trend already used (7.3% a year, NO_REFORM_R1).
- **Washington check:** across years, correlate Washington's yearly ADU rate with its all-units permit rate (OFM, 2011–2025). This tests D1's assumption that ADUs move with the market.
- **Pass rule:**
  - Report each state's pre-law growth with a 90% interval (bootstrap over years).
  - Flag any state whose interval excludes 7.3%.
  - Report the Washington correlation with its interval.

## Limits stated in advance

- 8 law states, so D1's adjustment rests on 8 heat values.
- D2 covers 3 of the 8 states.
- California's pre-period (2012–2016) has thin, early-zero counts.
- Market heat is measured on all housing. ADUs may follow a different cycle.

## Outputs

- Code: `scripts/run_adu_market_drift.py`.
- Data: `reference/adu_market_drift_*.csv`.
- Results: `docs/adu/MARKET_DRIFT_RESULTS.md`.

## Changes after writing (audit review, 2026-11-06, before any count)

The audit accepted the plan with 6 fixes (`/mnt/project-files/audit/adu_market_drift_plan_review_2026-11-06.md`). These replace the matching parts above.

1. **Pass rule.**
   - Heat sits on both sides of the drift fit, so noise alone pushes b below 0. The decision is therefore made on the outcome, not on b.
   - The whole chain is bootstrapped together: the drift fit (non-law states resampled), the law states' predicted drifts, the pooled refit and the Wisconsin engine.
   - The decision measure is the change in Wisconsin's 2027–2031 addition, in ADU permits: drift-adjusted minus adopted, at typical adoption, with a 90% interval. 90% is a convention, not a tested level.
   - If the interval includes 0, the result is reported as "no measurable drift effect".
   - The full chain takes minutes per draw, so it runs 200 draws (seed 20261106). The count is fixed now.
2. **Horizon.**
   - Drift is fitted separately for each horizon h = 1 to 6 years after the heat window: drift_h = a_h + b_h × heat, with heat over Y−2..Y and the outcome in year Y+h alone.
   - A law state's post-law year k (law year = Y+1) gets drift_k.
   - Years past 6 do not occur in the fit: the longest post-law series, California and Oregon, run to k = 6.
3. **How strongly ADUs follow the market.**
   - The main D1 line divides by exp(drift), which assumes ADUs move 1-for-1 with all housing.
   - D2 also fits the log–log slope of Washington's yearly ADU permits on its all-units permits (OFM, 2011–2025), with a 90% interval from a bootstrap over years.
   - A second, labelled D1 line uses that slope in place of 1.
4. **Small samples in D2.**
   - Rhode Island has 2 year-on-year steps. It is reported with no interval and flagged.
   - Pre-law growth for California and Washington is the year slope of a Poisson fit on counts, with single-family homes as exposure. This handles California's early zeros.
   - Intervals come from a bootstrap over years.
5. **The law states and years** (AQ-065 coding, adopted fit):

| Cluster | First law year | Post-law years in the fit | Heat window (3 years before the law) |
| --- | --- | --- | --- |
| California | 2020 | 2020–2025 (k 1–6) | 2017–2019 |
| Oregon (32-city panel and Portland) | 2020 | 2020–2025 (k 1–6) | 2017–2019 |
| Vermont | 2021 (permit-year basis) | 2021–2023 (k 1–3) | 2018–2020 |
| Utah | 2022 | 2023–2025 (k 2–4) | 2019–2021 |
| Maine | 2025 | 2025 (k 1) | 2022–2024 |
| Massachusetts | 2025 | 2025 (k 1) | 2022–2024 |
| Rhode Island | 2025 | 2025 (k 1) | 2022–2024 |
| Washington | 2026 | 2026 (k 1) | 2023–2025 |
| Colorado (Denver's city series) | 2025 | 2025 (k 1) | 2022–2024 |

   - No heat window falls before 2010.
   - Denver's one law-year row is in the adopted fit. It gets Colorado's drift.
   - Washington's 2026 and the 2025 rows need the national rate in 2026 for some horizons. Where the BPS files end (2025), the outcome year is not observed, and those rows are fitted only on horizons with data. The drift for a law state's year k still comes from the fit at h = k.
6. **Data match.**
   - The Census Building Permits Survey state annual files (`data/raw/census_bps_state/`) are the source.
   - The Baseline thread's panel (`reference/baseline_bakeoff_part1_rows.csv`) is a cross-check only. Before counting, state-year totals are compared. The script lists every difference, and the BPS files win.

**Added limit.** The heat denominator is a fixed home count (ACS 2020–2024), the same in every year. So early years read a little high relative to later years in fast-growing states. This affects all states alike in the national ratio, but not exactly.

**Not done.** California's A2 finding is not applied as a fixed adjustment (audit agrees). It measured places within California drifting toward California's average, not states drifting toward the national average.

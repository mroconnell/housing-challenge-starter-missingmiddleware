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

## Changes after writing

None yet.

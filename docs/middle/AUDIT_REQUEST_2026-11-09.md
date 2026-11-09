# Audit request: middle housing test design v2 (before lock)

Sent 2026-11-09 at Ryan's request, from the middle housing thread. Please review the design before it is locked. No test in it has been run.

## What to review

**The design:** [TEST_DESIGN_DRAFT.md](TEST_DESIGN_DRAFT.md), draft v2.

**Supporting work, in order:**

| Step | File | What it established |
| --- | --- | --- |
| 1. Candidates | [CANDIDATES.md](CANDIDATES.md), `reference/middle_housing_candidates.csv` | 20 reforms with dates and sources. Usable now: Oregon, California, Minneapolis, Raleigh, Spokane, Walla Walla, Portland |
| 2. Oregon line | [OREGON_CUTOFF_CHECK.md](OREGON_CUTOFF_CHECK.md) | The law used PSU's certified July 2020 estimate. Three cities over 10,000 by Census were left out. HB 3395 (2023) closed the gap from 2025-06-30. A housing-plan rule shares the line |
| 3. No-peeking rules | [MEASUREMENT_CHECK_LOG.md](MEASUREMENT_CHECK_LOG.md) | Rules fixed before the measurement work, plus a disclosure of everything seen before they existed, and each helper's edge cases |
| 4. Measurement | [MEASUREMENT_CHECK_RESULTS.md](MEASUREMENT_CHECK_RESULTS.md), [measurement/](measurement/) | How Census, WA OFM, CA HCD, Maine and city records file townhouses, lot splits, 5–6 unit buildings and conversions. In California, projects of 5–6 homes held 3.0% of 5+ homes in 2018–2021 |
| 5. Power | [POWER_CHECK.md](POWER_CHECK.md), `scripts/middle_power_check.py` | Smallest detectable effects from 2012–2018 permits only. Leaving out 5+ buildings roughly halves the noise |

## Key choices and why

| Choice | Why | Decided by |
| --- | --- | --- |
| Census permits everywhere | Exist in every state (the rules favour methods that work with thin data); one consistent filing rule | Ryan, 2026-11-08 |
| Count homes, not lots | Lot splits are not homes | Ryan, 2026-11-08 |
| Main measure: homes in 1–4 unit buildings | Census files townhouses, side-by-side duplexes and split-lot homes as 1-unit; leaving out 5+ roughly halves the noise | Ryan, 2026-11-09 |
| All homes always shown beside it; lead fixed in advance | Picking the lead after results would be cherry-picking | Ryan, 2026-11-09 |
| Primary result: Test 1, homes in 1–4 unit buildings | Many tests and measures invite chance findings | Ryan accepted, 2026-11-09 |
| Test 1 inference by fake law-state pairs | Two treated states make a clustered bootstrap look too precise | Ryan accepted, 2026-11-09 |
| Border counties left out; reform-list screening | Spillover and unknown local reforms are backdoors | Ryan accepted, 2026-11-09 |
| California labelled "2022 package" | SB 9 cannot be separated from concurrent state laws | Ryan accepted, 2026-11-09 |
| City records from Raleigh, Mecklenburg and Sacramento out | Their terms grant no open licence | Ryan, 2026-11-09 |

## Things we ask the audit to check in particular

1. **Disclosure.** Some post-reform numbers in tested places were seen on 2026-11-06, before the no-peeking rules existed. They are listed in the log. Do they compromise any choice made since? The main measure was proposed by Ryan for noise reasons, after the power check, which used only 2012–2018 data.
2. **Fake law-state ranking.**
   - Is ranking Oregon and California against pairs of untested states the right main inference with only 2 treated states?
   - Is matching by division and population band enough?
3. **Test 2.** Is an 11-city side check worth keeping, given the shared cutoff with the housing-plan rule?
4. **Windows.**
   - Oregon's before window (2015–2019) includes 2019, the year the law passed (2019-08-08). Its local deadlines were 2021–2022.
   - California's after window starts in 2023.
   - Are these fair?
5. **Measure.** Does homes in 1–4 unit buildings (mostly detached houses) need more than the 2–4 unit share side line to guard against swings in house-building?
6. **Reading rules.** Are the rules symmetric and complete? Does the design state any expected result anywhere?
7. **Power check method.** Its windows (2012–2014 against 2016–2018) fall in the recovery after the housing crash. Is that a fair measure of noise?

## Not in scope

- No tool change is proposed.
- The Wisconsin transfer plan is separate and not yet drafted.

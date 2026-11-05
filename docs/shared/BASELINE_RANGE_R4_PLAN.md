# Baseline range, round 4: tighter 90% ranges (DRAFT, not locked, nothing run)

Written 2026-11-05 by the baseline thread. Ryan: "yes" (20:43 UTC) to a round that tries to tighten the LASSO range to 90% and to narrow the all-states range. Status: **draft, for the audit's review.** Ryan's go is already given for this round, so it runs once the audit clears it and the script is committed.

## Set-up (as in round 3)

Round 3's plan ([BASELINE_RANGE_SIMILAR_PLAN.md](BASELINE_RANGE_SIMILAR_PLAN.md)) carries over unchanged:
- leave one state out;
- traits from data up to t;
- training on start years s ≤ t − 5;
- inner calibration on the training states only;
- main check years 2009–2020 (*post hoc*, labelled), with 2005–2020 also reported;
- Wisconsin and the 10 challenge states reported, not used to pick.

## Methods

| Id | Method | Change from round 3 |
| --- | --- | --- |
| A | All states pooled, around L0 | None (benchmark) |
| AT | A with freak-outlier states removed from training | At each t, training states whose swing is above Q3 + 3 × IQR of the training states' swing are dropped. The rule is fixed. |
| AR | A with recent start years weighted more | Weight on a ratio from start year s is 0.5^((t − 5 − s) ÷ h), with the half-life h in {3, 5, 10, no decay} tuned by the inner loop |
| AL3 | A around L3 (pulled toward the long-run rate) | Ratios are actual ÷ L3's prediction, with b fitted per start year by the bake-off's no-look-ahead rule. The central becomes L3's (132,458 for Wisconsin 2027–2031). |
| ARL3 | AR around L3 | Both changes |
| E | LASSO miss size | None (benchmark) |
| E2 | E recalibrated | Three changes: (i) the target is log(max(\|log r\|, 0.02)), so near-zero misses do not dominate; (ii) predicted miss sizes are capped to the 1st–99th percentile of the training out-of-fold predictions; (iii) c is the narrowest value on a grid of 0.05 whose out-of-fold coverage on the training states is at least 90% (GroupKFold(10) by state). LassoCV settings are as in round 3. |

## Scores and pick

These are as in round 3:
- coverage on the 50 states other than Wisconsin, with the block-bootstrap range;
- mean width in log(high ÷ low); the median width is also reported, because a few huge widths can drive the mean;
- Wisconsin hits;
- coverage on the challenge states.

**Pick rule:**
- **Qualifiers:** methods with point coverage of at least 90% on the 50 other states, in 2009–2020.
- **Winner:** the qualifier with the smallest mean width.
- **Ties** (within 0.01) go to the simpler method, in the order A, AT, AR, AL3, ARL3, E, E2.
- **If none qualifies,** A stays.

**Reading notes:**
- Seven methods compete, and some reuse round-3 results, so the winner's coverage is a little optimistic. Wisconsin and the challenge states are the cleaner checks.
- AL3 and ARL3 change the central. Ryan has said he does not mind which central is used (18:02 UTC).

## Wisconsin 2027–2031

Each method's range, with training on start years up to 2020 and traits at 2025, is scaled to v3 as before. AL3 and ARL3 are centred on 132,458.

## Rules

- The script is committed before the run, and runs stay on Ryan's Mac.
- A change to the tool needs Ryan's OK.

## Plan log

- 2026-11-05: draft.

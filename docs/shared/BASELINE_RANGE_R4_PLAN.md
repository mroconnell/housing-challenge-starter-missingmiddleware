# Baseline range, round 4: tighter 90% ranges (LOCKED 2026-11-05; a *post hoc* round)

Written 2026-11-05 by the baseline thread. Ryan: "yes" (20:43 UTC) to a round that tries to tighten the LASSO range to 90% and to narrow the all-states range. Status: **draft, for the audit's review.** Ryan's go is already given for this round, so it runs once the audit clears it and the script is committed.

**This whole round is post hoc (audit 1).** The five new methods were designed after seeing round 3's results: E over-covered, and A reached 88.7%. They are scored on checks already seen: the same 50 × 12 checks, the Wisconsin checks and the challenge-state checks. Round 3 shaped the methods, and seven methods compete on checks already seen, so the winner's coverage is optimistic. No clean hold-out remains.

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
| AT | A with freak-outlier states removed from training | At each t, training states whose swing is above Q3 + 3 × IQR of the training states' swing are dropped from training only; a high-swing state is still checked as a target (audit 3). Q3 + 3 × IQR is a convention, not from evidence. |
| AR | A with recent start years weighted more | Weight on a ratio from start year s is 0.5^((t − 5 − s) ÷ h), with the half-life h in {3, 5, 10, no decay} tuned by the inner loop. The half-life grid is a convention. |
| AL3 | A around L3 (pulled toward the long-run rate) | Ratios are actual ÷ L3's prediction, with b for start year s fitted on start years up to s − 5 across all 51 states (audit 4). So b uses the held-out state's own past, never its future; it does not leave the held-out state out, which is a small shared-parameter leak. The central becomes L3's (132,458 for Wisconsin 2027–2031). |
| ARL3 | AR around L3 | Both changes |
| E | LASSO miss size | None (benchmark) |
| E2 | E recalibrated | Three changes: (i) the target is log(max(\|log r\|, 0.02)), so near-zero misses do not dominate; (ii) predicted miss sizes are capped to the 1st–99th percentile of the training out-of-fold predictions; (iii) c is the narrowest value on a grid of 0.05 whose out-of-fold coverage on the training states is at least 90% (GroupKFold(10) by state). LassoCV settings are as in round 3. The 0.02 floor, the 1st–99th cap, the 0.05 grid and the 10 folds are conventions, not from evidence (audit 2). |

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
- **If none qualifies,** nothing changes in the tool, and A is reported as the benchmark (audit 5). The tool shows the v3 80% range until Ryan picks.

**Reading notes:**
- Seven methods compete, and some reuse round-3 results, so the winner's coverage is a little optimistic. Wisconsin and the challenge states are the cleaner checks.
- AL3 and ARL3 move the central to 132,458. That changes the baseline, so it needs Ryan's own OK, separate from this round's go (audit 6). He has said he does not mind which central is used (18:02 UTC).

## Wisconsin 2027–2031

Each method's range, with training on start years up to 2020 and traits at 2025, is scaled to v3 as before. AL3 and ARL3 are centred on 132,458.

## Rules

- The script is committed before the run, and runs stay on Ryan's Mac.
- A change to the tool needs Ryan's OK.

## Plan log

- 2026-11-05: draft.
- 2026-11-05, script written before any run (`scripts/run_baseline_range_r4.py`; smoke-tested on synthetic data only). Implementation notes:
  - **E is reused.** Its results are read back from round 3, the same code and seed, and not recomputed.
  - **A family quantiles.** A, AT, AR, AL3 and ARL3 use one weighted-quantile function, with equal weights where unweighted. So A's numbers can differ slightly from round 3's `np.quantile` version.
  - **L3 ratios.** These exist from start year 1997, the first year whose b can be fitted without look-ahead, so AL3 and ARL3 train on start years 1997 to t − 5.
- 2026-11-05 20:46 UTC, audit: cleared once items 1–7 are in. Items 1–6 are written in. Item 7: the script was committed at cb94f102 before any run. LOCKED at this commit.


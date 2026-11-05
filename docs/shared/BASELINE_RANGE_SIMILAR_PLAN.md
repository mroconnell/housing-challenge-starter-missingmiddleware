# Baseline range, round 3: learned "similar states" (DRAFT, not locked, nothing run)

Written 2026-11-05 by the baseline thread. Status: **draft. Waiting on the audit's review and Ryan's OK.**

## Why

Ryan (19:05–19:20 UTC) accepts a range that holds 90% of the right answers from 2009 on, but the all-states range is wide: 48,709 to 244,147 homes for 2027–2031. He asked to narrow it by learning which states are like Wisconsin, chosen by the data and not by hand ("something a bit more scientific").

## The question

Does a range learned from states like the target, with "like" learned from data, hold the outcome 90% of the time while being narrower than the all-states range?

## Set-up

- **Level:** L0, the flat 3-year average; the central stays 124,000.
- **Miss:** each state and start year s gives a ratio r = actual ÷ predicted five-year all-sizes total, the same as round 2.
- **Leave one state out.** Each of the 51 states takes a turn as the target. For a target j and a check start year t:
  - **Training:** the other 50 states, start years s ≤ t − 5 only.
  - **Traits:** measured only from years up to t.
- **Check years:**
  - **Main:** 2009–2020 (12 per state). Ryan accepted this window; it is *post hoc*, chosen after round 2 showed that the misses sit in 2005–08.
  - **Also reported:** 2005–2020.

## State traits (at t, from data up to t only)

1. **Swing:** standard deviation of log annual permits, 1990 to t.
2. **Pace:** permits per 1,000 homes, 3-year average at t.
3. **Recent tilt:** log(3-year average ÷ 10-year average) at t.
4. **Apartment share:** the share of units in 5+ unit buildings, 3 years to t.
5. **Own past miss:** the mean |log r| over the state's own start years s ≤ t − 5.
6. **Census region:** four indicators.

Traits are standardised on the training states at each t.

## Methods (each gives a 90% range for the target)

| Id | Method | What it learns |
| --- | --- | --- |
| A | All training states pooled (round 2's method) | Nothing; benchmark |
| B | The target's own past only (round 2's R0) | Nothing; benchmark |
| C | k nearest training states on the traits; k is tuned | Who is similar, and how many |
| D | Kernel-weighted: every training state counts, weighted by closeness on the traits; the bandwidth is tuned | How fast similarity fades |
| E | LASSO miss-size model: a LASSO (`sklearn LassoCV`, 5-fold grouped by state) predicts log of the miss size from the traits; the range is pred × exp(± c × predicted miss size), with c calibrated | Which traits predict big misses |

- **Calibration, the same for every method.** On the training states only, by an inner leave-one-state-out, each method is set to the narrowest setting that reaches 90% coverage:
  - the quantile level for A to D;
  - c for E.
- **Tuning.** The same inner loop tunes k (5, 10, 15, 20, 30) and the bandwidth (0.5, 1, 2 trait-distance units).
- **Not used.** The target and its outcome are never used for its own range.

## Scores

For each method:
- **Coverage:** the share of held-out target checks inside the range, over the 50 states other than Wisconsin. The block-bootstrap 90% range is over check years (5-year blocks, 2,000 draws, seed 20261105).
- **Width:** the mean of log(high ÷ low) over those checks. Lower is narrower.
- **Wisconsin:** reported as a check, not used to pick: hits out of 12 (main) and out of 16, plus its width.
- **Monthly start points (reported only).** Not in this round. They would need the monthly state files, and overlapping windows add little; noted for later.

## Pick rule

- **Who qualifies:** methods whose point coverage on the 50 other states is at least 90%.
- **The winner:** the qualifier with the smallest width. A width within 0.01 counts as a tie and goes to the simpler method, in the order A, B, C, D, E.
- **If no method qualifies,** A stays, and the shortfall is reported.

## Wisconsin 2027–2031

The winning method, with training on all 50 other states and start years up to 2020 and Wisconsin's traits at 2025, gives the range around L0. It is scaled to v3 (×124,000 ÷ 118,148), with the round-2 range beside it.

## Rules

- **Before the run:** the script is committed, and the audit reviews this plan.
- **Running:** runs stay on Ryan's Mac; scikit-learn is already in the project's `ml` extra, so no new dependency.
- **The tool:** a change needs Ryan's OK. Effects on the ADU, TOD and parking baseline bands are listed with the results.

## Plan log

- 2026-11-05: draft.

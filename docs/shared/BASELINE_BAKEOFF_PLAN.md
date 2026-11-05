# Baseline bake-off: locked plan (DRAFT, not locked, nothing run)

Written 2026-11-05 by the baseline thread. Owner: "yes" (16:45 UTC) to writing this plan. Status: **draft for Ryan's choices (D1–D4) and the audit's review.** Nothing is fetched or run until Ryan's go after the audit. Anything chosen after seeing a result is labelled *post hoc*.

## The question

Ryan's goal (2026-11-05): a reliable forecast of Wisconsin's housing permits over 2027–2031 if the state passes none of the reforms. The current baseline (v3) holds each town flat at its 2023–2025 average: 124,000 homes permitted over 2027–2031, range 65,250 to 177,672.

That rule was chosen by replaying only four start years (2019–2022), all in a rising market. This plan tests Ryan's six ideas against it over many more start years, including the 2006–2011 crash:

1. use more years for the state trend;
2. use regional (county) trends;
3. use data from before 2015;
4. pull hot or cold towns back toward the average;
5. smooth out lumpy big projects;
6. learn from other states.

## Design: two parts, scored separately

The baseline is split into two parts, each tested on its own:

- **Level:** how many homes Wisconsin permits in total over the five years.
- **Shares:** how that total splits among the 1,925 municipality pieces, by building size.

The final baseline is level × shares. This matters because parking's earlier test found one method can be better at state totals while another is better town by town.

## Part 1: the level

**Data.** Census state permit files, 1990–2025, for all 50 states and DC; Wisconsin's are already on disk. Census state housing-unit estimates, 1990–2025, are needed for the per-home candidates (to fetch).

**Start years.** 2000 to 2020: 21 start years, each scored on the next five years. This lets every candidate, including 10-year windows, use the same start years. The 21 periods overlap, so they hold about four independent five-year periods per state.

**Candidates.** Each predicts the next five years' total from data up to the start year only.

| Id | Candidate | Idea |
| --- | --- | --- |
| L0 | Flat 3-year average (current) | — |
| L1 | Flat 5-, 7- and 10-year averages | 1 |
| L2 | Long-run permits per existing home (all years since 1990) × homes at the start year | 1, 4 |
| L3 | Partial pull back: 3-year level × (long-run level ÷ 3-year level)^b, with b fitted only on earlier start years | 4 |
| L4 | Straight-line trend over 10 years and over all years | 1 |

**Score.** The mean, over start years, of |log(predicted ÷ actual)| for the five-year total. Lower is better: 0.10 means about 10% off. Bias (mean log ratio) and the crash start years (2005–2009) are reported separately.

**Pick rule (D1, D2).** A candidate replaces L0 only if all three hold:
- it beats L0 by at least 10% on the all-states score;
- a block bootstrap over start years (5-year blocks, 2,000 draws, seed 20261105) shows it better in at least 80% of draws;
- it is not worse than L0 on Wisconsin alone by more than 5%.

If more than one candidate passes, the lowest all-states score wins. If none passes, L0 stays.

**Range.** It is redone with the winning level method's own out-of-sample errors: the 10th to 90th percentile of its predicted ÷ actual ratios for Wisconsin, by building size. The all-states version is a sensitivity.

## Part 2: the shares

**Data (to fetch).** Census place permit files for Wisconsin, 1990–2014 (the Midwest region files exist back to 1980). The older files have no FIPS codes, so rows are linked to 2015+ rows by Census's 6-digit permit ID, then to municipality pieces with the current crosswalk. County files are needed for 1990–1999 (2000–2025 are on disk). The Milwaukee property-file fix is carried back to 2000.

**Coverage check (before any score).** A year is used only if the linked rows hold at least 95% of that year's Wisconsin state units. Years that fail are dropped and listed.

**Start years.** 2004 to 2020, or fewer if the coverage check drops years.

**Candidates.** Each gives every piece a share of the state total, by building size.

| Id | Candidate | Idea |
| --- | --- | --- |
| S0 | Own 3-year share (current) | — |
| S1 | Own 5- and 10-year shares | 3, 5 |
| S2 | County pace, split within the county by each piece's own 10-year share | 2 |
| S3 | Shrink: each piece's rate per 1,000 homes blended with its county's rate, by weight n ÷ (n + k), where n is the piece's homes and k is fitted only on earlier start years | 4, 5 |
| S4 | Lumpy-year cap: in a 5-year window, a year counts at most 2 times the piece's average of its other years (3 times as a sensitivity) | 5 |

**Score.** Each candidate's shares are scaled to the actual state total, so only the split is tested. The score is the sum over pieces and sizes of |predicted − actual|, divided by actual units: the error in homes per home permitted. Big-city and small-town results are also reported separately (pieces with at least, or fewer than, 1,000 homes).

**Pick rule.** The same three-part rule as the level, with Wisconsin pieces in place of states (no 5% check, since this part is Wisconsin only).

## Other states (idea 6)

- Part 1 uses every state, so Wisconsin's level is chosen on all states' history.
- Parking's no-reform model results (`docs/parking/NO_REFORM_MODEL_RESULTS.md`) are shown as a reference row and not rerun: boosted trees on 9,109 US places, about 114,000 for Wisconsin.

## Not in this round (D4)

The tutor's version of idea 4 used parking's method 3 level score as the shrink target. That score was trained on repeal places across the US, not on Wisconsin towns. S3 tests the same idea with a county target instead. The method 3 version can be a second round if S3 passes.

## Rules

- Scripts are committed before any run, and the lock time is recorded here.
- Every fitted number (b, k) uses only start years before the one being scored.
- Runs stay on Ryan's Mac. Long runs are detached with checkpoints.
- The audit reviews this lock and the results.
- A change to the tool needs Ryan's own OK.
- Any change is reported with its effect on each scenario:
  - **ADU:** the 124,000 denominator in the shared comparison.
  - **TOD:** station-area baselines and the combined view.
  - **Parking:** shares, and its bundle and combined bundle rebuilds.

## Choices for Ryan

| Id | Choice | Recommended |
| --- | --- | --- |
| D1 | Choose the level on all states (Wisconsin checked) or on Wisconsin only (21 start years) | All states: Wisconsin alone has about 4 independent periods |
| D2 | Margin to replace the current rule | 10% better, in 80% of bootstrap draws |
| D3 | Split level and shares, or pick one method for both | Split |
| D4 | Leave the method 3 score shrink for a second round | Yes |

## Plan log

- 2026-11-05: draft written. Not locked.

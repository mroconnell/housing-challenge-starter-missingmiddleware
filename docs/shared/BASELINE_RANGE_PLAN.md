# Baseline range, round 2: plan (DRAFT, not locked, nothing run)

Written 2026-11-05 by the baseline thread. Status: **draft. Waiting on Ryan's go and the audit's review. Nothing runs before both.**

## Why

Ryan (2026-11-05 18:02 UTC) cares most that the 90% range actually holds the answer. The bake-off ([BASELINE_BAKEOFF_RESULTS.md](BASELINE_BAKEOFF_RESULTS.md)) found that Wisconsin-only ranges held the actual five-year total only 6 or 7 times in 16 past checks.

This round tests whether a range built from all states' history does better.

**Partly post hoc.** The all-states range was already seen as a sensitivity in 574fced5: 46,987 to 286,716 homes for L3 at the 2.5th–97.5th percentiles. Adopting it would be partly chosen after seeing that result, and it is labelled so.

## What is tested

- **Ranges:**
  - **R0:** multipliers from Wisconsin's own start years (current method);
  - **R1:** multipliers from all 51 states' start years, pooled.
- **Levels:** both L0 (flat 3-year) and L3 (pulled to the long-run rate), since Ryan has no preference between them. L3's b follows the bake-off's no-look-ahead rule.
- **Multipliers (audit 4).**
  - **Main:** actual ÷ predicted on the all-sizes five-year total. A range is the predicted total × the percentiles. This matches the hit test, which uses the all-sizes total, and it does not assume that every size misses in the same direction in the same year.
  - **Alternative, reported only:** the per-size sum (each size's prediction × that size's percentile, then summed), as in v3. It is wider, because it adds up each size's worst case.
- **Target:** 90% (the 5th–95th percentiles).

## Coverage check (nested)

- **Rebuilt each year.** For each check start year t from 2005 to 2020, the multipliers come only from start years s ≤ t − 5, from 1992, and for R1 across all states. The range is then applied to t's own prediction.
- **A hit** is t's actual five-year all-sizes total landing inside the range.
- **Wisconsin:** 16 checks, so coverage moves in steps of 6.25 points.
- **All states:** 51 × 16 = 816 checks. They share the national cycle, so they are not independent. They are reported as a rate, with a block-bootstrap 90% range over start years (5-year blocks, 2,000 draws, seed 20261105).

## Pick rule

**Picking set (audit 1).** The step and the method are picked on the 50 states other than Wisconsin, so Wisconsin's coverage is a check the pick never saw.

- **Steps.** These are tried in order: 5th–95th, then 2.5th–97.5th, then the smallest and largest past values (min–max).
- **Narrowest step that reaches the target.** For each level and range method, the chosen step is the narrowest one whose coverage on the 50 other states is at least 90%.
- **The 90% bar is on the point rate (audit 3),** not on the lower end of its bootstrap range. The 800 checks share the national cycle, so the bootstrap range is wide, and its lower end would almost never reach 90%. The bootstrap range is reported beside the rate.
- **R0 and R1.** The method that reaches the target with the narrower Wisconsin 2027–2031 range wins. If only one reaches it, that one wins.
- **Wisconsin's own past (audit 2; Ryan's call, D-R1).** Wisconsin's 16 checks are reported, not used to pick. Coverage there moves in 6.25-point steps: 14 of 16 is 87.5%, below the 90% target, and 15 of 16 is 93.75%. If Ryan wants Wisconsin to be a pass bar, he picks 14 or 15 of 16 before the run.

**Reporting only (audit 5).** R1's coverage is also shown by state volatility group. The groups are terciles of each state's standard deviation of log annual permits, 1990 to the check year, and Wisconsin's tercile is named. This shows whether pooling covers calm states well and volatile states badly, or the other way round.

**If coverage still falls short.** If no step reaches the target, the min–max range of the better-covering method is reported with its shortfall, labelled "does not reach 90% in past checks". The range is not widened by hand, and no evidence-free floor is added.

## Reporting

- **Wisconsin 2027–2031** low and high for each level, range method and step. These are scaled to v3 by the ratio to L0 (×124,000 ÷ 118,148), with the per-size scaling check beside them.
- **Coverage tables:** Wisconsin and all states.
- **Scenario effects:** how much the range changes, and what changes in each scenario.
  - **ADU:** the shared comparison's denominator range.
  - **TOD and parking:** the baseline band on their screens.

## Rules

- The script is committed before the run, and the audit reviews this plan first.
- Runs stay on Ryan's Mac.
- A change to the tool needs Ryan's OK.

## Plan log

- 2026-11-05: draft written after the audit's notes (18:03 UTC: 90% target, nested check, coverage on Wisconsin and all states, a shortfall rule, the post hoc label).
- 2026-11-05 18:05 UTC, audit: cleared once items 1–4 are written in and Ryan says go. Written in: pick on the 50 states other than Wisconsin (1); the Wisconsin bar left to Ryan as D-R1 (2); the 90% bar on the point rate (3); the main method is all-sizes total multipliers, with the per-size sum as the alternative (4); R1 coverage by volatility tercile (5).

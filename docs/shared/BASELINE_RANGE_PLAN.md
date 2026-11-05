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
- **Multipliers:** actual ÷ predicted five-year units, by building size. A range is the sum over sizes of predicted × the size's percentile.
- **Target:** 90% (the 5th–95th percentiles).

## Coverage check (nested)

- **Rebuilt each year.** For each check start year t from 2005 to 2020, the multipliers come only from start years s ≤ t − 5, from 1992, and for R1 across all states. The range is then applied to t's own prediction.
- **A hit** is t's actual five-year all-sizes total landing inside the range.
- **Wisconsin:** 16 checks, so coverage moves in steps of 6.25 points.
- **All states:** 51 × 16 = 816 checks. They share the national cycle, so they are not independent. They are reported as a rate, with a block-bootstrap 90% range over start years (5-year blocks, 2,000 draws, seed 20261105).

## Pick rule

The steps are tried in order: 5th–95th, then 2.5th–97.5th, then the smallest and largest past values (min–max). For each level and range method, the chosen step is the narrowest one where:
- all-states coverage is at least 90%; and
- Wisconsin coverage is at least 14 of 16 (87.5%, the nearest step at or above 87.5%; 15 of 16 would be 93.75%).

Between R0 and R1, the method that reaches the target at the narrower Wisconsin 2027–2031 range wins. If only one reaches it, that one wins.

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

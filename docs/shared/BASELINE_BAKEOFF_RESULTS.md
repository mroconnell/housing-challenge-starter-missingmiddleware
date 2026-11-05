# Baseline bake-off: results

Written 2026-11-05 by the baseline thread. Plan: [BASELINE_BAKEOFF_PLAN.md](BASELINE_BAKEOFF_PLAN.md) (locked 2026-11-05; clarifications in its Plan log, all made before the counts they affect). Scripts:
- `scripts/fetch_baseline_bakeoff.py`
- `scripts/build_baseline_bakeoff_links.py`
- `scripts/run_baseline_bakeoff.py --part 1` and `--part 2`

Outputs: `reference/baseline_bakeoff_part1_*.csv`, `reference/baseline_bakeoff_part2_*.csv`, `reference/baseline_bakeoff_link*.csv`.

**Status: the audit cleared the results (2026-11-05 17:37 UTC). Adopting L3 is Ryan's call. The tool is not changed.** The shared baseline stays v3 (124,000) until Ryan says otherwise.

## Answer

1. **The state total: a challenger passed.**
   - L3 is the 3-year average, pulled part of the way toward Wisconsin's long-run permits per existing home.
   - It beat the current rule (L0, the flat 3-year average) on all three pick tests.
   - For Wisconsin 2027–2031 it gives **132,458 homes permitted**, against 124,000 now: +8,458, or +6.8%.
2. **The split among towns: the current rule stays.** No challenger passed. The closest was the 5-year average (S1a): 1.3% better, short of the 2% bar. By the reading rule, this result says little, because the test holds only about 3 independent periods.
3. **The range is too narrow, by a lot.** The current method's 10th–90th range held the actual outcome in only 6 of 16 past five-year checks (37.5%), against an 80% target. Even the widest step held it in 7 of 16 (43.8%). By the stop rule, the widest step (2.5th–97.5th) is used and the shortfall is reported.
   - L3's widest range for 2027–2031 is **56,592 to 206,406 homes**, against v3's 65,250 to 177,672.
4. **Region (L5, Census-division pool):** it did not pass. Its score was 1.1% better, and the bootstrap range crossed 0. Ryan's D6 reading (test region now, or in round 2) therefore does not change the pick.

## Part 1: the state total

Score: mean |log(predicted ÷ actual)| of the five-year total, over 51 states (50 states plus DC) and 21 start years (2000–2020). Lower is better: 0.336 means the typical five-year forecast is off by about 40% (e^0.336 = 1.40). The difference column is the candidate's score minus L0's, with its 90% paired-bootstrap range (2,000 draws of 5-year blocks of start years, the same draws for all states).

| Candidate | All states | Difference from L0 (90% range) | Wisconsin only | Crash starts 2005–2009 | Passes? |
| --- | ---: | --- | ---: | ---: | --- |
| L0 flat 3-year (current) | 0.336 | — | 0.346 | 0.611 | — |
| L1a flat 5-year | 0.366 | +0.030 (0.000 to +0.061) | 0.398 | 0.688 | No |
| L1b flat 7-year | 0.383 | +0.047 (−0.013 to +0.096) | 0.431 | 0.692 | No |
| L1c flat 10-year | 0.390 | +0.054 (−0.034 to +0.104) | 0.451 | 0.674 | No |
| L2 long-run rate per home | 0.401 | +0.065 (+0.004 to +0.127) | 0.552 | 0.696 | No |
| **L3 partial pull to the long-run rate** | **0.324** | **−0.012 (−0.022 to −0.003)** | **0.309** | 0.611 | **Yes** |
| L4a 10-year trend line | 3.081 | +2.745 | 6.507 | 0.801 | No |
| L4b trend line since 1990 | 0.398 | +0.062 (−0.019 to +0.135) | 0.500 | 0.815 | No |
| L5 division pool | 0.332 | −0.004 (−0.011 to +0.014) | 0.352 | 0.636 | No |

**L3's pick tests:**
- 3.7% below L0's score (0.324 against 0.336; the bar is 2%);
- the 90% range of the difference is entirely below 0;
- Wisconsin alone is 10.5% better (0.309 against 0.346; the bar is not more than 5% worse).

**Where L3's gain comes from.**
- L3's pull strength b is fitted only on start years whose five outcome years had finished.
- For start years 2000–2010, the fit chose b = 0, so L3 was identical to L0.
- From 2011 on, after the crash's outcomes were known, b rose to 0.05–0.35. All of L3's gain is in start years 2011–2020, when forecasts made in the slow years that leaned toward the long-run rate came closer.
- So L3's evidence is essentially one episode, the recovery after 2008. The block bootstrap allows for some of that, but not for "this cycle was unusual".

**Other results.**
- **L4a broke.** A 10-year trend line fitted through the crash went negative, so its log error is very large. The plan counted negative fitted years as fitted, not 0. A negative five-year total is clipped to 1e-9 before the log; the plan does not specify this clip, and it cannot change the pick. It was never a contender.
- **Building sizes.** L3 is better than L0 for 1-unit, 2-unit and 3–4 unit buildings, and slightly worse for 5+ units (0.410 against 0.405).
- **Census divisions.** L3 is better than L0 in 8 of 9 divisions; the exception is division 9, Pacific (0.360 against 0.358). For Wisconsin's division, East North Central, it is 0.353 against 0.369 (`_by_group.csv`).

**Wisconsin 2027–2031** (start year 2025; b fitted on start years up to 2020 = 0.35; an earlier version said 0.40, a rounding artefact in a printout). Each figure is homes permitted over the five years. The published Census files are scaled by the ratio to L0 (×124,000 ÷ 118,148), as the plan log says, so v3's Milwaukee and fill corrections are kept.

| | Published Census files | Scaled to v3 |
| --- | ---: | ---: |
| L0 (current rule) | 118,148 | 124,000 |
| **L3** | **126,207** | **132,458** |
| L5 (region) | 115,371 | 121,086 |
| L1c (10-year) | 107,022 | 112,322 |

**Scaling check (audit):** applying the ratio to L0 by building size, not one ratio for the total, gives 131,876 (1 unit 73,756; 2 units 8,037; 3–4 units 1,281; 5+ units 48,801). That is 582 below the one-ratio figure, because v3's Milwaukee and fill corrections fall mostly on 5+ units, where L3 is lower.

L3's rise is mostly in 1-unit buildings (73,084 against 62,915 published) and 3–4 units. Its 5+ units fall (43,966 against 46,812), because Wisconsin's long-run rate per home is above its recent rate for houses and below it for apartments.

## The range and its out-of-sample check

The range multipliers are actual ÷ predicted from Wisconsin's own start years. The coverage check rebuilds the range for each start year 2005–2020 from start years at least 5 years earlier, and asks whether that start year's actual five-year total landed inside. There are 16 checks, so coverage moves in steps of 6.25 points.

| Candidate | 10th–90th | 5th–95th | 2.5th–97.5th |
| --- | ---: | ---: | ---: |
| L0 (current) | 6 of 16 (37.5%) | 7 of 16 (43.8%) | 7 of 16 (43.8%) |
| L3 | 7 of 16 (43.8%) | 7 of 16 (43.8%) | 7 of 16 (43.8%) |

None reaches the 80% target. The reason is plain from the history:
- ranges built from the 1990s and early 2000s did not expect the crash;
- ranges built after the crash did not expect the recovery.

By the stop rule, the 2.5th–97.5th range is used, with a shortfall of 36 points. **Past ranges built this way held the outcome 7 of 16 times.** With 24–29 values per building size, the 2.5th and 97.5th percentiles sit close to the smallest and largest past values.

| Wisconsin 2027–2031, homes permitted (scaled to v3) | Low | Central | High |
| --- | ---: | ---: | ---: |
| v3 now (L0, 10th–90th) | 65,250 | 124,000 | 177,672 |
| L0, 2.5th–97.5th | 53,875 | 124,000 | 204,889 |
| **L3, 2.5th–97.5th (the plan's rule)** | **56,592** | **132,458** | **206,406** |
| L3, 10th–90th | 65,246 | 132,458 | 185,592 |
| L3, 2.5th–97.5th, all-states multipliers (sensitivity) | 46,987 | 132,458 | 286,716 |

The low and high are scaled by the same ratio as the central (×124,000 ÷ 118,148). This final-range table is a reporting addition, written after Part 1 ran (d039d77); it does not touch scores or the pick. Source: `reference/baseline_bakeoff_part1_final_ranges.csv`, `_coverage_summary.csv`.

## Part 2: the split among towns

**Linking.** Town permit rows for 1990–2025 link to today's 1,925 pieces through the foundation crosswalk, plus 8 hand-checked renames (plan log). Linked units are 99.9% to 100.7% of the state file in every year, except 1991–1993 (105%), where the town files themselves sum above the state file. Every year passes the 95% check.

Score: the sum over pieces and sizes of |predicted − actual| ÷ actual units, with each candidate scaled to the actual state total. It is averaged over 17 start years (2004–2020). Lower is better: 0.53 means the split misplaces about 53 homes per 100 permitted.

| Candidate | Score | Difference from S0 (90% range) | Places with 1,000+ homes | Under 1,000 homes | Passes? |
| --- | ---: | --- | ---: | ---: | --- |
| S0 own 3-year (current) | 0.530 | — | 0.549 | 0.445 | — |
| S1a own 5-year | 0.523 | −0.007 (−0.014 to −0.004) | 0.540 | 0.445 | No (1.3%, under the 2% bar) |
| S1b own 10-year | 0.527 | −0.002 (−0.022 to +0.005) | 0.543 | 0.455 | No |
| S2a county 3-year pace | 0.527 | −0.003 (−0.019 to +0.006) | 0.545 | 0.450 | No |
| S2b county 10-year pace | 0.530 | +0.000 (−0.020 to +0.008) | 0.546 | 0.457 | No |
| S3 shrink toward the county | 0.529 | −0.000 (−0.001 to +0.001) | 0.548 | 0.442 | No |
| S4 lumpy-year cap (2×) | 0.535 | +0.006 (−0.012 to +0.018) | 0.554 | 0.464 | No |
| S4 cap 3× (sensitivity) | 0.532 | +0.002 (−0.012 to +0.010) | 0.551 | 0.459 | — |

- **Shrinking (S3) chose almost no pull.** The fitted k was 10 to 32 homes, against a typical town of about 1,000. The best shrink was nearly none, which is the tutor's idea tested with a county target.
- **Capping lumpy years (S4) made the split worse.** Big projects in one year tend to be followed by more big projects in the same place.
- **The 5-year average (S1a)** was better in the bootstrap (range entirely below 0) but missed the 2% margin. It is a candidate worth naming for a second round, not a change now.

**Joint check (reported only).** The level × split on Wisconsin pieces, not scaled: L0 × S0 scores 0.747 and L3 × S0 scores 0.753 (0.8% worse). At the town level, L3's higher total does not help, so the gain is in the state total, not in where homes land.

## What it means for the scenarios (if Ryan adopts L3)

| Scenario | Effect |
| --- | --- |
| ADU | The shared comparison divides by the baseline. Each ADU share of the baseline falls by about 6.4% (×124,000 ÷ 132,458). ADU's own permit numbers do not change. |
| TOD | Station-area baselines are shares of town rows, so they rise by about 6.8%, with the same split. TOD effects measured per existing home do not change, but "share of baseline" lines do. TOD and combined bundles need rebuilding. |
| Parking | The same: per-1,000-existing-home effects do not change; "share of baseline" lines and the baseline line itself rise by about 6.8%. Parking and combined bundles need rebuilding. |
| Range | Wider on both sides under the plan's stop rule (56,592 to 206,406), and it should carry a sentence that past ranges held the outcome only about 7 times in 16. |

## Points for Ryan (audit)

1. **The pull strength b.** The 2027–2031 figure uses b = 0.35 (corrected from 0.40, which was a rounding artefact). That value was used in scored start years 2018–2020, so this point falls away.
2. **L3 leans high in Wisconsin.** Its average log ratio is +0.126 (over-predicting by about 13%), against +0.083 for L0. It is closer on average, but it over-predicts more.
3. **One episode.** All of the gain comes from start years 2011–2020.
4. **The range.** Past ranges held the outcome 7 of 16 times at best.

## Limits

- L3's gain rests on one episode, the post-2008 recovery.
- Homes come from decennial counts plus permits, with no demolitions. The 1990 state counts are the 1999-revised April 1990 figures (a small labelled leak).
- Today's one-unit homes split county rows and changed-type towns (a small look-ahead).
- Annexations are not rebuilt.
- Part 2 has about 3 independent periods.

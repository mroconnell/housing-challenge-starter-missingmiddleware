# Baseline range, round 2: results

Written 2026-11-05 by the baseline thread. Plan: [BASELINE_RANGE_PLAN.md](BASELINE_RANGE_PLAN.md) (locked; Ryan's go 18:08 UTC). Script: `scripts/run_baseline_range.py` (3f39680c, committed before the run). Outputs:
- `reference/baseline_range_coverage.csv`
- `reference/baseline_range_coverage_summary.csv`
- `reference/baseline_range_wisconsin.csv`

**Status: for the audit and Ryan. The tool is not changed.**

## Answer

1. **Only one range clears the plan's 90% bar, and it is not usable.** The locked rule picks it: all states pooled (R1), smallest-to-largest past values, around the flat 3-year central (L0). It held 95.1% of past checks in the other 50 states and 15 of 16 in Wisconsin. But its Wisconsin 2027–2031 range runs from 27,907 to 6,554,640 homes, because one state's most extreme past ratio sets the top.
2. **No range built from middle percentiles reaches 90% over all check years.**
   - The pooled 5th–95th held 64.9% in the other 50 states and 12 of 16 in Wisconsin.
   - The pooled 2.5th–97.5th held 70.5% and 12 of 16.
   - Wisconsin-only ranges (R0) held at most 58.1% and 7 of 16.
3. **Almost every miss comes from the first crash.** In check years 2005–2008, the past data held no crash, so no range expected one: pooled 5th–95th coverage was 0–4% in those years.
4. ***Post hoc*: once a crash is in the data, the pooled ranges hold.** This subset was chosen after seeing the results:

   | Check years 2009–2020 | Other 50 states | Wisconsin |
   | --- | ---: | ---: |
   | L0, pooled 5th–95th | 86.0% | 12 of 12 |
   | L0, pooled 2.5th–97.5th | 92.5% | 12 of 12 |

   Every range built today includes the 2007–2011 crash.

## Coverage, all check years 2005–2020

The main method uses multipliers on the all-sizes total. "Other 50" is the share of 800 state-year checks whose actual five-year total landed inside, with a block-bootstrap 90% range over check years. Wisconsin is 16 checks.

| Level | Range from | Step | Other 50 (90% range) | Wisconsin | WI 2027–2031, homes (scaled to v3) |
| --- | --- | --- | --- | ---: | --- |
| L0 | Wisconsin only | 5th–95th | 53.8% (30.9–77.4%) | 6 of 16 | 53,344 to 183,435 |
| L0 | Wisconsin only | 2.5th–97.5th | 56.6% (33.4–81.2%) | 7 of 16 | 51,433 to 186,954 |
| L0 | Wisconsin only | min–max | 58.1% (35.1–82.6%) | 7 of 16 | 49,957 to 190,515 |
| L0 | All states | 5th–95th | 64.9% (41.6–90.6%) | 12 of 16 | 56,436 to 216,977 |
| L0 | All states | 2.5th–97.5th | 70.5% (50.0–94.9%) | 12 of 16 | 48,709 to 244,147 |
| **L0** | **All states** | **min–max (the rule's pick)** | **95.1% (90.2–100%)** | **15 of 16** | **27,907 to 6,554,640** |
| L3 | Wisconsin only | 5th–95th | 50.6% | 7 of 16 | 56,129 to 182,925 |
| L3 | All states | 5th–95th | 62.0% | 11 of 16 | 58,561 to 226,187 |
| L3 | All states | 2.5th–97.5th | 68.0% | 12 of 16 | 50,138 to 248,535 |
| L3 | All states | min–max | 80.0% | 12 of 16 | 29,810 to 1,449,156 |

- **Per-size sums** (the alternative, reported only) cover a few points more and are wider. Pooled 2.5th–97.5th around L0, for example, covers 75.2% and gives 45,889 to 316,158.
- **Volatility groups** (pooled 5th–95th, L0): calm states 70.9%, middle 68.2%, volatile 55.3%. Pooling does not over-cover Wisconsin. Its tercile changes between check years, so no single group is named.
- Source: `_coverage_summary.csv`.

## Reading

- **The plan's rule picked a range that cannot be used.** The 6.5 million top comes from one extreme state ratio. That is a literal outcome of the rule, reported as such, and it is not a recommendation.
- **The useful finding is post hoc.** Pooled middle-percentile ranges held well in every check year after a crash was in the record, and every range built now has one. On that subset, the pooled 2.5th–97.5th around the current central held 92.5% in the other 50 states and 12 of 12 in Wisconsin: 48,709 to 244,147 homes for 2027–2031. Adopting it would rest on a subset chosen after seeing the results, so it is Ryan's call and should be labelled that way.
- **A correction to the bake-off write-up.** L3's pull strength for 2027–2031 is b = 0.35, not 0.40. The earlier "0.40" was a rounding artefact in a printout; the figure 132,458 was always computed with 0.35. So the audit's point that 0.40 was never tested falls away: 0.35 was used in scored start years 2018–2020.

## Choices for Ryan

| Option | Wisconsin 2027–2031 range, homes | Basis |
| --- | --- | --- |
| A. Keep v3 (Wisconsin only, 10th–90th) | 65,250 to 177,672 | An 80% range; held 6 of 16 in past checks |
| **B. All states pooled, 2.5th–97.5th, around 124,000 (recommended, post hoc)** | **48,709 to 244,147** | Held 92.5% (other 50) and 12 of 12 (Wisconsin) since 2009; 70.5% and 12 of 16 over all years |
| C. The rule's literal pick | 27,907 to 6,554,640 | Not usable |

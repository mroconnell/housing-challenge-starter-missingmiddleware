# County test of the LASSO's tight ranges: results (*post hoc*)

Written 2026-11-05 by the baseline thread.
- **Plan:** [BASELINE_RANGE_COUNTY_PLAN.md](BASELINE_RANGE_COUNTY_PLAN.md) (lock and script 47d1f151; run 20:58:47 UTC).
- **Outputs:** `reference/baseline_range_county_checks.csv`, `_summary.csv`.

**Status: for the audit and Ryan. Not a pick; the tool is not changed.**

## Answer

1. **By the locked reading rule, the test cannot say: "too few".** At the county level, the LASSO almost never gave a range as tight as Wisconsin's 2027–2031 range (log width 1.1 or less). It did so once, in 6,620 checks.
2. **Its somewhat tighter county ranges held well under 90%.** The bootstrap figures for these two bins are reported, but they are not a fair measure, because all of these checks come from one start year:

   | Log width | Checks | Held | Start years |
   | --- | ---: | ---: | --- |
   | 1.1–1.3 | 545 | 81.8% | all 2009 |
   | 1.3–1.5 | 92 | 67.4% | 73 from 2009, 19 from 2010 |

   - **They are one forecast.** In 2009 the training data held only start years up to 2004, all before the crash, so the LASSO saw calm history and gave tighter ranges. They are effectively one forecast made once, not hundreds of separate tests. The block bootstrap over years cannot show year-to-year variation with only one year, so its ranges understate the uncertainty.
   - **Reading (not a rule outcome).** When the LASSO's history looked calm, its tighter ranges were over-confident. That is one episode.
3. **Overall, at the county level** (2009–2020, 739 counties in 51 states, 6,620 checks):
   - **The LASSO (E2):** held 95.6% (bootstrap 92.7–99.2%), with a median log width of 2.14. Wisconsin's counties held 134 of 140 (95.7%).
   - **All counties pooled (A):** held 84.5% (bootstrap 70.9–91.8%), with a median width of 1.98. Wisconsin's counties held 126 of 140 (90.0%).
4. **The question stays open.** The county test can neither confirm nor rule out that the LASSO's tight Wisconsin range (log width 1.03) holds 90% of the time. Its only nearby evidence comes from the 2009 forecasts, and that evidence points to over-confidence.

## Why counties rarely got tight ranges

Counties swing much more than states, so the LASSO gives them wide ranges: the median log width is 2.1 from 2010 on. The tightest ranges appear only in 2009, the first check year, when its training history was calm.

## Choices for Ryan (unchanged from round 4)

| Range, Wisconsin 2027–2031 | Low | High | Record (states, 2009–2020) |
| --- | ---: | ---: | --- |
| All states (round 4) | 56,500 | 218,865 | 88.3%; Wisconsin 12 of 12 |
| All states, 2.5th–97.5th (round 2) | 48,709 | 244,147 | 92.5% (post hoc window); Wisconsin 12 of 12 |
| LASSO (E2) | 74,119 | 207,450 | 98.8%; Wisconsin 12 of 12; tighter than any range it gave Wisconsin; untested at this width |

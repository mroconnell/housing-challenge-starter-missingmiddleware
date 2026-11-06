# ADU market-drift check: results

Run 2026-11-06 under [MARKET_DRIFT_PLAN.md](MARKET_DRIFT_PLAN.md), which was written and audited before running, with its post hoc changes logged and timed. Code: [`scripts/run_adu_market_drift.py`](../../scripts/run_adu_market_drift.py). Outputs: `reference/adu_market_drift_*.csv`. Nothing in the tool has changed. Ryan decides any change.

**Units.**
- Changes are ADU permits in Wisconsin over 2027–2031, at typical adoption (the former central, 10,492).
- Heat and drift are log ratios of a state's all-units permit rate to the national rate. −0.19 means about 17% below.

**Order.** A 2-draw smoke test, started at 19:37:26 UTC after the audit's fixes, showed +826. The main line and the decision rule were locked before it and are unchanged. The counted run (200 draws) started at 19:40:14 UTC. At the interval ends, 200 draws carry about 1–2 points of coverage error.

## Answer

- **By the locked rule: "drift effect measured."**
  - Main line: +826 ADU permits (10,492 → 11,318).
  - 90% interval, by convention, from the chain bootstrap: +384 to +1,261.
- **The regression to the mean Ryan described contributes about nothing.**
  - The heat term alone gives −51. This post hoc line has no interval, so "about nothing" is a point reading, not a tested zero.
  - Hot law states (Utah, Oregon, Colorado) were due to cool, and cold ones (Rhode Island, Massachusetts, Vermont) to warm. Each slope is small (b = −0.01 to −0.06), and the two groups roughly cancel.
- **The +826 comes from the intercepts, and most of that is a construction effect, not drift.**
  - Non-law states lose ground against a national rate weighted by homes, because growth sits in a few large states.
  - Weighting the national rate equally across states (post hoc, no interval) cuts the change to +254.
- **My reading: don't move the ADU lines.** Keep the drift-adjusted figures as a "How sure" sensitivity, for Ryan to decide. The rule's test is met, but the change is mostly an artefact of how the drift was defined.

## D1. Drift from states with no ADU law

Drift fit per horizon h (years after the 3-year heat window). Data: Census BPS all units, 2010–2025; 48 to 51 states.

| h | Intercept a (home-weighted nation) | Slope b | Intercept a (equal-weighted, post hoc) | Slope b (equal-weighted) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | −0.033 | −0.014 | −0.010 | −0.012 |
| 2 | −0.048 | −0.027 | −0.013 | −0.024 |
| 3 | −0.064 | −0.041 | −0.017 | −0.037 |
| 4 | −0.076 | −0.044 | −0.024 | −0.040 |
| 5 | −0.093 | −0.049 | −0.032 | −0.045 |
| 6 | −0.111 | −0.059 | −0.040 | −0.053 |

Law states before their laws (heat), with predicted and actual drift in their first law year:

| State | Law year | Heat | Predicted drift, k = 1 | Actual drift, k = 1 |
| --- | ---: | ---: | ---: | ---: |
| California | 2020 | −0.19 | −0.030 | −0.161 |
| Oregon | 2020 | +0.19 | −0.035 | −0.205 |
| Vermont | 2021 | −0.51 | −0.026 | −0.064 |
| Utah | 2022 | +0.94 | −0.046 | −0.138 |
| Maine | 2025 | −0.24 | −0.029 | +0.164 |
| Massachusetts | 2025 | −0.80 | −0.022 | −0.087 |
| Rhode Island | 2025 | −1.30 | −0.014 | +0.277 |
| Washington | 2026 | +0.08 | −0.034 | not yet |
| Colorado (Denver) | 2025 | +0.36 | −0.038 | −0.086 |

Actual drift is shown for reference only. It is not used: it would mix the law's own effect into the adjustment.

**Wisconsin, ADU permits over 2027–2031:**

| Line | Lower side line | Typical adoption | High side line | 8-state median | A3 range | Change at typical |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Adopted | 6,320 | 10,492 | 19,784 | 10,038 | 8,055–13,666 | 0 |
| **Drift-adjusted, 1-for-1 (main)** | 6,834 | 11,318 | 21,336 | 10,752 | 8,689–14,742 | **+826 (90%: +384 to +1,261)** |
| Drift-adjusted, Washington elasticity 1.32 | 6,997 | 11,579 | 21,831 | 10,994 | 8,890–15,082 | +1,087 |
| Post hoc: heat term only | 6,261 | 10,441 | 19,722 | 10,125 | 8,016–13,599 | −51 |
| Post hoc: equal-weighted national rate | 6,462 | 10,746 | 20,284 | 10,291 | 8,250–13,997 | +254 |

- The A3 range for each line is that line's typical figure × the adopted A3 factors.
- Bootstrap: 200 draws over states with no law, through the drift fit, the law states' drifts, the pooled refit and the Wisconsin engine. Median change +765.

**Wisconsin's own market (report only).**
- Wisconsin's heat over 2023–2025 is −0.19, a cool market.
- The fit predicts its drift is negative, and that comes from the intercepts again. Scaled by it, the ADU baseline would go from 786 to 731.
- The heat term alone would raise it slightly. The all-housing drift belongs to the Baseline thread.

## D2. ADU pre-trends and how ADUs follow the market

| State | Pre-law years | Yearly ADU growth before the law | 90% interval (bootstrap over years) | Against the 7.3% no-reform trend |
| --- | --- | ---: | --- | --- |
| Washington | 2011–2025 (OFM) | 18.2% | 16.4% to 19.5% | Above it |
| California | 2012–2016 (BuildinganADU) | 40.2% | 19.4% to 87.4% | Above it |
| Rhode Island | 2021–2023 | 7.0% | no interval (2 steps; flagged) | — |

- Growth is the year slope of a Poisson fit on counts, with single-family homes as exposure.
- **Washington's and California's ADU permits rose much faster before their laws than the 7.3% no-reform trend.** Both had local reforms and earlier state rules in those years: Washington's 1993 rule, and California's ADU bills before 2017. So these are not clean no-reform years.
- They hint that the 7.3% trend may be low for active states. A higher trend would raise the ADU baseline and lower the law's addition. This is reported, not applied.
- **Washington's ADUs against its all-units permits:** log–log slope 1.32 (90% interval 0.06 to 2.04; 15 years). ADUs do move with the market, but the slope is poorly pinned down, so the 1-for-1 assumption cannot be tested well.

## Checks

- **Panel check.** The Baseline thread's state panel matches the Census BPS files in 612 of 612 state-window totals (`adu_market_drift_panel_check.csv` is empty).
- **The adopted run reproduces the tool:** 10,492.

## Limits

- Drift rests on 8 law states' heat, and only 3 states have pre-law ADU counts.
- Heat is measured on all housing. ADUs may follow a different cycle.
- The denominator is a fixed home count (ACS 2020–2024).
- Drift is measured against the national rate, but the adjustment divides absolute ADU rates by that relative drift. It leaves out how the national rate itself changed. So the intercept part is not a clean drift measure under either weighting.
- The intercepts depend on how the national rate is weighted. The planned definition (home-weighted) and the post hoc one (equal-weighted) differ by 572 ADU permits at typical adoption.

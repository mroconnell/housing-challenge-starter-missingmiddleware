# ADU placebo test: results

Run 2026-10-27 under the plan in [PLACEBO_PLAN.md](PLACEBO_PLAN.md). The plan was written before any of these comparisons were computed; changes made after it are listed in its last section. Code: `scripts/run_adu_placebo.py`. Tables: `reference/adu_placebo_series.csv` (one row per real-law series), `adu_placebo_eligible.csv` (every no-law series × fake law year), `adu_placebo_summary.csv` (group results and the placebo distributions) and `adu_placebo_wi.csv` (Wisconsin engine cases). The adopted ADU outputs (`reference/adu_model_*.csv`) are unchanged.

**Units.** Every rate below is ADU permits per 1,000 one-unit detached homes per year. The numerator is the series' ADU count; Wisconsin counts second-home permits on single-family lots. The denominator is the ACS 2020–2024 one-unit detached homes in that geography times the years in the window. A **change** is the after rate minus the before rate, in the same units. A **ratio** is the after rate divided by the before rate. "Before" is the 3 years before the law year and "after" is the 3 years after it; the law year itself is dropped.

## Plain-language summary

- **By the pre-registered rule, the statewide law matters beyond the trend, and the dose-response order holds.**
  - **Strong-law places (A):** the average rose from 0.24 to 0.99, a change of +0.75 and a ratio of 4.1. These are 2 series, California and Washington cities outside Seattle.
  - **Weaker-law places (B):** the average rose from 0.42 to 0.87, a change of +0.45 and a ratio of 2.1. These are 2 series, Rhode Island and Chittenden County, Vermont.
  - **No-law places (C):** the median of 2,000 placebo draws rose from 0.53 to 0.75, a change of +0.25 and a ratio of 1.52. In the plan's comparison, no draw out of 2,000 reached A's or B's change or ratio.
  - So the order is A > B > C on both measures.
- **But the evidence is thinner than that sounds.**
  - **Small groups.** A and B each have only 2 series. Compared with placebo groups of the same size (2 no-law series per draw), the result is weaker:
    - A's change of +0.75 is matched or beaten by 16% of draws (316 of 2,000). Only its ratio of 4.1 stands out: 2.7% of draws (54 of 2,000) reach it.
    - B is matched or beaten by about a quarter of draws (26% for the change, 25% for the ratio).
  - **Single series.** One at a time, each real-law series sits inside the spread of single no-law series. California's change is matched or beaten by 7% of the 101 no-law series-and-year combinations, Rhode Island's by 10%, Washington's by 19% and Vermont's by 44%.
- **No-law places did rise, but almost only when they changed their own rules.**
  - The pre-registered test counts this rise as material. The median no-law ratio of 1.52 is above the plan's 1.25 threshold.
  - Dropping the windows that contain a local reform (pre-stated check S2) leaves no rise at all: change −0.04, ratio 0.92. Those reforms are Seattle 2019, Portland 2010 and 2016, Austin 2015, Madison 2021, Minneapolis 2020–21, Denver 2023 and Montgomery County 2019.
  - So the "national trend" in these places is mostly local reform.
- **Wisconsin.** Suppose every place's current-law rate rose the way the no-law places did (ratio 1.52 per 4 years, about +11% a year).
  - The statewide baseline for 2027–2031 would rise from 604.6 to 1,083.3 permits (+478.6).
  - The central law addition would fall from 8,756.6 to 8,324.3 permits (−432.4).
  - The total with the law would barely move, from 9,361.3 to 9,407.5 permits (+46.3, or +0.5%).
  - So a rising baseline changes how the total is split between "would have happened anyway" and "the law". It hardly changes the total.
- **Recommendation: keep the model.** Add the rising baseline as a named baseline-only sensitivity, not as the main case. Do not change the law effect. The pre-registered rule says "add a rising baseline", because the no-law rise passes the materiality threshold. The reasons for not following it are in section 6, and it is the owner's call.

## 1. The series

### Real laws (groups A and B)

| Group | Series | Year 0 | Before: count / thousand home-years = rate | After: count / thousand home-years = rate | Change | Ratio |
| --- | --- | --- | --- | --- | ---: | ---: |
| A | California, CA-study non-holdout groups | 2016 | 2014–15 period rate 0.12 (rates only) | 2017 0.66; 2018–19 1.48 → 1.21 | +1.09 | 10.1 |
| A | Washington cities and towns excl. Seattle (OFM estimate years) | EY2023 | EY2020–22: 1,163 / 3,176.8 = 0.37 | EY2024–26: 2,466 / 3,176.8 = 0.78 | +0.41 | 2.12 |
| B | Rhode Island | 2024 | 2021–23: 186 / 812.4 = 0.23 | 2025: 262 / 270.8 = 0.97 | +0.74 | 4.23 |
| B | Chittenden County, VT (by year built) | 2020 | 2017–19: 71 / 116.0 = 0.61 | 2021–23: 89 / 116.0 = 0.77 | +0.16 | 1.25 |
| A, S3 | Oregon 32 cities excl. Portland (law year as "before") | 2018 | 2018: 166 / 364.5 = 0.46 | 2019–21: 979 / 1,093.5 = 0.90 | +0.44 | 1.97 |
| A, S6 | California's 15 Madison-like cities | 2016 | 2013–15: 7 / 2,025.5 = 0.003 | 2017–19: 111 / 1,944.3 = 0.06 | +0.05 | 16.5 |

**Washington's Madison-like cities** (sub-check; already inside the Washington series). Before is EY2020–22, after is EY2024–26:
- **Spokane:** 29 → 92 permits; 0.15 → 0.47.
- **Spokane Valley:** 19 → 16 permits; 0.23 → 0.20.
- **Tacoma:** 45 → 313 permits; 0.25 → 1.77.
- **Vancouver:** 68 → 87 permits; 0.52 → 0.67.
- **Yakima:** 6 → 30 permits; 0.09 → 0.45.

**Levels only** (no year before the law, so no change can be measured):
- **Maine 2025:** 516 permits / 526.2 thousand home-years = 0.98.
- **Massachusetts 2025:** 1,224 / 1,549.6 = 0.79.
- **Utah, report years 2023–25:** 2,752 / 2,441.8 = 1.13.
- **New Hampshire conversions proxy, 2020–24:** 1,886 / 2,052.2 = 0.92.
- **Oregon's 4 Madison-like cities, 2018–23:** 529 / 776.5 = 0.68.

**Moved from B to C.** Honolulu and Montgomery County have no years after their state's law (Hawaii 2024, Maryland 2025), so they cannot be B. Their years are no-law years, so they joined C. Utah and New Hampshire have no before year.

So each group has 2 usable series. Mercatus rates Rhode Island, Utah and Vermont as weaker states, yet all three are in the adopted pooled model.

### No-law places (group C)

The 11 series are:
- Minneapolis 2017–2025.
- Denver 2016–2023.
- Austin 2005–2023.
- Portland 2005–2017.
- Madison 2014–2025.
- Sun Prairie and Pleasant Prairie, pooled.
- Honolulu 2016–2023.
- Montgomery County 2019–2024.
- **Under an older, weaker state law** (flagged; dropped in S1):
  - Seattle 2005–2022;
  - Washington cities excluding Seattle, EY2011–2023;
  - California's 15 Madison-like cities, 2012–2016.

Together they give 101 combinations of series and eligible fake law year. 22 of those combinations fall in the calendar-matched years 2016, 2020, 2023 and 2024. California's pre-2017 cities have no calendar-matched year, so each main draw uses 10 series.

| Statistic | 5th percentile | Median | 95th percentile |
| --- | ---: | ---: | ---: |
| Single no-law series, all 101 fake years: change | −0.12 | +0.12 | +1.42 |
| Single no-law series, all 101 fake years: ratio (96 with a before rate above 0) | 0.40 | 1.61 | 5.43 |

The no-law places did very different things:
- **Fell:** Minneapolis fell after its 2020–21 changes (change −0.16 around 2020), and so did Honolulu (−0.54 around 2020).
- **Rose sharply after local reforms:** Portland (+1.42 around 2016), Seattle (+1.93 around 2020) and Madison (+0.20 around 2023).
- **Rose steadily:** Washington cities before the state law, +0.13 to +0.25 for every fake year from 2016 to 2022.

## 2. Where A and B fall in C's distribution

The share of placebo draws whose value is at or above A's or B's is the one-sided placebo p-value.

| Case | Statistic | A | B | C 5th / median / 95th | Share of C draws ≥ A | Share ≥ B |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| **Main (plan): all C series, calendar-matched years** | change | +0.75 | +0.45 | +0.18 / +0.25 / +0.38 | 0.000 | 0.000 |
| | ratio | 4.08 | 2.06 | 1.33 / 1.52 / 1.71 | 0.000 | 0.000 |
| S1: only states with no ADU law of any kind (8 series) | change | +0.75 | +0.45 | +0.13 / +0.17 / +0.22 | 0.000 | 0.000 |
| | ratio | 4.08 | 2.06 | 1.24 / 1.34 / 1.47 | 0.000 | 0.000 |
| S2: windows without a local reform (6 series have one) | change | +0.75 | +0.45 | −0.05 / −0.04 / −0.02 | 0.000 | 0.000 |
| | ratio | 4.08 | 2.06 | 0.88 / 0.92 / 0.95 | 0.000 | 0.000 |
| S3: Oregon added to A (3 series) | change | +0.65 | +0.45 | as main | 0.000 | 0.000 |
| | ratio | 3.06 | 2.06 | as main | 0.000 | 0.000 |
| S4: every eligible year | change | +0.75 | +0.45 | +0.03 / +0.18 / +0.36 | 0.000 | 0.005 |
| | ratio | 4.08 | 2.06 | 1.10 / 1.54 / 2.09 | 0.000 | 0.064 |
| S5: home-weighted (A = Washington only) | change | +0.41 | +0.63 | +0.06 / +0.12 / +0.18 | 0.000 | 0.000 |
| | ratio | 2.12 | 3.28 | 1.14 / 1.26 / 1.37 | 0.000 | 0.000 |
| S6: California's Madison-like cities in A | change | +0.23 | +0.45 | as main | **0.611** | 0.000 |
| | ratio | 2.26 | 2.06 | as main | 0.000 | 0.000 |
| D1 (added): 2 C series per draw, calendar-matched | change | +0.75 | +0.45 | −0.27 / +0.14 / +0.98 | **0.158** | **0.260** |
| | ratio | 4.08 | 2.06 | 0.65 / 1.56 / 2.72 | 0.027 | **0.254** |
| D1 (added): 2 C series per draw, every year | change | +0.75 | +0.45 | −0.29 / +0.12 / +0.94 | **0.084** | **0.154** |
| | ratio | 4.08 | 2.06 | 0.53 / 1.59 / 4.19 | 0.052 | **0.311** |

All cases use 2,000 draws with seed 20261027.

**Reading it:**
- **The plan's rules separate A clearly from C:** at most 0.5% of draws (10 of 2,000) reach A's or B's change in any of the pre-stated cases S1 to S5.
- **The plan's distribution is too narrow for a 2-series group.** It averages about 10 C series per draw.
  - With groups of 2 (D1), A's ratio still stands out: 2.7% of draws reach it.
  - A's change does not stand out: 16% of draws reach it.
  - B does not stand out on either measure.
- **The A result leans on California's statewide groups.** With California's inland Madison-like cities instead (S6), A's change (+0.23) is below the median no-law change: 61% of draws are at or above it. These cities were near zero before 2017, so their ratio (16.5) is large while their change is small.
- **Own pre-law trend (exploratory):**
  - **Washington cities excluding Seattle:** before the state law, placebo years 2012–2022 gave changes from +0.03 to +0.25 and ratios from 1.3 to 2.0. After the law, the change was +0.41 and the ratio 2.12, just above that range.
  - **Chittenden County:** placebo years 2011–2018 gave changes from +0.06 to +0.42. After Act 179 the change was +0.16, inside that range. Vermont has allowed ADUs by right since 2004, which Act 179 eased further.

## 3. Decision rule (as pre-registered)

| Rule | Result |
| --- | --- |
| 1. Law matters beyond the trend (A's change and ratio both above C's 95th percentile) | **Holds** in the main case (+0.75 > +0.38; 4.08 > 1.71) and in S1–S5. Under D1 (added), A's ratio is above C's 95th percentile but its change is not, which would be **mixed** |
| 2. Trend could explain it (A's change at or below C's 95th percentile) | Not in the main case; yes under D1 and S6 |
| 4. Trend share (C's median change / A's change) | 0.249 / 0.748 = **33%** of A's rise was also seen, on the median, in no-law places in the same calendar years. Without local-reform windows (S2) it is about 0% (−0.04 / 0.75) |
| 5. Dose-response A > B > C's median | **Holds** on both measures in the main case: change +0.75 > +0.45 > +0.25; ratio 4.08 > 2.06 > 1.52. It fails home-weighted (S5: B +0.63 > A +0.41) and with California's Madison-like cities (S6: A +0.23 < B +0.45) |
| 6. No-law places rose materially (C's median ratio ≥ 1.25 or median change ≥ 0.10) | **Yes** in the main case (ratio 1.52; change +0.25) and in S1 (1.34; +0.17). **No** in S2 (0.92; −0.04) |

The pre-registered recommendation rule follows from rules 1 and 6: **add a rising baseline**. Section 6 explains why the recommendation here departs from it.

## 4. Implications for Wisconsin

**How this was run.** These are the adopted engine settings (the scenario, per-area levels and Madison path from `scripts/run_adu_model.py`), rerun with only the current-law baseline changed. Nothing in `reference/adu_model_*.csv` was written. The rerun reproduces the adopted totals exactly before any change is made.

**The adopted baseline.** Wisconsin's current-law rate is 121.3 permits a year over 1,839,569 one-unit detached homes, about 0.066 per 1,000 homes a year.

All figures in the table are permits summed over 2027–2031:

| Case | Baseline | Law's addition, lower / central / upper | Total with the law, central | Change in baseline | Change in central addition | Change in central total |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Adopted (flat baseline) | 604.6 | 5,538.1 / 8,756.6 / 16,888.9 | 9,361.3 | — | — | — |
| Rising, proportional, at C's median ratio 1.52 per 4 years | 1,083.3 | 5,107.3 / 8,324.3 / 16,455.2 | 9,407.5 | +478.6 | −432.4 | +46.3 (+0.5%) |
| Rising, proportional, at C's 95th-percentile ratio 1.71 | 1,287.2 | 4,921.9 / 8,138.2 / 16,268.6 | 9,425.4 | +682.6 | −618.4 | +64.1 (+0.7%) |
| Rising, additive, at C's median change of +0.25 per 4 years (sensitivity) | 3,748.6 | 2,799.7 / 5,966.9 / 14,086.2 | 9,715.5 | +3,144.0 | −2,789.7 | +354.2 (+3.8%) |

**The proportional case.** Each place's current-law rate is multiplied by 1.11 for each year after the centre of the 2022–2025 measurement window (2023.5). That is ×1.44 in 2027 and ×2.18 in 2031.

**The additive case.** Every place, rural towns included, gains 0.062 per 1,000 homes for each year after 2023.5. That is +0.22 in 2027 and +0.47 in 2031, against today's statewide 0.066. The increase is taken from big-city no-law places and applied to places that permit almost nothing. Read it as an upper bound, not a forecast.

**Why the total hardly moves.** In the engine, the law lifts each place to a with-law level taken from statewide-law states. That level already contains whatever national trend those states saw. A higher baseline therefore mostly comes out of the law's addition. The total with the law moves only in the ramp-up years (2027–2029, while the law is below full effect) and where a place's baseline would pass its with-law level.

## 5. Limits

- **Few series.** A and B have 2 usable series each. Oregon, Maine, Massachusetts, Utah and New Hampshire have no before year. Honolulu and Maryland have no after year. The group comparison is close to comparing four episodes with a pool of 11 places.
- **Different data types.**
  - State series are self-reported permit totals that include ADUs built with a new house.
  - Chittenden counts by year built.
  - California is a period-rate summary.
  - The city series are issued ADU units excluding ADUs built with a new house.
  - Montgomery is a keyword count.
  - Wisconsin counts second-home permits; Sun Prairie counts applications.
  - Rates are comparable in units, not in definition.
- **Calendar timing.**
  - A's and B's windows sit in 2013–2026. Several C windows sit in 2005–2016, before the national ADU interest of the 2020s.
  - The calendar-matched rule limits this, but Portland and Seattle can only use 2016.
  - Washington's year 1 (EY2024) began 2023-04-02, before the law took effect on 2023-07-23. Most of its cities did not have to comply until 2025-06-30.
- **Confounding local reforms.** Most of C's rise is in windows with a local reform:
  - **Minneapolis:** 2014 ADUs; the 2040 plan (2020); owner occupancy removed in 2021. Its rate fell afterward.
  - **Denver:** 2023 form standards, and 2024 citywide, which is outside the C years.
  - **Austin:** the 2015 ADU reform. HOME (2024) retired the permit category, so 2024 onward is not used.
  - **Portland:** the fee waiver (2010) and 2016 siting rules.
  - **Seattle:** 2009 and 2019.
  - **Madison:** by right in December 2021.
  - **Montgomery County:** 2019.
  - The A and B series also contain city reforms on their own timetables, such as Tacoma 2019 and Spokane 2021–22.
- **Older state laws inside C.** Washington's 1993 law and California's 2003 AB 1866 applied to Seattle, the Washington cities before 2023 and the California cities before 2017. Dropping them (S1) lowers C's rise; it does not raise it.
- **Weights.** The equal weight per series is a choice. Home-weighting makes Washington, not California, define A, and reverses A and B (S5).
- **Partial years.** Wisconsin 2026 (Madison's provisional 42 second homes, 1 January to 23 October) is not used.

## 6. Recommendation

**Keep the model. Add a rising baseline as a named sensitivity, not the main case. Do not change the law effect.**

**Why not change the law effect.** On every check, places after a statewide law end up well above what no-law places reach without a local reform:
- In the main case, the after-law average was 0.99 for A and 0.87 for B. No-law places reached 0.75 at the median, and only 0.39 in windows without a local reform (S2).
- The adopted with-law levels come from those post-law states, not from before/after changes. A placebo on changes does not undercut them.

**Why the rising baseline is not the main case, though the rule calls for it:**
1. Almost all of the no-law rise comes with local reforms (S2 ratio 0.92). In Wisconsin, Madison's 2021 reform is already in the measured baseline, and Milwaukee's 2025 reform already has its own sensitivity case.
2. The 2-series comparison (D1) shows the plan's C distribution was too narrow, so the rule's "material" threshold sits on a fragile basis.
3. Whichever way it goes, the total with the law moves by only +46.3 permits (+0.5%) in the central case. What changes is the split: up to about 432 of the 8,757 central addition permits (5%) could instead be credited to a rising baseline.

**Presentation.** If the owner prefers to follow the pre-registered rule, the rising proportional baseline can become the main case, with the same total. The law's central addition would then be 8,324.3 permits over 2027–2031 instead of 8,756.6. Either way, the tool could say: "about a third of the rise seen after statewide laws also appeared in no-law cities over the same years, mostly where those cities changed their own rules."

## Reproduce

```
uv run python scripts/run_adu_placebo.py            # writes reference/adu_placebo_*.csv (about 3 seconds)
uv run python scripts/run_adu_placebo.py --no-engine # placebo only, without data/processed
bash scripts/test.sh                                 # includes tests/test_adu_placebo.py
```

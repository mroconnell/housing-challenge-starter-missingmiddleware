# Scenario options: the owner's four Gate 4 questions

Prepared 2026-10-26. **Status: analysis for the owner's decision. Nothing adopted has changed:** the engine outputs (`reference/adu_model_*.csv`), the parameters and the tool are untouched. Code: [`scripts/run_scenario_options.py`](../../scripts/run_scenario_options.py) (about 3 seconds). Outputs: `reference/scenario_options_*.csv`.

**Basis.** The adopted model (AQ-042): pooled revision option (ii) cap + A2, configuration A (California in the common level), Madison on the Madison-like path, Madison floor 0.2345. The script reproduces the adopted engine to within 1 permit (lower 4,407, central 8,721, Strong adoption 16,853; baseline 644.9) before it computes anything new.

**Units.**
- A **rate** is second-home permits on single-family lots in a year ÷ thousands of one-unit detached homes (ACS 2020–2024 B25024_002). It is written "per 1,000 single-family homes per year".
- A **typical-place level** is a state's modelled rate at its own typical place (homes-weighted average market) with the law in force 4 or more years. The central's typical-place level is 1.0035 per 1,000 single-family homes per year.
- **Additional permits** are with-law permits minus the current-law baseline, summed over 2027–2031 for all of Wisconsin. Wisconsin has 1,839,569 single-family homes. The adopted baseline is 645 permits over 2027–2031.

## Summary

| Question | Answer |
| --- | --- |
| 1. Lower scenario | **Recommend "like the slowest statewide-law states" = the mean of Rhode Island (0.62) and Oregon (0.68): 5,502 additional permits over 2027–2031.** That is 63% of the central's 8,721. Its typical-place level is 0.65 per 1,000 single-family homes per year, against 0.53 for today's 10th-percentile lower (4,407). California's 2017 wave is not a usable low at California's own level (8,948, above the central). The Madison multiplier is about 1, so it gives no low. |
| 2. Reference line, all 8 states | The 8-state median is 0.75, 0.93, 0.87 and 1.29 per 1,000 single-family homes per year in years 1–4, from 7, 5, 5 and 4 states. **Only California has a year 5**, so year 5 repeats year 4 (flagged). Wisconsin's addition on this line is **8,811 permits** over 2027–2031: 90 permits (1%) above the central's 8,721. Over years 1–4 alone it is 6,564 against the central's 6,657, i.e. 93 below. The data put the line on top of the central, not clearly above it. |
| 3. Madison treatment | Madison's treatment affects only Madison's addition. Its baseline is unchanged unless the 2026 pace is adopted as its current-law rate. Extending the path to looser sets lowers the central by 63 to 279 permits (1–3%). The Washington and Oregon evidence does not support extending it to all mid-size cities: the cities' **pooled** rate (all permits ÷ all homes) is close to the model in years 1–2. **Recommendation: keep the path for Madison alone, and keep Madison's current-law rate at 2022–2025** until 2026 is final. |
| 4. Milwaukee | "Calculated" is the tool's label for every *estimated* rate, and that covers stated ramps. It is not a claim that Milwaukee's rate is measured. **Per the owner's direction, switch to Milwaukee's measured 2022–2025 rate (35 ÷ 405.608 = 0.0863):** the 2027–2031 baseline falls by 40.3 permits (644.9 → 604.6) and the central addition rises by 36.0 (8,720.7 → 8,756.7). The cache (through 2026-06-15) shows no clear post-reform rise: 8 candidates ÷ 88.3 thousand home-years = 0.091 (95% interval 0.039–0.179), and no detached ADU. |

## 1. Lower scenario

**How each candidate is built.**
- **(a) Bottom states.** A state's typical-place level replaces the common level. Every area's central level is multiplied by (that level ÷ 1.0035), so the model's within-state differences between places stay. The ramp is recomputed the way the engine computes it. Madison stays on its path in every candidate, as adopted.
- **(b) California's 2017 wave.** California's observed statewide rates in 2017–2019 come from [`pooled_revision_ca_inputs.csv`](../../reference/pooled_revision_ca_inputs.csv), counts with the cap and A2 rule: 4,974 ÷ 8,323,006 homes = 0.5976 in 2017, 8,719 ÷ 8,057,229 = 1.0821 in 2018, and 12,354 ÷ 8,146,808 = 1.5164 in 2019. They are converted to a typical-place level with California's own ratio: typical-place level 2.4501 ÷ statewide 2023–2025 rate 3.4561 (81,368 ADU units ÷ 23,543,548 home-years) = 0.7089. The path is applied without a ramp on top. Year 3 is held for 2030–2031.
- **(c) Multipliers.** Inputs are in [`scenario_options_multiplier_inputs.csv`](../../reference/scenario_options_multiplier_inputs.csv).

Results: [`scenario_options_lower.csv`](../../reference/scenario_options_lower.csv), by year in [`scenario_options_lower_by_year.csv`](../../reference/scenario_options_lower_by_year.csv). "Additional" is permits over 2027–2031. "% of central" is that count ÷ the central's 8,721. Levels are per 1,000 single-family homes per year.

| Candidate | Additional | % of central | Typical-place level, years 1–3 → 4+ | Statewide rate 2027 → 2031 | Lower ≤ central? | In plain words |
| --- | ---: | ---: | --- | --- | --- | --- |
| Central (adopted, for reference) | 8,721 | 100% | 0.64, 0.80, 0.83 → 1.00 | 0.77 → 1.19 | — | Like a typical statewide-law state. |
| **(a1) Mean of RI and OR** | **5,502** | **63%** | 0.40, 0.51, 0.53 → **0.65** | 0.51 → 0.79 | yes, in every area and year | Wisconsin performs like the average of the two slowest statewide-law states, Rhode Island and Oregon. |
| (a2) Mean of RI, OR and MA | 6,109 | 70% | 0.45, 0.57, 0.59 → 0.72 | 0.56 → 0.86 | yes, in every area and year | Like the average of the three slowest statewide-law states. |
| (a3) Median of RI, OR and MA (= Oregon) | 5,782 | 66% | 0.43, 0.54, 0.56 → 0.68 | 0.53 → 0.82 | yes, in every area and year | Like Oregon, the middle of the three slowest states. |
| (a4) a1 with Oregon's observed ramp | 6,309 | 72% | 0.56, 0.65, 0.65 → 0.65 | 0.67 → 0.79 | statewide yes; 7 of 9,625 area-years are above the central | Like a1, but the climb follows Oregon's 2019–2022 record, which was nearly flat from year 1. |
| (b1) California 2017–2019, at California's level | 8,948 | 103% | 0.42, 0.77, 1.08 → 1.08 (held) | 0.50 → 1.28 | **no**: above the central from year 3 | Wisconsin does what California did under its first, weaker law. |
| (b2) California 2017–2019, as a share of California's later level | 3,488 | 40% | 0.17, 0.31, 0.44 → 0.44 (held) | 0.26 → 0.54 | statewide yes; 13 area-years where the floor binds | Wisconsin reaches the share of a typical state's level that California reached of its own later level (17%, 31%, 44%). |
| (c1) Madison ÷ 7 Madison-like peers before their law | 8,703 | 100% | multiplier 0.998 | 0.77 → 1.19 | yes | Madison already runs at its peers' pre-law rate, so nothing is discounted. |
| (c2) Madison ÷ already-permissive peers (Vancouver, Tacoma) | 2,827 | 32% | multiplier 0.357 → 0.36 | 0.28 → 0.45 | yes | Madison runs at a third of the rate of peers that had liberal rules before their state law. |
| (c3) Madison ÷ the model's "own rules, no state law" rate | 1,635 | 19% | multiplier 0.057 (the floor binds almost everywhere) | 0.24 → 0.26 | statewide yes | Not usable (see below). |
| (c4) Wisconsin ÷ statewide-law states before their law | 1,787 | 20% | multiplier 0.230 → 0.23 | 0.20 → 0.32 | yes | The multiplicative case: Wisconsin keeps its low start. Before-and-after evidence contradicts it. |
| (c5) c4 damped by the 7-city elasticity | 4,150 | 48% | multiplier 0.504 → 0.50 | 0.39 → 0.62 | yes | Low starts carry over partly, as they did across 7 Madison-like cities. |
| **(d) Current lower** (10th percentile, central ÷ 1.885) | **4,407** | 51% | 0.33, 0.42, 0.43 → 0.53 | 0.41 → 0.65 | yes | Below every statewide-law state: a statistical cut, not a group of states. |

**(a) Bottom states.**
- The stage-2 levels in [`pooled_revision_stage2_levels.csv`](../../reference/pooled_revision_stage2_levels.csv) are, per 1,000 single-family homes per year at a typical place, law in force 4+ years: Rhode Island 0.6214, Oregon 0.6826, Massachusetts 0.8508. The mean of Rhode Island and Oregon is 0.6520. That is 0.6497 of the common level.
- **Rhode Island's and Massachusetts's levels are not observed at year 4.** Each state has only year 1 (2025) observed. Its year-4 level is the model's translation of that one year through the pooled ramp. Oregon is the only bottom state with years 1–4 observed.
- **Oregon's observed ramp (a4).** Oregon's rates, 32 cities excluding Portland, × 0.951, were 0.754, 0.931, 0.869 and 0.874 per 1,000 single-family homes per year in years 1–4. Divided by year 4, they are 0.86, 1.07, 0.99, 1. Made non-decreasing, that is 0.86, 1, 1, 1, 1.
  - This ramp rests on one state's 4 years, so I would not adopt it.
  - It shows the pooled ramp may be slow for Oregon, which rose fast in year 1 and then went flat.

**(b) California's first wave.**
- At California's own level (b1), the 2017 law is not a low. California's 2019 rate under the weaker law was already 1.52 statewide and 1.08 at a typical place, above the central's 1.00. California's market is the hottest of the eight states.
- As a share (b2), it is a low (3,488). But it describes a weaker, non-benchmark law. The scenario is a benchmark law, so b2 answers a different policy question.
- The 2017 counts have no parcel numbers, so the cap and A2 rule cannot be applied to 2017 (California's 2017 rate is unadjusted).

**(c) Multiplier from already-permissive places.**

The owner's suggestion, made precise: multiplier = Madison's current rate ÷ the pre-law rate of comparable places in other states before their statewide law. Wisconsin's level is then the central × that multiplier. Madison's rate is 40 units ÷ 213.168 thousand home-years = 0.1876 per 1,000 single-family homes per year.
- **Madison-like peers (c1).** Seven Madison-like cities have a before period: Spokane 0.264, Spokane Valley 0.184, Tacoma 0.542, Vancouver 0.509 and Yakima 0.081 (Washington, EY2019–2023), and Cranston 0.188 and Warwick 0.077 (Rhode Island, 2023). Their median is 0.188. **Madison runs exactly at its peers' pre-law median (multiplier 0.998).** This supports Madison's adopted path, which is those peers' observed post-law median. It gives no lower.
- **Already-permissive peers (c2).** Vancouver (liberal rules from 2017) and Tacoma (2019 reform) had permissive rules before their state law. They ran at a median of 0.526. Madison, also permissive, runs at 0.357 of that. This is the closest reading of "how Madison performs vs pre-reform permissive places". But it rests on 2 cities.
- **Model-based (c3).** The pooled model gives Madison's market 3.27 per 1,000 single-family homes per year with its own ADU rules and no statewide law (1.46 without its own rules). Madison's 0.1876 is 0.057 of that. The model's own-rules term is learned from Seattle, Portland, Austin, Denver and Minneapolis, which are large, hot markets, so this is not a fair comparison. **Not identifiable in a usable way.**
- **Statewide (c4, c5).** Wisconsin's current-law rate is 0.0715 per 1,000 single-family homes per year (homes-weighted engine rate). Washington excluding Seattle ran at 0.394 and Rhode Island at 0.229 before their laws. Wisconsin's rate is 0.230 of their median.
  - Applied fully (c4), that is the multiplicative model. Before-and-after states contradict it: Rhode Island started at 0.23 and reached a typical-place level of 0.62.
  - Damped by the elasticity across the 7 cities (c5): the slope of log post-law rate (years 1–3 mean) on log pre-law rate is 0.468. The multiplier is then 0.230^0.468 = 0.504, which gives 4,150.
  - Seven cities and two states are too few to rely on.
- **Bottom line on (c).** It is identifiable for Madison, where it is about 1, so it gives no low. For the state it rests on the multiplicative assumption, which the before-and-after evidence contradicts. Only Wisconsin's own post-law data (none yet) could identify it.

**Recommendation: (a1), the mean of Rhode Island and Oregon, 5,502 additional permits over 2027–2031** (total with the baseline: 6,147).
- It is an average of the two actual lowest performers, as the owner asked, not a statistical cut.
- Its typical-place level, 0.65 per 1,000 single-family homes per year, sits between those two states (0.62 and 0.68).
- Lower ≤ central holds in every area and every year.
- Suggested info text: "Like the slowest statewide-law states (the average of Rhode Island and Oregon)."
- Caveat for the label: Rhode Island has one observed year. Oregon alone (a3, 5,782) is the most data-backed single state.
- Effect: the lower rises from 4,407 to 5,502 (+1,095, +25%). The range then reads 5,502 / 8,721 / 16,853. The lower would no longer be symmetric with the upper (the central ÷ 1.585, against × 1.885 for the upper).

## 2. Reference line: median of all eight statewide-law states

**Method.** Each state's observed statewide rate by year since its law:
- The seven other states as in the adopted line, × 0.951 for vacant-lot ADUs.
- California with the cap and A2 rule, coded as the model codes it: the 2019 package, so 2020 = year 1.

The median runs across the states with data in each year. Wisconsin's addition = 1,839,569 homes × the rate ÷ 1,000 − the statewide baseline, as for the adopted line. Points: [`scenario_options_reference_points.csv`](../../reference/scenario_options_reference_points.csv). Line: [`scenario_options_reference_line.csv`](../../reference/scenario_options_reference_line.csv).

Rates are per 1,000 single-family homes per year; permits are Wisconsin additional permits in that year.

| Year since law (forecast year) | States with data | Their rates | 8-state median | Adopted 7-state median | Wisconsin addition, 8-state line | Wisconsin addition, adopted 7-state line | Central's addition |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 (2027) | 7 | VT 0.64, WA 0.64, MA 0.75, OR 0.75, RI 0.92, ME 0.93, CA 1.52 | 0.754 | 0.753 | 1,264 | 1,261 | 1,297 |
| 2 (2028) | 5 | WA 0.77, VT 0.79, OR 0.93, UT 1.06, CA 2.39 | 0.931 | 0.859 | 1,586 | 1,454 | 1,627 |
| 3 (2029) | 5 | VT 0.76, WA 0.80, OR 0.87, UT 0.98, CA 2.97 | 0.869 | 0.833 | 1,467 | 1,402 | 1,685 |
| 4 (2030) | 4 | OR 0.87, UT 1.18, VT 1.40, CA 3.25 | 1.293 | 1.184 (3 states) | 2,247 | 2,046 | 2,049 |
| 5 (2031) | **1 (CA 3.42)**: carried forward from year 4 | — | 1.293 (flag) | 1.184 (flag; 0 states) | 2,247 (flag) | 2,046 (flag) | 2,063 |
| **2027–2031** | | | | | **8,811** | **8,208** | **8,721** |
| 2027–2030 only (years with a median) | | | | | 6,564 | 6,162 | 6,657 |

**Reading.**
- With California in, the line rises by 603 permits (8,208 → 8,811), because California is the highest state in every year.
- California moves the median only where few states have data. In year 1, with 7 states, it changes nothing (0.753 → 0.754). In years 2–4 it shifts the middle state up.
- Against the central:
  - The 8-state line is below the central in each of years 1–3, by 34, 41 and 218 permits.
  - It is above in year 4, by 198. That year's median is the average of Utah and Vermont, from 4 states, one of them California.
  - Year 5 is a carry-forward.
- Over all five years the line is 90 permits (1%) above the central. Over the four years that have data it is 93 permits below.
- **What the data say:** with California included, the median path and the central agree within about 1% over 2027–2031. The line is not clearly above the central.
- **Display:** show the line for 2027–2030 only, or show 2031 dashed with "carried forward from 2030; only California has a fifth year".

## 3. Madison treatment

**What Madison's treatment affects.**
- The path replaces Madison's with-law rate, the same in every scenario.
- It changes only **Madison's addition**: 135 permits on the path against 326 at its pooled central level. Statewide, that moves the central by 191, the lower by 17 and the upper by 521.
- It does not change the baseline. Madison's current-law rate stays 0.1876 and its baseline 50.0 permits over 2027–2031.
- It does not change any other area.
- Because the path is the same in every scenario, it also narrows the range: Madison's own addition is 135 in the lower, the central and Strong adoption alike.

**Extending the path to similar places** ([`scenario_options_madison.csv`](../../reference/scenario_options_madison.csv)). Each place keeps its own current-law rate; only its with-law rate becomes the path. Additions are permits over 2027–2031.

| Set | Places | Single-family homes | Set's addition, pooled level → path | Statewide lower / central / upper | Change in central |
| --- | --- | ---: | --- | --- | ---: |
| Adopted: Madison only | Madison | 53,292 | 326 → 135 | 4,407 / 8,721 / 16,853 | — |
| Value $250k–$500k and 10,000+ homes | Madison, Waukesha, Wauwatosa, Brookfield, New Berlin, Menomonee Falls | 118,393 | 746 → 337 | 4,399 / 8,504 / 16,242 | −217 (−2.5%) |
| Permissive rules or measured activity: benchmark-coded places plus a measured rate at or above Madison's | Madison, Appleton, Wauwatosa, Kaukauna (0.43 measured, quality C); 7 areas | 93,315 | 494 → 240 | 4,438 / 8,658 / 16,615 | −63 (−0.7%) |
| All cities and villages with 10,000+ homes except Milwaukee | 20 places (23 areas) | 351,686 | 1,541 → 1,072 | 4,746 / 8,444 / 15,415 | −277 (−3.2%) |
| Same, including Milwaukee | 21 places (26 areas) | 453,088 | 1,811 → 1,340 | 4,906 / 8,441 / 15,106 | −279 (−3.2%) |

Extending the path lowers the central and the upper but **raises the lower**, because the path sits above the lower's level for these cities. Brookfield and New Berlin are restricted-coded and Waukesha is still ramping. Two places with permissive rules (Appleton, Wauwatosa) have no measured permits.

**Starting Madison from its 2026 pace.** Through 2026-10-23, 296 days = 43.218 thousand home-years.
- 42 units ÷ 43.218 = **0.972** per 1,000 single-family homes per year.
- 13 units without the templated programme ÷ 43.218 = **0.301**.

| Madison's current-law rate | With-law path | Madison baseline | Madison addition | Statewide baseline | Statewide central | Baseline + central |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0.1876 (adopted) | adopted path 0.452 → 1.076 | 50.0 | 134.9 | 644.9 | 8,720.7 | 9,365.6 |
| 0.972 (all 42 units) | adopted path, never below the current rate | 259.0 | 5.6 | 853.8 | 8,591.4 | 9,445.2 |
| 0.972 | path climbs from the pace: 0.972 + the peers' rise over their pre-law median 0.188 → 1.236 … 1.860 | 259.0 | 134.8 | 853.8 | 8,720.6 | 9,574.5 |
| 0.301 (13 units) | adopted path | 80.2 | 104.8 | 675.0 | 8,690.6 | 9,365.6 |
| 0.301 | path climbs from the pace → 0.565 … 1.189 | 80.2 | 134.8 | 675.0 | 8,720.6 | 9,395.7 |
| 0.1876 kept | path climbs from the 42-unit pace | 50.0 | 343.8 | 644.9 | 8,929.6 | 9,574.5 |

Starting from the 2026 pace moves mostly the **baseline** (up to +209 permits), not the addition. If the with-law path is the adopted path, the higher current-law rate eats the addition (135 → 6). The 2026 figure is provisional (10 months). Of its 42 units, 29 (69%) come from one templated programme.

**Does the evidence support extending the path to all mid-size cities?** No ([`scenario_options_midsize_check.csv`](../../reference/scenario_options_midsize_check.csv)). Rates per 1,000 single-family homes per year, years 1 to 5:

| | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Model central, Wisconsin's 20 cities and villages of 10,000+ homes outside Milwaukee (homes-weighted) | 0.74 | 0.90 | 0.93 | 1.11 | 1.11 |
| 9 Washington and Oregon Madison-like cities, **median city** (the adopted path) | 0.45 | 0.54 | 0.60 | 0.80 (4 cities) | 1.08 (4 cities) |
| Same cities, **pooled** (all permits ÷ all homes) | 0.70 (241 ÷ 346,919 homes) | 0.94 (327) | 0.61 (213) | 0.87 (113 ÷ 129,423) | 1.13 (146) |

- "About half the model" compares the median city with the model. A statewide total is a sum over places, and the statistic that matches a sum is the pooled rate.
- The pooled rate is within 6% of the model in years 1–2. It falls to 0.61 in year 3, after Tacoma's 2019-reform surge ended (109, 149, then 55 permits).
- Six of the 9 cities made their own reforms in the window, and Washington's law was not yet binding for most of them.
- So the evidence says the median mid-size city lags. It does not show that mid-size cities as a group fall short of the model.

**Recommendation.**
- Keep the path for **Madison alone**. It is pre-registered, Madison sits exactly at its peers' pre-law median (section 1(c1)), and only Madison meets the definition.
- Do not extend it. The looser sets move the central by only 1–3%, and the pooled evidence does not support the cut.
- Keep Madison's current-law rate at the 2022–2025 rate until 2026 is final. Then rerun the baseline sensitivity: +209 permits with all 42 units, +30 with the 13 non-templated units.
- Optionally, note in the tool that the path is a median city (conservative for Madison).

## 4. Milwaukee

**Why it says "Calculated".**
- The tool has three status pills. Rates with status *estimated* are shown as "Calculated" (`ui/src/format.ts`; bundle text: "a rules-group rate or a stated ramp, not the place's own permit records").
- Milwaukee's rate has status *estimated*, with the basis "assumed ramp from Milwaukee's observed pre-reform candidate rate to a Madison-like level". It is coded `restricted` (owner occupancy at application only). Its rate is set to Madison's 0.1876 by mid-2029, because its August 2025 rules are otherwise Madison-like.
- So the number is an assumption shown under the pill for computed rates. That is why it reads as more certain than it is.

**What it affects, and by how much** ([`scenario_options_milwaukee.csv`](../../reference/scenario_options_milwaukee.csv)). Milwaukee has 101,402 single-family homes (5.5% of 1,839,569). Values are permits over 2027–2031 unless a rate is named.

| Milwaukee current-law rate | Rate by year 2027–2031 | Milwaukee baseline | Statewide baseline | Milwaukee addition, lower / central / upper | Statewide central |
| --- | --- | ---: | ---: | --- | ---: |
| Adopted: assumed ramp to 0.1876 | 0.117, 0.151, 0.185, 0.188, 0.188 | 84.0 | 644.9 | 107.7 / 270.2 / 577.1 | 8,720.7 |
| **Measured 2022–2025: 35 ÷ 405.608 thousand home-years = 0.0863, flat (owner's preference)** | 0.086 each year | **43.8** | **604.6 (−40.3)** | 143.5 / **306.2 (+36.0)** / 613.2 | **8,756.7 (+36.0)** |
| Measured since the reform: 8 ÷ 88.3 = 0.0906, flat | 0.091 | 45.9 | 606.8 (−38.1) | 141.6 / 304.4 / 611.4 | 8,754.9 (+34.2) |
| Restricted-group rate 0.0607, flat | 0.061 | 30.8 | 591.7 (−53.2) | 154.4 / 317.3 / 624.3 | 8,767.8 (+47.1) |

- Under the measured rate, the statewide lower becomes 4,443.1 (+35.7) and the upper 16,888.6 (+36.1).
- The addition rises by less than the baseline falls (+36.0 against −40.3) because the addition is ramped in its first three years and the baseline is not.
- Milwaukee's central with-law level (0.796) is unchanged. Baseline + central moves from 9,365.6 to 9,361.3 (−4.3).

**Coverage table** (single-family homes; baseline and central additional permits over 2027–2031; [`scenario_options_milwaukee.csv`](../../reference/scenario_options_milwaukee.csv)):

| Status | As now | Milwaukee measured (status "observed", quality C) | Ramp kept, relabelled "assumed" |
| --- | --- | --- | --- |
| Observed | 59,624 homes; 51.2 baseline; 176.2 added | 161,026 homes; 95.0; 482.4 | 59,624; 51.2; 176.2 |
| Calculated (estimated) | 512,512; 209.1; 2,117.0 | 411,110; 125.1; 1,846.8 | 411,110; 125.1; 1,846.8 |
| Assumed | 1,267,433; 384.5; 6,427.5 | 1,267,433; 384.5; 6,427.5 | 1,368,835; 468.5; 6,697.7 |

**What the data say.**
- **Measured rate.** Milwaukee's 2022–2025 rate is 35 candidate permits ÷ 405.608 thousand home-years (101,402 homes × 4 years) = 0.0863 per 1,000 single-family homes per year (95% interval 0.060–0.120). These are unverified candidates from open data: no description, no unit count, quality C. The window includes the first 5 months after the reform.
- **Post-reform permits in the cache.** The permit file (`data/raw/milwaukee_permits/buildingpermits.csv`, downloaded 2026-10-24) ends at **2026-06-15**. Since 2025-08-02 it holds:
  - 8 central-rule candidates (conversions or attached units on one-unit homes);
  - 11 under the upper rule;
  - no detached-garage ADU.

  8 ÷ 88.3 thousand home-years = 0.091 (95% interval 0.039–0.179). Before the reform (2017-01 to 2025-08-01) it was 46 ÷ 870.4 = 0.053 (0.039–0.070). The post-reform interval overlaps both the pre-reform rate and the 2022–2025 rate. **There is no clear post-reform rise**, and the cache has nothing after 2026-06-15.
- **Recommendation (the owner's stated preference, which the data support):** set Milwaukee's current-law rate to the measured 0.0863 with status observed (quality C). Keep the ramp to Madison's level as a baseline sensitivity (+40.3 baseline, −36.0 central). Revisit when permits after 2026-06-15 are published.
- Changing this is a conductor's step: `scripts/build_wi_baseline.py`, then the engine. It is not done here.

## Reproduce

```
uv run python scripts/run_scenario_options.py
```

Inputs, all local and already used by the adopted runs: the engine inputs, `reference/pooled_revision_wi_y_by_area.csv`, `pooled_revision_wi.csv`, `pooled_revision_ca_inputs.csv`, `madison_like_cities.csv`, `madison_like_median_path.csv`, `pooled_revision_madison_like_wi.csv`, and the pooled data that `run_pooled_regression.load()` reads. The pooled model is refitted once, as in `run_pooled_revision.py`.

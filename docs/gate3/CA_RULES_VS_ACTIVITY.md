# Do pre-2020 local ADU rules predict ADU activity? A California test

Prepared 2026-10-24 for the owner's idea: test whether coded local ADU rules predict ADU activity in California, where many places have measured permits. If they did, rule codings could assign activity groups to Wisconsin places with no permit data. Code is in `missing_middleware/comparison/ca_ordinances.py`; run it with `uv run python scripts/build_ca_ordinances.py`. Tests are in `tests/test_ca_ordinances.py`.

**All results are associations across California places. They are not causal effects of rules.** The pre-registered study ([CA_COMPARISON_PLAN.md](CA_COMPARISON_PLAN.md)) and its holdout test are not touched or recomputed. This analysis only reads their published groups and rates.

## Plain summary

- **Short answer: no.** On their own, coded 2019 rules are a weak predictor of activity. They should not be used to assign activity groups to unmeasured Wisconsin places. Home value is a much stronger predictor, and adding rules to home value and income does not improve classification.
- **What exists already.** Three pre-2020 coded datasets are public and were used:
  - **Terner Center land use survey (2017–18):** 271 jurisdictions, of which 249 are study places. It covers ordinance status, minimum lot size, maximum size, parking and fees.
  - **CCI ADU Scorecard (ordinances received by HCD through September 2019):** letter grades for 204 jurisdictions, 195 of them study places. Only the overall grade is public.
  - **HCD's list of local ADU ordinances received (as of 1 May 2019):** covers all 539 jurisdictions.
  - **Gap:** none of the three codes owner occupancy or discretionary review per place.
- **Our own coding.** We coded the full AQ-026 scheme for **60 of a planned 73** non-holdout places, from dated 2017–2019 ordinance text. The other 13 could not be accessed. Most sources are dated city documents rather than Wayback snapshots (see Deviations).
- **What the rules do show** (2017–2019 is before the 2020 state laws; 2023–2025 is the plateau after them):
  - **Before the 2020 laws, more restrictions went with less activity.** This is a modest association.
    - Each extra binding flag in the Terner survey goes with a 2017–2019 ADU rate **0.78 times as high** [0.64–0.97], holding home value and income equal. The rate is permits per 1,000 one-unit detached homes per year; the fit covers 197 places with 9,525 permits over 11.8 million home-years, excluding Los Angeles.
    - In our hand coding, owner occupancy and extra parking went with fewer active places. Owner-occupancy places were active in 10 of 36; places without it, in 10 of 16. Once home value and income are held equal, most of this disappears.
  - **After the 2020 state laws, the 2019 restriction counts no longer track the plateau rate.**
    - Terner flag count, rate ratio for 2023–2025 per extra flag: **1.04** [0.88–1.21].
    - Hand-coded tier-1 count, same ratio: **1.32** [0.84–2.17].
    - This is consistent with the statewide law overriding most local restrictions.
  - **Discretionary review is the one hand-coded feature still linked to lower post-law activity.** 10 of the 54 places where this flag is known required it. Holding home value and income equal, their 2023–2025 rate was **0.47 times as high** [0.18–0.97]. It is based on 10 places, so it is a lead, not a finding.
  - **Having filed an ordinance with HCD goes with more activity, but adds little beyond home value.**
    - Holding value and income equal, the 2017–2019 rate was **1.46 times as high** [1.11–1.90] and the 2023–2025 rate **1.34 times** [1.04–1.73] (366 places, excluding Los Angeles).
    - The direction is ambiguous: places with demand may simply have updated their ordinances first.
- **As classifiers** (cross-validated AUC: 0.5 is a coin flip, 1.0 is perfect), across 367 non-holdout places, 89 of them active:
  - **Home value + income:** separates active places from the rest with AUC **0.81**.
  - **Ordinance-filed indicators alone:** **0.63**.
  - **Both together:** **0.81**, no gain over value and income alone.
  - **Hand-coded sample** (60 places, 21 active): value + income **0.82**, tier-1 and tier-2 counts **0.56**, both **0.81**.
- **For Wisconsin:**
  - Keep grouping unmeasured places by the rule already in use, not by coded rules.
  - Treat rule codings as explanation and as a check, not as a group-assignment input. This is consistent with AQ-028: flags explain results and are not multipliers.
  - If one feature is worth coding for Wisconsin's unmeasured places, it is **discretionary review** (conditional-use or plan-commission approval), then **owner occupancy**. Wisconsin already codes both.

## 1. Existing coded datasets (step 1)

Coverage counts refer to the 457 study jurisdictions with complete market data (`reference/ca_regression_ca_jurisdictions.csv`); 90 of them are holdout places. The inventory is in `reference/ca_rules_vs_activity_sources.csv`.

| Source | Date of coding | Coverage | Variables | Maps to AQ-026 |
| --- | --- | --- | --- | --- |
| **Terner California Residential Land Use Survey** (Mawhorter and Reid 2018). Public CSV, [ternercenter.berkeley.edu](https://ternercenter.berkeley.edu/california-land-use-survey-data/) | Planner self-reports, Aug 2017 – Oct 2018 | 271 jurisdictions; 249 study places (198 non-holdout, 51 holdout) | Local ADU ordinance adopted / in process / none; ADU minimum lot size; maximum unit size; off-street parking spaces; total fees for a typical ADU; how often ADU applications arrive | Status; `lot_minimum` (> 0 sq ft); `size_below_benchmark` (< 600 sq ft); `extra_parking` (> 0 spaces); `fees` (≥ $10,000, a cost proxy that includes building-permit fees). No owner occupancy, discretionary review, form, siting or district |
| **CCI ADU Scorecard, interim report** (Chapple et al., 1 Feb 2020), Appendix C. [urbandisplacement.org PDF](https://www.urbandisplacement.org/wp-content/uploads/2021/09/ADU-Scorecard-InterimReport-200201-1.pdf) | Ordinances received by HCD by 6 Sep 2019, so pre-2020 rules | 204 graded; 195 study places (160 non-holdout, 35 holdout) | One letter grade (A to F) built from 16 criteria: lot size, coverage/FAR, ADU parking, replacement parking, setbacks, sizes, height, zones, review time, added review layers, fees, JADU, owner occupancy, clarity; plus 2018 permits, ordinance year and link | Composite only. Per-criterion scores are available only by email request ("old scorecard grades"), which is outside our rules |
| **HCD "ADU ordinances received by HCD"** (`jurisdiction-ordinances.xlsx`), [Wayback capture 2019-08-31](https://web.archive.org/web/20190831103132/http://www.hcd.ca.gov/policy-research/docs/ordinances/jurisdiction-ordinances.xlsx) | List current as of 1 May 2019 | 539 jurisdictions; 191 study places had filed (157 non-holdout, 34 holdout) | Received / not received; link and date of each filed ordinance | First-pass proxy. "Not received" does **not** mean no ADUs: the state default standards applied |
| CCI 2021 grades ([aducalifornia.org/grades](https://www.aducalifornia.org/grades/)) | Ordinances received Dec 2019 – Feb 2021 | 119 ordinances | Grade per jurisdiction | Post-2020 rules; **not used** |
| Casita Coalition / "ordinance report card" and similar | Post-2020 | — | — | Post-2020; not used |
| HCD ordinance PDFs and review letters | 2017–2019 | ~200 PDFs | Full text | `hcd.ca.gov` returns HTTP 403 to scripts, and only 2 of the PDFs are archived on Wayback; **not usable** |
| Academic replications: Pfeiffer (2019, Terner), Wielga (2023), Cityscape 25(2) (2023) | — | — | All use the Terner survey above | No separate coded file found |

The scorecard PDF host refuses scripted requests (HTTP 403). Its text was read through the Exa fetch service on 2026-10-24 and is stored under `data/raw/ca_adu_scorecard_2020/`. Downloaded bytes and SHA-256 hashes are in `data/raw/ca_ordinances_2019_handcoding/_sources_manifest.json`.

**Coverage is thin on the features that matter most.** Owner occupancy and discretionary review are the tier-1 features Wisconsin codes. They are only inside the CCI composite grade, so step 2 was needed.

## 2. Hand coding from 2017–2019 ordinance text (step 2)

**Sample.** We drew 73 non-holdout places from 9 strata: the 2017–2019 activity group (active / middle / restrictive) crossed with the home-value tercile (cut points $572,700 and $874,900, from non-holdout places). The seed was fixed at 20261024 (`co.draw_hand_sample`; the build checks that the coded file matches the draw).

- **Why stratify this way.** Active places are mostly expensive and restrictive places mostly cheap: 56 of 89 active places are in the top value tercile and 57 of 70 restrictive places in the bottom tercile. So the draw over-weights the overlap: cheap active, expensive restrictive, and the middle tercile. This gives the best chance of seeing rules apart from home value.
- **Consequence.** Shares in the hand sample are **not** representative of California.

**Coding.** Coders worked blind to each place's permits and group. They followed a written protocol applying the AQ-026 scheme as written: benchmark = detached or attached, at least 600 sq ft, by right, no extra parking, no occupancy rule. Each row records:

- the source URL and its date;
- the date of the ordinance version coded;
- quoted evidence for every true flag and for the approval pathway;
- a confidence level.

The coded file is `reference/ca_ordinances_2019.csv`; the source downloads are in `data/raw/ca_ordinances_2019_handcoding/`.

**Result: 60 coded and 13 could not be accessed.**

- **Who could not be accessed.** Of the 13: 2 active, 5 middle and 6 restrictive places. Coding failed more often for restrictive places, which is a possible bias.
- **Confidence:** 17 high, 34 medium, 9 low.
- **Sources:**
  - 8 Wayback code pages;
  - 5 Wayback city documents;
  - 47 dated ordinance documents fetched from their current hosts: adopted ordinances, staff reports with the adopted text, and dated city handouts.
- **Status:** 57 mention and allow ADUs, 2 rely on the state default (Los Angeles County, Millbrae), 1 prohibits (La Habra Heights).
- **Rights class:** 58 restricted, 1 at benchmark (Fort Bragg, inland code), 1 prohibited.

**Flag prevalence among the 60 coded places** (true / false / unknown):

| Flag | Tier | True | False | Unknown |
| --- | --- | --- | --- | --- |
| Owner occupancy | 1 | 36 | 16 | 8 |
| Related occupant | 1 | 0 | 55 | 5 |
| Extra parking | 1 | 54 | 3 | 3 |
| Discretionary review | 1 | 10 | 44 | 6 |
| Form limited | 1 | 1 | 56 | 3 |
| Size below benchmark | 2 | 43 | 13 | 4 |
| Siting | 2 | 4 | 41 | 15 |
| Lot minimum | 2 | 12 | 40 | 8 |
| District limited | 2 | 18 | 32 | 10 |
| Fees | 2 | 21 | 0 | 39 |

**What the coding shows.** Almost every pre-2020 California ordinance required extra parking (54 of 57 places where it is known). Most capped attached units at 50% of the house, which flags size below the benchmark (43 of 56 known). So those two flags hardly vary and cannot discriminate between places. Fees were never found to be absent, so the fees flag is uninformative. The flags that vary are owner occupancy, discretionary review, lot minimum and district limits.

## 3. Do 2019 rules predict activity? (step 3)

**Outcomes:**

- (a) The 2017–2019 activity group, and the 2017–2019 rate: ADU permits per 1,000 one-unit detached homes per year (ACS 2020–2024 homes, three complete years).
- (b) The 2023–2025 plateau rate, in the same units: permits over the observed years.

Both come from the study's main measure as published in `reference/ca_regression_ca_jurisdictions.csv`.

**Pooled rates** are homes-weighted: total permits ÷ (homes × years) × 1,000. Medians are across places, unweighted. Main results use the **367 non-holdout places**. Versions that include the 90 holdout places (flagged `holdout` in every table) are in the CSVs and agree closely: for example, HCD filing vs the 2017–2019 rate gives ρ = 0.33 for non-holdout places and 0.34 for all places.

### 3a. Cross-tabs (non-holdout places)

**HCD had received a post-2017 local ordinance by May 2019:**

| Filed? | Places | Active | Middle | Restrictive | 2017–19 median rate | 2023–25 median rate |
| --- | --- | --- | --- | --- | --- | --- |
| Yes | 157 | 54 (34%) | 93 | 10 (6%) | 0.64 | 3.03 |
| No | 210 | 35 (17%) | 115 | 60 (29%) | 0.20 | 1.37 |

Within home-value terciles, the gap mostly closes:

- **Cheapest third:** restrictive places are 4 of 19 filers and 53 of 104 non-filers. Median 2023–25 rate: 1.28 for filers vs 0.66 for non-filers.
- **Middle third:** 5 of 67 vs 4 of 55; median 3.09 vs 2.36.
- **Top third:** 1 of 71 vs 3 of 51; median 3.51 vs 2.69.

(`ca_rules_vs_activity_within_value.csv`)

**Hand-coded tier-1 flags** (owner occupancy, related occupant, extra parking, discretionary review, form; known true), 60 places. This sample is stratified, so its shares are not statewide:

| Tier-1 flags | Places | Active | Middle | Restrictive | 2017–19 median | 2023–25 median |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 4 | 3 | 0 | 1 | 1.43 | 2.68 |
| 1 | 17 | 7 | 8 | 2 | 0.71 | 1.96 |
| 2 | 34 | 10 | 11 | 13 | 0.16 | 1.32 |
| 3 | 5 | 1 | 1 | 3 | 0.00 | 1.58 |

**Tier-2 flags** show no gradient: the median 2023–25 rate is 1.55, 1.65, 1.58 and 0.99 for 0, 1, 2 and 3 flags.

**Individual hand-coded flags:**

| Flag | Value | Places | Active | Restrictive | 2017–19 pooled (permits / home-years) | 2023–25 pooled (permits / home-years) |
| --- | --- | --- | --- | --- | --- | --- |
| Owner occupancy | true | 36 | 10 | 14 | 0.45 (598 / 1.32 m) | 3.41 (4,340 / 1.27 m) |
| Owner occupancy | false | 16 | 10 | 3 | 1.10 (1,183 / 1.08 m) | 4.00 (4,273 / 1.07 m) |
| Discretionary review | true | 10 | 2 | 5 | 0.42 (108 / 0.26 m) | 1.82 (445 / 0.24 m) |
| Discretionary review | false | 44 | 19 | 10 | 0.78 (1,781 / 2.27 m) | 3.92 (8,748 / 2.23 m) |
| Extra parking | true | 54 | 18 | 18 | 0.69 | 3.55 |
| Extra parking | false | 3 | 3 | 0 | 1.58 | 2.96 |

Rates are permits per 1,000 one-unit detached homes per year. "m" = million home-years.

**Terner survey flag count** (lot minimum, size, parking and fees; known true), 198 places:

| Flags | Places | Active | Restrictive | 2017–19 median | 2023–25 median |
| --- | --- | --- | --- | --- | --- |
| 0 | 39 | 18 | 4 | 0.76 | 2.32 |
| 1 | 69 | 28 | 11 | 0.61 | 3.03 |
| 2 | 74 | 18 | 10 | 0.34 | 2.66 |
| 3 | 16 | 1 | 2 | 0.17 | 1.62 |

**CCI grade**, 160 graded places:

| Grade | Places | Active | 2017–19 median | 2023–25 median |
| --- | --- | --- | --- | --- |
| B+ or A | 16 | 12 | 2.34 | 3.06 |
| B− / B | 37 | 19 | 1.07 | 3.29 |
| C / C+ | 68 | 13 | 0.45 | 2.54 |
| C− or lower | 39 | 12 | 0.41 | 3.51 |

The grade tracks 2017–19 activity but not the post-law plateau.

**Home-value tercile**, the competing explanation, 367 places:

| Value tercile | Places | Active | Restrictive | 2017–19 median | 2023–25 median |
| --- | --- | --- | --- | --- | --- |
| Low | 123 | 7 | 57 | 0.02 | 0.81 |
| Mid | 122 | 26 | 9 | 0.37 | 2.83 |
| High | 122 | 56 | 4 | 0.89 | 3.28 |

### 3b. Rank correlations (Spearman ρ, 95% bootstrap interval, non-holdout places)

| Predictor | Places | vs 2017–19 rate | vs 2023–25 rate | vs active (1/0) | Log home value on the same places, vs 2017–19 / 2023–25 |
| --- | --- | --- | --- | --- | --- |
| HCD filing (1/0) | 367 | 0.33 [0.25, 0.41] | 0.33 [0.23, 0.41] | 0.21 | 0.62 / 0.55 |
| CCI graded (1/0) | 367 | 0.35 [0.26, 0.42] | 0.35 [0.25, 0.43] | 0.22 | 0.62 / 0.55 |
| CCI grade points | 160 | 0.29 [0.15, 0.46] | 0.01 [−0.13, 0.20] | 0.26 | 0.48 / 0.33 |
| Terner: ordinance adopted / in process / none | 198 | 0.06 [−0.09, 0.20] | 0.01 [−0.14, 0.14] | 0.00 | 0.59 / 0.48 |
| Terner flag count | 198 | −0.24 [−0.34, −0.14] | −0.04 [−0.13, 0.08] | −0.24 | 0.59 / 0.48 |
| Hand tier-1 count | 60 | −0.27 [−0.53, −0.01] | −0.14 [−0.32, 0.10] | −0.23 | 0.40 / 0.33 |
| Hand tier-2 count | 60 | −0.05 [−0.22, 0.24] | 0.02 [−0.18, 0.29] | −0.09 | 0.40 / 0.33 |
| Hand owner occupancy | 52 | −0.31 [−0.60, −0.05] | −0.16 [−0.45, 0.05] | −0.33 | 0.40 / 0.33 |
| Hand extra parking | 57 | −0.27 [−0.41, −0.07] | −0.13 [−0.27, −0.03] | −0.31 | 0.40 / 0.33 |
| Hand discretionary review | 54 | −0.18 [−0.41, 0.14] | −0.22 [−0.47, 0.00] | −0.19 | 0.40 / 0.33 |
| Log median household income | 367 | 0.42 | 0.34 | 0.28 | — |

In every universe, home value correlates with activity more strongly than any rule variable does. In the hand sample, home value's correlation is weaker (0.40 / 0.33) because the draw was designed to break the link between value and activity group.

### 3c. Small models

Poisson models of permit counts, with log(homes × years ÷ 1,000) as the exposure offset and log home value and log income as controls. The intervals are a jurisdiction bootstrap with 1,000 draws, because the counts are over-dispersed. Los Angeles is 11,213 of the 23,417 non-holdout 2017–19 permits and dominates homes-weighted fits, so the statewide-source rows are shown without it; the full-sample rows are in the CSV.

| Predictor (places; permits 2017–19 / 2023–25) | Rate ratio, 2017–19 | Rate ratio, 2023–25 |
| --- | --- | --- |
| HCD filing, 1 vs 0 (366, excl. LA; 12,204 / 55,908) | 1.46 [1.11, 1.90] | 1.34 [1.04, 1.73] |
| CCI graded, 1 vs 0 (366, excl. LA) | 1.44 [1.10, 1.88] | 1.32 [1.01, 1.70] |
| Terner flag count, per flag (197, excl. LA; 9,525 / 42,281) | 0.78 [0.64, 0.97] | 1.04 [0.88, 1.21] |
| Terner extra parking, 1 vs 0 (164, excl. LA) | 0.61 [0.43, 1.09] | 1.31 [0.87, 1.90] |
| Hand tier-1 count, per flag (60; 1,920 / 9,492) | 0.90 [0.56, 1.45] | 1.32 [0.84, 2.17] |
| Hand all flags, per flag (60) | 1.00 [0.79, 1.29] | 1.14 [0.93, 1.42] |
| Hand owner occupancy, 1 vs 0 (52; 1,781 / 8,613) | 1.05 [0.40, 2.24] | 2.03 [0.86, 6.33] |
| Hand discretionary review, 1 vs 0 (54; 1,889 / 9,193) | 0.49 [0.19, 1.17] | 0.47 [0.18, 0.97] |

**Explained deviance.** This is the share of deviance explained compared with a common-rate model. For the HCD filing model excluding LA, value and income alone explain 0.44 (2017–19) and 0.35 (2023–25). Adding the rule variable raises these to 0.46 and 0.37. Across the controlled rows, rules add 0–9 percentage points. The largest gain, 9 points, is owner occupancy for 2023–25, where the rate ratio of 2.03 points the opposite way from a restriction effect (`ca_rules_vs_activity_models.csv`).

### 3d. Could rules assign activity groups?

Logistic models compared by area under the ROC curve (AUC). Each comparison uses the same places for all three models. AUC is computed within held-out folds, averaged over 5 stratified folds × 20 repeats. Non-holdout places only (`ca_rules_vs_activity_classification.csv`).

| Target | Places (target / all) | Rule set | Value + income | Rules only | Rules + value + income |
| --- | --- | --- | --- | --- | --- |
| Active | 89 / 367 | HCD filing + CCI graded | 0.81 | 0.63 | 0.81 |
| Active | 65 / 198 | Terner status + flag count | 0.81 | 0.63 | 0.81 |
| Active | 21 / 60 | Hand tier-1 + tier-2 counts | 0.82 | 0.56 | 0.81 |
| Active | 20 / 45 | Hand owner occupancy + parking + discretionary | 0.83 | 0.65 | 0.84 |
| Restrictive | 70 / 367 | HCD filing + CCI graded | 0.87 | 0.68 | 0.87 |
| Restrictive | 27 / 198 | Terner status + flag count | 0.90 | 0.54 | 0.89 |
| Restrictive | 19 / 60 | Hand tier-1 + tier-2 counts | 0.81 | 0.63 | 0.80 |
| Restrictive | 14 / 45 | Hand owner occupancy + parking + discretionary | 0.81 | 0.65 | 0.81 |

## 4. Recommendation for Wisconsin (step 4)

1. **Do not assign activity groups to unmeasured Wisconsin places from rule codings.**
   - In California, rules alone sort places only modestly better than chance (AUC 0.56–0.68).
   - Value and income sort them much better (0.81–0.90), and adding rules does not help (AUC changes of −0.02 to +0.01).
   - Wisconsin's rule v1 / v1.1 grouping (unmeasured = restrictive) and the market-adjusted regression already carry the home-value signal. California suggests that signal is the main one.
2. **Rule features that matter most, in order:**
   - **(i) Discretionary review**, the one feature still linked to lower activity after the 2020 law, at about 0.5× (rate ratio 0.47 [0.18, 0.97]).
   - **(ii) Owner occupancy**, linked to fewer active places before 2020 but not after once market is held equal.
   - **(iii) Whether a local ordinance exists or was updated**, about 1.3–1.5×, but probably partly a result of demand rather than a cause of it.
   - Extra parking, size caps and fees could not be tested well, because nearly every pre-2020 California ordinance had them.
   - Tier-2 counts showed no association.
3. **Use codings for explanation and checks.** For example, flag Wisconsin places with discretionary approval (7 of the 37 coded places) as a downside sensitivity, consistent with AQ-028. AQ-027's direction that unknown rules behave like restricted is neither supported nor contradicted here.
4. **Transfer caution.**
   - California's pre-2020 local rules sat under a state floor from 2017: ministerial approval for compliant units, parking caps, and void non-compliant ordinances. So the "restrictive rules" here are milder than Wisconsin's prohibitions.
   - The test cannot say whether a Wisconsin-style outright ban predicts zero activity. Only 1 coded California place prohibited ADUs: La Habra Heights, 0 permits in 2017–19 and 0.84 per 1,000 homes a year in 2023–25.

## Deviations and limits

- **Sources (deviation from step 2).** The request was for Wayback snapshots of municipal code pages captured in 2018–2019. Only 13 of the 60 codings are from Wayback captures (8 code pages, 5 city documents). The other 47 are dated 2016–2019 ordinance documents fetched from current city or agenda-portal hosts.
  - **Why:** municode and qcode section pages were mostly never archived (they are JavaScript shells), HCD's ordinance PDFs return 403 and are not archived, and the Wayback CDX API was down or rate-limited for much of the session.
  - **What each row records:** the document's own date, and the snapshot date where there is one.
  - **Weaker sources:** a few rows use a later document that reprints or redlines the pre-2020 text (Lincoln, Beaumont, Sonora, El Centro, Madera County, Temecula), or a summary (housing elements for Livingston, Modesto, Plymouth and Laguna Niguel). These are marked medium or low confidence.
- **Version rule.** Coders were told to code the version in force on 2018-07-01. Three places used the version that governed most of 2018–2019 instead, because the earlier text could not be found or was an urgency moratorium (Eastvale, Guadalupe, Chowchilla). Half Moon Bay and Orland followed the rule even though a replacement governed most of 2019. Each case is noted in `coder_notes`.
- **Pre-2017 ordinances coded as written.** Several ordinances arguably became void on 2017-01-01 under SB 1069 / AB 2299, so state standards may have applied in practice: Amador County, Monterey County, Ceres, Lincoln, El Cajon, Santa Paula, Sonora, Marina, Ferndale, and the La Habra Heights ban. They are coded as written, per the protocol. This adds noise that would weaken any link between rules and activity.
- **Unknown flags** count as not-true in the flag counts, as in Wisconsin, and `n_unknown` is reported per place. Places that could not be coded skew restrictive (6 of 13).
- **Fees.** The Terner fee flag (≥ $10,000 total) includes building-permit fees, so it is a cost proxy, not the AQ-026 ADU-specific fee flag.
- **Reverse causation.** Ordinance filing and CCI grades may follow demand, so their associations are not rule effects.
- **Los Angeles** dominates homes-weighted results and was the documented early adopter. The statewide-source models are shown without it.
- **Holdout places** appear only in rows marked `all_incl_holdout` and in the jurisdiction table (column `holdout`). The hand sample has none.

## Files

- `reference/ca_ordinances_2019.csv`: hand coding. 73 rows, 60 coded. Each row has its source URL, snapshot date, quoted evidence and confidence.
- `reference/ca_rules_vs_activity_jurisdictions.csv`: one row per study jurisdiction (457), with every source attached and the holdout flag.
- `reference/ca_rules_vs_activity_sources.csv`: inventory of the existing datasets.
- `reference/ca_rules_vs_activity_crosstabs.csv`: predictor level × activity group, pooled and median rates, with permits and home-years.
- `reference/ca_rules_vs_activity_within_value.csv`: the same cross-tabs within home-value terciles.
- `reference/ca_rules_vs_activity_correlations.csv`: Spearman ρ with bootstrap intervals.
- `reference/ca_rules_vs_activity_models.csv`: Poisson rate ratios, with and without value and income controls.
- `reference/ca_rules_vs_activity_classification.csv`: AUC comparisons.
- Raw sources (git-ignored): `data/raw/terner_tcrlus_2018/`, `data/raw/wayback_ca_adu/`, `data/raw/ca_adu_scorecard_2020/`, and `data/raw/ca_ordinances_2019_handcoding/` (per-batch downloads, the coding protocol and the sources manifest).

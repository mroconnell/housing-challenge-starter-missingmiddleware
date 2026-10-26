# Wisconsin Current-Law Rate and Baseline

> **Update 2026-10-26 (AQ-043):** Milwaukee now uses its measured 2022–2025 rate (0.0863 permits per 1,000 single-family homes per year, observed), and the ramp in section 4 is a baseline-only sensitivity. The statewide baseline is **604.6** permits over 2027–2031 (was 644.9). Other figures below that include Milwaukee's ramp (the ~650 total, Milwaukee's 12.5% share, the top-20 table) are the 2026-10-24 values; current values are in `reference/wi_baseline_statewide.csv` and `reference/wi_baseline_top20.csv`.

Gate 3, work package B. Built 2026-10-24. Code: `missing_middleware/model/baseline.py`, `scripts/build_wi_baseline.py`; tests: `tests/test_wi_baseline.py`. Model: [SCOPE_AND_MODEL.md](../gate1/SCOPE_AND_MODEL.md) revision 3, `B[a,t] = H[a] × x[a] × g[a,t] / 1000`. Decisions used: AQ-023, AQ-027, AQ-028, AQ-029, AQ-032, AQ-033 in the [assumptions log](../ASSUMPTIONS_AND_QUESTIONS.md).

## Summary

- **What x is.** x counts second homes added on single-family lots (AQ-032) per 1,000 one-unit detached homes per year, under each place's current local rules.
- **Observed today:**
  - **Madison**, at benchmark: 39 second homes in 2022–2025, so **x = 0.18** (95% interval 0.13–0.25). The ADU-type part alone is 0.16.
  - **Pleasant Prairie**, where ADUs are banned: **0.04** (0.01–0.12).
  - **Sun Prairie**, while ADUs were banned: **0.02** (0.003–0.09).
  - These counts are small, so the intervals are wide.
- **Everywhere else, x is estimated from the place's rules group.** The group values are below. Uncoded places (69% of homes) behave like `restricted` (AQ-027).

  | Group | x low | x central | x high | Basis |
  | --- | --- | --- | --- | --- |
  | prohibited | 0.010 | **0.031** | 0.073 | Observed, Pleasant Prairie and Sun Prairie pooled |
  | restricted | 0.031 | **0.062** | 0.131 | Observed, Madison 2014–2023 and Fitchburg pooled |
  | benchmark | 0.062 | **0.183** | 0.250 | Observed in Madison 2022–2025 |
  | undetermined (uncoded) | 0.031 | **0.062** | 0.131 | Assumed to behave like restricted |

- **Milwaukee** has allowed ADUs by right since 2025-08-02. **Since 2026-10-26 (AQ-043) its current-law rate is its measured 2022–2025 rate, held flat:** 35 candidate second-home permits ÷ 405.608 thousand home-years (101,402 single-family homes × 4 years) = **0.0863** permits per 1,000 single-family homes per year (95% interval 0.060–0.120), status *observed*, quality C (unverified open-data candidates). Its baseline is 43.8 permits over 2027–2031 (was 84.0 with the ramp).
  - Its open permit data shows 8 candidate second homes in the first 10.5 months after the reform, so x = 0.09 (0.04–0.18): no clear rise yet. Before the reform it was 0.05 (0.04–0.07).
  - No detached ADU shows up yet.
  - The Gate 3 assumed ramp to Madison's level (0.18 by mid-2029, central) is now a baseline-only sensitivity case: statewide baseline 644.9 instead of 604.6 permits over 2027–2031 (+40.2), central addition −36.0 (`reference/adu_model_sensitivities.csv`, `reference/adu_model_baseline_only_effects.csv`). Section 4 keeps the ramp's derivation.
- **Statewide baseline, 2027–2031: about 650 second homes on single-family lots (low 310, high 1,280).** The rate is about 125–133 a year, or 0.07 per 1,000 homes a year. 2026 is a bridge year: about 120 homes (60–250).
- **Where the baseline comes from.**
  - The 20 largest contributors make up 35% of the total.
  - Milwaukee alone is 12.5% and Madison 7.4%.
  - Uncoded places make up 60% of the baseline, because they hold most of the homes.
- **The assumption that matters most.** Treating uncoded places like prohibited instead of restricted would cut the baseline by 200 homes (to 457).
- **Against the owner's prior** (AQ-031, a comparison only):
  - Prohibited places come in well under 0.1, as the owner expected.
  - Madison's benchmark rate of 0.18 is about a tenth of the "somewhat above 2" the owner expected.

All values are labeled observed, estimated, or assumed. Ranges are scenario paths, not statistical intervals (AQ-012). The exception is the Poisson intervals on observed counts.

## 1. Observed x

Counts come from the committed series. Homes are ACS 2020–2024 one-unit detached homes. Exposure is thousand home-years. Intervals are exact Poisson 95%. Source: `reference/wi_baseline_observed.csv`.

| Key | Window | Units | Homes | Exposure | x per 1,000/yr | 95% interval | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| madison_2022_2025 (**floor window, G2-9**) | 2022–2025 | 39 | 53,292 | 213.2 | **0.183** | 0.130–0.250 | observed |
| madison_2022_2025_adu_type | 2022–2025 | 35 | 53,292 | 213.2 | 0.164 | 0.114–0.228 | observed |
| madison_2022_2025_excl_templated | 2022–2025 | 32 | 53,292 | 213.2 | 0.150 | 0.103–0.212 | observed (sensitivity) |
| madison_2024_2025 | 2024–2025 | 25 | 53,292 | 106.6 | 0.235 | 0.152–0.346 | observed (sensitivity) |
| madison_2026_provisional | 2026-01-01 to 2026-10-23 | 42 | 53,292 | 43.2 | 0.973 | 0.701–1.315 | observed, provisional, sensitivity only |
| madison_2014_2021 (restricted regime) | 2014–2021 | 21 | 53,292 | 426.3 | 0.049 | 0.030–0.075 | observed |
| madison_2022_2023 (restricted regime) | 2022–2023 | 14 | 53,292 | 106.6 | 0.131 | 0.072–0.220 | observed |
| pleasant_prairie_2014_2025 | 2014–2025 | 3 | 6,332 | 76.0 | **0.039** | 0.008–0.115 | observed |
| pleasant_prairie_2014_2025_upper | 2014–2025 | 6 | 6,332 | 76.0 | 0.079 | 0.029–0.172 | observed (upper bound) |
| pleasant_prairie_2014_2025_adu_type | 2014–2025 | 1 | 6,332 | 76.0 | 0.013 | 0.000–0.073 | observed |
| sun_prairie_2016_2026may (restrictive period) | 2016-01-01 to 2026-05-04 | 2 | 8,118 | 83.9 | **0.024** | 0.003–0.086 | observed |
| sun_prairie_2016_2026may_adu_type | same | 2 | 8,118 | 83.9 | 0.024 | 0.003–0.086 | observed |
| fitchburg_2022_2026jul (restricted) | 2022-01-01 to 2026-07-31 | 0 | 5,999 | 27.5 | 0.000 | 0.000–0.134 | observed (text only) |
| milwaukee_pre_central | 2017-01-01 to 2025-08-01 | 46 | 101,402 | 870.4 | 0.053 | 0.039–0.070 | observed candidate |
| milwaukee_pre_upper | same | 92 | 101,402 | 870.4 | 0.106 | 0.085–0.130 | observed candidate |
| milwaukee_post_central | 2025-08-02 to 2026-06-15 | 8 | 101,402 | 88.3 | 0.091 | 0.039–0.179 | observed candidate |
| milwaukee_post_upper | same | 11 | 101,402 | 88.3 | 0.125 | 0.062–0.223 | observed candidate |

**Madison.**
- The rules were restricted until December 2021: conditional use plus owner occupancy.
- From 2021-12-16 ADUs were by right, but owner occupancy was still required until 2024-04-25.
- After that, Madison is at benchmark.
- The 2022–2025 window (G2-9) therefore mixes two owner-occupancy years with two benchmark years. Its series rises every year: 5, 9, 11, 14.
- The 2025 count includes 7 templated-programme units. They are real current-law production, so they stay in x, with a sensitivity that drops them.

**Pleasant Prairie and Sun Prairie.**
- Pleasant Prairie counts issued permits. Sun Prairie counts submitted applications.
- Pleasant Prairie's 3 units are best read as 0–3.
- Sun Prairie's restrictive period ends 2026-05-04. Its August 2026 duplex conversion falls after the reform and is not counted.

**Fitchburg** (new evidence; the source was listed in [COMPARISON_CITY_SEARCH.md](../gate2/COMPARISON_CITY_SEARCH.md)).
- The City posts yearly Excel files of every issued permit.
- Every permit description from 2022-01-01 to 2026-07-31 was scanned, 50,007 text cells in all, with the ADU-type text rule in `FITCHBURG_ADU_PATTERN`.
- There were no hits. Fitchburg was `restricted` throughout:
  - until 2025-09-09, only an attached owner-occupied dependency unit, by conditional use;
  - after that, ADUs by right with a size cap.
- Limits of this evidence:
  - It is text only, with no parcel check, so a duplex conversion described without ADU wording would be missed.
  - The 2019–2021 files carry generic descriptions, so the window starts in 2022. Including them would change the restricted rate from 0.0625 to 0.0606.
- Applicant names, e-mails, and phone numbers are never loaded into outputs.

**Milwaukee** (open permit data, CC-BY).
- The data has no description and no unit count, so the counts are *candidates*.
- The candidate rule:
  - The permit is a residential permit marked "Dwelling units impact: Added or Gained".
  - It matches a single parcel in the current Master Property file.
  - The parcel's recorded building predates the permit year.
- **Central** count: the parcel records 1 unit, and the permit is an alteration (a conversion or attached unit) or a detached garage that adds a unit.
- **Upper** count: also allows 2 recorded units, and new one- or two-family construction on an occupied lot.
- Pre-reform candidates exist because Milwaukee's RT (two-family) districts already allowed a second unit by right.

## 2. Estimated x for every other municipality

**Groups.** Each municipality piece takes its coded current class from `reference/wi_rights_exposure.csv` (scenario `adu_full`). Classes map to groups as follows:

| Class | Group |
| --- | --- |
| `scenario_benchmark` | benchmark |
| `restricted` | restricted |
| `prohibited_explicit`, `prohibited_implicit` | prohibited |
| `undetermined` (all 1,882 uncoded pieces) | undetermined |
| `no_zoning` (none coded yet) | undetermined |

**How each group's values are set.** Source: `reference/wi_baseline_rates_by_group.csv`.

| Group | Low | Central | High | How |
| --- | --- | --- | --- | --- |
| prohibited | 0.010 | 0.031 | 0.073 | Pooled count of Pleasant Prairie and Sun Prairie, 5 units over 159.9 thousand home-years; exact Poisson interval |
| restricted | 0.031 | 0.062 | 0.131 | Pooled restricted regimes: Madison 2014–2021 (21 units), Madison 2022–2023 (14), Fitchburg (0) = 35 over 560.4. Low is the prohibited central (a restricted place can be as quiet as a banned one). High is Madison 2022–2023 (by right, owner occupancy only) |
| benchmark | 0.062 | 0.183 | 0.250 | Madison 2022–2025. Low is the restricted central (a smaller, weaker market than Madison). High is Madison's upper Poisson bound |
| undetermined | 0.031 | 0.062 | 0.131 | Assumed: behaves like restricted (AQ-027). Low is the prohibited central |

**Who uses these values.**
- Pleasant Prairie and Madison keep their own observed x and intervals.
- Milwaukee is a special case (section 4).
- Every other coded place takes its group's value, labeled *estimated*.
- Uncoded places take the undetermined values, labeled *assumed*.

**Places still ramping.** Some places moved detached ADUs from prohibited to allowed on a dated change in `wi_adu_rules.csv`. Their rate ramps linearly from the prohibited rate to their group rate (assumed):

| Place | Date of change |
| --- | --- |
| Appleton | 2021-07-13 |
| West Allis | 2022-05-03 |
| Oshkosh | 2023-02-28 |
| La Crosse | 2024-02-17 |
| Fond du Lac | 2025-02-26 |
| Franklin | 2025-06-09 |
| Milwaukee | 2025-08-02 |
| Sun Prairie | 2026-05-08 (ramps from its own observed 0.024) |
| Waukesha | 2026-09-01 |

- **Ramp length by path:** 6 years (low), 4 years (central), 2 years (high), measured at mid-year.
- **Why 4 years for central:** Madison after by-right approval (December 2021) produced 5, 9, 11, then 14 second homes and was still rising after four years.
- Eau Claire, Fitchburg, and Green Bay changed their rules but were already restricted before, so they do not ramp.

**Plain reading.** The group rates are small and close together.
- A banned place produces about 3 second homes per 100,000 single-family homes a year.
- A restricted or unknown place produces about 6.
- Madison produces about 18.

## 3. Hold-out of coded places

**Drawn first.** The hold-out was drawn and saved to `reference/wi_holdout_coded_places.csv` before any group rate was computed. It used identifiers only, seed 20261024 (the same seed as the California plan), and `round(0.20 × 34)` = 7 places.

**Held out:** De Pere, Superior, Franklin, Wauwatosa, Appleton, Mount Pleasant, Racine.
- These places are never used to fit a rate. They get predicted values like any other place.
- The build checks that the draw still reproduces.

**What can be tested now.** The pre-registered rule says to predict rights from first-pass ordinance status alone:
- `mentioned_allowed` predicts an allowed place;
- `unmentioned` or `prohibited` predicts a prohibited place.

Results (`reference/wi_baseline_holdout_check.csv`):

| Set | Correct | Misses |
| --- | --- | --- |
| Held-out places | **7 of 7** | none |
| Places not held out | 27 of 30 | Kenosha and Beloit are `unmentioned` but restricted; Manitowoc's code names ADUs but is implicitly prohibited |

**Rates cannot be tested yet.** None of the 7 held-out places has record-level permits obtainable by plain HTTP (Gate 2 search):

| Place | Permit source |
| --- | --- |
| De Pere | Monthly PDFs; the site blocks scripts |
| Appleton | Weak, partial |
| Franklin, Wauwatosa, Mount Pleasant, Racine | None |
| Superior | None found |

**Later tests:**
- Read De Pere's PDFs by hand, or ask the owner whether a records request is acceptable.
- Once the first-pass scan is extended to uncoded places, use the status rule to predict their class, and spot-check a random sample.
- Fit the simple regression of observed rates on class, restriction flags, and context (AQ-027) once more places have permit records.

**Out-of-sample check, not part of the hold-out.**
- Milwaukee's candidate post-reform rate is 0.091 (0.039–0.179).
- The rate predicted from its ordinance status (allowed, so restricted) is 0.062.
- The two are consistent, but the interval is wide.

**Deviation from the pre-registered wording.** The plan ([CA_COMPARISON_PLAN.md](CA_COMPARISON_PLAN.md), "Wisconsin") says "a random sample of the 37 coded Wisconsin places".
- I excluded the three observed pilots from the draw. They are the fitting set the owner named (AQ-028), and holding one out would leave nothing to fit that group with.
- **What the literal draw would have been:** the same seed over all 37 gives De Pere, Sun Prairie, Manitowoc, Milwaukee, West Allis, Mount Pleasant, and Menomonee Falls.
  - That draw holds out a pilot (Sun Prairie).
  - The status rule scores 6 of 7 on it (Manitowoc is the miss).
  - Its only rate test is Milwaukee, which is consistent (above).

**Timing disclosure.** I explored the Milwaukee open data before drawing the hold-out. The draw used identifiers and a fixed seed only, so this exploration could not influence which places were drawn.

## 4. Milwaukee's baseline ramp g (sensitivity case since AQ-043)

**Update 2026-10-26 (AQ-043).** The adopted baseline no longer uses this ramp. Milwaukee's x is its measured 2022–2025 rate, 0.0863 (35 candidate permits ÷ 405.608 thousand home-years), held flat with g = 1, status *observed*; `reference/wi_baseline_milwaukee_ramp.csv` now holds that flat rate. The reasons: the post-reform candidates (0.091, 95% interval 0.039–0.179) show no clear rise, and the ramp to Madison's level was an assumption. The ramp below is kept as the baseline-only sensitivity "Milwaukee rises to Madison's rate after its 2025 reform": baseline 644.9 permits over 2027–2031 (+40.2), central addition −36.0, total with the law +4.2. The text and table below describe the Gate 3 ramp as it was.

**Rules.** File 240999, effective 2025-08-02:
- detached and attached ADUs by right;
- no parking requirement;
- size up to 1,300 sq ft detached;
- owner occupancy required only at application.

It is coded `restricted`, but its only flag is owner occupancy at application, so I use a Madison-like target. Milwaukee's x is labeled *estimated*, with the ramp *assumed*.

**Evidence since the reform** (`reference/wi_baseline_milwaukee_candidates.csv`), 2025-08-02 to 2026-06-15, the end of the published data:
- 8 candidate conversions or attached units on one-unit homes (9 under the upper rule);
- no detached-garage units;
- 2 possible new dwellings on occupied lots (upper rule only).

So the rate is 0.091 (0.039–0.179) per 1,000 a year, against 0.053 (0.039–0.070) in 2017 to mid-2025. That is consistent with no change or with a doubling. There is no sign of a detached-ADU market yet.

**Proposed ramp (assumed).**
- **Start:** the observed pre-reform candidate rate.
- **Central:** rises linearly to Madison's 0.183 by mid-2029.
- **Low:** rises to the restricted central (0.062) over 6 years.
- **High:** rises to Madison's upper bound (0.250) over 2 years.
- The central value for 2026 (0.083) sits right at what was observed so far (0.091).

Source: `reference/wi_baseline_milwaukee_ramp.csv`.

| Year | x central | g central | B central | B low | B high |
| --- | --- | --- | --- | --- | --- |
| 2026 (bridge) | 0.083 | 0.45 | 8.4 | 4.3 | 17.4 |
| 2027 | 0.115 | 0.63 | 11.7 | 4.7 | 24.7 |
| 2028 | 0.148 | 0.81 | 15.0 | 5.1 | 25.4 |
| 2029 | 0.180 | 0.98 | 18.3 | 5.5 | 25.4 |
| 2030 | 0.183 | 1.00 | 18.6 | 5.9 | 25.4 |
| 2031 | 0.183 | 1.00 | 18.6 | 6.3 | 25.4 |
| **2027–2031** | | | **82.0** | **27.5** | **126.2** |

`g` is defined against each path's own plateau. That is why g is higher on the low path, which has a lower target.

## 5. Statewide baseline B

**Statewide totals** (`reference/wi_baseline_statewide.csv`). The three paths move together across all areas: the uncertainty is shared, not independent per place. Units are second homes on single-family lots.

| Year | Low | Central | High |
| --- | --- | --- | --- |
| 2026 (bridge, not in totals) | 60 | 122 | 246 |
| 2027 | 61 | 125 | 255 |
| 2028 | 62 | 129 | 256 |
| 2029 | 63 | 133 | 256 |
| 2030 | 63 | 133 | 256 |
| 2031 | 64 | 133 | 256 |
| **2027–2031** | **313** | **654** | **1,279** |

The total covers 1,839,569 one-unit detached homes in 1,925 municipality pieces. The pieces sum exactly to the state, so there is no unallocated remainder.

**By how x was set** (`reference/wi_baseline_by_x_status.csv`):

| How x was set | Pieces | Homes | 2027–2031 central |
| --- | --- | --- | --- |
| Observed | 2 | 59,624 | 50 |
| Estimated | 41 | 512,512 | 208 |
| Assumed | 1,882 | 1,267,433 | 396 |

**By context group** (central, 2027–2031): urban 223, rural 222, suburban 131, small community 78. Counties are in `reference/wi_baseline_by_county.csv`, led by Milwaukee (117), Dane (73), and Waukesha (33).

**Sensitivities** (central, 2027–2031; `reference/wi_baseline_sensitivities.csv`):

| Change | Total | Change |
| --- | --- | --- |
| Main | 654 | |
| Uncoded places behave like prohibited (old AQ-023 default) | 457 | −198 |
| No ramp (g = 1) | 667 | +13 |
| Madison x = 2024–2025 | 668 | +14 |
| Madison x without the templated programme | 645 | −9 |
| Madison x = 2026 provisional, to date | 865 | +210 |

**20 largest contributors** (2027–2031; `reference/wi_baseline_top20.csv`). Together they are 227 homes, 35% of the central total.

| # | Municipality | County | Class | x basis | x (plateau) | Low | Central | High | Share |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Milwaukee city | Milwaukee | restricted | estimated (ramp) | 0.183 | 27.5 | 82.0 | 126.2 | 12.5% |
| 2 | Madison city | Dane | scenario_benchmark | observed | 0.183 | 34.7 | 48.8 | 66.6 | 7.4% |
| 3 | Appleton city | Outagamie | scenario_benchmark | estimated | 0.183 | 5.9 | 17.2 | 23.5 | 2.6% |
| 4 | Wauwatosa city | Milwaukee | scenario_benchmark | estimated | 0.183 | 4.0 | 11.8 | 16.2 | 1.8% |
| 5 | Green Bay city | Brown | restricted | estimated | 0.062 | 4.2 | 8.3 | 17.5 | 1.3% |
| 6 | Kenosha city | Kenosha | restricted | estimated | 0.062 | 3.8 | 7.5 | 15.9 | 1.1% |
| 7 | Eau Claire city | Eau Claire | restricted | estimated | 0.062 | 2.6 | 5.3 | 11.1 | 0.8% |
| 8 | Oshkosh city | Winnebago | restricted | estimated | 0.062 | 2.4 | 5.1 | 10.8 | 0.8% |
| 9 | West Allis city | Milwaukee | restricted | estimated | 0.062 | 2.4 | 4.8 | 10.1 | 0.7% |
| 10 | Waukesha city | Waukesha | restricted | estimated (ramp) | 0.062 | 1.6 | 4.1 | 9.8 | 0.6% |
| 11 | New Berlin city | Waukesha | restricted | estimated | 0.062 | 1.9 | 3.8 | 8.0 | 0.6% |
| 12 | Wausau city | Marathon | restricted | estimated | 0.062 | 1.9 | 3.7 | 7.8 | 0.6% |
| 13 | La Crosse city | La Crosse | restricted | estimated | 0.062 | 1.6 | 3.6 | 7.6 | 0.5% |
| 14 | Racine city | Racine | prohibited_explicit | estimated | 0.031 | 1.1 | 3.5 | 8.3 | 0.5% |
| 15 | Fond du Lac city | Fond du Lac | restricted | estimated | 0.062 | 1.5 | 3.5 | 7.9 | 0.5% |
| 16 | Beloit city | Rock | restricted | estimated | 0.062 | 1.7 | 3.3 | 6.9 | 0.5% |
| 17 | Janesville city | Rock | prohibited_implicit | estimated | 0.031 | 1.0 | 3.1 | 7.2 | 0.5% |
| 18 | Oak Creek city | Milwaukee | restricted | estimated | 0.062 | 1.3 | 2.7 | 5.6 | 0.4% |
| 19 | Appleton city (Calumet part) | Calumet | scenario_benchmark | estimated | 0.183 | 0.9 | 2.6 | 3.6 | 0.4% |
| 20 | Franklin city | Milwaukee | restricted | estimated (ramp) | 0.062 | 1.1 | 2.6 | 5.9 | 0.4% |

Every municipality piece, with its x, status, basis and five-year range, is in `reference/wi_baseline_by_municipality.csv`.

## 6. Worked example: Madison (observed)

1. **Homes.** H = 53,292 one-unit detached homes (ACS 2020–2024, MOE ±1,235).
2. **Count.** Second homes on single-family lots 2022–2025: 5 + 9 + 11 + 14 = **39**.
   - Detached ADUs: 3, 6, 10, 12.
   - Conversions: 2, 1, 0, 1.
   - Single-family-to-duplex conversions: 0, 2, 1, 1.
   - The ADU-type part alone (detached, attached, conversion, two-unit) is 35.
3. **Exposure.** 53.292 thousand homes × 4 years = 213.17 thousand home-years.
4. **Rate.** x = 39 / 213.17 = **0.183 per 1,000 homes per year**.
   - The exact Poisson 95% interval for a count of 39 is 27.7–53.3, so x is 0.130–0.250.
5. **Baseline per year.** B = 53,292 × 0.183 / 1000 = **9.75 second homes a year**.
   - Madison did not ramp from a ban, so g = 1.
   - 2027–2031: **48.8** (low 34.7, high 66.6).
6. **Reading.** Madison's series is still rising (14 in 2025; 42 in 2026 to date, 29 of them from one templated programme). The flat 2022–2025 rate is a conservative current-law baseline.
   - Using 2024–2025 instead (0.235) adds 14 statewide.
   - Using 2026 (provisional) adds 210 statewide.

## 7. Estimated example: Star Prairie village (uncoded)

1. **Homes.** H = 260 one-unit detached homes. Star Prairie is in St. Croix County, context group small community.
2. **Rules.** None coded and no first-pass status, so its class is `undetermined`.
3. **Rate.** Under AQ-027 an undetermined place behaves like `restricted`, so x = **0.062** per 1,000 homes a year (low 0.031, high 0.131). Labeled *assumed*.
4. **Baseline per year.** B = 260 × 0.0625 / 1000 = **0.016 second homes a year**. Five years: **0.08** (0.04–0.17).
5. **Display.** Shown as "about 0.06 per 1,000 homes a year; fewer than one second home expected over five years (0–1)". The modeled value is labeled, never hidden or shown as a lot-level forecast.

## Deviations and limits

**Deviations**
1. The hold-out excludes the three pilots (section 3). The literal draw from all 37 is reported alongside.
2. The pre-registered hold-out test predicts rates from ordinance status. No held-out place has permit records, so only the status-to-class check could be run now. The rate test is listed as later work.
3. Madison's x uses the G2-9 floor window (2022–2025) for consistency with the floor. It keeps the 2025 templated units as real current-law production. The version without them is a sensitivity (−9 statewide).

**Limits**
- **Small counts.** Every observed rate rests on 0–46 events. The prohibited group rests on 5.
- **The restricted rate is mostly Madison**, Wisconsin's strongest ADU market. It may be high for rural towns, where demand and septic limits differ; the low path uses the prohibited rate. Towns under county zoning take the undetermined rate, whoever writes their rules.
- **Weaker evidence.** Milwaukee's counts are unverified candidates. Fitchburg is text only.
- **Comparability.** Sun Prairie counts submitted applications, while the others count issued permits.
- **Ramps.** Ramp lengths are assumed, informed only by Madison's 2022–2025 shape.
- **Engine conventions for the conductor.** In `x_rate` the engine gets each ramping place's *plateau* rate, with `g` below 1. Two consequences:
  - The additional-units formula `H × (y − x)` uses the plateau x, so for Milwaukee it understates the gap between the with-law rate and the still-ramping baseline in 2027–2029. Using `x × g` would close that gap; this is the conductor's decision.
  - The engine holds the baseline identical across paths. The low and high baselines here are a baseline range, separate from the y paths.

## Reproduce

```
uv run python scripts/build_wi_baseline.py --fetch   # downloads Milwaukee permits (3 MB), MPROP (90 MB), Fitchburg (8 xlsx, 1 MB)
uv run python scripts/build_wi_baseline.py           # rebuild from local raw files (about 3 s)
bash scripts/test.sh                                 # offline tests, including tests/test_wi_baseline.py
```

The build needs the statewide foundation (`data/processed/foundation/`). It writes the `reference/wi_baseline_*.csv` aggregates and local files in `data/processed/model_baseline/`:
- `baseline_long.parquet`;
- `assigned_rates.parquet`;
- `engine_areas.parquet` and `engine_baseline_growth.parquet`, which are inputs for `missing_middleware/model/engine.py`;
- `run_manifest.json`, with checksums.

**Sources**, all accessed 2026-10-24 by plain HTTP:

| Source | License | sha256 (first 16) |
| --- | --- | --- |
| [Milwaukee building permits](https://data.milwaukee.gov/dataset/buildingpermits) | CC-BY | `c3ff9d0965b024e4` |
| [Milwaukee Master Property file](https://data.milwaukee.gov/dataset/mprop) | CC-BY | `2bbbe466b1967f00` |
| [Fitchburg Building Permit Reports](https://www.fitchburgwi.gov/3007/Building-Permit-Reports) | public record, no license stated | per file in the manifest |

- **Milwaukee permits:** 16,685 issued permits, 2015-06 to 2026-06-15.
- **Milwaukee Master Property file:** only address, units, and year built are read. Owner fields are never loaded.
- **Fitchburg:** 2019–2026 Excel files. Applicant fields are never loaded.

Raw files stay in `data/raw/` (git-ignored). Committed outputs hold no addresses, record numbers, or names.

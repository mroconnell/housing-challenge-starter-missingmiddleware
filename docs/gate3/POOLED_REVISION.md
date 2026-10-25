# Pooled model with the owner's outcome rules, and the G3F-2 test

Prepared 2026-10-25 for the owner (AQ-040, G3F-1 to G3F-3; AQ-041: California option (ii) is the main candidate). Status: **candidate outputs, not adopted.** The adopted files (`reference/pooled_*.csv`, `reference/adu_model_*.csv`) are unchanged; everything here is in new files named `pooled_revision_*`.

**Units used throughout.** Unless a sentence says otherwise:
- a **rate** is ADU (second-home) permits issued in a year ÷ thousands of one-unit detached homes (ACS 2020–2024 B25024_002): "permits per 1,000 single-family homes per year";
- **additional permits** are with-law permits minus the current-law baseline, summed over Wisconsin's five forecast years 2027–2031, from the engine (Madison floor applied, path ramp applied). The engine baseline is **645 permits over 2027–2031** (644.9; it was 654 before the AQ-039 Wisconsin rerun);
- a **log error** is log(predicted rate ÷ observed rate) for a held-out state over its post-law years; +0.10 means about 10% too high. **RMS** is the root of the mean squared log error over the 7 non-California statewide-law states (Washington, Oregon, Rhode Island, Massachusetts, Maine, Utah, Vermont).

All results are descriptive associations across states and places, not causal effects.

## Plain-language summary

- **G3F-2 answer: keep California in the between-state common level (configuration A).** Under the main California option (cap + A2), A predicts the 7 held-out non-California states with an RMS log error of **0.113**, against **0.132** with California left out (B) and **0.243** for the best covariate weighting (C, a between-state income term).
  - **A over B is within noise.** The gap is 0.019 log points (about 2%). Resampling the 7 states, A has the lower error in 66% of resamples and B in 33%. Removing one state from the data and rerunning, A wins 5 of 7 times; B wins when Washington or Rhode Island is removed.
  - **What is not noise:** B predicts every state except Washington and Massachusetts too low (mean log error −0.087), and A too high on average (+0.055). Neither is clearly better.
  - **Covariates still make it worse,** as in the adopted model: a between-state term on home value gives RMS 0.531 (Maine predicted at about a quarter of its rate, log error −1.32), income 0.243, price-to-income 0.318. They never win a resample against A or B more than 1% of the time.
  - The same ranking holds for all three California options.
- **Wisconsin, main candidate (California cap + A2, configuration A, Madison floor 0.2345):**
  - Lower **4,424**, central **8,912**, upper ("Strong adoption") **17,374** additional permits over 2027–2031. The adopted figures were 4,789 / 9,526 / 18,398.
  - Central rate path: 0.79, 0.98, 1.01, 1.21, 1.21 permits per 1,000 single-family homes per year in 2027–2031.
  - Of the 614-permit drop in the central (9,526 → 8,912): the vacant-lot rule removes about 406, the California cap + A2 rule about 205 (9,523 → 9,318 with the other rules off), the Wisconsin baseline update about 3; Minneapolis and the new floor move it by less than 1.
- **The "Strong adoption" upper, stated plainly (G3F-1):** it is the 90th percentile of how much statewide-law states' levels differ (8 states, California included). Its year-4-and-later rate for Wisconsin is 2.28 permits per 1,000 single-family homes per year. Only California's level is above that point; the other seven states sit at 0.62–1.19 at their typical place. So the info icon can say: "Above every statewide-law state except California; about what you would see if Wisconsin got close to California's level of permitting in the years after its statewide laws." Putting Wisconsin exactly at California's adjusted level gives 22,694.
- **Pending decision, information only — Madison-like path:** Madison is the only Wisconsin place that meets the Madison-like definition. If it followed the observed Madison-like median path (0.452, 0.542, 0.601, 0.799, 1.076) instead of the pooled level, the central would be **8,721** instead of 8,912: Madison's own addition falls from 326 to 135 permits over 2027–2031.

## 1. Input options

Each is a named, switchable option in [`pooled_revision.py`](../../missing_middleware/comparison/pooled_revision.py); the runner is [`run_pooled_revision.py`](../../scripts/run_pooled_revision.py).

### California ADU counts (three options)

Applied to every California jurisdiction-year row in the pooled data, so they reach both the within-state stage (457 jurisdictions' rates) and California's between-state level and adoption values. Removals are counted per jurisdiction-year from [`ca_mf_lot_adu_share_by_jurisdiction.csv`](../../reference/ca_mf_lot_adu_share_by_jurisdiction.csv). A statewide factor by year is applied where a jurisdiction-year has observed ADUs but no A2 parcel data; in the current data that never happens (all 3,230 adjusted jurisdiction-years have parcel data). Years before 2018 (no APNs) are unchanged.

| Option | Rule | California 2023–2025, 457 pooled jurisdictions: ADU units ÷ home-years → rate | California's level (law in force, year 4+, typical place) |
| --- | --- | --- | ---: |
| (i) as used | study main measure | 87,303 ÷ 23,543,548 → 3.71 | 2.61 |
| **(ii) cap + A2 (main, AQ-041)** | at most 2 ADU units per parcel, cumulated 2018–2025, plus the definite A2 APN rule (3+ units on one APN in a year before 2023-01-01, 4+ from then) | 81,368 ÷ 23,543,548 → **3.46** | **2.45** |
| (iii) cap + LA-calibrated (sensitivity) | cap plus the central multifamily-lot share calibrated to LA County | 66,834 ÷ 23,543,548 → 2.84 | 2.08 |

- Option (iii) is rebuilt per jurisdiction-year from the band counts and the LA calibration files ([`ca_mf_lot_adu_share_la_calibration_bands.csv`](../../reference/ca_mf_lot_adu_share_la_calibration_bands.csv), [`..._la_calibration_fit.csv`](../../reference/ca_mf_lot_adu_share_la_calibration_fit.csv)) with the jurisdiction's ACS share of units in 2+-unit structures. It reproduces the statewide yearly totals in [`ca_mf_lot_adu_share_rates_by_year.csv`](../../reference/ca_mf_lot_adu_share_rates_by_year.csv) to 0.1 ADU unit in every year 2018–2025 (for example 22,050.0 ADU units in 2023). Option (ii) reproduces them exactly.
- Statewide rates by year for each option: [`pooled_revision_ca_inputs.csv`](../../reference/pooled_revision_ca_inputs.csv). For example 2025: 3.91 (as used, 31,945 ADU units ÷ 8,178,290 homes), 3.61 (cap + A2, 29,549), 2.97 (LA-calibrated, 24,308).
- The California activity groups (set from 2017–2019) are kept as published in the California-only sensitivity.

### Other inputs (on in every revised run)

| Rule | Applied to | Factor | Effect on the main central (additional permits over 2027–2031) |
| --- | --- | ---: | ---: |
| Vacant-lot new-house ADUs (AQ-039, G3F-3) | every non-California row whose count includes ADUs built with a new house: all 7 state series and the five cities' counts | × (1 − 0.049) = 0.951 | 9,318 without it → 8,912 with it (−406) |
| Minneapolis duplex-lot ADUs | Minneapolis rows (2017–2025) | × (1 − 0.127) = 0.873 | under 1 permit (Minneapolis has no statewide law, so it enters only the within-state law and local-reform terms) |
| Madison floor | every area and path in the engine | 0.2345 instead of 0.229 | under 1 permit (it binds almost nowhere at the central level) |

- California is not given the vacant-lot factor: its counts already exclude the ADUs built with a new house that the study could identify. Wisconsin is not adjusted (its counts already exclude vacant-lot ADUs).
- **Madison floor** = 40 second-home units in Madison 2022–2025 ÷ 213.168 thousand home-years (53,292 one-unit detached homes × 4 years) = 0.1876, ÷ 0.8 = **0.2345** permits per 1,000 single-family homes per year.
  - It is now set once, in `madison_floor` in [`adu_model_params.json`](../../reference/adu_model_params.json), with both variants and an `in_use` selector, read through [`params.py`](../../missing_middleware/model/params.py) by `run_adu_model.py` (every path and the rural sensitivity), `run_ca_regression.py` and `run_pooled_regression.py`.
  - `in_use` is still `adopted_2026_10_24` (0.229), so the adopted outputs reproduce unchanged. **To adopt, set `in_use` to `g3f_revision_2026_10_25`.** The revision runner always uses 0.2345.

## 2. G3F-2 test: California in or out of the common level

**Method.** For each California option, each non-California statewide-law state is held out of both stages; the model is refitted on everything else and predicts the held-out state's post-law rate from its own market and years since law. Configurations:
- **A:** California is one of the 8 states that set the between-state common level (the adopted model).
- **B:** California is left out of the between-state step (7 states set the common level). Its 457 jurisdictions still teach the within-state stage (place-to-place slopes, law and year terms).
- **C:** California is in, but its weight is set by a between-state covariate: log median home value, log median household income, or log price-to-income. The best of the three (income in every option) is the "C" compared below.

Within-state form in every case: the adopted value + income + size form. Files: [`pooled_revision_g3f2.csv`](../../reference/pooled_revision_g3f2.csv), [`pooled_revision_loso.csv`](../../reference/pooled_revision_loso.csv), [`pooled_revision_drop_one.csv`](../../reference/pooled_revision_drop_one.csv).

**Log error by held-out state, main option (ii) cap + A2:**

| Held-out state | A: California in | B: California out | C: income term | C: home-value term | C: price-to-income term |
| --- | ---: | ---: | ---: | ---: | ---: |
| Washington | +0.17 | +0.04 | +0.18 | +0.31 | +0.36 |
| Oregon | +0.04 | −0.09 | +0.04 | +0.05 | +0.25 |
| Rhode Island | −0.05 | −0.19 | −0.03 | −0.13 | −0.17 |
| Massachusetts | +0.19 | +0.04 | +0.47 | +0.34 | +0.16 |
| Maine | +0.00 | −0.15 | −0.34 | −1.32 | −0.67 |
| Utah | −0.08 | −0.23 | −0.08 | −0.08 | −0.09 |
| Vermont | +0.11 | −0.04 | +0.17 | +0.03 | −0.12 |
| **RMS, 7 states** | **0.113** | 0.132 | 0.243 | 0.531 | 0.318 |
| Mean log error | +0.055 | −0.087 | +0.060 | −0.114 | −0.041 |

**RMS log error over the 7 states, every option:**

| California option | A: California in | B: California out | C (best: income) | Winner |
| --- | ---: | ---: | ---: | --- |
| (i) as used | 0.114 | 0.132 | 0.251 | A |
| **(ii) cap + A2** | **0.113** | 0.132 | 0.243 | **A** |
| (iii) cap + LA-calibrated | 0.108 | 0.135 | 0.224 | A |

**How firm the ranking is (noise).** With 7 states, A against B is not settled:

| Check | (i) as used | (ii) cap + A2 | (iii) LA-calibrated |
| --- | --- | --- | --- |
| Resample the 7 states with replacement (5,000 resamples): share in which A / B / C has the lowest RMS | 64% / 36% / 1% | 66% / 33% / 1% | 75% / 24% / 1% |
| Remove one state from the data and rerun on the other 6: times A wins, of 7 | 5 (B wins without WA or RI) | 5 (B wins without WA or RI) | 5 (B wins without WA or RI) |
| RMS range over those 7 reruns, A / B | 0.112–0.170 / 0.103–0.171 | 0.108–0.159 / 0.104–0.163 | 0.099–0.147 / 0.106–0.161 |

**Reading.**
- By the owner's rule (whichever predicts the held-out non-California states best), **A wins under every California option**. The margin is small (0.019 log points under option (ii)) and inside the noise: the result rests on Washington and Rhode Island, and flips when either is removed.
- The two configurations err in opposite directions. Without California the common level is about 12% lower (0.88 against 1.00 permits per 1,000 single-family homes per year at a typical place, law in force, year 4+), and it then under-predicts 5 of the 7 states.
- The California adjustments make A slightly better (0.114 → 0.113 → 0.108) because a lower California level pulls the common level toward the other states.
- **Covariate weighting (C) is re-checked with the adjusted data and still fails.** Every between-state market term predicts held-out states worse than either A or B, mainly Maine, the market closest to Wisconsin (home value term: Maine predicted at exp(−1.32) = 0.27 of its rate). This matches the adopted model's finding.

## 3. Wisconsin results

Engine totals, Madison floor 0.2345, path ramps from the pooled year terms (applied once; the California ramp is not added). All values are additional permits over 2027–2031 statewide, on top of the 645-permit engine baseline. File: [`pooled_revision_wi.csv`](../../reference/pooled_revision_wi.csv), by year in [`pooled_revision_wi_by_year.csv`](../../reference/pooled_revision_wi_by_year.csv).

| | (ii) cap + A2, A — **main candidate** | (iii) LA-calibrated, A — sensitivity | (i) as used, A — comparison | Adopted (AQ-038) |
| --- | ---: | ---: | ---: | ---: |
| Baseline (permits, 2027–2031) | 645 | 645 | 645 | 645 |
| **Lower** ("like the slower statewide-law states", 10th percentile) | **4,424** | 4,586 | 4,455 | 4,789 |
| **Central** ("like a typical statewide-law state") | **8,912** | 8,579 | 9,112 | 9,526 |
| **Upper: "Strong adoption"** (90th percentile) | **17,374** | 15,621 | 18,019 | 18,398 |
| Wisconsin at California's own level | 22,694 | 19,150 | 23,977 | — |
| Central rate, 2027 → 2030–31 (per 1,000 single-family homes per year) | 0.79 → 1.21 | 0.79 → 1.14 | 0.79 → 1.25 | 0.83 → 1.30 |
| Year-4+ rate, lower / upper | 0.64 / 2.28 | 0.65 / 2.02 | 0.65 / 2.39 | 0.69 / 2.43 |
| Between-state spread τ (log scale, 8 states); 80% factor | 0.42; × or ÷ 1.89 | 0.38; × or ÷ 1.76 | 0.43; × or ÷ 1.91 | 0.42; × or ÷ 1.87 |
| Engine ramp, central path (years 1–5) | 0.63, 0.80, 0.82, 1, 1 | 0.67, 0.83, 0.84, 1, 1 | 0.61, 0.78, 0.81, 1, 1 | 0.62, 0.78, 0.81, 1, 1 |
| **Reference line: statewide adoption** (median observed path; no California in it) | 8,664 as reported; **8,208** with the vacant-lot rule | same | same | 8,654 |
| Sensitivity: multiplicative law (Wisconsin's current rate × the pooled law factor) | 722 | 683 | 753 | 758 |
| Sensitivity: California-only market regression, refitted on the option's counts | 2,361 | 2,185 | 2,350 | 2,337 |
| Sensitivity: no ramp (full rate from 2027) | 10,476 | 9,879 | 10,835 | 11,294 |
| Sensitivity: rural and small-community places at the Madison floor | 4,921 | 4,776 | 5,008 | 5,185 |

- Lower and upper path ramps for (ii): 0.61, 0.78, 0.81, 1, 1 and 0.64, 0.80, 0.83, 1, 1.
- If the owner preferred B despite the test, the option-(ii) figures would be 5,191 / 7,767 / 11,482 (lower / central / upper). B's upper is then no longer California-driven: τ falls to 0.24 across 7 states, so the "Strong adoption" basis above would not apply.
- The adoption line rates with the vacant-lot rule are 0.75, 0.86, 0.83, 1.18, 1.18 permits per 1,000 single-family homes per year (as reported: 0.79, 0.90, 0.88, 1.24, 1.24). It is 8,664 rather than the adopted 8,654 because the baseline it subtracts is now 645, not 654.

**"Strong adoption" (G3F-1), basis stated plainly.**
- **What the number is:** Wisconsin's central path × 1.89, the 90th percentile of how far a new statewide-law state's level can sit from the common level, given how the 8 known states (California included) differ.
- **What it corresponds to:** at a typical place, law in force, year 4+, the upper level is 1.89 permits per 1,000 single-family homes per year. The states' own levels, option (ii), are California 2.45; Washington 1.19, Utah 1.08, Maine 1.00, Vermont 0.90, Massachusetts 0.85, Oregon 0.68, Rhode Island 0.62 ([`pooled_revision_stage2_levels.csv`](../../reference/pooled_revision_stage2_levels.csv)). Only California is above it.
- **Suggested info-icon text:** "Strong adoption: higher than every state with a statewide ADU law except California. It lies between a typical statewide-law state (1.00) and California's level of permitting in the years after its statewide laws (2.45, counting no more than 2 ADUs per parcel and leaving out ADUs the parcel records show are on multifamily lots)." Wisconsin exactly at California's level would be 22,694.

**Reproduction check.** With California as used, the non-California rules off, the 0.229 floor and configuration A, the revision code gives 9,527 direct and 9,523 from the engine, against the adopted 9,518 direct and 9,526 engine (lower 4,785 vs 4,789; upper 18,392 vs 18,398). The small gaps come from the AQ-039 Wisconsin rerun of 2026-10-25 (current-law rates and the 645-permit baseline), which postdates the adopted pooled run. The California-only regression refitted on as-used counts reproduces the per-area `y_central` in `wi_y_by_area.csv` to within 0.0001 permits per 1,000 single-family homes per year.

## 4. Pending owner decision (information only, not adopted): Madison-like path

Definition from [MADISON_LIKE_CITIES.md](MADISON_LIKE_CITIES.md) section 0: incorporated (Wisconsin city or village), 20,000–120,000 one-unit detached homes (ACS 2020–2024 place B25024_002), median value $250,000–$500,000 (B25077_001), not the state's largest city.

- **Only Madison qualifies** (53,292 homes, $372,900). [`pooled_revision_madison_like_wi.csv`](../../reference/pooled_revision_madison_like_wi.csv) lists every city or village with 10,000+ homes.
  - Milwaukee is the largest city (101,402 homes) and fails on value too ($184,000).
  - Green Bay (26,655 homes, $207,200), Kenosha (24,161, $225,200), Racine (22,636, $166,500) and Appleton (21,690, $231,400) fail on value.
  - Waukesha ($315,500), Wauwatosa, Brookfield ($443,900) and New Berlin pass on value but have under 20,000 homes (12,121–15,931).
- **Result.** Madison on the observed median path of WA and OR Madison-like cities (0.452, 0.542, 0.601, 0.799, 1.076 permits per 1,000 single-family homes per year in years 1–5, [`madison_like_median_path.csv`](../../reference/madison_like_median_path.csv)), with no ramp on top since the path is already observed:

  | California option | Madison, pooled level | Madison, Madison-like path | Statewide central, pooled | Statewide central, Madison on the path |
  | --- | ---: | ---: | ---: | ---: |
  | (ii) cap + A2 | 326 | 135 | 8,912 | **8,721** |
  | (iii) LA-calibrated | 312 | 135 | 8,579 | 8,402 |
  | (i) as used | 335 | 135 | 9,112 | 8,912 |

  All values are additional permits over 2027–2031. Under option (ii), Madison's pooled rate is 1.07, 1.31, 1.36, 1.63, 1.63 permits per 1,000 single-family homes per year in 2027–2031 (current-law rate 0.188), against 0.452–1.076 on the path.
- Because only one place qualifies, this choice moves the statewide central by about 2% (191 of 8,912). It matters more for Madison's own figure than for Wisconsin's.

## 5. Compact results table (main candidate first)

| California option | G3F-2 winner (RMS A / B / best C) | Lower | Central | Strong adoption | Adoption line | Multiplicative | CA-only | No ramp | Rural at floor | Central, Madison on path |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **(ii) cap + A2** | **A** (0.113 / 0.132 / 0.243) | **4,424** | **8,912** | **17,374** | 8,208 | 722 | 2,361 | 10,476 | 4,921 | 8,721 |
| (iii) LA-calibrated | A (0.108 / 0.135 / 0.224) | 4,586 | 8,579 | 15,621 | 8,208 | 683 | 2,185 | 9,879 | 4,776 | 8,402 |
| (i) as used | A (0.114 / 0.132 / 0.251) | 4,455 | 9,112 | 18,019 | 8,208 | 753 | 2,350 | 10,835 | 5,008 | 8,912 |

Additional permits over 2027–2031 on a 645-permit baseline; vacant-lot and Minneapolis rules and the 0.2345 floor in every row.

## Deviations and limits

1. The G3F-2 test scores 5 configurations on the same 7 states. A's 0.113 is the best of those, so it is optimistic; the A-against-B gap is within noise (section 2).
2. "C" is the best of three covariate terms, picked on the same score; even so it loses.
3. The vacant-lot factor 0.951 is one median over 17 cities, applied to every non-California series, whatever the state's own share.
4. California-only regression: activity groups are kept as published (set on 2017–2019 counts); only the 2023–2025 counts change.
5. The Madison-like alternative is computed directly (Madison's rate on the observed path each year minus its current-law rate), not through the engine, because the engine has one ramp per path.
6. Not changed: `POOLED_MODEL.md`, `adu_model_params.json` paths (only the floor moved into one place), the adopted reference outputs. To adopt option (ii) the conductor would: set `madison_floor.in_use` to the revision, write the option-(ii) configuration-A per-area levels into the engine inputs, and update the path ramps and labels.

## Reproduce

```
uv run python scripts/run_pooled_revision.py     # about 45 seconds; writes reference/pooled_revision_*.csv
uv run --with pytest python -m pytest -q          # includes tests/test_pooled_revision.py
```

Code: [`pooled_revision.py`](../../missing_middleware/comparison/pooled_revision.py), [`params.py`](../../missing_middleware/model/params.py), [`run_pooled_revision.py`](../../scripts/run_pooled_revision.py); tests [`test_pooled_revision.py`](../../tests/test_pooled_revision.py). Inputs are all local, the same as `run_pooled_regression.py` and `run_ca_mf_lot.py`; no new downloads.

# TOD Wisconsin statewide net: plan (logged before any run, 2026-10-31)

Owner ask (16:11): "permits after reform minus baseline permits without reform, statewide in Wisconsin", using existing models, with fast fit-and-fix rounds. After each run: check for errors and odd outliers, fix the code, rerun.

## Model (existing: round-8 share model, plan items 57–59)

- **Law-on model:** trained on upzoned lots after the reform. **Law-off model:** trained on all other lots before the reform, plus no-reform cities. Fast tool, homes per acre (item 55), 3 seeds.
- Training uses all 9 reform cities plus the 4 no-reform cities. The holdout read is done, so Chicago, Madison and Bellevue may now train.
- **Wisconsin lots:** `wi_lots.parquet` (Milwaukee and Madison: law-area lots plus a ½-mile ring). Built with traits as of 2023; homes built 2019–2024 as homes before.
- **Shares:** each lot's predicted homes ÷ the table's total, law on and law off. Effect share = upzoned lots' share with the law − without.
- **Place total (no reform):** the city's all-housing baseline, 2027–2031, from the shared baseline (`docs/shared/HOUSING_BASELINE.md` central 122,619 statewide). Times the table's share of the city's 2020 homes.
- **Net added homes:**
  - bound A (pure relocation) = 0;
  - bound B (pure addition) = effect share × place total, raw and calibrated (k = 0.18, item 59).
- **Statewide:** Milwaukee + Madison, scaled by the statewide near-stop baseline ÷ the two cities' near-stop baseline (they hold 82% of near-stop homes). Shown on today's 14,464 and on the re-based 17,597.

## Known issue to test in round 1

In training, upzoned lots more than ½ mile from rail or rapid stops were relabelled "upzoned not near transit" and treated as law off (item 48). In Wisconsin, most upzoned lots are near 15-minute bus stops only (Milwaukee 95%, Madison 70% are more than ½ mile from rail or rapid). Two variants:

- **R1a:** every Wisconsin upzoned lot gets law on (bus areas extrapolated).
- **R1b:** only lots within ½ mile of rail or rapid get law on (as in training; a narrower benchmark, plan item 61 option a).

## Checks after each run

Sanity flags (units, policy, out of range), the 20 lots with the largest effect, effect by distance band and stop type, and seed spread. Fixes are logged here before the rerun.

## Comparison

The tool's literature scenarios (171 / 2,509 / 17,148) are shown alongside. No tool number changes without the owner.

## Round log

**Round 1 (both variants, one seed).** Coding errors fixed before it ran:
- the cost lookup was repeated for every one of 193,000 lots (an hour lost);
- a string-times-number error in the Wisconsin rank key (city names now carry "WI ").

Results (bound B, homes over 2027–2031):
- Variant a: raw 8,786, calibrated 1,581.
- Variant b: raw 7,056, calibrated 1,270.

Checks:
- **Law-off share on law-on lots, model vs actual 2019–2024:**
  - Milwaukee: 34.5% vs 24.5% (a); 6.5% vs 3.8% (b).
  - Madison: 22.7% vs 26.1% (a); 12.2% vs 13.0% (b).
  - Reasonable.
- **Raw law-off level:** about 25,000–27,000 homes per city over 5 years, against 5,382 (Milwaukee) and 10,716 (Madison) built 2019–2024 on a 5-year basis. The raw level is 2.5–5× too high. Only shares are used, so this does not enter the result.
- **Outliers (errors):**
  - Milwaukee's airport lot (1,504 acres, 42.945 −87.899);
  - the West Towne Mall lots in Madison (37, 16 and 12 acres; 1,939 homes predicted on one lot in 5 years with no law).
  - Cause: homes per acre times acres, far beyond any training project.
  - Round 2 caps the acres used at the 99th percentile of training lots that built.
- **Not errors:**
  - Lots near rail show negative effects in variant a. In a share model, when most of the city gets the law, lots already allowed lose share to newly upzoned lots.
  - Large vacant upzoned lots in northeast Madison (57 and 40 acres; zoning level 0 before) are plausible greenfield.

**Round 2 (acre cap; 3 seeds × 2 variants).** Acres used are capped at 2.97, the 99th percentile of training lots that built; 2,914 Wisconsin lots are above it. The airport and mall outliers are gone, and the top lots are now 140–340 homes over 5 years on 1–6 acres.

Statewide bound B, homes over 2027–2031:

| Variant | Raw | Calibrated |
| --- | --- | --- |
| a | 8,683–11,505 | 1,563–2,071 |
| b | 7,229–10,754 | 1,301–1,936 |

The seed spread is about ±15% around the middle.

New finding, a coding mismatch: training labels upzoned industrial-use lots "upzoned_from_industrial", but the Wisconsin table called them plain "upzoned" (222 lots). Round 3 relabels them and adds the standing sanity flags.

**Round 3 (industrial label; standing checks; 3 seeds × 2 variants): clean round.** No new errors. Every flag and outlier is explained:

| Check | Finding | Explained / verified |
| --- | --- | --- |
| Industrial relabel (222 lots) | Results identical to round 2 to the home | The model never splits on that label; the training and Wisconsin rows are otherwise unchanged |
| Acres > 500, width > 2,000 m (1 Milwaukee lot) | Milwaukee's airport | Capped since round 2; it contributes at most 2.97 acres' worth |
| Distance > 5 km to rail or rapid (64,290 Milwaukee and 5,527 Madison lots) | True distances: Milwaukee's rail and rapid lines are the downtown streetcar and one east–west bus rapid line | Same in the training no-reform rows (Milwaukee placebo 61,894) |
| 95% (Milwaukee) and 70% (Madison) of upzoned lots beyond 805 m | The Wisconsin law includes 15-minute bus stops | Variant b runs the training rule |
| Share upzoned within ½ mile above training's 99th percentile for 38% of Milwaukee lots (median 0.71 vs top 0.77) | The law upzones most of the city | Trees cannot extrapolate: values above the top are read as the top. Scale is not a blocker (item 61) |
| Top lots by effect | 140–340 homes on 1–6 acres, mostly lots where the law first allows homes (zoning level 0) near downtown Milwaukee and on Madison's east side | Plausible project sizes |

### Result: net added homes statewide, 2027–2031

| Bound | Variant a (all upzoned lots) | Variant b (rail/rapid ½ mile only) |
| --- | --- | --- |
| A, pure relocation | 0 | 0 |
| B, pure addition, calibrated (k = 0.18) | 1,563–2,071 | 1,301–1,936 |
| B raw (uncalibrated sensitivity) | 8,683–11,505 | 7,229–10,754 |

The ranges are the spread over 3 seeds. Milwaukee and Madison are modelled; the rest of the state is scaled by the near-stop baseline (×1.147 today, ×1.143 re-based), which is an assumption. The re-based baseline barely changes the result, because the shares, not the baseline, carry the effect.

For comparison, the tool's literature scenarios are 171 / 2,509 / 17,148.

**Round 4 (audit E1: calibration measured on this model).** K was hard-coded at 0.18 from item 59, which used the 6-city round-8 model and a different uplift. It is now measured on the current model with the uplift bound B uses: law-on share minus law-off share on upzoned lots. Each of the 9 reform cities is left out in turn, and K = sum of actual share changes ÷ sum of model uplifts. One coding error was fixed before the run: a path-join error when saving the K table.

| Seed | K (pooled, 9 cities) |
| --- | ---: |
| 20261031 | 0.116 |
| 7 | 0.110 |
| 11 | 0.120 |

Per city, main seed (`reference/tod_wi_net_round4a_k.csv`):

| City | Model uplift | Actual change in share | Ratio |
| --- | ---: | ---: | ---: |
| Bellevue | 0.542 | 0.000 | 0.00 |
| Charlotte | 0.612 | 0.259 | 0.42 |
| Chicago | 0.055 | 0.060 | 1.09 |
| Los Angeles | 0.522 | −0.268 | −0.51 |
| Madison | 0.127 | 0.070 | 0.55 |
| New York | 0.376 | 0.338 | 0.90 |
| Philadelphia | 0.168 | 0.121 | 0.72 |
| Saint Paul | 0.530 | −0.205 | −0.39 |
| Seattle | 0.138 | −0.018 | −0.13 |

Outliers explained:
- **Los Angeles and Saint Paul:** the share falls because the upzoned lots held nearly all of the before-window homes (98.8% and 100%). Saint Paul has one before year and 50 homes. Los Angeles's comparison land built almost nothing before; Cornfield was checked in item 60.
- **Bellevue:** almost nothing was built (as in the holdout read).

These are thin-data cities, not coding errors, and they pull the pooled K down.

**K is not well pinned down.** These are sensitivities only; the main stays pooled over all 9 cities (no cities dropped, owner item 37):

| K | Value |
| --- | ---: |
| Median of city ratios | 0.42 |
| Pooled without the three thin cities | 0.56 |

**Statewide net added homes, 2027–2031 (round 4):**

| Bound | Variant a (all upzoned lots) | Variant b (rail/rapid ½ mile only) |
| --- | --- | --- |
| A, pure relocation | 0 | 0 |
| B calibrated, K measured (0.110–0.120) | 1,008–1,382 | 839–1,292 |
| B, K = 0.42 (median ratio; sensitivity) | about 3,650–4,830 | about 3,040–4,520 |
| B raw | 8,683–11,505 | 7,229–10,754 |

**Write-up notes (audit):**
- The 2.97-acre cap may understate large greenfield lots, such as the 57- and 40-acre lots in northeast Madison.
- Madison now trains the model and is also a forecast target, so it no longer works as a test.
- The raw law-off level is 2.5–5× too high. It is not used; only shares are.

**Central value:** this is the owner's call, with the reason written beside it. The tool is not changed (owner, 17:44: finish the rounds first).

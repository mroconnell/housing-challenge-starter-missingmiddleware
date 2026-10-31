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

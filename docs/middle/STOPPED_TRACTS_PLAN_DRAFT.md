# Middle housing: "stopped" middle-housing places (Test 8, plan DRAFT)

Drafted 2026-11-13 from Ryan's idea (thread, 2026-11-13): tracts with many 2–4 unit homes from before about 1980, and almost
none since, are likely places that once allowed small buildings and then banned them. Do places like that respond
more, or less, when a state law makes 2–4 homes legal again?

**Status: draft, not locked.** This test was added after the Test 1 results were seen. It is labelled **post hoc**
wherever it is reported. It states no expected result. The audit reviews it before it runs. It does not change the
tool's range; any tool use needs Ryan's OK.

**What has and has not been seen.** Seen: Test 1 results by state (four-state and per state). Not seen: any tract
counts, any place score, or any split of places by score.

## The question

In Oregon, California, Maine and Vermont, did places with more "stopped" middle housing gain more (or fewer) homes in
2–4 unit buildings after the law than places with less, each against similar places without a law?

## Data (all public domain, Census Bureau; user agent "missing-middleware-research/1.0 (public data)")

| Piece | Source | Why this one |
| --- | --- | --- |
| 2–4 unit homes by decade built, per tract | ACS 2019–2023 5-year, table B25127 (occupied homes; owner plus renter) | Every tract in every state; one consistent source for law and comparison states |
| 2–4 unit homes standing in 2000, per tract | 2000 Census SF3, table H030 (rows 4 and 5: 2 units, 3 or 4 units; all homes) | Survival check: what stood then vs what ACS counts as built before 2000 now |
| 2000 → 2010 → 2020 tract links | Census tract relationship files | Puts 2000 counts on 2020 tracts (split by land area share) |
| Tract → place | 2020 block assignment files plus 2020 block housing-unit counts (PL 94-171, H1) | Tracts cross place lines; each tract's homes go to places by its blocks' housing units |
| Permits, comparisons, windows | Exactly as Test 1 (locked plan) | Same outcome M2, same places, same windows, same matching |

- 1990 tract data are not on the Census API; 1970 and 1980 need NHGIS (account, own terms). Left out.
- ACS counts occupied homes only and only buildings still standing. The 2000 check measures how much was lost.

## Definitions (fixed now)

- **Old 2–4 homes:** 2–4 unit homes built before 1980 (B25127 bands 1939 or earlier, 1940–59, 1960–79).
- **New 2–4 homes:** 2–4 unit homes built 1980–2019 (bands 1980–99, 2000–19). 2020+ is left out (it overlaps the
  after windows).
- **Stopped tract:** old 2–4 homes are at least **10%** of the tract's occupied homes, and new 2–4 homes are at most
  **10%** of its old 2–4 homes.
- **Place score:** share of the place's occupied homes (2020 blocks, weighted) that sit in stopped tracts.
- **High / low places:** within each law state, places at or above the state's median score that are above 0 are
  "high"; places with score 0 are "low"; the rest are "middle" and are reported but not in the main contrast. If a state
  has fewer than 10 high or 10 low places, it is left out of the contrast and this is reported.

## The estimate

- For each law state, run Test 1's state statistic (M2 rate difference, per 1,000 single-family homes per year,
  same windows and same ½–2× population matching) twice: once on its high places, once on its low places, each
  against the same comparison pool.
- **Contrast** = high minus low, averaged over the law states that pass the size rule (equal weights, as Test 1).
- **Second unit:** the same with Test 1's log rate ratio.

## Inference and reading rules (symmetric; fixed now)

- **Fake law states:** the same contrast in 10,000 sets of 4 fake law states drawn from Test 1's 34 screened states,
  each place scored the same way, seed 20261113.
- **90% range** = [real − fake 95th percentile, real − fake 5th percentile] of the fake contrasts (as Test 1).
- **Reading:**
  - real contrast above the fake 95th percentile: stopped places gained more 2–4 unit homes after the law;
  - below the fake 5th percentile: stopped places gained fewer;
  - otherwise: we do not know. Never read as "no difference"; the width is always reported.
- **Power first:** before the real contrast is computed, the fake contrasts' spread on 2012–2018 windows (Test 1's
  fake windows) is reported as the smallest detectable contrast. The real run happens either way.

## Checks (reported beside, never promoted)

- **Survival:** per state, 2–4 unit homes standing in 2000 (H030) vs ACS 2–4 homes built before 2000, on 2020 tracts.
  Reported as a loss share; tracts with a loss over 50% are flagged.
- **Thresholds:** 5% and 20% in place of each 10% (four variants).
- **Pre-trend:** the same contrast on Test 1's fake reform years (Test 4 windows), law states only.
- **Size:** the contrast with places matched on population tercile within state.

## Backdoors this does not close

- Old, dense places differ in many ways (age, transit, prices). A difference is not only zoning.
- "Stopped" can also mean built out (no land), not banned.
- Census permits are by place, so tract signals are averaged.

## Outputs

`scripts/middle_test8_stopped.py`; `reference/middle_test8_tract_scores.csv`, `reference/middle_test8_place_scores.csv`,
`reference/middle_test8_summary.csv`; results in `docs/middle/TEST8_RESULTS.md`. Raw downloads under
`data/raw/middle_tracts/` (gitignored).

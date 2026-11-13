# Middle housing: "stopped" middle-housing places (Test 8, plan LOCKED 2026-11-13)

Drafted 2026-11-13 from Ryan's idea (thread, 2026-11-13): tracts with many 2–4 unit homes from before about 1980, and almost
none since, are likely places that once allowed small buildings and then banned them. Do places like that respond
more, or less, when a state law makes 2–4 homes legal again?

**Status: draft v2 (audit fixes 1–6 and the smaller items made; audit review
`audit/middle_test8_stopped_tracts_plan_review_2026-11-13.md`). Locks on this commit per the audit; no second review.**
Previously: draft, not locked. This test was added after the Test 1 results were seen. It is labelled **post hoc**
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
| 2–4 unit homes by decade built, per tract | ACS 2020–2024 5-year, table B25127 (occupied homes; owner plus renter), from the Census table-based summary file (same vintage as Test 1's denominator) | Every tract in every state; one consistent source for law and comparison states |
| 2–4 unit homes standing in 2000, per tract | 2000 Census SF3, table H032 (occupied homes by units in structure: owner and renter, 2 units and 3 or 4 units), to match ACS occupied homes (audit) | Survival check: what stood then vs what ACS counts as built before 2000 now |
| 2000 → 2010 → 2020 tract links | Census tract relationship files | Puts 2000 counts on 2020 tracts: 2000→2010 by housing-unit share (audit); 2010→2020 by land-area share (the 2020 file has no housing counts) |
| Tract → place | 2020 block assignment files (incorporated place and county subdivision) plus 2020 block housing-unit counts (PL 94-171, H1) | Tracts cross place lines; each tract's homes go to places by its blocks' housing units. Census permit places in New Jersey, New York, Pennsylvania, Maine and Vermont are towns and townships (county subdivisions), so both links are kept and matched to each permit place the way Test 1 names it |
| Permits, comparisons, windows | Exactly as Test 1 (locked plan) | Same outcome M2, same places, same windows, same matching |

- 1990 tract data are not on the Census API; 1970 and 1980 need NHGIS (account, own terms). Left out.
- ACS counts occupied homes only and only buildings still standing. The 2000 check measures how much was lost.

## Definitions (fixed now)

- **Old 2–4 homes:** 2–4 unit homes built before 1980 (B25127 bands 1939 or earlier, 1940–59, 1960–79).
- **New 2–4 homes:** 2–4 unit homes built 1980–2019 (bands 1980–99, 2000–19). 2020+ is left out (it overlaps the
  after windows).
- **Denominator:** occupied homes built before 2020 (B25127 total less the "built 2020 or later" bands), because
  homes built in 2020 or later overlap the after windows (audit fix 4). B25127 band labels are read from the Census
  API group file and checked before any scoring.
- **Stopped tract:** old 2–4 homes are at least **10%** of the tract's occupied homes built before 2020, and new 2–4 homes are at most
  **10%** of its old 2–4 homes.
- **Place score:** share of the place's 2020 housing units (blocks, PL 94-171 H1) that sit in stopped tracts.
- **High / low places:** within each state, the median is taken over places with a score above 0. Places at or above
  that median are "high"; places with score 0 are "low"; the rest are "middle" and are reported but not in the main
  contrast. If a state has fewer than 10 high or 10 low places, it is left out of the contrast and this is reported.
- **Conventions, not evidence:** the 1980 cut, the 10% / 10% stopped rule, the median split and the 10-place minimum are
  conventions chosen before any count was read (audit fix 2). The threshold variants below test the 10% rules.
- **Permit units (audit fix 3):** blocks go to each permit unit's own geography, keyed exactly as Test 1 keys it:
  incorporated places, and county subdivisions (towns and townships) where Census permits are filed by town (Maine,
  Vermont, New Jersey, New York, Pennsylvania and others). This applies to law, comparison and fake states alike.

## The estimate

- For each law state, run Test 1's state statistic (M2, same windows and same ½–2× population matching) twice: once on
  its high places, once on its low places, each against the same comparison pool.
- **Contrast** = high minus low, averaged over the law states that pass the size rule (equal weights, as Test 1).
- **Order of units (audit fix 1, as Test 1):** the log rate ratio is primary; the rate difference per 1,000
  single-family homes per year is second.
- **Unmatched share:** the share of single-family homes with no comparison place at ½–2× size is reported for each
  group (high and low) in each state (California's largest cities are the known case).

## Inference and reading rules (symmetric; fixed now)

- **Fake law states:** the same contrast in 10,000 sets of 4 fake law states drawn from Test 1's 34 screened states,
  each place scored the same way, seed 20261113.
- **Size rule in the fakes (audit fix 5):** the 10 high / 10 low rule is applied to each fake state. If a real state
  drops out, its slot is dropped from every fake set too. How often a fake state fails the rule is reported.
- **90% range** = [real − fake 95th percentile, real − fake 5th percentile] of the fake contrasts (as Test 1).
- **Point (audit fix 6):** real contrast minus the fake median, shown next to the range; the fake median is reported.
- **Reading:**
  - real contrast above the fake 95th percentile: stopped places gained more 2–4 unit homes after the law;
  - below the fake 5th percentile: stopped places gained fewer;
  - otherwise: we do not know. Never read as "no difference"; the width is always reported.
- **Power first:** before the real contrast is computed, the fake contrasts' spread on 2012–2018 windows (Test 1's
  fake windows) is reported as the smallest detectable contrast, 2.486 × the standard deviation of the fake contrasts
  (the power check's formula). The real run happens either way.

## Checks (reported beside, never promoted)

- **Survival:** per state, occupied 2–4 unit homes in 2000 (H032) vs ACS 2–4 homes built before 2000, on 2020 tracts.
  Reported as a loss share; tracts with a loss over 50% are flagged.
- **Thresholds:** 5% and 20% in place of each 10% (four variants).
- **Pre-trend:** the same contrast on Test 1's fake reform years (Test 4 windows), law states only.
- **Size:** the contrast with places matched on population tercile within state.

## Backdoors this does not close

- Old, dense places differ in many ways (age, transit, prices). A difference is not only zoning.
- "Stopped" can also mean built out (no land), not banned.
- Census permits are by place, so tract signals are averaged.
- Neighbouring places share tracts, so their scores are not independent. The fake-state inference keeps whole states
  together, which carries this through.

## Outputs

`scripts/middle_test8_stopped.py`; `reference/middle_test8_tract_scores.csv`, `reference/middle_test8_place_scores.csv`,
`reference/middle_test8_summary.csv`; results in `docs/middle/TEST8_RESULTS.md`. Raw downloads under
`data/raw/middle_tracts/` (gitignored).

## Changes before lock

- 2026-11-13: ACS vintage set to 2020–2024 (table-based summary file; the API needs a key per call); county-subdivision link added for the five states whose permit places are towns. No tract counts read yet.

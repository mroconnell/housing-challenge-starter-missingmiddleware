# Test 8 results: places with "stopped" middle housing (post hoc)

Run 2026-11-14 by the [locked plan](TEST8_PLAN_LOCKED.md). **Post hoc:** added after Test 1's results. Script
`scripts/middle_test8_stopped.py`; outputs `reference/middle_test8_summary.csv`, `_place_scores.csv`,
`_tract_scores.csv`, `_survival.csv`, `_fake_state_rule.csv`. Download check: [TEST8_DOWNLOAD_CHECK.md](TEST8_DOWNLOAD_CHECK.md).

## Answer

**We do not know.** The test could only run in California, and its range is very wide.

- **Only California passed the size rule** (at least 10 "high" and 10 "low" places with full reporting). Oregon, Maine
  and Vermont have too few places with any stopped tract: 14 of 132, 25 of 388 and 24 of 204 permit places score above
  0, so their high half falls under 10 once the reporting rule is applied. Their slots were dropped from the fakes too.
- **79% of fake states also failed the size rule** (main thresholds). With California's windows, only 7 fake states
  pass: Illinois, Michigan, New Jersey, New York, Ohio, Pennsylvania and Wisconsin, none in the West (audit). The
  10,000 sets therefore draw from 7 numbers: the percentile moves in steps of about 14 points (57 = 4 of 7), and the
  range ends sit near the smallest and largest of 7 values.

| Version | States | High / low places (CA) | Point, log ratio (real − fake median) | 90% range, log | Same as % | Percentile | Reading |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| Main (10% / 10%) | California | 30 / 165 | +0.22 | −1.68 to +1.04 | −81% to +184% | 57 | we do not know |
| Old 5% | California | 50 / 125 | +0.75 | −1.16 to +1.36 | −69% to +290% | 73 | we do not know |
| Old 20% | none pass | — | — | — | — | — | not run |
| New 5% | California | 20 / 184 | −0.58 | −2.32 to +0.42 | −90% to +52% | 42 | we do not know |
| New 20% | California | 37 / 151 | +0.23 | −0.43 to +1.58 | −35% to +383% | 75 | we do not know |

- **Rate difference (second unit), main:** real −0.19 extra 2–4 unit homes per 1,000 single-family homes per year,
  high minus low; point −0.15 (range −0.75 to −0.03). The rate range excludes 0 while the log-ratio range (primary)
  does not; by the plan the log ratio governs. Both ranges rest on the same 7 fake values (audit). With one state and 7 fake states, neither is read as a finding.
- **Unmatched homes (California):** 59% of single-family homes in the high group had no comparison place at ½–2× their
  size (big older cities); 0% in the low group. The high group's comparison is thin.

## Checks

- **Power (fake years, all four slots):** smallest detectable log contrast 0.46 (2.486 × SD 0.18). With only
  California, the realised spread is far wider (SD 0.83, detectable 2.05).
- **Pre-trend (California on fake years 2012–14 vs 2016–18):** log −0.03 against the fake median, range −0.65 to +0.70,
  percentile 43. No sign of a pre-existing gap.
- **Size terciles:** only the largest third of California places passes the size rule: point +0.46, range −1.44 to
  +0.75, percentile 68.
- **Survival (2000 vs now):** across the 38 states, ACS counts 14% fewer occupied 2–4 unit homes built before 2000 than
  the 2000 Census counted as occupied (California 5%, Oregon 1%, Maine 12%, Vermont 18%). This mixes demolition,
  conversion, vacancy and survey noise. Many single tracts differ by over half, mostly from ACS sampling noise.

## What this means

- The idea is reasonable, but these four laws cannot test it: three of the states are small-town states with few
  stopped places.
- California alone gives a range from a large fall to a large rise.
- Nothing here changes the tool.

## Disclosures

- Post hoc (added after Test 1). Town links by DHC tract parts were logged after lock, before any count was read.
- 36 of 16,017 permit units could not be linked to tracts (4 in law states, all small Maine and Vermont towns). The audit's housing-total checks (towns, blocks, New York tracts) ran after these results were computed; all passed except 14 Suffolk County, NY tracts with no ACS row (fake states only). See the download check.
- A bug in the size-tercile check stopped the first run before any result was printed; fixed (rank-based terciles) and
  rerun. A tract-code padding bug in the survival check (2000 codes without the "00" suffix) was found from impossible
  results and fixed; it did not touch the main test.

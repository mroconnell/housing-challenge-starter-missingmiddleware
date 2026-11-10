# How many extra 5–6 unit homes might Wisconsin see? (arithmetic, not a test)

Run 2026-11-09 at Ryan's request, after Test 1. This is not part of the locked plan. It is labelled **post hoc** and is arithmetic on Test 1's estimate, not a new test.

## Share of 5–6 unit homes within 2–6 unit homes, in the four law states

| Source | Years | 5–6 unit homes | 2–4 unit homes | 5–6 share of 2–6 |
| --- | --- | ---: | ---: | ---: |
| California progress reports (projects of exactly 5 or 6 homes in the "5+" category) | 2018–2021 | 7,318 | 20,169 | 26.6% |
| California progress reports | 2022 | 1,957 | 5,015 | 28.1% |
| California progress reports | 2023–2025 | 5,844 | 16,403 | 26.3% |
| Census, lower bound (only place-years where every 5+ building must have 5 or 6 units: units − 5 × buildings ≤ 1) | 2018–2025 | | | |
| Oregon | | 299 | 5,367 | 5.3% |
| California | | 2,168 | 33,898 | 6.0% |
| Maine | | 473 | 2,372 | 16.6% |
| Vermont | | 409 | 1,210 | 25.3% |
| All four states | | 3,349 | 42,847 | 7.2% |
| *Wisconsin, for reference* | | 187 | 11,984 | 1.5% |

- **The Census figures are lower bounds.** They miss every place-year that mixes 5–6 unit buildings with larger ones.
- **The California progress-report figures may run high.** A row is a project, and a 6-home row can be part of a bigger building.
- **Working range for the share: about 7% to 27%.** That means 5–6 unit homes add about 0.08 to 0.36 homes for every home in 2–4 unit buildings.

## Applied to Test 1's estimate for Wisconsin

- **Test 1 (2–4 unit homes):** +0.23 per 1,000 single-family homes per year (90% range −0.07 to +0.65). Read: we do not know.
- **Applied to Wisconsin:** 1,839,569 single-family homes gives about +420 homes a year in 2–4 unit buildings (range −130 to +1,200).

| | Per year | Over 5 years |
| --- | --- | --- |
| Extra 5–6 unit homes at the central estimate | about 30 to 150 | about 160 to 760 |
| Same, using Wisconsin's own lower-bound share (1.5%, factor 0.015) | about 6 | about 30 |
| As buildings (about 5.5 homes each) | about 6 to 28 | about 30 to 140 |
| At the top of Test 1's range (+1,200 a year) | up to about 430 homes (about 80 buildings) | up to about 2,200 homes |
| At the bottom of Test 1's range | about −10 to −45 homes | |

**Assumptions:**
- New middle housing would split between 2–4 and 5–6 unit buildings the way past building did.
- Test 1's 2–4 unit estimate is the base. Test 1 itself reads "we do not know".
- Census 2–4 counts miss townhouses (Test 6), which this arithmetic does not add back.

## 90% range (added 2026-11-10 at Ryan's request; post hoc)

Code: [`scripts/middle_five_six_range.py`](../../scripts/middle_five_six_range.py). It uses 20,000 draws of Test 1's effect (four states, M2), taken as the real result minus fake-set noise. Each draw is combined with a share of 5–6 unit homes drawn evenly between 7.2% and 26.6%.

| Share range | Extra 5–6 unit homes in Wisconsin, 2027–2031: 5th percentile | Median | 95th percentile |
| --- | ---: | ---: | ---: |
| Law states, 7.2%–26.6% | about −150 | about +390 | about +1,400 |
| Including Wisconsin's own 1.5% | about −100 | about +280 | about +1,300 |

**Correction:** the earlier upper figure (+2,960) wrongly scaled 5–6 unit homes by the townhouse factor. Townhouses are one-unit buildings and do not change the 5–6 share.

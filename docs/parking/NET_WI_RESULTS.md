# Parking: Wisconsin permits after reform minus without reform, 2027–2031, results

Written 2026-10-31 by the parking conductor. Plan and every round's fixes: [NET_WI_PLAN.md](NET_WI_PLAN.md). Scripts: `scripts/run_parking_net_wi.py`, `scripts/check_parking_net_wi.py`, and the no-reform model `scripts/run_parking_no_reform.py`. Final round: net round 7, on no-reform round 6 data. Files: `reference/parking_net_wi_*_r7.csv`, `reference/parking_net_wi_audit_checks_r7.csv`.

## Answer

A statewide parking repeal adds about **0 homes** over 2027–2031, net of the no-reform baseline (122,619). Both routes agree on the central figure.

| Route | Lower | Central | Upper | What the range is |
| --- | ---: | ---: | ---: | --- |
| A: repeal places vs similar places (the tool) | 0 | 0 | 19,937 | Placebo-based high end; the tool shows no negative |
| B: no-reform model with a dated repeal trait (boosted trees) | −4,171 | 0 | 0 | 5th, 50th and 95th percentile of 105 fits (5 seeds × 21 resamples of reform places) |
| B, fake repeal (noise floor) | −9,316 | −3,308 | 0 | 5 seeds |

- **Route B finds no measurable effect.** In 56% of fits the trees ignore the repeal trait entirely and give exactly 0. The mean is −1,064. The real range sits inside the fake one.
- **Route B is thin:** 28 dated, apartment-scale repeal places (58 place-origin rows, outside Wisconsin).
- **The regression version of route B is not used.** Its net (median −23,599) is no further from 0 than its fake-repeal net (−31,903 to +10,795).

## Clean-round checks (round 7)

- **No coding errors.** The fake-reform draws repeat exactly under a different Python hash seed (round 4 check).
- **Homes vary by origin:** 98.4% of 9,663 places.
- **Homes match their source.** For Madison, homes equal the ACS release ending 2016 and 2019 exactly. Origin 2025 adds exactly the 2025 permits (3,383) to ACS 2020–2024.
- **There is no jump at 2021→2022** (0 of 9,235 places).
- **2019→2020 jump:** 5,115 of 8,882 places change more than 5% (median +3.1%). This is expected: the source switches from the 2015–2019 ACS to the 2020–2024 ACS, which are five years apart. The largest jumps are boom towns: Fulshear +229%, Timnath +207%, Celina +203%. No 2020–2024 origin is used in fitting or scoring; only 2025 is used, for the forecast.

## Outliers, explained and verified

- **San Francisco,** the largest held-out miss in homes: actual 1,689 a year against a same pace of 4,590. This is SF's real post-2018 drop in permits.
- **Ecorse, MI,** the largest miss by log error: predicted 11 a year, actual 0. It permitted 198 in 2017, 59 in 2019, then 0 every year through 2025.
- **Hartford, CT:** predicted 98 a year, actual 7. It permits 5–11 a year, with one spike of 141 in 2023.
- **Fake repeal, seed 20261034:** its fake places grew faster. Home-weighted, they gained 4.23 permits per 1,000 homes per year against 2.47 for the rest, led by Hardeeville, SC, a real boom (209 permits in 2016, 1,718 in 2025). In the other seeds the fake places grew more slowly, and the trees follow that sign.

## Data problems found and fixed along the way

1. The state scale was 5× too large (round 1).
2. The fake repeal was on at every origin (round 1).
3. Fake draws were not reproducible (round 3).
4. Homes at the origin used the outcome years' own permits (the audit's leak).
5. The permit file's population is unreliable. It is the census count and is sometimes wrong (Milwaukee 34,451 until 2021). Homes now come from the ACS release ending at each origin, fetched for every state.

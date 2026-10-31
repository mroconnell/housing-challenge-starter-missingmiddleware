# Parking improvement loop, round 2: results

Written 2026-10-31 by the parking conductor. Plan and the changes made before computing: [IMPROVE_R2_PLAN.md](IMPROVE_R2_PLAN.md).

## Answer

- **The headline stays.** The high end is still 19,937 homes over 2027–2031 (+1.49 permits per 1,000 existing homes per year).
- **Why:** under the rule set in advance, a new high end replaces it only if every repeal place has at least 20 placebo stand-ins. In both new versions, San Jose and Austin had fewer than 20.
- **V7 and V7s join the sensitivity cases.** Both are above the headline, as every cleaned-data version has been.

## Results

The unit is permits per 1,000 existing homes per year. The average is weighted by homes × after-years over 73 repeal places.

| Version | Real average | 90% resampling range | Placebo 5th / 50th / 95th percentile | High end | Five-year homes, 2027–2031 | Fewest stand-ins |
| --- | ---: | --- | --- | ---: | ---: | --- |
| Headline (current) | −1.10 | −3.59 to 1.53 | – | +1.49 | 19,937 | – |
| V6 (any reform disqualifies) | −0.28 | −3.00 to 2.85 | – | – | 49,712 | 9 places under 20 |
| V6u (undated kept) | −0.83 | −3.58 to 2.02 | – | – | 29,843 | San Jose 19 |
| **V7 (apartment-scale reforms only)** | −0.40 | −3.50 to 2.82 | −2.54 / −0.06 / 2.52 | +2.18 | 29,307 | San Jose 18, Austin 19 |
| **V7s (V7 plus CA, OR and WA state laws)** | −0.53 | −3.60 to 2.64 | −2.50 / 0.01 / 2.60 | +2.06 | 27,671 | San Jose 17, Austin 18 |

- **Share of placebo sets at or below the real average:** 0.41 (V7), 0.36 (V7s). The real repeals look like ordinary places.
- **Comparison pools (median places):** 28 (V7), 68 (V7s).
- **Placebo places:** 8,715 (V7), 35,375 (V7s). V7s has more because the state laws free the pools: its places are excluded only after 2023/2024, so more of them qualify for the earlier windows.
- **Flags:** in each, 2 real places have fewer than 20 stand-ins.

## Reading

- **The central estimate is still about zero** under every cleaning: the real average is between −1.10 and −0.28, inside the noise.
- **The high end depends on the cleaning.** It ranges from 19,937 to 49,712 homes. The two best-founded cleanings (V7, V7s) give about 27,700–29,300.
- **Proposal to Ryan** (not applied): the rule keeps 19,937 because two big cities are 1–3 stand-ins short. If Ryan prefers the better-cleaned data, V7s's 27,671 is the candidate.

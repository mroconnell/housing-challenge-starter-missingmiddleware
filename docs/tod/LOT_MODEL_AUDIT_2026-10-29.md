# Lot model: independent methodology audit

Written 2026-10-29 at the owner's request ("examine every step of our methodology to find all the mistakes of this nature"). A separate reviewer, told only the mistakes already fixed (lot plan items 12, 14, 15, 18, 23, 24), read the code and data read-only and reported the findings below. Fixes are in [LOT_MODEL_PLAN.md](LOT_MODEL_PLAN.md) item 25.

## Confirmed

| # | Mistake | Size | Fix (item 25) |
| --- | --- | --- | --- |
| 1 | The causal forest only sees the rules before; it never sees how big the upzoning is | Median relative gain on upzoned lots: Wisconsin +3.4, training +0.5 | Upzoned forest fitted and predicted on the rules after |
| 2 | "Use" means zoning class in training, land-use class in Wisconsin | "Residential": training mostly New York only; Wisconsin 93–96% of upzoned lots | Use traits dropped from the causal forest |
| 3 | Madison's Wisconsin lots share duplicate-lot keys with Madison's training lots | 8,803 of 37,823 Wisconsin Madison upzoned lots halved; matching training rows halved | Keys and within-city ranks kept apart |
| 4 | Some reforms are scored with almost no comparison land | Greenpoint–Williamsburg: 0.1 comparison acres vs 175.6 upzoned; its 3,919 homes are 39% of New York's actual | Minimum comparison land: 25% of upzoned acres, else the city's other comparison land, flagged |
| 5 | Construction cost in each year's dollars; rent in 2024 dollars | Rent-to-cost about ×1.6 too high for New York 2005 | Cost converted to 2024 dollars with the same price index |
| 6 | Tract census traits and 2010 homes dated after some reforms | 38,020 New York lots (2003–2008) and Bellevue (2009) | Flagged ("traits after reform"); a check run without those reforms |
| 7 | Wisconsin stop traits count 15-minute bus; training counts rail and rapid only | Median stops within 1 mile: Milwaukee 61 vs training 6–29 | Distance and stop traits on rail and rapid only, in both |
| 8 | Missing values filled with medians over all rows, including holdouts and Wisconsin | about 180,000 training lots' fill value moves when Wisconsin is added | Fill values from training rows only, frozen for Wisconsin |

## Suspected

| # | Issue | Handling |
| --- | --- | --- |
| 9 | Homes on lot: training = 2010 block homes shared by area; Wisconsin = actual homes on the lot | Wisconsin switched to the same block-share rule (2020 blocks) |
| 10 | Madison's after years include the reform year | Kept, as in the pre-registered Madison test; noted |
| 11 | Milwaukee building-before probably too low (4,501 homes 2019–2024 vs Madison 12,859) | Land-use filter widened to any lot with homes; condos without own outline remain a known gap |
| 12 | Wisconsin comparison lots measured from the law area, not from stops | Affects only neighbourhood-share traits; noted |
| 13 | Wisconsin upzones about 168,000 lots, training about 21,000 | Per-lot effects reported by group; a check that lots with tiny gains get near-zero effects |

## Checked and fine

- Rare-group pooling: adding Wisconsin changes no group's status.
- No lot is upzoned in one reform and a comparison lot in another.
- The 5-year basis gives the right year counts in every city.

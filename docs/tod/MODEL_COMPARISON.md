# TOD: comparing the models as possible tool lines (2026-11-01)

For the owner's decision. **No tool number has changed.** Sources: [MODEL_MENU_RESULTS.md](MODEL_MENU_RESULTS.md), [WI_NET_PLAN.md](WI_NET_PLAN.md), [PACE_MODEL_RESULTS.md](PACE_MODEL_RESULTS.md). All figures are Wisconsin, 2027–2031, homes permitted.

## 1. Homes near stops with no reform (baseline)

| Option | Homes | Evidence | Status |
| --- | ---: | --- | --- |
| Tool today: survey pace × share of existing homes near stops | 14,464 | — | Too low: stops get more than their share of new homes (Milwaukee 95% of new vs 68% of homes) |
| **Survey pace, re-based on new-home shares** | **18,322** | Same rule as the parking and statewide central; nests in 122,619 | Audit-recommended central (final) |
| Lot model (random forest, leaf 50, no lot size) | 18,255 | Beats the survey's own "same pace" on held-out cities (0.36 vs 0.55) | Cross-check; agrees within 0.4% |
| "Recent strength continues" side line | 19,605–23,086 | Parking's ×1.07–1.26 | Side line |

## 2. Extra homes from the TOD law

| Option | Extra homes | Evidence | Status |
| --- | ---: | --- | --- |
| Tool: little / typical / strong (literature) | 171 / 2,509 / 17,148 | Published studies | Current lines |
| **Lot models, pure addition, calibrated (bound B)** | **about 500–1,200** (method range 455–1,198; licence-clean causal forest 1,882) | 7 methods + two causal forests (multilevel dropped); no-model benchmark 798; single fits (one left-out calibration each) range from about 30 to 2,500 | Candidate new line |
| Lot models, raw | about 3,000–14,500 | Overstates the shift about fivefold or more on held-out cities | Not a line |

What the lot models can and cannot say:
- **Direction (can):** upzoned lots near transit take a larger share of a city's new homes after a reform.
- **Size of that shift (cannot yet):** no method beats a no-model rule (the other cities' average rise in share). No trait group helps predict it in a new city.
- **Net new homes:** bound B treats every predicted home as new. Our only evidence on relocation is that next-door blocks did not lose building (NET_EFFECT_RESULTS.md: 0 of 10 rings lost building; Chicago's gained). Citywide relocation could not be measured. By the owner's rule (2026-11-01), a 0 floor is not shown, because there is no evidence for it.
- **Why the line rests on the no-model rule:** shuffling the zoning-change traits *improves* the share model on held-out cities (score −0.061; correlation of predicted with actual change 0.25 → 0.33). The models can tell "upzoned or not", but not "bigger upzoning, more homes". So the about-800 line comes from the no-model benchmark (other reform cities' average rise in share). The zoning traits stay in, because they define the reform.
- **A trait for the next baseline round:** 2010 census homes on the lot make the baseline forest slightly better when shuffled (−0.028). This fits the timing issue found in round 2. It does not touch 18,322 or 18,255. Dropping it will be tested next baseline round under the registered rule.

## Possible tool changes for the owner (not made)

1. Replace the TOD baseline 14,464 with **18,322**, and show the forest's 18,255 as a cross-check.
2. Add a **"lot-model" line at about 800 extra homes (range 500–1,200)** next to little / typical / strong. Label it "if every predicted home is new; next-door blocks showed no loss". Adding it beside the scenarios is the safe first step (audit). Replacing "typical" is the owner's call.
3. Keep the literature lines. The lot-model evidence sits between "little" (171) and "typical" (2,509).

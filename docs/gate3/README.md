# Gate 3 Packet (revised): Baseline, Policy Response, and Uncertainty

Revised 2026-10-24 by the conductor after the owner's G3 decisions (AQ-034, AQ-035) and a second independent review. **Status: awaiting owner decision.** The first packet (unadjusted California central of about 6,500) is in git history.

## What this gate decides

Whether the ADU model is defensible enough to demonstrate in the Gate 4 pilot. The mechanics are settled; two decisions remain: **how Wisconsin places are grouped (rule v1 vs v1.1)** and **where to anchor the central scenario**.

## Scenarios as they stand now (rule v1, regression levels)

Additional second homes on single-family lots permitted statewide over 2027–2031, on top of a current-law baseline of about **650**. These are **named scenarios, not statistical intervals** (AQ-035).

| Scenario | What it assumes | Additional |
| --- | --- | --- |
| **No statewide law** (shown separately) | Permissive local rules only, Midwest behavior (Madison 0.18, Minneapolis 0.17 per 1,000 homes a year) | about **600** |
| Lower | Regression, low California draw, slow ramp | about **1,000** |
| Central | Regression point prediction, California restrictive-town ramp | about **2,300** |
| Upper | Regression, high California draw, fast ramp | about **5,900** |

Every total was recomputed independently and matches. The state total depends almost entirely on the homes-weighted with-law rate and the ramp; the regression mainly decides *where* units land.

## What the new evidence shows

| Evidence for a Wisconsin-like market | With-law rate (per 1,000 homes a year) |
| --- | --- |
| Midwest cities, local reform only (Madison, Minneapolis) | about 0.2 |
| Regression, Wisconsin homes-weighted (central / upper) | 0.49 / 1.01 (plateau) |
| **States 1–4 years after a statewide law** (WA, OR, ME, RI, MA, UT, VT) | **about 0.94 median**, actually reached |
| Maine (closest market to Wisconsin, $297k) | 0.98 in year 1 |

Like for like (average rate actually reached over 2027–2031, ramp included), the scenarios run 0.14 / 0.18 / **0.33** / 0.72. The statewide-law states, at about 0.94 in their first years, sit **above even the upper scenario**. The regression under-predicts them more as home values fall (Maine by 4×), because it carries a California home-value slope that the other states do not show and extrapolates it below California's range, where 61% of Wisconsin's homes are.

## Two problems found by the second review

1. **Madison is "active" by construction under rule v1.** Only four Wisconsin places have measured second-home permits, so the "top quarter" of them is a single place, Madison, whatever its rate. The model then predicts Madison would permit 2.5 second homes per 1,000 single-family homes per year under the law, about 14 times the 0.18 per 1,000 per year it actually permitted in 2022–2025. Madison has 53,292 of Wisconsin's 1,839,569 single-family homes (2.9%), but the model gives it 378 of the 2,337 extra permits projected statewide in the central scenario (16%).
2. **The central is likely low.** Averaged over the five forecast years including the slow start, the central scenario reaches 0.33 second-home permits per 1,000 single-family homes per year statewide. The seven states with statewide ADU laws and post-law data reached a median of 0.94 per 1,000 homes per year in their first one to four years, nearly three times the central.

## Owner review: step by step, with my self-assessment

| Step | What you do | What you should see | My result |
| --- | --- | --- | --- |
| 1 | Follow one baseline and one reform calculation | Pleasant Prairie: 6,332 homes, current 0.039 → baseline about 1; with-law rate from the regression for its market and group, times the central ramp | **Pass** (mechanics verified twice) |
| 2 | Check existing activity reduces the change | Each place's addition is its with-law rate minus its current rate; Madison's current 0.18 is subtracted | **Pass mechanically; Madison's with-law rate is the problem (decision R1)** |
| 3 | Source and rationale for the central | Market-adjusted California regression ([CA_REGRESSION.md](CA_REGRESSION.md)) | **Needs revision:** cross-checks put it low (decision R2) |
| 4 | What separates lower and upper | California sampling (bootstrap draws) plus ramps; transfer uncertainty is not in it | **Pass after relabeling as named scenarios** |
| 5 | Historical validation and strongest challenge | California holdout (aggregate −5%); out-of-state cities and states ([OTHER_CITIES.md](OTHER_CITIES.md), [STATEWIDE_STATES.md](STATEWIDE_STATES.md)); Madison vs Sun Prairie | **The out-of-state evidence is now the strongest test and it says "higher"** |
| 6 | Decide | Below | Yours |

## Decisions requested

| ID | Decision | Options | Recommendation | Effect |
| --- | --- | --- | --- | --- |
| R1 | Grouping rule | v1 as is; **v1.1:** the top-quarter ranking may label a place "active" only once at least 20 places in the state have measured permits; until then a measured place with any permits is "middle", a measured place with zero permits is "restrictive", and places with no data are "restrictive". Still one general rule, no per-state cutoff | **v1.1** | Today Madison and Sun Prairie become "middle" (Madison predicted at 1.16 per 1,000 homes per year instead of 2.5); paths about 900 / 2,100 / 5,400 extra permits before R2 |
| R2 | Central anchor | (a) regression as is, about 2,300; **(b) triangulated with-law rate about 0.75 per 1,000 (homes-weighted), about 3,800**; (c) statewide-states level 1.0, about 5,200 | **(b)**, keeping the regression's geographic pattern but scaling its level | Four independent routes land at 3,750–4,050 (regression scaled by its miss on the states and adjusted for measurement; states' median rise over their pre-law rate; California's own places under $400k) |
| R3 | Scenario set | Baseline (current law, nothing changes) about 650 permits; **no statewide law** about 600 extra (every place rises to at least Madison's rate, 0.23 per 1,000 homes per year, through local action only; separate panel); **lower** about 900–1,000 extra (regression at the low end of California's statistical uncertainty, slow Central Valley ramp; the Madison floor sets the rate for about 64% of homes); **central** about 3,800 extra (regression geography, statewide level 0.75 anchored on statewide-law states); **upper** about 5,200–5,900 extra (other statewide-law states' level of about 1.0; the regression's high end lands in the same place) | Adopt | Totals including baseline about 1,250 / 1,600 / 4,450 / 5,850–6,550 |
| R4 | Presentation | Show baseline plus additional (total permits: about 4,450 at the recommended central) beside the additional; round to hundreds; municipal figures as shares, not forecasts | Adopt | Avoids the misreadings the reviewer listed |

## Limitations to state wherever results appear

Results are gross permits for second homes on single-family lots, not completions or net new housing. All with-law rates are transferred from other states, described, not causally estimated; the statewide-law states have at most four post-law years and count some ADUs built with new houses. Group totals are reliable; municipal figures are not forecasts. 239 unzoned towns (4% of homes) are included at their own predicted rate.

## Recommendation

**Adopt R1–R4, then advance to Gate 4.** With v1.1 and the triangulated central, the model is demonstrable: the mechanics are verified, every number traces to a stated assumption, and the out-of-state evidence, not a judgment ratio, sets the level.

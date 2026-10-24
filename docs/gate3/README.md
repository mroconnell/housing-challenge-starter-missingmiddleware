# Gate 3 Packet: Baseline, Policy Response, and Uncertainty

Prepared 2026-10-24 by the conductor. **Status: awaiting owner decision.** Gate 3 is not passed until the owner says so.

## What this gate decides

Whether the ADU model's mechanics and evidence are defensible enough to build the pilot demonstration on (Gate 4): the current-law baseline, the response to a statewide benchmark law, and the lower, central, and upper paths. **The central answer depends almost entirely on one judgment: how much of California's response to transfer to Wisconsin.** That is the main decision below.

## Headline numbers (proposed parameters, not adopted)

Additional second homes on single-family lots permitted statewide over 2027–2031, on top of a current-law baseline of about **650** (range 310–1,280):

| Path | Rate with the law (per 1,000 homes a year) | Model | Five-year additional |
| --- | --- | --- | --- |
| Lower | 0.23 | Madison floor (observed 2022–25 ÷ 0.8) | about **900** |
| Central (as run) | 1.23 | California restrictive places after the 2020 package, unadjusted | about **6,500** |
| Upper (as run) | 3.75 | Owner's ADU-share model | about **23,300** |

These are scenario paths, not statistical confidence intervals. The independent validation agent recomputed every total exactly.

## Artifacts

| What | Where |
| --- | --- |
| California comparison study (pre-registered) | [CA_STUDY_RESULTS.md](CA_STUDY_RESULTS.md); plan [CA_COMPARISON_PLAN.md](CA_COMPARISON_PLAN.md); run `uv run python scripts/run_ca_study.py` |
| Wisconsin current-law baseline | [WI_BASELINE.md](WI_BASELINE.md); run `uv run python scripts/build_wi_baseline.py` |
| Model engine and statewide run | `missing_middleware/model/engine.py`; parameters `reference/adu_model_params.json`; run `uv run python scripts/run_adu_model.py`; results `reference/adu_model_*.csv` |
| Sensitivities | `reference/adu_model_sensitivities.csv` |
| Madison vs Sun Prairie check | `uv run python scripts/check_madison_sun_prairie.py` |

## Owner review: step by step, with my self-assessment

| Step | What you do | What you should see | My result |
| --- | --- | --- | --- |
| 1 | Follow one baseline and one reform calculation with the same inputs | Pleasant Prairie, central path: 6,332 one-unit homes; current rate x = 0.039; baseline 6.332 × 0.039 × 5 ≈ **1.3**; additional 6.332 × (1.23 − 0.039) × ramp sum 3.06 ≈ **23** | **Pass.** Matches the engine output and the reviewer's independent recompute. |
| 2 | Check that existing permissions reduce the change | Under the outcome approach (AQ-028), current production does this, not a rights fraction. Madison (x = 0.183) adds 53.3 × (1.23 − 0.183) × 3.06 ≈ **171**; at x = 0 it would add about 201 | **Pass mechanically, with a concern:** Madison is credited with a sixfold rise (decision G3-2). |
| 3 | Read the source and rationale for the central assumption | 1.23 [0.70–2.01] = California places with zero ADUs before 2020, 2023–25 plateau after the 2020 package ([CA_STUDY_RESULTS.md](CA_STUDY_RESULTS.md)) | **Fail as a Wisconsin central estimate**, in my and the reviewer's judgment: it is an unadjusted California level (see challenge below). |
| 4 | Compare lower and upper paths and what drives the difference | 26-fold spread; the level of y drives nearly all of it; the ramp is second (no ramp: +4,100 on central); spillover and the Madison floor do not bind on central or upper | **Pass**; the drivers are clear. The upper path is not independent of California's levels (its share model ≈ California's all-group plateau × 0.97). |
| 5 | Inspect the historical validation and the strongest challenge | See next sections | **Needs your judgment.** |
| 6 | Decide defensibility or request revision | Decisions below | **Recommend revising the central path before Gate 4** (G3-1). |

## Validation

- **California holdout (20% of jurisdictions, never used for fitting):** the group curve predicted 2020–2025 ADUs within 5% in aggregate (18,391 vs 17,417), but individual places missed by a median 1.07 per 1,000 a year. Group totals are informative; municipal figures are not.
- **Madison vs Sun Prairie (pre-registered Wisconsin check):** Madison's by-right reform is associated with **+0.135 [0.013–0.234]** per 1,000 homes a year relative to Sun Prairie (2022–25 vs 2016–21); placebo pre-trend +0.016, consistent with none. Sun Prairie's tiny counts make it a weak control, so this is mostly Madison's own change (×4.8). It matches the lower path's increment and is about one ninth of the central path's.
- **Back-test:** applied to Madison's 2021 reform, the central path would have predicted about 139 second homes for 2022–25; 39 were observed. The lower path predicts about 29.
- **Wisconsin holdout (7 coded places):** ordinance status predicted the rights group 7 of 7; their rates cannot be tested yet (no public permit records).

## Strongest challenge (independent validation agent)

The central path assumes Wisconsin's first statewide law brings restricted places to 1.23 per 1,000 homes a year. That is the rate California's small inland places reached only after their **third** statewide law, with an ADU industry already formed. One city with a pre-approved-plan program (Lancaster) supplies a third of that group's recent permits; without it the plateau is 0.87 (about 4,500 Wisconsin units). California's lower-cost Central Valley maps to about **1,560** Wisconsin units over five years after its first strong law (2017) and about **5,240** after the full 2020 package (validation agent's calculation). Madison's reform added +0.135, and the central path over-predicts Madison by 3.6×. **The single assumption that matters is the Wisconsin-to-California transfer ratio; everything else tested moves the central total by under ±10%.**

The case for the higher numbers: your view that a statewide law builds a specialized industry a single city cannot (AQ-024), and Madison's provisional 2026 surge (0.97, or 0.30 without the templated program) as early in-state evidence of that mechanism.

## Sensitivities on the central path (five-year additional)

| Change | Total |
| --- | --- |
| As run (1.23) | 6,519 |
| California middle group (2.39) | 13,049 |
| California interval low / high (0.70 / 2.01) | 3,536 / 10,910 |
| Without Lancaster (0.87, post-hoc) | 4,493 |
| Market-adjusted: California × 0.67 / 0.5 / 0.25 / 0.15 | 4,234 / 3,057 / 1,361 / 940 |
| Rural and small-community places at the Madison floor | 3,574 |
| No ramp | 10,659 |

## Decisions requested

| ID | Decision | Options | My recommendation |
| --- | --- | --- | --- |
| G3-1 | **Re-centre the paths** | (a) keep California unadjusted as central (about 6,500); (b) market-adjust the central path to a California low-cost analogue; (c) other | **(b):** lower = Wisconsin-observed response (Madison floor, about 900); **central = market-adjusted California, ratio about 0.5 (about 3,000, between the Central Valley first-law and full-package analogues)**; upper = California restrictive level unadjusted (about 6,500); keep your share model (about 23,000) as a labeled stress test, "if Wisconsin builds a California-scale ADU industry", not as the upper path |
| G3-2 | Rule for places already at benchmark | (a) every place converges to the statewide level (as run; Madison +171); (b) benchmark places get only the spillover multiplier on their own rate (Madison about +40) | **(a)**, consistent with your statewide-industry view; remove the unused spillover parameter and document that the statewide level drives Madison's addition |
| G3-3 | Lower-path ramp | Same ramp as central, or California Central Valley's slower first-law ramp | **Slower ramp** for the lower path (the validation found the "no slower ramp observed" claim false) |
| G3-4 | Presentation | Round to the nearest hundred; label paths as scenarios; show the baseline range separately | **Yes** |
| G3-5 | Unzoned towns | Treat as receiving the full statewide level now, or code `no_zoning` towns before Gate 4 (they add nothing under AQ-026) | **Code them before Gate 5**; accept the overstatement for the pilot |

## Limitations to state wherever results appear

Results are gross permits for second homes on single-family lots, not completions or net new housing. California counts include some junior ADUs and legalizations. Restricted and uncoded Wisconsin rates lean on Madison, the state's strongest market. Municipal figures carry large uncertainty; county, context-group, and state totals are the reliable level.

## Recommendation

**Revise the central path (G3-1) and the related items, then advance to Gate 4.** The mechanics, data, and checks are sound; the open question is the transfer of California's response, which is a judgment you should make explicitly rather than one the model makes silently.

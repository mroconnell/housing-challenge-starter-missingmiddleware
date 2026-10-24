# Gate 3 Packet (final): Baseline, Policy Response, and Uncertainty

Prepared 2026-10-24 by the conductor. **Status: awaiting the owner's final Gate 3 decision.** Earlier versions are in git history. Decisions to date: AQ-034 to AQ-038 in the [assumptions log](../ASSUMPTIONS_AND_QUESTIONS.md).

Every number below is either a **count of second-home permits** (ADUs plus single-family-to-duplex conversions on lots that already have a home, AQ-032), statewide over the five forecast years 2027–2031, or a **rate** in second-home permits per 1,000 single-family homes per year. Wisconsin has 1,839,569 single-family (one-unit detached) homes.

## What this gate decides

Whether the statewide model is defensible enough to demonstrate in the Gate 4 pilot: the current-law baseline, the response to a statewide benchmark ADU law, and the scenarios that express uncertainty.

## The answer the model gives

Under current law, Wisconsin would permit about **650 second homes** on single-family lots over 2027–2031, about 130 a year, or 0.07 per 1,000 single-family homes per year.

With a statewide benchmark ADU law, the model adds:

| Scenario (labelled by meaning) | Rate once ramped up | Additional permits over 2027–2031 | Total with baseline |
| --- | --- | --- | --- |
| Like the slower statewide-law states (Rhode Island, Oregon) | 0.69 per 1,000 homes per year | about **4,800** | about 5,400 |
| **Like a typical statewide-law state** | 1.30 per 1,000 homes per year | about **9,500** | about 10,200 |
| At California's level (decision G3F-1 on the label) | 2.43 per 1,000 homes per year | about **18,400** | about 19,000 |
| *Reference line: the median path statewide-law states actually reached* | 0.79 → 1.24 per 1,000 homes per year (years 1–4) | about **8,650** | about 9,300 |

These are **scenarios, not statistical confidence intervals**. The lower and upper come from how much the eight statewide-law states differ from one another (the model's 80% range of state levels).

**Named downside sensitivities** (not scenarios):
- About **760** additional if the law only multiplied Wisconsin's current rate by the statewide-law factor the model estimates. Measured before-and-after pairs in other states contradict this, but no Midwest state has post-law data yet.
- About **2,300** additional if Wisconsin behaved like the California-only market regression, i.e. if Wisconsin stays closer to Madison and Minneapolis, which permit 0.18 and 0.26 per 1,000 homes per year under permissive local rules without a statewide law.

## How the central is built

1. **Pooled model** ([POOLED_MODEL.md](POOLED_MODEL.md)) across California's jurisdictions, seven other statewide-law states (Washington, Oregon, Maine, Rhode Island, Massachusetts, Utah, Vermont's Chittenden County), and five cities (Seattle, Portland, Austin, Denver, Minneapolis).
2. **Within each state**, places differ by home value, household income, and size; **across states**, one common level once a statewide law is in force fits best. Market terms across states made predictions worse.
3. **Ramp-up** from the pooled data: years 1–3 reach about 64%, 80%, and 82% of the year-4 level.
4. **Test:** each statewide-law state was predicted with that state left out. The average miss was 11% on the log scale (Washington 18% high, Massachusetts 20% high, Maine almost exactly). A simple benchmark (each state predicted as the average of the others) misses by 14%, so the test mainly shows the states are alike.
5. **Engine:** each area's addition = its single-family homes × (with-law rate − current rate) × ramp, never below its current rate. The engine reproduces the pooled model's totals exactly.

## Owner review: step by step, with my self-assessment

| Step | What you do | What you should see | My result |
| --- | --- | --- | --- |
| 1 | Follow one baseline and one reform calculation | Madison: 53,292 single-family homes; current rate 0.183 per 1,000 per year gives a baseline of about 49 permits over five years; with-law plateau 1.75 per 1,000 per year; additional = 53.292 × (1.75 − 0.18) × ramp sum 4.21 ≈ **351 permits** | **Pass** (recomputed independently) |
| 2 | Check current activity reduces the change | Each place's current rate is subtracted; Madison's 0.18 lowers its addition | **Pass** |
| 3 | Read the source of the central | Pooled model, typical statewide-law state | **Pass with two caveats** (decisions G3F-2, G3F-3) |
| 4 | What separates lower and upper | How statewide-law states differ; the upper is California's level | **Pass after the upper is labelled correctly** (G3F-1) |
| 5 | Validation and strongest challenge | Leave-one-state-out test; California holdout; the Midwest gap below | **Your judgment** |
| 6 | Decide | Below | Yours |

## Strongest remaining challenge

The model contains no Wisconsin data in its fit. Places with permissive local rules but no statewide law sit far below it: Madison permits 0.18 per 1,000 homes per year where the model's no-law level for a place like Madison is 3.4; Wisconsin overall permits 0.07 where the model's no-law level is 0.52. The case for the model is that states with before-and-after data (California, Rhode Island, Washington, Vermont) reached the same first-year level regardless of how low they started, which is the statewide-industry effect. The case against is that no Midwest state has post-law data; Iowa's first full year (2026) is the first test.

## Decisions requested

| ID | Decision | Options | Recommendation |
| --- | --- | --- | --- |
| G3F-1 | Upper scenario label | Keep 18,400 labelled "At California's level"; or replace it with the spread without California (about 12,200) and keep 18,400 as a sensitivity | **Keep 18,400, labelled "At California's level"**: honest about what it represents, and California is the one state with a mature ADU industry |
| G3F-2 | California in the common level | The "typical state" level (1.30) is pulled up by California and sits above six of the seven other states; without California in that step the central is about **8,300** (range about 5,600–12,200) | **Keep California in**, but show "without California" (about 8,300) as a named sensitivity |
| G3F-3 | New-house ADUs | Other states' counts include ADUs built together with a new house; Wisconsin's outcome does not. Counting them at 80% gives a central of about **7,800** and an adoption line of about 6,800 | **Show as a named sensitivity** beside the headline; the true share is unknown |
| G3F-4 | Advance to Gate 4 | Yes / revise | **Yes**, with these labels and sensitivities |

## What a legislator might misread, stated in the tool

- Totals are over five years (the central is about 1,900 a year), are permits, not completed or net new homes, and are on top of the baseline.
- The range shows how states differ, not statistical certainty.
- Town figures are rough shares of the statewide result, not local forecasts; rural areas get 43% of the addition with 39% of homes, partly because rural home values include acreage.
- Results describe what other states experienced after their laws; they are associations, not proven causal effects.

## Supporting documents

[POOLED_MODEL.md](POOLED_MODEL.md) · [STATEWIDE_STATES.md](STATEWIDE_STATES.md) · [OTHER_CITIES.md](OTHER_CITIES.md) · [CA_STUDY_RESULTS.md](CA_STUDY_RESULTS.md) · [CA_REGRESSION.md](CA_REGRESSION.md) (now a sensitivity) · [WI_BASELINE.md](WI_BASELINE.md) · [WI_UNZONED_TOWNS.md](WI_UNZONED_TOWNS.md) · [WI_RULES_VS_ACTIVITY.md](WI_RULES_VS_ACTIVITY.md) · [CA_RULES_VS_ACTIVITY.md](CA_RULES_VS_ACTIVITY.md)

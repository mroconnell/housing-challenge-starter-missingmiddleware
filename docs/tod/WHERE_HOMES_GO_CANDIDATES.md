# Candidate models for "where homes go" and "how many"

Started 2026-10-31 at the owner's request. A running list of ways to predict TOD homes for a state with little city data. Each must use inputs any state has. Scale is not a blocker (plan item 61).

## Current working model (tested but limited)

| # | Candidate | What it predicts | Status |
| --- | --- | --- | --- |
| 1 | **Share model** (round 8) | Each lot's share of a place's new homes, law on vs law off. Place total from the Census permit survey (any US place). | Working model to beat. Beat "same share" on 6 training cities; closest on Chicago and Madison holdouts when calibrated; Bellevue wrong. |

TOD effect is shown as a range: bound A (pure relocation, 0 extra homes) to bound B (pure addition, calibrated). Owner open to B as a labelled sensitivity.

## Candidates to try

| # | Candidate | Idea | Status |
| --- | --- | --- | --- |
| 2 | **No-reform pace model** | Predict a place's homes per year with no reform from data any state has (past permits, rents, incomes, jobs, land). Test on no-reform cities and pre-reform years. Never iterated on its own so far. | Proposed |
| 3 | Pace + share combined | Pace model (2) gives the place total; share model (1) splits it to lots | Depends on 2 |
| 4 | True causal forest (EconML) | Lot-level extra homes, with honest splitting | Queued |
| 5 | Two-step site assembly | Chance a lot gets combined, then chance the site builds | Queued |
| 6 | Whole-city lot samples | Add a representative sample of each reform city's lots, near and far | Proposed |
| 7 | "Does it pay" land-value traits | Land value vs building value, rent vs cost | LAND_VALUE_PLAN.md |
| 8 | Setbacks | Lot shape and setback room as traits | research/SETBACKS_IDEA.md |
| 9 | Stacy et al. average | Literature effect, no model | Fallback only |

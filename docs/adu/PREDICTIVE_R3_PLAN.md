# ADU model runs, run 3: plan written before running

Written 2026-10-31 by the ADU conductor, under Ryan's ask (2026-10-31): once data and coding are clean, run the full list of models, including the causal forests, for both the no-reform baseline and the law's prediction. ADU's statewide net check met the stopping rule (docs/adu/NET_STATEWIDE_R1.md). No result below had been computed when this file was committed.

## What runs

The same 5 methods as runs 1 and 2 ([PREDICTIVE_PLAN.md](PREDICTIVE_PLAN.md) section 5; guess-zero reported too), on the same panel of states, cities, tracts and Wisconsin places:

| Method | Law part | No-reform part |
| --- | --- | --- |
| Plain average | same-law-status average of the training states | same |
| Adopted model, refitted | two-stage model with law terms | its law = 0 prediction |
| Causal forest (two parts, 500 trees) | forest on law rows | forest on no-law rows |
| Boosted trees (two parts) | on law rows | on no-law rows |
| Regularised regression (two parts) | on law rows | on no-law rows |

## What changes from run 2: the adopted data and coding (AQ-065)

- Vermont counted by permit year (each count one year earlier).
- Oregon law years from 2020; 2019 dropped for the 32-city panel and Portland's tracts.
- Seattle's 2024 tract rows: local rules only.
- Reporting shares as now adopted (Rhode Island and Massachusetts homes shares; AQ-064).

No other setting changes: the same folds, seeds, variables, pass rule and flags.

## Scores

1. **Law side:** runs 1–2's tests 1–3 and pass rule, unchanged.
2. **No-reform side (new):** every row with no statewide law is scored when its state (fold) is held out. For each held-out unit, pooled predicted rate vs pooled observed rate; score = median of |log((predicted + 0.05) ÷ (observed + 0.05))| over units, the same score as the no-reform round 1. The forward test (train on earlier years, predict later ones) stays in the no-reform round 1 script, which already chose the tool's baseline.
3. **Flags** before the run (owner rule), and the worst miss traced.

## Use

- Nothing in the tool changes unless a method passes the pre-set rule on the law side, or clearly beats the adopted no-reform rule (same pace plus trend) on the no-reform side. Ryan decides.
- Results go to the audit as they come.

## Changes after writing

None yet.

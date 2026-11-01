# ADU model runs, run 3: results

Run 2026-10-31 under [PREDICTIVE_R3_PLAN.md](PREDICTIVE_R3_PLAN.md), committed before running. Code: `scripts/build_adu_predictive_panel.py --run 3`, `scripts/run_adu_predictive.py --run 3`. Outputs: `reference/adu_predictive_run3_*.csv`. The run was cut off twice when the session ended; the seed checks and the Wisconsin step were finished by rerunning on the saved predictions (`--reuse`), which changes nothing in the main-seed results.

**Units.** Rates are ADU permits per 1,000 single-family homes per year. A log error is log(predicted ÷ observed) for a place or state whose whole state was left out of training. Wisconsin figures are additional ADU permits, 2027–2031.

## Answer

- **No-reform side:** the flexible models predict other states' no-law levels better than the adopted model's law-off part. But every model over-predicts Madison, Wisconsin's own city, by 4 to 18 times. So a cross-state model is not a safe Wisconsin baseline. The tool's baseline (each place's own measured rate plus the no-reform trend) stays.
- **Law side, "how much":** boosted trees passed on the main seed (0.17 against the adopted model's 0.22), but only 2 of the 5 extra seeds. **Not robust.**
- **Law side, "where":** the causal forest passes on all 5 seeds; boosted trees on 4 of 5. These are candidates for a "where" line, not for the statewide total.
- **Wisconsin, from the two models that passed something:** boosted trees 6,619; causal forest 13,942. The tool's central is 10,349. They sit inside the tool's range (6,223–19,294).
- **Worst misses:** Utah is under-predicted by every method (−0.36 to −0.96). Its counts are self-reported internal ADUs only, so its rate is hard to place. Seattle's tracts (3.8 permits per 1,000 homes per year with no state law) are under-predicted by every method on the no-reform side.

## 1. No-reform side (every row with no statewide law, own state held out)

Score: median over 10 units of |log((predicted + 0.05) ÷ (observed + 0.05))|.

| Method | Score | Worst unit |
| --- | ---: | --- |
| Regularised regression | 0.47 | Madison tracts |
| Boosted trees | 0.58 | Austin tracts |
| Causal forest | 0.62 | Madison tracts |
| Plain average | 0.84 | Madison tracts |
| Adopted model, law off | 0.94 | Madison tracts |
| Guess zero | 2.12 | Seattle tracts |

| Unit | Observed | Plain average | Adopted, law off | Causal forest | Boosted trees | Regularised |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Madison tracts (WI) | 0.09 | 0.75 | 1.59 | 0.73 | 0.34 | 0.52 |
| Minneapolis tracts | 0.22 | 0.73 | 1.26 | 0.52 | 0.15 | 0.39 |
| Austin tracts | 1.00 | 0.63 | 1.42 | 0.59 | 0.16 | 0.64 |
| Seattle tracts | 3.82 | 0.63 | 0.65 | 0.75 | 0.80 | 1.10 |
| Washington cities | 0.38 | 0.63 | 0.35 | 0.26 | 0.09 | 0.15 |

## 2. Law side

| Test | Plain average | Adopted model | Causal forest | Boosted trees | Regularised | Passes (main seed) | Seeds passing (of 5) |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 How much (mean miss) | 0.226 | 0.218 | 0.257 | 0.173 | 0.478 | boosted trees | boosted trees 2 |
| 2 Where, rates | 1.071 | 2.272 | 0.983 | 0.866 | 0.929 | forest, boosted trees | forest 5; boosted trees 4 |
| 3 Where only | 0.407 | 0.393 | 0.378 | 0.386 | 0.382 | none | none |

Held-out log error by state, test 1:

| State | Plain average | Adopted | Causal forest | Boosted trees | Regularised |
| --- | ---: | ---: | ---: | ---: | ---: |
| Washington | +0.46 | +0.31 | +0.24 | +0.07 | +0.45 |
| Oregon | +0.33 | +0.34 | +0.27 | +0.07 | +0.31 |
| Rhode Island | +0.07 | −0.10 | −0.00 | +0.08 | +0.27 |
| Massachusetts | +0.19 | +0.11 | +0.10 | −0.03 | −0.33 |
| Maine | −0.06 | −0.07 | −0.50 | −0.27 | −0.92 |
| Utah | −0.11 | −0.36 | −0.54 | −0.61 | −0.96 |
| Vermont | +0.23 | −0.17 | +0.13 | +0.05 | +0.29 |

The adopted model scores 0.24 here, not the tool's 0.13, because this panel splits cities into tracts and uses different rows.

## 3. Flags before the run (owner rule; nothing stopped)

43 flags: 24 policy-definition (reporting shares, partial years, recoded law years), 11 missing inputs (small tracts' ACS medians, filled and flagged), 6 unit checks, 2 held-out units far from the training range. Same kinds as run 2.

## 4. Next

- Send to the audit; fix anything it finds; rerun.
- Then compare the models as possible extra lines in the tool: boosted trees (6,619) and causal forest (13,942) for the statewide total, and the forest's "where" pattern. Ryan decides; the tool is unchanged.

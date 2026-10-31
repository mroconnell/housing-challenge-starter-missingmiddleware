# TOD lot model: locked result vs final result

Written 2026-10-31 for readers and judges (audit scorecard, plan item 50.1). Many rules changed after the item-36 result was seen. This page sets the two results side by side and lists every later change with its reason, so a reader can check that the answer was not chased. Full log: [LOT_MODEL_PLAN.md](LOT_MODEL_PLAN.md), section 9.

## The two results on the three cities never used for training

| | Locked (item 36, 2026-10-29) | Final (round 8, read 2026-10-31) |
| --- | --- | --- |
| Model | Causal forest (two random forests), extra homes vs a comparison area | Gradient boosting, two models; share of a city's new homes on upzoned lots |
| Chicago | Predicted 294 extra homes; actual 892; plain average 1,384 (plain average closer) | Upzoned share: actual 9.9%; raw 21.8%; calibrated 7.2%; same-as-before 4.0% (calibrated closest) |
| Madison | Predicted −435; actual 2,260; plain average 2,186 (plain average closer) | Actual 19.0%; raw 29.7%; calibrated 15.3%; same-as-before 12.1% (calibrated closest) |
| Bellevue | Predicted 91; actual −90; plain average 1,209 (model closer) | Actual 0%; raw 95.6%; calibrated 17.2%; same-as-before 0% (model wrong) |
| Verdict | Failed its locked rule (closer on 1 of 3) | No pass rule (owner, item 42). Closest on 2 of 3 when calibrated; Bellevue wrong |

The two do not measure the same thing.
- The locked result scores **extra homes** against a hand-picked comparison area. That area turned out to be mis-measured in Madison (item 37).
- The final result scores **where new homes go** in the whole study area, with the city total held at its previous pace.

## Every change after the locked result

| Item | Change | Why | Effect |
| --- | --- | --- | --- |
| 37 | Keep every lot; total-homes test | Owner: dropping lots is cherry-picking | Madison's comparison area no longer trimmed. It had read 0 homes after the reform; with the full ring, Madison's actual is about +190, as in the pre-registered test |
| 38–39 | Placebo cities Madison (outside overlay) and Milwaukee; "everything is a trait"; "no reform" trait | Owner | Adds no-reform lots |
| 40–41 | Leak fixed (a city's own placebo lots never train it); "rezoned later" = 0 at forecast time | Audit | Removes hindsight |
| 42 | No pass/fail threshold | Owner: thresholds arbitrary | Results reported plainly |
| 43–45 | Missing census releases fetched; cost per home fixed (Milwaukee, New York); floor area −1 where none; room-to-build from census homes | Units table caught them | Placebo cities had placeholder rents and incomes before |
| 46–47 | Columbus and Kansas City as no-reform cities (20% city samples); cost traits dropped | Owner | More no-reform markets |
| 48 | Upzoned lots more than ½ mile from transit relabelled | Owner | Training TOD lots are transit-based |
| 49 | Improvement loop with a fast tool; holdouts untouched until the end | Owner | — |
| 51–56 | Rounds 1–7 fixes: predict homes after (not change); stable loss; place's own pace; reform-share traits dropped (acted as city labels); homes per acre; market trend | Each round's "ask why" | Seed spread found as large as round-to-round swings (item 58) |
| 57–59 | Two-part design: city total = same pace; model predicts shares; one calibration declared; holdout read declared | Audit | Round 8: model 0.31–0.47 vs 0.65 (same share) across 6 seeds |
| 60 | Checks: New York assembled sites, Los Angeles Cornfield | Audit | Cornfield's 0 is most likely real |

## What the final result supports

- **Direction:** upzoning near transit shifts where new homes go. The share on upzoned lots rose in New York, Charlotte, Philadelphia, Chicago and Madison, and the model predicts a rise.
- **Size:** the raw model overstates the shift about fivefold (k = 0.18). The calibrated model is the closest of the three guesses in Chicago and Madison.
- **Net new homes:** not identified. Bound A (pure relocation) is 0; bound B (pure addition) is Chicago 629, Madison 400 and Bellevue 18 homes over 5 years, raw.
- **Fails:** Bellevue, where almost nothing was built.
- **Not supported:** using this model alone for Wisconsin's headline. Wisconsin's law covers about 8 times the training cases' upzoned lots, and the law-off check overstated Wisconsin shares.
- The tool's scenarios (171 / 2,509 / 17,148) are unchanged.

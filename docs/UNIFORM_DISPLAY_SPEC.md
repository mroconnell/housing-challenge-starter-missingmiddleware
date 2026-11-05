# One display for all three reforms: a 90% range, then reasons to believe (draft spec, not shipped)

Drafted 2026-11-03 at the owner's request (18:56: "a range with 90% CI that shows the low and high of that range? Then,
we plot additional lines across them for context as reasons to believe"). Revised 2026-11-04 for the owner's rule (16:49):
"We no longer need 'Center' lines. We're showing a range with a confidence interval. And then we're plotting side lines
against each one". It builds on the tutor's shared rules, the audit, and the parking and ADU threads' inputs.
**Nothing in the tool changes until the owner approves this spec.**

All figures are extra homes permitted in Wisconsin, 2027–2031, compared with current law, unless a unit is stated.

## Shared rules

1. **Each reform shows one 90% range, with its low and high ends labelled. There is no centre line.**
2. **One method for the range.** The range is a place bootstrap of the reform effect only: places resampled with
   replacement, and the effect recomputed on each draw. Where the effect comes from a model fitted across states, it
   is that model's held-out prediction error instead (ADU's A3). Where fake-reform estimates were run, it may instead
   be their spread around the measured effect (parking). Each is 90%, the 5th to 95th percentile.
3. **The current-law range stays separate.** It is shown as its own grey band: for all housing, 56,500 to 218,865 homes over 2027–2031 (aims at 90%; shared baseline v4). It held 12 of 12 Wisconsin checks and 88.3% of other-state checks for 2009–2020, a window chosen after the results. It missed the 2005–08 run-up to the crash, like every method tested. Only the statewide total was tested. The two are combined only if a total
   ("current law plus the reform") is shown, and then once, by simulation: a paired draw of each, never a sum of ends.
4. **Two-sided, with no zero floors.** A range may cross 0, and the low end is shown as measured.
5. **Coverage check.** Where a scenario's own test shows its 90% range covers the truth less than 90% of the time,
   the range is widened by the measured factor; otherwise it is shown as is. A range taken from fake-reform estimates
   already carries the true spread and is not widened.
   - Parking: no widening (placebo spread, matched test 40).
   - ADU: factor 1 (7 of 7 states inside).
   - TOD: test below, locked before it runs.
   - One method line per reform goes under its range. Reforms are not compared by range width, because the methods
     differ.
6. **Side lines are the reasons to believe.** Each is a thin labelled line across the range: what it is (the method
   and the places), its number and its unit. Several side lines may sit inside one range. None is singled out as
   "the" estimate, and none changes the range.
7. **Exact numbers, one confidence level.** Every range is 90% and quoted at its exact ends, not rounded (owner,
   2026-11-04). **Every number states its unit.** Shares of the 124,000-home all-housing baseline are given for the low and high
   ends.
8. **Where a doc or table would quote one number, quote the range instead:** "X to Y extra homes, 2027–2031 (90%
   range)".
   - Tables list the reforms in a fixed order (ADUs, TOD, parking), with no ranking. A range midpoint is not used as a
     stand-in for a centre.
   - A total across reforms is a range from a paired simulation of the reforms' draws, never a sum of ends.
   - Side lines may be quoted by name ("the 8-state median path, 10,038"), never as the reform's result.

## The three ranges

| Reform | 90% range | Source of the range | Coverage |
| --- | --- | --- | --- |
| ADUs (ADU permits: second homes on single-family lots, not all homes) | 8,055 to 13,666 (exact; owner 2026-11-04: "Exact numbers everywhere with the same CI"). Label beside it: "Covers law-side error only. It leaves out Wisconsin-side inputs: today's rates where they are assumed (74% of the addition is in such places; the codings tested move the result from 9,319 to 10,734), and how the with-law level is spread across places." | A3 held-out prediction error (model fitted across states) | 7 of 7 states inside; too few to measure a factor, so factor 1 |
| TOD | 3,922 to 16,335 (the bootstrap 4,866 to 15,361 widened ×1.1827, because the coverage test found 84.5%; not 7,580 to 12,010, which is the lowest and highest with one place left out) | place bootstrap of the 11 district places, 2,000 draws (`reference/tod_line_draws.csv`), widened per the coverage test | 84.5% before widening (`reference/tod_coverage_test.csv`) |
| Parking | −45,853 to +19,818 (exact: the measured average −1.1417 plus the placebo 5th and 95th percentiles minus their median, −3.4364 to +1.4852 permits per 1,000 homes a year, × 2,668,677 eligible homes × 5 ÷ 1,000; `reference/parking_placebo_full_summary.csv`). Shares of the 124,000 baseline: −37.0% to +16.0% | placebo spread around the measured average of the 76 repeal places, unwidened | not widened, and why: test 40's 84% was for a bootstrap range, which parking does not use. This range comes from fake-reform estimates, whose spread already matched test 40 (audit, 2026-11-03), so it is already a 90% range (rule 5). TOD is widened because its range is a bootstrap. |

## Side lines (reasons to believe)

| Reform | Side lines (label: number) |
| --- | --- |
| ADUs | Typical adoption (the former central): 10,492. Median path of the 8 statewide-law states: 10,038. Like Rhode Island and Oregon, the 2 slowest statewide-law states: 6,321. High end, near California (only California is higher): 19,784. On How sure only: what-ifs 791 and 2,255; bias-corrected range 7,516 to 13,317. ADU thread to confirm the first label. |
| TOD | Average district place, 11 places (the former central): 10,028. Edge test, rezoned lots' own gain (5 places): 3,958. Average scaled to a 15% district (11 places): 12,521. Rezoning near new transit lines, 2×2 (9 places): 13,451. Same minus the growth already under way before the reforms: 5,624. |
| Parking | Measured average, 76 repeal places: −15,234. Median repeal place: −1,557. Oregon state mandate, covered Oregon cities vs Washington cities: about +16,800 (Oregon cities on DLCD's 48-city list in covered metros, against Washington cities at 0.5–2× their population, Portland dropped; Washington's 2024–25 middle-housing parking laws may pull this line toward zero). Not shown: San Diego, Chicago, and the count models that fail the pre-trend check (including the negative binomial, all homes, +204; tests 38–39). On How sure only: the high ends from the improvement rounds, about 27,700 to 49,700. |

- The parking "centre 0" question goes away, and so does its note.
- A side line can sit outside its range (ADU 19,784). It is drawn there and labelled; the range doesn't change.

## Screens affected (all three reforms)

- **Statewide comparison:** one headline card per reform: the 90% range, low and high ends labelled, unit, and shares
  of the baseline for each end. Below it, the side lines, one sentence each. The ADU card says its figures are ADU
  permits (second homes on single-family lots), not all homes.
- **Where the bands come from:** the chart and Where bands are drawn from each reform's draws, so the draws must match
  the card.
  - TOD: its draws (`reference/tod_line_draws.csv`) are widened ×1.1827 about 10,028, so the band shows 3,922 to
    16,335, not 4,866 to 15,361.
  - Parking: its draws are the placebo-set averages shifted by (the real average minus the placebo median).
  - ADU: it has no draws, so its band uses the two ends. A total across reforms (paired simulation) needs ADU draws
    first.
- **The yearly chart:** a shaded 90% band (the draws spread along the same yearly ramp), the grey current-law band,
  and the labelled side lines (5-year totals in the legend). No centre line. The "extra homes only" view gets the
  same.
- **Where:** each area shows its range, which scales from the statewide draws because the tool spreads homes by a fixed
  share. Say so in one line. A sortable column uses the range's low end, labelled as such.
- **How sure:** the tornado moves from "difference from the central" to each what-if's own total, drawn against the
  90% range band. The coverage note and method line go at the top.
- **Brief:** the 90% range in the headline sentence, then the side lines.
- **The record-year warning:** checked at the range's high end.
- **Docs owned by the ADU thread** (`README.md`, `docs/POLICY_SCENARIO_COMPARISON.md`, `docs/MODEL_AND_ASSUMPTIONS.md`):
  the Lower / Central / Upper table becomes "90% range" plus "Side lines", in fixed order with no ranking (rule 8).
- **The combined view** stays shelved. If it comes back, it shows a range from a paired simulation of the reforms'
  draws.

## TOD coverage test (proposed, locked before it runs; revised after the audit)

- **Question:** how often does TOD's place-bootstrap 90% range contain the true average effect, given 11 places?
- **Fake effects:** the C-PT fake-years effects (`reference/tod_causal_central_pretrend.csv`), for all 10 places that
  have one. They have the same outcome and unit as the range (extra homes per 100 lot acres a year within ¼ mile). The
  edge-test P1 fake districts are not used, because they measure a different unit (the direct effect at district
  boundaries).
  - Used: New York, Philadelphia, Austin, Charlotte, Chicago 2015, Denver, Portland 2020, Seattle Mount Baker,
    Seattle Othello, Salt Lake City.
  - Left out: Saint Paul. It has no fake-years effect, because its before window is one year.
- **Check 1, width (one check), two pools:**
  - Main pool, which sets the widening factor: the 11 real place effects (the range is built from them). Truth =
    their mean, 33.54.
  - Sensitivity pool: the 10 fake effects. Truth = their mean.
  - For each pool: each run draws 11 places with replacement from the pool and builds the same 2,000-draw bootstrap 90%
    range. Coverage = the share of runs whose range contains the pool's true average. 1,000 runs, seed 20261103.
  - No injected sizes: adding a constant shifts the draws and the truth equally, so it cannot change coverage.
- **Check 2, bias (reported beside):** the fake effects' mean and its 90% range. C-PT found 14.5 (−3.8 to 38.8),
  against the real 35.4, and 1.7 without Seattle Othello (9 places). The range includes 0, so this check neither
  shows nor rules out bias; the text says so. Widening fixes width, not bias.
- **Widening rule, fixed now:** if the main pool's coverage is below 90%, widen both ends away from the bootstrap
  point estimate (used only for this, not shown) by the factor that brings coverage to 90% in this simulation. Show
  the widened range with one line saying so. At 90% or above, show it as is.

### Results (run 2026-11-04, owner approved 16:51)

- **Timing:** the lock was committed 2026-11-03 (e1994c8b), before any run. The script and the results came in one later
  commit (e276824b, 2026-11-04).
- **Factor:** about 1.18 (1.17 to 1.26 depending on the order places are drawn in; 1.1827 with the fixed order).
- **Caution:** a check on the fake effects covered less (69%), so the widened range may still be narrow.


Run as locked: `scripts/run_tod_coverage_test.py`, output `reference/tod_coverage_test.csv`. 1,000 runs per pool, 11
places drawn per run, 2,000-draw bootstrap per run, seed 20261103. Effects are extra homes per 100 lot acres a year
within ¼ mile.

**Check 1, coverage** (share of 1,000 runs whose 90% range holds the pool's true mean):

| Pool | Places in pool | True mean (homes per 100 lot acres a year) | Runs covered (of 1,000) | Coverage (%) |
|---|---|---|---|---|
| Real effects (main) | 11 | 33.54 | 845 | 84.5 |
| C-PT fake effects (sensitivity) | 10 | 14.51 | 686 | 68.6 |

- Both pools fall below 90%.
- The main pool sets the widening.

**Check 2, bias** (homes per 100 lot acres a year):

| Measure | Places | Mean | 90% range |
|---|---|---|---|
| Fake effects | 10 | 14.51 | −3.84 to 38.81 |
| Fake effects without Seattle Othello | 9 | 1.72 | not computed |
| Real effects, for comparison | 11 | 33.54 | 16.27 to 51.37 |

- The fake range includes 0.
- So bias is neither shown nor ruled out.
- Widening fixes width, not bias.

**Widening** (main pool coverage 84.5% is below 90%):

| Item | Value |
|---|---|
| Widening factor f (ratio, both ends) | 1.1827 |
| Coverage with f applied (%) | 90.0 |
| Published 90% range (Wisconsin homes, 2027-2031) | 4,866 to 15,361 |
| Point used for widening only (homes; 33.5373 × 298.97) | 10,028 |
| Widened 90% range (Wisconsin homes, 2027-2031) | 3,922 to 16,335 |

- Show 3,922 to 16,335 as TOD's range.
- One line says it was widened.
- Simulation noise: f moves with place order.
  - Reversed and sorted pool orders gave f = 1.169 and 1.255 (coverage 85.6% and 81.4%). Not part of the lock; the
    locked run (sorted place names, as the export script) stands.

## Open questions for the owner

1. **Approve the spec** for building? The build touches every scenario's screens; I would do the shared parts and
   TOD, and the ADU and parking threads their own numbers and side-line labels.

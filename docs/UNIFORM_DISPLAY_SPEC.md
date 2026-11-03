# One display for all three reforms: a 90% range, then reasons to believe (draft spec, not shipped)

Drafted 2026-11-03 at the owner's request (18:56: "a range with 90% CI that shows the low and high of that range? Then,
we plot additional lines across them for context as reasons to believe"). It builds on the tutor's shared rules and
parking's and ADU's inputs. **Nothing in the tool changes until the owner approves this spec.**

All figures are extra homes permitted in Wisconsin, 2027–2031, compared with current law, unless a unit is stated.

## Shared rules

1. **One method for the range.** The range is a place bootstrap of the reform effect only: places resampled with
   replacement, and the effect recomputed on each draw. Where the effect comes from a model fitted across states, it
   is that model's held-out prediction error instead (ADU's A3). Where fake-reform estimates were run, it may instead be their spread around the measured effect (parking). Each is 90%, the 5th to 95th percentile.
   A state bootstrap for ADU would need the owner's OK.
2. **The centre is that same method's point estimate.** Otherwise the range and the centre answer different
   questions (see open question 1, for parking).
3. **The current-law range stays separate.** It is shown as its own grey band. The two are combined only if a total
   ("current law plus the reform") is shown, and then once, by simulation: a paired draw of each, never a sum of ends.
4. **Two-sided, with no zero floors.** A range may cross 0, and the low end is shown as measured.
5. **Coverage check.** Where a scenario's own test shows its 90% range covers the truth less than 90% of the time,
   the range is widened by the measured factor; otherwise it is shown as is. A range taken from fake-reform estimates
   already carries the true spread and is not widened. Parking: its band comes from placebo
   percentiles, which already matched test 40, so no widening and no coverage note (audit). ADU: 7 of 7 states inside,
   factor 1. TOD: test below, locked before it runs.
   One method line per reform, under its range. Reforms are not compared by range width, because the methods differ.
6. **Side lines are context, not scenarios.** Each is a thin dashed line across the range. It is labelled with what it
   is (the method and the places), plus its number and unit. A side line never changes the centre or the range.
7. **Every number states its unit.** Shares of the 124,000-home all-housing baseline are given beside, as now.

## The three reforms

| Reform | Centre | 90% range | Source of the range | Coverage |
| --- | ---: | --- | --- | --- |
| ADU (ADU permits: second homes on single-family lots, not all homes) | 10,492 | 8,000 to 13,700 (exact 8,055 to 13,666, rounded outward; A3, owner's OK pending); label beside it: "Covers law-side error only. It leaves out Wisconsin-side inputs: today's rates where they are assumed (74% of the addition is in such places; the codings tested move the central from 9,319 to 10,734), and how the with-law level is spread across places." | A3 held-out prediction error (model fitted across states) | checked on 7 states, 7 of 7 inside; too few states to measure a factor, so factor 1 (largest miss Washington +0.19 against ±0.25) |
| TOD | 10,028 | 4,866 to 15,361 (not 7,580 to 12,010: that is the lowest and highest with one place left out, not a 90% range) | place bootstrap of the 11 district places, 2,000 draws (`reference/tod_line_draws.csv`) | test below |
| Parking | 0 (open question 1) | −45,900 to +19,800 | placebo spread around the measured average of the 76 repeal places, unwidened | matched test 40; no widening |

## Reasons-to-believe side lines

| Reform | Side lines (label: number) |
| --- | --- |
| TOD | Edge test, rezoned lots' own gain (5 places): 3,958. Average scaled to a 15% district (11 places): 12,521. Rezoning near new transit lines, 2×2 (9 places): 13,451. Same minus the growth already under way before the reforms: 5,624. |
| Parking | Inside the band, not a dashed line: a marker "measured average, 76 repeal places: −15,234", with the note "0 is used because the data cannot tell the effect from no change." Side lines: median repeal place: −1,557. Oregon state mandate: about +16,800. Not shown: San Diego, Chicago, and the count models that fail the pre-trend check (including the negative binomial, all homes, +204; tests 38–39). On How sure only: the high ends from the improvement rounds, about 27,700 to 49,700. |
| ADU | Like Rhode Island and Oregon, the 2 slowest statewide-law states: 6,321 ADU permits. Median path of the 8 statewide-law states: 10,038. High end, near California (only California is higher): 19,784. The what-ifs 791 and 2,255 stay on How sure, off the chart. Sensitivity line (one): bias-corrected range 7,516 to 13,317. |

The current lower and upper lines retire as scenario lines:
- TOD's 3,958 and 12,521 become side lines.
- Parking's −15,234 and +19,818 are replaced by the range and side lines.
- ADU's 6,321 and 19,784 become side lines (labels above).

## Screens affected (all three reforms)

- **Statewide comparison:** one headline card (centre, 90% range, unit, shares) instead of three cards. The ADU card says its figures are ADU permits (second homes on single-family lots), not all homes. Below it,
  a short list of side lines with one sentence each.
- **The yearly chart:** the centre line, a shaded 90% band (draws spread along the same yearly ramp), the grey
  current-law band, and dashed side lines (5-year totals in the legend). The "extra homes only" view gets the same.
- **Where:** area figures use the centre. The area range scales by the statewide draws, as the tool spreads homes
  by a fixed share. Say so in one line.
- **How sure:** the tornado stays, measured from the centre. Add the range and its coverage note at the top. Each
  side line keeps its own range there.
- **Brief:** the centre and 90% range in the headline sentence.
- **The record-year warning:** checked at the centre and at the 95th percentile.
- **Docs owned by the ADU thread** (`README.md`, `docs/POLICY_SCENARIO_COMPARISON.md`, `docs/MODEL_AND_ASSUMPTIONS.md`):
  the ranking table gets "Centre" and "90% range" columns instead of Lower / Central / Upper.
- **The combined view** stays shelved. If it comes back, its range is a paired simulation of the reforms' draws.

## TOD coverage test (proposed, locked before it runs; revised after the audit, 19:06)

- **Question:** how often does TOD's place-bootstrap 90% range contain the true average effect, given 11 places?
- **Fake effects:** the C-PT fake-years effects (`reference/tod_causal_central_pretrend.csv`), for all 10 places that
  have one. These are the same outcome and unit as the central (extra homes per 100 lot acres a year within
  ¼ mile). The edge-test P1 fake districts are not used, because they measure a different unit (the direct effect at
  district boundaries).
  - Used: New York, Philadelphia, Austin, Charlotte, Chicago 2015, Denver, Portland 2020, Seattle Mount Baker,
    Seattle Othello, Salt Lake City.
  - Left out: Saint Paul, which has no fake-years effect because its before window is one year.
- **Check 1, width (one check), two pools:**
  - Main pool, which sets the widening factor: the 11 real place effects (the range is built from them); truth =
    their mean, 33.54.
  - Sensitivity pool: the 10 fake effects; truth = their mean.
  - For each pool: Each run draws 11 places
  with replacement from the pool, then builds the same 2,000-draw bootstrap 90% range. Coverage = the share of runs
  whose range contains the pool's true average. 1,000 runs, seed 20261103. No injected sizes: adding a constant
  shifts the draws and the truth equally, so it cannot change coverage.
- **Check 2, bias (reported beside):** the fake effects' mean and its 90% range. C-PT found 14.5 (−3.8 to 38.8),
  against the real 35.4, and 1.7 without Seattle Othello (9 places). The range includes 0, so this check neither
  shows nor rules out bias; the text says so. Widening fixes width, not bias.
- **Widening rule, fixed now:** if the main pool's Check 1 coverage is below 90%, widen the range about the centre by the factor that
  brings it to 90% in this simulation, and show the widened range with one line saying so. At 90% or above, show it
  as is.

## Open questions for the owner

1. **Parking's centre.** Keep 0 as the centre, with −15,234 marked inside the band as the measured average and the note
   "0 is used because the data cannot tell the effect from no change"? Or use −15,234 as the centre (rule 2)?
   Recommendation (and the audit's): keep 0. This breaks rule 2 for parking only, and the note says so.
2. **ADU range.** Adopt A3, 8,000 to 13,700, labelled "covers law-side error only", with the bias-corrected range
   7,516 to 13,317 as one sensitivity line?
3. **TOD coverage test.** Run it as locked above before shipping? Recommendation: yes. It takes about 20 minutes.

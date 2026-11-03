# One display for all three reforms: a 90% range, then reasons to believe (draft spec, not shipped)

Drafted 2026-11-03 at the owner's request (18:56: "a range with 90% CI that shows the low and high of that range? Then,
we plot additional lines across them for context as reasons to believe"). It builds on the tutor's shared rules and
parking's and ADU's inputs. **Nothing in the tool changes until the owner approves this spec.**

All figures are extra homes permitted in Wisconsin, 2027–2031, compared with current law, unless a unit is stated.

## Shared rules

1. **One method for the range.** The range is a place bootstrap of the reform effect only: places resampled with
   replacement, and the effect recomputed on each draw. Where the effect comes from a model fitted across states, it
   is that model's held-out prediction error instead (ADU's A3). Either way it is 90%, the 5th to 95th percentile.
   A state bootstrap for ADU would need the owner's OK.
2. **The centre is that same method's point estimate.** Otherwise the range and the centre answer different
   questions (see open question 1, for parking).
3. **The current-law range stays separate.** It is shown as its own grey band. The two are combined only if a total
   ("current law plus the reform") is shown, and then once, by simulation: a paired draw of each, never a sum of ends.
4. **Two-sided, with no zero floors.** A range may cross 0, and the low end is shown as measured.
5. **Coverage check.** Where a scenario has a test of how often its 90% range covers the truth, the range is widened to
   the measured factor. Parking's test 40 found 84% coverage, so its bootstrap range is widened ×1.17. A scenario
   with no coverage test says "coverage not yet checked" under its range. TOD has none yet; I can run one (hide each
   place, check whether the other 10 places' range covers it).
6. **Side lines are context, not scenarios.** Each is a thin dashed line across the range. It is labelled with what it
   is (the method and the places), plus its number and unit. A side line never changes the centre or the range.
7. **Every number states its unit.** Shares of the 124,000-home all-housing baseline are given beside, as now.

## The three reforms

| Reform | Centre | 90% range | Source of the range | Coverage |
| --- | ---: | --- | --- | --- |
| ADU (ADU permits: second homes on single-family lots, not all homes) | 10,492 | 8,100 to 13,700 (exact 8,055 to 13,666; A3, owner's OK pending) | A3 held-out prediction error (model fitted across states) | checked on 7 states, 7 of 7 inside; too few states to measure a factor, so factor 1 (largest miss Washington +0.19 against ±0.25) |
| TOD | 10,028 | 4,866 to 15,361 | place bootstrap of the 11 district places, 2,000 draws (`reference/tod_line_draws.csv`) | not yet checked |
| Parking | see open question 1 | −45,900 to +19,800 | bootstrap around the measured average of the 76 repeal places (audit: unwidened) | test 40: 84%; see open question 2 |

## Reasons-to-believe side lines

| Reform | Side lines (label: number) |
| --- | --- |
| TOD | Edge test, rezoned lots' own gain (5 places): 3,958. Average scaled to a 15% district (11 places): 12,521. Rezoning near new transit lines, 2×2 (9 places): 13,451. Same minus the growth already under way before the reforms: 5,624. |
| Parking | Measured average, 76 repeal places: −15,234. Median repeal place: −1,557. Oregon state mandate: about +16,800. Count model (negative binomial), all homes: +204. High ends from the improvement rounds: about 27,700 to 49,700. Not shown: San Diego, Chicago, and the count models that fail the pre-trend check. |
| ADU | Like Rhode Island and Oregon, the 2 slowest statewide-law states: 6,321 ADU permits. Median path of the 8 statewide-law states: 10,038. High end, near California (only California is higher): 19,784. The what-ifs 791 and 2,255 stay on How sure, off the chart. |

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

## Open questions for the owner

1. **Parking's centre.** The range comes from the measured average (−15,234), but the current central is 0 ("no
   measurable change"). Rule 2 would make the centre −15,234. The alternative is to keep 0 as the centre and show
   −15,234 as a side line, with a note that 0 sits inside the range. Recommendation: keep 0, labelled "no measurable
   change", because the 90% range includes 0 and that is the owner's current reading of the evidence (2026-11-01).
   This breaks rule 2 for parking only, and the note says so. The owner's call.
2. **Widening.** The audit says the parking band is unwidened, although its test found 84% coverage. Recommendation:
   show it unwidened, with the coverage note "this range covered the truth in about 84 of 100 tests". Use the
   widened version (about −51,100 to +25,800) only if the owner prefers a strict 90%.
3. **TOD coverage.** Run the hide-one-place coverage test before shipping? Recommendation: yes. It takes about
   20 minutes.

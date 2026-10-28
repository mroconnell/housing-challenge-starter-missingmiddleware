# Upzonings and downzonings together, with building pressure: plan written before fitting

Written 2026-10-28 by the TOD conductor, at the owner's request. He asked to use downzonings in the predictive modelling, because places where a cut does or does not bind "will help express variables in the predictive models". No unit below has been fitted, and no downzoning outside New York has been measured, before this file was committed. Changes go in section 7 with a date and a reason.

## 1. Question

If upzoned and downzoned land are pooled, with each case's building pressure before the change as a variable, can any of the 8 methods predict a held-out city's response per unit of allowed floor area changed better than the plain average?

## 2. Units

The sources are the case adapters already built: New York (pooled rezonings), Philadelphia (2012 remapping members), Chicago, Saint Paul and Seattle (two cases). Floor area ratio is the dose in all of them. Charlotte (height only) and Los Angeles (no floor-area data) are left out.

- **Up unit:** a case's or member's treated land, as in the permit cases.
- **Down unit:** a case's or member's eligible lots whose allowed floor area ratio fell and that lie within ½ mile of a rail or subway stop (National Transit Map), with at least 3 acres. Lots can be inside the reform, or in the adapter's "changed outside the reform" group, which is where most downzonings outside New York and Philadelphia sit.
  - For lots outside the reform, the change date is taken as the case's reform year, because the adapters record only that the change fell inside the window. These units are flagged and judged in a check without them.
- **Comparison:** the case's unchanged lots within ¼ mile (the "comparison" area), the same for up and down units of a case.

## 3. Outcome and variables

- **Outcome:** response per 1.0 of floor area ratio changed: (homes permitted per eligible acre per year, after minus before, unit minus comparison) ÷ (change in floor area ratio). Before is 6 years and after 5, from the case's own windows.
  - A cut that lowers building gives a positive response, the same sign as a rise that raises it.
  - A cut that doesn't bind gives about zero.
- **Weight:** unit acres.
- **Variables:**
  1. **Building pressure before:** homes permitted per eligible acre per year on the unit's own land in the before years. This is new, and the main reason for the test.
  2. **Same for the comparison land.**
  3. **Direction:** up = 1, down = 0.
  4. **Size of the change:** absolute floor area ratio change.
  5. **Allowed floor area ratio before.**
  6. Unit acres (log).
  7. City median rent and home value (inventory).

## 4. Methods and rule

- **Methods:** the 8 methods of [CENSUS_PREDICT_PLAN.md](CENSUS_PREDICT_PLAN.md), with the same settings, seed 20261027, and the multilevel line for uncertainty. Building pressure alone (weighted regression) is reported as its own line.
- **Leave-one-city-out.** Fold cities: New York, Philadelphia, Saint Paul, Seattle. Holdout: Chicago (never fitted).
- **Pass:** a method must beat the plain average in at least 3 of the 4 fold cities, on mean error, and on Chicago. A pass is checked for robustness (other seeds, largest unit out, equal weights).
- **Check:** the same rule with the "changed outside the reform" down units left out.

## 5. Also reported

- The down units' responses, with building pressure.
- Whether high pressure before goes with a large response in both directions: weighted correlation, shown, not judged.

## 6. Use

A robust pass would go to the owner as a way to place or size the TOD response by pressure (AQ-056). Otherwise this is context. No number changes without the owner.

## 7. Changes after writing

None yet.

Recorded 2026-10-28 while running:

1. **Down units found:** New York 6 inside rezonings and 9 changed outside them; Philadelphia 44; Saint Paul 1. Chicago and Seattle had no downzoned land near rail with at least 3 acres, so Chicago enters only through its up unit.
2. **The correlation line** first failed on a weighting bug in its own code. It was fixed and rerun; no model result changed.

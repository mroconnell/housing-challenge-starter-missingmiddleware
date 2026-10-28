# Lot-level model: which lots build after an upzoning, and does a project pay for itself? Plan written before fitting

Written 2026-10-28 by the TOD conductor, at the owner's request ("predicting the likelihood of a parcel to be developed instead of a city to gain permits"; then items 1 and 2 of the suggested reframes, "genius"). No lot-level model has been fitted before this file was committed. Changes go in section 9 with a date and a reason.

## 1. Question

For each lot near transit in the case cities: what is the chance that it gets a permit for new homes in the 5 years after an upzoning, and how many homes? How much does the upzoning raise that chance, and does the raise depend on lot traits that carry from city to city? Applied to Milwaukee and Madison lots, this gives where the extra homes would go and how many.

## 2. Lots

- **Cities and areas:**
  - each case's treated lots (allowed density rose) and comparison lots (unchanged), from the case adapters, with their permits matched to lots;
  - New York (17 pooled rezonings), Philadelphia, Charlotte, Saint Paul, Seattle (2 cases), Los Angeles (2 cases), Chicago;
  - Madison's 2023 overlay;
  - Milwaukee for application only.
- **Window:** each case's own 6 years before and 5 years after.
- **Lots kept:** eligible lots (residential, mixed or commercial use; no parks or institutions), as in the cases.

## 3. Outcome (two parts)

1. **Builds:** 1 if the lot has at least one permit for new homes in the 5 after years, else 0.
2. **Size:** homes permitted on the lot in those years, if it builds.

The same two outcomes in the 6 before years are used as a lot trait (section 4, item 6) and for the before-and-after comparison.

## 4. Lot traits

Each trait is used where the city's public lot data has it. Missing values get the city median plus a "missing" flag.

1. Lot area.
2. Existing homes on the lot (before the window).
3. Building age (year built).
4. **Building value ÷ land value** (assessor). A low ratio means a cheap building on valuable land: a "soft site".
5. Use class: vacant, parking, commercial, single-family, multifamily.
6. Homes permitted on the lot or its block in the before years.
7. Distance to the nearest rail or rapid-bus station.
8. Allowed floor area before, and the gain from the upzoning (0 for comparison lots).
9. **Does a project pay for itself?** (section 5).
10. City market: median rent (census tract, before the window).

**Data to fetch:** assessor values and year built where the case files lack them:
- Cook County (Chicago);
- Ramsey County (Saint Paul);
- Mecklenburg County (Charlotte);
- Philadelphia property assessments;
- King County (Seattle);
- Los Angeles County.

New York's tax-lot data already has them, and Wisconsin's statewide parcels and Milwaukee's property file have land and improvement values. All are public; no owner names are kept and no lot ids are committed.

## 5. Does a project pay for itself? (feasibility)

For each lot, under the rules before and after:

- **Homes allowed** = allowed floor area ÷ floor area per home (the cases' measured figures; New York 1,000 sq ft where unmeasured).
- **Value of a new building** = homes allowed × floor area per home × tract median rent per sq ft × 12 ÷ a cap rate of 5%.
- **Cost** = homes allowed × construction cost per home. That is the Census permit survey's reported construction value per home for buildings of 5 or more homes, in that city and year, plus the lot's assessed land and building value.
- **Pays** = value ÷ cost. The trait is the ratio before and after, and whether it crosses 1.0.

Rents and costs are city- or tract-level and approximate. This trait asks whether the limit is likely to bind, not for an exact profit.

## 6. Methods

- **Part 1 (builds):** logistic regression and gradient boosting.
- **Part 2 (size, given building):** weighted regression and gradient boosting.
- **The upzoning's effect** = predicted homes with the "after" rules minus with the "before" rules, for the same lot.
- **Plain baseline:** each city-area's before-years build rate, applied to every lot in it, with the cases' measured difference-in-differences.
- **Leave-one-city-out.** Holdouts never fitted: Chicago and Madison's 2023 overlay.

## 7. Pass rule

The lot model counts as better if it beats the plain baseline on held-out cities in both of these:

- **Total extra homes** in the upzoned area: mean absolute error across fold cities, and on Chicago and on Madison separately.
- **Where homes go:** the area under the ROC curve for "builds" on held-out cities is at least 0.70. That is, it ranks a lot that built above one that didn't 70% of the time.

**Robustness:** another seed, and the largest project left out.

## 8. Use

- **A pass gives the tool two things:**
  - a lot-by-lot map of likely building in Milwaukee and Madison;
  - a model-based extra-homes total under the law, and under a sliver-sized law.
- These go to the owner as a candidate (AQ-059).
- A fail leaves the current scenarios, with the lot map shown as context if the ranking part passes.

## 9. Changes after writing

1. **2026-10-28, before any data was fetched: values only from before the window.** Today's assessor values would leak the outcome, because a lot that was rebuilt now has a high building value. So the building ÷ land value trait, and the land and building cost in section 5, use only snapshots dated before each case's window:
   - New York: MapPLUTO archives;
   - Chicago: Cook County assessed-value history;
   - Seattle: King County value history;
   - Philadelphia: assessment history, for members whose window starts in 2014 or later;
   - Madison and Milwaukee: assessor history where available.

   Los Angeles, Charlotte and Saint Paul have no public history, so they get the "missing" flag for this trait. Year built is likewise taken only from before-window snapshots.
2. **2026-10-28, owner's decision: lots inherit their neighbourhood's averages.** The owner confirmed that each lot takes its census tract's median rent, median home value and median household income. These come from the 5-year American Community Survey ending the year before the case's window, as in the 91-variable test.
3. **2026-10-28, before fitting: the pays-for-itself trait is simplified.** Assessed values are not comparable across cities: New York, Cook County and others assess different shares of market value, and most cities have no pre-window values. So section 5 becomes a **rent-to-cost ratio**:

   (tract median gross rent × 12 ÷ 5% cap rate) ÷ (Census permit-survey construction value per home in buildings of 5 or more homes, in that city, the year before the reform).

   Per lot, it is computed under the old and new rules as that ratio times the share of the lot's allowed homes not already built. The building ÷ land value trait stays where pre-window values exist (New York, Chicago), with a missing flag elsewhere.
4. **2026-10-28, before fitting: duplicate lots are down-weighted.** A lot can sit in the comparison area of several New York or Philadelphia rezonings. Each appearance gets weight 1 ÷ (number of appearances of that lot within its city).
5. **2026-10-28, before fitting: baseline and errors made concrete.**
   - **Actual extra homes for a held-out city** = homes permitted on its upzoned lots after, minus upzoned acres × the comparison lots' homes per acre after, minus the same difference before.
   - **Baseline:** the training cities' acre-weighted mean of that difference per upzoned acre, times the held-out city's upzoned acres.
   - **Model:** the sum over upzoned lots of predicted homes under the new rules minus under the old rules.
6. **2026-10-28, owner's decision, recorded before the fit results were read: the pass rule is the total only.** The owner wrote: "we don't actually care about lot building accuracy if the regional total is accurate". The lot ranking (area under the ROC curve) is reported but no longer part of passing. The model passes if it beats the plain baseline on total extra homes, both on the mean error across fold cities and on Chicago and Madison separately.

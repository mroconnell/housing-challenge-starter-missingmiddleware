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
7. **2026-10-28, after the first run, which overflowed: project size gets a ceiling for each lot.** In the first run the linear size model's predictions exploded on Charlotte's lots (exponents beyond the training range), giving absurd totals.
   - At the owner's direction, each lot's ceiling now comes from the data: the homes its zoning allows (lot area × allowed floor area ratio ÷ 1,000 sq ft per home), times the stretch real projects reached.
   - The stretch is the 99th percentile, among building lots in the training cities, of homes permitted ÷ homes allowed. It covers bonuses and variances.
   - This applies to both models. Nothing else changed.
8. **2026-10-28, after the first results, owner's request: more strict holdout cities.** Bellevue (BelRed, 2009) is added as a third holdout, never fitted, from its case adapter (lots, zoning by ordinance, permits with units). Minneapolis cannot be added: its Hiawatha case has no boundary layer and no unit counts before 2010. The pass rule is unchanged: the total must beat the plain average on the fold mean and on each holdout. The fold cities and their results are unchanged.
9. **2026-10-28, owner's request, written before running: all 91 census variables on every lot.** Each lot inherits its tract's values for all 91 variables of the all-variables test ([ALLVARS_PLAN.md](ALLVARS_PLAN.md)), from the 5-year ACS ending the year before its case's reform. Ratios are the tract's numerator ÷ denominator; medians are the tract value.
   - They are added to the 22 lot traits, and the boosted two-part model is refitted.
   - Same holdouts (Chicago, Madison, Bellevue) and the same pass rule.
   - Reported as a separate run ("all variables"), beside the 22-trait run, with the traits ranked by how much the holdouts' ranking worsens when each is shuffled.
10. **2026-10-28, owner's request, written before running: all 8 methods on lots ("run C").** Each method gets a two-part lot version: one model for the chance a lot builds, one for homes if it builds.
    1. Weighted regression: logistic plus linear (the existing simpler model).
    2. LASSO: L1-penalised logistic plus L1 linear, penalty fixed by cross-validation on a 20% sample of the training lots.
    3. Elastic net: same with L1 ratio 0.5.
    4. Regression tree: depth 3, at least 200 lots per leaf.
    5. Random forest: 200 trees, at least 50 lots per leaf.
    6. Gradient boosting: as already run.
    7. Causal forest: approximated by separate random forests for upzoned and unchanged lots (a "T-learner"); the effect is the upzoned forest's prediction minus the unchanged forest's, on upzoned lots.
    8. Nearest neighbours: the 50 nearest training lots on standardised traits.

    Same traits as the all-variables run, same holdouts (Chicago, Madison, Bellevue), same pass rule. Each method is judged separately. The best of 8 is reported with a warning that picking the best of many looks better than it is.
11. **2026-10-28, owner's question, written before runs B and C: two "many stalls" traits.** Both vary lot to lot.
    - **Share of upzoned land within ½ mile:** acres of upzoned lots within 805 m of the lot's point ÷ acres of all lots in the table within 805 m, counted within the same case.
    - **Rail and rapid stops within 1 mile:** National Transit Map stops within 1,609 m of the lot.

    Both are added to the features of runs B and C. Run A (already running) does not have them.
12. **2026-10-28, after runs A–C: a units error is fixed before any rerun.** The lot table's "allowed density" column mixed units:
    - floor area ratio in New York, Chicago, Madison, Saint Paul, Seattle and Bellevue;
    - feet of height in Charlotte;
    - an ordering of districts (not a dose) in Philadelphia and Los Angeles.

    Charlotte's 40-foot-to-75-foot changes were read as +35 floor area ratio, which is why linear models blew up on Charlotte. Fix:
    - The raw level is replaced by its rank within the city (unit-free).
    - The change becomes the relative change (after ÷ before − 1), used only in floor-area-ratio cities, with an "upzoned" flag and a "relative change known" flag everywhere.
    - The homes-per-lot ceiling uses zoning capacity only in floor-area-ratio cities. Elsewhere it uses the training cities' 99th-percentile homes per acre on building lots.

    Runs A–C are reported as they ran (superseded). The owner asked for questions before rerunning.
13. **2026-10-28, owner's decision, before any rerun: two reruns, two rules.**
    - **Run D** repeats runs A, B and C with the units fix (item 12) and nothing else.
    - **Run E** builds all 8 methods the causal-forest way, so no method can ignore the reform:
      - one model is fitted on upzoned training lots and one on unchanged training lots;
      - each predicts the lot's change in homes permitted (after minus before);
      - a city's extra homes = the sum over its upzoned lots of the upzoned model's prediction minus the unchanged model's.

      Methods: weighted regression, LASSO, elastic net, depth-3 tree, random forest, boosting, nearest neighbours. The causal forest is the random-forest version.
    - **Rules.** Both are reported for every method in both runs.
      - **Old rule:** lower fold mean error than the plain average, and closer on each of Chicago, Madison and Bellevue.
      - **New rule:** lower fold mean error than both the plain average and a model that always guesses zero, and closer than the plain average on at least 2 of the 3 holdouts.

      Run D is judged by the old rule and run E by the new one; the other rule is shown beside each.
    - **Note:** the lot table now carries the two "many stalls" traits, so run D's repeat of run A includes them too. That is the only difference from run A apart from the units fix.
14. **2026-10-28, owner's direction, written before any rerun: rapid-bus stops added, and only lots within ½ mile of a stop.** The stop list was rail only, so lots near rapid bus were coded as far from transit:
    - Madison's upzoned lots were coded about 96 km from a stop (its rapid bus is not rail);
    - Los Angeles's Warner Center lots about 7 km (the G Line is a busway);
    - in Philadelphia 37% of upzoned lots were beyond ½ mile, because many rezonings were not transit-based.

    Owner: "TOD is meant to be within a certain distance of transit", so this is coded, not trained on. Fix:
    - **Stops** = the existing National Transit Map rail stops, plus Los Angeles Metro's 17 G Line busway stations from the same map, plus Madison's rapid-bus stops from `reference/tod_stops.csv` (the same map, the Wisconsin benchmark's list). Stops are as of 2026, as for rail; Madison's and Bellevue's lines opened after their reforms but were planned at the time.
    - **Lots kept:** upzoned and comparison lots within 805 m (½ mile) of a stop, as in the Wisconsin benchmark's rail and rapid ½-mile rung.
    - Distance to station, stops within 1 mile and share of upzoned land within ½ mile are recomputed on the kept lots.
    - Runs D (all three parts) and E are repeated on the kept lots, tagged "half mile", with both rules. Everything else is unchanged.
    - The run D 8-method part was stopped before finishing, as it would be superseded; run E's first version is let finish and reported as superseded.
15. **2026-10-28, owner's decisions after the acres audit (`reference/tod_audit_acres.csv`), written before any rebuild.**
    - **Industrial and institutional land whose zoning changed to allow homes is upzoned land** (owner: "Brownfield development and other zoning conversions are part of the mix"; AQ-060). In the lot table, a lot inside a reform whose zoning before was industrial or institutional, and whose zoning after allows homes, is treated. Its homes before are its census homes (usually 0). This adds about 587 acres in Charlotte and 232 in Los Angeles's Cornfield Arroyo Seco.
    - **Lots inside a reform whose allowed density did not rise are kept, not dropped** (owner: "using both numbers … letting the predictive model sort out the relevant one"). They get `in_reform = 1`, `upzoned = 0`, and are fitted with the comparison lots. The actual extra homes and the model's total still count upzoned lots only; the in-reform-not-rising lots enter only as training rows. Madison has about 2,047 such eligible acres, Charlotte about 138 ("already at the law").
    - **Existing homes on every lot** from 2010 census blocks: each block's 2010 homes are shared among its lots in the lot table by lot area. New York keeps its lot counts, with the census value beside it.
    - Unchanged: single-family-use lots in Madison stay out (the overlay did not change single-family rules, as in the Madison test); parks and campuses stay out; the ½-mile rule of item 14 stays.
    - Runs D and E are repeated on the rebuilt table, tagged "rebuilt". The ½-mile runs already going are let finish and reported as an intermediate step.
16. **2026-10-28, owner's direction, written before the rebuild ran ("those are TEN variables we are supposed to be including"): every lot is kept with a label for what the reform did to it.** This replaces item 15's keep-or-drop choices; item 15's industrial and campus conversions and census homes stay.
    - **Lots kept:** every lot inside the reform, and every lot in its comparison area, whatever its class; then item 14's ½-mile rule.
    - **Label (`lot_group`)**, one per lot: upzoned; upzoned from industrial; upzoned from campus; in the reform but density did not rise; in the reform and already allowed it; single-family left untouched; campus or park left unchanged; rezoned again in the window; other not eligible in the reform; comparison eligible; comparison industrial; comparison campus or park; other not eligible.
    - **Features:** the label (one column per group), and each reform's share of its acres in each in-reform group.
    - **Counted extra homes are unchanged in concept:** homes on upzoned lots (all three upzoned groups) against eligible comparison lots, minus the same before. Other groups are training rows only.
    - Example seen while testing the code on Charlotte (before any fit): "rezoned again in the window" holds 157 acres with 1,461 homes permitted after, and "upzoned from industrial" 563 acres with 1,710 homes.
17. **2026-10-28, owner's suggestion, written before the rebuild finished: rare lot groups are pooled.** A lot group found in fewer than 3 of the non-holdout cities becomes one "rare" group, and its reform shares are added into one "rare share". A holdout's group that training never saw is therefore "rare", not a new unknown column. Which groups are rare is decided on the six non-holdout cities together (not refitted per fold), and is printed with the results.
18. **2026-10-28, after the ½-mile runs, before the rebuilt runs: Bellevue's density levels are flags, not floor area ratios.** Bellevue's case adapter codes "before" as 0 and "after" as 1 (allowed housing or not). The lot model read these as floor area ratios, so each big BelRed lot looked like it gained a ratio of 1, which drove the boosted size model to about 300 homes per lot (Bellevue guessed 8,934 extra homes, actual −113). Bellevue is removed from the floor-area-ratio cities: it gets the level rank, the upzoned flag and the per-acre ceiling, like Charlotte, Philadelphia and Los Angeles. The flag check now flags a floor area ratio that takes only the values 0 and 1. Nothing else changes.
19. **2026-10-28, written before running: robustness checks of section 7 for the first method that passed.** Boosting with all 91 census variables (run D-B) passed the old rule on the rebuilt table (`reference/tod_lot_model_results_runD_allvars_rebuilt.csv`). Before it is offered to the owner as a candidate prediction line, it is rerun twice, with everything else unchanged:
    - **Another seed:** random seed 7 instead of 20261027.
    - **Largest project out:** in each city, the lot with the most homes permitted after is removed, from both the actual extra homes and the training rows.

    It stays a candidate only if it passes the old rule in both. Many versions have been tried (runs A to E and their fixes), so a single pass could be luck; this is stated with any result.
20. **2026-10-28, written after the rebuilt runs finished, before running the checks: robustness for the causal forest, and D-B's result.**
    - **D-B (boosting, 91 variables) robustness, item 19:** another seed passes the old rule; largest project out fails it (Madison error 721 homes vs the plain average's 596), though it still passes the new rule. Under item 19's own test, D-B is **not** a candidate.
    - **Causal forest** (separate forests for upzoned and unchanged lots) passed the old rule on the rebuilt table, in run D-C and in run E (the same method in both). The same two checks of item 19 are run on it, with only that method: seed 7, and each city's largest project out. It becomes a candidate prediction line only if it passes the old rule in both.
21. **2026-10-29, written before building anything for Wisconsin: applying the causal forest to the Wisconsin law.** The causal forest passed the old rule on the rebuilt table and both robustness checks (`reference/tod_lot_model_results_runE_rebuilt*.csv`). It is applied to Milwaukee and Madison as a candidate prediction line for the owner (AQ-059), with no scenario number changing until the owner decides.
    - **Lots:** every Milwaukee and Madison parcel from the station-area build (`scripts/build_tod_station_areas.py`, same loaders and the same law rules), today's zoning as "before" and the modelled law as "after".
    - **Upzoned:** eligible lots in the main definition's station areas whose allowed homes rise under the law (capacity gain > 0). Lot groups as in item 16: in the law area but not rising → "density did not rise"; not eligible → by class; lots outside the law area within ½ mile → comparison.
    - **Density traits:** floor area ratio before = current allowed homes × floor area per home ÷ lot area; after = the law's allowed homes on the same basis. Milwaukee is treated as a floor-area-ratio city.
    - **Other traits:** as in training, from the latest data before 2027: 5-year ACS 2020–2024 for rent, value, income and the 91 variables; homes on the lot from the City records (Milwaukee MPROP, Madison parcels) as the census-homes trait; distance and stops within 1 mile from the Wisconsin qualifying stops (`reference/tod_stops.csv`, rail and rapid and 15-minute bus, as the law defines them); construction cost from the Census permit survey for 2024.
    - **Building before:** Madison from its permits with unit counts (2019–2024). Milwaukee's open permits carry no unit counts, so homes built 2019–2024 come from MPROP (homes on lots with year built in those years). This is a known difference and is reported.
    - **Model:** the causal forest refitted on all 9 case cities (no holdouts), three versions (seed 20261027, seed 7, largest project out). Extra homes over 5 years = the sum over upzoned lots of the upzoned forest's prediction minus the unchanged forest's.
    - **Range:** the three versions' lowest and highest, and a second range from the model's held-out misses: the median ratio of |miss| to the plain average's |miss| across the 9 leave-one-out cities, applied around the point estimate. Both are reported; neither is a statistical interval.
    - **Flags:** the standing flag check is run on the Wisconsin lots against the training cities, and every flag is reported with the estimate.
    - **Shown beside:** the current scenarios for Milwaukee and Madison (`reference/tod_model_by_area.csv`), and the statewide 171 / 2,509 / 17,148.
22. **2026-10-29, while building the Wisconsin lot table, before any prediction: two practical changes to item 21.**
    - Tract traits come from the 5-year ACS 2018–2022, the latest release the all-variables readers hold locally (the same release Madison's training lots use), not 2020–2024.
    - The Wisconsin law upzones most lots near its stops: 130,190 Milwaukee lots (21,208 acres) and 37,823 Madison lots (11,776 acres) count as upzoned. This is far broader than any training case; the flag check will show it, and the result is read with that in mind.
23. **2026-10-29, owner's agreement, written before rescoring: each reform is scored against its own comparison land.** Actual extra homes were computed per city with one pooled comparison area. Where a city has several reforms (New York 17, Philadelphia 83, Seattle 2, Los Angeles 2), one reform's neighbours set the bar for another: Cornfield Arroyo Seco's comparison land (297 homes after, near Chinatown) set it for Warner Center, about 25 miles away, turning Los Angeles's total to −1,449 homes (Warner Center alone +165, Cornfield −585).
    - **Fix:** a city's actual extra homes = the sum over its reforms (case units) of each reform's own difference: upzoned homes after minus upzoned acres × its own comparison homes per acre after, minus the same before. A reform with no comparison land contributes its upzoned change with no adjustment, and is listed.
    - The plain average uses the same per-reform actuals (training cities' sum of actual extra ÷ sum of upzoned acres, × the city's upzoned acres).
    - Model guesses are unchanged (they sum predicted lot effects and never used the pooled comparison), so every rebuilt run is **rescored** from its saved city guesses, without refitting, and both rules are reapplied. The original scores stay in the files as run; rescored results are written beside them (`*_rescored.csv`).
24. **2026-10-29, found in the owner's methodology review, written before any refit: before and after windows have different lengths.** Homes "before" are summed over 6 years and homes "after" over 5 in every case except Madison (3 after years, 2023–2025) and Saint Paul (1 before year, 2010). Subtracting a 6-year count from a 5-year count biases each lot's change, and Madison's 3-year actual was compared with 5-year guesses.
    - **Fix:** both are put on a 5-year basis before any difference is taken: homes before × 5 ÷ before years; homes after × 5 ÷ after years. This applies to the causal forest's outcome (change per lot), to the actual extra homes and the plain average (item 23's per-reform scoring), and to the Wisconsin application.
    - Saint Paul's single before year is noisy; it stays, flagged, as in the case results.
    - Build-or-not and size outcomes (used by the other methods, not the causal forest) are unchanged.
    - The causal forest (three versions) is refitted and rescored; the "does it pay" runs and the Wisconsin estimate are restarted on the fixed outcome. Earlier causal-forest scores stay in their files as run.
25. **2026-10-29, after the independent audit ([LOT_MODEL_AUDIT_2026-10-29.md](LOT_MODEL_AUDIT_2026-10-29.md)), written before any refit.** Fixes, all applied together:
    1. **Causal forest sees the upzoning:** the upzoned forest is fitted on upzoned lots' traits under the rules after (including relative gain and floor area after) and predicts upzoned lots under the rules after; the unchanged forest uses the rules before, as now. This is a design change made after results were seen, so the method is judged again by both rules and the item 19 checks, and this is stated with any result.
    2. **Use traits dropped** from the causal forest.
    3. **Wisconsin lots kept apart** from training lots in duplicate-lot keys and within-city ranks.
    4. **Minimum comparison land:** a reform whose eligible comparison land is under 25% of its upzoned acres is scored against all eligible comparison land in its city; such reforms are listed.
    5. **Construction cost in 2024 dollars** (CPI-U, as rent).
    6. **Early reforms flagged:** lots whose tract traits or 2010 homes come from after their reform get a flag trait; a check run leaves those reforms out.
    7. **Stop traits on rail and rapid stops only,** in training and in Wisconsin (the 15-minute bus rule still decides which Wisconsin lots the law upzones).
    8. **Fill values from training rows only** (non-holdout case cities), frozen for Wisconsin.
    9. **Wisconsin homes on lot** shared from 2020 census blocks by lot area, as training.
    10. **Milwaukee building-before** from any lot with homes built 2019–2024.
    Then: the causal forest's three versions (item 19), rescored with item 23–24 scoring; the check without early reforms; then the Wisconsin estimate.
26. **2026-10-29, owner's question ("the places that look extremely good, are we making mistakes there?"), written before any change.** Checking the top-scoring reforms found homes placed on lots too small to hold them: 94 building lots show more than 500 homes per acre (one 0.1-acre lot with 835 homes, one 0-acre lot with 631), holding 14,324 of the table's 70,870 homes after (New York 10,413; Chicago 2,816; Philadelphia 794; Seattle 301). These are permit locations landing on a sliver, a condominium billing lot or one lot of a later-merged site. City totals are little affected when the right lot group is hit, but the model learns that tiny lots build hundreds of homes.
    - **Fix:** a lot whose homes before or after exceed 500 per acre hands them to the nearest lot in the same reform, within 60 m of its point, that is big enough to hold them at 500 per acre; ties go to the same lot group. If none qualifies, the homes stay and the lot is flagged. The number of homes moved, and any that cross between upzoned and comparison land, are reported by reform.
    - Applied to the rebuilt ½-mile table before the item 25 refit. Greenpoint–Williamsburg's and the other high scores are rechecked after it.

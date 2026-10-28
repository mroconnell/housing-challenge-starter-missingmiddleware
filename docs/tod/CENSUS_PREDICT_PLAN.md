# Prediction tools on the census set, and New York's downzoned lots: plan written before running

Written 2026-10-28 by the TOD conductor, at the owner's request ("rerun the 8 prediction methods on this 21 reform set with pre-reform density and holdouts named in advance. Try the NY downzoned lots mirror test too"). Neither test has been run before this file was committed; the commit is the timestamp. Changes go in section 6 with a date and a reason.

**Disclosure.** Each reform's census result is already known ([CENSUS_CASES_RESULTS.md](CENSUS_CASES_RESULTS.md), section 6). The holdouts protect against tuning a model to them, not against knowing them.

## 1. Part A: the 8 prediction methods on the census set

### Units and outcome

- **Units.** The 21 census-measured reforms of CENSUS_CASES_RESULTS section 6, plus Phoenix's 14 acres; Charlotte is left out (land only). Each reform is one unit; a New York rezoning is one unit.
- **Measured uniformly for this test.** Blocks are placed by centre point; the comparison land is the case's own ring:
  - ¼ mile for the cases with net-effect files (Saint Paul, Seattle, Los Angeles, Chicago, Philadelphia, New York);
  - ½ mile for the boundary cases (Jersey City, Milpitas, Phoenix, Bellevue, Austin, Tysons, Salt Lake City, Seattle Roosevelt).
- **Outcome:** net homes added from 2010 to 2020 per acre per year, upzoned land minus comparison land.
- **Weight:** upzoned acres, as in the earlier tests.

### Variables

All are known before each reform; none uses race or ethnicity.

1. **Pre-reform density:** homes per acre on the upzoned land in 2010, entered as its logarithm (+1).
2. **Size of the upzoned area:** acres, logarithm.
3. **Comparison land's own density in 2010** (homes per acre, logarithm +1).
4. **City median gross rent and median home value**, from the case inventory ([reference/tod_cases.csv](../../reference/tod_cases.csv)), in 2024 dollars as recorded there.
5. **City size:** homes in 2010 (2010 Gazetteer), logarithm.
6. **Rail opened after 2009 within the area** (yes or no): Salt Lake City, Seattle (North Beacon Hill and Othello opened 2009, so no), Milpitas (2020), Bellevue (2024), Tysons (2014). Set from the case inventory and research notes.

### Methods and rule

- **The 8 methods of [TRAITS_RESULTS.md](TRAITS_RESULTS.md):**
  - weighted regression;
  - LASSO;
  - elastic net;
  - regression tree (depth 2);
  - random forest;
  - gradient boosting;
  - honest causal forest;
  - nearest neighbours (k = 5).

  The multilevel model is reported as a ninth line, as before. All use the same settings and seed 20261027.
- **Leave-one-city-out.** New York's 6 rezonings, Seattle's 3 and Los Angeles's 2 each count as one city, so a city's units are never split between training and testing.
- **Holdouts, never fitted:**
  - Chicago, the standing holdout;
  - Milpitas, the earlier census holdout.
- **Fold cities:** New York, Seattle, Los Angeles, Saint Paul, Philadelphia, Jersey City, Phoenix, Bellevue, Austin, Tysons, Salt Lake City (11).
- **Pass rule (same as before):** a method passes only if it beats the plain average (acre-weighted mean of the training units) in at least two thirds of the fold cities (8 of 11), on the mean error across fold cities, and on each holdout by itself.
- **A pass is also checked for robustness** (other seeds, each fitted city's largest unit left out, equal weights) before it counts.
- **Pre-reform density alone:** the weighted regression with only variable 1 is reported as its own line, because the owner asked about it.

### How it is used

A robust pass would be brought to the owner as a candidate for narrowing the TOD range (AQ-056). A fail means the census set, like the permit set, cannot tell in advance which places respond more. No number changes without the owner (AQ-055).

## 2. Part B: New York's downzoned lots, the mirror test

### Question

In New York's 2003–2013 rezonings, did lots whose allowed density fell get fewer new homes afterwards than unchanged lots nearby?

### Areas and measures

- **Downzoned lots:** lots in a rezoning whose allowed residential floor area fell, measured with the same before-and-after MapPLUTO zoning and the same floor-area rules used for the upzoned lots in the New York case ([CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md)). Lots must be within ½ mile of a subway or rail station, by the case's own station layer.
- **Comparison lots:** the case's unchanged lots within ¼ mile of the rezoning, as for the upzoned test.
- **Permit measure:** difference in differences of homes permitted per eligible acre per year, downzoned against comparison, 6 years before against 5 years after. Rezonings are stacked by event year, as in the pooled New York case. 90% interval from resampling projects, 2,000 draws, seed 20261033.
- **Census measure:** net homes added from 2010 to 2020 per acre, downzoned lots against comparison lots. Only rezonings adopted 2008–2013 are used (centre-point blocks).
- **Mirror comparison:** the downzoned effect is set beside the upzoned effect from the same rezonings, per 1.0 of floor area ratio changed where floor-area change is available.

### Expectation

None written down. Downzonings in New York often fixed lower-density blocks in place where little was being built, so a small effect would not be surprising.

## 3. Outputs

- `reference/tod_census_predict.csv`: one row per method.
- `reference/tod_nyc_downzoning.csv`.
- Results: `docs/tod/CENSUS_PREDICT_RESULTS.md`.

## 6. Changes after writing

None yet.

# Prediction tools on the census set, and New York's downzoned lots: results

Run 2026-10-28 against [CENSUS_PREDICT_PLAN.md](CENSUS_PREDICT_PLAN.md) (changes in its section 6). Code: [scripts/run_tod_census_predict.py](../../scripts/run_tod_census_predict.py), [scripts/run_tod_nyc_downzoning.py](../../scripts/run_tod_nyc_downzoning.py). Outputs: `reference/tod_census_predict*.csv`, `reference/tod_nyc_downzoning*.csv`.

## Summary

- **Part A: no method passes.** Pre-reform density alone fails too. On 21 census-measured reforms in 13 cities, none of the 8 methods predicts a city's response better than the plain average in enough cities. That is the same result as the permit-based tests. Places differ in ways these variables do not capture.
- **The useful number from Part A is the multilevel model's range for a new city:** +0.09 to +0.80 extra net homes per acre per year on upzoned land, centred on +0.44.
- **Part B: downzoning near stations did almost nothing; upzoning in the same rezonings did a lot.**
  - **Downzoned lots near stations:** −0.06 homes permitted per acre per year (90% interval −0.26 to +0.15), on 402 acres.
  - **Upzoned lots in the same rezonings:** +2.07 (1.61 to 2.55), on 1,255 acres.
  - **Per 1.0 of floor area ratio:** −0.05 for a cut and +0.64 for a rise.
- **Nothing changes.** The finalized TOD numbers (AQ-055) stay at 171, 2,509 and 17,148.

## Part A: the 8 methods

Units: 21 reforms (New York 6, Seattle 3, Los Angeles 2, one each elsewhere) and Phoenix's 7 acres. Outcome: net homes per acre per year, 2010–2020, upzoned minus comparison land. Holdouts: Chicago and Milpitas.

| Method | Fold cities better (of 11; 8 needed) | Mean error: method / plain average | Beats average on Chicago | On Milpitas | Verdict |
| --- | ---: | --- | --- | --- | --- |
| Weighted regression | 3 | 0.666 / 0.268 | no | yes | fail |
| LASSO | 0 | 0.290 / 0.268 | no | no | fail |
| Elastic net | 0 | 0.342 / 0.268 | no | no | fail |
| Regression tree | 5 | 0.312 / 0.268 | yes | no | fail |
| Random forest | 4 | 0.268 / 0.268 | no | no | fail |
| Gradient boosting | 5 | 0.385 / 0.268 | yes | no | fail |
| Honest causal forest | 5 | 0.277 / 0.268 | no | yes | fail |
| Nearest neighbours | 2 | 0.304 / 0.268 | no | no | fail |
| Pre-reform density alone | 5 | 0.277 / 0.268 | no | no | fail |

- **The causal forest came closest**, as it did on the permit set. It beat the average in 5 of 11 cities and on Milpitas, but not on mean error or Chicago.
- **Pre-reform density doesn't sort places.** Big gains came at both ends: New York's 161st Street (37 homes per acre in 2010) and Milpitas (1.5). Bellevue started near zero and gained moderately.
- **Multilevel model, all 11 fold cities:** the overall mean is +0.44 extra net homes per acre per year. A new city's own mean is likely between +0.09 and +0.80 (90%). That is the honest "how sure" for a single place's per-acre response.

## Part B: New York's downzoned lots near stations

Lots inside the 2003–2013 rezonings whose allowed residential floor area fell, within ½ mile of a subway or rail stop. They are compared with the rezonings' unchanged lots within ¼ mile, and set beside the upzoned lots of the same rezonings.

| Side | Acres | Homes permitted per acre per year, after vs before, minus comparison (90% interval) | Average change in floor area ratio | Per 1.0 of floor area ratio |
| --- | ---: | --- | ---: | ---: |
| Downzoned | 402 | −0.06 (−0.26 to +0.15) | −1.24 | −0.05 |
| Upzoned | 1,255 | +2.07 (+1.61 to +2.55) | +3.24 | +0.64 |

- **The response is lopsided.** Cutting density near stations barely lowered building, while raising it raised building a lot. The upzoned figure per 1.0 of floor area ratio (+0.64) matches the pooled New York case (+0.67).
- **Why:** New York's downzonings mostly locked in low-rise blocks where little was being built anyway: Park Slope's side streets, Kew Gardens–Richmond Hill and Jamaica's residential blocks. A cap that doesn't bind changes nothing.
- **For Wisconsin:** removing a limit matters only where the limit binds. This supports the model's rule of adding homes only where the law allows more than current zoning, and never subtracting.
- **Census side (shown, not judged):** only 4 rezonings with downzoned land were adopted 2008–2013. Their census differences range from −4.9 to +3.6 net homes per acre over the decade, with wide intervals. East Fordham Road's 2.4 acres had no homes in 2010.

## Part B, rezoning by rezoning: where did a downzoning cost homes? (added 2026-10-28, after the results, at the owner's question)

Not pre-registered. The same estimate for each rezoning's downzoned lots near stations: homes permitted per acre per year after against before, minus the comparison lots. Output: `reference/tod_nyc_downzoning_by_rezoning.csv`.

| Rezoning (adopted) | Downzoned acres | Homes permitted on them: 6 years before / 5 years after | Difference per acre per year (90% interval) | About this many homes a year |
| --- | ---: | --- | --- | ---: |
| Third Ave–Tremont Ave, Bronx (2010) | 30 | 407 / 28 | **−1.90 (−3.57 to −0.55)** | **−57** |
| Jamaica Plan, Queens (2007) | 97 | 330 / 149 | −0.15 (−0.38 to +0.07) | −14 |
| Park Slope, Brooklyn (2003) | 171 | 66 / 177 | +0.07 (−0.10 to +0.25) | +11 |
| Greenpoint–Williamsburg, Brooklyn (2005) | 40 | 42 / 117 | +0.41 (+0.02 to +0.86) | +16 |
| Kew Gardens–Richmond Hill, Queens (2005) | 48 | 25 / 46 | +0.03 (−0.14 to +0.19) | +1 |
| Seven others | under 3 each | almost none | | about 0 |

- **One clear opportunity cost: Third Ave–Tremont.** Builders were active on these lots before the cut (407 homes in 6 years), and building nearly stopped afterwards (28 in 5 years), far more than on the unchanged lots nearby. That is about 57 fewer homes a year, roughly 290 over five years, on 30 acres.
- **Jamaica points the same way** (330 before, 149 after), but its interval includes zero.
- **Where the cut didn't bind, nothing was lost.** In Park Slope, Kew Gardens and Greenpoint, building on downzoned lots was low before and rose afterwards with the market, as on the unchanged lots.
- **The pattern:** a cut costs homes where it binds, meaning builders were already pushing past the new limit. That is the mirror image of the upzoning rule the model uses.
- **Caution:** this was looked for after the pooled result, among 12 rezonings. One clear case out of 12 could partly be chance, and Third Ave–Tremont's before years (2004–2009) were a building boom in the Bronx.

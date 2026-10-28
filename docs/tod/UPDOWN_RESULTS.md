# Upzonings and downzonings together, with building pressure: results

Run 2026-10-28 against [UPDOWN_PLAN.md](UPDOWN_PLAN.md) (changes in its section 7). Code: [scripts/run_tod_updown.py](../../scripts/run_tod_updown.py). Outputs: `reference/tod_updown_units.csv`, `reference/tod_updown_models.csv`.

## Summary

- **No method passes.** Pooling 99 upzoned and 60 downzoned units, and adding building pressure before the change, still does not predict a held-out city's response better than the plain average.
- **Building pressure alone comes closest of all methods so far.** Its mean error is below the plain average's (0.210 against 0.221) and it beats the average on Chicago, but it wins in only 2 of the 4 fold cities (3 needed).
- **The idea behind it shows up clearly on the downzoning side.** Where builders were active before a cut, the cut lowered building more. The weighted correlation between pressure before and the response is +0.54 for downzoned units, and +0.62 without the "changed outside the reform" units.
- **On the upzoning side pressure tells us almost nothing** (+0.06). Land being upzoned was usually quiet before (0.17 homes permitted per acre per year), so past building doesn't show where new capacity will be used.
- **Nothing changes.** The TOD numbers (AQ-055) stay at 171, 2,509 and 17,148.

## Units

| Kind | Units | Acres | Response per 1.0 of floor area ratio (weighted mean) | Homes permitted per acre per year before (weighted mean) |
| --- | ---: | ---: | ---: | ---: |
| Upzoned | 99 (New York 22, Philadelphia 73, Chicago, Saint Paul, Seattle 2) | 3,445 | +0.245 | 0.17 |
| Downzoned, inside the rezoning | 51 (New York 6, Philadelphia 44, Saint Paul 1) | 1,855 | −0.038 | 0.20 |
| Downzoned, changed outside the reform | 9 (New York) | 330 | +0.073 | 0.31 |

The response is the change in homes permitted per acre per year (after minus before, unit minus comparison), divided by the change in allowed floor area ratio. So a cut that lowers building and a rise that raises it both count as positive. Downzoned land's average is near zero: most cuts didn't bind.

## Methods

Fold cities New York, Philadelphia, Saint Paul and Seattle; Chicago held out. A pass needs 3 of 4 fold cities, a lower mean error and a win on Chicago.

| Method | Fold cities better | Mean error: method / average | Chicago | Verdict |
| --- | ---: | --- | --- | --- |
| Weighted regression | 0 | 0.448 / 0.221 | no | fail |
| LASSO | 0 | 0.226 / 0.221 | no | fail |
| Elastic net | 2 | 0.220 / 0.221 | no | fail |
| Regression tree | 1 | 0.369 / 0.221 | no | fail |
| Random forest | 0 | 0.338 / 0.221 | no | fail |
| Gradient boosting | 0 | 0.332 / 0.221 | no | fail |
| Honest causal forest | 1 | 0.225 / 0.221 | yes | fail |
| Nearest neighbours | 2 | 0.286 / 0.221 | no | fail |
| **Building pressure alone** | 2 | **0.210** / 0.221 | **yes** | fail |

- **Multilevel model:** response per 1.0 of floor area ratio +0.135 homes per acre per year; for a new city −0.04 to +0.31 (90%).
- **Check without the "changed outside" down units:** the same picture. Building pressure alone again has the lowest error (0.218 against 0.226) and wins on Chicago, but in only 2 of 4 cities.

## Reading it

- **Downzonings confirm the binding idea.** Cuts cost homes where building was already happening (Third Ave–Tremont is the clearest), and nothing where it wasn't.
- **Upzonings are harder.** Upzoned land was mostly quiet before, so its past building can't reveal latent demand. A better signal of whether a rise will be used would be demand around the land (the neighbourhood or market), not on it. The trait tests tried neighbourhood rents, values and incomes and found nothing robust.
- **Too few cities.** With 4 fold cities, one city decides a pass. Downzonings near transit from more cities, for example the transit-adjacent entries in Stacy et al.'s list ([research/STACY_AEI_REVIEW.md](research/STACY_AEI_REVIEW.md)), would be needed to test building pressure properly.

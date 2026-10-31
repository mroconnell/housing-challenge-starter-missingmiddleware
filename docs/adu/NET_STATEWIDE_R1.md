# ADU statewide net, round 1 (owner ask 2026-10-31)

Ryan's ask: using the existing model, permits after the reform minus permits with no reform, statewide in Wisconsin, 2027–2031. Run, check for errors and odd outliers, fix, rerun. Code: [`scripts/run_adu_net_statewide.py`](../../scripts/run_adu_net_statewide.py). Outputs: `reference/adu_net_statewide.csv`, `adu_net_statewide_top_places.csv`.

## Answer

| Scenario | With the law | No reform | **Net added** | Share of the shared all-housing baseline (122,619) |
| --- | ---: | ---: | ---: | ---: |
| Lower | 7,009 | 786 | **6,223** | 5.1% |
| Central | 11,135 | 786 | **10,349** | 8.4% |
| Upper | 20,080 | 786 | **19,294** | 15.7% |

Units: ADU permits (second homes on single-family lots), Wisconsin, 2027–2031. Against the as-published all-housing baseline (118,822) the central is 8.7%. Held-out score of the model behind it: 0.130 (average log error, 7 states each predicted while left out).

## What was checked, and what was fixed

1. **With the law minus no reform equals the addition,** in every path: yes.
2. **Places, counties, Assembly and Senate districts add up to the state:** yes, once the check was fixed. My first check summed the district file's yearly rows and its five-year rows together, so it counted everything twice. That was a bug in the check, not the model. Fixed to use the five-year rows only; rerun clean.
3. **No place below zero:** none.
4. **Outliers.** Additional permits per 1,000 single-family homes per year: median 1.00, 99th percentile 2.46. The five highest places are all 3.21. They are small, very high-value villages (Lac La Belle, Oconomowoc Lake, Maple Bluff and others) held at the value cap (AQ-061), so they cannot go higher. Bayside appears with 46 homes because only its Ozaukee County piece is in this row; that is a county split, not an error.

No model change came out of this round.

## Note on overlap with the all-housing baseline

The Census permit survey often does not count ADUs (conversions and units in existing buildings). So most ADU permits are on top of the 122,619, not inside it. The share column is a scale, not a part of a whole.

## Round 2: clean rerun, every outlier verified (Ryan's stopping rule)

Rerun of the same checks with the fixed check. **No errors.** Net added permits unchanged: 6,223 / 10,349 / 19,294. Each outlier was checked against the source tables:

| Outlier | What it is | Verified against |
| --- | --- | --- |
| 8 highest additions, all 3.21 permits per 1,000 single-family homes per year (Chenequa, Shorewood Hills, Lac La Belle ×2, Oconomowoc Lake, Manitowish Waters, Bayside, Maple Bluff) | Very high-value places held at the value cap (AQ-061) | The same 8 area ids are the 8 rows of `reference/adu_model_value_capped_places.csv` |
| Bayside with 46 homes; Lac La Belle with 1 | Village pieces in a second county (Bayside: Milwaukee County 1,345 homes, Ozaukee County 46; Lac La Belle: Waukesha 110, Jefferson 1) | `engine_areas.parquet` and `foundation/areas.parquet` |
| Lowest additions among places with 1,000+ homes (Antigo, Menominee, Clintonville, Marinette 0.38–0.45) | Lowest home values in the state, so the value-based spread gives them the least | Their uncoded current rate is the common 0.076 (below) |
| Madison's low addition (0.42) | Madison follows the Madison-like cities' path, and its own measured rate is already high (owner decision, Gate 4) | `adu_model_params.json` area path |
| Highest current-law rates: 0.278 (Wauwatosa, Appleton, Madison) and 0.128 (Milwaukee) | Benchmark-group rate 0.1876 (Madison 2022–2025: 40 permits ÷ 213.2 thousand home-years) and Milwaukee's measured 0.0863, each × the average no-reform trend over 2027–2031 (×1.48) | `wi_baseline_rates_by_group.csv`, `wi_baseline_observed.csv`, `adu_no_reform_trend.csv` |
| Uncoded places' current-law rate 0.076 | Restricted-group rate 0.0515 × 1.48 | `wi_baseline_rates_by_group.csv` |

Stopping rule met: a round with no errors and every outlier explained and verified.

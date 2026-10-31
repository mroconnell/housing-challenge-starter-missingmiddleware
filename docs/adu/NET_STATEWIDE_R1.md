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

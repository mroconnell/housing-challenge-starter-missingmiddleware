# Parking: "Ask why" review of work so far

Written 2026-10-28 by the parking conductor, at Ryan's request: a one-off review that takes the biggest misses and outliers, traces what drove each, and looks for coding or definition mistakes. Light checks are now built into parking runs (`missing_middleware/parking/checks.py`). They flag problems and never stop a run.

## Findings

| # | Question | What drove it | Mistake? | Effect on the tool |
| --- | --- | --- | --- | --- |
| 1 | Why did placebo cities average +1.5 when the method should give about 0? | Each placebo set draws one stand-in city for each real city. The biggest real cities have very few stand-ins. San Jose has 2 (average +5.5), Raleigh 1 (+3.6) and San Francisco 4 (+1.5), and they carry the most weight. All 4,626 placebo cities pooled average only +0.16 (median −0.35). | **Yes, in the reading.** The "method leans toward growth" claim was wrong, and "real places did worse than 97% of placebo sets" overstates the evidence. | The high end uses the placebo spread (+0.95, 12,695 homes). That spread rests on the same few big stand-ins, so it is lumpy. A fix is proposed below. |
| 2 | Why is the 76-place average negative (−1.14)? | Weighting by homes makes 5 big cities 43% of the weight: San Francisco, Austin, San Jose, Raleigh and Sacramento. Austin (−12.3, repealed in 2023 just as Texas permits fell) and Minneapolis (−8.5, repealed in 2021 after a 2019–2020 rush) reflect market timing. Unweighted, the average is **+0.42**; the median is −0.12; without the 5 biggest cities it is −0.31. | Not a coding error, but it is a framing issue. The "slightly fewer homes" headline is a big-city timing story. | The central case is 0 either way. The wording should say "about zero", not "slightly fewer". |
| 3 | Why is Seattle the outlier (+35.7 per 1,000 lots per year; +18.8 per 1,000 homes near transit)? | Its gain came mostly in 2016–2019, years 4–7 after the 2012 reform. In the urban villages, permits per 1,000 lots were 21 to 42 a year in 2013–2015, then 62, 151 (2017), 37 and 82. That timing matches Seattle's boom and the rush to file before its 2019 affordable-housing fee (Mandatory Housing Affordability) and village upzoning. The "before" years, 2006–2011, also include the 2010–2011 slump (4.5 and 3.7). | **Yes, a definition gap.** The window ran past years 1–3 and into another policy's run-up. | It strengthens the decision not to use Seattle in the totals. |
| 4 | Why is Chicago negative (−2.6)? | The comparison ring is 402–805 m from stations. The 2015 ordinance also covered half a mile along "pedestrian streets", so part of the comparison ring got the reform too. | **Yes, a definition gap**, like TOD's rail-only stop list. It pulls Chicago's result toward zero. | Small: Chicago is not in the totals. It could be fixed with Chicago's pedestrian-street map. |
| 5 | Why were some repeal places missing from the census route? | Windham, Seabrook, Hanover and Hampden are towns (county subdivisions), not census places, so the place-only match missed them. | **Yes, a coding gap.** | Small: the census route is a side check. |
| 7 | Do federal permit counts miss homes in parking places? (from TOD's audit: in 2010–2019, census growth was 1.92 times permits in Philadelphia and 0.46 times in Milwaukee) | Milwaukee: the shared baseline already replaces its federal apartment count with the city's property file. Philadelphia is not one of the 76 places. An undercount only biases a repeal place's effect if it changes around the repeal date. | Not found so far. A per-place census ÷ permits check for the 76 places would need 2010–2019 permits in more states. | None now. The low Milwaukee ratio reflects demolitions, which the permit-based baseline does not net out. |
| 6 | Are any repeal places matched to the wrong permit row? | The Census permit file's population was checked against ACS for all 76. None differs by more than half or double. | No | None |

## Proposed fixes (need Ryan's go-ahead to change the tool)

1. **Placebo test:** draw stand-ins for big cities from a wider pool (the Census division, then the nation, at ½–2× population), so every real city has at least 20 stand-ins. Then recompute the high end. This would likely move it, in either direction.
2. **Wording:** describe the 76-place average as "about zero" and show the unweighted average and median beside it.
3. **Seattle and Chicago lot tests:** cut the windows to years 1–3, and move Chicago's pedestrian-street lots out of the comparison ring.

## Checks now built in (flags only)

- A group (city or place) whose typical value is far outside the others' range.
- Values outside each column's unit range. Units are labelled in `checks.UNITS`.
- Rows that break the policy's own definition (for example, Chicago reform lots farther than 402 m from a station).
- After each run, the worst-missed held-out unit is named for tracing.

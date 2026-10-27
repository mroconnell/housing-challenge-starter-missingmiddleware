# Control cities with no TOD reform: results

Run 2026-10-27 against the plan written before looking ([CONTROL_CITIES_PLAN.md](CONTROL_CITIES_PLAN.md); changes made while running are in its section 9). Code: [missing_middleware/tod/control_cities.py](../../missing_middleware/tod/control_cities.py), [scripts/run_tod_control_cities.py](../../scripts/run_tod_control_cities.py). Data: Census Building Permits Survey place files 2000–2025 and 2010 Census home counts, fetched by [scripts/fetch_tod_control_cities.py](../../scripts/fetch_tod_control_cities.py). Outputs: `reference/tod_control_cities_{results,pooled,controls,rates}.csv`.

## Summary

- **The whole-city comparison agrees with the cities' own results, but it is far too noisy to narrow Wisconsin's range.**
- **Noise.** Fake reforms in cities that made none move whole-city building by a lot. In the six reform cities, the smallest change this comparison can detect is 3.7% to 5.1% (main estimates; 3.7% to 4.8% leaving out Seattle's second test) of a city's homes over five years. The reforms' own measured net effects are 0.04% to 1.47% of the city's homes over five years. So the reforms are too small, relative to their cities, to show up against other cities.
- **Rule 1, agreement: passes, but it is weak evidence.** In 5 of the 6 cities, the city's own net estimate lies inside the whole-city 90% interval; the exception is Seattle. Agreement comes mostly from how wide the intervals are.
- **Rule 2, narrowing: fails.** The pooled interval per upzoned home is about 1,250 percentage points wide, against a 5.4-point gap between the little and strong scenarios.
- **Seattle shows why cities are compared with themselves.** Seattle's permits rose by 14 more homes per 1,000 existing homes a year than its matched cities' after 2012. That is about 7% of the city's homes over five years. Its two station-area rezonings covered 364 of the city's 308,516 homes in 2010 (0.12%), so they cannot explain it. The gap is Seattle's citywide 2013–2019 building boom, which the within-city comparison cancels and the city-to-city comparison does not.
- **Nothing changes.** The finalized TOD numbers (AQ-055) stay: 171, 2,509 and 17,148 extra homes over 2027–2031.

## 1. Each reform city against its 10 matched cities (main estimate)

Outcome: homes permitted per 1,000 homes in 2010, per year. "Effect" is the reform city's change from before to after, less its matched cities' average change. The 90% interval comes from fake reforms in the eligible cities (plan section 6).

| City (reform year) | Eligible control cities | Reform city before → after (homes permitted per 1,000 homes a year) | Effect (homes per 1,000 homes a year, 90% interval) | As a share of the city's homes over five years (90% interval) | Smallest detectable, five years | City's own net estimate, five years | Inside? |
| --- | ---: | --- | --- | --- | ---: | ---: | --- |
| Charlotte (2019) | 80 | 25.9 → 32.6 | −1.3 (−9.3 to 5.9) | −0.80% (−5.81% to 3.70%) | 4.75% | 0.34% | yes |
| Saint Paul (2011) | 379 | 2.3 → 5.3 | 2.3 (−6.4 to 10.3) | 1.14% (−3.19% to 5.16%) | 4.18% | −0.12% | yes |
| Los Angeles (2013) | 16 | 4.2 → 10.2 | 3.2 (−6.8 to 8.0) | 1.62% (−3.41% to 3.98%) | 3.69% | 0.04% | yes |
| Seattle (2012) | 87 | 13.1 → 29.4 | 14.2 (5.7 to 21.0) | 7.07% (2.83% to 10.48%) | 3.82% | −0.06% | no |
| Seattle (2014) | 87 | 13.8 → 32.4 | 13.8 (1.6 to 21.9) | 6.89% (0.81% to 10.95%) | 5.07% | 0.14% | no |
| Chicago (2015, held out) | 20 | 2.3 → 6.1 | 0.1 (−10.2 to 6.8) | 0.03% (−5.08% to 3.39%) | 4.24% | 0.11% | yes |
| Madison (2023, held out) | 402 | 20.6 → 27.0 | 5.4 (−4.5 to 14.4) | 2.69% (−2.25% to 7.20%) | 4.72% | 1.47% | yes |

Notes:

- **Charlotte** is measured as Mecklenburg County's permit office, which issues all of Charlotte's permits (plan section 9, item 1). Its rates are per 1,000 county homes; the five-year shares are converted to Charlotte's 319,918 homes in 2010.
- **Own net estimates** are the five-year net homes from [NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md), divided here by the city's 2010 homes. For Madison that gives 1.47% (1,598 net homes ÷ 108,843 homes in 2010); the net-effect results report 1.24% on Madison's 2020 count (128,508).
- **Small control pools.** Los Angeles and Chicago are so large that only 16 and 20 cities pass the size and exclusion rules, even after the size band widened.
- The matched cities and blend weights are in `reference/tod_control_cities_controls.csv`; the yearly rates in `reference/tod_control_cities_rates.csv`.

## 2. All six cities together

Seattle's two tests are averaged first, so each city counts once.

- **As a share of each city's homes over five years:** 1.94% on average (90% interval −0.10% to 3.73%). The interval barely includes zero, and Seattle is what pulls it up.
- **Per upzoned home** (each city's estimate ÷ its treated area's share of the city's homes, NET_EFFECT_RESULTS section 7): 1,078% (350% to 1,601%). This is not a usable number. Seattle's treated area held 0.12% of its homes, so its citywide boom, divided by that sliver, swamps the average. It is reported only because the plan's rule 2 asks for it.
- **Rule 2:** the interval is 1,250 percentage points wide against a 5.4-point gap between the scenarios, so it fails. Whether a scenario falls outside the interval is not judged when the interval is that wide.

## 3. Fixed checks (plan section 8)

Share of the city's homes over five years:

| City (reform year) | Main | Weighted blend | 5 matched | 20 matched | Buildings of 5+ homes only | Same-metro controls allowed | Fake date, 4 years early |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Charlotte (2019) | −0.80% | −3.89% | −3.57% | 0.61% | −1.28% | −0.80% | 6.50% |
| Saint Paul (2011) | 1.14% | 1.77% | 0.84% | 1.33% | 0.80% | 1.14% | −0.88% |
| Los Angeles (2013) | 1.62% | 0.53% | 1.34% | 0.48% | 0.83% | 1.62% | −0.20% |
| Seattle (2012) | 7.07% | 6.37% | 6.97% | 6.80% | 6.24% | 7.07% | −0.64% |
| Seattle (2014) | 6.89% | 7.33% | 7.37% | 5.97% | 6.14% | 6.89% | 2.92% |
| Chicago (2015) | 0.03% | −0.38% | 0.44% | −0.78% | 0.99% | 0.03% | −3.43% |
| Madison (2023) | 2.69% | 2.06% | 4.22% | 3.66% | 5.23% | 2.69% | 2.76% |

- **The checks move each estimate by several percent of the city's homes.** That is the same size as the noise, and much larger than any reform's measured effect.
- **Seattle stays at 6% to 7% in every check** except the fake date. Its gap opens after 2012, with the boom, not before.
- **The fake-date test** (a pretend reform 4 years before the real one) puts 1 of 7 cities outside its 90% interval: Charlotte, +6.50% (0.43% to 10.98%), for a pretend 2015 reform. About 1 in 10 is expected by chance, but under plan section 8 it means the method can pick up differences in Charlotte that are not the reform.
- **Charlotte's weighted blend disagrees** with its own net estimate: −3.89% (−8.29% to −0.05%) leaves out the city's 0.34%. With the main estimate's agreement, the fake-date result and this, Charlotte's whole-city comparison is unreliable either way.
- "Same-metro controls allowed" changes no estimate: none of the 10 closest cities came from the reform city's own metro either way.

## 4. What this means

- **The question was worth asking.** If whole-city building had jumped in the reform cities and not in similar cities, it would have been strong evidence for the larger scenarios. It did not, in any city whose rezoning was more than a sliver (Seattle's gap is not the reform).
- **It cannot denoise the range.** A city-to-city comparison carries about ±4% to ±5% of a city's homes of noise over five years. Reforms covering 0.1% to 2.5% of a city's homes cannot move the city by more than a fraction of that. To narrow the range with this design, we would need reforms covering a large share of a city (like Auckland's 75%), or many more reform cities pooled.
- **It supports the method already used.** Comparing upzoned land with unchanged land in the same city removes the citywide swings that dominate this test. Seattle is the clearest example.

## 5. What it cannot tell us

- Whether control cities made local reforms we do not know about. If they did, the comparison leans toward finding no effect.
- Anything about New York and Philadelphia, whose rezonings came in many steps.
- Anything about Wisconsin directly. Madison is in the test, but its result is as noisy as the others.

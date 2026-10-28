# From measured cities to Wisconsin: results

Run 2026-10-28 against [CONVERSION_PLAN.md](CONVERSION_PLAN.md) (changes in its section 7). Code: [scripts/run_tod_conversion.py](../../scripts/run_tod_conversion.py). Outputs: `reference/tod_conversion_points.csv`, `reference/tod_conversion_fit.csv`, `reference/tod_conversion_wisconsin.csv`.

## Summary

- **The rule fails its own test, so it is not offered as a replacement.** The better shape (diminishing returns) predicts Madison inside Madison's interval. It predicts Chicago at 0.19% of the city's homes over five years, outside Chicago's narrow interval (0.08% to 0.14%).
- **What it would say for Wisconsin, as context only:**

  | Definition | Diminishing shape | Straight line |
  | --- | ---: | ---: |
  | Current | about 11,100 | about 10,400 |
  | Rail and rapid only (½ mile) | about 5,100 | about 3,000 |

  The current scenarios are 171, 2,509 and 17,148 extra homes over 2027–2031.
- **Broad reforms measured as whole cities came out negative, and the reason is the method, not the reform:**
  - Seattle's 2019 upzoning: −5.0% of its homes over five years (−9.1% to −2.0%);
  - Minneapolis 2040: −7.6% (−12.9% to −3.5%);
  - Portland 2021: −3.3% (−6.8% to +0.5%).

  All three had big 2013–2019 apartment booms that then fell back after 2020 (interest rates, the pandemic), more than their matched cities. A whole-city comparison can't separate that fall from the reform. That is the same ±4–5% noise found in the control-city test.
- **So the line rests on the slivers plus Auckland.** It can't be tested where Wisconsin's law would sit (about two thirds of Milwaukee's and Madison's homes covered).
- **Nothing changes.** AQ-059 is still open.

## The cities

| City | Reform | Share of homes upzoned | Whole-city gain, five years (90% interval) | Source |
| --- | --- | ---: | --- | --- |
| Milpitas | 2008 plan | 3.1% | 7.71% (2.33 to 13.74) | census |
| Madison (holdout) | 2023 overlay | 2.5% | 1.24% (0.03 to 2.43) | permits |
| Bellevue | 2009 BelRed | 0.3% | 1.24% (−0.32 to 3.09) | census |
| New York | 2003–2009 program, whole city | 1.1% | 1.05% (−0.24 to 4.43) | matched cities |
| Philadelphia | 2012 remapping | 2.1% | 0.64% (0.30 to 1.00) | permits |
| Salt Lake City | 2010 district | 1.2% | 0.62% (−0.21 to 1.57) | census |
| Austin | station plans | 0.4% | 0.49% (0.24 to 0.75) | census |
| Fairfax County | Tysons 2010 | 2.2% | 0.41% (−0.26 to 1.05) | census |
| Charlotte | 2019 districts | 0.8% | 0.34% (0.07 to 0.62) | permits |
| Jersey City | 2010 plan | 3.8% | 0.31% (−0.71 to 1.36) | census |
| Chicago (holdout) | 2013–2015 ordinances | 0.5% | 0.11% (0.08 to 0.14) | permits |
| New York | 17 rezonings | 0.5% | 0.11% (0.05 to 0.17) | permits |
| Seattle | 2012–2014 rezones | 0.1% | 0.09% (−0.14 to 0.32) | permits |
| Los Angeles | 2013 plans | 0.4% | 0.04% (−0.07 to 0.14) | permits |
| Saint Paul | 2011 | 0.7% | −0.12% (−0.49 to 0.24) | permits |
| **Auckland** | 2016 | **75%** | **4.11%** | published |
| **Los Angeles TOC** | 2017 (incentives only) | **61%** | **0.03%** | published |
| Seattle | 2019 MHA, whole city | 46% | −5.01% (−9.12 to −1.98) | matched cities |
| Minneapolis | 2040 Plan, whole city | 81% | −7.59% (−12.90 to −3.47) | matched cities |
| Portland | 2021 RIP, whole city | 58% | −3.25% (−6.77 to +0.48) | matched cities |

## The fit

| Shape | b | Leave-one-city-out error (percentage points) | Madison: predicted, inside? | Chicago: predicted, inside? |
| --- | ---: | ---: | --- | --- |
| Straight line (gain = b × share) | 3.32 | 2.38 | 0.08%, yes | 0.02%, no |
| Diminishing (gain = b × √share) | 2.63 | 2.30 | 0.42%, yes | 0.19%, no |

## What it means

- **Broad upzonings can't be measured well as whole cities against other cities.** Market swings at the city level are bigger than the reform. The two broad cases we trust (Auckland, Los Angeles TOC) come from studies with designs built for that. They are already our strong and little scenarios.
- **The ballpark stands as a sensitivity.** If upzoning a city's station areas works like Auckland's with diminishing returns, Wisconsin's current law would add about 11,000 homes over five years: between today's typical and strong. A rail-and-rapid-only law would add about 5,000. These are worth showing as sensitivities, not as the typical value.

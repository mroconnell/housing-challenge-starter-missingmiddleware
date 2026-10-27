# ADU placebo test: plan written before running

Written 2026-10-27, after Ryan asked for the ADU equivalent of the parking and TOD placebo tests ([docs/parking/PLACEBO_PLAN.md](../parking/PLACEBO_PLAN.md)). The rules below were fixed before any before/after change or placebo distribution was computed. Results: [PLACEBO_RESULTS.md](PLACEBO_RESULTS.md).

**What was already known when this was written.** The yearly counts used here are already published in [docs/gate3/STATEWIDE_STATES.md](../gate3/STATEWIDE_STATES.md) and [docs/gate3/OTHER_CITIES.md](../gate3/OTHER_CITIES.md), and some of their period rates are quoted there. So this is not a blind test: the plan fixes the windows, the units, the weights, the placebo-year rule and the decision rule before the comparison is run, so that none of them can be tuned to the answer.

## Question

Do ADU permit rates rise more after a statewide ADU law than they rise, over the same kind of window, in places that had no statewide law? If no-law places rose too, part of what the model credits to the law is the national ADU trend.

Three groups:

- **(A) Strong statewide law** (Mercatus 2025 "strong").
- **(B) Weaker statewide law** (Mercatus 2025 "weaker": poison pills such as owner occupancy, extra parking, or limited lots).
- **(C) No statewide law (placebo):** cities with yearly ADU counts in years when their state had no ADU law, given fake "law years".

## Outcome

ADU permits (units where the source counts units) per 1,000 one-unit detached homes per year.

- **Numerator:** the series' own ADU count for the year (Wisconsin: second-home permits on single-family lots, the model's outcome).
- **Denominator:** ACS 2020–2024 5-year one-unit detached homes (B25024_002) for the series' geography, held constant over time, times the number of years in the window. Rates therefore move only with counts.
- Missing years are missing, not zero; a window's rate uses the years it has.

## Windows

- **Year 0** is the calendar year (or reporting year) that contains the law's effective date. It is dropped, because it is part before and part after. Where a law takes effect on 1 January, year 0 is the year before (California: law effective 2017-01-01, so year 0 = 2016, matching [reference/madison_like_annual.csv](../../reference/madison_like_annual.csv)).
- **Before:** years −3 to −1 (at least 1 year required).
- **After:** years +1 to +3 (at least 1 year required).
- A window rate = sum of counts in the window / (homes × years observed in the window) × 1,000.

## Effect measures (per series)

- **Change (D)** = after rate − before rate, in ADUs per 1,000 one-unit detached homes per year.
- **Ratio (R)** = after rate / before rate. Undefined when the before rate is 0 (shown as n/a).

## Group statistics and weighting

- **Unit of analysis:** one series per law episode (a state aggregate or a city). Overlapping series are not both counted in a group (for example, the Washington cities series already contains Spokane and Tacoma).
- **Primary, equal weight per series:** group change D̄ = mean of the series' D; group ratio = mean of after rates / mean of before rates (a ratio of means, so a zero before rate does not break it).
- **Secondary, home-weighted:** pooled counts / pooled home-years in each window, across the group's series.

## Series in each group

| Group | Series | Year 0 | Notes |
| --- | --- | --- | --- |
| A | California, non-holdout grouped jurisdictions | 2016 | Period rates from the CA study (0.12 for 2014–16; 0.66 for 2017; 1.48 for 2018–19); after = (0.66 + 2 × 1.48) / 3 |
| A | Washington cities and towns excluding Seattle (OFM) | EY2023 | OFM estimate year (Apr–Mar); law effective 2023-07-23 |
| A, sensitivity | Oregon 32-city panel excluding Portland | 2018 | No pre-law year exists; sensitivity uses the 2018 law year as "before" |
| A, level only | Maine, Massachusetts | 2024 / 2025 | No before year; reported as levels, not changes |
| A, sub-check | Washington Madison-like cities (Spokane, Spokane Valley, Tacoma, Vancouver, Yakima); California Madison-like cities (15) | EY2023 / 2016 | Inside the state series above; shown separately, not added to the group |
| A, sub-check | Oregon Madison-like cities (Eugene, Gresham, Medford, Salem) | 2018 | No before year; level only |
| B | Rhode Island statewide | 2024 | Law effective 2024-06-25; only 2025 is after |
| B | Chittenden County, Vermont | 2020 | Act 179 effective 2020-10-12; counts by year built |
| B, level only | Utah, New Hampshire (conversions proxy) | — | No before year |
| C (moved from B) | Honolulu; Montgomery County, MD | — | All their data are before their state's law (Hawaii 2024-05-28, Maryland 2025-10-01), so they have no after window as B; they are no-law places in those years and join C |
| C | Minneapolis 2017–2025 | — | Minnesota: no statewide ADU law |
| C | Denver 2016–2023 | — | Colorado's law took effect 2024-05-13, so 2024 onward is excluded |
| C | Austin 2005–2023 | — | Texas: no statewide ADU law in these years; the HOME changes retired the permit category in 2024 |
| C | Portland, OR 2005–2017 | — | Before SB 1051 (2018) |
| C | Madison 2014–2025 (second homes on single-family lots) | — | Wisconsin: no statewide ADU law. 2026 is a part year and is not used |
| C | Sun Prairie and Pleasant Prairie (pooled) | — | The two other measured Wisconsin places with yearly series; the other places in `reference/wi_measured_permits_2022_2025.csv` have only a 2022–2025 total |
| C, older weak state law | Seattle 2005–2022; Washington cities excluding Seattle EY2011–EY2023; California Madison-like cities 2012–2016 | — | Washington's 1993 law required local ADU rules but allowed discretionary permits; California's 2003 law (AB 1866) required ministerial review. Neither is a Mercatus statewide law, but both are something. Included in C; dropped in sensitivity S1 |

Rhode Island, Utah and Vermont are in the adopted pooled model although Mercatus rates them weaker.

## Placebo law years for group C

- **Primary, calendar-matched:** each C series' fake year 0 is drawn from the real year-0s of the A and B series used in the comparison: {2016 (California), 2020 (Vermont), 2023 (Washington), 2024 (Rhode Island)}. This matches the national ADU trend at the same calendar time as the real laws.
- **Secondary, every year:** any year 0 for which the series has at least 1 before year and 1 after year within its no-law years.
- A fake year 0 is eligible for a series only if at least 1 before year and at least 1 after year fall inside its no-law years and its data. A series with no eligible year in a draw is skipped in that draw (counted).
- **Resampling:** 2,000 draws, seed 20261027. In each draw every C series gets one eligible year 0 at random (uniform), and the group statistics are computed exactly as for A and B.

## What is reported

- Each group's and series' before rate, after rate, D and R.
- C's resampled distribution of D̄ and of the group ratio: 5th, 50th and 95th percentiles.
- Where A's and B's D̄ and ratio fall in C's distribution: the share of C draws at or above them.
- The spread of single C series' D (all eligible fake years) against single A and B series' D.
- Dose-response: is A > B > C (C's median), on D̄ and on the ratio?

## Decision rule

1. **The statewide law matters beyond the trend** if A's D̄ and A's group ratio are both above C's 95th percentile.
2. **The national trend (with local reforms) could explain it** if A's D̄ is at or below C's 95th percentile.
3. **Mixed** if only one of D̄ and the ratio is above C's 95th percentile.
4. **Trend share:** C's median D̄ / A's D̄ = the share of A's rise that no-law places also showed.
5. **Dose-response holds** if A > B > C's median on both D̄ and the ratio; partly if only on one.
6. **No-law places rose materially** if C's median group ratio is at least 1.25 (a rise of 25% or more between window centres four years apart) or C's median D̄ is at least 0.10 ADUs per 1,000 homes per year.

## Wisconsin implications (computed separately; adopted outputs untouched)

Run the adopted engine (`scripts/run_adu_model.py` scenario, levels and Madison path; `missing_middleware.model.engine.run`) with only the current-law baseline changed, write nothing to `reference/adu_model_*.csv`, and report baseline, addition and with-law total for 2027–2031 on each path:

- **Rising baseline, proportional (main):** each area's current-law rate x is multiplied by f^(t − 2023.5), where t is the forecast year (2027–2031), 2023.5 is the centre of the 2022–2025 measurement window, and f = (C's median group ratio)^(1/4), the annual factor implied by a ratio between window centres four years apart. Existing baseline ramps (g) stay.
- **Rising baseline, additive (sensitivity):** x_t = x × g + (C's median D̄ / 4) × (t − 2023.5).
- Also with C's 95th-percentile ratio, as the high trend case.

## Recommendation rule

- Rule 1 holds and the C rise is not material → **keep the model**.
- Rule 1 holds and the C rise is material → **add a rising baseline** (the law's addition falls by about the baseline's rise; the total with the law changes little).
- Rule 1 fails → **change the law effect**, an owner decision: the statewide-law level is not supported beyond the trend.

## Pre-stated sensitivities

- **S1** C restricted to places whose state had no ADU law of any kind (drop Seattle, Washington cities pre-2023, California cities pre-2017).
- **S2** Drop C draws whose window (first before year to last after year) contains a major local reform effective date: Minneapolis 2020-01-01 and 2021-02-26; Denver 2023-07-05; Austin 2015-11-30; Portland 2010-04-01 and 2016-01-01; Seattle 2009-12-04 and 2019-08-08; Madison 2021-12 (by right); Montgomery County 2019. (A draw re-picks among that series' remaining eligible years; a series with none is skipped.)
- **S3** Oregon added to A with its 2018 law year as "before".
- **S4** Every-year placebo rule instead of calendar-matched.
- **S5** Home-weighted group statistics.
- **S6** California's 15 Madison-like cities instead of the non-holdout groups as the California series.

## Changes after writing

Each change is listed with its date and whether it came before or after the results were seen. None of them changes the pre-registered verdict, which is reported first in the results.

- **2026-10-27, while coding, before results:** S5 (home-weighted) leaves out California's non-holdout series, because it has period rates only and no counts or homes. In S5, group A is Washington alone.
- **2026-10-27, after the first run: D1, size-matched placebo groups (added).** The plan compares the mean of A's 2 series with the mean of about 10 C series per draw. An average of 10 varies much less than an average of 2, so the plan's C distribution is too narrow for a 2-series group. D1 draws 2 distinct C series per draw (the size of A and of B), with the calendar-matched rule and, separately, the every-year rule. Reported next to the plan's rule, not instead of it.
- **2026-10-27, after the first run: own pre-law trend (exploratory, added).** Placebo years inside Chittenden County's own years before Act 179 (2010–2019). Washington's own pre-law years were already in C. Rows are in `reference/adu_placebo_eligible.csv` under kind "own pre-law placebo (exploratory)". They are not in C and not in the decision rule.

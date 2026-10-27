# TOD net effect, borrowing and coverage: results

Run 2026-10-27 under [NET_EFFECT_PLAN.md](NET_EFFECT_PLAN.md), which was written before any of these comparisons were computed. Every departure is listed in the plan's section 8 with its date. Outputs:
- [reference/tod_net_effect_by_case.csv](../../reference/tod_net_effect_by_case.csv)
- [reference/tod_coverage_traits.csv](../../reference/tod_coverage_traits.csv)
- [reference/tod_net_traits_test.csv](../../reference/tod_net_traits_test.csv)

Code:
- [net_effect.py](../../missing_middleware/tod/net_effect.py)
- [run_tod_net_effect.py](../../scripts/run_tod_net_effect.py)
- [build_tod_net_coverage.py](../../scripts/build_tod_net_coverage.py) (coverage)

## Summary

- **Little sign of borrowing next door.** In no city did building fall in the ¼-mile ring around the upzoned land, measured against land ¼ to 1½ miles away. Nine of the ten 90% intervals include zero. The one that does not (Chicago) shows the ring *gaining*: +0.034 homes per eligible acre per year.
- **Every city's net effect is small compared with its whole housing stock.**
  - Over five years it ranges from −0.12% (Saint Paul, a weak case) to +1.24% (Madison).
  - The median city is +0.11%.
  - Each city's 90% interval is narrower than the gap between the borrowed figures (Los Angeles about 0.03% and Auckland about 4.1% over five or six years).
- **No coverage, shape, binding-limit or car-dependence trait passes** the trait-test rule. Two, elongation and the share of workers commuting by transit, beat the plain average in 4 of 6 fitted cities and on the mean error, but failed on both Chicago and Madison.

## 1. Borrowing: did building move out of the ring?

Borrowing is the ring's change against far land, in homes permitted per eligible acre per year, after against before. A negative value means building left the ring.

| Case | Ring acres | Far acres | Borrowing (homes per eligible acre per year) | 90% interval |
| --- | --- | --- | --- | --- |
| New York pooled rezonings | 2,344 | 23,042 | +0.036 | −0.069 to +0.150 |
| Philadelphia remapping | 11,345 | 123,556 | +0.017 | −0.011 to +0.046 |
| Charlotte 2019 | 3,082 | 12,539 | +0.028 | −0.014 to +0.070 |
| Saint Paul Green Line (1 before year) | 1,450 | 11,117 | −0.007 | −0.020 to +0.007 |
| Los Angeles Warner Center | 301 | 4,570 | −0.003 | −0.006 to +0.001 |
| Los Angeles Cornfield Arroyo Seco | 154 | 1,645 | +0.188 | −0.285 to +0.717 |
| Seattle North Beacon Hill and Othello | 344 | 3,767 | −0.025 | −0.082 to +0.027 |
| Seattle Mount Baker | 248 | 2,129 | +0.253 | −0.080 to +0.645 |
| Chicago (held out) | 6,601 | 23,870 | +0.034 | +0.025 to +0.043 |
| Madison (held out) | 458 | 3,864 | +0.178 | −0.327 to +0.718 |

Acres are eligible acres; stacked cases sum their members. The rates behind each line (before and after, for treatment, ring and far land) are in the CSV.

**In plain words:** the next-door blocks did not lose building after the upzonings. If anything they gained a little, which is the opposite of borrowing. The rings are small and their intervals are wide (plan section 7). So small borrowing cannot be ruled out in most cities, but large borrowing can.

## 2. Net effect, each city

The net effect is the homes gained on upzoned land plus the ring's change, both measured against far land, in extra homes a year. The citywide share divides it by the city's housing stock: 2010 Census homes, or 2020 for Madison.

| City | Net extra homes a year (90% interval) | City stock (homes) | Net share a year | Net share over 5 years (90% interval) | Coverage: share of land / of homes | Case shape |
| --- | --- | --- | --- | --- | --- | --- |
| New York | 711 (349 to 1,130) | 3,371,062 | 0.021% | 0.11% (0.05% to 0.17%) | 85% / 99% | corridor (0.69) |
| Philadelphia | 862 (403 to 1,338) | 670,171 | 0.129% | 0.64% (0.30% to 1.00%) | 77% / 93% | nodes (0.17) |
| Charlotte | 215 (45 to 398) | 319,918 | 0.067% | 0.34% (0.07% to 0.62%) | 8% / 12% | corridor (0.79) |
| Saint Paul | −29 (−117 to 58) | 120,795 | −0.024% | −0.12% (−0.49% to 0.24%) | 54% / 69% | corridor (0.56) |
| Los Angeles (two cases) | 102 (−206 to 389) | 1,413,995 | 0.007% | 0.04% (−0.07% to 0.14%) | 39% / 66% | corridor (1.00 and 0.85) |
| Seattle (two cases) | 54 (−88 to 194) | 308,516 | 0.017% | 0.09% (−0.14% to 0.32%) | 68% / 83% | nodes (0.00 and 0.00) |
| Chicago (held out) | 264 (188 to 334) | 1,194,337 | 0.022% | 0.11% (0.08% to 0.14%) | 80% / 94% | nodes (0.37) |
| Madison (held out) | 320 (8 to 624) | 128,508 | 0.249% | 1.24% (0.03% to 2.43%) | 38% / 63% | nodes (0.47) |

**Notes on the table:**
- **Case shape** is the share of the reform's upzoned land in pieces at least ½ mile long (in brackets). It is labelled "corridor" at 0.5 or more and "nodes" below.
- **Madison** sits just under the cut, at 0.47.
- **Coverage** is the share of the city within ½ mile of a rail or rapid station or ¼ mile of a 15-minute bus stop. It is measured from today's stops and timetables (plan section 8, item 5).

**What makes up the net effect.** Most of the net comes from the upzoned land itself. Chicago is the exception: its ring gained 224 extra homes a year against far land, against 40 on the upzoned land. That is because its ring is large (6,601 acres against 259 upzoned acres).

**Coverage, stated with the plan's warning.** With eight cities, coverage cannot be separated from everything else about them. No pattern shows anyway:
- the most covered cities (New York, Chicago and Philadelphia, 77% to 85% of land) have five-year net shares of 0.11% to 0.64%;
- the least covered (Charlotte, 8%) has 0.34%;
- the largest share (Madison, 1.24%) is a city with 38% coverage.

Shape does not line up with the net share either: "corridor" cities range from −0.12% to 0.34%, and "nodes" cities from 0.09% to 1.24%.

## 3. Comparison with the borrowed figures

The borrowed figures come from [research/NET_EFFECT_SOURCES.md](research/NET_EFFECT_SOURCES.md). All three are net figures for a whole city.

| Source | Published figure | Same basis as the table (five years) |
| --- | --- | --- |
| Los Angeles TOC (Kestelman) | +0.04 percentage points of stock over six years, 2017–2023 | about +0.03% |
| Stacy et al. 2023 | +0.8% of USPS addresses per loosening reform (95% about +0.2% to +1.4%), average of years 3 and later | +0.8% (a level, not a five-year sum) |
| Auckland (Greenaway-McGrevy and Phillips) | +4.11% of 530,300 dwellings, 2016–2021 | +4.35% for 2017–2021 |

**How the cities compare:**
- **Los Angeles** measures +0.04% (−0.07% to +0.14%) here, the same size as the Los Angeles TOC figure. They are different reforms.
- **Five cities sit near the bottom (little) end,** between −0.12% and +0.11%: New York, Chicago, Seattle, Los Angeles and Saint Paul.
- **Charlotte (0.34%) and Philadelphia (0.64%)** sit between the Los Angeles and Stacy et al. figures.
- **Madison (1.24%)** is above Stacy et al., with a wide interval: 0.03% to 2.43%.
- **No city's interval reaches Auckland's 4.1%.** Auckland upzoned three-quarters of its residential land, far more of the city than any of these reforms.

## 4. Can the cities' own net effects narrow Wisconsin's range? (plan section 6)

**The plan's test is met.** Every city's 90% interval for the five-year share is narrower than the spread between the borrowed studies. That spread runs from about 0.03% (Los Angeles TOC) to about 4.1% (Auckland), about 4 percentage points. The widest city interval is Madison's, 2.4 points; the others are 0.06 to 0.73 points.

**The candidate for the owner** (AQ-050, AQ-056) is the lowest, median and highest city five-year net share:

| Point | Five-year net share | City |
| --- | --- | --- |
| Lowest | −0.12% | Saint Paul (context case, 1 before year) |
| Lowest among measured cases | +0.04% | Los Angeles |
| Median of the eight cities | +0.11% | between New York (0.106%) and Chicago (0.110%) |
| Highest | +1.24% | Madison, held out (3 after years, scaled to 5) |
| Highest among fitted cities | +0.64% | Philadelphia |

This would pull down the "typical" and "strong" ends of Wisconsin's range: from 0.8% and 4.1% to roughly 0.1% and 0.6% to 1.2%.

**Three cautions before the owner decides:**
1. **These are shares of the whole city.** Each reform upzoned a small slice of its city, so a city share depends on how much land the reform covered. It is not an effect per covered home. The CSV also gives net extra homes per upzoned acre a year, which travels better: about 1.0 to 1.3 in New York, Philadelphia and Chicago, and 0.1 to 0.5 in Los Angeles Warner Center, Charlotte and Madison.
2. **Far land may itself be affected** (section 5). If so, the "far" baseline is not a clean counterfactual.
3. **Los Angeles's far land is cut off at the edge of the fetched area.**

Nothing changes without the owner's approval.

## 5. Distant borrowing (check only, not judged)

This check compares homes permitted on the city's land more than 1½ miles from the upzoning with homes permitted in the other counties of the metro (Census permits). The comparison is after against before. The figure is (city-beyond growth ÷ region growth) − 1.

| Case | Beyond 1½ miles, homes a year: before → after | Other metro counties: before → after | Relative growth − 1 |
| --- | --- | --- | --- |
| New York (mean per member) | 21,521 → 22,086 | 27,774 → 19,280 | +0.48 |
| Philadelphia (mean per member) | 2,539 → 6,823 | 8,018 → 10,346 | +1.08 |
| Charlotte | 4,129 → 7,029 | 10,472 → 14,857 | +0.20 |
| Saint Paul (units only from 2010) | 12 → 213 | 5,657 → 11,193 | not meaningful |
| Seattle North Beacon Hill and Othello | 3,982 → 8,394 | 6,675 → 7,489 | +0.88 |
| Seattle Mount Baker | 4,805 → 9,302 | 5,281 → 8,272 | +0.24 |
| Chicago | 155 → 136 | 5,387 → 9,000 | −0.48 |
| Madison | 570 → 264 | 358 → 343 | −0.52 |
| Los Angeles | no citywide permit file | | |

**What it shows:**
- **No sign of distant borrowing in most cities.** In New York, Philadelphia, Charlotte and Seattle, the city's distant land grew *faster* than the rest of the metro.
- **Chicago and Madison are the exceptions.** Their distant land grew more slowly than the rest of the region: −48% and −52% relative growth. That fits the Auckland pattern of building drawn from distant areas. It would mean far land in those two cities is itself depressed, which overstates their net effects.
- **Small bases.** Both distant-land totals are small: Chicago 155 homes a year (units parsed from permit descriptions), Madison 570. This is a check, not a test.

## 6. Unit traits under the trait-test rule

The rule is the latest one in [TRAITS_PLAN.md](TRAITS_PLAN.md) section 8: a trait must beat the plain average in at least 4 of the 6 fitted cities, on the mean error, and on Chicago and Madison each by itself. Errors are the acre-weighted mean absolute error in homes per eligible acre per year, averaged over the fitted cities.

| Trait | Fitted cities better | Mean error: plain average → trait | Beats average on Chicago / Madison | Verdict |
| --- | --- | --- | --- | --- |
| Island size (covered patch acres) | 1 of 6 | 0.856 → 0.902 | no / no | fail |
| Largest contiguous upzoned site (acres) | 2 of 6 | 0.856 → 0.881 | no / yes | fail |
| Elongation of upzoned land | 4 of 6 | 0.856 → 0.837 | no / no | fail |
| Corridor share | 3 of 6 | 0.856 → 0.869 | no / yes | fail |
| Binding limit (built ÷ allowed density) | 0 of 3 testable | 1.200 → 2.529 | no / no | fail (testable in 3 fitted cities only) |
| Share of households with no vehicle | 2 of 6 | 0.856 → 0.877 | no / no | fail |
| Share of workers commuting by transit | 4 of 6 | 0.856 → 0.843 | no / no | fail |
| Mean commute time | 2 of 6 | 0.856 → 0.887 | no / no | fail |

**What the traits show:**
- **Island size barely varies.** In six of the eight cities, one continuous covered patch holds 80% or more of the covered land, so nearly every unit in a city sits in the same island. The exceptions are Charlotte (57%) and Saint Paul (67%).
- **The binding-limit ratio** is low in most units: built density is well below what the old limit allowed. The New York median is 0.58, and the medians elsewhere are 0.02 to 0.17.
- **Every value is in the CSVs.** City coverage and each unit's value are in `tod_coverage_traits.csv`. The verdicts and each city's errors are in `tod_net_traits_test.csv`.

**In plain words:** none of these traits predicts the held-out cities better than the plain average. Elongated upzonings and transit-commuting areas looked slightly better within the fitted cities, but got Chicago and Madison wrong. Eight traits were tried, so one or two near-misses are expected by chance.

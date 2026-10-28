# Parking: can a model predict near-transit gains in held-out places? Plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request: use option B or the Seattle-only rate only "if we had a real predictive model … [that] could accurately predict holdouts". No per-village or per-station figure named here has been computed before this file was committed. Changes go in the last section with a date and a reason.

## 1. Units

Each unit is one near-transit area where parking minimums were removed or cut.

| Region | Units | Reform | Outcome period | Outcome source |
| --- | --- | --- | --- | --- |
| Seattle | each hub or residential urban village (24) | 2012 | 2000–2010 vs 2010–2020 | census blocks |
| Minneapolis | each light-rail station area: blocks within ½ mile, each block assigned to its nearest station, downtown (1.5 km) left out | 2015 | 2000–2010 vs 2010–2020 | census blocks |
| California | each jurisdiction's land within ½ mile of a major transit stop (185 jurisdictions; TOD's AB 2097 test) | 2023 | years before vs 2023–2025 | permits |

## 2. Outcome

Extra homes per 1,000 existing homes per year in the near-transit area, after the reform minus before, net of the same change in a comparison area:
- **Seattle and Minneapolis:** the change in change against the rest of the city. Census net homes, divided by 0.86 to put them on a permit footing.
- **California:** TOD's difference-in-differences against land ½ to 1½ miles from the same stops (`reference/tod_ab2097_by_jurisdiction.csv`).

## 3. Inputs (the same for every region)

1. **Rail:** whether the area has a rail station (light rail, streetcar, commuter or heavy rail), from the National Transit Map rail stops.
2. **Size:** log of homes in the area before the reform (2010 census for Seattle and Minneapolis, 2020 for California).
3. **Prior gap:** the area's growth minus its comparison's growth before the reform.
   - Seattle and Minneapolis: 2000–2010, per 1,000 homes per year.
   - California: the before-period rates.

## 4. Tools and test

- **Tools:** one weighted average; weighted linear regression on the three inputs; lasso; random forest. These are the same tools as the parking all-variables test.
- **Weights:** homes in the area.
- **Error:** home-weighted mean absolute error on held-out units.
- **Main test (leave one region out):** fit on two regions, predict every unit in the third. Repeat for each region.
- **Pass rule:** a tool passes if it beats one average (fitted on the same two regions) by at least 5% in at least 2 of the 3 held-out regions, and by at least 5% on all held-out units pooled.
- **Also reported:** within-region 10-fold cross-validation, repeated 20 times, seed 20261028, with the same 5% bar.

## 5. Use

- **If a tool passes:** it predicts near-transit gains for Wisconsin's areas near major transit stops. The result goes to Ryan as a proposal to replace the high end.
- **If none passes:** the near-transit rate is not supported for prediction. That is reported, and the tool keeps its current range unless Ryan decides otherwise.

## Changes after writing
- **2026-10-28, after running:** Minneapolis platforms were merged by name and areas under 100 homes dropped (12 areas). California rail is marked by stops inside the jurisdiction's boundary.

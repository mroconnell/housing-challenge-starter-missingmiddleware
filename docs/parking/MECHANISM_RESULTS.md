# Parking: per-project (mechanism) estimate, results

Written 2026-11-01 by the parking mechanism thread. Plan, committed before any result: [MECHANISM_PLAN.md](MECHANISM_PLAN.md) (4 deviations logged there). Script: `scripts/run_parking_mechanism.py`. Files: `reference/parking_mechanism_*.csv`. This is a candidate line for Ryan; the tool and other scenarios are unchanged.

## Answer

- **Projects get bigger after repeal.** Apartment buildings had more homes each.
- **But fewer apartment buildings were permitted.**
- **Total apartments: no measurable change.** This matches the tool's central of 0.
- **Parking cost alone adds little.** About +570 homes in Wisconsin over 2027–2031.

| What changed after repeal (38–73 US repeal places) | Result | Unusual against fake repeals? |
| --- | --- | --- |
| Homes per apartment building (5+ units) | **+43%** (pre-set weighting); +13% to +20% other ways | Yes for the pre-set version (99.9th percentile); borderline otherwise (94th) |
| Number of apartment buildings permitted | **−0.063 buildings per 1,000 existing homes per year** | Yes, low side (3rd percentile) |
| Homes in apartment buildings | −1.03 permits per 1,000 existing homes per year (−2.74 to +0.89) | No (17th percentile) |
| Homes in 2–4 unit buildings (small lots) | −0.065 permits per 1,000 existing homes per year (−0.14 to +0.03) | No (27th percentile) |

"Fake repeals" are never-reformed places of similar size in the same region, given the real repeal years (20,000 sets). The percentile says where the real result sits among them.

## Wisconsin, 2027–2031 (homes permitted, beside the tool lines)

| Line | Lower | Central | Upper | Status |
| --- | ---: | ---: | ---: | --- |
| Tool today (count comparison) | 0 | 0 | 19,937 | In use |
| Route A, bigger projects only (pre-set conversion) | 16,306 | 18,590 | 20,030 | Passes its pre-set tests, **but its key assumption fails** (see below) |
| Route A, all apartment homes (bigger but fewer projects) | about −36,800 | about −13,800 | about +12,000 | No measurable change |
| Route B, cost chain | 227 | 566 | 1,226 | Evidence only (pre-set rule) |
| Low-line candidates from earlier work | −15,303 / −18,100 | – | – | Pending |

- **Route A, bigger projects only:** +43% homes per building × 42,807 apartment homes in the baseline where minimums still bind. The range is the 5th–95th percentile when each place is left out in turn. With the whole 76-place resampling range it is 5,601 to 29,717.
- **Why that line should not be used:** it assumes the number of apartment buildings stays at baseline. The data say it fell. Bigger-but-fewer adds up to no measurable change in apartment homes.
- **Route A, all apartment homes:** −1.03 permits per 1,000 existing homes per year × 13,424 Wisconsin homes over five years per 1.0 (the factor used in `METRO_RESULTS.md`). The range uses the resampling 5th–95th percentile.

**My recommendation:** keep the tool's lines. Use the per-project findings to explain *how* repeal works: developers build fewer, larger buildings with less parking, and total output does not measurably change.

## Part A details: project size in Census permits

Source: Census Building Permits Survey place files, 2012–2025, which give buildings and homes by building size. Same 76 repeal places, windows and comparison places as the tool's comparison. 73 of 76 have the permit years needed; 38 have at least 2 apartment buildings in each window, in the place and in its comparison group.

| Measure (homes per apartment building) | Change after repeal, against comparison places | Percent | Placebo percentile | Fake-repeal 5th–95th |
| --- | ---: | ---: | ---: | --- |
| Weighted by buildings (pre-set) | +0.361 log points | +43% | 99.9 | −0.48 to +0.17 |
| Same, without Austin (31% of the weight) | +0.287 | +33% | 99.1 | −0.52 to +0.18 |
| Unweighted mean | +0.127 | +13% | 93.9 | −0.31 to +0.14 |
| Median place | +0.186 | +20% | 93.8 | −0.26 to +0.22 |
| Own change only, no comparison places | +0.128 | +14% | 93.9 | −0.50 to +0.14 |

Pre-set tests for the main version: outside the fake-repeal 5th–95th range (yes), and the average from other states predicts each state's places better than zero (yes: error 0.44 against 0.52 log points). Rows from the unplanned checks are in `parking_mechanism_part_a_robustness.csv`.

**Reading.**
- The direction is steady: 21 of 38 places (55%) got bigger, and every version is above the 93rd placebo percentile.
- The size is not steady: 13% to 43% depending on weighting. Austin counts heavily, and its own size barely moved (45.7 to 47.9 homes per building); its comparison places shrank.
- **Project size is noisier than permit counts, not less.** The pre-set question: the fake-repeal 5th–95th width is 0.70 log points for project size, against 0.41 of the before-rate for all permits.
- **Fewer buildings:** the average place permitted 0.063 fewer apartment buildings per 1,000 existing homes per year than its comparison places. That is unusual (3rd percentile of fakes), and it cancels the bigger buildings.
- **Possible reasons** (not tested): parking-free sites favour larger infill projects; 2022–2024 interest rates hit small projects hardest; many repeals came with zoning rewrites (28 of 38 places; projects got bigger with or without one: +0.36 and +0.36 log points).

## Part B details: the cost chain

> extra homes = apartment homes where minimums bind × supply response × (spaces not built per home × cost per space ÷ total cost per home)

Per project, at central values (a typical Wisconsin apartment home where minimums bind):

| Piece | Value | Source |
| --- | ---: | --- |
| Old minimum | 1.32 spaces per home | 16 Wisconsin city codes (2025 compilation); others drawn from them |
| Share of old required spaces not built | 0.365 (median of 4 studies; range 0.21–0.54) | Buffalo, Los Angeles, Seattle, Champaign project studies |
| Spaces not built | 0.48 spaces per home | product of the two above |
| Cost per space | $22,700 | Structured $29,900–$52,000 in urban places; surface $1,500–$10,000 plus land elsewhere |
| Saved per home | $9,800 | |
| Total cost per home | $250,700 | Census permit value $159,203 per home (Wisconsin 5+ unit buildings, 2023–2025) ÷ 0.635 hard-cost share |
| Saved, share of cost | 3.9% | |
| More apartments | 1.2% (0.4% to 2.3%) | × supply response 0.30 (0.11 to 0.59; Baum-Snow and Han 2024) |

Wisconsin total, homes in 2+ unit buildings over 2027–2031 (10,000 draws):

| Case | 5th | Median | 95th |
| --- | ---: | ---: | ---: |
| All pieces vary | 227 | 566 | 1,226 |
| Buffalo only for the share not built (closest market to Wisconsin) | 172 | 335 | 563 |
| Structured parking only in Madison and Milwaukee | 148 | 374 | 836 |
| Supply response held at 0.30 | 264 | 545 | 942 |
| Share not built held at 0.365 | 305 | 593 | 997 |

The supply response and the share not built drive most of the spread.

**Held-out tests.**
- **B1, leave one study out** (share of old required spaces not built): misses are −0.22 (Buffalo), −0.05 (Los Angeles), +0.04 (Seattle), +0.23 (Champaign). All four studies sit inside the draw range, so the range is not widened.
- **B2, against real repeals:** B predicts +0.11 permits in 2+ unit buildings per 1,000 existing homes per year in 75 repeal places (Buffalo left out). They measured −1.24. B's error (4.42) is 1.2% worse than predicting zero (4.36). The test cannot separate them, but under the pre-set rule B is **evidence only**.
- **B3, against Part A:** B's +1.2% is inside the all-apartment-homes range from Part A, and far below the +43% in homes per building. Cheaper parking alone does not explain bigger buildings.

**Limits of B.** It cannot go negative by construction; that is a limit of the method, not a finding. The Seattle share is from a secondary summary. Census permit values often understate construction cost, which would make B's percent too high.

## Where Wisconsin minimums still bind (Part C)

- **No minimums already** (9 "at" places, plus Pewaukee city and Roberts): no change.
- **Madison:** 2,188 of 19,170 new apartment homes built 2015–2024 (11.4%) are in downtown districts; 8,473 (44.2%) are downtown or in the TOD overlay.
- **Milwaukee:** 3,721 of 13,999 new apartment homes built 2015–2024 (26.6%) are in downtown C9 districts.
- **Result:** of 51,086 baseline homes in 5+ unit buildings over 2027–2031, 40,646 to 44,968 are where minimums bind (42,807 at the midpoint). For all 2+ unit buildings: 48,723 to 53,085 of 59,544.

## Files

| File | What it holds |
| --- | --- |
| `parking_mechanism_part_a_summary.csv` | Part A averages, ranges, placebo and held-out scores (A1–A3, all units, 5+ homes) |
| `parking_mechanism_part_a_places.csv`, `_excluded.csv` | Each repeal place's before/after buildings and homes; places left out and why |
| `parking_mechanism_part_a_robustness.csv` | Unplanned checks on homes per building |
| `parking_mechanism_where_binding.csv`, `_exempt_shares.csv` | Wisconsin areas, exempt shares, land values |
| `parking_mechanism_part_b_wi.csv`, `_per_project.csv`, `_b1_loso.csv`, `_b2_vs_repeals.csv` | Cost chain results and tests |

Rebuild: `uv run python scripts/run_parking_mechanism.py part_a` (about 20 minutes), then `summarise_a`, `robust_a`, `part_c`, `part_b`.

## Sources

- Hess, D. B., and Rehler, J. (2021), *JAPA* 87(3), 396–408 (Buffalo).
- Sohoni, S., and Lee, B. (2024), "After the Minimum Parking Requirement", *JAPA* 90(3), 471–485 (Champaign).
- Gabbe, C. J., Pierce, G., and Clowers, G. (2020), *Land Use Policy* (Seattle; secondary summary, Transfers Magazine).
- WGI, *Parking Structure Cost Outlook for 2024* (median $29,900 per space); UCLA Center for Parking Policy (2026), *No Such Thing as Free Parking* (above-ground average $52,000 per space).
- Baum-Snow, N., and Han, L. (2024), "The Microgeography of Housing Supply", *Journal of Political Economy*.
- Terner Center (2020), *The Hard Costs of Construction* (hard costs more than 60% of total).
- City of Mankato Planning Commission (2025), "Parking Information – Other Communities" (multifamily minimums).
- Census Building Permits Survey; Wisconsin statewide parcels V9 (2023); Madison tax parcels; Milwaukee MPROP.

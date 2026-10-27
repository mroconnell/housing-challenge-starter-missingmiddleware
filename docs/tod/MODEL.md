# TOD Gate 3 model, stage 1: both methods, the blind Madison predictions and the statewide run

Written 2026-10-26 by the Gate 3 model work package (stage 1 of 2) and implements [GATE3_MODEL_SPEC.md](GATE3_MODEL_SPEC.md). Section 11 (2026-10-27) implements the adopted net-effect sizing (AQ-050), which is now the main output. **No Madison building permit was read, counted or tabulated in this stage**, not even citywide, so the Madison predictions below are blind. The Madison count is stage 2 ([MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md)).

**Headline (updated 2026-10-27 for AQ-050).** The owner adopted sizing by citywide net effect. The statewide addition is now a share of the 2020 homes in the main-case station areas, 313,564 homes. Each share comes from a study that measured a whole city's net effect after upzoning, and is taken per upzoned home. Method A's per-acre response is used only to place homes across areas. The per-acre totals are now a sensitivity. Section 11 has the method; sections 2 to 10 keep the per-acre work it rests on.

- **Without the law:** 14,464 homes would be permitted near stops in 2027–2031 (all-housing baseline v2, central; low 8,386, high 21,874).
- **The law would add** (extra homes permitted, state):

| Scenario | Share of station-area stock, 2027–2031 | 2027 | 2028 | 2029 | 2030 | 2031 | 2027–2031 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Little response (Los Angeles) | 0.055% | 17 | 16 | 45 | 82 | 11 | **171** |
| Typical response (Stacy et al. 2023) | 0.8% | 245 | 233 | 663 | 1,202 | 166 | **2,509** |
| Strong response (Auckland) | 5.47% | 833 | 2,417 | 3,186 | 4,304 | 6,408 | **17,148** |
| Reference line (median of the three studies; equals the typical response) | 0.8% | 245 | 233 | 663 | 1,202 | 166 | 2,509 |

- **The typical response's range** is 665 to 4,352 homes, from Stacy et al.'s 95% interval of +0.2% to +1.4%.
- **Where the homes go:** Milwaukee city 50.7% and Madison city 49.3%, from method A's per-acre placement.
- **Per-acre sizing (sensitivity):** 14,212, 39,767 and 151,973 homes. The Wisconsin-measured per-acre rate, capped at the peer metros' 95th percentile, gives 6,834.
- **The Madison test** confirmed method A's per-acre prediction only weakly ([MADISON_TEST_RESULTS.md](MADISON_TEST_RESULTS.md)).
- **Method B** cannot be computed (section 5).

**Earlier results (stage 1, 2026-10-26), kept for the record**
- **Method A works as specified.** It predicts that Madison's TOD overlay added **0.25 homes per eligible acre per year** (90% interval 0.14 to 0.38) to the overlay's permits, compared with the ¼-mile ring. That is the New York pooled set's 0.671 extra homes per eligible acre per year per 1.0 of added floor area ratio (FAR), times the overlay's measured added FAR of 0.374, averaged over 2,932 eligible acres.
- **Method B cannot be computed as specified.** The specified cost test says no new mid-rise apartment earns its cost anywhere near stops in Milwaukee or Madison. Yet Milwaukee built 2,923 homes in 34 buildings of 5 or more homes in 2018–2025 on land zoned for 30 or more homes per acre, so take-up has no denominator (section 5).

## 1. Files and how to run

```bash
uv run --all-extras python scripts/run_tod_model.py           # rebuilds the lot layer, about 1 minute
uv run --all-extras python scripts/run_tod_model.py --cached  # reuses data/processed/tod_model/*.parquet
bash scripts/test.sh                                           # includes tests/test_tod_model.py
```

- **Code:**
  - [missing_middleware/tod/model.py](../../missing_middleware/tod/model.py): the pure functions (ramp, method A, feasibility, take-up, predictions, baseline near stops, aggregation).
  - [scripts/run_tod_model.py](../../scripts/run_tod_model.py): input and output. It reuses the parcel loaders and capacity code of `scripts/build_tod_station_areas.py`, adding land values and census tracts. Its station-area lots reproduce `reference/tod_station_areas.csv` exactly: main-case capacity gain is 1,918,185 homes, and the coded cities' added floor area matches. A test checks both.
- **Outputs** (`reference/`):

| File | What it holds |
| --- | --- |
| `tod_madison_test_predictions.csv` | Both methods' blind predictions for the Madison test, with intervals and status |
| `tod_model_statewide.csv` | **Main (net-effect sizing).** State × scenario × year (2027–2031 and the five-year total): parameter, timing, source, baseline near stops (low, central, high), addition, the typical range, share of stock, with-law total |
| `tod_model_by_area.csv` | Main: municipality piece × scenario, additions by year |
| `tod_model_by_county.csv`, `tod_model_by_assembly_district.csv`, `tod_model_by_senate_district.csv` | Main, aggregated |
| `tod_model_sensitivities.csv` | Five-year state totals: net-effect sensitivities and, with `sizing = per_acre`, the per-acre ones (section 7 and the Wisconsin-rate runs) |
| `tod_model_checks.csv` | Madison share comparison and the scale check rerun, both sizings |
| `tod_model_per_acre_statewide.csv`, `tod_model_per_acre_by_area.csv`, `tod_model_per_acre_by_county.csv` | **Sensitivity:** method A sized per acre, the former main outputs, with an unchanged layout |
| `tod_model_params.csv` | Every parameter with its value, unit, source and kind |
| `tod_model_feasibility.csv` | Method B diagnostics: cost, value and break-even rent by city |

- **Raw files** (git-ignored) are in `data/raw/tod_model/`, with `manifest.json` (URL, access date, bytes, SHA-256, licence). They are the HUD 2024 cost table, ACS B25111, the CBRE H1 2024 cap rate survey and the IREM 2024 income/expense summary. They were fetched with `curl` on 2026-10-26; the URLs are in the manifest.
- **Privacy:** parcel ids are used only in memory to join raw files. The lot cache in `data/processed/tod_model/` has none, and is git-ignored. Committed tables are by municipality or coarser. A test checks that no committed model file has a parcel-id column or a long number.

## 2. Parameters and sources

| Parameter | Value | Unit | Source | Kind |
| --- | --- | --- | --- | --- |
| *r*, typical | 0.671 (90%: 0.365 to 1.020) | extra homes permitted per eligible acre per year per 1.0 added FAR | New York pooled set, `reference/tod_case_estimates.csv` | measured |
| *r*, little | 0.240 | same | Chicago 2015 (held out), same file | measured |
| *r*, strong | 2.565 | same | mean of Park Slope (2.934) and Downtown Brooklyn (2.197) | measured |
| *r*, reference line | 0.456 | same | median of the measured per-FAR cases: the New York pooled set (which contains Park Slope and Downtown Brooklyn) and Chicago | measured |
| Ramp, years 1–5 | 0.489, 0.464, 1.321, 2.395, 0.331 | share of *r* in each year (mean 1) | New York pooled set's gap per added FAR by year since the change (0.33, 0.31, 0.89, 1.61, 0.22), from `reference/tod_case_rates_by_year.csv`, ÷ its mean | measured |
| Floor area per home | 1,192 (Milwaukee), 1,512 (Madison), 1,467 (elsewhere) | gross sq ft per home | `reference/tod_floor_area_per_home.csv` | measured |
| Building cost | $229.70 (Milwaukee), $227.75 (Madison), $233.28 (Kenosha), $226.77 (Eau Claire) | 2024 dollars of hard construction cost per sq ft | HUD 2024 Unit TDC Limits, Wisconsin, elevator building, 2-bedroom (900 sq ft) housing construction cost. Per sq ft it is the same for every bedroom count. Waukesha and Ozaukee use Milwaukee | published |
| Capitalisation rate | 5.75% | net operating income ÷ value | CBRE U.S. Cap Rate Survey H1 2024: Milwaukee, multifamily infill, Class A stabilised, 5.5%–6%, midpoint. Madison is not in the survey | published |
| Operating costs | 38.8% | operating expenses (with taxes, insurance and management) ÷ gross rents collected | IREM Income/Expense IQ National Summary 2024, multifamily: $7,981.42 per unit ÷ $20,575 per unit | published |
| Rent | tract value | dollars per month | ACS 2020–2024 B25064 median gross rent by tract. Where a tract is suppressed, the municipality's (11 of 160,692 lots in the main-case bands) | measured |
| New-building rent ratio | 1.066 (Milwaukee), 1.285 (Madison) | ratio | ACS 2020–2024 B25111: median gross rent in buildings built 2020 or later ÷ all buildings, by municipality. 1.0 where suppressed (flagged) | measured |
| Land | lot value | dollars | Assessed land value, 2025 tax roll: MPROP `C_A_LAND` for Milwaukee, V12 `LNDVALUE` elsewhere | measured |
| Take-up | **none** | share of feasible capacity permitted per year | Milwaukee: 2,923 homes ÷ 8 years ÷ 0 homes of feasible capacity | not computable |
| Madison overlay added FAR | 0.374 | FAR, acre-weighted | overlay stories minus base-district stories × lot coverage, from `reference/tod_zoning_rules_madison.csv` | coded rules |

**Departures from the spec, stated:**
1. **Two sources for the cap rate and operating costs, not one.** No single published source giving both a Wisconsin-relevant cap rate and an operating-cost ratio was found in the time available. Sources searched:
   - the Milwaukee and Madison assessors (no published apartment income model found);
   - the Cook County assessor (blocks scripts);
   - Freddie Mac's 2024 outlook (cap rates only);
   - NAA (paywalled);
   - a Kansas Department of Revenue study (server refused connections).

   CBRE gives the cap rate and IREM the operating costs. Neither value was tuned. The method B result does not hinge on them (section 5).
2. **New-building rent.** The spec scales rents "by the ratio of new-building to all-building rents in each city's recent permits, if available". Permits carry no rents. ACS B25111 gives the measured ratio of rents in buildings built 2020 or later to rents in all buildings, by municipality, so it is used. The unscaled reading, which is the spec's fallback, is a sensitivity. Both readings give no feasible capacity in Milwaukee or Madison.
3. **Ramp, year-5 alternative.** Year 5 is replaced by the mean of years 3 to 5. The divisor stays the measured mean of years 1 to 5, which is what *r* is. So the sensitivity raises the total, rather than only reshaping it.

## 3. Method A (per-acre sizing; a sensitivity since AQ-050)

addition(area, year *k*) = Σ over eligible lots of (lot acres × max(law FAR − current FAR, 0)) × *r* × ramp(*k*)

- **Added floor area per lot** is `added_floor_area_sqft` from the station-area build. It is 0 where current zoning already allows the law's FAR, on planned developments, and in Madison's downtown districts.
- **Areas:** main-case bands (rail and rapid stops within ½ mile, 15-minute buses within ¼ mile).
  - Milwaukee city: 14,198 eligible acres and 6,008 acre-units of added FAR, an acre-weighted mean of 0.42 added FAR.
  - Madison city: 10,180 eligible acres and 5,840 acre-units, a mean of 0.57.
- **Ramp:** because the ramp averages 1, each five-year total is 5 × *r* × the area's acre-units of added FAR.
- **No negatives:** an area with no added FAR adds 0.

**Results, per-acre sizing** (extra homes permitted, state; `tod_model_per_acre_statewide.csv`):

| Scenario | 2027 | 2028 | 2029 | 2030 | 2031 | 2027–2031 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Little response | 1,390 | 1,319 | 3,754 | 6,808 | 941 | 14,212 |
| Reference line | 2,641 | 2,504 | 7,129 | 12,929 | 1,786 | 26,990 |
| Typical response | 3,891 | 3,690 | 10,505 | 19,050 | 2,632 | 39,767 |
| Strong response | 14,868 | 14,102 | 40,144 | 72,801 | 10,059 | 151,973 |

- **Where:** in the typical response, Milwaukee city adds 20,165 homes over 2027–2031 and Madison city 19,603. Without the law, the two cities would permit 3,394 and 9,220 homes near stops over the same years.
- **Year 5 drop:** the year-by-year shape is the New York pooled set's, including its year-5 drop. That drop is shown as measured.

**Scale check.** Wisconsin's all-housing baseline is 122,619 homes over 2027–2031 statewide. The typical response's addition near stops in two cities, 39,767 homes, is 32% of it. The strong response, 151,973 homes, exceeds it. *r* comes from New York rents and building types. The Madison test (stage 2) is the check on whether it transfers.

## 4. The blind Madison predictions

`reference/tod_madison_test_predictions.csv`. Unit: extra homes permitted per eligible acre per year, inside the overlay minus the ¼-mile ring outside it, after (2023–2025) minus before (2017–2022). This is the pre-registered difference-in-differences.

| Method | Prediction | 90% interval | How |
| --- | ---: | --- | --- |
| **A (judged)** | **0.251** | **0.136 to 0.382** | 0.671 × 0.374 added FAR |
| A, ramp-matched (shown, not judged) | 0.091 | 0.049 to 0.138 | the New York pooled set's mean gap per added FAR in the years the test covers (event years 0–2, since 2023 is the adoption year) × 0.374 |
| **B (judged)** | **not computable** | — | Milwaukee take-up has no denominator (section 5). The overlay's change in feasible capacity is also 0 homes |

- **Dose.** The dose is the overlay's added FAR on the pre-registered eligible land: 2,931.7 acres, single-family use excluded, the same as `reference/tod_madison_test_land.csv`.
- **Where the dose comes from.** Only five districts gain stories in the overlay:
  - RMX, 5 to 8 stories: 715 of the 1,096 acre-units of added FAR;
  - CC, 5 to 6 stories: 239;
  - TR-V2, 3 to 4: 52;
  - TSS and NMX, 3 to 4: 62 and 28.

  CC-T, SR-V2, TR-U2, PD and the employment districts get no added FAR. In TR-U2 the summary prints fewer overlay stories than base stories.
- **What the dose leaves out.** The overlay also permits 3- and 4-home buildings in small residential districts, and removed parking minimums. Neither is in the FAR dose, so the prediction is for added floor area alone.
- **Capacity on paper.** The overlay's change in capacity, before any cost test, is 22,887 homes on that land.
- **Chicago, for the tie-break (spec 4.4):**
  - Method A predicts 0.671 × 0.50 = 0.34 extra homes per eligible acre per year. Chicago measured +0.12 (−0.02 to +0.26).
  - Method B cannot be predicted for Chicago either. It would need Chicago land values and costs, and it fails at the take-up step anyway.

## 5. Method B: why it stops

The spec's test: capitalised net rent per home = 12 × rent × new-building ratio × (1 − 38.8%) ÷ 5.75%. A lot is feasible when that, times the homes the law allows, covers building cost per home (HUD cost per sq ft × measured floor area per home) plus assessed land.

| Area | Building cost per home | Rent needed, with land free (ACS, before the new-building ratio) | Median tract rent near stops | Highest tract rent near stops | Feasible capacity gain (homes) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Milwaukee city | $273,798 | $2,011 a month | $1,042 | $1,961 | 0 of 736,177 |
| Madison city | $344,355 | $2,098 a month | $1,400 | $1,759 | 0 of 464,239 |
| Places not coded | about $334,000 | about $2,616 a month | $1,164 | $2,156 | 1,686 of 717,769 |

Source: `reference/tod_model_feasibility.csv`. The row for the places not coded uses one place's cost and ratio; it is indicative only.

- **The take-up denominator is 0.** Under current zoning, Milwaukee land zoned for 30 or more homes per acre has room for 315,571 more homes (7,385 acres), and none of it passes the test.
- **But building happened there.** 2,923 homes were built in 34 buildings of 5 or more homes in 2018–2025 on that land. Take-up = 2,923 ÷ 8 years ÷ 0 has no value.
- **Two readings of the inputs fail alike.** This holds with rents scaled to new buildings and without (sensitivity `rent_unscaled`). In both, Madison's overlay changes feasible capacity by 0 homes.
- **Why the test fails.** It treats every home as carrying a full share of gross floor area: 1,192 to 1,512 sq ft, including common areas and parking. It prices that area at HUD's hard cost, against median rents of all rented homes in each tract. Real projects that were built clear this test with rents, costs or financing that the table's inputs do not capture: newer-building premiums within a tract, tax credits, tax incremental financing, or smaller homes.
- **No rescue was attempted.** Changing the cost basis, rent or cap rate until the test passes would be tuning to the cases, which the spec forbids. The conductor should decide whether method B is dropped (method A then wins the test by default, spec 4.4) or re-specified before the Madison count.

## 6. Baseline near stops, and places whose zoning is not coded

- **Baseline near stops:** each municipality's all-housing baseline (v2, every building size) × its share of 2020 homes near stops (`reference/tod_near_stop_homes_by_muni.csv`).
  - Statewide that is **14,464 homes over 2027–2031**, central case. The low case is 8,386 and the high case 21,874.
  - Milwaukee city has 3,394 of them and Madison city 9,220.
  - It matches the shared baseline's split (a test checks it). Additions sit on top.
- **Places not coded get no method A dose in the main case.** The spec takes added FAR from `added_floor_area_sqft`, and the station-area build sets it to 0 for these 27 places. That 0 means no current FAR is coded, not that density does not rise. As specified, they add nothing under method A.
- **The alternative is a large judgement.** Treat the existing homes as the current allowance, as the fallback does for capacity. Then added floor area = capacity gain × 1,467 sq ft, and these places would add 81,136 homes in the typical response. Over 2027–2031 the total would be 120,903 instead of 39,767. Their acre-weighted added FAR (about 2.4) is far above the coded cities' (0.42 and 0.57). The fallback compares the law with what is built, not with what zoning allows. Calibrating it by the coded cities' ratio (0.719) still gives 98,092. Both are sensitivities below. **This needs an owner or conductor decision**, best by coding Wauwatosa and West Allis.

## 7. Sensitivities

Five-year state totals, 2027–2031, in extra homes permitted (method A per acre, typical response, unless stated). Source: `tod_model_sensitivities.csv`, rows with `sizing = per_acre`.

| Group | Sensitivity | Baseline near stops | Addition |
| --- | --- | ---: | ---: |
| Main | as specified | 14,464 | 39,767 |
| The law's addition | *r* at the low and high ends of its 90% interval | 14,464 | 21,616 and 60,448 |
| | Park Slope alone (2.934); Downtown Brooklyn alone (2.197) | 14,464 | 173,820 and 130,125 |
| | year-5 ramp = mean of years 3 to 5 | 14,464 | 47,864 |
| | floor area per home 1,000 sq ft (no change to coded added FAR) | 14,464 | 39,767 |
| | single-family lots left out (G2-8) | 14,464 | 11,590 |
| | uncoded places get a dose from their capacity | 14,464 | 120,903 |
| | the same, scaled by 0.719 (coded ÷ fallback capacity in Milwaukee and Madison) | 14,464 | 98,092 |
| Baseline only | low baseline; high baseline | 8,386; 21,874 | 39,767 |
| | Census as published for Milwaukee | 11,875 | 39,767 |
| Where homes land | rail and rapid stops only (½ mile) | 6,140 | 9,439 |
| | high case (20-minute buses, ¼ mile) | 15,725 | 45,883 |
| | all 15-minute stops within ½ mile | 18,383 | 56,338 |

- **Single-family lots carry most of the coded cities' added FAR.** Their current floor-area estimate is low: 2 to 3 stories × 70% coverage. So leaving them out cuts the addition by 71%.
- **Method B:** every row is blank, because take-up is not computable. Its feasible capacity gain is shown in each row.

## 8. Checks (spec section 8)

These are in `tests/test_tod_model.py`.
- No addition is negative.
- Areas with no added FAR, or no feasible capacity, add zero.
- Areas add up to the state, and so do counties and Assembly and Senate districts; years add up to the five-year total.
- The baseline near stops equals the shared baseline × near-stop shares, 14,464.
- Capacity equals the station-area table.
- The predictions file exists, and the run script references no Madison permit file or function.
- No parcel ids are committed.

Still to do:
- **Commit order is the proof that the predictions are blind.** This stage did not commit; the conductor commits the predictions before the Madison count.
- **The independent verifier** recomputes the state totals (stage 2).

## 9. What is measured and what is assumed

- **Measured:**
  - *r*, the ramp and floor area per home;
  - tract rents and the new-building rent ratio;
  - assessed land values;
  - Milwaukee's new homes on land zoned for 30 or more homes per acre;
  - the baseline and near-stop shares.
- **Published, not ours:** HUD costs, the CBRE cap rate and IREM operating costs.
- **Coded or assumed:**
  - the zoning rules (stories × coverage stands in for FAR where the code prints none, with 70% coverage by default);
  - the uncoded places' treatment (section 6);
  - the assignment of district crosswalk shares. These come from the ADU crosswalk, which weights by detached homes, not by homes near stops, so a municipality's TOD addition is split across districts as its detached homes are.
- **Not modelled:**
  - the law's interaction with parking reform;
  - New York-to-Wisconsin market transfer. The Madison test addresses it;
  - Madison lots with no V12 land value. They are 30% of Madison parcel records, mostly single-family and condominium units far from stops. The land values matter only to method B, which fails before land enters.

## 10. Scale check

This is a check shown to the owner, not a cap. No model number changes because of it. It asks a single question. Spread over all the land near stops, does a scenario's response per acre mean more apartment permits than a metro of Milwaukee's or Madison's size has ever had?

**How it is measured**
- **The rate:** homes in buildings of 5 or more homes permitted in a year, per 1,000 existing homes on July 1 of that year. It is a yearly rate.
- **Permits:** Census Building Permits Survey (BPS) annual county files, 2000–2025, including the Census estimates for places that did not report.
- **Existing homes:** Census housing-unit estimates by county (July 1). The 2000–2009 figures are intercensal, 2010–2019 come from Vintage 2020 and 2020–2025 from Vintage 2025. Moving from one vintage to the next leaves a small step. For example, the Milwaukee metro's stock rises by 10,794 homes between 2019 and 2020.
- **Peer metros:** the 79 US metropolitan areas with a 2020 Census population of 500,000 to 2,500,000 people. Areas use the July 2023 federal (OMB) definitions, and population is the sum of each area's counties from the Census 2010–2020 intercensal table. Each metro keeps the same counties in every year, so its series is not broken when the official definitions change. The 79 metros over 26 years give 2,054 metro-years.
- **Left out:** the five Connecticut metros. Since 2023, permits there are reported by planning region, but earlier permits and the pre-2020 housing estimates use the old counties, and the two do not match. Three peer counties have no permit-issuing places at all (Torrance NM, Bracken KY, Hudspeth TX); they count as 0 permits.
- **Checked:** for 2024 and 2025, all 158 metro totals built from counties match the published BPS metro files exactly.
- **Milwaukee metro** means Milwaukee, Waukesha, Ozaukee and Washington counties. **Madison metro** means Dane, Columbia, Green and Iowa counties. Both match the 2023 definitions.

**The benchmarks**
- **Highest year in any peer metro:** in 2021 the Austin metro permitted 25,642 homes in 5+ unit buildings. It had 996,124 existing homes, so the rate was 25.7 per 1,000 (a yearly rate).
- **95th percentile:** 9.06 per 1,000 existing homes. 95% of the 2,054 metro-years were at or below it.
- **Milwaukee metro:**
  - Its highest year was 2016: 2,328 homes in 5+ unit buildings ÷ 675,947 existing homes, or 3.44 per 1,000.
  - In 2021–2025 its average was 1.80 per 1,000. That is the mean of the five yearly rates; it permitted 1,268 such homes a year on average.
- **Madison metro:**
  - Its highest year was 2021: 5,235 homes ÷ 309,537 existing homes, or 16.9 per 1,000. Only six of the 2,054 metro-years were higher.
  - In 2021–2025 its average was 13.4 per 1,000, with 4,314 such homes a year on average.
  - **So Madison is already above the 95th percentile with no law at all.**

**How a scenario is converted**
- A scenario's homes added each year are counted as permits for 5+ unit buildings. That is an assumption.
- A metro's addition is the sum over its counties in the per-acre county file (`reference/tod_model_by_county.csv` when this check was run; now `reference/tod_model_per_acre_by_county.csv`). These county sums add up to the statewide file in every scenario and year.
- All of the statewide addition falls in the two metros: 50.7% in Milwaukee County and 49.3% in Dane County. These shares are the same in every scenario and every year.
- The addition is divided by the metro's existing homes on July 1, 2025: 710,943 in the Milwaukee metro and 331,967 in the Madison metro.
- The result is added to the metro's own 2021–2025 average rate. The model's own baseline near stops is smaller: 1.19 per 1,000 existing homes a year for Milwaukee and 6.13 for Madison. Each is the 2027–2031 central baseline near stops ÷ 5 years ÷ 2025 existing homes. These are shown only as context.
- Only method A is checked. Method B has no numbers (section 5).

**Results, in the peak year (2030, ramp share 2.395)**

| Scenario | Metro | Extra homes in 2030 | Extra per 1,000 existing homes | Total per 1,000 (with 2021–2025 average) | Above peer maximum (25.7)? | Above 95th percentile (9.06)? | Above own maximum? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Little response | Milwaukee | 3,452 | 4.9 | 6.7 | No | No | Yes (3.44) |
| Reference line | Milwaukee | 6,556 | 9.2 | 11.0 | No | Yes | Yes |
| Typical response | Milwaukee | 9,660 | 13.6 | 15.4 | No | Yes | Yes |
| Strong response | Milwaukee | 36,915 | 51.9 | 53.7 | Yes | Yes | Yes |
| Little response | Madison | 3,356 | 10.1 | 23.6 | No | Yes | Yes (16.9) |
| Reference line | Madison | 6,373 | 19.2 | 32.6 | Yes | Yes | Yes |
| Typical response | Madison | 9,390 | 28.3 | 41.7 | Yes | Yes | Yes |
| Strong response | Madison | 35,886 | 108.1 | 121.5 | Yes | Yes | Yes |

The extra rate is the extra homes ÷ 2025 existing homes × 1,000, a yearly rate.

**Which years go over (2027–2031)**
- **Above the highest peer year (25.7 per 1,000):**
  - The strong response goes over in Milwaukee in 2029 and 2030, and in Madison in all five years.
  - The typical response goes over in Madison in 2029 and 2030.
  - The reference line goes over in Madison in 2030.
  - The little response never goes over.
- **Above the 95th percentile (9.06 per 1,000):**
  - In Milwaukee: the strong response in 2027–2030, the typical response in 2029–2030 and the reference line in 2030. The little response never does.
  - In Madison, every scenario goes over in every year, because the metro's own recent rate (13.4) is already above the 95th percentile.
- **Above the metro's own highest year:**
  - In Milwaukee: the typical and strong responses in all five years, the reference line in 2027–2030 and the little response in 2029–2030.
  - In Madison: the typical and strong responses in all five years, the reference line in 2027–2030 and the little response in 2029–2030.

**What it means**
- The little response stays within what peer metros have done in both metros.
- The reference line and typical response stay below the highest peer year in Milwaukee. In Madison they pass it in the ramp's peak years, because Madison already permits apartments at a high rate.
- The strong response would require a rate about twice the highest peer year in Milwaukee (53.7 vs 25.7 per 1,000). In Madison it would be about five times that year (121.5 per 1,000). No peer metro has done that in 26 years.
- To reach the highest peer year, the Milwaukee metro could add about 17,000 extra homes in one year: (25.7 − 1.80) × 710,943 ÷ 1,000. The Madison metro could add about 4,100: (25.7 − 13.4) × 331,967 ÷ 1,000.

**Files:** `scripts/run_tod_scale_check.py` (fetches the raw Census files into `data/raw/census_bps_cbsa/` with `_downloads.json` the first time, then runs offline); `missing_middleware/tod/scale_check.py` (the pure functions); `reference/tod_scale_check.csv` (benchmark, metro-history and scenario rows, told apart by the `kind` column); `reference/tod_scale_check_metro_years.csv` (the 2,054 peer metro-years); `tests/test_tod_scale_check.py`.

## 11. Main sizing: citywide net effect (AQ-050)

The owner adopted this sizing on 2026-10-27 (AQ-050). The values are corrected as in [GATE3_MODEL_SPEC.md](GATE3_MODEL_SPEC.md) section 9 and [research/NET_EFFECT_SOURCES.md](research/NET_EFFECT_SOURCES.md).

The switch is `model.size_additions(..., mode="per_acre" | "net_effect")`. Net effect is the main mode, and per acre is the sensitivity.

**How it works**
- **The statewide addition** = a citywide net effect × the 2020 census homes in the main-case station areas, 313,564 (`tod_near_stop_homes_by_muni.csv`).
- **Per upzoned home:** each effect is divided by its study's coverage share, so it applies per upzoned home. The as-published reading is a sensitivity.
- **Timing:** each scenario's yearly shares of the five-year total.
- **Placement:** each municipality gets its share of method A's per-acre addition.
  - In the main case that is Milwaukee city 50.7% and Madison city 49.3%.
  - The uncoded places get no share, because method A gives them no dose (section 6). A sensitivity gives them one.
- **Never negative:** no addition is negative.

**Scenario values**

| Scenario | Published effect | Corrections | Share of station-area stock, 2027–2031 | Timing |
| --- | --- | --- | ---: | --- |
| Little | Los Angeles TOC (Kestelman 2025): +0.04 percentage points of stock growth over six years, 2017–2023 | × 5/6 for five years = 0.0333%; ÷ 0.61, the share of LA's homes in the program's area | **0.0546%** | New York pooled ramp (no yearly profile published) |
| Typical | Stacy et al. 2023 (*Urban Studies*): +0.8% of USPS addresses per loosening reform, average of years 3 and later (s.e. 0.3 points) | None. Coverage is not measured, so it is used as published | **0.8%** (range 0.2% to 1.4%, the 95% interval) | New York pooled ramp, see below |
| Strong | Auckland (Greenaway-McGrevy and Phillips 2023): 21,808 extra permits over 2016–2021 = 4.11% of 530,300 dwellings | ÷ 0.752, the share of residential land upzoned | **5.47%** | Auckland's profile, rescaled (below) |
| Reference line | Median of the three values above. Each study is counted once, and no case is in two places | — | 0.8% (equal to the typical response) | New York pooled ramp |

**Timing assumptions, stated**
- **Stacy et al.:**
  - The paper's effect is an average over years 3 and later after a reform. Its year-by-year model shows no rising path, and the implementation years show no significant effect.
  - The model nevertheless places the whole 0.8% inside 2027–2031, shaped by the New York pooled ramp: shares of 9.8%, 9.3%, 26.4%, 47.9% and 6.6%.
  - This is generous to the law in years 1 and 2. The total over five years equals the paper's level effect, which is an assumption.
- **Auckland:**
  - The paper's year 0 is 2015, so 2016–2021 are its years 1 to 6.
  - Its year 1 (2016, when the plan became operative) is negative, −2.63, and the law never subtracts. So the five model years take the shape of 2017–2021, which are paper years 2 to 6: 2.34, 6.79, 8.95, 12.09 and 18.00 per statistical area.
  - Those five values are rescaled so they sum to the stated total, 21,808 permits (each × 21,808 ÷ (48.17 × 479)). This nets 2016's negative year into the total.
  - The shares are 4.9%, 14.1%, 18.6%, 25.1% and 37.4%. Permits were still rising in 2021, so the strong scenario peaks in 2031.
- **Los Angeles:** no yearly profile is published, so the New York pooled ramp is used.

**Results** (`tod_model_statewide.csv`): see the headline table at the top. Extra homes over 2027–2031: little 171, typical 2,509 (665 to 4,352), strong 17,148. Without the law, 14,464 homes would be permitted near stops.

**Sensitivities** (`tod_model_sensitivities.csv`; five-year state totals, extra homes)

| Sensitivity | Little | Typical | Strong |
| --- | ---: | ---: | ---: |
| Main (per upzoned home) | 171 | 2,509 | 17,148 |
| Typical at the ends of Stacy et al.'s 95% interval | | 665 to 4,352 | |
| As published (no coverage division) | 105 | 2,509 | 12,895 |
| Strong timed by the New York ramp | | | 17,148 (2030 peak) |
| Uncoded places placed by their capacity dose (Milwaukee metro share of the typical response: 1,683 instead of 1,272) | 171 | 2,509 | 17,148 |
| Rail and rapid stops only (stock 89,528) | 49 | 716 | 4,896 |
| High case (stock 351,606) | 192 | 2,813 | 19,228 |
| All 15-minute stops within ½ mile (stock 403,304) | 220 | 3,226 | 22,055 |
| Baseline only: low / high / Census as published | baseline 8,386 / 21,874 / 11,875; additions unchanged | | |

**Per-acre sizing (sensitivity, `sizing = per_acre`):**
- **Method A as in sections 3 and 7:** little 14,212, typical 39,767, strong 151,973 and reference line 26,990. The section 7 variants are in the same file.
- **Method A with the Wisconsin-measured response:**
  - *r* = 0.2275 extra homes per eligible acre per year per 1.0 of added FAR, the mean of Madison's 0.215 and Chicago's 0.240.
  - **Uncapped:** 13,477 extra homes.
  - **Capped:** 6,834. Each metro is capped year by year so its total 5+ unit permits stay at or below the peer 95th percentile, 9.06 per 1,000 existing homes a year.
  - **The caps:** the Milwaukee metro may add up to 5,161 homes a year and never reaches it. The Madison metro's cap is 0, because its own 2021–2025 rate, 13.4 per 1,000, is already above the 95th percentile.

**Check 1: Madison's measured overlay effect as a share of stock** (`tod_model_checks.csv`, `check = madison_share`)
- **Measured (2023–2025):** the effect × acres × 3 years, with the test's 90% interval carried through.
  - **Per-FAR effect over all 2,931.7 eligible overlay acres:** 707 extra homes, **1.76%** of the 40,185 homes on overlay lots (−3.66% to +6.76%).
  - **Effect on the 614.7 treated acres only:** 388 homes. That is 0.96% of the same overlay stock (−2.0% to +3.7%), or **8.7% per upzoned home**: the 4,461 homes on treated land, −18% to +33%.
- **Each scenario, model years 1–3, share of station-area stock per upzoned home:**

  | Scenario | Net effect | Per acre |
  | --- | ---: | ---: |
  | Little | 0.025% | 2.06% |
  | Typical | 0.36% | 5.77% |
  | Strong | 2.05% | 22.0% |

- **Reading:**
  - Madison's overlay-wide share (1.76%) is closest to the net strong scenario's (2.05%).
  - Its per-upzoned-home share (8.7%) lies above every net scenario and between the per-acre typical and strong scenarios.
  - Both measured intervals include zero and every net scenario, so Madison cannot pick a scenario.
  - Madison's figure is the local effect (overlay against ring), which by construction can count building moved from nearby blocks. The net-effect scenarios exclude that.
  - The measured shares use 2026 assessor homes; the scenarios use 2020 census homes.

**Check 2: scale check rerun** (`check = scale`). The method is as in section 10. All figures are 5+ unit permits per 1,000 existing homes a year, including each metro's 2021–2025 average (Milwaukee 1.80, Madison 13.4).

| Scenario (net effect) | Milwaukee metro: peak extra; peak total (year) | Madison metro: peak extra; peak total (year) | Above the peer maximum (25.7)? | Above the 95th percentile (9.06)? | Above the metro's own maximum (3.44; 16.9)? |
| --- | --- | --- | --- | --- | --- |
| Little | 0.06; 1.85 (2030) | 0.12; 13.6 (2030) | no | Madison only, every year, from its own baseline | no |
| Typical | 0.86; 2.65 (2030) | 1.78; 15.2 (2030) | no | Madison only, as above | no |
| Strong | 4.57; 6.37 (2031) | 9.51; 23.0 (2031) | no | Madison only, as above | yes, both metros, 2028–2031 |

- No net-effect scenario reaches the highest peer year.
- Only the strong scenario passes either metro's own record.
- For comparison, the per-acre typical response peaks at 15.4 in Milwaukee and 41.7 in Madison (section 10).

**Files and tests**
- The main outputs are listed in section 1.
- `scripts/run_tod_scale_check.py` (not owned by this package) still reads `tod_model_by_county.csv` and `tod_model_statewide.csv` for method A rows. Those rows are now in `tod_model_per_acre_by_county.csv` and `tod_model_per_acre_statewide.csv`, with the same layout. The script's two paths need updating before it is rerun. Its committed output, `tod_scale_check.csv`, is unchanged.
- `tests/test_tod_model.py` (`TestNetSizing`) checks:
  - the switch;
  - the corrected parameter values;
  - Auckland's rescaled profile, which sums to 21,808 permits;
  - no negative additions;
  - state = share × stock;
  - areas, counties and districts add up to the state, with the baseline 14,464;
  - years add up to the five-year total;
  - scenarios are ordered and the typical range brackets the typical response;
  - the per-acre sensitivity is still ordered;
  - the cap holds.

**Limits**
- **Applying the effects to station-area stock.** All three studies measure citywide effects of citywide or large-area reforms. Wisconsin's station areas cover a smaller part of each city, which leaves more nearby land to pull building from. The source check notes that the per-upzoned-home effect could then be lower, not higher.
- **Stacy et al.** counts reforms of all kinds, mostly ADU and lot-size rules (28 of 96 changed floor area, density or height). It measures addresses, not permits.
- **The Los Angeles coverage share (0.61)** is derived from rounded means in the dissertation's Table 1.1. The working-paper PDF could not be read, and its figure may differ slightly ("fewer than 560 units").
- **Placement rests on method A's shares,** which put every home in the two coded cities.

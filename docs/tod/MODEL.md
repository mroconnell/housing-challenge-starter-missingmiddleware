# TOD Gate 3 model, stage 1: both methods, the blind Madison predictions and the statewide run

Written 2026-10-26 by the Gate 3 model work package (stage 1 of 2). It implements [GATE3_MODEL_SPEC.md](GATE3_MODEL_SPEC.md). **No Madison building permit was read, counted or tabulated in this stage**, not even citywide, so the Madison predictions below are blind. The Madison count is stage 2 ([MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md)).

**Headline**
- **Method A works as specified.** It predicts that Madison's TOD overlay added **0.25 homes per eligible acre per year** (90% interval 0.14 to 0.38) to the overlay's permits, compared with the ¼-mile ring. That is the New York pooled set's 0.671 extra homes per eligible acre per year per 1.0 of added floor area ratio (FAR), times the overlay's measured added FAR of 0.374, averaged over 2,932 eligible acres.
- **Method B cannot be computed as specified.** The specified cost test says no new mid-rise apartment earns its cost anywhere near stops in Milwaukee or Madison. Yet Milwaukee built 2,923 homes in 34 buildings of 5 or more homes in 2018–2025 on land zoned for 30 or more homes per acre. The take-up rate therefore has a denominator of 0 homes and no value. Per the brief, this part is stopped and explained (section 5); nothing was tuned to rescue it.
- **Statewide, method A, main case:** 14,464 homes would be permitted near stops in 2027–2031 without the law (all-housing baseline v2, central). The law would add:

| Scenario | *r* | Extra homes, 2027–2031 |
| --- | --- | --- |
| Little response (Chicago) | 0.240 | 14,212 |
| Reference line | 0.456 | 26,990 |
| Typical response (New York pooled set) | 0.671 | 39,767 |
| Strong response (Park Slope and Downtown Brooklyn) | 2.565 | 151,973 |

  - *r* is extra homes permitted per eligible acre per year per 1.0 of added FAR.
  - The reference line is the median of the measured per-FAR cases.
  - In this main case all of the addition is in Milwaukee city and Madison city. Section 6 explains why the uncoded suburbs add nothing here, and what they add if given a dose.

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
| `tod_model_statewide.csv` | State × method × scenario × year (2027–2031 and the five-year total): baseline near stops (low, central, high), addition, with-law total |
| `tod_model_by_area.csv` | Municipality piece × method × scenario: inputs, baseline near stops, additions by year |
| `tod_model_by_county.csv`, `tod_model_by_assembly_district.csv`, `tod_model_by_senate_district.csv` | The same, aggregated |
| `tod_model_sensitivities.csv` | Spec section 7, five-year state totals |
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

## 3. Method A

addition(area, year *k*) = Σ over eligible lots of (lot acres × max(law FAR − current FAR, 0)) × *r* × ramp(*k*)

- **Added floor area per lot** is `added_floor_area_sqft` from the station-area build. It is 0 where current zoning already allows the law's FAR, on planned developments, and in Madison's downtown districts.
- **Areas:** main-case bands (rail and rapid stops within ½ mile, 15-minute buses within ¼ mile).
  - Milwaukee city: 14,198 eligible acres and 6,008 acre-units of added FAR, an acre-weighted mean of 0.42 added FAR.
  - Madison city: 10,180 eligible acres and 5,840 acre-units, a mean of 0.57.
- **Ramp:** because the ramp averages 1, each five-year total is 5 × *r* × the area's acre-units of added FAR.
- **No negatives:** an area with no added FAR adds 0.

**Results, main case** (extra homes permitted, state; `tod_model_statewide.csv`):

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

Five-year state totals, 2027–2031, in extra homes permitted (method A, typical response, unless stated). Source: `tod_model_sensitivities.csv`.

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
- A metro's addition is the sum over its counties in `reference/tod_model_by_county.csv`. These county sums add up to the statewide file in every scenario and year.
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

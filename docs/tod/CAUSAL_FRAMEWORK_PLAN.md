# TOD causal framework: locked plan

Owner approved the framework on 2026-11-02 at 23:29 (pitch: learning thread, "measure the cause, then carry it to
Wisconsin"). The learning thread's implementable plan is
[learning/tod_causal_framework_plan_v1.md](learning/tod_causal_framework_plan_v1.md). This file is the locked
version. Each section below was written **before its first count** (date given). Anything chosen after seeing a result
is labelled *post hoc* and shown beside the locked version. Later sections are added by other threads.

Shared rules (all tests):

- **Places:** the 11 D-11 places of [OPTION_D_PLAN.md](OPTION_D_PLAN.md): New York, Philadelphia, Austin 2009,
  Charlotte 2019, Chicago 2015, Denver 2018, Portland 2020, Seattle Mount Baker 2014, Seattle Othello 2012,
  Salt Lake City 2010, Saint Paul 2011. A place is dropped from a test only by a rule written here.
- **Outcome data:** the station-area lot tables (`data/processed/tod_station_area/lots_*.parquet`), dates
  "permit_est" with hand-check corrections (`run_tod_station_model.event_windows`), implausible lots left out, land
  counted once (`acres_land`), each case's own before and after windows.
- **Units:** lead with extra new homes per 100 lot acres a year. Beside it: per 1,000 existing city homes, and the
  district's share of the city's new homes.
- **Intervals:** 90% throughout. Report per place, pooled (each place equal weight) and the leave-one-place-out range.
- **Outputs:** summaries only in `reference/` (no parcel ids, no lot rows). Nothing in the tool or its reference lines
  changes from these tests.

## Test 1 (T1): citywide check (locked 2026-11-02, before any count)

Two measures. **1A** is the lot-table measure asked for first (as `scripts/run_tod_citywide_per1000.py`). **1B** is the
learning plan's whole-city permit-survey version (added at the coordinator's request the same evening, also before
any count). Script: `scripts/run_tod_causal_citywide.py`. Output: `reference/tod_causal_citywide_11.csv`.

### 1A. Station-area extra homes, scaled to the city (lot tables)

- **Estimand:** extra homes permitted a year attributable to the reform near reform stops, as the station-area model
  measures it, expressed per 1,000 existing city homes (a year and over 5 years).
- **Comparison:** reform stops vs comparison stops, per band:
  extra = (reform after/yr − reform before/yr) − reform existing homes × (comparison change per existing home).
  Two scopes: all bands to 1 mile, and ¼ mile only. Functions reused from `run_tod_citywide_per1000.py` unchanged.
- **Places:** all 11. Seattle's two cases are two places (as D-11); New York's and Philadelphia's rezonings are
  summed within the place, a lot claimed by k rezonings weighted 1/k (as that script).
- **Interval:** 1,000 bootstrap draws over stops, reform and comparison stops resampled separately, seed 20261102,
  case index in the fixed order of the place list above; a place's draws are summed draw by draw over its cases.
- **City homes:** New York, Philadelphia, Charlotte, Saint Paul, Seattle, Chicago: the 2026-10-27 table's stock
  (2010 Census). Portland: as `run_tod_citywide_per1000.py`. Austin, Salt Lake City: 2010 Census blocks inside the
  2020 place boundary (the 2000 count the rule asks for is not on disk; flagged). Denver: 2020 Census blocks inside the
  2024 place boundary (no 2010 Colorado blocks on disk; flagged, overstates the 2017 stock by the 2018–2020 growth).
- **Units shown:** extra homes per 100 lot acres a year (÷ reform-group lot acres in the scope; also ÷ district acres,
  i.e. in-reform-area acres in the scope), per 1,000 city homes a year and over 5 years, and
  **district share of the city's new homes in the after window** = new homes on in-reform-area lots (all groups, after
  window, 1/k weights) per year ÷ Census permit survey (BPS) place total per year over the same years. BPS sources:
  New York = sum of its five boroughs; Charlotte = Mecklenburg County office (covers more than the city: the share is
  a lower bound, flagged). The two counts come from different sources (lot tables vs BPS); flagged.
- **Carry-through (coordinator addition, spillover downside):** per place, extra per 1,000 homes over all bands to
  1 mile ÷ extra per 1,000 homes within ¼ mile. Below 1 means part of the ¼-mile gain is offset farther out (within
  1 mile). This is not a whole-city net (lots beyond 1 mile are not in the tables); 1B is.
- **Reading rule (locked):** pooled all-bands-to-1-mile extra per 1,000 homes a year (equal-weight mean, draws
  averaged draw by draw): "consistent" if positive with a 90% interval above 0; "not contradicted" if positive with an
  interval including 0; "contradicts" if the point is ≤ 0. 1A is a second measure; 1B feeds the downside case.

### 1B. Whole-city difference-in-differences on the Census permit survey (learning plan T1)

- **Estimand:** net extra homes permitted in the whole city per 1,000 existing city homes a year caused by the reform,
  including homes that moved into the station area from elsewhere in the city (counted as a loss).
- **Data:** BPS annual place files 2000–2025 (`data/raw/tod_control_cities/bps`), all units (main) and 5+ units
  (second series); 2010 Census housing units by place (Gazetteer HU10). Linking, the 0-month non-report rule and
  Charlotte as the Mecklenburg County office (per 1,000 county homes, converted to city homes) as
  `missing_middleware/tod/control_cities.py`.
- **Windows:** reform year = the case's effective year; before = the 5 years before it; after = the case's after
  window (capped at 2025).
- **Controls:** eligible places = same Census region (Northeast, Midwest, South, West); 2010 homes within ×0.5–2 of the
  reform city's (widened ×1.5 each side, repeatedly, until at least 3 are eligible); not in the reform city's metro
  (CBSA); not in the TOD case inventory; not a reform city; no statewide transit-area density law in force by the last
  after year (as `control_cities.STATE_LAW_YEAR`); full permit reports in every year used. From these, the 10 closest on
  before-years mean rate and linear trend (each ÷ its SD across eligible places), or all if fewer (minimum 3), weighted
  equally (the control-cities plan's method A). The 10 control cities matched on 2026-10-27 are reused where the same
  rules select them; this is not forced.
- **Interval:** fake reforms in each eligible place, its own controls drawn the same way from the other eligible
  places; 90% interval = estimate − the 95th and 5th percentiles of the fake effects.
- **New York and Philadelphia are left out of 1B** (rule, not result): their rezonings span many years (New York
  2003–2013, Philadelphia 2012–2019), so there is no single before and after for the whole city, and New York has no
  US place within ×0.5–2 of its size. They are listed as "not estimable".
- **Pre-trend pass rule (a):** a placebo reform 3 years early (fake year = reform year − 3; before = the 5 years before
  the fake year; after = fake year to reform year − 1, all before the real reform), same control rule and fake-reform
  interval. A place passes if that placebo's 90% interval includes 0. A failing place is reported but left out of the
  pooled figure and of R's median.
- **R (b):** per place, R = citywide net extra homes a year (1B effect × city homes ÷ 1,000) ÷ station-area total extra
  homes a year (1A, ¼ mile only, same years; the T2 matched figure replaces it when T2 is run). Interval from 2,000
  paired draws (one fake-reform effect, one station-area bootstrap draw). R is defined only where the station-area
  ¼-mile extra is above 0 (else "not defined": a ratio over a non-positive gain has no reading).
- **Feeds Wisconsin (downside case):** median R across passing places, capped at 1. If the pooled interval of that
  median (2,000 draws, one draw per place) includes 1, the downside uses its lower end, labelled "not detectable at
  citywide scale". Known limit, stated beside it: the 2026-10-27 control-city study could only detect changes of
  about 4–5% of a city's homes over 5 years.

## Test 2 (T3): edge test, difference in discontinuities at district boundaries (locked 2026-11-02, before any count)

Script: `scripts/run_tod_causal_edge.py`. Output: `reference/tod_causal_edge_test.csv`.

- **Estimand:** the direct effect of rezoning on rezoned lots: building on lots just inside the district vs lots
  just outside, after minus before. **Interpretation lock:** this is the "floor" (direct effect only). Spillover onto
  nearby outside lots makes it understate the direct effect; builders shifting projects across the line make it
  overstate it (checked below). It is compared with the station-area measured effect (the main), never replaces it.
- **Lots:** each case's lots whose nearest stop is a reform stop within 1 mile (learning plan: boundary segments within
  1 mile of a stop). Sensitivity: within ½ mile (the first request). Implausible lots and lots without land acres left out.
- **Signed distance to the district boundary** (+ inside, − outside; inside = the stored `in_reform_area`):
  - *Polygon districts* (Denver, Portland, Austin, Salt Lake City; `station_cases.cluster_west.reform_area`):
    distance from the lot point to the boundary of the **union** of the district polygons. Polygon edges come from
    `geom._segments`; an edge is kept as boundary only if points 0.5 m either side of its midpoint differ in union
    membership (`geom.points_in_any(..., union=True)`), so shared internal edges between adjacent district polygons
    drop out. Kept edges are densified to points ≤ 5 m apart and the nearest is found with a k-d tree (error ≤ 2.5 m).
  - *Lot-defined districts* (New York and Philadelphia treated lots, Chicago's zoning-and-distance rule, and the
    treated lot points of Charlotte, Seattle and Saint Paul): no single polygon defines the district, so the boundary
    is the line midway between lots of different status: distance = half the distance to the nearest lot point of the
    opposite status in the same case table (any group).
  - Sensitivity: the lot-midway distance in the polygon places too.
- **Outcome and estimator (main):** within a bandwidth h of the line, each side's rate = 100 × Σ(after homes/after
  years − before homes/before years) ÷ Σ land acres (ratio of sums, as the station-area model); estimate = inside
  rate − outside rate, extra homes per 100 lot acres a year. Chosen as main over local linear because new homes are
  very lumpy (a few lots carry most homes), so per-lot slopes are unstable. Sensitivity: local linear (each side,
  lot rate on signed distance, weights acres × triangular kernel; difference of intercepts at 0).
- **Bandwidths (learning plan):** main 91 m (300 ft); sensitivities 46 m (150 ft) and 183 m (600 ft).
- **Segments:** the boundary point of each lot (nearest boundary point, or the midpoint to the opposite lot) is put in
  a 400 m grid cell; a cell is a boundary segment. Only segments with lots on **both** sides within h are used (a side
  with no lots is water, rail, a park, a freeway or the study edge). Segments where public land is ≥ 50% of either
  side's acres within h are dropped (parks, rail yards, campuses).
  - **Water:** TIGER 2024 area water (public domain) where on disk (Cook, Mecklenburg, Ramsey, King, New York's five
    counties, Philadelphia): segments whose boundary point is within 30 m of water are tagged and left out. Denver,
    Portland, Austin, Salt Lake City: no water layer on disk, not tagged (noted).
  - **Arterial roads:** no open road layer is on disk, so segments are **not** tagged for arterials in this run
    (downloading TIGER roads needs the owner's OK). Reported as a gap.
    *Update 2026-11-02 (after the first run, coordinator-approved):* TIGER roads fetched and segments tagged; see the
    results section. Main = all segments; "without arterial segments" reported beside it.
- **Places and pooling:** a place's cases are pooled lot by lot (a lot in k of the place's edge samples weighted 1/k).
  A place is estimable at h if it has at least 20 lots on each side. Pooled = equal-weight mean of passing places.
  Interval: 1,000 cluster-bootstrap draws resampling segments within each place (seed 20261103); pooled draws are the
  mean of place draws. Leave-one-place-out range reported.
- **Balance (pass rule a, learning plan):** the inside − outside gap in the **before-window** rate (homes per 100 lot
  acres a year) at h = 91 m; a place passes if its 90% interval includes 0; a failing place is reported but left out of
  the pooled figure. Descriptive balance (reported, not a rule): land value per acre (log), lot size (log acres),
  building age at the reform year, lot vacant (no building value), tract vacancy rate; standardized mean difference
  inside − outside, flagged when |SMD| > 0.25.
- **Shifting checks (pass rule b, coordinator addition):**
  - *Donut:* the main estimate with lots within 25 m of the line dropped.
  - *Bunching:* on the outside only, after-window rate at 0–100 m outside minus the rate 100–200 m outside, minus the
    same difference in the before window (pooled, segment bootstrap). A negative value whose 90% interval excludes 0
    suggests building shifted from just outside to just inside; then the floor uses the donut estimate (labelled).
- **Overall PASS (locked):** the edge test is usable as the floor if (1) at least 5 places are estimable and pass
  balance at 91 m, and (2) the 46 m and 183 m pooled estimates both lie inside the main's 90% interval. If it passes:
- **USE:** "direct effect only" Wisconsin floor = pooled direct effect (or the donut if bunching is flagged)
  × 15% × 4,874.1 ¼-mile lot acres ÷ 100 × 5 years × 1.2269, extra homes 2027–2031, with the pooled interval carried
  through. Shown beside the station-area ¼-mile measured effect per place (`reference/tod_station_area_effects_by_city.csv`)
  and the implied direct share of it: edge estimate × the district's share of the ¼-mile reform band's land acres,
  per 100 band acres a year. If it fails, it is reported as a check only, not shown as a floor.

## Test 3 (T2): line-age matching (locked 2026-11-02 15:40 machine clock, before any count)

Separates the effect of the rezoning from growth caused by new transit. Script: `scripts/run_tod_causal_line_age.py`.
Output: `reference/tod_causal_line_age.csv` (place summaries only).

- **Estimand:** the station-area total effect within ¼ mile (all lots in the ¼-mile band of reform stops, rezoned or
  not), extra new homes per 100 lot acres a year, measured against comparison stops whose station opened in the same
  era, so that new-transit growth is not counted as the law's effect.
- **Places:** D-11 (shared rules). ¼-mile band only (the band the Wisconsin central uses).
- **Opening year per stop:** `opening_year_best` from `reference/tod_stop_table.csv`; where blank (most comparison
  stops), the same Wikidata (CC0) matcher and hand-coded agency facts as `scripts/build_tod_stop_extra_traits.py`
  (functions imported unchanged, run on comparison stations too; nothing in the stop table is rewritten). Where a
  line-level agency fact is added for comparison stops, it is listed with its source in the script. The station's
  opening year stands in for its line's. A stop with no year is "unknown".
- **Match rule M3 (main; learning plan v1 T2):** comparison stop c matches reform stop r (same case) if their
  opening years are within 3 years of each other, **or** both were open 10+ years at the case's reform year.
  **Sensitivity M10** (coordinator's first brief): opening years within ±10 years.
- **Unknown years:** a reform stop with unknown year is compared with all comparison stops of its case (flagged).
  A comparison stop with unknown year is **kept** in every reform stop's matched set (main, as briefed: "keep and
  flag"); variant "known only" drops it.
- **Estimator:** for each stop, Δ = 100 × (Σ after homes / after years − Σ before homes / before years) ÷ Σ land acres
  over its ¼-mile lots (the measured effect's ratio of sums; same dates, hand checks, implausible lots out). Case
  effect = Σ_r acres_r × (Δ_r − Δ_M(r)) ÷ Σ_r acres_r over reform stops r with at least one matched comparison stop
  that has ¼-mile lots, where Δ_M(r) pools the lots of r's matched comparison stops. (With every comparison stop
  matched this reproduces the measured effect exactly; checked in the run.) Reform stops with no match are dropped;
  the share of reform ¼-mile acres kept is reported. New York and Philadelphia = mean over their rezonings with an
  estimate (as measured).
- **Flag "rezoned with new transit":** a reform stop whose station opened after the reform or within 3 years before
  it (reform year − opening year ≤ 3). A place is flagged if over half its reform ¼-mile acres are on such stops
  (expected: Austin, Saint Paul, Seattle Othello; checked from data, not assumed).
- **Intervals (90%):** per place, 1,000 bootstrap draws resampling reform stops and comparison stops separately
  within each case (seed 20261102); pooled = equal-weight mean of places, draws averaged draw by draw; leave-one-place-
  out range of the pooled point.
- **PASS rule (learning plan v1):** the M3 matched version becomes the main T2 estimate if **at least 8 of 11 places
  keep at least 3 distinct matched comparison stops with known opening year** (counted over the place's cases);
  otherwise it is a sensitivity case.
- **Reported:** per place: measured effect (current), M3, M3 known-only, M10; pooled with and without flagged places;
  change in the D-11 average; implied Wisconsin central = pooled × 4,874.1 ¼-mile lot acres ÷ 100 × 5 × 1.2269
  (tool central today: D-11 average).
- **Transit-only check (reported beside, no rule):** (a) the existing Milwaukee Hop placebo
  (`reference/tod_station_checks_milwaukee_placebo.csv`, new streetcar, no rezoning); (b) inside the training cases,
  comparison stops that opened within 3 years before the reform or during the after window ("new-line, no-rezoning")
  minus the case's other comparison stops, ¼ mile, same Δ, pooled over cases that have both.

### T2b: 2×2 of line age × upzoning (owner-approved addition 23:36; locked 2026-11-02 before any count)

Script: `scripts/run_tod_causal_line_age.py --twobytwo`. Output: `reference/tod_causal_line_age_2x2.csv`.

- **Unit:** stops within ¼ mile. Outcome per stop: Δ = before-vs-after change in new homes per 100 lot acres a year
  (ratio of sums over the stop's ¼-mile lots; permit_est dates, hand checks, implausible out, `acres_land`), exactly
  as T2.
- **Line age (per stop, opening years as T2):** **new** = opened from 3 years before the case's reform year through
  the end of its after window; **old** = opened 10+ years before the reform year (or a line code "old"). Anything else
  (4–9 years old, opened after the after window, unknown year) is excluded; counts reported.
- **Upzoning:** **up** = reform stop of the case; **no** = comparison stop.
- **Places, main:** the D-11 cases plus the Milwaukee Hop placebo (pretend reform 2019, after 2020–2024; its lots in
  `checks_milwaukee_placebo_lots.parquet` have no stop ids, so Milwaukee enters as one place in the new/no cell: all
  its ¼-mile lots, Hop and rapid-bus groups, since the Hop opened 2018 and CONNECT 1 2023 are both "new"; that table
  has recorded `acres`, not `acres_land`, flagged). **Sensitivity:** add Honolulu 2017, Bellevue BelRed 2009 and
  Seattle Roosevelt 2012 (candidate table), the new-line-and-upzoned places outside D-11; and D-11 alone.
- **Cell mean:** per case, the acre-pooled Δ of its stops in the cell; per place, mean over its cases with stops in
  the cell (New York, Philadelphia); per cell, mean over the places that contribute (each place equal weight).
- **Effects:** transit alone = new/no − old/no; upzoning alone = old/up − old/no; interaction = new/up − new/no −
  old/up + old/no (differences of pooled cell means, as briefed). Beside them (diagnostic, not the rule): the same
  contrasts computed within place where a place has the needed cells, then averaged.
- **Interval:** 90%, cluster bootstrap by place (resample places with replacement, 2,000 draws, seed 20261102; a draw
  in which a cell is empty is dropped and the count reported).
- **PASS / USE rule (learning plan "T2b", locked as written):** the interaction is **material** if its 90% interval
  excludes zero AND it exceeds 25% of the upzoning-alone effect (in absolute size). If material and positive,
  Wisconsin's law effect near its new lines = upzoning alone + interaction (only transit-alone growth moves to the
  baseline). If not material, the law effect = upzoning alone. Wisconsin figures = effect × 4,874.1 ÷ 100 × 5 × 1.2269.
  T2 and T2b are reported together; the owner picks the T2 central after T2b.
- **Reported:** cell counts (stops, places, cases), cell means with intervals, the three effects with intervals, and
  their Wisconsin readings.

## Test 4 (T4): Los Angeles TOC tier cutoffs, difference in discontinuities (locked 2026-11-02, before any count)

Script: `scripts/run_tod_causal_la_toc_rd.py`. Output: `reference/tod_causal_la_toc_rd.csv` (summaries only).

**The law (verified from the official TOC Guidelines, effective 2017-09-22, revised 2018-02-26, Chart 1, printed p.5;
https://planning.lacity.gov/ordinances/docs/TOC/TOCGuidelines.pdf).** Tier by distance from "any point on the lot"
to the station entrance (rail) or the middle of the bus-route intersection:

| Major transit stop | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
| --- | --- | --- | --- | --- |
| Two regular buses (15-min peak) | 750–2,640 ft | < 750 ft | – | – |
| Regular + Rapid Bus | 1,500–2,640 ft | 750–<1,500 ft | < 750 ft | – |
| Two Rapid Buses | – | 1,500–2,640 ft | < 1,500 ft | – |
| Metrolink station | 1,500–2,640 ft | 750–<1,500 ft | < 750 ft | – |
| Metro Rail station | – | – | ≤ 2,640 ft | < 750 ft if the station meets another rail line or a Rapid Bus |

Density bonus by tier 50 / 60 / 70 / 80% (FAR +40/45/50/55%; parking caps fall to none in Tier 4); minimum affordable
share e.g. 8/9/10/11% extremely low income. So there are **no 750- or 1,500-ft rail cutoffs for Metro Rail except
Tier 4 at 750 ft**, and the lot's tier is the best over all nearby stops (bus included).

- **Estimand:** the jump in the change (after minus before) in new homes per 100 lot acres a year at a tier cutoff,
  i.e. the effect of a one-tier-higher incentive (+10 points of density bonus, plus FAR and parking) for lots at the
  margin. Dose evidence only; no Wisconsin line (LA TOC requires affordable units; Wisconsin's law would not).
- **Lots:** `lots_la_toc_2017.parquet`, City of Los Angeles lots only (`city_name`), implausible out, land acres > 0;
  dates permit_est with hand checks; before 2011–2016, after 2018–2022 (the case's windows). Outcome per lot:
  y = 100 × (after homes ÷ 5 − before homes ÷ 6) ÷ land acres.
- **Treatment map:** the City's TOC tier map of October 2017 (`toc_tiers_oct2017.geojson`, FINALTIER 1–4; already
  used by the lot table). Lot point in polygon → its tier (0 = none).
- **Design A (main: the map's own tier edges, sharp).** For each cutoff k|k−1 (4|3, 3|2, 2|1, 1|none): running
  variable = signed distance (m) from the lot point to the boundary of the union of tier ≥ k polygons (+ inside); lots
  used: tier exactly k inside, tier exactly k−1 outside. Boundary points every ≤ 5 m, shared internal edges removed
  (as T3's `boundary_points`). This handles bus-based tiers by construction.
- **Design B (brief: distance to the nearest rail station).** Running variable = distance from the lot point to the
  nearest Metro Rail station point (stop table, subway and light rail, any city) at 229 m (750 ft) and 805 m (2,640 ft);
  Metrolink stations likewise at 229 / 457 / 805 m (run only if ≥ 200 lots each side within the bandwidth). Reduced
  form; first stage = jump in the map tier's density bonus (0/50/60/70/80%) at the cutoff; fuzzy ratio = reduced form ÷
  first-stage jump, per 10 points of bonus. Station points are platforms, not entrances, and lot points are not the
  nearest lot edge: both blur the cutoff (the reason A is main).
- **Estimator (main):** local linear on each side, weights = land acres × triangular kernel, difference of
  intercepts. Beside it: ratio of sums within the bandwidth (T3's main).
- **Bandwidth (main, data-driven, fixed before running):** Imbens–Kalyanaraman (2012) MSE-optimal rule for a
  triangular kernel, computed per cutoff on y with acre weights: pilot h₁ = 1.84 × SD(x) × N^(−1/5) on lots within
  ±1,000 m; density f̂ and each side's variance σ²± within h₁; third derivative from a global cubic with a jump; second
  derivatives from a local quadratic on each side within h₂± = 3.56 × (σ²±/(f̂ m₃²))^(1/7) × N±^(−1/7); regularisation
  r± = 2160 σ²± / (N± h₂±⁴); h = 3.4375 × [(σ²₊ + σ²₋) / (f̂ ((m₊″ − m₋″)² + r₊ + r₋))]^(1/5) × N^(−1/5), clipped to
  [25 m, 300 m] (fixed now). Beside it: the brief's 46 / 76 / 122 m (150 / 250 / 400 ft; brief's main 76 m).
- **Interval:** 90%, cluster bootstrap resampling 400 m boundary segments (A) or nearest stations (B), 1,000 draws,
  seed 20261104.
- **Balance (same rule as T3):** the same RD on the before-window rate (homes per 100 lot acres a year); a cutoff
  passes if its 90% interval includes 0. Descriptive (flagged if the 90% interval excludes 0): log land value per
  acre, log lot size, existing homes per acre.
- **Donut (same as T3):** drop lots within 25 m of the cutoff; reported beside.
- **PASS rule:** each cutoff's jump is reported with its 90% interval; a cutoff **passes** if balance holds at the main
  bandwidth. **USE:** dose evidence if at least one Design A cutoff passes and its donut estimate has the same sign:
  "a positive passing jump supports the per-unit-of-capacity view". No size is carried to Wisconsin.

## Results: Test 1 (T1) and Test 2 (T3 edge test), run 2026-11-02

Run with the rules above, unchanged. Files: `reference/tod_causal_citywide_11.csv`, `reference/tod_causal_edge_test.csv`.
Scripts: `scripts/run_tod_causal_citywide.py`, `scripts/run_tod_causal_edge.py`. One code bug fixed before reading
results (R first used the 1-mile figure instead of the ¼-mile one; rerun). No rule changed.

### Test 1A: station-area extra homes, scaled to the city (lot tables)

Extra homes per 100 lot acres a year near reform stops (reform-band land); per 1,000 existing city homes over 5 years;
90% intervals from resampling stops.

| Place | ¼ mile: per 100 lot acres a year | ¼ mile: per 1,000 city homes, 5 years | To 1 mile: per 1,000 city homes, 5 years | 1 mile ÷ ¼ mile | District share of city's new homes (after window) |
| --- | --- | --- | --- | --- | --- |
| New York | 19.6 (7.8 to 31.6) | 1.7 (0.7 to 2.8) | 2.7 (0.6 to 5.1) | 1.57 | 8.9% (summed over 23 rezonings) |
| Philadelphia | 14.0 (10.2 to 17.9) | 4.8 (3.5 to 6.1) | 22.2 (18.4 to 26.1) | 4.66 | 26.8% (summed over 83 rezonings) |
| Austin 2009 | 23.8 (−0.2 to 49.1) | 1.5 (0.0 to 3.0) | −8.5 (−12.5 to −4.8) | −5.83 | 2.6% |
| Charlotte 2019 | 16.2 (−0.3 to 33.5) | 5.2 (−0.1 to 10.8) | 23.5 (5.8 to 39.5) | 4.51 | 2.2% (county total; lower bound) |
| Chicago 2015 | 2.4 (−7.5 to 11.6) | 1.5 (−4.8 to 7.4) | 3.9 (−3.8 to 10.7) | 2.52 | 4.6% |
| Denver 2018 | 124.5 (−19.5 to 297.5) | 6.7 (−1.1 to 16.1) | 7.0 (−3.7 to 19.0) | 1.04 | 13.2% |
| Portland 2020 | −25.3 (−50.2 to 29.4) | −14.6 (−29.0 to 16.9) | 31.1 (−37.9 to 159.4) | −2.14 | 12.9% |
| Seattle Mount Baker 2014 | 81.2 (20.8 to 125.4) | 1.8 (0.5 to 2.8) | −1.1 (−3.7 to 1.7) | −0.63 | 0.3% |
| Seattle Othello 2012 | 25.2 (−7.3 to 54.7) | 0.6 (−0.2 to 1.3) | −6.1 (−11.7 to −0.2) | −10.24 | 0.4% |
| Salt Lake City 2010 | 46.6 (−2.4 to 91.6) | 34.9 (−1.8 to 68.8) | 32.4 (−6.7 to 67.8) | 0.93 | 113% (not meaningful: lot data are completions, BPS are permits) |
| Saint Paul 2011 | 17.2 (−0.8 to 38.0) | 5.8 (−0.3 to 12.9) | −1.0 (−9.6 to 9.7) | −0.18 | 20.9% |
| **Pooled (11, equal weight)** | **31.4** (leave one out 22.1 to 37.1) | **4.5** (0.8 to 8.8) | **9.6** (1.5 to 22.1) | | 18.7% |

- Reading rule (locked): pooled to-1-mile figure is positive with an interval above 0: **"consistent"**.
- Carry-through (1 mile ÷ ¼ mile) is below 1 in 6 of 11 places (negative in 5). The ¼-mile gain is partly offset by
  less building ¼–1 mile out in Austin, both Seattle cases, Saint Paul and Portland; it grows farther out in New York,
  Philadelphia, Charlotte and Chicago. No single factor fits all places.
- Flags: Austin and Salt Lake City city homes from 2010 blocks (2000 not on disk); Denver from 2020 blocks.

### Test 1B: whole-city difference-in-differences (Census permit survey)

Net extra homes permitted per 1,000 existing city homes a year vs matched non-reform cities; 90% intervals from fake reforms.

| Place | Per 1,000 homes a year | Placebo 3 years early | Pre-trend pass | 5+ unit series | R = citywide net ÷ station-area ¼-mile gain |
| --- | --- | --- | --- | --- | --- |
| Austin 2009 | 6.2 (0.3 to 20.3) | 2.2 (−4.1 to 7.1) | yes | 6.1 | 21.2 (−447 to 183) |
| Charlotte 2019 | 1.6 (−13.5 to 9.9) | 7.9 (−2.4 to 15.4) | yes | −2.1 | 1.5 (−30 to 22) |
| Chicago 2015 | 1.9 (−0.6 to 3.8) | −2.3 (−6.1 to 0.1) | yes | 1.5 | 6.1 (−15 to 24) |
| Denver 2018 | −5.5 (−9.8 to −1.1) | 12.3 (5.0 to 16.1) | **no** | −1.6 | (left out) |
| Portland 2020 | −13.7 (−16.8 to −11.9) | 3.0 (−2.8 to 7.1) | yes | −12.7 | not defined (¼-mile gain below 0) |
| Seattle Mount Baker 2014 | 14.8 (8.0 to 19.1) | 7.6 (4.1 to 11.3) | **no** | 15.0 | (left out) |
| Seattle Othello 2012 | 16.1 (11.0 to 19.5) | 0.1 (−8.1 to 7.5) | yes | 15.9 | 136 (−398 to 696) |
| Salt Lake City 2010 | 2.2 (−4.4 to 10.8) | 0.6 (−4.4 to 12.3) | yes | 1.0 | 0.3 (−1.5 to 3.8) |
| Saint Paul 2011 | 1.8 (−4.8 to 6.2) | −2.3 (−4.4 to 2.1) | yes | 1.1 | 1.5 (−13 to 14) |
| **Pooled (7 passing)** | **2.3 (−1.0 to 5.7)**, leave one out 0.0 to 5.0 | | | | median **3.8 (−1.4 to 15.5)** |

- New York and Philadelphia: not estimable (rule). Chicago's size band widened to ×0.15–×6.75 (5 Midwest controls).
- **Downside factor, locked rule:** the median-R interval includes 1, so the rule takes its lower end: **−1.38**. That
  value has no sensible reading (it would remove more than the whole gain). The reason is plain: station-area gains are
  37 to 563 homes a year, while whole-city permit swings vs peers are thousands. The whole-city data **cannot detect**
  the station-area gain, let alone the share that moved. Not used; the owner decides what the downside case should be
  (open question, not changed here).

### Test 2 (T3): edge test

Extra new homes per 100 lot acres a year, inside minus outside the district line, after minus before; 91 m (300 ft)
bandwidth; 90% intervals from resampling 400 m boundary segments.

| Place | Edge effect | Lots in / out | Pre-reform gap (balance) | Balance pass | Station-area ¼-mile effect | Edge × district share of ¼-mile land |
| --- | --- | --- | --- | --- | --- | --- |
| New York | 146.1 (84.2 to 222.3) | 7,389 / 21,732 | −27.3 (−41.8 to −12.8) | no | 19.6 | 10.7 |
| Philadelphia | 86.2 (42.2 to 134.6) | 5,382 / 66,109 | 0.2 (−6.3 to 7.3) | yes | 47.5 | 2.1 |
| Austin 2009 | 35.0 (2.8 to 74.9) | 696 / 917 | 1.0 (−5.8 to 7.7) | yes | 23.8 | 15.1 |
| Charlotte 2019 | 16.9 (−4.1 to 37.9) | 1,405 / 6,072 | −29.7 (−41.2 to −19.8) | no | 28.4 | 5.3 |
| Chicago 2015 | 6.6 (−29.8 to 44.5) | 2,365 / 25,423 | 12.1 (−7.1 to 40.0) | yes | 6.7 | 0.3 |
| Denver 2018 | 298.6 (130.2 to 483.1) | 652 / 1,035 | 7.9 (−80.3 to 80.4) | yes | 115.4 | 47.1 |
| Portland 2020 | 8.1 (−0.3 to 16.9) | 12,213 / 22,314 | −12.0 (−19.3 to −5.0) | no | −32.8 | 1.2 |
| Seattle Mount Baker 2014 | 81.5 (−226.7 to 400.8) | 41 / 342 | −30.1 (−46.1 to −6.5) | no | 75.6 | 7.0 |
| Seattle Othello 2012 | 118.2 (−12.1 to 336.8) | 110 / 865 | −66.4 (−173.0 to −8.1) | no | 21.5 | 14.7 |
| Salt Lake City 2010 | 68.9 (5.7 to 139.2) | 532 / 845 | −2.0 (−4.3 to −0.2) | no | 48.1 | 21.1 |
| Saint Paul 2011 | 14.8 (−31.1 to 69.7) | 339 / 1,678 | 15.5 (0.0 to 45.6) | yes | 15.0 | 4.4 |
| **Pooled (5 passing balance)** | **88.2 (50.8 to 129.1)**; leave one out 35.7 to 108.7 | | | | | |
| All 11 (balance ignored; not used) | 80.1 (42.7 to 118.2) | | | | | |

- Sensitivities, pooled 5 places: 46 m 93.3 (51.6 to 139.6); 183 m 82.3 (50.6 to 115.7); donut 25 m 73.4
  (20.2 to 128.7); ½ mile only 91.8 (55.9 to 127.8). Local linear (per place) is close to the main except the small
  Seattle cases. Lot-midway distance in the polygon places: Austin 11.0 vs 35.0 (sensitive), Denver 260 vs 299.
- **Bunching:** pooled −5.5 (−20.1 to 9.1): no sign of building shifted from just outside to just inside. No place's
  interval is below 0.
- **Balance traits (|standardized difference| > 0.25):** inside lots are larger in 7 places (lot size the most common
  imbalance); building age differs in 6, vacant lots in 6, land value per acre in Chicago and Saint Paul (1.24),
  tract vacancy in 3. New York and Portland are balanced on traits but fail the pre-reform building gap.
- **Locked rule: PASS** (5 places pass balance; 46 m and 183 m inside the main interval; no bunching, so the main is used).
- **Direct-effect-only Wisconsin floor** = 88.2 × 15% × 4,874.1 ÷ 100 × 5 × 1.2269 = **3,958 extra homes, 2027–2031
  (2,279 to 5,791; leave one place out 1,600 to 4,873)**. Denver carries much of it.
- Chicago's district is a lot-by-lot zoning mosaic, so nearly all its inside lots sit within 46 m of an outside lot.

**Rerun 2026-11-02 with arterial and water tags** (coordinator-approved fetch of public-domain TIGER/Line files,
`scripts/fetch_tod_causal_roads.py` → `data/raw/tod_causal_roads/` with manifest; added after the first run, no rule
changed). Arterials = TIGER 2020 primary and secondary roads (MTFCC S1100, S1200) of each place's counties; a lot's
boundary point is "on an arterial" if within 20 m of one and within 30° of parallel to the boundary (polygon edge
direction, or perpendicular to the lot-to-opposite-lot line); a segment follows an arterial if at least half its lots
within the bandwidth are. Area water (TIGER 2024) added for Denver, Portland (Multnomah, Washington, Clackamas),
Austin (Travis, Williamson) and Salt Lake City, applied under the locked water rule.
- Water: only Portland changes (6 of 423 segments dropped; 8.1 → 9.0; still fails balance). Other places unchanged.
- Arterial segments are rare: 0–2% of segments per place (Philadelphia 1%, Charlotte 2%, New York 1%, others 0%).
  Only 1–12% of boundary points sit within 20 m of an S1100/S1200 road at all. TIGER codes many city arterials as
  local roads (S1400), so this tag likely under-counts arterial edges.
- **With arterial segments (main): 88.2 (50.8 to 129.1). Without: 87.7 (50.2 to 126.0).** The pass rule result is
  unchanged (PASS), and the Wisconsin direct-effect-only floor stays **3,958 (2,279 to 5,791; leave one place out
  1,600 to 4,873)**; without arterial segments it would be 3,933 (2,253 to 5,653).

## Test 5 (T5): Massachusetts MBTA Communities, feasibility then year-1 direction (locked 2026-11-02, before any count)

Script: `scripts/run_tod_causal_mbta.py`. Outputs: `docs/tod/MBTA_FEASIBILITY.md` (scan and go / no-go) and
`reference/tod_causal_mbta_event.csv` (summaries).

- **Data:** Census Building Permits Survey annual Northeast place files `ne2015a`–`ne2025a` (already on disk,
  `data/raw/tod_control_cities/bps`; public domain); Massachusetts towns are the rows with state 25 (county
  subdivisions, 351 a year). Town homes: ACS 2015–2019 B25001 by county subdivision (`data/raw/parking_acs_history/
  acs5_2019_cousub25.json`). Community list, deadline and status: the state's (EOHLC) compliance status sheet dated
  2025-09-18 (https://www.mass.gov/files/csv/2025-09/Compliance%20Status%20Sheet%20as%20of%209-18-25.csv), saved
  under `data/raw/tod_mbta/`. Its deadline column is the original category deadline, except towns that missed theirs,
  which show 7/14/2025 (the post-*Milton* deadline).
- **Cohorts (intent to treat, by original deadline):** 2023 = rows with 12/31/2023 plus Milton (a rapid-transit
  community; its 2023 zoning was overturned by referendum, listed 7/14/2025); 2024 = rows with 12/31/2024 plus the
  other 7/14/2025 rows (missed a 2024 deadline); 2025 = rows with 12/31/2025 (adjacent small towns).
- **Feasibility PASS (learning plan):** at least 20 towns that are Compliant or Conditionally compliant on the sheet
  and whose original deadline is 12/31/2024 or earlier (so 2025, or 2024 and 2025, are full years after it in BPS).
- **If it passes, year-1 effect only (sign and 90% interval; no size carried to Wisconsin):** outcome = units
  permitted per 1,000 homes (all units; 5+ units as a second series). For cohort g, year 1 = g + 1; base = mean of
  g − 3 … g − 1. ATT(g) = (cohort's year-1 − base) − (not-yet-due towns' year-1 − base); not-yet-due controls: for g =
  2023 (year 2024) the 2024 and 2025 cohorts; for g = 2024 (year 2025) the 2025 cohort. Towns weighted equally;
  pooled = cohort-size-weighted mean of the two ATTs. Interval: 2,000 bootstrap draws resampling towns within each
  group, seed 20261105. **Pre-trend placebo:** the same estimator one year early (pseudo year 1 = g, base g − 4 … g − 2).
- **Variants:** compliant-only treated towns; reported-only BPS columns with towns reporting 0 months dropped;
  homes-weighted.
- **Reading rule:** "positive" if the pooled 90% interval is above 0, "negative" if below, else "no detectable
  year-1 change". Per the learning plan, a zero or negative mandated effect whose interval excludes the D-11
  chosen-district average adds a "mandated district" sensitivity; the per-town BPS measure is not in the same unit as
  the station-area effect, so this comparison is stated in words only.

## Results: Test 3 (T2 line age, T2b 2×2), Test 4 (LA TOC) and Test 5 (Massachusetts), run 2026-11-02

Unit unless stated: extra new homes per 100 lot acres a year within ¼ mile. Wisconsin = effect × 4,874.1 ÷ 100 × 5 ×
1.2269 (extra homes 2027–2031). Intervals 90%.

### T2: line-age matching (`reference/tod_causal_line_age.csv`)

- **Data fix after the first run (coordinator, labelled as a fix, rule unchanged):** Denver Union Station had no
  opening year (the stop table's one "RTD rail (Multiple)" stop; Wikidata did not match it). Filled with its
  earliest rail line, the RTD C Line light rail of April 2002 (RTD news release, URL in the script); A/B/G
  commuter rail (2016) and the bus concourse (2014) came later. No other D-11 comparison stop is unknown. Two
  Portland reform streetcar stops (OHSU Plaza, S Moody & Meade South; 74 acres) have no source found and stay unknown
  (compared with all comparison stops). Before the fix the locked "keep unknown" rule gave Denver 174.5 and the M3
  pooled 36.1 (10,794): one station's missing year moved the pooled by 13 points.
- **PASS:** 10 of 11 places keep ≥ 3 matched comparison stops with known year (Austin has 1 comparison stop):
  **M3 is the main T2 estimate.**

| Place | Measured | M3 (90% interval) | M10 | Share of reform ¼-mile acres "new transit" |
| --- | --- | --- | --- | --- |
| Austin | 23.8 | 23.8 (−0.2 to 51.1) | 23.8 | 100% (flagged) |
| Charlotte | 28.4 | 15.5 (−0.9 to 51.6) | 20.1 | 40% |
| Chicago 2015 | 6.7 | 7.0 (−0.7 to 14.1) | 8.1 | 0% |
| Denver | 115.4 | 32.4 (−120.4 to 263.6) | 102.0 | 52% (flagged) |
| New York | 19.6 | 19.5 (7.4 to 33.4) | 20.3 | 0% |
| Philadelphia | 47.5 | 47.5 (40.4 to 54.2) | 49.8 | 0% |
| Portland 2020 | −32.8 | −43.7 (−66.4 to −22.1) | −24.3 | 0% |
| Saint Paul | 15.0 | 15.0 (−2.3 to 37.7) | 15.0 | 100% (flagged) |
| Salt Lake City | 48.1 | 46.7 (3.5 to 88.5) | 49.6 | ~50% (flagged) |
| Seattle Mount Baker | 75.6 | 66.4 (16.0 to 129.4) | 66.4 | 0% |
| Seattle Othello | 21.5 | 24.8 (−12.9 to 57.0) | 24.8 | 100% (flagged) |

| Pooled (equal places) | Effect (90%) | Leave-one-out | Wisconsin (90%) |
| --- | --- | --- | --- |
| Measured, all 11 (tool central) | 33.5 (18.3 to 50.1) | 25.3 to 40.2 | 10,028 (5,483 to 14,990) |
| **M3, all 11 (main T2)** | **23.2 (9.1 to 47.3)** | 18.9 to 29.9 | **6,932 (2,717 to 14,147)** |
| M3, without the 5 flagged places | 18.7 (9.4 to 32.1) | 9.2 to 31.2 | 5,595 (2,814 to 9,594) |
| M3, flagged places only | 28.5 (−2.3 to 77.3) | | 8,536 |
| M10, all 11 | 32.3 (17.5 to 49.4) | 25.4 to 38.0 | 9,669 |
| Measured, without flagged | 24.2 (12.9 to 36.7) | | 7,225 |

The move from 33.5 to 23.2 is almost all Denver (115.4 → 32.4: its 38th & Blake stop, A Line 2016, +444, is now
compared with other new A/G Line stops, not with old downtown stops) and Charlotte (28.4 → 15.5). Transit-only
checks: Milwaukee Hop placebo +18.2 (after 2020–2024) / +10.1 (2019–2023); inside the training cases, new-line
comparison stops minus old ones +26.5 (6 places; −29.5 to +165.3, Denver largest).

### T2b: 2×2 (`reference/tod_causal_line_age_2x2.csv`; main = D-11 + Milwaukee Hop placebo; DUS fix in)

| Cell | Mean (90%) | Places | Stops |
| --- | --- | --- | --- |
| New line, no rezoning | 12.5 (−5.4 to 32.9) | 9 | 35 (+ Milwaukee lots) |
| Old line, no rezoning | −5.3 (−21.0 to 8.4) | 9 | 10,334 (NY/PHL repeat across rezonings) |
| Old line, rezoned | 1.8 (−15.0 to 20.6) | 7 | 759 |
| New line, rezoned | 57.5 (27.7 to 94.2) | 7 | 38 |

| Effect | Value (90%) | Wisconsin (90%) | Within-place version |
| --- | --- | --- | --- |
| Transit alone | 17.8 (−9.1 to 50.0) | 5,315 | 26.7 (6 places) |
| Rezoning alone (old lines) | 7.1 (−11.6 to 25.5) | 2,129 | 14.1 (7 places) |
| Interaction | 37.9 (15.7 to 57.8) | 11,322 | 33.8 (4 places) |

- **Rule: interaction MATERIAL** (interval excludes 0; 37.9 > 25% of 7.1). Law effect near new lines = rezoning
  alone + interaction = new/rezoned − new/no = **45.0 → Wisconsin 13,451**; transit alone (17.8) goes to the
  baseline. D-11 without Milwaukee: 44.0 → 13,142 (material). Leave-one-place-out of the interaction (before the
  DUS fix): 33.1 to 49.4.
- Sensitivity adding Honolulu, BelRed, Roosevelt: not material (20.9, −24.3 to 54.5), but their rezoned stations
  opened after the after windows, so they add only comparison stops to the old/no cell (BelRed −215.5).
- 176 stops excluded (4–9 years old, opened after the after window, or unknown); Portland's 22 rezoned stops of
  2012–2015 are among them.
- Caveat: the new/rezoned cell is 38 stops in 7 places, and the cities chose to rezone around those new stations
  (selection); old lines rezoned show almost no gain.

### T4: LA TOC tier cutoffs (`reference/tod_causal_la_toc_rd.csv`)

284,915 City of LA lots in the lot table (tier 0: 102,238; 1: 59,069; 2: 26,145; 3: 88,271; 4: 9,192). Jump =
inside − outside in the change (after − before) of new homes per 100 lot acres a year; IK bandwidth main.

| Cutoff (design A: map edge) | IK bandwidth | Jump (90%) | Donut 25 m | Balance: before-rate gap (90%) | Pass |
| --- | --- | --- | --- | --- | --- |
| Tier 4 \| 3 | 155 m | +5.3 (−62.0 to 78.1) | −50.9 | −62.2 (−123.8 to −10.4) | no |
| Tier 3 \| 2 | 167 m | −11.8 (−34.0 to 9.8) | −34.4 | −5.4 (−21.7 to 8.1) | **yes** |
| Tier 2 \| 1 | 93 m | −33.1 (−60.0 to −8.9) | −34.1 | +14.6 (1.0 to 35.6) | no |
| Tier 1 \| none | 126 m | +1.5 (−6.2 to 10.2) | −11.5 | −2.7 (−5.7 to −0.2) | no |

Design B (distance to rail station points): Metro Rail 750 ft +38.8 (−27.5 to 107.8; first stage only 1.5 bonus
points, so no usable fuzzy ratio); Metro Rail 2,640 ft +9.0 (−5.4 to 24.2), balance passes, first stage 10.5 bonus
points, fuzzy 8.6 per 10 points (−4.9 to 24.6); Metrolink cutoffs near 0 (10 stations). Brief's fixed 76 m: tier 3|2
+10.3 (−24.6 to 44.8), tier 4|3 +41.0 (−78.8 to 171.4); signs flip across bandwidths at every map edge.

- **Rule:** 1 of 4 map-edge cutoffs passes balance with a same-sign donut (tier 3|2), so it is usable as dose
  evidence — and it shows **no positive jump** (−11.8, interval spans 0). The tier 2|1 jump is negative but fails
  balance. Reading: at the margin, one more TOC tier (+10 points of density bonus with more affordable units
  required) did not raise building in 2018–2022. This does not support the "per unit of added capacity" view; it is
  consistent with LA TOC's measured station-area effect near zero (−13.3, broad-places check). Lot points (not lot
  edges) and platform points (not entrances) blur the cutoffs.

### T5: Massachusetts (`docs/tod/MBTA_FEASIBILITY.md`, `reference/tod_causal_mbta_event.csv`)

- **Feasibility PASS:** 104 towns compliant or conditional with original deadline ≤ 12/31/2024 (needed 20); all 177
  matched to BPS county subdivisions; BPS annual files exist 2015–2025.
- **Year 1 (units permitted per 1,000 homes):** pooled −2.6 (−5.1 to −0.4), "negative" by the rule; but the one-year-
  early placebo is −1.5 (−4.0 to +1.0) and −2.2 (−4.6 to −0.2) for 5+ units, so the gap predates the deadlines
  (comparison = rural adjacent small towns). Reading: no sign of a first-year rise. No number carried to Wisconsin.

## Test 2 expansion: more upzoning maps, census-block version, placebos (locked 2026-11-02, machine clock 16:05, before any count)

Owner requests (owner clock 2026-11-02 23:55: "run the edge test on a larger number of upzone maps"; 23:59: add
stops without rezonings as a placebo). Script: `scripts/run_tod_causal_edge_expand.py`. Output:
`reference/tod_causal_edge_expand.csv` (summaries only; no lot rows, block ids or parcel ids). Everything in Test 2
above holds unless changed here: 91 m main bandwidth, 46 m and 183 m sensitivities; 400 m boundary segments with lots
on both sides; public ≥ 50% and water (30 m) segments dropped; arterial tag reported beside; 25 m donut; bunching;
balance = before-window inside − outside gap, pass if its 90% interval includes 0; 20 lots a side to be estimable;
1,000 segment-bootstrap draws; pooled = equal-weight mean of balance-passing units, pooled draws = mean of unit
draws; leave-one-unit-out range. The original 11-place run (`reference/tod_causal_edge_test.csv`) is re-computed
inside the script with the same seeds as a check and not changed.

**E1. Six more places (lot tables, rules exactly as Test 2):**
- Broad upzonings: Bellevue BelRed 2009, Honolulu 2017, Los Angeles TOC 2017, San Diego 2021, Chicago 2022.
  District: Seattle Roosevelt 2012 (`candidates/lots_seattle_roosevelt_2012.parquet`).
- Signed distance follows each builder's reform-area geometry:
  - Polygon union boundary (as Denver etc.): Honolulu (Waipahu TC and West Loch zone-change polygons), LA TOC (the
    four Oct 2017 tier polygons), San Diego (SANDAG 2022 transit priority areas).
  - Chicago 2022 (inside = reform-group lot within 805 m of its Chicago CTA/Metra station): signed distance =
    805 m − distance to the nearest station (exact distance to the union of the ½-mile circles); boundary point on
    the circle in the station-to-lot direction (stations re-read with `station_cases.chicago.stations()`).
  - Lot midway (as the lot-defined districts): Bellevue BelRed and Seattle Roosevelt (their stored inside flag is
    "within 30 m of a treated parcel point"). Roosevelt sensitivity: distance to the union of the ordinance's upzoned
    polygons (`cluster_north.roosevelt_polys`).
  - Lot-midway sensitivity also run in the polygon places, as before.
- Water and arterial layers only where already on disk (no new downloads): water for LA (06037), King (53033) and
  Cook (17031); arterials for King and Cook. Honolulu and San Diego: no water layer; LA, Honolulu, San Diego: no
  road file. Noted as gaps.

**E2. New York and Philadelphia per rezoning:** every rezoning lot table on disk is its own unit (on disk: 23 New
York, 83 Philadelphia; the 22 and 64 in the owner's message are the older station-area-plan counts; rezonings with
no inside lots or under 20 lots a side are reported as not estimable). Each uses its own table, inside flag and own
before/after windows (a lot shared by several rezonings appears once per rezoning, weight 1 in each). Lot-midway
distance as before. Reported: count of estimable units and count passing balance per city. **City pool (main):**
equal-weight mean of a city's balance-passing rezonings (draws = mean of their draws); the city then enters the
overall pool once. **Version B:** each passing rezoning a separate unit.

**E3. Census-block version (the 21 census-set reforms of CENSUS_CASES_RESULTS section 6, areas exactly as
`run_tod_census2000.census_set_areas`):**
- Blocks as points (internal points; 2000 SF1 headers, 2010 and 2020 TIGER, cached in
  `data/processed/tod_census_cases`), homes and block land area. Each vintage's blocks are placed by their own point.
- **Inside** = block point inside the reform's upzoned land. Polygon reforms (Jersey City, Milpitas, Phoenix,
  Bellevue, Austin, Tysons, Salt Lake City, Seattle Roosevelt): the polygons, signed distance = distance from the
  block point to the union boundary (as Test 2's polygon places). Lot-defined reforms (Saint Paul, Seattle Othello,
  Seattle Mount Baker, LA Warner Center, LA Cornfield Arroyo Seco, Chicago 2013–2015, Philadelphia 2012, the New
  York rezonings 2008–2013): the **upzoned** lots' union (the upzoning boundary; the census set's "treated" lots are a
  subset), signed distance = half the distance to the nearest block point of the other status in the same vintage
  (the block-midway rule, mirroring lot midway). Outside blocks inside the reform's excluded area (the census set's
  `ex`, e.g. BelRed's other BR zones) or another boundary reform's area are dropped.
- **Outcome:** within bandwidth h, each side's rate = (homes 2020 − homes 2010) ÷ mean block acres (2010 and 2020
  vintages), net homes per acre per decade; estimate = inside − outside. Reported also as net homes per 100 block
  acres a year (× 10). **Bandwidth main 150 m; sensitivities 100 m and 300 m.** No donut (block points too coarse).
- **Segments:** 400 m cells of each block's boundary point; a segment is used if it has blocks on both sides in both
  vintages of the decade measured. No public or water rule (no block-level flags; census land excludes water).
  Estimable: at least 10 blocks a side in each vintage used. 1,000 segment-bootstrap draws (seed 20261106).
- **Balance:** the same estimator on 2000 → 2010; pass if its 90% interval includes 0. Flag (not a rule) where the
  2000–2010 decade is partly after adoption (adopted before 2010). Change-in-change (2010–20 gap − 2000–10 gap)
  reported beside. Bunching: outside blocks 0–150 m vs 150–300 m, 2010–20 rate gap minus 2000–10 rate gap.
- **Pooling:** each reform one unit (census-set convention), equal weight, balance-passing only; version with New
  York's rezonings pooled to one city unit first. "Usable boundary" = estimable at 150 m.

**Groups and Wisconsin floors.** District-type = the 11 D-11 places (New York and Philadelphia by the E2 city pool)
+ Seattle Roosevelt; broad = the five E1 broad places; census-block = E3. Each group: per unit, pooled, leave one out,
count passing balance; group pass rule as Test 2 (≥ 5 passing units; both sensitivity bandwidths' pooled estimates
inside the main's 90% interval). Floor = pooled × 15% × 4,874.1 ÷ 100 × 5 × 1.2269 (donut if pooled bunching is
flagged), with interval and leave-one-out carried through:
- (a) the original 5 places (re-computed; should be 88.2 → 3,958);
- (b) all passing district-type units (E2 city pools), and version B (rezonings separate);
- (c) everything passing: (b) + passing broad places + passing census-block reforms (New York census rezonings pooled
  to one unit). Census rates are per 100 **block** acres (gross land with streets) and net of losses; converted to
  per 100 lot acres by ÷ 0.75 (the station-area plan's streets factor), labelled. (c) also shown lot-based only.

**P1. Placebo: fake districts moved onto comparison stops (D-11 places).**
- Each case's stop locations are recovered from its lot table (least squares on each stop's lots' x, y and distance).
- Each comparison stop c gets one reform stop r's real map (random draw among the case's reform stops that have
  inside lots, seed 20261107 + place index; r's used in turn before repeating). r's reform-group lots, with their
  real inside/outside status, are translated by (c − r) (same size and orientation). Each comparison-group lot whose
  nearest stop is c takes the status of the nearest translated lot within 100 m (else left out).
- Avoiding real reform areas: comparison lots within 200 m of any real inside lot of the case, or flagged inside,
  are left out.
- Then the identical test on the comparison lots (lot-midway distance on the fake status; same windows, bandwidths,
  segments, water, balance, bunching; places pooled lot by lot with 1/k weights as Test 2).
- **Pass:** pooled (balance-passing places, as Test 2) 90% interval includes 0; all-estimable pool beside.

**P2. Placebo: zoning lines that did not change, near comparison stops.**
- Places with zoning for both ends of the window on disk: Saint Paul (Nov 2010 and Nov 2017 layers; same zone at
  both), Seattle Othello and Mount Baker (current layer; no ordinance dated inside the case's before-start..after-end
  in ZONINGHISTORY), Charlotte (pre-UDO layer; last rezone date before the before window, no approved petition in
  the window; the June 2023 UDO translation falls in the after window, flagged), Portland (May 2018 and Mar 2020
  layers; same zone; **reported, not pooled**: the 2021 Residential Infill Project changed every single-dwelling lot
  during the after window). New York, Philadelphia (2012 code change), Denver, Austin, Salt Lake City, Chicago
  (comparison stops are suburbs without a zoning layer): not possible, said so.
- Lots: comparison-group lots, zone unchanged; "inside" = higher tier (multifamily, commercial, mixed use: Saint
  Paul RT2, RM, TN, B, BC, OS; Seattle Lowrise, Midrise/High-Density Multi-Family, Neighborhood Commercial,
  Commercial, Seattle Mixed, Downtown; Charlotte R-xMF, UR, MUDD, UMUD, B, O, NS, CC, TOD, MX; Portland R1–R3, RH,
  RX, C*, EX), "outside" = single-family / two-family tier (Saint Paul R1–R4, RL, RT1; Seattle Neighborhood
  Residential; Charlotte R-3 to R-8, RE; Portland R2.5–R20, RF); industrial, institutional, open space, PD/PUD and
  others left out. Lot-midway distance between the tiers; the identical test.
- **Pass:** pooled over all estimable pooled places 90% interval includes 0 (a zoning line differs in level by
  construction, so the before-gap balance is reported, not used to drop places); balance-passing pool beside.
- **Net reading:** if a placebo pool's interval excludes 0, the real pooled edge effect is also reported as "edge
  effect minus placebo" (draw by draw), and its Wisconsin floor beside the main.

**Addition (coordinator, same session, still before any count): two pre-period checks per unit; the primary filter
is pending the owner.**
- **(a) Level balance (the locked Test 2 rule):** before-window inside − outside gap; pass if its 90% interval
  includes 0.
- **(b) Pre-trend:** the before window split into two equal halves (first ⌊n/2⌋ years and last ⌊n/2⌋ years; the
  middle year dropped when n is odd), new homes per 100 lot acres a year in the second half minus the first, inside
  minus outside; same segments and bootstrap; pass if its 90% interval includes 0. Halves come from the per-building
  event files with the same date rule (`permit_est`); a hand-check-corrected lot's halves are scaled by its corrected
  ÷ uncorrected before-window total (duplicates 0). Units with a one-year before window (Saint Paul 2011: 2010 only)
  cannot be tested and are left out under (b). Census blocks have only 2000/2010/2020 counts, so (b) cannot be run
  for E3; census units enter the (b) pools not at all (they appear under (a) and no filter).
- **Every pool, city pool, group rule and Wisconsin floor is reported three ways:** filtered by (a), by (b), and with
  no filter (all estimable units). Placebo pools likewise.

## Owner decision, 2026-11-03 00:17 (Ryan: "sure", to "lock in 3,958 / 10,028 / 13,451")
- Lower = T3 edge-test direct-effect floor (3,958 on the 5 balance-passing places; to be refreshed by the Test 2 expansion
  before the tool is rebuilt).
- Central = D-11 plain average (10,028), kept by the owner ("you can keep d-11").
- Upper = T2b near-new-lines reading: rezoning alone + interaction, 45.0 extra homes per 100 lot acres a year, 13,451.
  This departs from the locked T2/T2b rule (which made 13,451 the central); the owner chose it as the upper because the
  2×2's new-line rezoned cell comes from cities that chose to rezone around new stations, while Wisconsin's law sets
  districts by rule.
- Transit-alone growth (≈ +17.8, ≈ 5,300 homes) belongs in the baseline, not the law; to check that the Wisconsin
  near-stop baseline covers growth near the new BRT and Hop stops.

## Results: Test 2 expansion (E1–E3, P1–P2), run 2026-11-02

Run with the expansion rules above, unchanged. File: `reference/tod_causal_edge_expand.csv` (1,173 summary rows; no
lot, block or parcel ids). Script: `scripts/run_tod_causal_edge_expand.py`. Fixes before reading results: the P2
Seattle history parser crashed on empty history cells (fixed, rerun); census pools no longer print a "donut" row (no
donut for blocks). No rule changed.

Unit: extra new homes per 100 lot acres a year, inside minus outside the line, after minus before (census: net homes
per 100 block acres a year, 2010→2020). 90% intervals. Wisconsin factor = 15% × 4,874.1 ÷ 100 × 5 × 1.2269 = 44.9.

**Check: the original run reproduces exactly** — 11 places, 5 pass balance, pooled 88.2 (50.8 to 129.1), floor
3,958 (2,279 to 5,791; leave one out 1,600 to 4,873).

### E1: six more places

| Place | Group | Edge effect (91 m) | Lots in / out | Segments | Balance (a) | Pre-trend (b) |
| --- | --- | --- | --- | --- | --- | --- |
| Bellevue BelRed 2009 | broad | 0.1 (0.0 to 0.2) | 119 / 115 | 12 | pass | pass |
| Honolulu 2017 | broad | 0.4 (−0.6 to 1.3) | 296 / 703 | 23 | **fail** | pass |
| Los Angeles TOC 2017 | broad | 2.4 (−9.5 to 12.1) | 15,784 / 14,721 | 547 | pass | pass |
| San Diego 2021 | broad | −4.7 (−14.1 to 1.5) | 5,283 / 3,791 | 207 | pass | pass |
| Chicago 2022 | broad | −0.2 (−1.7 to 1.3) | 31,635 / 29,958 | 702 | pass | pass |
| Seattle Roosevelt 2012 | district | **2,073 (1,805 to 3,077)** | 72 / 317 | **4** | pass | pass |

- **Broad upzonings show no edge jump:** pooled (4 passing) −0.6 (−4.1 to 2.5), leave one out −1.6 to 0.8; 46 m and
  183 m agree. Fewer than 5 units, so the group rule fails on count.
- **Roosevelt is extreme and fragile:** a few large projects on 8.9 inside acres; only 4 boundary segments; 46 m
  gives 399 (0 to 2,710), polygon distance 1,355. It dominates any pool it enters.
- Gaps: no water layer for Honolulu or San Diego; no road file for LA, Honolulu, San Diego (no downloads made).

### E2: New York and Philadelphia per rezoning

| City | Rezoning tables on disk | Estimable (≥ 20 lots a side) | Pass (a) | Pass (b) | Pass both | City pool (a) | City pool (b) | City pool, no filter |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| New York | 23 | 19 | 10 | 16 | 10 | 263.4 (160.0 to 382.1) | 214.4 (130.2 to 305.1) | 250.0 (147.7 to 340.8) |
| Philadelphia | 83 (64 with inside lots) | 42 | 30 | 28 | 24 | 144.9 (24.4 to 214.9) | 148.0 (49.0 to 221.6) | 151.7 (58.5 to 192.3) |

- New York at place level failed balance (inside building already higher before); per rezoning, 10 of 19 pass and
  their pool is larger than the place-level 146. Per-rezoning estimates vary widely (New York −44 to 1,052;
  Philadelphia −415 to 1,622; medians 147 and 9).
- The pre-trend test (b) passes more units than (a). Many small rezonings have no before-window building on either
  side, so their (b) interval is 0 to 0 and passes trivially: (b) is weak here.

### E3: census-block version (150 m)

Usable boundaries (≥ 10 blocks a side in usable segments): **14 of the 21 reforms** (plus New York 2013, no blocks).
Not usable: Milpitas, Phoenix (14 acres), Bellevue BelRed, Seattle Mount Baker, New York 090365ZMX, 090272ZMK,
090104ZMQ (too few blocks on one side).

| Reform | Edge, net homes per 100 block acres a year | Blocks in / out | Balance 2000→10 gap | Pass (a) |
| --- | --- | --- | --- | --- |
| Jersey City 2010 | 2.5 (−41.0 to 40.6) | 40 / 52 | 8.0 (−142.5 to 170.3) | yes |
| Austin station plans | 55.3 (12.3 to 98.6) | 57 / 54 | 0.5 (−6.1 to 6.8) | yes |
| Tysons 2010 | 9.5 (−55.2 to 54.6) | 20 / 22 | 27.3 (−1.2 to 56.1) | yes |
| Salt Lake City 2010 | 3.7 (−34.6 to 52.3) | 28 / 29 | −5.0 (−34.3 to 14.6) | yes |
| Saint Paul 2011 | −4.7 (−23.9 to 11.8) | 41 / 132 | 10.3 (−4.6 to 29.3) | yes |
| Seattle Othello 2012 | 126.5 (−18.7 to 253.3) | 13 / 65 | −39.6 (−118.2 to 31.5) | yes |
| LA Warner Center 2013 | −37.5 (−68.9 to −6.5) | 31 / 51 | −7.6 (−71.5 to 55.6) | yes |
| LA Cornfield Arroyo Seco 2013 | −4.3 (−32.4 to 33.9) | 43 / 109 | 17.8 (−7.1 to 50.6) | yes |
| Chicago 2013–2015 | 8.9 (−11.4 to 31.6) | 222 / 1,618 | 11.2 (−39.1 to 58.9) | yes |
| Philadelphia 2012 | 18.7 (10.5 to 27.4) | 482 / 3,049 | 22.0 (3.8 to 39.6) | **no** |
| New York 080099AZMM | 5.0 (−85.5 to 128.1) | 14 / 76 | −17.2 (−108.6 to 63.0) | yes |
| New York 090303ZMX | 50.7 (−8.9 to 114.9) | 22 / 70 | −9.5 (−112.2 to 87.5) | yes |
| New York 100407ZMX | 104.4 (40.2 to 186.0) | 35 / 158 | 10.7 (−59.7 to 90.5) | yes |
| Seattle Roosevelt 2012 | 275.7 (138.9 to 538.2) | 19 / 45 | −12.0 (−62.5 to 19.9) | yes |

- **Pooled (13 passing, each reform one unit): 45.8 (24.5 to 70.9)**, leave one out 26.6 to 52.7; 100 m 34.0,
  300 m 45.8 (both inside): group rule **PASS**. New York pooled first: 44.4 (21.9 to 69.5). No filter: 43.9.
- In lot-acre terms (÷ 0.75) about 61 — below the lot-based district pools, and net of demolitions.
- Few segments in several reforms (4–9), so single-reform intervals are rough. Pre-trend (b) cannot be run on census
  counts.

### Pooled groups and Wisconsin floors

Floor = extra homes 2027–2031, direct effect only (90% interval; leave one unit out). No pool's bunching check is
flagged, so every floor uses the main estimate. Rule = ≥ 5 units and 46 m / 183 m pooled inside the main interval.

| Pool | Filter (a) level balance | Filter (b) pre-trend | No filter |
| --- | --- | --- | --- |
| (a) original places | 88.2 → **3,958** (2,279 to 5,791; LOO 1,600 to 4,873); 5 places; rule PASS | 86.7 → 3,889 (1,989 to 5,753; LOO 2,833 to 4,288); 10; PASS | 80.2 → 3,595 (1,909 to 5,302; LOO 2,616 to 3,925); 11; PASS |
| (b) district-type, NY/PHL city pools | 405.2 → 18,174 (15,611 to 24,841; LOO 5,706 to 21,154); 7; **FAIL** | 279.1 → 12,519 (10,320 to 17,081; LOO 4,472 to 13,741); 11; FAIL | 260.4 → 11,678 (9,561 to 15,820; LOO 4,286 to 12,712); 12; FAIL |
| (b2) district-type, rezonings separate | 209.1 → 9,378 (5,780 to 11,927; LOO 7,478 to 10,014); 45; PASS | 194.0 → 8,701 (6,053 to 11,034; LOO 7,080 to 9,226); 53; PASS | 195.0 → 8,746 (6,005 to 10,432; LOO 7,542 to 9,136); 71; PASS |
| (c) everything passing (census ÷ 0.75) | 158.4 → 7,107 (6,088 to 9,491; LOO 3,017 to 7,552); 22; FAIL | 191.8 → 8,601 (7,092 to 11,742; LOO 2,976 to 9,188); 16 (no census); FAIL | 131.0 → 5,876 (4,862 to 7,714; LOO 2,765 to 6,166); 29; FAIL |
| (c2) everything passing, lot-based only | 257.7 → 11,556 (9,927 to 15,798; LOO 3,413 to 12,732); 11; FAIL | same as (c) | 183.7 → 8,238 (6,720 to 11,168; LOO 2,941 to 8,766); 17; FAIL |

- **Every pool containing Seattle Roosevelt fails the bandwidth rule**, and its leave-one-out low is the pool without
  Roosevelt (e.g. (b) under (a): 127.2 per 100 acres → 5,706). Roosevelt rests on 4 segments; the pooled interval
  (mean of unit draws) is skewed by its draws and can sit off-centre. Read the (b) and (c) figures as unstable.
- (b2) passes because 40+ rezonings dilute Roosevelt; it weights New York and Philadelphia by their number of
  rezonings, not once each.
- Broad upzonings pull (c) down; the census set (~61 in lot terms) sits between broad (≈ 0) and district (100–250).

### Placebos

| Place | P1: fake district on comparison stops | P2: unchanged zoning line |
| --- | --- | --- |
| New York | −1.0 (−3.9 to 2.1) | not possible (no zoning layer) |
| Philadelphia | 2.3 (−4.5 to 10.2) | not possible (2012 code change) |
| Austin 2009 | too few lots | not possible |
| Charlotte 2019 | 3.8 (−14.9 to 20.4) | −16.5 (−35.4 to −0.4); fails balance (a) and (b) |
| Chicago 2015 | 6.9 (−13.4 to 36.8) | not possible (suburban comparison stops) |
| Denver 2018 | −61.6 (−138.7 to 11.1) | not possible |
| Portland 2020 | 0.0 (34 / 107 lots; degenerate) | no usable line (the two tiers sit > 1 km apart in comparison lots); not pooled anyway |
| Seattle Mount Baker 2014 | 92.4 (−21.5 to 203.5); fails (b) | too few lots (most lines changed in 2008–2019) |
| Seattle Othello 2012 | −13.5 (−212.0 to 192.8) | 4.4 (−13.2 to 27.4) |
| Salt Lake City 2010 | 14.2 (−16.6 to 59.5); fails (a) | not possible |
| Saint Paul 2011 | 0.0 (4 segments; degenerate) | −2.8 (−9.1 to 7.4) |

- **P1 pooled: 3.3 (−23.8 to 31.1) under (a), 9 places; −6.1 (−32.5 to 21.9) under (b); 4.3 (−19.7 to 29.6) with
  no filter. PASS** (includes 0) under all three.
- **P2 pooled (Portland left out): 0.8 (−8.8 to 14.3) under (a), 2 places; 4.4 under (b), 1 place; −4.9 (−13.5 to
  6.0) with no filter, 3 places. PASS**, but only 1–3 places.
- No placebo shows a sizeable gap, so no net-of-placebo correction is needed. The CSV still lists "edge effect minus
  placebo" for every floor: (a) original 3,812 (minus P1) and 3,921 (minus P2) vs 3,958.
- The P1 interval half-width (≈ 27) is a third of the original pooled effect (88), so the test could see a gap of
  that size, but not a small one.

## Test 2b-L: binding lines inside broad upzonings (locked 2026-11-02, machine clock 16:52, before any count)

Owner request (owner clock 2026-11-03 00:49; "sounds good" 00:50): broad maps may be bigger than demand, so their
edge sits on land nobody wanted to build on and shows ≈ 0. Find the line inside each broad map where demand runs
out, and test whether an edge drawn there shows a jump like the district places (pooled 88.2 per 100 lot acres a
year, 90% interval as in the Test 2 floor). Script: `scripts/run_tod_causal_binding_line.py`; output
`reference/tod_causal_binding_line.csv` (summaries only). Everything in Test 2 / E1 holds unless changed here.

- **Places:** Los Angeles TOC 2017, San Diego 2021, Chicago 2022, Bellevue BelRed 2009 (main pool). Honolulu 2017
  reported beside, not pooled. Lot samples exactly as E1.
- **Demand score (pre-reform traits only; never anything from the after window):**
  - Main: distance to the nearest stop (a line a law could actually draw).
  - Sensitivity S1: before-window new homes per 100 lot acres a year in the lot's 400 m neighbourhood (inside-map
    lots, the lot itself left out).
  - Sensitivity S2: land value per lot acre before the reform, where the lot table has it; else not run.
- **Candidate lines:** the score's cut points that put 10%, 20%, ..., 90% of the map's inside lot acres on the
  high-demand side (9 candidates per place).
- **Split (cross-fit):** stops are split into two halves at random (seed 20261103; lots go with their nearest
  stop). In half A, for each candidate, compute the line jump = (after − before rate, high-demand side) minus
  (after − before rate, low-demand side), lots within 91 m of the candidate line, both sides inside the map. The
  binding line for half B is the candidate with the largest half-A jump. Then the reverse. No line is chosen with
  the half it is tested on.
- **Test at the chosen line:** the Test 2 edge estimate (91 m; balance (a); 25 m donut; bunching; 1,000
  stop-cluster bootstrap draws), run in the held-out half; the place estimate = mean of the two halves.
- **Pooled:** equal-weight mean of balance-passing places; leave-one-place-out range.
- **Reading (fixed now):**
  - "Supports the idea" if the pooled 90% interval excludes 0 and overlaps the district pool's 90% interval.
  - "Jump, but smaller" if it excludes 0 and sits wholly below the district interval.
  - "No binding line found" if it includes 0.
  - Also reported: the chosen line's share of map acres and its distance to the stop, per place and half (if the
    two halves pick very different lines, say so).
- **Use:** evidence only. Nothing in the tool changes without the owner's OK. If it supports the idea, the possible
  use (owner's call) is adding the four places to the floor pool at their binding lines.
- **Selection-bias check:** run the same procedure with the after window replaced by a second before window
  (placebo years); the pooled jump should include 0.

## Results: Test 2b-L (binding lines inside broad upzonings), run 2026-11-02

Run with the Test 2b-L rules above. File: `reference/tod_causal_binding_line.csv` (91 summary rows; no lot rows,
parcel ids or stop ids). Script: `scripts/run_tod_causal_binding_line.py`; cross-fit unit test:
`tests/test_tod_causal_binding_line.py`.

Unit: extra new homes per 100 lot acres a year, high-demand side minus low-demand side of the line (both inside the
map), after window minus before window, lots within 91 m. 90% intervals from 1,000 stop-cluster bootstrap draws.
Wisconsin factor = 44.9 (as the Test 2 floor: 88.2 → 3,958). District pool to compare with: 88.2 (50.8 to 129.1).

**Deviations (labelled; nearest thing to the locked rule):**
- **S2 ran for Chicago 2022 only.** Only its lot table holds a pre-reform land value (Cook 2016 certified values).
  Los Angeles, San Diego, Bellevue and Honolulu tables hold the current roll (after the reform), so S2 was not run there.
- **S1 neighbourhood is counted on a 20 m grid.** Distances are accurate to about 15 m, so a full lot-pair count was not needed.
- **Placebo-years S1 uses only the first half of the before window.** The full before window would contain the
  placebo "after" years.
- **Place balance = mean of the two halves' before-window gaps** (draw by draw). The plan did not say how to combine halves.
  Stricter version (both halves must pass) noted below.
- **One half only, or none:** Honolulu's half A and both Bellevue halves had too few lots (each half has 1 stop).
- **Arterial tag not run** (it was a beside item in E1).
- **Line distance for S1 and S2:** a score line is not a circle. Its "distance to stop" = the acre-weighted mean
  distance of lots within 91 m of it.

### Per place, main score (distance to the nearest stop)

| Place | Half tested (line chosen on) | Effect, extra homes per 100 lot acres a year (90%) | Balance (before-window gap) | Line: share of map acres on high side | Line: metres from stop | Lots high / low side |
| --- | --- | --- | --- | --- | --- | --- |
| Los Angeles TOC 2017 | A (B) | 14.6 (1.3 to 31.1) | pass | 30% | 574 | 7,118 / 8,148 |
| | B (A) | 13.0 (−5.2 to 40.9) | **fail** | 80% | 1,227 | 4,294 / 4,502 |
| | place | **13.8 (1.6 to 29.5)** | pass (mean gap −8.0) | | | 11,412 / 12,650 |
| San Diego 2021 | A (B) | 9.2 (0.8 to 21.8) | **fail** | 70% | 1,105 | 2,768 / 2,466 |
| | B (A) | 7.1 (−39.8 to 64.4) | pass | 20% | 451 | 2,489 / 2,578 |
| | place | **8.1 (−15.9 to 37.9)** | pass (mean gap −1.0) | | | 5,257 / 5,044 |
| Chicago 2022 | A (B) | −5.9 (−25.8 to 10.7) | pass | 30% | 355 | 12,817 / 15,991 |
| | B (A) | 0.5 (−2.7 to 4.0) | pass | 80% | 670 | 16,514 / 16,370 |
| | place | **−2.7 (−12.8 to 5.6)** | pass | | | 29,331 / 32,361 |
| Bellevue BelRed 2009 | both | not estimable (138 inside lots, 2 stops; < 20 lots a side) | | | | |
| Honolulu 2017 (beside) | B (A) only | 0.0 (no building on either side; 1 stop) | pass | 20% | 207 | 25 / 46 |

- **The two halves pick very different lines in every place.** The gap is 50 percentage points of map acres in each:
  Los Angeles 30% vs 80%, San Diego 70% vs 20%, Chicago 30% vs 80%. The training-half jumps swing in sign from one
  candidate to the next. So no stable demand edge shows up.
- Donut (25 m) and bunching match the main result. Pooled donut: 8.9 (−3.5 to 23.6). Pooled bunching: −1.9
  (−6.2 to 2.6), not flagged.

### Pooled (balance-passing places, each place weighted equally)

| Score | Window | Places | Pooled effect, per 100 lot acres a year (90%) | Leave one out | Wisconsin, extra homes 2027–2031 (90%) | Reading (locked rule) |
| --- | --- | --- | --- | --- | --- | --- |
| Distance to stop (main) | real | 3 (LA, SD, Chicago) | **6.4 (−3.5 to 18.1)** | 2.7 to 11.0 | 288 (−157 to 810) | **No binding line found** |
| Distance to stop (main) | placebo years | 2 (LA, Chicago) | 2.6 (−10.1 to 15.6) | −0.5 to 5.7 | — | includes 0: placebo passes |
| S1 neighbourhood rate | real | 0 (all fail balance) | — | — | — | not estimable under the rule |
| S1, no balance filter (beside) | real | 3 | 28.6 (16.9 to 42.5) | 16.4 to 35.7 | 1,281 (756 to 1,905) | would be "jump, but smaller" |
| S1, no balance filter (beside) | placebo years | 3 | **57.0 (31.6 to 83.5)** | 42.4 to 80.2 | — | **placebo fails** |
| S2 land value (Chicago only) | real | 1 | 0.9 (−6.9 to 7.4) | — | 43 (−308 to 332) | No binding line found |
| S2 land value (Chicago only) | placebo years | 1 | 8.9 (0.6 to 19.7) | — | — | placebo fails (small) |

- **Reading: "No binding line found."** The main pooled interval, 6.4 (−3.5 to 18.1), includes 0. It sits wholly
  below the district interval (50.8 to 129.1). The stricter balance rule (both halves must pass) leaves only
  Chicago: −2.7 (−12.8 to 5.6). The reading is the same.
- **The placebo check passes for the main score.** Placebo-years pooled: 2.6 (−10.1 to 15.6), includes 0. So the cross-fit
  choice itself does not make a jump.
- **S1 cannot be read.** Its lines fail balance in every place: the before-window rates on the two sides already
  differ (gaps −17 to −54). Its placebo years show a large false jump (57.0) where no reform happened. A line drawn on
  past building picks up building trends already under way. The S1 "jump" (28.6) is not evidence of a reform effect.
- **Use:** none. The tool and its lines are unchanged. The four broad places are not added to the floor pool.

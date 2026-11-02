# Option D: transit district mandate — modelling plan (LOCKED 2026-11-02 10:45)

Owner, 2026-11-02 10:37: "Let's adopt option D rigorously for the tool. Model it out with the fast fit and fix like
before, improve it until you have a clean round, and then run all the models to see if the more advanced tools
predict the policy better than an average."

## 1. The model law (what the tool would show)

| Item | Proposal |
| --- | --- |
| Who must act | Every Wisconsin city with qualifying rail or rapid-bus stops (today: Milwaukee, Madison, Kenosha, plus suburbs with stops) |
| What | Zone a by-right multifamily district near those stops |
| District size (central) | 15% of the lot acres within ¼ mile of the city's qualifying stops |
| District size (range) | 10% to 25% (the span the training places actually used) |
| Minimum density in the district | 15 homes per acre, by right |
| Who picks the land | The city |

This replaces the current benchmark law (upzoning 71% of nearby lots) as the TOD scenario's policy. The current
lines stay in the write-up as history.

## 2. Evidence base: the 11 district-like places

Places whose reform covered under 30% of lots within ¼ mile, measured as the reform stops' coverage minus the
comparison stops' coverage:

| Place | Share of ¼-mile lots in the district | Measured effect within ¼ mile (extra new homes per 100 lot acres a year) |
| --- | --- | --- |
| Philadelphia | 1.7% | +47.5 |
| Chicago 2015 | 3.4% | +9.0 |
| Seattle Mount Baker | 3.5% | +75.6 |
| Denver | 7.1% | +112.2 |
| Seattle Othello | 7.3% | +21.7 |
| New York | 7.6% | +28.1 |
| Salt Lake City | 14.7% | +50.4 |
| Saint Paul | 16.1% | +15.4 |
| Charlotte | 20.4% | +10.3 |
| Portland 2020 | 24.7% | −32.7 |
| Austin | 25.7% | +23.8 |

The 5 broad places (BelRed 50%, Honolulu 52%, LA TOC 81%, San Diego 97%, Chicago 2022 100%) are left out of the
training set. They stay as a check: a model trained on districts should not be able to predict a broad upzoning.

## 3. Stages (same staged method as before)

1. **Measure (done).** Each place's effect within ¼ mile from the station-area comparison: reform stops vs comparison
   stops, before vs after. Same windows, permit-year estimate and hand checks as the locked station-area plan.
2. **Benchmarks.** The rules a model must beat on places it has not seen:
   - zero;
   - the average of the other district places (the "average" rule).
3. **Fast fit.** The lot model with lot traits only, trained on the 11 places. The effect is the prediction with the
   district switched on minus switched off, on the district's own lots and on lots around them. Test: hide one place
   at a time, predict its measured effect, and compare the median error with the two benchmarks.
4. **Fix and repeat until a clean round.** A clean round means:
   - the model beats both benchmarks on hidden places;
   - its Wisconsin answer moves less than 10% across 5 random seeds (the steadiness fix from today: near-all lots,
     no random early stopping, averaging several fits).
   Each fix is logged with its date before the rerun, as before.
5. **All models.** Add trait groups one at a time, keeping one only if it lowers the hidden-place error:
   - place traits (transit frequency, jobs, walkability);
   - tract traits (78 Census variables);
   - affordability rules (today's inclusionary coding);
   - other model forms (the model menu).
   The answer to "do the advanced tools beat an average?" is that table.
6. **Bands.** ¼ mile is the main band. ¼ to ½ mile counts only if a model beats zero there on hidden places.
   Otherwise it counts zero, as in the locked rule.

## 4. Where the district goes in Wisconsin

The training cities picked land builders wanted (old industrial land, low-value lots). So the main version picks
Wisconsin's district the same way:
- a placement model, fitted on the 11 places, scores each ¼-mile lot by how alike it is to lots those cities zoned;
- each city's top-scoring lots, up to 15% of its ¼-mile acres, form the district.

Sensitivity: random placement, averaged over many draws. This shows how much the answer depends on cities choosing
well.

Caveat for the write-up: cities that chose districts by themselves probably chose better land than a state mandate
would force. The random-placement line is the guard against that.

## 5. What the tool would show

- **Line:** extra homes over 2027–2031 statewide from the district mandate.
- **Range:** each training place left out in turn, plus the 10%–25% district size.
- **Central:** whichever passes the stages: the best model if it beats the average rule, otherwise the average rule.
  The rule is fixed now, before any results.
- No zero floors (owner rule).

## 6. Owner decisions (2026-11-02 10:45)

1. District size: "base the district size on the benchmark policy which is based on what we have good data for ...
   15% of lot acres within .25 miles of the stops is a good start." Locked: 15%.
2. Option D replaces the current TOD benchmark law in the tool: "correct".
3. "I'd rather not pick specific sites but instead just show density in a radius of the TOD. But random is fine too."
   Locked: no site picking. The district is spread at random over the ¼-mile land, so each lot there is in the
   district with probability 0.15, and the answer is the expected extra homes. This replaces section 4's placement
   model; the "like the training cities" placement is dropped.

Departures and fixes after locking are logged below with dates, before each rerun.

## 7. Log

- **2026-11-02, round 1 (fast fit, lot traits, 5 averaged fits).** Not clean. Median error within ¼ mile on hidden
  places: model 36.1 vs others' average 19.3 vs zero 28.1 (extra homes per 100 lot acres a year); a second set of 5
  fits gave 47.8, and Wisconsin ¼ mile 806 vs 1,633. Causes found: (1) Austin has no land values and Philadelphia no
  year built, so a hidden place with a gap goes down a branch learned from another place's gap (hidden Austin
  predicted +324); (2) New York and Philadelphia carried about 95% of the training weight although the place is the
  unit of the test.
- **Round 2 fixes (logged before rerun):** fill whole-place gaps with the median over training lots; give each place
  the same total weight. Nothing else changes.
- **2026-11-02, round 2 result.** Not clean. Within ¼ mile the model now predicts close to zero for every hidden
  place (median error 28.5 vs zero 28.1 vs others' average 19.3). Lot-level noise swamps the district signal.
- **Round 3 fix (logged before rerun):** fit at the level the effect is measured: one row per stop and band, target =
  change in new homes per 100 lot acres a year (after minus before), features = reform stop, coverage, band, the
  band's lot acres and acre-weighted means of the lot traits; each place equal weight; trait gaps filled as round 2.
- **2026-11-02, round 3 result.** Not clean. Within ¼ mile: model 34.7 and 28.6 (two sets of fits) vs others'
  average 19.3 vs zero 28.1. The model again predicts small effects for the places with the largest measured gains
  (Denver, Mount Baker, Salt Lake City, Philadelphia).
- **Stage 5 (all models) run next, as the plan says, to answer whether any richer model beats the average:** lot and
  stop level, each with place traits, tract traits and the affordability-mandate coding added. If none beats the
  others' average on hidden places, the central line is the average rule (section 5, fixed before results).
- **2026-11-02, stage 5 (all models) result.** No model beats the others' average within ¼ mile on hidden places
  (median error, extra new homes per 100 lot acres a year; others' average 19.3, zero 28.1): lot + place 22.3; lot +
  place + tract 24.3; lot + mandate 28.6; stop level + place 32.1; + place + tract 30.7; + mandate 43.6. In ¼–½ mile no
  rule beats zero (zero 9.3, average 10.4), so that band counts zero.
- **Central by the pre-set rule: the average rule.** 8,856 extra homes statewide over 2027–2031 (each place left out:
  6,715 to 10,624), from the 11 places' mean effect of 32.9 extra homes per 100 lot acres a year × 4,874 Wisconsin lot
  acres within ¼ mile × 5 years × 1.106 statewide scale (scripts/build_tod_optiond_line.py,
  reference/tod_optiond_line.csv). The places' districts averaged 12% of ¼-mile lots, against the law's 15%; scaled to
  15% by their pooled ratio: 11,057 (8,053 to 14,836). Which one the tool shows is the owner's call.
- **2026-11-02 (after 14:25), random forest and causal forest added (logged before running).** Owner, 14:25: "did we
  run a causal forest and random forest on all 90ish traits?" Not yet for option D. Added `--learner` to
  scripts/run_tod_optiond.py (default `gb` = the gradient boosting above, unchanged):
  - `rf`: random forest (300 trees, leaf ≥50 stop-band rows at stop level / ≥200 lots at lot level, each tree on 30%
    of rows at stop level; at lot level a smaller share per tree for run time, stated with the result). Same on/off
    effect as the boosting model.
  - `cf` and `cf_honest`: a causal forest at stop level, scikit-learn only (no EconML, licence rule), as methods 9/10
    of scripts/run_tod_model_menu.py: cross-fitted outcome and treatment models, then a forest on the residuals
    (R-learner); the honest version re-estimates each leaf on a held-back half. Treatment = reform stop; outcome =
    change in new homes per 100 lot acres a year; traits = the acre-weighted trait means. Coverage is not a trait
    (it exists only at reform stops): one forest per band, so the ¼-mile forest gives the effect of a district like
    the training places' (about 12% of ¼-mile lots). Hidden place = acre-weighted effect over its reform stops;
    Wisconsin = that effect on Wisconsin ¼-mile stops × their lot acres, × 5 years × statewide scale.
  - All runs: gaps filled, each place equal weight (fixes fill,equal). Trait groups lot+place+tract (~90 traits)
    and lot+place. Test and benchmarks unchanged (others' average 19.3, zero 28.1 within ¼ mile).
- **2026-11-02, the tool's lines (owner decisions; AQ-071).** Central = the average rule, 8,856 (6,715 to 10,624);
  upper = the same scaled to a 15% district, 11,057 (8,053 to 14,836), replacing Auckland; lower = the best lot model
  (lot + place traits, 5 averaged fits), 450 (−121 to 818), owner 14:24: "I love that". All three are rows of
  reference/tod_optiond_line.csv (lower: `optiond_little`), timed by the New York pooled ramp, beyond ¼ mile zero, no
  zero floors. Homes are placed by each place's lot acres within ¼ mile of rail and rapid stops (the random district).
  scripts/run_tod_model.py, the TOD bundle and the combined bundle rebuilt; the former lines (13,229; Auckland 17,148;
  43) are what-ifs on How sure.
- **2026-11-02 14:54, statewide scale switched (owner: "You can switch.").** The scale to the state is now land, not
  homes: all Wisconsin lot acres within ¼ mile of rail and rapid stops ÷ those in the cities of Milwaukee and Madison
  (reference/tod_station_areas.csv, band rapid_quarter): 6,394 ÷ 5,212 = 1.2269, computed in
  scripts/build_tod_optiond_line.py (the same land the placement uses). Was homes within ½ mile, 1.1062. The lot model's
  file already carried ×1.1062, so the little line is rescaled by 1.2269 ÷ 1.1062. Lines: little 499 (−134 to 908),
  central 9,822 (7,448 to 11,784), upper 12,264 (8,931 to 16,454). Combined headline −14,828 / 9,822 / 30,222.
- **2026-11-02, auditor review items (no line changes).** (a) District-size what-ifs by the upper line's method:
  10% 8,176, 25% 20,440 (How sure). (b) The upper line leans on small districts: among the 11 places the effect falls
  with district share (Spearman −0.41); a straight-line fit at 15% gives 7,718 (6,960 on the old scale). (c) Broad-places
  check (reference/tod_optiond_broad_check.csv): for the 5 broad places (BelRed, Honolulu, LA TOC, San Diego, Chicago
  2022; measured −14.3 to +29.4 per 100 lot acres a year within ¼ mile) the average rule predicts +32.9 for each (median
  miss 41.4), the scaled rule 136 to 273 (median miss 226), zero misses by a median 10.7: these results describe
  districts, not citywide upzoning. (d) The Madison (2029, 2030) and Milwaukee (2030) record-year exceedance of the
  central and upper lines is stated beside the lines on the compare screen.
- **2026-11-02 16:31, exploration "B" (owner: "Give B a whirl. We're just exploring the data for now.").** Not a tool
  change. Inclusion rule, written before the rerun (from docs/tod/OPTION_D_CANDIDATES.md codes): a place is in B if
  its reform (1) was mapped by the city around one or more stations (not citywide, not owner-by-owner rezonings),
  (2) is at least partly by right, and (3) covers under 30% of the lots within ¼ mile. Out of the 11: Chicago 2015
  (bonus only through a Council rezoning per site), Portland 2020 and Philadelphia (citywide changes, not
  station-aimed). In: New York, Austin, Charlotte, Denver, Seattle Mount Baker, Seattle Othello, Salt Lake City, Saint
  Paul; Seattle Roosevelt 2012 to be added (fits with the "rail not open" trait). Caveat recorded: the per-place
  effects were known before this rule was written, so B is exploratory and not a pre-registered line.
- **2026-11-02 (after 16:46), exploration: stop-based model vs place-based average (logged before running).** Owner,
  16:46, asked whether a model built on reform stops beats the place-based average. Not a tool change. Script:
  scripts/run_tod_optiond_stops.py (imports scripts/run_tod_optiond.py, which is unchanged); outputs
  reference/tod_optiond_stopmodel_*.csv (no parcel ids). Same 11 places, fixes fill and equal, lots loaded once
  (seed 1, near-all lots, lot + block group + tract traits) and the stop-band table cached to
  data/processed/tod_station_area/optiond_stops_cache.parquet (local, not committed).
  - **Unit:** one reform stop-band (¼ mile is the main target; ¼–½ mile also reported). Its own measured effect = its
    change (after minus before, new homes per 100 lot acres a year, as `to_stops`) minus the acre-weighted average
    change of the comparison stop-bands in the same case and band. Comparison stops are the counterfactual only, not
    rows. One model per band.
  - **Test:** hide all stops of one place at a time (a place is never split); fit on the other 10.
  - **Benchmarks per hidden stop:** (a) the other places' average stop effect (each place's stop effects averaged
    first, acre-weighted, then the places averaged equally); (b) zero.
  - **Models** (traits: acre-weighted means of the lot, block group and tract traits, plus the stop-band's district
    coverage; each place's stops weighted to the same total, acre-weighted within the place):
    1. gradient boosting, 5 averaged fits (`Bag`, leaf ≥20 rows, as the round-3 stop model);
    2. random forest, 5 averaged forests (`Forest`, 300 trees, leaf ≥20 rows, each tree on 50% of rows);
    3. causal-forest-style R-learner (`CausalForest`, not honest, as the existing option D run), fitted on all
       stop-bands of the band (reform and comparison, as it needs both), traits without coverage, read on the hidden
       place's reform stops;
    4. small linear model (weighted least squares), traits fixed now: share of lot acres vacant; log land value per
       acre; log(1 + existing homes per acre); jobs reachable by transit (block group, `sld_transit_job_access`).
       Gaps filled with the training median. Variant 4b adds district coverage as a fifth trait (needed for the 15%
       Wisconsin district).
  - **Scores:** (i) median absolute error per stop, each place's stops weighted so each place counts equally;
    (ii) place totals: acre-weighted mean of the predicted stop effects over the place's reform stops (New York and
    Philadelphia: averaged over rezonings, as measured) vs the place's measured effect; median absolute error over
    places, compared with the existing 19.32 (average) and 28.12 (zero) within ¼ mile.
  - **Wisconsin:** each Wisconsin ¼-mile stop-band with coverage 0.15; extra homes = predicted effect × stop lot
    acres / 100 × 5 years × statewide scale 1.2269 (reference/tod_optiond_line.csv); central = fit on all 11, range =
    each place left out. Compared with the tool's central 9,822.
  - **Scope cut before any fit (owner, 16:51):** "You don't need to run the full causal models on this set yet —
    let's just gather data and explore it for now." Models 2 (random forest) and 3 (R-learner) dropped; run only the
    two benchmarks, the 4-trait linear model (and 4b) and the gradient boosting (cheap at stop level: a few hundred
    rows a band). The stop-band cache is kept for a richer stop table later. No model results had been produced when
    the cut was made (only the cache was built).
- **2026-11-02 17:10, seed-variance test for the honest causal forest (logged before running).** Owner asked. The
  honest causal forest at stop level with lot + place traits scored 19.0 within ¼ mile (others' average 19.3), but
  from one fit, with a Wisconsin ¼-mile answer of −658 (each place left out: −5,742 to 16,197). Rerun on the same data
  with 5 model seeds (20261102, 1, 2, 3, 4; `--cf-seed`, which sets the folds, the honest halves and the trees). Saved
  for each seed: each hidden place's predicted effect (loco file) and the Wisconsin answer for every left-out fit plus
  the full fit (new file reference/tod_optiond_wisconsin_each_<tag>.csv). Reported: median error per seed and for the
  5-seed average prediction; Wisconsin central per seed and averaged; how much of the spread in the left-out answers
  comes from the seed versus from which place is left out.
- **2026-11-02, stop-based exploration result.** Not clean; the stop-based model does not beat the place-based average.
  828 reform stop-bands within ¼ mile (Philadelphia 340, Chicago 2015 191, New York 159, Portland 75, Charlotte 23,
  Salt Lake City 16, Saint Paul 10, Austin 5, Denver 5, Seattle Mount Baker 2, Seattle Othello 2); 770 in ¼–½ mile.
  Stop effects are very noisy (¼ mile: median +4.2, middle half −6.3 to +50.4, extremes −1,164 to +1,234 extra homes
  per 100 lot acres a year). The acre-weighted stop effects reproduce the measured effect exactly for the 9
  single-rezoning places; New York (22.2 vs 28.1) and Philadelphia (59.6 vs 47.5) differ because their comparison
  lots are the seed-1 sample. Within ¼ mile (median absolute error, extra homes per 100 lot acres a year):
  | Method | Per stop (each place equal) | Place totals vs measured (11 places) | Wisconsin 2027–2031, extra homes (range: each place left out) |
  | --- | --- | --- | --- |
  | Others' average stop effect | 36.0 | 19.8 | 9,990 (7,632 to 11,968) |
  | Zero | 23.9 | 28.1 | 0 |
  | Gradient boosting (5 fits, 94 traits + coverage) | 39.9 | 36.4 | 13,840 (10,667 to 19,464) |
  | Linear, 4 traits | 42.0 | 28.4 | 6,165 (2,515 to 8,330) |
  | Linear, 4 traits + coverage | 42.5 | 29.0 | 6,155 (−1,638 to 8,364) |
  Per stop, zero wins (most stops add little; a few add a lot). Place totals: the others' average (19.8; 19.3 with the
  measured New York and Philadelphia) stays best; the linear models tie zero; boosting is worse than zero (it
  predicts +133 for hidden Austin, +196 to +310 from the linear models for hidden New York). ¼–½ mile: zero best on
  both scores (per stop 11.7, places 9.3), so that band still counts zero. Wisconsin = predicted effect × 4,874
  ¼-mile lot acres / 100 × 5 × 1.2269; tool central 9,822. Files: scripts/run_tod_optiond_stops.py,
  reference/tod_optiond_stopmodel_{summary,places,stops}.csv. No tool change.
- **2026-11-02 18:22, stop-outlier data review, round 1 (logged before any fix).** Owner: "use these first
  stop-based results to find possible errors in the data like the condo multi-lot counts. Look at high outliers for
  mistakes, look at low outliers for mistakes, then look at the things in the center. Fix those mistakes and then
  rerun the boosted model on stop traits." 18:23: "keep fixing and fitting until you get a clean run with no
  mistakes" (clean = no confirmed data error left; at most 5 rounds). 18:24: the clean run also fits boosting with
  all lot, block group and tract traits, and a second version adding stop-table traits.
  Reviewed (reference/tod_optiond_stopmodel_stops.csv as written 10:09, which predates the land fix): ¼ mile top 30
  and bottom 30 reform stop-bands, ¼–½ mile top 15 and bottom 20, and 15 random stop-bands near the median in each
  band. For each, the lots carrying its change (window totals as the model reads them, hand-check corrections
  applied) and, in New York and Philadelphia, the raw DOB jobs / L&I permits within 80 m (address, units, status,
  scope text). 260 driver lots (New York 104, Philadelphia 63, Portland 53, Chicago 31, Denver 9).
  - **Confirmed error 1, New York hotel rooms counted as homes.** DOB new-building jobs list hotel rooms in
    "proposed dwelling units". New York and Philadelphia were never in the big-lot hand check. Check: MapPLUTO 18v1
    (the lot tables' own vintage) building class on the job's lot, where the 18v1 building was built in or after the
    job's year less 1. 209 hotel lots (class H or RH), e.g. a 2003 Times Square hotel job of 873 "units", 0
    residential units in 18v1; 8 condo-hotel towers (class RC, no residential units; e.g. a 390-unit SoHo
    condo-hotel); 10 condo towers whose job added hotel rooms to the residences (e.g. a 377-unit job = 214-room hotel
    + 163 condos; a 346-unit job = 189-room hotel + 157 condos); 19 health, nursing, shelter or care buildings
    (class I or N; beds or rooms). Mostly on the comparison side (Midtown and Lower Manhattan hotel boom), so they
    inflated comparison growth.
  - **Confirmed error 2, New York superseded jobs.** A lot with 2+ jobs where the 18v1 building matches the latest
    job's units (±10%): the earlier jobs were replaced, not built (e.g. one Downtown Brooklyn lot with jobs of 322
    (2007), 184 (2008) and 826 (2013) units and one 826-unit building; a far-West-Side lot with 764 (2013) and
    1,175 (2014)). 65 lots. The builder merged same-count refilings within 2 years only.
  - **Confirmed error 3, Philadelphia re-issued permits.** Same parcel, same unit count, permitted again 1–4 years
    later (staged permits within 548 days were already merged): 3 lots, largest 166 units permitted 2021 and 2024.
  - **Confirmed error 4, stale land in the stop table.** The stop rows used `acres` (stacked condo records counted per
    unit; e.g. a Charlotte ¼-mile stop-band at 442.6 acres vs 70.0 acres of land). Fixed by the land-once helper
    (`acres_land`, scripts/fix_tod_station_acres.py); the stop cache is rebuilt on it.
  - **Confirmed error 5, one Philadelphia addition counted twice.** A Center City high-rise counted as 234 + 55 units
    (an 11-storey addition permit "part of" the main permit, whose text says 248 units): 289 → 248 in one before
    window (one hand-entered row).
  - **Plausible, not changed:** a Chicago South Loop lot with Cook year built 2011 (398 homes) but a 2013 permit for 199 (already hand-checked
    "plausible"); Portland condo records with 0 acres (land on the common parcel); Chicago lots of 100+ homes moved
    into a window by the event dates and not yet hand-checked (all Cook apartment-sheet buildings of 2016–2020,
    consistent with permits where present); dormitory-coded Philadelphia parcels whose permits say dwelling units.
  - **Real (kept):** Philadelphia Front–Girard (an 861-unit 2019 permit), Spring Garden and Girard 4th St (the
    December 2021 permit rush before the tax-abatement change), Chicago Loop and South Loop towers (hand-checked),
    New York Downtown Brooklyn and Hudson Yards towers, Portland Pearl and South Waterfront towers in the before
    window with nothing after (the low tail). Tiny land denominators (e.g. 0.78 acres in a ¼–½-mile band where
    chained trolley stops split the land) are real geometry, not errors: such stops swing ±1,000+ per 100 acres.
    Philadelphia and New York stops repeat across rezonings (one stop in up to 11 cases); that is the case design
    (place totals average over rezonings), not a data error.
  - **Center:** no systematic gap found: zero-permit stops are low-growth areas with no 20+ unit permits nearby;
    no missing years within any window; lots with no land area are condo records (0 acres) or rights of way.
  - **Fix (in the pipeline):** scripts/build_tod_hand_check_rules.py writes rule rows (evidence starting "rule ",
    source MapPLUTO 18v1 / DOB job filings / L&I permits) into data/processed/tod_station_area/hand_check_big_lots.csv,
    which model time already applies; one row per case, lot and window. Then the stop cache is rebuilt and
    scripts/run_tod_optiond_stops.py rerun.
- **2026-11-02 18:50, names (owner: "Great names. Use them here on out.").** Every result is labelled by evidence set,
  training level and method. Evidence set: **D-11** (the 11 district places) or **D-B** (the 8 station-focused
  places; Seattle Roosevelt shown separately). Training level: **lot model** (one row per lot) or **stop model** (one
  row per station and distance band). Method: average, zero, boosted, random forest, causal forest, 4-trait. The
  tool's central line is "D-11, average".

### Lot land fixes (2026-11-02, owner OK 18:04 and 19:55; logged in docs/tod/STATION_AREA_PLAN.md)
- `acres_land` replaces `acres` in every per-acre effect and the lot-size trait: stacked condo records share their parcel's land; San Diego's blank `acreage` filled with the SANDAG parcel area; any land still missing (mainly Chicago, 28% of ¼-mile lots) filled from census block land at the same city's lot-to-block share (`acres_land_source`; reference/tod_station_acres_census_fill.csv). `scripts/run_tod_optiond.py` changed in one line (`to_stops`: lot-acre weights use `acres_land`).
- Option D lines, statewide extra homes 2027–2031 (range = each place left out): average 9,822 (7,448–11,784) before any fix → 10,409 after the stacking fix → **10,262 (7,837–12,268)** after the fills; 15% scaled 12,264 → 12,996 → 12,813; lot model (lower line) 499 → 716 → **620 (−26 to 1,072)**. Mean ¼-mile effect of the 11 places 32.85 → 34.81 → 34.32 extra homes per 100 lot acres a year.
- **2026-11-02, seed-variance test redone on one data state (logged before running).** The first five seeds ran
  across three data and code states (lot tables rebuilt by the land fixes while the runs went; `to_stops` switched to
  `acres_land`), so they are not comparable and are discarded. Rerun: all five seeds in one process on one data load
  (`--cf-seeds 20261102,1,2,3,4`), on the lot tables as rebuilt at 12:04 (Pacific, machine clock) with `acres_land`
  weights. Run with one OpenMP thread per process (`OMP_NUM_THREADS=1`): the boosting nuisance models were ~35× slower
  under thread contention with other jobs; results do not depend on the thread count.
- **2026-11-02 21:04, stabilised honest causal forest (owner exploration; logged before running).** Learner
  `cf_stable` in scripts/run_tod_optiond.py, stop level, D-11, lot + place traits, scikit-learn trees only:
  (1) 2,000 trees; (2) each tree draws half of the places as whole places (cluster = place, as grf's `clusters`),
  not stops; (3) honesty 0.3: of the drawn places, 30% grow the tree and 70% estimate the leaf effects (split by
  place, as grf does with clusters); (4) minimum leaf 40 stop-band rows (2× the 20 used before); nuisance models
  cross-fitted over folds of whole places. (5) Doubly robust (AIPW) average effect within ¼ mile, over all stops and
  over reform stops, from out-of-bag effects, with a 95% interval from resampling places (2,000 draws). (6) grf-style
  calibration test: regress y − m(x) on the mean forest prediction and the differential forest prediction (both × (t −
  e(x))), place-clustered standard errors; heterogeneity counts as found if the differential coefficient is
  significantly above 0 (one-sided, p < 0.05). Scored as before (hidden-place median miss vs others' average and zero)
  on the ¼-mile band only (run time), 5 seeds on one data load; Wisconsin spread across seeds reported. NY hotel /
  superseded-job hand-check fixes: not in this data state unless the lot tables are rebuilt before the run starts.
- **2026-11-02 (after 21:18), "remove the noise" test: partialling out and double ML, lot model (pre-registered;
  logged before any fit).** Owner, 21:10–21:18: "once we remove the noise from all these other variables which make it
  better or worse to develop a lot near this stop, here is the difference reform makes"; approved as a test
  ("validate your theory by running it"); he doubts the treatment-model step helps, so it runs with and without it.
  Script scripts/run_tod_optiond_dml.py (imports scripts/run_tod_optiond.py and scripts/run_tod_station_lotmodel.py,
  both unchanged); outputs reference/tod_optiond_dml_*.csv. scikit-learn only.
  - **Evidence sets:** D-11 and D-B (the 8 station-focused places; Seattle Roosevelt has no lot table, so not in).
  - **Rows:** lots (lot model), comparison lots sampled as sampling "full" (New York / Philadelphia: one fixed set
    per seed). One fit per band: ¼ mile is the main band, ¼–½ mile reported. Permit-year dates and hand checks as
    the measured effects (including any "rule " rows present in hand_check_big_lots.csv at load).
  - **Outcome:** y = 100 × (lot's new homes a year in the after window − in the before window) ÷ the lot's land acres
    (`acres_land`, floored at 0.001 acre so homes on records with no land stay in the sum); row weight ω = lot weight
    × land acres, rescaled so each place has the same total weight in the band. Weighted means of y are then extra
    new homes per 100 lot acres a year, built as the measured effects are.
  - **Treatment D:** main = in the reform area of a reform stop (in_reform_area × reform stop). Check = reform stop
    (stop exposure).
  - **Traits X (no place identifiers):** lot traits (9, incl. the before-window rate), place traits without the band
    flags (distance, transit frequency, jobs, walk-to-transit, no-car share, job growth, historic), the ~78 tract
    variables, and stop-table traits of the lot's stop: own-system ridership before reform (log, NTD 5-year average),
    trips per hour peak and midday at the node (all systems), number of systems at the node, transfer hub, and the
    band's developable, vacant and underused land (acres counted once, log(1 + acres) and as shares of the band's
    land). Whole-place gaps filled with the training median (fix "fill").
  - **Learners:** gradient boosting as `Bag` (300 rounds, rate 0.05, leaf ≥ 200 lots, no early stopping; one fit per
    nuisance per seed); classifier with the same settings for P(D | X). Cross-fitted over 5 folds of whole places.
  - **Version A (outcome only, "partialling out"):** θ_A = weighted least-squares slope of y − m̂(X) on D (with an
    intercept), weights ω.
  - **Version B (adds the treatment model):** B-PLR = Robinson's partialling-out estimator Σω(D − ê)(y − m̂) ÷
    Σω(D − ê)²; B-AIPW = doubly robust effect on the treated lots, Σω[D(y − μ̂0) − (1 − D) ê/(1 − ê)(y − μ̂0)] ÷ ΣωD,
    μ̂0 = outcome model fitted on untreated lots. ê trimmed to [0.01, 0.99]; lots and land trimmed reported.
  - **Interval:** place-cluster bootstrap (resample places with replacement, 500 draws) of the final step, with the
    cross-fitted nuisance predictions held fixed (stated as a limitation: nuisance refits are not bootstrapped).
  - **Hidden-place test (scoring rule, fixed now):** hide a place, estimate θ on the other 10 (D-B: 7) with folds
    over those places only, predict the hidden place's measured band effect: D = in-area → θ × the hidden place's
    district share (land share of its reform-stop band lots in the reform area; New York and Philadelphia averaged
    over rezonings, as measured); D = reform stop → θ. Score = median absolute miss over hidden places, against the
    others' average and zero recomputed on the same data (15.18 within ¼ mile after the land fixes, before any
    hand-check rules). "Removing the noise beats the average" if a version's ¼-mile median miss is below the
    others' average; "the treatment step helps" if B's miss is below A's for the same D.
  - **Stability:** 5 seeds (1–5: comparison sample, fold assignment, model seeds), full-data θ per seed; spread
    reported (the plan's steadiness bar: Wisconsin answer moves < 10%). Hidden-place test on seed 1.
  - **Wisconsin (central rule as the average line):** D = in-area: θ × 0.15 × 4,874.1 ¼-mile lot acres ÷ 100 × 5
    years × 1.2269; D = reform stop: θ × 4,874.1 ÷ 100 × 5 × 1.2269 (a district like the training places', about
    12%). Range = the cluster-bootstrap interval. Caveat: the training districts were city-picked land; Wisconsin's
    is spread at random.
- **2026-11-02, seed-variance result: honest causal forest, stop level, lot + place traits (4 seeds; 5th stopped by
  owner, 21:26).** One process, one data load (lot tables of 12:04 Pacific with the land fixes, `acres_land`
  weights); seeds 20261102, 1, 2, 3 (seed 4 stopped). The earlier single-run figures (19.0 within ¼ mile; Wisconsin
  37,744 / 5,794 / 10,118 / 221 and misses 51.6 / 14.6 / 23.8 / 33.7) mixed three data states and are superseded.
  Benchmarks on this data: others' average 16.0, zero 28.4 within ¼ mile; 10.2 and 9.3 in ¼–½ mile (median miss,
  extra new homes per 100 lot acres a year, 11 hidden places).

  | Seed | Median miss within ¼ mile | Median miss ¼–½ mile | Wisconsin ¼ mile, full fit (extra homes 2027–2031) |
  | --- | --- | --- | --- |
  | 20261102 | 36.0 | 16.4 | −7,614 |
  | 1 | 60.3 | 33.8 | −9,832 |
  | 2 | 35.1 | 22.4 | −440 |
  | 3 | 39.6 | 18.5 | −4,146 |
  | Average of the 4 seeds' predictions | 28.2 | 24.0 | −5,508 |

  No seed beats the others' average (16.0) or zero (28.4) within ¼ mile. Each place's prediction swings by tens of
  homes per 100 acres between seeds (Chicago −18 to +120; Austin −50 to +48). Wisconsin, each place left out (44
  answers): −14,151 to +13,363. Split of that spread: which place is left out 29%, seed 9%, the two together 62%;
  typical spread across seeds for a fixed left-out place: 5,610 homes (standard deviation). The biggest swings come
  from leaving out Austin, Portland, Charlotte and Mount Baker. Verdict: the honest causal forest is unstable and
  does not predict hidden places; it is not used. Files: reference/tod_optiond_{loco,wisconsin,wisconsin_each}_
  lot_place_fix_equal_fill_stops_k1_s1_cf_honest{,_cs1,_cs2,_cs3}.csv (the `_cs4` files are from the old data and
  are void).
- **2026-11-02, stabilised causal forest moved to LOT level (coordinator spec after 21:04; logged before running).**
  Replaces the stop-level `cf_stable` run (not run). `--learner cf_stable --level lot` in scripts/run_tod_optiond.py:
  D-11, ¼-mile band, lot rows from scripts/run_tod_optiond_dml.py's loader (lot + block-group/place + tract traits +
  stop-table traits of the lot's stop: pre-reform ridership, peak and midday trips, systems at the node, transfer
  hub, developable / vacant / underused land deduplicated by band; no post-reform ridership); comparison lots
  sampled, one fixed NY/PHL set per seed; outcome and weights as that script (each place the same total weight).
  Forest: 2,000 trees; each tree draws half of the places as whole places; honesty 0.3 by place; at most 5,000 lots
  per drawn place per tree (grf's samples per cluster; run time); 30% of traits tried per split (≈ grf's default);
  minimum leaf 400 lots (2× the lot-level boosting leaf of 200); nuisances cross-fitted over folds of whole places.
  Two treatments: reform stop (main, comparable with the measured effect) and lot in the reform area (prediction ×
  the place's district land share, as the DML script). Reported: hidden-place median miss vs others' average and
  zero; AIPW average effect (all lots and treated lots) with a place-bootstrap interval; calibration test; Wisconsin
  ¼-mile for the full fit and each left-out fit; 5 seeds. Starts after the DML smoke run has reported.
- **2026-11-02, "remove the noise" smoke run (owner 21:24: light run first, to get kinks out; not a result).** D-11,
  seed 1, about 10% of comparison lots (weighted ×10), all reform-stop lots, 2 folds of whole places, 100 boosting
  rounds, no hidden-place loop. Data: lot tables with the New York / Philadelphia hand-check rule rows applied (3,929
  rows with evidence "rule "), land fixes in. Diagnostics with lot ids stay in the scratchpad (not in reference/).
  Effects (extra new homes per 100 lot acres a year, ¼ mile): in-area A 102.3, B-PLR 67.3, B-AIPW 43.6; reform stop
  A 65.9, B-PLR 33.1, B-AIPW 650.3 (blown up). ¼–½ mile: in-area 50.3 / 18.7 / 19.4; reform stop 2.3 / 31.5 / 1,446.
  Measured New York ¼-mile effect is now 19.6 (was 28.1) after the rule rows, so the benchmarks move.
  Kinks found (no fit counted):
  1. Place-level levels are not removed: the outcome model, trained on other places and without place identifiers,
     leaves mean residuals of −430 (Salt Lake City comparison lots) to +49 (Portland) per 100 lot acres a year
     within ¼ mile, ten times the effects. A then partly compares places, not lots.
  2. No overlap for the treatment model: in-area propensities fall below 0.01 for 35% of ¼-mile lots and 93% of
     ¼–½-mile lots; most real district lots get a pick chance under 0.02 (Portland 3,038 of 3,088; Chicago 2,138 of
     3,190; Philadelphia 2,081 of 3,429). Reform-stop propensities near 1 on some comparison lots (Denver 165) make
     B-AIPW explode. Folds of whole places mean each place's district is predicted from other cities' choices.
  3. Data: no inf or constant traits; Denver lacks block-group job growth. Of the 100 largest lot residuals per band,
     14 already have a hand-check row; the others are known real cases (Philadelphia Front–Girard 861 homes, repeated
     across rezonings; Charlotte and Chicago towers checked "plausible" or "confirmed"), public land of 100+ acres
     with nothing built, and 4 New York lots of 490–835 homes (one window) with no hand-check row (not hotels by the
     rule; worth a look). No new confirmed error.
  Run time: about 5 minutes a band for the smoke settings; the pre-registered full settings come to about 1 hour a
  band per set and seed, so the hidden-place loop is about 11 hours for D-11 ¼ mile alone. Waiting for a decision
  before the full run.
- **2026-11-02, departures from the "remove the noise" pre-registration (approved by the coordinator under the
  owner's research-design delegation; logged before the full run, with the smoke evidence above).**
  1. *Within-case centring.* In the final step the outcome residual y − m̂(X) and the treatment are centred on their
     case (rezoning) means, weighted, so district lots are compared with the other lots of the same case, as the
     measured effects are. Applies to A and B. Evidence: smoke-run place-mean residuals of −430 to +49 per 100 lot
     acres a year, ten times the effects.
  2. *Treatment model within case.* P(in the reform area | X) is fitted inside each case (5 lot folds within the case,
     gradient-boosting classifier, leaf ≥ 20 lots for small cases; cases with no district lots take the case share),
     because it describes how a city picked its district. Scored versions: A and B-PLR. B-AIPW is kept only as a
     diagnostic (propensities trimmed to [0.01, 0.99], flagged unstable). Treatment = in the reform area is the main
     treatment; reform stop is a diagnostic (version A only). Evidence: with folds of whole places, most real district
     lots had a pick chance under 0.02 and B-AIPW blew up (650 and 1,446).
  3. *Run time.* 150 boosting rounds at rate 0.1 (was 300 at 0.05); 5 place-folds for the full fits, 3 in the
     hidden-place loop; hidden-place test within ¼ mile only, seed 1 only; full-data effects for seeds 1–5, both
     bands; D-11 and D-B in two parallel processes (3 threads each).
  4. *Benchmarks recomputed on the fixed data* (rule rows in; New York ¼ mile 28.1 → 19.6), each evidence set's
     others' average taken over its own places.
  - *Hand check of the large New York lots from the smoke residuals* (MapPLUTO 18v1 on the lot, as the rules use): 12
    lots of 490–921 homes in one window. 10 match the 18v1 residential units within 1% (e.g. 835 vs 835, 631 vs 631,
    921 vs 921): real. One 554-home 2005 job vs 458 residential units in a 59-floor condo tower: within normal unit
    re-counting, left. One 814-home 2009 job on a 59-floor condo lot with 940 units in all but 187 residential in
    18v1: possibly condo-hotel units, but 18v1 condo-lot residential counts are not reliable enough to call it;
    unverifiable, left unchanged. No confirmed error, no rows added.
- **2026-11-02 (after the land fix), stop-outlier review: fixes applied and round 2.** Coordinator: the land fix is
  complete (acres_land in all 122 lot tables); apply. Outputs before the fixes saved to the session scratchpad
  (before_ny_fixes/).
  - **Applied:** `.venv/bin/python scripts/build_tod_hand_check_rules.py` wrote 3,929 rule rows (New York 3,828 case
    rows: hotel 209 lots, condo-hotel 8, hotel + condo 10, health / home / shelter 19, superseded jobs 65;
    Philadelphia re-issued 3 lots, 101 case rows); hand-entered: the Philadelphia addition (289 → 248, 43 case rows) and **two
    Seattle hand-check corrections stranded by the event dates** (found in round 1's check of hand-check rows
    against the event windows): a 238-unit dormitory corrected in Mount Baker but now in Othello's after window
    with no row there, and a 158-room congregate building corrected in Mount Baker's before window while its record
    now falls in Mount Baker's after window. Rows sit in the local hand-check file (5,371 rows). Reran
    run_tod_station_model.py (effects), run_tod_optiond.py lot,place k5 fill,equal, build_tod_optiond_line.py, and
    the stop model (cache rebuilt) on D-11 and D-B.
  - **Measured effects that moved** (extra homes per 100 lot acres a year): New York ¼ mile 28.1 → 19.6, ¼–½ mile
    17.6 → 4.7, ½–1 mile 10.3 → 12.2 (hotels sat on both sides, more of them inside the rezonings' ¼-mile rings);
    Philadelphia ¼ mile 47.5 → 47.5; Othello ¼–½ −71.6 → −68.3; Mount Baker ½–1 −8.7 → −8.1. Others unchanged.
  - **Option D lines** (Wisconsin 2027–2031, extra homes): average rule 10,262 (7,837 to 12,268) → 10,028 (7,580
    to 12,010); 11-place mean effect 34.3 → 33.5. Lot model (lower line) 620 (−26 to 1,072) → 824 (−90 to 1,006);
    its ¼-mile hidden-place error 22.4 vs average 16.0 vs zero 28.4. Pre-registered versions: raw 5-year total
    4,609 → 4,381, scaled 6,593 → 6,287.
  - **Round 2 review** (same lists on the rerun): 27 driver lots not seen in round 1 (New York 18, Portland 8,
    Philadelphia 1). Every New York one matches its MapPLUTO 18v1 building's units (e.g. 551, 490, 256 units);
    Portland ones are hand-checked high-rises (plausible) or under 100 homes; the Philadelphia one is a 104-unit
    2012 building. Center sample: nothing off (Chicago stop land now above recorded acres where the same-city
    fill gives lots without area a size). **No new confirmed error: the run is clean.**
  - **Stop model, clean run** (median absolute error, extra homes per 100 lot acres a year; Wisconsin = extra homes
    2027–2031, central = fit on all places of the set, range = each place left out; before = land-fixed data
    without these fixes):

    | Label | ¼ mi per stop (before → after) | ¼ mi place totals | ¼ mi Wisconsin after (range) | ¼–½ mi per stop | ¼–½ mi place totals |
    | --- | --- | --- | --- | --- | --- |
    | D-11, stop model, others' average | 37.5 → 36.3 | 15.1 → 16.6 | 10,119 (7,680 to 12,111) | 16.3 → 16.9 | 14.8 → 10.8 |
    | D-11, stop model, zero | 27.2 → 26.9 | 28.4 → 28.4 | 0 | 11.8 → 11.7 | 9.8 → 9.3 |
    | D-11, stop model, boosted all traits | 44.1 → 39.3 | 36.7 → 36.1 | 18,690 (11,559 to 23,641) | 19.1 → 19.5 | 11.8 → 17.4 |
    | D-11, stop model, boosted all traits + stop traits | 32.4 → 34.8 | 22.7 → 28.3 | 11,932 (7,576 to 12,127) | 27.5 → 33.3 | 10.5 → 12.8 |
    | D-B, stop model, others' average | 43.4 → 41.8 | 24.1 → 25.5 | 12,664 (9,543 to 14,006) | 23.0 → 23.7 | 25.9 → 19.9 |
    | D-B, stop model, zero | 28.5 → 28.5 | 28.3 → 26.1 | 0 | 14.0 → 14.0 | 13.7 → 7.4 |
    | D-B, stop model, boosted all traits | 40.4 → 44.4 | 48.9 → 58.1 | 17,793 (4,495 to 20,259) | 17.8 → 18.8 | 28.0 → 24.7 |
    | D-B, stop model, boosted all traits + stop traits | 44.7 → 43.4 | 46.6 → 60.4 | 18,954 (−1,200 to 22,074) | 21.1 → 19.8 | 25.5 → 21.2 |

    Boosted = 5 averaged gradient-boosting fits on 94 lot / block-group / tract traits + coverage; "+ stop traits"
    adds 27 stop-table traits (trips per hour peak and midday, EPA D4c, points merged, footprint, names merged,
    own-system NTD ridership 5-year average before the reform, all systems' ridership, systems at the node,
    transfer hub, node trips peak and midday, the band's land / developable / vacant / underused acres counted once,
    homes per acre, land value per acre, jobs per acre, transit job access, share of lots vacant, mode). Left out:
    station-level and post-reform ridership (owner), grade (20% of reform stations known) and opening year (47% in
    the extra-traits file; both under the 80% bar). Wisconsin has no trips per hour for Madison (AQ-045) and BRT is
    absent from the training places, so the stop-trait version reads Wisconsin through gaps. **Result:** the data
    are clean but the stop model still does not beat the place-based average on place totals in either set
    (D-11 ¼ mile: average 16.6, boosted 36.1, boosted + stop traits 28.3, zero 28.4); per stop, zero stays best.
    ¼–½ mile: zero best on both scores. New York's stop rows reproduce 10.9 vs the measured 19.6 (comparison lots
    are the seed-1 sample). Files: reference/tod_optiond_stopmodel_{summary,places,stops}.csv (D-11) and *_db.csv
    (D-B). No tool change.
- **2026-11-02 14:45, "remove the noise" interim result (seed 1, within ¼ mile; fixed data; reference/tod_optiond_dml_interim.csv).**
  Extra new homes per 100 lot acres a year; interval = 95% from resampling places (nuisances held fixed); hidden-place
  score = median absolute miss of the place's measured ¼-mile effect; Wisconsin = extra homes 2027–2031.
  | Set | Version (treatment: in reform area) | Effect (interval) | Hidden miss: model / others' average / zero | Wisconsin (interval) |
  | --- | --- | --- | --- | --- |
  | D-11 | A, outcome model only | 75.4 (−2.9 to 160.6) | 30.2 / 16.0 / 28.4 | 3,383 (−129 to 7,205) |
  | D-11 | B-PLR, adds treatment model | 32.2 (−13.7 to 132.6) | 18.9 / 16.0 / 28.4 | 1,445 (−615 to 5,947) |
  | D-B | A | 26.9 (−126.9 to 162.3) | 23.4 / 26.2 / 26.1 | 1,208 (−5,692 to 7,278) |
  | D-B | B-PLR | −20.8 (−128.7 to 108.7) | 47.7 / 26.2 / 26.1 | −931 (−5,774 to 4,874) |
  Diagnostics: reform-stop treatment (A) D-11 29.3 (−1.7 to 61.6), hidden miss 36.5; D-B −65.9 (−189.0 to 36.8), miss
  25.6. B-AIPW −389 (D-11) and −485 (D-B), unusable as expected. Within each case 93–96% of lots get a pick chance
  outside [0.01, 0.99] (comparison-stop lots have no chance of being in the district).
  Reading: on D-11 no version beats the others' average (16.0); B-PLR (18.9) beats zero, A does not. On D-B, A edges
  both benchmarks (23.4 vs 26.2 and 26.1), but there the average itself does not beat zero, the interval spans
  −127 to +162, and B-PLR turns the effect negative, so it is not a usable win. The in-area version under-predicts
  every place with a large measured effect (Denver 115, Mount Baker 76, Philadelphia 47 → predictions 1–6), because
  most of the measured band effect sits on lots outside the mapped district or comes from place-level differences
  the within-case comparison removes. Remaining seeds and ¼–½ mile are still running; final summary to follow.

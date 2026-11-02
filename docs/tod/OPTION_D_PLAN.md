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

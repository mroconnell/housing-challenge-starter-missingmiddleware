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

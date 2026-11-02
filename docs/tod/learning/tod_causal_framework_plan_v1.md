# TOD causal framework: implementable plan (v1)

Drafted 2026-11-02 by the learning thread for the TOD session, at Ryan's request ("work with the learning session to develop its stage 1 and 2 for you to implement"). Builds on [tod_framework_pitch_2026-11-02.md](tod_framework_pitch_2026-11-02.md) (revision 2) and the TOD session's reply. The TOD session owns the locked version in `docs/tod/CAUSAL_FRAMEWORK_PLAN.md`; where the two differ, the locked file wins and this one should be updated.

## Shared rules (apply to every test)

- **Headline estimand:** net new homes permitted statewide in 2027–2031 caused by the option D district law (15% of lot acres within ¼ mile of rail and rapid stops, by right, ≥15 homes per acre).
- **Places:** the 11 district places in OPTION_D_PLAN.md. A place is dropped from a test only by a rule written here, never after seeing its result. Every drop is listed.
- **Outcome:** new homes, same windows, permit-year estimate and hand-check corrections as the locked station-area plan. Lead unit: extra homes per 100 lot acres a year. Report beside it: share of the city's new homes in the area, and (where zoning is coded) homes per 100 homes of added capacity.
- **Lock first:** each test's pass rule goes into `docs/tod/CAUSAL_FRAMEWORK_PLAN.md` before its first count. Anything chosen after seeing results is labelled post hoc and shown beside the locked version.
- **Report everything:** each place's estimate with a 90% interval, the pooled estimate, and the leave-one-place-out range. No result is hidden because it is inconvenient.

## Stage 1: causal tests

### T1. Citywide net check (all 11 places)

- **Estimand:** net extra homes permitted in the whole city per 1,000 existing city homes a year, caused by the reform. It includes homes that moved into the station area from elsewhere in the city (as a loss).
- **Data:** Census Building Permits Survey place files (all units; 5+ units as a second series), city housing stock from the census before the reform. Same source as the Wisconsin baseline.
- **Comparison:** difference-in-differences against matched non-reform cities: same Census region, population within ×0.5–2, similar 5-year pre-reform permit trend. Use the 10 control cities already matched where they fit; add donors to reach at least 3 per place. Pre-period 5 years; post-period up to 5 years.
- **Pass rule:** (a) pre-trend check: the pre-period gap, tested as a placebo reform 3 years early, has a 90% interval that includes zero; a place failing it is reported but left out of the pooled figure. (b) For each place, compute the ratio R = citywide net homes ÷ station-area total homes (T2's figure, same years).
- **Feeds Wisconsin:** the downside "moved from elsewhere" case multiplies the central by the median R across passing places, capped at 1. If the pooled interval for R includes 1, the downside uses the lower end of that interval, labelled "not detectable at citywide scale." Known limit: the earlier control-city study could only detect changes of about 4–5% of a city's homes over 5 years; say so beside the case.

### T2. Line-age matching (separates the law from new transit)

- **Estimand:** the station-area total effect of the rezoning (all lots within ¼ mile of reform stops, rezoned or not), net of growth caused by new transit service.
- **Data:** opening year of each reform and comparison stop's line (agency records, National Transit Database); the station-area lot table.
- **Comparison:** reform stops vs comparison stops whose line opened in the same window: both within 3 years of each other, or both 10+ years old. A reform passed within 3 years of its own line opening is flagged "rezoned with new transit."
- **Pass rule:** the matched version becomes the main estimate if at least 8 of 11 places keep at least 3 matched comparison stops. Otherwise it is a sensitivity case. Report the pooled ¼-mile effect with and without the flagged places.
- **Transit-only check:** the Milwaukee Hop placebo (new line, no rezoning) and any other new-line, no-rezoning stops measure a transit-only effect. Report it beside T2.
- **Feeds Wisconsin:** this matters directly. Wisconsin's qualifying lines are new (the Hop 2018, CONNECT 1 2023, Madison Route A 2024). Growth from those new lines would happen without the law, so it belongs in the baseline, not in the law's effect. The central should use the T2 matched effect.

### T3. Edge test (difference-in-discontinuities at district boundaries)

- **Estimand:** the direct effect on rezoned lots: extra building on lots just inside the district vs lots just outside, before vs after.
- **Data:** reform district maps for the 11 places; lot table with new homes by year, existing homes and lot acres.
- **Comparison:** lots within a fixed distance of the boundary (main 300 ft; sensitivity 150 and 600 ft), inside vs outside, after minus before. Use only boundary segments within 1 mile of a stop. Tag segments that follow an arterial road; report with and without them.
- **Pass rules:** (a) balance: the inside–outside gap before the reform has a 90% interval including zero, else the place is reported but left out of the pooled figure. (b) Shifting checks (locked by TOD): a 25 m donut sensitivity, and a bunching test comparing the rate just outside the line with the rate 100–200 m outside. If near-outside lots lose building, report the estimate with them dropped.
- **Feeds Wisconsin:** a "direct effect only" line = pooled direct effect × Wisconsin district acres (15% of the ¼-mile lot acres) × 5 years, shown as a floor. Decomposition shown in the tool: station-area total (T2) − direct effect (T3) = spillover plus any remaining other causes.

### T4. Distance-cutoff discontinuity (LA TOC tiers)

- **Estimand:** the effect of a stronger incentive at a tier boundary (more allowed density just inside the cutoff).
- **Data:** LA TOC tier map and its distance cutoffs; LA lot table.
- **Comparison:** lots just inside vs just outside each tier cutoff, before vs after 2017. Local linear fit; bandwidth chosen by a standard data-driven rule fixed before running; same balance and donut rules as T3.
- **Pass rule:** report the jump at each cutoff with a 90% interval; pass if balance holds.
- **Feeds Wisconsin:** dose evidence only. A positive jump supports the "per unit of added capacity" view (stronger allowance, more building). Not a line on its own. Note that LA TOC carries affordability requirements that Wisconsin's law does not.
- **Not used here:** California AB 2097 is a parking rule, not a density cutoff; it stays with the parking thread (TOD tested it Oct 27, no effect).
- **Rule for other distance bands:** use a distance discontinuity only where the law itself changes at that distance. Elsewhere, distance bands describe a gradient, not a discontinuity.

### T5. Massachusetts MBTA Communities (feasibility, then direction)

- **Estimand:** the direction of the effect of a *mandated* district, as opposed to one a city chose.
- **Data:** BPS town-level permits; each town's category, deadline and compliance status from the state housing office (check the deadlines against the official list before use; categories had staggered deadlines from end-2023 to end-2025).
- **Comparison:** staggered event study using only not-yet-due towns as controls.
- **Pass rule:** feasibility passes if at least 20 compliant towns have at least one full post-deadline year in BPS. If it passes, report the sign and interval of the year-1 effect. No size is carried to Wisconsin.
- **Feeds Wisconsin:** narrative and a flag. If the mandated effect is zero or negative with an interval excluding the chosen-district average, add a "mandated district" sensitivity at the T3 direct-effect floor.

### Dropped

- The stabilised causal forest (TOD session's recommendation): too few places to find reliable subgroups.

## Stage 2: carrying it to Wisconsin

1. **Central:** plain average of the 11 places' station-area total effects (T2 matched version if it passes) × Wisconsin's lot acres within ¼ mile × 5 years × the locked ramp × the statewide scale. Same structure as today's central.
2. **Upper:** the same scaled to a 15% district by the pooled ratio (as now).
3. **Lower:** the best lot model (as now).
4. **Shown beside the central:** direct-effect-only floor (T3); downside for relocation (T1); with and without "rezoned with new transit" places (T2).
5. **One-trait adjustment (sensitivity):** trait fixed now: log median home value of the station area (ACS), consistent with the ADU model. Effect = plain average + slope × (Wisconsin's value − place's value). Pass rule: kept only if its leave-one-place-out median absolute error is strictly below the plain average's (19.3 per 100 lot acres a year in the option D run). Otherwise not shown.
6. **Record-year warning (not a cap):** flag any year where Milwaukee's or Madison's total with the law passes its own record or the 95th percentile of peer metro-years. Clipping is Ryan's decision.
7. **After launch, written now:** when Milwaukee's and Madison's 2027+ permits are published, add each city as a 12th and 13th place with its own measured effect, and recompute the plain average. The first check is due when two full years exist (2029).

## Run order

1. T1 citywide check (all 11); for each place, report the share of the station-area gain that shows up as a citywide net gain
2. T2 line-age matching
3. T3 edge test
4. T4 LA TOC tiers
5. T5 Massachusetts feasibility
6. Stage 2 one-trait adjustment

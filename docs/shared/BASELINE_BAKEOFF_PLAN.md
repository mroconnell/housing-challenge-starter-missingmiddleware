# Baseline bake-off: locked plan (LOCKED 2026-11-05, nothing run)

Written 2026-11-05 by the baseline thread. Owner: "yes" (16:45 UTC) to writing this plan. Status: **LOCKED 2026-11-05 (lock time recorded in the Plan log).** The audit cleared revision 2 at 16:51 UTC. Ryan picked D1–D6 at 17:07 UTC ("okay, including D6"). The only change made after the audit's clearance is the D6 region candidate L5, added before any fetch or count. Nothing is fetched or run yet. The fetch script gets its own audit check first. Anything chosen after seeing a result is labelled *post hoc*.

## The question

Ryan's goal (2026-11-05): a reliable forecast of Wisconsin's housing permits over 2027–2031 if the state passes none of the reforms. The current baseline (v3) holds each town flat at its 2023–2025 average: 124,000 homes permitted over 2027–2031, range 65,250 to 177,672.

That rule was chosen by replaying only four start years (2019–2022), all in a rising market. This plan tests Ryan's six ideas against it over many more start years, including the 2006–2011 crash:

1. use more years for the state trend;
2. use regional (county) trends;
3. use data from before 2015;
4. pull hot or cold towns back toward the average;
5. smooth out lumpy big projects;
6. learn from other states.

## Design: two parts, scored separately

The baseline is split into two parts, each tested on its own:

- **Level:** how many homes Wisconsin permits over the five years, for each building size (1 unit, 2 units, 3–4 units, 5+ units).
- **Shares:** how each size's state total splits among the 1,925 municipality pieces.

The final baseline is level × shares. This matters because parking's earlier test found one method can be better at state totals while another is better town by town.

## Shared rules for fitting and scoring

- **Start year.** A start year t uses permit data for years up to and including t. Its outcome is the five years t+1 to t+5.
- **No look-ahead in fitted numbers (audit 1).** L3's b and S3's k are fitted separately for each scored start year t. They use only start years s ≤ t − 5, whose five outcome years end by t.
- **Fit start years.** These begin in 1992 (the first year with 3 prior years of state data) for Part 1, and in 1992 for Part 2 if 1990–1991 place data pass the coverage check (otherwise the first year after 2 covered years).
- **Same start years for every candidate.** Part 1 scores every candidate on start years 2000–2020. Part 2 scores every candidate on start years 2004–2020. Every scored start year has at least 4 fit start years.
- **Paired block bootstrap (audit 2).**
  - Start years are resampled in moving blocks of 5 consecutive start years, with replacement, until the series is filled; the last block is cut to length (21 start years for Part 1, 17 for Part 2).
  - Each draw resamples start years for all states (or all Wisconsin pieces) jointly, because the housing cycle is national.
  - The same draw scores L0 and the candidate, so the difference is paired.
  - 2,000 draws, seed 20261105.
- **Homes at a start year (audit 4).** Revised housing-unit estimates use later censuses, which a forecaster at the start year did not have. So homes at start year t are the most recent decennial census count at or before t (1990, 2000, 2010 or 2020), plus permits issued since that census. A census counts only from the year after its census year, when its counts were published (audit note b). So start year 2000 uses 1990 plus permits for 1991–2000, and likewise for 2010 and 2020. Demolitions are not subtracted (a stated bias: homes are slightly over-counted late in each decade). No intercensal estimates are used.

## Part 1: the level

**Data.** Census state permit files, 1990–2025, for all 50 states and DC (Wisconsin's are on disk; the others are fetched from the same Census URL). Decennial census housing units by state, 1990, 2000, 2010 and 2020 (Census API; 1990 from the Census 1990 summary file if the API lacks it).

**Region tags (Ryan, 2026-11-05 16:49 UTC).** Every state row keeps its Census region (4) and division (9), taken from the codes in the state permit files themselves. Wisconsin is Midwest, East North Central. The tags go into every Part 1 output file, so later matching can group by region. In this round they are used only to report scores by region and division, and not to pick.

**Start years.** 2000 to 2020: 21 start years. The periods overlap, so they hold about four independent five-year periods per state.

**Building sizes (audit 3).** Every candidate predicts each building size's state total on its own. The five-year all-sizes total is their sum.

**Candidates.** Each uses data up to the start year only.

| Id | Candidate | Idea |
| --- | --- | --- |
| L0 | Flat 3-year average (current) | — |
| L1a, L1b, L1c | Flat 5-, 7- and 10-year averages | 1 |
| L2 | Long-run permits per existing home (all years from 1990 to the start year) × homes at the start year | 1, 4 |
| L3 | Partial pull back: 3-year level × (L2 level ÷ 3-year level)^b, with b in [0, 1] fitted per the no-look-ahead rule by least mean \|log ratio\| on a grid of 0.05 | 4 |
| L4a, L4b | Straight-line trend over the last 10 years, and over all years from 1990 (least squares, extended five years; a negative fitted year counts as its fitted value, not 0) | 1 |
| L5 | Division pool (D6): the state's 3-year permits per existing home, blended with its Census division's 3-year permits per existing home (all states in the division, Wisconsin included) by weight w in [0, 1], fitted per the no-look-ahead rule by least mean \|log ratio\| on a grid of 0.05, × the state's homes at the start year | 6 |

**L5 details (audit, 17:08 UTC; written in before any fetch, not a re-lock).**
- **Division rate:** pooled. That is the division's permits over the 3 years ÷ the division's homes at the start year, per year.
- **w:** one value for all states, weighted toward the state's own rate. Its rate is w × own + (1 − w) × division.
- **Building sizes:** the blend is done for each size. One w is shared across sizes and fitted on the all-sizes score.
- **Units:** the five-year total = yearly rate per existing home × homes at the start year × 5.
- **At w = 1:** L5 is the state's own 3-year rate × homes. This differs a little from L0 because homes grow between the 3-year window and the start year, so L5 at w = 1 is not L0.

**Score.** For each state and start year, |log(predicted ÷ actual)| for the five-year all-sizes total. The score is the mean over states and start years. Lower is better: 0.10 means about 10% off. Also reported:
- bias (mean log ratio);
- the crash start years (2005–2009) on their own;
- each building size on its own;
- each Census region and division;
- Wisconsin on its own.

**Pick rule (D1, D2: option B).** A candidate replaces L0 only if all three hold:
1. its all-states score is at least 2% below L0's;
2. the 90% paired-bootstrap range of (candidate score − L0 score) lies entirely below 0;
3. it is not worse than L0 on Wisconsin alone by more than 5% of L0's Wisconsin score.

If more than one passes, the lowest all-states score wins. A tie, meaning scores within 0.001, goes to the simpler candidate in table order. If none passes, L0 stays.

**Reading line (audit).** There are 8 challengers (L1a, L1b, L1c, L2, L3, L4a, L4b, L5), so the chance that one passes by luck is higher than with a single challenger. The 90% range rule applies to each candidate separately. The rule is not changed.

**Range (audit 3).**
- **Method.** The range is redone with the winning level method's own out-of-sample errors. For each building size, it is the 10th to 90th percentile of predicted ÷ actual over Wisconsin's start years. It targets 80% coverage: in about 8 of 10 five-year periods, the outcome should land inside it.
- **Coverage check, as TOD did.** For each Wisconsin start year t from 2005 to 2020, the range is rebuilt from start years s ≤ t − 5 only. The check records whether t's actual total landed inside.
- **If coverage falls short.** If out-of-sample coverage is below 80%, the percentiles are widened in steps of 5 points (5th–95th, then 2.5th–97.5th) until it reaches 80%, and the widening is reported. Stop rule (audit note a): if 2.5th–97.5th still covers under 80%, it is used and the shortfall is reported. With 16 checks, coverage moves in steps of 6.25 points.
- **Sensitivity.** An all-states version of the range is shown alongside.

## Part 2: the shares

**Data (to fetch).**
- Census place permit files for Wisconsin, 1990–2014 (Midwest region files; they exist back to 1980).
- Census county permit files, 1990–1999 (2000–2025 are on disk).
- Piece-level homes for S3: decennial census housing units by county subdivision for 1990, 2000, 2010 and 2020 (Census API; 1990 from the 1990 summary file). Homes at a start year follow the shared rule above.
- The Milwaukee property-file fix is carried back to 2000. Before 2000, Milwaukee's apartment years stay as Census published, and this is labelled.

**Units counted.** The estimate columns (reported values plus Census imputation for unreported months), as in the current baseline. A row with 0 months reported in a year is missing, not zero.

**Linking 1990–2014 rows to today's pieces (audit 5).** Rules, applied in order:
1. **Same ID.** The 6-digit Census permit ID appears in 2015–2025 files: the row goes to that ID's piece or pieces, split across counties as now.
2. **Same name.** The same county with the same name and type (city, village, town): the row goes to that piece.
3. **Changed type.** The same county and the same base name, with a different type (a town that became a village, for example Fox Crossing village, formed from the town of Menasha in 2016): the row goes to the successor.
   - If the old town still exists beside the new village, the old row is split between them by their shares of current one-unit detached homes. This is an assumption, and it is listed. Using today's homes is a small look-ahead (audit note c).
4. **Unlinked.** The row's units go to its county's unallocated row.

Every rule-2, rule-3 and rule-4 case is listed in a link table before any score.

**Annexation.** Permits stay with the place that issued them that year. Old boundaries are not rebuilt. So a city that annexed land shows its later growth, and the town that lost land shows its decline. This is a stated limitation, and it favours candidates that use recent years.

**Pieces with no history** (incorporated later, or with no rows): years before they exist are missing, not zero. A candidate needing more years uses the years available. A piece with none takes its county's rate per 1,000 homes, as in the v3 fill.

**Coverage check (before any score).** A year is used only if the units linked to pieces (rules 1–3) are at least 95% of Wisconsin's state-file units that year (estimate columns, as published, before the Milwaukee fix). Years that fail are dropped and listed. Start years then follow from the years left.

**Start years.** 2004 to 2020, or fewer if the coverage check drops years.

**Candidates.** Each gives every piece a share of each building size's state total.

| Id | Candidate | Idea |
| --- | --- | --- |
| S0 | Own 3-year share (current) | — |
| S1a, S1b | Own 5- and 10-year shares | 3, 5 |
| S2a, S2b | County pace over the last 3 years (S2a) or the last 10 years (S2b), split within the county by each piece's own 10-year share (audit 6) | 2 |
| S3 | Shrink: each piece's 3-year rate per 1,000 homes, blended with its county's 3-year rate by weight n ÷ (n + k), where n is the piece's homes at the start year and k is fitted per the no-look-ahead rule on a log grid from 10 to 100,000 homes | 4, 5 |
| S4 | Lumpy-year cap: in a 5-year window, each year counts at most 2 times the piece's average of its other 4 years (3 times as a sensitivity) | 5 |

**Score.** Each candidate's shares are scaled to the actual state total, so only the split is tested. The score is the sum over pieces and building sizes of |predicted − actual|, divided by actual units: the error in homes per home permitted. Results are also reported separately for pieces with at least 1,000 homes and for those with fewer.

**Pick rule (audit 9).** Two parts: a candidate replaces S0 only if its score is at least 2% below S0's and the 90% paired-bootstrap range of the difference lies entirely below 0. There is no third check, because this part is Wisconsin only. Ties and "none passes" are handled as in Part 1.

**Reading rule (audit 8).** Part 2's 17 overlapping start years hold about 3 independent five-year periods. A "none passes" result there is likely to be uninformative: it means the test could not tell the candidates apart, not that S0 is best.

## Joint check (audit 10, reported only)

The winning level × winning shares is scored on Wisconsin pieces for start years 2004–2020, against L0 × S0. It uses the Part 2 score, without scaling to the actual total. This is reported and is not used to pick.

## Other states (idea 6)

- Part 1 uses every state, so Wisconsin's level is chosen on all states' history.
- Parking's no-reform model (`docs/parking/NO_REFORM_MODEL_RESULTS.md`): boosted trees on 9,109 US places, about 114,000 for Wisconsin over 2027–2031. **For scale only (audit 11).** It is not rerun and not a candidate.

## Not in this round (D4)

The tutor's version of idea 4 used parking's method 3 level score as the shrink target. That score was trained on repeal places across the US, not on Wisconsin towns. S3 tests the same idea with a county target instead. The method 3 version can be a second round if S3 passes.

## Rules

- Scripts are committed before any run, and the lock time is recorded here.
- The fetch script gets its own audit check before it runs (audit note e). It must send a plain user agent, read any Census key from the environment only, and write nothing that contains the key.
- Runs stay on Ryan's Mac. Long runs are detached with checkpoints.
- The audit reviews this lock and the results.
- A change to the tool needs Ryan's own OK.
- Sources: Census permit files, Census decennial counts and the City of Milwaukee property file are all already used in the baseline. The Census files are public domain.
- Any change is reported with its effect on each scenario:
  - **ADU:** the 124,000 denominator in the shared comparison.
  - **TOD:** station-area baselines and the combined view.
  - **Parking:** shares, and its bundle and combined bundle rebuilds.

## Ryan's choices (17:07 UTC: all as recommended, with D6 tested now)

| Id | Choice | Options | Recommended |
| --- | --- | --- | --- |
| D1 | Which history chooses the level | All states with a Wisconsin check, or Wisconsin only (21 start years) | All states: Wisconsin alone holds about 4 independent periods |
| D2 | What a challenger must clear to replace the current rule | A (first draft): 10% better, and better in at least 80% of bootstrap draws. B (as in method 3b): at least 2% better, and the 90% bootstrap range of the difference entirely below 0 | B. A's 80% is weaker than earlier locks (method 3: 5% margin; method 3b: 2% plus a 90% range below 0) |
| D3 | Split level and shares, or pick one method for both | Split, or one method | Split, with the joint check reported |
| D4 | The tutor's method 3 shrink | Leave it for a second round, or include it now | Second round |
| D5 | Other fixed numbers | 5% Wisconsin check; 95% linking coverage; 2-times cap (3 as sensitivity); 1,000-home split for reporting; 80% range target | As written. Reasons: 5% and 2-times are the smallest round steps we would act on; 95% keeps the linking error under the Milwaukee fix's size; 1,000 homes matches parking's place rule; 80% matches the current 10th–90th range |
| D6 | Test region now? | Add a named region candidate before the lock (for example, each state's level pooled with its Census division), or leave it to round 2. Adding it after results would be post hoc | Recommended round 2; **Ryan chose to test now: candidate L5** |

## Plan log

- 2026-11-05: draft written (b1fd4255). Not locked.
- 2026-11-05 16:50 UTC, audit review: not cleared, 11 items. Revision 2 addresses them:
  1. Fitted numbers use start years s ≤ t − 5; fit years from 1992; same scored start years for all candidates.
  2. Moving 5-year blocks, joint across states, paired.
  3. Level by building size; 80% target; out-of-sample coverage check with a widening rule.
  4. Decennial count plus permits; no revised estimates; 1990–2020 county-subdivision source named.
  5. Linking rules 1–4, annexation, no-history pieces, estimate columns, and the 95% denominator named.
  6. S2 split into 3- and 10-year versions.
  7. D2 options added; D5 lists the other fixed numbers.
  8. Part 2 reading rule.
  9. Part 2 rule reworded as two-part.
  10. Joint check, reported only.
  11. Parking row marked "for scale only".
- 2026-11-05 16:49 UTC, Ryan: track each state's region so matching can group by it later. Census region and division are tagged on every state row and output, and used for reporting only.
- 2026-11-05 16:51 UTC, audit: revision 2 cleared to lock once Ryan picks D1–D6. Notes a–e written in: widening stop rule; census used from the year after its census year; look-ahead noted in rule 3; D6 for region; fetch script audit check.
- 2026-11-05 17:07 UTC, Ryan: "okay, including D6". Read as OK to D1–D5 as recommended (all states; option B; split; method 3 shrink in round 2; fixed numbers as written), with region tested now. L5 added; pick rules written out for option B.
- **LOCKED 2026-11-05, commit time of this revision.** Before any fetch or count.
- 2026-11-05 17:08 UTC, audit accepted the lock (c4045967). Written in, not a re-lock: L5's five details (pooled division rate, one w, per size with a shared w, units, the w = 1 note) and the 8-challenger reading line.
- 2026-11-05, fetch script written (`scripts/fetch_baseline_bakeoff.py`, not run). Sources named for the 1990 counts, since the Census API has no 1990 decennial data: state housing units from ST-98-51 (the April 1, 1990 census count as revised and published in 1999, a small labelled leak), and Wisconsin county subdivisions from the 1990 P.L. 94-171 file. Waiting on the audit's check of the script.
- 2026-11-05, fetch done (44 files logged; the 1990 PL94 housing-unit field is HU100). Before any Part 1 count, three clarifications:
  - **Ratio direction.** The range multipliers are actual ÷ predicted, as in the current baseline's `long_run_ratios.csv` (an outcome = central × multiplier). The earlier "predicted ÷ actual" wording in the Range section was a slip.
  - **Wisconsin 2027–2031 reporting.** Each candidate is run at start year 2025 on the published state files. It is reported as its ratio to L0 at 2025, times the v3 central of 124,000, so v3's Milwaukee and fill corrections are kept. The raw published-file figures are shown beside it.
  - **Range start years.** For each candidate, these are every Wisconsin start year from 1992 (or the first year its window allows) to 2020.
- 2026-11-05, Part 2 linking, done before any Part 2 score (`scripts/build_baseline_bakeoff_links.py`; `reference/baseline_bakeoff_links.csv`, `_link_coverage.csv`):
  - **Rule 1 changed (pre-score).** The 6-digit permit IDs are not stable across eras (Abbotsford is 000200 in 1990 and 001000 from 1999), so IDs are not used to link. Every row instead goes through the foundation crosswalk (`foundation/crosswalk.py`), in order: FIPS MCD code (2007–2025 files carry it); place code; name in county (full name, then base name for a changed type); documented aliases. This is the lock's rules 2–4, with codes where they exist.
  - **County "Part Unincorporated Area" rows** (present in every year) are split each year among the county's towns with no own row that year, by today's one-unit detached homes. This is the foundation method, and it carries the same look-ahead as rule 3.
  - **Name cleaning.** Footnote marks (@n, (N), #) are dropped. The 1990–2006 files list cities with no type word, so a name without a lower-case type word is read as a city.
  - **Eight renames,** checked by hand against TIGER 2024 because the base-name rule would pick a wrong successor:
    - Menasha town → Fox Crossing village;
    - De Pere town → Ledgeview town;
    - Salem town → Salem Lakes village;
    - Pewaukee town → Pewaukee city;
    - Waukesha town → Waukesha village;
    - Brokaw village → Maine village;
    - De Forest → DeForest;
    - Buffalo city (1990–91) → Buffalo City city.
  - **Result.**
    - 14 towns link to the villages they became (for example Greenville, Lisbon, Richfield).
    - One identity is unmatched: Brokaw village 2007–2020, 21 units, which goes to the unallocated row.
    - **Coverage passes in every year, 1990–2025.** Linked units are 99.9% to 100.7% of the state file, except 1991–1993, where the place files themselves sum to about 5% more than the state file (105.0%, 105.1%, 104.9%). Part 2 scales shares to the state total, so this does not enter the share score.
- 2026-11-05, Part 2 written before any Part 2 score. Clarifications:
  - **Rows with 0 months reported.** They keep Census's imputed estimate, as v3 does. "Missing" applies to a piece with no row that year, and to Milwaukee's flagged years.
  - **Pieces with no outcome year.** A piece with no row in any outcome year is left out of that start year's score, and scaling uses the pieces scored.
  - **1,000-home split.** It uses today's ACS homes.
  - **S2's split.** It falls back to homes when a county had no permits in 10 years.
  - **The joint check.** It uses Part 1's published-file level, without the Milwaukee fix, against piece outcomes that include the fix. This is a small mismatch in a reported-only check.


# Parking placebo test: plan written before running

Written 2026-10-27 by the parking conductor, after Ryan asked whether control cities could add confidence. The plan is fixed before any placebo is computed.

## Question

How large an "effect" does the comparison method find in places that never removed their parking minimums? Is the real average (−1.10 permits per 1,000 existing homes per year, 71 places) distinguishable from that?

## Method

1. **Pool of placebo places:** Census permit places with no Parking Reform Network record of removing residential minimums citywide (rated at or near, any status). They must have ACS homes and complete permit years for their window.
2. **Placebo sets:** 500 sets, seed 20261027. Each set has 71 placebo places. Each is matched to one real repeal place and gets:
   - the same state;
   - a population within half to twice the real place's;
   - the real place's repeal year and number of after-years.

   Where a state has no eligible place in that window, the real place is skipped in that set and the skip is counted.
3. **Calculation:** each placebo place gets the exact effect calculation used for the real places: same comparison-place rules (excluding itself), same windows, same homes × after-years weight.
4. **Outcome per set:** the weighted average effect.

## What is reported

- the distribution of the 500 placebo averages (5th, 50th and 95th percentiles);
- where the real average −1.10 falls in it, as the share of placebo averages at or below −1.10;
- the spread of single placebo places' effects against the spread of the real places' effects. If they match, the place-to-place differences are noise;
- whether the 90% range from the placebo spread, centred on the real average, is narrower or wider than the current range (−3.50 to +1.54). A change to the tool's high end would go to Ryan as a decision.

## Changes after writing

- **2026-10-27, before running (for computing time):** for each real place, up to 20 eligible placebo places are drawn once, with the same seed, and their effects computed once. Each of the 500 sets then draws one of those 20 at random for each real place. The sets and the reported statistics are otherwise as above.
- **2026-10-27, after the first run (owner request):** a second run uses every eligible placebo place for each real place instead of 20, so the 500 sets draw from the full pool and overlap less. Same seed, same rules otherwise (`--full`; outputs `reference/parking_placebo_full_*.csv`). The first run's files are kept.

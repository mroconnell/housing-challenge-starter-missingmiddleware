# Parking: Wisconsin permits after reform minus permits without reform, plan written before running

Written 2026-10-31 by the parking conductor. Ryan asked all three scenarios to run fast fit-and-fix rounds that give one statewide Wisconsin figure: permits after reform minus no-reform baseline permits, 2027–2031. After each run: check for errors and odd outliers, fix the code, rerun. No pass bars. No result below has been computed before this file was committed.

## Two routes, both reported

1. **Route A, the existing comparison (unchanged):** repeal places against similar places, before and after. It gives a central of 0 and a high end of +1.49 per 1,000 existing homes per year, which is 19,937 homes over 2027–2031.
2. **Route B, the no-reform model with reform as a dated trait:** the round 3 no-reform model (`NO_REFORM_MODEL_RESULTS.md`), refit with a trait "material parking repeal took effect just before the outcome years".
   - **Net for Wisconsin:** each Wisconsin place's predicted permits with the trait on, minus with it off, from origin 2025 (outcomes 2027–2031), summed over the places without minimums today. Then scaled up to the whole state by the same ratio as the baseline: 122,619 ÷ the sum of M0 over the model's places (118,822 as the as-published sensitivity).

## Route B rows

- **No reform (trait 0):** as in the no-reform model.
- **Reform (trait 1):** a place with a material repeal (V7 coding) dated from 1 year before the origin to 2 years after it. Its feature years are then all or mostly before the repeal, and its outcome years (2–6 after the origin) are all after.
- **Left out:** every other reformed row, including undated reforms and state laws.

## Models

- **M4** (boosted trees) and **M3b** (regression with ACS traits), with the round 3 settings.
- **M0 + flat effect:** same pace, plus the average with-minus-without from route A. This is route A in route B's units, as a check.

## Scores and checks

- **Held-out reform places:** 20% of the reform places in each seed, which are never fitted. Their actual outcomes are scored with the trait on and with it off (median |log|, total ratio). If "on" scores better, the trait carries real information.
- **Noise floor:** the fake-reform placebo from the no-reform model, applied to Wisconsin the same way. A real net that sits inside the fake one is noise.
- **Range:** 5 seeds × 20 resamples of reform places (refit each time), with the 5th to 95th percentile of the Wisconsin net.
- **After each run:**
  - the 10 Wisconsin places with the largest net, traced;
  - reform rows with outcomes outside the national 1st–99th percentile;
  - the worst miss on held-out reform places.

## Use

- **The tool's numbers do not change without Ryan's approval.**
- Route B's net and range are set beside route A's 0 and 19,937. They go to Ryan and to the audit through the coordinator.

## Changes after writing
- **2026-10-31, Ryan (before running):** after each run, check for errors and odd outliers, fix the code and rerun. Stop when a round has no errors and every outlier is explained and verified.
- **2026-10-31, round 1 checks → round 2 fixes (before round 2 ran):**
  - **Coding error:** the scale from model places to the whole state used one year of same-pace permits where it needed five. Every round 1 net was 5 times too large.
  - **Coding error:** the fake reform was switched on at every origin of a fake place. A real repeal is on at only 1 or 2 origins. So the trees could learn place identity, and the noise floor was inflated. The fake now uses the same window around a fake year drawn from the real repeal years.
  - **Data note:** only 29 reform places (60 rows) have a dated, apartment-scale repeal that falls inside the window, outside Wisconsin. The route is thin, and that is stated.
  - **No-reform round 4 (leak fixed) moves the trees' baseline side case** from 114,042 to 124,582 (1.016 times same pace). The leak had pulled it down.
- **2026-10-31, round 2 checks → round 3 (before round 3 ran):** round 2 had no coding errors. Two things are not yet traced: the held-out reform places' worst misses, and why the trees' fake-reform net is 0 for most seeds but up to about 21,000 for one. Round 3 adds both traces and changes nothing else. The regression (M3b) is reported but not used: its real net (−25,000) and its fake net (−17,000 to +35,000) swing as widely as in the no-reform model.
- **2026-10-31, round 3 checks → round 4 (before round 4 ran):**
  - **Coding error:** the fake-reform years were drawn while looping over a Python set. Its order changes from run to run, so the fake nets were not reproducible: round 2's trees fake net was 5,778 on average, and round 3's was 1,984, from identical code paths. The real nets are not affected; they were identical in rounds 2 and 3. The loop is now sorted, in this script and in the no-reform model's placebo.
  - **Outliers traced in round 3:**
    - The held-out reform place with the largest miss is San Francisco, origin 2018. 1,689 homes a year were permitted against a same pace of 4,590, a real post-2018 collapse. Minneapolis (2021 repeal, with the 2040 plan) and Hayward also came in below same pace.
    - The largest Wisconsin net is Madison: −2.2 homes a year, out of 2,938 a year at same pace (0.07%).
  - Round 4 reruns both scripts with the sorted loop. No other change.
- **2026-10-31, round 4 checks → round 5 (before round 5 ran):**
  - **Round 4 had no coding errors.** It was rerun with a different Python hash seed and gave identical results: the fake nets are now reproducible.
  - **One outlier is not yet verified.** The trees' fake-reform Wisconsin net is 0 in 3 seeds, but about 10,500–10,900 homes in 2 (seeds 20261033 and 20261034). Round 5 records, for each seed, how the fake-reform rows' change in permits compares with the rest's, and which fake places grew fastest. Nothing else changes.
- **2026-10-31, round 5 checks → round 6 (before round 6 ran):**
  - **Fake-reform outlier, seed 20261034, explained:** its fake rows grew 32.8 more permits per 1,000 homes per year than the rest (+32.78 against +3.05). Most of the gap is Hardeeville, SC (+542, +462, +389). It is a real boom, enlarged by a stale population (see the no-reform plan, round 5). The trees learned "fake = fast growth".
  - **Seed 20261033 is not explained by the plain average** (−0.32). Round 6 adds the home-weighted average.
  - Round 6 uses the no-reform model's round 5 data.
- **2026-10-31, round 6 results and audit checks → round 7 (before round 7 ran):**
  - **Round 6 (trees), Wisconsin net 2027–2031:** median 0 (57% of 105 runs exactly 0), mean −1,024, 5th to 95th percentile −5,438 to 0. The fake-reform range is −3,148 to 6,095.
  - **Fake-reform seeds explained:** home-weighted, the fake rows in seeds 32–34 grew 1.3–4.0 more permits per 1,000 homes per year than the rest. In seeds 31 and 35, they grew 1.2–1.3 less. The trees follow that sign.
  - **Audit checks on round 6 data:** homes varied by origin in 98.9% of places, and Madison's homes rose by exactly its origin-year permits. But 107 places jumped more than 3× where the source switched (Milwaukee ×13.5), because the permit file's population is unreliable. Round 7 uses ACS homes from the release ending at each origin (no-reform round 6).
  - **Held-out misses by log error:**
    - Ecorse, MI: predicted 12 a year, actual 0. Its permits were 198 in 2017, 59 in 2019, then 0 every year to 2025.
    - Hartford, CT: predicted 90, actual 7. Its permits were 5–11 a year, with one spike of 141 in 2023.
    - Both are lumpy small series, not data errors.

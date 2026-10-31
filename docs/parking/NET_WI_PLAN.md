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

# Baseline range, county test of the LASSO's tight ranges (LOCKED 2026-11-05)

Written 2026-11-05 by the baseline thread. Ryan: "yeah! Run it on counties" (20:56 UTC). Status: **draft, for the audit's review.** Ryan's go is given, so it runs once the audit clears it and the script is committed.

## The question

At the state level, the recalibrated LASSO range (E2, round 4) gave a range as tight as Wisconsin's 2027–2031 range only 7 times, and it held 3 of them. That is too few to know its coverage at that width.

This test asks: **when E2 gives a tight range, does it hold about 90% of the time?** It uses US counties, which give thousands of checks in place of 7.

**Not a pick.** This round does not choose a baseline range. It tests whether E2's tight ranges can be trusted. It is *post hoc*: the question came from round 4's results.

## Data

- **Census county permit files, 1990–2025.** These are national files, already on disk:
  - `data/raw/baseline_bakeoff/bps_county/co1990–1999a.txt`;
  - `data/raw/census_bps_cbsa/co2000–2014a.txt`;
  - `data/raw/census_bps_county/co2015–2025a.txt`.
- **No new download.** Counties are keyed by state and county FIPS.
- **Counties included at a start year:** those with at least 900 permitted units over the 3 years to that start year. This keeps out counties whose ratios are dominated by single projects. The cut-off is a convention, not from evidence. The number of counties is reported after the run.

## Design (as round 4's E2, with counties as units)

- **Unit:** a county. Its ratio r is actual ÷ predicted five-year all-sizes total, where L0 is the flat 3-year average.
- **Leave one state out.** All counties of the target state are held out together, so that neighbours do not share information. Training is the counties of the other 50 states, with start years s ≤ t − 5.
- **Traits, from data up to t only:**
  - swing (standard deviation of log annual permits, 1990 to t);
  - log level (log of the 3-year average);
  - tilt (log of the 3-year ÷ 10-year average);
  - apartment share (5+ units, 3 years);
  - own past miss;
  - Census region.
- **No homes data.** "Pace per 1,000 homes" is replaced by log level, so no housing-unit file is needed.
- **E2 exactly as round 4:**
  - target log(max(|log r|, 0.02));
  - `LassoCV(alphas=100)`, inner GroupKFold(5) by state;
  - out-of-fold GroupKFold(10) by state;
  - a 1st–99th cap;
  - c is the narrowest value on a 0.05 grid with at least 90% out-of-fold coverage.

  These settings are conventions, as before.
- **A (all counties pooled), the benchmark:** the narrowest symmetric quantile pair with at least 90% inner leave-one-state-out coverage.
- **Check years:** 2009–2020 (main), with 2005–2020 also reported.

## What is reported

1. **E2's coverage by width bin:** the log width of the range in four bins, ≤ 1.1, 1.1–1.3, 1.3–1.5 and > 1.5. The bin edges are conventions; the 1.1 edge was chosen after seeing Wisconsin's 1.03 (audit 2). Each bin shows:
   - the number of checks;
   - the number of distinct counties;
   - the number of distinct states;
   - coverage, with a 90% bootstrap range. The bootstrap resamples states with all their counties, crossed with 5-year blocks of start years: 2,000 draws, seed 20261105.
2. **E2 and A overall:** coverage and mean and median width.
3. **Wisconsin's counties:** coverage for E2 and A.

## Reading rule (fixed before the run)

For E2's tightest bin (log width ≤ 1.1, where Wisconsin's 2027–2031 width of 1.03 falls):
- **Consistent with 90%:** the 90% bootstrap range includes 90%. If that range is wide (more than 20 points, for example 70% to 100%), the test is weak even though it is consistent.
- **Below 90%:** the range is entirely below 90%. Then E2's tight ranges are over-confident for counties. That says nothing on its own about A for Wisconsin.
- **Above 90%:** the range is entirely above 90%. Then E2 is too wide even when it is tight.
- **Too few:** the bin has fewer than 100 checks, or covers fewer than 10 states. Then the test cannot say.

The 100-check minimum, the 10-state minimum and the 20-point "weak" mark are conventions (audit 2).

Counties are not states: they swing more and share state-level shocks. So this result informs the state-level choice, but it does not settle it.

## Rules

- The script is committed before the run, and runs stay on Ryan's Mac.
- Nothing in the tool changes from this test. The choice of range is Ryan's.

## Plan log

- 2026-11-05: draft.
- 2026-11-05 20:58 UTC, audit: cleared once items 1–6 are in. Items 1–5 are written in, and the script is committed with this lock (item 6). LOCKED.


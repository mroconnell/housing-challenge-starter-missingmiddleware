# Chicago "L" ridership after transit-area upzoning: plan written before looking

Written 2026-10-27 by the TOD conductor, at the owner's request ("Yes run that"), before any station ridership has been tabulated against the rezonings. The commit that adds this file is the timestamp. Any later change goes in section 7 with a date and a reason. Data source: [research/RIDERSHIP_DATA.md](research/RIDERSHIP_DATA.md).

## 1. Question

Did ridership at Chicago "L" stations whose surroundings were upzoned under the 2013 and 2015 TOD ordinances change differently from ridership at similar stations whose surroundings were not upzoned? Does the change grow with the amount of upzoned land, or with the homes later permitted near the station?

## 2. Data

- **Ridership:** CTA "L" station entries, daily, from the City of Chicago data portal (CTA ridership, "L" station entries daily totals), 2009–2019.
  - Years from 2020 on are excluded, because the pandemic changed ridership everywhere.
  - Fetched by script with a manifest.
- **Upzoned land and homes permitted:** the Chicago station-area units already built for the trait test (`reference/tod_case_units.csv` and the Chicago case code). For each station:
  - treated eligible acres;
  - added floor area;
  - homes permitted near it, 2009–2019.
- **Station locations:** the CTA "L" stops dataset on the same portal.

## 3. Groups

- **Treated stations:** stations whose ½-mile area holds at least 5 eligible acres of land upzoned by the ordinances, the same rule as the trait test.
- **Comparison stations:** all other "L" stations with entries in every year 2009–2019.
- **Dropped from both groups:**
  - stations opened, closed or rebuilt in the window;
  - Red Line South stations, closed May–October 2013;
  - Loop stations where entries mix transfers.

  The list of dropped stations is written into the results before any comparison is computed.

## 4. Outcome and periods

- **Outcome:** average weekday entries per station, by calendar year. The main measure is the logarithm (percentage change); the change in entries is shown too.
- **Before:** 2009–2014. **After:** 2016–2019. 2015 is the change year, shown but not used.

## 5. Estimates

- **Main:** the difference-in-differences of log average weekday entries, treated against comparison, after against before.
- **Dose:** the change in log entries for each station, regressed on its treated acres, and separately on homes permitted near it, 2016–2019, per 1,000 existing homes.
- **Uncertainty:** 90% intervals from resampling stations, 2,000 draws, seed 20261027.
- **Sensitivity cases, fixed now:**
  - Saturday plus Sunday entries instead of weekdays;
  - leaving out the 5 busiest stations;
  - 2013 as the change year (the first ordinance).

## 6. How it is used

Context for legislators and for the "Why" screen: whether upzoning near transit went with more riders in a Midwestern city. It does not change any housing number. Chicago stays a held-out case for the housing model; this ridership test does not refit anything.

## 7. Changes after writing

None yet.

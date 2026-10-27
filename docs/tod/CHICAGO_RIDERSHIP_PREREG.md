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

Recorded 2026-10-27 while running the test (results: [CHICAGO_RIDERSHIP_RESULTS.md](CHICAGO_RIDERSHIP_RESULTS.md)). Items 1 to 9 were fixed before any comparison was computed; items 10 and 11 were added after the main results were seen.

1. **"Closed" made measurable** (reason: the plan names no rule). A station is dropped as closed if it had no entries on at least 7 days in a row in 2009–2019, or no entries in some year. This drops 13 stations with temporary closures (7 Red Line North stations closed about 40 days each in 2012; Wellington and Paulina in 2009; California and Damen (Blue) in 2014; Dempster-Skokie in 2015; Kimball 9 days in 2013), in addition to the plan's named groups.
2. **"Rebuilt" made concrete** (reason: rebuilds without a closure do not show in the entries). Stations rebuilt while open, from CTA project records: Wilson (2014–2018), Clark/Division (2013–2015), Grand (Red, 2012). Blue Line "Your New Blue" renovations that kept stations open were not counted as rebuilds.
3. **"Loop stations" read as every station inside the Loop**, elevated and subway (18 ids; reason: the plan does not list them).
4. **Repeated rows** (reason: data defect). The portal file repeats 618 station-days in 2011 with slightly different counts; each pair is averaged.
5. **Average weekday entries** are averaged over weekdays with entries above zero (reason: a zero is a closure day, not a ridership level).
6. **Station measures within ½ mile of the CTA station point** (average of its platform points): treated acres by parcel representative point; homes permitted counts all new-construction permits within ½ mile, not only those on eligible land; existing homes are 2010 census housing units. Circles of neighbouring stations overlap. Reason: the plan says "½-mile area" and "near it"; the trait test's own Chicago units split treated land by nearest station instead and were not reused.
7. **Dose regressions** use all kept stations (treated and comparison), ordinary least squares, one variable at a time. Reason: the plan does not say which stations.
8. **Resampling:** for the difference in differences, treated and comparison stations are resampled separately (group sizes fixed); for the dose slopes, all stations together. Reason: the plan does not say.
9. **Sensitivities:** "Saturday plus Sunday" uses the CTA's Saturday and Sunday-or-holiday day types; "5 busiest" means the 5 kept stations with the highest average weekday entries in 2009–2014; "2013 as the change year" uses 2009–2012 before and 2014–2019 after.
10. **Unplanned check, stations outside Chicago left out** (added after the main results; reason: the ordinances do not apply in Evanston, Skokie, Oak Park, Forest Park, Cicero or Rosemont, and permits there are not in the Chicago file). Reported separately; it does not replace the main estimate.
11. **Unplanned check, 2013 left out of the before years** (added after the main results; reason: during the 2013 Red Line South closure the CTA sent riders to Green Line South stations, 7 of which are treated; Garfield (Green) averaged 7,030 weekday entries in 2013 against 1,347 in 2012). Reported separately; it does not replace the main estimate.

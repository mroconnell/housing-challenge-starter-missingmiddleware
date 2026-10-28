# Parking: lot-level test, plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request, using TOD's lot table (`data/processed/tod_lot_model/lots.parquet`, 355,853 lots in 8 cities; plan `docs/tod/LOT_MODEL_PLAN.md`). No parking outcome has been computed from this table before this file was committed. Changes go in the last section with a date and a reason.

## 1. Question

On individual lots, did removing parking minimums make new homes more likely, especially on small or narrow lots? And does knowing a lot was covered by a parking reform help predict building on lots in a city the model has not seen?

## 2. Lots with and without the parking reform

| City | Lots with the reform | Comparison lots | Before | After |
| --- | --- | --- | --- | --- |
| Seattle (TOD's Mount Baker and North Beacon Hill/Othello units) | Inside a hub or residential urban village (2012 reform) | Outside the villages, in the same units | stored years up to 2011 | 2013 to the last stored year |
| Chicago | Within 402 m (¼ mile) of a CTA or Metra station (2015 ordinance) | 402–805 m from a station | 2009–2012, before the 2013 ordinance | 2016–2020 |

- **Left out:** lots TOD marks as upzoned (`treated = 1`), so the parking change is not mixed with an upzoning.
- **Not used:** Charlotte, whose 2019 parking change came with its TOD rezoning, and the other cities, which have no confirmed parking reform in their windows.

## 3. Outcomes

- **Built:** whether a lot got any new-homes permit in a year (from `permit_years`).
- **Units:** new homes permitted on the lot in a year.

Both are reported per 1,000 lots per year.

## 4. Tests

1. **Effect.** (After − before) for reform lots minus (after − before) for comparison lots, for "built" and "units".
   - 90% range: 2,000 bootstrap draws of 500 m grid cells.
   - Reported for each city, and pooled with each city weighted by its lots.
2. **Which lots.** The same effect for:
   - narrow lots (width under 10 m) and the rest;
   - small lots (under 0.1 acre) and the rest.
3. **Prediction on unseen cities.**
   - **Model:** gradient boosting predicting whether a lot is built in its after-years. Inputs: lot size, width, prior floor area, use, distance to station, homes on the lot, built before, tract rent, home value and income, and city. It is fitted with and without a "parking reform" flag.
   - **Training lots:** all lots except the held-out city's. The other cities' lots have the flag set to 0.
   - **Held out:** Seattle, then Chicago.
   - **Score:** the error in the predicted number of reform lots built, and the Brier score (the average squared error of the predicted chance a lot is built).
   - **Pass rule:** the flag passes if it lowers both scores by at least 5% in both held-out cities.

## 5. Use

- **If the flag passes:** the lot model, with the flag, is proposed to Ryan for predicting Wisconsin lots near transit.
- **If not:** the result is reported, and the tool keeps its range.

## Changes after writing

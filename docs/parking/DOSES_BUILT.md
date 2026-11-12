# Parking doses: built (2026-11-12)

Plan: `docs/parking/DOSE_PLAN.md` (Ryan's choices C1–C11 and the Audit fixes override the text above them).
Script: `scripts/build_parking_doses.py` (committed before any run: ed456961; later changes each committed before their re-run: b379c827, a1a01d17, 17370e1c, 406d4742).
Table: `reference/parking_doses.csv`, 112 rows. Coding inputs, verbatim: `reference/parking_dose_inputs.json`.
GIS layers and Census files: `data/raw/parking_dose/<reform_id>/` (git-ignored; each has `_sources.json`).

**No outcome was read.** No permit or unit count by place or year was opened, and no effect was computed.

## What a dose is

- Dose = 100 × the homes-weighted share of the housing parking requirement that this reform removed.
- Homes = 2020 Census block housing units, placed by block internal point (C10).
- Removal = (old − new) ÷ old spaces per home, standard 20-unit building (half 1-bedroom, half 2-bedroom).
- C4: where parts of a place were already exempt or reduced the day before, only the increment counts.
- `dose_units_2_4` = the dose, except Norman (70.60) and Milwaukie (0).
- `dose_sensitivity_mapped` = the mapped carve-out dose for Berkeley, Windham, Kingston and Carrboro.
- `coverage_homes_share_2010` = audit fix 5 check on 2010 blocks, for the ten 2015–2019 mapped rows.

## Counts (rows of the table)

| Dose source | The 74 | Other reforms | All |
|---|---|---|---|
| computable (both factors from data) | 64 | 19 | 83 |
| partly (one factor assumed) | 10 | 6 | 16 |
| fallback (C3 class dose) | 0 | 13 | 13 |
| **All** | **74** | **38** | **112** |

- C3 placeholder 50s: 1 row (Pomona 2024), and it is not the event (C9).
- The 74 citywide repeals, by dose (number of places):

| Dose | Places |
|---|---|
| 100 | 30 |
| 75 to under 100 | 25 |
| 50 to under 75 | 6 |
| 25 to under 50 | 9 |
| 0 to 25 | 4 |

- Lowest of the 74 (C4 increments): Albany OR 10.96, Ashland 11.61, Milwaukie 17.76, Central Point 22.93, Tualatin 27.98. Oregon's state transit rule (OAR 660-012-0440, from 2022-12-31) is the prior for 14 Oregon places.
- 5 of the 74 have an earlier exemption that was found but not mapped, so their 100 is an upper bound: Buffalo, Bastrop, Avondale Estates, Kalamazoo, La Crosse. Lansing KS, Northfield, Saranac Lake and Trenton have similar unconfirmed or PDF-only findings.

## Eligibility changes found

| Reform | Change |
|---|---|
| Spokane 2023 vs 2024 | **Event year not frozen.** C9 says 2023 (dose 91.48). Coordinator recommends 2024 (increment 8.52). Ryan to choose. |
| North Canton 2023 | Main Street exemption dates from 2021. Dose 0 (no change for housing). |
| Waukegan 2024 | Not commercial-only: citywide 2 → 1 per home plus B4 and L1–L3. Dose 50.48. |
| Lewisburg 2023 | Not downtown-only: borough-wide cut too. Dose 24.08. |
| Bloomsburg 2024 | Mostly not new (old C district had no parking). Dose 1.17. |
| Albany NY 2017 | Date confirmed (USDO effective 2017-06-01). Dose 49.76, all from the small-lot exemption. |
| Fremont 2015 | **Event is 2014** (Ord. 28-2014, 9-9-14; the 2015 Ord. 16-2015 left the parking table unchanged). Not eligible. |
| Portland OR 2018 | Pre-reform Title 33 ch. 33.510 (7/8/16, Wayback 2017-01-31) shows no minimums in every Central City area: dose 0 kept. |
| Honolulu 2017 | Parking cut was 2020 (Ord. 20-41), not 2017. |
| Shoreline 2022 | Likely fails the optional-reduction screen. |
| Saranac Lake 2016 | A 2024 letter says minimums stayed for new housing. Marked unsure. |
| Hartford 2017 | Old minimum is 1.5 per home in the code, not the universe's 1.0. |
| Hampden, Portsmouth OH | PRN dates 2023, universe 2022. Not changed. |

## Audit rulings applied (2026-11-12)

**Wayback captures.** All 69 are listed in `reference/parking_dose_wayback_audit.csv` (URL, capture date, sha256, use, side of the reform date).
- 58 on the right side, 10 on the wrong side, 1 not available (Berkeley, never read).
- Changed:

| Reform | Dose before | Dose now | Why |
|---|---|---|---|
| Albany NY 2017 | 49.76 | 10 (fallback) | New rule only from a pre-adoption draft; its layer is also "illustrative only" |
| Portland ME 2024 | 18.4 | 100 | Transit prior used route data captured after the reform |
| Salem 2023 | 35.87 | 79.77 | Frequent-corridor prior used a feed captured after the repeal; downtown district and the 1-per-home cap kept |
| Hudson 2019 | 100 | 100 | Schedules captured after the reform; no prior was coded |

- Wrong side but kept, with the reason in the row: Binghamton (file stamped 2023-12-29 and linked from a pre-reform page; switching gives the placeholder 50), Bangor, Avondale Estates, Pomona 2019.

**Full text read** (no longer search extracts): Durham (UDO as amended 2023-10-16), Hanover (Zoning Ordinance 2022 and 2023), Boise (legacy Title 11, 2017 edition). All coded values confirmed. Durham's repeal took effect 2024-01-01; event year kept at 2023 (adoption).

**New columns.**
- `dose_if_unlicensed_refused`: the row's fallback dose if Ryan refuses layers with no stated licence (citywide repeals fall back to 100). 53 rows would change.
- `dose_state_law_prior`: state transit laws counted as prior everywhere.
  - San Jose 99.55 → 44.89 (Caltrans current major stops; the helper's 52.02 used another layer).
  - Tigard 99.01 → 43.23 (Oregon rule).
  - Bakersfield 84.85 → 84.26.
  - Sacramento already counts AB 2097; Corvallis's repeal took effect the same day as the Oregon rule. No other row is affected.

## Blocked (cited, not worked around)

- parkingreform.org (403, every place tried); ecode360.com (403); codelibrary.amlegal.com (403); municode API (Cloudflare).
- City sites: Boise clerk (Cloudflare), Bakersfield code (403), Binghamton (whole site 403), Pomona (403), Spokane (403), San Jose records (403), Alameda (403), Roanoke documents (403), Durham code and documents (403/Cloudflare), Gainesville LDC (403), Ashland code (403), Tigard news (403), La Crosse GIS (Cloudflare and Access Denied).
- transitfeeds.com (403); Wayback copies used for old GTFS and code text instead.
- News: berkeleyside (429), southernminn (429), others 403.
- No accounts, records requests or clerk requests were made.

## Needs Ryan's OK

1. **Spokane event year** (above). The freeze waits on it.
1a. **Binghamton:** keep 20 (wrong-side capture explained) or use the placeholder 50?
1b. **Hanover rounding:** building total (35 spaces, as coded) or per home (40; priors 0.625 and 0.75)?
2. **Layers with no licence stated:** 60 of 112 rows name one; 53 of them would change dose if refused (`dose_if_unlicensed_refused`).
3. **State laws as prior:** Sacramento counts AB 2097 (47.61). San Jose does not (99.55; 52.02 if it did). Tigard leaves out the state rule (99.01; 43.23 if in).
4. **Choices with big effects:** Albany OR follows city staff (10.96; strict rule 97.04); Oregon 1-per-home cap counted as prior; Raleigh frequent-transit stand-in (58.88; 81.77 without); Hanover discretion (42.71 or weak repeal 15).
5. **Assumptions:** Pomona 4 storeys; Berkeley C-DMU 0.75; Boise C-5 for old P-1; Albuquerque downtown prior.
6. **Hand-digitising:** Trenton downtown parking districts (PDF only), Penndel overlay (only on file at the borough).
7. **Boise:** P-1 district still stood in by C-5 zones; the 2017 code map could be traced instead.
8. **Fremont** now ineligible (2014): the estimator's list of 24 must drop it.

## Freeze

Not frozen yet. When the Spokane event is chosen: run `uv run python scripts/build_parking_doses.py --spokane-event <2023|2024>` (about an hour), then add the hash line for reference/parking_doses.csv here and commit both files together.

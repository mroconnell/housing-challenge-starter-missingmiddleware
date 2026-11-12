# Test 57 code notes (code step; nothing run on real outcomes)

Date: 2026-11-12 (UTC). Plan: `docs/parking/CAUSAL_FRAMEWORK_PLAN.md`, Test 57 up to the LOCK (06:08 UTC).

**No outcome was read.** No DOB job, HPD unit or SF permit was counted by arm or by year. The code was checked on made-up data only. Geometry was checked with no outcomes (cell parts and acres per arm, below).

## Files

| File | What it does |
| --- | --- |
| `scripts/fetch_parking_t57_outcomes.py` | Fetch DOB NOW, HPD, MIH areas, SF 2009 zoning, SF special use districts, SF planning areas |
| `scripts/parking_t57_common.py` | Runs, estimator, ranges, MDE, too-few rule, reading rules |
| `scripts/build_parking_t57_ny_panel.py` | NY panels (6 runs) |
| `scripts/build_parking_t57_sf_panel.py` | SF wave A panel (1 run) |
| `scripts/summarise_parking_t57.py` | `--first` (no effect) and `--all` (95 cells, reading) |
| `scripts/run_parking_t57.sh` | `check`, `first`, `all` |
| `tests/test_parking_t57.py` | 14 checks on made-up data |

Run order: `bash scripts/run_parking_t57.sh first` (after Ryan's go), report counts and MDE, then `bash scripts/run_parking_t57.sh all`.

## Cell map (95 cells, asserted)

"Cell" here = one reported number with a 90% range.

| Run | Role | Main effect | Event-study years (ref −1) | Placebo dates | Cells |
| --- | --- | --- | --- | --- | --- |
| `ny_dob` | **Headline**: NY 2016, all DOB units, MIH lots dropped | 1 | −5, −4, −3, −2, 0 … +7 | −3, −4 | 15 |
| `ny_dob_keepmih` | Alongside: MIH lots kept ("bundled with MIH") | 1 | same | −3, −4 | 15 |
| `ny_dob_samezone` | Sensitivity 1: same-zoning edge | 1 | same | −3, −4 | 15 |
| `ny_dob_legacy2020` | Sensitivity 2: legacy file only, after-window to 2020 | 1 | −5 … −2, 0 … +4 | −3, −4 | 12 |
| `ny_hpd` | Alongside: HPD affordable units, MIH dropped | 1 | −2, 0 … +7 | none | 10 |
| `ny_hpd_keepmih` | Alongside: HPD, MIH kept | 1 | same | none | 10 |
| `sf_a` | SF wave A case (not headline) | 1 | −5 … −2, 0 … +10 | −3, −4 | 18 |
| **Total** | | 7 | 78 | 10 | **95** |

Windows:

| Run | Wave year (year 0) | Before | After |
| --- | --- | --- | --- |
| NY DOB runs | 2016 | 2011–2015 | 2017–2023 (legacy-only: 2017–2020) |
| NY HPD runs | 2016 | 2014–2015 | 2017–2023 |
| SF wave A | 2008 | 2003–2007 | 2009–2018 |
| Placebo −3 (NY) | fake 2013 | 2008–2012 | 2014–2015 |
| Placebo −4 (NY) | fake 2012 | 2007–2011 | 2013–2015 |
| Placebo −3 (SF) | fake 2005 | 2003–2004 | 2006–2007 |
| Placebo −4 (SF) | fake 2004 | 2003 | 2005–2007 |

## Estimator (as the plan names it)

- **Measure:** homes per 100 eligible lot acres a year (TOD's).
- **Effect:** difference in differences of mean yearly rates.
- **Event study:** year k vs year −1, treated minus comparison.
- **Ranges:** 90%, 2,000 cluster-bootstrap draws, seed 20261105.
  - Cluster = 500 m grid cell.
  - A cell split by the line is one cluster; both parts move together.
- **Counts:** range excludes 0.
- **Pre-trend:** any lead (−5 to −2) or placebo date excludes 0.
- **Too few to read:** under 20 cell parts per arm, or under 30 before-window jobs per arm.
- **MDE:** 2.486 × SD of the main effect's bootstrap draws.

## Choices where the plan is silent (for the audit)

**Windows and dates**
1. Year 0 shown, not used in before/after means. TOD's rule; plan's SF "after-years from 2009".
2. Before-window = 5 years (matches leads −5 to −1).
3. Event study runs to the end of each after-window, not only +3.
   - Reason: the plan says the 2022 421-a rush (+6) is shown.
   - Years beyond +3 have no reading rule (`in_plan_window` = False).
4. **Placebo dates = −3 and −4.** See mismatch 1.
5. Placebo after-window ends the year before the real wave (not-yet-treated rule). Placebo year 0 not used.
6. SF: one calendar alignment on 2008 for both plan areas.
   - Eastern Neighborhoods (2009) is "after" from 2009, as the plan says.
   - 2008 is year 0 for all SF lots.

**Estimator**
7. Arm rate = sum of units ÷ sum of eligible acres (acre-weighted pool), as TOD.
8. Every cell of a run uses the same 2,000 draws (one seed per run).
9. MDE uses the spread of the real main-effect draws. Only the SD is written; no centre or percentile.
   - Computing it needs after-window outcomes by arm. Audit may prefer another null.
10. "Cell parts" for the too-few rule = (cluster, arm) pairs with eligible acres > 0.
11. "Jobs" for the too-few rule = DOB jobs with ≥1 unit; HPD buildings with ≥1 unit; SF permits with ≥1 unit.

**NY arms and land**
12. **Manhattan Core outside lots dropped** (CDs 101–108; 1,033 band lots). No minimums there since 1982, so already treated. See mismatch 3.
13. Lot arm by PLUTO 16v1 centroid; band 50–400 m from the land line (exact distance, not the 50 ft raster).
14. Eligible land: TOD's NY rule. Residential, commercial or mixed zoning; land use not 08 or 09. Acres = LotArea.
15. MIH lot = centroid in an MIH area; date = earliest adoption among areas holding it.
    - Records filed on/after the date dropped.
    - Acres pro-rated in the adoption year, 0 after.
16. Same-zoning edge: lot kept if its nearest land-line point has lots on both sides with the same modal district (check script's method).
    - 38.5% of land-line points qualify.
    - Lot-level, not whole-cell.

**NY outcomes**
17. DOB units = proposed dwelling units, jobs with ≥1 unit, every filing status (incl. later withdrawn or disapproved).
18. DOB NOW: one row per job: the initial filing (-I1), else the earliest (7 jobs).
19. Placement: same BBL unless that lot's centroid is over 100 m from the record's point; else nearest lot centroid within 40 m.
    - Centroids, not polygons (TOD used polygons).
20. HPD: New Construction only; units = extremely low + very low + low + moderate + middle income ("other" = super's units left out); dated by project start.
    - Point: latitude/longitude, else the internal fields.
21. Sensitivities and HPD use the primary MIH rule (drop), except the two keep-MIH runs.

**SF**
22. Lots: DataSF active parcels (2026), condo sub-lots folded (154,610 lots). Acres from parcel polygons.
23. Market–Octavia treated from the 2009 layer: RTO, NCT-3, Hayes NCT, Upper Market NCT, inside the M–O planning area.
24. EN treated from the current layer: UMU, MUG, MUR, MUO, SPD, RTO-M, NCT-Mission, NCT-24th-Mission.
    - Inside the 2008 EN areas (incl. Central SoMa); not in Schlage SUD.
25. Controls need all of:
    - current district in the clean list (minus Bayview);
    - a control-type district in 2009 (RH, RM, NC, NCD, C-2): drops 2026 moves into these;
    - outside M–O and all EN areas;
    - outside Telegraph Hill–NB Residential, North of Market 1–2, Bernal Heights, Washington–Broadway and Schlage SUDs.
26. SF outcome: new-construction permits (types 1, 2), not cancelled, gross proposed units, by issue year. As Test 50's main.
27. SF clusters: 500 m grid (EPSG:3310); a cell with both arms is one cluster.

## Things that didn't match the lock

All ruled on in the plan's "Test 57 audit code rulings (06:28 UTC)" block. Since then:
- `--first` also writes `reference/parking_t57_hpd_placement.csv` (HPD not-placed share by year, whole city, not by arm).
- The balance table leaves out the Manhattan Core outside lots.
- The SF 2009 zoning licence source is recorded (DataSF Terms of Use, Section IX: PDDL by default).

Original list:

1. **Placebo dates.** Plan: one date "3 years earlier". Addendum 2: "the −4 placebo". Lock: "both placebo dates". Code runs −3 and −4. Test 56 used −2 and −4.
2. **SF controls: 41 vs Bayview.** The 41 clean rows include NCD-Bayview. The rules block says Bayview is out. Code uses 40.
3. **Manhattan Core.** Outside the zone on the Manhattan line, there have been no minimums since 1982. Code drops those lots (plan: never use already-treated areas as controls). The balance table now leaves them out too (1,023 on its 50 ft raster).
4. **SF plan-area mask.** The lock sets aside the unlicensed SF Planning plan-area layer. DataSF has a public-domain copy (bkzf-eahq), which the feasibility step missed. Code uses it as a mask only; treatment comes from zoning.
5. **SF 2009 zoning licence.** The lock calls it PDDL. The dataset's licence field is blank. Recorded as "PDDL per portal default".
6. **2026-rezoned SF lots.** There is no lot list for Ord. 244-25. Code drops them with the 2009-district test (item 25) and by zoning name. A lot moved in 2026 from an excluded district into a clean one would still pass. That is rare.
7. **HPD placement.** 1,468 of 4,755 new-construction buildings (30.9%) can't be placed. About 1,000 have no BBL and no point. See fetch table.

## Geometry check (no outcomes)

| Item | Treated | Comparison |
| --- | --- | --- |
| NY eligible cell parts, primary | 637 | 458 |
| NY eligible acres, primary | 7,984 | 5,739 |
| NY eligible cell parts, same-zoning | 399 | 337 |
| NY split clusters (eligible) | 252 | — |
| NY MIH-mapped eligible band lots | 988 | 312 |
| SF cell parts | 53 | 372 |
| SF lot acres | 620 | 9,537 |
| SF lots (M–O 1,896; EN 2,754) | 4,650 | 116,398 |

All arms are above the 20-cell floor. The 30-jobs floor needs outcomes, so it is left to `--first`.

## Fetch results (whole-file row totals)

| File | Source | Rows |
| --- | --- | --- |
| `dobnow_nb.json` | DOB NOW w9ak-ipjd (NB + ALT-CO filings) | 76,093 |
| — of which ALT-CO (dropped) | | 17,054 |
| — NB jobs (one per job) | | 9,880 |
| `hpd_affordable_by_building.json` | HPD hg8x-zxpr | 9,551 (4,766 new construction) |
| `mih_areas.geojson` | DCP m79g-k9r4 | 291 areas, all dated |
| `sf_zoning_2009.geojson` | DataSF jud5-ja46 | 23,355 |
| `sf_sud.geojson` | DataSF 5yf5-ms5f | 145 |
| `sf_planning_areas_datasf.geojson` | DataSF bkzf-eahq | 72 |

Record placement (whole file; records with ≥1 unit and a date):

| Source | Records | By BBL | By point | Not placed |
| --- | --- | --- | --- | --- |
| DOB legacy | 92,608 | 71,883 | 18,080 | 2,645 (2.9%) |
| DOB NOW | 7,689 | 5,117 | 2,132 | 440 (5.7%) |
| HPD | 4,755 | 2,438 | 849 | 1,468 (30.9%) |

- Licences: NYC Open Data terms (licence field blank); SF special use districts and planning areas are "Public Domain U.S. Government".
- No request was refused. Own user agent; no workaround.

## Synthetic smoke tests (`tests/test_parking_t57.py`, 14 checks, all pass)

- A planted effect (1.5) is recovered exactly; leads, year 0 and the placebo are exactly 0.
- A planted pre-trend makes lead −5 exclude 0.
- Split cells: one cluster, both parts weighted together in every draw.
- Same seed gives the same draws (2,000 × clusters).
- MDE = 2.486 × SD; no estimate or percentile in the MDE output.
- Too few: 19 cells, or 0 before-window jobs in one arm, sets the flag.
- Cell counts per run and windows (incl. placebo windows) match the table above; total 95.
- Summariser `--first` then `--all` end to end on 7 made-up panels: 95 rows; the planted headline effect reads "counts"; labels present.
- Reading rules: lead overrides counts; too-few overrides all; lags never set the pre-trend label.
- NY build pieces: MIH pro-rating, MIH record drop, keep-MIH, BBL vs point placement.
- HPD not-placed share by year: whole city, no arm column; passed through by `--first`.

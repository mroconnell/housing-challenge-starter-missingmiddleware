# Test 57 feasibility (data checks before the lock)

Date: 2026-11-12 (UTC). Full table: `reference/parking_t57_feasibility.csv` (28 rows).

**No outcome was read.** No permit or unit count was split by area or by time around any reform date. Only file fields, date spans and whole-file row totals were checked.

## Verdict by wave

| Wave | Status | Why |
| --- | --- | --- |
| SF wave A (Market–Octavia 2008, Eastern Neighborhoods 2009) | Feasible, with a new data pull | Boundaries and dates found. The permit file on disk starts in 2013, so it has no before-years. |
| SF wave B (Central SoMa) | **Fails** | No residential minimums were left to remove. The land was already max-only (2009, 2011, 2013). |
| SF wave C (citywide 2019-01-21) | Not testable | No untreated SF areas left (as planned). |
| NY 2016 (ZQA Transit Zone) | Feasible, with two open items | The 2016 boundary file is not in hand. The affordable-units source starts in 2014. |
| NY 2024 (City of Yes) | Not testable | Too recent (as planned). |

## San Francisco

**Wave dates** (one year per area, from the ordinance):

| Area | Ordinance | Effective date | Wave year |
| --- | --- | --- | --- |
| Market–Octavia | 72-08 | 2008-05-30 | 2008 |
| Eastern Neighborhoods | 298-08 (with 297–300-08) | about 2009-01-19 | 2009 |
| Central SoMa | 296-18 | 2019-01-12 | none (no residential change) |
| Citywide | 311-18 (not 290-18) | 2019-01-21 | 2019 |

**Boundaries.**
- SF Planning "Planning Areas" layer has all plan areas.
  - Saved to `data/raw/parking_t57/` (git-ignored).
  - No licence stated; no DataSF (PDDL) copy found.
- The layer is current, not 2008.
  - Central SoMa is cut out of East SoMa and Western SoMa.
- **Central SoMa overlaps Eastern Neighborhoods: yes.**
  - 382 of 384 sample points (99%; 50 m grid) lie in the Eastern Neighborhoods fee area.
- About 10% of Market–Octavia sample points (65 of 666) are in Downtown C-3-G.
  - That part was max-only since 2006: leave it out.
- Treat by zoning district, not plan polygon.
  - RH and RM lots inside Eastern Neighborhoods kept minimums.
- The DataSF "2009" historic zoning layer has mixed vintage: check it before use.

**Controls that changed inside wave A's window (drop before any count).**
- Balboa Park / Ocean Ave (2009; extended 2016)
- North Beach, Broadway, Chinatown (2010; rest 2014)
- SoMa RED, RSD, SLR, SLI, SSO, M-1, C-M (2011)
- Glen Park (2012); Western SoMa (2013)
- Schlage Lock (2014); Van Ness–Polk RC (2014)
- Divisadero and Fillmore (2014); Japantown (2016)
- Also always treated: Rincon Hill/Transbay (2005), Downtown C-3 (2006).
- Citywide, not by area: affordable/senior to 0 (2008-07-31), waivers (2015), ADUs, bike swaps (2017).
- Not checked: Excelsior NCD (2013); remaining RH/RM/NC districts one by one.

**Outcome (measure: permits ISSUED).**
- On disk: `data/raw/parking_lot_cities/sf_permits.json` (12,701 rows, PDDL).
  - Fields: block, lot, issued date, existing and proposed units, point location.
  - Issued dates 2013-01-02 to 2026-10-30. **Too late for wave A.**
- Online source (DataSF i98e-djp9) goes back to 1906.
  - For 2003–2012 new-building permits: location filled on 99.8%, proposed units on 96.7% (whole-city shares).
  - A re-pull from 2003 fixes wave A. This is a new fetch: needs Ryan's OK.

## New York

**The 2016 rule (adopted 2016-03-22, N 160049 ZRY).**
- Inside the Transit Zone, no parking required for:
  - new income-restricted units, incl. MIH units (ZR 25-251);
  - affordable senior residences (ZR 25-252).
- Mixed-income buildings: only by BSA or CPC permit (at least 20% affordable).
- **Market-rate minimums did not change in 2016.**
- No lot-size rule found.

**What this means for the primary outcome (audit fix 5).** The change hit only affordable and senior units. So the primary outcome should be those units, if a source works:
- HPD "Affordable Housing Production by Building" (hg8x-zxpr): dated and located.
  - But it starts in 2014: 2 before-years, not 5.
  - It has no senior flag.
- No other dated, located, public affordable source found.
- **Decision at the lock:** HPD with short leads, or all new-building units labelled "possibly diluted toward 0".

**Transit Zone boundary.**
- Current layer (NYC Open Data dpnc-b2hd) saved to `data/raw/parking_t57/`.
  - It includes amendments from 2022 and 2024 (three map sets).
- The 2016 file was not obtained.
  - nyc.gov download blocked (HTTP 403); not worked around.
  - NYU archive link now dead.
- Line type: covers whole community districts plus parts of others. Zoning-line fit not tested yet.

**City of Yes:** adopted 2024-12-05. After-window ends 2023.

**Changes at the same time** (fix 6):

| Change | Date(s) | Source |
| --- | --- | --- |
| MIH text | 2016-03-22 | same day as ZQA |
| MIH rezonings | 2016-04-20 onward (12 neighbourhood plans to 2022) | Open Data m79g-k9r4 (291 areas) |
| 421-a lapse | 2016-01-15 to 2017-04-10 | rush before Jan 2016 |
| 421-a start deadline | 2022-06-15 | rush before June 2022 |
| ZQA envelope | 2016-03-22, citywide | heights up about 10–20 ft |

- TOD's list names the MIH rezonings but has no MIH layer on disk.
- TOD's `nyzma.geojson` (all zoning map changes, with dates) is on disk.

**Outcome (measure: jobs FILED).**

| Source | Filing dates | Location | Affordable flag |
| --- | --- | --- | --- |
| DOB legacy (ic3t-wcy2), on disk | 1989 to about end-2020 | lat/lon on 99.1% | none |
| DOB NOW (w9ak-ipjd), online | 2021-03-03 to now | lat/lon on 98.5% | none |
| HPD by building (hg8x-zxpr), online | 2014-01-03 to now | lat/lon and BBL | income bands; no senior |

- Possible gap Jan–Feb 2021 between DOB files: check in the code step.

**Licences.**
- SF: PDDL 1.0 (DataSF).
- NY: NYC Open Data terms; licence field blank on the datasets.

## Sources
Ordinance sources, URLs and confidence are in the CSV. Blocked: codelibrary.amlegal.com (403); nyc.gov Transit Zone zip (403).

## Addendum 2 checks (2026-11-12 UTC; audit addendum 2 of 02:01 UTC)

**No outcome was read.** No permit, DOB job or HPD unit was counted by area or by time. The only DOB numbers below are whole-city monthly totals for the Dec 2020 to Apr 2021 gap check. Housing in the balance table is the existing stock in MapPLUTO 16v1 (March 2016).

Files:
- Scripts: `scripts/fetch_parking_t57_gis.py`, `scripts/build_parking_t57_nyc_tz.py`, `scripts/check_parking_t57_dob_gap.py`, `scripts/build_parking_t57_sf_districts.py`.
- Tables: `reference/parking_t57_nyc_tz_check.csv` (168 rows), `reference/parking_t57_sf_districts.csv` (120 districts).
- GIS stays in `data/raw/parking_t57/` (git-ignored).

### 1. New York: the 2016 Transit Zone line

**The 2016 file was found.**
- DCP's own 2016 file (`nyctransitzones_201601`, created 2016-06-30, published 2016-07-07) is on the Internet Archive.
  - Wayback capture 2025-12-22 of the nyc.gov Bytes archive zip.
  - nyc.gov itself still answers HTTP 403 to non-browser clients. Not worked around.
- **It is now the primary 2016 line.** The rebuild is the check.
- Area: 212.6 km² (2016 file) vs 212.8 km² (current layer).

**A fourth amendment exists.** The ZR amendment history lists four amendments after 2016, all adding land:

| Amendment | Effective | Maps | Land added (tax blocks) | Rebuild: added land removed | Over-removed |
| --- | --- | --- | --- | --- | --- |
| N 180084 ZRX, E 241 St | 2019-02-13 | 1 | Bronx 5087 | 1.2 ha | 0 ha |
| N 220313 ZRK, Innovative Urban Village | 2022-11-22 | 12 | Brooklyn 4430, 4431, 4434 | 4.5 ha | 0 ha |
| N 240016 ZRX, Bronx Metro-North | 2024-08-15 | Key, 2, 3 | Bronx 4042, 4045, 4046, 4058, 4060–4063, 4091 | 8.0 ha | 1.0 ha |
| N 230183 ZRK, Brooklyn Yards | 2024-11-21 | 13, 14 | Brooklyn 5509, 5516, 5523 | 5.8 ha | 0 ha |

- Sources: ZR amendment history (zr.planning.nyc.gov), CPC report N 240016 (Wayback copy), ZAP applicant text maps for the other three. CPC reports for 220313, 230183 and 180084 have no public copy (nyc.gov 403; no Wayback copy).
- Metro-North adds 1 full and 5 partial blocks. Removing whole blocks over-removes 1.0 ha.

**Rebuild vs the 2016 file** (50 ft raster):
- The current layer has 25.7 ha the 2016 file lacks. The 4 pieces of 1 ha or more (8.2, 5.9, 5.5 and 1.4 ha) all sit on amendment blocks.
- The rest (6.2 ha added, 8.7 ha removed) is thin slivers along the line: re-digitising, not law changes.
- After the rebuild, differences wider than about 100 ft: 0.7 ha extra and 1.2 ha missing, citywide.

**Map by map against the adopted 2016 maps** (Appendix I, eff. 3/22/16, web file of 4/5/16, Wayback copy):
- Each map page was fitted to the GIS by correlation (scale and shift).
- Score: share of the page's map pixels where shading and GIS agree.

| Map | Page vs 2016 file | Page vs current layer | Rebuild vs 2016 file (wider than ~100 ft) | Result |
| --- | --- | --- | --- | --- |
| 1 | 97.6% | 97.5% | 0 ha | pass |
| 2 | 98.8% | 98.6% | 0.9 ha missing | pass |
| 3 | 98.6% | 98.3% | 1.2 ha missing | **fix** (use 2016 file) |
| 4 | 98.5% | 98.5% | 0 ha | pass |
| 5 | 98.2% | 98.2% | 0 ha | pass |
| 6 | 98.3% | 98.3% | 0 ha | pass |
| 7 | 98.4% | 98.4% | 0 ha | pass |
| 8 | 98.0% | 98.0% | 0 ha | pass |
| 9 | 98.7% | 98.7% | 0 ha | pass |
| 10 | 99.3% | 99.3% | 0 ha | pass |
| 11 | 99.2% | 99.2% | 0 ha | pass |
| 12 | 98.8% | 98.6% | 0.7 ha extra | pass |
| 13 | 98.8% | 98.7% | 0 ha | pass |
| 14 | 98.1% | 97.9% | 0 ha | pass |
| 15 | 98.8% | 98.8% | 0 ha | pass |

- **No map is dropped.** On every map the 2016 file matches the adopted page as well as or better than today's layer.
- Remaining page mismatches are strips about a street wide along the line, and shorelines. Checked by eye on Maps 1, 2 and 5. No block-sized gap found.
- Key Map: only used to locate the maps (schematic; correlation 0.70).
- Text check ("all of" community districts in the adopted text): 15 of 19 districts are 99% or more inside the 2016 file. Brooklyn 306, 307 and Bronx 202 are 97–98% (shoreline edges). Manhattan 111 is 64%: the 219 ha outside is Randall's and Wards Islands (parks).
- Council removals: Rockaways (Queens 414) 0% inside. Brooklyn 313 (Coney Island) 23%, Brooklyn 312 68%, Bronx 203 72%: these left the "all of" list but kept mapped parts, as the Council map shows.
- Bronx 204 is missing from the 4/5/16 web text (typo; fixed in the 3/6/17 web copy). The 2016 file has 99.9% of it.

### 2. New York: what the line follows, cells, balance

**Line type** (2016 line sampled every 25 ft; 60 ft either side):

| Line piece | Share |
| --- | --- |
| Whole line | 310 km |
| Water or city edge on one side | 32% of whole line |
| Land line (city land both sides) | 211.5 km |
| Along a borough line | 2.6% of land line |
| Along a community-district line (incl. borough) | 20.2% of land line |
| Along a zoning-district change, not a CD line | 25.0% of land line |
| Along neither | 54.8% of land line |
| No lots within 300 ft on one side (parks, rail yards) | 32.6% of land line |

- Zoning: era layer = MapPLUTO 16v1 lot zoning (March 2016). No public 2016 zoning-district polygons found (DCP 2016 zoning zips not on Wayback).
  - Method: the most common ZoneDist1 of lots within 300 ft on each side. Approximate.
  - Where both sides have lots, about 43% of the land line runs along a zoning change (28.8% of 67.4%).
- So the line mostly cuts through districts and zoning. It is not mainly a zoning or CD line.

**Cells** (500 m grid; band 50–400 m from the land line, each side; split cells give one part per arm):

| Count | Inside | Outside |
| --- | --- | --- |
| Cell parts in band | 773 | 712 |
| Cell parts with at least 1 ha of land | 667 | 583 |
| Band land area | 7,484 ha | 6,175 ha |
| Cell parts citywide (no band) | 1,133 | 2,197 |

- 427 cells are split by the line.
- Both arms are far above the 20-cell "too few" floor. The 30-jobs floor needs outcomes, so it is not checked here.

**Pre-period balance** (16v1 lots by centroid in each band; no outcomes):

| Measure | Inside | Outside |
| --- | --- | --- |
| Tax lots | 98,165 | 75,357 |
| Lot area | 12,202 acres | 9,298 acres |
| Median lot size | 2,450 sq ft | 2,500 sq ft |
| Mean lot size | 5,415 sq ft | 5,375 sq ft |
| R1–R5 zoning (share of lot area) | 40.1% | 56.4% |
| R6–R10 zoning | 31.4% | 14.5% |
| Commercial zoning | 3.9% | 4.3% |
| Manufacturing zoning | 20.1% | 12.9% |
| Other (parks, blank) | 4.5% | 12.0% |
| Existing homes (March 2016) | 545,108 | 264,067 |
| Homes per lot acre | 44.7 | 28.4 |
| Median homes per lot acre, cell parts with 2.5+ lot acres | 39.7 (602 parts) | 28.6 (445 parts) |
| Homes in buildings built before 1940 | 53.8% | 43.9% |
| Median year built (home-weighted) | 1935 | 1948 |
| Lots with any homes | 88.6% | 92.4% |

- Lot sizes match across the line.
- Zoning, density and age do not. Inside is denser, older and has more high-density and manufacturing zoning.
- These are levels in 2016, not trends. A trend in the existing stock was not computed (it would mean counting homes by year).

### 3. New York: DOB filing gap, Jan–Feb 2021

Whole-city new-building jobs per month (not split by area):

| Month | Legacy, file on disk | Legacy, online table | DOB NOW, all NB filings | DOB NOW, first filings | DOB NOW ALT-CO |
| --- | --- | --- | --- | --- | --- |
| Dec 2020 | 313 | 313 | 0 | 0 | 0 |
| Jan 2021 | 297 | 297 | 0 | 0 | 0 |
| Feb 2021 | 329 | 329 | 0 | 0 | 0 |
| Mar 2021 | 17 | 17 | 68 | 65 | 35 |
| Apr 2021 | 10 | 10 | 126 | 115 | 40 |

- **No hole in the data.** The legacy file keeps taking new-building filings through February 2021. DOB NOW new-building filings start 2021-03-03.
- **But the plan's seam makes a hole.** Under "legacy through 2020-12-31, DOB NOW from 2021-01-01", Jan–Feb 2021 would count 0.
  - Fix for the lock: put the seam at 2021-03-01 (legacy through 2021-02-28). Then the 12/10 scaling is not needed.
  - March 2021 has filings in both files (17 legacy, 68 DOB NOW). The lock should say how March is counted.
- Whole-city level: about 300 a month before March 2021; 85 in March and 136 in April 2021 (both files). This affects both arms. Label it in the write-up.

### 4. San Francisco: zoning districts and controls

**Treatment layer:** DataSF "Zoning Map - Zoning Districts" (3i4a-hu95), PDDL-1.0. Saved to `data/raw/parking_t57/`.

**Problem: the layer is 2026, not 2008 or 2018.** The Family Zoning Plan (Ord. 244-25 map, 245-25 text, operative 2026-01-12):
- moved some RH and RM lots to RTO-C (new) or RTO-1;
- moved some NC and P lots to C-2;
- renamed RTO to RTO-1.
- So current RH, RM, NC, C-2 and RTO-1 polygons are not the old boundaries.
- **Needs a decision:** a 2008/2009 and a 2018 boundary. Option: DataSF "Historic Zoning Districts - 2009" (PDDL; has the 2008 Market–Octavia districts, not the Eastern Neighborhoods ones). No 2018 layer found on DataSF.

**Code history check** (2003-01-01 to 2018-12-31; ordinances on sfbos.archive.sf.gov, SF Planning summaries, gocodebook Sec. 151.1 history):
- **Excelsior changed.** Ord. 261-13 (eff. 2013-12-27) replaced the minimum with a maximum of 1 per unit. Dropped from controls.
- Other new changes found: Polk and Pacific NCDs (Ord. 205-17, 2017-12-03); RCD (max-only by 2018, Ord. 202-18 list; date not verified); Parkmerced (Ord. 90-11, 2011).
- Ord. 202-18 (Aug 2018) lists every district on max-only rules. All other districts kept the 1-per-unit minimum until Ord. 311-18 (2019-01-21).
- Waiver-route changes (Ord. 63-11, 52-15) and citywide rules (112-08, ADUs, 99-17) don't split areas. Label them.

**Clean control list** (verified unchanged; 41 districts, 4,175 ha in today's layer):
- RH-1(D), RH-1, RH-1(S), RH-2, RH-3.
- RM-1, RM-2, RM-3, RM-4.
- NC-1, NC-2, NC-3, NC-S.
- Named NCDs: 24th-Noe Valley, Castro, Haight, Inner Clement, Outer Clement, Inner Sunset, Sacramento, Union, Upper Fillmore, West Portal.
- NCDs made from NC land (1:1 kept): Noriega, Irving, Taraval, Judah (2012); Cole Valley, Lakeside Village, Inner Balboa, Outer Balboa, Inner Taraval, Lower Haight, Cortland, San Bruno, Geary Blvd, Mission Bernal, Lower Polk (2020); Leland (2025).
- Bayview NCD: plausible only (redevelopment overlay not checked).
- C-2: rate only. Leave out the Washington-Broadway SUD.
- Also leave out lots in:
  - Telegraph Hill-North Beach Residential SUD;
  - North of Market SUD;
  - Market–Octavia and Eastern Neighborhoods plan areas;
  - 2026 rezoned lots.
- Bernal Heights SUD is unverified.

**Wave A treated list** (leaves out C-3-G, DTRs, Downtown C-3, EN RH/RM lots):

| Plan | Effective | Districts (today's names) |
| --- | --- | --- |
| Market–Octavia (Ord. 72-08) | 2008-05-30 | RTO-1 (old RTO; drop 2026 additions), NCT-3, NCT-Hayes, NCT-Upper Market (2008 part only) |
| Eastern Neighborhoods (Ord. 298-08) | about 2009-01-19 | UMU, MUG (not Schlage Lock), MUR, MUO, SPD, RTO-M, NCT-Mission, NCT-24th-Mission, NCT-Valencia |

- **NCT-Valencia date conflict:** the first feasibility row put it in Ord. 72-08 (2008); this check finds it in Ord. 298-08 (2009). Wave A either way; the year needs a decision.
- Dropped from treated, because the current layer mixes dates: NCT-SoMa (2009 and 2013 parts), NCT-2 (Dogpatch 2009 and Geneva 2009 Balboa Park), NCT-1.
- Excluded as changed in the window: Excelsior, Japantown, Polk, Pacific, Broadway, North Beach, Chinatown (CCB, CVR, CRNC), RC-3, RC-4, RCD, Divisadero, Fillmore, Ocean, Glen Park, Folsom, Western SoMa (WMUG, WMUO, SALI, RED-MX), RED, M-1, C-3, DTRs, CMUO, Parkmerced.
- Unverifiable (excluded): Mission Bay, Treasure/Yerba Buena Island, Hunters Point, Job Corps, RTO-C, post-2015 development-agreement districts.

### What fails or is open

| Item | Status |
| --- | --- |
| NY 2016 line | Found (DCP 2016 file); all 15 maps pass or fixed; none dropped |
| NY line type | Mostly cuts through districts; 20% CD lines, about a quarter zoning-only |
| NY balance | Lot size balanced; zoning, density and age not |
| NY DOB gap | No hole if the seam moves to 2021-03-01; hole under the plan's stated seam |
| SF layer vintage | **Fails as is**: 2026 layer; needs 2008/2009 and 2018 boundaries |
| SF Excelsior | Changed 2013: out of controls |
| SF NCT-Valencia year | 2008 or 2009: open |

### Blocked sites (not worked around)
- nyc.gov: HTTP 403 to non-browser clients for the Transit Zone zip, community district and borough zips, Appendix I PDF and the CPC reports 160049, 180084, 220312, 220313, 230182, 230183, 240016. Wayback copies used where they exist.
- codelibrary.amlegal.com: HTTP 403.
- gocodebook.com Sec. 151 pages: HTTP 404 (section repealed in 2025).
- No DCP 2016 zoning-district zip on Wayback.

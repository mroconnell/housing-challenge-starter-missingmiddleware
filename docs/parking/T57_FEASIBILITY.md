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

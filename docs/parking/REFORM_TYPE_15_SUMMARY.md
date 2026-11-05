# Parking reform coding for 15 places: summary for handoff

**What this is:** a descriptive coding of the parking reform in each of the 15 places that have 5 or more years of permit data after their repeal. It is used to ask whether the repeals differ in kind, so they can't be treated as one policy. Nothing in the tool changed because of it.

**Files (repo `missing-middleware`):**
- **Data:** `reference/parking_reform_type_15.csv`, one row per place and 40 fields, with source URLs and Wayback capture dates.
- **Plan:** `docs/parking/CAUSAL_FRAMEWORK_PLAN.md`, section "Reform-type coding". The coding was committed (cf4388cc) before it was joined to any result.
- **Results:** `docs/parking/WORK_SESSION_RESULTS.md`, section "Reform-type coding for the 15 long-set places".
- **Related:** `reference/parking_old_minimums.csv` holds the old minimums, and `reference/parking_sample_corrections.csv` the sample removals.

**How it was coded:**
- **Sources:** five helpers coded three places each from public sources, following one written brief.
- **Blocked sites:** sites that block automated access (parkingreform.org, Municode, eCode360, amlegal, Planetizen) are cited, not worked around.
- **Records requests:** none.
- **Audit:** the work was checked. San Francisco's approval paths are low confidence, because the code text couldn't be read.

**Fields per place:**
- **Repeal:** adoption and effective dates, repeal type (full / partial / other), which housing types it covers, and its geographic scope.
- **Old and new requirement:** for a house, a duplex, a 3–4 unit building, a 20-unit building and a 100-unit building.
- **Approval path, before and after:** by right, administrative, or hearing; for houses, ADUs, 2-unit, 3–4 unit and 5+ unit buildings.
- **Context:** whether the repeal changed the approval path, other zoning changes within a year, and earlier exemptions.
- **Quality:** sources, confidence and notes.

**Results:**

| Place | State | Year | Repeal type | Old minimum, 20 units | 5+ units after repeal | Repeal changed approval? |
| --- | --- | --- | --- | --- | --- | --- |
| San Francisco | CA | 2019 | Full, citywide | 20 (Sec. 151 districts); 0 in Sec. 151.1 districts | Mixed: hearing above size thresholds | Partly |
| Emeryville | CA | 2020 | Full, citywide | About 16 | Hearing (design review) | Partly |
| Bastrop | TX | 2019 | Full, citywide (whole code replaced) | Not found | Mixed by zone | Partly |
| Buffalo | NY | 2017 | Full, citywide | 20 | Mixed: hearing if 5,000+ sq ft | Yes |
| Hudson | NY | 2019 | Full, citywide | 20 | Board review; hearing optional | No |
| Canandaigua (Town) | NY | 2020 | Full, townwide | Not found | Mixed: Planning Board site plan | No |
| Hartford | CT | 2017 | Full, citywide (maximums kept) | 20 (downtown already 0) | By right where allowed | No |
| Seabrook | NH | 2019 | Not residential (non-residential only) | n/a | Not allowed | No |
| Windham | ME | 2018 | Full for 3+ units; village houses keep 1 per unit | 25–40 | Board review; hearing optional | Partly |
| Dunwoody | GA | 2019 | Full (old minimums became maximums) | 42.5 | Mixed by zone | No |
| Branson | MO | 2018 | Near (text still says spaces "shall be provided") | 40 | By right | No |
| Maumee | OH | 2020 | Reform, not a repeal (discretionary reduction) | Not found | Mixed | No |
| Mount Pleasant | MI | 2018 | Full, citywide | Not found | Mixed by zone | Partly |
| Saranac Lake | NY | 2016 | Full, village-wide | Not found | Board review; hearing optional | Partly |
| Ecorse | MI | 2020 | Full (maximums added) | Not found | By right, with site plan review | Unknown |

**Key findings:**
- **Repeal type varies:**
  - 11 are plain full residential repeals.
  - Windham is partial.
  - Branson is "near".
  - Maumee is a reform, not a repeal.
  - Seabrook is not a residential repeal.
- **Strength of the change varies:** the old minimum for a 20-unit building ran from about 16 (Emeryville) to 42.5 (Dunwoody). It wasn't found for 6 places.
- **Approval path varies:**
  - by right: 3 places;
  - mixed by zone or size: 7;
  - board review with an optional hearing: 3;
  - design-review hearing: 1;
  - not allowed: 1.
- **Approval rules mostly unchanged:** only Buffalo clearly changed its approval rules with the repeal. Seven changed them partly, mostly through whole-code rewrites.

**Changes to the sample that came from this coding:**
- **Canandaigua:** the repeal was the Town's, so the Town's permit series replaces the City's. The City is kept out of the Town's comparison pools.
- **Seabrook:** removed, because it's not a residential repeal (Ryan, 2026-11-05 15:50 UTC).
- **Maumee:** coded as a parking reform, not a repeal, and discretionary. It is removed from the sample and kept as a sensitivity (Ryan, 15:54 UTC).
- **Branson:** kept in the sample, with a "without Branson" sensitivity.
- **Result:** the main sample went from 76 places to 74. The rerun barely moved the main estimate. Method 2's range widened and now just misses the like-for-like bar, and its backtest now fails.

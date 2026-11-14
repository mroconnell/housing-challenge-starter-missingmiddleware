# Test 8 download check (2026-11-14)

What came down against what was asked for. Raw files: `data/raw/middle_tracts/` (gitignored; `_downloads.json` lists
url, bytes, sha256). Fetch scripts: `scripts/fetch_middle_tracts.py`, `scripts/fetch_middle_towns.py` (commit 24658f7c).
States: the 4 law states plus the 34 comparison-screen states (38).

| Piece | Expected | Got | Gap |
| --- | ---: | ---: | --- |
| County block files (2020 PL H1 housing units) | 2,553 counties | 2,553 | none |
| Block assignment files (block → place) | 38 states | 38 | none |
| 2000 SF3 H032 tract files | 38 states | 38 | none |
| ACS 2020–24 B25127 tracts vs 2020 tract list | 61,288 tracts | 61,274 | 14 in New York (likely water-only or zero-home tracts; not checked one by one) |
| Town files (tract parts by town, DHC 080) | 4,754 towns | 4,754 | 12 came back empty |
| Permit units linked to any tract | 16,017 | 15,981 | 36 unlinked (0.2%) |

**Unlinked permit units (36).** Each gets no score, so it sits outside both the high and low groups. In the law
states: 4, all small (Maine: Atkinson, Bancroft, Maine Unorganized Territory; Vermont: Enosburgh). Likely reasons, not
yet confirmed one by one:
- incorporated, merged or dissolved after 2020, so the 2020 code differs (e.g. Cahokia Heights IL 2021, St George LA
  2024, Princeton township NJ merged 2013; Atkinson and Bancroft ME deorganized);
- consolidated city-counties filed under a different code (Indianapolis, Macon, Mecklenburg County, Arlington County;
  the last two are screened out of Test 1 anyway);
- name or code mismatches between the permit file and 2020 geography (Enosburgh VT, Mount Lebanon and Penn Hills PA,
  several Wisconsin villages).

Full list: Helena, Macon, Mulberry, Riverside town, The Rock town (GA); Cahokia Heights (IL); Indianapolis (IN);
Decatur (IA); Latonia Lakes (KY); St George (LA); Atkinson town, Bancroft town, Maine Unorganized Territory (ME);
Baldwin, Credit River, Hassan township, Village of Minnetonka Beach, Thomson (MN); Silver Creek village (MO); Princeton
township (NJ); Mecklenburg County (NC); East Fork township, Lumber City borough, Mount Lebanon municipality, Penn Hills
municipality, West Lawn borough (PA); Rocky Top, Lakewood (TN); Enosburgh town (VT); Arlington County (VA); Brokaw
village, Rib Mountain village, Silver Lake village, Vernon village, Waukesha village, Williamstown town (WI).

**Not yet checked:** whether each linked unit's housing total matches its 2020 count; whether the 2000 → 2020 tract
links lose homes. The audit is asked to look at both.

## Housing-total checks (audit, 2026-11-14)

- **A. Towns:** 4,742 of 4,754 town files match their 2020 town housing total exactly (Census 2020 DHC H1); 0 short.
  The 12 empty files are town codes with no 2020 town (merged, dissolved or county-level units); two 2020 towns have
  0 homes. No refetch needed.
- **B. Blocks:** 6,147,279 blocks in the block-assignment files; 0 without a PL housing count. Every state's block
  total equals its PL state total.
- **C. New York:** the 14 tracts missing from ACS are all in Suffolk County (36103) and hold about 18,600 homes in
  2020, not 0. ACS 2020–24 has no row for them. Towns that include them score only their other tracts. New York is a
  comparison and fake state only. Why this cannot change the reading (audit): the Suffolk tracts count as "not stopped";
  New York is one of the 7 fake values behind California's range; moving one value shifts the percentile by one step
  at most (to 43 or 71), still "we do not know"; and the real California contrast does not use New York.
- **Order:** these checks ran after the first Test 8 results had been computed (the audit's request arrived during the
  run). They found nothing that changes the inputs, so the run stands. The optional code fixes (Indianapolis,
  Macon-Bibb, Mount Lebanon, Penn Hills, Enosburgh) were not made; none is in California.

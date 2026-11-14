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

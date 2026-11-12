# Parking: dates for the 33 undated places, results

Written 2026-11-12 by a parking-thread helper. Data research only: no permit outcomes were read, no places were added to the sample, and no estimate was run. Output: `reference/parking_repeal_checks_dates33.csv`. It has the same columns as `parking_repeal_checks_expanded.csv`, plus `date_status`.

## Which 33

- **Source of the 33:** rows of `reference/parking_expanded_match.csv` whose first drop reason is "no repeal date found".
- **The rule in `scripts/run_parking_expanded.py`:**
  - The event year is `event_year` if filled in.
  - Otherwise it is the year of `effective_date`.
  - Otherwise it is the year of `adoption_date`.
  - So an adoption date alone is usable.
  - A place drops if all three are blank.
- **Other places with this reason:** 18 more places also carry "no repeal date found". Each was dropped first for a weaker ordinance check, so they were not part of this task.

## Answer

| Result | Places (of 33) |
| --- | ---: |
| Effective date found | 0 |
| Adoption date only (usable under the rule) | 0 |
| Repeal year in 2015–2024 | 0 |
| Still undated | 33 |

- **No place gained a date.** Most never had housing minimums to remove.
- **Evidence says "never had minimums" (no event):** 22 places. `no_event` is set to True for them.
- **Unresolved:** 11 places. The code history is missing, or the site blocked us.
- **Rating changed:** 1 place. Prompton, PA moves from at to weaker. Wayne County's subdivision ordinance applies there and requires 1.5 spaces per home for multifamily.
- **Nearest to a date:** Covington, GA. Its "no minimum" text is first dated to a chapter re-enactment of 2016-05-02. The chapter before it (laws of 2008–2014) was not found, so 2016 is not proven as the removal year. It is left blank.

## Still undated, and why

### Never had minimums: 22 places (`no_event` = True)

| Place | Why no date |
| --- | --- |
| Lincoln, KS | No zoning. Zoning articles "reserved". |
| Bucklin, KS | No zoning. Zoning article "reserved". |
| Paden City, WV | No zoning or subdivision rules. |
| New Florence, PA | No zoning. County land-development rules unchecked. |
| Prompton, PA | No zoning. County rules require parking, so rated weaker. |
| Crossville, TN | No use zoning. Subdivision rules: 2 spaces per lot. |
| Monticello, AR | No zoning. Manufactured homes: 2 spaces each. |
| Patagonia, AZ | No zoning. Use permit needed except single homes. |
| Ray City, GA | 1985 zoning, never amended, no schedule. |
| Cohutta, GA | Code since 1986, no dwelling ratio. |
| Algoma, WI | Current and prior code, no per-home ratio. |
| Neodesha, KS | Code since 1997, no parking section. |
| Council Grove, KS | Code since 1981, no parking text. |
| Plainville, KS | No parking text. Referenced document unchecked. |
| St. Francis, KS | Code since 1978, no "parking" at all. |
| Ellendale, ND | Only an advisory commercial clause. |
| Bethany, MO | Code since 1968, no dwelling ratio. |
| Louisiana, MO | 1983 wording kept. The 2007 laws re-adopted the code; they did not repeal a ratio. |
| Geneva, NE | No schedule in any history note. |
| Neligh, NE | 2001 code, no space requirement. |
| Arapahoe, NE | 2015 and 2025 versions, no schedule. |
| Stronghurst, IL | No parking chapter in zoning. |

- **Caveat:** for most of these, only the current code was read, not older versions.
- **What "no event" means here:** no minimums were found in any version read.

### Unresolved: 11 places

| Place | Why no date |
| --- | --- |
| Covington, GA | 2016 re-enactment is a candidate, not proven. News site returned 429. |
| Hull, GA | Code posted as a 2021 draft. No adoption vote found. |
| Corrales, NM | Earlier versions of §18-39 (1989–2017) not found. |
| Keyser, WV | A 2019 law mentions a "duly adopted zoning ordinance". amlegal returned 403. |
| Diamond, MO | Zoning never had a ratio. Manufactured-home sites need 1 space each. |
| Leoti, KS | Zoning appendix blocked (Municode 403). |
| Hill City, KS | amlegal returned 403. Code defines "parking space". |
| Pine Bluffs, WY | Town site and zoningpoint returned 403. |
| Dighton, KS | No code online. |
| Bertrand, NE | No code text online. |
| Catlin, IL | No zoning text online. Possible new zoning in 2026. |

- **No sites worked around:** none of the blocks above were bypassed.
- **Blocked or failed sites:**
  - 403: municode, amlegal, ecode360, civiciq, zoningpoint, pinebluffswy.gov, parkingreform.org.
  - 429: covnews.com.
  - 404: a 2022 Covington minutes PDF.

## Next steps (not done)

- **Covington:** read the 2016-05-02 ordinance or the 2008 chapter, if the city or covnews can be reached.
- **Keyser and Hill City:** re-check when amlegal is reachable.
- **Leoti:** re-check when Municode is reachable.
- **Prompton:** the new weaker rating could also be applied to the main check file. Not done here.

# TOD station areas: land, zoning and capacity

Written 2026-10-26 (TOD Gate 2, work package 4). Updated the same day for the Gate 2 decisions in AQ-049:
- G2-6: Milwaukee's 2025 amendments are coded.
- G2-8: a sensitivity leaves single-family lots out.
- G2-9: places whose zoning is not coded get a fallback.
- Floor area per home is now measured, not assumed.

This file builds the land and zoning inputs that method B (capacity, feasibility and take-up, [GATE1_PACKET.md](GATE1_PACKET.md) section 4.2) needs:
- the City of Milwaukee and the City of Madison, with coded zoning;
- every other municipality near a qualifying stop, with the existing-density fallback.

Rules followed: AQ-044 to AQ-049 in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md). Sources come from [WI_CAPACITY_DATA.md](research/WI_CAPACITY_DATA.md) and stops from [TRANSIT_PIPELINE.md](TRANSIT_PIPELINE.md).

All numbers are **capacity**: homes the rules would allow on paper. They are not forecasts of building. Feasibility and take-up come at Gate 3.

## 1. How to run

```bash
uv run --all-extras python scripts/fetch_tod_parcels_zoning.py --counties all   # needs network; about 6 minutes
uv run --all-extras python scripts/build_tod_station_areas.py                  # offline; about 40 seconds
bash scripts/test.sh                                                           # includes tests/test_tod_capacity.py
```

Options:
- `--only v12|mke_zoning|mad_zoning|docs` refetches one part.
- `--counties milwaukee,dane` limits the parcel fetch. The default is those two; `all` means every county with a qualifying stop: Dane, Eau Claire, Kenosha, Milwaukee, Ozaukee and Waukesha.

Raw files go to `data/raw/tod_capacity/` (git-ignored) with `manifest.json`. The manifest records URL, access time, bytes, SHA-256, licence, feature counts and the final Internet Archive capture URL. It also hashes the raw files reused from earlier fetches.

## 2. Sources

| Input | Source | Used for |
| --- | --- | --- |
| Parcel outlines | Wisconsin V12 statewide parcels (2026 release), REST. Only parcels intersecting a 0.6-mile buffer of the stops in `reference/tod_stops.csv`: 219,954 in Milwaukee County (149,803 in the city), 65,319 in Dane, plus Eau Claire, Kenosha, Ozaukee and Waukesha counties. No owner or address fields are requested | Lot area (polygon area in EPSG:3071); V12 class for places not coded |
| Homes, zoning and land use, Milwaukee | Master Property file (MPROP, 2026 assessment, CC BY), joined on TAXKEY = V12 PARCELID. 99.8% of city V12 parcels in the buffer match | Existing homes, zoning district, use class |
| Zoning polygons, Milwaukee | City zoning layer 11 (CC BY), same buffer | District for the 290 lots with no MPROP zoning |
| Parcels, Madison | City of Madison tax parcels (already in the repo): `TotalDwellingUnits`, `PropertyUse`, `ZoningAll`, outlines | Area, existing homes, use class, zoning district |
| Zoning polygons, Madison | City OPEN_DATA layer 9 (2,473 polygons) | Fallback district. Not needed in this run: every Madison parcel had `ZoningAll` |
| TOD overlay, Madison | `data/raw/madison_tod/tod_boundary.geojson` (already in the repo) | Overlay flag and overlay stories |
| Zoning rules, Milwaukee | Hand-coded (D6) in `reference/tod_zoning_rules_milwaukee.csv` (53 districts). Chapter 295 subchapters 5 to 9 come from Internet Archive copies (D2), captured 2025-03-10 to 2026-10-11, because the city site blocks scripts. RT5 comes from Common Council file 240997 | Current allowed homes per acre and floor area |
| Zoning rules, Madison | Hand-coded (D6) in `reference/tod_zoning_rules_madison.csv` (44 districts), from the city's Zoning District Summary of 13 March 2026 | Same |
| Homes in places not coded | 2020 census blocks (`HOUSING20`, already in the repo for the transit pipeline) | Existing homes, shared out to lots |
| Floor area per home | Madison Construction Summary permits (in the repo) and Milwaukee MPROP (section 3.4) | The floor-area cap on homes per acre |

Every rule row carries its code section, source URL, capture date and a status:
- `verified`: the number is printed in the source;
- `source_lead`: an assumption, or a rule set elsewhere, such as planned developments.

## 3. Method

### 3.1 Bands

Each lot is placed by the distance from its representative point (a point inside the lot) to the nearest stop of each kind, in EPSG:3071. The band is the strongest law that applies:

| Band | Rule | Modelled law (GATE1_PACKET.md section 3) | In definitions |
| --- | --- | --- | --- |
| `rapid_quarter` | within ¼ mile of a rail or rapid stop | 65 ft, FAR 3.0, 100 homes per acre | main, high, b_half, c_half |
| `rapid_half` | ¼ to ½ mile of a rail or rapid stop | 55 ft, FAR 2.5, 80 homes per acre | all |
| `bus15_quarter` | within ¼ mile of a 15-minute bus stop | 55 ft, FAR 2.5, 80 homes per acre | all |
| `bus20_quarter` | within ¼ mile of a 20-minute bus stop | as above | high, c_half |
| `bus15_half` | ¼ to ½ mile of a 15-minute bus stop | as above (sensitivity) | b_half, c_half |
| `bus20_half` | ¼ to ½ mile of a 20-minute bus stop | as above (sensitivity) | c_half |

The law's values sit in one place, `MODELLED_LAW` in `missing_middleware/tod/capacity.py`. Per AQ-049 G2-4 they stay on the SB 79 floors unless the case evidence says otherwise.

The law's homes per acre is the lower of:
- its density limit;
- its FAR × 43,560 sq ft ÷ floor area per home.

At the measured floor areas (section 3.4), the FAR binds in Madison: 86.4 homes per acre within ¼ mile of rail or rapid stops, and 72.0 in the 80-homes-per-acre bands. In Milwaukee the density limit binds: 100 and 80.

### 3.2 Coded cities (Milwaukee and Madison)

**Lots.** Records that share an identical outline (condominium units stacked on one lot) are merged, so land is counted once and their homes are summed. Madison's condominium notation records carry no homes of their own.

**Existing homes.**
- Milwaukee: MPROP `NR_UNITS` on residential land uses (codes 88xx) only. Hotel rooms and units recorded on commercial or parking records are not counted.
- Madison: `TotalDwellingUnits`.

**Eligible land.**
- Included: lots in residential, mixed-use, commercial, downtown or planned-development zoning.
- Excluded uses: institutions (schools, churches, colleges, tax-exempt government land), parks and open space, cemeteries, railways and utilities, and water.
- Streets are not parcels, so they drop out by construction.
- Industrial, park, institutional, agricultural and airport zoning is not eligible.
- Milwaukee's Industrial-Mixed (IM) district allows homes (LB3 standards), so it is coded as mixed use.
- **Single-family lots count**, because the modelled law applies to residential parcels (G2-8). `use_class` is kept so they can be filtered out.

**Current allowance per district** (`district_rule`):
- `density`: 43,560 ÷ minimum lot area per home (Milwaukee), or the top of the printed homes-per-acre range (Madison). Either is capped by a floor-area estimate.
- `far`: the code sets no density limit, so homes per acre = FAR × 43,560 ÷ floor area per home. Milwaukee downtown (C9) uses the base FAR coefficient of Table 295-705-1, without open-space bonuses.
- Floor-area estimate: the code's FAR where printed, else stories × maximum lot coverage. Stories come from the code (Madison) or from height ÷ 11 ft (Milwaukee). Where the code gives no coverage, 70% is used.
- Madison's TOD overlay: the overlay's maximum stories replace the base district's where higher (MGO 28.104). The March 2026 summary prints no change in homes per acre for the overlay, so density limits are unchanged there.
- `existing_is_rule`: planned developments (Milwaukee PD and RED; Madison PD, SEC, MXC, LMX and THV). The existing homes are the current allowance.
- `assumed_at_or_above_law`: Madison's downtown districts (DR1, DR2, UOR, UMX, DC). Their height comes from the Downtown Height Map, which is not coded, so they get no gain.

### 3.3 Places not coded (fallback, G2-9)

Every other municipality with lots in a band uses the fallback: 27 places in the main case and 32 in the widest definition, plus 1.4 acres of V12 parcels with no place name.
- **Lots and use.** V12 parcels outside the two cities. Use comes from the V12 class:
  - 1 residential, 2 commercial, or both: eligible. Wisconsin assesses apartment buildings of 4 or more homes as commercial.
  - Exempt (X1 to X4), manufacturing, agricultural, undeveloped (5) and other: not eligible, because their zoning is unknown.
- **Homes.** Each 2020 census block's `HOUSING20` is shared out to the eligible lots whose representative point lies in the block, in proportion to lot area; failing that, to all lots in the block.
  - 143,389 block homes were placed on fetched lots.
  - The main-case total for these places (58,272 homes) matches the transit pipeline's census count (57,322; 313,564 statewide minus 256,242 in the two cities) within 1.7%.
- **Rule.** Zoning is marked `not_coded`, with `rule_type = existing_density_fallback`. The current allowance equals the existing homes, and the law applies as elsewhere at the pooled floor area per home (1,467 sq ft).
- **Single-family estimate.** V12 has no single-family flag. A residential-class lot holding fewer than 1.5 of its block's homes is labelled `single_family_est` for the G2-8 sensitivity.

### 3.4 Floor area per home (measured)

The floor area per home is measured as the median over new buildings of 5 or more homes, 2018 to 2025, citywide (`reference/tod_floor_area_per_home.csv`):

| Area | Source | Buildings | Homes | Median sq ft per home | Middle half (25th to 75th percentile) |
| --- | --- | --- | --- | --- | --- |
| Madison | Construction Summary new-building permits BLDNCC/BLDNRC, use "Five and more family" or "Condominiums", 5 or more homes, conversions and alterations dropped: `BLDG_SQFT` ÷ Dwell | 253 | 16,928 | **1,512** | 1,363 to 1,786 |
| Milwaukee | MPROP 2026, buildings with 5 or more homes built 2018 to 2025: `BLDG_AREA` ÷ `NR_UNITS`. The city's permit file has no floor area or unit count | 73 | 5,730 | **1,192** | 999 to 1,353 |
| Pooled | both | 326 | 22,658 | **1,467** | 1,278 to 1,692 |

- Each city uses its own value. Places not coded use the pooled value.
- 1,000 sq ft, the Gate 2 placeholder, is kept as a sensitivity (`capacity_gain_sqft1000`).
- The two sources measure different things:
  - Madison's permit floor area is gross, so it includes structured parking, commercial space and common areas;
  - Milwaukee's assessor building area probably counts less of that.
- Madison permits were read citywide only. **Nothing was broken down by TOD overlay or area**; that count belongs to the pre-registered test.

### 3.5 Capacity gain

Capacity gain per lot = max(area × law − max(area × current, existing homes), 0), summed over lots.
- Existing homes are subtracted once, through the inner max.
- Lots already at or above the law get 0.
- `law_allowed_homes` = max(area × law, current allowance).
- `added_floor_area_sqft` = max(law FAR − current FAR, 0) × area. This is the "dose" for scaling cases per unit of added floor area (AQ-047 item 8). It is 0 for planned developments and for places not coded.

## 4. Outputs

`reference/tod_station_areas.csv` has one row per place × band × zoning district × use class × eligible flag. It has 2,309 rows and never one row per lot.

Columns:
- place: `city`, `county`, `zoning_coded` (1 for Milwaukee and Madison; 0 for the fallback);
- band: `band` and the definition flags `in_main`, `in_high`, `in_b_half`, `in_c_half`;
- the band's law: `law_homes_per_acre`, `law_far`, `law_height_ft`, plus `sqft_per_home` and `law_homes_per_acre_effective`;
- zoning: `district`, `zoning_class`, `rule_type`, `rule_status`;
- use: `use_class`, `eligible`;
- land: `lots` (count), `acres` (all lots), `eligible_acres`;
- homes: `existing_homes`, `existing_homes_eligible`, `current_allowed_homes`, `law_allowed_homes`;
- gain: `capacity_gain`, `capacity_gain_sqft1000` (1,000 sq ft sensitivity), `capacity_gain_excl_single_family` (G2-8 sensitivity), `added_floor_area_sqft`;
- Madison overlay: `acres_in_overlay`, `eligible_acres_in_overlay`, `share_acres_in_tod_overlay`.

To total one definition, filter `in_<key> == 1`.

Other output files:
- `reference/tod_station_area_summary.csv`: totals by definition for Milwaukee city, Madison city, the places not coded, and the state.
- `reference/tod_floor_area_per_home.csv`: the section 3.4 measurement.
- `reference/tod_madison_test_land.csv`: the land layer for the pre-registered Madison test ([MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md) section 2), for the whole city.
  - Areas: inside the overlay; outside it within ¼ mile of its edge; the rest of the city.
  - Eligible land follows the pre-registration: residential, mixed-use or commercial zoning (planned development included), excluding parks, water, streets, institutions, cemeteries, **and single-family use**. The file also gives the single-family acres excluded.
  - **No permits were read or counted** for this file. Counting permits by overlay is a separate, pre-registered step.

## 5. Results (run of 2026-10-26)

### 5.1 Main case

Eligible land only. Homes are counts and acres are parcel acres. Floor area per home is measured: 1,192 sq ft in Milwaukee, 1,512 in Madison and 1,467 in the places not coded.

| Area | Band | Eligible acres | Existing homes | Homes allowed now | Homes allowed by the law | Capacity gain (homes) |
| --- | --- | --- | --- | --- | --- | --- |
| Milwaukee | rail/rapid ≤ ¼ mile | 916 | 23,836 | 81,516 | 118,167 | 35,123 |
| Milwaukee | rail/rapid ¼–½ mile | 769 | 14,619 | 45,107 | 78,521 | 32,991 |
| Milwaukee | 15-minute bus ≤ ¼ mile | 12,512 | 146,172 | 353,220 | 1,027,098 | 668,062 |
| **Milwaukee** | **total** | **14,198** | **184,627** | **479,843** | **1,223,785** | **736,176** |
| Madison | rail/rapid ≤ ¼ mile | 2,419 | 32,386 | 124,536 | 229,398 | 103,629 |
| Madison | rail/rapid ¼–½ mile | 2,443 | 20,167 | 86,270 | 189,720 | 103,332 |
| Madison | 15-minute bus ≤ ¼ mile | 5,318 | 35,229 | 132,185 | 389,880 | 257,277 |
| **Madison** | **total** | **10,180** | **87,782** | **342,991** | **808,999** | **464,239** |
| Not coded (27 places) | rail/rapid ≤ ¼ mile | 728 | 3,858 | 3,858 | 64,884 | 61,026 |
| Not coded | rail/rapid ¼–½ mile | 1,018 | 5,183 | 5,183 | 75,560 | 70,378 |
| Not coded | 15-minute bus ≤ ¼ mile | 8,559 | 48,997 | 48,997 | 635,363 | 586,366 |
| **Not coded** | **total** | **10,305** | **58,039** | **58,039** | **775,808** | **717,769** |
| **State** | **total** | **34,682** | **330,448** | **880,873** | **2,808,591** | **1,918,185** |

The places not coded are mostly in Milwaukee County: 7,622 eligible acres and 526,266 homes of gain. Wauwatosa (1,941 acres) and West Allis (1,424 acres) lead. Dane County has 2,183 acres and 156,662 homes, led by Verona city (859 acres). Kenosha County has 318 acres and 21,720 homes; Waukesha County has 182 acres and 13,121 homes.

### 5.2 Changes from the first Gate 2 run (1,000 sq ft, no RT5, cities only)

- **RT5 (G2-6): no change.** File 240997 created RT5 at 800 sq ft of lot per home (54.5 homes per acre), 48 ft and 70% coverage. No lot is zoned RT5 yet in the 2026 MPROP or the zoning layer. The same file restates Table 295-505-2, and the coded RS and RT values match it.
  - The ADU ordinance (file 240999, passed 2025-07-15) adds accessory homes but does not change lot area per principal home.
  - The broader density ordinance (file 241391) is still in committee.
  - So Milwaukee's coded capacity is unchanged by the 2025 amendments.
- **Measured floor area.**
  - Milwaukee's gain rises slightly, from 734,569 to 736,176 homes (+0.2%). The larger home size lowers the current floor-area cap, while the law stays density-bound.
  - Madison's gain falls from 545,677 to 464,239 homes (−14.9%). At 1,512 sq ft the law's FAR binds below its density limit.
- **Places not coded** add 717,769 homes of gain on 10,305 eligible acres. The state main-case total becomes 1,918,185 homes, against 1,280,247 for the two cities alone at 1,000 sq ft.

### 5.3 Sensitivities (main case, capacity gain in homes)

| Area | Measured floor area (main) | 1,000 sq ft per home | Single-family lots excluded (G2-8) |
| --- | --- | --- | --- |
| Milwaukee | 736,176 | 734,569 | 332,350 |
| Madison | 464,239 | 545,677 | 223,008 |
| Not coded | 717,769 | 780,944 | 448,199 (estimated single-family) |
| **State** | **1,918,185** | **2,061,190** | **1,003,556** |

Single-family lots hold 55% of Milwaukee's main-case gain (403,827 of 736,176 homes) and 52% of Madison's (241,231 of 464,239).

### 5.4 Other definitions

State totals, measured floor area (`reference/tod_station_area_summary.csv`):

| Definition | Eligible acres | Capacity gain (homes) |
| --- | --- | --- |
| Main case | 34,682 | 1,918,185 |
| High case (20-minute bus ¼ mile; adds Eau Claire) | 40,026 | 2,266,107 |
| (b) all ½ mile, 15-minute | 48,703 | 2,827,344 |
| (c) all ½ mile, 20-minute | 57,534 | 3,411,868 |

### 5.5 Madison overlay and test land

4,628 of Madison's 10,180 main-case eligible acres (45%) lie inside the TOD overlay. The overlay raised stories but, per the city summary, not homes per acre. So most overlay land still gains under the modelled law: about 189,000 homes, an approximation from row-level overlay shares.

The pre-registered test land (single-family excluded):

| Area | Eligible acres | Existing homes on them | Single-family acres excluded |
| --- | --- | --- | --- |
| Inside the TOD overlay | 2,932 | 29,162 | 1,788 |
| Outside, within ¼ mile of the overlay edge | 1,226 | 13,031 | 1,537 |
| Rest of the city | 7,107 | 44,944 | 7,714 |

### 5.6 Cross-check with census blocks

Existing homes on all main-case lots run above the 2020 census homes near stops from the transit pipeline:
- Milwaukee: 186,743 against 175,633 (+6.3%);
- Madison: 87,951 against 80,609 (+9.1%).

This fits six years of building, since these are 2026 assessor counts against 2020 census counts. A lot-based rather than block-based edge also contributes. The places not coded use the census counts themselves; see section 3.3.

## 6. Coverage and known gaps

- **The fallback overstates gain relative to the coded method.** It treats existing homes as the current allowance. Where current zoning allows more than exists, the coded method subtracts the larger allowance. Applying the fallback rule to the coded cities would give:
  - Milwaukee: about 1,039,000 homes instead of 736,176 (+41%);
  - Madison: about 721,000 instead of 464,239 (+55%).

  These are approximations: law-allowed minus existing homes, by row. A per-place calibration from the coded cities, or coding the larger suburbs (Wauwatosa, West Allis), would narrow this. The fallback rows are marked `zoning_coded = 0` so the tool can trace them.
- **Fallback homes are 2020 counts**, shared by lot area within each block. Apartments and houses in the same block get the same homes per acre. A block straddling the 0.6-mile fetch edge puts all its homes on the fetched lots.
- **Code versions.** Milwaukee's subchapter 5 and 6 tables come from March 2025 copies (later captures are Cloudflare blocks). Legistar was checked for adopted ordinances through October 2026, searching titles for zoning, standards, density, dwelling, housing and residential. Only RT5 (file 240997) and ADUs (file 240999) change subchapter 5. Rezonings of single sites are not tracked.
  - Madison's rules come from the March 2026 summary, not the ordinance text.
  - The TOD overlay's density effect is not in the summary and is not coded: 3- and 4-home buildings in small residential districts (MGO 28.104).
  - The Housing Forward ordinance number is unconfirmed.
- **Simplifications.**
  - Madison uses the top of each density range.
  - Milwaukee uses the standard lot area per home, not the permanent-supportive-housing allowance.
  - Downtown Milwaukee FAR excludes open-space bonuses, and conditional-use extra stories are not counted.
  - 11 ft per story and 70% default coverage are parameters.
  - For 3-story Madison districts (TSS, NMX) the floor-area cap binds below the printed density.
- **Planned developments** are treated as allowing what exists. This overstates their gain if their plans already allow more.
- **Downtown Madison** is assumed at or above the law (no gain), because the Downtown Height Map is not coded.
- **Uncoded zoning inside Milwaukee:** district `X` (15 acres in the main case) and 4 acres with no zoning are reported on their own rows and are not eligible.
- **Use classes.**
  - Milwaukee's come from MPROP land-use groups, read from their codes; the city's documentation PDF was not script-readable.
  - Madison's come from `PropertyUse`.
  - Places not coded use the V12 class. Tax-exempt land counts as institutional, which leaves out some public housing.
- **Lot placement** uses one point per lot, so a large lot is wholly in or out of a band.

## 7. Privacy and licences

- **Privacy.**
  - Raw parcel files, which carry parcel ids, stay in git-ignored `data/raw/tod_capacity/`.
  - Committed tables are aggregated to district and use class. A test checks that no committed file has a parcel-id column, or a number of 8 or more digits outside URLs.
  - Owner, mailing-address and site-address fields are never requested.
  - The floor-area measurement reads only permit number, use, floor area, homes, description and date from Madison's permit report.
- **Licences and terms.**
  - Milwaukee MPROP and zoning: Creative Commons Attribution, City of Milwaukee.
  - V12: public records (Wis. Stat. 59.72), Wisconsin DOA and State Cartographer's Office.
  - Madison layers, summary and permit report: public records (D1); only aggregates are published.
  - Internet Archive copies of the Milwaukee code: D2.
  - Milwaukee Legistar file text: public law.
  - Census blocks: public domain.

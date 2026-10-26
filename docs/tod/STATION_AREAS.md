# TOD station areas: land, zoning and capacity (Milwaukee and Madison)

Written 2026-10-26 (TOD Gate 2, work package 4). This builds the land and zoning inputs that method B (capacity, feasibility and take-up) in [GATE1_PACKET.md](GATE1_PACKET.md) section 4.2 needs, for the City of Milwaukee and the City of Madison. Rules followed: AQ-044 to AQ-047 in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md); sources from [WI_CAPACITY_DATA.md](research/WI_CAPACITY_DATA.md); stops from [TRANSIT_PIPELINE.md](TRANSIT_PIPELINE.md).

All numbers are **capacity**: homes the rules would allow on paper. They are not forecasts of building. Feasibility and take-up come later (Gate 3).

## 1. How to run

```bash
uv run --all-extras python scripts/fetch_tod_parcels_zoning.py   # needs network; about 5 minutes
uv run --all-extras python scripts/build_tod_station_areas.py   # offline; about 20 seconds
bash scripts/test.sh                                            # includes tests/test_tod_capacity.py
```

`fetch_tod_parcels_zoning.py --only v12|mke_zoning|mad_zoning|docs` refetches one part. Raw files go to `data/raw/tod_capacity/` (git-ignored) with `manifest.json` (URL, access time, bytes, SHA-256, licence, feature counts, final Internet Archive capture URL, and hashes of the raw files reused from earlier fetches).

## 2. Sources

| Input | Source | Used for |
| --- | --- | --- |
| Parcel outlines, Milwaukee | Wisconsin V12 statewide parcels (2026 release), REST, only parcels intersecting a 0.6-mile buffer of the stops in `reference/tod_stops.csv` (219,954 parcels in Milwaukee County; 149,803 in the city). No owner or address fields requested | Parcel area (polygon area in EPSG:3071) |
| Homes, zoning and land use, Milwaukee | Master Property file (MPROP, 2026 assessment, CC BY), joined on TAXKEY = V12 PARCELID (99.8% of city V12 parcels in the buffer match) | Existing homes, zoning district, use class |
| Zoning polygons, Milwaukee | City zoning layer 11 (CC BY), same buffer | District for the 290 lots with no MPROP zoning |
| Parcels, Madison | City of Madison tax parcels (already in the repo): `TotalDwellingUnits`, `PropertyUse`, `ZoningAll`, outlines | Area, existing homes, use class, zoning district |
| Zoning polygons, Madison | City OPEN_DATA layer 9 (2,473 polygons) | Fallback district (not needed in this run: every Madison parcel had `ZoningAll`) |
| TOD overlay, Madison | `data/raw/madison_tod/tod_boundary.geojson` (already in the repo) | Overlay flag and overlay stories |
| Zoning rules | Hand-coded (owner decision D6): `reference/tod_zoning_rules_milwaukee.csv` (52 districts) from Chapter 295 subchapters 5 to 9 (Internet Archive copies, D2, captured 2025-03-10 to 2026-10-11; the city site blocks scripts); `reference/tod_zoning_rules_madison.csv` (44 districts) from the city's Zoning District Summary of 13 March 2026 | Current allowed homes per acre and floor area |
| V12 parcels, Dane County | Same service and buffer (65,319 parcels) | Fetched for the suburbs; not used yet (section 6) |

Every rule row carries its code section, source URL, capture date and a status: `verified` (number printed in the source) or `source_lead` (an assumption or a rule set elsewhere, such as planned developments).

## 3. Method

**Station-area bands.** Each lot is placed by the distance from its representative point (a point inside the lot) to the nearest stop of each kind, in EPSG:3071. The band is the strongest law that applies:

| Band | Rule | Modelled law (GATE1_PACKET.md section 3) | In definitions |
| --- | --- | --- | --- |
| `rapid_quarter` | within ¼ mile of a rail or rapid stop | 65 ft, FAR 3.0, 100 homes per acre | main, high, b_half, c_half |
| `rapid_half` | ¼ to ½ mile of a rail or rapid stop | 55 ft, FAR 2.5, 80 homes per acre | all |
| `bus15_quarter` | within ¼ mile of a 15-minute bus stop | 55 ft, FAR 2.5, 80 homes per acre | all |
| `bus20_quarter` | within ¼ mile of a 20-minute bus stop | as above | high, c_half |
| `bus15_half` | ¼ to ½ mile of a 15-minute bus stop | as above (sensitivity) | b_half, c_half |
| `bus20_half` | ¼ to ½ mile of a 20-minute bus stop | as above (sensitivity) | c_half |

The main case is rapid ½ mile plus 15-minute bus ¼ mile. The law values sit in one place, `MODELLED_LAW` in `missing_middleware/tod/capacity.py`, so they can be revised from the case evidence (AQ-047 item 1). The law's homes per acre is its density capped by its FAR (both bind at the density here).

**Lots.** Records that share an identical outline (condominium units stacked on one lot) are merged so land is counted once and their homes are summed. Madison's condominium notation records carry no homes of their own.

**Existing homes.** Milwaukee: MPROP `NR_UNITS` on residential land uses (codes 88xx) only; hotel rooms and units recorded on commercial or parking records are not counted. Madison: `TotalDwellingUnits`.

**Eligible land.** Lots in residential, mixed-use, commercial, downtown or planned-development zoning, excluding institutional uses (schools, churches, colleges, tax-exempt government land), parks and open space, cemeteries, railways and utilities, and water. Streets are not parcels, so they are excluded by construction. Industrial, park, institutional, agricultural and airport zoning is not eligible. **Single-family lots count** (the modelled law applies to residential parcels); `use_class` is kept so they can be filtered out. Milwaukee's Industrial-Mixed (IM) district allows homes (LB3 standards) and is coded as mixed use.

**Current allowance per district** (`district_rule`):
- `density`: 43,560 ÷ minimum lot area per home (Milwaukee) or the top of the printed homes-per-acre range (Madison), capped by a floor-area estimate.
- `far`: no density limit in the code; homes per acre = FAR × 43,560 ÷ 1,000 sq ft per home. Milwaukee downtown (C9) uses the base FAR coefficient of Table 295-705-1 without open-space bonuses.
- Floor-area estimate: the code's FAR where printed, else stories × maximum lot coverage. Stories come from the code (Madison) or height ÷ 11 ft (Milwaukee). Where the code gives no coverage, 70% is used.
- Inside Madison's TOD overlay, the overlay's maximum stories replace the base district's where higher (MGO 28.104). The March 2026 summary prints no change in homes per acre for the overlay, so density limits are unchanged there.
- `existing_is_rule`: planned developments (Milwaukee PD and RED; Madison PD, SEC, MXC, LMX, THV): the existing homes are the current allowance.
- `assumed_at_or_above_law`: Madison's downtown districts (DR1, DR2, UOR, UMX, DC), whose height comes from the Downtown Height Map, which is not coded. They get no gain.

**Capacity gain per lot** = max(area × law − max(area × current, existing homes), 0), then summed. Existing homes are subtracted once, through the inner max. Lots already at or above the law get 0. `law_allowed_homes` = max(area × law, area × current). `added_floor_area_sqft` = max(law FAR − current FAR, 0) × area, the "dose" for scaling cases per unit of added floor area (AQ-047 item 8); it is blank (0) for planned developments.

## 4. Outputs

`reference/tod_station_areas.csv`: one row per city × band × zoning district × use class × eligible flag (1,990 rows; never one row per lot). Columns: band and definition flags (`in_main`, `in_high`, `in_b_half`, `in_c_half`), the band's law (`law_homes_per_acre`, `law_far`, `law_height_ft`), `district`, `zoning_class`, `rule_type`, `rule_status`, `use_class`, `eligible`, `lots` (count), `acres` (all lots), `eligible_acres`, `existing_homes`, `existing_homes_eligible`, `current_allowed_homes`, `law_allowed_homes`, `capacity_gain`, `added_floor_area_sqft`, `acres_in_overlay`, `eligible_acres_in_overlay`, `share_acres_in_tod_overlay` (Madison only; 0 in Milwaukee). Sum a definition by filtering `in_<key> == 1`.

`reference/tod_madison_test_land.csv`: the land layer for the pre-registered Madison test ([MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md) section 2), for the whole city: inside the overlay, outside it within ¼ mile of its edge, and the rest of the city. Eligible follows the pre-registration: residential, mixed-use or commercial zoning (planned development included), excluding parks, water, streets, institutions and cemeteries, **and excluding single-family use**. The file also gives the single-family acres excluded. **No permits were read or counted** for this file; the permit count by overlay is a separate, pre-registered step.

## 5. Results (run of 2026-10-26)

**Main case** (eligible land only; homes are counts; acres are parcel acres):

| City | Band | Eligible acres | Existing homes | Homes allowed now | Homes allowed by the law | Capacity gain (homes) |
| --- | --- | --- | --- | --- | --- | --- |
| Milwaukee | rail/rapid ≤ ¼ mile | 916 | 23,836 | 92,702 | 127,428 | 33,574 |
| Milwaukee | rail/rapid ¼–½ mile | 769 | 14,619 | 49,390 | 82,723 | 32,942 |
| Milwaukee | 15-minute bus ≤ ¼ mile | 12,512 | 146,172 | 356,131 | 1,030,000 | 668,054 |
| **Milwaukee** | **total** | **14,198** | **184,627** | **498,222** | **1,240,150** | **734,569** |
| Madison | rail/rapid ≤ ¼ mile | 2,419 | 32,386 | 145,206 | 275,945 | 129,479 |
| Madison | rail/rapid ¼–½ mile | 2,443 | 20,167 | 99,254 | 219,234 | 119,859 |
| Madison | 15-minute bus ≤ ¼ mile | 5,318 | 35,229 | 135,392 | 432,165 | 296,339 |
| **Madison** | **total** | **10,180** | **87,782** | **379,852** | **927,344** | **545,677** |

Reading the table:
- Eligible land is 14,198 of 22,819 parcel acres in Milwaukee's main-case area (62%) and 10,180 of 15,679 in Madison's (65%). The rest is parks, institutions, industry, cemeteries and rail land.
- Current zoning allows 35.1 homes per eligible acre in Milwaukee (498,222 homes ÷ 14,198 acres) and 37.3 in Madison (379,852 ÷ 10,180). Existing density is 13.0 and 8.6 homes per eligible acre.
- Capacity gain per eligible acre is 51.7 homes in Milwaukee (734,569 ÷ 14,198) and 53.6 in Madison (545,677 ÷ 10,180).
- Single-family lots hold 55% of Milwaukee's gain (403,665 of 734,569 homes) and 51% of Madison's (278,264 of 545,677).
- 4,628 of Madison's 10,180 eligible acres (45%) lie inside the TOD overlay. The overlay raised stories but, per the city summary, not homes per acre, so most overlay land still gains under the modelled law (about 228,000 homes; this is approximate, from row-level overlay shares).
- Rules marked `source_lead` (planned developments, downtown Madison) cover 733 of Milwaukee's eligible acres (48,715 homes of gain) and 1,898 of Madison's (126,302 homes).

**Other definitions** (eligible acres; capacity gain in homes):

| Definition | Milwaukee | Madison |
| --- | --- | --- |
| Main case | 14,198 acres; 734,569 | 10,180 acres; 545,677 |
| High case (20-minute bus ¼ mile) | 16,949 acres; 908,146 | same as main (no 20-minute-only routes) |
| (b) all ½ mile, 15-minute | 17,896 acres; 969,111 | 13,154 acres; 730,008 |
| (c) all ½ mile, 20-minute | 22,184 acres; 1,244,437 | same as (b) |

**Madison test land layer** (pre-registered definition, single-family excluded):

| Area | Eligible acres | Existing homes on them | Single-family acres excluded |
| --- | --- | --- | --- |
| Inside the TOD overlay | 2,932 | 29,162 | 1,788 |
| Outside, within ¼ mile of the overlay edge | 1,226 | 13,031 | 1,537 |
| Rest of the city | 7,107 | 44,944 | 7,714 |

**Cross-check with census blocks.** Existing homes on all main-case lots (186,743 in Milwaukee; 87,951 in Madison) are 6.3% and 9.1% above the 2020 census homes near stops from the transit pipeline (175,633 and 80,609; `reference/tod_near_stop_homes_by_muni.csv`). The direction fits six years of building since 2020 (2026 assessor counts against 2020 census counts) and a lot-based rather than block-based edge.

## 6. Coverage and known gaps

- **Two cities only.** The suburbs (16.7% of homes near stops in the main case, WI_CAPACITY_DATA.md) have no coded zoning. V12 parcels for both counties are fetched, but V12 has no home counts or zoning. Per the Gate 1 rule (T9) and WI_CAPACITY_DATA section 7, they fall back to existing density (census-block homes per acre of V12 parcel land) until their zoning is coded; that step is not built here.
- **Code versions.** Milwaukee residential and commercial tables come from March 2025 copies; later captures are Cloudflare blocks. The 2025 Growing MKE amendments (including a new RT5 district) are not reflected; no RT5 lot appears in MPROP or the zoning layer yet, but changed standards in existing districts would be missed. Madison rules come from the March 2026 summary, not the ordinance text; the TOD overlay's density effect (3- and 4-home buildings in small residential districts, MGO 28.104) is not in the summary and is not coded, and the Housing Forward ordinance number is unconfirmed.
- **Simplifications.** Top of Madison's density range; Milwaukee's standard lot area per home (not the permanent-supportive-housing allowance); downtown Milwaukee FAR without open-space bonuses; conditional-use extra stories not counted; 11 ft per story, 70% default coverage and 1,000 sq ft per home are parameters in `capacity.py`. For 3-story Madison districts (TSS, NMX) the floor-area cap binds below the printed density (91 vs 124 homes per acre in TSS).
- **Planned developments** (Milwaukee PD and RED, Madison PD and master-plan districts) are treated as allowing what exists. This overstates their gain if their plans already allow more.
- **Downtown Madison** is assumed at or above the law (no gain) because the Downtown Height Map is not coded.
- **Uncoded or unknown zoning:** Milwaukee district `X` (15 acres in the main case) and 4 acres with no zoning are reported on their own rows, not eligible.
- **Use classes** for Milwaukee come from MPROP land-use groups read from their codes (the city's documentation PDF was not script-readable); for Madison from `PropertyUse`. Tax-exempt land is treated as institutional, which excludes some public housing.
- **Lot placement** uses one point per lot, so a large lot is wholly in or out of a band.

## 7. Privacy and licences

Raw parcel files (with parcel ids) stay in git-ignored `data/raw/tod_capacity/`. Committed tables are aggregated to district and use class; a test checks that no committed file has a parcel-id column or an 8-digit-or-longer number outside URLs. Owner, mailing-address and site-address fields are never requested. Milwaukee MPROP and zoning: Creative Commons Attribution, City of Milwaukee. V12: public records (Wis. Stat. 59.72), Wisconsin DOA and State Cartographer's Office. Madison layers and summary: public records (D1). Internet Archive copies of the Milwaukee code: D2.

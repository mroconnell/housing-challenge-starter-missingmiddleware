# Wisconsin towns with no zoning

**Plain summary (2026-10-24).** Of Wisconsin's 1,243 towns, **239 have no general zoning**. Neither county zoning nor their own town zoning applies to them. They hold **76,633 one-unit detached homes**, about 4% of the state's 1.84 million. These are the towns in the AQ-026 `no_zoning` class.

| Status | Towns | One-unit detached homes |
| --- | ---: | ---: |
| Under county general zoning | 742 | 442,692 |
| Own town zoning | 248 | 195,270 |
| No general zoning | 239 | 76,633 |
| Could not be classified | 14 | 3,799 |
| **Total** | **1,243** | **718,394** |

Unzoned towns are mostly small and rural, with a median of 269 homes. Five counties hold a third of them: Clark (29), Taylor (17), Chippewa (16), Vernon (14) and Rusk (14). In 159 of the 239 the county does have general zoning, but the town board never adopted it. The largest unzoned towns are Sugar Camp (Oneida, 1,490 homes), Nasewaupee (Door, 1,117), Georgetown (Polk, 1,102), Chetek (Barron, 1,059) and Egg Harbor (Door, 1,038).

**Counties with no county general zoning (15):** Brown, Clark, Crawford, Fond du Lac, Juneau, Kewaunee, Milwaukee, Ozaukee, Pepin, Rock, Sheboygan, Taylor, Vernon, Washington and Wood. In seven of them every town has its own zoning: Brown, Fond du Lac, Kewaunee, Ozaukee, Rock, Sheboygan and Washington (Milwaukee County has no towns). The unzoned towns in these counties are therefore in Clark, Crawford, Juneau, Pepin, Taylor and Vernon. Wood County is a special case, described below.

**Fourteen towns could not be classified.** They hold 3,799 homes and stay `unknown`; none was guessed.
- **Ten Wood County towns:** a 1934 county ordinance applies there, and it is unclear whether it counts as general zoning.
- **Three Taylor County towns** (Chelsea, Hammel, Molitor): the sources conflict.
- **Platteville town** (Grant County): the county leaves it off its list of zoned towns, but DOA codes it county-zoned.

If the ten Wood towns are treated as unzoned, the unzoned count rises to 249 towns and 79,032 homes.

Files: [reference/wi_town_zoning_status.csv](../../reference/wi_town_zoning_status.csv) (one row per town), built by [scripts/build_wi_town_zoning.py](../../scripts/build_wi_town_zoning.py) with [missing_middleware/foundation/town_zoning.py](../../missing_middleware/foundation/town_zoning.py) and tested in [tests/test_wi_town_zoning.py](../../tests/test_wi_town_zoning.py).

## Definition

The owner's request of 2026-10-24 and AQ-026 define when a town is zoned. A town is zoned if either of these applies:
- its county adopted general (comprehensive) zoning under Wis. Stat. 59.69 and the town board approved it (`county_general`);
- the town adopted its own general zoning under village powers, s. 60.62 / 62.23(7), including s. 60.61 (`town_own`).

Otherwise the town is `unzoned`. Shoreland, floodplain, airport, farmland-preservation-only and county-forest zoning do not count. Interim zoning under 62.23(7)(da) is counted as own town zoning and noted as such.

## Source and method

1. **Statewide inventory.** The base source is the Wisconsin Department of Administration's *Comp Plan and Land Regs Inventory* spreadsheet (https://doa.wi.gov/DIR/Comp-Plan-and-Land-Regs-Inventory.xlsx). It has one row per county, city, village and town. Its "General Zoning" field is `county`, `municipal` or `no`, and its schema sheet uses the same statutory definition as above, also excluding special-purpose zoning.
   - doa.wi.gov timed out from this network, so the Internet Archive capture of 2025-02-15 was used (https://web.archive.org/web/20250215161415id_/https://doa.wi.gov/DIR/Comp-Plan-and-Land-Regs-Inventory.xlsx).
   - The workbook was last modified 2025-01-30; its sha256 is `2c7c3855a220…`. The raw file and `SOURCE.json` are in `data/raw/wi_doa_land_regs_inventory/` (git-ignored).
   - The accompanying report, the [2023 Comp Plan and Land Regs Inventory Report](https://doa.wi.gov/DIR/2023-Comp-Plan-and-Land-Regs-Inventory-Report.pdf) (data as of June 2023), counted 746 county-zoned, 245 own-zoned and 253 unzoned towns. The 2025 file has 743, 244 and 255.
2. **Join.** The spreadsheet's 5-digit FIPS code is the county-subdivision code, which is unique statewide. All 1,243 towns in `areas.parquet` matched it:
   - Blooming Grove's FIPS is stored as a number; it is zero-padded.
   - Rib Falls (Marathon) is listed by DOA as a "Village". It is a town in TIGER 2024; it was matched and the mismatch noted.
3. **Spot checks.** County and town sources were checked for 12 counties, chosen to cover counties with many unzoned towns and the counties DOA itself flagged as ambiguous: Barron, Chippewa, Clark, Crawford, Grant, Juneau, Monroe, Pepin, Rusk, Taylor, Vernon and Wood. Where a dated county or town source names a town with the same status as DOA, the row is marked `verified` (84 towns). All other rows keep `source_lead`, meaning they rest on the DOA inventory only.
4. **Corrections.** Where a newer or more specific source disagrees with DOA, the row was changed and both sources are recorded in `notes`:

| Town (county) | DOA 2025 | Now | Reason |
| --- | --- | --- | --- |
| Eastman (Crawford) | county | unzoned | Crawford County "is not comprehensively zoned"; the town's ordinance list has no zoning ordinance |
| Angelo (Monroe) | no | town_own (interim) | Interim zoning ordinance, effective 2026-07-01 |
| Little Black (Taylor) | no | town_own | Town zoning code adopted 2017 |
| Cameron, Marshfield (Wood) | no | town_own | Wood County lists both among its 12 towns with their own zoning |
| Platteville (Grant) | county | unknown | Grant County's 2026 list of county-zoned towns omits it; part of the town is under city extraterritorial zoning |
| Chelsea, Hammel, Molitor (Taylor) | no | unknown | A 2013 UW-Extension guide says these towns have their own planning/zoning; DOA says none |
| 10 Wood towns | no | unknown | See below |

**Spot-check agreement.**
- Chippewa, Rusk and Barron agreed with DOA exactly.
- Grant agreed except Platteville.
- Monroe agreed except Angelo, which adopted zoning after the DOA file.
- Crawford agreed except Eastman.
- Taylor, Vernon, Juneau and Pepin were confirmed to have no county general zoning.

## Wood and Clark counties

- **Wood County.** Its 1934 zoning ordinance (Ord. 700) was adopted under the county zoning statute and approved by the town boards, and the county says it is still in effect in all 22 towns.
  - It has two districts:
    - a Forestry & Recreation district, where dwellings are barred;
    - an Unrestricted district, where any lawful use is allowed.
  - It has no lot or setback standards.
  - DOA does not count it as general zoning. The district map was not obtained.
  - Twelve Wood towns have their own zoning (DOA listed 10). The other 10 are `unknown`: Arpin, Cary, Cranmoor, Hansen, Hiles, Milladore, Remington, Richfield, Sherry and Wood, with 2,399 homes.
  - The owner may decide that this ordinance is not general zoning. In that case these 10 towns become `unzoned`.
- **Clark County.** Its 1934 zoning survives only as "Zoning of County-Owned Land" (Code ch. 22, art. X). It does not regulate private land in towns, so Clark's 29 towns without their own zoning stay `unzoned`, with a note.

## Caveats

- **The base file predates a wave of 2026 town ordinances.** In 2026 several unzoned towns adopted or planned interim zoning or moratoria, mostly against data centers:
  - Angelo (Monroe) adopted interim zoning; it is reclassified here.
  - Big Bend (Rusk) reportedly adopted a moratorium; its type is not verified.
  - About nine Vernon County towns planned moratoria.
  - Vernon County is drafting its first county zoning ordinance, which towns would opt into.

  Some towns now coded `unzoned` may therefore have interim zoning today. Because interim zoning freezes existing uses, it can be more restrictive than no zoning.
- **Town zoning is the least-checked group.** Own-town-zoning rows outside the spot-checked counties rest on DOA alone (227 of 248 are `source_lead`). DOA missed at least three own-zoned towns (Little Black, Cameron, Marshfield), so a few more `unzoned` rows may in fact be zoned. The opposite error, a town wrongly coded as zoned, was found once (Eastman).
- **Some unzoned towns still have rules.** A town can have no zoning yet still run a building-permit ordinance with minimum lots or setbacks; Kildare (Juneau) is an example. Such towns remain `unzoned` under the definition above. Septic (POWTS), shoreland and floodplain rules apply in all towns.
- **Most county web pages carry no date.** For those, `source_date` records "undated (read 2026-10-24)".

## Reproduce

```
uv run python scripts/build_wi_town_zoning.py --fetch   # download the DOA workbook (Wayback), then build
uv run python scripts/build_wi_town_zoning.py           # rebuild from the cached workbook
bash scripts/test.sh                                    # includes tests/test_wi_town_zoning.py
```

Columns of `wi_town_zoning_status.csv`:
- `area_id` (`muni:` + GEOID);
- `geoid`;
- `name`;
- `county_name`;
- `zoning_status` (`county_general` / `town_own` / `unzoned` / `unknown`);
- `source_url`;
- `source_date`;
- `verification` (`verified` / `source_lead` / `unknown`);
- `notes`.

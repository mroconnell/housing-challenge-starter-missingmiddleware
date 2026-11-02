# Stop table (reference/tod_stop_table.csv)

Owner ask (2026-11-02): basic data by stop for a possible stop-based reform model, with sanity checks. No model is
fitted here. Built by `scripts/build_tod_stop_table.py`:

    .venv/bin/python scripts/build_tod_stop_table.py            # build, write, print the checks
    .venv/bin/python scripts/build_tod_stop_table.py --checks   # checks only, from the written table

## Which stops

One row per stop per case.

| Set | Cases | Stops from | Role values |
|---|---|---|---|
| Station-area lot study (16 places) | every `data/processed/tod_station_area/lots_*.parquet` case: LA TOC 2017, San Diego 2021, Honolulu 2017, Chicago 2015 and 2022, New York (23 rezonings), Philadelphia (83 rezonings), Denver 2018, Portland 2020, Austin 2009, Salt Lake City 2010, Seattle Othello 2012 and Mount Baker 2014, Bellevue 2009, Saint Paul 2011, Charlotte 2019 | `run_tod_station_checks.stops_for(case)` (LA, San Diego, Honolulu, Chicago, cluster cases); New York and Philadelphia: `station_cases/nyc_phl.stops(city)` with the group each stop has in that case's lot table | reform, comparison |
| Candidate | seattle_roosevelt_2012 (`candidates/`) | `cluster_north.stops_for` | reform, comparison |
| Wisconsin | wi_milwaukee, wi_madison (lot table `wi_lots_station.parquet`), wi_other (Kenosha, Wauwatosa, Shorewood Hills, Sun Prairie: no lot table) | `reference/tod_stops.csv` flag_a_rapid == 1 (266 stop points) merged as `build_tod_station_wisconsin.stations()` | wisconsin |

`reference/tod_station_area_stations.csv` is an earlier stage's list. Its cases la_cornfield_arroyo_seco_2013,
la_warner_center_2013, madison_tod_overlay_2023 and Milwaukee "none" have no lot table, so they are not rows here; their
stations are the same NTM / Wisconsin stations already in the table (LA TOC and Wisconsin rows).

New York and Philadelphia: the same station appears once per rezoning case (the lot vintage and the reform/comparison
group differ by case). Use `stop_key` (city + station point rounded to 1 m) to get one row per physical station.

## How a station is built (unchanged from the lot tables)

Stop points (NTM platforms, parent stations and entrances where the source has them; agency station points
elsewhere) within 150 m are merged: the union of 75 m buffers, each connected part is one station, the station point is
the part's centroid (`geom_extra_station.merge_within / merge_stops`). Lot distance = from the lot's representative
point to the station point. The script rebuilds the member points from the same source and filters the case used and
matches each station point to its rebuilt part (`member_match_m`, 0.00 m everywhere means the rebuild is exact).

## Columns

Units: m = metres; acres; $ = dollars as held in each lot table (assessed values differ by city and year, compare
within a city only). Bands: q1 = 0–¼ mile (≤ 402 m), q2 = ¼–½ mile (402–805 m), m1 = ½–1 mile (805–1,609 m).
Suffix _q = lots within ¼ mile; _h = lots within ½ mile (q1 + q2).

### Identity
| Column | Meaning |
|---|---|
| case, city, role | case id; city; reform / comparison / wisconsin |
| stop_id | the stop's id in that case's lot table (New York, Philadelphia: city-wide id; Wisconsin: lot-table id, wi_other new ids) |
| stop_name, place | name of the member point nearest the station point (blank in Wisconsin: tod_stops.csv has no names); Census place |
| lat, lon | station point (centroid of the merged part), WGS 84 |
| stop_key | city + station point rounded to 1 m: the physical-station key across cases |
| comparison_kind, excluded_reason, downtown | carried from cluster_north stops (Seattle, Bellevue, Saint Paul, Charlotte) |
| agency, gtfs_stop_ids, in_lot_table | Wisconsin only |

### Station form
| Column | Meaning |
|---|---|
| mode | heavy rail / light rail / light rail/trolley (Philadelphia) / streetcar / commuter rail / BRT, from the source's stop type |
| stop_type_text | the stop type the case builder carried |
| n_points_merged | stop points merged into the station |
| n_platform_points, n_entrance_points, n_parent_points | members by type: platform/stop, entrance (GTFS location_type 2), parent station point (location_type 1) |
| point_types, point_type_source | the counts as text, and where the type comes from (NTM location_type; city/agency layer points are one point per station or station-line) |
| footprint_m | largest distance between two merged points (m) |
| n_names_merged, names_merged | distinct member names (several names = several stations or a chain merged) |
| member_match_m | distance from the stored station point to the rebuilt part's centroid (m) |
| grade, grade_source | underground / elevated / open cut / embankment / at grade / unknown. New York: NYC subway station layer Construction_type (Sub, Elv/Via, Cut, Fil); LA B/D Lines (NTM "Subway, Metro"): underground; Honolulu Skyline: elevated; BRT and streetcar: at grade (street running). Elsewhere unknown. OpenStreetMap was not used (ODbL share-alike, owner decision D5) |
| lines | New York: the station-line names merged |
| opening_year, opening_year_source | Denver: RTD layer YEAR_OPEN (earliest at the station); Seattle: Link opening years in cluster_north (Roosevelt 2021); Saint Paul Green Line 2014; Austin MetroRail 2010; else unknown |

### Service
| Column | Meaning |
|---|---|
| tph_peak | trips per hour at the station, 07:00–09:00, both directions, all lines of the mode family (unique GTFS trips with a stop time at a GTFS stop within 200 m of the station point, ÷ 2) |
| tph_midday | the same, 10:00–14:00, ÷ 4 |
| tph_source, gtfs_stops_matched | feed, weekday used (the Tuesday nearest 2026-11-10 inside the feed's calendar), GTFS stop points matched |
| sld_d4c_station_bg | EPA Smart Location Database D4c (aggregate transit service frequency, peak, per hour) of the block group of the lot nearest the station point — the fallback, and the only service measure for Madison |

Feeds (data/raw/tod_stop_table/manifest.json; data/raw/tod_net_coverage/gtfs; data/raw/tod_transit/gtfs): MTA subway;
SEPTA Regional Rail + SEPTA metro/trolley (from the bus feed, route types 0/1, overnight replacement buses left out);
CTA + Metra; LA Metro rail + G Line (route 901, bus feed); MTS Trolley; Honolulu Skyline; RTD rail; TriMet MAX,
Streetcar, WES; UTA TRAX/S-Line; CapMetro route 550; Sound Transit Link; Metro Transit light rail; CATS LYNX/CityLYNX.
Wisconsin: exact GTFS stop ids of the station's members, all routes stopping there (MCTS feed copy covers 2025-03 to
2025-08, so MCTS uses 2025-08-19; The Hop, Kenosha 2026-11-10). **Madison Metro GTFS is not used (AQ-045)**: tph blank,
use sld_d4c_station_bg.

### Ridership (average weekday)
| Column | Meaning |
|---|---|
| ridership_weekday_2019, ridership_weekday_latest, ridership_year_latest | average weekday boardings or entries |
| ridership_measure, ridership_note | what the number is; why blank |

| City | Measure | Source (data/raw/tod_stop_table/ridership/, data/raw/cta_ridership/) |
|---|---|---|
| New York | entries (not boardings), 2019 and 2024, subway only; a station complex matched to several stations is split equally | MTA hourly ridership, aggregated by complex per weekday (data.ny.gov) |
| Chicago | CTA 'L' entries, 2019 weekday ('W') mean; Metra blank | City of Chicago portal |
| Philadelphia | Regional Rail boardings (2019 counted; 2024 SEPTA estimate), all lines and directions summed; trolley average weekday ons, summer 2025 (in "latest"); Market-Frankford / Broad Street blank (the only file's licence bars copying) | OpenDataPhilly |
| Saint Paul | Green Line average weekday ons, both directions, by station name (latest release; period not stated) | Metropolitan Council |
| Salt Lake City | TRAX/S-Line average weekday boardings, mean of monthly averages, summed over lines; 2019 and 2025 | UTA open data |
| Others | blank: Sound Transit (dashboard/PDF), RTD (dashboard), TriMet (PDF), LA Metro (line totals), CATS (2018 PDF), MTS (none open), CapMetro (raw APC only), Skyline (system totals), MCTS/Hop (system totals), Madison (none) | — |

Measures differ by city; compare ranks within a city only.

### Surroundings (from the case's lot table; each lot counts once, at its nearest stop as assigned in the lot table)
| Column | Meaning |
|---|---|
| lots_{q1,q2,m1}, acres_{…} | all lots in the band and their acres |
| dev_lots_{…}, dev_acres_{…} | developable: private (public == False) and not a park / cemetery / utility / right-of-way use (table below) |
| vacant_dev_lots/acres_{…} | developable lots with building value = 0 |
| underused_dev_lots/acres_{…} | developable lots with building value < land value (bldg_to_land < 1; **includes the vacant lots**) |
| stacked_dup_lots_{…} | records that repeat another record's lot point (to 1 m) and acres: condominium units that each carry the whole parcel's area (LA County, Charlotte, San Diego, Chicago) |
| acres_dedup_{…}, dev_acres_dedup_{…}, vacant_dev_acres_dedup_{…}, underused_dev_acres_dedup_{…} | the same acres counting each stacked parcel once — **use these for land amounts**; the plain acres columns repeat the lot tables as they are |
| homes_per_acre_{q,h} | existing homes ÷ lot acres with stacked records counted once (homes_existing of the lot table: homes standing before the case's before-window) |
| median_land_value_per_acre_{q,h} | median over lots of land value ÷ acres (lots with acres > 0 and land value > 0) |
| share_lots_vacant_{q,h} | share of lots with a building value that have building value 0 |
| tract_median_home_value_{q,h}, tract_median_rent_{q,h} | median over lots of the lot's tract ACS v_c04 / v_c01 (lot-weighted) |
| jobs_per_acre_{q,h}, transit_job_access_{q,h} | acre-weighted mean of the lots' block-group SLD D1C and D5br |
| share_lots_in_reform_area_{q,h} | share of the lots in the case's reform area (coverage) |
| dist_recomputed_max_diff_m | largest gap between the lot table's dist_m and the distance recomputed here (m); Wisconsin ≈ 9 m because its lot table measured in EPSG 3071 and this table in EPSG 5070 |

### Reform history
| Column | Meaning |
|---|---|
| reform_year | the case's reform year (Wisconsin: 2025, the law's start used in the lot table) |
| rezonings_within_quarter, n_rezonings_within_quarter | New York and Philadelphia only: every lot-model rezoning (case id and year) with a reform-area lot within ¼ mile of the station point, and their count (the same for all cases of a station) |

### Distance-definition check (all stops)
Stop assignment kept as in the lot table; only the distance changes, from the station point to the **nearest merged
member point** (platform, entrance or parent point).
| Column | Meaning |
|---|---|
| distchk_lots_band_changed, distchk_acres_band_changed | lots (and their acres) whose band changes |
| distchk_lots_{q1,q2,m1}_centroid / _nearest, distchk_acres_… | lots and acres per band under each definition |
| distchk_max_shift_m | largest drop in a lot's distance (m) |

## Developable land: use mapping by city

| City | Use field in the lot table | Removed besides public lots | Too coarse? |
|---|---|---|---|
| New York | MapPLUTO LandUse | 07 transportation & utility, 09 open space & outdoor recreation; public = OwnerType C/M/O | no |
| Philadelphia | OPA building description | Fairmount Park / city park, cemetery, public utility, railroad, right of way, golf; public = fully tax-exempt (includes non-profits) | partly: exempt non-profits also removed |
| Chicago | Cook County class code | RR, EX | **yes**: parks, cemeteries sit inside EX (also public); utilities not separable |
| Los Angeles | LA County UseType (8 classes) | Government (stand-in for public: the public flag is empty in the lot table) | **yes**: parks/cemeteries not separable from private Recreational / Institutional |
| San Diego | assessor land-use code | none (no code dictionary held); tax-exempt removed as public | **yes** |
| Honolulu | none | none | **yes: no use, no owner type** — developable = all lots |
| Austin | none | none | **yes: no use, no owner type** — developable = all lots |
| Denver | assessor class text | Denver park, park, golf, cemetery, utility, railroad, right of way | no |
| Portland | property use text | park, golf, cemetery, utility, railroad, right of way | no |
| Salt Lake City | county class (14) | Tax Exempt - Government | **yes**: parks, utilities, cemeteries not separable |
| Seattle, Bellevue | King County present use | Park, Public; cemetery; utility (public and private); right of way; easement; golf | no |
| Saint Paul | Ramsey County use text | cemetery/graveyard, railroad, utility, park, golf, right of way | no |
| Charlotte | Mecklenburg land use text | park, rec area, golf, cemetery, utility, rail and road right of way | no |
| Madison | city property class | golf, conservancy, cemetery (as build_tod_station_areas park_open_space); exempt classes are public | no |
| Milwaukee | MPROP 4-digit land use | 6553 cemetery; 40xx–41xx rail/transit; 46xx pipelines; 49xx utilities | partly: parks have no separate code here (land-use group not kept); city parks drop out only as public |

## Sanity checks

See the run log printed by the script (`--checks`); findings of the 2026-11-02 build are listed in the section below.

### Findings, build of 2026-11-02

Size: 12,010 rows (stop × case); 1,470 physical stations (`stop_key`).

| City | Stations | City | Stations |
|---|---|---|---|
| New York | 449 | Portland | 88 |
| Chicago | 268 | San Diego | 64 |
| Philadelphia | 204 | Madison | 53 |
| Los Angeles | 126 | Charlotte | 42 |
| Denver | 33 | Milwaukee | 31 |
| Salt Lake City | 27 | Honolulu | 21 |
| Seattle | 14 | Saint Paul | 14 |
| Bellevue | 10 | Austin | 6 |
| Wisconsin, other places | 20 (Wauwatosa 11, Kenosha 5, Shorewood Hills 3, Sun Prairie 1) | | |

1. **Rebuild is exact.** member_match_m = 0.00 m everywhere. Distances recomputed from the lot points match dist_m to
   0.00 m, except Wisconsin (up to 9.4 m: the lot table measured in EPSG 3071).
2. **Duplicates.** No duplicate (case, stop_id).
   - One duplicate (case, stop_key) in 6 Philadelphia cases. Two stops (ids 78 and 189) sit 0.5 m apart near Broad &
     Girard: the Broad Street subway and the Girard trolley. The builder merges each kind separately.
   - 65 pairs of different stations lie under 200 m apart. Most are different modes at one place: CTA with Metra,
     subway with trolley in Philadelphia, Amtrak with SEPTA platforms. There are also BRT and streetcar stops 150–200 m
     apart.
3. **Chained trolley stops in Philadelphia.** Trolley stops every ~80 m join into one long "station":
   - footprints up to 1,265 m (Woodland Av, 16 points);
   - 1,175 m (Lansdowne Av, 18 points);
   - 6 more trolley "stations" over 400 m.
   These are corridors, not stations. They are also where the distance definition matters most (item 6).
4. **Wisconsin BRT.**
   - Madison: paired platforms are mostly merged (median 2 points, 41 m footprint), but 6 pairs of separate stations
     lie 170–240 m apart (possibly one BRT stop counted twice).
   - Milwaukee County: one 17-point station is 816 m long (a chain).
   - Kenosha streetcar: 5 stations with footprints 308–613 m.
   - Stops on the Milwaukee / Wauwatosa and Madison / Shorewood Hills lines are split. The lot-table builder merges
     only inside the two cities, so one stop becomes two stations 20–72 m apart (one in wi_milwaukee or wi_madison,
     one in wi_other).
5. **Ridership vs trips per hour** (Spearman rank, one row per station):

   | City | Year | Stations | Rank with peak trips | Rank with midday trips |
   |---|---|---|---|---|
   | New York | 2019 | 428 | 0.72 | 0.65 |
   | New York | 2024 | 428 | 0.74 | 0.65 |
   | Chicago (CTA) | 2019 | 139 | 0.76 | 0.61 |
   | Salt Lake City | 2019 | 26 | 0.60 | 0.60 |
   | Salt Lake City | 2025 | 27 | 0.65 | 0.65 |
   | Philadelphia Regional Rail | 2019 | 50 | 0.57 | 0.35 |
   | Philadelphia (Regional Rail 2024 + trolley ons 2025) | latest | 153 | 0.31 | 0.28 |
   | Saint Paul | latest | 14 | −0.03 | none |

   Saint Paul has one line with the same frequency at every station, so the rank check means nothing there.
6. **Centroid vs nearest merged point.**
   - 452 of 1,161 reform stop rows have at least one lot that changes band. That is 40,415 of 3,305,248 lots (1.2%).
   - Share of lots that change band, by city:

     | City | Lots changing band | Change in lots within ¼ mile |
     |---|---|---|
     | Seattle | 4.0% | +18% |
     | Bellevue | 3.5% | +16% |
     | Los Angeles | 3.0% | +13% (NTM entrances) |
     | Saint Paul | 2.4% | +7% |
     | Salt Lake City | 2.1% | +7% |
     | Madison | 2.0% | not computed |
     | Philadelphia | 2.0% | +7% |
     | New York, Chicago, Denver, Charlotte, Austin, Honolulu | 0.2% or less | — |

   - Top stops by lots changing band:

     | Stop | Case | Lots changing band | Largest distance drop |
     |---|---|---|---|
     | Girard Av & 26th St | phl_140799 | 3,601 | 364 m |
     | Girard Av & 20th St | phl_130349 | 1,904 | 181 m |
     | Lansdowne Av & 59th St | phl_180505 | 1,730 | 592 m |
     | Reseda | LA | 696 | 2,559 acres changing band |
     | North Hollywood | LA | 638 | — |
     | Lancaster Av & 48th St | phl_130349 | 518 | — |
     | Lancaster Av & Westminster St | phl_140936 | 501 | — |
     | Lake | LA | 451 | — |
     | Highland Park | LA | 415 | — |
     | Hyde Park | LA | 395 | — |
7. **Developable land.**
   - Developable acres ≤ total acres in every band: 0 violations. Vacant and underused acres ≤ developable acres: 0
     violations.
   - **Stacked condominium records inflate acres.** Lot acres within ¼ mile run up to 21.7 times the ¼-mile circle (LA),
     8.4 times (San Diego) and 7.2 times (Charlotte).
   - After counting each stacked record once (acres_dedup_*), the maximum is 1.0 in LA and 1.3 in Charlotte. Use the
     *_dedup columns for land.
   - Left over after dedup, real large parcels:
     - San Diego Stadium (369 acres);
     - Chicago Clark/Lake (365 acres: one 267-acre class-592 parcel, to be checked);
     - Chicago Grand-Red (331 acres).
   - Cities where use data cannot separate parks or public land: Austin and Honolulu (no use, no owner). In those,
     developable = all lots.
   - Coarse use data: Los Angeles, San Diego, Salt Lake City and Chicago, and Milwaukee parks.
8. **Missing data** (share of station rows blank):
   - grade: unknown for 828 of 1,470 stations;
   - opening year: known only for Denver, Seattle, Saint Paul and Austin;
   - trips per hour, blank for these reasons:
     - Madison: barred (AQ-045);
     - Honolulu: 8 of 21 stations, Kalihi to Ala Moana, have no service in the 2026 feed;
     - Denver: 8 of 33, the downtown Welton / California loop, have no GTFS stop within 200 m in the feed;
     - Austin: 1 of 6;
     - New York: 5%;
     - Los Angeles: 10%;
   - SLD D4c is blank for 80% of San Diego rows: the lot table's SLD transit frequency is blank for 92% of San Diego
     lots, so check the lot table's join;
   - ridership: only New York, Chicago CTA, Philadelphia Regional Rail and trolley, Saint Paul and Salt Lake City;
   - Wisconsin has no stop names, because tod_stops.csv has none.

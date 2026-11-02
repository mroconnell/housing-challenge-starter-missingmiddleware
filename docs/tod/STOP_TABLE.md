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
System (metro) level annual ridership (NTD) and multi-system node columns: section "System (metro) level ridership"
below.

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

Measures differ by city; compare ranks within a city only. Longer annual series for reform and Wisconsin stations (and
the 5-year pre/post averages) are in the extra-traits columns, section "Extra traits" below.

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

## Extra traits: opening year, grade, ridership series (reference/tod_stop_extra_traits.csv)

Owner ask (2026-11-02 18:26): ridership, grade and opening year for more stations; scope (18:27) reform stations of the
16 places (+ Seattle Roosevelt) and Wisconsin's stations; **comparison stations are not filled yet**. Built by
`scripts/build_tod_stop_extra_traits.py`; merged into the stop table as **added columns only** (no existing column
changes) by `scripts/build_tod_stop_table.py --merge-extra` (the full build merges it too). One row per (case,
stop_key) for every case row of a priority station (in New York and Philadelphia that includes the cases where the
station is a comparison stop). Blank on all other rows.

| Column | Meaning |
|---|---|
| wikidata_qids, wikidata_labels, wikidata_lines | Wikidata items matched to the station: within 300 m of the station point and label similar to a member name (normalised ratio ≥ 0.6, or one name containing the other); items closed (P3730) or "former railway station" left out |
| wikidata_match_m, wikidata_name_sim | farthest matched item (m); weakest name similarity of the matched items |
| opening_year_extra, opening_year_extra_source | agency fact hand-coded in `reference/tod_stop_grade_opening_handcoded.csv` (with URL), else Wikidata P1619 date of official opening (earliest matched item), else Wikidata P571 inception |
| opening_year_best | the stop table's opening_year where it has one, else opening_year_extra |
| opening_after_reform | 1 if opening_year_best > the case's reform year (the station did not exist at the reform) |
| grade_extra, grade_extra_source | Wikidata P31 station class: underground / elevated / at grade ("station located on surface") / open cut ("in a cut") / highway median; several classes = "mixed (...)" (stations merged across lines, or one item with two classes) |
| grade_best | the stop table's grade where known, else grade_extra, else unknown |
| ridership_series | every year with a value, `year:value;…` (the station's sources summed over lines / platforms / directions) |
| ridership_series_measure, ridership_series_source | measure and source of the series (see table below) |
| ridership_pre5_avg, ridership_pre5_years, ridership_pre5_n | mean over the years reform_year−5 … reform_year−1 that have a value, the years used and their count |
| ridership_post5_avg, ridership_post5_years, ridership_post5_n | the same for reform_year+1 … reform_year+5 |
| ridership_near_reform, ridership_near_reform_year | the value of the year nearest the reform year (tie: the earlier) |
| ridership_pre2020_last, ridership_pre2020_last_year | latest value up to 2019 |
| ridership_last, ridership_last_year | latest value |

**Use only the PRE average as a model trait.** Ridership after the reform partly reflects the new homes the reform
allowed, so ridership_post5_avg is an outcome, not a trait. The pre average uses whatever years exist in the window
(see _years / _n); a station that opened after the reform has none. Wisconsin: every station opened 2018–2024, so any
"pre-reform" ridership would be the 2023–2025 years just before the 2025 law (none is filled yet, see below). COVID
years (2020–2022) sit inside several windows (Portland post, Denver post, Chicago 2022 pre): check _years.

Years: calendar years, except LA Metro, SEPTA subway/trolley (Annual Service Plans) and SANDAG, which are fiscal years
named by the calendar year they end in (FY2017 = Jul 2016–Jun 2017).

| City | Years in the series | Measure | Source (data/raw/tod_stop_table/ridership/…) |
|---|---|---|---|
| New York | 2007–2019, 2024, 2025 | average weekday entries by station complex, split equally over the stations a complex matches | MTA "Average Weekday Subway Ridership" tables (mta_annual: Internet Archive copies of mta.info 2007–2013, MTA 2019 ridership tables 2014–2019); 2024–2025 the stop table's MTA hourly file |
| Chicago (CTA) | 2001–2025 | average weekday entries | City of Chicago 5neh-572f daily entries, weekday mean per year (cta_annual); Metra none |
| Philadelphia | Regional Rail 2008, 2009, 2011, 2013, 2015, 2017, 2019, 2022–2024; MFL/BSL FY2015–2018; trolley FY2015–2018 (101/102 to 2018, city routes 2015) and summer 2025 | boardings (Regional Rail, trolley), turnstile entries (MFL/BSL) | SEPTA Annual Service Plans FY2010–FY2020 (septa_hist; numbers recorded as facts, SEPTA site copyright notice in its manifest); OpenDataPhilly Regional Rail 2017–2024 and trolley 2025 |
| Saint Paul | 2014 (part year) – 2025 | average weekday boardings | Met Council stop boardings/alightings by year (metc_annual, public domain) |
| Salt Lake City | 2017–2025 (2026 part year left out) | average weekday boardings, mean of monthly averages | UTA open data (existing file) |
| Los Angeles | rail FY2017–FY2019; G Line FY2017–FY2019, FY2025 | average weekday boardings | LA Metro DPGTL archive station workbooks and G Line stop APC (la_metro). A 2025 rail sheet by a third party was **not used** |
| San Diego | FY2025–FY2026 | average weekday boardings (APC) | SANDAG Transit Ridership Dashboard service (sd_mts); nothing before 2024 found |
| Denver | 2012–2019 | average weekday boardings (Mon–Thu from Aug 2014) | RTD Rail Station Activity reports, Internet Archive copies (denver_rtd); RTD stopped station reports after 2019 |
| Portland (MAX) | 2017–2025 except 2022 | average weekday boardings (census ons) | TriMet MAX passenger census (trimet); 2022 repeats 2021 and is left out; streetcar stops none |
| Seattle | 2013 (fall sample), 2016 (Q4), 2017–2019, 2020 (Q4) | average weekday boardings | Sound Transit SIP 2015 and Q4 service delivery reports (sound_transit); none after 2020 (dashboard only) |
| Austin | 2016 (April only) | weekday boardings | CapMetro TOD Priority Tool station profiles (capmetro) |
| Bellevue, Charlotte, Honolulu reform stations, Wisconsin | none | — | CATS: only a removed records-request PDF; Skyline: top 5 stations only (no reform station); Madison: MPO April 2025 stop boardings exist but were assigned to stops with Metro's GTFS, held back pending an AQ-045 ruling; MCTS, The Hop, Kenosha: system totals only |

Matching: by coordinates to the nearest station of the whole table within 250–300 m (150 m for trolley stops) where the
source has coordinates; else by normalised name against every member name of the station (New York: name + borough +
routes against the MTA station list, digits must agree, same-name stations need a route in common). Rows dropped as
unreliable: SEPTA MFL FY2018 (repeats FY2017), BSL City Hall (definition jump), Regional Rail 2015 rows equal to 2013
(not recounted), Highland 2013 (listed twice), "North Philadelphia" Regional Rail (two stations share the name).

Opening years and grade, hand-coded agency facts (`reference/tod_stop_grade_opening_handcoded.csv`): MCTS CONNECT 1
2023 (revenue service 2023-06-04, Milwaukee County Legistar 23-828); Madison Rapid Route A 2024 (2024-09-22, city news
release); The Hop M Line 2018 (2018-11-02), Lakefront stop (L Line only) 2024 (full L Line opening 2024-04-11);
Kenosha streetcar 2000 (SEWRPC); Honolulu Skyline segment 1 2023 (2023-06-30). Wikidata (CC0) supplies the rest; its
dates are what Wikidata holds (for a rebuilt station it may be the original or the rebuilt station's date, e.g. CTA
Grand/Cicero 2006).

**Coverage, reform and Wisconsin stations** (count of unique stations with a value; before = the stop table's own
grade / opening_year / ridership_weekday_2019-or-latest columns, after = grade_best / opening_year_best / any ridership
year; build of 2026-11-02):

| Place | Stations | Grade before | Grade after | Opening year before | Opening year after | Ridership before | Ridership after | Pre-5-year average | Post-5-year average |
|---|---|---|---|---|---|---|---|---|---|
| Austin | 5 | 0 | 0 | 5 | 5 | 0 | 5 | 0 | 0 |
| Bellevue | 3 | 0 | 1 | 0 | 3 | 0 | 0 | 0 | 0 |
| Charlotte | 23 | 0 | 20 | 0 | 12 | 0 | 0 | 0 | 0 |
| Chicago | 194 | 0 | 122 | 0 | 147 | 119 | 120 | 117 | 119 |
| Denver | 5 | 0 | 3 | 5 | 5 | 0 | 4 | 4 | 4 |
| Honolulu | 2 | 2 | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| Kenosha | 5 | 5 | 5 | 0 | 5 | 0 | 0 | 0 | 0 |
| Los Angeles | 82 | 38 | 67 | 0 | 59 | 0 | 62 | 0 | 62 |
| Madison | 53 | 53 | 53 | 0 | 53 | 0 | 0 | 0 | 0 |
| Milwaukee | 31 | 31 | 31 | 0 | 31 | 0 | 0 | 0 | 0 |
| New York | 129 | 126 | 129 | 0 | 118 | 126 | 126 | 6 | 120 |
| Philadelphia | 149 | 0 | 48 | 0 | 60 | 109 | 148 | 48 | 96 |
| Portland | 75 | 37 | 37 | 0 | 36 | 0 | 38 | 37 | 38 |
| Saint Paul | 10 | 0 | 0 | 10 | 10 | 10 | 10 | 0 | 10 |
| Salt Lake City | 16 | 0 | 16 | 0 | 16 | 16 | 16 | 0 | 0 |
| San Diego | 48 | 0 | 3 | 0 | 39 | 0 | 46 | 0 | 46 |
| Seattle | 4 | 0 | 4 | 4 | 4 | 0 | 3 | 3 | 3 |
| Shorewood Hills | 3 | 3 | 3 | 0 | 3 | 0 | 0 | 0 | 0 |
| Sun Prairie | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Wauwatosa | 11 | 11 | 11 | 0 | 11 | 0 | 0 | 0 | 0 |
| Total | 849 | 307 | 556 | 24 | 620 | 380 | 578 | 215 | 498 |

Checks (build of 2026-11-02):
- Opening year: 40 priority stations (43 case rows) opened after their case's reform year (opening_after_reform = 1): Austin MetroRail 2010, Bellevue East Link 2024, Saint Paul Green Line 2014, Honolulu Skyline 2023, Seattle Roosevelt 2021, Denver National Western Center 2020, LA K Line / Regional Connector / D Line extension 2022–2026, Salt Lake North Temple 2013 and 600 South 2022, Chicago Washington/Wabash 2017, Damen and Peterson/Ridge 2024, New York 34 St–Hudson Yards 2015. One date before 1860: Chicago LaSalle Street (Metra) 1852 (Wikidata's original-station item; the other matched item says 1951). Where the stop table already had an opening year (Denver, Seattle, Saint Paul, Austin), Wikidata never differs by more than 1 year.
- Grade: where the stop table already had a grade and Wikidata has one, they agree for 118 of 139 stations; the 21 others are mostly New York stations the MTA layer calls elevated and Wikidata calls at grade or mixed (the MTA value is kept in grade_best).
- Wikidata match: median 29 m, 95% under ~200 m; 55 of 613 matched stations have a name similarity under 0.7 (check wikidata_labels before relying on them).
- Ridership vs peak trips per hour (Spearman rank, unique stations, latest pre-2020 value): New York 0.75 (122), Chicago 0.73 (119), Salt Lake City 0.65 (15), Portland 0.59 (37), Philadelphia 0.56 (128, mixed modes), San Diego 0.60 (46, latest), Los Angeles 0.19 (61: BRT and rail mixed; G Line stations have high peak trips and low boardings), Saint Paul −0.06 (one line, same frequency everywhere).
- New series vs the stop table's 2019 ridership (same station, same year): New York ratio 0.98–1.03 (annual table vs hourly file), Philadelphia and Salt Lake City 1.00, Chicago 1.00 except LaSalle/Van Buren 2.04 (the merged station also holds the Blue Line LaSalle station 140 m away; the stop table's own column counted only one).
- One Philadelphia pair (Broad Street subway and Girard trolley, 0.5 m apart) shares a stop_key, so it shares its extra traits.

## System (metro) level ridership and multi-system nodes (reference/tod_stop_system_traits.csv)

Owner asks (2026-11-02 20:10, 20:11, 20:12): system-total ridership before / after / overall; how stations where
several systems meet are counted. Built by `scripts/build_tod_stop_system_traits.py` for **every row (reform,
comparison, Wisconsin)**; written to `reference/tod_stop_system_traits.csv`, merged into
`reference/tod_stop_extra_traits.csv` (which therefore now also has rows for comparison stations, blank in its other
columns) and added to the stop table by `--merge-extra`. Only columns were added; the 143 earlier columns are unchanged
(checked value by value).

**This is a system (metro) level trait, not a station or city value.** A transit system spans its metro area, so
every station of one system in one case gets the same number. It is one of the few metro-level slots in the stop
model. **Only system_upt_pre5_avg (and the pre sum) is usable as a trait**; the post average partly reflects the homes
the reform allowed (an outcome), and the all-years average mixes before and after.

Source: FTA National Transit Database, "Complete Monthly Ridership (with Adjustments and Estimates)"
(data.transportation.gov 8bui-9xvu, the monthly module adjusted data release; public domain), in
`data/raw/tod_stop_table/ntd/` with manifest.json. Unit: **annual unlinked passenger trips (UPT)**: every boarding
counts, including transfers between lines, so NTD totals are higher than an agency's "entries" (New York subway 2019:
2,724 million UPT vs MTA's ~1,698 million entries, ratio 1.6). Annual = calendar-year sum over months and types of
service; a year is used only when all 12 months have a value and the total is above 0 (the opening year and 2026, which
ends in August, are left out). Data cover 2002–2025.

| Column | Meaning |
|---|---|
| systems_at_node, n_systems_at_node | every NTD system (agency NTD ID + mode, with agency name) with a stop point within node_radius_m of the station point: the station's own system, other stop-table stations, and National Transit Map rail stops of all agencies. Bus stops are not included (only BRT / streetcar systems the stop table holds); Amtrak is not in the NTD |
| transfer_hub | 1 if n_systems_at_node ≥ 2 |
| node_radius_m | the larger of 200 m (the stop table's GTFS matching distance) and 150 m + half the station's footprint (the station builder merges points within 150 m) |
| own_system | the station's own system ("NTDID MODE"); the Philadelphia pair sharing a stop_key has two |
| system_ntd_id, system_mode, system_agency | the system used for system_upt_*: the **largest system at the node** (highest all-years average UPT) |
| system_series_note | mode changes and gaps in that system's series (table below) |
| system_upt_pre5_avg, _years, _n | mean annual UPT over reform_year−5 … reform_year−1 (complete years only): **the trait** |
| system_upt_post5_avg, _years, _n | the same for reform_year+1 … +5 (an outcome) |
| system_upt_all_avg, _years, _n | mean over every complete year 2002–2025 |
| system_upt_{pre5,post5,all}_covid_years | the years 2020–2022 inside that window (COVID-affected) |
| system_upt_unit | "annual unlinked passenger trips (NTD UPT, calendar year, all types of service)" |
| system_upt_reform_year_used | the case's reform year; **Wisconsin 2027** (the law's start, owner 20:10; the stop table's reform_year column says 2025, the lot table's value). Wisconsin pre = the latest 5 complete years (2021–2025, or fewer where the system is newer); no post |
| own_system_upt_pre5_avg | pre average of the station's own system (differs from system_upt_pre5_avg only at nodes where another system is larger) |
| system_upt_pre5_sum_all, system_upt_pre5_sum_all_n_systems | pre averages summed over every system at the node that has pre years, and how many were summed |
| trips_peak_all_systems, trips_midday_all_systems | unique trips per hour (07–09 ÷ 2, 10–14 ÷ 4, as tph_*) at **every** GTFS stop within node_radius_m, each feed of the city counted, summed over feeds. Wisconsin: the stop table's tph (own agency, exact member stop ids, all routes) + the other Wisconsin agencies' trips within node_radius_m. Madison blank (AQ-045) |
| trips_all_systems_feeds | feeds and weekday used |
| trips_all_systems_missing | systems at the node with no local feed: **not counted** in trips_*_all_systems (e.g. LIRR, Metro-North, NJ Transit, PATH, PATCO, Metrolink, Keystone) |

Station → system mapping (complete: every one of the 1,470 stations has one):

| Stations | System used (NTD ID, mode) | Series note |
|---|---|---|
| New York subway | 20008 HR (MTA NYCT); Staten Island Railway stations 20099 HR | — |
| Philadelphia | 30019 HR (Market-Frankford, Broad St), 30019 CR (Regional Rail), 30019 LR/SR (trolleys) | trolleys are LR in the NTD to 2011 and SR from 2012: one series |
| Chicago | 50066 HR (CTA), 50118 CR (Metra) | — |
| Los Angeles | 90154 HR, LR; G Line 90154 RB | RB only from 2012 (the G Line was inside bus before), complete from 2013 |
| San Diego | 90026 LR (MTS) | from 2008 |
| Honolulu | 90002 HR (Skyline) | opened 2023; complete years 2024–2025: no pre or post for the 2017 case |
| Denver | 80006 LR, 80006 CR (RTD) | CR from 2016 (complete 2017) |
| Portland | 00008 LR (TriMet MAX); streetcar 00058 SR | streetcar: TriMet SR 2012, City of Portland from 2013; inside TriMet LR before |
| Salt Lake City | 80001 LR (UTA TRAX/S-Line) | — |
| Austin | 60048 YR (MetroRail) | CR 2010–2011, YR from 2012; opened 2010, so no pre for the 2009 case |
| Seattle, Bellevue | 00040 LR (Sound Transit Link) | before 2009 this is Tacoma Link only (Bellevue 2009 pre = 0.88 million) |
| Saint Paul | 50027 LR (Metro Transit) | — |
| Charlotte | 40008 LR (LYNX), 40008 SR (CityLYNX) | SR from 2015 |
| Milwaukee BRT (CONNECT 1) | 50008 MB (MCTS bus) | **BRT is not a separate NTD mode for MCTS: the whole bus system** |
| Milwaukee streetcar | 55312 SR (The Hop) | opened 2018; complete 2019– |
| Madison BRT (Route A) | 50005 RB (Madison Metro) | RB from Sept 2024: one complete year (2025), so pre_n = 1 |
| Kenosha streetcar | 50003 SR | LR to 2011, SR from 2012 |

### How multi-system nodes are counted (owner question 20:12)

Stations are built **per mode group** (Philadelphia: Regional Rail, subway/elevated and trolley merged separately;
Chicago: CTA and Metra separately; other cities one group from one source), so a place where several systems meet is
usually **several rows**, one per mode group.

- **tph_peak / tph_midday (existing columns): not summed across a node.** Every feed of the city is used and summed
  per row, but each GTFS stop goes to its **nearest** row within 200 m only, so a node split into rows splits its
  trips; systems with no feed in the stop table (NJ Transit, PATCO, LIRR, Metro-North, PATH, Metrolink, Amtrak) are
  never counted. Hence the new trips_*_all_systems columns. They are **not additive across rows**: two rows of one node
  both hold the whole node's trips.
- **Station ridership (existing and extra-traits columns): one agency's source per row**, matched to the nearest row;
  never summed across agencies (e.g. Philadelphia 30th St: Regional Rail boardings on the Regional Rail row, the
  subway row blank because the Market-Frankford file cannot be copied).

| Node | Rows in the table | systems_at_node | tph_peak → trips_peak_all_systems | Not counted (no feed) |
|---|---|---|---|---|
| Philadelphia 30th St | subway row and trolley row ("Drexel Station at 30th St"), Regional Rail row ("Gray 30th St Station") 250 m away | subway / trolley rows: SEPTA HR + LR/SR; Regional Rail row: SEPTA CR + NJ Transit CR + PennDOT Keystone CR | subway 64.5 → 109.5; trolley 45.0 → 109.5; Regional Rail 29.5 → 29.5 | NJ Transit, Keystone (and Amtrak) |
| LA Union Station | one row (B/D Lines; the A Line and "L.A. Union Station" points merged into it) | Metro HR + Metro LR + Metrolink CR | 38.5 → 38.5 (Metro rail feed already holds the A Line there) | Metrolink (and Amtrak) |
| Chicago Clark/Lake | one CTA row | CTA HR only: Ogilvie (Metra, "Chicago OTC" row) is ~890 m from the station point, outside the node | 71.0 → 71.0 | — |
| Chicago LaSalle St (Metra) and LaSalle/Van Buren (CTA) | two rows | CTA HR + Metra CR at both | Metra row 43.5 → 65.5; CTA row 22.0 → 65.5 | — |
| Chicago Union Station | one Metra row | Metra CR (Clinton Blue Line beyond the radius) | 26.5 → 26.5 | (Amtrak) |
| Denver Union Station | one row | RTD LR + RTD CR | 47.0 → 47.0 (one RTD feed, both route types, already summed) | — |
| New York with LIRR / PATH / Metro-North / NJ Transit | Atlantic Av–Barclays Ctr and Atlantic Av (LIRR), Woodside–61 St (LIRR), 34 St–Penn Station (LIRR / NJ Transit), Grand Central (Metro-North), Cortlandt St, 6 Av, 23 St, 34 St–Herald Sq (PATH) | NYCT HR + the railroad | unchanged (subway only) | LIRR, Metro-North, NJ Transit, PATH |

Transfer hubs (n_systems_at_node ≥ 2): 86 of 1,470 stations (Philadelphia 22, Los Angeles 15, New York 15, Chicago 11,
Denver 6, Portland 5, San Diego 4, Kenosha 2, Salt Lake City 2, Seattle 2, Charlotte 1, Milwaukee 1). The largest
system differs from the station's own at Metra stations next to CTA, trolley stations next to the subway or Regional
Rail, Portland streetcar stops next to MAX, LA Union Station and 7th St/Metro Center (LA LR is larger than HR), and
Philadelphia's Regional Rail 30th St row, where **NJ Transit's commuter rail (73 million a year) is larger than SEPTA
Regional Rail (30 million)**, so that row's system_upt_* is NJ Transit's; own_system_upt_pre5_avg keeps SEPTA's.

### Checks (build of 2026-11-02)

- Magnitudes (million UPT, 2019): NYCT subway 2,724 (MTA entries ~1,698: NTD counts transfers), CTA rail 218, SEPTA
  subway/elevated 91, LA Metro HR 42, Sound Transit Link 25, MCTS bus 29, The Hop 0.76. All in line with published
  agency totals for unlinked trips.
- Mapping complete: 0 stations without a system.
- Coverage (rows with a value, of 12,010): pre 11,983 (missing: Austin 2009, MetroRail opened 2010; Honolulu 2017,
  Skyline opened 2023); post 11,885 (Honolulu and, by design, Wisconsin); all-years 12,010. Short pre windows: New
  York cases 2003–2006 (data start 2002), Denver commuter rail (1 year), LA G Line (4), Charlotte streetcar (3),
  Madison (1).
- COVID years in the pre window: chicago_2022 (2020, 2021), san_diego_2021 (2020), Wisconsin Milwaukee and other
  (2021, 2022). Post windows of cases from 2015 on include 2020–2022.
- trips_peak_all_systems ≥ tph_peak at every station (ratio median 1.00; up to 7.7 in Chicago, where Metra and CTA rows
  sit next to each other).

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
   - opening year: known only for Denver, Seattle, Saint Paul and Austin (extra traits now fill reform and Wisconsin
     stations, see "Extra traits");
   - trips per hour, blank for these reasons:
     - Madison: barred (AQ-045);
     - Honolulu: 8 of 21 stations, Kalihi to Ala Moana, have no service in the 2026 feed;
     - Denver: 8 of 33, the downtown Welton / California loop, have no GTFS stop within 200 m in the feed;
     - Austin: 1 of 6;
     - New York: 5%;
     - Los Angeles: 10%;
   - SLD D4c is blank for 80% of San Diego rows: the lot table's SLD transit frequency is blank for 92% of San Diego
     lots, so check the lot table's join;
   - ridership: only New York, Chicago CTA, Philadelphia Regional Rail and trolley, Saint Paul and Salt Lake City (extra
     traits add LA, San Diego, Denver, Portland MAX, Seattle, Austin, Philadelphia subway and longer series);
   - Wisconsin has no stop names, because tod_stops.csv has none.

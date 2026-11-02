# Open-licence geometry (replacing shapely/GEOS, pyproj, pyogrio and geopandas)

**Why.** The contest accepts permissively licensed dependencies only (Official Rules 7(b)). shapely's wheels bundle
GEOS (LGPL-2.1), and pyproj and pyogrio require certifi (MPL-2.0); geopandas depends on shapely. The owner asked on
2026-11-02 to recode the geometry with permissive tools rather than keep certifi as an exception.

**What replaces them.** `missing_middleware/geom.py` (Apache-2.0, ours), using only numpy and scipy (BSD-3-Clause) and
the standard library:
- readers: shapefiles (`.shp`/`.dbf`/`.prj`, from folders or zips; `.dbf` via `missing_middleware/dbf.py`) and GeoJSON;
- projections from the published formulas: Albers (EPSG:5070, 3310), Lambert conformal conic (state planes),
  transverse Mercator (UTM, Wisconsin TM, Illinois East, MTM 10), Mercator and web Mercator; `.prj` WKT parsed;
- operations: point-in-polygon joins (holes respected), areas, centroids, points guaranteed inside polygons, nearest
  neighbours and within-distance (scipy `cKDTree`), distance from points to polygons.

**Accuracy (checked 2026-11-02 against the old stack, before it was removed).**
| Check | Result |
| --- | --- |
| NAD83 state planes, Albers, UTM vs PROJ (20 systems, 50 random points each) | 0.00 m |
| NAD83(HARN) / NAD83(CSRS) systems vs PROJ | 0.8–1.3 m (PROJ applies a datum shift; we treat NAD83 realisations as one datum) |
| Wisconsin 2024 Census places (EPSG:5070): areas | 5e-9 relative |
| Centroids | 3 mm |
| 50,000 random points, which place contains each | 100% agreement (0 mismatches) |
| Distances from 3,000 points to the nearest place (up to 800 m) | 6e-9 m |
Fixes on 2026-11-02 after parking's port (reported by the parking thread): areas and centroids now computed about each
ring's first vertex (large EPSG:5070 coordinates had cost up to 0.94% on small parcels; US places now match GEOS to
7e-11); point-in-polygon uses the even-odd rule over all of a feature's rings, as GEOS does (nested shells, islands in
holes; 100,000-point checks in California, Washington and Kansas: 0 mismatches); shapefile holes go to the shell
holding most of their vertices and edge midpoints; .dbf text decoded with the .cpg code page (TIGER is UTF-8).
Point location follows GEOS "within" (even-odd over a feature's rings); for zones whose parts may overlap (buffers,
unions of program areas) pass `union=True`, which tests each part on its own and combines them (parking's suggestion).
NAD27 data are refused (a datum grid shift would be needed); none of our sources use NAD27.

**Proof that outputs are unchanged.** `scripts/check_geo_port.py` compares every `reference/` CSV with the last
commit before the port (f30ec96), column by column; results per chain are logged below.

## Port log
| Chain | Scripts | Status | Output diff |
| --- | --- | --- | --- |
| Geometry module and tests | missing_middleware/geom.py, tests/test_geom.py | done | n/a |
| TOD headline chain | build_tod_stops, fetch_tod_parcels_zoning, build_tod_station_areas, run_tod_model, run_tod_madison_test, tod/transit.py, tod/net_effect.py; new missing_middleware/geom_extra_tod.py (GEOS-identical representative point, exact outline keys, point-to-line distance, polygon-polygon distance, minimum-area rectangle, intersection area) | done 2026-11-02 | Tool numbers unchanged (little 43.1, central 13,229.3, strong 17,147.6, baseline 14,654); tod_model_statewide and Madison test predictions byte-identical; no lot changed band, district, overlay, tract, eligibility or use (250,816 station-area lots); lot areas within 3.5e-7 relative (NAD83(HARN) datum shift), which flips a few last rounded digits in area columns; tod_scale_check baseline column refreshed to baseline v3 (not geometry). fetch_tod_parcels_zoning not rerun (network). |
| Parking census and older reforms | 3 scripts (parking thread) | done | identical |
| Parking near transit and block catalog | 3 scripts (parking thread) | done | identical |
| Parking mechanism, transit share, surface lots | 3 scripts (parking thread) | done | identical (where_binding is stale against baseline v3 only, not geometry) |
| Parking lot test | 1 script (parking thread) | done | identical |
| Parking lot cities | 1 script (parking thread) | done | effects identical; predictions within width-rounding noise (9–13 homes a year); conclusions unchanged |
| Foundation and ADU chain | foundation/geo.py, foundation/build.py, permits/geo.py, permits/madison.py, permits/comparison.py, comparison/ca_inputs.py, build_madison_permits, build_comparison_permits, build_adu_predictive_panel, build_district_allocation, build_ui_bundle; new missing_middleware/geom_extra_foundation.py (GEOS-identical interior points and topology-preserving simplify, overlay areas, nearest polygon, precision grid, validity check, GeoParquet and GDAL-style shapefile/GeoJSON readers) | done 2026-11-02 | Every reference CSV byte-identical; Madison, Pleasant Prairie and Sun Prairie permit data byte-identical (report dates aside); foundation tables identical except parent_municipality_share (1.4e-9 relative); district allocation identical (area weights 4e-10). Display only: map outlines rounded to 1e-4° differ for 484 of 1,913 municipalities (vertices on a rounding half-way point move one step, about 10 m), 64 of them also where rounding makes a ring touch itself (GEOS rebuilds those with a full overlay; largest outline area change 1.3%); Assembly 54 and Senate 18 lose one vertex at the 150 m simplify tolerance. |
| TOD station-area chain | build_tod_station_lot_table, station_cases/*, enrich_tod_station_lots, build_tod_station_wisconsin, run_tod_station_checks, run_tod_station_model, run_tod_station_area, run_tod_new_city_test, tod/case_*.py, tod/cases.py, tod/traits.py; new missing_middleware/geom_extra_station.py (GEOS-identical representative points and areas, 150 m platform merge, nearest with lowest-position ties, WKB, GeoPackage and File Geodatabase readers, GEOS-style buffers) | done 2026-11-02 | All 122 lot tables: every case/group/band cell identical to the pre-port summary; NYC and Philadelphia (106 cases), Wisconsin, Honolulu, Seattle, Bellevue, Saint Paul, Denver, Austin and Salt Lake City identical lot by lot, events included. Where several lots sit at the same point (LA, San Diego, Charlotte, Chicago) a permit can land on a different one of them (totals unchanged); one Portland lot 2 km out changes side. Station effects by city and the central line identical (13,229.3); Wisconsin versions within 5e-7. Merged stations with exactly tied nearest stops can take a different stop's name (12 comparison stops renamed); the Portland Central City flag now also lists "NW 6th & Davis" so flags are unchanged. Austin new-city diagnostic +1 permit home (GEOS buffer edge). Lot-trait model: central 39 (tool 43.1) unchanged; its leave-one-place-out range moves because lots stacked at one point are sampled in a different order (see AQ note pending owner). |
| TOD research scripts (cases, traits, census, lot model, net effect, coverage, AB 2097, ridership, SF caps, NYC downzoning) | fetch_tod_cases, run_tod_cases, run_tod_traits, run_tod_allvars, case_la/case_seattle fetch, run_tod_census_cases/_share/_grow/_predict, run_tod_census2000, run_tod_slc_census, run_tod_conversion, run_tod_updown, run_tod_audit_permits_census, run_tod_lot_model/_loop/_wisconsin, run_tod_model_menu, run_tod_net_effect, build_tod_net_coverage, tod/net_effect.py, run_ab2097_test/_distance_bands, run_chicago_ridership, run_tod_sf_caps, run_tod_nyc_downzoning; new helpers appended to geom_extra_tod (buffered download box, Region/Buffer/PointBuffers with overlap areas and region polygons, GEOS minimum rotated rectangle, UTM choice), geom_extra_station (point-buffer pairs), geom_extra_foundation (GeoParquet point caches) | done 2026-11-02 | Census, AB 2097, ridership, SF caps, slc and audit outputs identical or last rounded digit; coverage cache rebuilt identical (`--start 2026-10-27`). Net-effect area caches now hold the lots themselves (`treated_lots`/`upzoned_lots`) instead of drawn unions; unions, far land, distances and case shapes match the old caches. Remaining differences come from the case adapters ported earlier (a few lots at the 1/4-mile buffer edge change ring acres by up to 0.07%; Seattle Mount Baker far land -0.18 acres), from the GEOS buffer approximations (1/4-1 1/2 mile band acres ±0.2, lots-in-band share ±5e-5) and from one GEOS buffer quirk (largest contiguous site in 3 units: GEOS split groups of lots that are pairwise within 1 m). Not rerun: network fetches, lot-model fits (geometry stages checked one by one), model menu. |
| ADU Gate 2 review map | build_gate2_review_map (local review page, git-ignored output) | done 2026-11-02 | 83 pilot tracts identical; 6 of 1,925 simplified municipality outlines differ (0.03% to 0.8% of area, at most 3 vertices; display only). |
| Packages removed | pyproject.toml `geo` extra now scipy only; uv.lock drops geopandas, shapely, pyproj, pyogrio and certifi; certifi exception removed from scripts/check_python_licenses.py | done 2026-11-02 | Licence check: 20 distributions, 20 permissive, 0 exceptions; Python tests 732 OK; npm licences all permissive. |

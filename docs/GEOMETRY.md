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

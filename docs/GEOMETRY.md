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
NAD27 data are refused (a datum grid shift would be needed); none of our sources use NAD27.

**Proof that outputs are unchanged.** `scripts/check_geo_port.py` compares every `reference/` CSV with the last
commit before the port (f30ec96), column by column; results per chain are logged below.

## Port log
| Chain | Scripts | Status | Output diff |
| --- | --- | --- | --- |
| Geometry module and tests | missing_middleware/geom.py, tests/test_geom.py | done | n/a |

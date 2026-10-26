"""Build the TOD major-transit-stop layer and count 2020 homes near stops, by municipality.

    uv run --all-extras python scripts/fetch_tod_transit.py     # once, needs network
    uv run --all-extras python scripts/build_tod_stops.py

In:  data/raw/tod_transit/ (NTM layers, GTFS feeds, manifest.json)
     data/raw/census_tiger_2020_tabblock/tl_2020_55_tabblock20.zip (HOUSING20, POP20, internal points)
     data/raw/census_cb_2024/cb_2024_55_cousub_500k.zip (municipalities)
Out: reference/tod_stops.csv, reference/tod_near_stop_homes_by_muni.csv, reference/tod_definition_summary.csv

Method and definitions: docs/tod/TRANSIT_PIPELINE.md and docs/tod/MAJOR_TRANSIT_STOP.md.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_tod_transit import DEFAULT_NO_GTFS, GTFS_FEEDS, NO_GTFS  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import transit as T  # noqa: E402

D = RAW / "tod_transit"
BLOCKS = RAW / "census_tiger_2020_tabblock" / "tl_2020_55_tabblock20.zip"
COUSUB = RAW / "census_cb_2024" / "cb_2024_55_cousub_500k.zip"
CRS_M = 3071  # NAD83(HARN) / Wisconsin Transverse Mercator, metres
HALF, QUARTER = 0.5 * T.MILE_M, 0.25 * T.MILE_M
BIG_CITY_POP = 35_000
MILWAUKEE_CITY, MADISON_CITY = "5507953000", "5502548000"
METRO_COUNTIES = ("079", "025")  # Milwaukee County, Dane County

DEFINITIONS = [  # key, description, rapid radius, bus radius, bus threshold (None: no bus), all stops
    ("rapid_half", "(a) rail and rapid transit only, 1/2 mile", 0.5, None, None),
    ("main", "Main case: rail and rapid 1/2 mile, 15-minute bus 1/4 mile", 0.5, 0.25, T.MAIN_N),
    ("high", "High case: rail and rapid 1/2 mile, 20-minute bus 1/4 mile", 0.5, 0.25, T.HIGH_N),
    ("b_half", "(b) rail and rapid plus 15-minute bus, all 1/2 mile", 0.5, 0.5, T.MAIN_N),
    ("c_half", "(c) rail and rapid plus 20-minute bus, all 1/2 mile", 0.5, 0.5, T.HIGH_N),
    ("any_half", "(e) any stop, 1/2 mile (context only, not major transit)", 0.5, 0.5, 0),
]


def load_ntm():
    import geopandas as gpd

    agencies = pd.DataFrame(json.loads((D / "ntm" / "agencies.json").read_text()))
    names = {}
    for _, a in agencies.iterrows():
        for k in ("NTD_ID", "NTAD_NTD_ID"):
            if a.get(k):
                names[str(a[k])] = a["Agency_Name"]
    excluded = {i for i, n in names.items() if T.is_excluded_agency(n)}
    stops = pd.DataFrame(json.loads((D / "ntm" / "stops.json").read_text()))
    # Boarding points only: location_type 0 or blank (stations, entrances and 'Null' rows dropped).
    lt = stops["location_type"].fillna("").astype(str).str.strip()
    stops = stops[lt.isin(["0", ""]) & ~stops["ntd_id"].isin(excluded)].copy()
    routes = gpd.read_file(D / "ntm" / "routes.geojson")
    routes = routes[~routes["ntd_id"].isin(excluded) & routes.geometry.notna()].copy()
    for c in ("route_short_name", "route_long_name", "route_desc", "route_type"):
        routes[c] = routes[c].fillna("").astype(str).str.strip()
    return names, stops, routes


def route_frequencies(routes: pd.DataFrame, manifest: dict) -> tuple[np.ndarray, dict[str, str], dict[str, dict]]:
    """Peak one-direction trips per hour for each NTM route row, and the source per agency."""
    tph = np.zeros(len(routes))
    src: dict[str, str] = {}
    facts: dict[str, dict] = {}
    key = routes["route_short_name"].where(routes["route_short_name"] != "", routes["route_long_name"]).values
    for nid, f in GTFS_FEEDS.items():
        rel = f"gtfs/{nid}_{f['label']}.zip"
        rec = manifest.get("files", {}).get(rel)
        if rec is None or not (D / rel).exists():
            src[nid] = "none: GTFS feed not fetched (see manifest failed list)"
            continue
        start = dt.date.fromisoformat(rec["accessed_utc"][:10])
        peaks, fx = T.gtfs_route_peaks(D / rel, start)
        fx.update(source_kind=rec["source_kind"], url=rec["url"], last_modified=rec.get("last_modified", ""))
        facts[nid] = fx
        sel = (routes["ntd_id"] == nid).values
        tph[sel] = [float(peaks.get(k, 0)) for k in key[sel]]
        kind = "agency GTFS" if rec["source_kind"] == "official" else "agency GTFS via Mobility Database copy"
        src[nid] = f"{kind}; service day {fx['service_day']}; feed valid {fx['valid_from']} to {fx['valid_through']}"
    m = (routes["ntd_id"] == T.MADISON_NTD_ID).values
    tph[m] = [T.madison_trips_per_hour(d) for d in routes.loc[m, "route_desc"]]
    for nid in routes["ntd_id"].unique():
        src.setdefault(nid, NO_GTFS.get(nid, DEFAULT_NO_GTFS))
    return tph, src, facts


def assign_muni(points, cs) -> np.ndarray:
    """Index into `cs` of the county subdivision containing each point (nearest one when the point
    falls outside every shoreline-clipped polygon)."""
    import shapely

    tree = shapely.STRtree(cs.geometry.values)
    out = np.full(len(points), -1)
    pi, gi = tree.query(points, predicate="within")
    out[pi] = gi
    miss = np.flatnonzero(out < 0)
    if len(miss):
        out[miss] = tree.query_nearest(points[miss], return_distance=False, all_matches=False)[1]
    return out


def main() -> None:
    import geopandas as gpd
    import pyogrio

    manifest = json.loads((D / "manifest.json").read_text())
    names, stops, routes = load_ntm()
    routes["tph"], src, facts = route_frequencies(routes, manifest)
    routes["rapid"] = [T.is_rapid(n, t, s, names.get(n, "")) for n, t, s in
                       zip(routes["ntd_id"], routes["route_type"], routes["route_short_name"])]

    sg = gpd.GeoDataFrame(stops, geometry=gpd.points_from_xy(stops.stop_lon.astype(float), stops.stop_lat.astype(float)),
                          crs=4326).to_crs(CRS_M)
    rg = routes.to_crs(CRS_M)
    sp, sa = sg.geometry.values, sg["ntd_id"].values

    def on(mask):
        return T.stops_near_routes(sp, sa, rg.geometry.values[mask], rg["ntd_id"].values[mask])

    A = on(rg["rapid"].values)
    B = on((rg["tph"] >= T.MAIN_N).values) | A
    C = on((rg["tph"] >= T.HIGH_N).values) | A

    # Blocks and municipalities
    bl = pyogrio.read_dataframe(BLOCKS, read_geometry=False, columns=["GEOID20", "HOUSING20", "POP20", "INTPTLAT20", "INTPTLON20"])
    bp = gpd.GeoSeries(gpd.points_from_xy(bl.INTPTLON20.astype(float), bl.INTPTLAT20.astype(float)), crs=4269).to_crs(CRS_M).values
    hu = bl.HOUSING20.astype(float).values
    cs = pyogrio.read_dataframe(COUSUB).to_crs(CRS_M).reset_index(drop=True)
    bmun = assign_muni(bp, cs)
    geoid = cs["GEOID"].values[bmun]
    pop = pd.Series(bl.POP20.astype(float).values).groupby(geoid).sum()
    big = {g for g, n in zip(cs["GEOID"], cs["NAMELSAD"]) if n.endswith(" city") and pop.get(g, 0) >= BIG_CITY_POP}
    smun = cs["GEOID"].values[assign_muni(sp, cs)]

    def within(mask, r):
        return T.blocks_within(bp, sp[mask], r)

    allstops = np.ones(len(sp), bool)
    masks = {
        "rapid_half": within(A, HALF),
        "b_half": within(B, HALF),
        "c_half": within(C, HALF),
        "any_half": within(allstops, HALF),
    }
    masks["main"] = masks["rapid_half"] | within(B, QUARTER)
    masks["high"] = masks["rapid_half"] | within(C, QUARTER)
    # Sensitivity: rail and rapid get the 1/4-to-1/2 mile outer ring only in cities of 35,000+ people.
    radii = np.where(np.isin(smun[A], list(big)), HALF, QUARTER)
    rapid_35k = T.blocks_within_variable(bp, sp[A], radii)
    masks["main_35k"] = rapid_35k | within(B, QUARTER)
    stop_counts = {"rapid_half": int(A.sum()), "main": int(B.sum()), "high": int(C.sum()), "b_half": int(B.sum()),
                   "c_half": int(C.sum()), "any_half": len(sp), "main_35k": int(B.sum())}

    # ---- reference/tod_stops.csv: every stop that qualifies under (c), the widest major-stop definition
    out = sg.loc[C, ["ntd_id", "stop_id", "stop_lat", "stop_lon"]].copy()
    out.insert(1, "agency", out["ntd_id"].map(names))
    out["lat"] = out.pop("stop_lat").astype(float).round(5)
    out["lon"] = out.pop("stop_lon").astype(float).round(5)
    out["flag_a_rapid"], out["flag_b_15min"], out["flag_c_20min"] = A[C].astype(int), B[C].astype(int), C[C].astype(int)
    out["frequency_source"] = [src.get(n, NO_GTFS.get(n, DEFAULT_NO_GTFS)) for n in out["ntd_id"]]
    out = out.sort_values(["ntd_id", "stop_id"]).reset_index(drop=True)
    out.to_csv(REFERENCE / "tod_stops.csv", index=False)

    # ---- reference/tod_near_stop_homes_by_muni.csv
    keys = ["main", "high", "rapid_half", "b_half", "c_half", "any_half", "main_35k"]
    df = pd.DataFrame({"geoid": geoid, "homes": hu} | {k: hu * masks[k] for k in keys}).groupby("geoid").sum()
    cs_idx = cs.set_index("GEOID")
    muni = pd.DataFrame({
        "area_id": "muni:" + df.index,
        "name": cs_idx.loc[df.index, "NAMELSAD"].values,
        "county": cs_idx.loc[df.index, "NAMELSADCO"].values,
        "homes_2020": df["homes"].astype(int).values,
    })
    for k in keys:
        muni[f"homes_near_{k}"] = df[k].astype(int).values
    for k in keys:
        muni[f"share_near_{k}"] = np.where(muni.homes_2020 > 0, muni[f"homes_near_{k}"] / muni.homes_2020.where(muni.homes_2020 > 0, 1), 0).round(4)
    muni = muni.sort_values("area_id").reset_index(drop=True)
    muni.to_csv(REFERENCE / "tod_near_stop_homes_by_muni.csv", index=False)

    # ---- reference/tod_definition_summary.csv
    state = int(hu.sum())
    rows = []
    desc = {k: (d, rr, br, n) for k, d, rr, br, n in DEFINITIONS}
    desc["main_35k"] = ("Check: main case, but rail and rapid 1/2 mile only in cities of 35,000+ (else 1/4 mile)", 0.5, 0.25, T.MAIN_N)
    for k in keys:
        d, rr, br, n = desc[k]
        h = int(muni[f"homes_near_{k}"].sum())
        g = muni.set_index("area_id")[f"homes_near_{k}"]
        two = int(g.get(f"muni:{MILWAUKEE_CITY}", 0) + g.get(f"muni:{MADISON_CITY}", 0))
        cty = int(g[g.index.str[7:10].isin(METRO_COUNTIES)].sum())
        rows.append({"definition": k, "description": d, "rapid_radius_mi": rr, "bus_radius_mi": br if br is not None else "",
                     "bus_min_trips_per_hour": n if n is not None else "", "stops": stop_counts[k], "homes": h,
                     "state_homes_2020": state, "share_of_state": round(h / state, 4),
                     "milwaukee_city_homes": int(g.get(f"muni:{MILWAUKEE_CITY}", 0)),
                     "madison_city_homes": int(g.get(f"muni:{MADISON_CITY}", 0)),
                     "share_in_two_cities": round(two / h, 4) if h else 0,
                     "share_in_milwaukee_dane_counties": round(cty / h, 4) if h else 0})
    summ = pd.DataFrame(rows)
    summ.to_csv(REFERENCE / "tod_definition_summary.csv", index=False)

    pd.set_option("display.width", 250)
    print(summ.drop(columns=["description"]).to_string(index=False))
    print("frequent routes (>=3 trips/hour) by agency:")
    print(routes[routes.tph >= T.HIGH_N].groupby("ntd_id").route_short_name.apply(lambda s: ",".join(sorted(set(s)))).to_string())
    print("rapid stops outside cities of 35,000+:", int((~np.isin(smun[A], list(big))).sum()), "of", int(A.sum()))
    print(json.dumps({"frequency_source": src, "feeds": facts}, indent=1))


if __name__ == "__main__":
    main()

"""CA AB 2097 study, step 1b (part 1): rail, ferry and Amtrak stations, and the land around them. Counts only.

Plan: docs/parking/CA_AB2097_PLAN.md (locked 2026-11-05; section 8 rail-only edge blocks; section 9). Runs only after
the audit has checked this script. Reads no permits.

Inputs
- Rail stops: the federal National Transit Map stops extract already on disk
  (data/raw/parking_transit/ntm_rail_stops_national.json; BTS NTAD, CC BY 3.0, compiled 2026-09-23; the project's
  common stop source under AQ-045). Stop types 0 (light rail, streetcar), 1 (subway, metro), 2 (rail).
- Amtrak stations: BTS NTAD Amtrak Stations (public domain), California rows with StnType = 'RAIL' (thruway bus
  stops left out). Fetched here (attributes and points only) into data/raw/ca_ab2097/ (git-ignored).
- Ferry terminals: Caltrans' current major transit stop layer already on disk (data/raw/ab2097/
  major_transit_stops.geojson), existing stops with hqta_type 'major_stop_ferry'.
- Opening and closing dates: reference/ca_ab2097_rail_openings.csv (stations opened, closed or moved on or after
  2018-01-01, each with a source). A station not in that table is treated as open before 2018 (an assumption,
  stated in the output).
- 2020 census blocks and jurisdictions: the same readers as the earlier AB 2097 test (scripts/run_ab2097_test.py).

Rules (from the plan)
- Stops of the same mode within 150 m are one station.
- "Existing" = open on or before 2022-12-31. Stations opened 2018-2022 are flagged for the with/without check.
- Amtrak-only stations (no other rail mode within 150 m) are flagged for the "without Amtrak-only" check.
- Distances are straight-line, from the station point (Albers, EPSG:3310), with the project's own geometry code.

Outputs (no addresses)
- reference/ca_ab2097_rail_stations.csv: one row per station (mode, name, system id, opened status, flags, lon/lat).
- reference/ca_ab2097_rail_coverage.csv: homes (2020) and land acres within ½ mile, and in the ⅓–½ and ½–⅔ mile
  bands, by station set (all existing rail; without Amtrak-only; without streetcar systems; without 2018–2022
  openings; ferry), statewide and for Palo Alto.

    uv run python scripts/ca_ab2097_step1b_rail.py
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402
import run_ab2097_test as run  # noqa: E402  (block readers and distance helpers)

UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
RAWD = RAW / "ca_ab2097"
AMTRAK = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_Amtrak_Stations/FeatureServer/0/query"
NTM_RAIL = RAW / "parking_transit" / "ntm_rail_stops_national.json"
OPENINGS = REFERENCE / "ca_ab2097_rail_openings.csv"
CA_BOX = (-124.6, 32.4, -114.1, 42.1)  # lon/lat box; final test is a block-jurisdiction match
MERGE_M = 150.0
EXISTING_BY = "2022-12-31"
MILE = ab.MILE_M
BANDS = {"0-1/2": (0.0, 0.5), "1/3-1/2": (1 / 3, 0.5), "1/2-2/3": (0.5, 2 / 3)}
# Streetcar-only systems (National Transit Database ids), for the "without streetcar" check. Filled by hand from
# NTD agency names in the review of this script's first output; empty means the check is not yet run.
STREETCAR_NTD: set[str] = set()


def get_json(url: str, params: dict) -> dict:
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def fetch_amtrak() -> pd.DataFrame:
    RAWD.mkdir(parents=True, exist_ok=True)
    f = RAWD / "ntad_amtrak_stations_ca.json"
    if not f.exists():
        j = get_json(AMTRAK, {"where": "State='CA' AND StnType='RAIL'", "outFields": "Code,StationName,StnType,lon,lat",
                              "returnGeometry": "false", "f": "json"})
        rows = [x["attributes"] for x in j.get("features", [])]
        f.write_text(json.dumps({"source": AMTRAK, "licence": "public domain (17 U.S.C. 101; NTAD item text)",
                                 "where": "State='CA' AND StnType='RAIL'", "rows": rows}))
    rows = json.loads(f.read_text())["rows"]
    d = pd.DataFrame(rows).rename(columns={"StationName": "name", "Code": "system_id"})
    d["mode"] = "intercity_rail"
    return d[["mode", "name", "system_id", "lon", "lat"]]


def ntm_rail() -> pd.DataFrame:
    s = pd.DataFrame(json.loads(NTM_RAIL.read_text())["stops"])
    s = s[s.stop_lon.between(CA_BOX[0], CA_BOX[2]) & s.stop_lat.between(CA_BOX[1], CA_BOX[3])]
    first = s.stop_type.astype(str).str.split(";").str[0]
    s["mode"] = first.map({"0": "light_rail_or_streetcar", "1": "heavy_rail", "2": "commuter_rail"})
    s = s.dropna(subset=["mode"])
    return s.rename(columns={"stop_name": "name", "ntd_id": "system_id", "stop_lon": "lon", "stop_lat": "lat"})[
        ["mode", "name", "system_id", "lon", "lat"]]


def ferry() -> pd.DataFrame:
    from missing_middleware.geom_extra_station import read_vector
    f = read_vector(RAW / "ab2097" / "major_transit_stops.geojson", 4326)
    f = f[(f["hqta_type"] == "major_stop_ferry") & (f["plan_name"].fillna("").str.strip() == "")]
    return pd.DataFrame({"mode": "ferry", "name": f.get("stop_id", ""), "system_id": f.get("agency_primary", ""),
                         "lon": f["x"].astype(float), "lat": f["y"].astype(float)})


def to_stations(stops: pd.DataFrame) -> pd.DataFrame:
    """Merge stops of the same mode within MERGE_M into one station, named after its nearest stop."""
    from missing_middleware.geom_extra_station import merge_stops
    out = []
    for mode, g in stops.groupby("mode"):
        g = run.lonlat_points(g.reset_index(drop=True), g.lon, g.lat)
        cx, cy, named = merge_stops(g.x.to_numpy(float), g.y.to_numpy(float), r=MERGE_M)
        for k in range(len(cx)):
            first = g.iloc[int(named[k])]
            out.append({"mode": mode, "name": first["name"], "system_id": first["system_id"], "x": cx[k], "y": cy[k]})
    return pd.DataFrame(out)


def attach_dates(st: pd.DataFrame) -> pd.DataFrame:
    st["opened"] = "before 2018 (assumed: not in openings table)"
    st["opened_date"] = ""
    if not OPENINGS.exists():
        st["opened"] = "openings table missing"
        return st
    o = pd.read_csv(OPENINGS, dtype=str)
    o = o[o.event.isin(["opened", "relocated"]) & o.lat.notna() & o.lon.notna()]
    if len(o):
        og = run.lonlat_points(o.reset_index(drop=True), o.lon.astype(float), o.lat.astype(float))
        from missing_middleware.geom_extra_station import nearest_lowest
        idx, d = nearest_lowest(st.x.to_numpy(float), st.y.to_numpy(float), og.x.to_numpy(float), og.y.to_numpy(float))
        hit = d <= 300.0
        st.loc[hit, "opened_date"] = og.date.to_numpy(object)[idx[hit]]
        st.loc[hit, "opened"] = np.where(og.date.to_numpy(object)[idx[hit]] <= EXISTING_BY, "2018-2022", "after 2022")
    return st


def coverage(st: pd.DataFrame, blocks: pd.DataFrame) -> pd.DataFrame:
    sets = {
        "existing rail (all modes)": st[(st.mode != "ferry") & (st.opened != "after 2022")],
        "existing rail without Amtrak-only": st[(st.mode != "ferry") & (st.opened != "after 2022") & ~st.amtrak_only],
        "existing rail without streetcar systems": st[(st.mode != "ferry") & (st.opened != "after 2022")
                                                      & ~st.system_id.isin(STREETCAR_NTD)],
        "existing rail without 2018-2022 openings": st[(st.mode != "ferry") & (st.opened == "before 2018 (assumed: not in openings table)")],
        "existing ferry": st[st.mode == "ferry"],
    }
    rows = []
    for name, s in sets.items():
        if s.empty:
            continue
        d = run.nearest_m(blocks, s)
        for area, sel in (("California", np.ones(len(blocks), bool)), ("Palo Alto", (blocks.juris == "PALO ALTO").to_numpy())):
            for band, (lo, hi) in BANDS.items():
                m = sel & (d >= lo * MILE) & (d < hi * MILE)
                rows.append({"station_set": name, "stations": len(s), "area": area, "band_miles": band,
                             "homes_2020": float(blocks.homes[m].sum()), "acres": float(blocks.acres[m].sum()),
                             "blocks": int(m.sum())})
    return pd.DataFrame(rows)


def main() -> None:
    stops = pd.concat([ntm_rail(), fetch_amtrak(), ferry()], ignore_index=True)
    st = to_stations(stops)
    # Amtrak-only: an intercity station with no other rail station within MERGE_M
    other = st[(st.mode != "intercity_rail") & (st.mode != "ferry")]
    from missing_middleware.geom_extra_station import nearest_lowest
    _, d = nearest_lowest(st.x.to_numpy(float), st.y.to_numpy(float), other.x.to_numpy(float), other.y.to_numpy(float))
    st["amtrak_only"] = (st.mode == "intercity_rail") & (d > MERGE_M)
    st = attach_dates(st)

    blocks = run.read_blocks(["GEOID20", "COUNTYFP20", "ALAND20", "HOUSING20", "INTPTLAT20", "INTPTLON20"])
    blocks["juris"] = run.block_juris(blocks)
    blocks["homes"] = blocks.HOUSING20.astype(float)
    blocks["acres"] = blocks.ALAND20.astype(float) / 4046.8564224
    # keep stations inside California (nearest block within 2 km)
    _, dblk = nearest_lowest(st.x.to_numpy(float), st.y.to_numpy(float), blocks.x.to_numpy(float), blocks.y.to_numpy(float))
    st = st[dblk <= 2000].copy()

    from missing_middleware.geom_extra_station import transform
    st["lon"], st["lat"] = transform(st.x.to_numpy(float), st.y.to_numpy(float), run.CRS, 4326)
    st.drop(columns=["x", "y"]).round({"lon": 6, "lat": 6}).to_csv(REFERENCE / "ca_ab2097_rail_stations.csv", index=False)
    cov = coverage(st, blocks)
    cov.to_csv(REFERENCE / "ca_ab2097_rail_coverage.csv", index=False)
    print(st.groupby(["mode", "opened"]).size().to_string())
    print(f"Amtrak-only stations: {int(st.amtrak_only.sum())}")
    print(cov[cov.band_miles == "0-1/2"].to_string(index=False))


if __name__ == "__main__":
    main()

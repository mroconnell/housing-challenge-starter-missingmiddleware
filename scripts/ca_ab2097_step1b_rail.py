"""CA AB 2097 study, step 1b (part 1): rail, ferry and Amtrak stations, and the land around them. Counts only.

Plan: docs/parking/CA_AB2097_PLAN.md (locked 2026-11-05; section 8 rail-only edge blocks; section 9). Runs only after
the audit has checked this script. Reads no permits.

Inputs
- Rail stops: the federal National Transit Map stops extract already on disk
  (data/raw/parking_transit/ntm_rail_stops_national.json; BTS NTAD, CC BY 3.0, compiled 2026-09-23; the project's
  common stop source under AQ-045). Stop types 0 (light rail, streetcar), 1 (subway, metro), 2 (rail).
- Amtrak stations: BTS NTAD Amtrak Stations (public domain), California rows with StnType = 'TRAIN' (thruway bus
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
- Blocks are counted whole, by their internal point, as in the earlier AB 2097 test.

Outputs (no addresses)
- reference/ca_ab2097_rail_stations.csv: one row per stop, with its station id (mode, name, system id, opened status,
  flags, lon/lat).
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
        j = get_json(AMTRAK, {"where": "State='CA' AND StnType='TRAIN'", "outFields": "Code,StationName,StnType,lon,lat",
                              "returnGeometry": "false", "f": "json"})
        tv = get_json(AMTRAK, {"where": "State='CA'", "outFields": "StnType", "returnDistinctValues": "true",
                               "returnGeometry": "false", "f": "json"})
        print("NTAD Amtrak StnType values (CA):", sorted({x["attributes"]["StnType"] for x in tv.get("features", [])}))
        if j.get("exceededTransferLimit"):
            raise SystemExit("Amtrak query hit the transfer limit; page it before use")
        rows = [x["attributes"] for x in j.get("features", [])]
        print(f"Amtrak stations fetched (CA, RAIL): {len(rows)}")
        f.write_text(json.dumps({"source": AMTRAK, "licence": "public domain (17 U.S.C. 101; NTAD item text)",
                                 "where": "State='CA' AND StnType='TRAIN'", "rows": rows}))
    rows = json.loads(f.read_text())["rows"]
    if not rows:
        f.unlink()
        raise SystemExit("0 Amtrak stations came back; check the StnType value before running (audit)")
    d = pd.DataFrame(rows).rename(columns={"StationName": "name", "Code": "system_id"})
    d["mode"] = "intercity_rail"
    return d[["mode", "name", "system_id", "lon", "lat"]]


def ntm_rail() -> pd.DataFrame:
    s = pd.DataFrame(json.loads(NTM_RAIL.read_text())["stops"])
    s = s[s.stop_lon.between(CA_BOX[0], CA_BOX[2]) & s.stop_lat.between(CA_BOX[1], CA_BOX[3])]
    types = s.stop_type.astype(str).str.split(";")
    s["mode"] = types.str[0].map({"0": "light_rail_or_streetcar", "1": "heavy_rail", "2": "commuter_rail"})
    s["shared_with_bus"] = types.apply(lambda t: "3" in t)  # rail stop also coded as a bus stop: street level
    s = s.dropna(subset=["mode"])
    return s.rename(columns={"stop_name": "name", "ntd_id": "system_id", "stop_lon": "lon", "stop_lat": "lat"})[
        ["mode", "name", "system_id", "lon", "lat", "shared_with_bus"]]


def ferry() -> pd.DataFrame:
    from missing_middleware.geom_extra_station import read_vector
    f = read_vector(RAW / "ab2097" / "major_transit_stops.geojson", 4326)
    f = f[(f["hqta_type"] == "major_stop_ferry") & (f["plan_name"].fillna("").str.strip() == "")]
    return pd.DataFrame({"mode": "ferry", "name": f.get("stop_id", ""), "system_id": f.get("agency_primary", ""),
                         "lon": f["x"].astype(float), "lat": f["y"].astype(float)})


def to_stations(stops: pd.DataFrame) -> pd.DataFrame:
    """Stop points in metres, each with a station id: stops of the same mode within MERGE_M of each other (buffers of
    radius MERGE_M/2 that touch) share a station. Distances are measured to stop points, not to station centres, so
    a chain of close stops never moves the ½-mile line."""
    from missing_middleware.geom_extra_station import merge_within
    out = []
    for mode, g in stops.groupby("mode"):
        g = run.lonlat_points(g.reset_index(drop=True), g.lon, g.lat)
        _, _, members = merge_within(g.x.to_numpy(float), g.y.to_numpy(float), r=MERGE_M / 2)
        sid = np.empty(len(g), dtype=object)
        for k, m in enumerate(members):
            sid[m] = f"{mode}:{k}"
        g["station_id"] = sid
        out.append(g)
    st = pd.concat(out, ignore_index=True)
    st["shared_with_bus"] = st["shared_with_bus"].fillna(False).astype(bool)
    return st


# Openings-table modes mapped to this script's station modes.
TABLE_MODE = {"heavy_rail": "heavy_rail", "light_rail": "light_rail_or_streetcar", "streetcar": "light_rail_or_streetcar",
              "commuter_rail": "commuter_rail", "intercity_rail": "intercity_rail", "ferry": "ferry"}
# Openings-table system names -> National Transit Database ids in the stop data (rail systems only). A table row
# dates only stops of its own system, so a new station never re-dates an older line's stop next to it (audit).
SYSTEM_NTD = [("Muni", "90015"), ("BART", "90003"), ("LA Metro", "90154"), ("San Diego MTS", "90026"),
              ("VTA", "90013"), ("SacRT", "90019"), ("Caltrain", "90134"), ("Metrolink", "90151"),
              ("SMART", "90299"), ("NCTD", "90030"), ("ACE", "90182")]


def ntd_of(system: str) -> str | None:
    for key, ntd in SYSTEM_NTD:
        if key.lower() in str(system).lower():
            return ntd
    return None


# Join groups for dates: subway-running light rail is coded as either mode in the stop data, so the two urban rail
# modes form one group; other modes join only to themselves.
JOIN_GROUP = {"heavy_rail": "urban_rail", "light_rail_or_streetcar": "urban_rail", "commuter_rail": "commuter_rail",
              "intercity_rail": "intercity_rail", "ferry": "ferry"}


def read_openings() -> pd.DataFrame:
    """The openings table, checked: full YYYY-MM-DD dates (compared as text), known modes and events, coordinates.
    A relocation is two rows: 'closed' at the old site and 'opened' at the new one."""
    o = pd.read_csv(OPENINGS, dtype=str)
    bad_date = ~o.date.fillna("").str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    bad_mode = ~o["mode"].isin(TABLE_MODE)
    bad_event = ~o.event.isin(["opened", "closed"])
    no_xy = o.lat.isna() | o.lon.isna()
    problems = []
    for name, m in (("date not YYYY-MM-DD", bad_date), ("unknown mode", bad_mode), ("event not opened/closed", bad_event),
                    ("no coordinates", no_xy)):
        if m.any():
            problems.append(f"{int(m.sum())} rows with {name}:\n"
                            + o.loc[m, ["system", "station_name", "mode", "event", "date"]].to_string(index=False))
    if problems:  # a dropped "opened" row would wrongly count its station as open before 2018 (audit)
        raise SystemExit("openings table has bad rows; fix them before running:\n" + "\n".join(problems))
    o = o.copy()
    o["smode"] = o["mode"].map(TABLE_MODE)
    return run.lonlat_points(o.reset_index(drop=True), o.lon.astype(float), o.lat.astype(float))


def attach_dates(st: pd.DataFrame) -> pd.DataFrame:
    """Opening status of today's stops (a table row dates the stops of its group within 150 m of its point), plus stations that existed at the end of 2022 but have since closed or
    moved away (added back from the table's 'closed' rows dated after 2022)."""
    from missing_middleware.geom_extra_station import nearest_lowest
    st["opened"] = "before 2018 (assumed: not in openings table)"
    st["opened_date"] = ""
    if not OPENINGS.exists():
        raise SystemExit(f"{OPENINGS} is missing; it must exist before this script runs (audit)")
    o = read_openings()
    op = o[o.event == "opened"].copy()
    op["group"] = op.smode.map(JOIN_GROUP)
    nomap = op[op.system.map(ntd_of).isna() & ~op.group.isin(["ferry", "intercity_rail"])]
    if len(nomap):  # a rail row whose system is not in SYSTEM_NTD must not fall back to the mode group (audit)
        raise SystemExit("openings rows with a rail system not in SYSTEM_NTD:\n"
                         + nomap[["system", "station_name"]].to_string(index=False))
    grp = st["mode"].map(JOIN_GROUP).to_numpy(object)
    unmatched, missing_existing = [], []
    for _, r in op.iterrows():  # join within the same group: the nearest stop's whole station takes the date
        if str(r.get("prior_same_system_service", "")).strip().lower() == "yes":
            print(f"not dated (same system served the site before 2018): {r.station_name}")
            continue
        ntd = ntd_of(r.system)
        same_sys = np.ones(len(st), bool) if ntd is None else (st.system_id.astype(str).str.split(";").apply(lambda t: ntd in t)).to_numpy()
        sel = np.flatnonzero((grp == r.group) & same_sys)
        if not len(sel):
            unmatched.append(r.station_name)
            continue
        dx, dy = st.x.to_numpy(float)[sel] - r.x, st.y.to_numpy(float)[sel] - r.y
        dist = np.hypot(dx, dy)
        hit = sel[dist <= MERGE_M]  # only stops within 150 m of the table's point take its date (audit)
        if not len(hit):
            unmatched.append(f"{r.station_name} ({r.smode}, nearest {dist.min():.0f} m)")
            if r.date <= EXISTING_BY:
                missing_existing.append(r)  # existed at the end of 2022 but is not in today's stop data near here
            continue
        idx = st.index[hit]
        st.loc[idx, "opened_date"] = r.date
        st.loc[idx, "opened"] = "2018-2022" if r.date <= EXISTING_BY else "after 2022"
        span = float(np.hypot(np.ptp(st.x.to_numpy(float)[hit]), np.ptp(st.y.to_numpy(float)[hit])))
        print(f"dated {r.station_name} {r.date}: {len(hit)} stops, span {span:.0f} m")
    if unmatched:
        # an opened station missing from today's stop data either opened after the stop data were compiled
        # (2026-09-23) or has coordinates off by more than 300 m; both are listed for the step 1 review
        print("openings rows with no stop of the same group within 300 m:", "; ".join(unmatched))
    if missing_existing:  # add the table's point as a stop, so a 2018-2022 opening is never left out of the map
        m = pd.DataFrame(missing_existing)
        print("added from the openings table (opened by 2022, no stop of its group within 150 m):",
              "; ".join(m.station_name))
        st = pd.concat([st, pd.DataFrame({"mode": m.smode.to_numpy(), "name": m.station_name.to_numpy(),
                                          "system_id": m.system.to_numpy(), "x": m.x.to_numpy(), "y": m.y.to_numpy(),
                                          "opened": "2018-2022", "opened_date": m.date.to_numpy(),
                                          "shared_with_bus": False,
                                          "station_id": [f"table:{i}" for i in range(len(m))]})], ignore_index=True)
    gone = o[(o.event == "closed") & (o.date > EXISTING_BY)]
    if len(gone):
        add = pd.DataFrame({"mode": gone.smode, "name": gone.station_name, "system_id": gone.system,
                            "x": gone.x, "y": gone.y, "opened": "closed or moved after 2022 (added back)",
                            "opened_date": gone.date, "shared_with_bus": False,
                            "station_id": [f"added:{i}" for i in range(len(gone))]})
        st = pd.concat([st, add], ignore_index=True)
    return st


def coverage(st: pd.DataFrame, blocks: pd.DataFrame) -> pd.DataFrame:
    sets = {
        "existing rail (all modes)": st[(st["mode"] != "ferry") & (st.opened != "after 2022")],
        "existing rail without Amtrak-only": st[(st["mode"] != "ferry") & (st.opened != "after 2022") & ~st.amtrak_only],
        "existing rail without street-level stops shared with bus": st[(st["mode"] != "ferry") & (st.opened != "after 2022")
                                                                       & ~st.shared_with_bus],
        "existing rail without 2018-2022 openings": st[(st["mode"] != "ferry") & (st.opened == "before 2018 (assumed: not in openings table)")],
        "existing ferry": st[st["mode"] == "ferry"],
    }
    rows = []
    if not STREETCAR_NTD:
        rows.append({"station_set": "existing rail without streetcar systems", "area": "California",
                     "band_miles": "not run yet (streetcar systems not yet listed)"})
    else:
        sets["existing rail without streetcar systems"] = st[(st["mode"] != "ferry") & (st.opened != "after 2022")
                                                             & ~st.system_id.isin(STREETCAR_NTD)]
    for name, s in sets.items():
        if s.empty:
            continue
        d = run.nearest_m(blocks, s)
        for area, sel in (("California", np.ones(len(blocks), bool)), ("Palo Alto", (blocks.juris == "PALO ALTO").to_numpy())):
            for band, (lo, hi) in BANDS.items():
                m = sel & (d >= lo * MILE) & (d < hi * MILE)
                rows.append({"station_set": name, "stations": s.station_id.nunique(), "stops": len(s), "area": area,
                             "band_miles": band,
                             "homes_2020": float(blocks.homes[m].sum()), "acres": float(blocks.acres[m].sum()),
                             "blocks": int(m.sum())})
    return pd.DataFrame(rows)


def main() -> None:
    stops = pd.concat([ntm_rail(), fetch_amtrak(), ferry()], ignore_index=True)
    st = to_stations(stops)
    st = attach_dates(st)
    # Amtrak-only: an intercity station with no other rail station within MERGE_M (after closed stations are added back)
    other = st[(st["mode"] != "intercity_rail") & (st["mode"] != "ferry")]
    from missing_middleware.geom_extra_station import nearest_lowest
    _, d = nearest_lowest(st.x.to_numpy(float), st.y.to_numpy(float), other.x.to_numpy(float), other.y.to_numpy(float))
    st["amtrak_only"] = (st["mode"] == "intercity_rail") & (d > MERGE_M)  # no other rail stop within 150 m
    # check (audit): which non-Amtrak systems sit within 150 m of Amtrak stations, so an Amtrak feed inside the
    # National Transit Map rows would show here
    near = st[(st["mode"] == "intercity_rail") & ~st.amtrak_only]
    if len(near):
        j, _ = nearest_lowest(near.x.to_numpy(float), near.y.to_numpy(float), other.x.to_numpy(float), other.y.to_numpy(float))
        print("systems sharing a station with Amtrak (NTD id: count):",
              other.system_id.to_numpy(object)[j].tolist() and pd.Series(other.system_id.to_numpy(object)[j]).value_counts().to_dict())

    blocks = run.read_blocks(["GEOID20", "COUNTYFP20", "ALAND20", "HOUSING20", "INTPTLAT20", "INTPTLON20"])
    blocks["juris"] = run.block_juris(blocks)
    blocks["homes"] = blocks.HOUSING20.astype(float)
    blocks["acres"] = blocks.ALAND20.astype(float) / 4046.8564224
    # keep stations inside California: point in any California county (Census 2024 cartographic counties)
    from missing_middleware.geom_extra_station import first_within, read_vector
    cty = read_vector(RAW / "census_cb_2024" / "cb_2024_us_county_500k.zip", run.CRS, columns=["STATEFP"])
    cty = cty[cty.STATEFP == "06"]
    inside = first_within(st.x.to_numpy(float), st.y.to_numpy(float), list(cty["geometry"])) >= 0
    print(f"stations outside California dropped: {int((~inside).sum())}")
    st = st[inside].copy()

    from missing_middleware.geom_extra_station import transform
    st["lon"], st["lat"] = transform(st.x.to_numpy(float), st.y.to_numpy(float), run.CRS, 4326)
    st.drop(columns=["x", "y"]).round({"lon": 6, "lat": 6}).to_csv(REFERENCE / "ca_ab2097_rail_stations.csv", index=False)
    print(f"stops: {len(st):,}; stations: {st.station_id.nunique():,}; street-level stops shared with bus: "
          f"{int(st.shared_with_bus.sum()):,}")
    cov = coverage(st, blocks)
    cov.to_csv(REFERENCE / "ca_ab2097_rail_coverage.csv", index=False)
    print(st.groupby(["mode", "opened"]).station_id.nunique().to_string())
    print(f"Amtrak-only stations: {st.loc[st.amtrak_only, 'station_id'].nunique()}")
    print(cov[cov.band_miles == "0-1/2"].to_string(index=False))


if __name__ == "__main__":
    main()

"""WRITTEN AFTER THE MAIN RESULTS WERE SEEN (2026-11-05); it follows the spec fixed before the first run (plan section 9,
"exact spec of the bus side checks", part 1). Choices not in that spec are marked "not in the spec".

CA AB 2097 study: dated late-2022 bus major stops from web-archive copies of agency schedule files (GTFS), compared
with today's Caltrans bus major stops, and the headline re-run with the 2022 stops.

    uv run python scripts/ca_ab2097_bus2022.py --fetch   # download archived GTFS copies (git-ignored); check calendars
    uv run python scripts/ca_ab2097_bus2022.py --run

Fetch
- Feeds: every California feed in reference/ca_ab2097_gtfs_archive_coverage.csv with a saved copy in
  2022-01-01..2023-06-30 (web archive). All 200/3xx copies in that window are downloaded from the archive's raw-file
  address (https://web.archive.org/web/<timestamp>id_/<url>), 5 seconds apart, user agent
  "missing-middleware-research/1.0 (public data)", into data/raw/ca_ab2097/gtfs2022/ (git-ignored). Each feed's own
  terms are not stated in the archive; feeds are research inputs only, never committed or shared.
- A copy qualifies if its service calendar (calendar.txt and calendar_dates.txt) runs on Wednesday 2022-12-14. Among
  qualifying copies of a feed, the one whose calendar start is latest on or before 2022-12-14 is used.

Labels (audit): major stops are found within one feed, so two agencies' routes meeting (for example AC Transit and Muni)
do not count; both peaks must be met in the same direction; the agency hand list is not in the spec; agencies with no
qualifying archive copy keep today's stops and are listed in reference/ca_ab2097_side_bus2022_kept_today.csv.

Run (qualifying feeds only)
- Service on 2022-12-14: trips whose service_id runs that day. Bus routes only (route_type 3 and 700-799).
- A route "qualifies" at a stop if, in one direction, it has 8+ departures 7:00-8:59 and 8+ departures 16:00-17:59
  (4+ an hour in both peaks; the 2023 15-minute rule). A bus major stop is a qualifying stop with a stop of a
  DIFFERENT qualifying route within 150 m (the plan's meeting distance).
- Compare per agency with today's Caltrans existing bus/BRT major stops of the same agency (agency names matched by
  the hand list AGENCY_MATCH below; not in the spec: the spec said "those agencies' counties"; matching by agency keeps
  other agencies' stops in shared counties). Report stops in both (within 150 m), only 2022, only today, and 2020 homes
  within 1/2 mile of each set.
- Headline re-run (homes other than ADUs, main group, main map) with today's bus stops of the matched agencies replaced
  by their 2022 bus major stops. Outputs: reference/ca_ab2097_side_bus2022.csv (per agency) and
  reference/ca_ab2097_side_bus2022_headline.csv.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ca_ab2097_estimate as E  # noqa: E402
import run_ab2097_test as run  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
DIR = RAW / "ca_ab2097" / "gtfs2022"
DAY = "20221214"
WIDE = ("20220101", "20230630")
# GTFS provider (Mobility Database name) -> Caltrans agency_primary (hand list; only agencies with bus major stops)
AGENCY_MATCH = {
    "San Francisco Municipal Transportation Agency (SFMTA - Muni)": "City and County of San Francisco",
    "San Diego International Airport, Metropolitan Transit System (MTS)":
        "San Diego Metropolitan Transit System, Airport, Flagship Cruises",
    "Los Angeles County Metropolitan Transportation Authority (LA Metro)": "Los Angeles County Metropolitan Transportation Authority",
    "Santa Clara Valley Transportation Authority (VTA)": "Santa Clara Valley Transportation Authority",
    "San Mateo County Transit District (samTrans)": "San Mateo County Transit District",
    "Golden Gate Transit": "Golden Gate Bridge, Highway and Transportation District",
    "Santa Cruz Metro (SCMTD)": "Santa Cruz Metro",
    "Monterey-Salinas Transit (MST)": "Monterey-Salinas Transit",
    "Los Angeles Department of Transportation (LADOT - DASH - Commuter Express)": "City of Los Angeles",
    "County Connection (CCCTA)": "Central Contra Costa Transit Authority",
    "GTrans": "City of Gardena",
}


def get(url: str, timeout: int = 300) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, b""


def captures(url: str) -> list[str]:
    q = urllib.parse.urlencode({"url": url, "from": WIDE[0], "to": WIDE[1], "output": "json", "fl": "timestamp",
                                "filter": "statuscode:[23].."})
    st, body = get(f"https://web.archive.org/cdx/search/cdx?{q}")
    if st != 200:
        return []
    return sorted({r[0] for r in json.loads(body or b"[]")[1:]})


def runs_on(z: zipfile.ZipFile, day: str = DAY) -> tuple[set, str | None]:
    """service_ids running on `day`, and the earliest calendar start among them."""
    names = set(z.namelist())
    wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][
        pd.Timestamp(day).weekday()]
    on, starts = set(), []
    if "calendar.txt" in names:
        c = pd.read_csv(z.open("calendar.txt"), dtype=str)
        c.columns = c.columns.str.strip()
        m = (c.start_date <= day) & (c.end_date >= day) & (c[wd].str.strip() == "1")
        on |= set(c.service_id[m])
        starts += list(c.start_date[m])
    if "calendar_dates.txt" in names:
        d = pd.read_csv(z.open("calendar_dates.txt"), dtype=str)
        d.columns = d.columns.str.strip()
        d = d[d.date == day]
        on |= set(d.service_id[d.exception_type.str.strip() == "1"])
        on -= set(d.service_id[d.exception_type.str.strip() == "2"])
    return on, (min(starts) if starts else None)


def fetch() -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    cov = pd.read_csv(REFERENCE / "ca_ab2097_gtfs_archive_coverage.csv")
    cov = cov[cov.captures_2022_01_to_2023_06 > 0]
    log = []
    for r in cov.itertuples():
        for ts in captures(r.url):
            f = DIR / f"{r.mdb_id}_{ts}.zip"
            if not f.exists():
                st, body = get(f"https://web.archive.org/web/{ts}id_/{r.url}")
                time.sleep(5)
                if st != 200 or not body[:2] == b"PK":
                    log.append({"provider": r.provider, "mdb_id": r.mdb_id, "timestamp": ts, "status": f"not a zip ({st})"})
                    continue
                f.write_bytes(body)
            try:
                with zipfile.ZipFile(f) as z:
                    on, start = runs_on(z)
                log.append({"provider": r.provider, "mdb_id": r.mdb_id, "timestamp": ts, "status": "ok",
                            "services_on_2022_12_14": len(on), "calendar_start": start})
            except (zipfile.BadZipFile, KeyError, ValueError) as e:
                log.append({"provider": r.provider, "mdb_id": r.mdb_id, "timestamp": ts, "status": f"unreadable ({e})"})
    lg = pd.DataFrame(log)
    lg["qualifies"] = lg.get("services_on_2022_12_14", pd.Series(dtype=float)).fillna(0) > 0
    lg.to_csv(REFERENCE / "ca_ab2097_side_bus2022_copies.csv", index=False)
    print(lg.to_string(index=False))


def major_stops(z: zipfile.ZipFile) -> pd.DataFrame:
    on, _ = runs_on(z)
    rd = lambda n: pd.read_csv(z.open(n), dtype=str).rename(columns=str.strip)  # noqa: E731
    routes, trips, st, stops = rd("routes.txt"), rd("trips.txt"), rd("stop_times.txt"), rd("stops.txt")
    rt = pd.to_numeric(routes.route_type, errors="coerce")
    bus = set(routes.route_id[(rt == 3) | rt.between(700, 799)])
    trips = trips[trips.service_id.isin(on) & trips.route_id.isin(bus)]
    if "direction_id" not in trips:
        trips["direction_id"] = "0"
    s = st[st.trip_id.isin(trips.trip_id)].merge(trips[["trip_id", "route_id", "direction_id"]], on="trip_id")
    t = s.departure_time.fillna(s.arrival_time).fillna("")
    h = pd.to_numeric(t.str.split(":").str[0], errors="coerce")
    s["am"], s["pm"] = h.between(7, 8), h.between(16, 17)
    g = s.groupby(["stop_id", "route_id", "direction_id"])[["am", "pm"]].sum().reset_index()
    q = g[(g.am >= 8) & (g.pm >= 8)][["stop_id", "route_id"]].drop_duplicates()
    q = q.merge(stops[["stop_id", "stop_lat", "stop_lon"]], on="stop_id")
    q = run.lonlat_points(q, q.stop_lon.astype(float), q.stop_lat.astype(float))
    from scipy.spatial import cKDTree
    tree = cKDTree(q[["x", "y"]].to_numpy())
    major = np.zeros(len(q), bool)
    for i, j in tree.query_pairs(150.0):
        if q.route_id.iat[i] != q.route_id.iat[j]:
            major[i] = major[j] = True
    return q[major].drop_duplicates("stop_id")[["stop_id", "x", "y"]]


def run_checks() -> None:
    from missing_middleware.geom_extra_station import nearest_lowest, read_vector
    lg = pd.read_csv(REFERENCE / "ca_ab2097_side_bus2022_copies.csv", dtype={"timestamp": str, "calendar_start": str})
    ok = lg[lg.qualifies & (lg.calendar_start.fillna("99999999") <= DAY)]
    ok = ok.sort_values("calendar_start").groupby("mdb_id").tail(1)
    ct = read_vector(RAW / "ab2097" / "major_transit_stops.geojson", run.CRS)
    ct = ct[ct.hqta_type.isin(["major_stop_bus", "major_stop_brt"]) & (ct.plan_name.fillna("").str.strip() == "")]
    b = pd.read_parquet(E.CACHE / "blocks.parquet").merge(
        run.read_blocks(["GEOID20", "INTPTLAT20", "INTPTLON20"])[["GEOID20", "x", "y"]], on="GEOID20")
    rows, replaced, new_stops = [], [], []
    for r in ok.itertuples():
        with zipfile.ZipFile(DIR / f"{r.mdb_id}_{r.timestamp}.zip") as z:
            m = major_stops(z)
        ag = AGENCY_MATCH.get(r.provider)
        today = ct[ct.agency_primary == ag][["x", "y"]] if ag else ct.iloc[0:0][["x", "y"]]
        def homes_near(pts):
            if not len(pts):
                return 0.0
            return float(b.homes[run.nearest_m(b, pts) < E.MILE / 2].sum())
        both = 0
        if len(m) and len(today):
            _, d = nearest_lowest(m.x.to_numpy(), m.y.to_numpy(), today.x.to_numpy(), today.y.to_numpy())
            both = int((d <= 150).sum())
        rows.append({"provider": r.provider, "copy_timestamp": r.timestamp, "calendar_start": r.calendar_start,
                     "caltrans_agency": ag or "no match (no bus major stops today or not in hand list)",
                     "major_stops_2022": len(m), "major_stops_today": len(today), "in_both_within_150m": both,
                     "homes_2020_within_half_mile_2022": homes_near(m), "homes_2020_within_half_mile_today": homes_near(today)})
        if ag:
            replaced.append(ag)
            new_stops.append(m[["x", "y"]])
    pd.DataFrame(rows).to_csv(REFERENCE / "ca_ab2097_side_bus2022.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    # headline with today's bus stops of the matched agencies replaced by their 2022 stops
    st = E.stop_sets()
    keep_bus = ct[~ct.agency_primary.isin(replaced)][["x", "y"]]
    kept = ct[~ct.agency_primary.isin(replaced)].groupby("agency_primary").size().rename("bus_major_stops_today")
    kept.reset_index().to_csv(REFERENCE / "ca_ab2097_side_bus2022_kept_today.csv", index=False)
    rail = st["rail_only"]
    other = st["_other_than_rail"]  # ferry + today's bus + planned; rebuild without today's bus of replaced agencies
    stops = pd.concat([rail, keep_bus] + new_stops, ignore_index=True)
    ferry_planned = other.merge(ct[["x", "y"]], on=["x", "y"], how="left", indicator=True)
    stops = pd.concat([stops, ferry_planned[ferry_planned._merge == "left_only"][["x", "y"]]], ignore_index=True)
    p = pd.read_parquet(E.CACHE / "permits.parquet")
    a2 = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=E.A2_COLS, low_memory=False)
    pp = E.add_census_points(E.clean_permits_full(a2), set(E.raw_keys(a2)))
    pp = pp[pp.lat.notna()].copy()
    pts = run.lonlat_points(pp, pp.lon, pp.lat)
    pp["zone_bus2022"] = ab.zone_of(run.nearest_m(pts, stops))
    pp["upz"] = run.in_toc(pts) & (pp.juris == ab.LA)
    b["zone_bus2022"] = ab.zone_of(run.nearest_m(b, stops))
    rep = ab.full_reporters(p)
    main_j = [j for j in rep if j not in E.PLACEBO | E.DROPPED]
    c = E.cells_for(b, "bus2022")
    g = E.group("main", E.with_treated_land(c, main_j))
    est, dr = E.event_study(g, c, E.permits_for(pp, "bus2022"), "homes_non_adu")
    e, d = E.period_contrast(est, dr, E.BEFORE, E.AFTER)
    lo, hi = E.interval(d)
    out = pd.DataFrame([{"case": "headline with 2022 bus major stops for matched agencies (side check, after results)",
                         "agencies_replaced": "; ".join(replaced), "estimate": e, "low": lo, "high": hi,
                         "n_jurisdictions": len(g.juris),
                         "unit": "homes other than ADUs per 1,000 existing homes (2020) per year, 2023-2025 vs 2018-2022"}])
    out.to_csv(REFERENCE / "ca_ab2097_side_bus2022_headline.csv", index=False)
    print(out.round(3).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if a.run:
        run_checks()


if __name__ == "__main__":
    main()

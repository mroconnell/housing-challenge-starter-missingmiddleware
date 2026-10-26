"""Major transit stops and the homes near them: pure functions (no network, no file paths).

Method (docs/tod/MAJOR_TRANSIT_STOP.md, AQ-044, AQ-045, AQ-047):
- Stop locations and route lines come from the BTS National Transit Map (NTM).
- A bus route is *frequent at N trips an hour* when, in one direction, at least N trips start in
  the 7:00 hour and at least N start in the 8:00 hour on a representative Tuesday to Thursday.
  Frequency comes from the agency's GTFS schedule file, except Madison, whose frequency comes from
  the route descriptions Madison publishes (carried in the NTM routes layer).
- A stop qualifies when it lies within 30 metres of a qualifying route line of the same agency.
- Rail and rapid transit: NTM rail route types, The Hop, the Kenosha streetcar (SC), MCTS CONNECT 1
  (CN1) and Madison Rapid Route A. Amtrak is excluded (AQ-047 item 10).
- Homes are 2020 census block housing units whose block internal point lies within the distance.

The geometric helpers take shapely geometries in a projected CRS measured in metres.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import re
import zipfile
from collections import defaultdict
from typing import Iterable, Mapping

MILE_M = 1609.344
STOP_TOLERANCE_M = 30.0
PEAK_HOURS = (7, 8)
MAIN_N = 4   # 15-minute service
HIGH_N = 3   # 20-minute service
WEEKDAYS_TUE_THU = (1, 2, 3)
SCAN_DAYS = 120

# GTFS route_type values that are rail or other fixed guideway (tram, subway, rail, ferry, cable car,
# monorail). 3 is bus; 11 trolleybus is treated as bus.
RAIL_ROUTE_TYPES = frozenset({"0", "1", "2", "4", "5", "6", "7", "12"})
HOP_NTD_ID = "55312"           # The Hop streetcar, City of Milwaukee (routes coded as bus)
MCTS_NTD_ID = "50008"
MADISON_NTD_ID = "50005"
KENOSHA_NTD_ID = "50003"
RAPID_ROUTES = frozenset({(MCTS_NTD_ID, "CN1"), (MADISON_NTD_ID, "A"), (KENOSHA_NTD_ID, "SC")})
RAPID_AGENCIES = frozenset({HOP_NTD_ID})
EXCLUDED_AGENCY_PATTERN = re.compile(r"amtrak", re.I)


# --------------------------------------------------------------------------- GTFS tables

def read_gtfs_table(z: zipfile.ZipFile, name: str) -> list[dict]:
    """Rows of one GTFS table (files may sit in a sub-folder of the zip). Missing table -> []."""
    names = {n.split("/")[-1]: n for n in z.namelist()}
    if name not in names:
        return []
    with z.open(names[name]) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")))


def _s(row: Mapping, key: str) -> str:
    return (row.get(key) or "").strip()


def active_services(calendar: Iterable[Mapping], calendar_dates: Iterable[Mapping], day: dt.date) -> set[str]:
    """service_ids running on `day`, from calendar.txt with calendar_dates.txt exceptions applied."""
    ds = day.strftime("%Y%m%d")
    wd = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")[day.weekday()]
    act = {_s(c, "service_id") for c in calendar
           if _s(c, "start_date") <= ds <= _s(c, "end_date") and _s(c, wd) == "1"}
    for x in calendar_dates:
        if _s(x, "date") == ds:
            if _s(x, "exception_type") == "1":
                act.add(_s(x, "service_id"))
            else:
                act.discard(_s(x, "service_id"))
    return act


def feed_validity(calendar: Iterable[Mapping], calendar_dates: Iterable[Mapping],
                  feed_info: Iterable[Mapping] = ()) -> tuple[dt.date, dt.date]:
    """First and last service date of a feed (feed_info dates win when present)."""
    for fi in feed_info:
        if _s(fi, "feed_start_date") and _s(fi, "feed_end_date"):
            return _date(_s(fi, "feed_start_date")), _date(_s(fi, "feed_end_date"))
    dates = [_s(c, "start_date") for c in calendar] + [_s(c, "end_date") for c in calendar]
    dates += [_s(x, "date") for x in calendar_dates if _s(x, "exception_type") == "1"]
    dates = [d for d in dates if d]
    if not dates:
        raise ValueError("feed has no service dates")
    return _date(min(dates)), _date(max(dates))


def _date(s: str) -> dt.date:
    return dt.datetime.strptime(s, "%Y%m%d").date()


def representative_weekday(trips: Iterable[Mapping], calendar: list[Mapping], calendar_dates: list[Mapping],
                           start: dt.date, scan_days: int = SCAN_DAYS) -> dt.date:
    """The Tuesday, Wednesday or Thursday with the most scheduled trips in the `scan_days` days from
    max(start, feed start). If the feed has already expired at `start`, scan from the feed start.
    Ties go to the earliest date."""
    lo, hi = feed_validity(calendar, calendar_dates)
    d0 = max(lo, start)
    if d0 > hi:
        d0 = lo
    per_service: dict[str, int] = defaultdict(int)
    for t in trips:
        per_service[_s(t, "service_id")] += 1
    best = None
    for i in range(scan_days):
        day = d0 + dt.timedelta(days=i)
        if day > hi:
            break
        if day.weekday() in WEEKDAYS_TUE_THU:
            n = sum(per_service[s] for s in active_services(calendar, calendar_dates, day))
            if best is None or n > best[1]:
                best = (day, n)
    if best is None:
        raise ValueError("no Tuesday to Thursday inside the feed's validity")
    return best[0]


def trip_start_hours(stop_times: Iterable[Mapping], trip_ids: set[str]) -> dict[str, int]:
    """Clock hour (0-based, may exceed 23) at which each trip leaves its first timed stop."""
    first: dict[str, tuple[int, str]] = {}
    for x in stop_times:
        t = _s(x, "trip_id")
        if t not in trip_ids:
            continue
        tm = _s(x, "departure_time") or _s(x, "arrival_time")
        if not tm:
            continue
        seq = int(float(_s(x, "stop_sequence") or 0))
        if t not in first or seq < first[t][0]:
            first[t] = (seq, tm)
    return {t: int(tm.split(":")[0]) for t, (_, tm) in first.items()}


def route_key(route: Mapping) -> str:
    """Name used to match a GTFS route to an NTM route: short name, else long name."""
    return _s(route, "route_short_name") or _s(route, "route_long_name")


def route_peak_trips(routes: Iterable[Mapping], trips: Iterable[Mapping], start_hours: Mapping[str, int],
                     hours: tuple[int, ...] = PEAK_HOURS) -> dict[str, int]:
    """Per route name: the best single direction's *minimum* over `hours` of trips starting in that hour.

    A route is frequent at N when this value is >= N, i.e. one direction has at least N trip starts
    in every one of the peak hours. Directions are never added together. Route ids sharing a name
    are pooled (agencies sometimes split one public route into several ids)."""
    name = {_s(r, "route_id"): route_key(r) for r in routes}
    cnt: dict[tuple[str, str], dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for t in trips:
        tid = _s(t, "trip_id")
        if tid not in start_hours:
            continue
        cnt[(name.get(_s(t, "route_id"), ""), _s(t, "direction_id"))][start_hours[tid]] += 1
    out: dict[str, int] = defaultdict(int)
    for (rn, _dir), hh in cnt.items():
        out[rn] = max(out[rn], min(hh[h] for h in hours))
    return dict(out)


def gtfs_route_peaks(zip_path, start: dt.date) -> tuple[dict[str, int], dict]:
    """Read a GTFS zip and return (route name -> peak one-direction trips, facts about the feed)."""
    with zipfile.ZipFile(zip_path) as z:
        routes = read_gtfs_table(z, "routes.txt")
        trips = read_gtfs_table(z, "trips.txt")
        cal = read_gtfs_table(z, "calendar.txt")
        cd = read_gtfs_table(z, "calendar_dates.txt")
        fi = read_gtfs_table(z, "feed_info.txt")
        day = representative_weekday(trips, cal, cd, start)
        act = active_services(cal, cd, day)
        day_trips = [t for t in trips if _s(t, "service_id") in act]
        ids = {_s(t, "trip_id") for t in day_trips}
        names = {n.split("/")[-1]: n for n in z.namelist()}
        with z.open(names["stop_times.txt"]) as f:
            hours = trip_start_hours(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")), ids)
    lo, hi = feed_validity(cal, cd, fi)
    facts = {"service_day": day.isoformat(), "valid_from": lo.isoformat(), "valid_through": hi.isoformat(),
             "trips_on_day": len(day_trips), "feed_version": _s(fi[0], "feed_version") if fi else ""}
    return route_peak_trips(routes, day_trips, hours), facts


# --------------------------------------------------------------------------- Madison route descriptions

_EVERY = re.compile(r"every\s+(\d+)\s+minutes", re.I)
_APPLIES = re.compile(r"\b(weekday|monday\s+thru\s+(?:friday|saturday)|monday\s+through\s+(?:friday|saturday)|daily)\b", re.I)
_WINDOW = re.compile(r"from approximately (\d{1,2})\s*(AM|PM) until (\d{1,2})\s*(AM|PM)", re.I)


def _hour24(h: str, ampm: str) -> int:
    h = int(h) % 12
    return h + (12 if ampm.upper() == "PM" else 0)


def madison_trips_per_hour(desc: str | None) -> float:
    """Weekday morning-peak trips an hour implied by a Madison Metro route description.

    Reads each sentence that covers weekdays ("Weekday ...", "Monday thru Saturday ...", "Daily ...")
    and takes the shortest "every N minutes" headway. A sentence is skipped when it starts with
    "Evening", is limited to a stretch of the route ("between X and Y"), or names a time window that
    does not cover 7:00 to 9:00. No usable sentence gives 0.
    Examples: "Weekday daytime schedule trips operate at least every 15 minutes." -> 4.0."""
    best = None
    for s in re.split(r"(?<=\.)\s+", desc or ""):
        s = s.strip()
        if not s or s.lower().startswith("evening") or not _APPLIES.search(s) or " between " in s.lower():
            continue
        w = _WINDOW.search(s)
        if w and not (_hour24(w.group(1), w.group(2)) <= PEAK_HOURS[0] and _hour24(w.group(3), w.group(4)) >= PEAK_HOURS[-1] + 1):
            continue
        for m in _EVERY.finditer(s):
            mins = int(m.group(1))
            if mins > 0 and (best is None or mins < best):
                best = mins
    return 60.0 / best if best else 0.0


# --------------------------------------------------------------------------- route classification

def is_excluded_agency(agency_name: str | None) -> bool:
    """Amtrak is dropped from every definition (owner, AQ-047 item 10)."""
    return bool(EXCLUDED_AGENCY_PATTERN.search(agency_name or ""))


def is_rapid(ntd_id: str, route_type: str | None, short_name: str | None, agency_name: str = "") -> bool:
    """Rail or rapid transit route: rail route types, The Hop, Kenosha SC, MCTS CN1, Madison A."""
    if is_excluded_agency(agency_name):
        return False
    ntd_id = (ntd_id or "").strip()
    return ((route_type or "").strip() in RAIL_ROUTE_TYPES or ntd_id in RAPID_AGENCIES
            or (ntd_id, (short_name or "").strip()) in RAPID_ROUTES)


def qualifies(peak_trips: float, n: int) -> bool:
    """Route-level frequency test: the route's best direction has >= n trips in each peak hour."""
    return peak_trips >= n


# --------------------------------------------------------------------------- geometry

def stops_near_routes(stop_points, stop_agency, route_lines, route_agency, tolerance_m: float = STOP_TOLERANCE_M):
    """Boolean array: stop lies within `tolerance_m` of at least one route line of the same agency.

    stop_points / route_lines: arrays of shapely geometries in a metric CRS.
    stop_agency / route_agency: agency ids (same length as the geometry arrays)."""
    import numpy as np
    import shapely

    stop_points = np.asarray(stop_points, dtype=object)
    stop_agency = np.asarray(stop_agency, dtype=object)
    route_lines = np.asarray(route_lines, dtype=object)
    route_agency = np.asarray(route_agency, dtype=object)
    hit = np.zeros(len(stop_points), dtype=bool)
    for ag in set(route_agency.tolist()):
        lines = route_lines[route_agency == ag]
        sel = np.flatnonzero(stop_agency == ag)
        if len(lines) == 0 or len(sel) == 0:
            continue
        tree = shapely.STRtree(lines)
        idx = tree.query(stop_points[sel], predicate="dwithin", distance=tolerance_m)[0]
        hit[sel[np.unique(idx)]] = True
    return hit


def blocks_within(block_points, stop_points, radius_m: float):
    """Boolean array over blocks: the block's internal point lies within `radius_m` of any stop."""
    import numpy as np
    import shapely

    block_points = np.asarray(block_points, dtype=object)
    m = np.zeros(len(block_points), dtype=bool)
    stop_points = np.asarray(stop_points, dtype=object)
    if len(stop_points) == 0 or len(block_points) == 0:
        return m
    tree = shapely.STRtree(block_points)
    idx = tree.query(stop_points, predicate="dwithin", distance=radius_m)[1]
    m[np.unique(idx)] = True
    return m


def blocks_within_variable(block_points, stop_points, radii_m):
    """Like blocks_within, but each stop has its own radius (used for the 35,000-person city rule)."""
    import numpy as np

    radii_m = np.asarray(radii_m, dtype=float)
    stop_points = np.asarray(stop_points, dtype=object)
    m = np.zeros(len(block_points), dtype=bool)
    for r in np.unique(radii_m):
        m |= blocks_within(block_points, stop_points[radii_m == r], float(r))
    return m


def homes_within(block_points, block_homes, stop_points, radius_m: float) -> int:
    """Total housing units in blocks whose internal point lies within `radius_m` of any stop."""
    import numpy as np

    return int(np.asarray(block_homes, dtype=float)[blocks_within(block_points, stop_points, radius_m)].sum())

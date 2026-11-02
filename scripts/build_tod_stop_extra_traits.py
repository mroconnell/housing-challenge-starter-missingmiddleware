"""Extra station traits for the stop table (owner ask 2026-11-02 18:26): opening year, grade and ridership for more stations.

Scope (owner 18:27): reform stations of the 16 places (+ Seattle Roosevelt) and Wisconsin's stations only; comparison
stations are left out of this file for now. Writes reference/tod_stop_extra_traits.csv, one row per (case, stop_key)
of reference/tod_stop_table.csv; scripts/build_tod_stop_table.py merges it as ADDED columns (existing columns unchanged).

Inputs (all local, see each folder's manifest.json):
  data/raw/tod_stop_table/wikidata/wd_<city>.json   Wikidata (CC0) station items by bounding box: P1619 opening, P571
                                                    inception, P31 classes, P81 line
  data/raw/tod_stop_table/ridership/<source>/       agency station ridership (annual series)
  reference/tod_stop_grade_opening_handcoded.csv    line-level grade / opening facts from agency sources (with URL)

Ridership columns (average weekday boardings or entries; measure differs by city, compare within a city only):
  ridership_pre5_avg  = mean over the years reform_year-5 .. reform_year-1 that have a value (a TRAIT)
  ridership_post5_avg = mean over reform_year+1 .. reform_year+5 (an OUTCOME: partly reflects new homes; not a trait)

    .venv/bin/python scripts/build_tod_stop_extra_traits.py          # writes the csv and prints checks

System (metro) level NTD ridership and multi-system node columns (all roles, so this file also has rows for comparison
stations) come from scripts/build_tod_stop_system_traits.py (reference/tod_stop_system_traits.csv), merged in main().
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

CRS = 5070
STOPS = REFERENCE / "tod_stop_table.csv"
OUT = REFERENCE / "tod_stop_extra_traits.csv"
HAND = REFERENCE / "tod_stop_grade_opening_handcoded.csv"
RID = RAW / "tod_stop_table" / "ridership"
WD = RAW / "tod_stop_table" / "wikidata"
USE_MADISON_MPO = False   # Madison MPO stop boardings were assigned to stops with Metro's GTFS: owner to rule (AQ-045)


# =========================================================================== stations

def stations() -> tuple[pd.DataFrame, pd.DataFrame]:
    T = pd.read_csv(STOPS, low_memory=False)
    keep = T.role.isin(["reform", "wisconsin"])
    prio = set(T.loc[keep, "stop_key"])
    # all stations are kept for matching (a source point must go to its nearest station, not the nearest reform station);
    # only the priority stations are written
    U = T.sort_values("role", key=lambda r: r.map({"reform": 0, "wisconsin": 0}).fillna(1)).drop_duplicates("stop_key").reset_index(drop=True)
    U["prio"] = U.stop_key.isin(prio)
    U["x"], U["y"] = X.transform(U.lon.values, U.lat.values, 4326, CRS)
    U["names"] = (U.stop_name.fillna("").astype(str) + ";" + U.names_merged.fillna("").astype(str)).str.split(";")
    # (case, stop_key) is unique except one Philadelphia pair (Broad St subway and Girard trolley 0.5 m apart share a
    # stop_key): one row per (case, stop_key), and that pair shares its traits
    C = T.loc[T.stop_key.isin(prio), ["case", "stop_key", "city", "role", "reform_year"]].drop_duplicates(["case", "stop_key"])
    return U, C


def norm(s: str) -> str:
    s = str(s).lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"\b(station|stn|transit center|transportation center|t\.c|tc|- .*$)\b", " ", s)
    s = s.replace("&", " and ").replace("/", " ").replace("-", " ").replace(".", " ").replace("'", "")
    for a, b in ((r"\bstreet\b", "st"), (r"\bavenue\b", "av"), (r"\bave\b", "av"), (r"\bboulevard\b", "blvd"),
                 (r"\bmount\b", "mt"), (r"\bsaint\b", "st"), (r"\binternational\b", "intl"), (r"\bnorth\b", "n"),
                 (r"\bsouth\b", "s"), (r"\beast\b", "e"), (r"\bwest\b", "w"), (r"\broad\b", "rd"), (r"\bparkway\b", "pkwy")):
        s = re.sub(a, b, s)
    return re.sub(r"\s+", " ", s).strip()


def match_xy(U: pd.DataFrame, lon, lat, maxd: float = 300.0) -> np.ndarray:
    """stop_key of the nearest station within maxd m ('' if none)."""
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    out = np.full(len(lon), "", dtype=object)
    ok = np.isfinite(lon) & np.isfinite(lat)
    if not ok.any() or not len(U):
        return out
    x, y = X.transform(lon[ok], lat[ok], 4326, CRS)
    d, i = cKDTree(np.c_[U.x.values, U.y.values]).query(np.c_[x, y], distance_upper_bound=maxd)
    out[np.flatnonzero(ok)] = np.where(np.isfinite(d), U.stop_key.values[np.minimum(i, len(U) - 1)], "")
    return out


def match_name(U: pd.DataFrame, names, alias: dict | None = None, cutoff: float = 0.92) -> np.ndarray:
    """stop_key of the station whose stop name or a merged member name equals the source name (normalised)."""
    idx: dict[str, set] = {}
    for k, nm in zip(U.stop_key, U.names):
        for n in nm:
            if n.strip():
                idx.setdefault(norm(n), set()).add(k)
    alias = {norm(a): norm(b) for a, b in (alias or {}).items()}
    out = []
    for n in names:
        q = alias.get(norm(n), norm(n))
        ks = idx.get(q)
        if not ks:
            close = difflib.get_close_matches(q, list(idx), n=1, cutoff=cutoff)
            ks = idx.get(close[0]) if close else None
        out.append(next(iter(ks)) if ks and len(ks) == 1 else "")
    return np.array(out, dtype=object)


# =========================================================================== ridership sources (long: stop_key, year, value)

def _agg(df: pd.DataFrame, src: str, measure: str) -> pd.DataFrame:
    df = df[(df.stop_key != "") & np.isfinite(df.value) & (df.value > 0)]
    g = df.groupby(["stop_key", "year"], as_index=False).value.sum()
    g["src"], g["measure"] = src, measure
    return g


def r_new_york(U):
    u = U[U.city == "New York"]
    st = pd.read_csv(RID / "mta_subway_stations.csv")
    st["k"] = match_xy(u, st.gtfs_longitude, st.gtfs_latitude, 250.0)
    st["routes"] = st.daytime_routes.fillna("").str.split()
    st["n"] = st.stop_name.map(norm)
    boro = {"Bronx": "Bx", "Brooklyn": "Bk", "Manhattan": "M", "Queens": "Q"}
    a = pd.read_csv(RID / "mta_annual" / "tidy.csv")
    a["boro"] = a.period_note.str.extract(r"borough=([A-Za-z ]+);")[0].str.strip().map(boro)
    # station row -> complex ids: each '/'-part matched to the best MTA station of that borough (name, then routes)
    keymap = {}
    for (name, line, b) in a[["station_name", "line", "boro"]].drop_duplicates().itertuples(index=False):
        lines = set(str(line).replace(" ", "").split(","))
        cids = set()
        for part in re.split(r"\s*/\s*", re.sub(r"\*", "", str(name))):
            q = norm(part)
            dig = re.findall(r"\d+", q)
            c = st[(st.borough == b) & st.n.map(lambda s: re.findall(r"\d+", s) == dig)]
            if not len(c):
                continue
            ratio = c.n.map(lambda s: difflib.SequenceMatcher(None, s, q).ratio())
            jac = c.routes.map(lambda r: len(lines & set(r)) / max(len(lines | set(r)), 1))
            ok = (ratio >= 0.9) | ((ratio >= 0.75) & (jac > 0))   # a same-name station of another line needs a route in common
            if ((ratio >= 0.9) & (jac > 0)).any():
                ok &= jac > 0
            elif (ratio >= 0.9).sum() > 1:                        # several same-name stations, none sharing a route: ambiguous
                continue
            sc = (ratio + 0.5 * jac)[ok]
            if len(sc):
                cids.add(int(c.complex_id.loc[sc.idxmax()]))
        keymap[(name, line, b)] = cids
    cx = st[st.k != ""].groupby("complex_id").k.apply(lambda s: sorted(set(s)))
    rows = []
    for r in a.itertuples(index=False):
        cids = keymap[(r.station_name, r.line, r.boro)]
        ks = sorted({k for c in cids for k in cx.get(c, [])})
        for k in ks:
            rows.append((k, r.year, float(r.value) / len(ks)))
    nm = sum(bool(v) for v in keymap.values())
    print(f"  New York annual: station rows matched to a complex {nm}/{len(keymap)}")
    out = [_agg(pd.DataFrame(rows, columns=["stop_key", "year", "value"]), "MTA average weekday subway ridership tables 2007-2019 (mta_annual)",
                "average weekday entries")]
    for yr in (2024, 2025):
        d = pd.read_csv(RID / f"mta_subway_weekday_daily_by_complex_{yr}.csv")
        d = d[d.transit_mode == "subway"]
        avg = d.groupby(d.station_complex_id.astype(str).str.strip()).entries.sum() / d.service_date.nunique()
        rows = []
        for cid, ks in cx.items():
            if str(cid) in avg.index:
                rows += [(k, yr, avg[str(cid)] / len(ks)) for k in ks]
        out.append(_agg(pd.DataFrame(rows, columns=["stop_key", "year", "value"]), "MTA hourly ridership, weekday mean (existing stop-table input)",
                        "average weekday entries"))
    return pd.concat(out)


def r_chicago(U):
    u = U[(U.city == "Chicago") & (U.stop_type_text == "CTA rail")]
    a = pd.read_csv(RID / "cta_annual" / "tidy.csv")
    a = a[a.year <= 2025]
    loc = a.dropna(subset=["lat"]).groupby("station_id")[["lat", "lon"]].first()
    a = a.join(loc, on="station_id", rsuffix="_s")
    a["stop_key"] = match_xy(u, a.lon_s, a.lat_s, 250.0)
    return _agg(a, "CTA 'L' station entries daily (City of Chicago 5neh-572f), weekday mean per year (cta_annual)", "average weekday entries")


SEPTA_SUBWAY = {  # septa_hist name (line) -> stop-table name
    ("Girard", "Market-Frankford Line"): "Front-Girard", ("Girard", "Broad Street Line"): "Broad-Girard",
    ("Spring Garden", "Market-Frankford Line"): "Spring Garden", ("Spring Garden", "Broad Street Line"): "Broad-Spring Garden",
    ("2nd Street", "Market-Frankford Line"): "2nd St", ("5th Street", "Market-Frankford Line"): "5th St/Independence Hall",
    ("8th Street", "Market-Frankford Line"): "8th-Market", ("13th Street", "Market-Frankford Line"): "13th St",
    ("15th Street", "Market-Frankford Line"): "15th St/City Hall - B1", ("30th Street", "Market-Frankford Line"): "Drexel Station at 30th St",
    ("34th Street", "Market-Frankford Line"): "34th St", ("40th Street", "Market-Frankford Line"): "40th St",
    ("46th Street", "Market-Frankford Line"): "46th St", ("52nd Street", "Market-Frankford Line"): "52nd St",
    ("60th Street", "Market-Frankford Line"): "60th St", ("63rd Street", "Market-Frankford Line"): "63rd St",
    ("Frankford Transportation Center", "Market-Frankford Line"): "Frankford Transit Center", ("Frankford T.C", "Market-Frankford Line"): "Frankford Transit Center",
    ("Arrott Transportation Center", "Market-Frankford Line"): "Arrott Transit Center", ("Arrott T.C", "Market-Frankford Line"): "Arrott Transit Center",
    ("Allegheny", "Market-Frankford Line"): "Kensington-Allegheny", ("Fairmount", "Broad Street Line"): "Fairmount",
    ("Race-Vine (Convention Center)", "Broad Street Line"): "Race-Vine", ("Race-Vine", "Broad Street Line"): "Race-Vine",
    ("North Philadelphia", "Broad Street Line"): "North Philadelphia", ("Fern Rock Transportation Center", "Broad Street Line"): "Fern Rock Transit Center",
    ("Fern Rock T.C", "Broad Street Line"): "Fern Rock Transit Center", ("Olney Transportation Center", "Broad Street Line"): "Olney",
    ("Olney T.C", "Broad Street Line"): "Olney", ("8th-Market", "Broad-Ridge Spur"): "8th-Market", ("Chinatown", "Broad-Ridge Spur"): "Chinatown",
}
SEPTA_RR_ALIAS = {"Market East Station": "Jefferson Station", "Market East": "Jefferson Station", "University City": "Penn Medicine Station",
                  "North Philadelphia": "North Philadelphia Septa", "Temple U": "Temple University", "Fern Rock T C": "Fern Rock Transit Center",
                  "Fern Rock TC": "Fern Rock Transit Center", "St Martins": "St. Martins"}


def r_philadelphia(U):
    u = U[U.city == "Philadelphia"]
    rail, sub, trol = (u[u.stop_type_text == t] for t in ("Rail", "Subway/elevated", "Trolley"))
    out = []
    # Regional Rail 2017-2024 (open data, coordinates)
    g = pd.DataFrame([f["properties"] for f in json.load(open(RID / "septa_regional_rail_station_ridership_2017_2024.geojson"))["features"]])
    g = g[g.Service_Ty.astype(str).str.contains("Weekday", case=False)]
    s = g.groupby(["Stop_ID", "Year"]).agg(value=("Boards", "sum"), lat=("Latitude", "first"), lon=("Longitude", "first")).reset_index()
    s["stop_key"], s["year"] = match_xy(rail, s.lon, s.lat, 250.0), s.Year.astype(int)
    out.append(_agg(s, "SEPTA Regional Rail ridership by station 2017-2024 (OpenDataPhilly; 2024 = SEPTA estimate)", "average weekday boardings"))
    # SEPTA Annual Service Plans (facts with source page; SEPTA site copyright notice, see septa_hist/manifest.json)
    h = pd.read_csv(RID / "septa_hist" / "tidy.csv")
    h = h[~((h.line == "Market-Frankford Line") & (h.year == 2018))]                       # FY2018 repeats FY2017 exactly
    h = h[~((h.line == "Broad Street Line") & (h.station_name == "City Hall"))]          # definition jump FY2018
    rr = h[h.line == "Regional Rail"].copy()
    rr = rr.drop_duplicates(["station_name", "year"], keep=False)                          # Highland 2013 listed twice
    r13 = rr[rr.year == 2013].set_index("station_name").value
    rr = rr[~((rr.year == 2015) & rr.station_name.map(r13).eq(rr.value))]                  # 2015 rows repeating 2013 (not recounted)
    rr["stop_key"] = match_name(rail, rr.station_name.str.replace(r"\d$", "", regex=True), SEPTA_RR_ALIAS)
    rr.loc[rr.station_name.str.contains("North Philadelphia", case=False), "stop_key"] = ""  # two stations share the name
    out.append(_agg(rr, "SEPTA Annual Service Plans FY2010-FY2017, Regional Rail census (septa_hist)", "average weekday boardings"))
    sb = h[h.line.isin(["Market-Frankford Line", "Broad Street Line", "Broad-Ridge Spur"])].copy()
    nm = [SEPTA_SUBWAY.get((n, l), n) for n, l in zip(sb.station_name, sb.line)]
    sb["stop_key"] = match_name(sub, nm, cutoff=0.97)
    out.append(_agg(sb, "SEPTA Annual Service Plans FY2017-FY2020, station performance (septa_hist; fiscal year = calendar year of its end)",
                    "average weekday turnstile entries (MFL/BSL)"))
    tr = h[h.line.str.contains("trolley|shared", case=False)].copy()
    tr["stop_key"] = match_name(trol, tr.station_name, cutoff=0.95)
    out.append(_agg(tr, "SEPTA Annual Service Plans, trolley stop boards FY2015-FY2018 (septa_hist)", "average weekday boardings (trolley)"))
    t = pd.DataFrame([f["properties"] for f in json.load(open(RID / "septa_trolley_stop_summary_summer2025.geojson"))["features"]])
    t = pd.DataFrame({"stop_key": match_xy(trol, t.Lon, t.Lat, 150.0), "year": 2025, "value": pd.to_numeric(t.Weekdays_O, errors="coerce")})
    out.append(_agg(t, "SEPTA trolley stop summary summer 2025 (OpenDataPhilly)", "average weekday boardings (trolley)"))
    return pd.concat(out)


def r_saint_paul(U):
    u = U[U.city == "Saint Paul"]
    m = pd.read_csv(RID / "metc_annual" / "tidy.csv")
    m = m[m.line.str.contains("Green")]
    m["stop_key"] = match_xy(u, m.lon, m.lat, 250.0)
    return _agg(m, "Metro Transit stop boardings/alightings by year (Met Council, public domain; Green Line 2014 = part year)", "average weekday boardings")


def r_salt_lake(U):
    u = U[U.city == "Salt Lake City"]
    r = pd.read_csv(RID / "uta_rail_stop_ridership_weekday_monthly_2017_on.csv")
    loc = pd.read_csv(RID / "uta_rail_stops_locations.csv").drop_duplicates("stopabbr").set_index("stopabbr")
    r = r[r["mode"].astype(str).str.contains("Light|Streetcar|TRAX|S-Line", case=False) & (r.year_ <= 2025)]   # 2026 = part year
    w = r.groupby(["stopabbrone", "route", "year_"]).avgboardings.mean().groupby(["stopabbrone", "year_"]).sum().reset_index()
    w = w[w.stopabbrone.isin(loc.index)]
    w["stop_key"] = match_xy(u, loc.loc[w.stopabbrone].longitude.values, loc.loc[w.stopabbrone].latitude.values, 250.0)
    w = w.rename(columns={"year_": "year", "avgboardings": "value"})
    return _agg(w, "UTA rail stop ridership, weekday monthly averages 2017 on (UTA open data; mean of months, summed over lines)", "average weekday boardings")


def r_los_angeles(U):
    u = U[U.city == "Los Angeles"]
    a = pd.read_csv(RID / "la_metro" / "la_metro_station_weekday_boardings.csv")
    a = a[a.provenance.str.startswith("official")]                                        # third-party 2025 rail sheet left out
    a["year"] = a.period.str.extract(r"FY(\d{4})")[0].astype(int)
    a["stop_key"] = ""
    rail, brt = a["mode"].eq("rail"), a["mode"].eq("BRT")                                 # rail rows to rail stations, G Line rows to BRT stations
    a.loc[rail, "stop_key"] = match_xy(u[u["mode"] != "BRT"], a.lon[rail], a.lat[rail], 300.0)
    a.loc[brt, "stop_key"] = match_xy(u[u["mode"] == "BRT"], a.lon[brt], a.lat[brt], 300.0)
    a["value"] = a.avg_weekday_boardings
    return _agg(a, "LA Metro station boardings FY2017-FY2019 (rail, DPGTL archive) and G Line stop APC FY2017-2019, FY2025; FY = year of its end",
                "average weekday boardings")


def r_san_diego(U):
    u = U[U.city == "San Diego"]
    a = pd.read_csv(RID / "sd_mts" / "sd_mts_trolley_station_weekday_boardings.csv")
    a["year"] = a.period.str.extract(r"FY(\d{4})")[0].astype(int)
    a["value"] = a.avg_weekday_boardings
    a["stop_key"] = match_name(u, a.station_name, {"Fifth Avenue Station": "5th Avenue Station", "Grantville Station": "Union Grantville Station",
                                                   "Alvarado Station": "UCSD Health East Station"})
    return _agg(a, "SANDAG Passenger Counting Program APC (ridership dashboard service), FY2025-FY2026 only", "average weekday boardings")


def r_denver(U):
    u = U[U.city == "Denver"]
    a = pd.read_csv(RID / "denver_rtd" / "denver_rtd_rail_station_weekday_boardings_annual.csv")
    a["stop_key"], a["value"] = match_xy(u, a.lon, a.lat, 300.0), a.avg_weekday_boardings
    return _agg(a, "RTD Rail Station Activity reports 2012-2019 (Internet Archive copies), mean of runboards per year", "average weekday boardings")


def r_portland(U):
    u = U[(U.city == "Portland") & (U["mode"] == "light rail")]
    a = pd.read_csv(RID / "trimet" / "trimet_max_station_weekday_boardings_annual.csv")
    a = a[a.year != 2022]
    a["stop_key"], a["value"] = match_xy(u, a.lon, a.lat, 300.0), a.avg_weekday_boardings
    return _agg(a, "TriMet MAX passenger census 2017-2025 (spring/fall mean; 2022 repeats 2021, left out)", "average weekday boardings")


def r_seattle(U):
    u = U[U.city.isin(["Seattle", "Bellevue"])]
    a = pd.read_csv(RID / "sound_transit" / "tidy.csv")
    a["stop_key"] = match_name(u, a.station_name, {"Tukwila International Boulevard": "Tukwila Int'l Blvd", "SeaTac / Airport": "SeaTac/Airport",
                                                   "International District / Chinatown": "Int'l Dist/Chinatown"})
    return _agg(a, "Sound Transit SIP 2015 (fall 2013 sample) and Q4 service delivery reports 2016 (Q4 only), 2017-2019, 2020 (Q4 only)",
                "average weekday boardings")


def r_austin(U):
    u = U[U.city == "Austin"]
    a = pd.read_csv(RID / "capmetro" / "tidy.csv")
    a["stop_key"] = match_name(u, a.station_name, {"Downtown": "Convention Center", "MLK Jr.": "MLK Blvd", "Highland": "Highland Mall",
                                                   "Crestview": "Lamar Blvd / Justin"})
    return _agg(a, "CapMetro TOD Priority Tool station profiles (April 2016 only)", "average weekday boardings")


def r_madison(U):
    if not USE_MADISON_MPO:
        return pd.DataFrame(columns=["stop_key", "year", "value", "src", "measure"])
    u = U[U.city.isin(["Madison", "Shorewood Hills", "Sun Prairie"])]
    a = pd.read_csv(RID / "wi_rapid" / "tidy.csv")
    a = a[a.line == "Rapid Route A"]
    a["stop_key"] = match_xy(u, a.lon, a.lat, 150.0)
    return _agg(a, "Greater Madison MPO weekday boardings by stop, April 2025", "average weekday boardings (Route A)")


def ridership_long(U) -> pd.DataFrame:
    parts = []
    for f in (r_new_york, r_chicago, r_philadelphia, r_saint_paul, r_salt_lake, r_los_angeles, r_san_diego, r_denver, r_portland,
              r_seattle, r_austin, r_madison):
        p = f(U)
        print(f"  {f.__name__}: stations {p.stop_key.nunique()}, station-years {len(p)}")
        parts.append(p)
    R = pd.concat(parts, ignore_index=True)
    # one value per station-year: first source in the order above wins (sources rarely overlap; Philadelphia modes differ by station)
    R = R.drop_duplicates(["stop_key", "year"], keep="first")
    return R


def ridership_traits(C: pd.DataFrame, R: pd.DataFrame) -> pd.DataFrame:
    by = {k: g.sort_values("year") for k, g in R.groupby("stop_key")}
    rows = []
    for case, k, ry in C[["case", "stop_key", "reform_year"]].itertuples(index=False):
        g = by.get(k)
        r = {"case": case, "stop_key": k}
        if g is not None and len(g):
            yv = dict(zip(g.year.astype(int), g.value))
            ry = int(ry)
            pre = {y: v for y, v in yv.items() if ry - 5 <= y <= ry - 1}
            post = {y: v for y, v in yv.items() if ry + 1 <= y <= ry + 5}
            near = min(yv, key=lambda y: (abs(y - ry), y))
            p20 = [y for y in yv if y <= 2019]
            r.update({
                "ridership_pre5_avg": round(np.mean(list(pre.values())), 1) if pre else np.nan,
                "ridership_pre5_years": ",".join(map(str, sorted(pre))), "ridership_pre5_n": len(pre),
                "ridership_post5_avg": round(np.mean(list(post.values())), 1) if post else np.nan,
                "ridership_post5_years": ",".join(map(str, sorted(post))), "ridership_post5_n": len(post),
                "ridership_near_reform": round(yv[near], 1), "ridership_near_reform_year": near,
                "ridership_pre2020_last": round(yv[max(p20)], 1) if p20 else np.nan, "ridership_pre2020_last_year": max(p20) if p20 else np.nan,
                "ridership_last": round(yv[max(yv)], 1), "ridership_last_year": max(yv),
                "ridership_series": ";".join(f"{y}:{yv[y]:.0f}" for y in sorted(yv)),
                "ridership_series_measure": " | ".join(dict.fromkeys(g.measure)),
                "ridership_series_source": " | ".join(dict.fromkeys(g.src)),
            })
        rows.append(r)
    return pd.DataFrame(rows)


# =========================================================================== Wikidata: opening year and grade

GRADE_CLASS = {"underground station": "underground", "underground railway station": "underground", "underground metro station": "underground",
               "elevated station": "elevated", "elevated metro station": "elevated", "station located on surface": "at grade",
               "station located in a cut": "open cut", "railway station in a highway median": "highway median"}
RAIL_CLASS = {"tram stop", "railway station", "metro station", "light rail station", "elevated station", "station located on surface",
              "underground station", "underground railway station", "underground metro station", "elevated metro station",
              "station located in a cut", "railway station in a highway median", "union station", "one-way station",
              "dead-end railway station", "multi-level interchange railway station", "interchange station", "railway stop",
              "Keilbahnhof", "bus rapid transit station", "bus station", "airport railway station", "streetcar stop"}


def wikidata_items() -> pd.DataFrame:
    rows = []
    for f in sorted(WD.glob("wd_*.json")):
        for b in json.load(open(f))["results"]["bindings"]:
            g = lambda k: b.get(k, {}).get("value")  # noqa: E731
            m = re.match(r"Point\((-?[\d.]+) (-?[\d.]+)\)", g("coord") or "")
            if not m:
                continue
            rows.append({"qid": g("item").rsplit("/", 1)[-1], "label": g("itemLabel"), "lon": float(m.group(1)), "lat": float(m.group(2)),
                         "open": (g("open") or "")[:4], "incep": (g("incep") or "")[:4], "closed": (g("closed") or "")[:4],
                         "inst": g("instLabel") or "", "line": g("lineLabel") or ""})
    D = pd.DataFrame(rows)
    I = D.groupby("qid").agg(label=("label", "first"), lon=("lon", "first"), lat=("lat", "first"),
                             open=("open", lambda s: min([v for v in s if v.isdigit()], default="")),
                             incep=("incep", lambda s: min([v for v in s if v.isdigit()], default="")),
                             closed=("closed", lambda s: max([v for v in s if v.isdigit()], default="")),
                             inst=("inst", lambda s: sorted(set(s))), line=("line", lambda s: sorted(set(v for v in s if v)))).reset_index()
    I = I[I.inst.map(lambda c: bool(set(c) & RAIL_CLASS)) & I.closed.eq("") & ~I.inst.map(lambda c: "former railway station" in c)]
    return I.reset_index(drop=True)


def wikidata_match(U: pd.DataFrame, I: pd.DataFrame, maxd: float = 300.0, min_sim: float = 0.6) -> pd.DataFrame:
    """Each station: Wikidata items within maxd m whose label is similar to a station name (best name ratio >= min_sim)."""
    ix, iy = X.transform(I.lon.values, I.lat.values, 4326, CRS)
    tree = cKDTree(np.c_[ix, iy])
    out = []
    for r in U.itertuples(index=False):
        if not r.prio or (r.role == "wisconsin" and r.mode == "BRT"):
            continue
        cand = tree.query_ball_point([r.x, r.y], maxd)
        names = [norm(n) for n in r.names if str(n).strip()]
        acc = []
        for j in cand:
            lab = norm(I.label.iat[j])
            sim = max((difflib.SequenceMatcher(None, lab, n).ratio() for n in names), default=0.0)
            # labels like 'Othello station' vs 'Othello': also accept containment
            if any(n and min(len(n), len(lab)) >= 0.6 * max(len(n), len(lab)) and (n in lab or lab in n) for n in names):
                sim = max(sim, 0.9)
            if sim >= min_sim:
                acc.append((j, sim, float(np.hypot(ix[j] - r.x, iy[j] - r.y))))
        if not acc:
            continue
        best = max(s for _, s, _ in acc)
        acc = [a for a in acc if a[1] >= best - 0.15]
        js = [a[0] for a in acc]
        opens = [int(I.open.iat[j]) for j in js if I.open.iat[j]]
        incs = [int(I.incep.iat[j]) for j in js if I.incep.iat[j]]
        grades = sorted({GRADE_CLASS[c] for j in js for c in I.inst.iat[j] if c in GRADE_CLASS})
        out.append({"stop_key": r.stop_key, "wikidata_qids": " ".join(I.qid.iat[j] for j in js),
                    "wikidata_labels": " | ".join(I.label.iat[j] for j in js),
                    "wikidata_match_m": round(max(a[2] for a in acc), 0), "wikidata_name_sim": round(min(a[1] for a in acc), 2),
                    "wd_open_min": min(opens) if opens else np.nan, "wd_open_max": max(opens) if opens else np.nan,
                    "wd_incep_min": min(incs) if incs else np.nan,
                    "wd_grade": "/".join(grades), "wd_lines": " | ".join(sorted({l for j in js for l in I.line.iat[j]}))})
    return pd.DataFrame(out)


# =========================================================================== hand-coded agency facts, assembly, checks

def handcoded(U: pd.DataFrame) -> pd.DataFrame:
    H = pd.read_csv(HAND, dtype=str).fillna("")
    out = []
    for h in H.itertuples(index=False):
        u = U[U.city == h.city]
        if h.key_type == "stop_type_text" and h.key_value != "ALL":
            u = u[u.stop_type_text == h.key_value]
        elif h.key_type == "gtfs_stop_id":
            u = u[u.gtfs_stop_ids.fillna("").str.split().map(lambda s: h.key_value in s)]
        elif h.key_type == "stop_key":
            u = u[u.stop_key == h.key_value]
        for k in u.stop_key:
            out.append({"stop_key": k, "hc_open": float(h.opening_year) if h.opening_year else np.nan, "hc_open_src": h.opening_source,
                        "hc_grade": h.grade, "hc_grade_src": h.grade_source})
    # later rows (more specific keys) win
    return pd.DataFrame(out).drop_duplicates("stop_key", keep="last") if out else pd.DataFrame(columns=["stop_key"])


def assemble() -> pd.DataFrame:
    U, C = stations()
    print("ridership:")
    R = ridership_long(U)
    RT = ridership_traits(C, R)
    I = wikidata_items()
    M = wikidata_match(U, I)
    H = handcoded(U)
    S = U[["stop_key", "opening_year", "grade"]].rename(columns={"opening_year": "_oy", "grade": "_gr"}).merge(M, on="stop_key", how="left").merge(H, on="stop_key", how="left")
    for c in ("hc_open", "hc_open_src", "hc_grade", "hc_grade_src", "wd_grade", "wikidata_qids"):
        if c not in S:
            S[c] = np.nan if c == "hc_open" else ""
    S[["hc_open_src", "hc_grade", "hc_grade_src", "wd_grade", "wikidata_qids"]] = S[["hc_open_src", "hc_grade", "hc_grade_src", "wd_grade", "wikidata_qids"]].fillna("")
    oy, osrc = [], []
    for r in S.itertuples(index=False):
        if np.isfinite(r.hc_open):
            oy.append(r.hc_open), osrc.append("agency (hand-coded): " + r.hc_open_src)
        elif np.isfinite(r.wd_open_min):
            oy.append(r.wd_open_min), osrc.append(f"Wikidata P1619 date of official opening, earliest of matched items ({r.wikidata_qids})"
                                                   + (f"; items differ up to {int(r.wd_open_max)}" if r.wd_open_max != r.wd_open_min else ""))
        elif np.isfinite(r.wd_incep_min):
            oy.append(r.wd_incep_min), osrc.append(f"Wikidata P571 inception, earliest of matched items ({r.wikidata_qids})")
        else:
            oy.append(np.nan), osrc.append("")
    S["opening_year_extra"], S["opening_year_extra_source"] = oy, osrc
    S["grade_extra"] = np.where(S.hc_grade != "", S.hc_grade, S.wd_grade.str.replace("/", " / "))
    S["grade_extra"] = S.grade_extra.map(lambda g: g if " / " not in g else "mixed (" + g + ")")
    S["grade_extra_source"] = np.where(S.hc_grade != "", "agency (hand-coded): " + S.hc_grade_src,
                                       np.where(S.wd_grade != "", "Wikidata P31 station class (" + S.wikidata_qids + ")", ""))
    # best-of columns: the stop table's own value where it has one, else the extra value
    S["opening_year_best"] = S._oy.where(S._oy.notna(), S.opening_year_extra)
    S["grade_best"] = np.where(S._gr.fillna("unknown") != "unknown", S._gr, S.grade_extra.replace("", "unknown"))
    S = S.rename(columns={"wd_lines": "wikidata_lines"})
    keep = ["stop_key", "wikidata_qids", "wikidata_labels", "wikidata_match_m", "wikidata_name_sim", "wikidata_lines",
            "opening_year_extra", "opening_year_extra_source", "opening_year_best", "grade_extra", "grade_extra_source", "grade_best"]
    out = C[["case", "stop_key", "reform_year"]].merge(S[keep], on="stop_key", how="left").merge(RT, on=["case", "stop_key"], how="left")
    out["opening_after_reform"] = np.where(out.opening_year_best.notna(), (out.opening_year_best > out.reform_year).astype(int), np.nan)
    return out.drop(columns=["reform_year"])


def checks(E: pd.DataFrame) -> None:
    pd.set_option("display.width", 220, "display.max_columns", 30, "display.max_colwidth", 70)
    T = pd.read_csv(STOPS, low_memory=False)
    T = T.merge(E, on=["case", "stop_key"], how="inner")
    u = T.drop_duplicates("stop_key")
    print(f"\nrows {len(E):,} (case x station), stations {E.stop_key.nunique():,}")
    print("\n== coverage by city, unique stations (before = stop table column, after = best-of / new)")
    g = u.assign(gb=u.grade.ne("unknown"), ga=u.grade_best.ne("unknown"), ob=u.opening_year.notna(), oa=u.opening_year_best.notna(),
                 rb=u.ridership_weekday_2019.notna() | u.ridership_weekday_latest.notna(), ra=u.ridership_last.notna(),
                 pre=u.ridership_pre5_avg.notna(), post=u.ridership_post5_avg.notna())
    tab = g.groupby("city")[["stop_key"]].count().rename(columns={"stop_key": "stations"}).join(
        g.groupby("city")[["gb", "ga", "ob", "oa", "rb", "ra", "pre", "post"]].sum())
    tab.loc["TOTAL"] = tab.sum()
    print(tab.rename(columns={"gb": "grade_before", "ga": "grade_after", "ob": "open_before", "oa": "open_after", "rb": "rider_before",
                              "ra": "rider_after", "pre": "pre5_avg", "post": "post5_avg"}).to_string())
    print("\n== opening year checks: before 1860 or after 2026")
    print(u[(u.opening_year_best < 1860) | (u.opening_year_best > 2026)][["city", "stop_name", "opening_year_best", "opening_year_extra_source"]].to_string(index=False))
    print("\n== stations opened after the case's reform year (case rows)")
    a = T[T.opening_after_reform == 1]
    print(a.groupby("city").size().to_string())
    print(a.drop_duplicates("stop_key")[["city", "stop_name", "reform_year", "opening_year_best"]].head(40).to_string(index=False))
    print("\n== stop table opening year vs Wikidata where both exist (differences > 1 year)")
    d = u[u.opening_year.notna() & u.opening_year_extra.notna() & ((u.opening_year - u.opening_year_extra).abs() > 1)]
    print(d[["city", "stop_name", "opening_year", "opening_year_extra", "wikidata_labels"]].to_string(index=False))
    print("\n== grade by city and mode (unique stations)")
    print(u.groupby(["city", "mode"]).grade_best.value_counts().unstack(fill_value=0).to_string())
    print("\n== stop table grade vs Wikidata grade where both known")
    b = u[(u.grade != "unknown") & u.grade_extra.fillna("").ne("")]
    print(pd.crosstab(b.grade, b.grade_extra).to_string())
    print("\n== Wikidata match distance and name similarity")
    print(u.wikidata_match_m.describe().round(0).to_string(), "\n", u.wikidata_name_sim.value_counts(bins=[0, .7, .8, .9, 1.0]).to_string())
    print("\n== ridership vs trips per hour (unique stations): Spearman by city")
    for c, h in u.groupby("city"):
        for rc in ("ridership_pre2020_last", "ridership_last", "ridership_pre5_avg"):
            z = h[[rc, "tph_peak"]].dropna()
            if len(z) >= 5:
                print(f"  {c:15s} {rc:24s} n={len(z):4d} rho(peak)={z[rc].corr(z.tph_peak, method='spearman'):.2f}")
    print("\n== new ridership vs stop table ridership (same year), ratio median by city")
    for yc, oc in (("ridership_pre2020_last", "ridership_weekday_2019"),):
        z = u[(u.ridership_pre2020_last_year == 2019) & u[oc].notna() & u[yc].notna()]
        if len(z):
            print((z[yc] / z[oc]).groupby(z.city).describe()[["count", "min", "50%", "max"]].round(2).to_string())


def main() -> None:
    E = assemble()
    # system (metro) level ridership and multi-system node columns, all roles (scripts/build_tod_stop_system_traits.py)
    SYS = REFERENCE / "tod_stop_system_traits.csv"
    if SYS.exists():
        E = E.merge(pd.read_csv(SYS, low_memory=False), on=["case", "stop_key"], how="outer", validate="one_to_one")
    E.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(E):,} rows, {E.shape[1]} columns)")
    checks(E)


if __name__ == "__main__":
    main()

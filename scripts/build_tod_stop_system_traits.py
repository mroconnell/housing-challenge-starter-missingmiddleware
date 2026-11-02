"""System (metro) level ridership and multi-system nodes for the stop table (owner asks 2026-11-02 20:10 and 20:12).

One row per (case, stop_key) of reference/tod_stop_table.csv, ALL roles (reform, comparison, Wisconsin). Writes
reference/tod_stop_system_traits.csv and merges its columns into reference/tod_stop_extra_traits.csv (rows added for
stations that file did not have); scripts/build_tod_stop_table.py --merge-extra then ADDS the columns to the stop table.

1. System ridership (a SYSTEM / METRO level trait: a transit system spans its metro area; not a station or city value)
   FTA National Transit Database "Complete Monthly Ridership (with Adjustments and Estimates)", data.transportation.gov
   8bui-9xvu (public domain), unlinked passenger trips (UPT) by agency (NTD ID), mode and type of service, monthly.
   Annual = calendar-year sum over types of service; a year counts only when all 12 months have a value and the total
   is > 0. system_upt_pre5_avg = mean over reform_year-5 .. reform_year-1 (a TRAIT); post5 = reform_year+1 .. +5 (an
   OUTCOME); all = every complete year 2002-2025. Wisconsin: reform year 2027 (the law's start, owner 20:10); pre = the
   latest 5 complete years (2021-2025); no post.
2. Systems at the node: every NTD agency + mode whose stop points lie within node_radius_m of the station point
   (the larger of 200 m — the stop table's GTFS matching distance — and 150 m + half the station's footprint; the
   stop builder merges points within 150 m): the station's own system,
   other stop-table stations, and National Transit Map rail stops (all agencies; bus stops not included).
   system_upt_* use the LARGEST system at the node (by its all-years average); system_upt_pre5_sum_all sums the pre
   averages of every system at the node.
3. trips_peak/midday_all_systems: unique trips per hour at every GTFS stop within node_radius_m, from every feed the
   stop table uses for the city, summed over feeds (the stop table's tph_* give each GTFS stop to its NEAREST station
   row only, so a node split into rows by mode splits its trips). Systems at the node with no local feed are listed in
   trips_all_systems_missing (not counted).

    .venv/bin/python scripts/build_tod_stop_system_traits.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

CRS = 5070
STOPS = REFERENCE / "tod_stop_table.csv"
OUT = REFERENCE / "tod_stop_system_traits.csv"
EXTRA = REFERENCE / "tod_stop_extra_traits.csv"
NTD_DIR = RAW / "tod_stop_table" / "ntd"
NTD_CSV = NTD_DIR / "ntd_complete_monthly_ridership_8bui-9xvu.csv"
NTM_FILES = [RAW / "tod_census_cases" / "ntm_rail_stops.json", NTD_DIR / "ntm_rail_stops_extra.json"]
NTM_G = RAW / "tod_census_cases" / "ntm_la_g_line.json"
WI_REFORM = 2027
LAST_FULL = 2025
COVID = (2020, 2021, 2022)
UNIT = "annual unlinked passenger trips (NTD UPT, calendar year, all types of service)"

# system key "NTDID MODE" -> components (ntd_id, mode, first year, last year); a key not listed is (id, mode, all years)
COMPOSITE = {
    "30019 LR/SR": [("30019", "LR", 2002, 2011), ("30019", "SR", 2012, 2100)],   # SEPTA trolleys: LR until 2011, SR from 2012
    "50003 SR": [("50003", "LR", 2002, 2011), ("50003", "SR", 2012, 2100)],      # Kenosha streetcar
    "00001 SR": [("00001", "LR", 2002, 2011), ("00001", "SR", 2012, 2100)],      # Seattle Streetcar (King County)
    "60048 YR": [("60048", "CR", 2002, 2011), ("60048", "YR", 2012, 2100)],      # CapMetro MetroRail
    "00008 YR": [("00008", "CR", 2002, 2011), ("00008", "YR", 2012, 2100)],      # TriMet WES
    "90030 YR": [("90030", "LR", 2002, 2011), ("90030", "YR", 2012, 2100)],      # NCTD Sprinter
    "00058 SR": [("00008", "SR", 2012, 2012), ("00058", "SR", 2013, 2100)],      # Portland Streetcar (inside TriMet LR before 2012)
}
NOTES = {
    "30019 LR/SR": "SEPTA trolley: NTD mode LR to 2011, SR from 2012 (one series)",
    "90154 RB": "LA Metro BRT reported as RB from 2012; G Line inside bus (MB) before, so no years before 2012",
    "50008 MB": "MCTS CONNECT 1 BRT is not a separate NTD mode: whole MCTS bus (MB) system used",
    "50005 RB": "Madison Metro BRT (Route A) reported as RB from 2024 (opened Sept 2024); earlier years are bus (MB), not used",
    "00040 LR": "Sound Transit LR before 2009 is Tacoma Link only (Central Link opened July 2009)",
    "00058 SR": "Portland Streetcar: TriMet SR 2012, City of Portland SR from 2013; before 2012 inside TriMet LR (not split)",
    "90002 HR": "Skyline opened June 2023",
    "55312 SR": "The Hop opened Nov 2018",
    "40008 SR": "CityLYNX Gold Line opened July 2015",
    "60048 YR": "MetroRail opened March 2010: NTD CR 2010-2011, YR from 2012",
    "50003 SR": "Kenosha streetcar: NTD LR to 2011, SR from 2012",
}
TYPE_MODE = {'"Subway, Metro"': "HR", '"Rail"': "CR", '"Tram, Streetcar, Light rail"': "LR"}
TRAM_BY_AGENCY = {"30019": "LR/SR", "00001": "SR", "00058": "SR", "50003": "SR", "60048": "YR", "90030": "YR"}
RAIL_BY_AGENCY = {"20099": "HR"}   # Staten Island Railway: NTM type Rail, NTD heavy rail

# the feeds of build_tod_stop_table.FEEDS by city -> the systems they cover (for trips_all_systems_missing)
FEED_SYSTEMS = {
    "New York": {"20008 HR", "20099 HR"}, "Philadelphia": {"30019 CR", "30019 HR", "30019 LR/SR"},
    "Chicago": {"50066 HR", "50118 CR"}, "Los Angeles": {"90154 HR", "90154 LR", "90154 RB"}, "San Diego": {"90026 LR"},
    "Honolulu": {"90002 HR"}, "Denver": {"80006 LR", "80006 CR"}, "Portland": {"00008 LR", "00008 YR", "00058 SR"},
    "Salt Lake City": {"80001 LR"}, "Austin": {"60048 YR"}, "Seattle": {"00040 LR"}, "Bellevue": {"00040 LR"},
    "Saint Paul": {"50027 LR"}, "Charlotte": {"40008 LR", "40008 SR"},
    "Wisconsin": {"50008 MB", "55312 SR", "50003 SR"},
}


# =========================================================================== NTD annual series

def ntd_annual() -> tuple[pd.DataFrame, dict]:
    n = pd.read_csv(NTD_CSV, dtype=str, usecols=["NTD ID", "Agency", "Mode", "Date", "UPT"])
    n["UPT"] = pd.to_numeric(n.UPT.str.replace(",", ""), errors="coerce")
    n["year"] = n.Date.str[-4:].astype(int)
    m = n.groupby(["NTD ID", "Mode", "Date", "year"], as_index=False).UPT.sum(min_count=1)
    a = m.groupby(["NTD ID", "Mode", "year"]).agg(upt=("UPT", "sum"), months=("UPT", "count")).reset_index()
    a["complete"] = (a.months == 12) & (a.upt > 0)
    names = n.drop_duplicates("NTD ID").set_index("NTD ID").Agency.to_dict()
    return a, names


def series(key: str, A: pd.DataFrame) -> pd.Series:
    """Complete calendar years -> UPT for a system key."""
    comps = COMPOSITE.get(key) or [(key.split()[0], key.split()[1], 2002, 2100)]
    parts = []
    for nid, mode, y0, y1 in comps:
        s = A[(A["NTD ID"] == nid) & (A.Mode == mode) & A.year.between(y0, y1) & A.complete]
        parts.append(s.set_index("year").upt)
    s = pd.concat(parts).sort_index() if parts else pd.Series(dtype=float)
    return s[s.index <= LAST_FULL]


def window(s: pd.Series, y0: int, y1: int):
    w = s[(s.index >= y0) & (s.index <= y1)]
    yrs = [int(y) for y in w.index]
    return (float(w.mean()) if len(w) else np.nan, ";".join(map(str, yrs)), len(yrs),
            ";".join(str(y) for y in yrs if y in COVID))


# =========================================================================== stations and their systems

def own_system(r) -> str:
    c, m = r.city, r["mode"]
    if r.role == "wisconsin" or c in ("Milwaukee", "Madison") or isinstance(r.agency, str):
        return {"City of Milwaukee": "55312 SR", "Milwaukee County": "50008 MB", "City of Madison": "50005 RB",
                "City of Kenosha": "50003 SR"}.get(r.agency, "")
    if c == "New York":
        return "20099 HR" if "Staten Island" in str(r.lines) else "20008 HR"
    tab = {
        "Philadelphia": {"heavy rail": "30019 HR", "commuter rail": "30019 CR", "light rail/trolley": "30019 LR/SR"},
        "Chicago": {"heavy rail": "50066 HR", "commuter rail": "50118 CR"},
        "Los Angeles": {"heavy rail": "90154 HR", "light rail": "90154 LR", "BRT": "90154 RB"},
        "San Diego": {"light rail": "90026 LR"}, "Honolulu": {"heavy rail": "90002 HR"},
        "Denver": {"light rail": "80006 LR", "commuter rail": "80006 CR"},
        "Portland": {"light rail": "00008 LR", "streetcar": "00058 SR", "commuter rail": "00008 YR"},
        "Salt Lake City": {"light rail": "80001 LR"}, "Austin": {"commuter rail": "60048 YR"},
        "Seattle": {"light rail": "00040 LR"}, "Bellevue": {"light rail": "00040 LR"},
        "Saint Paul": {"light rail": "50027 LR"}, "Charlotte": {"light rail": "40008 LR", "streetcar": "40008 SR"},
    }
    return tab.get(c, {}).get(m, "")


def ntm_points() -> pd.DataFrame:
    fr = []
    for f in NTM_FILES:
        s = pd.DataFrame(json.load(open(f)))
        fr.append(s[["ntd_id", "stop_name", "stop_lat", "stop_lon", "stop_type_text"]])
    g = pd.DataFrame(json.load(open(NTM_G)))
    g["stop_type_text"] = "G Line"
    fr.append(g[["ntd_id", "stop_name", "stop_lat", "stop_lon", "stop_type_text"]])
    s = pd.concat(fr, ignore_index=True).dropna(subset=["stop_lat", "stop_lon"])
    s["ntd_id"] = s.ntd_id.astype(str).str.zfill(5)

    def sysk(r):
        t = str(r.stop_type_text)
        if t == "G Line":
            return f"{r.ntd_id} RB"
        mode = TYPE_MODE.get(t, "LR")
        if mode == "LR":
            mode = TRAM_BY_AGENCY.get(r.ntd_id, "LR")
            if r.ntd_id == "40008" and "CityLYNX" in str(r.stop_name):   # CATS Gold Line streetcar stops
                mode = "SR"
        if mode == "CR":
            mode = RAIL_BY_AGENCY.get(r.ntd_id, "CR")
        return f"{r.ntd_id} {mode}"
    s["sys"] = s.apply(sysk, axis=1)
    s["x"], s["y"] = X.transform(s.stop_lon.values.astype(float), s.stop_lat.values.astype(float), 4326, CRS)
    return s


def node_systems(U: pd.DataFrame, P: pd.DataFrame) -> pd.Series:
    """stop_key -> sorted list of system keys at the node."""
    tU = cKDTree(np.c_[U.x.values, U.y.values])
    tP = cKDTree(np.c_[P.x.values, P.y.values])
    out = {}
    for i, r in enumerate(U.itertuples(index=False)):
        s = {r.own} if r.own else set()
        for j in tU.query_ball_point([r.x, r.y], r.rad):
            if U.own.iat[j]:
                s.add(U.own.iat[j])
        for j in tP.query_ball_point([r.x, r.y], r.rad):
            s.add(P.sys.iat[j])
        out[r.stop_key] = sorted(s)
    return pd.Series(out)


# =========================================================================== trips per hour summed over systems

def trips_all(U: pd.DataFrame) -> pd.DataFrame:
    import build_tod_stop_table as B
    rows = {}
    for city, feeds in B.FEEDS.items():
        Uc = U[U.city == city]
        if not len(Uc):
            continue
        acc = np.zeros((len(Uc), 2))
        labs = []
        for path, filt, lab in feeds:
            if not path.exists():
                continue
            E, st, day = B.feed_departures(path, filt)
            st = st[st.stop_id.isin(set(E.stop_id))]
            sx, sy = X.transform(st.stop_lon.values, st.stop_lat.values, 4326, CRS)
            t = cKDTree(np.c_[sx, sy])
            pk = E[(E.sec >= 7 * 3600) & (E.sec < 9 * 3600)]
            md = E[(E.sec >= 10 * 3600) & (E.sec < 14 * 3600)]
            pk_by, md_by = pk.groupby("stop_id").trip_id.apply(set), md.groupby("stop_id").trip_id.apply(set)
            sid = st.stop_id.values
            for k, r in enumerate(Uc.itertuples(index=False)):
                ids = [sid[j] for j in t.query_ball_point([r.x, r.y], r.rad)]
                a = set().union(*[pk_by.get(i, set()) for i in ids]) if ids else set()
                b = set().union(*[md_by.get(i, set()) for i in ids]) if ids else set()
                acc[k, 0] += len(a) / 2
                acc[k, 1] += len(b) / 4
            labs.append(f"{lab} ({path.name}, weekday {day})")
            print(f"  trips: {city} {lab} day {day}")
        for k, r in enumerate(Uc.itertuples(index=False)):
            rows[r.stop_key] = (acc[k, 0], acc[k, 1], "; ".join(labs), city)
    # Wisconsin: the station's own trips (stop table tph, exact member stop ids, all routes) + other WI agencies'
    # trips at their stops within the node radius
    W = U[U.role == "wisconsin"]
    if len(W):
        own_tp = W.set_index("stop_key")[["tph_peak", "tph_midday"]]
        add = pd.DataFrame(0.0, index=W.stop_key, columns=["p", "m"])
        labs = []
        for ag, path in B.WI_FEEDS.items():
            E, st, day = B.feed_departures(path, lambda r: True)
            sx, sy = X.transform(st.stop_lon.values, st.stop_lat.values, 4326, CRS)
            t = cKDTree(np.c_[sx, sy])
            sid = st.stop_id.values
            for r in W.itertuples(index=False):
                if r.agency == ag:
                    continue
                ids = set(sid[j] for j in t.query_ball_point([r.x, r.y], r.rad))
                e = E[E.stop_id.isin(ids)]
                add.loc[r.stop_key, "p"] += e[(e.sec >= 7 * 3600) & (e.sec < 9 * 3600)].trip_id.nunique() / 2
                add.loc[r.stop_key, "m"] += e[(e.sec >= 10 * 3600) & (e.sec < 14 * 3600)].trip_id.nunique() / 4
            labs.append(f"{ag} ({path.name}, weekday {day})")
        for k in W.stop_key:
            p0, m0 = own_tp.loc[k, "tph_peak"], own_tp.loc[k, "tph_midday"]
            rows[k] = (p0 + add.loc[k, "p"], m0 + add.loc[k, "m"],
                       "own: stop table tph (exact member stop ids, all routes); others: " + "; ".join(labs), "Wisconsin")
    T = pd.DataFrame.from_dict(rows, orient="index", columns=["trips_peak_all_systems", "trips_midday_all_systems",
                                                              "trips_all_systems_feeds", "_feedcity"])
    return T


# =========================================================================== assemble

def assemble() -> pd.DataFrame:
    T = pd.read_csv(STOPS, low_memory=False)
    A, names = ntd_annual()
    U = (T.sort_values("role", key=lambda r: r.map({"reform": 0, "wisconsin": 0}).fillna(1))
         .drop_duplicates("stop_key").reset_index(drop=True).copy())
    # a stop_key shared by two rows of different mode (one Philadelphia pair): own systems of both
    own_all = T.assign(own=T.apply(own_system, axis=1)).groupby("stop_key").own.apply(lambda s: sorted(set(x for x in s if x)))
    U["own"] = U.apply(own_system, axis=1)
    U["x"], U["y"] = X.transform(U.lon.values, U.lat.values, 4326, CRS)
    U["rad"] = np.maximum(200.0, 150.0 + U.footprint_m.fillna(0) / 2)
    P = ntm_points()
    NS = node_systems(U, P)
    for k, v in own_all.items():   # add the second own system of the shared stop_key
        NS[k] = sorted(set(NS.get(k, [])) | set(v))
    allkeys = sorted(set(k for v in NS for k in v))
    S = {k: series(k, A) for k in allkeys}
    size = {k: (float(s.mean()) if len(s) else -1.0) for k, s in S.items()}
    print("trips per hour over all systems:")
    TR = trips_all(U)

    C = T[["case", "stop_key", "role", "city", "reform_year"]].drop_duplicates(["case", "stop_key"]).copy()
    rows = []
    for r in C.itertuples(index=False):
        sysl = NS.get(r.stop_key, [])
        own = own_all.get(r.stop_key, [])
        big = max(sysl, key=lambda k: size.get(k, -1)) if sysl else ""
        wi = r.role == "wisconsin"
        ry = WI_REFORM if wi else int(r.reform_year)
        d = {"case": r.case, "stop_key": r.stop_key, "system_upt_reform_year_used": ry,
             "n_systems_at_node": len(sysl),
             "systems_at_node": "; ".join(f"{k} ({names.get(k.split()[0], '?')})" for k in sysl),
             "transfer_hub": int(len(sysl) >= 2),
             "own_system": "; ".join(own), "system_ntd_id": big.split()[0] if big else "",
             "system_mode": big.split()[1] if big else "", "system_agency": names.get(big.split()[0], "") if big else "",
             "system_series_note": NOTES.get(big, ""), "system_upt_unit": UNIT}
        s = S.get(big, pd.Series(dtype=float))
        if wi:
            yrs = sorted(s.index)[-5:]
            pre = window(s, yrs[0], yrs[-1]) if yrs else (np.nan, "", 0, "")
            post = (np.nan, "", 0, "")
        else:
            pre, post = window(s, ry - 5, ry - 1), window(s, ry + 1, ry + 5)
        al = window(s, 2002, LAST_FULL)
        for nm, w in (("pre5", pre), ("post5", post), ("all", al)):
            d[f"system_upt_{nm}_avg"], d[f"system_upt_{nm}_years"], d[f"system_upt_{nm}_n"], d[f"system_upt_{nm}_covid_years"] = w
        # own system pre (when the largest at the node is another system) and sum over all node systems
        if own:
            so = S.get(own[0], pd.Series(dtype=float))
            if wi:
                yo = sorted(so.index)[-5:]
                d["own_system_upt_pre5_avg"] = window(so, yo[0], yo[-1])[0] if yo else np.nan
            else:
                d["own_system_upt_pre5_avg"] = window(so, ry - 5, ry - 1)[0]
        tot, nn = 0.0, 0
        for k in sysl:
            sk = S.get(k, pd.Series(dtype=float))
            if wi:
                yk = sorted(sk.index)[-5:]
                v = window(sk, yk[0], yk[-1])[0] if yk else np.nan
            else:
                v = window(sk, ry - 5, ry - 1)[0]
            if np.isfinite(v):
                tot, nn = tot + v, nn + 1
        d["system_upt_pre5_sum_all"] = tot if nn else np.nan
        d["system_upt_pre5_sum_all_n_systems"] = nn
        rows.append(d)
    out = pd.DataFrame(rows)
    rad = U.set_index("stop_key").rad
    out["node_radius_m"] = out.stop_key.map(rad).round(1)
    TR2 = TR.reindex(out.stop_key)
    for c in ("trips_peak_all_systems", "trips_midday_all_systems", "trips_all_systems_feeds"):
        out[c] = TR2[c].values
    miss = []
    for r in out.itertuples(index=False):
        fc = TR._feedcity.get(r.stop_key, None)
        cov = FEED_SYSTEMS.get(fc, set()) if isinstance(fc, str) else set()
        sysl = NS.get(r.stop_key, [])
        miss.append("; ".join(k for k in sysl if k not in cov) if isinstance(fc, str) else "; ".join(sysl))
    out["trips_all_systems_missing"] = miss
    # Madison: own trips not computable (AQ-045)
    mad = out.own_system.eq("50005 RB")
    out.loc[mad, ["trips_peak_all_systems", "trips_midday_all_systems"]] = np.nan
    out.loc[mad, "trips_all_systems_feeds"] = "not computed: Madison Metro GTFS not allowed (AQ-045)"
    return out


def checks(E: pd.DataFrame, T: pd.DataFrame) -> None:
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 90)
    M = T[["case", "stop_key", "city", "role", "stop_name", "mode", "tph_peak", "tph_midday"]].drop_duplicates(["case", "stop_key"]).merge(E, on=["case", "stop_key"])
    u = M.drop_duplicates("stop_key")
    print(f"\nrows {len(E):,}; stations {E.stop_key.nunique():,}")
    print("\n== unmapped stations (no own system)")
    print(u[u.own_system.eq("")][["city", "role", "stop_name", "mode"]].to_string(index=False) or "  none")
    print("\n== coverage by city and role (rows): pre5 filled, post5 filled, all filled")
    g = M.assign(pre=M.system_upt_pre5_avg.notna(), post=M.system_upt_post5_avg.notna(), al=M.system_upt_all_avg.notna())
    print(g.groupby(["city", "role"])[["pre", "post", "al"]].agg(["sum", "count"]).to_string())
    print("\n== system series (annual UPT, millions) by system used")
    s = u.groupby(["system_ntd_id", "system_mode", "system_agency"]).agg(stations=("stop_key", "size"),
                                                                          all_avg_m=("system_upt_all_avg", lambda x: round(x.iloc[0] / 1e6, 2)),
                                                                          years=("system_upt_all_years", "first"))
    s["years"] = s.years.str.split(";").map(lambda y: f"{y[0]}-{y[-1]} ({len(y)})" if y and y[0] else "")
    print(s.to_string())
    print("\n== pre5 by case (millions), years, COVID years in window")
    print(M.groupby(["case", "system_ntd_id", "system_mode"]).agg(pre=("system_upt_pre5_avg", lambda x: round(x.iloc[0] / 1e6, 2)),
                                                                   yrs=("system_upt_pre5_years", "first"), covid=("system_upt_pre5_covid_years", "first"),
                                                                   post=("system_upt_post5_avg", lambda x: round(x.iloc[0] / 1e6, 2))).head(140).to_string())
    print("\n== transfer hubs (n_systems_at_node >= 2), unique stations by city")
    print(u.groupby("city").transfer_hub.agg(["sum", "count"]).to_string())
    print("\n== largest system at node differs from the station's own system")
    dd = u[(u.own_system != "") & (u.system_ntd_id + " " + u.system_mode != u.own_system.str.split("; ").str[0])]
    print(dd[["city", "stop_name", "own_system", "systems_at_node"]].to_string(index=False))
    print("\n== named nodes")
    pat = "30th St|Union Station|Clark/Lake|Ogilvie|Chicago Union|Denver Union|Jamaica|Atlantic Av|World Trade|Christopher|33 St$|Fulton St|Penn|Suburban|Jefferson"
    q = u[u.stop_name.astype(str).str.contains(pat) & u.city.isin(["Philadelphia", "Los Angeles", "Chicago", "Denver", "New York"])]
    print(q[["city", "stop_name", "mode", "systems_at_node", "tph_peak", "trips_peak_all_systems", "tph_midday",
             "trips_midday_all_systems", "trips_all_systems_missing"]].to_string(index=False))
    print("\n== trips_all vs tph (unique stations): ratio summary by city")
    z = u[u.tph_peak > 0]
    print((z.trips_peak_all_systems / z.tph_peak).groupby(z.city).describe()[["count", "min", "50%", "max"]].round(2).to_string())


def main() -> None:
    E = assemble()
    E.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(E):,} rows, {E.shape[1]} columns)")
    if EXTRA.exists():
        X0 = pd.read_csv(EXTRA, low_memory=False)
        new = [c for c in E.columns if c not in ("case", "stop_key")]
        X0 = X0.drop(columns=[c for c in new if c in X0.columns])
        X1 = X0.merge(E, on=["case", "stop_key"], how="outer", validate="one_to_one")
        X1.to_csv(EXTRA, index=False)
        print(f"merged into {EXTRA} ({len(X1):,} rows, {X1.shape[1]} columns)")
    checks(E, pd.read_csv(STOPS, low_memory=False))


if __name__ == "__main__":
    main()

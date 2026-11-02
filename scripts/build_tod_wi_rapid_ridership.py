"""Wisconsin rapid-transit stop ridership: every published stop- or station-level number found, keyed by source stop name.

Owner ask (2026-11-02 20:15): "try harder for Milwaukee's BRT, The Hop and Kenosha". Sources and the search log are in
data/raw/tod_stop_table/ridership/wi_rapid/manifest.json. Writes (added files only; the stop table is not changed):

  data/raw/tod_stop_table/ridership/wi_rapid/stop_ridership_by_name.csv   one row per (source stop, period, measure)
  data/raw/tod_stop_table/ridership/wi_rapid/system_monthly.csv           fallback: line / system totals by month

Matching: each source stop goes to the nearest station of reference/tod_stop_table.csv within 150 m, using the source's
own coordinates (Madison: the MPO layer's stop_lat / stop_lon; never Metro's GTFS, AQ-045) or, for MCTS / The Hop, the
agency stop ids already listed in the stop table's gtfs_stop_ids column (MCTS and Hop GTFS are not barred).
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W = ROOT / "data" / "raw" / "tod_stop_table" / "ridership" / "wi_rapid"
STOPS = ROOT / "reference" / "tod_stop_table.csv"


def dist_m(lat1, lon1, lat2, lon2):
    k = math.pi / 180
    x = (lon2 - lon1) * k * math.cos((lat1 + lat2) / 2 * k)
    y = (lat2 - lat1) * k
    return 6371000 * math.hypot(x, y)


def load_stations():
    rows = list(csv.DictReader(open(STOPS)))
    st = {}
    for r in rows:
        if not r["case"].startswith("wi_"):
            continue
        k = r["stop_key"]
        s = st.setdefault(k, {"stop_key": k, "lat": float(r["lat"]), "lon": float(r["lon"]), "agency": r["agency"],
                              "ids": set(r["gtfs_stop_ids"].split()), "cases": set()})
        s["cases"].add(r["case"])
    return list(st.values())


def by_xy(st, lat, lon, maxd=150.0):
    best = min(st, key=lambda s: dist_m(lat, lon, s["lat"], s["lon"]))
    d = dist_m(lat, lon, best["lat"], best["lon"])
    return (best["stop_key"], round(d, 1)) if d <= maxd else ("", round(d, 1))


def by_ids(st, agency, ids):
    keys = sorted({s["stop_key"] for s in st if s["agency"] == agency and s["ids"] & set(ids)})
    return ";".join(keys)


COLS = ["system", "line", "source_stop_name", "source_stop_id", "level", "period", "year", "measure", "value", "unit_note",
        "stop_key", "match_method", "match_m", "source_url", "source_file", "licence", "note"]


def main():
    st = load_stations()
    out = []

    # ---------------------------------------------------------------- Madison Rapid Route A (Greater Madison MPO, April 2025)
    mpo = "https://maps.cityofmadison.com/arcgis/rest/services/MPO/Ridership_AllRoutes/MapServer/2/query?where=StopMode%3D%27RB%27&outFields=*&returnGeometry=false&f=json"
    for r in csv.DictReader(open(W / "tidy.csv")):
        if r["line"] not in ("Rapid Route A", "all routes at stop"):
            continue
        k, d = by_xy(st, float(r["lat"]), float(r["lon"]))
        out.append(dict(system="Madison Metro Transit (counts) / Greater Madison MPO (publisher)", line=r["line"],
                        source_stop_name=r["station_name"], source_stop_id=r["station_id"], level="platform (one direction)",
                        period="2025-04 (22-day weekday APC sample)", year=2025, measure=r["measure"],
                        value=round(float(r["value"]), 2), unit_note="boardings per average weekday; one platform",
                        stop_key=k, match_method="MPO layer's own stop_lat/stop_lon, nearest station <=150 m", match_m=d,
                        source_url=mpo, source_file="madison_mpo_ridership_allroutes_layer2_rb.json",
                        licence="not stated on layer (copyright MATPB); City of Madison data policy",
                        note="MPO app: 'Metro's APC data is pending certification by the Federal Transit Administration'"))

    # ---------------------------------------------------------------- MCTS CONNECT 1 (only published station figure)
    out.append(dict(system="Milwaukee County Transit System", line="CONNECT 1 BRT", source_stop_name="Water Street (Wisconsin & Water BRT station)",
                    source_stop_id="9648;9649", level="station (both directions)", period="2023-06-04 to 2023-06-10 (first week)",
                    year=2023, measure="rides per day at station (MCTS: 'rides'; Marquette Today / Milwaukee Business Journal: people exiting)",
                    value=300, unit_note="rounded to 100 by MCTS; first week, fares free",
                    stop_key=by_ids(st, "Milwaukee County", ["9648", "9649"]),
                    match_method="MCTS GTFS stop ids 9648/9649 (WISCONSIN & WATER BRT STATION) in stop table gtfs_stop_ids", match_m="",
                    source_url="https://www.metro-magazine.com/news/mcts-announces-ridership-numbers-on-connect-1 ; https://today.marquette.edu/2023/06/marquette-campus-stops-among-new-bus-rapid-transit-lines-most-popular/",
                    source_file="", licence="news report of an MCTS release (fact only)",
                    note="stop_key also holds Van Buren and Jackson BRT stations and 9 Hop stops; the 300 is Water St only"))
    areas = [("Downtown Milwaukee", 700, 900, 900), ("Marquette University", 500, 600, 900), ("Near West Side", None, None, 700),
             ("Wauwatosa", None, None, 250), ("Milwaukee Regional Medical Center", 200, 200, 175)]
    srcs = [("2023-06-04 to 2023-06-10", 2023, "https://www.metro-magazine.com/news/mcts-announces-ridership-numbers-on-connect-1", ""),
            ("summer 2023 (report dated 2023-08-18)", 2023, "https://legistar.granicus.com/MilwaukeeCounty/attachments/81f66846-3934-45e7-8f10-46a36fbac947.pdf", "mcts_legistar_23-828_powerpoint.pdf"),
            ("fall 2023 (report dated 2023-11-08)", 2023, "https://legistar.granicus.com/MilwaukeeCounty/attachments/8ae711b1-15d7-4bcd-8136-52231decbfcd.pdf", "mcts_legistar_23-994_powerpoint.pdf")]
    for name, *vals in areas:
        for (per, yr, url, f), v in zip(srcs, vals):
            if v is None:
                continue
            out.append(dict(system="Milwaukee County Transit System", line="CONNECT 1 BRT", source_stop_name=name, source_stop_id="",
                            level="area (several stations; not station level)", period=per, year=yr,
                            measure="rides per day to the area (destination; MCTS 'rides')", value=v, unit_note="rounded by MCTS",
                            stop_key="", match_method="not matched: area figure", match_m="", source_url=url, source_file=f,
                            licence="Milwaukee County public record / news report (fact only)", note=""))

    # ---------------------------------------------------------------- The Hop: Lakefront stop, July 2024
    out.append(dict(system="The Hop (City of Milwaukee DPW)", line="L Line", source_stop_name="Lakefront", source_stop_id="TL-10;TL-20",
                    level="stop", period="2024-07 (31 days, all days)", year=2024, measure="boardings (APC 'Total ON') in month",
                    value=3366, unit_note="month total; slide also says avg 109 boardings a day (3,366 / 31 = 108.6)",
                    stop_key=by_ids(st, "City of Milwaukee", ["TL-10", "TL-20"]),
                    match_method="Hop GTFS stop ids TL-10/TL-20 ('Lakefront') in stop table gtfs_stop_ids", match_m="",
                    source_url="https://milwaukee.legistar1.com/milwaukee/attachments/0570d688-6a35-4fde-8d5e-4810ffdcd740.pdf",
                    source_file="mke_legistar_240191_hop_presentation_2024-09-11.pdf",
                    licence="City of Milwaukee public record (Legistar file 240191)",
                    note="July includes Summerfest (Jul 4-6: 380/650/738) and German Fest / Air & Water Show weekend (Jul 26-28: 176/365/143)"))
    out.append(dict(system="The Hop (City of Milwaukee DPW)", line="L Line", source_stop_name="Lakefront", source_stop_id="TL-10;TL-20",
                    level="stop", period="2024-07 (31 days, all days)", year=2024, measure="boardings per day, mean of all days",
                    value=109, unit_note="as stated on the slide", stop_key=by_ids(st, "City of Milwaukee", ["TL-10", "TL-20"]),
                    match_method="Hop GTFS stop ids TL-10/TL-20", match_m="",
                    source_url="https://milwaukee.legistar1.com/milwaukee/attachments/0570d688-6a35-4fde-8d5e-4810ffdcd740.pdf",
                    source_file="mke_legistar_240191_hop_presentation_2024-09-11.pdf",
                    licence="City of Milwaukee public record (Legistar file 240191)", note="festival-heavy month; not a typical weekday"))

    with open(W / "stop_ridership_by_name.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, COLS)
        w.writeheader()
        w.writerows(out)

    # ---------------------------------------------------------------- fallback: monthly totals
    mon = []
    hop = json.load(open(W / "hop_monthly_ridership.json"))
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    for y, d in hop.items():
        for m, v in d.items():
            if v.get("total") is None:
                continue
            mon.append(dict(system="The Hop", line="M + L Line (whole system)", month=f"{y}-{months.index(m) + 1:02d}",
                            measure="boardings in month (APC)", value=v["total"], value_daily=v.get("daily"),
                            source="thehopmke.com/ridership (embedded ridershipDataJSON)", licence="(c) The Hop; no data terms stated",
                            note=v.get("note") or ""))
    names = {("50003", "SR"): ("Kenosha Area Transit", "Kenosha Streetcar"), ("50003", "LR"): ("Kenosha Area Transit", "Kenosha Streetcar (reported as LR to 2011)"),
             ("55312", "SR"): ("The Hop", "M + L Line (whole system)"), ("50005", "RB"): ("Madison Metro Transit", "Rapid Route A (mode RB)")}
    for r in csv.DictReader(open(W / "ntd_monthly_upt_wi_sr_rb.csv")):
        s, l = names[(r["ntd_id"], r["mode"])]
        mon.append(dict(system=s, line=l, month=r["date"][:7], measure="unlinked passenger trips in month (NTD, adjusted/estimated)",
                        value=r["upt"], value_daily="", source="FTA NTD Complete Monthly Ridership, data.transportation.gov 8bui-9xvu",
                        licence="Public Domain U.S. Government", note=f"ntd_id {r['ntd_id']} mode {r['mode']} tos {r['tos']}"))
    mon.sort(key=lambda r: (r["system"], r["source"], r["month"]))
    with open(W / "system_monthly.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(mon[0]))
        w.writeheader()
        w.writerows(mon)
    print(len(out), "stop rows;", len(mon), "monthly rows")


if __name__ == "__main__":
    main()

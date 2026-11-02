"""TOD "today" snapshot for all 16 station-area reform places: existing homes per acre (2020) within 1/4 and 1/2 mile
of each place's reform stops (the stops its reform covered, as the station-area study coded them).

    .venv/bin/python scripts/build_tod_reform_density.py      # fetches missing Census block files first (network)

In:  reference/tod_station_area_stations.csv (role == "reform"; New York, Philadelphia and 11 other places)
     scripts/run_tod_station_checks.py stops_for() (group == "reform"; Los Angeles TOC, San Diego, Honolulu: the same
     stops the station-area model used)
     data/raw/census_tiger_2020_tabblock/tl_2020_{st}_tabblock20.zip (via build_tod_today_density.fetch_blocks)
Out: reference/tod_reform_density.csv   one row per place (or group pool) and band

Method: exactly as scripts/build_tod_today_density.py (its read_blocks / measure / local_tm are reused): a block counts
if its internal point lies within the band of any of the place's stops; homes = sum of HOUSING20; land = sum of ALAND20
(water excluded) in acres; homes per acre = homes / land acres. Each stop location counted once per place. Typical stop
= median over the place's stops of each stop's own homes per acre within 1/2 mile. Places near a state line also read
the neighbouring state's blocks (New York + New Jersey, Philadelphia + New Jersey, Chicago + Indiana, Portland +
Washington), so blocks across the line are not lost.

Groups: "older (2009-2014)" = the six older reforms (same numbers as reference/tod_today_density.csv); "newer (2015 on)"
= the eight later reforms; "pooled rezonings (many years)" = New York's 22 rezonings and Philadelphia's 64 remappings
(2003-2019), each city's reform stops pooled. A pooled row per group: blocks counted once per city (each stop once);
the cities' totals then summed; typical stop = median over all the group's stops. Chicago 2015 and Chicago 2022 share
one stop list in the station-area study, so both rows use the same stops and Chicago is counted once in the pool.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_tod_today_density as TD  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

OUT = REFERENCE / "tod_reform_density.csv"
OLD, NEW, POOL = "older (2009–2014)", "newer (2015 on)", "pooled rezonings (many years)"
GROUP_ORDER = [OLD, NEW, POOL]

# (place, reform year, group, stop source, case ids, state FIPS read (first = home state), pool key)
PLACES = [
    ("Austin", "2009", OLD, "table", ["austin_2009"], ["48"], "Austin"),
    ("BelRed (Bellevue)", "2009", OLD, "table", ["bellevue_belred_2009"], ["53"], "Bellevue"),
    ("Salt Lake City", "2010", OLD, "table", ["slc_2010"], ["49"], "Salt Lake City"),
    ("Saint Paul", "2011", OLD, "table", ["stpaul"], ["27"], "Saint Paul"),
    ("Seattle Othello", "2012", OLD, "table", ["seattle_nbh_othello_2012"], ["53"], "Seattle"),
    ("Seattle Mount Baker", "2014", OLD, "table", ["seattle_mount_baker_2014"], ["53"], "Seattle"),
    ("Chicago", "2015", NEW, "table", ["chicago"], ["17", "18"], "Chicago"),
    ("Honolulu", "2017", NEW, "checks", ["honolulu_2017"], ["15"], "Honolulu"),
    ("Los Angeles TOC", "2017", NEW, "checks", ["la_toc_2017"], ["06"], "Los Angeles"),
    ("Denver", "2018", NEW, "table", ["denver_2018"], ["08"], "Denver"),
    ("Charlotte", "2019", NEW, "table", ["charlotte"], ["37"], "Charlotte"),
    ("Portland", "2020", NEW, "table", ["portland_2020"], ["41", "53"], "Portland"),
    ("San Diego", "2021", NEW, "checks", ["san_diego_2021"], ["06"], "San Diego"),
    ("Chicago", "2022", NEW, "table", ["chicago"], ["17", "18"], "Chicago"),
    ("New York (22 rezonings)", "2003–2019", POOL, "city", ["New York"], ["36", "34"], "New York"),
    ("Philadelphia (64 remappings)", "2003–2019", POOL, "city", ["Philadelphia"], ["42", "34"], "Philadelphia"),
]


def reform_stops(src: str, keys: list[str], st: pd.DataFrame) -> pd.DataFrame:
    if src == "table":
        s = st[st.case.isin(keys) & (st.role == "reform")]
    elif src == "city":
        s = st[st.city.isin(keys) & (st.role == "reform")]
    else:
        import run_tod_station_checks as C
        S = C.stops_for(keys[0])
        S = S[S.group == "reform"]
        lon, lat = C.X.transform(S.x.values, S.y.values, C.CRS, 4326)
        s = pd.DataFrame({"stop": S.stop_name.values, "lat": lat, "lon": lon})
    if s.empty:
        raise SystemExit(f"no reform stops for {keys}")
    # each stop location once (the same station listed under several cases or lines)
    return s.assign(lat=s.lat.round(6), lon=s.lon.round(6)).drop_duplicates(["lat", "lon"])[["stop", "lat", "lon"]]


def main() -> None:
    st = pd.read_csv(REFERENCE / "tod_station_area_stations.csv")
    blocks: dict[str, pd.DataFrame] = {}

    def blocks_for(fips: list[str]) -> pd.DataFrame:
        for f in fips:
            if f not in blocks:
                print(f"reading blocks {f}", flush=True)
                blocks[f] = TD.read_blocks(f).assign(home_state=f)
        return pd.concat([blocks[f] for f in fips], ignore_index=True)

    rows, done, by_city = [], {}, {}
    for place, year, group, src, keys, fips, city in PLACES:
        key = (src, tuple(keys))
        if key not in done:
            s = reform_stops(src, keys, st)
            b = blocks_for(fips)
            pooled, per = TD.measure(b, s, TD.local_tm(s))
            done[key] = (s, pooled, per)
            if len(fips) > 1:  # homes counted from the neighbouring state, for the notes
                other = b[b.home_state != fips[0]]
                if len(other):
                    p2, _ = TD.measure(other, s, TD.local_tm(s))
                    print(f"  {place}: homes from state(s) {fips[1:]}: "
                          + ", ".join(f"{k} {v[0]:.0f}" for k, v in p2.items()))
        s, pooled, per = done[key]
        by_city.setdefault(group, {}).setdefault(city, ([], fips))[0].append(s)
        for band in TD.BANDS:
            h, a = pooled[band]
            rows.append({"group": group, "place": place, "reform_year": year, "band": band, "n_stops": len(s),
                         "homes_2020": int(round(h)), "land_acres": round(a, 1),
                         "homes_per_acre": round(h / a, 2) if a else np.nan,
                         "typical_stop_homes_per_acre_half_mile":
                             round(float(per["homes_per_acre_half_mile"].median()), 2) if band == "half_mile" else np.nan})
    for group in GROUP_ORDER:
        cities = []  # (stops, pooled, per) per city, each stop location once within the city
        for city, (ss, fips) in by_city[group].items():
            s = pd.concat(ss).drop_duplicates(["lat", "lon"])
            cities.append((s, *TD.measure(blocks_for(fips), s, TD.local_tm(s))))
        n = sum(len(v[0]) for v in cities)
        med = float(pd.concat([v[2]["homes_per_acre_half_mile"] for v in cities]).median())
        for band in TD.BANDS:
            h = sum(v[1][band][0] for v in cities)
            a = sum(v[1][band][1] for v in cities)
            rows.append({"group": group, "place": f"{group} — pooled", "reform_year": "", "band": band, "n_stops": n,
                         "homes_2020": int(round(h)), "land_acres": round(a, 1), "homes_per_acre": round(h / a, 2),
                         "typical_stop_homes_per_acre_half_mile": round(med, 2) if band == "half_mile" else np.nan})
    out = pd.DataFrame(rows)
    out["_g"] = out.group.map(GROUP_ORDER.index)
    out["_p"] = out.place.str.endswith("pooled").astype(int)
    out = out.sort_values(["_g", "_p", "reform_year", "place", "band"], kind="stable",
                          key=lambda c: c.map({"quarter_mile": 0, "half_mile": 1}) if c.name == "band" else c)
    out = out.drop(columns=["_g", "_p"])
    out["source"] = ("Census 2020 blocks (TIGER/Line tabblock20 HOUSING20, ALAND20); block counted if its internal "
                     "point is within the band of any reform stop")
    out.to_csv(OUT, index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(out.drop(columns=["source"]).to_string(index=False))
    print(f"wrote {OUT} ({len(out)} rows)")


if __name__ == "__main__":
    main()

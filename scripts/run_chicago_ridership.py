"""Chicago "L" ridership test (plan: docs/tod/CHICAGO_RIDERSHIP_PREREG.md).

    uv run --all-extras python scripts/run_chicago_ridership.py --stage stations   # step 1: station measures
    uv run --all-extras python scripts/run_chicago_ridership.py --stage lists      # step 2: dropped/treated/comparison lists
    uv run --all-extras python scripts/run_chicago_ridership.py --stage estimate   # step 3: comparisons

The stages run in this order so that the dropped-station list and the group lists are written into
docs/tod/CHICAGO_RIDERSHIP_RESULTS.md before any comparison is computed (plan section 3).

Inputs (git-ignored): data/raw/cta_ridership/ (scripts/fetch_cta_ridership.py) and the Chicago case data in
data/raw/tod_cases/ (scripts/fetch_tod_cases.py). The Chicago case adapter (missing_middleware/tod/case_chicago.py)
is imported, never edited: it labels each parcel treatment / comparison and eligible.

Per station (CTA "L" stop locations, 8pix-ypme; platforms of one station averaged to one point), within 1/2 mile:
- treated_acres: eligible acres of upzoned (treatment) parcels, by representative point;
- added_floor_area_sqft: sum over those parcels of acres x 43,560 x (FAR after - FAR before);
- homes_permitted: homes in new-construction permits issued 2016-2019 (units parsed and staged permits merged with
  the case adapter's own functions), by permit location;
- homes_permitted_2009_2019: the same, 2009-2019 (context);
- existing_homes: 2010 census block housing units, by block internal point.
Circles of neighbouring stations overlap, so one parcel or permit can count for more than one station.

Outputs
- data/processed/tod_ridership/stations.csv (git-ignored cache of the station measures)
- reference/tod_chicago_ridership_by_station_year.csv: station name, year, average weekday and weekend-day entries
- reference/tod_chicago_ridership_results.csv: every estimate with its interval
- docs/tod/CHICAGO_RIDERSHIP_RESULTS.md: section 2, the lists (stage lists); sections 3-6 are written by hand from the
  estimate stage's CSV (re-running stage lists keeps section 1 and rewrites from section 2 on)
"""
from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE, ROOT, processed_dir  # noqa: E402
from missing_middleware.tod import cases as C  # noqa: E402
from missing_middleware.tod import ridership as R  # noqa: E402

RAWC = RAW / "cta_ridership"
OUT = processed_dir("tod_ridership")
DOC = ROOT / "docs" / "tod" / "CHICAGO_RIDERSHIP_RESULTS.md"
LISTS_MARK = "<!-- lists end -->"
# Stations outside the City of Chicago that the Chicago parcel hull does not catch (Oak Park, Forest Park, Cicero,
# Rosemont), for the unplanned check only
SUBURBAN_IN_HULL = {"40020": "Harlem/Lake", "40610": "Ridgeland", "41350": "Oak Park (Green)", "40180": "Oak Park (Blue)",
                    "40980": "Harlem (Forest Park branch)", "40390": "Forest Park", "40420": "Cicero (Pink)",
                    "40580": "54th/Cermak", "40820": "Rosemont"}


def load_daily() -> pd.DataFrame:
    return R.clean_daily(pd.read_csv(RAWC / "l_station_entries_daily_2009_2019.csv", dtype={"station_id": str}))


def load_stops() -> pd.DataFrame:
    s = pd.read_csv(RAWC / "l_stops.csv", dtype=str)
    xy = s["location"].str.extract(r"\(([-\d.]+),\s*([-\d.]+)\)").astype(float)
    s["lat"], s["lon"] = xy[0], xy[1]
    return s.groupby("map_id", as_index=False).agg(lat=("lat", "mean"), lon=("lon", "mean"),
                                                   station=("station_descriptive_name", "first")).rename(
        columns={"map_id": "station_id"})


@contextmanager
def capture():
    rec = []
    ou = C.uniform_areas

    def u(parcels, *a, **k):
        r = ou(parcels, *a, **k)
        rec.append(parcels)
        return r
    C.uniform_areas = u
    try:
        yield rec
    finally:
        C.uniform_areas = ou


def build_stations() -> pd.DataFrame:
    import geopandas as gpd
    from missing_middleware.tod import case_chicago as K
    with capture() as rec:
        K.build()
    parcels = rec[0]
    stops = load_stops()
    st = gpd.GeoDataFrame(stops, geometry=gpd.points_from_xy(stops["lon"], stops["lat"]), crs=4326).to_crs(K.CRS_M)
    circ = gpd.GeoDataFrame(st[["station_id"]], geometry=st.geometry.buffer(C.HALF_MILE_M), crs=K.CRS_M)

    tr = parcels[(parcels["area"] == C.TREAT) & parcels["eligible"].astype(bool)].copy()
    tr["added_sqft"] = tr["acres"] * C.SQM_PER_ACRE / 0.09290304 * (tr["far_after"] - tr["far_before"])
    tp = gpd.GeoDataFrame(tr[["acres", "added_sqft"]], geometry=tr.geometry.representative_point(), crs=K.CRS_M)
    j = gpd.sjoin(tp, circ, predicate="within")
    a = j.groupby("station_id").agg(treated_acres=("acres", "sum"), added_floor_area_sqft=("added_sqft", "sum"))

    p = pd.read_csv(K.DIR / "permits_new_construction.csv", dtype=str).drop_duplicates("permit_")
    p["units"] = p["work_description"].map(K.parse_units)
    p["year"] = pd.to_numeric(p["issue_date"].str[:4], errors="coerce")
    p["lat"] = pd.to_numeric(p["latitude"], errors="coerce")
    p["lon"] = pd.to_numeric(p["longitude"], errors="coerce")
    p = p[(p["units"] > 0) & p["year"].between(2009, 2019)].dropna(subset=["lat", "lon"])
    pg = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p["lon"], p["lat"]), crs=4326).to_crs(K.CRS_M)
    pg["x"], pg["y"] = pg.geometry.x, pg.geometry.y
    pg = K.dedupe_staged(pg)
    jp = gpd.sjoin(pg[["units", "year", "geometry"]], circ, predicate="within")
    hp = jp[jp["year"].between(2016, 2019)].groupby("station_id")["units"].sum().rename("homes_permitted")
    hp_all = jp.groupby("station_id")["units"].sum().rename("homes_permitted_2009_2019")

    bz = RAW / "tod_cases" / "census_2010_blocks" / "tabblock2010_17_pophu.zip"
    bbox = tuple(circ.to_crs(4269).total_bounds)
    b = gpd.read_file(bz, bbox=bbox).to_crs(K.CRS_M)
    bp = gpd.GeoDataFrame({"homes": b["HOUSING10"]}, geometry=b.geometry.representative_point(), crs=K.CRS_M)
    jb = gpd.sjoin(bp, circ, predicate="within")
    eh = jb.groupby("station_id")["homes"].sum().rename("existing_homes")

    # in Chicago: the station lies inside the convex hull of the Chicago parcels (for an unplanned check only)
    hull = parcels.union_all().convex_hull
    st["in_chicago_hull"] = st.geometry.within(hull)
    out = stops.merge(st[["station_id", "in_chicago_hull"]], on="station_id")
    for s in (a, hp, hp_all, eh):
        out = out.merge(s, left_on="station_id", right_index=True, how="left")
    for c in ("treated_acres", "added_floor_area_sqft", "homes_permitted", "homes_permitted_2009_2019"):
        out[c] = out[c].fillna(0.0)
    out.to_csv(OUT / "stations.csv", index=False)
    print(f"stations: {len(out)}; with >= 5 treated acres: {(out['treated_acres'] >= 5).sum()}")
    return out


def load_stations() -> pd.DataFrame:
    return pd.read_csv(OUT / "stations.csv", dtype={"station_id": str})


def fmt(x, nd=0):
    return f"{x:,.{nd}f}"


def lists_stage() -> None:
    daily = load_daily()
    st = load_stations()
    drops = R.drop_list(daily)
    ids = set(daily["station_id"])
    kept = sorted(ids - set(drops["station_id"]))
    names = daily.groupby("station_id")["stationname"].last()
    k = st[st["station_id"].isin(kept)].copy()
    missing_loc = sorted(set(kept) - set(k["station_id"]))
    if missing_loc:
        raise SystemExit(f"kept stations without a location: {missing_loc}")
    k["name"] = k["station_id"].map(names)
    k = k.sort_values("name")
    t, c = k[k["treated_acres"] >= R.TREATED_MIN_ACRES], k[k["treated_acres"] < R.TREATED_MIN_ACRES]
    (OUT / "groups.json").write_text(json.dumps({"kept": kept, "treated": list(t["station_id"]),
                                                 "comparison": list(c["station_id"])}, indent=1))
    L = ["## 2. Dropped stations and the two groups (written before any comparison)", "",
         f"Written by `scripts/run_chicago_ridership.py --stage lists` on 2026-10-27, before `--stage estimate` was "
         f"run. Up to this point only data availability (which days each station had entries) and the station measures "
         f"(upzoned acres, permits, homes) had been tabulated; no station's ridership change had been computed.", "",
         f"The ridership file has {len(ids)} station ids for 2009–2019. {len(drops)} are dropped, {len(kept)} are kept: "
         f"**{len(t)} treated** and **{len(c)} comparison** stations.", "",
         f"How \"closed\" was read (fixed before any comparison): a station with no entries on at least "
         f"{R.CLOSURE_DAYS} days in a row in 2009–2019, or with no entries in some year. How \"rebuilt\" was read: a full "
         "reconstruction or new station house recorded by the CTA (list in section 6). The Loop: every station inside "
         "the Loop, elevated and subway.", "",
         f"### Dropped ({len(drops)} stations)", "", "| Station | Id | Reason |", "|---|---|---|"]
    for r in drops.sort_values("stationname").itertuples():
        L.append(f"| {r.stationname} | {r.station_id} | {r.reason} |")
    L += ["", f"### Treated ({len(t)} stations: at least 5 eligible acres upzoned within ½ mile)", "",
          "| Station | Treated eligible acres | Added floor area (sq ft) | Homes permitted 2016–2019 | Existing homes 2010 |",
          "|---|---|---|---|---|"]
    for r in t.itertuples():
        L.append(f"| {r.name} | {fmt(r.treated_acres, 1)} | {fmt(r.added_floor_area_sqft)} | {fmt(r.homes_permitted)} | {fmt(r.existing_homes)} |")
    L += ["", f"### Comparison ({len(c)} stations)", "",
          "| Station | Treated eligible acres | Homes permitted 2016–2019 | Existing homes 2010 |", "|---|---|---|---|"]
    for r in c.itertuples():
        eh = "" if pd.isna(r.existing_homes) else fmt(r.existing_homes)
        L.append(f"| {r.name} | {fmt(r.treated_acres, 1)} | {fmt(r.homes_permitted)} | {eh} |")
    L += ["", LISTS_MARK, ""]
    text = DOC.read_text() if DOC.exists() else ""
    head = text.split("## 2. Dropped stations")[0] if text else ""
    DOC.write_text(head + "\n".join(L))
    print(f"lists written: dropped {len(drops)}, treated {len(t)}, comparison {len(c)}")


def estimate_stage() -> None:
    daily = load_daily()
    st = load_stations()
    g = json.loads((OUT / "groups.json").read_text())
    keep = set(g["kept"])
    stations = st[["station_id", "treated_acres", "homes_permitted", "existing_homes"]]
    specs = {}
    specs["main"] = R.estimate(daily, stations, keep)
    specs["weekend"] = R.estimate(daily, stations, keep, daytypes=R.WEEKEND)
    pre = R.station_year(daily[daily["station_id"].isin(keep)])
    pre = pre[pre["year"].isin(R.BEFORE)].groupby("station_id")["entries"].mean().sort_values(ascending=False)
    busiest = set(pre.index[:5])
    specs["no_busiest_5"] = R.estimate(daily, stations, keep, exclude=busiest)
    specs["change_2013"] = R.estimate(daily, stations, keep, before=list(range(2009, 2013)), after=list(range(2014, 2020)))
    # unplanned checks (not in the plan; reported separately)
    outside = set(st.loc[~st["in_chicago_hull"].astype(bool), "station_id"]) | set(SUBURBAN_IN_HULL)
    specs["x_chicago_only"] = R.estimate(daily, stations, keep, exclude=outside)
    # 2013: Red Line South riders were sent to Green Line South stations (several of them treated) during the closure
    specs["x_no_2013"] = R.estimate(daily, stations, keep, before=[2009, 2010, 2011, 2012, 2014])
    rows = []
    label = {"main": "Main: weekday entries, before 2009-2014, after 2016-2019",
             "weekend": "Sensitivity: Saturday plus Sunday/holiday entries",
             "no_busiest_5": "Sensitivity: leaving out the 5 busiest stations",
             "change_2013": "Sensitivity: 2013 as the change year (before 2009-2012, after 2014-2019)",
             "x_chicago_only": "Unplanned check: stations outside Chicago left out",
             "x_no_2013": "Unplanned check: 2013 left out of the before years (Red Line South diversion)"}
    for k, r in specs.items():
        base = {"spec": k, "description": label[k], "n_treated": r["n_treated"], "n_comparison": r["n_comparison"]}
        rows.append({**base, "measure": "did_log", "unit": "difference in mean log average weekday (or weekend-day) entries",
                     "estimate": r["did_log"], "low90": r["did_log_ci"][0], "high90": r["did_log_ci"][1]})
        rows.append({**base, "measure": "did_percent", "unit": "percent (exp(did_log)-1)",
                     "estimate": R.pct(r["did_log"]), "low90": R.pct(r["did_log_ci"][0]), "high90": R.pct(r["did_log_ci"][1])})
        rows.append({**base, "measure": "did_entries", "unit": "entries per day per station",
                     "estimate": r["did_entries"], "low90": r["did_entries_ci"][0], "high90": r["did_entries_ci"][1]})
        rows.append({**base, "measure": "dose_acres_per_10", "unit": "percent change in entries per 10 treated eligible acres",
                     "estimate": R.pct(10 * r["dose_acres"]), "low90": R.pct(10 * r["dose_acres_ci"][0]),
                     "high90": R.pct(10 * r["dose_acres_ci"][1])})
        rows.append({**base, "measure": "dose_permitted_per_10", "unit": "percent change in entries per 10 homes permitted 2016-2019 per 1,000 existing homes",
                     "estimate": R.pct(10 * r["dose_permitted"]), "low90": R.pct(10 * r["dose_permitted_ci"][0]),
                     "high90": R.pct(10 * r["dose_permitted_ci"][1])})
        for m in ("treated_entries_before", "treated_entries_after", "comparison_entries_before", "comparison_entries_after"):
            rows.append({**base, "measure": m, "unit": "mean average entries per day per station",
                         "estimate": r[m], "low90": np.nan, "high90": np.nan})
        for m in ("treated_d_log", "comparison_d_log"):
            rows.append({**base, "measure": m.replace("d_log", "change_percent"), "unit": "percent (exp(mean change in log)-1)",
                         "estimate": R.pct(r[m]), "low90": np.nan, "high90": np.nan})
    res = pd.DataFrame(rows)
    res["estimate"] = res["estimate"].round(4)
    res[["low90", "high90"]] = res[["low90", "high90"]].round(4)
    res.to_csv(REFERENCE / "tod_chicago_ridership_results.csv", index=False)
    specs["main"]["changes"].to_csv(OUT / "station_changes_main.csv", index=False)

    names = daily.groupby("station_id")["stationname"].last()
    wd = R.station_year(daily, R.WEEKDAY).rename(columns={"entries": "avg_weekday_entries", "days": "weekdays"})
    we = R.station_year(daily, R.WEEKEND).rename(columns={"entries": "avg_weekend_day_entries", "days": "weekend_days"})
    by = wd.merge(we, on=["station_id", "year"], how="outer")
    by["station_name"] = by["station_id"].map(names)
    by["group"] = np.where(by["station_id"].isin(g["treated"]), "treated",
                           np.where(by["station_id"].isin(g["comparison"]), "comparison", "dropped"))
    by = by[["station_id", "station_name", "year", "group", "avg_weekday_entries", "weekdays",
             "avg_weekend_day_entries", "weekend_days"]].sort_values(["station_name", "station_id", "year"])
    by[["avg_weekday_entries", "avg_weekend_day_entries"]] = by[["avg_weekday_entries", "avg_weekend_day_entries"]].round(1)
    by.to_csv(REFERENCE / "tod_chicago_ridership_by_station_year.csv", index=False)
    print(res[res["measure"].isin(["did_percent", "did_entries", "dose_acres_per_10", "dose_permitted_per_10"])].to_string())
    print("busiest 5:", [names[s] for s in pre.index[:5]])
    print("outside Chicago:", sorted(names[s] for s in outside if s in keep))
    # event years: mean log by group by year relative to 2014 (for the results text)
    sy = R.station_year(daily[daily["station_id"].isin(keep)])
    sy["log"] = np.log(sy["entries"])
    sy["grp"] = np.where(sy["station_id"].isin(g["treated"]), "t", "c")
    ev = sy.pivot_table(index="year", columns="grp", values="log", aggfunc="mean")
    ev["gap_pct_vs_2014"] = [(R.pct((ev.loc[y, "t"] - ev.loc[y, "c"]) - (ev.loc[2014, "t"] - ev.loc[2014, "c"]))) for y in ev.index]
    ev.round(4).to_csv(OUT / "event_years.csv")
    print(ev.round(3).to_string())


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=["stations", "lists", "estimate"], required=True)
    a = ap.parse_args(argv)
    {"stations": build_stations, "lists": lists_stage, "estimate": estimate_stage}[a.stage]()


if __name__ == "__main__":
    main()

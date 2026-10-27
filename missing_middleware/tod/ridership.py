"""Chicago "L" ridership after transit-area upzoning (plan: docs/tod/CHICAGO_RIDERSHIP_PREREG.md).

Pure functions on tables; geometry and file handling live in scripts/run_chicago_ridership.py.

Inputs
- daily: station_id, stationname, date, daytype (W weekday, A Saturday, U Sunday or holiday), rides (entries).
- stations: station_id, treated_acres (eligible acres of upzoned land within 1/2 mile), homes_permitted
  (homes in new-construction permits 2016-2019 within 1/2 mile), existing_homes (2010 census, within 1/2 mile).

Rules fixed by the plan
- Years 2009-2019. Before 2009-2014, after 2016-2019, change year 2015 (shown, not used).
- Treated: at least 5 treated eligible acres within 1/2 mile. Comparison: every other kept station.
- Dropped: stations opened, closed or rebuilt in the window; Red Line South stations (closed May-October 2013);
  Loop stations. Operational meaning of "closed" (chosen before any comparison was computed): a run of at least
  CLOSURE_DAYS consecutive days with no entries, or missing years.
- Outcome: average weekday entries per station per calendar year; main measure its natural log.
- Main: difference in differences of mean log entries (treated minus comparison, after minus before).
- Dose: each station's change in log entries regressed on its treated acres, and separately on homes permitted
  2016-2019 per 1,000 existing homes.
- 90% intervals from resampling stations: 2,000 draws, seed 20261027.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FIRST_YEAR, LAST_YEAR = 2009, 2019
BEFORE = list(range(2009, 2015))
AFTER = list(range(2016, 2020))
CHANGE_YEAR = 2015
TREATED_MIN_ACRES = 5.0
DRAWS, SEED = 2000, 20261027
CLOSURE_DAYS = 7
WEEKDAY, WEEKEND = ("W",), ("A", "U")

# Red Line South (Dan Ryan branch), closed 20 May to 19 October 2013 for track reconstruction
RED_SOUTH = {"41000": "Cermak-Chinatown", "40190": "Sox-35th", "41230": "47th (Red)", "41170": "Garfield (Red)",
             "40910": "63rd (Red)", "40990": "69th", "40240": "79th", "41430": "87th", "40450": "95th/Dan Ryan"}
# Stations inside the Loop (bounded by Lake, Wabash, Van Buren/Congress and Wells): the elevated Loop stations and the
# State and Dearborn subway stations under it. Several are joined to other lines by free in-system transfers.
LOOP = {"40380": "Clark/Lake", "40260": "State/Lake", "40200": "Randolph/Wabash", "40640": "Madison/Wabash",
        "41700": "Washington/Wabash", "40680": "Adams/Wabash", "40850": "Harold Washington Library-State/Van Buren",
        "40160": "LaSalle/Van Buren", "40040": "Quincy/Wells", "40730": "Washington/Wells", "41660": "Lake (Red)",
        "41090": "Monroe (Red)", "40560": "Jackson (Red)", "40500": "Washington/State (Red)",
        "40370": "Washington (Blue)", "40790": "Monroe (Blue)", "40070": "Jackson (Blue)", "41340": "LaSalle (Blue)"}
# Opened or rebuilt in the window without a closure visible in the entries (sources in CHICAGO_RIDERSHIP_RESULTS.md)
OPENED_OR_REBUILT = {
    "41510": "Morgan: opened May 2012",
    "41680": "Oakton-Skokie: opened April 2012",
    "41690": "Cermak-McCormick Place: opened February 2015",
    "41700": "Washington/Wabash: opened August 2017",
    "40540": "Wilson: rebuilt 2014-2018 (CTA Wilson Station Reconstruction, completed February 2018)",
    "40630": "Clark/Division: station rebuilt with new entrances (CTA rehabilitation, 2013-2015)",
    "40330": "Grand (Red): station rebuilt (CTA renovation completed 2012)",
}


def clean_daily(daily: pd.DataFrame) -> pd.DataFrame:
    """One row per station and date. The portal file repeats some 2011 station-days with slightly different counts;
    the repeats are averaged."""
    d = daily.copy()
    d["station_id"] = d["station_id"].astype(str)
    d["date"] = pd.to_datetime(d["date"].astype(str).str[:10])
    d["rides"] = pd.to_numeric(d["rides"], errors="coerce")
    d = d[d["date"].dt.year.between(FIRST_YEAR, LAST_YEAR)]
    g = d.groupby(["station_id", "date"], as_index=False).agg(
        rides=("rides", "mean"), daytype=("daytype", "first"), stationname=("stationname", "last"))
    return g


def longest_closure(daily: pd.DataFrame) -> pd.DataFrame:
    """Per station: longest run of consecutive days with no entries (missing days count as none), its dates, and
    the number of calendar years with any entries."""
    full = pd.date_range(f"{FIRST_YEAR}-01-01", f"{LAST_YEAR}-12-31")
    rows = []
    for sid, g in daily.groupby("station_id"):
        s = g.set_index("date")["rides"].reindex(full).fillna(0)
        z = s <= 0
        grp = (z != z.shift()).cumsum()
        runs = grp[z].value_counts()
        if len(runs):
            k = runs.idxmax()
            days = s.index[grp == k]
            rows.append({"station_id": sid, "closure_days": int(runs.max()), "closure_from": days.min().date(),
                         "closure_to": days.max().date()})
        else:
            rows.append({"station_id": sid, "closure_days": 0, "closure_from": None, "closure_to": None})
        rows[-1]["years_with_entries"] = int(g.loc[g["rides"] > 0, "date"].dt.year.nunique())
        rows[-1]["stationname"] = g["stationname"].iloc[-1]
    return pd.DataFrame(rows)


def drop_list(daily: pd.DataFrame) -> pd.DataFrame:
    """Stations dropped from both groups, with the reason (first matching reason in plan order)."""
    c = longest_closure(daily)
    out = []
    for r in c.itertuples():
        reason = None
        if r.station_id in OPENED_OR_REBUILT:
            reason = "opened or rebuilt in the window: " + OPENED_OR_REBUILT[r.station_id]
        elif r.years_with_entries < LAST_YEAR - FIRST_YEAR + 1:
            reason = f"entries in only {r.years_with_entries} of {LAST_YEAR - FIRST_YEAR + 1} years (opened or closed)"
        elif r.station_id in RED_SOUTH:
            reason = "Red Line South, closed May-October 2013"
        elif r.closure_days >= CLOSURE_DAYS:
            reason = f"closed {r.closure_days} days in a row, {r.closure_from} to {r.closure_to}"
        if r.station_id in LOOP:
            reason = "Loop station (entries mix transfers)" + (f"; also {reason}" if reason else "")
        if reason:
            out.append({"station_id": r.station_id, "stationname": r.stationname, "reason": reason})
    return pd.DataFrame(out, columns=["station_id", "stationname", "reason"])


def station_year(daily: pd.DataFrame, daytypes: tuple = WEEKDAY) -> pd.DataFrame:
    """Average entries per day of the given day types, by station and calendar year (days with entries only)."""
    d = daily[daily["daytype"].isin(daytypes) & (daily["rides"] > 0)].copy()
    d["year"] = d["date"].dt.year
    return d.groupby(["station_id", "year"], as_index=False).agg(entries=("rides", "mean"), days=("rides", "size"))


def station_changes(sy: pd.DataFrame, before: list[int], after: list[int]) -> pd.DataFrame:
    """Per station: mean log entries and mean entries before and after, and their changes."""
    s = sy.copy()
    s["log"] = np.log(s["entries"])
    b = s[s["year"].isin(before)].groupby("station_id").agg(log_before=("log", "mean"), entries_before=("entries", "mean"),
                                                             n_before=("year", "size"))
    a = s[s["year"].isin(after)].groupby("station_id").agg(log_after=("log", "mean"), entries_after=("entries", "mean"),
                                                            n_after=("year", "size"))
    c = b.join(a, how="inner")
    c = c[(c["n_before"] == len(before)) & (c["n_after"] == len(after))]
    c["d_log"] = c["log_after"] - c["log_before"]
    c["d_entries"] = c["entries_after"] - c["entries_before"]
    return c.reset_index()


def did(ch: pd.DataFrame, treated: pd.Series) -> dict:
    """Difference in differences from per-station changes. treated: boolean Series indexed like ch."""
    t, c = ch[treated.values], ch[~treated.values]
    return {"did_log": float(t["d_log"].mean() - c["d_log"].mean()),
            "did_entries": float(t["d_entries"].mean() - c["d_entries"].mean()),
            "n_treated": int(len(t)), "n_comparison": int(len(c))}


def slope(x: np.ndarray, y: np.ndarray) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    xc = x - x.mean()
    den = float((xc ** 2).sum())
    return float((xc * (y - y.mean())).sum() / den) if den > 0 else float("nan")


def bootstrap(ch: pd.DataFrame, treated: pd.Series, dose_cols: list[str], draws: int = DRAWS, seed: int = SEED,
              level: float = 0.90) -> dict:
    """90% intervals from resampling stations with replacement: treated and comparison stations are drawn
    separately (group sizes kept) for the difference in differences; all stations together for the dose slopes."""
    rng = np.random.default_rng(seed)
    tr = np.flatnonzero(treated.values)
    co = np.flatnonzero(~treated.values)
    dl, de = ch["d_log"].to_numpy(), ch["d_entries"].to_numpy()
    n = len(ch)
    out = {"did_log": [], "did_entries": []}
    out.update({c: [] for c in dose_cols})
    X = {c: ch[c].to_numpy(float) for c in dose_cols}
    for _ in range(draws):
        ti, ci = rng.choice(tr, len(tr)), rng.choice(co, len(co))
        out["did_log"].append(dl[ti].mean() - dl[ci].mean())
        out["did_entries"].append(de[ti].mean() - de[ci].mean())
        ai = rng.integers(0, n, n)
        for c in dose_cols:
            out[c].append(slope(X[c][ai], dl[ai]))
    lo, hi = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    return {k: (float(np.nanpercentile(v, lo)), float(np.nanpercentile(v, hi))) for k, v in out.items()}


def pct(x: float) -> float:
    """Log difference as a percentage change."""
    return float(100 * (np.exp(x) - 1))


def estimate(daily: pd.DataFrame, stations: pd.DataFrame, keep: set[str], daytypes: tuple = WEEKDAY,
             before: list[int] = BEFORE, after: list[int] = AFTER, exclude: set[str] | None = None,
             draws: int = DRAWS, seed: int = SEED) -> dict:
    """Main estimate, dose slopes and intervals for one specification."""
    sy = station_year(daily[daily["station_id"].isin(keep - (exclude or set()))], daytypes)
    ch = station_changes(sy, before, after).merge(stations, on="station_id", how="left")
    ch["treated_acres"] = ch["treated_acres"].fillna(0.0)
    ch["permitted_per_1000"] = 1000 * ch["homes_permitted"] / ch["existing_homes"].where(ch["existing_homes"] > 0)
    ch = ch.dropna(subset=["d_log"]).reset_index(drop=True)
    treated = ch["treated_acres"] >= TREATED_MIN_ACRES
    r = did(ch, treated)
    dose_ok = ch.dropna(subset=["permitted_per_1000"]).reset_index(drop=True)
    r["dose_acres"] = slope(ch["treated_acres"], ch["d_log"])
    r["dose_permitted"] = slope(dose_ok["permitted_per_1000"], dose_ok["d_log"])
    ci = bootstrap(ch, treated, ["treated_acres"], draws, seed)
    ci_p = bootstrap(dose_ok, dose_ok["treated_acres"] >= TREATED_MIN_ACRES, ["permitted_per_1000"], draws, seed)
    r["did_log_ci"] = ci["did_log"]
    r["did_entries_ci"] = ci["did_entries"]
    r["dose_acres_ci"] = ci["treated_acres"]
    r["dose_permitted_ci"] = ci_p["permitted_per_1000"]
    r["n_dose_permitted"] = int(len(dose_ok))
    t, c = ch[treated], ch[~treated]
    r.update({"treated_entries_before": float(t["entries_before"].mean()), "treated_entries_after": float(t["entries_after"].mean()),
              "comparison_entries_before": float(c["entries_before"].mean()),
              "comparison_entries_after": float(c["entries_after"].mean()),
              "treated_d_log": float(t["d_log"].mean()), "comparison_d_log": float(c["d_log"].mean())})
    r["changes"] = ch.assign(treated=treated.values)
    return r

"""Middle housing power check: smallest effect each proposed test could detect.

Research only (docs/middle/POWER_CHECK.md). No-peeking rules: docs/middle/MEASUREMENT_CHECK_LOG.md.
- Reads Census place permits for 2012-2018 ONLY (the year filter is applied as each file is read).
  Every candidate reform binds after 2018 except Houston (1998) and Walla Walla (2019-01-02), and
  candidate cities are never used as fake-treated places or stand-ins.
- Fake-treated states never have a candidate state law, and no candidate city is ever a stand-in or fake-treated.

Unit for every rate: homes permitted per 1,000 single-family homes (ACS 2020-2024 B25024 rows 2 + 3,
detached plus attached) per year.

Measures:
  all   homes in buildings of every size
  1to4  homes in 1-, 2- and 3-4-unit buildings (leaves out every 5+ building)
  2to4  homes in 2- and 3-4-unit buildings
Placebo windows (no reform anywhere in them): before 2012-2014, after 2016-2018.
Power rule: 80% chance of detection with a two-sided 90% test, so the multiplier is 1.645 + 0.842.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.foundation import parsers  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT = ROOT / "reference"
LAST_YEAR = 2018
BEFORE, AFTER = (2012, 2013, 2014), (2016, 2017, 2018)
K = 1.645 + 0.8416
SEED = 20261108
# States with a candidate state law (never fake-treated, never in comparison pools)
TESTED_STATES = {"06", "41", "53", "23", "50", "30", "04"}
# Comparison screen (design v5; docs/middle/measurement/COMPARISON_STATE_REFORMS.md). States where a statewide
# middle-housing, TOD/station-area, by-right multifamily or multifamily parking law first binds 2015-2025.
# They are never comparison places and never fake law states.
SCREENED_STATES = {"25": "MA", "08": "CO", "44": "RI", "09": "CT", "49": "UT", "33": "NH", "48": "TX", "12": "FL",
                   "24": "MD"}
NON_FAKE_STATES = TESTED_STATES | set(SCREENED_STATES)
# States whose middle-housing law binds by 2025 (never Test 3 stand-ins; audit fix 3)
LAW_STATES_2025 = {"06", "41", "53", "23", "50", "30"}
# Candidate cities: (state FIPS, BPS name). Never stand-ins, never fake-treated.
# Places with their own local reform of the same kinds first binding 2015-2025 (never comparisons or stand-ins)
SCREENED_PLACES = {("02", "Municipality of Anchorage"), ("16", "Boise City"), ("36", "Bronx"), ("36", "Brooklyn"), ("36", "Manhattan"), ("36", "Queens"), ("36", "Staten Island"), ("42", "Philadelphia"),
                   ("42", "Pittsburgh"), ("34", "Trenton"), ("36", "Buffalo"), ("32", "Reno"), ("27", "St. Paul"),
                   ("27", "Saint Paul"), ("17", "Chicago"), ("51", "Alexandria")}
CANDIDATE_CITIES = {("27", "Minneapolis"), ("48", "Austin"), ("48", "Houston"), ("37", "Durham"), ("37", "Raleigh"),
                    ("37", "Mecklenburg County"), ("53", "Walla Walla"), ("53", "Spokane"), ("06", "Sacramento"),
                    ("51", "Arlington County"), ("41", "Portland")}
# Cities for Test 3: state FIPS, BPS name (population and homes only are read for these; never their permits)
TEST3_CITIES = [("27", "Minneapolis"), ("37", "Raleigh"), ("53", "Spokane"), ("53", "Walla Walla"), ("41", "Portland")]
MEASURES = {"all": ["1unit", "2units", "3_4units", "5plus"], "1to4": ["1unit", "2units", "3_4units"],
            "2to4": ["2units", "3_4units"]}


def load_bps(reported_only: bool) -> pd.DataFrame:
    frames = []
    for f in sorted((RAW / "census_bps_place_us").glob("*a.txt")):
        year = int(f.name[2:6])
        if year > LAST_YEAR:  # no-peeking: later years are never read
            continue
        d = parsers.read_bps(f, "place", state_fips=None)
        d["year"] = year
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    assert d["year"].max() <= LAST_YEAR
    for c in ("state_fips", "bps_id", "county_fips", "fips_place", "fips_mcd", "name", "region", "division"):
        d[c] = d[c].astype(str).str.strip()
    d = d[(d["fips_place"] != "99990") & ~d["name"].str.contains("County|Balance", case=True) |
          d["name"].isin(["Mecklenburg County", "Arlington County"])]
    d["key"] = d["state_fips"] + "|" + d["bps_id"]
    d["acs_geoid"] = np.where(d["fips_place"].str.strip("0") != "",
                              "160|" + d["state_fips"] + d["fips_place"].str.zfill(5),
                              "060|" + d["state_fips"] + d["county_fips"].str.zfill(3) + d["fips_mcd"].str.zfill(5))
    suffix = "_units_rep" if reported_only else "_units"
    for m, groups in MEASURES.items():
        d[m] = d[[g + suffix for g in groups]].sum(axis=1)
    return d


def sf_homes() -> pd.Series:
    a = parsers.read_acs_sf(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25024.dat", state_fips="",
                            sumlevels=("060", "160"))
    a["acs_geoid"] = a["sumlevel"] + "|" + a["geoid"]
    return (a["B25024_E002"] + a["B25024_E003"]).groupby(a["acs_geoid"]).first()


def place_table(d: pd.DataFrame, homes: pd.Series, reported_only: bool) -> pd.DataFrame:
    yrs = BEFORE + AFTER
    w = d[d["year"].isin(yrs)]
    if reported_only:
        full = w.groupby("key")["months_reported"].apply(lambda s: (s == 12).sum())
        w = w[w["key"].isin(full[full == len(yrs)].index)]
    n = w.groupby("key")["year"].nunique()
    w = w[w["key"].isin(n[n == len(yrs)].index)]
    info = w.sort_values("year").groupby("key").last()[["state_fips", "region", "division", "name", "pop", "acs_geoid"]]
    info["homes"] = info["acs_geoid"].map(homes)
    for m in MEASURES:
        info[m + "_b"] = w[w["year"].isin(BEFORE)].groupby("key")[m].sum()
        info[m + "_a"] = w[w["year"].isin(AFTER)].groupby("key")[m].sum()
    info = info[(info["homes"] >= 100) & info["pop"].notna() & (info["pop"] > 0)]
    cand = {s + "|" + n for s, n in CANDIDATE_CITIES}
    nm = info["name"].str.replace(r" (city|town|village|borough|township|municipality)$", "", regex=True)
    scr = {st + "|" + n for st, n in SCREENED_PLACES}
    info["candidate"] = (info["state_fips"] + "|" + info["name"]).isin(cand) | (info["state_fips"] + "|" + nm).isin(scr) \
        | info["state_fips"].isin(SCREENED_STATES)
    return info


def rate(df: pd.DataFrame, m: str, part: str) -> float:
    return 1000 * df[f"{m}_{part}"].sum() / (df["homes"].sum() * 3)


def test1_state_stats(t: pd.DataFrame, m: str) -> pd.DataFrame:
    """Each untested state in turn as a fake law state (design v3, audit fix 1).
    Comparison pool: places in the same Census region, other untested states. Each fake-state place is
    matched to pool places at 1/2-2x its population; its comparison rate is that set's pooled rate, and the
    comparison side is the fake state's places weighted by their homes. Statistic: log rate ratio,
    after over before, fake state minus comparison."""
    pool = t[~t["state_fips"].isin(NON_FAKE_STATES) & ~t["candidate"]].copy()
    pops = pool["pop"].to_numpy()
    rows = []
    for st, tr in pool.groupby("state_fips"):
        reg = tr["region"].iloc[0]
        cmp_ = pool[(pool["region"] == reg) & (pool["state_fips"] != st)]
        if cmp_.empty or rate(tr, m, "b") == 0:
            continue
        cp, ch_ = cmp_["pop"].to_numpy(), cmp_["homes"].to_numpy()
        cb, ca = cmp_[m + "_b"].to_numpy(), cmp_[m + "_a"].to_numpy()
        wsum = num_a = num_b = 0.0
        for pop_i, h_i in zip(tr["pop"].to_numpy(), tr["homes"].to_numpy()):
            k = (cp >= pop_i / 2) & (cp <= pop_i * 2)
            if not k.any() or ch_[k].sum() == 0:
                continue
            num_b += h_i * cb[k].sum() / ch_[k].sum()
            num_a += h_i * ca[k].sum() / ch_[k].sum()
            wsum += h_i
        if wsum == 0 or num_b == 0 or num_a == 0 or rate(tr, m, "a") == 0:
            continue
        stat = np.log(rate(tr, m, "a") / rate(tr, m, "b")) - np.log(num_a / num_b)
        rows.append(dict(state=st, region=reg, places=len(tr), homes=tr["homes"].sum(),
                         rate_before=rate(tr, m, "b"), stat=stat))
    return pd.DataFrame(rows)


def test3_city(t: pd.DataFrame, all_d: pd.DataFrame, homes: pd.Series, st: str, name: str, m: str) -> dict:
    """Stand-ins: non-candidate places outside states whose law binds by 2025, at 1/2-2x the city's population, from its state,
    then its division, then the nation, until at least 20. Statistic: change in rate (after minus before)."""
    c = all_d[(all_d["state_fips"] == st) & (all_d["name"] == name)].sort_values("year").iloc[-1]
    pop, div = float(c["pop"]), c["division"]
    h = homes.get(c["acs_geoid"], np.nan)
    pool = t[~t["candidate"] & ~t["state_fips"].isin(LAW_STATES_2025) & t["pop"].between(pop / 2, pop * 2)]  # audit fix 3
    for scope in ("state", "division", "nation"):
        s = {"state": pool[pool["state_fips"] == st], "division": pool[pool["division"] == div],
             "nation": pool}[scope]
        if len(s) >= 20:
            break
    ch = 1000 * (s[m + "_a"] - s[m + "_b"]) / (s["homes"] * 3)
    q50, q95, sd = ch.quantile(0.5), ch.quantile(0.95), ch.std()
    mde = (q95 - q50) + 0.8416 * sd
    return dict(city=name, measure=m, population=pop, sf_homes=h, scope=scope, standins=len(s),
                standin_sd=sd, mde_per_1000=mde, mde_homes_per_year=mde * h / 1000)


def test2_oregon(t: pd.DataFrame, m: str) -> list[dict]:
    """Oregon cities by the law's own count (PSU certified July 2020, reference/oregon_psu_2020_city_population.csv),
    non-Metro, 5,000-24,999. Spread from cities outside 9,000-10,999 only. Statistic: change in rate."""
    psu = pd.read_csv(OUT / "oregon_psu_2020_city_population.csv").set_index("city")["psu_certified_july_2020"]
    metro = {"Wood Village", "Fairview", "Troutdale", "Milwaukie", "Gladstone", "Happy Valley", "West Linn",
             "Wilsonville", "Sherwood", "Cornelius", "Forest Grove", "Durham", "King City", "Tualatin", "Johnson City",
             "Rivergrove", "Maywood Park", "Lake Oswego", "Oregon City", "Tigard", "Beaverton", "Hillsboro",
             "Gresham", "Portland"}
    o = t[t["state_fips"] == "41"].copy()
    o["city"] = o["name"].str.replace(r" (city|town)$", "", regex=True)
    o["psu"] = o["city"].map(psu)
    o = o[o["psu"].between(5000, 24999) & ~o["city"].isin(metro)]
    o["change"] = 1000 * (o[m + "_a"] - o[m + "_b"]) / (o["homes"] * 3)
    sd = o.loc[~o["psu"].between(9000, 10999), "change"].std()
    rows = []
    for lo, hi in [(9500, 10499), (9000, 10999), (7500, 12499), (5000, 14999)]:
        b = o[o["psu"].between(lo, hi)]
        n1, n0 = int((b["psu"] > 10000).sum()), int((b["psu"] <= 10000).sum())
        mde = K * sd * np.sqrt(1 / n1 + 1 / n0) if n1 and n0 else np.nan
        rows.append(dict(measure=m, band=f"{lo}-{hi}", covered=n1, left_out=n0, spread_sd=sd,
                         mde_per_1000=mde, mde_homes_per_city_year=mde * b["homes"].mean() / 1000))
    return rows


def main() -> None:
    homes = sf_homes()
    out1, out2, out3 = [], [], []
    for reported_only in (True, False):
        d = load_bps(reported_only)
        t = place_table(d, homes, reported_only)
        label = "reported only, 12 months" if reported_only else "with Census fill-ins"
        rng = np.random.default_rng(SEED)
        for m in MEASURES:
            s = test1_state_stats(t, m)
            sd1 = s["stat"].std()
            pairs = [s["stat"].sample(2, random_state=int(rng.integers(1e9))).mean() for _ in range(5000)]
            sd2 = float(np.std(pairs, ddof=1))
            out1.append(dict(data=label, measure=m, fake_states=len(s), sd_one_state=sd1, sd_two_states=sd2,
                             mde_log_two_states=K * sd2, mde_pct_two_states=100 * (np.exp(K * sd2) - 1),
                             median_rate_before=s["rate_before"].median()))
            for r in test2_oregon(t, m):
                r["data"] = label
                out2.append(r)
            for st, nm in TEST3_CITIES:
                r = test3_city(t, d, homes, st, nm, m)
                r["data"] = label
                out3.append(r)
    o1, o3 = pd.DataFrame(out1), pd.DataFrame(out3)
    o2 = pd.DataFrame(out2)
    o2.to_csv(OUT / "middle_power_test2.csv", index=False)
    print(o2.round(2).to_string(index=False))
    o1.to_csv(OUT / "middle_power_test1.csv", index=False)
    o3.to_csv(OUT / "middle_power_test3.csv", index=False)
    pd.set_option("display.width", 200)
    print(o1.round(3).to_string(index=False))
    print(o3.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

"""Middle housing Test 2: Oregon cities just above and below the 10,000 line (locked plan,
docs/middle/TEST_PLAN_LOCKED.md, commit 8767525c). Run first by Ryan's choice at lock.

Groups: non-Metro Oregon cities by the law's own count (PSU certified July 2020,
reference/oregon_psu_2020_city_population.csv). Covered: more than 10,000. Left out: 10,000 or fewer,
minus any city the step 0 zoning check found already allowing duplexes on most single-family lots before 2021.
Bands: main 9,000-10,999; wider 5,000-14,999.
Windows: before 2016-2018; after 2022-2024 (HB 3395 extended duplexes to cities of 2,500+ from 2025-06-30).
Unit: homes permitted per 1,000 single-family homes per year. Single-family homes = ACS 2020-2024 B25024 rows 2+3,
moved to each year by the place's one-unit permits (as homes_by_year.py does): earlier years subtract one-unit
permits issued after them up to 2022; later years add one-unit permits from 2023.
Measures: M2 (homes in 2-4 unit buildings) leads; M1 (1-4) and M3 (all homes) beside it.
Statistic: covered cities' mean change (after rate minus before rate) minus left-out cities' mean change.
90% bootstrap over cities within each group, 10,000 draws, seed 20261103.
Reading: interval above 0 = a rise relative to left-out cities; below 0 = a fall; includes 0 = we do not know.
Data columns: Census filled-in (main); reported-only as sensitivity (cities reporting 12 months in every window year).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.foundation import parsers  # noqa: E402

RAW, OUT = ROOT / "data" / "raw", ROOT / "reference"
BEFORE, AFTER = (2016, 2017, 2018), (2022, 2023, 2024)
YEARS = range(2016, 2025)
SEED, DRAWS = 20261103, 10_000
METRO = {"Wood Village", "Fairview", "Troutdale", "Milwaukie", "Gladstone", "Happy Valley", "West Linn", "Wilsonville",
         "Sherwood", "Cornelius", "Forest Grove", "Durham", "King City", "Tualatin", "Johnson City", "Rivergrove",
         "Maywood Park", "Lake Oswego", "Oregon City", "Tigard", "Beaverton", "Hillsboro", "Gresham", "Portland"}
ALIAS = {"Mt. Angel": "Mount Angel"}
MEASURES = {"M2: 2-4 unit homes": ["2units", "3_4units"], "M1: 1-4 unit homes": ["1unit", "2units", "3_4units"],
            "M3: all homes": ["1unit", "2units", "3_4units", "5plus"]}
# Detection bars from the power check (9,000-10,999 band, Census fill-ins), per 1,000 SF homes per year
BARS = {"M2: 2-4 unit homes": 1.79, "M1: 1-4 unit homes": 8.38, "M3: all homes": 21.65}


def load(dropped_by_zoning: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for y in range(2016, 2025):
        d = parsers.read_bps(RAW / "census_bps_place_us" / f"we{y}a.txt", "place", state_fips="41")
        d["year"] = y
        frames.append(d)
    b = pd.concat(frames, ignore_index=True)
    b["city"] = b["name"].str.strip().str.replace(r" (city|town)$", "", regex=True)
    psu = pd.read_csv(OUT / "oregon_psu_2020_city_population.csv")
    psu["city"] = psu["city"].replace(ALIAS)
    psu = psu.set_index("city")["psu_certified_july_2020"]
    acs = parsers.read_acs_sf(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25024.dat", state_fips="41",
                              sumlevels=("160",))
    acs["fips_place"] = acs["geoid"].str[2:]
    sfh = (acs["B25024_E002"] + acs["B25024_E003"]).groupby(acs["fips_place"]).first()
    b["fips_place"] = b["fips_place"].astype(str).str.strip().str.zfill(5)
    b = b[b["city"].isin(psu.index) & ~b["city"].isin(METRO)]
    b["psu"] = b["city"].map(psu)
    b["sfh_acs"] = b["fips_place"].map(sfh)
    roster = b.groupby("city").agg(psu=("psu", "first"), years=("year", "nunique"), sfh=("sfh_acs", "first"))
    roster["dropped_zoning"] = roster.index.isin(dropped_by_zoning)
    return b, roster


def city_changes(b: pd.DataFrame, cols: list[str], reported_only: bool) -> pd.Series:
    suf = "_units_rep" if reported_only else "_units"
    one = "1unit" + suf
    out = {}
    for city, g in b.groupby("city"):
        g = g.set_index("year")
        if set(YEARS) - set(g.index) or pd.isna(g["sfh_acs"].iloc[0]):
            continue
        if reported_only and (g.loc[list(BEFORE + AFTER), "months_reported"] != 12).any():
            continue
        h22 = g["sfh_acs"].iloc[0]
        homes = {}
        for y in YEARS:
            if y <= 2022:
                homes[y] = h22 - sum(g.loc[t, one] for t in YEARS if y < t <= 2022)
            else:
                homes[y] = h22 + sum(g.loc[t, one] for t in YEARS if 2023 <= t <= y)
        p = g[[c + suf for c in cols]].sum(axis=1)
        rb = 1000 * p.loc[list(BEFORE)].sum() / sum(homes[y] for y in BEFORE)
        ra = 1000 * p.loc[list(AFTER)].sum() / sum(homes[y] for y in AFTER)
        out[city] = ra - rb
    return pd.Series(out)


def boot(cov: np.ndarray, non: np.ndarray, rng) -> tuple[float, float]:
    d = [rng.choice(cov, len(cov)).mean() - rng.choice(non, len(non)).mean() for _ in range(DRAWS)]
    return float(np.quantile(d, 0.05)), float(np.quantile(d, 0.95))


def main() -> None:
    dropped = set(sys.argv[1].split(",")) if len(sys.argv) > 1 and sys.argv[1] else set()
    b, roster = load(dropped)
    rows = []
    for data, rep in (("Census filled-in (main)", False), ("reported only (sensitivity)", True)):
        for band, (lo, hi) in {"main 9,000-10,999": (9000, 10999), "wider 5,000-14,999": (5000, 14999)}.items():
            for m, cols in MEASURES.items():
                ch = city_changes(b, cols, rep)
                r = roster.loc[roster.index.isin(ch.index)]
                r = r[r["psu"].between(lo, hi) & ~r["dropped_zoning"]]
                cov, non = ch[r.index[r["psu"] > 10000]], ch[r.index[r["psu"] <= 10000]]
                if len(cov) < 2 or len(non) < 2:
                    rows.append(dict(data=data, band=band, measure=m, covered=len(cov), left_out=len(non),
                                     note="too few cities"))
                    continue
                est = cov.mean() - non.mean()
                lo90, hi90 = boot(cov.to_numpy(), non.to_numpy(), np.random.default_rng(SEED))
                reading = ("rise relative to left-out cities" if lo90 > 0 else
                           "fall relative to left-out cities" if hi90 < 0 else "we do not know (range includes 0)")
                rows.append(dict(data=data, band=band, measure=m, covered=len(cov), left_out=len(non),
                                 covered_mean_change=cov.mean(), left_out_mean_change=non.mean(), estimate=est,
                                 ci90_low=lo90, ci90_high=hi90, reading=reading, detection_bar=BARS[m],
                                 covered_cities=", ".join(sorted(cov.index)), left_out_cities=", ".join(sorted(non.index))))
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "middle_test2_oregon_line.csv", index=False)
    roster.to_csv(OUT / "middle_test2_oregon_roster.csv")
    pd.set_option("display.width", 250)
    print(res.drop(columns=["covered_cities", "left_out_cities"], errors="ignore").round(2).to_string(index=False))


if __name__ == "__main__":
    main()

"""Middle housing Test 6: how much Census permit counts miss (locked plan, docs/middle/TEST_PLAN_LOCKED.md).

Compares townhouse-inclusive record counts (M5) with Census counts of homes in 2-4 unit buildings (M2) and in 1-4 unit
buildings (M1), before and after each reform. Report only.

Sources (licences in docs/middle/MEASUREMENT_CHECK_RESULTS.md):
- California: HCD progress reports, Table A2 (on disk). M5 = SFA + "2 to 4" homes with building permits; also
  "2 to 4" alone. Windows 2018-2021 / 2023-2025. Matched to Census places by name; bootstrap over places.
- Austin: open permits (data.austintexas.gov 3syk-w9eu, public domain), new building permits. M5 = R-103 / C-103 two-family
  + C-104 three-four family + R-101 single family filed as condominium (townhouse proxy). Windows 2020-2022 / 2025.
- Minneapolis: CCS permits (copyright waived). M5 = TFD (two-family) + 3to4 + TH (townhouse) new dwelling units.
  Windows 2017-2018 (the series starts 2016-12) / 2020-2025.
Portland is left out: no licence is stated. Census side: filled-in columns. Bootstrap for single cities is over years.
90% bootstrap, 2,000 draws, seed 20261103.
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.foundation import parsers  # noqa: E402

RAW, OUT = ROOT / "data" / "raw", ROOT / "reference"
UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
SEED, DRAWS = 20261103, 2000


def census_places(state: str) -> pd.DataFrame:
    frames = []
    for f in sorted((RAW / "census_bps_place_us").glob("*a.txt")):
        d = parsers.read_bps(f, "place", state_fips=state)
        d["year"] = int(f.name[2:6])
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["name"] = d["name"].str.strip()
    d["M2"] = d["2units_units"] + d["3_4units_units"]
    d["M1"] = d["M2"] + d["1unit_units"]
    return d


def get_json(url: str):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())


def ratio_boot(rec: np.ndarray, cen: np.ndarray, rng) -> tuple[float, float, float]:
    r = rec.sum() / cen.sum() if cen.sum() else np.nan
    n = len(rec)
    b = []
    for _ in range(DRAWS):
        i = rng.integers(0, n, n)
        if cen[i].sum() > 0:
            b.append(rec[i].sum() / cen[i].sum())
    return r, float(np.quantile(b, 0.05)), float(np.quantile(b, 0.95))


def california(rng) -> list[dict]:
    rec = {}
    with open(RAW / "hcd_apr_a2" / "tablea2.csv", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            if r["UNIT_CAT"] not in ("SFA", "2 to 4"):
                continue
            try:
                y, u = int(r["YEAR"]), float(r["NO_BUILDING_PERMITS"] or 0)
            except ValueError:
                continue
            k = (r["JURIS_NAME"].strip().upper(), y)
            rec.setdefault(k, {"SFA": 0.0, "2 to 4": 0.0})[r["UNIT_CAT"]] += u
    c = census_places("06")
    c["key"] = c["name"].str.replace(r" (city|town)$", "", regex=True).str.upper()
    out = []
    for label, yrs in (("before 2018-2021", range(2018, 2022)), ("after 2023-2025", range(2023, 2026))):
        cc = c[c["year"].isin(yrs)].groupby("key")[["M2", "M1"]].sum()
        names = [n for n in cc.index if any((n, y) in rec for y in yrs)]
        m5 = np.array([sum(rec.get((n, y), {}).get("SFA", 0) + rec.get((n, y), {}).get("2 to 4", 0) for y in yrs) for n in names])
        r24 = np.array([sum(rec.get((n, y), {}).get("2 to 4", 0) for y in yrs) for n in names])
        for num_label, num in (("M5 (SFA + 2 to 4)", m5), ("progress-report 2 to 4 only", r24)):
            for den in ("M2", "M1"):
                r, lo, hi = ratio_boot(num, cc.loc[names, den].to_numpy(), rng)
                out.append(dict(place="California (matched places)", period=label, places=len(names), record=num_label,
                                census=den, record_homes=num.sum(), census_homes=cc.loc[names, den].sum(),
                                ratio=r, ci90_low=lo, ci90_high=hi))
    return out


def austin(rng) -> list[dict]:
    q = ("https://data.austintexas.gov/resource/3syk-w9eu.json?$select=date_extract_y(issue_date) as y,permit_class,"
         "condominium,sum(housing_units) as u&$where=work_class='New' AND permittype='BP' AND issue_date between "
         "'2020-01-01' and '2025-12-31'&$group=y,permit_class,condominium&$limit=1000")
    rows = get_json(urllib.parse.quote(q, safe=":/?$=&,'()"))
    m5 = {}
    for r in rows:
        y, pcl, condo, u = int(r["y"]), r["permit_class"], r.get("condominium"), float(r.get("u") or 0)
        if pcl.endswith("103 Two Family Bldgs") or pcl.startswith("C- 104") or (pcl == "R- 101 Single Family Houses" and condo == "Yes"):
            m5[y] = m5.get(y, 0) + u
    c = census_places("48")
    c = c[c["name"] == "Austin"].set_index("year")
    return city_rows("Austin", m5, c, (range(2020, 2023), range(2025, 2026)), rng)


def minneapolis(rng) -> list[dict]:
    base = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/CCS_Permits/FeatureServer/0/query"
    m5 = {}
    for y in range(2017, 2026):
        where = (f"dwellingUnitsNew>0 AND occupancyType IN ('TFD','3to4','TH') AND issueDate >= DATE '{y}-01-01' "
                 f"AND issueDate < DATE '{y + 1}-01-01'")
        stats = '[{"statisticType":"sum","onStatisticField":"dwellingUnitsNew","outStatisticFieldName":"u"}]'
        url = base + "?" + urllib.parse.urlencode({"where": where, "outStatistics": stats, "f": "json"})
        try:
            v = get_json(url)["features"][0]["attributes"]["u"]
        except Exception:  # noqa: BLE001 - text field: fall back to fetching values
            url = base + "?" + urllib.parse.urlencode({"where": where, "outFields": "dwellingUnitsNew",
                                                       "returnGeometry": "false", "f": "json"})
            v = sum(float(f["attributes"]["dwellingUnitsNew"] or 0) for f in get_json(url)["features"])
        m5[y] = float(v or 0)
    c = census_places("27")
    c = c[c["name"] == "Minneapolis"].set_index("year")
    return city_rows("Minneapolis", m5, c, (range(2017, 2019), range(2020, 2026)), rng)


def city_rows(city: str, m5: dict, c: pd.DataFrame, windows, rng) -> list[dict]:
    out = []
    for label, yrs in zip(("before", "after"), windows):
        yrs = list(yrs)
        rec = np.array([m5.get(y, 0) for y in yrs])
        for den in ("M2", "M1"):
            cen = c.loc[yrs, den].to_numpy(dtype=float)
            r, lo, hi = ratio_boot(rec, cen, rng)
            out.append(dict(place=city, period=f"{label} {yrs[0]}-{yrs[-1]}", places=1, record="M5", census=den,
                            record_homes=rec.sum(), census_homes=cen.sum(), ratio=r, ci90_low=lo, ci90_high=hi))
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows = california(rng) + austin(rng) + minneapolis(rng)
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "middle_test6_census_gap.csv", index=False)
    pd.set_option("display.width", 220)
    print(r.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

"""Year-matched homes for the ADU comparison rows (audit 2026-10-29, item 6; AQ-064).

Why: every comparison row divides its ADU count by one-unit detached homes from ACS 2020-2024 (B25024_002), whatever
its year. Homes grew over time, so a 2012 rate read against 2022 homes is a little too low, and a 2026 rate a little
too high.

How: ACS 2020-2024 is treated as the stock in mid-2022. The stock in mid-year y is that stock plus the one-unit homes
permitted between mid-2022 and mid-y (Census Building Permits Survey, annual, 1-unit units):

    homes(y) = homes_ACS x index(y),   index(y) = 1 + (F(y) - F(2022)) / homes_ACS,
    F(y) = sum of 1-unit permits in years before y + half of year y's.

Units: index is a ratio (homes in mid-year y / homes in the ACS 2020-2024 period). It ignores demolitions and the lag
from permit to finished home (both small); 1-unit permits include attached houses (a slight overstatement of growth).
State series and their sub-state parts (Washington without Seattle, Oregon's 32 cities, Chittenden County) use the
state's index; city series use the city's own index; California's jurisdictions use California's. A year with no
permit file (2026; city years before 2012) repeats the nearest year's permits, flagged `filled`.

Pure functions; file readers take paths so tests can use fixtures.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REF_YEAR = 2022


def _num(s: str) -> float:
    s = s.strip()
    return float(s) if s else 0.0


def read_bps_state(dir_: Path) -> pd.DataFrame:
    """Annual state files stYYYYa.txt -> state_fips, year, units_1 (1-unit units permitted)."""
    out = []
    for f in sorted(Path(dir_).glob("st[0-9][0-9][0-9][0-9]a.txt")):
        year = int(f.name[2:6])
        for line in f.read_text(encoding="latin-1").splitlines():
            p = line.split(",")
            if len(p) < 7 or not p[0].strip().startswith(str(year)):
                continue
            out.append((p[1].strip().zfill(2), year, _num(p[6])))
    return pd.DataFrame(out, columns=["geo", "year", "units_1"])


def read_bps_places(dir_: Path, place_geoids) -> pd.DataFrame:
    """Annual regional place files (mw/ne/so/weYYYYa.txt) -> place geoid (state + FIPS place), year, units_1."""
    want = set(place_geoids)
    out = []
    for f in sorted(Path(dir_).glob("[mnsw][weo][0-9][0-9][0-9][0-9]a.txt")):
        year = int(f.name[2:6])
        for line in f.read_text(encoding="latin-1").splitlines():
            p = line.split(",")
            if len(p) < 19 or not p[0].strip().isdigit():
                continue
            gid = p[1].strip().zfill(2) + p[5].strip().zfill(5)
            if gid in want:
                out.append((gid, year, _num(p[18])))
    d = pd.DataFrame(out, columns=["geo", "year", "units_1"])
    return d.groupby(["geo", "year"], as_index=False)["units_1"].sum()


def stock_index(permits: pd.DataFrame, homes_acs: dict[str, float], years) -> pd.DataFrame:
    """index(y) per geography (see module doc). permits: geo, year, units_1; homes_acs: geo -> ACS homes."""
    out = []
    for geo, h in homes_acs.items():
        p = permits[permits["geo"].eq(geo)].set_index("year")["units_1"].to_dict()
        if not p:
            continue
        first, last = min(p), max(p)
        lo = min(min(years), REF_YEAR)
        hi = max(max(years), REF_YEAR)
        for t in range(lo, hi + 1):
            p.setdefault(t, p[last] if t > last else p[first])

        def F(y):
            return sum(v for t, v in p.items() if lo <= t < y) + 0.5 * p[y]

        for y in years:
            out.append(dict(geo=geo, year=int(y), index=1.0 + (F(y) - F(REF_YEAR)) / h,
                            filled=bool(y > last or y < first)))
    return pd.DataFrame(out)


def row_geo(rows: pd.DataFrame, cluster_fips: dict[str, str]) -> pd.Series:
    """The geography whose index each comparison row uses: a city row its place, every other row its state."""
    city = rows["group_id"].astype(str).str.startswith("place:")
    return rows["group_id"].astype(str).str[6:].where(city, rows["cluster"].map(cluster_fips))


def apply_homes_index(rows: pd.DataFrame, index: pd.DataFrame, cluster_fips: dict[str, str]) -> pd.DataFrame:
    """Scale each row's exposure (`years`) by index(geo, year), so exposure = ACS homes x index x years. Adds
    `homes_index`. Rows with no index keep 1.0."""
    r = rows.copy()
    key = pd.MultiIndex.from_arrays([row_geo(r, cluster_fips), r["year"].astype(int)])
    ix = index.set_index(["geo", "year"])["index"]
    r["homes_index"] = pd.Series(ix.reindex(key).to_numpy(), index=r.index).fillna(1.0)
    r["years"] = r["years"] * r["homes_index"]
    return r

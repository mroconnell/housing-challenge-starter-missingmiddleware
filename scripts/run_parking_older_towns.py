"""Permit route for older citywide repeals, 2004-2009 (docs/parking/BLOCK_CATALOG_PLAN.md, section 3).

    uv run python scripts/run_parking_older_towns.py

Census permit place files, Midwest region, 1999-2015 (1999-2008 in data/raw/parking_older_reforms, fetched with
curl from www2.census.gov/econ/bps/Place/Midwest Region/; 2009-2011 in data/raw/parking_census_check; 2012-2015 in
data/raw/census_bps_place_us). Homes and population: Census 2000 Gazetteer places.
Output: reference/parking_older_towns.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_older_reforms as orr  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

TOWNS = (("Brownville", "31", 2004), ("Ozawkie", "20", 2007), ("Westmoreland", "20", 2007), ("Philip", "46", 2009))


def main() -> None:
    files = [RAW / "parking_older_reforms" / f"mw{y}a.txt" for y in range(1999, 2009)] + \
            [RAW / "parking_census_check" / f"mw{y}a.txt" for y in range(2009, 2012)] + \
            [RAW / "census_bps_place_us" / f"mw{y}a.txt" for y in range(2012, 2016)]
    b = pd.concat([orr.read_old_bps(f) for f in files if f.exists()], ignore_index=True)
    b["key"] = b["state"] + "|" + b["bps_id"]
    b = b[~b["name"].str.lower().str.contains("county|balance|unincorporated")]
    g = orr.gazetteer2000()
    nm = b.drop_duplicates("key", keep="last")[["key", "state", "name"]].assign(base=lambda x: x["name"].str.lower())
    nm = nm.merge(g[["state", "base", "pop2000", "hu2000"]], on=["state", "base"], how="inner").drop_duplicates("key").set_index("key")
    units = b.pivot_table(index="key", columns="year", values="units", aggfunc="sum")
    rows = []
    for name, st, ey in TOWNS:
        k = nm[(nm["state"] == st) & (nm["base"] == name.lower())].index
        if not len(k):
            rows.append(dict(place=name, status="not found"))
            continue
        k = k[0]
        pre, post = list(range(ey - 5, ey)), list(range(ey + 1, ey + 4))
        need = pre + post
        ok = units.reindex(columns=need).notna().all(axis=1)
        p0 = nm.loc[k, "pop2000"]
        comp = nm[(nm["state"] == st) & nm["pop2000"].between(0.5 * p0, 2 * p0) & (nm.index != k)].index
        comp = [c for c in comp if ok.get(c, False)]
        if not ok.get(k, False) or len(comp) < 5:
            rows.append(dict(place=name, status="missing years or too few comparison places", comparison_places=len(comp)))
            continue
        r = lambda ks, yrs: units.loc[ks, yrs].sum().sum() / len(yrs) / nm.loc[ks, "hu2000"].sum() * 1000  # noqa: E731
        e = (r([k], post) - r([k], pre)) - (r(comp, post) - r(comp, pre))
        rows.append(dict(place=name, state_fips=st, event_year=ey, status="included", homes_2000=nm.loc[k, "hu2000"],
                         before=r([k], pre), after=r([k], post), cmp_before=r(comp, pre), cmp_after=r(comp, post),
                         effect=e, comparison_places=len(comp), permits_before=units.loc[k, pre].sum(), permits_after=units.loc[k, post].sum()))
    out = pd.DataFrame(rows)
    inc = out[out["status"] == "included"]
    if len(inc):
        w = inc["homes_2000"] * 3
        out = pd.concat([out, pd.DataFrame([dict(place="Group (weighted by homes)", status="summary",
                                                 effect=float(np.average(inc["effect"], weights=w)), homes_2000=inc["homes_2000"].sum())])])
    out.round(3).to_csv(REFERENCE / "parking_older_towns.csv", index=False)
    print(out.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

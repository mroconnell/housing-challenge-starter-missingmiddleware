"""Parking block-by-block catalog (docs/parking/BLOCK_CATALOG_PLAN.md).

    uv run --all-extras python scripts/run_parking_block_catalog.py

Reuses TOD's census block points (2000 Summary File 1 headers; 2010 and 2020 TIGER blocks) via
scripts/run_tod_census_cases.py and scripts/run_tod_census2000.py. Output: reference/parking_block_catalog.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from scripts import run_tod_census2000 as T  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402

SEED, DRAWS = 20261028, 2000
MILE = 1609.344
TOD_DIR = RAW / "tod_census_cases"
OLD = RAW / "parking_older_reforms"
MPLS_DOWNTOWN = (44.9778, -93.2650)   # downtown already had no minimums; blocks within 1.5 km are left out


def pt(lat, lon):
    return gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(R.CRS).iloc[0]


def place(st, geoid):
    d = TOD_DIR if (TOD_DIR / f"tl_2020_{st}_place.zip").exists() else OLD
    p = gpd.read_file(f"zip://{d}/tl_2020_{st}_place.zip")
    return p[p["GEOID"] == geoid].to_crs(R.CRS).geometry.union_all()


def stops():
    s = pd.DataFrame(json.load(open(TOD_DIR / "ntm_rail_stops.json")))
    return gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s["stop_lon"], s["stop_lat"]), crs=4326).to_crs(R.CRS)


def areas() -> list[dict]:
    out = []
    v = gpd.read_file(OLD / "seattle_urban_villages.geojson").to_crs(R.CRS)
    sea = place("53", "5363000")
    vil = v[v["UV_TYPE"].isin(["HUV", "RUV"])].geometry.union_all()
    other = v[v["UV_TYPE"].isin(["UC", "MIC"])].geometry.union_all()
    out.append(dict(case="Seattle urban villages (2012)", st="53", from_="2012-08-23", treated=vil.intersection(sea),
                    comp=sea.difference(vil).difference(other)))
    for name, lat, lon, ey, lab in (("South Hayward", 37.634340, -122.057182, "2011-07-01", "Hayward, South Hayward BART (2011)"),
                                    ("Warm Springs", 37.502307, -121.939358, "2015-07-01", "Fremont, Warm Springs (2015)")):
        c = pt(lat, lon)
        out.append(dict(case=lab, st="06", from_=ey, treated=c.buffer(MILE / 2), comp=c.buffer(1.5 * MILE).difference(c.buffer(MILE / 2))))
    mpls = place("27", "2743000")
    s = stops()
    s = s[s.within(mpls) & s["stop_type_text"].astype(str).str.contains("rail|Rail|Tram")]
    dt = pt(*MPLS_DOWNTOWN).buffer(1500)
    near = s.buffer(MILE / 2).union_all().intersection(mpls).difference(dt)
    out.append(dict(case="Minneapolis near-rail parking cut (2015)", st="27", from_="2015-07-01", treated=near,
                    comp=mpls.difference(near).difference(dt), stations=int(len(s))))
    return out


def rates(t0, t1, c0, c1):
    gt = (t1["homes"].sum() - t0["homes"].sum()) / t0["homes"].sum() * 100   # per 1,000 homes per year over a decade
    gc = (c1["homes"].sum() - c0["homes"].sum()) / c0["homes"].sum() * 100
    return gt - gc


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for a in areas():
        g = T.three(a["st"], a["treated"], a["comp"])
        (t0, c0), (t1, c1), (t2, c2) = g[2000], g[2010], g[2020]
        before, after = rates(t0, t1, c0, c1), rates(t1, t2, c1, c2)
        acre_before, acre_after = T.diffs(g)
        bs = np.empty((DRAWS, 2))
        for i in range(DRAWS):
            gg = {y: tuple(x.iloc[rng.integers(0, len(x), len(x))] for x in g[y]) for y in g}
            (u0, d0), (u1, d1), (u2, d2) = gg[2000], gg[2010], gg[2020]
            bs[i] = rates(u0, u1, d0, d1), rates(u1, u2, d1, d2)
        cic = bs[:, 1] - bs[:, 0]
        share = (pd.Timestamp("2020-04-01") - max(pd.Timestamp(a["from_"]), pd.Timestamp("2010-04-01"))).days / 3653
        rows.append(dict(case=a["case"], reform_from=a["from_"], share_of_2010s_under_reform=round(min(max(share, 0), 1), 2),
                         treated_homes_2000=t0["homes"].sum(), treated_homes_2010=t1["homes"].sum(), treated_homes_2020=t2["homes"].sum(),
                         comparison_homes_2000=c0["homes"].sum(), comparison_homes_2010=c1["homes"].sum(), comparison_homes_2020=c2["homes"].sum(),
                         gap_2000s=before, gap_2010s=after, change_in_change=after - before,
                         cic_p05=np.nanquantile(cic, 0.05), cic_p95=np.nanquantile(cic, 0.95),
                         gap_2000s_p05=np.nanquantile(bs[:, 0], 0.05), gap_2000s_p95=np.nanquantile(bs[:, 0], 0.95),
                         per_acre_gap_2000s=acre_before, per_acre_gap_2010s=acre_after, per_acre_cic=acre_after - acre_before,
                         stations=a.get("stations")))
    out = pd.DataFrame(rows)
    out.round(3).to_csv(REFERENCE / "parking_block_catalog.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

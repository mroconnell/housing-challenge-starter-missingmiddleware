"""Seattle 2012 and Portland 2002 transit-area parking reform checks (docs/parking/OLDER_REFORMS_PLAN.md).

    uv run python scripts/fetch_parking_older_reforms.py
    uv run python scripts/run_parking_older_reforms.py

Outputs: reference/parking_older_seattle_areas.csv, reference/parking_older_portland_places.csv,
reference/parking_older_results.csv

Geometry: missing_middleware/geom.py (open licence, docs/GEOMETRY.md); 2010 blocks are placed by GEOS's representative
point, ported in run_parking_census_check.py; joins to the city and the urban villages count ray crossings over all
rings of a feature, as GEOS did (the city's Greater Duwamish feature has a shell nested inside another shell, which
GEOS treats as a hole: Georgetown is outside the village). A 2010 block point's 2020 tract is the tract of the 2020
block that contains it (the old code dissolved 2020 blocks into tracts first; same answer).
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_census_check as rcc  # noqa: E402
from missing_middleware import geom  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

D = RAW / "parking_older_reforms"
SEED, DRAWS = 20261028, 2000
EA = 5070
TREATED = ("HUV", "RUV")
LEFT_OUT = ("UC", "MIC")
MF_CLASSES = ("L", "M", "H", "N", "C", "S")   # lowrise, midrise, highrise, neighborhood commercial, commercial, seattle mixed


# ---------------------------------------------------------------- Seattle
def seattle() -> list[dict]:
    v = geom.read_geojson(D / "seattle_urban_villages.geojson").to_crs(EA)
    city = geom.read_shapefile(D / "tl_2020_53_place.zip")
    city = city.subset(city.attrs["GEOID"] == "5363000").to_crs(EA)
    b20 = geom.read_shapefile(D / "tl_2020_53_tabblock20.zip")
    b20 = b20.subset(b20.attrs["COUNTYFP20"] == "033").to_crs(EA)
    b20.attrs = b20.attrs[["GEOID20", "COUNTYFP20", "TRACTCE20", "INTPTLAT20", "INTPTLON20"]]
    x20, y20 = geom.transform(b20.attrs["INTPTLON20"].astype(float).values, b20.attrs["INTPTLAT20"].astype(float).values, 4269, EA)
    pts20 = b20.attrs[["GEOID20", "TRACTCE20"]]
    b10a, x10, y10 = rcc.block_points_2010(D / "tabblock2010_53_pophu.zip", ["COUNTYFP10", "HOUSING10"], EA,
                                           where=lambda a: a["COUNTYFP10"] == "033")
    inside = rcc.points_in_polygons_evenodd(x10, y10, city.polys) >= 0      # within Seattle (inner join)
    b10, x10, y10 = b10a[inside].reset_index(drop=True), x10[inside], y10[inside]
    k = rcc.points_in_polygons_evenodd(x10, y10, v.polys)                   # urban villages do not overlap
    b10["UV_NAME"] = np.where(k >= 0, v.attrs["UV_NAME"].values[np.maximum(k, 0)], None)
    b10["UV_TYPE"] = np.where(k >= 0, v.attrs["UV_TYPE"].values[np.maximum(k, 0)], None)
    k = geom.points_in_polygons(x10, y10, b20.polys)                        # 2020 tract = tract of the 2020 block
    b10["TRACTCE20"] = np.where(k >= 0, b20.attrs["TRACTCE20"].values[np.maximum(k, 0)], np.nan)
    b10["UV_TYPE"] = b10["UV_TYPE"].fillna("OUT")
    b10["UV_NAME"] = b10["UV_NAME"].fillna("outside")
    b10["cluster"] = np.where(b10["UV_TYPE"] == "OUT", "tract " + b10["TRACTCE20"].astype(str), b10["UV_NAME"])
    homes = b10.groupby(["UV_TYPE", "cluster"])["HOUSING10"].sum()

    k = rcc.points_in_polygons_evenodd(x20, y20, v.polys)
    blk = pts20.assign(UV_NAME=np.where(k >= 0, v.attrs["UV_NAME"].values[np.maximum(k, 0)], None),
                       UV_TYPE=np.where(k >= 0, v.attrs["UV_TYPE"].values[np.maximum(k, 0)], None))
    blk["UV_TYPE"] = blk["UV_TYPE"].fillna("OUT")
    blk["cluster"] = np.where(blk["UV_TYPE"] == "OUT", "tract " + blk["TRACTCE20"].astype(str), blk["UV_NAME"])
    p = pd.DataFrame(json.load(open(D / "seattle_res_permits.json")))
    p["year"] = pd.to_numeric(p["YEAR_ISSUED"], errors="coerce")
    p["NET_UNITS"] = pd.to_numeric(p["NET_UNITS"], errors="coerce").fillna(0)
    p = p.merge(blk[["GEOID20", "UV_TYPE", "cluster"]], on="GEOID20", how="inner")
    p["mf_zone"] = p["CLASS"].fillna("").str[:1].isin(MF_CLASSES)

    pre, post_main, post_long = range(2007, 2012), range(2013, 2016), range(2013, 2018)
    units = p.groupby(["UV_TYPE", "cluster", "year"])["NET_UNITS"].sum()
    tab = []
    for (t, c), h in homes.items():
        row = dict(area_type=t, cluster=c, homes_2010=h)
        for y in range(2005, 2020):
            row[f"units_{y}"] = float(units.get((t, c, y), 0.0))
        tab.append(row)
    tab = pd.DataFrame(tab)
    tab.to_csv(REFERENCE / "parking_older_seattle_areas.csv", index=False)

    def rate(d, yrs):
        return d[[f"units_{y}" for y in yrs]].sum().sum() / len(yrs) / d["homes_2010"].sum() * 1000

    tr = tab[tab["area_type"].isin(TREATED)].reset_index(drop=True)
    co = tab[(tab["area_type"] == "OUT") & (tab["homes_2010"] > 0)].reset_index(drop=True)
    out = []
    rng = np.random.default_rng(SEED)
    for lab, post in (("Seattle 2012, urban villages vs rest of city, after 2013-2015", post_main),
                      ("Seattle 2012, after 2013-2017 (sensitivity)", post_long)):
        eff = lambda a, b: (rate(a, post) - rate(a, pre)) - (rate(b, post) - rate(b, pre))  # noqa: E731
        e = eff(tr, co)
        bs = [eff(tr.iloc[rng.integers(0, len(tr), len(tr))], co.iloc[rng.integers(0, len(co), len(co))]) for _ in range(DRAWS)]
        out.append(dict(case=lab, measure="per 1,000 existing homes per year", effect=e, p05=np.percentile(bs, 5), p95=np.percentile(bs, 95),
                        treated_before=rate(tr, pre), treated_after=rate(tr, post), comparison_before=rate(co, pre),
                        comparison_after=rate(co, post), treated_units=len(tr), comparison_units=len(co),
                        treated_homes=tr["homes_2010"].sum(), comparison_homes=co["homes_2010"].sum()))
    # sensitivity 2: comparison limited to multifamily and commercial zones; change in log permits
    q = p[p["UV_TYPE"].isin(TREATED) | ((p["UV_TYPE"] == "OUT") & p["mf_zone"])]
    g = q.assign(t=q["UV_TYPE"].isin(TREATED)).groupby(["t", "year"])["NET_UNITS"].sum()
    s = lambda t, yrs: sum(g.get((t, y), 0.0) for y in yrs) / len(yrs)  # noqa: E731
    lg = np.log(s(True, post_main) / s(True, pre)) - np.log(s(False, post_main) / s(False, pre))
    out.append(dict(case="Seattle 2012, comparison in multifamily and commercial zones only (sensitivity)",
                    measure="difference in log change of permits", effect=lg, p05=np.nan, p95=np.nan,
                    treated_before=s(True, pre), treated_after=s(True, post_main), comparison_before=s(False, pre),
                    comparison_after=s(False, post_main)))
    return out


# ---------------------------------------------------------------- Portland
def read_old_bps(path: Path) -> pd.DataFrame:
    rows = list(csv.reader(open(path, encoding="latin-1")))
    head2 = rows[1]
    ni = head2.index("Name")
    out = []
    for r in rows[2:]:
        if len(r) <= ni + 11 or not r[1].strip():
            continue
        u = lambda k: float(r[ni + k] or 0)  # noqa: E731
        out.append(dict(state=r[1].strip(), bps_id=r[2].strip(), name=r[ni].strip(), units=u(2) + u(5) + u(8) + u(11)))
    d = pd.DataFrame(out)
    d["year"] = int(path.name[2:6])
    return d


def gazetteer2000() -> pd.DataFrame:
    with zipfile.ZipFile(D / "places2k.zip") as z:
        txt = z.read(z.namelist()[0]).decode("latin-1")
    rows = []
    for line in io.StringIO(txt):
        rows.append(dict(usps=line[0:2], state=line[2:4], place=line[4:9], gname=line[9:73].strip(),
                         pop2000=float(line[73:82]), hu2000=float(line[82:91])))
    g = pd.DataFrame(rows)
    g["base"] = g["gname"].str.replace(r" (city|town|village|municipality|borough|city and borough)$", "", regex=True).str.lower()
    g = g[~g["gname"].str.endswith("CDP")]
    return g


def portland() -> tuple[list[dict], pd.DataFrame]:
    b = pd.concat([read_old_bps(f) for f in sorted(D.glob("we*a.txt"))], ignore_index=True)
    b["key"] = b["state"] + "|" + b["bps_id"]
    b = b[~b["name"].str.lower().str.contains("county|balance|unincorporated")]
    g = gazetteer2000()
    nm = b.drop_duplicates("key", keep="last")[["key", "state", "name"]].assign(base=lambda x: x["name"].str.lower())
    nm = nm.merge(g[["state", "base", "pop2000", "hu2000"]], on=["state", "base"], how="inner").drop_duplicates("key")
    years = set(range(1998, 2003)) | set(range(2004, 2007))
    have = b[b["year"].isin(years)].groupby("key")["year"].nunique()
    nm = nm[nm["key"].map(have).eq(len(years))]
    units = b.pivot_table(index="key", columns="year", values="units", aggfunc="sum")
    pdx = nm[(nm["state"] == "41") & (nm["base"] == "portland")].iloc[0]
    pacific = {"41", "53", "06", "02", "15"}
    pool = nm[nm["key"] != pdx["key"]]
    for scope, lo, hi in (("state", .5, 2), ("state", 1 / 3, 3), ("division", .5, 2), ("division", 1 / 3, 3)):
        c = pool[(pool["state"] == "41") if scope == "state" else pool["state"].isin(pacific)]
        c = c[(c["pop2000"] >= lo * pdx["pop2000"]) & (c["pop2000"] <= hi * pdx["pop2000"])]
        if len(c) >= 5:
            window = f"{scope} {lo:.2f}-{hi:.2f}"
            break
    pre, post = range(1998, 2003), range(2004, 2007)

    def rate(keys, yrs):
        return units.loc[list(keys), list(yrs)].sum().sum() / len(yrs) / nm.set_index("key").loc[list(keys), "hu2000"].sum() * 1000

    def eff(ctrl):
        return (rate([pdx["key"]], post) - rate([pdx["key"]], pre)) - (rate(ctrl, post) - rate(ctrl, pre))
    rng = np.random.default_rng(SEED)
    res = []
    for lab, cc in (("Portland 2002, citywide vs similar cities", c),
                    ("Portland 2002, without Seattle (sensitivity)", c[c["base"] != "seattle"])):
        keys = list(cc["key"])
        bs = [eff([keys[i] for i in rng.integers(0, len(keys), len(keys))]) for _ in range(DRAWS)]
        res.append(dict(case=lab, measure="per 1,000 existing homes per year", effect=eff(keys), p05=np.percentile(bs, 5),
                        p95=np.percentile(bs, 95), treated_before=rate([pdx["key"]], pre), treated_after=rate([pdx["key"]], post),
                        comparison_before=rate(keys, pre), comparison_after=rate(keys, post), treated_units=1,
                        comparison_units=len(keys), treated_homes=pdx["hu2000"], comparison_homes=cc["hu2000"].sum(),
                        comparison_window=window))
    places = pd.concat([nm[nm["key"] == pdx["key"]].assign(role="Portland"), c.assign(role="comparison")])
    for y in sorted(years):
        places[f"units_{y}"] = places["key"].map(units[y])
    return res, places


def main() -> None:
    s = seattle()
    pr, places = portland()
    places.to_csv(REFERENCE / "parking_older_portland_places.csv", index=False)
    r = pd.DataFrame(s + pr)
    r.round(4).to_csv(REFERENCE / "parking_older_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(r.round(2).to_string(index=False))
    print(places[["name", "state", "pop2000", "hu2000", "role"]].to_string(index=False))


if __name__ == "__main__":
    main()

"""Near-transit areas that never reformed (docs/parking/NEAR_TRANSIT_PLACEBO_PLAN.md).

    uv run --all-extras python scripts/run_parking_near_transit_placebo.py

Outputs: reference/parking_near_transit_placebo_units.csv, reference/parking_near_transit_placebo_results.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import voronoi_diagram

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import REFERENCE  # noqa: E402
from scripts import run_parking_block_catalog as B  # noqa: E402
from scripts import run_parking_near_transit_predict as P  # noqa: E402
from scripts import run_tod_census2000 as T  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402

SEED, DRAWS = 20261028, 2000
STATES = {"04": "Arizona", "06": "California", "17": "Illinois", "27": "Minnesota", "37": "North Carolina", "34": "New Jersey",
          "36": "New York", "42": "Pennsylvania", "48": "Texas", "49": "Utah", "51": "Virginia", "53": "Washington"}
NAMED_OUT = {"Seattle", "Minneapolis", "Salt Lake City", "Chicago", "Hayward", "Fremont", "San Diego", "Charlotte",
             "Albuquerque", "Penndel", "Portland"}


def excluded_names() -> set[tuple[str, str]]:
    t = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    t = t[(t["policy"] == "rm_min") & (t["scope"].fillna("").str.contains("transit-oriented") | t["benchmark_rating"].isin(["at", "near"]))]
    out = {(r.state, r.place.lower()) for r in t.itertuples()}
    e = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    out |= {(r.state, r.place.lower()) for r in e.itertuples()}
    out |= {(s, n.lower()) for s in STATES.values() for n in NAMED_OUT}
    return out


def units_for_state(st: str, rail, excl) -> list[dict]:
    try:
        pts = {y: (T.points_2000(st) if y == 2000 else R.block_points(st, y)) for y in (2000, 2010, 2020)}
    except Exception as ex:  # noqa: BLE001
        print(st, "skipped:", ex)
        return []
    places = gpd.read_file(f"zip://{B.TOD_DIR}/tl_2020_{st}_place.zip").to_crs(R.CRS)
    places = places[~places["NAME"].str.lower().map(lambda n: (STATES[st], n) in excl)]
    places = places[places["LSAD"] != "57"]  # census-designated places are not cities
    j = gpd.sjoin(rail[["geometry"]], places[["GEOID", "NAME", "geometry"]], predicate="within")
    rows = []
    for gid, sub in j.groupby("GEOID"):
        city = places[places["GEOID"] == gid].geometry.iloc[0]
        name = places.loc[places["GEOID"] == gid, "NAME"].iloc[0]
        st_pts = sub.geometry.drop_duplicates()
        st_pts = gpd.GeoSeries(st_pts.values, crs=R.CRS)
        # merge platforms within 200 m
        clusters = st_pts.buffer(200).union_all()
        centers = [g.centroid for g in (clusters.geoms if hasattr(clusters, "geoms") else [clusters])]
        if len(centers) > 1:
            cells = list(voronoi_diagram(gpd.GeoSeries(centers).union_all(), envelope=city.buffer(5000)).geoms)
        else:
            cells = [city.buffer(5000)]
        areas = []
        for c in centers:
            cell = next((x for x in cells if x.contains(c)), city)
            areas.append(c.buffer(B.MILE / 2).intersection(cell).intersection(city))
        near = gpd.GeoSeries(areas, crs=R.CRS).union_all()
        comp = city.difference(near)
        cm = {y: pts[y][R.within(pts[y], comp)] for y in pts}
        if cm[2010]["homes"].sum() < 1000:
            continue
        cg0, cg1 = P.growth(cm[2000], cm[2010]), P.growth(cm[2010], cm[2020])
        for k, a in enumerate(areas):
            t = {y: pts[y][R.within(pts[y], a)] for y in pts}
            if t[2000]["homes"].sum() < 100 or t[2010]["homes"].sum() < 100:
                continue
            g0, g1 = P.growth(t[2000], t[2010]), P.growth(t[2010], t[2020])
            rows.append(dict(region=f"{STATES[st]}: {name}", state=STATES[st], unit=f"{name} station {k + 1}", homes=t[2010]["homes"].sum(),
                             rail=1.0, prior_gap=(g0 - cg0) / P.CENSUS_TO_PERMITS,
                             outcome=((g1 - cg1) - (g0 - cg0)) / P.CENSUS_TO_PERMITS))
    print(st, len(rows), "areas", flush=True)
    return rows


def wls(d, cols):
    X = np.column_stack([np.ones(len(d))] + [d[c].values for c in cols])
    w = d["homes"].values
    W = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * W[:, None], d["outcome"].values * W, rcond=None)
    return dict(zip(["intercept"] + cols, beta))


def main() -> None:
    rail = B.stops()
    rail = rail[rail["stop_type_text"].astype(str).str.contains("rail|Rail|Tram|Subway|Metro")]
    excl = excluded_names()
    rows = []
    for st in STATES:
        rows += units_for_state(st, rail, excl)
    pl = pd.DataFrame(rows)
    pl["log_homes"] = np.log10(pl["homes"])
    pl.round(4).to_csv(REFERENCE / "parking_near_transit_placebo_units.csv", index=False)
    ref = pd.read_csv(REFERENCE / "parking_near_transit_units.csv")
    ref = ref[ref["region"].isin(["Seattle", "Minneapolis"])].copy()
    res = []
    # 1. same pattern?
    for lab, d in (("Non-reform station areas", pl), ("Reform areas (Seattle, Minneapolis)", ref)):
        b = wls(d, ["prior_gap", "log_homes"])
        res.append(dict(test="1. pattern", group=lab, areas=len(d), homes=d["homes"].sum(),
                        mean_outcome=float(np.average(d["outcome"], weights=d["homes"])),
                        slope_prior_gap=b["prior_gap"], slope_log_homes=b["log_homes"], intercept=b["intercept"]))
    # 2. parking effect
    both = pd.concat([pl.assign(reformed=0.0), ref.assign(reformed=1.0)], ignore_index=True)
    est = wls(both, ["prior_gap", "log_homes", "reformed"])["reformed"]
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(DRAWS):
        a = pl.iloc[rng.integers(0, len(pl), len(pl))]
        b = ref.iloc[rng.integers(0, len(ref), len(ref))]
        bs.append(wls(pd.concat([a.assign(reformed=0.0), b.assign(reformed=1.0)]), ["prior_gap", "log_homes", "reformed"])["reformed"])
    res.append(dict(test="2. parking effect", group="reformed vs not, same prior gap and size", areas=len(both),
                    effect=est, p05=np.percentile(bs, 5), p95=np.percentile(bs, 95)))
    # 3. prediction of reform areas from a model fitted on non-reform areas
    for t in ("one average", "weighted regression", "lasso"):
        p = P.predict(t, pl, ref, rng)
        res.append(dict(test="3. predict reform areas", group=t, areas=len(ref), error=P.wmae(p, ref),
                        mean_predicted=float(np.average(p, weights=ref["homes"])), mean_actual=float(np.average(ref["outcome"], weights=ref["homes"]))))
    r = pd.DataFrame(res)
    r.round(4).to_csv(REFERENCE / "parking_near_transit_placebo_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(pl.groupby("state").agg(areas=("unit", "size"), cities=("region", "nunique")).to_string())
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

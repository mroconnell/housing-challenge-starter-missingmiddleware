"""Near-transit areas that never reformed (docs/parking/NEAR_TRANSIT_PLACEBO_PLAN.md).

    uv run --all-extras python scripts/run_parking_near_transit_placebo.py

Outputs: reference/parking_near_transit_placebo_units.csv, reference/parking_near_transit_placebo_results.csv
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import REFERENCE  # noqa: E402
from scripts import run_parking_block_catalog as B  # noqa: E402
from scripts import run_parking_near_transit_predict as P  # noqa: E402

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


def _cross_params(a, b, c, d):
    """Parameters t in (0, 1) along segment a->b where it crosses segments c->d (arrays of segments)."""
    r = b - a
    q = d - c
    den = r[0] * q[:, 1] - r[1] * q[:, 0]
    ok = den != 0
    den = np.where(ok, den, 1.0)
    w = c - a
    t = (w[:, 0] * q[:, 1] - w[:, 1] * q[:, 0]) / den
    u = (w[:, 0] * r[1] - w[:, 1] * r[0]) / den
    m = ok & (t > 0) & (t < 1) & (u >= 0) & (u <= 1)
    return t[m]


def union_centroid(rings: list) -> tuple[float, float]:
    """Area centroid of the union of overlapping polygons (counter-clockwise rings), by Green's theorem over the
    union's boundary: the pieces of each ring's edges that lie outside every other ring."""
    o = rings[0][0].copy()                     # work relative to a local origin (precision of the cross products)
    rings = [r - o for r in rings]
    if len(rings) == 1:
        cx, cy = B.geom.feature_centroid([[rings[0]]])
        return cx + o[0], cy + o[1]
    A = Sx = Sy = 0.0
    for i, P in enumerate(rings):
        others = [Q for j, Q in enumerate(rings) if j != i]
        oseg = [(Q[:-1], Q[1:]) for Q in others]
        for e in range(len(P) - 1):
            a, b = P[e], P[e + 1]
            ts = np.sort(np.concatenate([[0.0, 1.0]] + [_cross_params(a, b, c, d) for c, d in oseg]))
            p = a + ts[:, None] * (b - a)
            mid = (p[:-1] + p[1:]) / 2
            out = np.ones(len(mid), bool)
            for Q in others:
                out &= ~B.geom.points_in_feature(mid[:, 0], mid[:, 1], [[Q]])
            p0, p1 = p[:-1][out], p[1:][out]
            cr = p0[:, 0] * p1[:, 1] - p1[:, 0] * p0[:, 1]
            A += cr.sum()
            Sx += ((p0[:, 0] + p1[:, 0]) * cr).sum()
            Sy += ((p0[:, 1] + p1[:, 1]) * cr).sum()
    return Sx / (3 * A) + o[0], Sy / (3 * A) + o[1]


def station_clusters(x, y, r: float = 200.0) -> list[tuple[float, float]]:
    """Centroids of the parts of the union of r-metre buffers (GEOS 64-gons) around the station points."""
    rings = [B.circle_ring(a, b, r) for a, b in zip(x, y)]
    n = len(rings)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    from scipy.spatial import cKDTree
    for i, j in cKDTree(np.c_[x, y]).query_pairs(2 * r + 1e-6):
        P, Q = rings[i], rings[j]
        touch = B.geom.points_in_feature(P[:-1, 0], P[:-1, 1], [[Q]]).any() or B.geom.points_in_feature(Q[:-1, 0], Q[:-1, 1], [[P]]).any() \
            or any(len(_cross_params(P[e], P[e + 1], Q[:-1], Q[1:])) for e in range(len(P) - 1))
        if touch:
            parent[find(i)] = find(j)
    groups: dict[int, list[int]] = {}
    for i in _str_leaf_order(rings):          # parts in the order GEOS's union returns them (station numbering)
        groups.setdefault(find(i), []).append(i)
    return [union_centroid([rings[i] for i in sorted(g)]) for g in groups.values()]


def _str_leaf_order(rings: list, node_capacity: int = 10) -> list[int]:
    """Leaf order of GEOS's STR tree over the rings' envelopes (sort by envelope centre x, cut into
    ceil(sqrt(ceil(n / capacity))) vertical slices, sort each slice by centre y). GEOS's cascaded union walks its inputs
    in this order, and the parts of the result come out in the order of their first input; checked against GEOS 3.14
    for all 198 cities with two or more parts (2026-11-02)."""
    n = len(rings)
    ex = np.array([[r[:, 0].min() + r[:, 0].max(), r[:, 1].min() + r[:, 1].max()] for r in rings])
    idx = np.argsort(ex[:, 0], kind="stable")
    per = math.ceil(n / math.ceil(math.sqrt(math.ceil(n / node_capacity))))
    out: list[int] = []
    for s in range(0, n, per):
        sl = idx[s:s + per]
        out += [int(i) for i in sl[np.argsort(ex[sl, 1], kind="stable")]]
    return out


def units_for_state(st: str, rail, excl) -> list[dict]:
    try:
        pts = {y: B.block_points(st, y) for y in (2000, 2010, 2020)}
    except Exception as ex:  # noqa: BLE001
        print(st, "skipped:", ex)
        return []
    places = B.place_layer(st)
    keep = ~places.attrs["NAME"].str.lower().map(lambda n: (STATES[st], n) in excl)
    keep &= places.attrs["LSAD"] != "57"  # census-designated places are not cities
    places = places.subset(keep)
    hit = B.geom.points_in_polygons(rail["x"].to_numpy(), rail["y"].to_numpy(), places.polys)
    j = pd.DataFrame({"x": rail["x"].to_numpy()[hit >= 0], "y": rail["y"].to_numpy()[hit >= 0],
                      "GEOID": places.attrs["GEOID"].to_numpy()[hit[hit >= 0]]})
    rows = []
    for gid, sub in j.groupby("GEOID"):
        k_city = int(np.flatnonzero(places.attrs["GEOID"].to_numpy() == gid)[0])
        city = B.Region.polygons([places.polys[k_city]])
        name = places.attrs["NAME"].iloc[k_city]
        st_pts = sub[["x", "y"]].drop_duplicates()
        # merge platforms within 200 m
        centers = station_clusters(st_pts["x"].to_numpy(), st_pts["y"].to_numpy())
        cx, cy = np.array([c[0] for c in centers]), np.array([c[1] for c in centers])
        areas = []
        for k, c in enumerate(centers):
            cell = B.Region.nearest_site(cx, cy, k)   # its Voronoi cell (the whole city when there is one station)
            areas.append((B.Region.circle(*c, B.MILE / 2) & cell) & city)
        near = B.Region.any_of(areas)
        comp = city - near
        cm = {y: pts[y][B.within(pts[y], comp)] for y in pts}
        if cm[2010]["homes"].sum() < 1000:
            continue
        cg0, cg1 = P.growth(cm[2000], cm[2010]), P.growth(cm[2010], cm[2020])
        for k, a in enumerate(areas):
            t = {y: pts[y][B.within(pts[y], a)] for y in pts}
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

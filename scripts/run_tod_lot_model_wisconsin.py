"""Apply the lot model's causal forest to Milwaukee and Madison under the modelled Wisconsin law
(docs/tod/LOT_MODEL_PLAN.md section 9, item 21).

    uv run --all-extras python scripts/run_tod_lot_model_wisconsin.py --stage build   # Wisconsin lot table
    uv run --all-extras python scripts/run_tod_lot_model_wisconsin.py --stage predict # three model versions

Writes data/processed/tod_lot_model/wi_lots.parquet (local) and reference/tod_lot_model_wisconsin.csv.
"""
from __future__ import annotations

import argparse
import importlib.util as ilu
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_station as XS  # noqa: E402
from missing_middleware import geom_extra_tod as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
import run_tod_lot_model as L  # noqa: E402

OUT = L.OUT / "wi_lots.parquet"
LAW_YEAR = 2027
EFF = 2023   # 5-year ACS 2018-2022, the latest the all-variables readers hold locally (item 21 change)
BEFORE = list(range(2019, 2025))


def _load(name: str):
    spec = ilu.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# Geometry without geopandas (docs/GEOMETRY.md): lots are polygon features (missing_middleware.geom's model) in the
# station-area build's EPSG:3071 ('poly', with GEOS interior points px, py); point sets are frames with x, y.

def width(geoms) -> list[float]:
    """Shorter side of each lot's minimum rotated rectangle (metres; NaN for degenerate lots)."""
    return list(X.min_rect_widths(list(geoms)))


def points_to_5070(pts: pd.DataFrame, crs) -> pd.DataFrame:
    """A point frame (x, y in crs) with x, y moved to EPSG:5070."""
    x, y = XS.transform(pts["x"].to_numpy(float), pts["y"].to_numpy(float), crs, 5070)
    return pts.assign(x=x, y=y)


def join_lots(pts: pd.DataFrame, polys: list) -> pd.DataFrame:
    """Spatial join 'within', inner: one row per (point, lot containing it), with the point's columns and index_right
    (the lot's position)."""
    pi, gi = XS.point_poly_pairs(pts["x"].to_numpy(float), pts["y"].to_numpy(float), polys)
    return pts.drop(columns=["x", "y"]).iloc[pi].assign(index_right=gi)


def built_points_milwaukee(crs) -> pd.DataFrame:
    """Homes on lots built 2019-2024 (MPROP year built and units; Milwaukee's open permits carry no unit counts)."""
    m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", dtype=str, usecols=["TAXKEY", "NR_UNITS", "YR_BUILT", "LAND_USE"])
    m["units"] = pd.to_numeric(m.NR_UNITS, errors="coerce").fillna(0)
    m["year"] = pd.to_numeric(m.YR_BUILT, errors="coerce")
    m = m[m.year.isin(BEFORE) & (m.units > 0)].drop_duplicates("TAXKEY")   # item 25.10: any lot with homes
    lay = G.read_geojson(RAW / "tod_capacity" / "v12_milwaukee.geojson", columns=["PARCELID"])
    v = lay.attrs.reset_index(drop=True)
    v["_g"] = np.arange(len(v))
    v = v.merge(m, left_on="PARCELID", right_on="TAXKEY")
    x, y = X.interior_points(X.polygons_to_crs([lay.polys[i] for i in v["_g"]], lay.crs, crs))
    return pd.DataFrame({"units": v.units.values, "year": v.year.values, "x": x, "y": y})


def built_points_madison(crs) -> pd.DataFrame:
    """Madison new-construction permits with unit counts, 2019-2024, placed on lots as in the Madison test."""
    M = _load("run_tod_madison_test")
    from missing_middleware.permits import madison
    from missing_middleware.permits.match import AddressIndex
    Lm = M.lots()
    ptab = madison.parcel_table(madison.load_parcels(RAW / "madison_parcels"))
    index = AddressIndex(madison.address_reference(ptab, madison.load_address_points(RAW / "madison_parcels")))
    d = M.permits_on_lots(Lm, index, M.ref_points(index.ref), ptab)
    d = d[d.placed & d.year.isin(BEFORE)]
    xy = Lm[["px", "py"]].reindex(d["lot"].astype(int))   # GEOS interior points (EPSG:3071)
    x, y = XS.transform(xy["px"].to_numpy(float), xy["py"].to_numpy(float), M.CRS_M, crs)
    return pd.DataFrame({"units": d["units"].values, "year": d["year"].values, "x": x, "y": y})


def city_frame(p: pd.DataFrame, city: str, rules, stops, built: pd.DataFrame, S) -> pd.DataFrame:
    """One Wisconsin city's lots in the lot model's columns. p: every city parcel (station-area loader)."""
    from scipy.spatial import cKDTree
    c = S.compute(p, city + " city", rules, stops)            # lots inside the law's station areas, with capacity
    inlaw = set(c["_key"])                                    # exact outlines (identical outlines were collapsed)
    allp = p.copy()
    allp["in_law"] = allp["_key"].isin(inlaw)
    allp["acres"] = allp["area_m2"] / S.M2_PER_ACRE
    # comparison lots: outside the law area, within 1/2 mile of it
    lt = cKDTree(np.c_[c["px"], c["py"]])
    dist = lt.query(np.c_[allp["px"], allp["py"]])[0]
    near = (~allp["in_law"]) & (dist <= 805)
    comp = allp[near].copy()
    comp["eligible"] = [S.C.is_eligible(z, u, "x") for z, u in zip(["residential"] * len(comp), comp.use_class)]
    comp["capacity_gain"] = 0.0
    comp["current_allowed_homes"] = np.nan
    comp["law_allowed_homes"] = np.nan
    c["in_law"] = True
    keep = ["poly", "px", "py", "acres", "homes", "use_class", "eligible", "capacity_gain", "current_allowed_homes",
            "law_allowed_homes", "in_law", "sqft_per_home"]
    for k in keep:
        if k not in comp:
            comp[k] = np.nan
    f = pd.concat([c[keep], comp[keep]], ignore_index=True)
    sq = float(c["sqft_per_home"].iloc[0])
    d = pd.DataFrame(index=f.index)
    d["city"], d["unit"], d["eff_year"] = city, f"wi_{city.lower()}_law", EFF
    d["x5070"], d["y5070"] = XS.transform(f["px"].to_numpy(float), f["py"].to_numpy(float), S.CRS_M, 5070)
    d["width_m"] = width(f["poly"])
    d["acres"] = f["acres"].values
    up = f["in_law"].astype(bool) & f["eligible"].astype(bool) & (f["capacity_gain"].fillna(0) > 0)
    d["treated"] = up.astype(float).values
    d["in_reform"] = f["in_law"].astype(float).values
    cls = f["use_class"].astype(str).str.lower()
    g = pd.Series("other_not_eligible", index=f.index, dtype=object)
    inl, el = f["in_law"].astype(bool), f["eligible"].astype(bool)
    g[~inl & el] = "comparison_eligible"
    g[~inl & ~el & cls.str.contains("industr")] = "comparison_industrial"
    g[~inl & ~el & cls.str.contains("institution|park|govern|exempt")] = "comparison_campus_or_park"
    g[inl & el & ~up] = "reform_density_not_rising"
    g[inl & ~el] = "reform_other_not_eligible"
    g[up] = "upzoned"
    d["lot_group"] = g.values
    d["comparison_eligible"] = (~inl & el).astype(float).values
    far0 = f["current_allowed_homes"] * sq / (f["acres"] * 43560)
    far1 = f["law_allowed_homes"] * sq / (f["acres"] * 43560)
    d["far_before"] = far0.values
    d["far_gain"] = (far1 - far0).where(up, 0.0).fillna(0).values
    d["use"] = np.where(cls.str.contains("residential|family|condo"), "res",
                        np.where(cls.str.contains("mixed"), "mixed", np.where(cls.str.contains("commercial"), "com",
                                 np.where(cls.str.contains("industr"), "ind", "unknown"))))
    d["census_homes"] = f["homes"].fillna(0).values
    # building before: on the lot and within 150 m (as near_units_before in training)
    bp = points_to_5070(built, S.CRS_M)
    pts = np.c_[d.x5070, d.y5070]
    t = cKDTree(np.c_[bp["x"], bp["y"]]) if len(bp) else None
    lot_j = join_lots(bp, XS.polys_to_crs(list(f["poly"]), S.CRS_M, 5070))
    d["units_before"] = lot_j.groupby("index_right")["units"].sum().reindex(d.index).fillna(0).values
    d["near_units_before"] = [float(bp["units"].values[n].sum()) for n in t.query_ball_point(pts, r=150)] if t else 0.0
    d["built_before"] = (d["units_before"] > 0).astype(float)
    d["units_after"], d["builds_after"] = 0.0, 0.0
    return d


def build() -> None:
    import hashlib
    sig = hashlib.sha256((Path(__file__).read_bytes() + (ROOT / "scripts" / "run_tod_lot_model.py").read_bytes())).hexdigest()
    done = OUT.with_suffix(".done")
    if OUT.exists() and done.exists() and done.read_text() == sig:
        print("Wisconsin lot table already built with this code; skipped", flush=True)
        return
    _build()
    done.write_text(sig)


def _build() -> None:
    S = _load("build_tod_station_areas")
    stops = S.stop_points()
    mke_rules, mad_rules = S.read_rules("milwaukee"), S.read_rules("madison")
    print("Milwaukee ...", flush=True)
    mke = S.load_milwaukee()
    fm = city_frame(mke, "Milwaukee", mke_rules, stops, built_points_milwaukee(S.CRS_M), S)
    print("Madison ...", flush=True)
    mad = S.load_madison({r["district"] for r in mad_rules})
    fd = city_frame(mad, "Madison", mad_rules, stops, built_points_madison(S.CRS_M), S)
    D = pd.concat([fm, fd], ignore_index=True)
    # qualifying stops for distance and the 1-mile count: the Wisconsin law's stops (rail, rapid, 15-minute bus)
    from scipy.spatial import cKDTree
    s = pd.read_csv(REFERENCE / "tod_stops.csv")
    s = s[s.flag_a_rapid == 1]   # item 25.7: rail and rapid only, as in training
    st = cKDTree(np.c_[L.lonlat_to_5070(s.lon, s.lat)])
    xy = D[["x5070", "y5070"]].to_numpy()
    D["dist_station_m"] = st.query(xy)[0]
    D["stops_1mile"] = [len(n) for n in st.query_ball_point(xy, r=1609)]
    share = np.full(len(D), np.nan)
    for unit, ix in D.groupby("unit").groups.items():
        dd = D.loc[ix]
        xy_ = dd[["x5070", "y5070"]].to_numpy()
        nb = cKDTree(xy_).query_ball_point(xy_, r=805)
        ac, tr = dd["acres"].to_numpy(), (dd["treated"].to_numpy() == 1)
        share[D.index.get_indexer(ix)] = [ac[n][tr[n]].sum() / ac[n].sum() if len(n) else np.nan for n in nb]
    D["share_upzoned_half_mile"] = share
    # item 25.9: homes on lot = 2020 census block homes shared among the table's lots in the block by lot area
    src = sorted(RAW.rglob("tl_2020_55_tabblock20.zip"))[0]
    lon, lat = XS.transform(D["x5070"].to_numpy(float), D["y5070"].to_numpy(float), 5070, 4269)
    b = XS.read_vector(src, None, columns=["GEOID20", "HOUSING20"], bbox=(lon.min(), lat.min(), lon.max(), lat.max()))
    k = XS.first_within(D["x5070"].to_numpy(float), D["y5070"].to_numpy(float), L.polys_5070(b))   # sjoin 'within', first match
    j = b.drop(columns="geometry").reset_index(drop=True).reindex(np.where(k >= 0, k, -1)).set_axis(D.index)
    grp = D["unit"].astype(str) + "|" + j["GEOID20"].astype(str)
    D["census_homes"] = (j["HOUSING20"].astype(float) * D["acres"] / D["acres"].groupby(grp).transform("sum")).values
    D = L.add_group_shares(D)
    D.to_parquet(OUT)
    print(D.groupby(["city", "lot_group"]).agg(lots=("acres", "size"), acres=("acres", "sum")).round(0).to_string())
    # tract traits with the lot model's own readers (ACS 2020-2024)
    L.STATE.update({"Milwaukee": "55", "Madison": "55"})
    L.PATHS["lots"] = OUT
    L.enrich()
    L.enrich_all()


def predict() -> None:
    from sklearn.ensemble import RandomForestRegressor
    from missing_middleware.tod import sanity as S
    L.BPS_NAME["Milwaukee"] = ("55", "Milwaukee")
    L.FAR_CITIES = L.FAR_CITIES + ("Milwaukee",)
    L.FIT["item25"] = True
    L.FIT["item32"] = True
    L.FIT["item34"] = True   # rezoned-later trait off for Wisconsin; missing-flag traits dropped   # item 21: Milwaukee treated as a floor-area-ratio city
    T = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    W = pd.read_parquet(OUT)
    W["cost_per_home"] = [L.cost_per_home(c, EFF - 1) for c in W["city"]]
    out = []
    for version in ("main", "seed7", "drop_largest"):
        Tv = T.drop(T.groupby("city")["units_after"].idxmax().values) if version == "drop_largest" else T
        cache = {k: L.cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(Tv["city"], Tv["eff_year"]))}
        Tv = Tv.assign(cost_per_home=[cache[(c, y)] for c, y in zip(Tv["city"], Tv["eff_year"])])
        Tv = L.dedupe_lots(Tv)   # item 32.6
        Wd = W.assign(w=1.0)
        A = pd.concat([Tv.assign(_wi=0), Wd.assign(_wi=1)], ignore_index=True)
        A["is_wi"] = A["_wi"]   # item 25.3: Wisconsin lots never share keys with training lots
        vc = [c for c in A.columns if c.startswith("v_")]
        V = A[vc].replace([np.inf, -np.inf], np.nan)
        ref = (A._wi == 0) & ~A["city"].isin(L.HOLD)
        V = V.fillna(V[ref].median())
        Xb = pd.concat([L.features(A.drop(columns=["_wi"]), False), V], axis=1)
        Xa = pd.concat([L.features(A.drop(columns=["_wi"]), True), V], axis=1)
        X = Xb
        if version == "main":
            fl = S.unit_flags(A, L.FAR_CITIES) + S.policy_flags(A[A._wi == 1]) + S.range_flags(X, A["city"])
            S.report([f for f in fl if f["city"] in ("Milwaukee", "Madison") or f["kind"] != "out of range"],
                     REFERENCE / "tod_lot_model_wisconsin_flags.csv")
        tr = A.index[A._wi == 0]
        Tb = L.five_year_basis(A[A._wi == 0])   # item 24
        dy = pd.Series(0.0, index=A.index)
        dy[Tb.index] = (Tb["ua5"] - Tb["ub5"]).values
        dy = dy.values
        seed = 7 if version == "seed7" else 20261027
        pred = {}
        for gflag in (1, 0):
            ix = tr[(A.loc[tr, "treated"] == gflag).values]
            if gflag == 0:   # item 32.4: the unchanged forest learns from eligible comparison lots, as the yardstick
                ix = tr[((A.loc[tr, "treated"] == 0) & (A.loc[tr, "comparison_eligible"] == 1)).values]
            XX = Xa if gflag == 1 else Xb   # item 25.1
            m = RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=seed)
            m.fit(XX.loc[ix], dy[ix], sample_weight=A.loc[ix, "w"])
            wt = A.index[(A._wi == 1) & (A["treated"] == 1)]
            pred[gflag] = pd.Series(m.predict(XX.loc[wt]), index=wt)
        if version == "main":   # item 25 note 13: per-lot effects by size of the gain
            e = pred[1] - pred[0]
            rg = Xa.loc[e.index, "rel_gain"]
            print("effect per lot by relative gain:", e.groupby(pd.cut(rg, [-0.01, 0.25, 1, 3, 10.01])).agg(["size", "mean", "sum"]).round(3).to_string(), flush=True)
        eff = (pred[1] - pred[0]) * A.loc[pred[1].index, "w"]
        for city in ("Milwaukee", "Madison"):
            ii = [i for i in eff.index if A.at[i, "city"] == city]
            out.append({"version": version, "city": city, "upzoned_lots": len(ii),
                        "upzoned_acres": float(A.loc[ii, "acres"].sum()), "extra_homes_5yr": float(eff.loc[ii].sum())})
            print(out[-1], flush=True)
    R = pd.DataFrame(out)
    R.round(1).to_csv(REFERENCE / "tod_lot_model_wisconsin.csv", index=False)
    print(R.pivot_table(index="city", columns="version", values="extra_homes_5yr").round(0).to_string())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["build", "predict"], required=True)
    a = ap.parse_args(argv)
    build() if a.stage == "build" else predict()


if __name__ == "__main__":
    main()

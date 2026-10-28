"""Lot-level model (docs/tod/LOT_MODEL_PLAN.md, written before fitting).

    uv run --all-extras python scripts/run_tod_lot_model.py --stage collect   # one lot table across case cities
    uv run --all-extras python scripts/run_tod_lot_model.py --stage fit       # two-part model, leave-one-city-out

The lot table is local only (data/processed/tod_lot_model/lots.parquet): it holds lot geometry-derived traits but no
lot ids. Committed outputs are aggregate: reference/tod_lot_model_results.csv.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import cases as C  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.run_tod_net_effect import _permits_from_points, capture  # noqa: E402

OUT = PROCESSED / "tod_lot_model"
LOTS = OUT / "lots.parquet"
HOLD = ("Chicago", "Madison")
STATE = {"New York": "36", "Philadelphia": "42", "Charlotte": "37", "Saint Paul": "27", "Seattle": "53",
         "Los Angeles": "06", "Chicago": "17", "Madison": "55"}


def rail(crs):
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    return gpd.GeoSeries(gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(crs)


def lot_frame(city: str, unit: str, args: dict, area: pd.Series, q: pd.DataFrame, per: dict, stops, eff: int) -> pd.DataFrame:
    L = args["parcels"]
    keep = area.isin([C.TREAT, C.COMP]) & args["eligible"].astype(bool)
    L = L[keep]
    pts = L.geometry.representative_point()
    d = pd.DataFrame(index=L.index)
    d["city"], d["unit"], d["eff_year"] = city, unit, int(eff)
    p5070 = pts.to_crs(5070)
    d["x5070"], d["y5070"] = p5070.x.values, p5070.y.values
    # lot width: the narrow side of the minimum rotated rectangle (metres)
    def _w(g):
        try:
            r = g.minimum_rotated_rectangle
            xs, ys = r.exterior.coords.xy
            sides = [((xs[i + 1] - xs[i]) ** 2 + (ys[i + 1] - ys[i]) ** 2) ** 0.5 for i in range(4)]
            return float(min(sides))
        except Exception:  # noqa: BLE001
            return np.nan
    d["width_m"] = [_w(g) for g in L.geometry]
    d["treated"] = (area[keep] == C.TREAT).astype(float)
    d["acres"] = L.geometry.area / C.SQM_PER_ACRE
    lb = args["level_before"].astype(float).reindex(L.index).replace(np.inf, np.nan)
    la = args["level_after"].astype(float).reindex(L.index).replace(np.inf, np.nan)
    d["far_before"] = lb
    d["far_gain"] = (la - lb).where(d["treated"] == 1, 0.0)
    d["use"] = L["zclass"].astype(str) if "zclass" in L else "unknown"
    sidx = stops.sindex
    near = sidx.nearest(pts.values, return_all=False)
    d["dist_station_m"] = pts.reset_index(drop=True).distance(stops.iloc[near[1]].reset_index(drop=True)).values
    for c in ("unitsRes", "NR_UNITS", "homes_before", "Units1"):
        if c in L:
            d["homes_on_lot"] = pd.to_numeric(L[c], errors="coerce")
            break
    p = q.dropna(subset=["pix"]).copy()
    p["pix"] = p["pix"].astype(int)
    p = p[p["pix"].isin(d.index)]
    b, a = per["before"], per["after"]
    pb = p[p["year"].isin(b)].groupby("pix")["units"].sum()
    pa = p[p["year"].isin(a)].groupby("pix")["units"].sum()
    yrs = p.groupby(["pix", "year"])["units"].sum().reset_index()
    yrs["s"] = yrs["year"].astype(str) + ":" + yrs["units"].round(0).astype(int).astype(str)
    d["permit_years"] = yrs.groupby("pix")["s"].agg(";".join).reindex(d.index).fillna("")
    d["window_first"], d["window_last"] = min(b + a), max(b + a)
    d["units_before"] = pb.reindex(d.index).fillna(0)
    d["units_after"] = pa.reindex(d.index).fillna(0)
    d["builds_after"] = (d["units_after"] > 0).astype(float)
    d["built_before"] = (d["units_before"] > 0).astype(float)
    # block-level pressure: homes permitted within 150 m in before years, per acre of lots there
    if len(p):
        pp = pts.loc[p["pix"]].values
        pg = gpd.GeoDataFrame({"u": p["units"].values, "yr": p["year"].values}, geometry=pp, crs=L.crs)
        pg = pg[pg["yr"].isin(b)]
        buf = gpd.GeoDataFrame(geometry=pts.buffer(150), crs=L.crs)
        j = gpd.sjoin(pg, buf, predicate="within")
        d["near_units_before"] = j.groupby("index_right")["u"].sum().reindex(d.index).fillna(0).values
    else:
        d["near_units_before"] = 0.0
    return d.reset_index(drop=True)


def collect() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frames, stops = [], {}
    from missing_middleware.tod import case_nyc as N
    for ulurp, (name, boro) in N.POOLED.items():
        with capture(nyc=N) as cap:
            try:
                m = N.build_member(ulurp, boro)
            except Exception as e:  # noqa: BLE001
                print(f"  {name}: {type(e).__name__}: {e}")
                continue
        args, area = cap["uniform"][-1]
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        jg, ix = cap["jobs"][-1]
        frames.append(lot_frame("New York", f"nyc_{ulurp}", args, area, _permits_from_points(jg, ix), m["per"], stops[crs], m["effective_year"]))
        print(f"New York {name}", flush=True)
    from missing_middleware.tod import case_philadelphia as P
    d = P._load()
    rm = d["rm"]
    dp = rm[(rm["Origination"] == "DistrictPlan") & rm["changes"] & rm["enacted"].dt.year.between(*P.MEMBER_YEARS)]
    q = _permits_from_points(d["permits"], d["permits"]["pix"])
    for bill in sorted(dp["Bill_Number_TXT"].astype(str).unique()):
        with capture() as cap:
            try:
                m = P.build_member(bill)
            except Exception:  # noqa: BLE001
                continue
        if not m["acres"].get(C.TREAT, 0) > 0:
            continue
        args, area = cap["uniform"][-1]
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        frames.append(lot_frame("Philadelphia", f"phl_{bill}", args, area, q, m["per"], stops[crs], m["effective"].year))
    print("Philadelphia", flush=True)
    for key, city in (("chicago", "Chicago"), ("stpaul", "Saint Paul"), ("charlotte", "Charlotte")):
        mod = importlib.import_module(f"missing_middleware.tod.case_{key}")
        with capture() as cap:
            ci, _ = mod.build()
        args, area = cap["uniform"][0]
        pts, pix = cap["locate"][-1]
        per = C.period_years(ci.effective_year, ci.first_year, ci.last_full_year)
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        frames.append(lot_frame(city, key, args, area, _permits_from_points(pts, pix), per, stops[crs], ci.effective_year))
        print(city, flush=True)
    from missing_middleware.tod import case_seattle as K
    for case in ("seattle_nbh_othello_2012", "seattle_mount_baker_2014"):
        with capture() as cap:
            f = K._frame(case)
        args, area = cap["uniform"][-1]
        pg = K._load()["permits"]
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        frames.append(lot_frame("Seattle", case, args, area, _permits_from_points(pg, pg["pix"]), f["per"], stops[crs], f["effective_year"]))
    print("Seattle", flush=True)
    from missing_middleware.tod import case_la as LA
    for case in ("la_warner_center_2013", "la_cornfield_arroyo_seco_2013"):
        with capture() as cap:
            parcels, qg, per, eff, rule, st = LA._areas(case)
        args, area = cap["uniform"][0]
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        frames.append(lot_frame("Los Angeles", case, args, area, _permits_from_points(qg, qg["pix"]), per, stops[crs], eff.year))
    print("Los Angeles", flush=True)
    # Madison 2023 overlay (holdout), as in run_tod_net_effect.build_madison
    from importlib import util as _ilu
    spec = _ilu.spec_from_file_location("run_tod_madison_test", ROOT / "scripts" / "run_tod_madison_test.py")
    M = _ilu.module_from_spec(spec)
    spec.loader.exec_module(M)
    from missing_middleware.permits import madison
    from missing_middleware.permits.match import AddressIndex
    from missing_middleware.tod import madison_test as MT
    from missing_middleware.tod import net_effect as NE
    Lm = M.lots()
    ptab = madison.parcel_table(madison.load_parcels(RAW / "madison_parcels"))
    ref = madison.address_reference(ptab, madison.load_address_points(RAW / "madison_parcels"))
    index = AddressIndex(ref)
    rpts = M.ref_points(index.ref)
    changed, _ = M.rezoned_lots(Lm, index, rpts)
    Lm["changed"] = changed
    margs = NE.bind_uniform_args(Lm, in_reform=Lm.in_overlay, rose=Lm.rose, level_before=Lm.far_base, level_after=Lm.far_ovl,
                                 uncapped_before=Lm.uncapped, changed_outside=Lm.changed, eligible=Lm.elig)
    marea, _ = C.uniform_areas(**margs)
    margs["eligible"] = Lm["elig"]
    dm = M.permits_on_lots(Lm, index, rpts, ptab)
    xm = dm[dm.placed].copy()
    qm = pd.DataFrame({"project": xm["project"].astype(str), "year": xm["year"], "units": xm["units"], "pix": xm["lot"].astype(int)})
    crs = str(Lm.crs)
    stops.setdefault(crs, rail(Lm.crs))
    frames.append(lot_frame("Madison", "madison_tod_overlay_2023", margs, marea, qm, {"before": list(MT.BEFORE), "after": list(MT.AFTER)},
                            stops[crs], 2023))
    print("Madison", flush=True)
    D = pd.concat(frames, ignore_index=True)
    D.to_parquet(LOTS)
    print(D.groupby(["city", "treated"]).agg(lots=("acres", "size"), builds_before=("built_before", "mean"),
                                             builds_after=("builds_after", "mean"), units_after=("units_after", "sum")).round(3).to_string())


TRACT_VARS = {"c01_median_rent": "rent", "c04_median_value": "home_value", "p11_median_income": "income"}


def enrich() -> None:
    """Lots inherit their census tract's median rent, home value and household income (owner, 2026-10-28), from the
    5-year ACS ending the year before each case's reform, read with the all-variables test's own readers."""
    import importlib.util
    from missing_middleware.tod import allvars as A
    spec = importlib.util.spec_from_file_location("run_tod_allvars", ROOT / "scripts" / "run_tod_allvars.py")
    AV = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(AV)
    D = pd.read_parquet(LOTS)
    D["end_year"] = D["eff_year"].map(A.survey_end_year)
    D["state"] = D["city"].map(STATE)
    pts = gpd.GeoSeries(gpd.points_from_xy(D["x5070"], D["y5070"]), crs=5070)
    for k in TRACT_VARS.values():
        D[k] = np.nan
    for (y, st), ix in D.groupby(["end_year", "state"]).groups.items():
        try:
            cells, ncells, _ = (AV.tbsf_cells if y >= 2021 else AV.seq_cells)(int(y), st)
            shp = AV.tract_shapes(A.tract_vintage(int(y)), st)
            cells = cells.join(shp.set_index("tract")[["ALAND_SQMI"]], how="left")
            parts = A.tract_parts(cells, ncells, int(y))
        except Exception as e:  # noqa: BLE001
            print(f"  {y} {st}: {type(e).__name__}: {e}")
            continue
        g = gpd.GeoDataFrame(geometry=pts.loc[ix].values, index=ix, crs=5070)
        j = gpd.sjoin(g, shp[["tract", "geometry"]].to_crs(5070), how="left", predicate="within")
        j = j[~j.index.duplicated()]
        for vid, col in TRACT_VARS.items():
            D.loc[ix, col] = j["tract"].map(parts[vid + "__num"]).values
        print(f"  {A.survey_label(int(y))} {st}: {len(ix):,} lots", flush=True)
    D.to_parquet(LOTS)
    print(D.groupby("city")[list(TRACT_VARS.values())].median().round(0).to_string())


COOK = "https://datacatalog.cookcountyil.gov/resource/uzyt-m557.json"
CHICAGO_TOWNSHIPS = ["Hyde Park", "Jefferson", "Lake", "Lake View", "North Chicago", "Rogers Park", "South Chicago", "West Chicago"]


def values() -> None:
    """Building and land values from before each window (plan section 9, item 1): New York from the MapPLUTO
    snapshot before each rezoning; Chicago from Cook County's 2012 assessed values. Other cities: missing flag."""
    import urllib.parse
    import urllib.request
    from missing_middleware.tod import case_nyc as N
    D = pd.read_parquet(LOTS)
    for c in ("land_value", "total_value", "year_built"):
        D[c] = np.nan
    pts = gpd.GeoSeries(gpd.points_from_xy(D["x5070"], D["y5070"]), crs=5070)
    # New York
    for unit, ix in D[D["city"] == "New York"].groupby("unit").groups.items():
        ulurp = unit.replace("nyc_", "")
        name, boro = N.POOLED[ulurp]
        bl = gpd.read_file(N.DIR / "bloomberg_rezonings.geojson")
        m = bl[bl["ULURPNO"].astype(str).str.lower() == ulurp]
        eff = pd.Timestamp(int(D.loc[ix[0], "eff_year"]), 7, 1)
        if len(m) and "Adopted" in m:
            eff = pd.to_datetime(m["Adopted"].iloc[0], errors="coerce") or eff
        per = C.period_years(eff.year, N.FIRST_YEAR, N.LAST_FULL_YEAR)
        vs = N.pick_vintages(eff, per["before"][0], per["after"][-1])
        path = N._shp(vs["before"], boro)
        cm = N._cols(path, ["AssessLand", "AssessTot", "YearBuilt"])
        lp = pts.loc[ix].to_crs(N.CRS_M)
        bb = tuple(gpd.GeoSeries(lp.values, crs=N.CRS_M).buffer(50).total_bounds)
        crs = gpd.read_file(path, rows=1).crs
        bb = tuple(gpd.GeoSeries([__import__("shapely").geometry.box(*bb)], crs=N.CRS_M).to_crs(crs).total_bounds)
        g = gpd.read_file(path, columns=list(cm.values()), bbox=bb).to_crs(N.CRS_M).rename(columns={v: k for k, v in cm.items()})
        j = gpd.sjoin(gpd.GeoDataFrame(geometry=lp.values, index=ix, crs=N.CRS_M), g, how="left", predicate="within")
        j = j[~j.index.duplicated()]
        D.loc[ix, "land_value"] = pd.to_numeric(j.get("AssessLand"), errors="coerce").values
        D.loc[ix, "total_value"] = pd.to_numeric(j.get("AssessTot"), errors="coerce").values
        D.loc[ix, "year_built"] = pd.to_numeric(j.get("YearBuilt"), errors="coerce").replace(0, np.nan).values
        print(f"  New York {name}: values for {np.isfinite(D.loc[ix, 'total_value']).mean():.0%} of lots", flush=True)
    # Chicago (Cook County 2012 assessed values; pins joined through the case's own parcel layer)
    cook_f = OUT / "cook_values_2012.parquet"
    if not cook_f.exists():
        rows, off = [], 0
        where = "year='2012' AND township_name in (" + ",".join(f"'{t}'" for t in CHICAGO_TOWNSHIPS) + ")"
        while True:
            q = urllib.parse.urlencode({"$select": "pin,certified_bldg,certified_land", "$where": where, "$limit": 50000, "$offset": off, "$order": "pin"})
            with urllib.request.urlopen(f"{COOK}?{q}", timeout=600) as r:
                page = json.load(r)
            rows += page
            off += len(page)
            if len(page) < 50000:
                break
        pd.DataFrame(rows).to_parquet(cook_f)
    cook = pd.read_parquet(cook_f)
    cook["pin10"] = cook["pin"].astype(str).str[:10]
    cook = cook.groupby("pin10")[["certified_bldg", "certified_land"]].agg(lambda s: pd.to_numeric(s, errors="coerce").sum())
    par = gpd.read_file(RAW / "tod_cases" / "chicago" / "parcels.geojson")[["pin10", "geometry"]].to_crs(5070)
    ix = D.index[D["city"] == "Chicago"]
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=pts.loc[ix].values, index=ix, crs=5070), par, how="left", predicate="within")
    j = j[~j.index.duplicated()]
    v = cook.reindex(j["pin10"].astype(str).str[:10].values)
    D.loc[ix, "land_value"] = v["certified_land"].values
    D.loc[ix, "total_value"] = (v["certified_land"] + v["certified_bldg"]).values
    print(f"  Chicago: values for {np.isfinite(D.loc[ix, 'total_value']).mean():.0%} of lots", flush=True)
    D["bldg_to_land"] = ((D["total_value"] - D["land_value"]) / D["land_value"]).where(D["land_value"] > 0)
    D.to_parquet(LOTS)
    print(D.groupby("city")[["bldg_to_land", "year_built"]].agg(lambda s: s.notna().mean()).round(2).to_string())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=["collect", "enrich", "values", "fit"], required=True)
    a = ap.parse_args(argv)
    if a.stage == "collect":
        collect()
    if a.stage == "enrich":
        enrich()
    if a.stage == "values":
        values()


if __name__ == "__main__":
    main()

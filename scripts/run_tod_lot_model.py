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
HOLD = ("Chicago", "Madison", "Bellevue")
FAR_CITIES = ("New York", "Chicago", "Madison", "Saint Paul", "Seattle", "Bellevue")   # levels are floor area ratios
STATE = {"New York": "36", "Philadelphia": "42", "Charlotte": "37", "Saint Paul": "27", "Seattle": "53",
         "Los Angeles": "06", "Chicago": "17", "Madison": "55", "Bellevue": "53"}


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


def add_bellevue() -> None:
    """Bellevue BelRed (2009) lots as a third holdout (plan section 9, item 8), appended to the lot table."""
    from missing_middleware.tod import case_bellevue as B
    with capture() as cap:
        ci, _ = B.build()
    # the adapter calls the uniform rule more than once; keep the call that has treated land (the context rule)
    args, area = max(cap["uniform"], key=lambda t: int((t[1] == C.TREAT).sum()))
    pg = B._prepare()["permits"]
    per = C.period_years(B.EFFECTIVE_YEAR, B.FIRST_YEAR, B.LAST_FULL_YEAR)
    stops = rail(args["parcels"].crs)
    f = lot_frame("Bellevue", "bellevue_belred_2009", args, area, _permits_from_points(pg, pg["pix"]), per, stops, B.EFFECTIVE_YEAR)
    D = pd.read_parquet(LOTS)
    D = pd.concat([D[D["city"] != "Bellevue"], f], ignore_index=True)
    D.to_parquet(LOTS)
    print(f.groupby("treated").agg(lots=("acres", "size"), builds_after=("builds_after", "mean"), units_after=("units_after", "sum")))


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
            t = pd.to_datetime(m["Adopted"].iloc[0], errors="coerce")
            if pd.notna(t) and t.year == eff.year:
                eff = t
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
        col = lambda k: pd.to_numeric(j[k], errors="coerce") if k in j else pd.Series(np.nan, index=j.index)  # noqa: E731
        D.loc[ix, "land_value"] = col("AssessLand").values
        D.loc[ix, "total_value"] = col("AssessTot").values
        D.loc[ix, "year_built"] = col("YearBuilt").replace(0, np.nan).values
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


BPS_NAME = {"New York": ("36", "New York"), "Philadelphia": ("42", "Philadelphia"), "Charlotte": ("37", "Mecklenburg County"),
            "Saint Paul": ("27", "St. Paul"), "Seattle": ("53", "Seattle"), "Los Angeles": ("06", "Los Angeles"),
            "Chicago": ("17", "Chicago"), "Madison": ("55", "Madison"), "Bellevue": ("53", "Bellevue")}


def cost_per_home(city: str, year: int) -> float:
    """Census permit survey: construction value per home in buildings of 5+ homes, that city and year (else the
    nearest year with at least 20 such homes)."""
    st, name = BPS_NAME[city]
    best = None
    for y in [year, year - 1, year + 1, year - 2, year + 2]:
        for reg in ("mw", "ne", "so", "we"):
            f = RAW / "tod_control_cities" / "bps" / f"{reg}{y}a.txt"
            if not f.exists():
                continue
            lines = f.read_text(errors="replace").splitlines()
            h2 = [c.strip() for c in lines[1].split(",")]
            ni = h2.index("Name")
            for line in lines[2:]:
                c = line.split(",")
                if len(c) > ni + 13 and c[1].strip().zfill(2) == st and c[ni].strip() == name:
                    u, v = float(c[ni + 11] or 0), float(c[ni + 12] or 0)
                    if u >= 20:
                        return v / u
    return best if best is not None else np.nan


def features(D: pd.DataFrame, after_rules: bool) -> pd.DataFrame:
    X = pd.DataFrame(index=D.index)
    X["log_acres"] = np.log(D["acres"].clip(lower=0.005))
    X["log_width"] = np.log(D["width_m"].clip(lower=1))
    X["homes_on_lot"] = np.log1p(D["homes_on_lot"].fillna(-1).clip(lower=0))
    X["homes_missing"] = D["homes_on_lot"].isna().astype(float)
    X["log_dist_station"] = np.log1p(D["dist_station_m"])
    # Unit-free density traits (plan section 9, item 12): cities record allowed density in different units
    # (floor area ratio; Charlotte feet of height; Philadelphia and Los Angeles an ordering), so the raw level is
    # replaced by its rank within the city, and the change by the relative change, only where a real FAR exists.
    far_city = D["city"].isin(FAR_CITIES)
    lb = D["far_before"].astype(float)
    X["level_rank_in_city"] = lb.groupby(D["city"]).rank(pct=True).fillna(0.5)
    up = D["treated"] == 1
    rel = (D["far_gain"].astype(float) / lb.where(lb > 0)).where(far_city & up)
    X["upzoned"] = up.astype(float) if after_rules else 0.0
    X["rel_gain"] = rel.clip(0, 10).fillna(0) if after_rules else 0.0
    X["rel_gain_known"] = (far_city & up).astype(float) if after_rules else 0.0
    X["far_now"] = (lb + (D["far_gain"].fillna(0) if after_rules else 0.0)).where(far_city)   # FAR cities only
    X["far_known"] = far_city.astype(float)
    X["built_before"] = D["built_before"]
    X["log_near_before"] = np.log1p(D["near_units_before"])
    X["log_rent"] = np.log(D["rent"].clip(lower=100)).fillna(np.log(1000))
    X["log_value"] = np.log(D["home_value"].clip(lower=10000)).fillna(np.log(200000))
    X["log_income"] = np.log(D["income"].clip(lower=5000)).fillna(np.log(50000))
    X["soft_site"] = np.log1p(D["bldg_to_land"].clip(lower=0)).fillna(0) if "bldg_to_land" in D else 0.0
    X["soft_missing"] = D["bldg_to_land"].isna().astype(float) if "bldg_to_land" in D else 1.0
    age = (D["eff_year"] - D["year_built"]) if "year_built" in D else pd.Series(np.nan, index=D.index)
    X["age"] = age.clip(0, 200).fillna(-1)
    X["rent_to_cost"] = (D["rent"].fillna(1000) * 12 / 0.05) / D["cost_per_home"]
    sqft = (X["far_now"].fillna(0) * D["acres"] * 43560)
    allowed = sqft / 1000.0
    X["pays_room"] = np.log1p((allowed - D["homes_on_lot"].fillna(0)).clip(lower=0)) * X["rent_to_cost"]
    for u in ("res", "com", "ind", "mixed"):
        X[f"use_{u}"] = (D["use"].astype(str) == u).astype(float)
    if "share_upzoned_half_mile" in D:
        X["share_upzoned_half_mile"] = D["share_upzoned_half_mile"]
        X["log_stops_1mile"] = np.log1p(D["stops_1mile"])
    X = X.replace([np.inf, -np.inf], np.nan)
    return X.fillna(X.median())


def ceiling(Dtr: pd.DataFrame, Xtr: pd.DataFrame):
    """Homes-per-lot ceiling learned from training building lots (owner, 2026-10-28; plan item 12). Where a real FAR
    exists: homes the zoning allows x the 99th-percentile stretch. Elsewhere: the 99th-percentile homes per acre."""
    b = Dtr["units_after"].values > 0
    far = Xtr["far_known"].values == 1
    allowed = (Xtr["far_now"] * Dtr["acres"] * 43560 / 1000).clip(lower=1).values
    stretch = float(np.nanquantile(Dtr["units_after"].values[b & far] / allowed[b & far], 0.99)) if (b & far).any() else np.inf
    per_acre = float(np.nanquantile(Dtr["units_after"].values[b] / Dtr["acres"].clip(lower=0.01).values[b], 0.99))
    def lim(D_, X_):
        a = (X_["far_now"] * D_["acres"] * 43560 / 1000).clip(lower=1).values * stretch
        p = D_["acres"].clip(lower=0.01).values * per_acre
        return np.where(X_["far_known"].values == 1, a, p)
    return lim


def fit(allvars: bool = False) -> None:
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler
    D = pd.read_parquet(LOTS)
    cache = {k: cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(D["city"], D["eff_year"]))}
    D["cost_per_home"] = [cache[(c, y)] for c, y in zip(D["city"], D["eff_year"])]
    print({k: round(v) for k, v in cache.items() if v == v}, flush=True)
    key = D["city"] + "|" + D["x5070"].round(1).astype(str) + "|" + D["y5070"].round(1).astype(str)
    D["w"] = 1.0 / key.map(key.value_counts())
    Xa, Xb = features(D, True), features(D, False)
    if allvars:
        vc = [c for c in D.columns if c.startswith("v_")]
        V = D[vc].replace([np.inf, -np.inf], np.nan)
        V = V.fillna(V.median())
        Xa, Xb = pd.concat([Xa, V], axis=1), pd.concat([Xb, V], axis=1)
    y1 = D["builds_after"].values
    y2 = np.log1p(D["units_after"].values)
    cities = [c for c in D["city"].unique() if c not in HOLD]

    def actual_extra(d):
        t, c = d[d.treated == 1], d[d.treated == 0]
        ta, ca = (t.acres * t.w).sum(), (c.acres * c.w).sum()
        return ((t.units_after * t.w).sum() - ta * (c.units_after * c.w).sum() / ca) - \
               ((t.units_before * t.w).sum() - ta * (c.units_before * c.w).sum() / ca), ta

    def model_predict(train_ix, test_ix, kind):
        tr = train_ix
        if kind == "logit":
            sc = StandardScaler().fit(Xa.loc[tr])
            m1 = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(Xa.loc[tr]), y1[tr], sample_weight=D.loc[tr, "w"])
            p = lambda X: m1.predict_proba(sc.transform(X))[:, 1]  # noqa: E731
            b = (y1[tr] == 1)
            m2 = LinearRegression().fit(sc.transform(Xa.loc[tr][b]), y2[tr][b], sample_weight=D.loc[tr, "w"][b])
            raw = lambda X: np.expm1(m2.predict(sc.transform(X)))  # noqa: E731
        else:
            m1 = GradientBoostingClassifier(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=20261027)
            m1.fit(Xa.loc[tr], y1[tr], sample_weight=D.loc[tr, "w"])
            p = lambda X: m1.predict_proba(X)[:, 1]  # noqa: E731
            b = (y1[tr] == 1)
            m2 = GradientBoostingRegressor(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=20261027)
            m2.fit(Xa.loc[tr][b], y2[tr][b], sample_weight=D.loc[tr, "w"][b])
            raw = lambda X: np.expm1(m2.predict(X))  # noqa: E731
        # lot ceiling (owner, 2026-10-28): homes the zoning allows on the lot x the stretch real projects reached
        lim = ceiling(D.loc[tr], Xa.loc[tr])
        def s_(X):
            return np.minimum(raw(X), lim(D.loc[X.index], X)).clip(min=1)
        te = test_ix
        tt = D.loc[te, "treated"] == 1
        Xa_t, Xb_t = Xa.loc[te][tt.values], Xb.loc[te][tt.values]
        extra = float(((p(Xa_t) * s_(Xa_t)) - (p(Xb_t) * s_(Xb_t))) @ D.loc[te][tt.values]["w"].values)
        auc = roc_auc_score(y1[te], p(Xa.loc[te]), sample_weight=D.loc[te, "w"]) if len(set(y1[te])) > 1 else np.nan
        return extra, auc

    rows = []
    for kind in (("boosting",) if allvars else ("logit", "boosting")):
        for c in cities + list(HOLD):
            test_ix = D.index[D["city"] == c]
            train_ix = D.index[D["city"].isin([x for x in cities if x != c])]
            act, ta = actual_extra(D.loc[test_ix])
            # baseline: training cities' acre-weighted extra per upzoned acre
            num, den = 0.0, 0.0
            for cc_ in [x for x in cities if x != c]:
                e, a = actual_extra(D[D["city"] == cc_])
                num, den = num + e, den + a
            base = num / den * ta
            ex, auc = model_predict(train_ix, test_ix, kind)
            rows.append({"model": kind, "city": c, "role": "holdout" if c in HOLD else "fold", "upzoned_acres": ta,
                         "actual_extra_homes": act, "baseline_extra": base, "model_extra": ex,
                         "error_baseline": abs(base - act), "error_model": abs(ex - act), "auc_builds": auc})
            print(kind, c, round(act), round(base), round(ex), round(auc, 3) if auc == auc else None, flush=True)
    E = pd.DataFrame(rows)
    summ = []
    for kind, g in E.groupby("model"):
        f, h = g[g.role == "fold"], g[g.role == "holdout"].set_index("city")
        ok_total = f["error_model"].mean() < f["error_baseline"].mean() and all(h.loc[c, "error_model"] < h.loc[c, "error_baseline"] for c in HOLD)
        auc_ok = all(h.loc[c, "auc_builds"] >= 0.70 for c in HOLD) and f["auc_builds"].mean() >= 0.70
        zero = f["actual_extra_homes"].abs().mean()
        new_ok = f["error_model"].mean() < min(f["error_baseline"].mean(), zero) and \
            sum(h.loc[c, "error_model"] < h.loc[c, "error_baseline"] for c in HOLD) >= 2
        summ.append({"model": kind, "fold_mean_error_guess_zero": zero, "passes_new_rule": bool(new_ok),
                     "fold_mean_error_baseline": f["error_baseline"].mean(), "fold_mean_error_model": f["error_model"].mean(),
                     "fold_cities_model_better": int((f["error_model"] < f["error_baseline"]).sum()), "fold_cities": len(f),
                     **{f"{c.lower()}_error_baseline": h.loc[c, "error_baseline"] for c in HOLD},
                     **{f"{c.lower()}_error_model": h.loc[c, "error_model"] for c in HOLD},
                     "fold_mean_auc": f["auc_builds"].mean(), **{f"{c.lower()}_auc": h.loc[c, "auc_builds"] for c in HOLD},
                     "passes_total": bool(ok_total), "passes_where": bool(auc_ok)})
    S = pd.DataFrame(summ)
    tag = "_runD_allvars" if allvars else "_runD"
    # Which lot traits the boosted "builds" model leans on (fitted on all fold cities; permutation on the holdouts)
    from sklearn.inspection import permutation_importance
    tr = D.index[D["city"].isin(cities)]
    m1 = GradientBoostingClassifier(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=20261027)
    m1.fit(Xa.loc[tr], y1[tr], sample_weight=D.loc[tr, "w"])
    ho = D.index[D["city"].isin(HOLD)]
    pi = permutation_importance(m1, Xa.loc[ho], y1[ho], scoring="roc_auc", n_repeats=5, random_state=20261027,
                                sample_weight=D.loc[ho, "w"].values)
    imp = pd.DataFrame({"trait": Xa.columns, "split_importance": m1.feature_importances_,
                        "holdout_auc_drop_when_shuffled": pi.importances_mean}).sort_values("holdout_auc_drop_when_shuffled", ascending=False)
    imp.round(4).to_csv(REFERENCE / f"tod_lot_model_importance{tag}.csv", index=False)
    print(imp.round(4).to_string())
    tag = "_runD_allvars" if allvars else "_runD"
    E.round(3).to_csv(REFERENCE / f"tod_lot_model_by_city{tag}.csv", index=False)
    S.round(4).to_csv(REFERENCE / f"tod_lot_model_results{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(E.round(2).to_string())
    print(S.round(3).T.to_string())


def add_saturation() -> None:
    """Plan section 9, item 11: share of upzoned land within 1/2 mile (same case), and stops within 1 mile."""
    from scipy.spatial import cKDTree
    D = pd.read_parquet(LOTS)
    share = np.full(len(D), np.nan)
    for unit, ix in D.groupby("unit").groups.items():
        d = D.loc[ix]
        xy = d[["x5070", "y5070"]].to_numpy()
        t = cKDTree(xy)
        nb = t.query_ball_point(xy, r=805)
        ac, tr = d["acres"].to_numpy(), (d["treated"].to_numpy() == 1)
        share[D.index.get_indexer(ix)] = [ac[n][tr[n]].sum() / ac[n].sum() if len(n) else np.nan for n in nb]
    D["share_upzoned_half_mile"] = share
    s_ = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    sp = gpd.GeoSeries(gpd.points_from_xy(s_.stop_lon, s_.stop_lat), crs=4326).to_crs(5070)
    st = cKDTree(np.c_[sp.x, sp.y])
    D["stops_1mile"] = [len(n) for n in st.query_ball_point(D[["x5070", "y5070"]].to_numpy(), r=1609)]
    D.to_parquet(LOTS)
    print(D.groupby(["city", "treated"])[["share_upzoned_half_mile", "stops_1mile"]].median().round(3).to_string())


def enrich_all() -> None:
    """All 91 tract variables of the all-variables test on every lot (plan section 9, item 9)."""
    import importlib.util as ilu
    from missing_middleware.tod import allvars as A
    spec = ilu.spec_from_file_location("run_tod_allvars", ROOT / "scripts" / "run_tod_allvars.py")
    AV = ilu.module_from_spec(spec)
    spec.loader.exec_module(AV)
    D = pd.read_parquet(LOTS)
    D["end_year"] = D["eff_year"].map(A.survey_end_year)
    D["state"] = D["city"].map(STATE)
    pts = gpd.GeoSeries(gpd.points_from_xy(D["x5070"], D["y5070"]), crs=5070)
    cols = {v["id"]: f"v_{v['id']}" for v in A.VARIABLES}
    new = pd.DataFrame(np.nan, index=D.index, columns=list(cols.values()))
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
        for v in A.VARIABLES:
            n, d = parts[v["id"] + "__num"], parts[v["id"] + "__den"]
            val = (n / d.where(d > 0)) if v["kind"] == "ratio" else n
            new.loc[ix, cols[v["id"]]] = j["tract"].map(val).values
        print(f"  {A.survey_label(int(y))} {st}: {len(ix):,} lots", flush=True)
    D = pd.concat([D.drop(columns=[c for c in cols.values() if c in D]), new], axis=1)
    D.to_parquet(LOTS)
    print("share of lots with each variable (median across variables):", float(new.notna().mean().median()))


def fit8(tlearner: bool = False) -> None:
    """Run C (plan section 9, item 10): all 8 methods, two-part lot versions, all-variables traits."""
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
    from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
    rng = np.random.default_rng(20261027)
    D = pd.read_parquet(LOTS)
    cache = {k: cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(D["city"], D["eff_year"]))}
    D["cost_per_home"] = [cache[(c, y)] for c, y in zip(D["city"], D["eff_year"])]
    key = D["city"] + "|" + D["x5070"].round(1).astype(str) + "|" + D["y5070"].round(1).astype(str)
    D["w"] = 1.0 / key.map(key.value_counts())
    Xa, Xb = features(D, True), features(D, False)
    vc = [c for c in D.columns if c.startswith("v_")]
    if vc:
        V = D[vc].replace([np.inf, -np.inf], np.nan)
        V = V.fillna(V.median())
        Xa, Xb = pd.concat([Xa, V], axis=1), pd.concat([Xb, V], axis=1)
    y1 = D["builds_after"].values
    y2 = np.log1p(D["units_after"].values)
    dy = (D["units_after"] - D["units_before"]).values
    cities = [c for c in D["city"].unique() if c not in HOLD]

    def actual_extra(d):
        t, c = d[d.treated == 1], d[d.treated == 0]
        ta, ca = (t.acres * t.w).sum(), (c.acres * c.w).sum()
        return ((t.units_after * t.w).sum() - ta * (c.units_after * c.w).sum() / ca) - \
               ((t.units_before * t.w).sum() - ta * (c.units_before * c.w).sum() / ca), ta

    def makers(kind):
        if kind == "wls":
            return lambda: LogisticRegression(max_iter=2000), lambda: LinearRegression(), True
        if kind == "lasso":
            return lambda: LogisticRegression(penalty="l1", solver="saga", C=0.1, max_iter=500), lambda: Lasso(alpha=0.01), True
        if kind == "elastic_net":
            return lambda: LogisticRegression(penalty="elasticnet", l1_ratio=0.5, solver="saga", C=0.1, max_iter=500), lambda: ElasticNet(alpha=0.01, l1_ratio=0.5), True
        if kind == "tree":
            return lambda: DecisionTreeClassifier(max_depth=3, min_samples_leaf=200), lambda: DecisionTreeRegressor(max_depth=3, min_samples_leaf=200), False
        if kind == "forest":
            return lambda: RandomForestClassifier(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=20261027), \
                   lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=20261027), False
        if kind == "boosting":
            return lambda: GradientBoostingClassifier(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=20261027), \
                   lambda: GradientBoostingRegressor(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=20261027), False
        if kind == "knn":
            return lambda: KNeighborsClassifier(n_neighbors=50, n_jobs=-1), lambda: KNeighborsRegressor(n_neighbors=50, n_jobs=-1), True
        raise ValueError(kind)

    def predict(kind, tr, te):
        tt = te[(D.loc[te, "treated"] == 1).values]
        sample = te if len(te) <= 20000 else rng.choice(te, 20000, replace=False)
        if tlearner:
            regs = {"wls": lambda: LinearRegression(), "lasso": lambda: Lasso(alpha=0.01), "elastic_net": lambda: ElasticNet(alpha=0.01, l1_ratio=0.5),
                    "tree": lambda: DecisionTreeRegressor(max_depth=3, min_samples_leaf=200),
                    "forest": lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=20261027),
                    "causal_forest": lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=20261027),
                    "boosting": lambda: GradientBoostingRegressor(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=20261027),
                    "knn": lambda: KNeighborsRegressor(n_neighbors=50, n_jobs=-1)}
            scale = kind in ("wls", "lasso", "elastic_net", "knn")
            sc = StandardScaler().fit(Xb.loc[tr]) if scale else None
            T = (lambda X: sc.transform(X)) if scale else (lambda X: X)  # noqa: E731
            out = []
            for g in (1, 0):
                ix = tr[(D.loc[tr, "treated"] == g).values]
                if kind == "knn" and len(ix) > 60000:
                    ix = rng.choice(ix, 60000, replace=False)
                m = regs[kind]()
                try:
                    m.fit(T(Xb.loc[ix]), dy[D.index.get_indexer(ix)], sample_weight=D.loc[ix, "w"])
                except TypeError:
                    m.fit(T(Xb.loc[ix]), dy[D.index.get_indexer(ix)])
                out.append(m.predict(T(Xb.loc[tt])))
            return float((out[0] - out[1]) @ D.loc[tt, "w"].values), np.nan
        if kind == "causal_forest":
            out = []
            for g in (1, 0):
                ix = tr[(D.loc[tr, "treated"] == g).values]
                m = RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=20261027)
                m.fit(Xb.loc[ix], dy[D.index.get_indexer(ix)], sample_weight=D.loc[ix, "w"])
                out.append(m.predict(Xb.loc[tt]))
            extra = float((out[0] - out[1]) @ D.loc[tt, "w"].values)
            return extra, np.nan
        c1, c2, scale = makers(kind)
        sc = StandardScaler().fit(Xa.loc[tr]) if scale else None
        T = (lambda X: sc.transform(X)) if scale else (lambda X: X)  # noqa: E731
        fit_ix = tr if kind != "knn" or len(tr) <= 60000 else rng.choice(tr, 60000, replace=False)
        ii = D.index.get_indexer(fit_ix)
        w = D.loc[fit_ix, "w"].values
        m1 = c1()
        try:
            m1.fit(T(Xa.loc[fit_ix]), y1[ii], sample_weight=w)
        except TypeError:
            m1.fit(T(Xa.loc[fit_ix]), y1[ii])
        b = y1[ii] == 1
        m2 = c2()
        try:
            m2.fit(T(Xa.loc[fit_ix][b]), y2[ii][b], sample_weight=w[b])
        except TypeError:
            m2.fit(T(Xa.loc[fit_ix][b]), y2[ii][b])
        lim = ceiling(D.loc[fit_ix], Xa.loc[fit_ix])
        def homes(X):
            size = np.minimum(np.expm1(np.clip(m2.predict(T(X)), 0, 12)), lim(D.loc[X.index], X)).clip(min=1)
            return m1.predict_proba(T(X))[:, 1] * size
        extra = float((homes(Xa.loc[tt]) - homes(Xb.loc[tt])) @ D.loc[tt, "w"].values)
        ys = y1[D.index.get_indexer(sample)]
        auc = roc_auc_score(ys, m1.predict_proba(T(Xa.loc[sample]))[:, 1]) if len(set(ys)) > 1 else np.nan
        return extra, auc

    rows = []
    methods = ("wls", "lasso", "elastic_net", "tree", "forest", "boosting", "causal_forest", "knn")
    for kind in methods:
        for c in cities + list(HOLD):
            te = D.index[D["city"] == c].to_numpy()
            tr = D.index[D["city"].isin([x for x in cities if x != c])].to_numpy()
            act, ta = actual_extra(D.loc[te])
            num = den = 0.0
            for x in [x for x in cities if x != c]:
                e, a = actual_extra(D[D["city"] == x])
                num, den = num + e, den + a
            base = num / den * ta
            ex, auc = predict(kind, tr, te)
            rows.append({"method": kind, "city": c, "role": "holdout" if c in HOLD else "fold", "actual_extra_homes": act,
                         "baseline_extra": base, "model_extra": ex, "error_baseline": abs(base - act), "error_model": abs(ex - act),
                         "auc_builds": auc})
            print(kind, c, round(act), round(base), round(ex), flush=True)
    E = pd.DataFrame(rows)
    summ = []
    for kind, g in E.groupby("method", sort=False):
        f, h = g[g.role == "fold"], g[g.role == "holdout"].set_index("city")
        ok = f["error_model"].mean() < f["error_baseline"].mean() and all(h.loc[c, "error_model"] < h.loc[c, "error_baseline"] for c in HOLD)
        zero = f["actual_extra_homes"].abs().mean()
        new_ok = f["error_model"].mean() < min(f["error_baseline"].mean(), zero) and \
            sum(h.loc[c, "error_model"] < h.loc[c, "error_baseline"] for c in HOLD) >= 2
        summ.append({"method": kind, "fold_mean_error_guess_zero": zero, "passes_new_rule": bool(new_ok), "fold_mean_error_baseline": f["error_baseline"].mean(), "fold_mean_error_model": f["error_model"].mean(),
                     "fold_cities_better": int((f["error_model"] < f["error_baseline"]).sum()),
                     **{f"{c.lower()}_better": bool(h.loc[c, "error_model"] < h.loc[c, "error_baseline"]) for c in HOLD},
                     "cities_better_of_9": int((g["error_model"] < g["error_baseline"]).sum()), "passes_total": bool(ok)})
    S = pd.DataFrame(summ)
    tag = "_runE" if tlearner else "_runD_all8"
    E.round(3).to_csv(REFERENCE / f"tod_lot_model_by_city{tag}.csv", index=False)
    S.round(4).to_csv(REFERENCE / f"tod_lot_model_results{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(2).to_string())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=["collect", "add_bellevue", "enrich", "enrich_all", "values", "fit", "fit_allvars", "fit8", "fit_runE", "add_saturation"], required=True)
    a = ap.parse_args(argv)
    if a.stage == "collect":
        collect()
    if a.stage == "add_bellevue":
        add_bellevue()
    if a.stage == "enrich":
        enrich()
    if a.stage == "values":
        values()
    if a.stage == "fit":
        fit()
    if a.stage == "enrich_all":
        enrich_all()
    if a.stage == "fit_allvars":
        fit(allvars=True)
    if a.stage == "fit8":
        fit8()
    if a.stage == "fit_runE":
        fit8(tlearner=True)
    if a.stage == "add_saturation":
        add_saturation()


if __name__ == "__main__":
    main()

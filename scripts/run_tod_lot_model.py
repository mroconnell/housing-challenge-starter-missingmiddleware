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
LOTS_HALF = OUT / "lots_halfmile.parquet"   # plan section 9, item 14
FIT = {"lots": LOTS, "suffix": ""}
LOTS_REBUILT = OUT / "lots_rebuilt.parquet"   # plan section 9, item 15
REBUILT = {"on": False}
PATHS = {"lots": LOTS, "half": LOTS_HALF}
SEED = {"v": 20261027}
ROBUST = {"drop_largest": False}
LOT_GROUPS = ("upzoned", "upzoned_from_industrial", "upzoned_from_campus", "upzoned_by_later_rezoning", "reform_density_not_rising", "reform_already_allowed",
              "reform_single_family_untouched", "reform_campus_or_park_unchanged", "reform_rezoned_again_in_window",
              "reform_other_not_eligible", "comparison_eligible", "comparison_industrial", "comparison_campus_or_park",
              "other_not_eligible")
HOLD = ("Chicago", "Madison", "Bellevue")
FAR_CITIES = ("New York", "Chicago", "Saint Paul", "Seattle")   # levels are printed floor area ratios. Bellevue out: 0/1 flags (item 18); Madison out: stories x 0.70, i.e. height (item 34)
LEVEL_SOURCE = {"New York": "printed FAR", "Chicago": "printed FAR", "Saint Paul": "printed FAR", "Seattle": "printed FAR",
                "Madison": "height", "Charlotte": "height", "Philadelphia": "district order", "Los Angeles": "district order",
                "Bellevue": "in/out flag", "Milwaukee": "homes per acre", "Madison placebo": "homes per acre",
                "Milwaukee placebo": "homes per acre", "Columbus placebo": "none", "Kansas City placebo": "none"}
STATE = {"Madison placebo": "55", "Milwaukee placebo": "55", "Columbus placebo": "39", "Kansas City placebo": "29", "New York": "36", "Philadelphia": "42", "Charlotte": "37", "Saint Paul": "27", "Seattle": "53",
         "Los Angeles": "06", "Chicago": "17", "Madison": "55", "Bellevue": "53"}


def rail(crs):
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    return gpd.GeoSeries(gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(crs)


def add_group_shares(D: pd.DataFrame) -> pd.DataFrame:
    """Each reform unit's share of in-reform acres in each lot group (plan section 9, item 16)."""
    if "lot_group" not in D:
        return D
    r = D[D["in_reform"] == 1]
    tot = r.groupby("unit")["acres"].sum()
    for g in LOT_GROUPS:
        if g.startswith(("reform_", "upzoned")):
            D[f"share_{g}"] = D["unit"].map(r[r["lot_group"] == g].groupby("unit")["acres"].sum() / tot).fillna(0.0)
    return D


def lot_class(city: str, L) -> pd.Series:
    """Zoning or use class before the reform, lower case (res, com, mixed, ind, inst, park, single_family, ...)."""
    for c in ("zclass", "use_class"):
        if c in L:
            return L[c].astype(str).str.lower()
    if city == "Los Angeles" and "zone_before" in L:
        from missing_middleware.tod import case_la as LA
        return L["zone_before"].map(LA.zclass).astype(str).str.lower()
    for c in ("z_before", "zoning_before", "zone_before"):
        if c in L and city == "Philadelphia":
            from missing_middleware.tod import case_philadelphia as PH
            return L[c].map(PH.zclass).astype(str).str.lower()
    return pd.Series("unknown", index=L.index)


def lot_frame(city: str, unit: str, args: dict, area: pd.Series, q: pd.DataFrame, per: dict, stops, eff: int) -> pd.DataFrame:
    L = args["parcels"]
    if REBUILT["on"]:
        # plan section 9, items 15-16: every lot inside the reform or in its comparison area is kept, with a label for
        # what the reform did to it; industrial or institutional land rezoned to allow homes counts as upzoned
        inr, rose = args["in_reform"].astype(bool), args["rose"].astype(bool)
        el = args["eligible"].astype(bool)
        el2 = el | (inr & rose)
        # item 31: groups fixed by the reform's map on the day it passed; later rezonings are a trait, not an exclusion
        chg_later = args["changed_outside"].astype(bool)
        area, _ = C.uniform_areas(**dict(args, eligible=el2, changed_outside=pd.Series(False, index=L.index)))
        keep = area.isin([C.TREAT, C.COMP]) | inr
        in_reform = inr
        cls = lot_class(city, L)
        chg = pd.Series(False, index=L.index)   # item 31: no "rezoned again" group
        g = pd.Series("other_not_eligible", index=L.index, dtype=object)
        g[~inr & el] = "comparison_eligible"
        g[~inr & ~el & cls.str.startswith("ind")] = "comparison_industrial"
        g[~inr & ~el & cls.str.startswith(("inst", "park"))] = "comparison_campus_or_park"
        g[inr & ~el & cls.str.startswith(("inst", "park")) & ~rose] = "reform_campus_or_park_unchanged"
        g[inr & ~el & cls.str.contains("single")] = "reform_single_family_untouched"
        g[inr & el & ~rose] = "reform_density_not_rising"
        g[inr & el2 & rose & (area != C.TREAT) & ~chg] = "reform_already_allowed"
        g[inr & chg] = "reform_rezoned_again_in_window"
        g[area == C.TREAT] = "upzoned"
        g[(area == C.TREAT) & ~el & cls.str.startswith("ind")] = "upzoned_from_industrial"
        g[(area == C.TREAT) & ~el & cls.str.startswith(("inst", "park"))] = "upzoned_from_campus"
        g[inr & ~el & ~rose & (g == "other_not_eligible")] = "reform_other_not_eligible"
        lot_group = g
        comp_eligible = (area == C.COMP) & el2 & ~inr
    else:
        keep = area.isin([C.TREAT, C.COMP]) & args["eligible"].astype(bool)
        in_reform = area == C.TREAT
        lot_group = pd.Series("upzoned", index=L.index).where(area == C.TREAT, "comparison_eligible")
        comp_eligible = area == C.COMP
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
    d["in_reform"] = in_reform[keep].astype(float).values
    d["lot_group"] = lot_group[keep].astype(str).values
    d["level_source"] = LEVEL_SOURCE.get(city, "unknown")   # item 34.5
    d["level_flag"] = L["level_flag"].astype(str).values if "level_flag" in L else ""
    d["rezoned_later"] = (chg_later[keep].astype(float).values if REBUILT["on"] else 0.0)
    d["comparison_eligible"] = comp_eligible[keep].astype(float).values
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
    D = add_group_shares(pd.concat(frames, ignore_index=True))
    D.to_parquet(PATHS['lots'])
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
    D = pd.read_parquet(PATHS['lots'])
    D = add_group_shares(pd.concat([D[D["city"] != "Bellevue"], f], ignore_index=True))
    D.to_parquet(PATHS['lots'])
    print(f.groupby("treated").agg(lots=("acres", "size"), builds_after=("builds_after", "mean"), units_after=("units_after", "sum")))


def enrich() -> None:
    """Lots inherit their census tract's median rent, home value and household income (owner, 2026-10-28), from the
    5-year ACS ending the year before each case's reform, read with the all-variables test's own readers."""
    import importlib.util
    from missing_middleware.tod import allvars as A
    spec = importlib.util.spec_from_file_location("run_tod_allvars", ROOT / "scripts" / "run_tod_allvars.py")
    AV = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(AV)
    D = pd.read_parquet(PATHS['lots'])
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
    D.to_parquet(PATHS['lots'])
    print(D.groupby("city")[list(TRACT_VARS.values())].median().round(0).to_string())


COOK = "https://datacatalog.cookcountyil.gov/resource/uzyt-m557.json"
CHICAGO_TOWNSHIPS = ["Hyde Park", "Jefferson", "Lake", "Lake View", "North Chicago", "Rogers Park", "South Chicago", "West Chicago"]


def values() -> None:
    """Building and land values from before each window (plan section 9, item 1): New York from the MapPLUTO
    snapshot before each rezoning; Chicago from Cook County's 2012 assessed values. Other cities: missing flag."""
    import urllib.parse
    import urllib.request
    from missing_middleware.tod import case_nyc as N
    D = pd.read_parquet(PATHS['lots'])
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
    D.to_parquet(PATHS['lots'])
    print(D.groupby("city")[["bldg_to_land", "year_built"]].agg(lambda s: s.notna().mean()).round(2).to_string())


BPS_NAME = {"New York": ("36", "New York"), "Philadelphia": ("42", "Philadelphia"), "Charlotte": ("37", "Mecklenburg County"),
            "Saint Paul": ("27", "St. Paul"), "Seattle": ("53", "Seattle"), "Los Angeles": ("06", "Los Angeles"),
            "Chicago": ("17", "Chicago"), "Madison": ("55", "Madison"), "Bellevue": ("53", "Bellevue"),
            "Madison placebo": ("55", "Madison"), "Milwaukee placebo": ("55", "Milwaukee"),
            "Columbus placebo": ("39", "Columbus"), "Kansas City placebo": ("29", "Kansas City")}


def cost_per_home(city: str, year: int) -> float:
    """Census permit survey: construction value per home in buildings of 5+ homes, that city and year (else the
    nearest year with at least 20 such homes)."""
    st, name = BPS_NAME[city]
    best = None
    if FIT.get("item37"):   # item 43: median over the 5 years around, each with at least 20 such homes (one-year values swing)
        names = (["Bronx borough", "Brooklyn borough", "Manhattan borough", "Queens borough", "Staten Island borough"]
                 if city == "New York" else [name])   # the permit survey reports New York City by borough
        vals = []
        for y in range(year - 2, year + 3):
            uu = vv = 0.0
            for reg in ("mw", "ne", "so", "we"):
                f = RAW / "tod_control_cities" / "bps" / f"{reg}{y}a.txt"
                if not f.exists():
                    continue
                lines = f.read_text(errors="replace").splitlines()
                h2 = [c.strip() for c in lines[1].split(",")]
                ni = h2.index("Name")
                for line in lines[2:]:
                    c = line.split(",")
                    if len(c) > ni + 13 and c[1].strip().zfill(2) == st and c[ni].strip() in names:
                        uu += float(c[ni + 11] or 0)
                        vv += float(c[ni + 12] or 0)
            if uu >= 20:
                vals.append(vv / uu)
        if vals:
            return float(np.median(vals))
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


# CPI-U annual averages (BLS CUUR0000SA0); 2009 on as in allvars.CPI_U (plan section 9, item 25.5)
CPI_U = {2001: 177.1, 2002: 179.9, 2003: 184.0, 2004: 188.9, 2005: 195.3, 2006: 201.6, 2007: 207.342, 2008: 215.303}


def cost_2024(D: pd.DataFrame) -> pd.Series:
    from missing_middleware.tod.allvars import CPI_U as C2
    cpi = {**CPI_U, **C2}
    yr = (D["eff_year"] - 1).clip(lower=min(cpi), upper=2024).astype(int)
    return D["cost_per_home"] * cpi[2024] / yr.map(cpi)


def dedupe_lots(D: pd.DataFrame) -> pd.DataFrame:
    """Plan section 9, item 32.6: stacked lots at one point within one reform become one row (keeping the copy with
    the most homes); the weight is 1 / (number of reforms whose table holds that point)."""
    key = D["city"] + "|" + D["x5070"].round(1).astype(str) + "|" + D["y5070"].round(1).astype(str)
    D = D.assign(_k=key, _h=D["units_after"] + D["units_before"])
    D = D.sort_values("_h", ascending=False).drop_duplicates(["_k", "unit"]).sort_index()
    D["w"] = 1.0 / D["_k"].map(D.groupby("_k")["unit"].nunique())
    if "sample_w" in D:   # item 46.3: sampled lots stand for the lots not drawn
        D["w"] = D["w"] * D["sample_w"].fillna(1.0)
    return D.drop(columns=["_k", "_h"])


def five_year_basis(D: pd.DataFrame) -> pd.DataFrame:
    """Homes before and after on a 5-year basis (plan section 9, item 24)."""
    by = (D["eff_year"] - D["window_first"]).clip(lower=1)
    ay = np.where(D["city"] == "Madison", 3, (D["window_last"] - D["eff_year"]).clip(lower=1))
    return D.assign(ub5=D["units_before"] * 5 / by, ua5=D["units_after"] * 5 / ay)


def features(D: pd.DataFrame, after_rules: bool) -> pd.DataFrame:
    X = pd.DataFrame(index=D.index)
    X["log_acres"] = np.log(D["acres"].clip(lower=0.005))
    X["log_width"] = np.log(D["width_m"].clip(lower=1))
    X["homes_on_lot"] = np.log1p(D["homes_on_lot"].fillna(-1).clip(lower=0))
    X["homes_missing"] = D["homes_on_lot"].isna().astype(float)
    X["log_dist_station"] = np.log1p(D["dist_station_m"])
    if FIT.get("item46"):   # item 46: cities with no rail or rapid stop get -1 and their own flag, not a filled median
        X["no_rail_rapid"] = D["dist_station_m"].isna().astype(float)
        X["log_dist_station"] = X["log_dist_station"].fillna(-1.0)
    # Unit-free density traits (plan section 9, item 12): cities record allowed density in different units
    # (floor area ratio; Charlotte feet of height; Philadelphia and Los Angeles an ordering), so the raw level is
    # replaced by its rank within the city, and the change by the relative change, only where a real FAR exists.
    far_city = D["city"].isin(FAR_CITIES)
    lb = D["far_before"].astype(float)
    grp = D["city"] + ("|wi" * D["is_wi"].fillna(0).astype(int) if "is_wi" in D else "")   # item 25.3
    X["level_rank_in_city"] = lb.groupby(grp).rank(pct=True).fillna(0.5)
    up = D["treated"] == 1
    fg = D["far_gain"].astype(float)
    rel = (fg / lb.where(lb > 0)).where(far_city & up)
    X["upzoned"] = up.astype(float) if after_rules else 0.0
    X["rel_gain"] = rel.clip(0, 10).fillna(0) if after_rules else 0.0
    if FIT.get("item34"):   # item 34.3: "known" only where the before level is positive and the gain finite
        known = far_city & up & (lb > 0) & np.isfinite(fg)
        X["rel_gain_known"] = known.astype(float) if after_rules else 0.0
        now = (lb + (fg.fillna(0) if after_rules else 0.0))
        X["far_now"] = now.where(far_city & np.isfinite(now))
        if FIT.get("item37"):   # item 45.1: no floor area ratio (other cities; Seattle single-family's 0) -> -1, not a median
            X["far_now"] = X["far_now"].where(far_city & (lb > 0) & np.isfinite(now), -1.0)
            X["far_known"] = (far_city & (lb > 0)).astype(float)
    else:
        X["rel_gain_known"] = (far_city & up).astype(float) if after_rules else 0.0
        X["far_now"] = (lb + (D["far_gain"].fillna(0) if after_rules else 0.0)).where(far_city)   # FAR cities only
    X["far_known"] = far_city.astype(float)
    X["built_before"] = D["built_before"]
    if FIT.get("item34"):   # item 35.2: homes built nearby per before year (Saint Paul has 1 before year, others 6)
        by = (D["eff_year"] - D["window_first"]).clip(lower=1) if "window_first" in D else pd.Series(6.0, index=D.index)
        X["log_near_before"] = np.log1p(D["near_units_before"] / by.fillna(6.0))
    else:
        X["log_near_before"] = np.log1p(D["near_units_before"])
    if FIT.get("item37"):   # item 44.2: no hard-coded fallbacks; missing values are filled once, from training medians
        X["log_rent"] = np.log(D["rent"].clip(lower=100))
        X["log_value"] = np.log(D["home_value"].clip(lower=10000))
        X["log_income"] = np.log(D["income"].clip(lower=5000))
    else:
        X["log_rent"] = np.log(D["rent"].clip(lower=100)).fillna(np.log(1000))
        X["log_value"] = np.log(D["home_value"].clip(lower=10000)).fillna(np.log(200000))
        X["log_income"] = np.log(D["income"].clip(lower=5000)).fillna(np.log(50000))
    X["soft_site"] = np.log1p(D["bldg_to_land"].clip(lower=0)).fillna(0) if "bldg_to_land" in D else 0.0
    X["soft_missing"] = D["bldg_to_land"].isna().astype(float) if "bldg_to_land" in D else 1.0
    age = (D["eff_year"] - D["year_built"]) if "year_built" in D else pd.Series(np.nan, index=D.index)
    X["age"] = age.clip(0, 200).fillna(-1)
    X["rent_to_cost"] = ((D["rent"] if FIT.get("item37") else D["rent"].fillna(1000)) * 12 / 0.05) / cost_2024(D)   # 25.5; 44.2
    sqft = (X["far_now"].fillna(0) * D["acres"] * 43560)
    allowed = sqft / 1000.0
    have = D["census_homes"].fillna(0) if (FIT.get("item37") and "census_homes" in D) else D["homes_on_lot"].fillna(0)   # 45.2
    X["pays_room"] = np.log1p((allowed.where(X["far_now"] > 0, 0) - have).clip(lower=0)) * X["rent_to_cost"]
    if "in_reform" in D:   # plan section 9, item 15
        X["in_reform"] = D["in_reform"].astype(float)
    if "lot_group" in D:   # plan section 9, item 16: what the reform did to the lot, and the reform's mix
        # item 17: a group found in fewer than 3 non-holdout cities is pooled into one "rare" group
        tr = ~D["city"].isin(HOLD)
        seen = D[tr].groupby("lot_group")["city"].nunique()
        common = [g for g in LOT_GROUPS if seen.get(g, 0) >= 3]
        X["group_rare"] = (~D["lot_group"].isin(common)).astype(float)
        X["reform_share_rare"] = 0.0
        for gname in LOT_GROUPS:
            sh = D[f"share_{gname}"] if f"share_{gname}" in D else None
            if gname in common:
                X[f"group_{gname}"] = (D["lot_group"] == gname).astype(float)
                if sh is not None:
                    X[f"reform_share_{gname}"] = sh
            elif sh is not None:
                X["reform_share_rare"] = X["reform_share_rare"] + sh
    if "lot_market_value" in D and FIT.get("land"):   # docs/tod/LAND_VALUE_PLAN.md section 2: does a project pay for itself?
        tr_b = (~D["city"].isin(HOLD)) & (D["units_after"] > 0)
        per_acre = float(np.nanquantile(D.loc[tr_b, "units_after"] / D.loc[tr_b, "acres"].clip(lower=0.01), 0.99))
        lvpa = (D["lot_market_value"] / D["acres"].clip(lower=0.01))
        lvpa = lvpa.fillna(lvpa.groupby(D["city"]).transform("median")).fillna(lvpa.median())
        buy = lvpa * D["acres"].clip(lower=0.01)
        cost = cost_2024(D)
        cost = cost.fillna(cost.median())
        price = D["rent"].fillna(1000) * 12 / 0.05

        def margin(after: bool):
            far = (lb + (D["far_gain"].fillna(0) if after else 0.0)).where(far_city)
            homes = (far * D["acres"] * 43560 / 1000).where(far_city, D["acres"] * per_acre).fillna(0)
            return homes * (price - cost) - buy
        m_old, m_now = margin(False), margin(after_rules)
        slog = lambda v: np.sign(v) * np.log1p(np.abs(v))  # noqa: E731
        X["pays"] = (m_now > 0).astype(float)
        X["flips_to_pays"] = ((m_now > 0) & (m_old <= 0)).astype(float)
        X["margin_per_acre"] = slog(m_now / D["acres"].clip(lower=0.01))
        X["margin_change_per_acre"] = slog((m_now - m_old) / D["acres"].clip(lower=0.01))
        X["log_lot_value_per_acre"] = np.log1p(lvpa)
        X["lot_value_missing"] = D["lot_value_missing"]
        X["assessed_not_market"] = D["assessed_not_market"]
    if "rezoned_later" in D and (not FIT.get("item32") or FIT.get("with_rezoned_later") or FIT.get("item37")):   # 31; 32.3; 39.1
        X["rezoned_later"] = D["rezoned_later"].astype(float)
    if FIT.get("item37"):   # item 39.2: no-reform (placebo) lots carry their own trait
        X["no_reform"] = (D["placebo"].fillna(0) if "placebo" in D else pd.Series(0.0, index=D.index)).astype(float)
    if "census_homes" in D:
        X["log_census_homes"] = np.log1p(D["census_homes"].clip(lower=0))
    if not FIT.get("item25"):
        for u in ("res", "com", "ind", "mixed"):
            X[f"use_{u}"] = (D["use"].astype(str) == u).astype(float)
    else:   # item 25.2: use traits dropped; 25.6: traits dated after the reform flagged
        X["traits_after_reform"] = (D["eff_year"] <= 2009).astype(float)
    if "share_upzoned_half_mile" in D:
        X["share_upzoned_half_mile"] = D["share_upzoned_half_mile"]
        X["log_stops_1mile"] = np.log1p(D["stops_1mile"])
    if FIT.get("item32"):   # item 32.5: traits known only in some cities act as city labels
        X = X.drop(columns=[c for c in ("homes_on_lot", "homes_missing", "soft_site", "soft_missing", "age") if c in X])
    if FIT.get("item46"):   # item 46.5: permit-survey cost is not comparable across cities
        X = X.drop(columns=[c for c in ("rent_to_cost", "pays_room") if c in X])
    X = X.replace([np.inf, -np.inf], np.nan)
    if FIT.get("item25"):   # item 25.8: fill values from non-holdout case-city rows only
        ref = ~D["city"].isin(HOLD) & ~(D["is_wi"].fillna(0).astype(bool) if "is_wi" in D else False)
        return X.fillna(X[ref].median())
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
    D = pd.read_parquet(FIT["lots"])
    if ROBUST["drop_largest"]:   # plan section 9, item 19: each city's largest project (lot with most homes after) out
        D = D.drop(D.groupby("city")["units_after"].idxmax().values).reset_index(drop=True)
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
        t = d[d.treated == 1]
        c = d[(d.treated == 0) & (d["comparison_eligible"] == 1)] if "comparison_eligible" in d else d[d.treated == 0]   # items 15-16
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
            m1 = GradientBoostingClassifier(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=SEED["v"])
            m1.fit(Xa.loc[tr], y1[tr], sample_weight=D.loc[tr, "w"])
            p = lambda X: m1.predict_proba(X)[:, 1]  # noqa: E731
            b = (y1[tr] == 1)
            m2 = GradientBoostingRegressor(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=SEED["v"])
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
    tag = ("_runD_allvars" if allvars else "_runD") + FIT["suffix"]
    # Which lot traits the boosted "builds" model leans on (fitted on all fold cities; permutation on the holdouts)
    from sklearn.inspection import permutation_importance
    tr = D.index[D["city"].isin(cities)]
    m1 = GradientBoostingClassifier(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=SEED["v"])
    m1.fit(Xa.loc[tr], y1[tr], sample_weight=D.loc[tr, "w"])
    ho = D.index[D["city"].isin(HOLD)]
    pi = permutation_importance(m1, Xa.loc[ho], y1[ho], scoring="roc_auc", n_repeats=5, random_state=SEED["v"],
                                sample_weight=D.loc[ho, "w"].values)
    imp = pd.DataFrame({"trait": Xa.columns, "split_importance": m1.feature_importances_,
                        "holdout_auc_drop_when_shuffled": pi.importances_mean}).sort_values("holdout_auc_drop_when_shuffled", ascending=False)
    imp.round(4).to_csv(REFERENCE / f"tod_lot_model_importance{tag}.csv", index=False)
    print(imp.round(4).to_string())
    tag = ("_runD_allvars" if allvars else "_runD") + FIT["suffix"]
    E.round(3).to_csv(REFERENCE / f"tod_lot_model_by_city{tag}.csv", index=False)
    S.round(4).to_csv(REFERENCE / f"tod_lot_model_results{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(E.round(2).to_string())
    print(S.round(3).T.to_string())


def add_saturation() -> None:
    """Plan section 9, item 11: share of upzoned land within 1/2 mile (same case), and stops within 1 mile."""
    from scipy.spatial import cKDTree
    D = pd.read_parquet(PATHS['lots'])
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
    D.to_parquet(PATHS['lots'])
    print(D.groupby(["city", "treated"])[["share_upzoned_half_mile", "stops_1mile"]].median().round(3).to_string())


# Rapid-bus stations missing from the rail-only stop list (plan section 9, item 14). Federal National Transit Map,
# Los Angeles Metro (NTD 90154) G Line busway stations; Madison's rapid stops come from reference/tod_stops.csv.
G_LINE = ("North Hollywood Station", "Laurel Canyon Station", "Valley College Station", "Woodman Station",
          "Sepulveda Station", "Woodley Station", "Balboa Station", "Reseda Station", "Tampa Station",
          "Pierce College Station", "De Soto Station", "Canoga Station", "Warner Center Transit Hub", "Sherman Way Station",
          "Roscoe Station", "Nordhoff Station", "Chatsworth Station")


def qualifying_stops_5070() -> np.ndarray:
    from scripts.fetch_tod_transit import NTM_LAYERS, ntm_query
    s_ = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    lat, lon = list(s_.stop_lat), list(s_.stop_lon)
    cache = RAW / "tod_census_cases" / "ntm_la_g_line.json"
    if not cache.exists():
        names = ",".join("'" + n + "'" for n in G_LINE)
        f, _ = ntm_query(NTM_LAYERS["stops"], f"ntd_id='90154' AND stop_name IN ({names})")
        cache.write_text(json.dumps([x["attributes"] for x in f]))
    g = pd.DataFrame(json.load(open(cache)))
    print("G Line stations found:", g["stop_name"].nunique(), "of", len(G_LINE), flush=True)
    w = pd.read_csv(REFERENCE / "tod_stops.csv")
    w = w[(w["flag_a_rapid"] == 1)]   # Wisconsin rail and rapid stops (Madison; Milwaukee for the item 37 placebo)
    lat += list(g.stop_lat) + list(w.lat)
    lon += list(g.stop_lon) + list(w.lon)
    p = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(5070)
    return np.c_[p.x, p.y]


def half_mile() -> None:
    """Plan section 9, item 14: rail plus rapid-bus stops; keep lots within 1/2 mile; recompute the stop traits."""
    from scipy.spatial import cKDTree
    D = pd.read_parquet(PATHS['lots'])
    st = cKDTree(qualifying_stops_5070())
    xy = D[["x5070", "y5070"]].to_numpy()
    D["dist_station_m"] = st.query(xy)[0]
    D["stops_1mile"] = [len(n) for n in st.query_ball_point(xy, r=1609)]
    nr = D["city"].isin(NO_RAIL)   # item 46: no rail or rapid stop open in their windows
    D.loc[nr, "dist_station_m"], D.loc[nr, "stops_1mile"] = np.nan, 0
    before = D.groupby(["city", "treated"]).size()
    if not FIT.get("item37"):
        D = D[D["dist_station_m"] <= 805].copy()   # item 14; item 37.1 stops trimming
    share = np.full(len(D), np.nan)
    D = D.reset_index(drop=True)
    for unit, ix in D.groupby("unit").groups.items():
        d = D.loc[ix]
        xy_ = d[["x5070", "y5070"]].to_numpy()
        nb = cKDTree(xy_).query_ball_point(xy_, r=805)
        ac, tr = d["acres"].to_numpy(), (d["treated"].to_numpy() == 1)
        share[D.index.get_indexer(ix)] = [ac[n][tr[n]].sum() / ac[n].sum() if len(n) else np.nan for n in nb]
    D["share_upzoned_half_mile"] = share
    D.to_parquet(PATHS['half'])
    after = D.groupby(["city", "treated"]).size()
    t = pd.DataFrame({"lots_before": before, "lots_kept": after}).fillna(0)
    t["median_dist_m"] = D.groupby(["city", "treated"])["dist_station_m"].median()
    t["median_share_upzoned"] = D.groupby(["city", "treated"])["share_upzoned_half_mile"].median()
    print(t.round(2).to_string())


def census_homes() -> None:
    """Plan section 9, item 15: 2010 census block homes shared among each block's lots in the table by lot area."""
    D = pd.read_parquet(PATHS["lots"])
    D["census_homes"] = np.nan
    pts = gpd.GeoDataFrame(D[["city"]].copy(), geometry=gpd.points_from_xy(D["x5070"], D["y5070"]), crs=5070)
    for city, st in STATE.items():
        ix = D.index[D["city"] == city]
        if not len(ix):
            continue
        src = sorted(RAW.rglob(f"tabblock2010_{st}_pophu.zip"))[0]
        b = gpd.read_file(src, bbox=tuple(pts.loc[ix].to_crs(4269).total_bounds), columns=["BLOCKID10", "HOUSING10"]).to_crs(5070)
        j = gpd.sjoin(pts.loc[ix, ["geometry"]], b[["BLOCKID10", "HOUSING10", "geometry"]], predicate="within", how="left")
        j = j[~j.index.duplicated()]
        blk = j["BLOCKID10"]
        # lots repeated across overlapping cases share one copy of the block's homes per case unit
        grp = D.loc[ix, "unit"].astype(str) + "|" + blk.astype(str)
        share = D.loc[ix, "acres"] / D.loc[ix, "acres"].groupby(grp).transform("sum")
        D.loc[ix, "census_homes"] = (j["HOUSING10"].astype(float) * share).values
        print(city, src.name, "lots matched", int(blk.notna().sum()), "of", len(ix), flush=True)
    D.to_parquet(PATHS["lots"])
    print(D.groupby("city")["census_homes"].describe()[["mean", "50%", "max"]].round(2).to_string())


LV = RAW / "tod_land_values"


def _nearest_value(D: pd.DataFrame, ix, lat, lon, val, max_m: float) -> pd.Series:
    from scipy.spatial import cKDTree
    pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(5070)
    ok = np.isfinite(pts.x.values) & np.isfinite(pts.y.values)
    t = cKDTree(np.c_[pts.x.values[ok], pts.y.values[ok]])
    d, j = t.query(D.loc[ix, ["x5070", "y5070"]].to_numpy())
    v = np.asarray(val)[ok][np.minimum(j, ok.sum() - 1)]
    return pd.Series(np.where(d <= max_m, v, np.nan), index=ix)


def _pin_in_polygon(D: pd.DataFrame, ix, polys, col: str) -> pd.Series:
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(D.loc[ix, "x5070"], D.loc[ix, "y5070"]), index=ix, crs=5070)
    j = gpd.sjoin(pts, polys[[col, "geometry"]].to_crs(5070), predicate="within", how="left")
    return j[~j.index.duplicated()][col].reindex(ix)


def land_values() -> None:
    """Lot market value before each reform (docs/tod/LAND_VALUE_PLAN.md section 3 and section 8)."""
    import zipfile
    D = pd.read_parquet(PATHS["half"])
    mv = pd.Series(np.nan, index=D.index)
    src = pd.Series("missing", index=D.index, dtype=object)
    # New York: assessed / Department of Finance class ratio (6% class 1 = 1-3 family homes; 45% otherwise)
    ix = D.index[D["city"] == "New York"]
    av = D.loc[ix, "total_value"].fillna(D.loc[ix, "land_value"])
    cls1 = (D.loc[ix, "use"].astype(str) == "res") & (D.loc[ix, "homes_on_lot"].fillna(9) <= 3)
    mv[ix] = av / np.where(cls1, 0.06, 0.45)
    src[ix] = "nyc_pluto_assessed_over_class_ratio"
    # Chicago: Cook County 2012 assessed / level (10% residential, 25% commercial and industrial)
    ix = D.index[D["city"] == "Chicago"]
    mv[ix] = D.loc[ix, "total_value"] / np.where(D.loc[ix, "use"].astype(str).isin(["com", "ind"]), 0.25, 0.10)
    src[ix] = "cook_2012_assessed_over_level"
    # King County: appraised land + improvements, tax year = reform year (values from 1 January of the year before)
    if (LV / "king_value_history.zip").exists():
        z = zipfile.ZipFile(LV / "king_value_history.zip")
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        years = set(D.loc[D["city"].isin(["Seattle", "Bellevue"]), "eff_year"].astype(int))
        parts = []
        for ch in pd.read_csv(z.open(name), dtype={"Major": str, "Minor": str}, usecols=["Major", "Minor", "TaxYr", "ApprLandVal", "ApprImpsVal"],
                              chunksize=2_000_000, encoding="latin-1"):
            parts.append(ch[ch["TaxYr"].isin(years)])
        kv = pd.concat(parts)
        kv["pin"] = kv["Major"].str.zfill(6) + kv["Minor"].str.zfill(4)
        kv["v"] = kv["ApprLandVal"] + kv["ApprImpsVal"]
        kv = kv.groupby(["pin", "TaxYr"])["v"].max()
        for city, f, col in (("Seattle", RAW / "tod_cases" / "seattle" / "parcels_2010.geojson", "PIN"),
                             ("Bellevue", RAW / "tod_cases" / "bellevue" / "parcels.geojson", "ParcelAFN")):
            ix = D.index[D["city"] == city]
            pins = _pin_in_polygon(D, ix, gpd.read_file(f), col).astype(str).str.zfill(10)
            yrs = D.loc[ix, "eff_year"].astype(int)
            mv[ix] = [kv.get((p, y), np.nan) for p, y in zip(pins, yrs)]
            src[ix] = "king_county_appraised"
    # Philadelphia: certified market value for the reform's tax year, 2016 on (section 8, item 1)
    if (LV / "philadelphia_assessments.csv").exists() and (LV / "philadelphia_opa_points.csv").exists():
        ix = D.index[(D["city"] == "Philadelphia") & (D["eff_year"] >= 2016)]
        pp = pd.read_csv(LV / "philadelphia_opa_points.csv", dtype={"parcel_number": str}).dropna()
        pid = _nearest_value(D, ix, pp["lat"].values, pp["lon"].values, pp["parcel_number"].values, 30.0)
        a = pd.read_csv(LV / "philadelphia_assessments.csv", usecols=["parcel_number", "year", "market_value"], dtype={"parcel_number": str})
        a = a.groupby(["parcel_number", "year"])["market_value"].max()
        mv[ix] = [a.get((p, int(y)), np.nan) if isinstance(p, str) else np.nan for p, y in zip(pid, D.loc[ix, "eff_year"])]
        src[ix] = "philadelphia_certified_market"
    # Los Angeles: roll 2012, assessed (Proposition 13), flagged
    la = [f for f in LV.glob("la_roll2012_*.json")]
    if la:
        r = pd.concat([pd.DataFrame(json.load(open(f))) for f in la]).dropna(subset=["CENTER_LAT", "CENTER_LON"])
        ix = D.index[D["city"] == "Los Angeles"]
        mv[ix] = _nearest_value(D, ix, r["CENTER_LAT"].values, r["CENTER_LON"].values, r["Roll_TotalValue"].values, 40.0)
        src[ix] = "la_roll2012_assessed_not_market"
    # Madison: Wisconsin statewide parcels V9 (2022 roll), estimated fair market value
    if (LV / "wi_parcels_v9_2023.zip").exists():
        ix = D.index[D["city"] == "Madison"]
        b = tuple(gpd.GeoSeries(gpd.points_from_xy(D.loc[ix, "x5070"], D.loc[ix, "y5070"]), crs=5070).to_crs(3071).total_bounds)
        w = gpd.read_file(f"/vsizip/{LV / 'wi_parcels_v9_2023.zip'}/V9.0.1_Wisconsin_Parcels_2023_10.3_Uncompressed.gdb",
                          layer="V901_WisconsinParcels_2023", bbox=b, columns=["ESTFMKVALUE", "TAXROLLYEAR"])
        mv[ix] = _pin_in_polygon(D, ix, w, "ESTFMKVALUE").astype(float)
        src[ix] = "wi_v9_est_fair_market"
    # Los Angeles: scale Proposition 13 assessed values to market by tract (LAND_VALUE_PLAN.md section 8, item 3)
    ix = D.index[(D["city"] == "Los Angeles") & mv.notna()]
    if len(ix) and "census_homes" in D:
        tract = D.loc[ix, "v_tract"] if "v_tract" in D else (D.loc[ix, "rent"].astype(str) + "|" + D.loc[ix, "home_value"].astype(str))
        res = D.loc[ix, "census_homes"].fillna(0) >= 1   # lots with homes (LA lots carry no use class)
        per_home = mv[ix] / D.loc[ix, "census_homes"].clip(lower=1)
        med = per_home[res].groupby(tract[res]).median()
        n = per_home[res].groupby(tract[res]).size()
        f = (D.loc[ix, "home_value"].groupby(tract).first() / med.where(n >= 5)).clip(1, 10)
        fac = tract.map(f)
        fac = fac.fillna(fac.median() if fac.notna().any() else 1.0)
        mv[ix] = mv[ix] * fac.values
        print("Los Angeles market factor: median", round(float(fac.median()), 2), "range", round(float(fac.min()), 2), "to", round(float(fac.max()), 2), flush=True)
    D["lot_market_value"] = mv.where(mv > 0)
    D["lot_value_source"] = src
    D["lot_value_missing"] = D["lot_market_value"].isna().astype(float)
    D["assessed_not_market"] = (src == "la_roll2012_assessed_not_market").astype(float)
    D.to_parquet(PATHS["half"])
    t = D.groupby("city").agg(lots=("acres", "size"), have_value=("lot_market_value", lambda v: v.notna().mean()),
                              median_value_per_acre=("lot_market_value", lambda v: (v / D.loc[v.index, "acres"]).median()))
    print(t.round(2).to_string())


def fix_density() -> None:
    """Plan section 9, item 26: homes on lots too small to hold them (> 500 per acre) move to the nearest big-enough
    lot of the same reform within 60 m."""
    from scipy.spatial import cKDTree
    D = pd.read_parquet(PATHS["half"])
    D["density_flag"] = 0.0
    moves = []
    for col in ("units_before", "units_after"):
        bad = D.index[(D[col] / D["acres"].clip(lower=0.001)) > 500]
        for unit, ix in pd.Series(bad, index=bad).groupby(D.loc[bad, "unit"]).groups.items():
            u = D.index[D["unit"] == unit]
            t = cKDTree(D.loc[u, ["x5070", "y5070"]].to_numpy())
            for i in ix:
                h = D.at[i, col]
                nb = [u[j] for j in t.query_ball_point(D.loc[i, ["x5070", "y5070"]].to_numpy(), r=60) if u[j] != i]
                ok = [j for j in nb if D.at[j, "acres"] * 500 >= h]
                if not ok:
                    D.at[i, "density_flag"] = 1.0
                    continue
                same = [j for j in ok if D.at[j, "lot_group"] == D.at[i, "lot_group"]]
                pool = same or ok
                d2 = ((D.loc[pool, "x5070"] - D.at[i, "x5070"]) ** 2 + (D.loc[pool, "y5070"] - D.at[i, "y5070"]) ** 2)
                j = d2.idxmin()
                D.at[j, col] += h
                D.at[i, col] = 0.0
                moves.append({"unit": unit, "column": col, "homes": h, "crosses_group": bool(D.at[j, "treated"] != D.at[i, "treated"])})
    D["builds_after"] = (D["units_after"] > 0).astype(float)
    D["built_before"] = (D["units_before"] > 0).astype(float)
    D.to_parquet(PATHS["half"])
    M = pd.DataFrame(moves)
    if len(M):
        M.groupby(["unit", "column", "crosses_group"])["homes"].sum().round(0).to_csv(REFERENCE / "tod_lot_model_density_moves.csv")
        print(M.groupby(["column", "crosses_group"])["homes"].agg(["size", "sum"]).to_string())
    print("lots left flagged:", int(D["density_flag"].sum()))


def recollect_item29() -> None:
    """Plan section 9, item 29: rebuild Chicago and Charlotte (take-up rezonings) and replace their rows."""
    frames, stops = [], {}
    for key, city in (("chicago", "Chicago"), ("charlotte", "Charlotte")):
        mod = importlib.import_module(f"missing_middleware.tod.case_{key}")
        with capture() as cap:
            ci, _ = mod.build()
        args, area = cap["uniform"][0]
        pts, pix = cap["locate"][-1]
        per = C.period_years(ci.effective_year, ci.first_year, ci.last_full_year)
        crs = str(args["parcels"].crs)
        stops.setdefault(crs, rail(args["parcels"].crs))
        f = lot_frame(city, key, args, area, _permits_from_points(pts, pix), per, stops[crs], ci.effective_year)
        print(city, f.groupby("lot_group").agg(lots=("acres", "size"), acres=("acres", "sum"), after=("units_after", "sum")).round(0).to_string(), flush=True)
        frames.append(f)
    D = pd.read_parquet(PATHS["lots"])
    keep = [c for c in frames[0].columns]
    D = pd.concat([D[~D["city"].isin(["Chicago", "Charlotte"])][[c for c in D.columns if c in keep]]] + frames, ignore_index=True)
    D = add_group_shares(D)
    D.to_parquet(PATHS["lots"])


PLUTO_VERSIONS = {2002: "02b", 2003: "03c", 2004: "04c", 2005: "05d", 2006: "06c", 2007: "07c", 2008: "08b", 2009: "09v1",
                  2010: "10v1", 2011: "11v1", 2012: "12v1", 2013: "13v1", 2014: "14v1", 2015: "15v1", 2016: "16v1",
                  2017: "17v1", 2018: "18v1"}


def spread_assembly() -> None:
    """Plan section 9, item 33: a New York lot's homes are shared over the day-one lots of the same reform that sit
    inside the tax lot that held the building in the first MapPLUTO release after the permit year."""
    import zipfile
    nyc_dir = RAW / "tod_cases" / "nyc"
    D = pd.read_parquet(PATHS["half"])
    D["assembled_site"] = 0.0
    ny = D.index[D["city"] == "New York"]
    pts = gpd.GeoSeries(gpd.points_from_xy(D.loc[ny, "x5070"], D.loc[ny, "y5070"]), index=ny, crs=5070)
    moved = {"units_before": 0.0, "units_after": 0.0}
    for col in ("units_before", "units_after"):
        src = [i for i in ny if D.at[i, col] > 0]
        jobs = []
        for i in src:
            yrs = []
            for part in str(D.at[i, "permit_years"]).split(";"):
                if ":" in part:
                    y = int(float(part.split(":")[0]))
                    after = y >= int(D.at[i, "eff_year"])
                    if after == (col == "units_after"):
                        yrs.append(y)
            y = max(yrs) if yrs else int(D.at[i, "eff_year"])
            jobs.append((i, min(max(y + 1, 2002), 2018)))
        byv = {}
        for i, y in jobs:
            byv.setdefault(PLUTO_VERSIONS[y], []).append(i)
        for v, idx in byv.items():
            z = zipfile.ZipFile(nyc_dir / f"mappluto_{v}.zip")
            shps = [n for n in z.namelist() if n.lower().endswith("mappluto.shp")]
            sp = pts.loc[idx]
            polys = []
            for n in shps:
                g = gpd.read_file(f"/vsizip/{nyc_dir / f'mappluto_{v}.zip'}/{n}", columns=[],
                                  bbox=tuple(sp.to_crs(2263).total_bounds))
                if len(g):
                    polys.append(g.to_crs(5070)[["geometry"]])
            if not polys:
                continue
            P = pd.concat(polys, ignore_index=True)
            P = gpd.GeoDataFrame(P, geometry="geometry", crs=5070)
            js = gpd.sjoin(gpd.GeoDataFrame(geometry=sp, crs=5070), P, predicate="within", how="inner")
            js = js[~js.index.duplicated()]
            for site, g in js.groupby("index_right"):
                poly = P.geometry.iloc[site]
                for i in g.index:
                    u = D.at[i, "unit"]
                    sib = D.index[(D["unit"] == u) & (D["treated"] == D.at[i, "treated"])]   # item 37.5: within the group
                    sib = sib[pts.reindex(sib).within(poly).fillna(False).values]
                    if len(sib) <= 1:
                        continue
                    h = D.at[i, col]
                    a = D.loc[sib, "acres"].clip(lower=0.001)
                    D.at[i, col] -= h
                    D.loc[sib, col] += h * a / a.sum()
                    D.loc[sib, "assembled_site"] = 1.0
                    moved[col] += h * (1 - a.get(i, 0) / a.sum())
        print(col, "homes spread to other day-one lots:", round(moved[col]), flush=True)
    D["builds_after"] = (D["units_after"] > 0).astype(float)
    D["built_before"] = (D["units_before"] > 0).astype(float)
    D.to_parquet(PATHS["half"])
    print("lots marked part of an assembled site:", int(D["assembled_site"].sum()))


PLACEBO = {"Madison placebo": 2017, "Milwaukee placebo": 2019, "Columbus placebo": 2017, "Kansas City placebo": 2012}   # 37.3, 46
NO_RAIL = ("Columbus placebo", "Kansas City placebo")   # item 46: no rail or rapid-bus stop open in their windows


def add_placebo() -> None:
    """Plan section 9, item 37.3: no-reform lots (Madison outside its 2023 overlay; Milwaukee), law-area lots of the
    Wisconsin station-area build, with homes in 6 pretend-before and 6 pretend-after years. treated = 0 everywhere."""
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("run_tod_lot_model_wisconsin", ROOT / "scripts" / "run_tod_lot_model_wisconsin.py")
    W = ilu.module_from_spec(spec)
    spec.loader.exec_module(W)
    from missing_middleware.tod import madison_test as MT
    S = W._load("build_tod_station_areas")
    stops = S.stop_points()
    frames = []
    for city, yr in PLACEBO.items():
        years = list(range(yr - 6, yr + 6))
        W.BEFORE = years
        if city.startswith("Madison"):
            MT.BEFORE, MT.SHOWN = years[:6], [years[-1]]
            rules = S.read_rules("madison")
            p = S.load_madison({r["district"] for r in rules})
            p = p[~p["in_overlay"].astype(bool)]          # outside the 2023 overlay
            built = W.built_points_madison(p.crs)
        else:
            rules = S.read_rules("milwaukee")
            p = S.load_milwaukee()
            built = W.built_points_milwaukee(p.crs)
        c = S.compute(p, city.split()[0] + " city", rules, stops)
        c = gpd.GeoDataFrame(c, geometry="geometry", crs=p.crs)
        d = pd.DataFrame(index=c.index)
        d["city"], d["unit"], d["eff_year"] = city, city.lower().replace(" ", "_"), yr
        p5070 = gpd.GeoSeries(c["pt"].values, crs=p.crs).to_crs(5070)
        d["x5070"], d["y5070"] = p5070.x.values, p5070.y.values
        d["width_m"] = W.width(c.geometry)
        d["acres"] = c["acres"].values
        el = c["eligible"].astype(bool)
        d["treated"], d["in_reform"], d["comparison_eligible"] = 0.0, 0.0, el.astype(float).values
        cls = c["use_class"].astype(str).str.lower()
        g = pd.Series("other_not_eligible", index=c.index, dtype=object)
        g[el] = "comparison_eligible"
        g[~el & cls.str.contains("industr")] = "comparison_industrial"
        g[~el & cls.str.contains("institution|park|govern|exempt")] = "comparison_campus_or_park"
        d["lot_group"] = g.values
        sq = float(c["sqft_per_home"].iloc[0])
        d["far_before"] = (c["current_allowed_homes"] * sq / (c["acres"] * 43560)).values
        d["far_gain"] = 0.0
        d["level_source"], d["level_flag"], d["rezoned_later"] = "homes per acre", "", 0.0
        d["use"] = "unknown"
        b = built.to_crs(5070)
        b = b[b["year"].isin(years)]
        j = gpd.sjoin(b, c[["geometry"]].to_crs(5070), predicate="within")
        bb = j[j["year"] < yr].groupby("index_right")["units"].sum()
        aa = j[j["year"] > yr].groupby("index_right")["units"].sum()   # after = the 5 years after the pretend year, as in the cases
        d["units_before"] = bb.reindex(d.index).fillna(0).values
        d["units_after"] = aa.reindex(d.index).fillna(0).values
        yrs = j.groupby(["index_right", "year"])["units"].sum().reset_index()
        yrs["s"] = yrs["year"].astype(int).astype(str) + ":" + yrs["units"].round(0).astype(int).astype(str)
        d["permit_years"] = yrs.groupby("index_right")["s"].agg(";".join).reindex(d.index).fillna("").values
        d["window_first"], d["window_last"] = years[0], years[-1]
        d["builds_after"] = (d["units_after"] > 0).astype(float)
        d["built_before"] = (d["units_before"] > 0).astype(float)
        from scipy.spatial import cKDTree
        bb_pts = b[b["year"] < yr]
        t = cKDTree(np.c_[bb_pts.geometry.x, bb_pts.geometry.y]) if len(bb_pts) else None
        d["near_units_before"] = ([float(bb_pts["units"].values[n].sum()) for n in t.query_ball_point(np.c_[d.x5070, d.y5070], r=150)]
                                  if t is not None else 0.0)
        d["placebo"] = 1.0
        print(city, len(d), "lots; homes before", int(d.units_before.sum()), "after", int(d.units_after.sum()), flush=True)
        frames.append(d.reset_index(drop=True))
    D = pd.read_parquet(PATHS["lots"])
    D = D[~D["city"].isin(list(PLACEBO))]
    D = add_group_shares(pd.concat([D] + frames, ignore_index=True))
    D.to_parquet(PATHS["lots"])


def add_placebo_us() -> None:
    """Plan section 9, item 46: Columbus (pretend 2017) and Kansas City (pretend 2012) no-reform lots, a 20% random
    sample of each city's lots (sample weight 5), homes from new-construction permits with unit counts."""
    from scipy.spatial import cKDTree
    src = RAW / "tod_placebo_cities"
    rng = np.random.default_rng(20261031)
    frames = []
    # --- Columbus
    p = gpd.read_file(src / "columbus_parcels.geojson")
    p = p[p.geometry.notna()].drop_duplicates("PARCELID")
    p["acres"] = pd.to_numeric(p["ACRES"], errors="coerce")
    p["cls"] = p["CLASSCD"].astype(str).str[:1]
    q = gpd.read_file(src / "columbus_permits.geojson")
    sub, cat = q["B1_PER_SUB_TYPE"].astype(str), q["B1_PER_CATEGORY"].astype(str)
    new = ((sub == "New Construction") & cat.isin(["Structure", "Structural"])) | (cat == "New Structure")
    q = q[new & q.geometry.notna()].copy()
    q["year"] = pd.to_numeric(q["ISSUED_YEAR"], errors="coerce")
    q["units"] = pd.to_numeric(q["UNITS"], errors="coerce")
    frames.append(_placebo_frame("Columbus placebo", 2017, p, q, lambda c: np.where(c == "I", "comparison_industrial",
                  np.where(c == "E", "comparison_campus_or_park", "comparison_eligible")), rng))
    # --- Kansas City
    k = gpd.read_file(src / "kc_parcels.geojson")
    k = k[k.geometry.notna()].drop_duplicates("kivapin")
    k["acres"] = pd.to_numeric(k["shape_area"], errors="coerce") / 43560.0
    k["cls"] = pd.to_numeric(k["landusecode"], errors="coerce").fillna(0).astype(int).astype(str).str[:1]
    r = pd.DataFrame(json.load(open(src / "kc_permits.json")))
    r["year"] = pd.to_numeric(r["year"], errors="coerce")
    r["units"] = pd.to_numeric(r["units"], errors="coerce")
    r = r[(r["units"] > 0)]
    pts = k.set_index("kivapin").geometry.representative_point()
    r = r[r["pin"].isin(pts.index)]
    r = gpd.GeoDataFrame(r, geometry=pts.reindex(r["pin"]).values, crs=k.crs)
    frames.append(_placebo_frame("Kansas City placebo", 2012, k, r, lambda c: np.where(c == "4", "comparison_industrial",
                  "comparison_eligible"), rng))
    D = pd.read_parquet(PATHS["lots"])
    D = D[~D["city"].isin(["Columbus placebo", "Kansas City placebo"])]
    D = add_group_shares(pd.concat([D] + frames, ignore_index=True))
    D.to_parquet(PATHS["lots"])


def _placebo_frame(city: str, yr: int, p, q, group_of, rng) -> pd.DataFrame:
    from scipy.spatial import cKDTree
    first = 2006 if city.startswith("Kansas") else yr - 6
    last = 2015 if city.startswith("Kansas") else yr + 5
    p = p.to_crs(5070)
    pts = p.geometry.representative_point()
    q = q.to_crs(5070)
    q = q[q["year"].between(first, last) & (q["units"] > 0)]
    j = gpd.sjoin(q[["year", "units", "geometry"]], p[["geometry"]], predicate="within", how="inner")
    j = j[~j.index.duplicated()]
    bb = j[j["year"] < yr].groupby("index_right")["units"].sum()
    aa = j[j["year"] > yr].groupby("index_right")["units"].sum()
    take = rng.random(len(p)) < 0.20                 # item 46.3: 20% random sample of all city lots, weight 5
    p, pts = p[take], pts[take]
    d = pd.DataFrame(index=p.index)
    d["city"], d["unit"], d["eff_year"] = city, city.lower().replace(" ", "_"), yr
    d["x5070"], d["y5070"] = pts.x.values, pts.y.values
    d["width_m"] = [_mrr_width(g) for g in p.geometry]
    d["acres"] = p["acres"].values
    d["treated"], d["in_reform"], d["sample_w"] = 0.0, 0.0, 5.0
    d["lot_group"] = group_of(p["cls"].values)
    d["comparison_eligible"] = (d["lot_group"] == "comparison_eligible").astype(float)
    d["far_before"], d["far_gain"] = np.nan, 0.0
    d["level_source"], d["level_flag"], d["rezoned_later"], d["use"] = "none", "", 0.0, "unknown"
    d["units_before"] = bb.reindex(d.index).fillna(0).values
    d["units_after"] = aa.reindex(d.index).fillna(0).values
    yrs = j.groupby(["index_right", "year"])["units"].sum().reset_index()
    yrs["s"] = yrs["year"].astype(int).astype(str) + ":" + yrs["units"].round(0).astype(int).astype(str)
    d["permit_years"] = yrs.groupby("index_right")["s"].agg(";".join).reindex(d.index).fillna("").values
    d["window_first"], d["window_last"] = first, last
    d["builds_after"] = (d["units_after"] > 0).astype(float)
    d["built_before"] = (d["units_before"] > 0).astype(float)
    bq = q[q["year"] < yr]
    t = cKDTree(np.c_[bq.geometry.x, bq.geometry.y]) if len(bq) else None
    d["near_units_before"] = ([float(bq["units"].values[n].sum()) for n in t.query_ball_point(np.c_[d.x5070, d.y5070], r=150)]
                              if t is not None else 0.0)
    d["placebo"] = 1.0
    print(city, len(d), "sampled lots; homes before", int(d.units_before.sum()), "after", int(d.units_after.sum()),
          "(x5 for the city)", flush=True)
    return d.reset_index(drop=True)


def _mrr_width(g) -> float:
    try:
        r = g.minimum_rotated_rectangle
        xs, ys = r.exterior.coords.xy
        return float(min(((xs[i + 1] - xs[i]) ** 2 + (ys[i + 1] - ys[i]) ** 2) ** 0.5 for i in range(4)))
    except Exception:  # noqa: BLE001
        return np.nan


def sanity_flags(stage: str) -> None:
    """Flags only, never stops the run (owner, 2026-10-28): units, policy distance, traits outside other cities' range."""
    from missing_middleware.tod import sanity as S
    D = pd.read_parquet(FIT["lots"])
    cache = {k: cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(D["city"], D["eff_year"]))}
    D["cost_per_home"] = [cache[(c, y)] for c, y in zip(D["city"], D["eff_year"])]   # item 44: real costs, not a placeholder
    X = features(D, False)
    fl = S.unit_flags(D, FAR_CITIES) + S.policy_flags(D) + S.range_flags(X, D["city"])
    if "level_source" in D:   # item 34.5: where each city's density level comes from
        for (c, src), n in D.groupby(["city", "level_source"]).size().items():
            fl.append({"kind": "level source", "city": c, "item": "far_before", "detail": f"{n} lots: {src}"})
    if "level_flag" in D:
        for (c, f), n in D[D["level_flag"].astype(str).str.len() > 0].groupby(["city", "level_flag"]).size().items():
            fl.append({"kind": "level source", "city": c, "item": "far_before", "detail": f"{n} lots: {f}"})
    # item 44.1: share of lots with a missing value (filled later), per city and trait
    raw = {"rent": D["rent"], "home_value": D["home_value"], "income": D["income"], "cost_per_home": D["cost_per_home"],
           "far_before": D["far_before"], "census_homes": D.get("census_homes", pd.Series(np.nan, index=D.index))}
    for k, v in raw.items():
        for c, sh in v.isna().groupby(D["city"]).mean().items():
            if sh > 0.05:
                fl.append({"kind": "filled", "city": c, "item": k, "detail": f"{sh:.0%} of lots missing, filled from training medians"})
    # item 44.3: dollar traits more than 2x off the other cities' median
    dol = pd.DataFrame({"rent": D["rent"], "home_value": D["home_value"], "income": D["income"],
                        "cost_2024": cost_2024(D)})
    med = dol.groupby(D["city"]).median()
    for k in med.columns:
        for c in med.index:
            other = med[k].drop(c).median()
            if pd.notna(med.at[c, k]) and other and not (0.5 <= med.at[c, k] / other <= 2):
                fl.append({"kind": "dollar ratio", "city": c, "item": k, "detail": f"median {med.at[c, k]:,.0f} vs other cities {other:,.0f}"})
    # item 45.3: lots farther from a rail or rapid stop than the training cities' 95th percentile
    if "dist_station_m" in D:
        trn = D["dist_station_m"][~D["city"].isin(HOLD) & ~D["city"].isin(list(PLACEBO))]
        p95 = float(trn.quantile(0.95))
        for c, sh in (D["dist_station_m"] > p95).groupby(D["city"]).mean().items():
            if sh > 0.05:
                fl.append({"kind": "out of range", "city": c, "item": "dist_station_m", "detail": f"{sh:.0%} of lots beyond the training 95th percentile ({p95:,.0f} m)"})
    # item 44.4: source years
    from missing_middleware.tod import allvars as A
    for c, y in D.groupby("city")["eff_year"].agg(lambda s: sorted(set(int(x) for x in s))).items():
        fl.append({"kind": "source year", "city": c, "item": "years", "detail": f"reform years {y[0]}–{y[-1]}; ACS ending {A.survey_end_year(y[0])}–{A.survey_end_year(y[-1])}; cost median over the 5 years around year before"})
    S.report(fl, REFERENCE / f"tod_lot_model_flags_{stage}{FIT['suffix']}.csv")


def enrich_all() -> None:
    """All 91 tract variables of the all-variables test on every lot (plan section 9, item 9)."""
    import importlib.util as ilu
    from missing_middleware.tod import allvars as A
    spec = ilu.spec_from_file_location("run_tod_allvars", ROOT / "scripts" / "run_tod_allvars.py")
    AV = ilu.module_from_spec(spec)
    spec.loader.exec_module(AV)
    D = pd.read_parquet(PATHS['lots'])
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
    D.to_parquet(PATHS['lots'])
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
    D = pd.read_parquet(FIT["lots"])
    if ROBUST["drop_largest"]:   # plan section 9, item 19: each city's largest project (lot with most homes after) out
        D = D.drop(D.groupby("city")["units_after"].idxmax().values).reset_index(drop=True)
    cache = {k: cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(D["city"], D["eff_year"]))}
    D["cost_per_home"] = [cache[(c, y)] for c, y in zip(D["city"], D["eff_year"])]
    if FIT.get("item32"):
        D = dedupe_lots(D).reset_index(drop=True)
    else:
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
    D = five_year_basis(D)
    dy = (D["ua5"] - D["ub5"]).values   # item 24
    cities = [c for c in D["city"].unique() if c not in HOLD]

    def actual_extra(d):
        t = d[d.treated == 1]
        c = d[(d.treated == 0) & (d["comparison_eligible"] == 1)] if "comparison_eligible" in d else d[d.treated == 0]   # items 15-16
        ta, ca = (t.acres * t.w).sum(), (c.acres * c.w).sum()
        return ((t.ua5 * t.w).sum() - ta * (c.ua5 * c.w).sum() / ca) - \
               ((t.ub5 * t.w).sum() - ta * (c.ub5 * c.w).sum() / ca), ta

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
            return lambda: RandomForestClassifier(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED["v"]), \
                   lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED["v"]), False
        if kind == "boosting":
            return lambda: GradientBoostingClassifier(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=SEED["v"]), \
                   lambda: GradientBoostingRegressor(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=SEED["v"]), False
        if kind == "knn":
            return lambda: KNeighborsClassifier(n_neighbors=50, n_jobs=-1), lambda: KNeighborsRegressor(n_neighbors=50, n_jobs=-1), True
        raise ValueError(kind)

    def predict(kind, tr, te):
        tt = te[(D.loc[te, "treated"] == 1).values]
        sample = te if len(te) <= 20000 else rng.choice(te, 20000, replace=False)
        if tlearner:
            regs = {"wls": lambda: LinearRegression(), "lasso": lambda: Lasso(alpha=0.01), "elastic_net": lambda: ElasticNet(alpha=0.01, l1_ratio=0.5),
                    "tree": lambda: DecisionTreeRegressor(max_depth=3, min_samples_leaf=200),
                    "forest": lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED["v"]),
                    "causal_forest": lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED["v"]),
                    "boosting": lambda: GradientBoostingRegressor(max_depth=3, n_estimators=200, learning_rate=0.05, subsample=0.5, random_state=SEED["v"]),
                    "knn": lambda: KNeighborsRegressor(n_neighbors=50, n_jobs=-1)}
            scale = kind in ("wls", "lasso", "elastic_net", "knn")
            sc = StandardScaler().fit(Xb.loc[tr]) if scale else None
            T = (lambda X: sc.transform(X)) if scale else (lambda X: X)  # noqa: E731
            out, models = [], {}
            for g in (1, 0):
                ix = tr[(D.loc[tr, "treated"] == g).values]
                if g == 0 and FIT.get("item32") and not FIT.get("item37") and "comparison_eligible" in D:   # item 32.4
                    ix = tr[((D.loc[tr, "treated"] == 0) & (D.loc[tr, "comparison_eligible"] == 1)).values]
                if kind == "knn" and len(ix) > 60000:
                    ix = rng.choice(ix, 60000, replace=False)
                XX = Xa if (g == 1 and FIT.get("item25")) else Xb   # item 25.1
                if scale:
                    sc = StandardScaler().fit(XX.loc[ix])
                m = regs[kind]()
                try:
                    m.fit(T(XX.loc[ix]), dy[D.index.get_indexer(ix)], sample_weight=D.loc[ix, "w"])
                except TypeError:
                    m.fit(T(XX.loc[ix]), dy[D.index.get_indexer(ix)])
                Xt = XX.loc[tt].copy()
                if FIT.get("item37") and "rezoned_later" in Xt:   # item 41.1: unknown at forecast time, also in this score
                    Xt["rezoned_later"] = 0.0
                out.append(m.predict(T(Xt)) if len(tt) else np.zeros(0))
                models[g] = (m, XX, sc if scale else None)
            if FIT.get("item37"):   # item 37.2: total homes built in the study area (law on for upzoned lots)
                up = (D.loc[te, "treated"] == 1).values
                pd_ = np.zeros(len(te))
                for g, mask in ((1, up), (0, ~up)):
                    if mask.any():
                        m, XX, scg = models[g]
                        Xg = XX.loc[te[mask]].copy()
                        if "rezoned_later" in Xg:   # item 41.1: unknown at forecast time, as for Wisconsin
                            Xg["rezoned_later"] = 0.0
                        pd_[mask] = m.predict(scg.transform(Xg) if scg is not None else Xg)
                wv = D.loc[te, "w"].values
                ua, ub = D.loc[te, "ua5"].values, D.loc[te, "ub5"].values
                TOT[(kind, D.at[te[0], "city"])] = {"total_actual": float(ua @ wv), "total_baseline": float(ub @ wv),
                                                     "total_model": float((ub + pd_) @ wv),
                                                     "upzoned_actual": float(ua[up] @ wv[up]), "upzoned_baseline": float(ub[up] @ wv[up]),
                                                     "upzoned_model": float((ub[up] + pd_[up]) @ wv[up])}
            return float((out[0] - out[1]) @ D.loc[tt, "w"].values) if len(tt) else 0.0, np.nan
        if kind == "causal_forest":
            out = []
            for g in (1, 0):
                ix = tr[(D.loc[tr, "treated"] == g).values]
                XX = Xa if (g == 1 and FIT.get("item25")) else Xb   # item 25.1: the upzoned forest sees the rules after
                m = RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED["v"])
                m.fit(XX.loc[ix], dy[D.index.get_indexer(ix)], sample_weight=D.loc[ix, "w"])
                out.append(m.predict(XX.loc[tt]))
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

    rows, TOT = [], {}
    methods = ("wls", "lasso", "elastic_net", "tree", "forest", "boosting", "causal_forest", "knn")
    if ROBUST.get("only"):
        methods = tuple(m for m in methods if m in ROBUST["only"])
    for kind in methods:
        for c in cities + list(HOLD):
            te = D.index[D["city"] == c].to_numpy()
            # item 40.1: a city's own no-reform lots never train the model that predicts it (Madison placebo vs Madison)
            base_c = c.removesuffix(" placebo")
            tr = D.index[D["city"].isin([x for x in cities if x != c and x.removesuffix(" placebo") != base_c])].to_numpy()
            act, ta = actual_extra(D.loc[te])
            num = den = 0.0
            for x in [x for x in cities if x != c]:
                e, a = actual_extra(D[D["city"] == x])
                num, den = num + e, den + a
            base = num / den * ta
            ex, auc = predict(kind, tr, te)
            rows.append({"method": kind, "city": c, "role": "holdout" if c in HOLD else ("placebo" if c in PLACEBO else "fold"), "actual_extra_homes": act,
                         "baseline_extra": base, "model_extra": ex, "error_baseline": abs(base - act), "error_model": abs(ex - act),
                         "auc_builds": auc})
            print(kind, c, round(act), round(base), round(ex), flush=True)
    E = pd.DataFrame(rows)
    if TOT:   # item 37.2: totals test
        for k in ("total_actual", "total_baseline", "total_model", "upzoned_actual", "upzoned_baseline", "upzoned_model"):
            E[k] = [TOT.get((m, c), {}).get(k, np.nan) for m, c in zip(E["method"], E["city"])]
        E["total_error_model"] = (E["total_model"] - E["total_actual"]).abs()
        E["total_error_baseline"] = (E["total_baseline"] - E["total_actual"]).abs()
        TS = []
        for kind, g in E.groupby("method", sort=False):
            h = g[g.role == "holdout"].set_index("city")
            pl = g[g.role == "placebo"]
            better = {c: bool(h.loc[c, "total_error_model"] < h.loc[c, "total_error_baseline"]) for c in HOLD if c in h.index}
            # item 41.2: judge the predicted change (after minus before), not the level
            chg_a = h["total_actual"] - h["total_baseline"]
            chg_m = h["total_model"] - h["total_baseline"]
            within = {c: bool(abs(chg_m[c] - chg_a[c]) <= 0.5 * abs(chg_a[c])) for c in HOLD if c in h.index}
            ok = bool(sum(better.values()) >= 2 and sum(within.values()) >= 2)
            TS.append({"method": kind, "mean_error_baseline": g["total_error_baseline"].mean(), "mean_error_model": g["total_error_model"].mean(),
                       **{f"{c.lower()}_better": v for c, v in better.items()},
                       **{f"{c.lower()}_change_within_50pct": v for c, v in within.items()},
                       "placebo_ok": bool((pl["total_error_model"] <= pl["total_error_baseline"]).all()), "passes_totals_test": ok})
        TS = pd.DataFrame(TS)
        TS.round(2).to_csv(REFERENCE / f"tod_lot_model_totals{('_runE' if tlearner else '_runD_all8') + FIT['suffix']}.csv", index=False)
        print(TS.round(1).to_string(), flush=True)
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
    tag = ("_runE" if tlearner else "_runD_all8") + FIT["suffix"]
    E.round(3).to_csv(REFERENCE / f"tod_lot_model_by_city{tag}.csv", index=False)
    S.round(4).to_csv(REFERENCE / f"tod_lot_model_results{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(2).to_string())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=["collect", "add_bellevue", "enrich", "enrich_all", "values", "fit", "fit_allvars", "fit8", "fit_runE", "add_saturation", "half_mile", "census_homes", "land_values", "fix_density", "recollect_item29", "spread_assembly", "add_placebo", "add_placebo_us"], required=True)
    ap.add_argument("--seed", type=int, default=0, help="robustness: another random seed (item 19)")
    ap.add_argument("--with-rezoned-later", action="store_true", help="check run: keep the rezoned-later trait (item 32.3)")
    ap.add_argument("--land-value", action="store_true", help="add the pays-for-itself traits (LAND_VALUE_PLAN.md)")
    ap.add_argument("--only", default="", help="comma-separated methods for fit8/fit_runE (robustness reruns)")
    ap.add_argument("--drop-largest", action="store_true", help="robustness: each city's largest project left out (item 19)")
    ap.add_argument("--rebuilt", action="store_true", help="plan item 15 lot table (industrial conversions, in-reform lots, census homes)")
    ap.add_argument("--half-mile", action="store_true", help="fit on lots within 1/2 mile of rail or rapid stops (item 14)")
    a = ap.parse_args(argv)
    if a.seed:
        SEED["v"] = a.seed
    if a.drop_largest:
        ROBUST["drop_largest"] = True
    if a.only:
        ROBUST["only"] = tuple(a.only.split(","))
    ap_rebuilt = a.rebuilt
    if ap_rebuilt:
        REBUILT["on"] = True
        PATHS.update(lots=LOTS_REBUILT, half=OUT / "lots_rebuilt_halfmile.parquet")
        FIT.update(item25=True, item32=True, item34=True, item37=True, item46=True, with_rezoned_later=a.with_rezoned_later)
        import missing_middleware.tod.case_nyc as _N
        import missing_middleware.tod.case_chicago as _K
        _N.EXCLUDE_HOTELS, _K.STAGED_RELAXED = True, True   # item 32.1-2
        FIT.update(lots=PATHS["half"], suffix="_v37" + ("_rzl" if a.with_rezoned_later else "") + ("_land" if a.land_value else "") + (f"_seed{a.seed}" if a.seed else "")
                   + ("_droplargest" if a.drop_largest else ""), land=a.land_value)
    elif a.half_mile:
        FIT.update(lots=LOTS_HALF, suffix="_halfmile")
    if a.stage == "half_mile":
        half_mile()
    if a.stage == "census_homes":
        census_homes()
    if a.stage == "land_values":
        land_values()
    if a.stage == "fix_density":
        fix_density()
    if a.stage == "recollect_item29":
        recollect_item29()
    if a.stage == "spread_assembly":
        spread_assembly()
    if a.stage == "add_placebo":
        add_placebo()
    if a.stage == "add_placebo_us":
        add_placebo_us()
    if a.stage.startswith("fit"):
        sanity_flags(a.stage)
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

"""Station-area lot tables for the northern cluster cases (docs/tod/STATION_AREA_PLAN.md: LOCKED, audit section G,
owner answers of 15:57, step C).

Cases and windows come from the lot model's table (data/processed/tod_lot_model/lots_rebuilt_halfmile.parquet), exactly
as case_windows() in scripts/run_tod_station_area.py: before = window_first..eff-1, after = eff+1..window_last.

    seattle_othello_2012      lot-model unit seattle_nbh_othello_2012
    seattle_mount_baker_2014  lot-model unit seattle_mount_baker_2014
    bellevue_belred_2009      lot-model unit bellevue_belred_2009
    stpaul_2011               lot-model unit stpaul (reform year 2011 in the lot model, not 2012)
    charlotte_2019            lot-model unit charlotte

Upzoned area: the lot model's treated lots (as points, the same input as upzoned_points()); a lot is in the reform
area if it lies within 30 m of a treated lot point.

Stops (platforms within 150 m merged into one station; the case's rail_stops.geojson, BTS national transit map):
- reform stops: stops of the reform city within 1/2 mile (805 m) of the upzoned area;
- comparison stops, two kinds (column comparison_kind): "out-of-city" = same-type stops in other cities of the metro
  where county year-built data exists (King County cities for Seattle and Bellevue), and "in-city" = the reform city's
  other same-type stops (the LOCKED plan keeps the in-city comparison and adds out-of-city stops where possible).
- "Same type" means the same line status in the reform year: Seattle, stations open by the reform year (Central Link,
  opened 2009); Bellevue, stations of East Link as approved by voters in 2008 (none open until 2024); Saint Paul, the
  Green Line (opened 2014); Charlotte, LYNX Blue Line stations plus CityLYNX Gold Line streetcar stops (flagged:
  streetcar is a different mode; the Blue Line alone leaves only two comparison stations).
- stops within 1/2 mile of another lot-model case's upzoned area in the same city whose reform year falls inside this
  case's windows are left out (Seattle: Othello and Mount Baker are each other's contaminated neighbours); lots nearest
  to them are dropped, not reassigned.
Each lot is matched to the nearest stop on its own side: lots in the reform city to the reform city's stops, lots in
other cities to the out-of-city comparison stops.

Saint Paul: Minneapolis was the planned out-of-city comparison, but the Hennepin County parcel points carry no homes
(NUM_UNITS is 0 on every row, DWELL_TYPE empty), so Saint Paul uses in-city comparison stops only (downtown).

Homes:
- King County (Seattle, Bellevue, comparison cities): Assessor extracts, year built x homes per record:
  residential buildings (NbrLivingUnits, YrBuilt), apartment complexes (NbrUnits, YrBuilt), condo complexes (residential
  unit records counted per complex, complex YrBuilt; placed on the complex's Major+0000 parcel). Records whose parcel
  has no point are placed at the mean point of their Major (plat). Condo complex NbrUnits is not used: mixed-use
  complexes count shops and parking in it.
- Saint Paul: city parcel file (LivingUnit, YearBuilt).
- Charlotte: no homes field in the county parcel file, so new homes come from county building permits (permit year,
  both sides in-city) placed on the nearest lot within 60 m; existing homes = 2010 Census block homes (HOUSING10)
  spread over the block's residential lots built before 2010 by building value, plus homes permitted 2010 to the year
  before the before window.
Parcel ids stay in data/ (lot tables are written by the builder to data/processed/).
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import RAW  # noqa: E402

CRS = 5070
QUARTER, HALF, MILE = 402.0, 805.0, 1609.0
RP = RAW / "tod_radius_programs"
TC = RAW / "tod_cases"
LOTS = ROOT / "data" / "processed" / "tod_lot_model" / "lots_rebuilt_halfmile.parquet"

META = {
    "seattle_othello_2012": {"unit": "seattle_nbh_othello_2012", "city": "Seattle", "metro": "king", "stops": "seattle", "state": "53"},
    "seattle_mount_baker_2014": {"unit": "seattle_mount_baker_2014", "city": "Seattle", "metro": "king", "stops": "seattle", "state": "53"},
    "bellevue_belred_2009": {"unit": "bellevue_belred_2009", "city": "Bellevue", "metro": "king", "stops": "bellevue", "state": "53"},
    "stpaul_2011": {"unit": "stpaul", "city": "Saint Paul", "metro": "stpaul", "stops": "stpaul", "state": "27"},
    "charlotte_2019": {"unit": "charlotte", "city": "Charlotte", "metro": "clt", "stops": "charlotte", "state": "37"},
}
PLACE = {"Seattle": "Seattle", "Bellevue": "Bellevue", "Saint Paul": "St. Paul", "Charlotte": "Charlotte"}

# Link station opening years (Sound Transit service changes) and the 2008 voter-approved East Link stations
LINK_OPENED = {**{s: 2009 for s in ("Westlake", "Symphony", "Pioneer Square", "Int'l Dist/Chinatown", "Stadium", "SODO",
                                    "Beacon Hill", "Mount Baker", "Columbia City", "Othello", "Rainier Beach",
                                    "Tukwila Int'l Blvd", "SeaTac/Airport")},
               **{s: 2016 for s in ("Univ of Washington", "Capitol Hill", "Angle Lake")}}
EAST_LINK_ST2 = ("South Bellevue", "East Main", "Bellevue Downtown", "Wilburton", "Spring District", "BelRed",
                 "Overlake Village", "Redmond Technology", "Mercer Island", "Judkins Park")
# comparison cities with their own station-area rezoning inside the window (flagged, shown in S.own_tod_rezoning)
OWN_TOD = {"Overlake Village": "yes: Redmond Overlake plan and zoning 2007-2011", "Redmond Technology": "yes: Redmond Overlake plan 2007-2011",
           "Tukwila Int'l Blvd": "not checked", "SeaTac/Airport": "not checked", "Mercer Island": "not checked",
           "Judkins Park": "not checked"}


def _windows() -> dict:
    d = pd.read_parquet(LOTS, columns=["unit", "eff_year", "window_first", "window_last", "placebo"])
    d = d[d.placebo != 1].drop_duplicates("unit").set_index("unit")
    out = {}
    for case, m in META.items():
        r = d.loc[m["unit"]]
        e = int(r.eff_year)
        out[case] = {"eff": e, "before": (int(r.window_first), e - 1), "after": (e + 1, int(r.window_last)),
                     "reform_city": m["city"], "lot_model_unit": m["unit"]}
    return out


CASES = _windows()
# one row per new-building record placed on a lot of D, any year from 2000 on (owner: keep data, compute windows later)
EVENTS: dict[str, pd.DataFrame] = {}


# --------------------------------------------------------------------------- upzoned land

def treated_points() -> dict[str, gpd.GeoSeries]:
    D = pd.read_parquet(LOTS, columns=["city", "unit", "treated", "x5070", "y5070", "placebo"])
    D = D[(D.treated == 1) & (D.placebo != 1)]
    return {str(u): gpd.GeoSeries(gpd.points_from_xy(g.x5070, g.y5070), crs=CRS) for u, g in D.groupby("unit")}


# --------------------------------------------------------------------------- stops

def stations(name: str) -> gpd.GeoDataFrame:
    g = gpd.read_file(TC / name / "rail_stops.geojson").to_crs(CRS)
    blobs = g.buffer(75).union_all()
    parts = list(blobs.geoms) if hasattr(blobs, "geoms") else [blobs]
    st = gpd.GeoDataFrame(geometry=[p.centroid for p in parts], crs=CRS)
    j = gpd.sjoin_nearest(st, g[["stop_name", "stop_type_text", "geometry"]], how="left").drop_duplicates(subset="geometry")
    j = j.reset_index(drop=True)[["stop_name", "stop_type_text", "geometry"]]
    j["stop_type_text"] = j.stop_type_text.str.strip('"')
    return j


def place_of(g: gpd.GeoDataFrame, state: str) -> pd.Series:
    p = gpd.read_file(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip")
    p = p[p.STATEFP == state].to_crs(CRS)[["NAME", "geometry"]]
    j = gpd.sjoin(g[["geometry"]], p, how="left", predicate="within")
    return j[~j.index.duplicated()]["NAME"].reindex(g.index)


def city_hall(city: str):
    import run_tod_station_area as SA
    _, _, la, lo = SA.CITIES[city]
    return gpd.GeoSeries(gpd.points_from_xy([lo], [la]), crs=4326).to_crs(CRS).iloc[0]


def stops_for(case: str) -> gpd.GeoDataFrame:
    m, c = META[case], CASES[case]
    S = stations(m["stops"])
    S["place"] = place_of(S, m["state"])
    nm = S.stop_name.str.replace(" Station", "", regex=False)
    if m["metro"] == "king":
        if case.startswith("seattle"):
            same = nm.map(LINK_OPENED).le(c["eff"])          # open by the reform year
        else:
            same = nm.isin(EAST_LINK_ST2)                       # approved 2008, none open in the window
        S["stop_type_text"] = np.where(case.startswith("seattle"), "Link light rail (open)", "Link light rail (approved 2008, opened 2024+)")
    elif m["metro"] == "stpaul":
        green = S.place.eq("St. Paul") | nm.isin(["Prospect Park", "Stadium Village", "East Bank", "West Bank"])
        same = green & S.place.eq("St. Paul")                  # Minneapolis: no homes counts in the Hennepin file
        S["stop_type_text"] = "Green Line light rail (opened 2014)"
    else:
        same = pd.Series(True, index=S.index)
        S["stop_type_text"] = np.where(S.stop_name.str.contains("CityLYNX"), "CityLYNX Gold Line streetcar", "LYNX Blue Line light rail")
    S = S[same].copy()
    tp = treated_points()
    area = tp[m["unit"]].union_all()
    S["dist_upzoned_m"] = S.distance(area).round(0)
    in_city = S.place.eq(PLACE[m["city"]])
    S["group"] = np.where(in_city & (S.dist_upzoned_m <= HALF), "reform", "comparison")
    S["comparison_kind"] = np.where(S.group == "reform", "", np.where(in_city, "in-city", "out-of-city"))
    # contaminated: near another case's upzoned land in this city, reformed inside this case's windows
    S["excluded_reason"] = ""
    for other, om in META.items():
        if other == case or om["city"] != m["city"]:
            continue
        if c["before"][0] <= CASES[other]["eff"] <= c["after"][1]:
            near = S.distance(tp[om["unit"]].union_all()) <= HALF
            S.loc[near & (S.group == "comparison"), "excluded_reason"] = f"own rezoning {CASES[other]['eff']} ({other})"
    S["own_tod_rezoning"] = nm.map(OWN_TOD).reindex(S.index).fillna("")
    S["downtown"] = S.distance(city_hall(m["city"])) <= MILE
    S = S.reset_index(drop=True)
    S["stop_id"] = np.arange(len(S))
    return S


# --------------------------------------------------------------------------- King County lots

def _kc(zname: str, fname: str, cols: list[str]) -> pd.DataFrame:
    d = pd.read_csv(zipfile.ZipFile(RP / "king" / zname).open(fname), dtype=str, encoding="latin1", usecols=cols)
    for k in d.columns:
        d[k] = d[k].str.strip()
    d["Major"] = d.Major.str.zfill(6)
    if "Minor" in d:
        d["Minor"] = d.Minor.str.zfill(4)
    return d


CONDO_RES_UNIT_TYPES = {1, 2, 3, 4, 15, 26, 27, 29, 30, 31}   # unit types with bedrooms/living area (not parking, storage, moorage, commercial)
PUBLIC_KC = re.compile(r"Govern|Public|Right of Way|Easement|Utility", re.I)


def king_records() -> pd.DataFrame:
    """One row per building record: key (Major+Minor), year built, homes, kind."""
    rb = _kc("Residential_Building.zip", "EXTR_ResBldg.csv", ["Major", "Minor", "NbrLivingUnits", "YrBuilt"])
    ap = _kc("Apartment_Complex.zip", "EXTR_AptComplex.csv", ["Major", "Minor", "NbrUnits", "YrBuilt"])
    cc = _kc("Condo_Complex_and_Units.zip", "EXTR_CondoComplex.csv", ["Major", "NbrUnits", "YrBuilt", "ComplexType"])
    cu = _kc("Condo_Complex_and_Units.zip", "EXTR_CondoUnit2.csv", ["Major", "Minor", "UnitType"])
    cu = cu[pd.to_numeric(cu.UnitType, errors="coerce").isin(CONDO_RES_UNIT_TYPES)]
    cc["units"] = cc.Major.map(cu.groupby("Major").size()).fillna(0)
    # complex types 2 and 5 (and 4, 6) are mostly rental buildings under a condo regime: the homes sit in one or two
    # condo "units" (e.g. "440 Res Units w/ retail over parking": 2 unit records), and the complex's NbrUnits holds the
    # homes. Type 1 (flats, townhouses) NbrUnits can be a multi-Major project total, so unit records are used there.
    n = pd.to_numeric(cc.NbrUnits, errors="coerce").fillna(0)
    regime = cc.ComplexType.isin(["2", "4", "5", "6"])
    cc["units"] = np.where(regime, np.maximum(cc.units, n), cc.units)
    rb = rb[~(rb.Major.isin(set(cc.Major)) & (rb.Minor == "0000"))]   # house record on a condo complex's own parcel
    R = pd.concat([
        pd.DataFrame({"key": rb.Major + rb.Minor, "major": rb.Major, "yb": rb.YrBuilt, "units": rb.NbrLivingUnits, "kind": "house"}),
        pd.DataFrame({"key": ap.Major + ap.Minor, "major": ap.Major, "yb": ap.YrBuilt, "units": ap.NbrUnits, "kind": "apartment"}),
        pd.DataFrame({"key": cc.Major + "0000", "major": cc.Major, "yb": cc.YrBuilt, "units": cc.units, "kind": "condo"}),
    ], ignore_index=True)
    R["yb"] = pd.to_numeric(R.yb, errors="coerce").fillna(0).astype(int)
    R["units"] = pd.to_numeric(R.units, errors="coerce").fillna(0).astype(float)
    return R[R.units > 0]


def king_lots() -> gpd.GeoDataFrame:
    P = pd.read_csv(RP / "king" / "parcels.csv", dtype={"MAJOR": str, "MINOR": str, "PIN": str}, low_memory=False)
    P["key"] = P.MAJOR.str.zfill(6) + P.MINOR.str.zfill(4)
    P["major"] = P.MAJOR.str.zfill(6)
    P = P.drop_duplicates("key")
    R = king_records()
    has_pt = P.LAT.notna()
    # records on parcels without a point: place at the mean point of the Major (plat); else dropped (counted)
    Pp = P[has_pt]
    maj = Pp.groupby("major")[["LAT", "LON"]].mean()
    lost = R[~R.key.isin(set(Pp.key))]
    can = lost[lost.major.isin(maj.index)]
    print(f"King records without a parcel point: {len(lost)} ({lost.units.sum():.0f} homes); placed at their plat: "
          f"{can.units.sum():.0f}; dropped: {lost.units.sum() - can.units.sum():.0f}", flush=True)
    extra = pd.DataFrame({"key": can.key.unique()})
    extra["major"] = extra.key.str[:6]
    extra = extra.join(maj, on="major")
    extra = extra.merge(P[["key", "CTYNAME", "LOTSQFT", "APPRLNDVAL", "APPR_IMPR", "PREUSE_DESC"]], on="key", how="left")
    extra["CTYNAME"] = extra.CTYNAME.fillna(extra.major.map(Pp.groupby("major").CTYNAME.first()))
    L = pd.concat([Pp[["key", "LAT", "LON", "CTYNAME", "LOTSQFT", "APPRLNDVAL", "APPR_IMPR", "PREUSE_DESC"]], extra.drop(columns="major")], ignore_index=True)
    L["placed"] = np.where(L.key.isin(set(Pp.key)), "parcel point", "plat mean point")
    g = R.groupby("key")
    yb = g.yb.apply(tuple)
    un = g.units.apply(tuple)
    kinds = g.kind.agg(lambda k: "+".join(sorted(set(k))))
    out = gpd.GeoDataFrame({
        "lot_key": L.key, "city_name": L.CTYNAME.astype(str).str.title().replace({"Seatac": "SeaTac", "Nan": None}),
        "acres": pd.to_numeric(L.LOTSQFT, errors="coerce") / 43560.0,
        "land_value": pd.to_numeric(L.APPRLNDVAL, errors="coerce"), "bldg_value": pd.to_numeric(L.APPR_IMPR, errors="coerce"),
        "use": L.PREUSE_DESC.astype(str).str.strip(), "public": L.PREUSE_DESC.astype(str).str.contains(PUBLIC_KC),
        "placed": L.placed, "record_kind": L.key.map(kinds).fillna(""),
    }, geometry=gpd.points_from_xy(L.LON, L.LAT), crs=4326).to_crs(CRS)
    out["_yb"] = [t if isinstance(t, tuple) else () for t in L.key.map(yb)]
    out["_un"] = [t if isinstance(t, tuple) else () for t in L.key.map(un)]
    out["year_built"] = [min([y for y in t if y > 0], default=np.nan) for t in out["_yb"]]
    return out


# --------------------------------------------------------------------------- Saint Paul lots

def stpaul_lots() -> gpd.GeoDataFrame:
    d = pd.read_csv(RP / "saint_paul" / "parcels.csv", low_memory=False)
    yb = pd.to_numeric(d.YearBuilt, errors="coerce")
    un = pd.to_numeric(d.LivingUnit, errors="coerce").fillna(0)
    # hotels and nursing homes (rooms and beds, not homes) are left out, as in the permit sources
    beds = (d.LandUseCodeDescription.fillna("") + " " + d.DwellingType.fillna("")).str.contains("HOTEL|MOTEL|NURSING HOME", case=False)
    print(f"Saint Paul living units on hotel or nursing-home parcels left out: {un[beds].sum():.0f}", flush=True)
    un = un.where(~beds, 0)
    L = gpd.GeoDataFrame({
        "lot_key": d.ParcelID.astype(str), "city_name": "Saint Paul",
        "acres": pd.to_numeric(d.ParcelSquareFeet, errors="coerce") / 43560.0,
        "land_value": pd.to_numeric(d.EMVLand, errors="coerce"), "bldg_value": pd.to_numeric(d.EMVBuilding, errors="coerce"),
        "use": d.LandUseCodeDescription.astype(str), "public": d.OwnershipCategory.astype(str).ne("Unknown") | d.TaxExemptYN.eq("Y"),
        "year_built": yb.where(yb > 0), "record_kind": d.DwellingType.astype(str), "placed": "parcel point",
    }, geometry=gpd.points_from_xy(d.Longitude, d.Latitude), crs=4326).to_crs(CRS)
    L["_yb"] = [((int(y) if y == y else 0),) for y in yb]
    L["_un"] = [(float(u),) for u in un]
    return L


# --------------------------------------------------------------------------- Charlotte lots

PUBLIC_CLT = re.compile(r"COUNTY|MUNICIPAL|SCHOOL - PUBLIC|RIGHT OF WAY|STATE|FEDERAL|CITY|COS NO", re.I)
RES_CLT = re.compile(r"SINGLE FAMILY|TOWN HOUSE  SFR|CONDOMINIUM$|CONDOMINIUM HIGH|CONDOMINIUM WATER|MULTI FAM|MOBILE HOME|RURAL HOMESITE|DUPLEX", re.I)


def charlotte_lots() -> gpd.GeoDataFrame:
    d = pd.read_csv(RP / "mecklenburg" / "parcels.csv", low_memory=False)
    d["sy"] = pd.to_numeric(d.structyear, errors="coerce").where(lambda s: s > 1700)
    g = d.groupby("parno")
    d = g.first().assign(year_built=g.sy.min()).reset_index()
    return gpd.GeoDataFrame({
        "lot_key": d.parno.astype(str), "city_name": d.scity.astype(str).str.title(),
        "acres": pd.to_numeric(d.gisacres, errors="coerce"),
        "land_value": pd.to_numeric(d.landval, errors="coerce"), "bldg_value": pd.to_numeric(d.improvval, errors="coerce"),
        "use": d.parusedesc.astype(str), "public": d.parusedesc.astype(str).str.contains(PUBLIC_CLT),
        "year_built": d.year_built, "record_kind": "", "placed": "parcel point",
    }, geometry=gpd.points_from_xy(d.cx, d.cy), crs=4326).to_crs(CRS)


STAGED = r"level|lvl|fl(?:oo)?r\b|story|podium|upfit|shell|core|F/F|\bS/C\b|units? \d|residential units"


def charlotte_permits() -> gpd.GeoDataFrame:
    """County building permits with homes (case_charlotte.load_permits: new residential buildings, placeholders out),
    points in CRS 5070 with year, units and the permit's parcel number.

    Staged permits: a mid- or high-rise is often permitted floor by floor ("Level 3 Units", "2nd FLR", "Shell", "F/F
    upfit"), and several of these permits repeat the whole building's home count (e.g. five same-day "Level 1-5"
    permits each with 70 homes). Among permits whose name marks a stage, only one per parcel, home count and year is
    kept. Separate buildings of a garden complex ("Building 1", "Building 2", same count, same day) are real and kept.
    Against the Census permit survey (Mecklenburg County office): raw 0.95 (2013-18) and 1.24 (2020-24); after this
    rule 0.88 and 0.95 (see census_check)."""
    from missing_middleware.tod import case_charlotte as CC
    d = CC.load_permits()
    staged = d.projname.astype(str).str.contains(STAGED, case=False)
    d = d[~(staged & d.duplicated(["parcelnum", "units", "year"]))]
    g = gpd.GeoDataFrame(d[["year", "units"]].assign(parcelnum=d.parcelnum.astype(str)),
                         geometry=gpd.points_from_xy(d.X.astype(float), d.Y.astype(float)), crs=2264).to_crs(CRS)
    return g.reset_index(drop=True)


def census_existing(D: gpd.GeoDataFrame, all_lots: gpd.GeoDataFrame, state: str) -> pd.Series:
    """2010 Census block homes spread over the block's residential lots standing in 2010, by building value
    (all lots of the block if none is residential; equally if values are missing)."""
    f = RAW / "tod_census_cases" / f"tabblock2010_{state}_pophu.zip"
    box = D.total_bounds
    B = gpd.read_file(f, bbox=tuple(gpd.GeoSeries(gpd.points_from_xy(box[[0, 2]], box[[1, 3]]), crs=CRS).to_crs(4269).total_bounds))
    B = B[B.HOUSING10 > 0].to_crs(CRS)[["BLOCKID10", "HOUSING10", "geometry"]]
    L = all_lots[["geometry", "use", "bldg_value", "year_built"]]
    L = L[L.intersects(B.union_all().envelope)] if len(L) > 200000 else L
    j = gpd.sjoin(L, B, how="inner", predicate="within")
    j = j[~j.index.duplicated()]
    res = j.use.str.contains(RES_CLT) & ~(j.year_built >= 2010)
    blk_has_res = res.groupby(j.BLOCKID10).transform("any")
    w = np.where(blk_has_res, res.astype(float), 1.0) * np.where(j.bldg_value.fillna(0) > 0, j.bldg_value.fillna(0), 1.0)
    w = pd.Series(w, index=j.index)
    share = w / w.groupby(j.BLOCKID10).transform("sum")
    homes = share * j.HOUSING10
    print(f"census 2010 homes in blocks touched: {B.HOUSING10.sum():.0f}; allocated to lots: {homes.sum():.0f}", flush=True)
    return homes.reindex(D.index).fillna(0.0)


# --------------------------------------------------------------------------- build

def _assign(L: gpd.GeoDataFrame, S: gpd.GeoDataFrame, reform_city: str) -> gpd.GeoDataFrame:
    """Nearest stop on the lot's own side (reform-city lots: reform-city stops; other lots: out-of-city stops)."""
    out = []
    in_city = L.city_name.eq(reform_city)
    for side, ls, ss in ((True, L[in_city], S[S.comparison_kind != "out-of-city"]),
                         (False, L[~in_city], S[S.comparison_kind == "out-of-city"])):
        if ss.empty or ls.empty:
            continue
        n = gpd.sjoin_nearest(ls[["geometry"]], ss[["stop_id", "geometry"]], how="inner", max_distance=MILE, distance_col="dist_m")
        out.append(n[~n.index.duplicated()][["stop_id", "dist_m"]])
    return pd.concat(out)


def build(case: str):
    m, c = META[case], CASES[case]
    S_all = stops_for(case)
    if m["metro"] == "king":
        L = king_lots()
        source = "county year built (King County Assessor; both sides)"
    elif m["metro"] == "stpaul":
        L = stpaul_lots()
        source = "county year built (Saint Paul parcels, Ramsey County values; in-city comparison only)"
    else:
        L = charlotte_lots()
        source = "county building permits (Mecklenburg; in-city both sides)"
    near = _assign(L, S_all, m["city"])
    D = L.loc[near.index].copy()
    D["stop_id"] = near.stop_id.astype(int).values
    D["dist_m"] = near.dist_m.values
    st = S_all.set_index("stop_id")
    D = D[st.excluded_reason.reindex(D.stop_id).eq("").values].copy()     # lots nearest a contaminated stop: dropped
    S = S_all[S_all.excluded_reason.eq("")].reset_index(drop=True)
    D["group"] = st.group.reindex(D.stop_id).values
    D["comparison_kind"] = st.comparison_kind.reindex(D.stop_id).values
    D["stop_name"] = st.stop_name.reindex(D.stop_id).values
    D["stop_type_text"] = st.stop_type_text.reindex(D.stop_id).values
    D["downtown_stop"] = st.downtown.reindex(D.stop_id).values
    D["band"] = pd.cut(D.dist_m, [-1, QUARTER, HALF, MILE], labels=["0-1/4", "1/4-1/2", "1/2-1"]).astype(str)
    tp = treated_points()[m["unit"]]
    tj = gpd.sjoin_nearest(D[["geometry"]], gpd.GeoDataFrame(geometry=tp), how="left", max_distance=30, distance_col="_d")
    D["in_reform_area"] = tj[~tj.index.duplicated()]._d.notna().reindex(D.index).values
    b0, b1 = c["before"]; a0, a1 = c["after"]
    if m["metro"] == "clt":
        p = charlotte_permits()
        # placed on the permit's own parcel number where that parcel is a lot of the table, else the nearest lot within 60 m
        own = pd.Series(D.index, index=D.lot_key).reindex(p.parcelnum.values).values
        pn = gpd.sjoin_nearest(p, D[["geometry"]], how="left", max_distance=60, distance_col="_d")
        pn = pn[~pn.index.duplicated()].index_right.reindex(p.index)
        on_parcel = pd.Series(own, index=p.index).notna()
        # a permit whose own parcel exists in the county file but lies outside the table stays off the table
        known = p.parcelnum.isin(set(L.lot_key))
        pj = p.assign(index_right=np.where(on_parcel, own, np.where(known, np.nan, pn.values)))
        pj["placed"] = np.where(on_parcel, "own parcel", np.where(pj.index_right.notna(), "nearest lot 60 m", "none"))
        hit = pj.index_right.notna()
        D.attrs["permit_placement"] = pj[hit].groupby("placed").units.sum().to_dict()
        print("permit homes placed:", D.attrs["permit_placement"], flush=True)
        for lab, (x, y) in {"homes_before_win": (b0, b1), "homes_after_win": (a0, a1), "_pre": (2010, b0 - 1)}.items():
            w = pj[hit & pj.year.between(x, y)]
            D[lab] = w.groupby("index_right").units.sum().reindex(D.index).fillna(0).values
        # permits near the kept stops but on no lot (diagnostic)
        sp = gpd.sjoin_nearest(p[~hit], S[["geometry"]], how="inner", max_distance=MILE)
        D.attrs["permits_on_no_lot"] = {k: float(sp[sp.year.between(*w)].units.sum()) for k, w in (("before", (b0, b1)), ("after", (a0, a1)))}
        print(f"permit homes within 1 mile of kept stops but on no lot (60 m): {D.attrs['permits_on_no_lot']}", flush=True)
        D["homes_census_2010"] = census_existing(D, L, m["state"])
        D["homes_existing"] = D.homes_census_2010 + D._pre
        D = D.drop(columns="_pre")
        D["_yb"] = [()] * len(D)
        D["_un"] = [()] * len(D)
    else:
        D["homes_before_win"] = [sum(u for y, u in zip(ys, us) if b0 <= y <= b1) for ys, us in zip(D._yb, D._un)]
        D["homes_after_win"] = [sum(u for y, u in zip(ys, us) if a0 <= y <= a1) for ys, us in zip(D._yb, D._un)]
        D["homes_existing"] = [sum(u for y, u in zip(ys, us) if not (y >= b0)) for ys, us in zip(D._yb, D._un)]
    D[["homes_before_win", "homes_after_win", "homes_existing"]] = D[["homes_before_win", "homes_after_win", "homes_existing"]].astype(float)
    if m["metro"] == "clt":
        e = pj[hit & (pj.year >= 2000)]
        e = e[e.index_right.isin(D.index)]
        EVENTS[case] = pd.DataFrame({"lot_index": e.index_right.astype(D.index.dtype).values, "homes": e.units.astype(float).values,
                                     "permit_year": e.year.astype(float).values, "completed_year": np.nan, "preferred": "permit",
                                     "source": "Mecklenburg building permit (" + e.placed.values + ")"})
    else:
        rows = [(i, float(u), float(y)) for i, ys, us in zip(D.index, D._yb, D._un) for y, u in zip(ys, us) if y >= 2000 and u > 0]
        e = pd.DataFrame(rows, columns=["lot_index", "homes", "completed_year"])
        EVENTS[case] = e.assign(permit_year=np.nan, preferred="completed",
                                source="King County Assessor year built" if m["metro"] == "king" else "Saint Paul parcels year built"
                                )[["lot_index", "homes", "permit_year", "completed_year", "preferred", "source"]]
    D["case"] = case
    D["source"] = source
    D["implausible"] = False
    S = S[["stop_id", "stop_name", "stop_type_text", "group", "comparison_kind", "place", "dist_upzoned_m", "downtown",
           "own_tod_rezoning", "geometry"]]
    return D, S


# --------------------------------------------------------------------------- checks (not used by the builder)

def census_check(case: str) -> pd.DataFrame:
    """Window totals of the case's citywide source against the Census permit survey (BPS) for the reform city."""
    from missing_middleware.tod.control_cities import read_bps
    m, c = META[case], CASES[case]
    bps = read_bps(RAW / "tod_control_cities" / "bps", years=range(2000, 2026))
    st = {"Seattle": ("53", "Seattle"), "Bellevue": ("53", "Bellevue"), "Saint Paul": ("27", "St. Paul"), "Charlotte": ("37", "Mecklenburg County")}[m["city"]]
    b = bps[(bps.state == st[0]) & (bps.name == st[1])]
    if m["metro"] == "king":
        L = king_lots()
        L = L[L.city_name == m["city"]]
    elif m["metro"] == "stpaul":
        L = stpaul_lots()
    else:
        L = None
        p = charlotte_permits()
    rows = []
    for k, (x, y) in (("before", c["before"]), ("after", c["after"])):
        if L is not None:
            own = sum(u for ys, us in zip(L._yb, L._un) for yy, u in zip(ys, us) if x <= yy <= y)
            lag = sum(u for ys, us in zip(L._yb, L._un) for yy, u in zip(ys, us) if x + 2 <= yy <= y + 2)
        else:
            own = float(p[p.year.between(x, y)].units.sum()); lag = np.nan
        cen = float(b[b.year.between(x, y)].units.sum())
        rows.append({"case": case, "window": k, "years": f"{x}-{y}", "source_homes": own, "census_permits": cen,
                     "ratio": own / cen if cen else np.nan, "source_shifted_2y": lag, "ratio_shifted": lag / cen if cen else np.nan,
                     "bps_name": "; ".join(sorted(b.name.unique()))})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-check", nargs="*", default=list(CASES))
    a = ap.parse_args()
    pd.set_option("display.width", 220)
    print(pd.concat([census_check(k) for k in a.census_check]).round(2).to_string())

"""New York City 2003-2004 upzonings in Brooklyn (Fourth Avenue in Park Slope, Downtown Brooklyn): case adapter.

Inputs (data/raw/tod_cases/nyc/, fetched by scripts/fetch_tod_cases.py):
- dob_nb_all.csv: Department of Buildings job filings, new-building jobs in all boroughs (document 01), with
  proposed dwelling units, the date the job was fully permitted, block and lot, and a geocoded point.
- nyzma.geojson: City Planning zoning map amendments with effective dates (official boundaries).
- bloomberg_rezonings.geojson: City Planning's list of city-initiated rezonings 2002-2013 (fetched for the pooled set).
- mappluto_<vintage>.zip, yearly archives 02b (March 2003) to 18v1: tax lots with zoning, land use, residential
  units and maximum allowed FAR. Each rezoning uses four snapshots (pick_vintages): start of its before years, just
  before, just after, and end of its after years.
- subway_stations.geojson: subway stations (second comparison).

Rules used here (docs/tod/CASE_RESULTS.md, section New York; areas by the uniform rule of CASE_ANALYSIS_PLAN.md
section 7, cases.uniform_areas):
- Treatment: lots (the "before" snapshot's polygons) whose representative point is inside the rezoning's zoning map
  amendment and whose allowed residential FAR rose between the before and after snapshots, unless already at the law.
- Lots whose allowed residential FAR changed between the start and before snapshots, outside the amendment between
  before and after, or anywhere between after and end, are in no area. Changes before March 2003 cannot be seen.
- Pooled set (build_pooled): Liao's 22 upzonings plus Park Slope, each built the same way within 1.5 km of its
  amendment, stacked in event time. No second comparison for the pooled set.
- Original rule (sensitivity): every lot in the amendment against its 1/4-mile ring.
- Outcome: proposed dwelling units of new-building jobs, by the year the job was fully permitted, one record per
  job number. Project (for resampling) = block and lot of the job.
- Dose: allowed residential FAR by district (RESID_FAR, from the Zoning Resolution's maximum residential FAR,
  Quality Housing where higher, no inclusionary bonus), new minus old, over eligible treatment land. PLUTO's
  maxAllwFAR (largest of residential, commercial and community-facility FAR) is reported as a check.
- Existing homes: residential units on the lots in MapPLUTO 02b.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "nyc"
CRS_M = 32118  # NAD83 / New York Long Island (metres)
ID_MATCH_MAX_M = 100.0
FIRST_YEAR, LAST_FULL_YEAR = 1991, 2025  # DOB BIS job filings; jobs filed in DOB NOW from about 2021 are not in this file

CASES = {
    "nyc_park_slope_fourth_ave_2003": {"ulurp": "030194azmk", "effective": "2003-04-30"},
    "nyc_downtown_brooklyn_2004": {"ulurp": "040171zmk", "effective": "2004-06-28"},
}

# Maximum residential FAR by residence district (Zoning Resolution 23-141/23-145 as in force 2002-2004; the higher of
# the height-factor and Quality Housing wide-street maximums, e.g. R6 3.0, R7 4.0, R8 7.2; no inclusionary bonus).
RESID_FAR = {
    "R1": 0.5, "R2": 0.5, "R2X": 0.85, "R3": 0.6, "R3A": 0.6, "R3X": 0.6, "R4": 0.9, "R4A": 0.9, "R4B": 0.9, "R5": 1.25,
    "R5A": 1.1, "R5B": 1.35, "R5D": 2.0, "R6": 3.0, "R6A": 3.0, "R6B": 2.0, "R7": 4.0, "R7A": 4.0, "R7B": 3.0,
    "R7D": 4.2, "R7X": 5.0, "R8": 7.2, "R8A": 6.02, "R8B": 4.0, "R8X": 6.02, "R9": 7.52, "R9A": 7.52, "R9X": 9.0,
    "R10": 10.0, "R10A": 10.0, "R10X": 10.0,
}
# Commercial districts: residential equivalent (ZR 35-23 / 34-112).
COMMERCIAL_EQUIV = {
    "C1-6": "R7", "C1-6A": "R7A", "C1-7": "R8", "C1-7A": "R8A", "C1-8": "R9", "C1-8A": "R9A", "C1-9": "R10",
    "C2-6": "R7", "C2-6A": "R7A", "C2-7": "R9", "C2-7A": "R9A", "C2-8": "R10",
    "C3": "R3", "C3A": "R3A", "C4-1": "R5", "C4-2": "R6", "C4-2A": "R6A", "C4-3": "R6", "C4-3A": "R6A", "C4-4": "R7",
    "C4-4A": "R7A", "C4-4D": "R8A", "C4-5": "R7", "C4-5A": "R7A", "C4-5X": "R7X", "C4-6": "R10", "C4-6A": "R10A", "C4-7": "R10",
    "C5-1": "R10", "C5-2": "R10", "C5-2A": "R10A", "C5-3": "R10", "C5-4": "R10", "C5-5": "R10",
    "C6-1": "R7", "C6-1A": "R6", "C6-2": "R8", "C6-2A": "R8A", "C6-3": "R9", "C6-3A": "R9A", "C6-3X": "R9X",
    "C6-4": "R10", "C6-4A": "R10A", "C6-4X": "R10X", "C6-4.5": "R10", "C6-5": "R10", "C6-6": "R10", "C6-7": "R10",
}


def zone_class(z: str | None) -> str | None:
    """res / com / mixed (eligible), ind (manufacturing, not eligible), park, or None."""
    if not isinstance(z, str) or not z.strip():
        return None
    s = z.upper().replace(" ", "")
    if s.startswith("PARK") or s in {"BPC", "NZS"}:
        return "park"
    if re.search(r"[/(]R\d", s) or (s.startswith("R") and re.search(r"\(M", s)):
        return "mixed"
    if s.startswith("R"):
        return "res"
    if s.startswith("C8") or s.startswith("C7"):
        return "com"  # commercial, though housing is not allowed (residential FAR 0)
    if s.startswith("C"):
        return "com"
    if s.startswith("M"):
        return "ind"
    return None


def resid_far(z: str | None) -> float:
    """Maximum residential FAR of a district string from PLUTO ('R6', 'C6-1', 'M1-2/R6A', 'R6(M1-2)')."""
    if not isinstance(z, str) or not z.strip():
        return float("nan")
    s = z.upper().replace(" ", "")
    m = re.search(r"(R\d+[A-Z]?)(?:-\d)?", s)
    if m and (s.startswith("R") or "/R" in s or "(R" in s):
        r = m.group(1)
        return RESID_FAR.get(r, RESID_FAR.get(r[:-1], float("nan")) if r[-1].isalpha() else float("nan"))
    if s.startswith("C"):
        base = re.match(r"(C\d(?:-\d(?:\.\d)?[A-Z]?)?)", s).group(1)
        eq = COMMERCIAL_EQUIV.get(base)
        if eq:
            return RESID_FAR[eq]
        return 0.0 if base.startswith(("C7", "C8")) else float("nan")
    if s.startswith("M"):
        return 0.0
    return float("nan")


# --------------------------------------------------------------------------- loading

# MapPLUTO archives and their nominal release dates (DCP releases; 02b is dated by its files, the others are set to
# the middle or end of their release year, so a rezoning's "before" and "after" snapshots are chosen with margins).
VINTAGES = {"02b": "2003-03-25", "03c": "2003-12-01", "04c": "2004-12-01", "05d": "2005-12-01", "06c": "2006-12-01",
            "07c": "2007-12-01", "08b": "2008-09-01", "09v1": "2009-06-01", "09v2": "2009-10-01", "10v1": "2010-06-01",
            "10v2": "2010-12-01", "11v1": "2011-06-01", "11v2": "2011-12-01", "12v1": "2012-06-01", "12v2": "2012-12-01",
            "13v1": "2013-06-01", "13v2": "2013-12-01", "14v1": "2014-06-01", "14v2": "2014-12-01", "15v1": "2015-06-01",
            "16v1": "2016-06-01", "17v1": "2017-06-01", "18v1": "2018-06-01"}
BEFORE_MARGIN_DAYS, AFTER_MARGIN_DAYS = 90, 150
BORO = {"BK": ("bk", "brooklyn", "BROOKLYN", "3"), "MN": ("mn", "manhattan", "MANHATTAN", "1"),
        "BX": ("bx", "bronx", "BRONX", "2"), "QN": ("qn", "queens", "QUEENS", "4"), "SI": ("si", "staten", "STATEN ISLAND", "5")}

# The pooled set: Liao (2026, Table 1) lists 22 city-initiated upzonings of 2004-2013 (aggregate residential capacity
# +20% or more); Park Slope (2003) is added as the plan's named 2003 member. ULURP numbers from City Planning's layers.
POOLED = {
    "030194azmk": ("Park Slope", "BK"), "040171zmk": ("Downtown Brooklyn", "BK"), "040273zmq": ("Hunters Point Subdistrict", "QN"),
    "040331zmm": ("Ladies Mile", "MN"), "050277zmq": ("East Flushing", "QN"), "050111azmk": ("Greenpoint-Williamsburg", "BK"),
    "040499azmm": ("Hudson Yards", "MN"), "050153zmq": ("Kew Gardens-Richmond Hill", "QN"),
    "050120zmx": ("Port Morris/Bruckner Blvd", "BX"), "050162azmm": ("West Chelsea/High Line", "MN"),
    "060471zmr": ("New Stapleton Waterfront", "SI"), "060335zmx": ("Pelham Parkway/Indian Village", "BX"),
    "070314azmq": ("Jamaica Plan", "QN"), "080099azmm": ("125th Street Corridor", "MN"), "090365zmx": ("161st Street", "BX"),
    "090272zmk": ("Coney Island", "BK"), "090310zmk": ("DUMBO", "BK"), "090303zmx": ("Lower Concourse", "BX"),
    "090104zmq": ("Special Forest Hills District", "QN"), "100369zmm": ("North Tribeca", "MN"),
    "100407zmx": ("Third Ave-Tremont Ave", "BX"), "110177zmm": ("West Clinton", "MN"), "130273zmx": ("East Fordham Road", "BX"),
}


def pick_vintages(eff: pd.Timestamp, before_start: int, after_end: int) -> dict:
    """start: last snapshot on or before 1 January of the first before year (or the first archive);
    before: last snapshot at least BEFORE_MARGIN_DAYS before the effective date; after: first snapshot at least
    AFTER_MARGIN_DAYS after it (build_member then moves it forward to the first snapshot that shows the change);
    end: first snapshot after the last after year (or the last archive)."""
    v = {k: pd.Timestamp(d) for k, d in VINTAGES.items()}
    keys = list(v)
    le = lambda t: [k for k in keys if v[k] <= t]  # noqa: E731
    ge = lambda t: [k for k in keys if v[k] >= t]  # noqa: E731
    start = (le(pd.Timestamp(f"{before_start}-01-01")) or keys[:1])[-1]
    before = (le(eff - pd.Timedelta(days=BEFORE_MARGIN_DAYS)) or keys[:1])[-1]
    after = (ge(eff + pd.Timedelta(days=AFTER_MARGIN_DAYS)) or keys[-1:])[0]
    end = (ge(pd.Timestamp(f"{after_end}-12-31")) or keys[-1:])[0]
    return {"start": start, "before": before, "after": after, "end": end}


def _shp(vintage: str, boro: str) -> str:
    import zipfile
    z = DIR / f"mappluto_{vintage}.zip"
    code, word = BORO[boro][0], BORO[boro][1]
    names = [n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith(".shp") and "mappinglot" not in n.lower()]
    hit = [n for n in names if (f"/{code}" in n.lower() or word in n.lower()) and "pluto" in n.lower()]
    hit = hit or [n for n in names if word in n.lower()]
    if not hit:
        raise FileNotFoundError(f"{vintage} {boro}: no borough shapefile in {names[:6]}")
    return f"zip://{z}!{sorted(hit, key=len)[0]}"


def _cols(path: str, wanted: list[str]) -> dict:
    import pyogrio
    fields = list(pyogrio.read_info(path)["fields"])
    low = {f.lower(): f for f in fields}
    return {w: low[w.lower()] for w in wanted if w.lower() in low}


_cache: dict = {}


def read_vintage(vintage: str, boro: str, bbox=None, base: bool = False):
    """Lots of one borough from one MapPLUTO archive (zoning only, or the base-year fields), in CRS_M."""
    import geopandas as gpd
    key = (vintage, boro, bbox, base)
    if key in _cache:
        return _cache[key]
    path = _shp(vintage, boro)
    want = ["zoneDist1"] + (["block", "lot", "landUse2", "LandUse", "unitsRes", "maxAllwFAR", "lotArea"] if base else ["maxAllwFAR"])
    cm = _cols(path, want)
    crs = gpd.read_file(path, rows=1).crs
    bb = None
    if bbox is not None:
        bb = tuple(gpd.GeoSeries([__import__("shapely").geometry.box(*bbox)], crs=CRS_M).to_crs(crs).total_bounds)
    g = gpd.read_file(path, columns=list(cm.values()), bbox=bb).to_crs(CRS_M)
    g = g.rename(columns={v: k for k, v in cm.items()})
    if "LandUse" in g.columns and "landUse2" not in g.columns:
        g = g.rename(columns={"LandUse": "landUse2"})
    g = g[g.geometry.notna() & ~g.geometry.is_empty].reset_index(drop=True)
    _cache[key] = g
    return g


def zone_at(pts, vintage: str, boro: str, bbox=None) -> tuple[pd.Series, pd.Series]:
    import geopandas as gpd
    z = read_vintage(vintage, boro, bbox)
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=pts, crs=CRS_M), z[["zoneDist1", "maxAllwFAR", "geometry"]] if "maxAllwFAR" in z
                  else z[["zoneDist1", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()].reindex(pts.index)
    mx = pd.to_numeric(j["maxAllwFAR"], errors="coerce") if "maxAllwFAR" in j else pd.Series(np.nan, index=pts.index)
    return j["zoneDist1"], mx


_jobs_cache: dict = {}


EXCLUDE_HOTELS = False   # lot model (LOT_MODEL_PLAN.md item 32) sets True; case results keep the original count


def hotel_lots() -> set[tuple[str, str, str]]:
    """(borough name, block, lot) of lots that MapPLUTO 18v1 classes as hotels with no residential units."""
    import zipfile
    import pyogrio
    z = zipfile.ZipFile(DIR / "mappluto_18v1.zip")
    out = set()
    for code, (_, _, name, _) in BORO.items():
        f = [n for n in z.namelist() if n.lower().endswith(f"{code.lower()}mappluto.dbf")]
        if not f:
            continue
        t = pyogrio.read_dataframe(f"/vsizip/{DIR / 'mappluto_18v1.zip'}/{f[0]}", columns=["Block", "Lot", "BldgClass", "UnitsRes"],
                                   read_geometry=False)
        h = t[t["BldgClass"].astype(str).str.upper().str.startswith("H") & (pd.to_numeric(t["UnitsRes"], errors="coerce").fillna(0) == 0)]
        out |= {(name, str(int(b)), str(int(l))) for b, l in zip(h["Block"], h["Lot"])}
    return out


def load_jobs(boro: str | None = None) -> pd.DataFrame:
    if "all" not in _jobs_cache:
        d = pd.read_csv(DIR / "dob_nb_all.csv", dtype=str)
        d = d.drop_duplicates("job__")
        if EXCLUDE_HOTELS:
            hl = hotel_lots()
            key = list(zip(d["borough"].astype(str).str.upper(), d["block"].astype(str).str.lstrip("0"), d["lot"].astype(str).str.lstrip("0")))
            hot = pd.Series([k in hl for k in key], index=d.index)
            print(f"  hotel jobs dropped: {int(hot.sum())} jobs, {int(pd.to_numeric(d.loc[hot, 'proposed_dwelling_units'], errors='coerce').fillna(0).sum())} units", flush=True)
            d = d[~hot]
        d["units"] = pd.to_numeric(d["proposed_dwelling_units"], errors="coerce").fillna(0)
        d["year"] = pd.to_numeric(d["fully_permitted"].str[-4:], errors="coerce")
        d = d[(d["units"] > 0) & d["year"].notna()]
        d["lat"] = pd.to_numeric(d["gis_latitude"], errors="coerce")
        d["lon"] = pd.to_numeric(d["gis_longitude"], errors="coerce")
        d["project"] = d["borough"].astype(str) + "-" + d["block"].astype(str) + "-" + d["lot"].astype(str)
        _jobs_cache["all"] = d.dropna(subset=["lat", "lon"])
    d = _jobs_cache["all"]
    return d if boro is None else d[d["borough"] == BORO[boro][2]]


def zoning_changed(z0: pd.Series, z1: pd.Series, f0: pd.Series, f1: pd.Series) -> pd.Series:
    """True where allowed residential FAR changed between two snapshots; where a FAR is unknown, where the district
    name changed. Lots missing from either snapshot count as unchanged."""
    a = z0.astype(str).str.upper().str.strip()
    b = z1.astype(str).str.upper().str.strip()
    known = f0.notna() & f1.notna()
    missing = z0.isna() | z1.isna()
    return ~missing & ((known & ((f0 - f1).abs() > 1e-9)) | (~known & (a != b)))


def locate_jobs(jg, lots, max_m: float = 40.0) -> pd.Series:
    """Index of the base-year lot for each job: same block and lot number first, unless that lot lies more than
    ID_MATCH_MAX_M from the job's own point; otherwise the lot containing or nearest to the job's geocoded point (DOB
    points sit on the street frontage), within max_m metres."""
    import geopandas as gpd
    key = lots["block"].astype(int).astype(str) + "-" + lots["lot"].astype(int).astype(str)
    lut = pd.Series(lots.index, index=key)
    lut = lut[~lut.index.duplicated()]
    jk = pd.to_numeric(jg["block"], errors="coerce").fillna(-1).astype(int).astype(str) + "-" + \
        pd.to_numeric(jg["lot"], errors="coerce").fillna(-1).astype(int).astype(str)
    ix = jk.map(lut)
    # an id match whose lot is far from the job's own point is not trusted (e.g. a Bergen Street job whose block and
    # lot point to a lot 1,345 m away): such jobs are placed by their point instead
    hit = ix.notna()
    if hit.any():
        d = jg.loc[hit].geometry.distance(lots.geometry.reindex(ix[hit].astype(int)).set_axis(jg.index[hit]), align=True)
        far = d[d > ID_MATCH_MAX_M].index
        ix.loc[far] = np.nan
        jg.attrs["rejected"] = int(len(far))
    miss = ix.isna()
    if miss.any():
        ix.loc[miss] = C.locate_points(jg.loc[miss], lots, max_m).values
    return ix


def build_member(ulurp: str, boro: str, whole_borough: bool = False, use_stations: bool = False) -> dict:
    """Areas, permits and dose of one rezoning under the uniform rule (cases.uniform_areas)."""
    import geopandas as gpd
    zma = gpd.read_file(DIR / "nyzma.geojson").to_crs(CRS_M)
    m = zma[zma["ULURPNO"].astype(str).str.lower() == ulurp]
    if m.empty or pd.isna(m["EFFECTIVE"].iloc[0]):
        bl = gpd.read_file(DIR / "bloomberg_rezonings.geojson").to_crs(CRS_M)
        m = bl[bl["ULURPNO"].astype(str).str.lower() == ulurp].rename(columns={"Adopted": "EFFECTIVE"})
    eff = pd.to_datetime(m["EFFECTIVE"].iloc[0], unit="ms").normalize()
    poly = m.geometry.union_all()
    eyear = eff.year
    per = C.period_years(eyear, FIRST_YEAR, LAST_FULL_YEAR)
    vs = pick_vintages(eff, per["before"][0], per["after"][-1])
    bbox = None if whole_borough else tuple(gpd.GeoSeries([poly], crs=CRS_M).buffer(1500).total_bounds)
    lots = read_vintage(vs["before"], boro, bbox, base=True).copy()
    pts = lots.geometry.representative_point()
    lots["zone_start"], _ = zone_at(pts, vs["start"], boro, bbox) if vs["start"] != vs["before"] else (lots["zoneDist1"], None)
    # PLUTO lags the zoning map: "after" is the first snapshot from AFTER_MARGIN_DAYS on in which at least 1% of the
    # amendment's lots show a different district (within 3 years), else the nominal pick
    keys = list(VINTAGES)
    cands = [k for k in keys[keys.index(vs["after"]):] if pd.Timestamp(VINTAGES[k]) <= eff + pd.Timedelta(days=3 * 365)]
    pin = pts[pts.within(poly)]
    for k in cands:
        z, _ = zone_at(pin, k, boro, bbox)
        if (z.astype(str).str.strip() != lots.loc[pin.index, "zoneDist1"].astype(str).str.strip()).mean() >= 0.01:
            vs["after"] = k
            break
    lots["zone_after"], lots["maxfar_after"] = zone_at(pts, vs["after"], boro, bbox)
    lots["zone_end"], _ = zone_at(pts, vs["end"], boro, bbox)
    for c in ("start", "after", "end"):
        lots[f"far_{c}"] = lots[f"zone_{c}"].map(resid_far)
    lots["far_before"] = lots["zoneDist1"].map(resid_far)
    lots["acres"] = lots.geometry.area / C.SQM_PER_ACRE
    lots["zclass"] = lots["zoneDist1"].map(zone_class)
    in_zma = pts.within(poly)
    rose = lots["far_after"] > lots["far_before"] + 1e-9
    changed = zoning_changed(lots["zone_start"], lots["zoneDist1"], lots["far_start"], lots["far_before"]) | \
        (~in_zma & zoning_changed(lots["zoneDist1"], lots["zone_after"], lots["far_before"], lots["far_after"])) | \
        zoning_changed(lots["zone_after"], lots["zone_end"], lots["far_after"], lots["far_end"])
    stations = None
    if use_stations:
        st = gpd.read_file(DIR / "subway_stations.geojson").to_crs(CRS_M)
        stations = st[st["Borough"].astype(str) == BORO[boro][3]].geometry
    lu = lots["landUse2"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
    lots["eligible"] = lots["zclass"].isin(["res", "com", "mixed"]) & ~lu.isin(["08", "09"])
    lots["area"], rule = C.uniform_areas(lots, in_zma, rose, lots["far_before"], lots["far_after"],
                                         pd.Series(True, index=lots.index), changed, lots["eligible"], stations=stations)
    el = lots[lots["area"].notna() & lots["eligible"]]
    jobs = load_jobs(boro)
    if bbox is not None:
        jobs = jobs[jobs["lon"].between(-74.3, -73.6)]
    jg = gpd.GeoDataFrame(jobs, geometry=gpd.points_from_xy(jobs["lon"], jobs["lat"]), crs=4326).to_crs(CRS_M)
    if bbox is not None:
        jg = jg.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    jg = jg[jg["year"].between(per["before"][0], per["after"][-1])].copy()
    jg["lot_ix"] = locate_jobs(jg, lots)
    jg["eligible"] = lots["eligible"].reindex(jg["lot_ix"]).fillna(False).astype(bool).values

    def permits_for(area: pd.Series) -> pd.DataFrame:
        q = jg.assign(area=area.reindex(jg["lot_ix"]).values)
        q = q[q["area"].notna() & q["eligible"]][["project", "area", "year", "units"]].copy()
        q["year"] = q["year"].astype(int)
        return q

    tr = el[el["area"] == C.TREAT]
    orig_area = C.assign_areas(lots, in_zma, stations=None)
    out = {
        "ulurp": ulurp, "boro": boro, "effective": eff, "effective_year": eyear, "per": per, "vintages": vs,
        "permits": permits_for(lots["area"]), "acres": el.groupby("area")["acres"].sum().to_dict(),
        "homes": el.groupby("area")["unitsRes"].sum().astype(float).to_dict() if "unitsRes" in el else {},
        "dose_table": tr.rename(columns={"far_before": "old_far", "far_after": "new_far"})[["acres", "old_far", "new_far"]],
        "original": (permits_for(orig_area), lots[orig_area.notna() & lots["eligible"]].groupby(orig_area)["acres"].sum().to_dict()),
        "capacity_ratio": float((lots.loc[in_zma, "far_after"] * lots.loc[in_zma, "acres"]).sum() /
                                max((lots.loc[in_zma, "far_before"] * lots.loc[in_zma, "acres"]).sum(), 1e-9)),
        "diag": {"rule": rule, "vintages": vs, "lots_in_amendment": int(in_zma.sum()), "treated_lots": int((lots["area"] == C.TREAT).sum()),
                 "zoning_before_treated": lots.loc[lots["area"] == C.TREAT, "zoneDist1"].value_counts().head(8).to_dict(),
                 "zoning_after_treated": lots.loc[lots["area"] == C.TREAT, "zone_after"].value_counts().head(8).to_dict(),
                 "lots_missing_far_in_amendment": int(lots.loc[in_zma, ["far_before", "far_after"]].isna().any(axis=1).sum()),
                 "dose_pluto_maxallwfar": round(C.dose(tr.assign(o=pd.to_numeric(tr.get("maxAllwFAR"), errors="coerce"), n=tr["maxfar_after"]), old="o", new="n"), 3),
                 "jobs_id_match_rejected_far_from_point": int(getattr(jg, "attrs", {}).get("rejected", 0)),
                 "second_comparison_stations": int(len(C.stations_not_upzoned(stations, tr.geometry.union_all()))) if stations is not None and len(tr) else 0},
    }
    return out


NAMED = {"nyc_park_slope_fourth_ave_2003": ("030194azmk", "BK"), "nyc_downtown_brooklyn_2004": ("040171zmk", "BK")}
CASES = NAMED  # run_tod_cases iterates CASES for the named members


def build(case: str) -> tuple[C.CaseInputs, dict]:
    ulurp, boro = NAMED[case]
    m = build_member(ulurp, boro, whole_borough=True, use_stations=True)
    ci = C.CaseInputs(case=case, role="fit", effective_year=m["effective_year"], first_year=FIRST_YEAR, last_full_year=LAST_FULL_YEAR,
                      permits=m["permits"], acres=m["acres"], homes=m["homes"], dose_table=m["dose_table"],
                      parking_change="none (minimums kept)", mandate="no",
                      notes="dose = residential FAR by district (Zoning Resolution); PLUTO maxAllwFAR dose in CASE_RESULTS.md",
                      original_spec=m["original"])
    diag = dict(m["diag"], original_rule_acres={k: round(v, 1) for k, v in m["original"][1].items()})
    return ci, diag


def build_pooled() -> tuple[C.CaseInputs, dict]:
    """The pooled set, stacked in event time: event year 0 is each member's effective year; units and acres are
    summed across members (each member's projects stay distinct). Members without 6 before and 5 after years in the
    data, or without treated land, are left out and listed."""
    allp, acres, homes, doses, orig_p, orig_a, diag = [], {}, {}, [], [], {}, {"members": {}}
    for ulurp, (name, boro) in POOLED.items():
        try:
            m = build_member(ulurp, boro)
        except Exception as e:  # noqa: BLE001
            diag["members"][name] = {"error": f"{type(e).__name__}: {e}"}
            continue
        per = m["per"]
        ok = len(per["before"]) == C.BEFORE_MAX and len(per["after"]) == len(C.AFTER_YEARS) and m["acres"].get(C.TREAT)
        d = dict(m["diag"], effective=str(m["effective"].date()), capacity_ratio=round(m["capacity_ratio"], 3),
                 acres={k: round(v, 1) for k, v in m["acres"].items()}, included=bool(ok),
                 dose=round(C.dose(m["dose_table"]), 3) if len(m["dose_table"]) else None)
        if m["acres"].get(C.TREAT) and m["acres"].get(C.COMP):
            d["member_did"] = round(C.did(m["permits"], m["acres"], per["before"], per["after"])["did"], 4)
        diag["members"][name] = d
        if not ok:
            continue
        e0 = m["effective_year"]
        for src, dst in ((m["permits"], allp), (m["original"][0], orig_p)):
            q = src.copy()
            q["year"] = q["year"] - e0
            q["project"] = ulurp + ":" + q["project"].astype(str)
            dst.append(q)
        for a, v in m["acres"].items():
            acres[a] = acres.get(a, 0.0) + v
        for a, v in m["homes"].items():
            homes[a] = homes.get(a, 0.0) + v
        for a, v in m["original"][1].items():
            orig_a[a] = orig_a.get(a, 0.0) + v
        doses.append(m["dose_table"])
    permits = pd.concat(allp, ignore_index=True)
    ci = C.CaseInputs(case="nyc_pooled_2003_2013", role="fit", effective_year=0, first_year=-C.BEFORE_MAX,
                      last_full_year=max(C.AFTER_YEARS), permits=permits, acres=acres, homes=homes,
                      dose_table=pd.concat(doses, ignore_index=True), parking_change="none (minimums kept)", mandate="no",
                      notes="stacked in event time: 'year' is years since each member's effective date; no second comparison",
                      original_spec=(pd.concat(orig_p, ignore_index=True), orig_a))
    diag["included"] = [n for n, d in diag["members"].items() if d.get("included")]
    return ci, diag

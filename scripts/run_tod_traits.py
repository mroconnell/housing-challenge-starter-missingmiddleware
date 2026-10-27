"""Run the TOD trait test (docs/tod/TRAITS_PLAN.md) in its pre-set order.

    uv run --all-extras python scripts/run_tod_traits.py --stage fetch    # trait sources (ACS, TIGER 2010, EPA SLD)
    uv run --all-extras python scripts/run_tod_traits.py --stage units    # 1. unit list, fixed before any trait
    uv run --all-extras python scripts/run_tod_traits.py --stage traits   # 2. trait values for the fixed units
    uv run --all-extras python scripts/run_tod_traits.py --stage test     # 3. held-out test (+ 4. Wisconsin if a trait passes)
    uv run --all-extras python scripts/run_tod_traits.py --stage explore  # owner-approved exploration: 66 pairs + one tree

Units are built with the case adapters (missing_middleware/tod/case_*.py, imported, never edited) and the Madison
test script. Station-area units re-use each case's own areas: the case's builder runs unchanged while
`cases.uniform_areas` and `cases.locate_points` are wrapped to record the lots, their areas and each permit's lot.

Outputs (committed; no parcel, permit, project or person identifiers):
- reference/tod_trait_units.csv        one row per unit: city, name, eligible acres, effect with 90% interval, dose
- reference/tod_trait_values.csv       one row per unit: the 12 traits
- reference/tod_trait_results.csv      one row per model (baseline, each trait, two-trait models): verdict, errors
- reference/tod_trait_errors.csv       one row per model and city: held-out errors and predicted vs measured means
- reference/tod_trait_heldout_units.csv  Chicago and Madison units: measured and predicted effects by model
- reference/tod_trait_wisconsin.csv    only if a trait passes (sensitivity; model outputs unchanged)
- reference/tod_trait_pairs.csv        exploratory: all 66 pairs under the stricter rule
- reference/tod_trait_tree.csv         exploratory: the regression tree (splits, held-out errors, verdict)
Caches (git-ignored): data/processed/tod_traits/
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
import re
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE, processed_dir  # noqa: E402
from missing_middleware.tod import cases as C  # noqa: E402
from missing_middleware.tod import traits as T  # noqa: E402

OUT = processed_dir("tod_traits")
RAWT = RAW / "tod_traits"
UNITS_CSV = REFERENCE / "tod_trait_units.csv"
VALUES_CSV = REFERENCE / "tod_trait_values.csv"
RESULTS_CSV = REFERENCE / "tod_trait_results.csv"
ERRORS_CSV = REFERENCE / "tod_trait_errors.csv"
HELDOUT_CSV = REFERENCE / "tod_trait_heldout_units.csv"
WI_CSV = REFERENCE / "tod_trait_wisconsin.csv"
PAIRS_CSV = REFERENCE / "tod_trait_pairs.csv"
TREE_CSV = REFERENCE / "tod_trait_tree.csv"
CITIES = ("nyc", "philadelphia", "charlotte", "stpaul", "chicago", "madison")
CITY_NAME = {"nyc": "New York", "philadelphia": "Philadelphia", "charlotte": "Charlotte", "stpaul": "Saint Paul",
             "chicago": "Chicago", "madison": "Madison"}
CASE_OF = {"nyc": "nyc_pooled_2003_2013", "philadelphia": "philadelphia_2012_remapping", "charlotte": "charlotte_tod_2019",
           "stpaul": "stpaul_green_line_2011", "chicago": "chicago_tod_2013_2015", "madison": "madison_tod_overlay_2023"}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


# =========================================================================== 1. units

@contextmanager
def capture():
    """Record what the case builders pass to and get from cases.uniform_areas and cases.locate_points."""
    rec = {"uniform": [], "locate": []}
    ou, ol = C.uniform_areas, C.locate_points

    def u(parcels, *a, **k):
        r = ou(parcels, *a, **k)
        rec["uniform"].append(parcels)
        return r

    def loc(points, parcels, *a, **k):
        r = ol(points, parcels, *a, **k)
        rec["locate"].append(r)
        return r
    C.uniform_areas, C.locate_points = u, loc
    try:
        yield rec
    finally:
        C.uniform_areas, C.locate_points = ou, ol


def unit_row(city: str, unit_id: str, name: str, unit_type: str, eff: int, per: dict, permits: pd.DataFrame,
             acres: dict, dose: float, dose_unit: str, note: str = "") -> dict:
    ok, reason = T.keep_unit(acres.get(C.TREAT, 0.0), acres.get(C.COMP, 0.0))
    b, a = per["before"], per["after"]
    e = T.unit_estimate(permits, acres, b, a) if ok else T.unit_estimate(permits, acres, [], [])
    if not ok and acres.get(C.TREAT) and acres.get(C.COMP) and b and a:
        e.update({k: v for k, v in C.did(permits, acres, b, a).items()})  # shown, not used
    fmt = (lambda y: f"{y[0]} to {y[-1]}" if y else "")
    return {"unit_id": unit_id, "city": CITY_NAME[city], "case": CASE_OF[city], "unit_name": name, "unit_type": unit_type,
            "role": "always held out" if city in ("chicago", "madison") else "fit (leave-one-city-out)",
            "effective_year": eff, "before_years": fmt(b), "after_years": fmt(a),
            "treatment_acres": round(acres.get(C.TREAT, 0.0), 2), "comparison_acres": round(acres.get(C.COMP, 0.0), 2),
            "kept": ok, "reason": reason,
            "effect": e["did"], "interval90_low": e["low"], "interval90_high": e["high"],
            "treat_rate_before": e["treat_before"], "treat_rate_after": e["treat_after"],
            "comp_rate_before": e["comp_before"], "comp_rate_after": e["comp_after"],
            "treatment_units_before": T.units_in(permits, C.TREAT, b), "treatment_units_after": T.units_in(permits, C.TREAT, a),
            "comparison_units_before": T.units_in(permits, C.COMP, b), "comparison_units_after": T.units_in(permits, C.COMP, a),
            "dose": dose, "dose_unit": dose_unit, "note": note}


def treat_frame(lots, idx, unit_id: str, vpi: pd.Series, homes: pd.Series | None, old: pd.Series | None,
                new: pd.Series | None, developed: pd.Series | None):
    """Treatment lots of a unit, with what the traits need (no identifiers)."""
    import geopandas as gpd
    g = gpd.GeoDataFrame({"unit_id": unit_id, "acres": lots.loc[idx].geometry.area / C.SQM_PER_ACRE,
                          "vpi": vpi.reindex(idx).astype(float).values,
                          "homes_before": homes.reindex(idx).astype(float).values if homes is not None else np.nan,
                          "old_level": old.reindex(idx).astype(float).values if old is not None else np.nan,
                          "new_level": new.reindex(idx).astype(float).values if new is not None else np.nan,
                          "developed": developed.reindex(idx).astype(float).values if developed is not None else np.nan},
                         geometry=lots.loc[idx].geometry.values, crs=lots.crs)
    return g


def station_units(city: str, parcels, permits: pd.DataFrame, pix: pd.Series, stations, eff: int, per: dict,
                  vpi: pd.Series, old: pd.Series, new: pd.Series, dose_unit: str, unit_type: str = "station area",
                  labels: pd.Series | None = None, prefix: str = "", homes: pd.Series | None = None):
    """Split a case's treatment into units (nearest station, or given labels), each against the case's comparison
    lots within 1/4 mile of the unit's own treatment lots."""
    el = parcels["eligible"].astype(bool)
    tr = parcels.index[(parcels["area"] == C.TREAT) & el]
    cp = parcels.index[(parcels["area"] == C.COMP) & el]
    if labels is None:
        labels = T.nearest_station(parcels.loc[tr].geometry.representative_point(), stations)
    labels = labels.reindex(tr)
    acres = parcels.geometry.area / C.SQM_PER_ACRE
    p = permits.copy()
    p["pix"] = pix.reindex(p.index).values
    yrs = per["before"] + per["after"]
    dev = pd.Series(False, index=parcels.index)
    dev.loc[p.loc[p["year"].isin(yrs) & p["pix"].notna(), "pix"].astype(int).unique()] = True
    rows, frames = [], []
    for lab in sorted(labels.dropna().unique()):
        ti = labels.index[labels == lab]
        ci = T.comparison_for_unit(parcels, ti, cp)
        pu = p[((p["area"] == C.TREAT) & p["pix"].isin(ti)) | ((p["area"] == C.COMP) & p["pix"].isin(ci))]
        a = {C.TREAT: float(acres[ti].sum()), C.COMP: float(acres[ci].sum())}
        sub = pd.DataFrame({"acres": acres[ti], "old_far": old.reindex(ti), "new_far": new.reindex(ti)})
        d = C.dose(sub.replace([np.inf, -np.inf], np.nan)) if dose_unit != "none" else np.nan
        uid = f"{prefix}{slug(lab)}"
        rows.append(unit_row(city, uid, f"{CITY_NAME[city]}: {lab}", unit_type, eff, per,
                             pu[["project", "area", "year", "units"]], a, d, dose_unit))
        frames.append(treat_frame(parcels, ti, uid, vpi, homes, old, new, dev))
    return rows, frames


def build_nyc():
    from missing_middleware.tod import case_nyc as N
    rows, frames, diag = [], [], {}
    for k, (ulurp, (name, boro)) in enumerate(N.POOLED.items()):
        with capture() as cap:
            try:
                m = N.build_member(ulurp, boro)
            except Exception as e:  # noqa: BLE001
                diag[name] = f"{type(e).__name__}: {e}"
                continue
        per = m["per"]
        full = len(per["before"]) == C.BEFORE_MAX and len(per["after"]) == len(C.AFTER_YEARS)
        if not (full and m["acres"].get(C.TREAT)):
            diag[name] = "not in the pooled set (no eligible treated land or incomplete window)"
            continue
        lots = cap["uniform"][-1]
        uid = f"nyc_{slug(name)}"
        dose = C.dose(m["dose_table"]) if len(m["dose_table"]) else np.nan
        rows.append(unit_row("nyc", uid, f"New York: {name}", "rezoning (pooled-set member)", m["effective_year"], per,
                             m["permits"], m["acres"], dose, "added FAR"))
        tr = lots.index[(lots["area"] == C.TREAT) & lots["eligible"].astype(bool)]
        lu = lots["landUse2"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
        vpi = lu.isin(["06", "10", "11"])  # PLUTO land use: industrial and manufacturing, parking, vacant
        homes = pd.to_numeric(lots["unitsRes"], errors="coerce").fillna(0)
        frames.append(treat_frame(lots, tr, uid, vpi, homes, lots["far_before"], lots["far_after"], None))
        diag[name] = "unit"
    return rows, frames, diag


def build_philadelphia():
    from missing_middleware.tod import case_philadelphia as P
    d = P._load()
    rm = d["rm"]
    dp = rm[(rm["Origination"] == "DistrictPlan") & rm["changes"] & rm["enacted"].dt.year.between(*P.MEMBER_YEARS)]
    bills = sorted(dp["Bill_Number_TXT"].astype(str).unique())
    rows, frames, diag = [], [], {}
    VPI = re.compile(r"^VAC|PARKING|^IND|INDUST|WHSE|WAREHOUSE", re.I)
    for b in bills:
        m = P.build_member(b)
        if not m["acres"].get(C.TREAT, 0) > 0:
            diag[b] = "no eligible treated land"
            continue
        uid = f"phl_{slug(b)}"
        per = m["per"]
        rows.append(unit_row("philadelphia", uid, f"Philadelphia: bill {b} ({m['name']})", "remapping bill",
                             m["effective"].year, per, m["permits"], m["acres"], np.nan, "none (height-only districts)"))
        tr = m["treated"]
        pix = d["permits"]["pix"].reindex(m["permits"].index)
        yrs = per["before"] + per["after"]
        pp = m["permits"].assign(pix=pix.values)
        dev = pd.Series(tr.index.isin(pp.loc[pp["year"].isin(yrs) & (pp["area"] == C.TREAT), "pix"].dropna().astype(int)), index=tr.index)
        vpi = tr["bldg_desc"].astype(str).str.contains(VPI)
        frames.append(treat_frame(tr, tr.index, uid, vpi, None, None, None, dev))
        diag[b] = "unit"
    return rows, frames, diag


def _stops(path, crs, keep=None):
    import geopandas as gpd
    s = gpd.read_file(path).to_crs(crs)
    if keep is not None:
        s = s[keep(s)]
    return T.cluster_stations(s, s["stop_name"].reset_index(drop=True))


def build_charlotte():
    from missing_middleware.tod import case_charlotte as K
    with capture() as cap:
        ci, _ = K.build()
    parcels, pix = cap["uniform"][0], cap["locate"][0]
    per = C.period_years(K.EFFECTIVE_YEAR, K.FIRST_YEAR, K.LAST_FULL_YEAR)
    st = _stops(K.DIR / "rail_stops.geojson", K.CRS_M)
    lu = parcels["landuse_description"].astype(str)
    vpi = lu.str.contains(r"PARKING|INDUSTRIAL|WAREHOUSE", case=False) | (parcels["txt_vacantorimproved"].astype(str).str.upper() == "VACANT")
    rows, frames = station_units("charlotte", parcels, ci.permits, pix, st, K.EFFECTIVE_YEAR, per, vpi,
                                 parcels["h_before"], parcels["h_after"], "added height (ft)", prefix="clt_")
    return rows, frames, {"stations": len(st)}


def build_chicago():
    from missing_middleware.tod import case_chicago as K
    import geopandas as gpd
    with capture() as cap:
        ci, _ = K.build()
    parcels, pix = cap["uniform"][0], cap["locate"][-1]
    per = C.period_years(K.EFFECTIVE_YEAR, K.FIRST_YEAR, K.LAST_FULL_YEAR)
    s = gpd.read_file(K.DIR / "rail_stops.geojson").to_crs(K.CRS_M)
    s = s[s.geometry.within(parcels.union_all().convex_hull)].reset_index(drop=True)
    st = T.cluster_stations(s, s["stop_name"])
    cls = parcels["assessorbldgclass"].astype(str).str.strip()
    # Cook County Assessor classes: 100 vacant land, 190 minor improvement on vacant land, 241 vacant land under
    # common ownership with adjacent residence; 550-599 industrial (5B) except 590 commercial minor improvement, which
    # is counted too (mostly parking lots and yards)
    num = pd.to_numeric(cls, errors="coerce")
    vpi = cls.isin(["100", "190", "241"]) | num.between(550, 599)
    rows, frames = station_units("chicago", parcels, ci.permits, pix, st, K.EFFECTIVE_YEAR, per, vpi,
                                 parcels["far_before"], parcels["far_after"], "added FAR", prefix="chi_")
    return rows, frames, {"stations": len(st)}


def build_stpaul():
    from missing_middleware.tod import case_stpaul as K
    with capture() as cap:
        ci, _ = K.build()
    parcels, pix = cap["uniform"][0], cap["locate"][-1]
    per = C.period_years(K.EFFECTIVE_YEAR, K.FIRST_YEAR, K.LAST_FULL_YEAR)
    st = _stops(K.DIR / "rail_stops.geojson", K.CRS_M, keep=lambda s: s["stop_name"].astype(str).str.contains(K.GREEN_LINE_STP))
    lu = parcels["LandUseCodeDescription"].astype(str)
    vpi = lu.str.contains(r"VACANT|PARKING|^IND|INDUSTRIAL|MANUFACTUR|WAREHOUSE", case=False)
    rows, frames = station_units("stpaul", parcels, ci.permits, pix, st, K.EFFECTIVE_YEAR, per, vpi,
                                 parcels["far_before"], parcels["far_after"].replace(np.inf, np.nan), "added FAR", prefix="stp_")
    for r in rows:
        r["note"] = "case is context only (1 before year: 2010)"
    return rows, frames, {"stations": len(st)}


CAPITOL_LONLAT = (-89.38421, 43.07466)   # Wisconsin State Capitol, Madison
MADISON_CORE_M = 1609.344                # 1 mile


def build_madison():
    import geopandas as gpd
    spec = importlib.util.spec_from_file_location("run_tod_madison_test", ROOT / "scripts" / "run_tod_madison_test.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    from missing_middleware.permits import madison
    from missing_middleware.permits.match import AddressIndex
    from missing_middleware.tod import madison_test as MT
    L = M.lots()
    parcels_tbl = madison.parcel_table(madison.load_parcels(RAW / "madison_parcels"))
    ref = madison.address_reference(parcels_tbl, madison.load_address_points(RAW / "madison_parcels"))
    index = AddressIndex(ref)
    ref_pts = M.ref_points(index.ref)
    changed, _ = M.rezoned_lots(L, index, ref_pts)
    L["changed"] = changed
    # the Madison test's areas, exactly as in run_tod_madison_test.main
    area, uinfo = C.uniform_areas(L, in_reform=L.in_overlay, rose=L.rose, level_before=L.far_base, level_after=L.far_ovl,
                                  uncapped_before=L.uncapped, changed_outside=L.changed, eligible=L.elig)
    med = uinfo["median_new_level_on_rising_land"]
    at_law = L.uncapped & (L.far_base.fillna(-1) >= med)
    excluded = (L.in_overlay & (area != C.TREAT)) | at_law | L.changed
    L["area"] = area.where(~excluded, None)
    L["eligible"] = L["elig"]
    d = M.permits_on_lots(L, index, ref_pts, parcels_tbl)
    x = d[d.placed].copy()
    x["area"] = L["area"].reindex(x.lot.astype(int)).values
    x["elig"] = L.elig.reindex(x.lot.astype(int)).values
    x = x[x.elig.astype(bool) & x.area.notna()]
    permits = x[["project", "area", "year", "units"]]
    pix = x["lot"].astype(int)
    per = {"before": list(MT.BEFORE), "after": list(MT.AFTER)}
    cx = gpd.GeoSeries(gpd.points_from_xy([CAPITOL_LONLAT[0]], [CAPITOL_LONLAT[1]]), crs=4326).to_crs(L.crs).iloc[0]
    tr = L.index[(L["area"] == C.TREAT) & L["eligible"].astype(bool)]
    rp = L.loc[tr].geometry.representative_point()
    names = {"core": "Isthmus core (within 1 mile of the Capitol)"}
    lab = pd.Series([names.get(s, f"{s} of the core") for s in
                     (T.sector_label(p.x - cx.x, p.y - cx.y, MADISON_CORE_M) for p in rp)], index=tr)
    vpi = L["use_class"].isin(["vacant", "parking", "industrial"])
    rows, frames = station_units("madison", L, permits, pix, None, 2023, per, vpi, L["far_base"].where(np.isfinite(L["far_base"])),
                                 L["far_base"].where(np.isfinite(L["far_base"])) + L["added_far"], "added FAR",
                                 unit_type="corridor segment", labels=lab, prefix="mad_", homes=L["homes"])
    return rows, frames, {"segments": int(lab.nunique()), "uniform_rule": uinfo}


BUILDERS = {"nyc": build_nyc, "philadelphia": build_philadelphia, "charlotte": build_charlotte, "stpaul": build_stpaul,
            "chicago": build_chicago, "madison": build_madison}


def stage_units(cities, rebuild: bool) -> None:
    for c in cities:
        f = OUT / f"units_{c}.pkl"
        if f.exists() and not rebuild:
            print(f"{c}: cached")
            continue
        print(f"== {c}", flush=True)
        rows, frames, diag = BUILDERS[c]()
        f.write_bytes(pickle.dumps({"rows": rows, "frames": frames, "diag": diag}))
        print(f"{c}: {len(rows)} candidate units, {sum(r['kept'] for r in rows)} kept", flush=True)
    write_units()


def load_city(c: str) -> dict:
    return pickle.loads((OUT / f"units_{c}.pkl").read_bytes())


def write_units() -> pd.DataFrame:
    rows = []
    for c in CITIES:
        if (OUT / f"units_{c}.pkl").exists():
            rows += load_city(c)["rows"]
    u = pd.DataFrame(rows)
    u["city"] = pd.Categorical(u["city"], T.CITY_ORDER, ordered=True)
    u = u.sort_values(["city", "unit_id"]).reset_index(drop=True)
    u["city"] = u["city"].astype(str)
    for k in ("effect", "interval90_low", "interval90_high", "treat_rate_before", "treat_rate_after", "comp_rate_before", "comp_rate_after"):
        u[k] = u[k].astype(float).round(4)
    u["dose"] = u["dose"].astype(float).round(3)
    bad = T.check_private(u, allowed=set())
    assert not bad, bad
    u.to_csv(UNITS_CSV, index=False, lineterminator="\n")
    print(u.groupby("city", sort=False).agg(candidates=("unit_id", "size"), kept=("kept", "sum"),
                                            treat_acres_kept=("treatment_acres", lambda s: s[u.loc[s.index, "kept"]].sum())).to_string())
    return u


# =========================================================================== fetch (trait sources)

ACS10_STATES = {"36": "NewYork", "42": "Pennsylvania", "37": "NorthCarolina", "17": "Illinois", "27": "Minnesota"}
ACS10_URL = "https://www2.census.gov/programs-surveys/acs/summary_file/2010/data/5_year_by_state/{s}_Tracts_Block_Groups_Only.zip"
ACS10_SEQ_URL = "https://www2.census.gov/acs2010_5yr/summaryfile/2006-2010_ACSSF_By_State_By_Sequence_Table_Subset/NewYork/Tracts_Block_Groups_Only"
ACS10_LOOKUP = "https://www2.census.gov/programs-surveys/acs/summary_file/2010/documentation/5_year/user_tools/Sequence_Number_and_Table_Number_Lookup.txt"
TIGER10_URL = "https://www2.census.gov/geo/tiger/TIGER2010/TRACT/2010/tl_2010_{st}_tract10.zip"
ACS22_URL = "https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/acsdt5y2022-{t}.dat"
SLD_LAYER = "https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/16"
SLD_COUNTIES = {"36": ["005", "047", "061", "081", "085"], "42": ["101"], "37": ["119"], "17": ["031"], "27": ["123"],
                "55": ["025", "035", "059", "079", "089", "133"]}
CENSUS_LICENCE = "Public domain (U.S. government work)"
SLD_LICENCE = "Public domain (U.S. EPA Smart Location Database v3, U.S. government work)"


def stage_fetch(refresh: bool = False, parts=("acs", "sld")) -> None:
    import hashlib
    import fetch_tod_cases as F
    FT = F
    man = F.Manifest(RAWT, "tod_traits", "U.S. Census Bureau; U.S. EPA")
    _dl = F.download_file

    def download(man, name, url, refresh, licence, **kw):
        """Files fetched earlier with curl (same URL) are hashed into the manifest instead of fetched again."""
        p = RAWT / name
        if p.exists() and name not in man.m["files"] and not refresh:
            b = p.read_bytes()
            man.m["files"][name] = {"url": url, "accessed_utc": FT.now(), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                                    "licence": licence, **{k: v for k, v in kw.items() if k != "timeout"}}
            man.save()
            print(f"  {name}: registered ({len(b):,} bytes)")
            return
        _dl(man, name, url, refresh, licence, **kw)
    F = type("F", (), {"download_file": staticmethod(download), "save_layer": staticmethod(F.save_layer)})
    for st, name in (ACS10_STATES.items() if "acs" in parts else []):
        if name == "NewYork":  # the whole-state zip stalls on the Census server; the per-sequence files are the same release
            for f in ("20105ny0053000.zip", "20105ny0098000.zip", "20105ny0099000.zip", "g20105ny.txt"):
                F.download_file(man, f"acs2010/NewYork_seq/{f}", f"{ACS10_SEQ_URL}/{f}", refresh, CENSUS_LICENCE, timeout=3600,
                                note="ACS 2006-2010 5-year summary file, tracts and block groups, one sequence")
        else:
            F.download_file(man, f"acs2010/{name}_Tracts_Block_Groups_Only.zip", ACS10_URL.format(s=name), refresh, CENSUS_LICENCE,
                            timeout=3600, note="ACS 2006-2010 5-year summary file, tracts and block groups")
        F.download_file(man, f"tiger2010/tl_2010_{st}_tract10.zip", TIGER10_URL.format(st=st), refresh, CENSUS_LICENCE)
    if "acs" in parts:
        F.download_file(man, "acs2010/Sequence_Number_and_Table_Number_Lookup.txt", ACS10_LOOKUP, refresh, CENSUS_LICENCE)
    for t in (("b25064", "b25077", "b19013") if "acs" in parts else ()):
        F.download_file(man, f"acs2022/acsdt5y2022-{t}.dat", ACS22_URL.format(t=t), refresh, CENSUS_LICENCE, timeout=3600,
                        note="ACS 2018-2022 5-year table-based summary file")
    for st, cos in (SLD_COUNTIES.items() if "sld" in parts else []):
        name = f"sld/sld_d5br_{st}.geojson"
        where = f"STATEFP='{st}' AND COUNTYFP IN ({','.join(repr(c) for c in cos)})"
        F.save_layer(man, name, SLD_LAYER, refresh, SLD_LICENCE, where=where,
                     out_fields="GEOID10,GEOID20,STATEFP,COUNTYFP,D5BR,TotEmp,Ac_Land", page=1000)
    print("fetched trait sources into", RAWT)


# =========================================================================== 2. traits

def acs2010_tract_values() -> pd.DataFrame:
    """Tract medians from the ACS 2006-2010 5-year summary file (2010 dollars): B25077 home value, B19013 income,
    B25064 gross rent. Sequence and position from the Census lookup file."""
    import zipfile
    look = pd.read_csv(RAWT / "acs2010" / "Sequence_Number_and_Table_Number_Lookup.txt", dtype=str, encoding="latin-1")
    pos = {}
    for t in ("B25077", "B19013", "B25064"):
        r = look[(look["Table ID"] == t) & look["Start Position"].notna()].iloc[0]
        pos[t] = (int(r["Sequence Number"]), int(r["Start Position"]))
    out = []
    for st, name in ACS10_STATES.items():
        whole = RAWT / "acs2010" / f"{name}_Tracts_Block_Groups_Only.zip"
        if whole.exists():
            z = zipfile.ZipFile(whole)
            names = z.namelist()
            gtext = z.open(next(n for n in names if re.search(r"g20105\w\w\.txt$", n, re.I))).read()
            efile = lambda seq: z.open(next(n for n in names if re.search(rf"e20105\w\w{seq:04d}000\.txt$", n, re.I)))  # noqa: E731
        else:  # the per-sequence files of the same release (New York: the whole-state zip would not download)
            d = RAWT / "acs2010" / f"{name}_seq"
            gtext = next(d.glob("g20105*.txt")).read_bytes()
            efile = lambda seq, d=d: (lambda zz: zz.open(next(n for n in zz.namelist() if n.startswith("e"))))(  # noqa: E731
                zipfile.ZipFile(next(d.glob(f"20105*{seq:04d}000.zip"))))
        # fixed-width geography file: SUMLEVEL at columns 9-11, LOGRECNO 14-20, GEOID 179-218 (1-based)
        lines = gtext.decode("latin-1").splitlines()
        g = pd.DataFrame({"logrecno": [s[13:20] for s in lines], "geoid": [s[178:218].strip() for s in lines]})
        g = g[g["geoid"].str.startswith("14000US")].copy()
        g["tract"] = g["geoid"].str[7:]
        vals = {}
        for t, (seq, start) in pos.items():
            e = pd.read_csv(efile(seq), header=None, dtype=str, encoding="latin-1")
            vals[t] = pd.Series(pd.to_numeric(e[start - 1], errors="coerce").values, index=e[5].astype(str).str.strip())
        for t, s in vals.items():
            g[t] = g["logrecno"].map(s)
        out.append(g)
    a = pd.concat(out, ignore_index=True)
    return a.rename(columns={"B25077": "home_value", "B19013": "income", "B25064": "rent"})[["tract", "home_value", "income", "rent"]]


def acs_tbsf_tract_values(folder: Path, year: int) -> pd.DataFrame:
    """Tract medians from an ACS table-based summary file (pipe-delimited, all geographies)."""
    cols = {"b25077": ("home_value", "B25077_E001"), "b19013": ("income", "B19013_E001"), "b25064": ("rent", "B25064_E001")}
    res = None
    for t, (name, col) in cols.items():
        f = folder / f"acsdt5y{year}-{t}.dat"
        d = pd.read_csv(f, sep="|", dtype=str, usecols=["GEO_ID", col])
        d = d[d["GEO_ID"].str.startswith("1400000US")]
        d = pd.DataFrame({"tract": d["GEO_ID"].str[9:], name: pd.to_numeric(d[col], errors="coerce")})
        res = d if res is None else res.merge(d, on="tract", how="outer")
    return res


def tract_shapes(kind: str):
    import geopandas as gpd
    if kind == "2010":
        gs = [gpd.read_file(f"zip://{RAWT / 'tiger2010' / f'tl_2010_{st}_tract10.zip'}")[["GEOID10", "geometry"]].rename(columns={"GEOID10": "tract"})
              for st in ACS10_STATES]
        return pd.concat(gs, ignore_index=True)
    g = gpd.read_file(f"zip://{RAW / 'census_tiger_2024' / 'tl_2024_55_tract.zip'}")[["GEOID", "geometry"]]
    return g.rename(columns={"GEOID": "tract"})


def blocks_2010_points(state: str, bbox_4269):
    import geopandas as gpd
    bz = RAW / "tod_cases" / "census_2010_blocks" / f"tabblock2010_{state}_pophu.zip"
    b = gpd.read_file(bz, bbox=bbox_4269)
    return gpd.GeoDataFrame({"homes": b["HOUSING10"].astype(float)}, geometry=b.geometry.representative_point(), crs=b.crs)


GAZ_PLACES = {"New York": ("36", "New York city"), "Philadelphia": ("42", "Philadelphia city"), "Charlotte": ("37", "Charlotte city"),
              "Saint Paul": ("27", "St. Paul city"), "Chicago": ("17", "Chicago city"), "Madison": ("55", "Madison city")}
# Downtown points (written down before joining): each city's City Hall, or the State Capitol in Madison.
DOWNTOWN = {"New York": (-74.00597, 40.71274, "New York City Hall (Manhattan)"),
            "Philadelphia": (-75.16357, 39.95233, "Philadelphia City Hall"),
            "Charlotte": (-80.84313, 35.22709, "Trade and Tryon (the Square), Uptown Charlotte"),
            "Saint Paul": (-93.09356, 44.94418, "Saint Paul City Hall"),
            "Chicago": (-87.63191, 41.88372, "Chicago City Hall"),
            "Madison": (-89.38421, 43.07466, "Wisconsin State Capitol")}
PARKING_CUT = {"New York": 0, "Philadelphia": 0, "Charlotte": 1, "Saint Paul": 1, "Chicago": 1, "Madison": 1}
STATE_OF = {"New York": "36", "Philadelphia": "42", "Charlotte": "37", "Saint Paul": "27", "Chicago": "17", "Madison": "55"}


def gazetteer_land() -> dict:
    import zipfile
    z = zipfile.ZipFile(RAW / "census_gazetteer_2024" / "2024_Gaz_place_national.zip")
    g = pd.read_csv(z.open(z.namelist()[0]), sep="\t", dtype=str)
    g.columns = [c.strip() for c in g.columns]
    out = {}
    for city, (st, nm) in GAZ_PLACES.items():
        r = g[(g["GEOID"].str[:2] == st) & (g["NAME"] == nm)]
        out[city] = float(r["ALAND_SQMI"].iloc[0])
    return out


def area_weighted_tract(frames, tracts, values: pd.DataFrame, crs) -> pd.Series:
    """Acre-weighted mean over treatment lots of their tract's value (lot assigned by its representative point)."""
    import geopandas as gpd
    pts = gpd.GeoDataFrame({"acres": frames["acres"].values, "unit_id": frames["unit_id"].values},
                           geometry=frames.geometry.representative_point().values, crs=crs)
    j = gpd.sjoin(pts, tracts.to_crs(crs), how="left", predicate="within")
    j = j[~j.index.duplicated()]
    j = j.merge(values, on="tract", how="left")
    res = {}
    for col in ("home_value", "income", "rent"):
        v = j[col].where(j[col] > 0)
        res[col] = j.assign(v=v).groupby("unit_id").apply(lambda g: T.weighted_mean(g["v"], g["acres"]), include_groups=False)
    return pd.DataFrame(res)


def sld_values(frames, crs, state: str) -> pd.Series:
    import geopandas as gpd
    s = gpd.read_file(RAWT / "sld" / f"sld_d5br_{state}.geojson").to_crs(crs)
    s["D5BR"] = pd.to_numeric(s["D5BR"], errors="coerce").where(lambda v: v >= 0)
    pts = gpd.GeoDataFrame({"acres": frames["acres"].values, "unit_id": frames["unit_id"].values},
                           geometry=frames.geometry.representative_point().values, crs=crs)
    j = gpd.sjoin(pts, s[["D5BR", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    return j.groupby("unit_id").apply(lambda g: T.weighted_mean(g["D5BR"], g["acres"]), include_groups=False)


def stage_traits() -> pd.DataFrame:
    import geopandas as gpd
    units = pd.read_csv(UNITS_CSV)
    kept = units[units["kept"]]
    tr10 = tract_shapes("2010")
    acs10 = acs2010_tract_values()
    for k in ("home_value", "income", "rent"):
        acs10[k] = acs10[k].map(lambda v: T.cpi_to_2024(v, 2010) if pd.notna(v) else v)
    acs22 = acs_tbsf_tract_values(RAWT / "acs2022", 2022)
    for k in ("home_value", "income", "rent"):
        acs22[k] = acs22[k].map(lambda v: T.cpi_to_2024(v, 2022) if pd.notna(v) else v)
    tr20 = tract_shapes("2020")
    land = gazetteer_land()
    rows = []
    for c in CITIES:
        city = CITY_NAME[c]
        data = load_city(c)
        frames = [f for f in data["frames"] if f["unit_id"].iloc[0] in set(kept["unit_id"])] if data["frames"] else []
        if not frames:
            continue
        crs = frames[0].crs
        F = pd.concat([f.to_crs(crs) for f in frames], ignore_index=True)
        F = gpd.GeoDataFrame(F, geometry="geometry", crs=crs)
        if c == "madison":
            acs = area_weighted_tract(F, tr20, acs22, crs)
        else:
            acs = area_weighted_tract(F, tr10[tr10["tract"].str[:2] == STATE_OF[city]], acs10, crs)
        jobs = sld_values(F, crs, STATE_OF[city])
        # existing homes before: New York = MapPLUTO units on the lots in the before snapshot; Madison = parcel dwelling
        # units; others = 2010 census block homes whose internal point lies in a treatment lot (cases.homes_by_area rule)
        if c not in ("nyc", "madison"):
            bbox = tuple(gpd.GeoSeries([F.union_all().envelope], crs=crs).to_crs(4269).total_bounds)
            b = blocks_2010_points(STATE_OF[city], bbox).to_crs(crs)
            j = gpd.sjoin(b, F[["unit_id", "geometry"]], how="inner", predicate="within")
            j = j[~j.index.duplicated()]
            homes = j.groupby("unit_id")["homes"].sum()
        else:
            homes = F.groupby("unit_id")["homes_before"].sum()
        dx, dy, _ = DOWNTOWN[city]
        dt = gpd.GeoSeries(gpd.points_from_xy([dx], [dy]), crs=4326).to_crs(crs).iloc[0]
        for uid, g in F.groupby("unit_id"):
            u = kept[kept["unit_id"] == uid].iloc[0]
            ac = g["acres"].sum()
            cen = g.geometry.representative_point()
            cx, cy = float((cen.x * g["acres"]).sum() / ac), float((cen.y * g["acres"]).sum() / ac)
            # vacant/parking/industrial share: New York from the before snapshot (all lots); elsewhere land use is
            # today's, so lots with a new-housing permit in the unit's before or after years are left out of the share
            gg = g if c == "nyc" else g[g["developed"] != 1]
            vshare = T.weighted_mean(gg["vpi"], gg["acres"]) if len(gg) else np.nan
            dose = u["dose"] if u["dose_unit"] in ("added FAR",) else np.nan
            rows.append({"unit_id": uid, "city": city,
                         "t01_home_value": acs.loc[uid, "home_value"] if uid in acs.index else np.nan,
                         "t02_lot_size": float(ac / len(g)),
                         "t03_existing_density": float(homes.get(uid, 0.0)) / u["treatment_acres"],
                         "t04_income": acs.loc[uid, "income"] if uid in acs.index else np.nan,
                         "t05_city_land_area": land[city],
                         "t06_rent": acs.loc[uid, "rent"] if uid in acs.index else np.nan,
                         "t07_added_far": dose,
                         "t08_rate_before": u["treat_rate_before"],
                         "t09_vacant_parking_industrial_share": vshare,
                         "t10_km_to_downtown": float(np.hypot(cx - dt.x, cy - dt.y) / 1000.0),
                         "t11_transit_jobs_access": float(jobs.get(uid, np.nan)),
                         "t12_parking_cut": PARKING_CUT[city],
                         "acs_vintage": "2018-2022" if c == "madison" else "2006-2010",
                         "treatment_lot_count": len(g)})
    v = pd.DataFrame(rows)
    v = v.round({k: 4 for k in T.TRAITS} | {"t01_home_value": 0, "t04_income": 0, "t06_rent": 0, "t11_transit_jobs_access": 0})
    assert not T.check_private(v, allowed={"t02_lot_size", "treatment_lot_count"})
    v.to_csv(VALUES_CSV, index=False, lineterminator="\n")
    print(v.groupby("city", sort=False)[list(T.TRAITS)].median().T.round(3).to_string())
    print("missing values:", v[list(T.TRAITS)].isna().sum().to_dict())
    return v


# =========================================================================== 3. held-out test

def model_frame() -> pd.DataFrame:
    u = pd.read_csv(UNITS_CSV)
    u = u[u["kept"]]
    v = pd.read_csv(VALUES_CSV)
    d = u[["unit_id", "city", "unit_name", "treatment_acres", "effect"]].merge(v.drop(columns="city"), on="unit_id", how="left")
    d["weight"] = d["treatment_acres"]
    for t in T.TRAITS:
        d[f"x_{t}"] = T.transform(d, t)
    return d


def stage_test() -> None:
    d = model_frame()
    results, errs, ho = [], [], []
    models = [("baseline (weighted mean)", [])] + [(t, [t]) for t in T.TRAITS]
    verdicts = {}
    for name, ts in models:
        cols = [f"x_{t}" for t in ts]
        e = T.heldout_errors(d, cols if ts else [])
        if ts:
            # model and baseline on the same units (those with the trait)
            pass
        j = T.judge(e) if ts else {"verdict": "baseline", "cities_better": None, "cities": int((e["role"] == "fold").sum()),
                                   "mean_error_baseline": float(e.loc[e["role"] == "fold", "error_baseline"].mean()),
                                   "mean_error_model": float(e.loc[e["role"] == "fold", "error_baseline"].mean())}
        verdicts[name] = j["verdict"]
        results.append(summary_row(name, ts, d, e, j))
        errs.append(e.assign(model=name))
        ho.append(heldout_preds(d, cols, name))
    passing = [t for t in T.TRAITS if verdicts[t] == "pass"]
    for a, b in T.two_trait_sets(passing):
        cols = [f"x_{a}", f"x_{b}"]
        e = T.heldout_errors(d, cols)
        j = T.judge(e)
        name = f"{a} + {b}"
        results.append(summary_row(name, [a, b], d, e, j))
        errs.append(e.assign(model=name))
        ho.append(heldout_preds(d, cols, name))
    R = pd.DataFrame(results)
    E = pd.concat(errs, ignore_index=True)
    H = pd.concat(ho, ignore_index=True)
    R.round(4).to_csv(RESULTS_CSV, index=False, lineterminator="\n")
    E = E[["model", "city", "role", "units", "treatment_acres", "fit_units", "fit_cities", "error_baseline", "error_model",
           "measured_mean", "predicted_mean_baseline", "predicted_mean_model", "note"]]
    E.round(4).to_csv(ERRORS_CSV, index=False, lineterminator="\n")
    H.round(4).to_csv(HELDOUT_CSV, index=False, lineterminator="\n")
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(R.round(3).to_string(index=False))
    print(E[E["role"] == "always held out"].round(3).to_string(index=False))
    if passing:
        stage_wisconsin(d, passing, verdicts)
    elif WI_CSV.exists():
        WI_CSV.unlink()


def summary_row(name, ts, d, e, j) -> dict:
    f = e[e["role"] == "fold"]
    row = {"model": name, "traits": " + ".join(ts) if ts else "", "label": " + ".join(T.TRAITS[t]["label"] for t in ts) if ts else "baseline",
           "units_used": int(e["units"].sum()), "fold_cities": int(len(f)), "verdict": j["verdict"],
           "fold_cities_better": j["cities_better"], "mean_error_baseline": j["mean_error_baseline"], "mean_error_model": j["mean_error_model"]}
    for c in T.CITY_ORDER:
        r = e[e["city"] == c]
        row[f"err_base_{slug(c)}"] = float(r["error_baseline"].iloc[0]) if len(r) else np.nan
        row[f"err_model_{slug(c)}"] = float(r["error_model"].iloc[0]) if len(r) else np.nan
    # slope on all fitting units (for direction only; not used to judge)
    if ts:
        cols = [f"x_{t}" for t in ts]
        fit = d[d["city"].isin(T.FIT_CITIES)].dropna(subset=cols + ["effect"])
        X = np.column_stack([np.ones(len(fit))] + [fit[c].values for c in cols])
        b = T.wls(X, fit["effect"].values, fit["weight"].values)
        row["slopes_all_fit_units"] = "; ".join(f"{t}: {v:+.4g}" for t, v in zip(ts, b[1:]))
    return row


def heldout_preds(d, cols, name) -> pd.DataFrame:
    fit = d[d["city"].isin(T.FIT_CITIES)].dropna(subset=cols + ["effect"])
    test = d[d["city"].isin(T.TEST_CITIES)].dropna(subset=cols + ["effect"])
    if test.empty or fit.empty:
        return pd.DataFrame()
    p = T.fit_predict(fit, test, cols)
    return pd.DataFrame({"model": name, "unit_id": test["unit_id"].values, "city": test["city"].values,
                         "unit_name": test["unit_name"].values, "treatment_acres": test["treatment_acres"].values,
                         "measured_effect": test["effect"].values, "predicted_effect": p})


# =========================================================================== 4. Wisconsin (only if a trait passes)

def stage_wisconsin(d: pd.DataFrame, passing: list[str], verdicts: dict) -> None:
    """Sensitivity only: per-acre rates implied by each passing trait for each Wisconsin station area (city and band),
    from a model fitted on all fitting units (never Chicago or Madison). The model's main outputs are not changed.

    Only trait 12 (parking cut, city level) is handled: in Wisconsin it is a property of the law, not of the station
    area, so each area gets the rate with the trait at 1 (the law also removes parking minimums, the Gate 1 benchmark
    T5) and at 0 (minimums left to the parking scenario, the current model). 90% interval: units redrawn within each
    fitting city, 2,000 draws, seed 20261027."""
    unsupported = [t for t in passing if t != "t12_parking_cut"]
    if unsupported:
        raise NotImplementedError("Wisconsin values not built for " + ", ".join(unsupported))
    fit = d[d["city"].isin(T.FIT_CITIES)].dropna(subset=["effect", "x_t12_parking_cut"])
    X = lambda f: np.column_stack([np.ones(len(f)), f["x_t12_parking_cut"].values])  # noqa: E731
    b = T.wls(X(fit), fit["effect"].values, fit["weight"].values)
    rng = np.random.default_rng(20261027)
    draws = []
    groups = [g for _, g in fit.groupby("city")]
    for _ in range(2000):
        f = pd.concat([g.iloc[rng.integers(0, len(g), len(g))] for g in groups])
        draws.append(T.wls(X(f), f["effect"].values, f["weight"].values))
    draws = np.array(draws)
    rates = {v: (b[0] + b[1] * v, *np.quantile(draws[:, 0] + draws[:, 1] * v, [0.05, 0.95])) for v in (0, 1)}
    sa = pd.read_csv(REFERENCE / "tod_station_areas.csv")
    sa = sa[sa["city"] != "(unknown)"]
    g = sa.groupby(["city", "county", "band"], as_index=False).agg(eligible_acres=("eligible_acres", "sum"),
                                                                     in_main=("in_main", "max"))
    g = g[g["eligible_acres"] > 0]
    for v, (r, lo, hi) in rates.items():
        tag = "with_parking_cut" if v else "without_parking_cut"
        g[f"rate_{tag}"] = round(r, 4)
        g[f"rate_{tag}_low"] = round(lo, 4)
        g[f"rate_{tag}_high"] = round(hi, 4)
    g["unit"] = "extra homes permitted per eligible acre of upzoned land per year (trait-test sensitivity; not a model output)"
    g["model"] = "weighted linear model of unit effects on t12_parking_cut, fitted on New York, Philadelphia, Charlotte and Saint Paul units"
    assert not T.check_private(g)
    g.to_csv(WI_CSV, index=False, lineterminator="\n")
    print("Wisconsin sensitivity rates:", {k: tuple(round(x, 3) for x in v) for k, v in rates.items()}, "areas:", len(g))


# =========================================================================== exploratory combinations

def stage_explore() -> None:
    """All 66 trait pairs and one regression tree (plan section 8, exploratory combinations), stricter pass rule."""
    import itertools
    d = model_frame()
    rows = []
    for a, b in itertools.combinations(list(T.TRAITS), 2):
        e = T.heldout_errors(d, [f"x_{a}", f"x_{b}"])
        j = T.judge_strict(e)
        r = {"trait_a": a, "trait_b": b, "label": f"{T.TRAITS[a]['label']} + {T.TRAITS[b]['label']}",
             "units_used": int(e["units"].sum()), **j}
        for c in T.CITY_ORDER:
            x = e[e["city"] == c]
            r[f"err_base_{slug(c)}"] = float(x["error_baseline"].iloc[0]) if len(x) else np.nan
            r[f"err_model_{slug(c)}"] = float(x["error_model"].iloc[0]) if len(x) else np.nan
        rows.append(r)
    P = pd.DataFrame(rows)
    P["note"] = np.where(P["verdict"].str.startswith("pass"), T.CHANCE_WARNING, "")
    P.round(4).to_csv(PAIRS_CSV, index=False, lineterminator="\n")
    cols = [f"x_{t}" for t in T.TRAITS]
    e = T.heldout_tree_errors(d, cols)
    j = T.judge_strict(e)
    full = T.fit_tree(d[d["city"].isin(T.FIT_CITIES)].dropna(subset=["effect"]), cols)
    tr = pd.DataFrame(T.tree_rows(full))
    tr.insert(0, "part", "tree fitted on all four fitted cities")
    tr["split_trait"] = tr["split_trait"].str.replace("x_", "", regex=False)
    tr["node"] = tr["node"].str.replace("x_", "", regex=False)
    er = e.assign(part="held-out error", node=e["city"])[["part", "node", "role", "units", "treatment_acres", "error_baseline",
                                                            "error_model", "measured_mean", "predicted_mean_baseline", "predicted_mean_model"]]
    er["splits"] = e["splits"].str.replace("x_", "", regex=False)
    summ = pd.DataFrame([{"part": "verdict", "node": j["verdict"], "units": int(e["units"].sum()),
                          "error_baseline": j["mean_error_baseline"], "error_model": j["mean_error_model"],
                          "splits": f"fold cities better: {j['fold_cities_better']} of {j['fold_cities']}; Chicago "
                                    f"{j['beats_baseline_chicago']}; Madison {j['beats_baseline_madison']}"
                                    + (f". {T.CHANCE_WARNING}" if j["verdict"].startswith("pass") else "")}])
    out = pd.concat([summ, tr, er], ignore_index=True)
    out.round(4).to_csv(TREE_CSV, index=False, lineterminator="\n")
    for f in (P, out):
        assert not T.check_private(f)
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 90)
    print("pairs passing:", int(P["verdict"].str.startswith("pass").sum()), "of", len(P))
    print(P.sort_values("mean_error_model")[["trait_a", "trait_b", "verdict", "fold_cities_better", "mean_error_baseline",
                                              "mean_error_model", "beats_baseline_chicago", "beats_baseline_madison"]].head(15).round(3).to_string(index=False))
    print(out.round(3).to_string(index=False))


# =========================================================================== main

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=["fetch", "units", "write-units", "traits", "test", "explore"], required=True)
    ap.add_argument("--city", nargs="*", default=list(CITIES))
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args(argv)
    if a.stage == "fetch":
        stage_fetch()
    elif a.stage == "units":
        stage_units(a.city, a.rebuild)
    elif a.stage == "write-units":
        write_units()
    elif a.stage == "traits":
        stage_traits()
    elif a.stage == "explore":
        stage_explore()
    else:
        stage_test()


if __name__ == "__main__":
    main()

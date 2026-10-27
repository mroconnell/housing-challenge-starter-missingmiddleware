"""Phoenix 2015 Walkable Urban Code: case adapter, measured by COUNT of new residential building permits (plan section 7,
2026-10-27). Context only: never pooled with unit-based cases or used to fit.

Inputs (data/raw/tod_cases/phoenix/, fetched by scripts/fetch_tod_cases.py):
- kiva/permits_<class>_<year>.csv: the City's Issued Permit Data export (old KIVA system), residential permits by
  Census structure class (001 one unit, 002 two, 003 three-four, 004 five-nine, 007 ten or more), 1995-2025, with
  permit type, number, issue date, parcel (APN), units. Raw only: the export carries owner and contractor names.
- wu_zoning.geojson: current WU (Walkable Urban Code) zoning polygons with their rezoning case number.
- wu_annual_plan.geojson: the City's list of WU rezonings with approval dates (filled for some) and case years.
- approved_zoning.geojson: other approved rezonings (case numbers carry the year).
- parcels.geojson: Maricopa County Assessor parcels near WU areas (APN, property use code, current zoning).
- rail_stops.geojson: Valley Metro light-rail stops (BTS National Transit Map).

Rules:
- Members: WU rezoning cases. Effective year = the approval date's year where the City's list gives it, otherwise
  the year in the case number (the year the case was filed: approval usually follows within months). Stacked in
  event time, like the New York pooled set.
- Treatment: parcels in a member's WU polygons. No layer gives zoning before most WU rezonings, so every WU parcel
  counts as having risen (the WU transects replaced suburban commercial and residential districts near stations),
  and "already at the law" cannot be tested.
- Lots in other approved rezonings whose case year falls in the member's window, and lots in other WU members, are
  in no area.
- Outcome: permits of type BLD (new building) and RSF/RSFC (new single-family), one per permit number; temporary
  certificates of occupancy (TCO), shell and other rows are dropped. Single-family = structure class 001;
  multifamily = 002-007. The single-family series moves to a new system in 2022 (no public archive), so it is used
  only through 2021; multifamily runs through 2025. Members are kept only where the series has all 6 before and 5
  after years.
- Second comparison: parcels within 1/2 mile of light-rail stops whose own 1/2-mile circle has no WU treatment.
"""
from __future__ import annotations

import glob
import re

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "phoenix"
CRS_M = 26949  # NAD83 / Arizona Central (metres)
SERIES_LAST = {"sf": 2021, "mf": 2025, "all": 2021}
FIRST_YEAR = 1995
NEW_TYPES = {"BLD", "RSF", "RSFC"}  # new building (multifamily) and new single-family permits; TCO, shell and other rows dropped
EXEMPT_PUC = re.compile(r"^9")  # Maricopa property use codes 9xxx: exempt, government and similar


def apn_key(s) -> str:
    return re.sub(r"[^0-9A-Z]", "", str(s).upper())


def case_year(case: str) -> int | None:
    m = re.search(r"-(\d{2})$", str(case).strip())
    return 2000 + int(m.group(1)) if m else None


def load_permits() -> pd.DataFrame:
    rows = []
    for f in sorted(glob.glob(str(DIR / "kiva" / "permits_*.csv"))):
        cls = re.search(r"permits_(\d{3})_", f).group(1)
        with open(f, encoding="utf-8-sig") as fh:
            lines = fh.readlines()[1:]
        if not lines:
            continue
        d = pd.read_csv(__import__("io").StringIO("".join(lines)), dtype=str, usecols=lambda c: c in
                        {"Type", "Number", "Issue Date", "Struct Class", "Parcel", "Units"})
        d["cls"] = cls
        rows.append(d)
    p = pd.concat(rows, ignore_index=True)
    p = p[p["Type"].astype(str).str.strip().isin(NEW_TYPES)].drop_duplicates("Number")
    p["year"] = pd.to_datetime(p["Issue Date"], errors="coerce", format="mixed").dt.year
    p["series"] = np.where(p["cls"] == "001", "sf", "mf")
    p["apn"] = p["Parcel"].map(apn_key)
    return p.dropna(subset=["year"])


def build_counts() -> list:
    import geopandas as gpd
    wu = gpd.read_file(DIR / "wu_zoning.geojson").to_crs(CRS_M)
    wu["geometry"] = wu.geometry.make_valid()
    plan = gpd.read_file(DIR / "wu_annual_plan.geojson")
    dates = {str(r.REDEFINE1).strip(): pd.to_datetime(r.DATE_APPRO, errors="coerce") for r in plan.itertuples()}
    wcol = next(c for c in wu.columns if c.upper().endswith("REDEFINE1"))
    wu["case"] = wu[wcol].astype(str).str.strip()
    wu["eff"] = [dates.get(c).year if pd.notna(dates.get(c)) else case_year(c) for c in wu["case"]]
    wu["dated_by"] = ["approval" if pd.notna(dates.get(c)) else "case number" for c in wu["case"]]
    wu = wu[wu["eff"].notna()]
    appr = gpd.read_file(DIR / "approved_zoning.geojson").to_crs(CRS_M)
    appr["geometry"] = appr.geometry.make_valid()
    ccol = next(c for c in appr.columns if c.upper().endswith("REDEFINE1"))
    appr["year"] = appr[ccol].map(case_year)
    parcels = gpd.read_file(DIR / "parcels.geojson").to_crs(CRS_M)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].drop_duplicates("APN").reset_index(drop=True)
    parcels["acres"] = parcels.geometry.area / C.SQM_PER_ACRE
    parcels["apn"] = parcels["APN"].map(apn_key)
    pts = parcels.geometry.representative_point()
    in_city = parcels["JURISDICTION"].astype(str).str.upper().str.contains("PHOENIX") | \
        parcels["PHYSICAL_CITY"].astype(str).str.upper().str.contains("PHOENIX")
    eligible = ~parcels["PUC"].astype(str).str.match(EXEMPT_PUC) & ~parcels["CITY_ZONING"].astype(str).str.upper().str.startswith(("PARK", "GC"))
    stops = gpd.read_file(DIR / "rail_stops.geojson").to_crs(CRS_M).geometry
    permits = load_permits()
    lut = pd.Series(parcels.index, index=parcels["apn"])
    lut = lut[~lut.index.duplicated()]
    permits["pix"] = permits["apn"].map(lut)
    in_any_wu = pts.within(wu.geometry.union_all())
    out = []
    for series in ("all", "sf", "mf"):
        last = SERIES_LAST[series]
        members = sorted(c for c, e in wu.groupby("case")["eff"].first().items() if e - C.BEFORE_MAX >= FIRST_YEAR and e + 5 <= last)
        q0 = permits if series == "all" else permits[permits["series"] == series]
        allp, acres, orig_p, orig_a, diag = [], {}, [], {}, {"members": {}}
        for case in members:
            mem = wu[wu["case"] == case]
            eff = int(mem["eff"].iloc[0])
            per = C.period_years(eff, FIRST_YEAR, last)
            in_mem = pts.within(mem.geometry.union_all())
            lo, hi = per["before"][0], per["after"][-1]
            oth = appr[appr["year"].between(lo, hi) & (appr[ccol].astype(str).str.strip() != case)]
            changed = (pts.within(oth.geometry.union_all()) if len(oth) else False) | (in_any_wu & ~in_mem)
            near = pts.within(mem.geometry.union_all().buffer(1500))
            sub = parcels[near]
            one = pd.Series(1.0, index=sub.index)
            area, rule = C.uniform_areas(sub, in_mem[near], in_mem[near], one * 0, one, pd.Series(False, index=sub.index),
                                         pd.Series(changed, index=parcels.index)[near], eligible[near],
                                         in_city=in_city[near], stations=stops)
            el = sub[area.notna() & eligible[near]]
            a = el.groupby(area[el.index])["acres"].sum().to_dict()
            q = q0[q0["year"].between(lo, hi)]

            def permits_for(ar, q=q):
                r = q.assign(area=ar.reindex(q["pix"]).values, el=eligible.reindex(q["pix"]).fillna(False).astype(bool).values)
                r = r[r["area"].notna() & r["el"]].copy()
                r = r.assign(project=case + ":" + r["pix"].astype(int).astype(str), units=1.0, year=r["year"].astype(int) - eff)
                return r[["project", "area", "year", "units"]]

            diag["members"][case] = {"effective": eff, "dated_by": mem["dated_by"].iloc[0], "acres": {k: round(v, 1) for k, v in a.items()}}
            if not a.get(C.TREAT):
                continue
            allp.append(permits_for(area))
            oa = C.assign_areas(sub, in_mem[near], in_city=in_city[near])
            orig_p.append(permits_for(oa))
            for k, v in a.items():
                acres[k] = acres.get(k, 0.0) + v
            for k, v in sub[oa.notna() & eligible[near]].groupby(oa)["acres"].sum().items():
                orig_a[k] = orig_a.get(k, 0.0) + v
        diag["included"] = [c for c, d in diag["members"].items() if d["acres"].get(C.TREAT)]
        diag["permits_located_by_apn_share"] = round(float(q0["pix"].notna().mean()), 4)
        label = {"all": "all new residential", "sf": "single-family (class 001)", "mf": "multifamily (classes 002-007)"}[series]
        ci = C.CaseInputs(case=f"phoenix_permit_count_{series}", role="context", effective_year=0, first_year=-C.BEFORE_MAX,
                          last_full_year=max(C.AFTER_YEARS),
                          permits=pd.concat(allp, ignore_index=True) if allp else pd.DataFrame(columns=["project", "area", "year", "units"]),
                          acres=acres, homes={}, dose_table=None, parking_change="reduced in WU (source_lead)", mandate="no",
                          dose_unit="none", measure="permits per eligible acre per year", status_override="context_permit_count",
                          original_spec=(pd.concat(orig_p, ignore_index=True), orig_a) if orig_p else None,
                          notes=f"{label} permits (count, not homes); WU rezonings stacked in event time; members effective by {last - 5}")
        out.append((ci, diag))
    return out


def build() -> tuple:
    """Kept for the unit-based run: Phoenix has no unit-based estimate (see build_counts)."""
    ci = C.CaseInputs(case="phoenix_walkable_urban_code_2015", role="fit", effective_year=2015, first_year=2015,
                      last_full_year=2025, permits=pd.DataFrame(columns=["project", "area", "year", "units"]), acres={},
                      homes={}, dose_table=None, parking_change="unknown", mandate="no", has_units=False,
                      status_override="context_only: no unit-based estimate; measured by permit counts instead (phoenix_permit_count_*)",
                      notes="see CASE_RESULTS.md")
    return ci, {}

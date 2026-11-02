"""Rule-based hand-check rows for New York and Philadelphia (stop-outlier review, owner 2026-11-02 18:22).

The hand check of every lot with 100+ new homes (data/processed/tod_station_area/hand_check_big_lots.csv) covered the
15 single cases but not New York (23 rezonings) or Philadelphia (83). The stop-outlier review found the same error types
there. This script writes them into the same file as rows that model time already applies
(run_tod_station_model.event_windows: 'wrong count' rows take homes_corrected as the lot's window total, 'duplicate'
rows go to 0). One row per case, lot and window whose total changes. Rows written here carry evidence starting
"rule "; rerunning the script replaces them and leaves the hand-entered rows alone.

New York (DOB new-building jobs; building from MapPLUTO 18v1, the lot vintage of the lot tables). A job counts as the
building standing on the lot in 18v1 when 18v1 YearBuilt >= the job's fully-permitted year - 1.
  nyc_hotel        18v1 building class hotel (H*) or condo hotel unit (RH): the job's "dwelling units" are rooms.
                   The standing job(s) on the lot together keep only 18v1 UnitsRes (residential units; 0 for hotels).
  nyc_condo_hotel  class RC (commercial condo) with 0 residential units in a building of 10+ floors (condo-hotels
                   such as 246 Spring St): as above, UnitsRes (0).
  nyc_institution  class I* (hospital, nursing and health) or N* (asylums, homes for the aged, shelters): beds or
                   rooms, not homes (same rule as the other cities' hand check): UnitsRes.
  nyc_hotel_condo  condo class (R*) tower of 20+ floors with one standing job and 18v1 UnitsTotal < 60% of the job's
                   units: hotel rooms over residences (e.g. a 214-room hotel under 163 condos filed as one 377-unit
                   job): the job keeps UnitsTotal.
  nyc_superseded   2+ jobs (20+ units) on one lot, the latest standing and within 10% of 18v1 UnitsTotal: the earlier
                   jobs were replaced by the latest one (refiled or redesigned; the builder only merges same-count
                   refilings within 2 years) and count 0.
Philadelphia (L&I new-construction permits; whole-building types; staged permits within 548 days already merged):
  phl_reissued     the same parcel point and the same unit count (20+) permitted again 1-4 years later: one
                   building, the later permit counts 0.

    .venv/bin/python scripts/build_tod_hand_check_rules.py [--dry]

Prints counts and homes changed by rule and window. Parcel ids stay in data/ (local).
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402

OUT = ROOT / "data" / "processed" / "tod_station_area"
HAND = OUT / "hand_check_big_lots.csv"
NYC_DIR = ROOT / "data" / "raw" / "tod_cases" / "nyc"
PLUTO_SRC = "https://www.nyc.gov/site/planning/data-maps/open-data/dwn-pluto-mappluto.page"
DOB_SRC = "https://data.cityofnewyork.us/Housing-Development/DOB-Job-Application-Filings/ic3t-wcy2"
PHL_SRC = "https://opendataphilly.org/datasets/licenses-and-inspections-building-permits/"


def pluto18() -> pd.DataFrame:
    zf = zipfile.ZipFile(NYC_DIR / "mappluto_18v1.zip")
    F = ["BldgClass", "UnitsRes", "UnitsTotal", "YearBuilt", "NumFloors", "XCoord", "YCoord"]
    out = []
    for n in [x for x in zf.namelist() if x.lower().endswith("mappluto.dbf")]:
        d, _ = X._dbf_columns(zf.read(n), F, "latin-1")
        out.append(d)
    d = pd.concat(out, ignore_index=True)
    for c in F[1:]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[(d.XCoord > 0) & (d.YCoord > 0)].reset_index(drop=True)
    d["x"], d["y"] = X.transform(d.XCoord.values.astype(float), d.YCoord.values.astype(float), 2263, 5070)
    d["BldgClass"] = d.BldgClass.astype(str).str.strip()
    return d


def cfgs() -> dict:
    import build_tod_station_lot_table as B
    return {**B.CASES, **{k: v for k, (_, v) in B.adapter_cases().items()}}


def nyc_job_fix(E: pd.DataFrame, b: pd.Series) -> tuple[pd.Series, pd.Series]:
    """E: one lot's events; b: its 18v1 building. Returns corrected homes and the rule per event ('' = unchanged)."""
    new, rule = E.homes.copy(), pd.Series("", index=E.index)
    cls, yb = str(b.BldgClass), float(b.YearBuilt or 0)
    stand = (yb > 0) & (yb >= E.permit_year - 1)
    big = E.homes >= 20
    keep_units = None
    if cls.startswith(("H", "RH")):
        keep_units, tag = float(b.UnitsRes or 0), "nyc_hotel"
    elif cls == "RC" and (b.UnitsRes or 0) == 0 and (b.NumFloors or 0) >= 10:
        keep_units, tag = 0.0, "nyc_condo_hotel"
    elif cls[:1] in ("I", "N"):
        keep_units, tag = float(b.UnitsRes or 0), "nyc_institution"
    if keep_units is not None:
        S = E[stand & big]
        if len(S) and S.homes.sum() > keep_units:
            last = S.sort_values(["permit_year", "homes"]).index[-1]
            new[S.index] = 0.0
            new[last] = keep_units
            rule[S.index] = tag
        return new, rule
    S = E[stand & big]
    if cls.startswith("R") and (b.NumFloors or 0) >= 20 and len(S) == 1 and (E[big].shape[0] == 1):
        i = S.index[0]
        if (b.UnitsTotal or 0) < 0.6 * E.homes[i]:
            new[i], rule[i] = float(b.UnitsTotal or 0), "nyc_hotel_condo"
        return new, rule
    J = E[big]
    if len(J) >= 2:
        last = J.sort_values(["permit_year", "homes"]).index[-1]
        ly, lh = E.permit_year[last], E.homes[last]
        if yb > 0 and yb >= ly - 1 and abs(lh - (b.UnitsTotal or 0)) <= 0.1 * lh:
            old = J.index[(J.permit_year < ly)]
            new[old], rule[old] = 0.0, "nyc_superseded"
    return new, rule


EVID = {
    "nyc_hotel": "rule nyc_hotel: MapPLUTO 18v1 hotel building class {cls} on the lot (built {yb}), {ures} residential "
                 "units; DOB new-building job(s) {jobs} counted rooms",
    "nyc_condo_hotel": "rule nyc_condo_hotel: MapPLUTO 18v1 class RC, 0 residential units, {fl} floors (built {yb}); "
                       "DOB job(s) {jobs} counted condo-hotel units",
    "nyc_institution": "rule nyc_institution: MapPLUTO 18v1 class {cls} (health / home / shelter), {ures} residential "
                       "units (built {yb}); DOB job(s) {jobs} counted beds or rooms",
    "nyc_hotel_condo": "rule nyc_hotel_condo: MapPLUTO 18v1 condo tower class {cls}, {fl} floors, {utot} units in all "
                       "(built {yb}); DOB job {jobs} included hotel rooms",
    "nyc_superseded": "rule nyc_superseded: MapPLUTO 18v1 building (built {yb}) has {utot} units = the latest DOB job; "
                      "earlier job(s) {jobs} on the lot were replaced",
    "phl_reissued": "rule phl_reissued: L&I new-construction permit for the same parcel and unit count issued again "
                    "{jobs}; one building, later permit counted 0",
}


def nyc_rows(C: dict, P: pd.DataFrame) -> list[dict]:
    T = cKDTree(np.c_[P.x, P.y])
    rows = []
    for f in sorted(OUT.glob("events_nyc_*.parquet")):
        case = f.stem.removeprefix("events_")
        if case not in C or not (OUT / f"lots_{case}.parquet").exists():
            continue
        E = pd.read_parquet(f)
        L = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=["group", "band", "x", "y"])
        lots = E.lot_index[E.homes >= 20].unique()
        if not len(lots):
            continue
        d, i = T.query(np.c_[L.x.values[lots], L.y.values[lots]])
        bmap = {lot: P.iloc[j] for lot, dd, j in zip(lots, d, i) if dd <= 1.0}
        rows += window_rows(case, C[case], E, L, bmap, "nyc")
    return rows


def phl_fix(E: pd.DataFrame, _b=None) -> tuple[pd.Series, pd.Series]:
    new, rule = E.homes.copy(), pd.Series("", index=E.index)
    J = E[E.homes >= 20].sort_values("permit_year")
    for h, g in J.groupby("homes"):
        y0 = None
        for i, y in zip(g.index, g.permit_year):
            if y0 is not None and 1 <= y - y0 <= 4:
                new[i], rule[i] = 0.0, "phl_reissued"
            else:
                y0 = y
    return new, rule


def phl_rows(C: dict) -> list[dict]:
    rows = []
    for f in sorted(OUT.glob("events_phl_*.parquet")):
        case = f.stem.removeprefix("events_")
        if case not in C or not (OUT / f"lots_{case}.parquet").exists():
            continue
        E = pd.read_parquet(f)
        L = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=["group", "band"])
        rows += window_rows(case, C[case], E, L, None, "phl")
    return rows


def window_rows(case, cfg, E, L, bmap, city) -> list[dict]:
    rows = []
    for lot, e in E.groupby("lot_index"):
        if not (e.homes >= 20).any():
            continue
        if city == "nyc":
            if lot not in bmap:
                continue
            b = bmap[lot]
            new, rule = nyc_job_fix(e, b)
        else:
            b = None
            new, rule = phl_fix(e)
        if not (rule != "").any():
            continue
        tag = rule[rule != ""].iloc[0]
        jobs = ", ".join(f"{h:.0f} ({y:.0f})" for h, y in zip(e.homes[rule != ""], e.permit_year[rule != ""]))
        ev = EVID[tag].format(cls=getattr(b, "BldgClass", ""), yb=int(getattr(b, "YearBuilt", 0) or 0),
                              ures=int(getattr(b, "UnitsRes", 0) or 0), utot=int(getattr(b, "UnitsTotal", 0) or 0),
                              fl=int(getattr(b, "NumFloors", 0) or 0), jobs=jobs)
        for win in ("before", "after"):
            a, z = cfg[win]
            inw = e.permit_year.between(a, z)
            old_t, new_t = float(e.homes[inw].sum()), float(new[inw].sum())
            if old_t == new_t:
                continue
            rows.append({"case": case, "lot_index": int(lot), "group": L.group.iat[lot], "band": L.band.iat[lot],
                         "window": win, "homes_recorded": old_t,
                         "class": "duplicate" if new_t == 0 and tag in ("nyc_superseded", "phl_reissued") else "wrong count",
                         "homes_corrected": new_t, "evidence_short": ev,
                         "source_url": PHL_SRC if city == "phl" else f"{PLUTO_SRC} ; {DOB_SRC}", "rule": tag})
    return rows


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    C = cfgs()
    R = pd.DataFrame(nyc_rows(C, pluto18()) + phl_rows(C))
    pd.set_option("display.width", 200)
    R["change"] = R.homes_corrected - R.homes_recorded
    R["city"] = R.case.str[:3]
    print(R.groupby(["rule", "window", "group"]).agg(rows=("change", "size"), homes_recorded=("homes_recorded", "sum"),
                                                     change=("change", "sum")).to_string())
    # physical lots (rows repeat across New York / Philadelphia rezonings)
    print("distinct (rule, evidence):", R.groupby("rule").evidence_short.nunique().to_dict())
    if a.dry:
        return
    H = pd.read_csv(HAND)
    H = H[~H.evidence_short.fillna("").str.startswith("rule ")]
    H = pd.concat([H, R[H.columns]], ignore_index=True)
    H.to_csv(HAND, index=False)
    print(f"wrote {HAND} ({len(R)} rule rows; {len(H)} rows in all)")


if __name__ == "__main__":
    main()

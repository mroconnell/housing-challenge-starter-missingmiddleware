"""Waunakee, WI (village, Dane Co.) adapter: "Residential Building Permits" ArcGIS layer.

Source: https://services7.arcgis.com/ITFBFLQBvUvHAQ7d/arcgis/rest/services/Residential_Building_Permits/FeatureServer/0
(public ArcGIS Online feature layer, GET `query`). 2000-2026, one row per NEW residential
dwelling permit: date, permit #, census class (101 single-family, 102/103 two-family,
105 multifamily), address, description ("New SFR", "New Duplex", ...), parcel #, units.

COVERAGE LIMITATION: the layer holds only new-dwelling permits (classes 101-105). Alterations,
additions, garage conversions and interior (basement) units are not in it, so attached and
conversion ADUs and single-family-to-duplex conversions are structurally invisible. A detached
ADU would only appear if it was permitted as a new dwelling (class 101/102) - none is labelled so.
ADUs were not allowed in the village before a 2024-05-06 ordinance amendment.

The OWNER field is never requested.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from . import classify
from . import fetch_util as fu

META = {
    "slug": "waunakee",
    "place": "Waunakee village",
    "geoids": ["5502584350"],
    "source_url": ("https://services7.arcgis.com/ITFBFLQBvUvHAQ7d/arcgis/rest/services/"
                   "Residential_Building_Permits/FeatureServer/0"),
    "source_desc": "ArcGIS feature layer of new residential dwelling permits (classes 101-105), 2000-2026",
    "stage": "issued",
    "license": "public ArcGIS Online layer (no stated licence)",
    "method": ("census class + description text; new dwellings checked against earlier permits on the same "
               "parcel. New-dwelling permits only: attached/conversion ADUs cannot be observed."),
}
FIELDS = ["OBJECTID", "DATE", "PERMIT", "CLASS", "ADDRESS", "DESCRIPTION", "COST", "PARCEL__", "YEAR",
          "Neighborhood_or_Development_Name", "TYPE_OF_HOUSING", "NUMBER_OF_UNITS"]  # no OWNER


def fetch(raw_dir: Path, log=print) -> dict:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    path, man_path = raw_dir / "residential_permits.json", raw_dir / "manifest.json"
    if path.exists() and man_path.exists():
        return fu.read_manifest(man_path)
    feats, offset = [], 0
    while True:
        log(f"waunakee: query offset {offset}")
        d = json.loads(fu.get(META["source_url"] + "/query", {
            "where": "1=1", "outFields": ",".join(FIELDS), "returnGeometry": "false", "f": "json",
            "orderByFields": "OBJECTID", "resultOffset": offset, "resultRecordCount": 1000}))
        if "error" in d:
            raise RuntimeError(d["error"])
        feats += [f["attributes"] for f in d.get("features", [])]
        if not d.get("exceededTransferLimit") and len(d.get("features", [])) < 1000:
            break
        offset += 1000
    path.write_text(json.dumps(feats))
    fu.write_manifest(man_path, [{"file": path.name, "url": META["source_url"] + "/query",
                                  "params": {"where": "1=1", "outFields": FIELDS}, "records": len(feats),
                                  "accessed": fu.now_iso(), "sha256": fu.sha256_file(path)}],
                      {"source": META["source_url"], "license": META["license"],
                       "note": "OWNER field deliberately not requested"})
    return fu.read_manifest(man_path)


def load(raw_dir: Path) -> pd.DataFrame:
    rows = json.loads((Path(raw_dir) / "residential_permits.json").read_text())
    df = pd.DataFrame(rows)
    out = pd.DataFrame({
        "permit_id": df["PERMIT"].astype(str).str.strip() + "#" + df["OBJECTID"].astype(str),
        "date": pd.to_datetime(df["DATE"], errors="coerce"),
        "permit_type": df["CLASS"].astype("Int64").astype(str),
        "description": df["DESCRIPTION"],
        "units_raw": pd.to_numeric(df["NUMBER_OF_UNITS"], errors="coerce").astype(float),
        "parcel_id": df["PARCEL__"],
        "type_of_housing": df["TYPE_OF_HOUSING"],
        "development": df["Neighborhood_or_Development_Name"],
    })
    addr = df["ADDRESS"].fillna("").str.strip()
    m = addr.str.extract(r"^(\d+[A-Za-z]?)\s+(.*)$")
    out["house_nbr"] = m[0]
    out["street"] = m[1].fillna(addr).str.upper().replace("", np.nan)
    out["year"] = out["date"].dt.year.fillna(df["YEAR"]).astype(int)
    cols = ["permit_id", "date", "year", "permit_type", "description", "units_raw", "parcel_id", "street",
            "house_nbr", "type_of_housing", "development"]
    return out[cols].reset_index(drop=True)


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y in range(2022, 2026):
        d = df[df.year == y]
        months = d.date.dt.month.nunique()
        out.append({"year": y, "months_with_records": months, "records": len(d),
                    "complete": bool(months == 12),
                    "note": "continuous export of NEW dwelling permits only (no alterations/conversions)"})
    return pd.DataFrame(out)


JUDGMENTS: dict[str, dict] = {
    "25-002#26": {"counts": False, "component": None,
                  "why": "new SFR at a different house number on the same (unsplit) parcel as new SFR 24-776, "
                         "11 weeks earlier, Evergreen Ter: adjacent new-subdivision lots, no existing house"},
    "24-005#113": {"counts": False, "component": None,
                   "why": "new SFR at a different house number on the same parcel as new SFR 23-729, 2 weeks "
                          "earlier, Indigo Ln: adjacent new-subdivision lots, no existing house"},
}


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    comp, units, reason, cand = [], [], [], []
    for r in df.itertuples():
        d = r.description if isinstance(r.description, str) else ""
        c, note = classify.text_class(d)
        rs, cd = "", False
        if c == "adu_legalization":
            c, rs, cd = None, "legalization (excluded)", True
        elif c:
            rs, cd = f"ADU text ({note})", True
        elif classify.SF_TO_TWO_RE.search(d):
            c, rs, cd = "sf_to_duplex", "text: single-family to two-family", True
        else:
            c = None
            if r.permit_type in ("102", "103"):
                rs, cd = "new two-family building (excluded: own lot, not a second home)", True
            elif r.permit_type in ("101",) and isinstance(r.parcel_id, str):
                prev = df[(df.parcel_id == r.parcel_id) & (df.date < r.date)]
                if len(prev):
                    same = prev[(prev.house_nbr == r.house_nbr) & (prev.street == r.street)]
                    if len(same) and (r.date - same.date.max()).days < 400:
                        rs, cd = "repeat new-SFR permit for the same address within a year (re-issue; excluded)", True
                    else:
                        rs, cd = "unconfirmed: new SFR on a parcel with an earlier dwelling permit", True
        comp.append(c)
        units.append(1 if c else 0)
        reason.append(rs)
        cand.append(cd)
    df["component"], df["units"], df["reason"], df["candidate"] = comp, units, reason, cand
    for pid, j in JUDGMENTS.items():
        m = df.permit_id == pid
        if m.any():
            df.loc[m, ["candidate", "reason"]] = [True, "judgment: " + j["why"]]
            df.loc[m, "component"] = j["component"] if j["counts"] else None
            df.loc[m, "units"] = j.get("units", 1) if j["counts"] else 0
    df["units"] = df["units"].astype(int)
    return df

"""Fetch data for the station-area radius programs (docs/tod/STATION_AREA_PLAN.md, LOCKED section).

Raw files stay local under data/raw/tod_radius_programs/<city>/ with a manifest (source, date, rows, sha256).
Stages: sd_permits, honolulu_permits, la_permits.
"""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "tod_radius_programs"


def _get(url: str, data: bytes | None = None, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "housing-policy-model/0.1"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))
    raise RuntimeError


def _manifest(city: str, name: str, url: str, rows: int, path: Path, note: str = "") -> None:
    m = RAW / city / "manifest.json"
    d = json.loads(m.read_text()) if m.exists() else {}
    d[name] = {"url": url, "accessed": str(date.today()), "rows": rows, "bytes": path.stat().st_size,
               "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "note": note}
    m.write_text(json.dumps(d, indent=1))


def arcgis_all(layer: str, where: str, fields: str, page: int = 2000) -> list[dict]:
    """Page through an ArcGIS layer by OBJECTID ranges; returns attribute dicts."""
    ids = json.loads(_get(f"{layer}/query?" + urllib.parse.urlencode({"where": where, "returnIdsOnly": "true", "f": "json"})))["objectIds"] or []
    ids.sort()
    out: list[dict] = []
    for i in range(0, len(ids), page):
        chunk = ids[i:i + page]
        body = urllib.parse.urlencode({"where": f"OBJECTID>={chunk[0]} AND OBJECTID<={chunk[-1]} AND ({where})",
                                       "outFields": fields, "returnGeometry": "false", "f": "json"}).encode()
        out += [f["attributes"] for f in json.loads(_get(f"{layer}/query", body))["features"]]
    return out


def sd_permits() -> None:
    layer = "https://webmaps.sandiego.gov/arcgis/rest/services/Planning/PLN_Housing_ServiceLayers/MapServer/0"
    where = "TOTAL_DU>0 AND APPROVAL_TYPE IN ('Building Permit','Combination Building Permit')"
    rows = arcgis_all(layer, where, "OBJECTID,APPROVAL_ID,PROJECT_ID,DEVELOPMENT_ID,APPROVAL_TYPE,APPROVAL_STATUS,"
                      "JOB_BC_CODE,JOB_BC_CODE_DESCRIPTION,APPROVAL_ISSUE_DATE,APPROVAL_CLOSE_DATE,LAT_JOB,LNG_JOB,"
                      "TOTAL_DU,TOTAL_ADU,TOTAL_JADU,APPROVAL_DU_BONUS,APPROVAL_STORIES,RECORD_DATA_SOURCE")
    p = RAW / "san_diego" / "permits.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows))
    _manifest("san_diego", "permits.json", layer, len(rows), p,
              "City of San Diego Housing Element permit layer; building and combination building permits with homes")
    print("san diego permits", len(rows))


STAGES = {"sd_permits": sd_permits}

if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("stage", choices=STAGES); STAGES[a.parse_args().stage]()

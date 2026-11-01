"""National trait files for the station-area model (docs/tod/STATION_AREA_PLAN.md, trait list v2).

Every state has these: Census LEHD LODES jobs by block (workplace area characteristics), by year.
Raw files stay local under data/raw/tod_station_traits/ with a manifest.
"""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.request
from datetime import date
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "tod_station_traits"
# states of the 14 cases, their comparison cities, and Wisconsin
STATES = ["ca", "co", "hi", "il", "mn", "nc", "ny", "or", "pa", "tx", "ut", "wa", "wi"]
LODES_YEARS = [2004, 2008, 2010, 2013, 2015, 2016, 2019, 2020, 2022]


def _get(url: str, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "housing-policy-model/0.1"}), timeout=300) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))
    raise RuntimeError


def lodes() -> None:
    out = RAW / "lodes"
    out.mkdir(parents=True, exist_ok=True)
    man = {}
    for st in STATES:
        for y in LODES_YEARS:
            name = f"{st}_wac_S000_JT00_{y}.csv.gz"
            url = f"https://lehd.ces.census.gov/data/lodes/LODES8/{st}/wac/{name}"
            p = out / name
            if not p.exists():
                try:
                    p.write_bytes(_get(url))
                except Exception as e:   # some states lack early years; recorded, not fatal
                    man[name] = {"url": url, "error": str(e)[:120]}
                    continue
            man[name] = {"url": url, "accessed": str(date.today()), "bytes": p.stat().st_size,
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print("lodes files", sum("error" not in v for v in man.values()), "missing", [k for k, v in man.items() if "error" in v])


def nrhp() -> None:
    """National Register of Historic Places polygons (National Park Service), all states, with listing date."""
    import urllib.parse
    layer = "https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/1"
    ids = sorted(json.loads(_get(f"{layer}/query?where=1%3D1&returnIdsOnly=true&f=json"))["objectIds"])
    feats = []
    for i in range(0, len(ids), 1000):
        c = ids[i:i + 1000]
        q = urllib.parse.urlencode({"where": f"OBJECTID>={c[0]} AND OBJECTID<={c[-1]}", "outFields": "NRIS_Refnum,RESNAME,ResType,City,State,CertDate,NumCBldg,BND_TYPE,STATUS",
                                    "outSR": 4326, "geometryPrecision": 6, "f": "geojson"})
        feats += json.loads(_get(f"{layer}/query?{q}"))["features"]
    p = RAW / "nrhp" / "nrhp_polygons.geojson"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    (p.parent / "manifest.json").write_text(json.dumps({p.name: {"url": layer, "accessed": str(date.today()), "rows": len(feats),
        "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "licence": "US federal government work (NPS)"}}, indent=1))
    print("nrhp polygons", len(feats))


def sld() -> None:
    """EPA Smart Location Database, national: version 2 (2013; 2012 transit schedules) and version 3 (2021; 2020
    schedules). Transit frequency, walkability, jobs access by block group. Public domain."""
    out = RAW / "sld"
    out.mkdir(parents=True, exist_ok=True)
    man = {}
    for name, url in (("SmartLocationDb_v2.zip", "https://edg.epa.gov/data/PUBLIC/OP/SLD/SmartLocationDb.zip"),
                      ("SmartLocationDatabaseV3.zip", "https://edg.epa.gov/EPADataCommons/public/OA/SLD/SmartLocationDatabaseV3.zip")):
        p = out / name
        if not p.exists():
            p.write_bytes(_get(url))
        man[name] = {"url": url, "accessed": str(date.today()), "bytes": p.stat().st_size,
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "licence": "Public domain (US EPA)"}
        print(name, p.stat().st_size)
    (out / "manifest.json").write_text(json.dumps(man, indent=1))


STAGES = {"lodes": lodes, "nrhp": nrhp, "sld": sld}

if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("stage", choices=STAGES); STAGES[a.parse_args().stage]()

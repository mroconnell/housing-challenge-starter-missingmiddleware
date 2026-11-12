"""Parking dose-response: build each reform's DOSE from public data (docs/parking/DOSE_PLAN.md, Ryan's choices C1-C11
and the "Audit fixes" block). Reads NO permit outcomes: no permit or unit counts by place or year are read here.

    uv run python scripts/build_parking_doses.py            # writes reference/parking_doses.csv
    uv run python scripts/build_parking_doses.py --only oth_madison_2023   # print one reform, write nothing

Dose = 100 x (homes-weighted mean of the housing-requirement removal share over the place's homes).
  - Homes = 2020 Census block housing units (HOUSING20, TIGER/Line TABBLOCK20), each block placed in or out of an area by
    its Census internal point (INTPTLAT20/INTPTLON20) - the Seattle-test method. Place membership from the Census 2020
    Block Assignment Files (incorporated place / CDP, or county subdivision for New England-style towns). C10: 2020
    blocks for all places. Audit fix 5: for 2015-2019 mapped reforms, the same areas are also scored on 2010 blocks
    (HOUSING10 from TABBLOCK2010 POPHU, internal points from TIGER 2010 TABBLOCK10, 2010 BAF) as coverage_homes_share_2010.
  - removal share in an area = (old - new) / old for the standard 20-unit building (half 1BR, half 2BR), from the
    ordinance; a full repeal = 1. Overlapping areas: the largest removal applies to a block.
  - C4: for citywide repeals that followed an earlier partial reform (or where parts of the place were already exempt
    the day before), the per-block dose is the increment: max(0, new removal - removal already in force before).
  - coverage_homes_share = share of homes where the (incremental) removal is > 0; removal_share = homes-weighted mean
    removal among those homes; dose = coverage x removal x 100 (identical to the block-weighted mean).
  - coverage_zoned_land_share (check only, C2): share of apartment-zoned land (25 m grid points over the zoning
    polygons whose zone matches apt_regex) whose removal is > 0.
  - Fallbacks (C3, labelled 'fallback'): TOD 25, weak repeal 15, commercial/downtown 10, broad mapped district 25,
    citywide reduction with tables not coded 50 (a PLACEHOLDER, flagged), no change for housing 0.

Per-reform inputs: data/raw/parking_dose/<reform_id>/input.json (layers beside it, git-ignored); every input file is
also copied verbatim into reference/parking_dose_inputs.json at build time so the coding is auditable in git.
Schema of input.json:
  {"reform_id", "event_year", "type", "geo": {"state_fips": "17", "kind": "place"|"mcd", "geoid": "1714000"},
   "areas": [{"label", "removal": 0-1, "where": SPEC}],          # omit for a pure fallback
   "prior": [{"label", "removal": 0-1, "where": SPEC}],          # C4 only (removal already in force before)
   "zoning_check": {"layer", "field", "apt_regex", "spacing_m": 25, "clip_to_place": true},
   "blocks_2010": true,                                          # audit fix 5
   "dose_source": "computable"|"partly"|"fallback", "fallback_class": "...", "use_fallback": false,
   "dose_units_2_4": null,         # 2-4 unit outcome dose for use-type reforms (default = dose)
   "sensitivity": {"areas": [...], "prior": [...]},
   "state_law_prior": [{"label", "removal", "where"}],   # extra prior for the 'state laws as prior' variant   # optional second scoring -> dose_sensitivity_mapped
   "dose_override": null,          # a number only for doses that are pure arithmetic of the ordinance (e.g. a citywide
                                   # cut 1.5 -> 1 = 33.3), never for mapped areas
   "eligibility": "...", "sources": [...], "licences": [...], "notes": "..."}
SPEC (evaluated on points in EPSG:5070):
  "all" | {"layer": path, "field": f, "regex": r} | {"near": path, "radius_m": r, "filter": {...}}
  | {"and": [SPEC, ...]} | {"or": [SPEC, ...]} | {"not": SPEC}
  "near" sources: GeoJSON points / lines (densified every 20 m) / polygons (distance to edge, 0 inside), a JSON list of
  [lon, lat], or a GTFS zip (stops.txt; filter {"stop_id_regex", "location_type": [0, 1]}).
Relative paths resolve against the reform's folder; paths starting with "data/" against the repo root.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware import geom as G  # noqa: E402
from missing_middleware.dbf import read_dbf_bytes  # noqa: E402

UNIVERSE = ROOT / "reference/parking_dose_universe.csv"
OUT = ROOT / "reference/parking_doses.csv"
INPUTS_OUT = ROOT / "reference/parking_dose_inputs.json"
DOSE_DIR = ROOT / "data/raw/parking_dose"
CENSUS_DIR = DOSE_DIR / "_census"
UA = "missing-middleware-research/1.0 (public data)"

FALLBACK = {  # Ryan's fallbacks + C3 (2026-11-12)
    "TOD": 25.0, "weak repeal": 15.0, "commercial-only": 10.0, "broad district": 25.0,
    "reduction (tables not coded) PLACEHOLDER": 50.0, "no change for housing": 0.0,
}
STATE_ABBR = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC",
              "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
              "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT",
              "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
              "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
              "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY"}


# ------------------------------------------------------------------------------------------------ Census inputs
def _fetch(url: str, dest: Path) -> Path:
    """Download a public-domain Census file once (no spoofing: a plain research user agent)."""
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(str(dest) + ".part", "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    Path(str(dest) + ".part").rename(dest)
    log = CENSUS_DIR / "_downloads.json"
    rec = json.loads(log.read_text()) if log.exists() else []
    rec.append({"file": dest.name, "url": url, "licence": "Public domain (U.S. government work)",
                "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "bytes": dest.stat().st_size})
    log.write_text(json.dumps(rec, indent=1))
    return dest


def _dbf_from_zip(path: Path, columns: list[str]) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".dbf"))
        df = read_dbf_bytes(z.read(name))
    return df[columns]


_BLOCKS: dict = {}


def blocks(state_fips: str, year: int) -> pd.DataFrame:
    """GEOID, hu, lon, lat for every block in a state (2020 or 2010)."""
    key = (state_fips, year)
    if key in _BLOCKS:
        return _BLOCKS[key]
    if year == 2020:
        held = ROOT / f"data/raw/census_tiger_2020_tabblock/tl_2020_{state_fips}_tabblock20.zip"
        p = held if held.exists() else _fetch(
            f"https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{state_fips}_tabblock20.zip",
            CENSUS_DIR / f"tl_2020_{state_fips}_tabblock20.zip")
        d = _dbf_from_zip(p, ["GEOID20", "HOUSING20", "INTPTLAT20", "INTPTLON20"])
        d.columns = ["GEOID", "hu", "lat", "lon"]
    else:
        p1 = _fetch(f"https://www2.census.gov/geo/tiger/TIGER2010/TABBLOCK/2010/tl_2010_{state_fips}_tabblock10.zip",
                    CENSUS_DIR / f"tl_2010_{state_fips}_tabblock10.zip")
        p2 = _fetch(f"https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_{state_fips}_pophu.zip",
                    CENSUS_DIR / f"tabblock2010_{state_fips}_pophu.zip")
        a = _dbf_from_zip(p1, ["GEOID10", "INTPTLAT10", "INTPTLON10"])
        b = _dbf_from_zip(p2, ["BLOCKID10", "HOUSING10"])
        d = a.merge(b, left_on="GEOID10", right_on="BLOCKID10", how="left")
        d = d[["GEOID10", "HOUSING10", "INTPTLAT10", "INTPTLON10"]]
        d.columns = ["GEOID", "hu", "lat", "lon"]
    d["GEOID"] = d["GEOID"].astype(str)
    d["hu"] = pd.to_numeric(d["hu"], errors="coerce").fillna(0.0)
    d["lat"] = pd.to_numeric(d["lat"], errors="coerce")
    d["lon"] = pd.to_numeric(d["lon"], errors="coerce")
    _BLOCKS[key] = d
    return d


def baf(state_fips: str, year: int, kind: str) -> pd.DataFrame:
    """Block -> place (kind 'place') or county subdivision (kind 'mcd') GEOID, from the Census Block Assignment Files."""
    ab = STATE_ABBR[state_fips]
    if year == 2020:
        url = f"https://www2.census.gov/geo/docs/maps-data/data/baf2020/BlockAssign_ST{state_fips}_{ab}.zip"
        dest = CENSUS_DIR / f"BlockAssign2020_ST{state_fips}_{ab}.zip"
    else:
        url = f"https://www2.census.gov/geo/docs/maps-data/data/baf/BlockAssign_ST{state_fips}_{ab}.zip"
        dest = CENSUS_DIR / f"BlockAssign2010_ST{state_fips}_{ab}.zip"
    p = _fetch(url, dest)
    tag = "INCPLACE_CDP" if kind == "place" else "MCD"
    with zipfile.ZipFile(p) as z:
        name = next(n for n in z.namelist() if tag in n.upper() and n.lower().endswith(".txt"))
        raw = z.read(name).decode("latin-1")
    sep = "|" if "|" in raw.splitlines()[0] else ","
    d = pd.read_csv(io.StringIO(raw), sep=sep, dtype=str)
    d.columns = [c.strip().upper() for c in d.columns]
    bid = d.columns[0]
    if kind == "place":
        pcol = next(c for c in d.columns if c.startswith("PLACE"))
        geo = state_fips + d[pcol].fillna("").str.zfill(5)
    else:
        ccol = next(c for c in d.columns if c.startswith("COUNTY"))
        mcol = next(c for c in d.columns if c.startswith("COUSUB"))
        geo = state_fips + d[ccol].fillna("").str.zfill(3) + d[mcol].fillna("").str.zfill(5)
    return pd.DataFrame({"GEOID": d[bid].astype(str), "geo": geo})


def place_blocks(g: dict, year: int) -> pd.DataFrame:
    b = blocks(g["state_fips"], year)
    a = baf(g["state_fips"], year, g.get("kind", "place"))
    ids = set(a.loc[a["geo"] == g["geoid"], "GEOID"])
    if not ids:
        raise ValueError(f"no {year} blocks for {g}")
    out = b[b["GEOID"].isin(ids)].reset_index(drop=True)
    x, y = G.transform(out["lon"].to_numpy(), out["lat"].to_numpy(), 4326, 5070)
    out["x"], out["y"] = x, y
    return out


# ------------------------------------------------------------------------------------------------ area specs
_LAYERS: dict = {}


def _path(p: str, base: Path) -> Path:
    return ROOT / p if p.startswith("data/") else base / p


def _layer(path: Path) -> G.Layer:
    if path not in _LAYERS:
        L = G.read_any(path)
        if L.kind != "point":  # drop features with empty geometry (e.g. INCOG Tulsa OBJECTID 18758)
            L = L.subset(np.array([bool(f) and all(len(part) for part in f) for f in L.polys]))
        _LAYERS[path] = L.to_crs(5070)
    return _LAYERS[path]


def _near_targets(spec: dict, base: Path):
    """Return ('points', x, y) or ('polys', polys) in EPSG:5070."""
    p = _path(spec["near"], base)
    flt = spec.get("filter") or {}
    if p.suffix.lower() == ".zip":  # GTFS
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.endswith("stops.txt"))
            s = pd.read_csv(z.open(name), dtype=str, skipinitialspace=True)
        s.columns = [c.strip() for c in s.columns]
        if "location_type" in flt and "location_type" in s.columns:
            s = s[s["location_type"].fillna("0").replace("", "0").astype(int).isin(flt["location_type"])]
        if "stop_id_regex" in flt:
            s = s[s["stop_id"].str.match(flt["stop_id_regex"])]
        x, y = G.transform(s["stop_lon"].astype(float).to_numpy(), s["stop_lat"].astype(float).to_numpy(), 4326, 5070)
        return "points", x, y
    obj = json.loads(p.read_text())
    if isinstance(obj, list):
        a = np.array(obj, float).reshape(-1, 2)
        x, y = G.transform(a[:, 0], a[:, 1], 4326, 5070)
        return "points", x, y
    L = _layer(p)
    if "field" in flt:
        L = L.subset(L.attrs[flt["field"]].astype(str).str.match(flt["regex"]).to_numpy())
    if L.kind == "point":
        return "points", L.x, L.y
    if L.kind == "line":
        xs, ys = [], []
        for feat in L.polys:
            for part in feat:
                for (x0, y0), (x1, y1) in zip(part[:-1], part[1:]):
                    n = max(1, int(np.ceil(np.hypot(x1 - x0, y1 - y0) / 20.0)))
                    t = np.linspace(0, 1, n + 1)
                    xs.append(x0 + t * (x1 - x0)); ys.append(y0 + t * (y1 - y0))
        return "points", np.concatenate(xs), np.concatenate(ys)
    return "polys", L.polys


def evaluate(spec, px, py, base: Path) -> np.ndarray:
    if spec == "all":
        return np.ones(len(px), bool)
    if "and" in spec:
        m = np.ones(len(px), bool)
        for s in spec["and"]:
            m &= evaluate(s, px, py, base)
        return m
    if "or" in spec:
        m = np.zeros(len(px), bool)
        for s in spec["or"]:
            m |= evaluate(s, px, py, base)
        return m
    if "not" in spec:
        return ~evaluate(spec["not"], px, py, base)
    if "layer" in spec:
        L = _layer(_path(spec["layer"], base))
        if spec.get("field"):
            L = L.subset(L.attrs[spec["field"]].astype(str).fillna("").str.match(spec["regex"]).to_numpy())
        return G.points_in_any(px, py, L.polys, union=True)
    if "near" in spec:
        r = float(spec["radius_m"])
        t = _near_targets(spec, base)
        if t[0] == "points":
            if not len(t[1]):
                return np.zeros(len(px), bool)
            _, d = G.nearest(px, py, t[1], t[2], max_distance=r)
            return np.isfinite(d) & (d <= r)
        return np.isfinite(G.distance_to_polygons(px, py, t[1], r))
    raise ValueError(f"bad spec {spec}")


def removal_surface(areas: list, px, py, base: Path) -> np.ndarray:
    rem = np.zeros(len(px))
    for a in areas or []:
        m = evaluate(a["where"], px, py, base)
        rem = np.where(m, np.maximum(rem, float(a["removal"])), rem)
    return rem


def score(inp: dict, base: Path, year: int) -> dict:
    b = place_blocks(inp["geo"], year)
    px, py, hu = b["x"].to_numpy(), b["y"].to_numpy(), b["hu"].to_numpy()
    new = removal_surface(inp.get("areas"), px, py, base)
    old = removal_surface(inp.get("prior"), px, py, base)
    inc = np.clip(new - old, 0, 1)
    tot = hu.sum()
    cov = hu[inc > 0].sum() / tot
    rem = (hu * inc).sum() / hu[inc > 0].sum() if cov > 0 else 0.0
    return {"homes": float(tot), "coverage": float(cov), "removal": float(rem), "dose": float(100 * (hu * inc).sum() / tot),
            "prior_exempt_share": float(hu[old > 0].sum() / tot) if inp.get("prior") else None,
            "prior_removal_mean": float((hu * old).sum() / tot) if inp.get("prior") else None}


def zoned_land_check(inp: dict, base: Path):
    z = inp.get("zoning_check")
    if not z:
        return None
    L = _layer(_path(z["layer"], base))
    L = L.subset(L.attrs[z["field"]].astype(str).fillna("").str.match(z["apt_regex"]).to_numpy())
    if not len(L):
        return None
    sp = float(z.get("spacing_m", 25))
    x0, y0, x1, y1 = G.bbox(L)
    gx, gy = np.meshgrid(np.arange(x0, x1, sp), np.arange(y0, y1, sp))
    px, py = gx.ravel(), gy.ravel()
    keep = G.points_in_any(px, py, L.polys, union=True)
    if z.get("clip"):
        keep &= G.points_in_any(px, py, _layer(_path(z["clip"], base)).polys, union=True)
    px, py = px[keep], py[keep]
    if not len(px):
        return None
    inc = np.clip(removal_surface(inp.get("areas"), px, py, base) - removal_surface(inp.get("prior"), px, py, base), 0, 1)
    return float((inc > 0).mean())


# ------------------------------------------------------------------------------------------------ assembly
COLS = ["reform_id", "place", "state", "event_year", "type", "event_used", "eligibility", "coverage_homes_share",
        "coverage_homes_share_2010", "coverage_zoned_land_share", "removal_share", "dose", "dose_source",
        "dose_units_2_4", "dose_sensitivity_mapped", "dose_if_unlicensed_refused", "dose_state_law_prior", "fallback_class", "prior_exempt_homes_share",
        "prior_removal_homes_mean", "homes_2020", "sources", "licences", "notes"]


def default_row(u: dict) -> dict:
    """A reform with no input file: citywide repeals in the 74 keep 100 (C4 not yet checked); others take the
    fallback class's dose."""
    r = {c: "" for c in COLS}
    r.update(reform_id=u["reform_id"], place=u["place"], state=u["state"], event_year=u["year"], type=u["type"],
             eligibility=u["could_join"])
    if u["type"] == "citywide residential":
        r.update(coverage_homes_share=1.0, removal_share=1.0, dose=100.0, dose_source=u["dose_status"] or "computable",
                 notes="citywide repeal: dose 100 by definition; no input file (C4 earlier-partial-reform check not recorded)")
    else:
        r.update(dose=u["fallback_dose"] or "", dose_source="fallback", notes="no input file: universe fallback")
    return r


def build_row(u: dict, inp: dict, base: Path) -> dict:
    r = default_row(u)
    r.update(event_year=inp.get("event_year", u["year"]), type=inp.get("type", u["type"]),
             eligibility=inp.get("eligibility", u["could_join"]), fallback_class=inp.get("fallback_class", ""),
             sources=" ; ".join(inp.get("sources", [])), licences=" ; ".join(inp.get("licences", [])),
             notes=inp.get("notes", ""), dose_source=inp.get("dose_source", ""))
    if inp.get("use_fallback") or (not inp.get("areas") and inp.get("dose_override") is None):
        fc = inp.get("fallback_class", "")
        r.update(dose=FALLBACK[fc] if fc in FALLBACK else u["fallback_dose"], dose_source="fallback",
                 coverage_homes_share="", removal_share="")
        if "PLACEHOLDER" in fc:
            r["notes"] = ("C3 PLACEHOLDER dose 50 (tables not coded). " + r["notes"]).strip()
        return r
    if inp.get("dose_override") is not None:  # pure ordinance arithmetic, citywide
        r.update(dose=float(inp["dose_override"]), coverage_homes_share=inp.get("coverage_override", 1.0),
                 removal_share=inp.get("removal_override", float(inp["dose_override"]) / 100))
        if inp.get("state_law_prior"):  # citywide arithmetic, with the state-law areas netted out
            v = {"geo": inp["geo"], "areas": [{"removal": float(r["removal_share"]), "where": "all"}],
                 "prior": inp["state_law_prior"]}
            r["dose_state_law_prior"] = round(score(v, base, 2020)["dose"] * float(inp["dose_override"]) /
                                              (100 * float(r["removal_share"])), 2)
        return r
    s = score(inp, base, 2020)
    r.update(coverage_homes_share=round(s["coverage"], 4), removal_share=round(s["removal"], 4),
             dose=round(s["dose"], 2), homes_2020=int(s["homes"]))
    if s["prior_exempt_share"] is not None:
        r["prior_exempt_homes_share"] = round(s["prior_exempt_share"], 4)
        r["prior_removal_homes_mean"] = round(s["prior_removal_mean"], 4)
    if inp.get("state_law_prior"):  # audit variant: state transit laws counted as prior everywhere
        v = dict(inp, prior=(inp.get("prior") or []) + inp["state_law_prior"])
        r["dose_state_law_prior"] = round(score(v, base, 2020)["dose"], 2)
    if inp.get("sensitivity"):  # e.g. mapped carve-out for near-benchmark places (main dose per plan)
        r["dose_sensitivity_mapped"] = round(score(inp["sensitivity"] | {"geo": inp["geo"]}, base, 2020)["dose"], 2)
    if inp.get("blocks_2010"):
        try:
            r["coverage_homes_share_2010"] = round(score(inp, base, 2010)["coverage"], 4)
        except Exception as e:  # noqa: BLE001
            r["notes"] += f" [2010 block check failed: {e}]"
    try:
        z = zoned_land_check(inp, base)
        r["coverage_zoned_land_share"] = "" if z is None else round(z, 4)
    except Exception as e:  # noqa: BLE001
        r["notes"] += f" [zoned-land check failed: {e}]"
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--out", default=str(OUT), help="output CSV (default reference/parking_doses.csv)")
    ap.add_argument("--spokane-event", choices=["2023", "2024", "pending"], default="pending",
                    help="which Spokane step is the event (C9 says 2023; coordinator asked Ryan 2026-11-12)")
    a = ap.parse_args()
    uni = list(csv.DictReader(open(UNIVERSE)))
    rows, inputs = [], {}
    for u in uni:
        if u["could_join"].lower().startswith("no") or u["reform_id"].startswith(("oth_california_statewide",
                                                                                     "oth_oregon_cfec")):
            continue
        if a.only and u["reform_id"] != a.only:
            continue
        base = DOSE_DIR / u["reform_id"]
        f = base / "input.json"
        if f.exists():
            inp = json.loads(f.read_text())
            inputs[u["reform_id"]] = inp
            r = build_row(u, inp, base)
        else:
            r = default_row(u)
        r["event_used"] = inputs.get(u["reform_id"], {}).get("event_used", "yes")
        if u["reform_id"] in ("oth_spokane_2023", "oth_spokane_2024"):  # staged; choice pending (coordinator 2026-11-12)
            yr = u["reform_id"][-4:]
            r["event_used"] = ("pending (Spokane event year not yet chosen)" if a.spokane_event == "pending"
                               else ("yes" if yr == a.spokane_event else f"no (Spokane event = {a.spokane_event})"))
        if r["dose_state_law_prior"] in ("", None):
            r["dose_state_law_prior"] = r["dose"]
        # audit: the dose this row falls back to if Ryan refuses layers with no stated licence (or a use-restricted one)
        lic = str(r["licences"]).lower()
        if ("no licence stated" in lic or "no license stated" in lic or "illustrative" in lic) and r["dose_source"] != "fallback":
            fc = r["fallback_class"]
            r["dose_if_unlicensed_refused"] = (100.0 if u["type"] == "citywide residential" else
                                               FALLBACK[fc] if fc in FALLBACK else (u["fallback_dose"] or ""))
        else:
            r["dose_if_unlicensed_refused"] = r["dose"]
        d24 = inputs.get(u["reform_id"], {}).get("dose_units_2_4")
        r["dose_units_2_4"] = r["dose"] if d24 is None else d24
        rows.append(r)
        print(u["reform_id"], r["dose"], r["dose_source"], r["coverage_homes_share"], r["removal_share"], flush=True)
    if a.only:
        print(json.dumps(rows, indent=1, default=str))
        return
    out = Path(a.out)
    pd.DataFrame(rows, columns=COLS).to_csv(out, index=False)
    INPUTS_OUT.write_text(json.dumps(inputs, indent=1, sort_keys=True))
    print("wrote", out, len(rows), "rows; sha256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()

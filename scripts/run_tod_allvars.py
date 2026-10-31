"""Run the TOD all-variables test (docs/tod/ALLVARS_PLAN.md) in its pre-set order.

    uv run --all-extras python scripts/run_tod_allvars.py --stage fetch    # ACS tract tables, TIGER 2000 tracts
    uv run --all-extras python scripts/run_tod_allvars.py --stage values   # 1. variable map and values, before any fit
    uv run --all-extras python scripts/run_tod_allvars.py --stage fit      # 2-3. models, pass rule, robustness checks

Fetch: the plan names the Census Data API, which now refuses calls without a key. With CENSUS_API_KEY set the API is
used; without it the same estimates are read from the Census summary files (per-state, per-sequence files for the
2005-2009 to 2014-2018 releases; the national table-based files for 2018-2022, of which only Wisconsin tract rows are
kept). Every file's URL, bytes and SHA-256 are in data/raw/tod_allvars/manifest.json (git-ignored).

Outputs (no parcel, permit, project or person identifiers):
- reference/tod_allvars_variable_map.csv  one row per variable: id, label, group, unit, ACS table, cells or formula
- reference/tod_allvars_values.csv        one row per unit: the ACS survey years and tract boundaries used, every variable
- reference/tod_allvars_models.csv        one row per model: verdict, errors by city, robustness checks
Units, folds, baseline, error and pass rule: missing_middleware/tod/traits.py and scripts/run_tod_traits.py (imported).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import allvars as A  # noqa: E402
from missing_middleware.tod import traits as T  # noqa: E402

RAWV = RAW / "tod_allvars"
MAP_CSV = REFERENCE / "tod_allvars_variable_map.csv"
VALUES_CSV = REFERENCE / "tod_allvars_values.csv"
MODELS_CSV = REFERENCE / "tod_allvars_models.csv"
ERRORS_PKL = "allvars_errors.pkl"
CENSUS_LICENCE = "Public domain (U.S. government work)"
SF = "https://www2.census.gov/programs-surveys/acs/summary_file"
STATES = {"36": ("NewYork", "ny"), "53": ("Washington", "wa"), "27": ("Minnesota", "mn"), "06": ("California", "ca"),
          "17": ("Illinois", "il"), "42": ("Pennsylvania", "pa"), "37": ("NorthCarolina", "nc"), "55": ("Wisconsin", "wi"),
          "29": ("Missouri", "mo"), "39": ("Ohio", "oh")}   # 29, 39: no-reform cities of the lot model (item 46)
CITY_STATE = {"New York": "36", "Philadelphia": "42", "Charlotte": "37", "Saint Paul": "27", "Chicago": "17", "Madison": "55",
              "Los Angeles": "06", "Seattle": "53", "Bellevue": "53"}   # Toronto: no ACS
CITY_KEY = {"New York": "nyc", "Philadelphia": "philadelphia", "Charlotte": "charlotte", "Saint Paul": "stpaul", "Chicago": "chicago",
            "Madison": "madison", "Los Angeles": "la", "Seattle": "seattle", "Bellevue": "bellevue", "Toronto": "toronto"}
UA = {"User-Agent": "missing-middleware research (TOD all-variables test)"}


# =========================================================================== units and the surveys they need

def units() -> pd.DataFrame:
    import run_tod_traits as R
    u = pd.read_csv(R.UNITS_CSV)
    u = u[u["kept"] & u["city"].isin(T.WIDE_CITY_ORDER)].copy()
    u["end_year"] = u["effective_year"].map(A.survey_end_year)
    u["state"] = u["city"].map(CITY_STATE)
    return u


def needs() -> list[tuple[int, str]]:
    u = units().dropna(subset=["state"])
    return sorted({(int(y), s) for y, s in zip(u["end_year"], u["state"])})


# =========================================================================== fetch

def lookup_url(y: int) -> str:
    if y <= 2012:
        return f"{SF}/{y}/documentation/5_year/user_tools/Sequence_Number_and_Table_Number_Lookup.txt"
    return f"{SF}/{y}/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt"


def seq_dir_alt(y: int, st: str) -> str | None:
    return f"{SF}/{y}/data/5_year_seq_by_state/{STATES[st][0]}/Tracts_Block_Groups_Only" if y <= 2013 else None


def seq_dir(y: int, st: str) -> str:
    """Per-sequence files of a release. Through 2009-2013 the older acsYYYY_5yr folders hold the same files and answered
    far faster on 2026-10-27; later releases are only under programs-surveys."""
    if y <= 2013:
        return f"https://www2.census.gov/acs{y}_5yr/summaryfile/{y - 4}-{y}_ACSSF_By_State_By_Sequence_Table_Subset/{STATES[st][0]}/Tracts_Block_Groups_Only"
    return f"{SF}/{y}/data/5_year_seq_by_state/{STATES[st][0]}/Tracts_Block_Groups_Only"


def get(url: str, timeout: int = 100, tries: int = 60, alt: str | None = None) -> tuple[bytes, str]:
    """The file and the URL it came from. The Census file server stalls on some requests and answers the same request
    at once a moment later, so requests are short and retried, alternating with a mirror folder when one exists."""
    urls = [url] + ([alt] if alt else [])
    for k in range(tries):
        u = urls[k % len(urls)]
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
                data, n = r.read(), r.headers.get("Content-Length")
            # the server sometimes closes a transfer early without an error: check length and zip integrity
            if n is not None and len(data) != int(n):
                raise IOError(f"short read {len(data)} of {n}")
            if u.endswith(".zip") and not zip_ok(data):
                raise IOError("damaged zip")
            return data, u
        except Exception as e:
            if (getattr(e, "code", None) == 404 and not alt) or k == tries - 1:
                raise
            time.sleep(min(20, 2 * (k + 1)))
    raise AssertionError


def zip_ok(data: bytes) -> bool:
    try:
        return zipfile.ZipFile(io.BytesIO(data)).testzip() is None
    except Exception:
        return False


class Man:
    def __init__(self):
        RAWV.mkdir(parents=True, exist_ok=True)
        self.path = RAWV / "manifest.json"
        self.m = json.loads(self.path.read_text()) if self.path.exists() else {"source_id": "tod_allvars", "publisher": "U.S. Census Bureau", "files": {}}

    def have(self, name):
        p = RAWV / name
        if not (name in self.m["files"] and p.exists()):
            return False
        return zip_ok(p.read_bytes()) if name.endswith(".zip") else p.stat().st_size == self.m["files"][name]["bytes"]

    def record(self, name, data: bytes, url, **kw):
        p = RAWV / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        self.m["files"][name] = {"url": url, "accessed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "bytes": len(data),
                                 "sha256": hashlib.sha256(data).hexdigest(), "licence": CENSUS_LICENCE, **kw}
        self.path.write_text(json.dumps(self.m, indent=1) + "\n")


def read_lookup(y: int) -> pd.DataFrame:
    lk = pd.read_csv(RAWV / f"{y}/lookup.txt", dtype=str, encoding="latin-1")
    # column names differ between releases; the order does not
    std = ["File ID", "Table ID", "Sequence Number", "Line Number", "Start Position", "Total Cells in Table",
           "Total Cells in Sequence", "Table Title"]
    lk = lk.iloc[:, :8].copy()
    lk.columns = std
    for c in std:
        lk[c] = lk[c].str.strip().replace({"": np.nan, ".": np.nan})
    return lk


def table_positions(lk: pd.DataFrame, table: str) -> tuple[list[tuple[int, int, int]], int, dict]:
    """[(sequence, first line, start column)], number of cells, and {line: title} of a table in a release."""
    rows = lk[lk["Table ID"] == table]
    starts = rows[rows["Start Position"].notna()]
    n = int(str(starts["Total Cells in Table"].dropna().iloc[0]).split()[0])
    num = rows[rows["Line Number"].fillna("").str.strip().str.fullmatch(r"\d+")]
    titles = {int(ln): str(tt) for ln, tt in zip(num["Line Number"], num["Table Title"])}
    parts, first = [], 1
    for seq, start in zip(starts["Sequence Number"], starts["Start Position"]):
        parts.append((int(seq), first, int(start)))
        first += int((num["Sequence Number"] == seq).sum())
    return parts, n, titles


def stage_fetch() -> None:
    man = Man()
    key = os.environ.get("CENSUS_API_KEY")
    nd = needs()
    print("surveys needed (end year, state):", nd)
    if key:
        raise SystemExit("CENSUS_API_KEY is set: the API path is not implemented in this run because no key was available "
                         "when it was written (see plan section 6); unset it to use the summary files.")
    tables = A.tables_used()
    jobs = []
    for y in sorted({y for y, _ in nd if y <= 2019}):
        if not man.have(f"{y}/lookup.txt"):
            man.record(f"{y}/lookup.txt", get(lookup_url(y))[0], lookup_url(y), note=f"ACS {A.survey_label(y)} 5-year sequence/table lookup")
        lk = read_lookup(y)
        seqs = sorted({p[0] for t in tables if (lk["Table ID"] == t).any() for p in table_positions(lk, t)[0]})
        missing = [t for t in tables if not (lk["Table ID"] == t).any()]
        if missing:
            print(f"  {y}: tables not in this release: {missing}")
        for _, st in [(a, b) for a, b in nd if a == y]:
            ab = STATES[st][1]
            alt = seq_dir_alt(y, st)
            jobs.append((f"{y}/{ab}/g{y}5{ab}.txt", f"{seq_dir(y, st)}/g{y}5{ab}.txt", "geography file", alt and f"{alt}/g{y}5{ab}.txt"))
            for q in seqs:
                f = f"{y}5{ab}{q:04d}000.zip"
                jobs.append((f"{y}/{ab}/{f}", f"{seq_dir(y, st)}/{f}", f"sequence {q}, tracts and block groups", alt and f"{alt}/{f}"))
    for st in sorted({s for y, s in nd if y == 2009}):
        jobs.append((f"tiger2000/tl_2010_{st}_tract00.zip", f"https://www2.census.gov/geo/tiger/TIGER2010/TRACT/2000/tl_2010_{st}_tract00.zip",
                     "TIGER/Line 2010 release, 2000 census tracts", None))
    jobs = [j for j in jobs if not man.have(j[0])]
    print(f"{len(jobs)} files to fetch")

    def one(j):
        return j, get(j[1], alt=j[3])
    with cf.ThreadPoolExecutor(12) as ex:
        for fut in cf.as_completed([ex.submit(one, j) for j in jobs]):
            (name, _, note, _), (data, url) = fut.result()
            man.record(name, data, url, note=note)
            print(f"  {name}: {len(data):,} bytes", flush=True)
    # 2018-2022 (Madison): national table-based files, Wisconsin tract rows kept; hash is of the whole file as served
    for y in sorted({y for y, _ in nd if y >= 2021}):
        sts = sorted({s for yy, s in nd if yy == y})

        def tb(t, y=y, sts=sts):
            name = f"{y}/tbsf/acsdt5y{y}-{t.lower()}_tracts_{'_'.join(sts)}.dat"
            if man.have(name):
                return None
            url = f"{SF}/{y}/table-based-SF/data/5YRData/acsdt5y{y}-{t.lower()}.dat"
            for k in range(6):
                try:
                    h, n, keep = hashlib.sha256(), 0, []
                    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=900) as r:
                        first = True
                        for line in r:
                            h.update(line)
                            n += len(line)
                            if first or any(line.startswith(f"1400000US{s}".encode()) for s in sts):
                                keep.append(line)
                            first = False
                    return name, url, b"".join(keep), n, h.hexdigest()
                except Exception as e:
                    if getattr(e, "code", None) == 404:
                        return name, url, None, 0, ""
                    if k == 5:
                        raise
                    time.sleep(10 * (k + 1))
        with cf.ThreadPoolExecutor(4) as ex:
            for res in ex.map(tb, tables):
                if res is None:
                    continue
                name, url, data, n, hx = res
                if data is None:
                    print(f"  {name}: not published (404)")
                    continue
                man.record(name, data, url, source_bytes=n, source_sha256=hx,
                           note=f"ACS {A.survey_label(y)} table-based summary file; only the header and tract rows of states {sts} kept")
                print(f"  {name}: {len(data):,} bytes kept of {n:,}", flush=True)
    print("fetched into", RAWV)


# =========================================================================== values

def seq_cells(y: int, st: str) -> tuple[pd.DataFrame, dict, dict]:
    """Tract cells of one release and state: DataFrame indexed by 11-digit tract GEOID with columns TABLE_line;
    table lengths; line titles (for checks)."""
    ab = STATES[st][1]
    lk = read_lookup(y)
    gtxt = (RAWV / f"{y}/{ab}/g{y}5{ab}.txt").read_bytes().decode("latin-1").splitlines()
    g = pd.DataFrame({"logrecno": [s[13:20] for s in gtxt], "geoid": [s[178:218].strip() for s in gtxt]})
    g = g[g["geoid"].str.startswith("14000US")]
    g = g.set_index("logrecno")
    cols, ncells, titles, cache = {}, {}, {}, {}
    for t in A.tables_used():
        if not (lk["Table ID"] == t).any():
            continue
        parts, n, tt = table_positions(lk, t)
        ncells[t], titles[t] = n, tt
        bounds = [p[1] for p in parts[1:]] + [n + 1]
        for (seq, first, start), last in zip(parts, bounds):
            if seq not in cache:
                z = zipfile.ZipFile(RAWV / f"{y}/{ab}/{y}5{ab}{seq:04d}000.zip")
                ef = next(nm for nm in z.namelist() if nm.lower().startswith("e"))
                e = pd.read_csv(z.open(ef), header=None, dtype=str, encoding="latin-1")
                cache[seq] = e.set_index(e[5].astype(str).str.strip())
            e = cache[seq]
            for ln in range(first, last):
                cols[f"{t}_{ln}"] = pd.to_numeric(e[start - 1 + ln - first], errors="coerce").reindex(g.index).values
    out = pd.DataFrame(cols, index=g["geoid"].str[7:].values)
    return out, ncells, titles


def tbsf_cells(y: int, st: str) -> tuple[pd.DataFrame, dict, dict]:
    res, ncells = None, {}
    for t in A.tables_used():
        fs = list((RAWV / f"{y}/tbsf").glob(f"acsdt5y{y}-{t.lower()}_tracts_*.dat"))
        if not fs:
            continue
        d = pd.read_csv(fs[0], sep="|", dtype=str)
        d = d[d["GEO_ID"].str.startswith(f"1400000US{st}")]
        ecols = [c for c in d.columns if c.startswith(f"{t}_E")]
        ncells[t] = len(ecols)
        x = pd.DataFrame({f"{t}_{int(c.split('_E')[1])}": pd.to_numeric(d[c], errors="coerce").values for c in ecols},
                         index=d["GEO_ID"].str[9:].values)
        res = x if res is None else res.join(x, how="outer")
    return res, ncells, {}


# label checks: the lines this module assumes, against each release's own titles (2005-2009 to 2014-2018)
LABEL_CHECKS = {("B25034", -1): r"1939 or earlier", ("B25034", -7): r"1990 to 1999", ("B23001", 4): r"In labor force",
                ("B23001", 8): r"Unemployed", ("B23001", 74): r"In labor force", ("B23001", 170): r"In labor force",
                ("B23001", 172): r"Unemployed", ("B07001", 17): r"Same house", ("B08301", 10): r"Public transportation",
                ("B08301", 21): r"Worked at home", ("B25070", 11): r"Not computed", ("B15002", 15): r"Bachelor",
                ("B15002", 35): r"Doctorate", ("B01001", 26): r"Female", ("B25044", 10): r"No vehicle",
                ("B08302", 7): r"7:00", ("B08303", 11): r"45 to 59", ("B19001", 14): r"100,000", ("B25014", 11): r"1.01",
                ("B11001", 8): r"alone", ("B11005", 2): r"under 18", ("B08008", 3): r"Worked in place of residence",
                ("B25024", 9): r"50 or more", ("B17001", 2): r"below poverty", ("B19058", 2): r"public assistance|Food Stamps|SNAP"}


def check_labels(titles: dict, ncells: dict, where: str) -> list[str]:
    import re
    bad = []
    for (t, ln), pat in LABEL_CHECKS.items():
        if t not in titles or not titles[t]:
            continue
        line = A.resolve_line(ln, ncells[t])
        got = titles[t].get(line, "")
        if not re.search(pat, got, re.I):
            bad.append(f"{where} {t} line {line}: '{got}' does not match '{pat}'")
    return bad


def tract_shapes(vintage: str, st: str):
    import geopandas as gpd
    if vintage == "2000":
        g = gpd.read_file(f"zip://{RAWV / 'tiger2000' / f'tl_2010_{st}_tract00.zip'}")
        return gpd.GeoDataFrame({"tract": g["CTIDFP00"], "ALAND_SQMI": g["ALAND00"].astype(float) / A.SQM_PER_SQMI}, geometry=g.geometry, crs=g.crs)
    if vintage == "2010":
        g = gpd.read_file(f"zip://{RAW / 'tod_traits' / 'tiger2010' / f'tl_2010_{st}_tract10.zip'}")
        return gpd.GeoDataFrame({"tract": g["GEOID10"], "ALAND_SQMI": g["ALAND10"].astype(float) / A.SQM_PER_SQMI}, geometry=g.geometry, crs=g.crs)
    g = gpd.read_file(f"zip://{RAW / 'census_tiger_2024' / f'tl_2024_{st}_tract.zip'}")
    return gpd.GeoDataFrame({"tract": g["GEOID"], "ALAND_SQMI": g["ALAND"].astype(float) / A.SQM_PER_SQMI}, geometry=g.geometry, crs=g.crs)


def built_traits(u: pd.DataFrame) -> pd.DataFrame:
    tv = pd.read_csv(REFERENCE / "tod_trait_values.csv")
    cov = pd.read_csv(REFERENCE / "tod_coverage_traits.csv")
    cov = cov[cov["level"] == "unit"]
    b = u[["unit_id", "city", "unit_name"]].merge(tv[["unit_id"] + [t for t in A.BUILT if t.startswith("t")]], on="unit_id", how="left")
    ncols = [t for t in A.BUILT if t.startswith("n")]
    b = b.merge(cov[["city", "unit_name"] + ncols].drop_duplicates(["city", "unit_name"]), on=["city", "unit_name"], how="left")
    return b.drop(columns="unit_name")


def stage_values() -> pd.DataFrame:
    import geopandas as gpd
    import run_tod_traits as R
    u = units()
    # 1. the variable map, before any value is joined to an effect
    rows = []
    for v in A.VARIABLES:
        tabs = sorted({k.rsplit("_", 1)[0] for part in (v["num"], v["den"] or {}) for k in part if k != "ALAND_SQMI"})
        rows.append({"variable_id": v["id"], "label": v["label"], "group": v["group"], "unit": v["unit"],
                     "source": "ACS 5-year detailed tables, by tract" + ("; TIGER/Line tract land area" if "ALAND" in v["cells_text"] or "land area" in v["cells_text"] else ""),
                     "acs_tables": " ".join(tabs), "cells_or_formula": v["cells_text"],
                     "unit_aggregation": "acre-weighted sum of tract numerators / acre-weighted sum of tract denominators" if v["kind"] == "ratio"
                     else "acre-weighted mean of tract values",
                     "dollars": "2024 dollars (CPI-U, survey end year)" if v["dollars"] else "", "entered_as": "log(value)" if v["log"] else "value",
                     "survey": "5-year ACS ending the year before the reform (2005-2009 for reforms of 2010 or earlier); per unit in tod_allvars_values.csv"})
    labels = {"t02_lot_size": "Average lot size of treatment parcels (acres per lot)", "t03_existing_density": "Existing density (homes per eligible acre before)",
              "t07_added_far": "Size of the upzoning (added floor area ratio)", "t08_rate_before": "Building rate before (homes permitted per eligible acre per year)",
              "t09_vacant_parking_industrial_share": "Share of treatment land vacant, parking or industrial", "t10_km_to_downtown": "Distance to downtown (km)",
              "t11_transit_jobs_access": "Jobs reachable by transit (EPA D5BR)", "t12_parking_cut": "Reform also cut parking minimums (1 = yes)",
              "n01_island_acres": "Island size (acres of the covered patch)", "n02_largest_site_acres": "Largest contiguous upzoned site (acres)",
              "n03_elongation": "Elongation of the upzoned patch (length / width)", "n04_corridor_share": "Corridor share (land in pieces at least 1/2 mile long)",
              "n05_binding_ratio": "Binding limit (homes per acre before / homes per acre the old FAR allowed)"}
    for t, (src, how) in A.BUILT.items():
        rows.append({"variable_id": t, "label": labels[t], "group": "already built for the TOD tests", "unit": "", "source": f"reference/{src}",
                     "acs_tables": "", "cells_or_formula": "as built for the trait test (TRAITS_PLAN.md) or net-effect test (NET_EFFECT_PLAN.md)",
                     "unit_aggregation": "unit value", "dollars": "", "entered_as": how, "survey": "see the trait's own plan"})
    vm = pd.DataFrame(rows)
    assert not any(A.RACE_TABLE.match(t) for t in A.tables_used()), "race or ethnicity table used"
    vm.to_csv(MAP_CSV, index=False, lineterminator="\n")
    print(f"variable map: {len(vm)} variables ({len(A.VARIABLES)} ACS, {len(A.BUILT)} built) -> {MAP_CSV.name}")
    # 2. tract values per release and state
    tract_parts, problems, nmissing = {}, [], {}
    for y, st in needs():
        cells, ncells, titles = (tbsf_cells if y >= 2021 else seq_cells)(y, st)
        problems += check_labels(titles, ncells, f"{A.survey_label(y)} {STATES[st][0]}")
        nmissing[(y, st)] = [t for t in A.tables_used() if t not in ncells]
        shp = tract_shapes(A.tract_vintage(y), st)
        cells = cells.join(shp.set_index("tract")[["ALAND_SQMI"]], how="left")
        tract_parts[(y, st)] = (A.tract_parts(cells, ncells, y), shp)
        print(f"  {A.survey_label(y)} {STATES[st][0]}: {len(cells):,} tracts, {len(ncells)} of {len(A.tables_used())} tables"
              + (f"; not in release: {nmissing[(y, st)]}" if nmissing[(y, st)] else ""), flush=True)
    if problems:
        raise SystemExit("label checks failed:\n" + "\n".join(problems))
    # 3. unit values (treatment lots by representative point, as in the trait test)
    out = []
    for city in T.WIDE_CITY_ORDER:
        cu = u[u["city"] == city]
        if cu.empty:
            continue
        key = CITY_KEY[city]
        if city == "Toronto" or not (R.OUT / f"units_{key}.pkl").exists():
            for r in cu.itertuples():
                out.append({"unit_id": r.unit_id, "city": city, "acs_survey": "none (Canada)" if city == "Toronto" else "none", "tract_boundaries": ""})
            continue
        frames = [f for f in R.load_city(key)["frames"] if len(f) and f["unit_id"].iloc[0] in set(cu["unit_id"])]
        F = gpd.GeoDataFrame(pd.concat([f.to_crs(frames[0].crs) for f in frames], ignore_index=True), geometry="geometry", crs=frames[0].crs)
        for r in cu.itertuples():
            y, st = int(r.end_year), r.state
            parts, shp = tract_parts[(y, st)]
            g = F[F["unit_id"] == r.unit_id]
            pts = gpd.GeoDataFrame({"acres": g["acres"].values}, geometry=g.geometry.representative_point().values, crs=F.crs)
            j = gpd.sjoin(pts, shp[["tract", "geometry"]].to_crs(F.crs), how="left", predicate="within")
            j = j[~j.index.duplicated()]
            vals = A.unit_values(j[["tract", "acres"]], parts)
            out.append({"unit_id": r.unit_id, "city": city, "acs_survey": A.survey_label(y),
                        "tract_boundaries": A.tract_vintage(y), "tracts": int(j["tract"].nunique()), **vals.to_dict()})
    V = pd.DataFrame(out).merge(built_traits(u), on=["unit_id", "city"], how="left")
    V = V[["unit_id", "city", "acs_survey", "tract_boundaries", "tracts"] + A.ACS_IDS + list(A.BUILT)]
    assert not T.check_private(V, allowed={"t02_lot_size"})
    V.round(5).to_csv(VALUES_CSV, index=False, lineterminator="\n")
    print(f"values: {len(V)} units -> {VALUES_CSV.name}")
    print(V.groupby("city", sort=False)["acs_survey"].agg(lambda s: ", ".join(sorted(set(s)))).to_string())
    miss = V[A.ALL_IDS].isna().sum()
    print("missing values by variable (non-zero):", miss[miss > 0].to_dict())
    return V


# =========================================================================== fit

def model_frame() -> tuple[pd.DataFrame, list[str]]:
    import run_tod_traits as R
    d = R.wide_frame()
    V = pd.read_csv(VALUES_CSV)
    X = A.entered(V.set_index("unit_id"))
    X.columns = [f"v_{c}" for c in X.columns]
    d = d.merge(X, left_on="unit_id", right_index=True, how="left")
    return d, list(X.columns)


def model_row(model: str, e: pd.DataFrame, n: int, extra: str = "") -> dict:
    import run_tod_traits as R
    j = T.judge_tools(e) if model != "baseline" else {}
    f = e[e["role"] == "fold"]
    row = {"model": A.MODELS[model], "verdict": j.get("verdict", "baseline"), "units_used": n,
           "fold_cities_better": j.get("fold_cities_better", np.nan), "fold_cities": int(len(f)), "fold_cities_needed": j.get("fold_cities_needed", np.nan),
           "mean_error_baseline": float(f["error_baseline"].mean()), "mean_error_model": float(f["error_model"].mean()),
           "beats_baseline_chicago": j.get("beats_baseline_chicago", np.nan), "beats_baseline_madison": j.get("beats_baseline_madison", np.nan)}
    for c in T.WIDE_CITY_ORDER:
        r = e[e["city"] == c]
        row[f"err_base_{R.slug(c)}"] = float(r["error_baseline"].iloc[0]) if len(r) else np.nan
        row[f"err_model_{R.slug(c)}"] = float(r["error_model"].iloc[0]) if len(r) else np.nan
    row["fold_notes"] = "; ".join(f"{r.city}: {r.note}" for r in e.itertuples() if r.note)
    row["detail"] = extra
    return row


def importance(model: str, d: pd.DataFrame, cols: list[str], top: int = 15) -> str:
    fit = d[d["city"].isin(T.WIDE_FIT_CITIES)]
    _, info = A.predict(model, fit, fit.head(1), cols)
    imp = info.get("_importance") or {k: abs(v) for k, v in info.get("_coef", {}).items()}
    if not imp:
        return "importance not available for this model"
    s = pd.Series(imp).sort_values(ascending=False)
    s = s[s > 0].head(top)
    return "fitted on all six: " + "; ".join(f"{k[2:]} {v:.3g}" for k, v in s.items())


def stage_fit() -> None:
    d, cols = model_frame()
    print(f"{len(d)} units, {len(cols)} variables")
    rows, errs = [], []
    for model in A.MODELS:
        print("==", model, flush=True)
        e = A.heldout(d, model, [] if model == "baseline" else cols)
        row = model_row(model, e, len(d))
        if model != "baseline":
            if row["verdict"] == "pass":
                rb = A.robustness(d, model, cols)
                row.update({f"robust_{k}": v for k, v in rb.items()})
                row["verdict"] = "pass" if rb["label"] == "robust pass" else "pass, not robust"
                row["detail"] = importance(model, d, cols) + ". Warning: the best of 5 models looks better than it is."
            else:
                row["robust_label"] = "not run: the model fails the main rule (checks apply only to a pass, plan section 6)"
                row["detail"] = "variable importance not shown: the model does not pass (plan section 4)"
        rows.append(row)
        errs.append(e.assign(model=model))
    R_ = pd.DataFrame(rows)
    assert not T.check_private(R_)
    R_.round(4).to_csv(MODELS_CSV, index=False, lineterminator="\n")
    E = pd.concat(errs, ignore_index=True)
    import run_tod_traits as R
    (R.OUT / ERRORS_PKL).write_bytes(__import__("pickle").dumps(E))
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 120)
    print(R_[["model", "verdict", "fold_cities_better", "mean_error_baseline", "mean_error_model", "err_base_chicago", "err_model_chicago",
              "err_base_madison", "err_model_madison"]].round(3).to_string(index=False))
    print(E[["model", "city", "error_baseline", "error_model", "measured_mean", "predicted_mean_model", "note"]].round(3).to_string(index=False))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=["fetch", "values", "fit"], required=True)
    a = ap.parse_args(argv)
    {"fetch": stage_fetch, "values": stage_values, "fit": stage_fit}[a.stage]()


if __name__ == "__main__":
    main()

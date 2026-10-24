"""Source register and keyless downloader for the California comparison data.

Every file is fetched over plain HTTPS from a public, keyless URL into
data/raw/<source_id>/ and recorded (URL, final URL, bytes, SHA-256, access
date) in data/raw/<source_id>/_downloads.json. Files already present are
reused unless force=True, so a rebuild is reproducible from the recorded
checksums. See docs/gate2/CA_COMPARISON_DATA.md.

The ACS 2020-2024 B25024 national summary file is shared with the Wisconsin
foundation (source id census_acs5_2024_tbsf, missing_middleware.foundation.sources).
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from missing_middleware.foundation import sources as fsources
from missing_middleware.foundation.sources import sha256
from missing_middleware.paths import raw_dir

UA = "missing-middleware-ca-comparison/0.1 (housing research; keyless public files)"

CKAN = "https://data.ca.gov/api/3/action"
APR_PACKAGE = "housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year"
APR_A2_RESOURCE = "fe505d9b-8c36-42ba-ba30-08bc4f34e022"
APR_A2_DICT_RESOURCE = "354a375a-821d-4d4e-97ab-4d79c2925fce"

COMPILATION_SHEET_ID = "10rb8p7DU379vQw9oeS_Z9dwK9F9c5ZBeTw09wQlvwQY"
COMPILATION_EXPORT = f"https://docs.google.com/spreadsheets/d/{COMPILATION_SHEET_ID}/export?format=csv&gid=0"
COMPILATION_LOCAL_FALLBACK = Path(
    "/Users/mroconnell/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/"
    "california-adu-permits-2012-2019.csv"
)

TIGER_CA_PLACE = "https://www2.census.gov/geo/tiger/TIGER2024/PLACE/tl_2024_06_place.zip"
PEP = "https://www2.census.gov/programs-surveys/popest"


@dataclass(frozen=True)
class Source:
    source_id: str
    publisher: str
    title: str
    vintage: str
    license: str
    landing: str
    files: tuple[tuple[str, str], ...]  # (local filename, url)


SOURCES: dict[str, Source] = {
    s.source_id: s
    for s in (
        Source(
            "hcd_apr_a2",
            "California Department of Housing and Community Development (HCD)",
            "Housing Element Annual Progress Report (APR) Table A2: housing development applications "
            "entitled, permitted and completed, project level",
            "Reporting years 2018-2025 (resource last modified on data.ca.gov 2026-10-23)",
            "data.ca.gov dataset license field: 'License not specified'; published as California open "
            "data (data.ca.gov terms of use). Record-level file contains project addresses/APNs; kept "
            "in data/raw only.",
            f"https://data.ca.gov/dataset/{APR_PACKAGE}",
            (
                ("tablea2.csv", f"{CKAN}/resource_show?id={APR_A2_RESOURCE}"),
                ("tablea2_datadictionary.docx", f"{CKAN}/resource_show?id={APR_A2_DICT_RESOURCE}"),
            ),
        ),
        Source(
            "buildinganadu_ca_2012_2019",
            "BuildinganADU.com (compiler); HCD (upstream attribution per compiler)",
            "California ADU Permits by City from 2012-2019 (public Google Sheet, Sheet1)",
            "Compilation of HCD-attributed annual ADU permit counts, 2012-2019 (undated)",
            "No license stated; publicly viewable third-party compilation. Used as descriptive input "
            "with attribution (AQ-017).",
            "https://www.buildinganadu.com/california-adu-charts",
            (("california-adu-permits-2012-2019.csv", COMPILATION_EXPORT),),
        ),
        Source(
            "census_tiger_2024_ca_place",
            "U.S. Census Bureau",
            "TIGER/Line 2024 places, California (attributes used: GEOID, NAME, CLASSFP, FUNCSTAT)",
            "TIGER/Line 2024 (boundaries as of 2024-01-01)",
            fsources.PUBLIC_DOMAIN,
            "https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html",
            (("tl_2024_06_place.zip", TIGER_CA_PLACE),),
        ),
        Source(
            "census_pep_hu_states",
            "U.S. Census Bureau",
            "Population Estimates Program housing-unit estimates, California and Wisconsin (state and "
            "county rows): Vintage 2020 (July 1, 2010-2020) and Vintage 2025 (July 1, 2020-2025)",
            "Vintage 2020 (HU-EST2020) and Vintage 2025 (CO-EST2025-HU)",
            fsources.PUBLIC_DOMAIN,
            "https://www.census.gov/programs-surveys/popest/data/data-sets.html",
            (
                ("HU-EST2020_06.csv", f"{PEP}/datasets/2010-2020/housing/HU-EST2020_6.csv"),
                ("HU-EST2020_55.csv", f"{PEP}/datasets/2010-2020/housing/HU-EST2020_55.csv"),
                ("CO-EST2025-HU-06.xlsx", f"{PEP}/tables/2020-2025/housing/totals/CO-EST2025-HU-06.xlsx"),
                ("CO-EST2025-HU-55.xlsx", f"{PEP}/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx"),
            ),
        ),
    )
}


def _manifest_path(source_id: str) -> Path:
    return raw_dir(source_id) / "_downloads.json"


def load_manifest(source_id: str) -> dict:
    p = _manifest_path(source_id)
    return json.loads(p.read_text()) if p.exists() else {}


def _resolve(url: str) -> str:
    """CKAN resource_show URLs resolve to the resource's download URL."""
    if "/api/3/action/resource_show" not in url:
        return url
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["result"]["url"]


def _download(url: str, dest: Path) -> str:
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=1800) as resp, open(tmp, "wb") as f:
        shutil.copyfileobj(resp, f, length=1 << 20)
        final = resp.geturl()
    tmp.replace(dest)
    return final


def fetch(source_id: str, force: bool = False, log=print) -> dict[str, Path]:
    src = SOURCES[source_id]
    folder = raw_dir(source_id)
    manifest = load_manifest(source_id)
    out: dict[str, Path] = {}
    for name, url in src.files:
        dest = folder / name
        if force or not dest.exists():
            entry = {"url": url, "accessed": dt.date.today().isoformat()}
            try:
                resolved = _resolve(url)
                entry["download_url"] = resolved.split("?")[0]
                log(f"  fetch {resolved.split('?')[0]}")
                _download(resolved, dest)
                entry["method"] = "keyless HTTPS download"
            except Exception as exc:  # noqa: BLE001 - fall back only where a local copy is registered
                if source_id == "buildinganadu_ca_2012_2019" and COMPILATION_LOCAL_FALLBACK.exists():
                    log(f"  export unreachable ({exc}); copying local copy {COMPILATION_LOCAL_FALLBACK}")
                    shutil.copyfile(COMPILATION_LOCAL_FALLBACK, dest)
                    meta = COMPILATION_LOCAL_FALLBACK.with_name("california-adu-permits-2012-2019.meta.json")
                    if meta.exists():
                        shutil.copyfile(meta, folder / meta.name)
                    entry["method"] = f"local copy of team retrieval: {COMPILATION_LOCAL_FALLBACK}"
                else:
                    raise
            entry.update(bytes=dest.stat().st_size, sha256=sha256(dest))
            manifest[name] = entry
        elif name not in manifest:
            manifest[name] = {
                "url": url, "bytes": dest.stat().st_size, "sha256": sha256(dest),
                "accessed": dt.date.fromtimestamp(dest.stat().st_mtime).isoformat(),
                "method": "file present before manifest was written",
            }
        out[name] = dest
    _manifest_path(source_id).write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return out


def fetch_all(force: bool = False, log=print) -> dict[str, dict[str, Path]]:
    out = {sid: fetch(sid, force=force, log=log) for sid in SOURCES}
    out["census_acs5_2024_tbsf"] = {"acsdt5y2024-b25024.dat": shared_acs_b25024()}
    return out


def shared_acs_b25024() -> Path:
    """The ACS B25024 national file is owned by the Wisconsin foundation build (read only here).

    Verifies the file against the foundation manifest checksum instead of re-downloading it.
    """
    path = raw_dir("census_acs5_2024_tbsf") / "acsdt5y2024-b25024.dat"
    m = fsources.load_manifest("census_acs5_2024_tbsf").get(path.name)
    if not path.exists():
        raise FileNotFoundError(f"{path} missing: run scripts/build_foundation.py first")
    if m and m.get("sha256") != sha256(path):
        raise ValueError(f"{path} does not match the foundation manifest checksum")
    return path


def register_rows() -> list[dict]:
    rows = []
    for sid, src in SOURCES.items():
        man = load_manifest(sid)
        for name, url in src.files:
            m = man.get(name, {})
            rows.append({"source_id": sid, "publisher": src.publisher, "title": src.title,
                         "vintage": src.vintage, "license": src.license, "landing": src.landing,
                         "file": name, "url": m.get("download_url", url), "bytes": m.get("bytes"),
                         "sha256": m.get("sha256"), "accessed": m.get("accessed"),
                         "method": m.get("method")})
    fman = fsources.load_manifest("census_acs5_2024_tbsf")
    m = fman.get("acsdt5y2024-b25024.dat", {})
    src = fsources.SOURCES["census_acs5_2024_tbsf"]
    rows.append({"source_id": "census_acs5_2024_tbsf", "publisher": src.publisher, "title": src.title,
                 "vintage": src.vintage, "license": src.license,
                 "landing": "https://www.census.gov/programs-surveys/acs/data/summary-file.html",
                 "file": "acsdt5y2024-b25024.dat", "url": m.get("url"), "bytes": m.get("bytes"),
                 "sha256": m.get("sha256"), "accessed": m.get("accessed"),
                 "method": "keyless HTTPS bulk download (shared with Wisconsin foundation)"})
    return rows


# ---------------------------------------------------------------------------
# CKAN datastore SQL queries (small aggregates; saved verbatim with checksums)
# ---------------------------------------------------------------------------

APR_TABLE_A_RESOURCE = "c78b769d-cc02-4050-91ef-79ded665b5a8"
APR_TABLE_D_RESOURCE = "37724925-2014-4646-ade8-3ba9f3ff9fb8"

API_QUERIES = {
    # Filing evidence: a jurisdiction-year with rows in Table A (applications) or
    # Table D (program implementation) filed an APR even if it had no Table A2 activity.
    "table_a_juris_years.json": f'SELECT "JURIS_NAME", "YEAR", COUNT(*) AS n FROM "{APR_TABLE_A_RESOURCE}" GROUP BY 1, 2',
    "table_d_juris_years.json": f'SELECT "JURIS_NAME", "YEAR", COUNT(*) AS n FROM "{APR_TABLE_D_RESOURCE}" GROUP BY 1, 2',
    # Cross-check of the downloaded A2 CSV against the live datastore.
    "table_a2_year_unitcat.json": (f'SELECT "YEAR", "UNIT_CAT", COUNT(*) AS n, SUM("NO_BUILDING_PERMITS"::numeric) AS bp '
                                   f'FROM "{APR_A2_RESOURCE}" GROUP BY 1, 2'),
}


def fetch_api_queries(force: bool = False, log=print) -> dict[str, Path]:
    import urllib.parse

    folder = raw_dir("hcd_apr_a2") / "api"
    folder.mkdir(exist_ok=True)
    manifest = load_manifest("hcd_apr_a2")
    out = {}
    for name, sql in API_QUERIES.items():
        dest = folder / name
        if force or not dest.exists():
            url = f"{CKAN}/datastore_search_sql?" + urllib.parse.urlencode({"sql": sql})
            log(f"  query {name}")
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=600) as r:
                body = r.read()
            if not json.loads(body).get("success"):
                raise RuntimeError(f"CKAN query failed: {name}")
            dest.write_bytes(body)
            manifest[f"api/{name}"] = {"url": f"{CKAN}/datastore_search_sql", "sql": sql,
                                       "accessed": dt.date.today().isoformat(), "bytes": dest.stat().st_size,
                                       "sha256": sha256(dest), "method": "CKAN datastore_search_sql (keyless)"}
        out[name] = dest
    _manifest_path("hcd_apr_a2").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return out


def read_api_records(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text())["result"]["records"]

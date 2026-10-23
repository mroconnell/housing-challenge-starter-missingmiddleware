"""Source register and keyless downloader for the Wisconsin statewide foundation.

Every file is fetched from a public, keyless Census Bureau URL into
data/raw/<source_id>/ and recorded (URL, bytes, SHA-256, access date) in
data/raw/<source_id>/_downloads.json. Re-running skips files already present
unless `force=True`, so a build is reproducible from the recorded checksums.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from missing_middleware.paths import raw_dir

UA = "missing-middleware-foundation/0.1 (Wisconsin housing research; keyless bulk files)"

BPS_YEARS = tuple(range(2015, 2026))  # 2015..2025 annual files
ACS_TABLES = ("b25024", "b25002", "b25034", "b01003")

ACS_SF = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData"
TIGER = "https://www2.census.gov/geo/tiger/TIGER2024"
BPS = "https://www2.census.gov/econ/bps"


@dataclass(frozen=True)
class Source:
    source_id: str
    publisher: str
    title: str
    vintage: str
    license: str
    files: tuple[tuple[str, str], ...]  # (local filename, url)


PUBLIC_DOMAIN = "U.S. Government work, public domain (17 U.S.C. 105); Census Bureau terms of service"

SOURCES: dict[str, Source] = {
    s.source_id: s
    for s in (
        Source(
            "census_acs5_2024_tbsf",
            "U.S. Census Bureau",
            "ACS 2020-2024 5-year table-based summary file (detailed tables)",
            "ACS 2020-2024 5-year (released 2025-12)",
            PUBLIC_DOMAIN,
            tuple((f"acsdt5y2024-{t}.dat", f"{ACS_SF}/acsdt5y2024-{t}.dat") for t in ACS_TABLES),
        ),
        Source(
            "census_tiger_2024",
            "U.S. Census Bureau",
            "TIGER/Line Shapefiles 2024 (state, county, county subdivision, place, tract, block group)",
            "TIGER/Line 2024 (boundaries as of 2024-01-01; 2020 tracts and block groups)",
            PUBLIC_DOMAIN,
            (
                ("tl_2024_us_state.zip", f"{TIGER}/STATE/tl_2024_us_state.zip"),
                ("tl_2024_us_county.zip", f"{TIGER}/COUNTY/tl_2024_us_county.zip"),
                ("tl_2024_55_cousub.zip", f"{TIGER}/COUSUB/tl_2024_55_cousub.zip"),
                ("tl_2024_55_place.zip", f"{TIGER}/PLACE/tl_2024_55_place.zip"),
                ("tl_2024_55_tract.zip", f"{TIGER}/TRACT/tl_2024_55_tract.zip"),
                ("tl_2024_55_bg.zip", f"{TIGER}/BG/tl_2024_55_bg.zip"),
            ),
        ),
        Source(
            "census_cbsa_cb_2024",
            "U.S. Census Bureau",
            "Cartographic boundary file, core-based statistical areas 2024 (1:20m) - used for metro/micro type only",
            "2024 (July 2023 OMB delineations)",
            PUBLIC_DOMAIN,
            (("cb_2024_us_cbsa_20m.zip", "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_cbsa_20m.zip"),),
        ),
        Source(
            "census_bps_state",
            "U.S. Census Bureau",
            "Building Permits Survey, annual state files",
            "Annual 2015-2025 (2025 final)",
            PUBLIC_DOMAIN,
            tuple((f"st{y}a.txt", f"{BPS}/State/st{y}a.txt") for y in BPS_YEARS),
        ),
        Source(
            "census_bps_county",
            "U.S. Census Bureau",
            "Building Permits Survey, annual county files",
            "Annual 2015-2025 (2025 final)",
            PUBLIC_DOMAIN,
            tuple((f"co{y}a.txt", f"{BPS}/County/co{y}a.txt") for y in BPS_YEARS),
        ),
        Source(
            "census_bps_place",
            "U.S. Census Bureau",
            "Building Permits Survey, annual permit-issuing place files, Midwest region",
            "Annual 2015-2025 (2025 final)",
            PUBLIC_DOMAIN,
            tuple((f"mw{y}a.txt", f"{BPS}/Place/Midwest%20Region/mw{y}a.txt") for y in BPS_YEARS),
        ),
        Source(
            "census_pep_v2025_hu",
            "U.S. Census Bureau",
            "Annual estimates of housing units for counties in Wisconsin (CO-EST2025-HU-55)",
            "Vintage 2025 (July 1, 2020-2025)",
            PUBLIC_DOMAIN,
            (
                (
                    "CO-EST2025-HU-55.xlsx",
                    "https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx",
                ),
            ),
        ),
    )
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest_path(source_id: str) -> Path:
    return raw_dir(source_id) / "_downloads.json"


def load_manifest(source_id: str) -> dict:
    p = _manifest_path(source_id)
    return json.loads(p.read_text()) if p.exists() else {}


def fetch(source_id: str, force: bool = False, log=print) -> dict[str, Path]:
    """Download every file of a source (skipping files already present)."""
    src = SOURCES[source_id]
    folder = raw_dir(source_id)
    manifest = load_manifest(source_id)
    out: dict[str, Path] = {}
    for name, url in src.files:
        dest = folder / name
        if force or not dest.exists():
            log(f"  fetch {url}")
            tmp = dest.with_suffix(dest.suffix + ".part")
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=600) as resp, open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f)
            tmp.replace(dest)
            manifest[name] = {
                "url": url,
                "bytes": dest.stat().st_size,
                "sha256": sha256(dest),
                "accessed": dt.date.today().isoformat(),
            }
        elif name not in manifest:
            manifest[name] = {
                "url": url,
                "bytes": dest.stat().st_size,
                "sha256": sha256(dest),
                "accessed": dt.date.fromtimestamp(dest.stat().st_mtime).isoformat(),
            }
        out[name] = dest
    _manifest_path(source_id).write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return out


def fetch_all(force: bool = False, log=print) -> dict[str, dict[str, Path]]:
    return {sid: fetch(sid, force=force, log=log) for sid in SOURCES}


def register_rows() -> list[dict]:
    """One row per downloaded file, for the source register / docs."""
    rows = []
    for sid, src in SOURCES.items():
        man = load_manifest(sid)
        for name, url in src.files:
            m = man.get(name, {})
            rows.append(
                {
                    "source_id": sid,
                    "publisher": src.publisher,
                    "title": src.title,
                    "vintage": src.vintage,
                    "license": src.license,
                    "file": name,
                    "url": url,
                    "bytes": m.get("bytes"),
                    "sha256": m.get("sha256"),
                    "accessed": m.get("accessed"),
                    "access_method": "keyless HTTPS bulk download",
                }
            )
    return rows

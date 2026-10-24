"""California Census Building Permits Survey (BPS), 2010-2025.

ADU-blind new-construction totals for California's state, counties, and
permit-issuing places, parsed with the same reader as the Wisconsin
foundation so the two states are directly comparable. Used with HCD ADU
counts to compute ADU shares of new units before and after each reform
wave (AQ-031); see docs/gate3/CA_COMPARISON_PLAN.md.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import urllib.request
from pathlib import Path

import pandas as pd

from missing_middleware.foundation.parsers import read_bps
from missing_middleware.paths import processed_dir, raw_dir

BPS = "https://www2.census.gov/econ/bps"
YEARS = range(2010, 2026)
CA = "06"
SOURCE_ID = "census_bps_ca"
FILES = {
    "state": lambda y: f"{BPS}/State/st{y}a.txt",
    "county": lambda y: f"{BPS}/County/co{y}a.txt",
    "place": lambda y: f"{BPS}/Place/West%20Region/we{y}a.txt",
}


def fetch(force: bool = False) -> dict:
    out = raw_dir(SOURCE_ID)
    manifest = {"source_id": SOURCE_ID, "publisher": "U.S. Census Bureau",
                "license": "Public domain (U.S. federal government work)", "files": []}
    for kind, url_for in FILES.items():
        for y in YEARS:
            url = url_for(y)
            path = out / f"{kind}_{y}.txt"
            if force or not path.exists():
                with urllib.request.urlopen(url, timeout=120) as r:
                    path.write_bytes(r.read())
            manifest["files"].append({
                "file": path.name, "url": url,
                "accessed": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def build() -> dict[str, pd.DataFrame]:
    src = raw_dir(SOURCE_ID)
    tables = {}
    for kind in FILES:
        frames = [read_bps(src / f"{kind}_{y}.txt", kind, state_fips=CA) for y in YEARS]
        tables[kind] = pd.concat(frames, ignore_index=True)
    out = processed_dir("comparison_ca")
    for kind, df in tables.items():
        df.to_parquet(out / f"bps_ca_{kind}_annual.parquet", index=False)
    return tables


def checks(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Integrity checks: state equals sum of counties each year (by construction in BPS)."""
    st = tables["state"].groupby("year").units_total.sum()
    co = tables["county"].groupby("year").units_total.sum()
    pl = tables["place"].groupby("year").units_total.sum()
    return pd.DataFrame({"state": st, "sum_counties": co, "sum_places": pl,
                         "one_unit_state": tables["state"].groupby("year")["1unit_units"].sum()})

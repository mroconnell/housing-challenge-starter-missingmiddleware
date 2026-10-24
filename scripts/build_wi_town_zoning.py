"""Build the general-zoning status of every Wisconsin town (AQ-026 `no_zoning`).

    uv run python scripts/build_wi_town_zoning.py           # uses the cached DOA workbook
    uv run python scripts/build_wi_town_zoning.py --fetch   # download it first (Wayback copy)

Inputs:
    data/raw/wi_doa_land_regs_inventory/inv_wayback.xlsx  DOA Comp Plan and Land Regs Inventory
        (https://doa.wi.gov/DIR/Comp-Plan-and-Land-Regs-Inventory.xlsx; doa.wi.gov times out from
        this network, so the Internet Archive capture of 2025-02-15 is used; workbook modified 2025-01-30)
    data/processed/foundation/{areas,inventory}.parquet
Outputs:
    reference/wi_town_zoning_status.csv     one row per town (1,243)
    data/raw/wi_doa_land_regs_inventory/SOURCE.json   URL, capture, checksum, access date
Prints counts and one-unit detached homes by status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.foundation import town_zoning as tz  # noqa: E402

RAW = ROOT / "data/raw/wi_doa_land_regs_inventory"
XLSX = RAW / "inv_wayback.xlsx"
OUT = ROOT / "reference/wi_town_zoning_status.csv"


def fetch() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(tz.DOA_WAYBACK_URL, headers={"User-Agent": "missingmiddleware-research"})
    with urllib.request.urlopen(req, timeout=120) as r:
        XLSX.write_bytes(r.read())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    if a.fetch or not XLSX.exists():
        fetch()
    sha = hashlib.sha256(XLSX.read_bytes()).hexdigest()
    (RAW / "SOURCE.json").write_text(json.dumps({
        "source_id": "wi_doa_land_regs_inventory", "url": tz.DOA_URL, "retrieved_from": tz.DOA_WAYBACK_URL,
        "capture": "2025-02-15T16:14:15Z", "workbook_modified": tz.DOA_DATE, "accessed": date.today().isoformat(),
        "sha256": sha, "license": "Wisconsin state government public record (no license stated)"}, indent=2))

    inv = tz.read_doa_inventory(XLSX)
    areas = pd.read_parquet(ROOT / "data/processed/foundation/areas.parquet")
    towns = areas[(areas["level"] == "municipality") & (areas["muni_type"] == "town")]
    status = tz.classify_towns(inv, towns)
    status.to_csv(OUT, index=False)

    homes = pd.read_parquet(ROOT / "data/processed/foundation/inventory.parquet")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(status)} towns; sha256(xlsx)={sha[:12]}")
    print(tz.summarize(status, homes).to_string(index=False))
    print(pd.crosstab(status["zoning_status"], status["verification"]).to_string())
    c = tz.county_status(inv)
    print("counties without general zoning (DOA):", ", ".join(sorted(c.loc[c["county_general_zoning"] != "county", "county"])))
    h = status.merge(homes[["area_id", "homes_1unit_detached"]], on="area_id")
    print("unzoned towns by county (towns, homes):")
    u = h[h["zoning_status"] == "unzoned"].groupby("county_name").agg(n=("geoid", "size"), homes=("homes_1unit_detached", "sum"))
    print(u.sort_values("homes", ascending=False).to_string())
    print("largest unzoned towns:")
    print(h[h["zoning_status"] == "unzoned"].nlargest(10, "homes_1unit_detached")[["name", "county_name", "homes_1unit_detached"]].to_string(index=False))
    print("unknown:", h[h["zoning_status"] == "unknown"][["name", "county_name", "homes_1unit_detached"]].to_string(index=False))


if __name__ == "__main__":
    main()

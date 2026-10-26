"""Fetch the Parking Reform Network reform-map data (pinned commit) and classify every US
reform record against the parking benchmark.

    uv run python scripts/build_parking_taxonomy.py [--fetch] [--commit SHA]

Raw: data/raw/prn_reform_map/{core,extended,option-values}.json + _downloads.json (git-ignored)
Out: reference/parking_reform_taxonomy.csv (all US records),
     reference/parking_reform_cases.csv (cities rated at/near the benchmark, adopted)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.parking import taxonomy  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

REPO = "ParkingReformNetwork/reform-map"
DEFAULT_COMMIT = "3a622311f83cc3ec566cb64f8f0e9d72d241b297"   # main on 2026-10-26
FILES = ("core.json", "extended.json", "option-values.json")
D = RAW / "prn_reform_map"


def fetch(commit: str) -> None:
    D.mkdir(parents=True, exist_ok=True)
    log = {}
    for f in FILES:
        url = f"https://raw.githubusercontent.com/{REPO}/{commit}/data/{f}"
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "missing-middleware research"}),
                                      timeout=120).read()
        (D / f).write_bytes(data)
        log[f] = {"accessed": dt.date.today().isoformat(), "bytes": len(data),
                  "sha256": hashlib.sha256(data).hexdigest(), "url": url, "licence": "MIT (repository LICENSE)"}
    (D / "_downloads.json").write_text(json.dumps(log, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--commit", default=DEFAULT_COMMIT)
    a = ap.parse_args()
    if a.fetch or not (D / "_downloads.json").exists():
        fetch(a.commit)
    core = json.loads((D / "core.json").read_text())
    ext = json.loads((D / "extended.json").read_text())
    df = taxonomy.classify(core, ext)
    df.to_csv(REFERENCE / "parking_reform_taxonomy.csv", index=False)
    cases = df[(df["place_type"] == "city") & (df["status"] == "adopted") & df["benchmark_rating"].isin(["at", "near"])
               & (df["policy"] == "rm_min")]
    cases = cases.drop(columns=["summary", "citation_urls"]).sort_values("population", ascending=False)
    cases.to_csv(REFERENCE / "parking_reform_cases.csv", index=False)
    print(df.groupby(["place_type", "benchmark_rating"]).size().to_string())
    print(f"{len(cases)} city records at/near the benchmark")


if __name__ == "__main__":
    main()

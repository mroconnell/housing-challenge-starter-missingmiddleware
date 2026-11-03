"""Download project-level data for test F1 (first stage) of docs/parking/CAUSAL_FRAMEWORK_PLAN.md.

    uv run python scripts/fetch_parking_first_stage.py [--refresh]

Raw (git-ignored): data/raw/parking_first_stage/, manifest in _downloads.json.
- mpls_planning_commission_schieferdecker.xlsx: Minneapolis Planning Commission approvals 2011-2025, one row per
  project (date, homes, car spaces, bike spaces, downtown flag, ward). Compiled by hand by Alex Schieferdecker from
  Planning Commission agendas; shared publicly on Google Drive from his 2021 streets.mn post. No licence stated.
  Third-party compilation, not a City of Minneapolis file.
- seattle_land_use_permits.csv: City of Seattle SDCI Land Use Permits (data.seattle.gov ht3q-kdvx), Public Domain.
  Parking appears only inside the free-text Description ("Parking for N vehicles proposed").
- buffalo_hess_rehler_2021_minus_minimums.pdf: Hess and Rehler (2021), JAPA 87(3), CC BY-NC-ND 4.0. Copy from the
  City of Mercer Island public record (the publisher site refuses automated downloads). The per-project Table A-2 is
  in the online supplement, which is not included here.

Not automated: the Metro Transit "Minneapolis Residential Development Trends" PDF (metrotransit.org refuses
automated downloads).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data" / "raw" / "parking_first_stage"
MAN = D / "_downloads.json"

SOURCES = {
    "mpls_planning_commission_schieferdecker.xlsx": dict(
        url="https://drive.google.com/uc?export=download&id=1rW4dsNhgJMhSZP8H0Q50tylKqsZWkJdV",
        page="https://drive.google.com/file/d/1rW4dsNhgJMhSZP8H0Q50tylKqsZWkJdV/view",
        cited_by="https://streets.mn/2021/02/23/5-takeaways-from-10-years-of-minneapolis-planning-commission-approvals/",
        publisher="Alex Schieferdecker (private compiler), from City of Minneapolis Planning Commission agendas",
        licence="None stated; publicly shared Google Drive file linked from the author's blog. Third-party compilation.",
    ),
    "seattle_land_use_permits.csv": dict(
        url="https://data.seattle.gov/api/views/ht3q-kdvx/rows.csv?accessType=DOWNLOAD",
        page="https://data.seattle.gov/d/ht3q-kdvx",
        publisher="City of Seattle, Seattle Department of Construction and Inspections",
        licence="Public Domain (data.seattle.gov licence field)",
    ),
    "buffalo_hess_rehler_2021_minus_minimums.pdf": dict(
        url="https://permitbulletin.mercerisland.gov/public/2024%20Comp%20Plan%20Periodic%20Review%20Admin%20Record/"
            "Exhibits%20301-350/ex%20316%20minus%20minimums%20development%20response%20to%20the%20removal%20of%20"
            "minimum%20parking%20requirements%20in%20buffalo.pdf",
        doi="10.1080/01944363.2020.1864225",
        publisher="Hess and Rehler (2021), Journal of the American Planning Association; copy in City of Mercer Island record",
        licence="CC BY-NC-ND 4.0 (open access article)",
    ),
}


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=600) as r:
        return r.read()


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    D.mkdir(parents=True, exist_ok=True)
    man = json.loads(MAN.read_text()) if MAN.exists() else {"files": {}}
    for name, meta in SOURCES.items():
        if not a.refresh and (D / name).exists() and name in man["files"]:
            print(f"  {name}: kept")
            continue
        data = get(meta["url"])
        if name.endswith(".xlsx") and not data.startswith(b"PK"):
            sys.exit(f"{name}: not an xlsx (Google Drive may have returned a warning page)")
        if name.endswith(".pdf") and not data.startswith(b"%PDF"):
            sys.exit(f"{name}: not a PDF")
        (D / name).write_bytes(data)
        man["files"][name] = {**meta, "accessed_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                              "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        print(f"  {name}: {len(data):,} bytes")
    man["not_fetched"] = {
        "metrotransit_mpls_development_trends.pdf": "https://www.metrotransit.org/media/xunki3z0/minneapolis_development_trends_final.pdf "
            "(HTTP 403 to scripts; aggregate trends 2014-2018 only, no per-project table expected)",
        "buffalo_hess_rehler_2021_supplement": "Technical Appendix Tables A-1..A-3 on tandfonline.com (HTTP 403 to scripts)",
    }
    MAN.write_text(json.dumps(man, indent=1) + "\n")


if __name__ == "__main__":
    main()

"""CA AB 2097 study, step 1a (part 2): which California agencies' 2022 bus schedule files were saved by the web
archive. Metadata only: counts of saved copies; no schedule file is downloaded.

Plan: docs/parking/CA_AB2097_PLAN.md, choice 3 (free public archives first; Ryan's pick on 2026-11-05: web-archive
copies of each agency's schedule file, the Mobility Database as backup for gaps).

Steps
1. Read the Mobility Database public catalog (feeds_v2.csv; read only, not stored in git) and keep California GTFS
   schedule feeds: provider, feed id, and the agency's own download URL (urls.direct_download).
2. For each agency URL, ask the web archive's capture index (CDX) for saved copies with HTTP 200 between
   2022-09-01 and 2022-12-31 (the window for the late-2022 map), and, separately, 2022-01-01 to 2023-06-30.
3. Write reference/ca_ab2097_gtfs_archive_coverage.csv: provider, feed id, URL, number of captures in each window,
   the capture nearest to 2022-11-15, and status. A summary line counts agencies with at least one late-2022 copy.

Every request sends "missing-middleware-research/1.0 (public data)". Two seconds between archive requests. A refused
or rate-limited request is recorded and not retried with other headers.

    uv run python scripts/ca_ab2097_step1a_gtfs_archive.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import REFERENCE  # noqa: E402

UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
CATALOG = "https://files.mobilitydatabase.org/feeds_v2.csv"
OUT = REFERENCE / "ca_ab2097_gtfs_archive_coverage.csv"
LATE = ("20220901", "20221231")
WIDE = ("20220101", "20230630")
TARGET = "20221115"


def get(url: str, timeout: int = 90) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, b""


def captures(url: str, start: str, end: str) -> tuple[int, list[str]]:
    q = urllib.parse.urlencode({"url": url, "from": start, "to": end, "output": "json",
                                "fl": "timestamp", "filter": "statuscode:200"})
    status, body = get(f"https://web.archive.org/cdx/search/cdx?{q}")
    if status != 200:
        return status, []
    try:
        rows = json.loads(body or b"[]")[1:]
    except json.JSONDecodeError:
        return -1, []
    return status, sorted(r[0] for r in rows)


def main() -> None:
    status, body = get(CATALOG, timeout=120)
    if status != 200:
        raise SystemExit(f"catalog not available (HTTP {status})")
    rd = csv.DictReader(io.StringIO(body.decode("utf-8", "replace")))
    need = {"id", "data_type", "location.country_code", "location.subdivision_name", "urls.direct_download", "provider"}
    if not need <= set(rd.fieldnames or []):
        raise SystemExit("expected catalog columns not found; header: " + ",".join(rd.fieldnames or []))
    feeds = [r for r in rd if r["data_type"] == "gtfs" and r["location.country_code"] == "US"
             and (r["location.subdivision_name"] or "").strip() == "California" and r["urls.direct_download"]]
    seen, rows = set(), []
    for r in feeds:
        u = r["urls.direct_download"].strip()
        if u in seen:
            continue
        seen.add(u)
        s1, late = captures(u, *LATE)
        time.sleep(2)
        s2, wide = captures(u, *WIDE)
        time.sleep(2)
        nearest = min(wide, key=lambda t: abs(int(t[:8]) - int(TARGET))) if wide else ""
        rows.append({"provider": r["provider"], "mdb_id": r["id"], "url": u,
                     "captures_2022_09_to_12": len(late), "captures_2022_01_to_2023_06": len(wide),
                     "nearest_to_2022_11_15": nearest[:8], "status": f"{s1}/{s2}"})
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["provider"])
        w.writeheader()
        w.writerows(rows)
    n_late = sum(1 for r in rows if r["captures_2022_09_to_12"] > 0)
    n_wide = sum(1 for r in rows if r["captures_2022_01_to_2023_06"] > 0)
    print(f"California GTFS feeds with an agency URL: {len(rows)}; with a saved copy Sep–Dec 2022: {n_late}; "
          f"Jan 2022–Jun 2023: {n_wide}; refused or failed lookups: {sum(1 for r in rows if r['status'] != '200/200')}")


if __name__ == "__main__":
    main()

"""CA AB 2097 study, step 1a: which sources exist (metadata only).

Plan: docs/parking/CA_AB2097_PLAN.md (section 6, step 1; section 8). Runs only after the plan is locked and the
audit has checked this script.

What it does (no permit data, no geometry, no feature downloads):
1. Web archive: lists dated captures (2022-01-01 to 2024-06-30) of Caltrans' High Quality Transit layers
   (the statewide major-stop map published before the 2024 20-minute change). Counts only; nothing is downloaded.
2. City and regional AB 2097 layers found in the city-lead search (docs/parking/CA_AB2097_CITY_LEADS.md):
   reads each layer's metadata JSON (name, last-edit date, description, licence or terms text). No features.
3. Rail station lists with opening dates: reads the metadata of candidate public layers (BTS NTAD).
4. GTFS archives: records whether the Mobility Database public catalog lists California feeds, reading the
   catalog CSV only (no feed downloads). Cal-ITP and Transitland are recorded as "checked by hand" leads.

Output: reference/ca_ab2097_step1a_sources.csv (source, url, status, dates, licence/terms text, notes).
Every request sends the user agent "missing-middleware-research/1.0 (public data)". A refused request is recorded,
never retried with other headers.

    uv run python scripts/ca_ab2097_step1a_sources.py
"""
from __future__ import annotations

import csv
import datetime as dt
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
OUT = REFERENCE / "ca_ab2097_step1a_sources.csv"
FIELDS = ["group", "source", "url", "status", "first_date", "last_date", "n_captures", "licence_or_terms", "notes"]

# 1. Caltrans HQTA layers (service and open-data download pages) to look up in the web archive.
HQTA_URLS = [
    "https://gis.data.ca.gov/datasets/f6c30480f0e84be699383192c099a6a4_0",  # HQTA Stops (open data page)
    "https://gis.data.ca.gov/datasets/863e61eacbf3463ab239beb3cee4a2c3_0",  # HQTA Areas
    "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Stops/MapServer/0",
    "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Areas/MapServer/0",
    "https://gisdata.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Stops/MapServer/0",
]
ARCHIVE_FROM, ARCHIVE_TO = "20220101", "20240630"

# 2. City and regional layers from the city-lead search (metadata JSON only).
CITY_LAYERS = [
    ("Oakland, Spring 2023 (15-minute rule)",
     "https://gisapps1.mapoakland.com/oakgis/rest/services/Prod/CEDA_App_PRODGIS/MapServer/22"),
    ("Oakland, Fall 2026 (20-minute rule)",
     "https://services.arcgis.com/9tC74aDHuml0x5Yz/arcgis/rest/services/NoParkingMinimumAB2097_Fall26/FeatureServer/0"),
    ("Sacramento, AB 2097 Parking (placebo city)",
     "https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/AB_2097_Parking/FeatureServer/0"),
    ("Truckee, Train Depot half mile",
     "https://services5.arcgis.com/i75zh9vlhYUpqwjr/arcgis/rest/services/TraiinDepot_AB2097/FeatureServer/0"),
]

# 3. Candidate rail-station layers (metadata only). Exact service URLs are confirmed when run; misses are recorded.
RAIL_LAYERS = [
    ("BTS NTAD Amtrak Stations",
     "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_Amtrak_Stations/FeatureServer/0"),
    ("BTS NTAD National Transit Map Stops",
     "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0"),
]

# 4. GTFS archive catalog.
MDB_CATALOG = "https://files.mobilitydatabase.org/feeds_v2.csv"
BY_HAND = [
    ("Cal-ITP GTFS schedule archive", "https://github.com/cal-itp/data-infra",
     "Archive pipeline code is AGPL-3.0 (not used). Public access to archived feeds: checked by hand."),
    ("Transitland feed archive", "https://www.transit.land/",
     "Needs an account and API key: Ryan's call. Not used unless Ryan says so."),
]


def get(url: str, timeout: int = 60) -> tuple[int, bytes]:
    """One GET with the project's user agent. Returns (HTTP status, body); status 0 on network error."""
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, b""


def ms_to_date(ms) -> str:
    if not ms:
        return ""
    return dt.datetime.fromtimestamp(int(ms) / 1000, dt.timezone.utc).date().isoformat()


def archive_captures(url: str) -> dict:
    q = urllib.parse.urlencode({"url": url, "from": ARCHIVE_FROM, "to": ARCHIVE_TO, "output": "json",
                                "fl": "timestamp,statuscode", "filter": "statuscode:200"})
    status, body = get(f"https://web.archive.org/cdx/search/cdx?{q}")
    row = {"group": "1 Caltrans HQTA (web archive)", "source": "web archive captures", "url": url,
           "status": str(status), "licence_or_terms": "", "notes": ""}
    if status != 200:
        row["notes"] = "archive refused or unavailable; recorded, not retried with other headers"
        return row
    rows = json.loads(body or b"[]")[1:]
    stamps = sorted(r[0] for r in rows)
    row.update(n_captures=len(stamps), first_date=stamps[0][:8] if stamps else "", last_date=stamps[-1][:8] if stamps else "")
    return row


def layer_metadata(group: str, name: str, url: str) -> dict:
    status, body = get(url + ("&" if "?" in url else "?") + "f=pjson")
    row = {"group": group, "source": name, "url": url, "status": str(status)}
    if status != 200 or not body:
        row["notes"] = "refused or unavailable; recorded, not retried with other headers"
        return row
    try:
        j = json.loads(body)
    except json.JSONDecodeError:
        row["notes"] = "response was not JSON"
        return row
    if "error" in j:
        row.update(status=f"{status} ({j['error'].get('code', '')})", notes=str(j["error"].get("message", ""))[:200])
        return row
    edit = (j.get("editingInfo") or {}).get("lastEditDate")
    row.update(last_date=ms_to_date(edit), licence_or_terms=(j.get("copyrightText") or "").strip()[:300],
               notes=f"name={j.get('name', '')}; description={(j.get('description') or '').strip()[:200]}")
    return row


def mdb_california() -> dict:
    status, body = get(MDB_CATALOG, timeout=120)
    row = {"group": "4 GTFS archives", "source": "Mobility Database catalog (CSV)", "url": MDB_CATALOG,
           "status": str(status), "licence_or_terms": "catalog: see mobilitydatabase.org; each feed keeps its agency licence"}
    if status != 200:
        row["notes"] = "refused or unavailable"
        return row
    rd = csv.DictReader(io.StringIO(body.decode("utf-8", "replace")))
    ca = [r for r in rd if (r.get("location.country_code") == "US"
                            and (r.get("location.subdivision_name") or "").strip() == "California"
                            and r.get("data_type") == "gtfs")]
    row["notes"] = (f"{len(ca)} California GTFS schedule feeds listed. Dated past versions need the API (account): "
                    "not used without Ryan's OK.")
    return row


def main() -> None:
    rows: list[dict] = []
    for u in HQTA_URLS:
        rows.append(archive_captures(u))
        time.sleep(2)  # be gentle with the archive
    for name, u in CITY_LAYERS:
        rows.append(layer_metadata("2 City and regional AB 2097 layers", name, u))
    for name, u in RAIL_LAYERS:
        rows.append(layer_metadata("3 Rail station lists", name, u))
    rows.append(mdb_california())
    for name, u, note in BY_HAND:
        rows.append({"group": "4 GTFS archives", "source": name, "url": u, "status": "checked by hand", "notes": note})
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    print(f"wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

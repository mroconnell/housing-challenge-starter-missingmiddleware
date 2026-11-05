"""CA AB 2097 study, step 1a (part 3): does the OpenMobilityData (former TransitFeeds) archive, stored publicly by
the Mobility Database, hold dated schedule files from late 2022? Metadata only: object names are listed; no schedule
file is downloaded.

Plan: docs/parking/CA_AB2097_PLAN.md, section 9 (Ryan 2026-11-05 18:13: "yeah, do both" = check this archive, and
add the National Transit Database service check for gap agencies).

Steps
1. List object names in the public bucket `openmobilitydata-data` (region us-west-1) under `public/feeds/`, with the
   S3 ListObjectsV2 API (anonymous, 1,000 names a page, 1 second between pages). Object names look like
   public/feeds/<provider>/<feed id>/<YYYYMMDD>/gtfs.zip.
2. Keep names dated 2022-01-01 to 2023-06-30 and summarise by provider and feed: number of dated copies, and the
   copies nearest to 2022-12-14 on each side.
3. Write reference/ca_ab2097_omd_archive_listing.csv (all providers; California ones are picked by hand from it in
   the step 1 review, with the rule written there) and print counts.

If the listing is refused (for example AccessDenied), that is recorded and the script stops; no other route is tried.
User agent: "missing-middleware-research/1.0 (public data)". The bucket's terms are recorded in the review.

    uv run python scripts/ca_ab2097_step1a_omd_archive.py
"""
from __future__ import annotations

import datetime as dt
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import REFERENCE  # noqa: E402

UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
BUCKET = "https://openmobilitydata-data.s3.us-west-1.amazonaws.com/"
PREFIX = "public/feeds/"
OUT = REFERENCE / "ca_ab2097_omd_archive_listing.csv"
START, END, TARGET = "20220101", "20230630", dt.date(2022, 12, 14)
KEY = re.compile(r"^public/feeds/([^/]+)/([^/]+)/(\d{8})/")
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"


def list_page(token: str | None) -> tuple[list[str], str | None]:
    q = {"list-type": "2", "prefix": PREFIX, "max-keys": "1000"}
    if token:
        q["continuation-token"] = token
    req = urllib.request.Request(BUCKET + "?" + urllib.parse.urlencode(q), headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        root = ET.fromstring(r.read())
    keys = [c.findtext(f"{NS}Key") for c in root.findall(f"{NS}Contents")]
    nxt = root.findtext(f"{NS}NextContinuationToken") if root.findtext(f"{NS}IsTruncated") == "true" else None
    return keys, nxt


def main() -> None:
    copies: dict[tuple[str, str], list[str]] = defaultdict(list)
    token, pages, names = None, 0, 0
    while True:
        try:
            keys, token = list_page(token)
        except urllib.error.HTTPError as e:
            raise SystemExit(f"listing refused (HTTP {e.code}); recorded, no other route tried")
        pages += 1
        names += len(keys)
        for k in keys:
            m = KEY.match(k or "")
            if m and START <= m.group(3) <= END:
                copies[(m.group(1), m.group(2))].append(m.group(3))
        if not token:
            break
        time.sleep(1)

    def day(s: str) -> dt.date:
        return dt.date(int(s[:4]), int(s[4:6]), int(s[6:]))

    rows = []
    for (prov, feed), ds in sorted(copies.items()):
        ds = sorted(set(ds))
        before = [d for d in ds if day(d) <= TARGET]
        after = [d for d in ds if day(d) > TARGET]
        rows.append({"provider": prov, "feed_id": feed, "copies_2022_01_to_2023_06": len(ds),
                     "copies_2022_09_to_12": sum(1 for d in ds if "20220901" <= d <= "20221231"),
                     "nearest_on_or_before_2022_12_14": before[-1] if before else "",
                     "nearest_after_2022_12_14": after[0] if after else ""})
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"pages listed: {pages}; object names: {names:,}; feeds with copies Jan 2022–Jun 2023: {len(rows):,}; "
          f"with copies Sep–Dec 2022: {sum(1 for r in rows if r['copies_2022_09_to_12'])}")


if __name__ == "__main__":
    main()

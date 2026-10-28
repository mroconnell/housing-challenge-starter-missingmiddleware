"""Draw Los Angeles TOC project filings from CEQAnet (docs/parking/LA_TOC_PLAN.md).

    uv run python scripts/fetch_parking_la_toc.py

Reads the saved CEQAnet search indexes in data/raw/parking_la_toc/, draws Notices of Exemption at random
(seed 20261028, at most 10 per year), fetches each description, and keeps residential TOC projects until 50 are
found. Every fetched filing is saved with whether it qualified, so replacements can be counted.
Output (raw, git-ignored): data/raw/parking_la_toc/ceqanet_sample.json
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW  # noqa: E402

D = RAW / "parking_la_toc"
TOC = re.compile(r"Transit[- ]Oriented Communit|\bTOC\b", re.I)
HOMES = re.compile(r"dwelling unit|residential unit|apartment|\bunits\b", re.I)


def desc(i: str) -> str:
    req = urllib.request.Request(f"https://ceqanet.lci.ca.gov/{i}", headers={"User-Agent": "Mozilla/5.0"})
    h = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "ignore")
    t = html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)))
    a = t.find("Document Description")
    b = t.find("Contact Information", a)
    return t[a + 20:b if b > 0 else a + 3000].strip()


def main() -> None:
    idx = {}
    for f in ("ceqanet_index.json", "ceqanet_index_toc_phrase.json"):
        idx.update(json.load(open(D / f)))
    noe = sorted(k for k, v in idx.items() if v["type"] == "NOE")
    order = list(np.random.default_rng(20261028).permutation(noe))
    out, per = [], {}
    for i in order:
        y = idx[i]["date"][:4]
        if per.get(y, 0) >= 10:
            continue
        try:
            d = desc(i)
        except Exception as ex:  # noqa: BLE001
            d = f"FETCH FAILED: {ex}"
        ok = bool(TOC.search(d) and HOMES.search(d))
        out.append(dict(id=i, date=idx[i]["date"], title=idx[i]["title"], qualifies=ok, desc=d))
        if ok:
            per[y] = per.get(y, 0) + 1
        if sum(per.values()) >= 50:
            break
        time.sleep(0.3)
    json.dump(out, open(D / "ceqanet_sample.json", "w"))
    print(len(out), "fetched;", sum(x["qualifies"] for x in out), "qualify;", per)


if __name__ == "__main__":
    main()

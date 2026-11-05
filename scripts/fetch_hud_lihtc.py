"""HUD LIHTC property database via HUD's ArcGIS open-data service (the huduser.gov zip download returned an AWS WAF
bot challenge on 2026-11-05 and is cited as blocked, not worked around). Public domain (US government work).

    uv run python scripts/fetch_hud_lihtc.py
Output: data/raw/hud_lihtc/lihtc_properties.json (selected fields only; not committed), _download.json (URL, date, SHA-256)
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW  # noqa: E402

URL = "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/LIHTC/FeatureServer/0/query"
FIELDS = "HUD_ID,PROJ_ST,N_UNITS,LI_UNITS,YR_PIS,YR_ALLOC,TYPE,LAT,LON,STATE2KX,PLACE2KX,CURCNTY,CURCOSUB"
UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}


def main() -> None:
    out = RAW / "hud_lihtc"
    out.mkdir(parents=True, exist_ok=True)
    rows, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"where": "1=1", "outFields": FIELDS, "returnGeometry": "false", "f": "json",
                                    "resultOffset": offset, "resultRecordCount": 2000, "orderByFields": "OBJECTID"})
        d = json.loads(urllib.request.urlopen(urllib.request.Request(URL + "?" + q, headers=UA), timeout=120).read())
        feats = d.get("features", [])
        rows += [f["attributes"] for f in feats]
        if not feats or not d.get("exceededTransferLimit"):
            break
        offset += len(feats)
    p = out / "lihtc_properties.json"
    p.write_text(json.dumps(rows))
    (out / "_download.json").write_text(json.dumps({"url": URL, "fields": FIELDS, "accessed": dt.date.today().isoformat(),
                                                    "rows": len(rows), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                                                    "license": "Public domain (17 U.S.C. 105)",
                                                    "note": "huduser.gov/lihtc/lihtcpub.zip returned an AWS WAF challenge (HTTP 202, x-amzn-waf-action: challenge) on 2026-11-05; cited as blocked"}, indent=2))
    print(len(rows), "rows")


if __name__ == "__main__":
    main()

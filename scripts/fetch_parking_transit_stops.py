"""National rail stops from the National Transit Map (US DOT BTS NTAD, public domain) for parking test T.

    uv run python scripts/fetch_parking_transit_stops.py
Output: data/raw/parking_transit/ntm_rail_stops_national.json (stops served by light rail, streetcar, subway or
commuter rail; Amtrak is not in the layer).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW  # noqa: E402

URL = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0/query"
TYPES = ["0", "1", "2", "1;2", "0;2;3", "0;3", "1;2;3", "0;2", "1;3", "1;3;11", "2;3", "0;1", "0;1;2;3", "0;1;3"]


def main() -> None:
    where = "stop_type IN (%s)" % ",".join(f"'{t}'" for t in TYPES)
    out, off = [], 0
    while True:
        q = urllib.parse.urlencode(dict(where=where, outFields="ntd_id,stop_id,stop_name,stop_lat,stop_lon,stop_type,stop_type_text,download_date",
                                        returnGeometry="false", f="json", resultOffset=off, resultRecordCount=2000, orderByFields="OBJECTID"))
        d = json.load(urllib.request.urlopen(URL + "?" + q, timeout=120))
        if "error" in d:
            raise SystemExit(d["error"])
        f = [x["attributes"] for x in d["features"]]
        out += f
        off += len(f)
        if not f or not d.get("exceededTransferLimit"):
            break
    dest = RAW / "parking_transit" / "ntm_rail_stops_national.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(dict(source=URL, where=where, accessed=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    licence="US DOT BTS NTAD, public domain", stops=out)))
    print(len(out), "stops,", len({x["ntd_id"] for x in out}), "agencies ->", dest)


if __name__ == "__main__":
    main()

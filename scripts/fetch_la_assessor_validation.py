"""One-time, validation-only download: Los Angeles County Assessor roll attributes for the
parcels (AINs) that carry an ADU building permit in HCD APR Table A2 (LA County jurisdictions,
2018-2025). Owner-approved as a check on the A2-only rules in docs/gate3/MULTIFAMILY_LOT_ADUS.md;
not a pipeline input.

Source: LA County Assessor, "Assessor Parcel Data (Rolls 2016 - 2020)" and "(Rolls 2021 - 2025)"
tables on the county open-data hub (ArcGIS feature services, keyless). Only use and building
fields are requested (no owner, situs or value fields). Output (git-ignored):
data/raw/la_county_assessor_rolls/roll_<YYYY>.csv and _downloads.json.

    uv run python scripts/fetch_la_assessor_validation.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.comparison import ca_mf_lot as M  # noqa: E402

OUT = ROOT / "data/raw/la_county_assessor_rolls"
SERVICES = {
    range(2016, 2021): "https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2016_2020_Table/FeatureServer/0/query",
    range(2021, 2026): "https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2021_Table/FeatureServer/0/query",
}
FIELDS = ["AIN", "RollYear", "UseType", "UseCode", "UseCodeDescChar1", "UseCodeDescChar2", "UseCodeDescChar3",
          "totBuildingDataLines", "YearBuilt", "EffectiveYearBuilt", "Units"]
BATCH = 900


def service_for(year: int) -> str:
    return next(u for r, u in SERVICES.items() if year in r)


def query(url: str, year: int, ains: list[str]) -> list[dict]:
    where = f"RollYear='{year}' AND AIN IN ({','.join(repr(a) for a in ains)})"
    data = urllib.parse.urlencode({"where": where, "outFields": ",".join(FIELDS), "returnGeometry": "false",
                                   "f": "json", "resultRecordCount": 2000}).encode()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=120) as r:
                j = json.load(r)
            if "error" in j:
                raise RuntimeError(j["error"])
            return [f["attributes"] for f in j["features"]]
        except Exception as e:  # noqa: BLE001
            if attempt == 4:
                raise
            print("retry", year, e)
            time.sleep(5 * (attempt + 1))
    return []


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, _ = M.read_a2_adu_rows(ROOT / "data/raw/hcd_apr_a2/tablea2.csv")
    la = rows[rows["cnty_name"].eq("Los Angeles")]
    ains = sorted(set(M.la_ain(la["apn"]).dropna()))
    print(len(ains), "distinct 10-digit AINs")
    manifest = {}
    for year in M.A2_YEARS:
        url = service_for(year)
        recs = []
        for i in range(0, len(ains), BATCH):
            recs += query(url, year, ains[i:i + BATCH])
        df = pd.DataFrame(recs, columns=FIELDS)
        f = OUT / f"roll_{year}.csv"
        df.to_csv(f, index=False)
        b = f.read_bytes()
        manifest[f.name] = dict(url=url.removesuffix("/query"), accessed=dt.date.today().isoformat(), bytes=len(b),
                                sha256=hashlib.sha256(b).hexdigest(), rows=len(df),
                                method=f"keyless ArcGIS query, POST where RollYear='{year}' AND AIN IN (batches of {BATCH}); "
                                       f"AINs = 10-digit APNs of A2 ADU permits in LA County jurisdictions, 2018-2025",
                                fields=FIELDS, use="validation only (owner-approved one-time check)")
        print(year, len(df))
    (OUT / "_downloads.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

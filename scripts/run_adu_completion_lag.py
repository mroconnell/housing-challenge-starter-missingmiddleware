"""ADU permit-to-completion lag (improvement loop round 1, check of variant V1).

Vermont counts ADUs by year built; every other comparison state counts permits. This measures how long an ADU takes
from permit to completion where both dates are public: Austin's secondary-apartment building permits (R-102), issued
2012 onwards, from the city's open-data permit file (data/raw/adu_completion_lag/, fetched by the Socrata API).
Units: years from permit issue to completion; shares are of completed permits.

Run: uv run python scripts/run_adu_completion_lag.py   Output: reference/adu_completion_lag.csv
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/raw/adu_completion_lag/austin_secondary_apartment_dates.csv"
URL = "https://data.austintexas.gov/resource/3syk-w9eu.csv"


def fetch() -> None:
    import hashlib
    import json
    import urllib.parse
    import urllib.request
    q = {"$select": "permit_number,issue_date,completed_date,status_current",
         "$where": "permittype='BP' AND permit_class='R- 102 Secondary Apartment' AND issue_date >= '2012-01-01'",
         "$limit": "50000"}
    SRC.parent.mkdir(parents=True, exist_ok=True)
    b = urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=120).read()
    SRC.write_bytes(b)
    (SRC.parent / "_downloads.json").write_text(json.dumps({SRC.name: {
        "url": URL, **q, "license": "Public Domain U.S. Government (data.austintexas.gov)", "bytes": len(b),
        "sha256": hashlib.sha256(b).hexdigest()}}, indent=1))


def lag_table(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["issue_year"] = d["issue_date"].dt.year
    c = d.dropna(subset=["completed_date"])
    c = c[c["completed_date"] >= c["issue_date"]].copy()
    c["lag_years"] = (c["completed_date"] - c["issue_date"]).dt.days / 365.25
    c["completed_year"] = c["completed_date"].dt.year
    gap = c["completed_year"] - c["issue_year"]
    old = d[d["issue_year"].between(2012, 2021)]
    return pd.DataFrame([dict(
        city="Austin", permits_issued=len(d), permits_completed=len(c),
        completed_share_issued_2012_2021=old["completed_date"].notna().mean(),
        median_lag_years=c["lag_years"].median(), p25_lag_years=c["lag_years"].quantile(0.25),
        p75_lag_years=c["lag_years"].quantile(0.75),
        share_completed_same_calendar_year=(gap == 0).mean(), share_completed_next_calendar_year=(gap == 1).mean(),
        share_completed_2plus_years_later=(gap >= 2).mean())])


def main():
    if not SRC.exists():
        fetch()
    d = pd.read_csv(SRC, parse_dates=["issue_date", "completed_date"])
    t = lag_table(d).round(4)
    t.to_csv(ROOT / "reference/adu_completion_lag.csv", index=False)
    print(t.T.to_string())


if __name__ == "__main__":
    main()

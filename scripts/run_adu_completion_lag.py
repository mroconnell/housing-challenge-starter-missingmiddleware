"""ADU permit-to-completion lag (improvement loop round 1, check of variant V1).

Vermont counts ADUs by year built; every other comparison state counts permits. This measures how long an ADU takes
from permit to completion where both dates are public: Austin's secondary-apartment building permits (R-102), issued
2012 onwards, from the city's open-data permit file (data/raw/adu_completion_lag/, fetched by the Socrata API).
Units: years from permit issue to completion; shares are of completed permits.

California (owner suggestion 2026-10-31): HCD Annual Progress Report Table A2 (data/raw/hcd_apr_a2/tablea2.csv), ADU rows.
A permit row (building-permit date) is linked to a later completion row (certificate-of-occupancy date) for the same
jurisdiction and parcel number (or street address where no parcel number), in jurisdictions reporting 20+ ADU
completions. Unlinked permits count as not completed, so completion shares are lower bounds.

Run: uv run python scripts/run_adu_completion_lag.py
Outputs: reference/adu_completion_lag.csv (Austin), reference/adu_completion_lag_ca.csv (California, by permit year)
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


def ca_cohorts(path: Path) -> pd.DataFrame:
    import numpy as np
    cols = ["JURIS_NAME", "YEAR", "APN", "STREET_ADDRESS", "UNIT_CAT", "BP_ISSUE_DT1", "CO_ISSUE_DT1"]
    a = pd.read_csv(path, usecols=cols, dtype=str, low_memory=False)
    a = a[a["UNIT_CAT"].eq("ADU")].copy()
    for c in ("BP_ISSUE_DT1", "CO_ISSUE_DT1"):
        a[c] = pd.to_datetime(a[c], errors="coerce")
    apn = a["APN"].fillna("").str.replace(r"[^0-9A-Za-z]", "", regex=True).str.upper()
    addr = a["STREET_ADDRESS"].fillna("").str.upper().str.replace(r"[^0-9A-Z]", "", regex=True)
    last = int(pd.to_numeric(a["YEAR"], errors="coerce").max())        # latest report year (2025)
    a.loc[a["CO_ISSUE_DT1"].dt.year > last, "CO_ISSUE_DT1"] = pd.NaT    # dates after the latest report are typos
    a.loc[a["BP_ISSUE_DT1"].dt.year > last, "BP_ISSUE_DT1"] = pd.NaT
    a = a[(apn.str.len() >= 6) | (addr.str.len() >= 6)]
    apn, addr = apn[a.index], addr[a.index]
    a["j"] = a["JURIS_NAME"].str.upper()
    a["key"] = a["j"] + "|" + np.where(apn.str.len() >= 6, apn, "A:" + addr)
    bp = a[a["BP_ISSUE_DT1"].notna()].drop_duplicates(["key", "BP_ISSUE_DT1"])[["key", "j", "BP_ISSUE_DT1"]]
    co = a[a["CO_ISSUE_DT1"].notna()].drop_duplicates(["key", "CO_ISSUE_DT1"])[["key", "j", "CO_ISSUE_DT1"]]
    rep = co.groupby("j").size()
    m = bp[bp["j"].isin(rep[rep >= 20].index)].merge(co[["key", "CO_ISSUE_DT1"]], on="key", how="left")
    m = m[m["CO_ISSUE_DT1"].isna() | (m["CO_ISSUE_DT1"] >= m["BP_ISSUE_DT1"])]
    m = m.sort_values("CO_ISSUE_DT1").drop_duplicates(["key", "BP_ISSUE_DT1"])
    m["by"], m["cy"] = m["BP_ISSUE_DT1"].dt.year, m["CO_ISSUE_DT1"].dt.year
    m["lag"] = (m["CO_ISSUE_DT1"] - m["BP_ISSUE_DT1"]).dt.days / 365.25
    out = []
    for y in range(2018, last + 1):
        g = m[m["by"].eq(y)]
        row = dict(permit_year=y, permits_linked_sample=len(g), median_lag_years_completed=g["lag"].median())
        for k in range(0, 8):
            row[f"share_completed_by_permit_year_plus_{k}"] = (g["cy"] <= y + k).mean() if y + k <= last else np.nan
        out.append(row)
    return pd.DataFrame(out)


def main():
    if not SRC.exists():
        fetch()
    d = pd.read_csv(SRC, parse_dates=["issue_date", "completed_date"])
    t = lag_table(d).round(4)
    t.to_csv(ROOT / "reference/adu_completion_lag.csv", index=False)
    print(t.T.to_string())
    ca = ca_cohorts(ROOT / "data/raw/hcd_apr_a2/tablea2.csv").round(4)
    ca.to_csv(ROOT / "reference/adu_completion_lag_ca.csv", index=False)
    print(ca.to_string(index=False))


if __name__ == "__main__":
    main()

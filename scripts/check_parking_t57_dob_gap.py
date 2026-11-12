"""Test 57 audit addendum 2: is January-February 2021 a hole between the two DOB new-building filing files?

    uv run python scripts/check_parking_t57_dob_gap.py

Whole-city monthly totals only (never split by area or by Transit Zone arm), December 2020 to April 2021:
  - legacy DOB job filings, new buildings (ic3t-wcy2), file on disk data/raw/tod_cases/nyc/dob_nb_all.csv, by
    pre__filing_date; plus the same count from the online table, as a check of the on-disk file;
  - DOB NOW: Build job filings (w9ak-ipjd), job_type 'New Building' (and 'ALT-CO - New Building with Existing
    Elements to Remain', shown apart), by filing_date, via Socrata count queries; all filings and initial filings
    (job_filing_number ending '-I1') apart.
Prints a table; writes nothing.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_tod_cases import UA  # noqa: E402

MONTHS = ["2020-12", "2021-01", "2021-02", "2021-03", "2021-04"]
LO, HI = "2020-12-01T00:00:00", "2021-05-01T00:00:00"


def soql(base: str, where: str, datefield: str) -> pd.Series:
    q = urllib.parse.urlencode({"$select": f"date_trunc_ym({datefield}) as m, count(*) as n",
                                "$where": f"{where} AND {datefield} >= '{LO}' AND {datefield} < '{HI}'",
                                "$group": "m", "$limit": 100})
    with urllib.request.urlopen(urllib.request.Request(f"{base}?{q}", headers=UA), timeout=300) as r:
        rows = json.load(r)
    return pd.Series({r["m"][:7]: int(r["n"]) for r in rows}, dtype="int64").reindex(MONTHS, fill_value=0)


def main() -> None:
    leg = pd.read_csv(RAW / "tod_cases/nyc/dob_nb_all.csv", usecols=["job__", "doc__", "job_type", "pre__filing_date"],
                      dtype=str)
    d = pd.to_datetime(leg["pre__filing_date"], errors="coerce", format="mixed")
    m = d.dt.strftime("%Y-%m")
    disk = m[m.isin(MONTHS) & (leg["job_type"] == "NB")].value_counts().reindex(MONTHS, fill_value=0)
    out = pd.DataFrame({"legacy NB jobs, file on disk": disk})
    leg_on = "https://data.cityofnewyork.us/resource/ic3t-wcy2.json"
    # legacy pre__filing_date is text (MM/DD/YYYY) online, so count month by month with a LIKE pattern
    online = {}
    for mm in MONTHS:
        y, mo = mm.split("-")
        q = urllib.parse.urlencode({"$select": "count(*) as n",
                                    "$where": f"job_type='NB' AND doc__='01' AND pre__filing_date like '{mo}/%/{y}'"})
        with urllib.request.urlopen(urllib.request.Request(f"{leg_on}?{q}", headers=UA), timeout=300) as r:
            online[mm] = int(json.load(r)[0]["n"])
    out["legacy NB jobs (doc 01), online table"] = pd.Series(online)
    now = "https://data.cityofnewyork.us/resource/w9ak-ipjd.json"
    out["DOB NOW New Building, all filings"] = soql(now, "job_type='New Building'", "filing_date")
    out["DOB NOW New Building, initial filings (-I1)"] = soql(now, "job_type='New Building' AND job_filing_number like '%-I1'",
                                                             "filing_date")
    out["DOB NOW ALT-CO new building w/ existing elements"] = soql(
        now, "job_type='ALT-CO - New Building with Existing Elements to Remain'", "filing_date")
    out.index.name = "month (whole city)"
    pd.set_option("display.width", 250)
    print(out.to_string())
    print("\nlegacy on disk: last NB pre__filing_date", d[leg["job_type"] == "NB"].max().date())


if __name__ == "__main__":
    main()

"""CA AB 2097 study: re-geocode Table A2 permit rows whose HCD geocode is not street-level, with the U.S. Census
Bureau geocoder (public domain, no account). NOT RUN until Ryan agrees and the audit has checked this script.

Plan: docs/parking/CA_AB2097_PLAN.md, section 9 (geocode fall-off entries; Ryan 2026-11-05 19:02).

Which rows
- Rows with permitted homes (report years 2018-2025) that fail `ab2097.is_geocoded` (no street-level HCD point) and
  whose STREET_ADDRESS starts with a house number.
- A comparison sample: 2,000 rows HCD did geocode to street level (250 per report year, seed 20261105), sent the
  same way, so the distance between HCD's point and the Census point can be reported.

Request (fixed before running)
- Census Geocoder batch endpoint, benchmark Public_AR_Current, address CSV columns: id, street, city, state, zip.
  City = the jurisdiction name for cities; for "... COUNTY" jurisdictions, the city part of HCD's STD_ADDRESS when
  present, else blank. State = CA. Zip = the 5-digit zip in STD_ADDRESS when present, else blank.
- Batches of 1,000 rows, 10 seconds between batches, user agent "missing-middleware-research/1.0 (public data)".
  A refused batch is recorded and retried at most twice after 60 seconds; then left as failed.
- Accepted: match status "Match" with match type "Exact" or "Non_Exact" (an address-range match on the street).
  Not accepted: "Tie" and "No_Match".

Outputs
- Cache (git-ignored): data/interim/ca_ab2097_geocode/ — the request batches (addresses) and Census replies.
  Addresses never leave this folder except in the request to Census.
- data/interim/ca_ab2097_geocode/points.parquet (git-ignored): row key (hash), lat, lon, match type.
- Committed, no addresses: reference/ca_ab2097_regeocode_rates.csv (by report year and jurisdiction: rows sent,
  matched exact, matched non-exact, tie, no match) and reference/ca_ab2097_regeocode_vs_hcd.csv (comparison sample:
  by report year, median and 90th-percentile distance in metres between HCD and Census points, share over 150 m).

    uv run python scripts/ca_ab2097_regeocode.py            # prints how many rows would be sent; sends nothing
    uv run python scripts/ca_ab2097_regeocode.py --send     # sends (only after Ryan's OK and the audit's check)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

UA = "missing-middleware-research/1.0 (public data)"
URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BENCHMARK = "Public_AR_Current"
CACHE = RAW.parent / "interim" / "ca_ab2097_geocode"
BATCH, PAUSE, SEED, SAMPLE_PER_YEAR = 1000, 10, 20261105, 250
COLS = ["JURIS_NAME", "YEAR", "NO_BUILDING_PERMITS", "LATITUDE", "LONGITUDE", "STD_ADDRESS", "STREET_ADDRESS"]
HOUSE_NO = re.compile(r"^\d+[A-Za-z]?\s+\S+")
ZIP = re.compile(r"\b(9\d{4})\b")
ACCEPT = {"Exact", "Non_Exact"}


def row_key(df: pd.DataFrame) -> pd.Series:
    parts = [df[c].astype(object).where(df[c].notna(), "").map(str) for c in ("JURIS_NAME", "YEAR", "STREET_ADDRESS")]
    idx = pd.Series([str(i) for i in df.index], index=df.index)
    k = parts[0] + "|" + parts[1] + "|" + parts[2] + "|" + idx
    return k.map(lambda s: hashlib.sha1(s.encode()).hexdigest()[:16])


def city_of(df: pd.DataFrame) -> pd.Series:
    j = df.JURIS_NAME.astype(str).str.strip()
    std_city = df.STD_ADDRESS.fillna("").astype(str).str.split(",").str[-3].fillna("").str.strip()
    return np.where(j.str.upper().str.endswith("COUNTY"), std_city, j.str.title())


def build_requests(a2: pd.DataFrame) -> pd.DataFrame:
    d = a2[pd.to_numeric(a2.NO_BUILDING_PERMITS, errors="coerce").fillna(0) > 0].copy()
    geo = ab.is_geocoded(pd.to_numeric(d.LATITUDE, errors="coerce"), pd.to_numeric(d.LONGITUDE, errors="coerce"),
                         d.STD_ADDRESS)
    d["street"] = d.STREET_ADDRESS.fillna("").astype(str).str.strip()
    d["city"] = city_of(d)
    d["zip"] = d.STD_ADDRESS.fillna("").astype(str).str.extract(ZIP, expand=False).fillna("")
    d["key"] = row_key(d)
    fail = d[~geo & d.street.str.match(HOUSE_NO)].assign(kind="failed_hcd")
    ok = d[geo]
    sample = ok.groupby("YEAR").sample(n=SAMPLE_PER_YEAR, random_state=SEED).assign(kind="comparison_sample")
    return pd.concat([fail, sample])[["key", "kind", "JURIS_NAME", "YEAR", "street", "city", "zip", "LATITUDE", "LONGITUDE"]]


def send_batch(rows: pd.DataFrame) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    for r in rows.itertuples():
        w.writerow([r.key, r.street, r.city, "CA", r.zip])
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"benchmark\"\r\n\r\n{BENCHMARK}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"addressFile\"; filename=\"batch.csv\"\r\n"
            f"Content-Type: text/csv\r\n\r\n{buf.getvalue()}\r\n--{boundary}--\r\n").encode()
    req = urllib.request.Request(URL, data=body, headers={"User-Agent": UA,
                                                          "Content-Type": f"multipart/form-data; boundary={boundary}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"batch refused or failed ({e}); attempt {attempt + 1} of 3")
            if attempt < 2:
                time.sleep(60)
    return ""


def parse(reply: str) -> pd.DataFrame:
    out = []
    for f in csv.reader(io.StringIO(reply)):
        if not f:
            continue
        status = f[2] if len(f) > 2 else ""
        mtype = f[3] if len(f) > 3 else ""
        lon = lat = np.nan
        if len(f) > 5 and f[5]:
            lon, lat = (float(v) for v in f[5].split(","))
        out.append({"key": f[0], "status": status, "match_type": mtype, "lat": lat, "lon": lon})
    return pd.DataFrame(out)


def metres(lat1, lon1, lat2, lon2) -> np.ndarray:
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6_371_008.8 * np.arcsin(np.sqrt(a))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true")
    a = ap.parse_args()
    a2 = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=COLS, low_memory=False)
    req = build_requests(a2)
    print(req.groupby(["kind", "YEAR"]).size().to_string())
    if not a.send:
        print("nothing sent (run with --send after Ryan's OK and the audit's check)")
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    replies = []
    for i in range(0, len(req), BATCH):
        part = req.iloc[i:i + BATCH]
        f = CACHE / f"reply_{i // BATCH:04d}.csv"
        if not f.exists():
            f.write_text(send_batch(part))
            time.sleep(PAUSE)
        replies.append(parse(f.read_text()))
    res = req.merge(pd.concat(replies, ignore_index=True), on="key", how="left")
    res["accepted"] = (res.status == "Match") & res.match_type.isin(ACCEPT)
    res.loc[res.accepted, ["key", "kind", "YEAR", "lat", "lon", "match_type"]].to_parquet(CACHE / "points.parquet")
    f = res[res.kind == "failed_hcd"]
    rates = f.groupby(["YEAR", "JURIS_NAME"]).agg(
        rows_sent=("key", "size"), exact=("match_type", lambda s: int((s == "Exact").sum())),
        non_exact=("match_type", lambda s: int((s == "Non_Exact").sum())),
        tie=("status", lambda s: int((s == "Tie").sum())),
        no_match=("status", lambda s: int((s != "Match").sum() - (s == "Tie").sum()))).reset_index()
    rates.to_csv(REFERENCE / "ca_ab2097_regeocode_rates.csv", index=False)
    s = res[(res.kind == "comparison_sample") & res.accepted].copy()
    s["m"] = metres(pd.to_numeric(s.LATITUDE), pd.to_numeric(s.LONGITUDE), s.lat, s.lon)
    cmp_ = s.groupby("YEAR").m.agg(n="size", median_m="median", p90_m=lambda x: x.quantile(0.9),
                                   share_over_150m=lambda x: (x > 150).mean()).reset_index()
    cmp_.round(2).to_csv(REFERENCE / "ca_ab2097_regeocode_vs_hcd.csv", index=False)
    print(rates.groupby("YEAR")[["rows_sent", "exact", "non_exact", "tie", "no_match"]].sum().to_string())
    print(cmp_.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

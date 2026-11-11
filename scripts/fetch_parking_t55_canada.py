"""Download Statistics Canada building permits by census subdivision (CSD) and 2016 private dwellings by CSD
for the Canadian sense check (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, Test 55). Fetch step only: no counts.

    uv run --all-extras python scripts/fetch_parking_t55_canada.py [--refresh]

Sources (both Statistics Canada Open Licence, https://www.statcan.gc.ca/en/terms-conditions/open-licence):
- Table 46-10-0087-01, "Rural Canada Housing Profiles, residential building permits, numbers and values, by type of
  residential building and type of work, 2018 to 2023" (annual, CSDs on 2021 boundaries, archived 2025-03-11).
  This is the only open StatCan table with dwelling units created by CSD; the current monthly permit tables
  (34-10-0066, 34-10-0285, 34-10-0292) stop at census metropolitan areas. So permits cover 2018-2023 only.
- Table 98-10-0002-01, "Population and dwelling counts: Canada and census subdivisions (municipalities)", 2021
  Census, which carries "Total private dwellings, 2016" re-tabulated on 2021 CSD boundaries (matches the permit
  table's boundaries). The 2016-boundary file 98-402-X2016001 on www12.statcan.gc.ca returned a bot "Security
  Check" page to automated access, so it is not used.

Raw (git-ignored): data/raw/parking_t55_canada/ with _downloads.json (url, date, bytes, sha256, licence).
Tidy (git-ignored): data/processed/t55/csd_permits_units_by_year.csv, data/processed/t55/csd_dwellings_2016.csv.

Notes on the permit table:
- Its metadata lists SCALAR_FACTOR "thousands" for every metric, but the national units-created total is
  ~236,000 in 2018 when read as plain units (in line with national permit counts), so values are taken as units.
- Cells with STATUS "x" are suppressed (confidentiality). From reference year 2022 on, StatCan also drops values
  with quality "F" from the compilation, so missing cells are not zeros. Both are counted per CSD-year.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "parking_t55_canada"
OUT = ROOT / "data" / "processed" / "t55"
UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
LICENCE = "Statistics Canada Open Licence (https://www.statcan.gc.ca/en/terms-conditions/open-licence)"
WDS = "https://www150.statcan.gc.ca/t1/wds/rest"
TABLES = {"46100087": "permits by CSD 2018-2023 (46-10-0087-01)", "98100002": "2021 Census population and dwelling counts by CSD (98-10-0002-01)"}
PROV = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB", "47": "SK", "48": "AB",
        "59": "BC", "60": "YT", "61": "NT", "62": "NU"}


def http_get(url: str, data: bytes | None = None, headers: dict | None = None, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


class Log:
    def __init__(self) -> None:
        RAW.mkdir(parents=True, exist_ok=True)
        self.path = RAW / "_downloads.json"
        self.m = json.loads(self.path.read_text()) if self.path.exists() else {"files": {}}

    def save_file(self, name: str, data: bytes, url: str, **extra) -> None:
        (RAW / name).write_bytes(data)
        rec = {"url": url, "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "bytes": len(data),
               "sha256": hashlib.sha256(data).hexdigest(), "licence": LICENCE, **extra}
        self.m["files"][name] = rec
        self.path.write_text(json.dumps(self.m, indent=1) + "\n")
        print(f"  {name}: {len(data):,} bytes")

    def have(self, name: str, refresh: bool) -> bool:
        return not refresh and (RAW / name).exists() and name in self.m["files"]


def fetch(log: Log, pid: str, refresh: bool) -> None:
    meta = f"{pid}_metadata.json"
    if not log.have(meta, refresh):
        url = f"{WDS}/getCubeMetadata"
        log.save_file(meta, http_get(url, data=json.dumps([{"productId": int(pid)}]).encode(),
                                     headers={"Content-Type": "application/json"}), url, method="POST",
                      body=f'[{{"productId":{pid}}}]', table=TABLES[pid])
    z = f"{pid}-eng.zip"
    if not log.have(z, refresh):
        loc = json.loads(http_get(f"{WDS}/getFullTableDownloadCSV/{pid}/en"))["object"]
        log.save_file(z, http_get(loc), loc, table=TABLES[pid])
    else:
        print(f"  {z}: kept")


def read_zip_csv(name: str, pid: str) -> pd.DataFrame:
    with zipfile.ZipFile(RAW / name) as zf:
        return pd.read_csv(io.BytesIO(zf.read(f"{pid}.csv")), dtype=str, encoding="utf-8-sig", keep_default_na=False)


def csd_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["DGUID"].str[4:9] == "A0005"].copy()  # CSD level
    df["csd_code"] = df["DGUID"].str[-7:]
    df["province"] = df["csd_code"].str[:2].map(PROV)
    df["dguid_vintage"] = df["DGUID"].str[:4]
    return df


def tidy_permits() -> pd.DataFrame:
    d = csd_cols(read_zip_csv("46100087-eng.zip", "46100087"))
    # CSD rows carry one location indicator per year ("Rural and small town area" or "Functional urban area"; 48 CSDs
    # switch between years, none has both in one year), so no "All areas" filter is applied at CSD level.
    d = d[d["Metrics"] == "Number of dwelling-units created"].copy()
    d["v"] = pd.to_numeric(d["VALUE"], errors="coerce")
    d["suppressed"] = d["STATUS"].eq("x")
    d["new_constr"] = d["v"].where(d["Type of work"] == "New construction")
    g = d.groupby(["csd_code", "REF_DATE"])
    t = pd.DataFrame({
        "csd_name": g["GEO"].first(),
        "province": g["province"].first(),
        "dguid_vintage": g["dguid_vintage"].first(),
        "location_indicator": g["Location indicator"].agg(lambda x: "; ".join(sorted(set(x)))),
        "dwelling_units_created": g["v"].sum(min_count=1),
        "dwelling_units_created_new_construction": g["new_constr"].sum(min_count=1),
        "n_cells_reported": g["v"].count(),
        "n_cells_suppressed_x": g["suppressed"].sum(),
    }).reset_index().rename(columns={"REF_DATE": "year"})
    t["year"] = t["year"].astype(int)
    t["source_table"] = "46-10-0087-01"
    return t[["csd_code", "csd_name", "province", "year", "dwelling_units_created", "dwelling_units_created_new_construction",
              "n_cells_reported", "n_cells_suppressed_x", "location_indicator", "dguid_vintage", "source_table"]].sort_values(["csd_code", "year"])


def tidy_dwellings() -> pd.DataFrame:
    d = csd_cols(read_zip_csv("98100002-eng.zip", "98100002"))
    col = [c for c in d.columns if "Total private dwellings, 2016" in c][0]
    pcol = [c for c in d.columns if "Population, 2016" in c][0]
    i = list(d.columns).index(col)
    t = pd.DataFrame({
        "csd_code": d["csd_code"], "csd_name": d["GEO"], "province": d["province"],
        "private_dwellings_2016": pd.to_numeric(d[col], errors="coerce"),
        "private_dwellings_2016_symbol": d.iloc[:, i + 1],
        "population_2016": pd.to_numeric(d[pcol], errors="coerce"),
        "boundaries": "2021 CSD boundaries (2016 counts re-tabulated by StatCan)",
        "source_table": "98-10-0002-01",
    })
    return t.sort_values("csd_code")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    log = Log()
    for pid in TABLES:
        fetch(log, pid, a.refresh)
    OUT.mkdir(parents=True, exist_ok=True)
    p, w = tidy_permits(), tidy_dwellings()
    p.to_csv(OUT / "csd_permits_units_by_year.csv", index=False)
    w.to_csv(OUT / "csd_dwellings_2016.csv", index=False)
    print(f"permits: {len(p):,} CSD-years, {p.csd_code.nunique():,} CSDs, years {p.year.min()}-{p.year.max()}")
    print(f"dwellings: {len(w):,} CSDs")
    for code, nm in (("4811061", "Edmonton"), ("3520005", "Toronto")):  # presence only, no values
        print(f"  {nm} {code}: permit rows {int((p.csd_code == code).sum())}, dwelling rows {int((w.csd_code == code).sum())}")


if __name__ == "__main__":
    sys.exit(main())

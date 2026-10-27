"""City traits for the parking trait test (docs/parking/TRAITS_PLAN.md): one row per US place
and county subdivision, built from ACS 2020-2024 and the Census 2024 Gazetteer. No effects are
read here; the traits are joined to effects only by scripts/run_parking_traits.py.

    uv run python scripts/build_parking_traits.py [--fetch]

Inputs: data/raw/census_acs5_2024_tbsf/acsdt5y2024-{b25002,b25024}.dat,
        data/raw/census_acs5_2024_tbsf_market/acsdt5y2024-{b25077,b19013}.dat,
        data/raw/census_gazetteer_2024/2024_Gaz_{place,cousubs}_national.zip (fetched; public domain)
Output: reference/parking_place_traits.csv (acs_geoid = "160|<place>" or "060|<county subdivision>")
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

GAZ = RAW / "census_gazetteer_2024"
GAZ_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/{f}"
GAZ_FILES = {"160": "2024_Gaz_place_national.zip", "060": "2024_Gaz_cousubs_national.zip"}


def fetch() -> None:
    GAZ.mkdir(parents=True, exist_ok=True)
    log = {}
    for f in GAZ_FILES.values():
        url = GAZ_URL.format(f=f)
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "missing-middleware research"}), timeout=120).read()
        (GAZ / f).write_bytes(data)
        log[f] = {"accessed": dt.date.today().isoformat(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "url": url}
    (GAZ / "_downloads.json").write_text(json.dumps(log, indent=2) + "\n")


def gazetteer() -> pd.DataFrame:
    rows = []
    for sl, f in GAZ_FILES.items():
        with zipfile.ZipFile(GAZ / f) as z:
            name = z.namelist()[0]
            d = pd.read_csv(z.open(name), sep="\t", dtype={"GEOID": str})
        d.columns = [c.strip() for c in d.columns]
        rows.append(pd.DataFrame({"acs_geoid": sl + "|" + d["GEOID"], "name": d["NAME"].str.strip(), "land_sqmi": d["ALAND_SQMI"].astype(float)}))
    return pd.concat(rows, ignore_index=True)


def acs(path: Path, cols: list[str]) -> pd.DataFrame:
    d = parsers.read_acs_sf(path, state_fips="", sumlevels=("040", "060", "160"))
    d["acs_geoid"] = d["sumlevel"] + "|" + d["geoid"]
    return d.set_index("acs_geoid")[cols]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    if a.fetch or not (GAZ / "_downloads.json").exists():
        fetch()
    t = acs(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", ["B25002_E001"]).rename(columns={"B25002_E001": "homes"})
    t = t.join(acs(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25024.dat", ["B25024_E001", "B25024_E002"]))
    t = t.join(acs(RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b25077.dat", ["B25077_E001"]).rename(columns={"B25077_E001": "home_value"}))
    t = t.join(acs(RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b19013.dat", ["B19013_E001"]).rename(columns={"B19013_E001": "income"}))
    t = t.reset_index()
    t["state"] = t["acs_geoid"].str.split("|").str[1].str[:2]
    st = t[t["acs_geoid"].str.startswith("040|")].set_index("state")[["home_value", "income"]]
    t = t[~t["acs_geoid"].str.startswith("040|")].merge(gazetteer(), on="acs_geoid", how="left")
    t["T1_home_value_rel"] = t["home_value"] / t["state"].map(st["home_value"])
    t["T2_income_rel"] = t["income"] / t["state"].map(st["income"])
    t["T3_log_density"] = np.log10((t["homes"] / t["land_sqmi"]).where(t["land_sqmi"] > 0))
    t["T4_single_family_share"] = t["B25024_E002"] / t["B25024_E001"]
    t["T5_log_land_sqmi"] = np.log10(t["land_sqmi"].where(t["land_sqmi"] > 0))
    t["T6_value_to_income"] = t["T1_home_value_rel"] / t["T2_income_rel"]
    # keep only the states needed: repeal places' states (dataset A), California (dataset B), Wisconsin (application)
    m = pd.read_csv(REFERENCE / "parking_comparison_match.csv", dtype={"key": str})
    keep = set(m["key"].dropna().str.split("|").str[0]) | {"06", "55"}
    t = t[t["state"].isin(keep)]
    t = t.replace([np.inf, -np.inf], np.nan)
    cols = ["acs_geoid", "name", "state", "homes", "home_value", "income", "land_sqmi"] + [c for c in t.columns if c.startswith("T")]
    t[cols].round(5).to_csv(REFERENCE / "parking_place_traits.csv", index=False)
    print(len(t), "places;", t[cols].notna().mean().round(3).to_dict())


if __name__ == "__main__":
    main()

"""Run the pre-registered parking repeal comparison (docs/parking/COMPARISON_PLAN.md).

    uv run python scripts/run_parking_comparison.py [--fetch]

Inputs (git-ignored raw data, fetched automatically with --fetch or when missing):
    data/raw/census_bps_place_us/{ne,mw,so,we}{2012..2025}a.txt   Census BPS place files (public domain)
    data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25002.dat         ACS homes (already used by the foundation)
    data/raw/census_acs5_2024_tbsf_market/acsdt5y2024-b25064.dat  ACS median gross rent
    data/raw/census_cbsa_cb_2024/cb_2024_us_cbsa_20m.zip          CBSA type (metro / micro)
    reference/parking_reform_cases.csv, parking_reform_taxonomy.csv, parking_repeal_checks.csv
Outputs:
    reference/parking_comparison_match.csv     each repeal place -> its Census permit place
    reference/parking_comparison_effects.csv   one row per repeal place and outcome
    reference/parking_comparison_models.csv    leave-one-place-out comparison of models
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

BPS_DIR = RAW / "census_bps_place_us"
REGIONS = {"ne": "Northeast%20Region", "mw": "Midwest%20Region", "so": "South%20Region", "we": "West%20Region"}
STATE_FIPS = {
    "Alabama": "01", "Alaska": "02", "Arizona": "04", "Arkansas": "05", "California": "06", "Colorado": "08",
    "Connecticut": "09", "Delaware": "10", "District of Columbia": "11", "Florida": "12", "Georgia": "13",
    "Hawaii": "15", "Idaho": "16", "Illinois": "17", "Indiana": "18", "Iowa": "19", "Kansas": "20",
    "Kentucky": "21", "Louisiana": "22", "Maine": "23", "Maryland": "24", "Massachusetts": "25",
    "Michigan": "26", "Minnesota": "27", "Mississippi": "28", "Missouri": "29", "Montana": "30",
    "Nebraska": "31", "Nevada": "32", "New Hampshire": "33", "New Jersey": "34", "New Mexico": "35",
    "New York": "36", "North Carolina": "37", "North Dakota": "38", "Ohio": "39", "Oklahoma": "40",
    "Oregon": "41", "Pennsylvania": "42", "Rhode Island": "44", "South Carolina": "45", "South Dakota": "46",
    "Tennessee": "47", "Texas": "48", "Utah": "49", "Vermont": "50", "Virginia": "51", "Washington": "53",
    "West Virginia": "54", "Wisconsin": "55", "Wyoming": "56",
}


def fetch_bps(force: bool = False) -> None:
    BPS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = BPS_DIR / "_downloads.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    for r, folder in REGIONS.items():
        for y in range(cmp.FIRST_YEAR, cmp.LAST_YEAR + 1):
            f = BPS_DIR / f"{r}{y}a.txt"
            if f.exists() and f.stat().st_size and not force:
                continue
            url = f"https://www2.census.gov/econ/bps/Place/{folder}/{f.name}"
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "missing-middleware research"}),
                                          timeout=120).read()
            f.write_bytes(data)
            log[f.name] = {"accessed": dt.date.today().isoformat(), "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest(), "url": url}
    log_path.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")


def read_bps_us() -> pd.DataFrame:
    frames = []
    for f in sorted(BPS_DIR.glob("*a.txt")):
        d = parsers.read_bps(f, "place", state_fips=None)
        d["year"] = int(f.name[2:6])
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def acs_table(path: Path, col: str) -> pd.Series:
    d = parsers.read_acs_sf(path, state_fips="", sumlevels=("040", "060", "160"))
    d["acs_geoid"] = d["sumlevel"] + "|" + d["geoid"]
    return d.set_index("acs_geoid")[col]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--match-only", action="store_true", help="write the match table and stop (no outcomes)")
    a = ap.parse_args()
    if a.fetch or not any(BPS_DIR.glob("*a.txt")):
        fetch_bps()
    p = cmp.panel(read_bps_us())
    homes_geo = acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
    rent_geo = acs_table(RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b25064.dat", "B25064_E001")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(homes_geo)
    homes = homes[homes > 0]

    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    cases = pd.read_csv(REFERENCE / "parking_reform_cases.csv")
    cases = cases[(cases["benchmark_rating"] == "at") & cases["adopted_year"].between(2015, 2022)].drop_duplicates("prn_key")

    # places with any citywide residential removal record (at or near, any status) never serve as comparisons
    reformed = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
    excluded = set()
    reform_year = {}   # BPS key -> earliest adoption year of a citywide residential removal (at or near, adopted)
    for r in reformed.drop_duplicates("prn_key").itertuples():
        k = cmp.match_place(p, STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if k:
            excluded.add(k)
            yrs = reformed[(reformed["prn_key"] == r.prn_key) & (reformed["status"] == "adopted")]["adopted_year"].dropna()
            if len(yrs):
                reform_year[k] = min(int(yrs.min()), reform_year.get(k, 9999))

    checks_path = REFERENCE / "parking_repeal_checks.csv"
    checks = pd.read_csv(checks_path) if checks_path.exists() else pd.DataFrame(columns=["prn_key"])
    rows = []
    for r in cases.itertuples():
        k = cmp.match_place(p, STATE_FIPS.get(r.state, "??"), r.place, r.population)
        ck = checks[checks["prn_key"] == r.prn_key]
        ev = int(r.adopted_year)
        use = True
        note = ""
        if not ck.empty:
            c = ck.iloc[0]
            if str(c.get("in_force", "")).lower() == "no" or str(c.get("benchmark_rating_checked", "")).lower() == "weaker":
                use, note = False, "ordinance check: not at the benchmark"
            eff = str(c.get("effective_date", "") or "")
            if eff[:4].isdigit() and int(eff[:4]) > ev:
                ev, note = int(eff[:4]), (note + "; " if note else "") + "effective year used"
        rows.append(dict(prn_key=r.prn_key, place=r.place, state=r.state, population=r.population,
                         adopted_year=int(r.adopted_year), event_year=ev, key=k,
                         bps_name=geo["name"].get(k) if k else None, use=use and k is not None,
                         note=note or ("not found in Census permit files" if k is None else "")))
    match = pd.DataFrame(rows)
    match.to_csv(REFERENCE / "parking_comparison_match.csv", index=False)
    if a.match_only:
        print(f"matched {match['key'].notna().sum()} of {len(match)}; comparison exclusions {len(excluded)}")
        return

    use = match[match["use"]]
    eff = cmp.effects(p, use[["prn_key", "place", "state", "population", "key", "event_year"]], excluded, homes)
    st_rent = {k.split("|")[1]: v for k, v in rent_geo.items() if k.startswith("040|")}
    eff["rel_rent"] = [rent_geo.get(geo["acs_geoid"].get(k)) / st_rent.get(k.split("|")[0], np.nan) for k in eff["key"]]
    cbsa = pd.Series(dtype=str)
    try:
        import geopandas as gpd
        g = gpd.read_file("zip://" + str(RAW / "census_cbsa_cb_2024" / "cb_2024_us_cbsa_20m.zip"), ignore_geometry=True)
        cbsa = g.set_index("CBSAFP")["LSAD"]
    except Exception as e:  # noqa: BLE001
        print("CBSA file not read:", e)
    bps_cbsa = read_bps_us().assign(key=lambda d: d["state_fips"].str.strip() + "|" + d["bps_id"].str.strip()) \
        .drop_duplicates("key", keep="last").set_index("key")["cbsa"].astype(str).str.strip()
    eff["metro"] = [1.0 if cbsa.get(bps_cbsa.get(k, ""), "") == "M1" else 0.0 for k in eff["key"]]
    eff["log_pop"] = cmp.log_pop(eff["population"])
    # For a later question (owner, 2026-10-26): does the effect differ when most of a state's
    # large cities have repealed? Share of the state's population in places of 50,000+ (BPS
    # population in the year before the repeal) living in places that had repealed by then.
    eff["state_large_city_share_repealed"] = [
        cmp.state_share_repealed(p, k.split("|")[0], int(y), reform_year) if isinstance(k, str) else np.nan
        for k, y in zip(eff["key"], eff["event_year"])]
    eff.to_csv(REFERENCE / "parking_comparison_effects.csv", index=False)

    out = []
    for outcome in ("all", "2plus"):
        d = eff[(eff["status"] == "included") & (eff["outcome"] == outcome)].dropna(subset=["effect", "log_pop"])
        specs = cmp.candidate_specs(has_rent=d["rel_rent"].notna().all())
        m = cmp.compare_models(d, specs)
        m.insert(0, "outcome", outcome)
        m["n_places"] = len(d)
        out.append(m)
    pd.concat(out).to_csv(REFERENCE / "parking_comparison_models.csv", index=False)
    print(f"matched {match['key'].notna().sum()} of {len(match)}; used {match['use'].sum()}; "
          f"included {eff[eff['status'] == 'included']['key'].nunique()}")


if __name__ == "__main__":
    main()

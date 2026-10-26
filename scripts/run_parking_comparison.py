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
    reference/parking_comparison_estimates.csv estimates and bootstrap ranges
    reference/parking_comparison_robustness.csv checks on the one-average estimate
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
    popn = geo["acs_geoid"].map(acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))

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

    checks = pd.read_csv(REFERENCE / "parking_repeal_checks.csv", dtype={"repealed_from_year": "Int64"})
    rows = []
    for r in cases.itertuples():
        k = cmp.match_place(p, STATE_FIPS.get(r.state, "??"), r.place, r.population)
        c = checks[checks["prn_key"] == r.prn_key].iloc[0]
        ev = int(c["event_year"])
        rating = c["benchmark_rating_checked"]
        last_post = ev + max(cmp.POST_YEARS)
        reason = []
        if k is None:
            reason.append("not found in Census permit files")
        if rating == "weaker":
            reason.append("ordinance check: weaker than the benchmark")
        if bool(c["no_event"]):
            reason.append("ordinance check: no minimums before either, so no repeal event")
        if pd.notna(c["repealed_from_year"]) and int(c["repealed_from_year"]) <= last_post:
            reason.append(f"minimums restored in {int(c['repealed_from_year'])}, inside the after period")
        arm = "main" if rating == "at" else "near"
        rows.append(dict(prn_key=r.prn_key, place=r.place, state=r.state, population=r.population,
                         adopted_year_prn=int(r.adopted_year), event_year=ev, rating_checked=rating, arm=arm,
                         simultaneous_rewrite=bool(c["simultaneous_rewrite"]), key=k,
                         bps_name=geo["name"].get(k) if k else None, use=not reason, note="; ".join(reason)))
    match = pd.DataFrame(rows)
    match.to_csv(REFERENCE / "parking_comparison_match.csv", index=False)
    if a.match_only:
        print(f"matched {match['key'].notna().sum()} of {len(match)}; comparison exclusions {len(excluded)}")
        return

    use = match[match["use"]]
    eff = cmp.effects(p, use[["prn_key", "place", "state", "population", "key", "event_year", "arm",
                              "simultaneous_rewrite"]], excluded, homes, popn)
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
    eff["population_prn"] = eff["population"]
    eff["population"] = [popn.get(k, np.nan) if isinstance(k, str) else np.nan for k in eff["key"]]
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
        for sample in ("main", "main_without_rewrites"):
            d = eff[(eff["status"] == "included") & (eff["outcome"] == outcome) & (eff["arm"] == "main")]
            if sample == "main_without_rewrites":
                d = d[~d["simultaneous_rewrite"]]
            d = d.dropna(subset=["effect", "log_pop"])
            specs = cmp.candidate_specs(has_rent=d["rel_rent"].notna().all())
            m = cmp.compare_models(d, specs)
            m.insert(0, "sample", sample)
            m.insert(0, "outcome", outcome)
            m["n_places"] = len(d)
            out.append(m)
    pd.concat(out).to_csv(REFERENCE / "parking_comparison_models.csv", index=False)

    # point estimates and bootstrap ranges (5th-95th percentile) for the one-average model and
    # the leave-one-out winner, main sample
    summ = []
    models = pd.concat(out)
    for outcome in ("all", "2plus"):
        d = eff[(eff["status"] == "included") & (eff["outcome"] == outcome) & (eff["arm"] == "main")].dropna(
            subset=["effect", "log_pop"]).reset_index(drop=True)
        specs = cmp.candidate_specs(has_rent=d["rel_rent"].notna().all())
        won = models[(models["outcome"] == outcome) & (models["sample"] == "main") & models["chosen"]]["model"].iloc[0]
        for name in dict.fromkeys(["M0 one average", won]):
            spec = specs[name]
            X = cmp.design(d, spec)
            beta = cmp.wls(X, d["effect"].values, d["homes"].values.astype(float))
            bs = cmp.bootstrap(d, spec)
            terms = ["intercept"] + [f"population >= {c:,}" for c in spec.get("bands", ())] + list(spec.get("vars", []))
            for j, t in enumerate(terms):
                summ.append(dict(outcome=outcome, model=name, term=t, estimate=beta[j],
                                 p05=np.percentile(bs[:, j], 5), p95=np.percentile(bs[:, j], 95),
                                 n_places=len(d), draws=len(bs)))
    pd.DataFrame(summ).to_csv(REFERENCE / "parking_comparison_estimates.csv", index=False)

    # robustness of the one-average estimate (homes-weighted unless stated)
    rob = []
    for outcome in ("all", "2plus"):
        inc = eff[(eff["status"] == "included") & (eff["outcome"] == outcome)].dropna(subset=["effect"])
        main = inc[inc["arm"] == "main"].reset_index(drop=True)

        def wmean(d):
            return float(np.average(d["effect"], weights=d["homes"])) if len(d) else np.nan

        def add(check, d, value=None, boot=True):
            lo = hi = np.nan
            if boot and len(d) > 2:
                b = cmp.bootstrap(d.reset_index(drop=True), {})[:, 0]
                lo, hi = np.percentile(b, 5), np.percentile(b, 95)
            rob.append(dict(outcome=outcome, check=check, n_places=len(d),
                            effect=wmean(d) if value is None else value, p05=lo, p95=hi))
        add("main, weighted by homes", main)
        add("main, unweighted mean", main, float(main["effect"].mean()), boot=False)
        add("main, median", main, float(main["effect"].median()), boot=False)
        add("without San Francisco", main[main["place"] != "San Francisco"])
        add("without the two Texas places", main[main["state"] != "Texas"])
        add("without places that rewrote zoning at the same time", main[~main["simultaneous_rewrite"]])
        add("main and near together", inc)
        for st in sorted(main["state"].unique()):
            add(f"leave out {st}", main[main["state"] != st], boot=False)
    pd.DataFrame(rob).to_csv(REFERENCE / "parking_comparison_robustness.csv", index=False)
    print(f"matched {match['key'].notna().sum()} of {len(match)}; used {match['use'].sum()}; "
          f"included {eff[eff['status'] == 'included']['key'].nunique()}")


if __name__ == "__main__":
    main()

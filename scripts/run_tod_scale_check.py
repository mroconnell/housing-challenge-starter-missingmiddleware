"""TOD scale check (docs/tod/GATE3_MODEL_SPEC.md section 9; results in docs/tod/MODEL.md section 10).

Asks whether each TOD scenario's per-acre response, carried over the whole station-area land,
implies more apartment permitting than a metro of Milwaukee's or Madison's size has ever absorbed.
It is a check shown to the owner, not a cap: no model number is changed.

    uv run --all-extras python scripts/run_tod_scale_check.py          # fetches what is missing, then runs
    uv run --all-extras python scripts/run_tod_scale_check.py --force  # re-downloads every raw file

Offline after the first run (every raw file is cached and skipped if present).

In:  reference/tod_model_per_acre_by_county.csv, reference/tod_model_per_acre_statewide.csv (method A scenarios;
     method B rows are blank and skipped)
     raw (git-ignored), fetched automatically into data/raw/census_bps_cbsa/ with _downloads.json
     (URL, access date, bytes, SHA-256):
       - Census Building Permits Survey (BPS) annual county files co{YYYY}a.txt, 2000-2014
         (2015-2025 are reused from data/raw/census_bps_county/ when cached there, else fetched here)
       - BPS annual CBSA files cbsa2024a.txt, cbsa2025a.txt (cross-check only)
       - PEP Vintage 2025 metro file cbsa-est2025-alldata.csv (the July 2023 OMB delineation:
         which counties make up each metro)
       - PEP 2010-2020 intercensal county table co-est2020int-pop.xlsx (its "April 1, 2020 Census"
         column gives the 2020 Census count per county)
       - PEP county housing-unit estimates (July 1): hu-est00int-tot.csv (intercensal, 2000-2009),
         HU-EST2020_ALL.csv (Vintage 2020, 2010-2019), CO-EST2025-HU.xlsx (Vintage 2025, 2020-2025)
Out: reference/tod_scale_check.csv              benchmark, metro history and scenario rows (kind column)
     reference/tod_scale_check_metro_years.csv  the peer panel: metro x year, 5+ permits, homes, rate

Method:
  - Metros are US metropolitan statistical areas in the July 2023 OMB delineation whose 2020 Census
    population (sum of their counties) is 500,000 to 2,500,000. Each metro keeps the same counties in
    every year, so a metro's series is not broken by delineation changes. That is why metros are
    built from the county files rather than read from the BPS metro files, which follow whatever
    delineation was current each year (MSA/PMSA before 2004, then CBSA vintages 2003-2023).
  - Connecticut metros are left out: the 2023 delineation and BPS from 2023 use the state's new
    planning regions, while BPS before 2023 and the housing-unit estimates before 2020 use the old
    counties. The two do not nest.
  - Rate = units in buildings with 5 or more units permitted in the year (BPS, with Census
    imputation) per 1,000 housing units on July 1 of that year (PEP), 2000-2025.
  - Scenario additions (method A, 2027-2031) are treated as 5+ unit apartment permits, divided by
    the metro's July 1 2025 housing units, and added to the metro's own 2021-2025 mean observed rate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import unicodedata
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import scale_check as S  # noqa: E402

D = RAW / "census_bps_cbsa"
COUNTY_CACHE = RAW / "census_bps_county"
YEARS = tuple(range(2000, 2026))
RECENT = tuple(range(2021, 2026))
POP_MIN, POP_MAX = 500_000, 2_500_000
HU_YEAR = 2025
MODEL_YEARS = (2027, 2028, 2029, 2030, 2031)
SCENARIOS = ("little", "reference_line", "typical", "strong")

METROS = {  # the county sets the brief names; checked against the 2023 delineation below
    "Milwaukee": ("33340", {"55079": "Milwaukee County", "55133": "Waukesha County",
                            "55089": "Ozaukee County", "55131": "Washington County"}),
    "Madison": ("31540", {"55025": "Dane County", "55021": "Columbia County",
                          "55045": "Green County", "55049": "Iowa County"}),
}

BPS = "https://www2.census.gov/econ/bps"
POPEST = "https://www2.census.gov/programs-surveys/popest"
URLS = {
    **{f"co{y}a.txt": f"{BPS}/County/co{y}a.txt" for y in YEARS},
    "cbsa2024a.txt": f"{BPS}/CBSA%20(beginning%20Jan%202024)/cbsa2024a.txt",
    "cbsa2025a.txt": f"{BPS}/CBSA%20(beginning%20Jan%202024)/cbsa2025a.txt",
    "cbsa-est2025-alldata.csv": f"{POPEST}/datasets/2020-2025/metro/totals/cbsa-est2025-alldata.csv",
    "co-est2020int-pop.xlsx": f"{POPEST}/tables/2010-2020/intercensal/county/co-est2020int-pop.xlsx",
    "hu-est00int-tot.csv": f"{POPEST}/datasets/2000-2010/intercensal/housing/hu-est00int-tot.csv",
    "HU-EST2020_ALL.csv": f"{POPEST}/datasets/2010-2020/housing/HU-EST2020_ALL.csv",
    "CO-EST2025-HU.xlsx": f"{POPEST}/tables/2020-2025/housing/totals/CO-EST2025-HU.xlsx",
}


# ---------------------------------------------------------------------------
# Fetch (skip if cached)
# ---------------------------------------------------------------------------

def raw_path(name: str) -> Path:
    """County files 2015-2025 already cached by the foundation build are reused in place."""
    cached = COUNTY_CACHE / name
    if name.startswith("co") and name.endswith("a.txt") and cached.exists():
        return cached
    return D / name


def fetch(force: bool = False) -> None:
    D.mkdir(parents=True, exist_ok=True)
    log_path = D / "_downloads.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    for name, url in URLS.items():
        p = raw_path(name)
        if p.exists() and not force:
            continue
        p = D / name
        req = urllib.request.Request(url, headers={"User-Agent": "missing-middleware research (public records)"})
        data = urllib.request.urlopen(req, timeout=120).read()
        p.write_bytes(data)
        log[name] = {"accessed": dt.date.today().isoformat(), "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest(), "url": url}
        print(f"fetched {name} ({len(data):,} bytes)")
    log_path.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.lower().replace(".", "").split())


def read_delineation() -> pd.DataFrame:
    """Metro CBSAs and their counties, July 2023 OMB delineation (as used by PEP Vintage 2025)."""
    df = pd.read_csv(raw_path("cbsa-est2025-alldata.csv"), dtype=str, encoding="latin1")
    metros = df[(df["LSAD"] == "Metropolitan Statistical Area")][["CBSA", "NAME"]].rename(
        columns={"CBSA": "cbsa", "NAME": "cbsa_name"})
    cos = df[df["LSAD"] == "County or equivalent"][["CBSA", "STCOU", "NAME"]].rename(
        columns={"CBSA": "cbsa", "STCOU": "fips", "NAME": "county_name"})
    return cos.merge(metros, on="cbsa", how="inner")


def name_to_fips() -> dict[str, str]:
    """'county, state' (normalised) -> 5-digit FIPS, from the Vintage 2020 housing file."""
    hu = pd.read_csv(raw_path("HU-EST2020_ALL.csv"), dtype=str, encoding="latin1")
    hu = hu[hu["SUMLEV"] == "050"]
    return {_norm(f"{c}, {s}"): st + co for c, s, st, co in zip(hu["CTYNAME"], hu["STNAME"], hu["STATE"], hu["COUNTY"])}


def read_census2020_pop(names: dict[str, str]) -> pd.Series:
    """2020 Census count by county (the intercensal table's 'April 1, 2020 Census' column)."""
    rows = parsers.read_xlsx_first_sheet(raw_path("co-est2020int-pop.xlsx"))
    hdr = next(r for r in rows if r and "April 1, 2020 Census" in [str(x) for x in r])
    col = [str(x) for x in hdr].index("April 1, 2020 Census")
    out = {}
    for r in rows:
        if r and isinstance(r[0], str) and r[0].startswith(".") and len(r) > col and isinstance(r[col], float):
            f = names.get(_norm(r[0].lstrip(".")))
            if f:
                out[f] = r[col]
    return pd.Series(out, name="pop2020")


def read_housing_units(names: dict[str, str]) -> pd.DataFrame:
    """County housing units, July 1, 2000-2025: intercensal 2000-2009, Vintage 2020 for 2010-2019,
    Vintage 2025 for 2020-2025. Long form: fips, year, housing_units, hu_source."""
    out = []
    a = pd.read_csv(raw_path("hu-est00int-tot.csv"), dtype=str, encoding="latin1")
    a = a[a["SUMLEV"] == "050"]
    for y in range(2000, 2010):
        out.append(pd.DataFrame({"fips": a["STATE"] + a["COUNTY"], "year": y,
                                 "housing_units": pd.to_numeric(a[f"HUEST_{y}"]),
                                 "hu_source": "PEP 2000-2010 intercensal (hu-est00int-tot)"}))
    b = pd.read_csv(raw_path("HU-EST2020_ALL.csv"), dtype=str, encoding="latin1")
    b = b[b["SUMLEV"] == "050"]
    for y in range(2010, 2020):
        out.append(pd.DataFrame({"fips": b["STATE"] + b["COUNTY"], "year": y,
                                 "housing_units": pd.to_numeric(b[f"HUESTIMATE{y}"]),
                                 "hu_source": "PEP Vintage 2020 (HU-EST2020_ALL)"}))
    rows = parsers.read_xlsx_first_sheet(raw_path("CO-EST2025-HU.xlsx"))
    yr = next(r for r in rows if len(r) > 3 and isinstance(r[2], float) and 2000 < r[2] < 2100)
    ycols = {i: int(v) for i, v in enumerate(yr) if isinstance(v, float) and 2000 < v < 2100}
    recs = []
    for r in rows:
        if r and isinstance(r[0], str) and r[0].startswith("."):
            f = names.get(_norm(r[0].lstrip(".")))
            if not f:
                continue  # Connecticut planning regions (not used) and nothing else in the universe
            for i, y in ycols.items():
                if i < len(r) and isinstance(r[i], float):
                    recs.append({"fips": f, "year": y, "housing_units": r[i],
                                 "hu_source": "PEP Vintage 2025 (CO-EST2025-HU)"})
    out.append(pd.DataFrame(recs))
    return pd.concat(out, ignore_index=True)


def read_bps_5plus() -> pd.DataFrame:
    """County units in 5+ unit buildings by year, 2000-2025 (BPS, with imputation)."""
    out = []
    for y in YEARS:
        df = parsers.read_bps(raw_path(f"co{y}a.txt"), "county", state_fips=None)
        out.append(pd.DataFrame({"fips": df["state_fips"] + df["county_fips"], "year": y,
                                 "units_5plus": df["5plus_units"], "units_total": df["units_total"]}))
    return pd.concat(out, ignore_index=True)


def read_bps_cbsa(year: int) -> pd.DataFrame:
    df = pd.read_csv(raw_path(f"cbsa{year}a.txt"), skiprows=3, header=None, dtype=str, encoding="latin1")
    return pd.DataFrame({"cbsa": df[2].str.strip(), "units_5plus_published": pd.to_numeric(df[15])})


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_panel() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    deli = read_delineation()
    names = name_to_fips()
    notes = {}
    ct = deli["fips"].str[:2] == "09"
    notes["ct_metros_dropped"] = sorted(deli.loc[ct, "cbsa_name"].unique())
    deli = deli[~deli["cbsa"].isin(deli.loc[ct, "cbsa"])]
    pop = read_census2020_pop(names)
    deli["pop2020"] = deli["fips"].map(pop)
    miss = deli[deli["pop2020"].isna()]
    if len(miss):
        raise SystemExit(f"2020 Census population missing for: {miss[['fips', 'county_name']].values.tolist()}")
    mpop = deli.groupby(["cbsa", "cbsa_name"], as_index=False)["pop2020"].sum()
    uni = mpop[(mpop["pop2020"] >= POP_MIN) & (mpop["pop2020"] <= POP_MAX)]
    deli = deli[deli["cbsa"].isin(uni["cbsa"])]

    for label, (code, cos) in METROS.items():
        got = set(deli.loc[deli["cbsa"] == code, "fips"])
        if got != set(cos):
            raise SystemExit(f"{label}: delineation counties {sorted(got)} differ from {sorted(cos)}")

    hu = read_housing_units(names)
    bps = read_bps_5plus()
    grid = deli[["cbsa", "cbsa_name", "fips"]].merge(pd.DataFrame({"year": YEARS}), how="cross")
    grid = grid.merge(hu, on=["fips", "year"], how="left").merge(bps, on=["fips", "year"], how="left")
    gaps_hu = grid[grid["housing_units"].isna()]
    if len(gaps_hu):
        raise SystemExit(f"housing units missing: {gaps_hu[['fips', 'year']].head(20).values.tolist()}")
    gaps_bps = grid[grid["units_5plus"].isna()]
    notes["county_years_absent_from_bps"] = gaps_bps[["fips", "year"]].values.tolist()
    grid["units_5plus"] = grid["units_5plus"].fillna(0.0)  # absent from the file = no permits reported
    panel = grid.groupby(["cbsa", "cbsa_name", "year"], as_index=False).agg(
        n_counties=("fips", "size"), units_5plus=("units_5plus", "sum"),
        housing_units=("housing_units", "sum"), hu_source=("hu_source", "first"))
    panel["rate_5plus_per_1000"] = 1000.0 * panel["units_5plus"] / panel["housing_units"]
    panel = panel.merge(uni[["cbsa", "pop2020"]], on="cbsa")

    # Cross-check: county-built metro totals against the published BPS CBSA files, 2024-2025.
    xc = []
    for y in (2024, 2025):
        pub = read_bps_cbsa(y)
        m = panel[panel["year"] == y].merge(pub, on="cbsa", how="left")
        m["diff"] = m["units_5plus"] - m["units_5plus_published"]
        xc.append(m)
    xc = pd.concat(xc)
    notes["cbsa_crosscheck_n"] = int(xc["units_5plus_published"].notna().sum())
    notes["cbsa_crosscheck_exact"] = int((xc["diff"].abs() < 0.5).sum())
    notes["cbsa_crosscheck_max_abs_diff"] = float(xc["diff"].abs().max())
    return panel, uni, notes


def model_additions() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Metro additions by scenario and year, plus a reconciliation with the statewide file."""
    c = pd.read_csv(REFERENCE / "tod_model_per_acre_by_county.csv")
    s = pd.read_csv(REFERENCE / "tod_model_per_acre_statewide.csv")
    c = c[(c["method"] == "A") & c["scenario"].isin(SCENARIOS)]
    long = c.melt(id_vars=["county", "scenario", "baseline_near_central_2027_2031"],
                  value_vars=[f"add_y{i}" for i in range(1, 6)], var_name="k", value_name="addition")
    long["year"] = long["k"].str[-1].astype(int) + 2026
    state = long.groupby(["scenario", "year"], as_index=False)["addition"].sum()
    sw = s[(s["method"] == "A") & s["year"].astype(str).isin([str(y) for y in MODEL_YEARS])].copy()
    sw["year"] = sw["year"].astype(int)
    rec = state.merge(sw[["scenario", "year", "addition"]], on=["scenario", "year"], suffixes=("_counties", "_statewide"))
    rec["diff"] = rec["addition_counties"] - rec["addition_statewide"]
    if rec["diff"].abs().max() > 0.01:
        raise SystemExit(f"county additions do not add up to the statewide file:\n{rec}")
    rows = []
    for label, (code, cos) in METROS.items():
        names = set(cos.values())
        m = long[long["county"].isin(names)].groupby(["scenario", "year"], as_index=False)["addition"].sum()
        base = c[c["county"].isin(names) & (c["scenario"] == "typical")]["baseline_near_central_2027_2031"].sum()
        m["metro"], m["cbsa"], m["near_stop_baseline_2027_2031"] = label, code, base
        rows.append(m)
    met = pd.concat(rows, ignore_index=True).merge(rec[["scenario", "year", "addition_statewide"]], on=["scenario", "year"])
    return met, rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--force", action="store_true", help="re-download every raw file")
    a = ap.parse_args()
    fetch(a.force)
    panel, uni, notes = build_panel()
    b = S.benchmarks(panel)
    met, rec = model_additions()

    out = []
    unit = "units in 5+ unit buildings permitted per 1,000 existing housing units (July 1), per year"
    top10 = panel.sort_values("rate_5plus_per_1000", ascending=False).head(10)
    out.append(dict(kind="benchmark", statistic="observed_max_peer_metro_year", metro=b.observed_max_metro,
                    year=b.observed_max_year, value=b.observed_max, unit=unit,
                    permits_5plus_units=float(top10.iloc[0]["units_5plus"]),
                    housing_units=float(top10.iloc[0]["housing_units"]),
                    note=f"highest of {b.n_metro_years} metro-years ({b.n_metros} metros x 2000-2025)"))
    out.append(dict(kind="benchmark", statistic="p95_peer_metro_years", value=b.p95, unit=unit,
                    note=f"95th percentile (linear interpolation) of {b.n_metro_years} metro-years"))
    out.append(dict(kind="benchmark", statistic="median_peer_metro_years",
                    value=float(panel["rate_5plus_per_1000"].median()), unit=unit,
                    note=f"median of {b.n_metro_years} metro-years"))
    for i, r in enumerate(top10.itertuples(), 1):
        out.append(dict(kind="benchmark", statistic=f"top10_rank_{i}", metro=r.cbsa_name, year=r.year,
                        value=r.rate_5plus_per_1000, permits_5plus_units=r.units_5plus,
                        housing_units=r.housing_units, unit=unit))

    hist = {}
    for label, (code, _) in METROS.items():
        s = panel[panel["cbsa"] == code].sort_values("year")
        h = S.own_history(s, RECENT)
        h["hu"] = float(s.loc[s["year"] == HU_YEAR, "housing_units"].iloc[0])
        h["name"] = s["cbsa_name"].iloc[0]
        h["recent_5plus_mean_units"] = float(s[s["year"].isin(RECENT)]["units_5plus"].mean())
        h["rank_of_peer_max"] = int((panel["rate_5plus_per_1000"] > h["own_max"]).sum()) + 1
        hist[label] = h
        out.append(dict(kind="metro_history", statistic="own_max", metro=h["name"], year=h["own_max_year"],
                        value=h["own_max"], unit=unit,
                        permits_5plus_units=float(s.loc[s["year"] == h["own_max_year"], "units_5plus"].iloc[0]),
                        housing_units=float(s.loc[s["year"] == h["own_max_year"], "housing_units"].iloc[0])))
        out.append(dict(kind="metro_history", statistic="recent_mean_2021_2025", metro=h["name"], value=h["recent_mean"],
                        unit=unit, permits_5plus_units=h["recent_5plus_mean_units"],
                        note="mean of the five yearly rates 2021-2025; permits column is the mean yearly count"))
        for r in s.itertuples():
            out.append(dict(kind="metro_history", statistic="year", metro=h["name"], year=r.year,
                            value=r.rate_5plus_per_1000, permits_5plus_units=r.units_5plus,
                            housing_units=r.housing_units, unit=unit))

    for r in met.itertuples():
        h = hist[r.metro]
        chk = S.scenario_check(r.addition, h["hu"], h["recent_mean"], b.observed_max, b.p95, h["own_max"])
        out.append(dict(kind="scenario", statistic="year", method="A", scenario=r.scenario, metro=h["name"], year=r.year,
                        addition_homes=r.addition, addition_statewide_homes=r.addition_statewide,
                        metro_share_of_statewide=(r.addition / r.addition_statewide if r.addition_statewide else np.nan),
                        housing_units=h["hu"], housing_units_year=HU_YEAR, **chk,
                        baseline_source="metro observed 5+ rate, mean of 2021-2025 yearly rates (BPS / PEP)",
                        model_near_stop_baseline_per_1000=S.per_1000(r.near_stop_baseline_2027_2031 / 5, h["hu"]),
                        observed_max=b.observed_max, p95=b.p95, own_max=h["own_max"], unit=unit,
                        note="addition treated as 5+ unit apartment permits"))
    df = pd.DataFrame(out)
    df["year"] = df["year"].astype("Int64")
    sc = df[df["kind"] == "scenario"]
    peak = sc.loc[sc.groupby(["scenario", "metro"])["extra_per_1000"].idxmax()].copy()
    peak["statistic"] = "peak_year"
    df = pd.concat([df, peak], ignore_index=True)
    order = ["kind", "statistic", "method", "scenario", "metro", "year", "value", "addition_homes",
             "addition_statewide_homes", "metro_share_of_statewide", "permits_5plus_units", "housing_units",
             "housing_units_year", "extra_per_1000", "baseline_per_1000", "total_per_1000",
             "exceeds_observed_max", "exceeds_p95", "exceeds_own_max", "observed_max", "p95", "own_max",
             "model_near_stop_baseline_per_1000", "baseline_source", "unit", "note"]
    df = df[order]
    for col in ("year", "housing_units_year"):
        df[col] = df[col].astype("Int64")
    df.round(4).to_csv(REFERENCE / "tod_scale_check.csv", index=False)
    pc = panel[["cbsa", "cbsa_name", "pop2020", "year", "n_counties", "units_5plus", "housing_units",
                "rate_5plus_per_1000", "hu_source"]].sort_values(["cbsa", "year"])
    pc.round(4).to_csv(REFERENCE / "tod_scale_check_metro_years.csv", index=False)

    # Console summary
    print(f"\nUniverse: {b.n_metros} metros (2020 Census pop {POP_MIN:,}-{POP_MAX:,}, 2023 delineation, CT dropped: "
          f"{notes['ct_metros_dropped']}), years {YEARS[0]}-{YEARS[-1]}")
    print(f"County-years absent from BPS (set to 0): {notes['county_years_absent_from_bps']}")
    print(f"CBSA cross-check 2024-2025: {notes['cbsa_crosscheck_exact']}/{notes['cbsa_crosscheck_n']} exact, "
          f"max abs diff {notes['cbsa_crosscheck_max_abs_diff']:.0f} units")
    print(f"Max: {b.observed_max_metro} {b.observed_max_year}: {b.observed_max:.2f}; p95 {b.p95:.2f}")
    print(top10[["cbsa_name", "year", "units_5plus", "housing_units", "rate_5plus_per_1000"]].to_string(index=False))
    for k, h in hist.items():
        print(f"{k}: own max {h['own_max']:.2f} ({h['own_max_year']}, rank {h['rank_of_peer_max']}), "
              f"recent mean {h['recent_mean']:.2f}, mean units {h['recent_5plus_mean_units']:.0f}, HU2025 {h['hu']:,.0f}")
    print(peak[["scenario", "metro", "year", "addition_homes", "metro_share_of_statewide", "extra_per_1000",
                "baseline_per_1000", "total_per_1000", "exceeds_observed_max", "exceeds_p95", "exceeds_own_max",
                "model_near_stop_baseline_per_1000"]].round(2).to_string(index=False))
    flags = sc.groupby(["scenario", "metro"]).apply(
        lambda g: pd.Series({"years_gt_max": list(g.loc[g["exceeds_observed_max"], "year"]),
                             "years_gt_p95": list(g.loc[g["exceeds_p95"], "year"]),
                             "years_gt_own": list(g.loc[g["exceeds_own_max"], "year"])}), include_groups=False)
    print(flags.to_string())
    share = met.groupby(["metro", "scenario"]).agg(a=("addition", "sum"), s=("addition_statewide", "sum"))
    print((share["a"] / share["s"]).round(4).to_string())


if __name__ == "__main__":
    main()

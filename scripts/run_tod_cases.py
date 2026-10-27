"""Measure the TOD comparison cases (docs/tod/CASE_ANALYSIS_PLAN.md) from the raw files fetched by
scripts/fetch_tod_cases.py.

    uv run --all-extras python scripts/run_tod_cases.py [--case charlotte nyc stpaul chicago]

Writes (committed, no parcel, permit or project identifiers):
- reference/tod_case_rates_by_year.csv: case, area, year, period, units, eligible_acres, rate, status
- reference/tod_case_estimates.csv: one row per case: estimate (difference-in-differences, units per eligible acre
  per year), 90% project-bootstrap interval, dose (added FAR), effect per dose, sensitivities, parking change,
  mandate, city median gross rent (ACS 2020-2024, from reference/tod_cases.csv), role
Diagnostics (not committed): data/processed/tod_cases/diagnostics.json

Held-out cases (Chicago) get their own estimate but never enter fit_set() or the pooled ramp.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import REFERENCE, processed_dir  # noqa: E402
from missing_middleware.tod import cases as C  # noqa: E402


def builders(selected: list[str]):
    out = []
    if "charlotte" in selected:
        from missing_middleware.tod import case_charlotte
        out.append(("charlotte_tod_2019", case_charlotte.build))
    if "stpaul" in selected:
        from missing_middleware.tod import case_stpaul
        out.append(("stpaul_green_line_2011", case_stpaul.build))
    if "nyc" in selected:
        from missing_middleware.tod import case_nyc
        for c in case_nyc.CASES:
            out.append((c, lambda c=c: case_nyc.build(c)))
    if "nyc_pooled" in selected:
        from missing_middleware.tod import case_nyc
        out.append(("nyc_pooled_2003_2013", case_nyc.build_pooled))
    if "philadelphia" in selected:
        from missing_middleware.tod import case_philadelphia
        out.append(("philadelphia_2012_remapping", case_philadelphia.build))
    if "raleigh" in selected:
        from missing_middleware.tod import case_raleigh
        out.append(("raleigh_tod_2021", case_raleigh.build))
    if "phoenix" in selected:
        from missing_middleware.tod import case_phoenix
        out.append(("phoenix_walkable_urban_code_2015", case_phoenix.build))
    if "annarbor" in selected:
        from missing_middleware.tod import case_annarbor
        out.append(("annarbor_tc1_2021", case_annarbor.build))
    if "raleigh_counts" in selected:
        from missing_middleware.tod import case_raleigh
        out.append(("raleigh_permit_count", case_raleigh.build_counts))
    if "phoenix_counts" in selected:
        from missing_middleware.tod import case_phoenix
        out.append(("phoenix_permit_count", case_phoenix.build_counts))
    if "annarbor_counts" in selected:
        from missing_middleware.tod import case_annarbor
        out.append(("annarbor_permit_count", case_annarbor.build_counts))
    if "chicago" in selected:
        from missing_middleware.tod import case_chicago
        out.append(("chicago_tod_2013_2015", case_chicago.build))
    return out


def bps_units(state: str, county: str, years) -> dict:
    """Total units authorized (1, 2, 3-4, 5+ unit buildings) for one county from the Census BPS annual files."""
    from missing_middleware.paths import RAW
    out = {}
    for y in years:
        for d in (RAW / "tod_cases" / "bps_county", RAW / "census_bps_county"):
            f = d / f"co{y}a.txt"
            if f.exists():
                for line in f.read_text(errors="replace").splitlines()[2:]:
                    c = line.split(",")
                    if len(c) > 16 and c[1].strip() == state and c[2].strip() == county:
                        out[y] = sum(int(float(c[i] or 0)) for i in (7, 10, 13, 16))
                break
    return out


def permit_file_checks() -> dict:
    """Yearly totals of the city permit files against the Census Building Permits Survey (county)."""
    out = {}
    try:
        from missing_middleware.tod import case_nyc
        j = case_nyc.load_jobs("BK")
        dob = j.groupby(j["year"].astype(int))["units"].sum()
        yrs = range(1996, 2011)
        bps = bps_units("36", "047", yrs)
        out["kings_dob_vs_bps"] = {y: {"dob_units": int(dob.get(y, 0)), "bps_units": bps.get(y)} for y in yrs}
    except Exception as e:  # noqa: BLE001
        out["kings_dob_vs_bps"] = f"{type(e).__name__}: {e}"
    try:
        from missing_middleware.tod import case_charlotte
        p = case_charlotte.load_permits()
        tot = p.groupby(p["year"].astype(int))["units"].sum()
        yrs = range(2010, 2025)
        bps = bps_units("37", "119", yrs)
        out["mecklenburg_permits_vs_bps"] = {y: {"permit_file_units": int(tot.get(y, 0)), "bps_units": bps.get(y)} for y in yrs}
    except Exception as e:  # noqa: BLE001
        out["mecklenburg_permits_vs_bps"] = f"{type(e).__name__}: {e}"
    try:
        from missing_middleware.paths import RAW
        from missing_middleware.tod import case_philadelphia
        pp = pd.read_csv(RAW / "tod_cases" / "philadelphia" / "permits_new_construction.csv", dtype=str).drop_duplicates("permitnumber")
        pp = pp[pp["typeofwork"].isin(case_philadelphia.WHOLE_BUILDING)]
        pp["units"] = pd.to_numeric(pp["numberofunits"], errors="coerce").fillna(0)
        pp = pp[pp["units"] > 0].dropna(subset=["lat", "lon"])
        import geopandas as gpd
        g = gpd.GeoSeries(gpd.points_from_xy(pp["lon"].astype(float), pp["lat"].astype(float)), crs=4326).to_crs(case_philadelphia.CRS_M)
        pp["x"], pp["y"], pp["issue_date"] = g.x.values, g.y.values, pp["permitissuedate"]
        from missing_middleware.tod.case_chicago import dedupe_staged
        pp = dedupe_staged(pp)
        tot = pp.groupby(pd.to_numeric(pp["permitissuedate"].str[:4], errors="coerce"))["units"].sum()
        yrs = range(2007, 2025)
        bps = bps_units("42", "101", yrs)
        out["philadelphia_permits_vs_bps"] = {y: {"permit_file_units": int(tot.get(y, 0)), "bps_units": bps.get(y)} for y in yrs}
    except Exception as e:  # noqa: BLE001
        out["philadelphia_permits_vs_bps"] = f"{type(e).__name__}: {e}"
    try:
        from missing_middleware.paths import RAW
        from missing_middleware.tod import case_chicago
        import geopandas as gpd
        cp = pd.read_csv(RAW / "tod_cases" / "chicago" / "permits_new_construction.csv", dtype=str).drop_duplicates("permit_")
        cp["units"] = cp["work_description"].map(case_chicago.parse_units)
        cp = cp[(cp["units"] > 0)].dropna(subset=["latitude", "longitude"])
        g = gpd.GeoSeries(gpd.points_from_xy(cp["longitude"].astype(float), cp["latitude"].astype(float)), crs=4326).to_crs(case_chicago.CRS_M)
        cp["x"], cp["y"] = g.x.values, g.y.values
        cp = case_chicago.dedupe_staged(cp)
        tot = cp.groupby(cp["issue_date"].str[:4].astype(int))["units"].sum()
        bps = {}
        for y in range(2012, 2025):
            f = RAW / "census_bps_place_us" / f"mw{y}a.txt"
            if f.exists():
                for line in f.read_text(errors="replace").splitlines()[2:]:
                    c = line.split(",")
                    if len(c) > 27 and c[1].strip() == "17" and c[16].strip() == "Chicago":
                        bps[y] = sum(int(float(c[i] or 0)) for i in (18, 21, 24, 27))
        out["chicago_parsed_vs_bps"] = {y: {"parsed_units": int(tot.get(y, 0)), "bps_units": bps.get(y)} for y in range(2006, 2025)}
    except Exception as e:  # noqa: BLE001
        out["chicago_parsed_vs_bps"] = f"{type(e).__name__}: {e}"
    return out


def median_rent(case: str) -> float | None:
    inv = pd.read_csv(REFERENCE / "tod_cases.csv", dtype=str)
    key = {"nyc_pooled_2003_2013": "nyc_bloomberg_rezonings_2003_2013", "philadelphia_2012_remapping": "philadelphia_2012_code",
           "raleigh_tod_2021": "raleigh_new_bern_2024", "raleigh_permit_count": "raleigh_new_bern_2024",
           "phoenix_permit_count": "phoenix_walkable_urban_code_2015", "annarbor_permit_count": "annarbor_tc1_2021"}.get(case, case)
    r = inv[inv["case_id"] == key]
    return float(r["median_gross_rent_usd_per_month"].iloc[0]) if len(r) else None


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--case", nargs="*", default=["charlotte", "stpaul", "nyc", "nyc_pooled", "philadelphia", "raleigh",
                                                   "phoenix", "chicago", "annarbor", "raleigh_counts", "phoenix_counts",
                                                   "annarbor_counts"])
    a = ap.parse_args(argv)
    rates_all, rows, events, diags = [], [], [], {}
    for case, fn in builders(a.case):
        print(f"== {case}")
        try:
            built = fn()
        except Exception as e:  # noqa: BLE001 - partial results are fine; record why
            traceback.print_exc()
            diags[case] = {"error": f"{type(e).__name__}: {e}"}
            continue
        built = built if isinstance(built, list) else [built]
        for ci, diag in built:
            ci.median_rent = median_rent(case)
            rates, row = C.estimate_case(ci)
            rates_all.append(rates)
            rows.append(row)
            diags[ci.case] = diag
            print({k: row[k] for k in ("case", "status", "estimate_units_per_acre_yr", "interval90_low", "interval90_high")})
    if not rows:
        print("no case built")
        return
    rates = pd.concat(rates_all, ignore_index=True)
    rates["units"] = rates["units"].round(0).astype(int)
    rates["eligible_acres"] = rates["eligible_acres"].round(1)
    rates["rate"] = rates["rate"].round(5)
    rates = rates[["case", "area", "year", "period", "units", "eligible_acres", "rate", "status"]]
    est = pd.DataFrame(rows)
    # merge with existing outputs so a single-case run keeps the others
    rp, ep = REFERENCE / "tod_case_rates_by_year.csv", REFERENCE / "tod_case_estimates.csv"
    if rp.exists() and ep.exists():
        old_r, old_e = pd.read_csv(rp), pd.read_csv(ep)
        rates = pd.concat([old_r[~old_r["case"].isin(est["case"])], rates], ignore_index=True)
        est = pd.concat([old_e[~old_e["case"].isin(est["case"])], est], ignore_index=True)
    order = ["charlotte_tod_2019", "stpaul_green_line_2011", "nyc_park_slope_fourth_ave_2003", "nyc_downtown_brooklyn_2004",
             "nyc_pooled_2003_2013", "philadelphia_2012_remapping", "raleigh_tod_2021", "phoenix_walkable_urban_code_2015",
             "chicago_tod_2013_2015", "annarbor_tc1_2021", "raleigh_permit_count_all", "raleigh_permit_count_sf",
             "raleigh_permit_count_mf", "phoenix_permit_count_all", "phoenix_permit_count_sf", "phoenix_permit_count_mf",
             "annarbor_permit_count_all"]
    est["_o"] = est["case"].map({c: i for i, c in enumerate(order)}).fillna(99)
    est = est.sort_values("_o").drop(columns="_o")
    rates["_o"] = rates["case"].map({c: i for i, c in enumerate(order)}).fillna(99)
    rates = rates.sort_values(["_o", "area", "year"]).drop(columns="_o")
    rates.to_csv(rp, index=False)
    est.to_csv(ep, index=False)
    out = processed_dir("tod_cases")
    summary = C.fit_set_summary(est)
    for r in est.itertuples(index=False):
        if not isinstance(r.before_years, str) or not r.before_years:
            continue
        b0, b1 = (int(x) for x in r.before_years.split(" to "))
        rr = rates[(rates["case"] == r.case) & rates["area"].isin([C.TREAT, C.COMP])]
        if rr.empty or not str(r.status).startswith("measured"):
            continue
        ev = C.event_years(rr, int(r.effective_year), list(range(b0, b1 + 1)))
        ev.insert(0, "case", r.case)
        ev["gap_per_dose"] = ev["gap_minus_before"] / r.dose_added_far if r.dose_added_far else float("nan")
        events.append(ev)
    ev_all = pd.concat(events, ignore_index=True) if events else pd.DataFrame()
    ramp = C.pooled_ramp(ev_all, est) if events else pd.DataFrame()
    if events:
        fit_cases = set(C.fit_set(est)["case"])
        e = ev_all[ev_all["case"].isin(fit_cases) & ev_all["event_year"].between(0, 5)]
        diags["_pooled_ramp_per_dose_fit_set"] = e.groupby("event_year")["gap_per_dose"].agg(["mean", "count"]).reset_index().to_dict(orient="records")
        diags["_event_years_all_cases"] = ev_all.round(4).to_dict(orient="records")
    diags["_fit_set"] = summary
    f = C.fit_set(est)
    no_cut = f["parking_change"].astype(str).str.startswith("none")
    diags["_fit_set_by_parking"] = {
        "without_parking_cuts": C.fit_set_summary(est[est["case"].isin(f.loc[no_cut, "case"])]),
        "with_parking_cuts": C.fit_set_summary(est[est["case"].isin(f.loc[~no_cut, "case"])])}
    diags["_fit_set_rent_vs_effect"] = f[["case", "median_rent", "effect_per_dose"]].to_dict(orient="records")
    diags["_permit_file_checks"] = permit_file_checks()
    diags["_pooled_ramp_fit_set"] = ramp.to_dict(orient="records")
    old = json.loads((out / "diagnostics.json").read_text()) if (out / "diagnostics.json").exists() else {}
    old.update(diags)
    (out / "diagnostics.json").write_text(json.dumps(old, indent=1, default=str) + "\n")
    print(f"wrote {rp.relative_to(REFERENCE.parent)} ({len(rates)} rows), {ep.relative_to(REFERENCE.parent)} ({len(est)} rows)")
    print("fit set:", summary)


if __name__ == "__main__":
    main()

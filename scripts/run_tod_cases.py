"""Measure the TOD comparison cases (docs/tod/CASE_ANALYSIS_PLAN.md) from the raw files fetched by
scripts/fetch_tod_cases.py.

    uv run --all-extras python scripts/run_tod_cases.py [--case charlotte nyc stpaul chicago]

Writes (committed, no parcel, permit or project identifiers):
- reference/tod_case_rates_by_year.csv: case, area, year, period, units, eligible_acres, rate, status
- reference/tod_case_units.csv: the added cities (plan section 7, 2026-10-27) split into trait-test units (station
  areas or district subareas), following missing_middleware/tod/traits.py
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
    # added cities (plan section 7, 2026-10-27): batch 1 (this work package) and batch 2 (separate adapters, registered
    # when their files exist). An adapter has either CASES and build(case), or build() alone.
    for key in ADDED:
        if key in selected:
            out += added_builders(key)
    # batch 2 (built in a separate work package; registered here)
    if "toronto" in selected:
        from missing_middleware.tod import case_toronto
        out.append(("toronto_eglinton_2014", toronto_context))
    if "ottawa" in selected:
        from missing_middleware.tod import case_ottawa
        out.append(("ottawa_td_zone_2012", case_ottawa.build))
    if "minneapolis" in selected:
        from missing_middleware.tod import case_minneapolis
        out.append(("minneapolis_hiawatha_2008_2012", case_minneapolis.build))
    return out


def toronto_context():
    """Toronto is context only (plan section 7, 2026-10-27): its treatment lots exclude the later site-specific
    rezonings where the Eglinton projects stand, so the strict treatment has no homes before or after. Both versions
    are reported: as built, and with the adjacent lots rezoned later (columns sens_toronto_with_rezoned_lots_*)."""
    from missing_middleware.tod import case_toronto
    ci, diag = case_toronto.build()
    ci.role = "context"
    ci.status_override = "context_only: treatment lots exclude the later site-specific rezonings where the Eglinton projects stand"
    s2 = diag.get("sens_with_later_rezoned_eglinton_lots") or {}
    ci.extra.update({f"sens_toronto_with_rezoned_lots_{k}": v for k, v in s2.items() if isinstance(v, (int, float))})
    ci.extra["sens_toronto_as_built_did"] = round(float(C.did(ci.permits, ci.acres, *(lambda p: (p["before"], p["after"]))(
        C.period_years(ci.effective_year, ci.first_year, ci.last_full_year)))["did"]), 4)
    return ci, diag


ADDED = ("la", "seattle", "bellevue")
BATCH2 = ("toronto", "ottawa", "minneapolis")


def _module(key: str):
    import importlib
    import importlib.util
    name = f"missing_middleware.tod.case_{key}"
    if importlib.util.find_spec(name) is None:
        print(f"(no adapter yet for {key})")
        return None
    return importlib.import_module(name)


def added_builders(key: str) -> list:
    m = _module(key)
    if m is None:
        return []
    if hasattr(m, "CASES"):
        return [(c, (lambda c=c, m=m: m.build(c))) for c in m.CASES]
    return [(getattr(m, "CASE_ID", getattr(m, "CASE", key)), m.build)]


def added_unit_frames(selected: list[str]) -> list:
    """(case id, unit_frame dict) for the added cities whose adapters provide unit_frame()."""
    out = []
    for key in ADDED:
        if key not in selected:
            continue
        m = _module(key)
        if m is None or not hasattr(m, "unit_frame"):
            continue
        cases = list(m.CASES) if hasattr(m, "CASES") else [getattr(m, "CASE_ID", getattr(m, "CASE", key))]
        for c in cases:
            try:
                out.append((c, m.unit_frame(c) if hasattr(m, "CASES") else m.unit_frame()))
            except Exception as e:  # noqa: BLE001
                print(f"unit frame {c}: {type(e).__name__}: {e}")
    return out


def toronto_unit_frame() -> dict:
    """Trait-test units for Toronto (station areas by nearest TTC station), from the adapter's own parcels and
    permits; flagged and kept out of the trait-test fit (plan section 7, 2026-10-27)."""
    import zipfile

    import geopandas as gpd
    from missing_middleware.tod import case_toronto as K
    from missing_middleware.tod import traits as T
    rec = []
    orig = C.uniform_areas

    def cap(parcels, *a, **k):
        r = orig(parcels, *a, **k)
        rec.append(parcels)
        return r
    C.uniform_areas = cap
    try:
        ci, _ = K.build()
    finally:
        C.uniform_areas = orig
    parcels = rec[0]
    with zipfile.ZipFile(K.DIR / "ttc_gtfs.zip") as z:
        st = pd.read_csv(z.open("stops.txt"), dtype=str)
    st = st[st["location_type"] == "1"].reset_index(drop=True)
    g = gpd.GeoDataFrame({"stop_name": st["stop_name"]}, geometry=gpd.points_from_xy(st["stop_lon"].astype(float), st["stop_lat"].astype(float)),
                         crs=4326).to_crs(K.CRS_M)
    stations = T.cluster_stations(g, g["stop_name"])
    tr = parcels.index[parcels["area"] == C.TREAT]
    parcels["unit_label"] = None
    parcels.loc[tr, "unit_label"] = T.nearest_station(parcels.loc[tr].geometry.representative_point(), stations).values
    parcels["old_level"], parcels["new_level"] = parcels["h_before"], parcels["h_after"]
    p = ci.permits.copy()
    p["pix"] = p["project"].str.split(":").str[-1].astype(int)
    return {"parcels": parcels, "permits": p, "per": C.period_years(ci.effective_year, ci.first_year, ci.last_full_year),
            "effective_year": ci.effective_year, "dose_unit": "added height (ft)", "unit_type": "station area",
            "trait_fit": False, "flag": "kept out of the trait-test fit: treatment excludes the later site-specific rezonings (plan section 7)"}


def unit_rows(case: str, uf: dict) -> list[dict]:
    """Trait-test units for one case (station areas or district subareas), following missing_middleware/tod/traits.py
    and scripts/run_tod_traits.py: each unit's eligible treatment lots against the case's comparison lots within 1/4
    mile of them; kept with at least 5 eligible acres in each; DiD and 90% interval by the case rules."""
    import numpy as np
    from missing_middleware.tod import traits as T
    parcels, permits, per = uf["parcels"], uf["permits"], uf["per"]
    el = parcels["eligible"].astype(bool)
    tr = parcels.index[(parcels["area"] == C.TREAT) & el]
    cp = parcels.index[(parcels["area"] == C.COMP) & el]
    acres = parcels.geometry.area / C.SQM_PER_ACRE
    labels = parcels["unit_label"].reindex(tr)
    b, a = per["before"], per["after"]
    rows = []
    for lab in sorted(labels.dropna().astype(str).unique()):
        ti = labels.index[labels.astype(str) == lab]
        ci = T.comparison_for_unit(parcels, ti, cp)
        pu = permits[((permits["area"] == C.TREAT) & permits["pix"].isin(ti)) | ((permits["area"] == C.COMP) & permits["pix"].isin(ci))]
        pu = pu[["project", "area", "year", "units"]]
        ac = {C.TREAT: float(acres[ti].sum()), C.COMP: float(acres[ci].sum())}
        ok, reason = T.keep_unit(ac[C.TREAT], ac[C.COMP])
        e = T.unit_estimate(pu, ac, b, a) if ok else T.unit_estimate(pu, ac, [], [])
        du = uf.get("dose_unit", "none")
        d = np.nan
        if du and not str(du).startswith("none") and "old_level" in parcels and "new_level" in parcels:
            sub = pd.DataFrame({"acres": acres[ti], "old_far": parcels["old_level"].reindex(ti), "new_far": parcels["new_level"].reindex(ti)})
            d = C.dose(sub.replace([np.inf, -np.inf], np.nan))
        fmt = (lambda y: f"{y[0]} to {y[-1]}" if y else "")
        rows.append({"case": case, "unit_name": lab, "unit_type": uf.get("unit_type", "station area or district"),
                     "effective_year": uf.get("effective_year"), "before_years": fmt(b), "after_years": fmt(a),
                     "treatment_acres": round(ac[C.TREAT], 2), "comparison_acres": round(ac[C.COMP], 2), "kept": ok, "reason": reason,
                     "effect": e["did"], "interval90_low": e["low"], "interval90_high": e["high"],
                     "treatment_units_before": T.units_in(pu, C.TREAT, b), "treatment_units_after": T.units_in(pu, C.TREAT, a),
                     "comparison_units_before": T.units_in(pu, C.COMP, b), "comparison_units_after": T.units_in(pu, C.COMP, a),
                     "dose": d, "dose_unit": du, "trait_fit": uf.get("trait_fit", True), "flag": uf.get("flag", "")})
    return rows


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
                                                   "annarbor_counts", *ADDED, *BATCH2])
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
             "annarbor_permit_count_all", "la_warner_center_2013", "la_cornfield_arroyo_seco_2013", "seattle_nbh_othello_2012",
             "seattle_mount_baker_2014", "bellevue_belred_2009", "toronto_eglinton_2014", "ottawa_td_zone_2012",
             "minneapolis_hiawatha_2008_2012"]
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
    ufs = added_unit_frames(a.case)
    if "toronto" in a.case:
        try:
            ufs.append(("toronto_eglinton_2014", toronto_unit_frame()))
        except Exception as e:  # noqa: BLE001
            print(f"toronto units: {type(e).__name__}: {e}")
    if ufs:
        up = REFERENCE / "tod_case_units.csv"
        new_rows = pd.DataFrame([r for c, uf in ufs for r in unit_rows(c, uf)])
        if up.exists():
            old_u = pd.read_csv(up)
            new_rows = pd.concat([old_u[~old_u["case"].isin([c for c, _ in ufs])], new_rows], ignore_index=True)
        for col in ("effect", "interval90_low", "interval90_high", "dose"):
            new_rows[col] = pd.to_numeric(new_rows[col], errors="coerce").round(4)
        new_rows.to_csv(up, index=False)
        print(f"wrote {up.relative_to(REFERENCE.parent)} ({len(new_rows)} units)")
    print("fit set:", summary)


if __name__ == "__main__":
    main()

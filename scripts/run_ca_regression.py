"""Market-adjusted California regression and Wisconsin per-area y (Gate 3 revision, AQ-034).

Inputs: the California study panel (scripts/run_ca_study.py), CA ACS denominators
(scripts/build_ca_comparison_data.py), Wisconsin engine areas (scripts/build_wi_baseline.py),
and four ACS 2020-2024 5-year market tables (B25077, B25064, B19013, B25003), downloaded
keylessly into data/raw/census_acs5_2024_tbsf_market/ on first run.

Outputs (committed, small aggregates): reference/ca_regression_*.csv and
reference/wi_y_by_area.csv. Processed detail: data/processed/ca_regression/.
Run: uv run python scripts/run_ca_regression.py [--skip-fetch] [--n-boot N]
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_regression as cr
from missing_middleware.model import engine as e
from missing_middleware.model.params import madison_floor
from missing_middleware.paths import PROCESSED, REFERENCE, processed_dir, raw_dir

MAIN = "group_value_hinge_size"
ALT_FORMS = ("group_value_size", "group_value_income_size", "group_only")
FLOOR = madison_floor()               # Madison floor (AQ-024), applied by the engine; set in adu_model_params.json
RAMP = (0.10, 0.53, 0.58, 0.85, 1.0)  # California restrictive-group ramp, capped at 1 (as run)
RAMPS = {
    "restrictive (as run)": RAMP,
    "middle-group increment share (as-run upper)": (0.24, 0.54, 0.77, 0.89, 1.0),
    "Central Valley after 2017 (G3-3 slower)": (0.12, 0.19, 0.25, 0.55, 1.0),
    "no ramp": (1.0, 1.0, 1.0, 1.0, 1.0),
}
MADISON = "muni:5502548000"
MAPPINGS = {"v1_state_relative": "state_relative", "a_absolute": "absolute", "b_relative": "relative",
            "c_rules": "rules"}
RECOMMENDED = "v1_state_relative"   # owner decision G3-6 (2026-10-24); a, b, c are sensitivities
# Ramps by path (owner accepted G3-3): lower = the slower Central Valley ramp after 2017, held at or
# below the central ramp in every year so paths stay ordered (year 1: 0.10 instead of 0.12);
# central = California restrictive group; upper = middle-group increment share (as run).
PATH_RAMPS = {"lower": (0.10, 0.19, 0.25, 0.55, 1.0), "central": RAMP, "upper": (0.24, 0.54, 0.77, 0.89, 1.0)}
LA, SD = "0644000", "0666000"

# Benchmark adoption years (owner input 2026-10-24). Default 2020 (the 2020 package).
ADOPTION = [
    {"census_geoid": LA, "name": "Los Angeles", "adoption_year": 2017, "status": "documented",
     "basis": "City's second-unit ordinance became null and void on 2017-01-01 (SB 1069/AB 2299); the City applied "
              "the state default standards: ministerial approval, no owner-occupancy requirement, parking waived "
              "within 1/2 mile of transit (most of the city). City's own ordinance came later. Permits 80 (2016) -> "
              "2,342 (2017).",
     "sources": "LA City Planning ADU information sheet (rev. Jan 2017), planning.lacity.gov/ordinances/docs/ADU/"
                "InformationSheet.pdf; Sightline Institute 2019-04-05, sightline.org/2019/04/05/la-adu-story-how-a-"
                "state-law-sent-granny-flats-off-the-charts/"},
    {"census_geoid": SD, "name": "San Diego", "adoption_year": 2020, "status": "source_lead_partial",
     "basis": "Council approved companion-unit amendments to comply with state law in 2017 and waived several ADU "
              "fees around 2018 (resolution R-311730, superseded 2022); owner-occupancy and parking terms of the "
              "2017 rules not verified, so not coded near-benchmark. Permits rose most from 2020-2023 (local ADU "
              "bonus program). Sensitivity: adoption 2018.",
     "sources": "sandiego.gov/sites/default/files/pc-17-043.pdf; sandiego.gov/sites/default/files/R-314270.pdf "
                "(2022 resolution citing R-311730); Bisnow, 'One Step Toward Defusing San Diego's Housing Crisis'"},
    {"census_geoid": "0668000", "name": "San Jose", "adoption_year": 2020, "status": "documented_not_benchmark",
     "basis": "Local ADU amendments effective 2018-07-27 widened districts but kept one parking space unless "
              "exempt; not near-benchmark, so default 2020.",
     "sources": "sanjoseca.gov ADU ordinance updates page; SPUR letter 2018-06-19"},
    {"census_geoid": "*", "name": "all other jurisdictions", "adoption_year": 2020, "status": "undocumented_default",
     "basis": "No local near-benchmark adoption before the 2020 package documented; default 2020.", "sources": ""},
]


def load_inputs(skip_fetch: bool):
    folder = raw_dir(cr.MARKET_SOURCE_ID)
    if skip_fetch:
        paths = {t: folder / f"acsdt5y2024-{t}.dat" for t in cr.MARKET_TABLES}
    else:
        paths = cr.fetch_market_tables(folder)
    mca = cr.read_market(paths, "06", ("050", "160"))
    mwi = cr.read_market(paths, "55", ("050", "060"))
    den = pd.read_parquet(PROCESSED / "comparison_ca/ca_denominators_acs2024.parquet")
    county_of = pd.Series(("06" + den["county_fips"]).values, index=den["geoid"].values)
    panel = pd.read_parquet(PROCESSED / "comparison_ca/study/study_panel.parquet")
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id", "context_group"]]
    return paths, mca, mwi, county_of, panel, areas, growth, geo


def engine_total(areas, growth, y, ramp=RAMP, floor=FLOOR, path="central") -> float:
    lv = pd.DataFrame({"area_id": areas["area_id"].values, f"y_{path}": y})
    sc = e.Scenario("ca_regression", {path: e.PathParams(level=0.0, floor_rate=floor, spillover=0.0, ramp=tuple(ramp))})
    return float(e.run(areas, sc, growth, area_levels=lv)["additional_units"].sum())


def fast_totals(areas, growth, Y, ramp=RAMP, floor=FLOOR) -> np.ndarray:
    """Vectorised engine formula for many y columns (areas x draws); checked against engine.run."""
    H = areas["homes"].to_numpy(float)[:, None]
    x = areas["x_rate"].to_numpy(float)[:, None]
    g = {(r.area_id, int(r.year)): float(r.g) for r in growth.itertuples()}
    y = np.maximum(np.maximum(Y, floor), x)
    tot = np.zeros(Y.shape[1])
    for i, t in enumerate(e.YEARS):
        gt = np.array([g.get((a, t), 1.0) for a in areas["area_id"]])[:, None]
        tot += (H * np.maximum(y - x * gt, 0.0) * ramp[i] / 1000).sum(axis=0)
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-fetch", action="store_true")
    ap.add_argument("--n-boot", type=int, default=cr.N_BOOT)
    args = ap.parse_args()
    paths, mca, mwi, county_of, panel, areas, growth, geo = load_inputs(args.skip_fetch)
    od = processed_dir("ca_regression")
    man = json.loads((raw_dir(cr.MARKET_SOURCE_ID) / "_downloads.json").read_text())

    # ---------------- California dataset ----------------
    d = cr.build_ca_dataset(panel, mca, county_of)
    d_all = d.copy()
    d = d[d["rent"].notna() & d["value"].notna() & d["income"].notna()].reset_index(drop=True)
    n_drop = len(d_all) - len(d)
    d.to_parquet(od / "ca_dataset.parquet", index=False)
    cols = ["census_geoid", "name", "juris_type", "group", "pre_rate", "homes", "n_years", "adu", "rate",
            "value", "rent", "income", "renter_share", "market_basis", "filled", "value_topcoded", "rent_topcoded"]
    d[cols].round(4).to_csv(REFERENCE / "ca_regression_ca_jurisdictions.csv", index=False)

    # ---------------- fits, CV, bootstrap ----------------
    fits = {s.name: cr.fit(d, s) for s in cr.SPECS}
    preds, cv = cr.cross_validate(d)
    preds.to_parquet(od / "cv_predictions.parquet", index=False)
    cv.round(4).to_csv(REFERENCE / "ca_regression_cv.csv", index=False)
    main_spec = cr.SPEC_BY_NAME[MAIN]
    draws = cr.bootstrap_betas(d, main_spec, n_boot=args.n_boot)
    coef = []
    for s in cr.SPECS:
        dr = draws if s.name == MAIN else cr.bootstrap_betas(d, s, n_boot=min(args.n_boot, 300))
        t = cr.plain_language(fits[s.name], dr)
        t["dispersion"] = fits[s.name].dispersion
        coef.append(t)

    # ---------------- Wisconsin inputs ----------------
    w = cr.wi_market(areas, mwi)
    w = w.merge(areas[["area_id", "x_rate", "rights_basis", "at_benchmark"]], on="area_id").merge(geo, on="area_id", how="left")
    # rule v1: state-relative activity groups from Wisconsin's own 2022-2025 observations
    wobs = cr.wi_observations_2022_2025(REFERENCE)
    wgrp = cr.state_relative_groups(wobs)
    wgrp.round(4).to_csv(REFERENCE / "ca_regression_wi_activity_groups.csv", index=False)
    gmap = dict(zip("muni:" + wgrp["jurisdiction"], wgrp["group"]))
    w["activity_group"] = w["area_id"].map(gmap).fillna("restrictive")   # unmeasured -> restrictive
    w["activity_measured"] = w["area_id"].isin(set("muni:" + wgrp.loc[wgrp["measured"], "jurisdiction"]))
    w["zoning_status"] = cr.load_zoning_status(REFERENCE, w["area_id"]).values
    w["group"] = cr.wi_group(w, "state_relative").values
    # the same rule reproduces California's published groups (non-holdout, 2017-2019)
    s_nh = cr.panel_series(panel[~panel["in_holdout"]])
    pre = s_nh[s_nh["year"].isin(cr.WAVE3_PRE)].groupby("census_geoid").agg(
        permits=("adu", "sum"), years=("adu", "count"), homes=("homes", "first"))
    pre["measured"] = pre["years"].eq(3)
    ca_v1 = cr.state_relative_groups(pre.reset_index().rename(columns={"census_geoid": "jurisdiction"}))
    pub = cr.jurisdiction_groups(s_nh, cr.WAVE3_PRE, cr.published_cutoff(panel, cr.WAVE3_PRE))["group"].map(cr.GROUP_NAMES).fillna("excluded")
    cmp_ = ca_v1.set_index("jurisdiction").join(pub.rename("published"))
    cmp_ = cmp_[cmp_["measured"]]
    ca_rule_check = {"cutoff": float(ca_v1["cutoff"].iloc[0]),
                     "agree": int((cmp_["group"] == cmp_["published"]).sum()), "n": int(len(cmp_))}
    flags = cr.extrapolation_flags(w, d)
    w = pd.concat([w, flags], axis=1)
    assert (w["area_id"].values == areas["area_id"].values).all()

    # main prediction and bootstrap paths, for each Wisconsin group mapping
    def make_paths(rule):
        wm = w.assign(group=cr.wi_group(w, rule).values)
        yc = fits[MAIN].predict_rate(wm)
        Yb = cr.predict_draws(wm, main_spec, draws)
        tb = fast_totals(areas, growth, Yb)
        assert abs(fast_totals(areas, growth, yc[:, None])[0] - engine_total(areas, growth, yc)) < 1e-6, \
            "fast_totals disagrees with engine"
        qlo, qhi = np.percentile(tb, [2.5, 97.5])
        jlo, jhi = int(np.argmin(np.abs(tb - qlo))), int(np.argmin(np.abs(tb - qhi)))
        # one coherent statewide draw per path; keep per-area ordering where a draw crosses the point
        ylo, yhi = np.minimum(Yb[:, jlo], yc), np.maximum(Yb[:, jhi], yc)
        sc = e.Scenario("ca_regression", {p: e.PathParams(level=0.0, floor_rate=FLOOR, spillover=0.0, ramp=PATH_RAMPS[p])
                                           for p in e.PATHS},
                        {"lower": f"{MAIN} ({rule}), bootstrap 2.5% statewide draw",
                         "central": f"{MAIN} ({rule}), point prediction",
                         "upper": f"{MAIN} ({rule}), bootstrap 97.5% statewide draw"})
        lv = pd.DataFrame({"area_id": w["area_id"], "y_lower": ylo, "y_central": yc, "y_upper": yhi})
        o = e.run(areas, sc, growth, area_levels=lv)
        probs = e.check_invariants(o)
        if probs:
            raise SystemExit(f"invariant failures ({rule}): {probs}")
        return {"group": wm["group"].values, "y_c": yc, "y_lo": ylo, "y_hi": yhi, "out": o,
                "state": e.five_year_totals(o), "q": (qlo, qhi)}

    P = {rule: make_paths(rule) for rule in MAPPINGS.values()}
    R = P[MAPPINGS[RECOMMENDED]]
    w["group"] = R["group"]
    y_c, y_lo, y_hi, out, state = R["y_c"], R["y_lo"], R["y_hi"], R["out"], R["state"]
    q_lo, q_hi = R["q"]
    out.to_parquet(od / "results_long.parquet", index=False)
    out_g = out.merge(geo[["area_id", "context_group"]], on="area_id")
    by_ctx = e.five_year_totals(out_g, ["context_group"])
    by_ctx.round(1).to_csv(REFERENCE / "ca_regression_wi_by_context.csv", index=False)
    mrows = []
    for key, rule in MAPPINGS.items():
        st_ = P[rule]["state"].set_index("path")["additional_units"]
        mad = w["area_id"].eq(MADISON).to_numpy()
        mo = P[rule]["out"]
        mrows.append({"mapping": key, "rule": rule, "lower": st_["lower"], "central": st_["central"], "upper": st_["upper"],
                      "madison_y_lower": P[rule]["y_lo"][mad][0], "madison_y_central": P[rule]["y_c"][mad][0],
                      "madison_y_upper": P[rule]["y_hi"][mad][0],
                      "madison_additional_central": mo[(mo.area_id == MADISON) & (mo.path == "central")].additional_units.sum(),
                      "areas_active": int((P[rule]["group"] == "active").sum()),
                      "areas_middle": int((P[rule]["group"] == "middle").sum()),
                      "active_places": "; ".join(sorted(set(w.loc[P[rule]["group"] == "active", "name"].dropna()))),
                      "middle_places": "; ".join(sorted(set(w.loc[P[rule]["group"] == "middle", "name"].dropna()))),
                      "recommended": key == RECOMMENDED})
    pd.DataFrame(mrows).round(3).to_csv(REFERENCE / "ca_regression_wi_mappings.csv", index=False)

    # ---------------- alternatives and sensitivities (central path) ----------------
    sens = []

    def add(kind, label, y=None, total=None, ramp=RAMP, floor=FLOOR, note=""):
        if total is None:
            total = engine_total(areas, growth, y, ramp=ramp, floor=floor)
        hw = float(np.average(np.maximum(np.maximum(y, floor), w["x_rate"]), weights=w["homes"])) if y is not None else np.nan
        mad = float(y[w["area_id"].eq(MADISON).to_numpy()][0]) if y is not None else np.nan
        sens.append({"kind": kind, "variant": label, "five_year_additional": round(total, 1),
                     "homes_weighted_y_after_floor": round(hw, 3), "madison_y": round(mad, 3), "note": note})

    add("main", f"central: {MAIN}", y_c)
    add("main", "lower: bootstrap 2.5% statewide draw", y_lo, total=float(state.loc[state.path == "lower", "additional_units"].item()))
    add("main", "upper: bootstrap 97.5% statewide draw", y_hi, total=float(state.loc[state.path == "upper", "additional_units"].item()))
    for name in ALT_FORMS:
        add("functional_form", name, fits[name].predict_rate(w))
    for s in cr.SPECS:
        if s.name not in ALT_FORMS and s.name != MAIN:
            add("other_spec", s.name, fits[s.name].predict_rate(w))
    # extrapolation: clamp Wisconsin values to the California range (no extrapolation below it)
    for lab, clamp in (("clamp value at CA minimum", d["value"].min()), ("clamp value at CA 5th percentile", d["value"].quantile(0.05))):
        add("extrapolation", lab, fits[MAIN].predict_rate(w.assign(value=w["value"].clip(lower=clamp))),
            note=f"clamp ${clamp:,.0f}")
    # knot sensitivity
    for knot in (500_000.0, 600_000.0, 800_000.0):
        old = cr.VALUE_KNOT
        cr.VALUE_KNOT = knot
        f_k = cr.fit(d, main_spec)
        add("knot", f"knot at ${knot/1000:.0f}k", f_k.predict_rate(w))
        cr.VALUE_KNOT = old
    # fitted only on the lower-value half of California
    low = d[d["value"] <= 700_000]
    add("sample", "group_value_size fitted on CA places valued <= $700k", cr.fit(low, cr.SPEC_BY_NAME["group_value_size"]).predict_rate(w))
    add("sample", f"{MAIN} without Los Angeles", cr.fit(d[d.census_geoid != LA], main_spec).predict_rate(w))
    add("sample", f"{MAIN} without county remainders (county-proxy market values)",
        cr.fit(d[d.market_basis.eq("place")], main_spec).predict_rate(w))
    lanc = d["name"].eq("Lancaster")
    add("sample", f"{MAIN} without Lancaster (post hoc)", cr.fit(d[~lanc], main_spec).predict_rate(w))
    d_issue = cr.build_ca_dataset(panel, mca, county_of, measure="adu_issue")
    d_issue = d_issue[d_issue[["value", "rent", "income"]].notna().all(axis=1)]
    add("measure", f"{MAIN}, HCD issue-year measure", cr.fit(d_issue, main_spec).predict_rate(w))
    # group mapping
    for rule in ("state_relative", "state_relative_unmeasured_middle", "absolute", "relative", "rules", "unmeasured_middle", "rules_unmeasured_middle",
                 "all_restrictive", "all_middle"):
        add("group_mapping", f"Wisconsin group mapping: {rule}", fits[MAIN].predict_rate(w.assign(group=cr.wi_group(w, rule).values)))
    # floor and ramp
    add("floor", "no Madison floor (regression y alone)", y_c, floor=0.0)
    for lab, rp in RAMPS.items():
        if lab != "restrictive (as run)":
            add("ramp", f"ramp: {lab}", y_c, ramp=rp)

    # ---------------- event-time model ----------------
    adopt = pd.Series({r["census_geoid"]: r["adoption_year"] for r in ADOPTION if r["census_geoid"] != "*"})
    pd.DataFrame(ADOPTION).to_csv(REFERENCE / "ca_regression_adoption_years.csv", index=False)
    d_ev = cr.build_ca_dataset(panel, mca, county_of, adoption=adopt)
    d_ev = d_ev[d_ev[["value", "rent", "income"]].notna().all(axis=1)].reset_index(drop=True)
    f_ev = cr.fit(d_ev, main_spec)
    t = cr.plain_language(f_ev, cr.bootstrap_betas(d_ev, main_spec, n_boot=min(args.n_boot, 300)))
    t["spec"] = MAIN + "__event_time"
    t["dispersion"] = f_ev.dispersion
    coef.append(t)
    y_ev = f_ev.predict_rate(w)
    add("event_time", f"{MAIN}, event-time plateau (LA adopts 2017)", y_ev)
    _, cv_ev = cr.cross_validate(d_ev, specs=(cr.SPEC_BY_NAME["group_only"], main_spec))
    cv_ev["spec"] = cv_ev["spec"] + "__event_time"
    adopt_sd = adopt.copy()
    adopt_sd[SD] = 2018
    d_sd = cr.build_ca_dataset(panel, mca, county_of, adoption=adopt_sd)
    d_sd = d_sd[d_sd[["value", "rent", "income"]].notna().all(axis=1)]
    add("event_time", f"{MAIN}, event-time plateau (LA 2017, San Diego 2018)", cr.fit(d_sd, main_spec).predict_rate(w))
    pd.concat([cv, cv_ev]).round(4).to_csv(REFERENCE / "ca_regression_cv.csv", index=False)

    # event-time curves and the active group's early rise
    s_all = cr.panel_series(panel)
    ev = cr.adoption_events(s_all, adopt)
    grp_cal = cr.jurisdiction_groups(s_all, cr.WAVE3_PRE, cr.published_cutoff(panel, cr.WAVE3_PRE))["group"].map(cr.GROUP_NAMES)
    grp_ev = cr.event_groups(s_all, adopt, cr.published_cutoff(panel, cr.WAVE3_PRE), cr.published_cutoff(panel, cr.WAVE1_PRE)).map(cr.GROUP_NAMES)
    rows = []
    for clock, grp, tcol in (("calendar (k = year - 2019)", grp_cal, None), ("event time", grp_ev, "k")):
        z = ev.assign(group=ev["census_geoid"].map(grp)).dropna(subset=["adu", "group"])
        z["t"] = z["year"] - 2019 if tcol is None else z["k"]
        for (g, k), q in z.groupby(["group", "t"]):
            if -2 <= k <= 9:
                rows.append({"clock": clock, "group": g, "k": int(k), "jurisdictions": q["census_geoid"].nunique(),
                             "adu": q["adu"].sum(), "homes": q["homes"].sum(),
                             "rate": q["adu"].sum() / q["homes"].sum() * 1000})
    evt = pd.DataFrame(rows)
    evt.round(4).to_csv(REFERENCE / "ca_regression_event_time.csv", index=False)
    act = s_all[s_all["census_geoid"].map(grp_cal).eq("active") & s_all["year"].isin(cr.WAVE3_PRE)].dropna(subset=["adu"])
    early = {"active_2017_2019_permits": act["adu"].sum(),
             "la_share": act.loc[act.census_geoid.eq(LA), "adu"].sum() / act["adu"].sum(),
             "sd_share": act.loc[act.census_geoid.eq(SD), "adu"].sum() / act["adu"].sum(),
             "active_rate_2017_2019": act["adu"].sum() / act.groupby("year")["homes"].sum().sum() * 1000}
    a2 = act[~act.census_geoid.isin([LA])]
    early["active_rate_2017_2019_without_la"] = a2["adu"].sum() / a2.groupby("year")["homes"].sum().sum() * 1000

    # ---------------- industry-formation check (owner experience, AQ-034 follow-up) ----------------
    ind = []
    for excl in ((), (LA,)):
        z = s_all[~s_all.census_geoid.isin(excl)].assign(group=s_all["census_geoid"].map(grp_cal)).dropna(subset=["adu", "group"])
        for g, q in z.groupby("group"):
            rate = q.groupby("year").apply(lambda u: u["adu"].sum() / u["homes"].sum() * 1000)
            for yr, v in rate.items():
                ind.append({"sample": "without Los Angeles" if excl else "all", "group": g, "year": int(yr), "rate": v,
                            "change_from_prior_year": v - rate.get(yr - 1, np.nan)})
    ind = pd.DataFrame(ind)
    ind.round(4).to_csv(REFERENCE / "ca_regression_industry_check.csv", index=False)
    ind_s = (ind.assign(window=np.select([ind.year.between(2017, 2019), ind.year.between(2021, 2025)],
                                         ["2017-2019 (yearly change)", "2021-2025 (yearly change)"], ""))
             .query("window != ''").groupby(["sample", "group", "window"])["change_from_prior_year"].mean().unstack())

    # ---------------- ramp by market ----------------
    rr = []
    s_m = s_all.assign(group=s_all["census_geoid"].map(grp_cal),
                       value=s_all["census_geoid"].map(d.set_index("census_geoid")["value"]))
    s_m = s_m.dropna(subset=["adu", "group", "value"])
    s_m["market"] = np.where(s_m["value"] <= 700_000, "value <= $700k", "value > $700k")
    for (g, mkt), q in s_m.groupby(["group", "market"]):
        rate = q.groupby("year").apply(lambda z: z["adu"].sum() / z["homes"].sum() * 1000)
        pre = rate.loc[list(cr.WAVE3_PRE)].mean()
        plat = rate.loc[list(cr.PLATEAU_YEARS)].mean()
        for k, yr in enumerate(range(2020, 2026), start=1):
            rr.append({"group": g, "market": mkt, "jurisdictions": q["census_geoid"].nunique(), "year_k": k,
                       "rate": rate.get(yr), "increment_share": (rate.get(yr) - pre) / (plat - pre) if plat != pre else np.nan,
                       "pre_rate": pre, "plateau": plat})
    pd.DataFrame(rr).round(4).to_csv(REFERENCE / "ca_regression_ramp_by_market.csv", index=False)

    # ---------------- write outputs ----------------
    pd.concat(coef).round(5).to_csv(REFERENCE / "ca_regression_coefficients.csv", index=False)
    sens_df = pd.DataFrame(sens)
    sens_df.to_csv(REFERENCE / "ca_regression_sensitivities.csv", index=False)
    st = state.copy()
    st["as_run_additional"] = st["path"].map({"lower": 884.3, "central": 6519.0, "upper": 23276.3})
    st["bootstrap_total_at_central_ramp"] = st["path"].map({"lower": q_lo, "central": np.nan, "upper": q_hi})
    st.round(1).to_csv(REFERENCE / "ca_regression_wi_statewide.csv", index=False)

    wi = pd.DataFrame({
        "area_id": w["area_id"], "name": w["name"], "county_id": w["parent_county_id"], "context_group": w["context_group"],
        "homes": w["homes"], "x_rate": w["x_rate"].round(4), "rights_basis": w["rights_basis"], "ca_group": w["group"],
        "median_value": w["value"], "value_basis": w["value_basis"], "median_rent": w["rent"], "rent_basis": w["rent_basis"],
        "median_income": w["income"], "extrapolation": w["extrapolation"],
        "y_lower": np.round(y_lo, 4), "y_central": np.round(y_c, 4), "y_upper": np.round(y_hi, 4),
        "y_engine_central": np.round(np.maximum(np.maximum(y_c, FLOOR), w["x_rate"]), 4),
        "y_alt_single_slope": np.round(fits["group_value_size"].predict_rate(w), 4),
        "y_alt_price_income": np.round(fits["group_value_income_size"].predict_rate(w), 4),
        "y_event_time": np.round(y_ev, 4),
        **{f"y_{k}_{p}": np.round(P[r][f"y_{q}"], 4) for k, r in MAPPINGS.items()
           for p, q in (("lower", "lo"), ("central", "c"), ("upper", "hi"))},
        "ca_group_a_absolute": P["absolute"]["group"], "ca_group_b_relative": P["relative"]["group"],
        "ca_group_c_rules": P["rules"]["group"], "ca_group_v1_state_relative": P["state_relative"]["group"],
        "zoning_status": w["zoning_status"],
        "model": MAIN,
    })
    wi.to_csv(REFERENCE / "wi_y_by_area.csv", index=False)

    # extrapolation summary
    ext = w.groupby("extrapolation").agg(areas=("area_id", "count"), homes=("homes", "sum")).reset_index()
    add_c = out[out.path == "central"].groupby("area_id")["additional_units"].sum()
    ext["central_additional"] = w.groupby("extrapolation")["area_id"].apply(lambda a: add_c.reindex(a).sum()).values
    ext.round(1).to_csv(REFERENCE / "ca_regression_extrapolation.csv", index=False)

    zs = w.assign(central_additional=w["area_id"].map(add_c)).groupby("zoning_status").agg(
        areas=("area_id", "count"), homes=("homes", "sum"), central_additional=("central_additional", "sum"))
    zoning_summary = zs.round(1).reset_index().to_dict("records")
    summary = {
        "n_ca": len(d), "n_ca_dropped_missing_market": n_drop, "groups": d["group"].value_counts().to_dict(),
        "market_basis": d["market_basis"].value_counts().to_dict(), "filled": d["filled"].value_counts().to_dict(),
        "ca_value_range": [float(d.value.min()), float(d.value.quantile(.05)), float(d.value.median()), float(d.value.max())],
        "ca_rent_range": [float(d.rent.min()), float(d.rent.quantile(.05)), float(d.rent.median())],
        "wi_value_hw": float(np.average(w.value, weights=w.homes)), "wi_rent_hw": float(np.average(w.rent, weights=w.homes)),
        "ca_value_hw": float(np.average(d.value, weights=d.homes)),
        "wi_basis": {c: w[f"{c}_basis"].value_counts().to_dict() for c in ("value", "rent", "income")},
        "state": state.round(1).to_dict("records"), "bootstrap_q": [q_lo, q_hi],
        "madison": {"y_lower": float(y_lo[w.area_id.eq(MADISON)][0]), "y_central": float(y_c[w.area_id.eq(MADISON)][0]),
                    "y_upper": float(y_hi[w.area_id.eq(MADISON)][0]),
                    "additional_central": float(out[(out.area_id == MADISON) & (out.path == "central")].additional_units.sum())},
        "early_rise": early, "ca_rule_v1_check": ca_rule_check,
        "zoning": zoning_summary, "event_fit_rows": len(d_ev), "raw_manifest": man,
    }
    (od / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    pd.set_option("display.width", 250)
    print(json.dumps({k: v for k, v in summary.items() if k != "raw_manifest"}, indent=1, default=float))
    print(pd.concat(coef).round(3)[["spec", "term", "coef", "robust_se", "boot_lo", "boot_hi", "effect", "effect_lo", "effect_hi"]].to_string(index=False))
    print(cv.round(3).to_string(index=False))
    print(cv_ev.round(3).to_string(index=False))
    print(sens_df.to_string(index=False))
    print(ext.to_string(index=False))
    print(ind_s.round(3))
    print(pd.read_csv(REFERENCE / "ca_regression_wi_mappings.csv").to_string(index=False))
    print(by_ctx.round(0).to_string(index=False))


if __name__ == "__main__":
    main()

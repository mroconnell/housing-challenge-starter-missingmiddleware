"""Pooled multi-state regression and statewide adoption curve for Wisconsin (Gate 3 revision,
owner direction 2026-10-24). See docs/gate3/POOLED_MODEL.md.

Inputs (all local; run scripts/run_ca_regression.py and scripts/build_statewide_states.py first):
  data/processed/ca_regression/ca_dataset.parquet, data/processed/comparison_ca/study/study_panel.parquet,
  data/processed/model_baseline/engine_areas.parquet (+ engine_baseline_growth.parquet),
  reference/statewide_states_annual.csv, reference/other_cities_annual.csv, reference/wi_baseline_statewide.csv,
  ACS 2020-2024 5-year table-based summary files: data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25024.dat and
  data/raw/census_acs5_2024_tbsf_market/acsdt5y2024-{b25077,b19013,b25064,b25003}.dat,
  Census 2020 place-code files in data/raw/statewide_states/census_place_codes/.

Outputs: reference/statewide_adoption_curve.csv, reference/pooled_*.csv,
data/processed/pooled_regression/summary.json.
Run: uv run python scripts/run_pooled_regression.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_regression as cr
from missing_middleware.comparison import pooled_regression as pr
from missing_middleware.comparison import statewide_states as ss
from missing_middleware.model import engine as e
from missing_middleware.model.params import madison_floor
from missing_middleware.paths import PROCESSED, RAW, REFERENCE, processed_dir

MAIN = "p_value_income_size"   # chosen on leave-one-state-out (see main())
CODES = RAW / "statewide_states" / "census_place_codes"
PLACE_CODES = {"53": CODES / "st53_wa_place2020.txt", "41": CODES / "st41_or_place2020.txt"}
FLOOR = madison_floor()   # Madison floor (AQ-024); set once in reference/adu_model_params.json
CITY_PLACES = {"seattle": "5363000", "portland": "4159000", "austin": "4805000", "denver": "0820000",
               "minneapolis": "2743000", "madison": "5548000", "tucson": "0477000", "spokane": "5367000"}
STATE_PARENT = {"WA_inc_exSeattle": "53", "OR_panel32_exPortland": "41", "RI_statewide": "44", "MA_statewide": "25",
                "ME_statewide": "23", "UT_mih": "49", "VT_chittenden": "50007"}


def acs_paths():
    return {"b25024": RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25024.dat",
            **{t: RAW / cr.MARKET_SOURCE_ID / f"acsdt5y2024-{t}.dat" for t in ("b25077", "b19013", "b25064", "b25003")}}


def build_members(acs: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for sid, parent in STATE_PARENT.items():
        den = ss.SERIES[sid]["denominator"]
        if den[0] in ("state", "county"):
            m = pr.members_for(acs, "cousubs", den[1], parent)
        else:
            ids = [g.replace("1600000US", "") for g in ss.geo_ids_for(den, PLACE_CODES)]
            m = pr.members_for(acs, "places", ids, parent)
        parts.append(m.assign(group_id=sid))
    for city, g in CITY_PLACES.items():
        m = pr.members_for(acs, "places", [g], g[:2])
        parts.append(m.assign(group_id=f"place:{g}"))
    return pd.concat(parts, ignore_index=True)


def load():
    acs = pr.read_acs_members(acs_paths(), {"53", "41", "44", "25", "23", "49", "50", "48", "08", "27", "55", "04"})
    members = build_members(acs)
    annual = pd.read_csv(REFERENCE / "statewide_states_annual.csv")
    cities = pd.read_csv(REFERENCE / "other_cities_annual.csv")
    ca = pd.read_parquet(PROCESSED / "ca_regression/ca_dataset.parquet")
    panel = pd.read_parquet(PROCESSED / "comparison_ca/study/study_panel.parquet")
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    paths = {t: RAW / cr.MARKET_SOURCE_ID / f"acsdt5y2024-{t}.dat" for t in cr.MARKET_TABLES}
    mwi = cr.read_market(paths, "55", ("050", "060"))
    wm = cr.wi_market(areas, mwi)
    wi = areas.merge(wm.drop(columns=["homes"]), on="area_id")
    co = mwi[mwi.sumlevel.eq("050")].set_index("geoid")["renter_share"]
    miss = wi["renter_share"].isna()
    wi.loc[miss, "renter_share"] = wi.loc[miss, "geoid"].str[:5].map(co)
    wi["renter_share_basis"] = np.where(miss, "county_fallback", "cousub")
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id", "context_group"]]
    wi = wi.merge(geo, on="area_id", how="left")
    base = pd.read_csv(REFERENCE / "wi_baseline_statewide.csv")
    baseline = base[base["year"].isin([str(y) for y in range(2027, 2032)])]["central"].astype(float).to_numpy()
    return dict(acs=acs, members=members, annual=annual, cities=cities, ca=ca, panel=panel, areas=areas,
                growth=growth, wi=wi, baseline=baseline)


def pooled(d, city_measure="units_incl_new_house", la_event=False, ca_years=range(2020, 2026), ca_law_year=2020,
           state_coding=None):
    s = pr.state_rows(d["annual"], state_coding or pr.STATE_CODING)
    c = pr.city_rows(d["cities"], measure=city_measure)
    car, cam = pr.ca_rows(d["panel"], d["ca"], years=ca_years, law_year=ca_law_year, la_event=la_event)
    return pr.assemble([(s, d["members"]), (c, d["members"]), (car, cam)])


# ---------------------------------------------------------------------------
# Specification grid (owner direction: carry forward the California CV specs; LOSO is the judge)
# ---------------------------------------------------------------------------
K = ("law", "local", "k1", "k2", "k3")
LAW_STATES = ("CA", "WA", "OR", "RI", "MA", "ME", "UT", "VT")
WITHIN = {   # within-state forms, named after the California-only spec they carry forward
    "none": ((), "no within-state market terms"),
    "value": (("value_dev",), "group_value"),
    "value_size": (("value_dev", "log_homes"), "group_value_size"),
    "hinge_size": (("value_dev", "hinge", "log_homes"), "group_value_hinge_size (CA main)"),
    "value_income_size": (("value_dev", "income_dev", "log_homes"), "group_value_income_size (CA best CV)"),
    "value_income_size_renter": (("value_dev", "income_dev", "log_homes", "renter_share"), "+ renter share (B25003)"),
    "value_income_size_pre": (("value_dev", "income_dev", "log_homes", "pre_dev"), "+ pre-law activity (group analogue)"),
}
BETWEEN = {
    "common_level": (),
    "value": ("value_ctx",),
    "income": ("income_ctx",),
    "price_to_income": ("pti_ctx",),
    "value_income": ("value_ctx", "income_ctx"),
}
STAGE2 = {"law_states": LAW_STATES, "all_clusters": None}
MAIN_KEY = ("value_income_size", "common_level", "law_states", "calendar")
ALLOC_KEY = ("value", "common_level", "law_states", "calendar")


def tspec(w, b, s2):
    return pr.TSpec(f"ts|{w}|{b}|{s2}", WITHIN[w][0] + K, BETWEEN[b], ca_carry=WITHIN[w][1],
                    stage2_clusters=STAGE2[s2])


def wi_rates(f, wi):
    y = pr.predict_wi_ts(f, wi)
    H = wi["homes"].to_numpy(float)
    return y, np.array([(H * y[f"y_k{k}"]).sum() / H.sum() for k in range(1, 6)]), float((H * y["y_nolaw"]).sum() / H.sum())


def wi_additional(wi, y, baseline, growth):
    Y = y[[f"y_k{k}" for k in range(1, 6)]].to_numpy()
    gmap = {(r.area_id, int(r.year)): float(r.g) for r in growth.itertuples()}
    G = np.array([[gmap.get((a, t), 1.0) for t in e.YEARS] for a in wi["area_id"]])
    per_area = pr.additional(wi, Y, baseline, G, per_area_max=True)
    simple = pr.additional(wi, Y, baseline, per_area_max=False)
    return per_area, simple


def interval_factor(f, level=0.80):
    n = len(f.stage2)
    t = pr.T_QUANTILES[level][max(min(n - 1, 10), 3)]
    return float(np.exp(t * f.tau * np.sqrt(1 + 1 / n)))


def main():
    d = load()
    wi, base, growth = d["wi"], d["baseline"], d["growth"]
    H = wi["homes"].to_numpy(float)
    od = processed_dir("pooled_regression")
    summary = {"wi_homes": float(H.sum()), "baseline_by_year": base.round(2).tolist(), "baseline_5yr": float(base.sum())}

    # ---------------- data ----------------
    p = pooled(d)
    p_event = pooled(d, la_event=True)
    rows_out = pr.predict_rows_ts(pr.fit_two_stage(p, tspec("none", "common_level", "law_states")), p)
    rows_out["obs_rate"] = rows_out["count"] / (rows_out["years"] * rows_out["homes"]) * 1000
    nonca = rows_out[rows_out["cluster"].ne("CA")]
    ca_agg = (rows_out[rows_out["cluster"].eq("CA")].groupby("year")
              .agg(count=("count", "sum"), homes=("homes", "sum"), k=("k", "first"), n_jurisdictions=("count", "size"))
              .reset_index().assign(cluster="CA", series="CA_jurisdictions (sum of 457 grouped jurisdictions)", law=1, local=0))
    ca_agg["obs_rate"] = ca_agg["count"] / ca_agg["homes"] * 1000
    cols = ["cluster", "series", "year", "law", "local", "k", "count", "homes", "obs_rate", "incl_new_house", "coverage", "pre_rate"]
    pd.concat([nonca[cols], ca_agg.reindex(columns=cols + ["n_jurisdictions"])], ignore_index=True).round(4) \
        .to_csv(REFERENCE / "pooled_dataset_rows.csv", index=False)
    mem = d["members"]
    ms = mem.groupby("group_id").apply(lambda g: pd.Series(pr.homes_weighted_market(g)), include_groups=False).reset_index()
    ca = d["ca"]
    ms = pd.concat([ms, pd.DataFrame([{"group_id": "CA_jurisdictions", **pr.homes_weighted_market(
        ca.assign(filled=ca["filled"].fillna("")))}]),
        pd.DataFrame([{"group_id": "WI_areas", **pr.homes_weighted_market(wi.assign(filled=""))}])], ignore_index=True)
    ms.round(4).to_csv(REFERENCE / "pooled_members_summary.csv", index=False)
    summary["n_rows"] = int(len(p.rows))
    summary["n_rows_by_cluster"] = p.rows.groupby("cluster").size().to_dict()

    # ---------------- A. statewide adoption curve ----------------
    pts = pr.adoption_points(p.rows, p.row_homes())
    pts.round(4).to_csv(REFERENCE / "pooled_adoption_points.csv", index=False)
    pts_wa = pr.adoption_points(pooled(d, state_coding=WA_COMPLIANCE).rows, pooled(d, state_coding=WA_COMPLIANCE).row_homes())
    variants = {"as_reported": pr.adoption_curve(pts),
                "new_house_x0.8": pr.adoption_curve(pts, new_house=True),
                "coverage_adjusted": pr.adoption_curve(pts, coverage=True),
                "new_house_and_coverage": pr.adoption_curve(pts, new_house=True, coverage=True),
                "wa_by_compliance_date": pr.adoption_curve(pts_wa)}
    ca_ctx = ca_context(d["panel"])
    curve = variants["as_reported"].copy()
    curve.insert(1, "forecast_year", [2026 + k for k in curve["k"]])
    for name, v in variants.items():
        app = pr.apply_curve(v["median_rate"].to_numpy(), base)
        curve[f"rate_{name}"] = v["median_rate"].to_numpy()
        curve[f"with_law_total_{name}"] = app["with_law_total"].to_numpy()
        curve[f"additional_{name}"] = app["additional"].to_numpy()
    ch = pr.chain_curve(pts)
    app = pr.apply_curve(ch["chain_rate"].to_numpy(), base)
    curve["rate_chain_linked"] = ch["chain_rate"].to_numpy()
    curve["chain_ratio"] = ch["ratio"].to_numpy()
    curve["chain_n_states"] = ch["n_states_ratio"].to_numpy()
    curve["with_law_total_chain_linked"] = app["with_law_total"].to_numpy()
    curve["additional_chain_linked"] = app["additional"].to_numpy()
    summary_chain = {"rates": ch["chain_rate"].round(4).tolist(), "additional_5yr": float(app["additional"].sum()),
                     "with_law_total_5yr": float(app["with_law_total"].sum())}
    curve["baseline"] = base
    curve["ca_rate_k_from_2017_law"] = [ca_ctx.get(2016 + k) for k in curve["k"]]
    curve["ca_rate_k_from_2020_package"] = [ca_ctx.get(2019 + k) for k in curve["k"]]
    curve.round(4).to_csv(REFERENCE / "statewide_adoption_curve.csv", index=False)
    summary["A"] = {name: {"rates": variants[name]["median_rate"].round(4).tolist(),
                           "n_states": variants[name]["n_states"].tolist(),
                           "additional_5yr": float(pr.apply_curve(variants[name]["median_rate"].to_numpy(), base)["additional"].sum()),
                           "with_law_total_5yr": float(pr.apply_curve(variants[name]["median_rate"].to_numpy(), base)["with_law_total"].sum())}
                    for name in variants}
    summary["A"]["chain_linked"] = summary_chain

    # ---------------- B. specification grid with leave one state out ----------------
    grid, loso_all, fits = [], [], {}
    keys = [(w, b, s2, "calendar") for w in WITHIN for b in BETWEEN for s2 in STAGE2]
    keys += [(w, "common_level", s2, "event_time_LA2017") for w in ("hinge_size", "value_income_size") for s2 in STAGE2]
    for key in keys:
        w, b, s2, cal = key
        sp = tspec(w, b, s2)
        pp = p_event if cal.startswith("event") else p
        f = pr.fit_two_stage(pp, sp)
        lo = pr.loso_ts(pp, sp).assign(within=w, between=b, stage2=s2, calendar=cal)
        sm = pr.loso_summary(lo)
        _, rates, nolaw = wi_rates(f, wi)
        y, _, _ = wi_rates(f, wi)
        add_pa, add_s = wi_additional(wi, y, base, growth)
        grid.append(dict(within=w, carries=WITHIN[w][1], between=b, stage2=s2, calendar=cal, **sm, tau=f.tau,
                         **{f"wi_rate_k{k}": rates[k - 1] for k in range(1, 6)}, wi_rate_nolaw=nolaw,
                         wi_with_law_total_5yr=float((rates * H.sum() / 1000).sum()),
                         wi_additional_5yr=float(add_pa.sum()), wi_additional_5yr_simple=float(add_s.sum())))
        loso_all.append(lo)
        fits[key] = f
    # one-stage pooled fits (one shared value/income slope for within and between states)
    for sp in pr.PSPECS:
        if sp.name.startswith("p_ctx"):
            continue
        f1 = pr.fit_pooled(p, sp)
        lo = pr.loso(p, sp).assign(within=sp.name, between="one_stage_shared_slope", stage2="", calendar="calendar")
        sm = pr.loso_summary(lo)
        y1 = pr.predict_wi(f1, wi)
        rates = np.array([(H * y1[f"y_k{k}"]).sum() / H.sum() for k in range(1, 6)])
        add_pa, add_s = wi_additional(wi, y1, base, growth)
        grid.append(dict(within=sp.name, carries=sp.ca_carry or sp.label, between="one_stage_shared_slope", stage2="",
                         calendar="calendar", **sm, tau=np.nan,
                         **{f"wi_rate_k{k}": rates[k - 1] for k in range(1, 6)},
                         wi_rate_nolaw=float((H * y1["y_nolaw"]).sum() / H.sum()),
                         wi_with_law_total_5yr=float((rates * H.sum() / 1000).sum()),
                         wi_additional_5yr=float(add_pa.sum()), wi_additional_5yr_simple=float(add_s.sum())))
        loso_all.append(lo)
    grid = pd.DataFrame(grid)
    grid.round(4).to_csv(REFERENCE / "pooled_spec_comparison.csv", index=False)
    lo_all = pd.concat(loso_all, ignore_index=True)
    lo_all.round(4).to_csv(REFERENCE / "pooled_loso.csv", index=False)
    best = grid.sort_values("rms_log_error").iloc[0]
    summary["best_by_loso"] = best[["within", "between", "stage2", "calendar", "rms_log_error"]].to_dict()

    # ---------------- B. main fit ----------------
    f = fits[MAIN_KEY]
    coef = pd.DataFrame({"term": f.within_names, "estimate": f.beta, "se_cluster": f.se_within,
                         "rate_ratio": np.exp(f.beta), "stage": "1 within"})
    st2 = f.stage2.assign(term="state level (alpha)", stage="2 between")
    st2["level_with_law_k4"] = np.exp(st2["alpha"] + f.beta[f.within_names.index("law")])
    pd.concat([coef, st2], ignore_index=True).round(4).to_csv(REFERENCE / "pooled_coefficients.csv", index=False)
    y_raw, rates, nolaw = wi_rates(f, wi)
    # Allocation (secondary): the statewide rate by year comes from the main specification; it
    # is spread over areas with the gentler value-only within-state gradient, because the
    # California income gradient puts resort towns at 6-23 per 1,000 (pooled_wi_y_by_area.csv
    # keeps the raw main-spec values too).
    f_alloc = fits[ALLOC_KEY]
    y_v, rates_v, _ = wi_rates(f_alloc, wi)
    y = y_v.copy()
    for k in range(1, 6):
        y[f"y_k{k}"] = y_v[f"y_k{k}"] * rates[k - 1] / rates_v[k - 1]
    y["y_nolaw"] = y_v["y_nolaw"] * nolaw / float((H * y_v["y_nolaw"]).sum() / H.sum())
    add_pa, add_s = wi_additional(wi, y, base, growth)
    fac80, fac95 = interval_factor(f, 0.80), interval_factor(f, 0.95)
    lo_main = lo_all[(lo_all.within == MAIN_KEY[0]) & (lo_all.between == MAIN_KEY[1]) & (lo_all.stage2 == MAIN_KEY[2])
                     & (lo_all.calendar == MAIN_KEY[3])]
    st_err = lo_main[lo_main.series.isin(pr.STATE_CODING)]["log_error"].to_numpy()
    fac_loso80 = float(np.exp(pr.T_QUANTILES[0.80][len(st_err) - 1] * np.sqrt(np.mean(st_err ** 2))))
    out = []
    for lab, fac in (("central", 1.0), ("lower_80", 1 / fac80), ("upper_80", fac80), ("lower_95", 1 / fac95),
                     ("upper_95", fac95), ("lower_80_loso", 1 / fac_loso80), ("upper_80_loso", fac_loso80)):
        yy = y.copy()
        for k in range(1, 6):
            yy[f"y_k{k}"] = y[f"y_k{k}"] * fac
        a_pa, a_s = wi_additional(wi, yy, base, growth)
        for i, t in enumerate(e.YEARS):
            out.append(dict(path=lab, year=t, forecast_year=2026 + t, factor=fac, rate=rates[i] * fac,
                            with_law_total=rates[i] * fac * H.sum() / 1000, baseline=base[i],
                            additional=a_pa[i], additional_simple=a_s[i]))
    wst = pd.DataFrame(out)
    tot = wst.groupby("path")[["with_law_total", "baseline", "additional", "additional_simple"]].sum().reset_index()
    tot["year"], tot["forecast_year"] = "1-5", "2027-2031"
    tot["rate"] = tot["with_law_total"] / (5 * H.sum() / 1000)
    pd.concat([wst, tot], ignore_index=True).round(4).to_csv(REFERENCE / "pooled_wi_statewide.csv", index=False)
    ramp = pr.implied_ramp(wi, y[[f"y_k{k}" for k in range(1, 6)]].to_numpy())
    summary["B_main"] = {"key": list(MAIN_KEY), "rates": rates.round(4).tolist(), "nolaw_rate": nolaw,
                         "tau": f.tau, "factor80": fac80, "factor95": fac95, "factor80_loso": fac_loso80,
                         "additional_5yr": tot.set_index("path")["additional"].round(1).to_dict(),
                         "with_law_total_5yr": tot.set_index("path")["with_law_total"].round(1).to_dict(),
                         "implied_engine_ramp": ramp.round(4).tolist(),
                         "within": dict(zip(f.within_names, f.beta.round(4))), "gamma": f.gamma.round(4).tolist()}

    # engine cross-check: plateau y per area with the implied ramp
    lv = pd.DataFrame({"area_id": wi["area_id"], "y_central": y["y_k5"]})
    sc = e.Scenario("pooled", {"central": e.PathParams(level=0.0, floor_rate=FLOOR, spillover=0.0, ramp=tuple(ramp))})
    eng = e.run(d["areas"], sc, growth, area_levels=lv)
    summary["B_main"]["engine_check_additional_5yr"] = float(eng["additional_units"].sum())
    summary["B_main"]["engine_check_baseline_5yr"] = float(eng["baseline_units"].sum())

    # per-area by-product
    byarea = wi[["area_id", "name", "parent_county_id", "context_group", "homes", "x_rate", "rights_basis", "value",
                 "income", "rent", "renter_share", "value_basis", "income_basis"]].copy()
    for k in range(1, 6):
        byarea[f"y_k{k}_central"] = y[f"y_k{k}"].to_numpy()
    byarea["y_plateau_central"] = y["y_k5"].to_numpy()
    byarea["y_plateau_lower_80"] = byarea["y_plateau_central"] / fac80
    byarea["y_plateau_upper_80"] = byarea["y_plateau_central"] * fac80
    byarea["y_nolaw_model"] = y["y_nolaw"].to_numpy()
    byarea["y_plateau_main_spec_raw"] = y_raw["y_k5"].to_numpy()
    byarea["y_plateau_flat"] = rates[-1]
    byarea["allocation"] = "value-only within-state gradient (" + "|".join(ALLOC_KEY) + "), scaled to the main statewide rate"
    Y = y[[f"y_k{k}" for k in range(1, 6)]].to_numpy()
    byarea["additional_5yr_central"] = (H[:, None] * np.maximum(Y - byarea["x_rate"].to_numpy()[:, None], 0) / 1000).sum(axis=1)
    byarea["model"] = "|".join(MAIN_KEY)
    byarea.round(4).to_csv(REFERENCE / "pooled_wi_y_by_area.csv", index=False)
    ctx_tab = byarea.groupby("context_group").agg(homes=("homes", "sum"), additional_5yr=("additional_5yr_central", "sum"))
    ctx_tab["share_homes"] = ctx_tab["homes"] / ctx_tab["homes"].sum()
    ctx_tab["share_additional"] = ctx_tab["additional_5yr"] / ctx_tab["additional_5yr"].sum()
    summary["B_main"]["by_context"] = ctx_tab.round(3).reset_index().to_dict("records")

    # ---------------- local-only places: Madison, Minneapolis ----------------
    summary["local_only"] = local_only_checks(f, wi, lo_main, d, "main") + local_only_checks(
        f_alloc, wi, lo_all[(lo_all.within == ALLOC_KEY[0]) & (lo_all.between == ALLOC_KEY[1])
                            & (lo_all.stage2 == ALLOC_KEY[2]) & (lo_all.calendar == ALLOC_KEY[3])], d, "value-only within")
    pd.DataFrame(summary["local_only"]).round(4).to_csv(REFERENCE / "pooled_validation_local.csv", index=False)

    # ---------------- convergence: pre-law level vs year-1 level ----------------
    conv = convergence_table(d, ca_ctx)
    conv.round(4).to_csv(REFERENCE / "pooled_convergence.csv", index=False)
    lp, l1 = np.log(conv["pre_rate"]), np.log(conv["year1_rate"])
    X = np.column_stack([np.ones(len(lp)), lp])
    b = np.linalg.lstsq(X, l1, rcond=None)[0]
    r = l1 - X @ b
    se = np.sqrt(r @ r / max(len(lp) - 2, 1) * np.linalg.inv(X.T @ X)[1, 1])
    summary["convergence"] = {"slope_log_year1_on_log_pre": float(b[1]), "se": float(se), "n": int(len(lp)),
                              "wi_pre": float((H * wi["x_rate"]).sum() / H.sum()),
                              "wi_year1_implied": float(np.exp(b[0] + b[1] * np.log((H * wi["x_rate"]).sum() / H.sum())))}

    # ---------------- sensitivities on the main specification ----------------
    sens = sensitivities(d, p, wi, base, growth, H)
    sens.round(4).to_csv(REFERENCE / "pooled_sensitivities.csv", index=False)
    summary["sensitivities"] = sens.set_index("sensitivity")[["wi_rate_plateau", "wi_additional_5yr"]].round(3).to_dict("index")
    (od / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps({k: summary[k] for k in ("A", "best_by_loso", "B_main", "convergence")}, indent=1, default=float)[:6000])
    print(grid.sort_values("rms_log_error")[["within", "between", "stage2", "calendar", "rms_log_error", "rms_log_error_ME_OR_VT",
                                             "log_error_ME", "log_error_OR", "log_error_VT", "wi_rate_k5", "wi_additional_5yr"]]
          .round(3).to_string())
    print(sens.round(3).to_string())


WA_COMPLIANCE = {**pr.STATE_CODING,
                 "WA_inc_exSeattle": ("WA", {**pr._span(2019, 2023, 0, 0), **pr._span(2026, 2026, 1, 0, 1)})}


def ca_context(panel) -> dict:
    p = panel.dropna(subset=["adu_main"])
    g = p.groupby("year").agg(adu=("adu_main", "sum"), homes=("sf_detached", "sum"))
    return (g["adu"] / g["homes"] * 1000).round(4).to_dict()


def convergence_table(d, ca_ctx) -> pd.DataFrame:
    """Measured before/after pairs: the pre-law rate and the year-1 rate after a statewide law."""
    a = d["annual"].set_index(["series", "year"])["per_1000_homes"]
    pre_ca = float(np.mean([ca_ctx[y] for y in (2014, 2015, 2016)]))
    rows = [
        dict(state="CA", series="all jurisdictions", pre_window="2014-2016", pre_rate=pre_ca, year1="2017", year1_rate=ca_ctx[2017]),
        dict(state="RI", series="RI_statewide", pre_window="2021-2023", pre_rate=0.229, year1="2025", year1_rate=float(a[("RI_statewide", 2025)])),
        dict(state="WA", series="WA_inc_exSeattle", pre_window="EY2019-2023", pre_rate=0.394, year1="EY2024", year1_rate=float(a[("WA_inc_exSeattle", 2024)])),
        dict(state="VT", series="VT_chittenden", pre_window="2016-2020", pre_rate=0.616, year1="2021", year1_rate=float(a[("VT_chittenden", 2021)])),
    ]
    return pd.DataFrame(rows).assign(ratio=lambda t: t["year1_rate"] / t["pre_rate"])


def local_only_checks(f, wi, lo_main, d, label="main") -> list[dict]:
    """Madison (in-sample WI geography, never fitted) and Minneapolis (held out): local rules only."""
    out = []
    law_coef = float(f.beta[f.within_names.index("law")])
    H = wi["homes"].to_numpy(float)
    y_local = pr.predict_wi_ts(f, wi, local=1)
    mi = wi.index[wi["area_id"].eq("muni:5502548000")][0]
    mad_obs = 0.183
    pred_nolaw = float(y_local["y_nolaw"].iloc[mi])
    pred_law = float(y_local["y_k5"].iloc[mi])
    out.append(dict(spec=label, place="Madison", observed=mad_obs, observed_window="2022-2025 (second homes; ADU-type part 0.164)",
                    pred_local_no_statewide_law=pred_nolaw, pred_local_with_statewide_law_plateau=pred_law,
                    obs_over_pred_no_law=mad_obs / pred_nolaw, law_rate_ratio=float(np.exp(law_coef)),
                    share_of_log_gap_explained_by_law=law_coef / np.log(pred_law / mad_obs),
                    note="fit never sees Wisconsin data; Madison's 2026 provisional rate 0.97 (0.30 without the templated programme)"))
    m = lo_main[lo_main["held_out"].eq("MN")].iloc[0]
    out.append(dict(spec=label, place="Minneapolis", observed=m["obs_rate"], observed_window=f"{m['years']} (incl. new-house ADUs)",
                    pred_local_no_statewide_law=m["pred_rate"], pred_local_with_statewide_law_plateau=m["pred_rate"] * np.exp(law_coef),
                    obs_over_pred_no_law=m["obs_rate"] / m["pred_rate"], law_rate_ratio=float(np.exp(law_coef)),
                    share_of_log_gap_explained_by_law=law_coef / np.log(m["pred_rate"] * np.exp(law_coef) / m["obs_rate"]),
                    note="Minnesota held out of both stages (leave one state out)"))
    nl = float((H * y_local["y_nolaw"]).sum() / H.sum())
    out.append(dict(spec=label, place="Wisconsin statewide, current law", observed=float((H * wi["x_rate"]).sum() / H.sum()),
                    observed_window="current-law baseline x (homes-weighted)",
                    pred_local_no_statewide_law=float((H * pr.predict_wi_ts(f, wi)["y_nolaw"]).sum() / H.sum()),
                    pred_local_with_statewide_law_plateau=float((H * pr.predict_wi_ts(f, wi)["y_k5"]).sum() / H.sum()),
                    obs_over_pred_no_law=float((H * wi["x_rate"]).sum() / H.sum()) / float((H * pr.predict_wi_ts(f, wi)["y_nolaw"]).sum() / H.sum()),
                    law_rate_ratio=float(np.exp(law_coef)), share_of_log_gap_explained_by_law=np.nan,
                    note=f"no-law prediction uses local=0; with local=1 for every area it is {nl:.3f}"))
    return out


def sensitivities(d, p, wi, base, growth, H) -> pd.DataFrame:
    w, b, s2, _ = MAIN_KEY
    rows = []

    def run(name, pp, spec=None, weights="equal_state", note=""):
        sp = spec or tspec(w, b, s2)
        f = pr.fit_two_stage(pp, sp, weights)
        y, rates, nolaw = wi_rates(f, wi)
        add_pa, _ = wi_additional(wi, y, base, growth)
        rows.append(dict(sensitivity=name, note=note, wi_rate_k1=rates[0], wi_rate_plateau=rates[-1],
                         wi_mean_rate_5yr=rates.mean(), wi_additional_5yr=float(add_pa.sum()), tau=f.tau))

    run("main", p)
    run("measurement: new-house ADUs x0.8 (state series and city incl-new-house counts)",
        pr.Pooled(pr.adjust_counts(p.rows, new_house=True), p.members))
    run("measurement: coverage (ME / 0.73, MA / (293/351), RI / (32/39))",
        pr.Pooled(pr.adjust_counts(p.rows, coverage=True), p.members))
    run("measurement: both", pr.Pooled(pr.adjust_counts(p.rows, new_house=True, coverage=True), p.members))
    run("cities: main measure (excludes ADUs built with a new house)", pooled(d, city_measure="adu_units"))
    run("Washington coded from local compliance (EY2026 = year 1; EY2024-25 dropped)", pooled(d, state_coding=WA_COMPLIANCE))
    run("California coded from the 2017 law (2017-2025 rows, k = year - 2016)",
        pooled(d, ca_years=range(2017, 2026), ca_law_year=2017))
    run("California plateau only (2023-2025 rows)", pooled(d, ca_years=range(2023, 2026)))
    run("event time: Los Angeles from 2017", pooled(d, la_event=True))
    run("stage 1 weights: homes (no state reweighting)", p, weights="homes")
    run("stage 1 weights: sqrt(home-years) per state", p, weights="sqrt")
    run("stage 2 without California", p, spec=pr.TSpec("x", WITHIN[w][0] + K, BETWEEN[b],
                                                         stage2_clusters=tuple(c for c in LAW_STATES if c != "CA")))
    run("stage 2 all clusters (adds Austin, Denver, Minneapolis)", p, spec=tspec(w, b, "all_clusters"))
    run("no within-state market terms", p, spec=tspec("none", b, s2))
    run("between: home value", p, spec=tspec(w, "value", s2))
    run("between: price-to-income", p, spec=tspec(w, "price_to_income", s2))
    # Wisconsin's own base: Wisconsin areas as a cluster with its measured current-law rate and
    # a constant (multiplicative) law effect
    rows.append(own_base(d, p, wi, base, growth, H))
    return pd.DataFrame(rows)


def own_base(d, p, wi, base, growth, H) -> dict:
    """Sensitivity: treat Wisconsin's measured current-law rate as its no-law level and add the
    pooled law and ramp terms (a constant rate-ratio law effect)."""
    w, b, s2, _ = MAIN_KEY
    f = pr.fit_two_stage(p, tspec(w, b, s2))
    lc = f.beta[f.within_names.index("law")]
    kk = [f.beta[f.within_names.index(f"k{k}")] if f"k{k}" in f.within_names else 0.0 for k in (1, 2, 3)] + [0.0, 0.0]
    x = wi["x_rate"].to_numpy(float)
    Y = np.column_stack([x * np.exp(lc + kk[i]) for i in range(5)])
    rates = (H[:, None] * Y).sum(axis=0) / H.sum()
    add = pr.additional(wi, Y, base, per_area_max=True)
    return dict(sensitivity="Wisconsin's own current rate x pooled law rate ratio (multiplicative law effect)",
                note="contradicted by the measured before/after pairs (pooled_convergence.csv)",
                wi_rate_k1=rates[0], wi_rate_plateau=rates[-1], wi_mean_rate_5yr=rates.mean(),
                wi_additional_5yr=float(add.sum()), tau=np.nan)


if __name__ == "__main__":
    main()

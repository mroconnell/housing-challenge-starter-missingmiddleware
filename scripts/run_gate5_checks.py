"""Gate 5 model self-checks (docs/gate5/MODEL_CHECKS.md). Reads the adopted run; changes no adopted output.

Writes, all in reference/:
  gate5_pilot_multiplier_check.csv  the adopted statewide addition next to simple pilot multipliers, and the adopted
                                    method with every pilot-derived input to the with-law rate removed
  gate5_context_contrast.csv        urban / suburban / small-community / rural: homes, market, rates, totals
  gate5_context_examples.csv        the three largest places in each context, with their rates and drivers
  gate5_model_drivers.csv           within-state terms of the adopted pooled model: the statewide-rate fit and the
                                    value-only allocation term (what moves a place's level; AQ-061)
  gate5_trace.csv                   2027-2031 totals by current-law rate basis x context (observed / estimated / assumed)
  gate5_sensitivity_summary.csv     unknown rules, alternative groupings, transferred response rates
  gate5_housing_health.csv          landing-screen housing indicators with year, source and uncertainty
Run (after scripts/run_adu_model.py and scripts/run_unknown_rules_variants.py):
  uv run python scripts/run_gate5_checks.py
Units: permits = second-home permits on single-family lots at issuance, summed over 2027-2031 unless a column says
otherwise; rates = permits per 1,000 one-unit detached homes per year.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from missing_middleware.model import engine as e  # noqa: E402
from missing_middleware.model.params import area_paths, madison_floor  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402

PILOTS = {"muni:5502548000": "Madison city", "muni:5505963300": "Pleasant Prairie village",
          "muni:5502578600": "Sun Prairie city"}
GROUP_RATE_BASES = ("prohibited_group_rate", "restricted_group_rate", "uncoded_like_restricted_AQ027")
CONTEXTS = ("urban", "suburban", "small_community", "rural")
YRS = 5


def tot(o: pd.DataFrame) -> dict:
    t = e.five_year_totals(o).set_index("path")
    return {p: (float(t.loc[p, "baseline_units"]), float(t.loc[p, "additional_units"])) for p in e.PATHS}


def market(areas: pd.DataFrame) -> pd.DataFrame:
    from missing_middleware.comparison import ca_regression as cr
    paths = {t: RAW / cr.MARKET_SOURCE_ID / f"acsdt5y2024-{t}.dat" for t in cr.MARKET_TABLES}
    m = cr.wi_market(areas, cr.read_market(paths, "55", ("050", "060")))
    return m[["area_id", "value", "income"]]


def drivers() -> pd.DataFrame:
    """Within-state coefficients of the adopted pooled model (refit, about 5 seconds). Two fits (AQ-061 wording):
    the value-income-size fit sets the statewide rate by year (role "statewide rate"); the value-only fit (W_ALLOC,
    slope about 1.01) spreads that statewide total across Wisconsin places (role "allocation", term
    alloc_value_dev). Income and size do not enter the allocation."""
    import run_pooled_regression as rp
    import run_pooled_revision as rv
    from missing_middleware.comparison import pooled_regression as pr
    from missing_middleware.model.params import area_levels_spec
    spec = area_levels_spec()
    d = rp.load()
    pan = rv.ca_panels(d["panel"])[spec["option"]]
    p = rv.build(d, pan)
    f = pr.fit_two_stage(p, rv.tspec(spec["config"]))
    fa = pr.fit_two_stage(p, rv.tspec(spec["config"], rv.W_ALLOC))
    meaning = {"value_dev": "log of the place's median home value relative to its state's homes-weighted mean",
               "income_dev": "log of the place's median household income relative to its state's mean",
               "log_homes": "log of the place's one-unit detached homes (size)",
               "law": "statewide law in force", "local": "local reform in force",
               "k1": "first year after the law", "k2": "second year", "k3": "third year"}
    rows = [{"term": n, "role": "statewide rate (value-income-size fit)", "coefficient_log_scale": round(float(b), 4),
             "se_cluster": round(float(s), 4), "rate_ratio_per_unit": round(float(np.exp(b)), 4),
             "rate_ratio_for_10pct_higher": round(float(1.1 ** b), 4) if n in ("value_dev", "income_dev", "log_homes") else None,
             "meaning": meaning.get(n, n)} for n, b, s in zip(f.within_names, f.beta, f.se_within)]
    j = fa.within_names.index("value_dev")
    b, s = float(fa.beta[j]), float(fa.se_within[j])
    rows.append({"term": "alloc_value_dev", "role": "allocation across Wisconsin places (value-only fit, W_ALLOC)",
                 "coefficient_log_scale": round(b, 4), "se_cluster": round(s, 4), "rate_ratio_per_unit": round(float(np.exp(b)), 4),
                 "rate_ratio_for_10pct_higher": round(float(1.1 ** b), 4),
                 "meaning": ("log of the place's median home value relative to Wisconsin's homes-weighted mean, top-coded at "
                             "California's largest gap (+1.01); the only term that spreads the statewide total across places")})
    return pd.DataFrame(rows)


def main():
    from run_adu_model import load_area_levels, load_scenario
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    res = pd.read_parquet(PROCESSED / "model_run/results_long.parquet")
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")[["area_id", "name", "parent_county_id", "context_group"]]
    scen, levels, apaths = load_scenario(), load_area_levels(), area_paths()
    floor = madison_floor()
    homes_state = float(areas.homes.sum())
    adopted = tot(res)
    A = {p: adopted[p][1] for p in e.PATHS}
    B = adopted["central"][0]

    # ---------------- 1. pilot multipliers vs the statewide method ----------------
    five = res.groupby(["area_id", "path"])[["baseline_units", "additional_units"]].sum().reset_index()
    c5 = five[five.path.eq("central")].set_index("area_id")
    h = areas.set_index("area_id").homes
    rows = [{"case": "adopted statewide method (central)", "central_additional_5yr": A["central"],
             "numerator": "sum over 1,925 areas of homes x (with-law rate - current-law rate) x ramp / 1,000",
             "denominator": "", "note": "with-law rate from the pooled 8-state + 5-city model; current-law rate by area"}]
    mad = "muni:5502548000"
    r = c5.loc[mad, "additional_units"] / h[mad]
    rows.append({"case": "Madison multiplier: Madison's addition per single-family home x Wisconsin's homes",
                 "central_additional_5yr": r * homes_state,
                 "numerator": f"Madison addition {c5.loc[mad, 'additional_units']:.1f} permits",
                 "denominator": f"Madison homes {h[mad]:,.0f}; x {homes_state:,.0f} state homes", "note": "not used"})
    pid = list(PILOTS)
    r3 = c5.loc[pid, "additional_units"].sum() / h[pid].sum()
    rows.append({"case": "Three-pilot multiplier: pilots' addition per home x Wisconsin's homes",
                 "central_additional_5yr": r3 * homes_state,
                 "numerator": f"pilots' addition {c5.loc[pid, 'additional_units'].sum():.1f} permits",
                 "denominator": f"pilots' homes {h[pid].sum():,.0f}; x {homes_state:,.0f} state homes", "note": "not used"})
    ratio = (c5.loc[mad, "baseline_units"] + c5.loc[mad, "additional_units"]) / c5.loc[mad, "baseline_units"]
    rows.append({"case": "Madison ratio: statewide baseline x (Madison with-law / Madison baseline) - baseline",
                 "central_additional_5yr": B * (ratio - 1),
                 "numerator": f"Madison with-law {c5.loc[mad, 'baseline_units'] + c5.loc[mad, 'additional_units']:.1f}",
                 "denominator": f"Madison baseline {c5.loc[mad, 'baseline_units']:.1f}; x state baseline {B:.1f}",
                 "note": "not used"})
    # the adopted method with no pilot input to the with-law rate: no Madison floor, no Madison path
    s0 = load_scenario(**{p: {"floor_rate": 0.0} for p in e.PATHS})
    t0 = tot(e.run(areas, s0, growth, levels, None))
    rows.append({"case": "adopted method without the Madison floor and without Madison's own path",
                 "central_additional_5yr": t0["central"][1],
                 "numerator": "as the adopted method, floor 0 and Madison at its pooled level", "denominator": "",
                 "note": f"lower {t0['lower'][1]:.1f}, upper {t0['upper'][1]:.1f}"})
    cen = res[res.path.eq("central")]
    bind = cen[(cen.y_rate - floor).abs() < 1e-9]
    rows.append({"case": "addition in areas where the Madison floor sets the with-law rate (central)",
                 "central_additional_5yr": bind.additional_units.sum(),
                 "numerator": f"{bind.area_id.nunique()} areas, {bind.drop_duplicates('area_id').homes.sum():,.0f} homes",
                 "denominator": "", "note": "floor binds where the pooled level is below 0.2345"})
    rows.append({"case": "addition in the three pilot areas (central)",
                 "central_additional_5yr": c5.loc[pid, "additional_units"].sum(),
                 "numerator": ", ".join(f"{PILOTS[i]} {c5.loc[i, 'additional_units']:.1f}" for i in pid),
                 "denominator": f"{h[pid].sum():,.0f} homes ({h[pid].sum() / homes_state:.1%} of the state)", "note": ""})
    pm = pd.DataFrame(rows)
    pm["share_of_adopted"] = pm.central_additional_5yr / A["central"]
    pm.round({"central_additional_5yr": 1, "share_of_adopted": 4}).to_csv(REFERENCE / "gate5_pilot_multiplier_check.csv", index=False)

    # ---------------- 2. contexts ----------------
    mk = market(areas)
    y5 = res[res.year.eq(5)].pivot_table(index="area_id", columns="path", values="y_rate")
    a = (areas.merge(geo, on="area_id", how="left").merge(mk, on="area_id", how="left")
         .merge(y5.add_prefix("y5_").reset_index(), on="area_id", how="left"))
    w = five.pivot_table(index="area_id", columns="path", values="additional_units").add_prefix("add_")
    a = a.merge(w.reset_index(), on="area_id").merge(c5[["baseline_units"]].reset_index(), on="area_id")
    a = a[a.homes > 0]

    def wavg(g, c):
        ok = g[c].notna()
        return float(np.average(g.loc[ok, c], weights=g.loc[ok, "homes"])) if ok.any() else np.nan

    def wgeo(g, c):
        ok = g[c].notna() & (g[c] > 0)
        return float(np.exp(np.average(np.log(g.loc[ok, c]), weights=g.loc[ok, "homes"])))

    ctx_rows = []
    for c in CONTEXTS + ("state",):
        g = a if c == "state" else a[a.context_group.eq(c)]
        H = g.homes.sum()
        ctx_rows.append({
            "context": c, "areas": len(g), "homes": H, "share_of_state_homes": H / homes_state,
            "homes_per_area_median": g.homes.median(),
            "median_home_value_homes_weighted_geomean": wgeo(g, "value"),
            "median_income_homes_weighted_geomean": wgeo(g, "income"),
            "x_current_law_rate": wavg(g, "x_rate"), "y_with_law_rate_2031_central": wavg(g, "y5_central"),
            "baseline_5yr": g.baseline_units.sum(), "additional_lower_5yr": g.add_lower.sum(),
            "additional_central_5yr": g.add_central.sum(), "additional_upper_5yr": g.add_upper.sum(),
            "baseline_rate_per_1000_per_year": g.baseline_units.sum() / H / YRS * 1000,
            "additional_rate_central_per_1000_per_year": g.add_central.sum() / H / YRS * 1000,
            "share_of_state_additional_central": g.add_central.sum() / A["central"],
            "homes_observed_x": g.loc[g.x_status.eq("observed"), "homes"].sum(),
            "homes_estimated_x": g.loc[g.x_status.eq("estimated"), "homes"].sum(),
            "homes_assumed_x": g.loc[g.x_status.eq("assumed"), "homes"].sum()})
    cc = pd.DataFrame(ctx_rows)
    cc.round(4).to_csv(REFERENCE / "gate5_context_contrast.csv", index=False)
    ex = (a.sort_values("homes", ascending=False).groupby("context_group").head(3)
          .assign(add_rate=lambda d: d.add_central / d.homes / YRS * 1000,
                  ctx_order=lambda d: d.context_group.map({c: i for i, c in enumerate(CONTEXTS)}))
          .sort_values(["ctx_order", "homes"], ascending=[True, False]))
    ex = ex[["context_group", "area_id", "name", "homes", "value", "income", "x_rate", "x_status", "x_basis",
             "y5_central", "baseline_units", "add_central", "add_rate"]].rename(columns={
                 "value": "median_home_value", "income": "median_income", "y5_central": "y_with_law_rate_2031_central",
                 "baseline_units": "baseline_5yr", "add_central": "additional_central_5yr",
                 "add_rate": "additional_rate_central_per_1000_per_year"})
    ex.round(4).to_csv(REFERENCE / "gate5_context_examples.csv", index=False)
    drivers().to_csv(REFERENCE / "gate5_model_drivers.csv", index=False)

    # ---------------- 3. trace ----------------
    tr = []
    keys = [("x_status", "context_group"), ("x_status",), ("context_group",), ()]
    for k in keys:
        grp = a.groupby(list(k)) if k else [((), a)]
        for name, g in grp:
            name = name if isinstance(name, tuple) else (name,)
            d = dict(zip(k, name))
            tr.append({"x_status": d.get("x_status", "all"), "context": d.get("context_group", "all"),
                       "areas": len(g), "homes": g.homes.sum(), "share_of_homes": g.homes.sum() / homes_state,
                       "baseline_5yr": g.baseline_units.sum(), "additional_lower_5yr": g.add_lower.sum(),
                       "additional_central_5yr": g.add_central.sum(), "additional_upper_5yr": g.add_upper.sum(),
                       "share_of_baseline": g.baseline_units.sum() / B,
                       "share_of_additional_central": g.add_central.sum() / A["central"],
                       "share_of_additional_lower": g.add_lower.sum() / A["lower"],
                       "share_of_additional_upper": g.add_upper.sum() / A["upper"]})
    trace = pd.DataFrame(tr)
    if abs(trace[(trace.x_status == "all") & (trace.context == "all")].additional_central_5yr.iloc[0] - A["central"]) > 1e-6:
        raise SystemExit("trace does not reconcile to the state")
    trace.round(4).to_csv(REFERENCE / "gate5_trace.csv", index=False)

    # ---------------- 4. sensitivity summary ----------------
    sens = []

    def add(group, case, b, t, source, note=""):
        if b is not None and abs(b - B) < 0.06:     # the sensitivity table stores the adopted baseline to 0.1
            b = B
        sens.append({"group": group, "case": case, "baseline_5yr": b,
                     "additional_lower_5yr": t.get("lower"), "additional_central_5yr": t.get("central"),
                     "additional_upper_5yr": t.get("upper"),
                     "d_baseline": b - B if b is not None else None,
                     "d_additional_central": t["central"] - A["central"] if t.get("central") is not None else None,
                     "d_total_central": (b + t["central"] - B - A["central"]) if b is not None and t.get("central") is not None else None,
                     "source": source, "note": note})

    add("adopted", "adopted model", B, A, "reference/adu_model_statewide.csv")
    un = pd.read_csv(REFERENCE / "adu_model_unknown_rules_statewide.csv")
    for v, g in un.groupby("unknown_treatment", sort=False):
        if v == "like_restricted":
            continue
        g = g.set_index("path")
        add("unknown local rules", g.label.iloc[0], float(g.loc["central", "baseline_units"]),
            {p: float(g.loc[p, "additional_units"]) for p in e.PATHS}, "reference/adu_model_unknown_rules_statewide.csv",
            f"{int(g.uncoded_homes.iloc[0]):,} of {int(g.state_homes.iloc[0]):,} homes in uncoded areas")
    # alternative grouping (a): context groups do not enter the fit or the engine
    add("alternative grouping", "context groups redrawn (any definition)", B, A, "engine and pooled-model inputs",
        "context_group is not an input to the pooled fit or the engine; it only labels results and selects the "
        "'rural at floor' case. Totals are unchanged by construction.")
    # (b) current-law evidence groups pooled: prohibited and restricted evidence as one 'not yet benchmark' group
    grp = pd.read_csv(REFERENCE / "wi_baseline_rates_by_group.csv").set_index("group")
    pooled_rate = float((grp.loc["prohibited", "units"] + grp.loc["restricted", "units"])
                        / (grp.loc["prohibited", "thousand_home_years"] + grp.loc["restricted", "thousand_home_years"]))
    a2 = areas.copy()
    m = a2.x_basis.isin(GROUP_RATE_BASES)
    a2.loc[m, "x_rate"] = pooled_rate
    t2 = tot(e.run(a2, scen, growth, levels, apaths))
    add("alternative grouping", f"prohibited and restricted evidence pooled into one current-law group "
        f"({pooled_rate:.4f})", t2["central"][0], {p: t2[p][1] for p in e.PATHS}, "this script",
        f"applies to {int(m.sum())} areas on a group rate ({a2.loc[m, 'homes'].sum():,.0f} homes); "
        "39 permits / 720.33 thousand home-years")
    # (c) rural-at-floor with a narrower rural definition
    sw = pd.read_csv(REFERENCE / "adu_model_sensitivities.csv")
    for ctxs, lab in ((("rural",), "rural only (small communities on their level)"),
                      (("rural", "small_community"), "rural and small communities (adopted sensitivity case)")):
        ids = set(geo.loc[geo.context_group.isin(ctxs), "area_id"])
        lv = levels.copy()
        lv.loc[lv.area_id.isin(ids), "y_central"] = floor
        t3 = tot(e.run(areas, scen, growth, lv, apaths))
        add("alternative grouping", f"places at the Madison floor: {lab}", B, {"central": t3["central"][1]}, "this script")
    want = float(sw[sw.change.str.startswith("rural and small-community")].central_additional_5yr.iloc[0])
    if abs(sens[-1]["additional_central_5yr"] - want) > 0.1:
        raise SystemExit(f"rural case {sens[-1]['additional_central_5yr']:.1f} != adu_model_sensitivities.csv {want}")
    # transferred response rates (from the adopted sensitivity table)
    for key, lab in (("Lower as a statistical 10th", "lower at the 10th percentile of the between-state spread"),
                     ("California out", "California out of the between-state level"),
                     ("LA-calibrated", "LA-calibrated multifamily correction for California"),
                     ("eligible-property basis", "eligible-property basis (per eligible property, not per house)"),
                     ("no ramp", "no ramp (full effect from 2027)"),
                     ("Madison at its pooled level", "Madison on the statewide estimate"),
                     ("multiplicative", "multiplicative law (scales current rates)"),
                     ("California-only", "California-only market regression")):
        r = sw[sw.change.str.contains(key, regex=False)].iloc[0]
        t = {p: (None if pd.isna(r[f"{p}_additional_5yr"]) else float(r[f"{p}_additional_5yr"])) for p in e.PATHS}
        add("transferred response rates", lab, float(r.baseline_5yr), t, "reference/adu_model_sensitivities.csv",
            r.change)
    ss = pd.DataFrame(sens)
    num = ss.select_dtypes("number").columns
    ss[num] = ss[num].round(1)
    ss.to_csv(REFERENCE / "gate5_sensitivity_summary.csv", index=False)

    # ---------------- 5. housing health indicators ----------------
    sc = pd.read_parquet(PROCESSED / "foundation/state_conditions.parquet")
    sc = sc[sc.area_id.astype(str).eq("55")]
    want_ind = {"housing_units": "housing stock (PEP)", "total_housing_units_acs": "housing stock (ACS)",
                "occupied_units": "occupancy", "vacant_units": "occupancy", "vacancy_rate": "vacancy",
                "units_1_detached": "housing mix", "units_1_attached": "housing mix", "units_2_4": "housing mix",
                "units_5_plus": "housing mix", "mobile_home": "housing mix", "built_2020_or_later": "age of stock",
                "permitted_units_total": "permitted production", "permitted_units_1unit": "permitted production",
                "permitted_units_2_4": "permitted production", "permitted_units_5plus": "permitted production"}
    hh = []
    for ind, theme in want_ind.items():
        g = sc[sc.indicator.eq(ind)].sort_values("year")
        if g.empty:
            hh.append({"theme": theme, "indicator": ind, "status": "missing"})
            continue
        r = g.iloc[-1]
        hh.append({"theme": theme, "indicator": ind, "latest_year": int(r.year), "years_available": f"{g.year.min()}-{g.year.max()}",
                   "value": float(r.value), "moe_90": None if pd.isna(r.moe) else float(r.moe), "status": r.status,
                   "source_id": r.source_id, "source_vintage": r.source_vintage,
                   "uncertainty": ("ACS 90% margin of error" if pd.notna(r.moe) else
                                   f"BPS reported (not imputed) share {r.reporting_coverage:.3f}" if pd.notna(r.reporting_coverage)
                                   else "none published")})
    pep = sc[sc.indicator.eq("housing_units")].set_index("year").value
    bps = sc[sc.indicator.eq("permitted_units_total")].set_index("year").value
    hh.append({"theme": "permitted production", "indicator": "permits_per_1000_housing_units_2025", "latest_year": 2025,
               "years_available": "2020-2025", "value": float(bps[2025] / pep[2025] * 1000), "status": "calculated",
               "source_id": "census_bps_state; census_pep_v2025_hu", "source_vintage": "BPS 2025 final / PEP Vintage 2025",
               "uncertainty": f"numerator {bps[2025]:,.0f} permitted units, denominator {pep[2025]:,.0f} housing units (July 1 2025)"})
    pd.DataFrame(hh).to_csv(REFERENCE / "gate5_housing_health.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 80)
    print(pm.round(1).to_string(index=False))
    print(cc.round(3).T.to_string())
    print(trace.round(3).to_string(index=False))
    print(ss[["group", "case", "baseline_5yr", "additional_central_5yr", "d_baseline", "d_additional_central",
              "d_total_central"]].to_string(index=False))
    print(pd.read_csv(REFERENCE / "gate5_model_drivers.csv").to_string(index=False))
    print(ex.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

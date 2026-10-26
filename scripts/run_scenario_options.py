"""Owner's Gate 4 analytical questions (docs/gate4/SCENARIO_OPTIONS.md): candidate lower scenarios,
an all-eight-states reference line, Madison's treatment and Milwaukee's current-law rate.

Adopted basis throughout (AQ-042): pooled revision option (ii) cap + A2, configuration A,
Madison on the Madison-like path, engine over 2027-2031 on the 645-permit baseline (the Gate 3 basis;
see gate3_inputs: the owner adopted lower (a1), Milwaukee's measured rate and the 8-state line on 2026-10-26,
AQ-043, applied by scripts/build_wi_baseline.py and scripts/run_adu_model.py). Nothing adopted is changed: this script only reads the adopted inputs and writes
reference/scenario_options_*.csv.

Units: rates are second-home permits on single-family lots per 1,000 one-unit detached homes
(ACS 2020-2024 B25024_002) per year; additional permits are summed over 2027-2031 statewide.
Run: uv run python scripts/run_scenario_options.py   (about a minute; refits the adopted pooled model once)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import run_pooled_regression as rp  # noqa: E402
import run_pooled_revision as rv  # noqa: E402
from missing_middleware.comparison import pooled_regression as pr  # noqa: E402
from missing_middleware.model import engine as e  # noqa: E402
from missing_middleware.model.params import area_paths, madison_floor  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

OPTION, CONFIG = "cap_a2", "A_ca_in_common_level"
MADISON = "muni:5502548000"
MILWAUKEE = "muni:5507953000"
FLOOR = madison_floor()
YEARS = np.arange(2027, 2032)


# The analysis was made on the Gate 3 adopted basis (before AQ-043): Milwaukee on its assumed ramp and the
# 10th-percentile lower. After AQ-043 the adopted engine inputs have Milwaukee at its measured rate, so this script
# reads the Gate 3 current-law rates that scripts/build_wi_baseline.py keeps as a baseline sensitivity, and checks
# itself against the Gate 3 totals below. Its outputs therefore stay the pre-adoption analysis.
GATE3_TOTALS = {"lower": 4407.3407, "central": 8720.6434, "upper": 16852.8023}


def gate3_inputs(d):
    from missing_middleware.paths import PROCESSED
    a = pd.read_parquet(PROCESSED / "model_baseline/engine_areas_milwaukee_ramp.parquet")
    g = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth_milwaukee_ramp.parquet")
    wi = d["wi"].drop(columns=["x_rate"]).merge(a[["area_id", "x_rate"]], on="area_id", validate="1:1")
    G = rv.growth_matrix(wi, g)
    base = (wi["homes"].to_numpy(float)[:, None] * wi["x_rate"].to_numpy(float)[:, None] * G / 1000).sum(axis=0)
    return {**d, "areas": a, "growth": g, "wi": wi, "baseline": base}


# ---------------------------------------------------------------------------
# vectorised engine (checked against engine.run and the adopted outputs in main)
# ---------------------------------------------------------------------------
class Engine:
    def __init__(self, wi, G, ylev):
        self.ids = wi["area_id"].to_numpy()
        self.H = wi["homes"].to_numpy(float)
        self.x = wi["x_rate"].to_numpy(float)
        self.G = G
        lv = ylev.set_index("area_id").loc[self.ids]
        self.Yk = np.column_stack([lv[f"y_k{k}_central"].to_numpy(float) for k in range(1, 6)])
        self.Yp = lv["y_plateau_central"].to_numpy(float)
        self.idx = {a: i for i, a in enumerate(self.ids)}

    def ramp(self, fac):
        H = self.H
        yb = (H[:, None] * self.Yk * fac).sum(axis=0) / H.sum()
        xb = (H * self.x).sum() / H.sum()
        return np.clip((yb - xb) / (yb[-1] - xb), 0, 1)

    def run(self, fac=1.0, ramp=None, level_path=None, fixed=None, x=None, G=None):
        """fac: multiplier on every area's central level. level_path: optional 5 multipliers (one per
        year, no ramp) instead of fac x ramp. fixed: {area_id: 5 rates} explicit paths (no ramp).
        x / G: optional overrides of current-law rates / baseline growth. Returns (additional by
        area x year, baseline by area x year)."""
        x = self.x if x is None else x
        G = self.G if G is None else G
        H = self.H[:, None]
        xg = x[:, None] * G
        if level_path is None:
            r = self.ramp(fac) if ramp is None else np.asarray(ramp, float)
            y = np.maximum(np.maximum(self.Yp * fac, FLOOR), x)[:, None]
            add = H * np.maximum(y - xg, 0) * r[None, :] / 1000
        else:
            y = np.maximum(np.maximum(self.Yp[:, None] * np.asarray(level_path)[None, :], FLOOR), x[:, None])
            add = H * np.maximum(y - xg, 0) / 1000
        for a, rates in (fixed or {}).items():
            i = self.idx[a]
            yt = np.maximum(np.maximum(np.asarray(rates, float), FLOOR), x[i])
            add[i] = self.H[i] * np.maximum(yt - xg[i], 0) / 1000
        return add, H * xg / 1000


def main():
    pd.set_option("display.width", 250)
    params = json.loads((REFERENCE / "adu_model_params.json").read_text())
    mpath = np.array(params["area_paths"]["madison_like_path"]["rates"], float)
    d = gate3_inputs(rp.load())
    wi, base = d["wi"], d["baseline"]
    G = rv.growth_matrix(wi, d["growth"])
    ylev = pd.read_csv(REFERENCE / "pooled_revision_wi_y_by_area.csv")
    ylev = ylev[ylev.option.eq(OPTION) & ylev.config.eq(CONFIG)]
    eng = Engine(wi, G, ylev)
    rev = pd.read_csv(REFERENCE / "pooled_revision_wi.csv")
    rr = rev[rev.option.eq(OPTION) & rev.config.eq(CONFIG)].iloc[0]
    fac80 = float(rr["factor80"])
    common = float(rr["common_level_k4"])
    fixed_m = {MADISON: mpath}
    H_tot = eng.H.sum()

    # ---- checks against the adopted engine outputs ----
    adopted = pd.Series(GATE3_TOTALS)
    chk = {"central": eng.run(1.0, fixed=fixed_m)[0].sum(), "lower": eng.run(1 / fac80, fixed=fixed_m)[0].sum(),
           "upper": eng.run(fac80, fixed=fixed_m)[0].sum()}
    for k, v in chk.items():
        assert abs(v - adopted[k]) < 1.0, (k, v, adopted[k])
    base5 = eng.run()[1].sum()
    assert abs(base5 - 644.8667) < 0.01, base5
    # and against engine.run itself for one scaled path
    lvl = pd.DataFrame({"area_id": eng.ids, "y_central": eng.Yp * 0.65})
    sc = e.Scenario("chk", {"central": e.PathParams(0.0, FLOOR, 0.0, tuple(eng.ramp(0.65)))})
    ref = e.run(d["areas"], sc, d["growth"], lvl, area_paths())
    assert abs(ref["additional_units"].sum() - eng.run(0.65, fixed=fixed_m)[0].sum()) < 1e-6
    central_by_year = eng.run(1.0, fixed=fixed_m)[0].sum(axis=0)
    central5 = central_by_year.sum()

    # ---- refit the adopted pooled model (for state levels, Oregon's ramp, CA path, local term) ----
    panels = rv.ca_panels(d["panel"])
    p = rv.build(d, panels[OPTION])
    f = pr.fit_two_stage(p, rv.tspec(CONFIG))
    lawc = f.beta[f.within_names.index("law")]
    lev = {c: float(np.exp(a + lawc)) for c, a in f.alpha.items()}
    ctx = pd.DataFrame([pr.context(wi["homes"], wi["value"], wi["income"])])
    a_wi = float(f.alpha_hat(ctx)[0])
    assert abs(np.exp(a_wi + lawc) - common) < 1e-3
    pts = pr.adoption_points(p.rows, p.row_homes())          # non-California states, vacant-lot rule applied

    def stat_rate(add_by_year):
        return (base + add_by_year) / H_tot * 1000

    # =====================================================================
    # Q1: lower-scenario candidates
    # =====================================================================
    rows, yrows = [], []

    def record(cid, label, plain, add, typical_by_year, basis, flag=""):
        a5 = add.sum()
        byy = add.sum(axis=0)
        # lower <= central per area and year
        cen = eng.run(1.0, fixed=fixed_m)[0]
        viol = int((add > cen + 1e-9).sum())
        rows.append(dict(candidate=cid, label=label, plain_language=plain, additional_2027_2031=round(a5, 1),
                         total_with_baseline=round(a5 + base5, 1), share_of_central=round(a5 / central5, 4),
                         typical_place_level_year4plus=round(float(typical_by_year[-1]), 4),
                         typical_place_level_by_year="|".join(f"{v:.4f}" for v in typical_by_year),
                         statewide_rate_by_year="|".join(f"{v:.4f}" for v in stat_rate(byy)),
                         lower_le_central_statewide=bool(a5 <= central5 + 1e-9),
                         area_years_above_central=viol, basis=basis, flag=flag))
        for i, t in enumerate(YEARS):
            yrows.append(dict(candidate=cid, year=t, additional=round(byy[i], 2), statewide_rate=round(stat_rate(byy)[i], 4),
                              typical_place_level=round(float(typical_by_year[i]), 4)))

    central_ramp = eng.ramp(1.0)
    typ_central = common * central_ramp
    record("central", "Central (adopted, for reference)", "Like a typical statewide-law state.",
           eng.run(1.0, fixed=fixed_m)[0], typ_central, "adopted engine central")

    # (a) bottom statewide-law states' own levels
    bottom = {"a1_mean_RI_OR": ("RI", "OR"), "a2_mean_RI_OR_MA": ("RI", "OR", "MA")}
    for cid, sts in bottom.items():
        L = float(np.mean([lev[s] for s in sts]))
        fac = L / common
        r = eng.ramp(fac)
        record(cid, f"Like the slowest statewide-law states: mean of {', '.join(sts)}",
               f"Wisconsin performs like the average of the {len(sts)} slowest statewide-law states "
               f"({' and '.join(f'{s} {lev[s]:.2f}' for s in sts)}), with the model's usual differences between places and its ramp-up.",
               eng.run(fac, fixed=fixed_m)[0], L * r,
               f"level {L:.4f} = mean of stage-2 levels; factor {fac:.4f} on every area's central level; ramp {np.round(r, 4).tolist()}")
    L = lev["OR"]
    record("a3_median_RI_OR_MA", "Like the slowest statewide-law states: median of RI, OR, MA (= Oregon)",
           "Wisconsin performs like the middle of the three slowest statewide-law states (Oregon, 0.68).",
           eng.run(L / common, fixed=fixed_m)[0], L * eng.ramp(L / common), f"level {L:.4f} (Oregon)")
    # Oregon's observed ramp (the only bottom state with years 1-4 observed)
    orp = pts[pts.cluster.eq("OR")].sort_values("k")
    or_rates = orp.set_index("k")["rate"]
    or_ramp_raw = np.array([or_rates[k] / or_rates[4] for k in (1, 2, 3)] + [1.0, 1.0])
    or_ramp = np.maximum.accumulate(np.clip(or_ramp_raw, 0, 1))
    L = float(np.mean([lev["RI"], lev["OR"]]))
    record("a4_mean_RI_OR_oregon_ramp", "Mean of RI and OR, with Oregon's observed ramp",
           "As a1, but the climb over the first years follows Oregon's own 2019-2022 record instead of the pooled ramp.",
           eng.run(L / common, ramp=or_ramp, fixed=fixed_m)[0], L * or_ramp,
           f"Oregon (32 cities excl. Portland, x0.951) rates k1-k4 {np.round(or_rates.loc[[1, 2, 3, 4]].to_numpy(), 4).tolist()}; "
           f"ramp = rate_k / rate_4 = {np.round(or_ramp_raw, 4).tolist()} (made non-decreasing: {np.round(or_ramp, 4).tolist()})",
           flag="Rhode Island and Massachusetts have only year 1 observed, so only Oregon's ramp can be observed")

    # (b) California's 2017 package, years 1-3 (2017-2019), cap + A2 counts
    ca = pd.read_csv(REFERENCE / "pooled_revision_ca_inputs.csv")
    ca = ca[ca.option.eq(OPTION)]
    ca_y = ca[ca.year.isin(["2017", "2018", "2019"])].set_index("year")["rate_per_1000"].astype(float)
    ca_pl = float(ca[ca.year.str.startswith("2023-2025")]["rate_per_1000"].iloc[0])
    to_typ = lev["CA"] / ca_pl                     # California statewide rate -> typical-place level
    ca_typ = ca_y.to_numpy() * to_typ
    path_abs = np.r_[ca_typ, ca_typ[-1], ca_typ[-1]]
    record("b1_ca_2017_wave_absolute", "California's 2017 package, years 1-3, at California's own level",
           "Wisconsin follows what California actually reached in 2017-2019 under its first, weaker law (counts with the cap and A2 rule), year 3 held for 2030-2031.",
           eng.run(level_path=path_abs / common, fixed=fixed_m)[0], path_abs,
           f"CA statewide rates 2017-2019 {np.round(ca_y.to_numpy(), 4).tolist()} x (CA typical level {lev['CA']:.4f} / CA 2023-2025 rate {ca_pl:.4f} = {to_typ:.4f}); no ramp on top",
           flag="years 4-5 carry year 3 forward; 2017 counts have no parcel numbers, so the cap and A2 rule cannot be applied to 2017")
    rel = ca_y.to_numpy() / ca_pl
    path_rel = common * np.r_[rel, rel[-1], rel[-1]]
    record("b2_ca_2017_wave_relative", "California's 2017 package, years 1-3, as a share of California's later level",
           "Wisconsin reaches the same share of a typical state's level that California reached of its own later level in 2017-2019 (17%, 31%, 44%), year 3 held.",
           eng.run(level_path=path_rel / common, fixed=fixed_m)[0], path_rel,
           f"shares {np.round(rel, 4).tolist()} = CA 2017-2019 rate / CA 2023-2025 rate {ca_pl:.4f}, x common level {common:.4f}",
           flag="a weaker, non-benchmark law; years 4-5 carry year 3 forward")

    # (c) multiplier from already-permissive / pre-reform places
    mlc = pd.read_csv(REFERENCE / "madison_like_cities.csv")
    pre = mlc[mlc.before_rate_per_1000.notna() & mlc.state.isin(["WA", "RI"])].copy()
    pre["post_mean_y1_3"] = pre[["rate_y1", "rate_y2", "rate_y3"]].mean(axis=1, skipna=True)
    mad_x = 40 / 213.168
    m_all = mad_x / pre["before_rate_per_1000"].median()
    permissive = pre[pre.city.isin(["Vancouver", "Tacoma"])]     # liberal own rules before the window (2017, 2019)
    m_perm = mad_x / permissive["before_rate_per_1000"].median()
    lx, ly = np.log(pre["before_rate_per_1000"]), np.log(pre["post_mean_y1_3"])
    b_el = float(np.polyfit(lx, ly, 1)[0])
    # model-based: Madison observed vs the pooled model's rate for a place with its own ADU rules and no statewide law
    ywl = pr.predict_wi_ts(f, wi, local=1)
    ynl = pr.predict_wi_ts(f, wi, local=0)
    i_m = int(np.flatnonzero(wi["area_id"].eq(MADISON))[0])
    mad_local_pred = float(ywl["y_nolaw"].iloc[i_m])
    mad_nolaw_pred = float(ynl["y_nolaw"].iloc[i_m])
    m_model = mad_x / mad_local_pred
    wi_x = float((eng.H * eng.x).sum() / H_tot)
    state_pre = {"WA": rp_pre("WA_inc_exSeattle"), "RI": rp_pre("RI_statewide")}
    m_state = wi_x / float(np.median(list(state_pre.values())))
    mult = pd.DataFrame([
        dict(multiplier="c1_madison_vs_7_madison_like_peers_pre_law", value=m_all,
             numerator=f"Madison 2022-2025 rate {mad_x:.4f} (40 units / 213.168 thousand home-years)",
             denominator=f"median pre-law rate of 7 Madison-like cities with a before period (5 WA EY2019-2023, 2 RI 2023) = {pre['before_rate_per_1000'].median():.4f}"),
        dict(multiplier="c2_madison_vs_already_permissive_peers_pre_law", value=m_perm,
             numerator=f"Madison {mad_x:.4f}",
             denominator=f"median pre-law rate of Vancouver (liberal rules from 2017) and Tacoma (2019 reform) = {permissive['before_rate_per_1000'].median():.4f}"),
        dict(multiplier="c3_madison_vs_model_local_rules_no_state_law", value=m_model,
             numerator=f"Madison {mad_x:.4f}",
             denominator=f"pooled model rate for Madison's market with its own ADU rules and no statewide law = {mad_local_pred:.4f} (no own rules: {mad_nolaw_pred:.4f})"),
        dict(multiplier="c4_wisconsin_vs_statewide_law_states_pre_law", value=m_state,
             numerator=f"Wisconsin current-law rate {wi_x:.4f} (homes-weighted engine x)",
             denominator=f"median pre-law rate of the 2 states with a before period: WA excl. Seattle {state_pre['WA']:.4f}, RI {state_pre['RI']:.4f}"),
        dict(multiplier="elasticity_post_on_pre_7_cities", value=b_el,
             numerator="slope of log(mean rate, years 1-3 after the state law) on log(pre-law rate)",
             denominator="7 Madison-like cities with a before period (Cranston, Warwick: year 1 only)"),
    ])
    for _, mrow in mult.iterrows():
        cid = mrow.multiplier
        if cid.startswith("elasticity"):
            continue
        fac = float(mrow.value)
        r = eng.ramp(min(fac, 10))
        record(cid, f"Multiplier {cid.split('_', 1)[0]}: central x {fac:.3f}",
               "Wisconsin's level = the central level x (how the comparison place performed relative to its peers before their law).",
               eng.run(fac, fixed=fixed_m)[0], common * fac * r, f"{mrow.numerator} / {mrow.denominator}",
               flag="multiplicative assumption; see SCENARIO_OPTIONS.md section 1(c)")
    fac_el = m_state ** b_el
    record("c5_wisconsin_partial_elasticity", f"Wisconsin vs states before their law, damped by the 7-city elasticity: central x {fac_el:.3f}",
           "Wisconsin starts lower than statewide-law states did; if lower starts carry over partially (as across 7 Madison-like cities), Wisconsin ends at this share of the central.",
           eng.run(fac_el, fixed=fixed_m)[0], common * fac_el * eng.ramp(fac_el),
           f"factor = c4 {m_state:.4f} ^ elasticity {b_el:.4f}", flag="weakly identified: 7 cities, 2 states")

    # (d) current lower
    record("d_current_10th_percentile", "Current lower: 10th percentile of the between-state spread (central / 1.885)",
           "Below every statewide-law state's typical level; a statistical cut, not a group of states.",
           eng.run(1 / fac80, fixed=fixed_m)[0], common / fac80 * eng.ramp(1 / fac80), f"factor 1/{fac80:.4f}")
    low = pd.DataFrame(rows)
    low.to_csv(REFERENCE / "scenario_options_lower.csv", index=False)
    pd.DataFrame(yrows).to_csv(REFERENCE / "scenario_options_lower_by_year.csv", index=False)
    mult.round(4).to_csv(REFERENCE / "scenario_options_multiplier_inputs.csv", index=False)
    print(low[["candidate", "additional_2027_2031", "share_of_central", "typical_place_level_year4plus",
               "statewide_rate_by_year", "lower_le_central_statewide", "area_years_above_central"]].to_string())
    print(mult[["multiplier", "value"]])
    print(pre[["state", "city", "before_rate_per_1000", "post_mean_y1_3"]])

    # =====================================================================
    # Q2: reference line, median of all eight statewide-law states incl. California
    # =====================================================================
    ca_k = ca[ca.year.isin([str(y) for y in range(2020, 2026)])].assign(k=lambda z: z.year.astype(int) - 2019)
    ca_pts = pd.DataFrame({"cluster": "CA", "k": ca_k.k.to_numpy(), "rate": ca_k.rate_per_1000.astype(float).to_numpy(),
                           "year": ca_k.year.astype(int).to_numpy()})
    allp = pd.concat([pts[["cluster", "k", "rate", "year"]], ca_pts], ignore_index=True)
    allp.round(4).to_csv(REFERENCE / "scenario_options_reference_points.csv", index=False)
    lrows = []
    last = None
    for k in range(1, 6):
        g8 = allp[allp.k.eq(k)]
        g7 = g8[g8.cluster.ne("CA")]
        n8 = g8.cluster.nunique()
        if n8 >= 2:
            last = (k, float(g8.rate.median()))
            med8, basis = last[1], "observed median"
        else:
            med8, basis = last[1], f"only {n8} state ({','.join(g8.cluster)}) has data; year {last[0]} median carried forward"
        med7 = float(g7.rate.median()) if len(g7) else np.nan
        lrows.append(dict(year_since_law=k, forecast_year=2026 + k, n_states_8=n8,
                          states_8=",".join(f"{c} {r:.2f}" for c, r in g8.sort_values("rate")[["cluster", "rate"]].itertuples(index=False)),
                          median_8_states=med8, basis_8=basis, n_states_7=g7.cluster.nunique(), median_7_states_adopted=med7))
    rl = pd.DataFrame(lrows)
    rl["median_7_states_adopted"] = rl["median_7_states_adopted"].ffill()
    for col in ("median_8_states", "median_7_states_adopted"):
        app = pr.apply_curve(rl[col].to_numpy(), base)
        rl[col.replace("median", "wi_additional")] = app["additional"].to_numpy()
    rl["wi_central_additional"] = central_by_year
    rl["wi_central_statewide_rate"] = stat_rate(central_by_year)
    rl.round(4).to_csv(REFERENCE / "scenario_options_reference_line.csv", index=False)
    print(rl.round(3).to_string())
    print("ref8 total", rl.wi_additional_8_states.sum(), "ref8 yrs1-4", rl.wi_additional_8_states.iloc[:4].sum(),
          "ref7", rl.wi_additional_7_states_adopted.sum(), "central", central5, "central yrs1-4", central_by_year[:4].sum())

    # =====================================================================
    # Q3: Madison treatment
    # =====================================================================
    ml = pd.read_csv(REFERENCE / "pooled_revision_madison_like_wi.csv")
    def ids_of(names):
        return [a for n in names for a in ml.loc[ml.name.eq(n), "area_ids"].iloc[0].split("|")]
    sets = {
        "M0_madison_only (adopted)": ["Madison city"],
        "M1_value_250_500k_and_10k_homes": ml[(ml.homes >= 10_000) & ml.value.between(250_000, 500_000)].name.tolist(),
        "M2_benchmark_rules_or_measured_activity": ["Madison city", "Appleton city", "Wauwatosa city", "Kaukauna city"],
        "M3_all_10k_cities_except_milwaukee": ml[(ml.homes >= 10_000) & ~ml.largest_city].name.tolist(),
        "M4_all_10k_cities_incl_milwaukee": ml[ml.homes >= 10_000].name.tolist(),
    }
    geo_ids = {}
    kauk = wi.loc[wi["name"].astype(str).str.startswith("Kaukauna city"), "area_id"].tolist()
    mrows = []
    pooled_madison = eng.run(1.0)[0]
    for sname, names in sets.items():
        ids = [a for n in names if n != "Kaukauna city" for a in ids_of([n])] + (kauk if "Kaukauna city" in names else [])
        ids = [a for a in ids if a in eng.idx]
        fx = {a: mpath for a in ids}
        out = {}
        for pth, fac in (("lower", 1 / fac80), ("central", 1.0), ("upper", fac80)):
            out[pth] = eng.run(fac, fixed=fx)[0].sum()
        sel = np.isin(eng.ids, ids)
        grp_pooled = pooled_madison[sel].sum()
        grp_path = eng.run(1.0, fixed=fx)[0][sel].sum()
        mrows.append(dict(variant=sname, places="; ".join(names), n_areas=len(ids), homes=int(eng.H[sel].sum()),
                          group_additional_pooled_level=round(grp_pooled, 1), group_additional_on_path=round(grp_path, 1),
                          statewide_lower=round(out["lower"], 1), statewide_central=round(out["central"], 1),
                          statewide_upper=round(out["upper"], 1), change_in_central_vs_adopted=round(out["central"] - central5, 1),
                          baseline=round(base5, 1)))
    # starting from Madison's 2026 pace
    days = (pd.Timestamp("2026-10-23") - pd.Timestamp("2026-01-01")).days + 1
    expo = 53_292 * days / 365 / 1000
    pace = {"adopted 2022-2025 (40 units / 213.168)": mad_x, "2026 provisional, all 42 units": 42 / expo,
            "2026 provisional, 13 units without the templated programme": 13 / expo}
    peers_pre = float(pre["before_rate_per_1000"].median())
    inc = mpath - peers_pre
    for plab, xr in pace.items():
        for pathlab, pth in (("adopted path", mpath), ("path climbs from the 2026 pace (pace + peers' rise over their pre-law median)", xr + inc)):
            if plab.startswith("adopted") and pathlab != "adopted path":
                continue
            x2 = eng.x.copy()
            x2[eng.idx[MADISON]] = xr
            add, b = eng.run(1.0, fixed={MADISON: pth}, x=x2)
            madd, mb = add[eng.idx[MADISON]].sum(), b[eng.idx[MADISON]].sum()
            mrows.append(dict(variant=f"P: Madison current-law rate = {plab}; with-law = {pathlab}",
                              places="Madison city", n_areas=1, homes=53_292, madison_current_rate=round(xr, 4),
                              madison_with_law_path="|".join(f"{v:.3f}" for v in np.maximum(pth, xr)),
                              madison_baseline=round(mb, 1), madison_additional=round(madd, 1), baseline=round(b.sum(), 1),
                              statewide_central=round(add.sum(), 1), change_in_central_vs_adopted=round(add.sum() - central5, 1),
                              total_with_baseline=round(add.sum() + b.sum(), 1)))
        if not plab.startswith("adopted"):
            # baseline kept at the adopted rate, with-law path climbs from the 2026 pace
            add, b = eng.run(1.0, fixed={MADISON: xr + inc})
            mrows.append(dict(variant=f"P: Madison current-law rate kept at 0.1876; with-law path climbs from {plab}",
                              places="Madison city", n_areas=1, homes=53_292, madison_current_rate=round(mad_x, 4),
                              madison_with_law_path="|".join(f"{v:.3f}" for v in xr + inc),
                              madison_baseline=round(b[eng.idx[MADISON]].sum(), 1),
                              madison_additional=round(add[eng.idx[MADISON]].sum(), 1), baseline=round(b.sum(), 1),
                              statewide_central=round(add.sum(), 1), change_in_central_vs_adopted=round(add.sum() - central5, 1),
                              total_with_baseline=round(add.sum() + b.sum(), 1)))
    mad = pd.DataFrame(mrows)
    mad.to_csv(REFERENCE / "scenario_options_madison.csv", index=False)
    print(mad.drop(columns=["places"]).to_string())
    print("exposure", days, expo, {k: round(v, 4) for k, v in pace.items()}, "peers_pre", peers_pre)
    # model rates in years 1-3 for the mid-size set vs the path (homes-weighted)
    sel3 = np.isin(eng.ids, [a for a in [x for n in sets["M3_all_10k_cities_except_milwaukee"] for x in ids_of([n])] if a in eng.idx])
    r = eng.ramp(1.0)
    ys = np.maximum(np.maximum(eng.Yp[sel3], FLOOR), eng.x[sel3])
    mid_model = eng.H[sel3, None] * (eng.x[sel3, None] + (ys - eng.x[sel3])[:, None] * r[None, :])
    mid_rate = mid_model.sum(axis=0) / eng.H[sel3].sum()
    print("mid-size cities (M3) homes-weighted with-law rate by year, model central:", np.round(mid_rate, 3))
    mlp = pd.read_csv(REFERENCE / "madison_like_median_path.csv")
    pd.DataFrame({"year_since_law": range(1, 6), "m3_model_central_rate": mid_rate,
                  "wa_or_median": mlp[mlp.group.eq("WA+OR Madison-like (main)")].median_rate.to_numpy(),
                  "wa_or_pooled": mlp[mlp.group.eq("WA+OR Madison-like (main)")].pooled_rate.to_numpy(),
                  "wa_or_n_cities": mlp[mlp.group.eq("WA+OR Madison-like (main)")].n_cities.to_numpy(),
                  "wi_statewide_central_rate": stat_rate(central_by_year)}).round(4).to_csv(
        REFERENCE / "scenario_options_midsize_check.csv", index=False)

    # =====================================================================
    # Q4: Milwaukee's current-law rate
    # =====================================================================
    im = eng.idx[MILWAUKEE]
    st = d["areas"].set_index("area_id").loc[eng.ids, "x_status"].to_numpy()
    mil_cases = {
        "adopted: assumed ramp to Madison's 0.1876 by mid-2029": (eng.x[im], G[im]),
        "observed 2022-2025 candidates: 35 / 405.608 = 0.0863, flat": (35 / 405.608, np.ones(5)),
        "observed since the reform: 8 / 88.3 = 0.0906, flat": (8 / 88.3, np.ones(5)),
        "restricted-group rate 0.0607 (its coded class), flat": (0.0607, np.ones(5)),
    }
    qrows = []
    for lab, (xm, gm) in mil_cases.items():
        x2, G2 = eng.x.copy(), G.copy()
        x2[im], G2[im] = xm, gm
        res = {}
        for pth, fac in (("lower", 1 / fac80), ("central", 1.0), ("upper", fac80)):
            add, b = eng.run(fac, fixed=fixed_m, x=x2, G=G2)
            res[pth] = (add, b)
        add, b = res["central"]
        q = dict(case=lab, milwaukee_x_by_year="|".join(f"{v:.4f}" for v in xm * gm),
                 milwaukee_baseline=round(b[im].sum(), 1), statewide_baseline=round(b.sum(), 1),
                 milwaukee_additional_lower=round(res["lower"][0][im].sum(), 1),
                 milwaukee_additional_central=round(add[im].sum(), 1),
                 milwaukee_additional_upper=round(res["upper"][0][im].sum(), 1),
                 statewide_lower=round(res["lower"][0].sum(), 1), statewide_central=round(add.sum(), 1),
                 statewide_upper=round(res["upper"][0].sum(), 1), milwaukee_with_law_central_plateau=round(max(eng.Yp[im], FLOOR, xm), 4))
        for status in ("observed", "estimated", "assumed"):
            for relabel in ("as_now", "milwaukee_assumed"):
                s2 = st.copy()
                if relabel == "milwaukee_assumed":
                    s2[im] = "assumed"
                m = s2 == status
                q[f"cov_{relabel}_{status}_homes"] = int(eng.H[m].sum())
                q[f"cov_{relabel}_{status}_baseline"] = round(b[m].sum(), 1)
                q[f"cov_{relabel}_{status}_central"] = round(add[m].sum(), 1)
        qrows.append(q)
    mil = pd.DataFrame(qrows)
    mil.to_csv(REFERENCE / "scenario_options_milwaukee.csv", index=False)
    print(mil.T.to_string())
    perm = pd.read_csv(ROOT / "data/raw/milwaukee_permits/buildingpermits.csv", usecols=["Date Issued"], low_memory=False)
    print("Milwaukee permit cache: last issued", pd.to_datetime(perm["Date Issued"], errors="coerce").max())


def rp_pre(series):
    return pr.PRE_LAW[series]


if __name__ == "__main__":
    main()

"""Pooled model with the owner's outcome rules as named input options, and the G3F-2 test
(AQ-040). See docs/gate3/POOLED_REVISION.md. Writes new files only; the adopted outputs
(reference/pooled_*.csv, adu_model_*.csv) are not touched.

Inputs: everything scripts/run_pooled_regression.py reads, plus
reference/ca_mf_lot_adu_share_by_jurisdiction.csv, ..._la_calibration_bands.csv,
..._la_calibration_fit.csv, ca_jurisdiction_crosswalk (processed), reference/wi_y_by_area.csv,
data/processed/ca_regression/ca_dataset.parquet, reference/madison_like_median_path.csv, and
the ACS B25024 / TIGER place files already used by scripts/run_ca_mf_lot.py.

Outputs:
  reference/pooled_revision_ca_inputs.csv        California counts and rates by option
  reference/pooled_revision_loso.csv             held-out errors, every option x configuration x state
  reference/pooled_revision_g3f2.csv             RMS by option x configuration, bootstrap and drop-one checks
  reference/pooled_revision_drop_one.csv         RMS with each non-California state removed from the data
  reference/pooled_revision_wi.csv               Wisconsin statewide results by option x configuration
  reference/pooled_revision_wi_by_year.csv       Wisconsin rates and additional permits by year
  reference/pooled_revision_stage2_levels.csv     each state's level (law in force, year 4+, typical place)
  reference/pooled_revision_madison_like_wi.csv  Wisconsin Madison-like screen
  reference/pooled_revision_wi_y_by_area.csv     per-area with-law levels for the engine (AQ-042):
                                                 option (ii) cap+A2 x A (adopted), (ii) x B and (iii) x A (sensitivities)
  reference/pooled_revision_adoption_line.csv    statewide adoption reference line, as reported and with the vacant-lot rule
  reference/pooled_revision_reference_points.csv the 8-state reference-line points read by scripts/run_adu_model.py (AQ-061)
  reference/pooled_revision_coverage.csv         reporting shares applied to the comparison counts (AQ-061)
AQ-061 (2026-10-28): the adopted fit divides counts by reporting shares, codes Washington from local compliance and
top-codes each Wisconsin area's value gap for allocation; extra option rows "cap_a2|<variant>" (FIT_VARIANTS) hold the
sensitivities. The per-area levels are now computed on the adopted current-law rates (engine_areas.parquet).
  data/processed/pooled_revision/summary.json
Run: uv run python scripts/run_pooled_revision.py
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
from missing_middleware.comparison import ca_inputs as I  # noqa: E402
from missing_middleware.comparison import ca_mf_lot as M  # noqa: E402
from missing_middleware.comparison import ca_regression as cr  # noqa: E402
from missing_middleware.comparison import pooled_regression as pr  # noqa: E402
from missing_middleware.comparison import pooled_revision as R  # noqa: E402
from missing_middleware.foundation.parsers import read_acs_sf  # noqa: E402
from missing_middleware.model import engine as e  # noqa: E402
from missing_middleware.model.params import madison_floor  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE, processed_dir  # noqa: E402

FLOOR_OLD = madison_floor("adopted_2026_10_24")
FLOOR_NEW = madison_floor("g3f_revision_2026_10_25")
W = rp.WITHIN["value_income_size"][0] + rp.K           # within-state form of the adopted model
W_ALLOC = rp.WITHIN["value"][0] + rp.K                 # allocation gradient (as adopted)
NONCA = tuple(c for c in rp.LAW_STATES if c != "CA")
STATES = pr.STATEWIDE_STATES                           # the 7 non-California statewide-law states
CONFIGS = {   # name -> (between-state terms, stage-2 clusters)
    "A_ca_in_common_level": ((), rp.LAW_STATES),
    "B_ca_out_of_common_level": ((), NONCA),
    "C_value": (("value_ctx",), rp.LAW_STATES),
    "C_income": (("income_ctx",), rp.LAW_STATES),
    "C_price_to_income": (("pti_ctx",), rp.LAW_STATES),
}
CONFIG_LABELS = {
    "A_ca_in_common_level": "A: California in the between-state common level (adopted)",
    "B_ca_out_of_common_level": "B: California out of the common level (still in the within-state stage)",
    "C_value": "C: between-state term on log median home value (California included)",
    "C_income": "C: between-state term on log median household income (California included)",
    "C_price_to_income": "C: between-state term on log price-to-income (California included)",
}
CA_ONLY_RAMP = (0.10, 0.53, 0.58, 0.85, 1.0)           # run_ca_regression.PATH_RAMPS["central"]
MADISON_LIKE_PATH = None                                # read in main()
# per-area levels written for the engine (scripts/run_adu_model.py reads them; AQ-042)
ENGINE_LEVELS = (("cap_a2", "A_ca_in_common_level"), ("cap_a2", "B_ca_out_of_common_level"),
                 ("cap_la_calibrated", "A_ca_in_common_level"))


def tspec(name, w=W):
    b, s2 = CONFIGS[name]
    return pr.TSpec(name, w, b, stage2_clusters=s2)


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------

def ca_panels(panel):
    jy = pd.read_csv(REFERENCE / "ca_mf_lot_adu_share_by_jurisdiction.csv")
    xw = pd.read_parquet(PROCESSED / "comparison_ca/ca_jurisdiction_crosswalk.parquet")
    acs = read_acs_sf(RAW / "census_acs5_2024_tbsf/acsdt5y2024-b25024.dat", state_fips="06",
                      sumlevels=("050", "155", "160"))
    places = I.read_tiger_places(RAW / "census_tiger_2024_ca_place/tl_2024_06_place.zip")
    mf = M.acs_mf_share(acs, places)
    ms = xw[["juris_name", "census_geoid"]].merge(mf, on="census_geoid", how="left").set_index("juris_name")["mf_share"]
    bands = pd.read_csv(REFERENCE / "ca_mf_lot_adu_share_la_calibration_bands.csv")
    fits = pd.read_csv(REFERENCE / "ca_mf_lot_adu_share_la_calibration_fit.csv")
    rem = {"cap_a2": R.removed_cap_a2(jy), "cap_la_calibrated": R.removed_cap_la_calibrated(jy, bands, fits, ms)}
    out = {"as_used": R.adjust_ca_panel(panel, None, None)}
    for k, r in rem.items():
        out[k] = R.adjust_ca_panel(panel, R.to_geoid(r, xw), R.statewide_factor(r))
    return out


# Adopted measurement and coding (AQ-061, owner decision 2026-10-28): counts divided by each series-year's reporting
# share (pooled_regression.COVERAGE: Maine, Massachusetts and Rhode Island 2025, Utah 2023-2025); Massachusetts 2025
# counted as 11/12 of a year (pooled_regression.PARTIAL_YEAR, always on); Washington's law years coded from local
# compliance (OFM estimate year 2026 = year 1; 2024-2025 dropped: run_pooled_regression.WA_COMPLIANCE).
ADOPTED_CODING = rp.WA_COMPLIANCE
VT_SOURCE_CHANGE_YEAR = 2024     # Vermont 2024: DHCD layer (CCRPC-sourced records), not CCRPC's own series


def build(d, panel, vacant=True, mpls=True, coverage=True, coding=None, drop_vt_2024=False, coverage_states=None):
    """The pooled data for one California option. Defaults = the adopted fit (AQ-061). coverage_states limits the
    coverage correction to those series (None = every series in COVERAGE); coding=pr.STATE_CODING restores the
    Gate 3 Washington coding (law years from enactment)."""
    p = rp.pooled({**d, "panel": panel}, state_coding=coding or ADOPTED_CODING)
    rows = p.rows
    if coverage:
        sel = rows["series"].isin(coverage_states) if coverage_states is not None else np.ones(len(rows), bool)
        adj = pr.adjust_counts(rows, coverage=True)
        rows = rows.copy()
        rows.loc[sel, ["count", "coverage"]] = adj.loc[sel, ["count", "coverage"]]
    if drop_vt_2024:
        rows = rows[~(rows["series"].eq("VT_chittenden") & rows["year"].eq(VT_SOURCE_CHANGE_YEAR))].reset_index(drop=True)
    return pr.Pooled(R.adjust_other_rows(rows, vacant_lot=vacant, minneapolis=mpls), p.members)


# Sensitivities of the adopted fit (option cap_a2 x configuration A), written beside the engine levels as extra
# "option" rows so scripts/run_adu_model.py can run them through the engine (AQ-061).
FIT_VARIANTS = {
    "cap_a2|no_coverage": dict(coverage=False),
    "cap_a2|coverage_me_ma_ri_only": dict(coverage_states=("ME_statewide", "MA_statewide", "RI_statewide")),
    "cap_a2|wa_from_enactment": dict(coding=pr.STATE_CODING),
    "cap_a2|vt_2024_dropped": dict(drop_vt_2024=True),
    "cap_a2|gate4_coding": dict(coverage=False, coding=pr.STATE_CODING),
}


# ---------------------------------------------------------------------------
# Wisconsin: rates, allocation, engine
# ---------------------------------------------------------------------------

def growth_matrix(wi, growth):
    gmap = {(r.area_id, int(r.year)): float(r.g) for r in growth.itertuples()}
    return np.array([[gmap.get((a, t), 1.0) for t in e.YEARS] for a in wi["area_id"]])


def engine_totals(wi, G, y_plateau, ramp, floor):
    """Vectorised engine.run (spillover 0): y = max(floor, y_area, x); additional by year =
    H x max(y - x g, 0) x ramp / 1000. Checked against engine.run in main()."""
    H = wi["homes"].to_numpy(float)[:, None]
    x = wi["x_rate"].to_numpy(float)[:, None]
    y = np.maximum(np.maximum(np.asarray(y_plateau, float)[:, None], floor), x)
    add = (H * np.maximum(y - x * G, 0) * np.asarray(ramp)[None, :] / 1000).sum(axis=0)
    base = (H * x * G / 1000).sum(axis=0)
    return add, base


def ca_value_dev_max(p) -> float:
    """Largest value gap seen in the California training data: max over California's member places of log(median
    value) minus California's homes-weighted mean log value (about +1.01; ACS top-codes values at $2,000,000)."""
    m = pr.member_frame(p)
    ca = m[m["cluster"].eq("CA")].drop_duplicates("geoid")
    return float((np.log(ca["value"].astype(float)) - ca["ctx_log_value"]).max())


def cap_value_gap(wi, cap):
    """Top-code each area's value gap (log value minus Wisconsin's homes-weighted mean log value) at `cap` (AQ-061:
    no allocation beyond the range seen in California). Returns the capped frame and a boolean flag per area."""
    w = wi.copy()
    v0 = wi["value"].to_numpy(float)
    for _ in range(20):                          # the context moves slightly when the top values are capped
        ctx = pr.context(w["homes"], w["value"], w["income"])["ctx_log_value"]
        lim = float(np.exp(ctx + cap))
        new = np.minimum(v0, lim)
        if np.allclose(new, w["value"].to_numpy(float), rtol=0, atol=1e-6):
            break
        w["value"] = new
    return w, v0 > lim + 1e-6


def wi_paths(p, name, wi, cap=True):
    """Main fit, allocation, and the area-by-year central rates (as run_pooled_regression). The value-income-size fit
    (W) sets the statewide rate by year; the value-only fit (W_ALLOC, slope about 1.01) spreads that total across
    areas. cap: the allocation uses each area's value gap top-coded at California's largest (AQ-061); the statewide
    rate is unchanged."""
    f = pr.fit_two_stage(p, tspec(name))
    fa = pr.fit_two_stage(p, tspec(name, W_ALLOC))
    H = wi["homes"].to_numpy(float)
    _, rates, nolaw = rp.wi_rates(f, wi)
    wa = cap_value_gap(wi, ca_value_dev_max(p))[0] if cap else wi
    y_v, rates_v, _ = rp.wi_rates(fa, wa)
    Y = np.column_stack([y_v[f"y_k{k}"].to_numpy() * rates[k - 1] / rates_v[k - 1] for k in range(1, 6)])
    return f, Y, rates, nolaw, H


def ca_only_regression(panel_adj, ca_ds, wiy, wi, G, floor):
    """California-only market regression (group_value_hinge_size) refitted on the option's
    2023-2025 counts (activity groups kept as published), engine central with its ramp."""
    s = cr.panel_series(panel_adj)
    po = cr.plateau_outcome(s)
    d = ca_ds.set_index("census_geoid").copy()
    d["adu"] = po["adu"].reindex(d.index).to_numpy()
    d = d.dropna(subset=["adu"]).reset_index()
    f = cr.fit(d, cr.SPEC_BY_NAME["group_value_hinge_size"])
    w = wi[["area_id"]].merge(wiy.rename(columns={"ca_group": "group", "median_value": "value"})[
        ["area_id", "group", "value", "homes", "y_central"]], on="area_id", how="left")
    y = f.predict_rate(w)
    add, _ = engine_totals(wi, G, y, CA_ONLY_RAMP, floor)
    return float(add.sum()), y, w["y_central"].to_numpy()


def multiplicative(f, wi, base):
    lc = f.beta[f.within_names.index("law")]
    kk = [f.beta[f.within_names.index(f"k{k}")] for k in (1, 2, 3)] + [0.0, 0.0]
    x = wi["x_rate"].to_numpy(float)
    Y = np.column_stack([x * np.exp(lc + kk[i]) for i in range(5)])
    return float(pr.additional(wi, Y, base, per_area_max=True).sum())


def wi_results(p, name, d, G, floor, panel_adj, madison_like_ids, sens=True, cap=True):
    wi, base = d["wi"], d["baseline"]
    f, Y, rates, nolaw, H = wi_paths(p, name, wi, cap=cap)
    fac80 = rp.interval_factor(f, 0.80)
    ctx = pd.DataFrame([pr.context(wi["homes"], wi["value"], wi["income"])])
    a_wi = float(f.alpha_hat(ctx)[0])
    fac_ca = float(np.exp(f.alpha["CA"] - a_wi))           # Wisconsin at California's own estimated level
    out = dict(config=name, tau=f.tau, n_stage2=len(f.stage2), factor80=fac80, factor_ca_level=fac_ca,
               wi_rate_k1=rates[0], wi_rate_k2=rates[1], wi_rate_k3=rates[2], wi_rate_plateau=rates[4],
               wi_nolaw=nolaw, ca_level_k4=float(np.exp(f.alpha["CA"] + f.beta[f.within_names.index("law")])),
               common_level_k4=float(np.exp(a_wi + f.beta[f.within_names.index("law")])))
    paths = {"lower": 1 / fac80, "central": 1.0, "upper_tau90": fac80, "upper_ca_level": fac_ca}
    by_year = []
    for pth, fac in paths.items():
        Yp = Y * fac
        direct = pr.additional(wi, Yp, base, G, per_area_max=True)
        ramp = pr.implied_ramp(wi, Yp)
        add, b = engine_totals(wi, G, Yp[:, 4], ramp, floor)
        out[f"direct_{pth}"] = float(direct.sum())
        out[f"engine_{pth}"] = float(add.sum())
        out[f"ramp_{pth}"] = "|".join(f"{r:.4f}" for r in ramp)
        out[f"rate_plateau_{pth}"] = rates[4] * fac
        for i, t in enumerate(e.YEARS):
            by_year.append(dict(config=name, path=pth, year=t, forecast_year=2026 + t, rate=rates[i] * fac,
                                with_law_total=rates[i] * fac * H.sum() / 1000, statewide_baseline=base[i],
                                engine_baseline=b[i], additional_direct=direct[i], additional_engine=add[i]))
    out["engine_baseline"] = float(b.sum())
    out["statewide_baseline"] = float(base.sum())
    if not sens:
        return out, by_year, f, Y
    ramp_c = pr.implied_ramp(wi, Y)
    out["sens_no_ramp"] = float(engine_totals(wi, G, Y[:, 4], (1, 1, 1, 1, 1), floor)[0].sum())
    rural = wi["context_group"].isin(["rural", "small_community"]).to_numpy()
    yr = np.where(rural, floor, Y[:, 4])
    out["sens_rural_at_floor"] = float(engine_totals(wi, G, yr, ramp_c, floor)[0].sum())
    out["sens_multiplicative"] = multiplicative(f, wi, base)
    # Madison-like Wisconsin places on the observed Madison-like path (pending owner decision)
    ml = wi["area_id"].isin(madison_like_ids).to_numpy()
    path = np.asarray(MADISON_LIKE_PATH)
    x = wi["x_rate"].to_numpy(float)
    add_ml = (H[ml, None] * np.maximum(path[None, :] - x[ml, None] * G[ml], 0) / 1000).sum(axis=0)
    add_c = engine_totals(wi.loc[ml], G[ml], Y[ml, 4], ramp_c, floor)[0]
    out["madison_like_homes"] = float(H[ml].sum())
    out["madison_like_pooled_engine"] = float(add_c.sum())
    out["madison_like_observed_path"] = float(add_ml.sum())
    out["central_with_madison_like_path"] = out["engine_central"] - out["madison_like_pooled_engine"] + out["madison_like_observed_path"]
    return out, by_year, f, Y


def level_frame(opt, n, wi, Y, fac80, p):
    """Per-area levels for the engine, with the value top-code flag (AQ-061) and the uncapped central level."""
    cap = ca_value_dev_max(p)
    _, flag = cap_value_gap(wi, cap)
    _, Yu, _, _, _ = wi_paths(p, n, wi, cap=False)
    ctx = pr.context(wi["homes"], wi["value"], wi["income"])["ctx_log_value"]
    return pd.DataFrame({
        "option": opt, "config": n, "area_id": wi["area_id"].to_numpy(),
        **{f"y_k{k}_central": Y[:, k - 1] for k in range(1, 6)},
        "y_plateau_lower_80": Y[:, 4] / fac80, "y_plateau_central": Y[:, 4],
        "y_plateau_upper_80": Y[:, 4] * fac80,
        "value_gap_log": np.log(wi["value"].to_numpy(float)) - ctx, "value_gap_cap_log": cap,
        "value_capped": flag, "y_plateau_central_uncapped": Yu[:, 4]})


def wi_madison_like(d):
    acs = pr.read_acs_members(rp.acs_paths(), {"55"}, sumlevels=("160",))
    geo = pd.read_parquet(PROCESSED / "foundation/areas.parquet")
    g = geo[geo["level"].eq("municipality") & geo["muni_type"].isin(["city", "village"])]
    g = g.assign(placefp=g["cousubfp"].astype(str).str.zfill(5))
    names = g.groupby("placefp").agg(name=("name", "first"), muni_type=("muni_type", "first"),
                                     area_ids=("area_id", lambda s: "|".join(sorted(s))), pieces=("area_id", "size"))
    a = acs.assign(placefp=acs["geoid"].str[2:7]).set_index("placefp")[["homes", "value"]]
    pl = names.join(a, how="left").reset_index()
    # Places with no 160 row: sum of the engine pieces' homes, homes-weighted value
    wi = d["wi"].set_index("area_id")
    for i, r in pl[pl["homes"].isna()].iterrows():
        ids = r["area_ids"].split("|")
        pl.loc[i, "homes"] = wi.loc[ids, "homes"].sum()
        pl.loc[i, "value"] = np.average(wi.loc[ids, "value"], weights=wi.loc[ids, "homes"].clip(lower=1))
    return R.madison_like_wi(pl)


# ---------------------------------------------------------------------------

def main():
    global MADISON_LIKE_PATH
    mlp = pd.read_csv(REFERENCE / "madison_like_median_path.csv")
    MADISON_LIKE_PATH = mlp[mlp["group"].eq("WA+OR Madison-like (main)")].sort_values("year_since_law")["median_rate"].to_numpy()
    d = rp.load()
    wi, base, growth = d["wi"], d["baseline"], d["growth"]
    G = growth_matrix(wi, growth)
    od = processed_dir("pooled_revision")
    summary = {"floor_old": FLOOR_OLD, "floor_new": FLOOR_NEW, "madison_like_path": MADISON_LIKE_PATH.tolist()}
    panels = ca_panels(d["panel"])
    ca_ds = pd.read_parquet(PROCESSED / "ca_regression/ca_dataset.parquet")
    wiy = pd.read_csv(REFERENCE / "wi_y_by_area.csv")

    # ---------------- Madison-like Wisconsin places ----------------
    mlw = wi_madison_like(d)
    keep = mlw[(mlw["homes"] >= 10_000) | mlw["madison_like"]].sort_values("homes", ascending=False)
    keep[["placefp", "name", "muni_type", "homes", "value", "largest_city", "madison_like", "pieces", "area_ids"]] \
        .round(1).to_csv(REFERENCE / "pooled_revision_madison_like_wi.csv", index=False)
    ml_ids = set("|".join(mlw.loc[mlw["madison_like"], "area_ids"]).split("|"))
    summary["madison_like_wi"] = mlw.loc[mlw["madison_like"], ["name", "homes", "value"]].to_dict("records")

    # ---------------- reproduction of the adopted run ----------------
    p0 = build(d, panels["as_used"], vacant=False, mpls=False, coverage=False, coding=pr.STATE_CODING)
    r0, _, f0, Y0 = wi_results(p0, "A_ca_in_common_level", d, G, FLOOR_OLD, panels["as_used"], ml_ids, sens=False, cap=False)
    lv = pd.DataFrame({"area_id": wi["area_id"], "y_central": Y0[:, 4]})
    ramp0 = pr.implied_ramp(wi, Y0)
    eng = e.run(d["areas"], e.Scenario("chk", {"central": e.PathParams(0.0, FLOOR_OLD, 0.0, tuple(ramp0))}), growth, lv)
    assert abs(eng["additional_units"].sum() - r0["engine_central"]) < 1e-6, "vectorised engine disagrees with engine.run"
    summary["reproduction"] = {k: r0[k] for k in ("direct_central", "engine_central", "engine_lower", "engine_upper_tau90",
                                                  "direct_lower", "direct_upper_tau90", "engine_baseline")}
    print("reproduction", summary["reproduction"])

    # ---------------- California inputs by option ----------------
    ca_rows = []
    for opt, pan in panels.items():
        ctx = rp.ca_context(pan)
        q = pan.dropna(subset=["adu_main"])
        for y in range(2017, 2026):
            z = q[q["year"].eq(y)]
            ca_rows.append(dict(option=opt, year=y, adu_units=float(z["adu_main"].sum()),
                                one_unit_detached_homes=float(z["sf_detached"].sum()), rate_per_1000=ctx.get(y),
                                basis=",".join(sorted(z["ca_adjust_basis"].unique()))))
        z = q[q["year"].between(2023, 2025) & q["census_geoid"].isin(ca_ds["census_geoid"])]
        ca_rows.append(dict(option=opt, year="2023-2025, 457 pooled jurisdictions", adu_units=float(z["adu_main"].sum()),
                            one_unit_detached_homes=float(z["sf_detached"].sum()),
                            rate_per_1000=float(z["adu_main"].sum() / z["sf_detached"].sum() * 1000), basis="home-years"))
    pd.DataFrame(ca_rows).round(4).to_csv(REFERENCE / "pooled_revision_ca_inputs.csv", index=False)

    # ---------------- G3F-2: leave one state out, non-California states ----------------
    loso_rows, g3, drop_rows, wi_rows, wy_rows, st2_rows, lv_rows = [], [], [], [], [], [], []
    for opt, pan in panels.items():
        p = build(d, pan)
        err = {}
        for name in CONFIGS:
            lo = pr.loso_ts(p, tspec(name), clusters=STATES)
            lo = lo[lo["series"].isin(pr.STATE_CODING)].assign(option=opt, config=name)
            loso_rows.append(lo)
            err[name] = lo.set_index("held_out")["log_error"].reindex(list(STATES))
        E = pd.DataFrame(err)
        boot = R.paired_bootstrap_wins(E)
        # drop each state from the data entirely, rerun LOSO on the other six
        dr = {}
        for s0 in STATES:
            ps = pr.subset(p, p.rows["cluster"].ne(s0).to_numpy())
            others = tuple(s for s in STATES if s != s0)
            for name in CONFIGS:
                lo = pr.loso_ts(ps, tspec(name), clusters=others)
                lo = lo[lo["series"].isin(pr.STATE_CODING)]
                dr[(s0, name)] = R.rms(lo["log_error"])
                drop_rows.append(dict(option=opt, dropped_state=s0, config=name, n_states=len(lo), rms_log_error=dr[(s0, name)]))
        rmsd = {n: R.rms(E[n]) for n in CONFIGS}
        best_c = min((n for n in CONFIGS if n.startswith("C_")), key=rmsd.get)
        abc = ["A_ca_in_common_level", "B_ca_out_of_common_level", best_c]
        winner = min(abc, key=rmsd.get)
        win_drop = pd.Series({s0: min(abc, key=lambda n: dr[(s0, n)]) for s0 in STATES})
        win_drop_score = pd.Series({s0: min(abc, key=lambda n: (E[n].drop(s0) ** 2).mean()) for s0 in STATES})
        for n in CONFIGS:
            g3.append(dict(option=opt, config=n, label=CONFIG_LABELS[n], rms_log_error=rmsd[n],
                           mean_log_error=float(E[n].mean()), max_abs_log_error=float(E[n].abs().max()),
                           **{f"log_error_{s}": float(E.loc[s, n]) for s in STATES},
                           in_abc=n in abc, winner=n == winner, bootstrap_win_share_all5=float(boot[n]),
                           bootstrap_win_share_abc=float(R.paired_bootstrap_wins(E[abc])[n]) if n in abc else np.nan,
                           drop_one_rms_min=min(dr[(s, n)] for s in STATES), drop_one_rms_max=max(dr[(s, n)] for s in STATES),
                           drop_one_wins_of_7=int((win_drop == n).sum()) if n in abc else np.nan,
                           drop_from_score_wins_of_7=int((win_drop_score == n).sum()) if n in abc else np.nan))
        summary.setdefault("g3f2", {})[opt] = {"rms": rmsd, "winner": winner, "best_C": best_c,
                                               "drop_one_winner": win_drop.to_dict()}
        # ---------------- Wisconsin by configuration ----------------
        ca_tot, y_ca, y_ref = ca_only_regression(pan, ca_ds, wiy, wi, G, FLOOR_NEW)
        if opt == "as_used":
            summary["ca_only_refit_check_max_abs_y_diff"] = float(np.nanmax(np.abs(y_ca - y_ref)))
            summary["ca_only_as_used_floor_old"] = ca_only_regression(pan, ca_ds, wiy, wi, G, FLOOR_OLD)[0]
        for n in CONFIGS:
            r, by, f, Y = wi_results(p, n, d, G, FLOOR_NEW, pan, ml_ids)
            r.update(option=opt, label=CONFIG_LABELS[n], winner=n == winner, in_abc=n in abc, sens_ca_only_regression=ca_tot)
            wi_rows.append(r)
            lawc = f.beta[f.within_names.index("law")]
            for c, a in f.alpha.items():
                st2_rows.append(dict(option=opt, config=n, cluster=c, in_stage2=c in set(f.stage2["cluster"]),
                                     level_with_law_k4=float(np.exp(a + lawc)), alpha=float(a)))
            wy_rows += [dict(option=opt, **b) for b in by]
            if (opt, n) in ENGINE_LEVELS:
                fac80 = r["factor80"]
                lv_rows.append(level_frame(opt, n, wi, Y, fac80, p))
        # toggles on the winner (each rule switched off alone)
        tog = {}
        for lab, kw, fl in (("vacant_lot_off", dict(vacant=False), FLOOR_NEW), ("minneapolis_off", dict(mpls=False), FLOOR_NEW),
                            ("floor_adopted_0.229", {}, FLOOR_OLD), ("all_non_ca_rules_off", dict(vacant=False, mpls=False), FLOOR_OLD)):
            rr, _, _, _ = wi_results(build(d, pan, **kw), winner, d, G, fl, pan, ml_ids, sens=False)
            tog[lab] = rr["engine_central"]
        summary["g3f2"][opt]["toggles_engine_central"] = tog
        print(opt, "winner", winner, {k: round(v, 3) for k, v in rmsd.items()}, tog)

    # ---------------- named sensitivities of the adopted fit (cap_a2 x A; AQ-061) ----------------
    adopted_cfg = "A_ca_in_common_level"
    for vname, kw in FIT_VARIANTS.items():
        pv = build(d, panels["cap_a2"], **kw)
        r, by, f, Y = wi_results(pv, adopted_cfg, d, G, FLOOR_NEW, panels["cap_a2"], ml_ids, sens=False)
        r.update(option=vname, label=CONFIG_LABELS[adopted_cfg], winner=False, in_abc=False)
        wi_rows.append(r)
        lawc = f.beta[f.within_names.index("law")]
        for c, a in f.alpha.items():
            st2_rows.append(dict(option=vname, config=adopted_cfg, cluster=c, in_stage2=c in set(f.stage2["cluster"]),
                                 level_with_law_k4=float(np.exp(a + lawc)), alpha=float(a)))
        wy_rows += [dict(option=vname, **b) for b in by]
        lv_rows.append(level_frame(vname, adopted_cfg, wi, Y, r["factor80"], pv))
        print(vname, {k: round(r[k], 1) for k in ("engine_lower", "engine_central", "engine_upper_tau90")})
    # no value top-code (allocation only; the statewide totals are the adopted ones)
    pa = build(d, panels["cap_a2"])
    r, by, f, Y = wi_results(pa, adopted_cfg, d, G, FLOOR_NEW, panels["cap_a2"], ml_ids, sens=False, cap=False)
    r.update(option="cap_a2|no_value_cap", label=CONFIG_LABELS[adopted_cfg], winner=False, in_abc=False)
    wi_rows.append(r)
    lawc = f.beta[f.within_names.index("law")]
    for c, a in f.alpha.items():
        st2_rows.append(dict(option="cap_a2|no_value_cap", config=adopted_cfg, cluster=c,
                             in_stage2=c in set(f.stage2["cluster"]), level_with_law_k4=float(np.exp(a + lawc)), alpha=float(a)))
    lvn = level_frame("cap_a2|no_value_cap", adopted_cfg, wi, Y, r["factor80"], pa)
    lvn["value_capped"] = False
    lv_rows.append(lvn)

    # ---------------- coverage shares used (AQ-061) ----------------
    from missing_middleware.comparison import statewide_states as ss
    ut = ss.ut_reporting_share(RAW / "statewide_states/ut", RAW / "census_gazetteer_2024/2024_Gaz_place_national.zip",
                               RAW / "census_acs5_2024_tbsf/acsdt5y2024-b25024.dat")
    for row in ut.itertuples():
        want = pr.COVERAGE["UT_mih"][row.year]
        if abs(row.share - want) > 5e-5 or row.unmatched:
            raise SystemExit(f"Utah {row.year} reporting share {row.share:.4f} != COVERAGE {want} ({row.unmatched})")
    cov_rows = []
    basis = {"ME_statewide": "published: 182 reporting towns, about 73% of Maine's population (no town list in the repository)",
             "MA_statewide": "published: 293 of 351 towns responded (share of towns; no town list in the repository)",
             "RI_statewide": "published: 32 of 39 municipalities reported in 2025 (share of towns; no town list)",
             "UT_mih": "computed: one-unit detached homes in the jurisdictions that answered / all of Utah's"}
    for sid, ys in pr.COVERAGE.items():
        for y, sh in ys.items():
            u = ut[ut.year.eq(y)] if sid == "UT_mih" else None
            cov_rows.append(dict(series=sid, year=y, reporting_share=round(sh, 4), basis=basis[sid],
                                 homes_reporting=float(u.homes_reporting.iloc[0]) if u is not None else np.nan,
                                 homes_state=float(u.homes_state.iloc[0]) if u is not None else np.nan,
                                 n_jurisdictions=int(u.n_jurisdictions.iloc[0]) if u is not None else np.nan,
                                 partial_year_share=pr.PARTIAL_YEAR.get((sid, y), 1.0)))
    pd.DataFrame(cov_rows).to_csv(REFERENCE / "pooled_revision_coverage.csv", index=False)

    pd.concat(loso_rows, ignore_index=True).round(4).to_csv(REFERENCE / "pooled_revision_loso.csv", index=False)
    pd.DataFrame(g3).round(4).to_csv(REFERENCE / "pooled_revision_g3f2.csv", index=False)
    pd.DataFrame(drop_rows).round(4).to_csv(REFERENCE / "pooled_revision_drop_one.csv", index=False)
    wdf = pd.DataFrame(wi_rows)
    first = ["option", "config", "label", "winner", "in_abc"]
    wdf[first + [c for c in wdf.columns if c not in first]].round(4).to_csv(REFERENCE / "pooled_revision_wi.csv", index=False)
    pd.DataFrame(st2_rows).round(4).to_csv(REFERENCE / "pooled_revision_stage2_levels.csv", index=False)
    pd.DataFrame(wy_rows).round(4).to_csv(REFERENCE / "pooled_revision_wi_by_year.csv", index=False)
    pd.concat(lv_rows, ignore_index=True).round(4).to_csv(REFERENCE / "pooled_revision_wi_y_by_area.csv", index=False)

    # adoption reference line (statewide-law states' median path; no California in it)
    pts = pr.adoption_points(p.rows, p.row_homes())   # last option's rows: vacant-lot rule applied
    p_rep = build(d, panels["as_used"], vacant=False, mpls=False)   # adopted coding and coverage, no vacant-lot rule
    pts0 = pr.adoption_points(p_rep.rows, p_rep.row_homes())
    summary["adoption_line"] = {}
    al_rows = []
    for lab, pt in (("as_reported", pts0), ("vacant_lot_x0.951", pts)):
        c = pr.adoption_curve(pt)
        app = pr.apply_curve(c["median_rate"].to_numpy(), base)
        for i, t in enumerate(e.YEARS):
            al_rows.append(dict(variant=lab, year=t, forecast_year=2026 + t, median_rate=float(c["median_rate"].iloc[i]),
                                with_law_total=float(app["with_law_total"].iloc[i]), baseline=float(base[i]),
                                additional=float(app["additional"].iloc[i])))
        summary["adoption_line"][lab] = {"rates": c["median_rate"].round(4).tolist(), "additional_5yr": float(app["additional"].sum()),
                                         "with_law_total_5yr": float(app["with_law_total"].sum())}
    pd.DataFrame(al_rows).round(4).to_csv(REFERENCE / "pooled_revision_adoption_line.csv", index=False)
    # 8-state reference-line points (AQ-043 line, AQ-061 inputs): the seven states' adopted rows (coverage, Washington
    # compliance coding, vacant-lot x0.951) plus California's cap+A2 statewide rate with 2020 = year 1. Replaces
    # reference/scenario_options_reference_points.csv as the input of scripts/run_adu_model.py reference_lines().
    ca_in = pd.DataFrame(ca_rows)
    ca_in = ca_in[ca_in.option.eq("cap_a2") & ca_in.year.isin(list(range(2020, 2026)))]
    ca_pts = pd.DataFrame({"cluster": "CA", "k": ca_in.year.astype(int) - 2019, "rate": ca_in.rate_per_1000.astype(float),
                           "year": ca_in.year.astype(int)})
    pts8 = pd.concat([pts[["cluster", "k", "rate", "year"]], ca_pts], ignore_index=True)
    pts8.round(4).to_csv(REFERENCE / "pooled_revision_reference_points.csv", index=False)
    (od / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    pd.set_option("display.width", 250)
    print(pd.DataFrame(g3)[["option", "config", "rms_log_error", "winner", "bootstrap_win_share_abc", "drop_one_wins_of_7"]].round(3).to_string())
    print(wdf[["option", "config", "winner", "engine_baseline", "engine_lower", "engine_central", "engine_upper_tau90",
               "engine_upper_ca_level", "sens_no_ramp", "sens_rural_at_floor", "sens_multiplicative", "sens_ca_only_regression",
               "central_with_madison_like_path"]].round(0).to_string())
    print(json.dumps(summary["adoption_line"], indent=1))


if __name__ == "__main__":
    main()

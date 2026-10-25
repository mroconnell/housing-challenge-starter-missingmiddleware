"""ADUs on multifamily lots in California (HCD APR Table A2), the benchmark cap, ADU order on
the parcel, the ACS ecological check and the Los Angeles County Assessor validation.

Writes reference/ca_mf_lot_adu_share*.csv. Documented in docs/gate3/MULTIFAMILY_LOT_ADUS.md.
Reads only files already in the repo's data folders; the LA County Assessor rolls
(data/raw/la_county_assessor_rolls, from scripts/fetch_la_assessor_validation.py) are used
for validation only and are optional.

    uv run python scripts/run_ca_mf_lot.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.comparison import ca_inputs as I  # noqa: E402
from missing_middleware.comparison import ca_mf_lot as M  # noqa: E402
from missing_middleware.foundation.parsers import read_acs_sf  # noqa: E402

REF = ROOT / "reference"
PROC = ROOT / "data/processed/comparison_ca"
A2 = ROOT / "data/raw/hcd_apr_a2/tablea2.csv"
LA_ROLLS = ROOT / "data/raw/la_county_assessor_rolls"
PLATEAU = (2023, 2024, 2025)
SUM_COLS = None  # filled from the summary


def to_geoid(jy: pd.DataFrame, xw: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    m = jy.merge(xw[["juris_name", "census_geoid"]], on="juris_name", how="left")
    return m.dropna(subset=["census_geoid"]).groupby(["census_geoid", "year"])[cols].sum().reset_index()


def main() -> None:
    rows, keys = M.read_a2_adu_rows(A2)
    xw = pd.read_parquet(PROC / "ca_jurisdiction_crosswalk.parquet")
    panel = pd.read_parquet(PROC / "study/study_panel.parquet")
    groups = pd.read_csv(PROC / "study/groups_by_jurisdiction.csv")
    out = {}

    # ---- 1. statewide by year, three cutoffs -------------------------------------------
    by_year = []
    for cut in M.SENSITIVITY_CUTOFFS:
        s = M.summarize(M.annotate(rows, keys, cut), ["year"])
        s.insert(0, "cutoff", cut.date().isoformat())
        s.insert(1, "is_main_cutoff", cut == M.MAIN_CUTOFF)
        by_year.append(s)
    by_year = pd.concat(by_year, ignore_index=True)
    by_year.round(6).to_csv(REF / "ca_mf_lot_adu_share_by_year.csv", index=False)

    r = M.annotate(rows, keys, M.MAIN_CUTOFF)
    jy = M.summarize(r, ["cnty_name", "juris_name", "year"])
    jy.round(6).to_csv(REF / "ca_mf_lot_adu_share_by_jurisdiction.csv", index=False)

    # ---- ACS multifamily share per jurisdiction (for the ecological check and calibration) --
    acs = read_acs_sf(ROOT / "data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25024.dat", state_fips="06",
                      sumlevels=("050", "155", "160"))
    places = I.read_tiger_places(ROOT / "data/raw/census_tiger_2024_ca_place/tl_2024_06_place.zip")
    mf = M.acs_mf_share(acs, places)
    r = r.merge(xw[["juris_name", "census_geoid"]], on="juris_name", how="left").merge(
        mf[["census_geoid", "mf_share"]], on="census_geoid", how="left")

    # ---- LA County Assessor validation and calibration (optional) ------------------------
    calib = la_validation(r, out) if (LA_ROLLS / "_downloads.json").exists() else None
    if calib is not None:
        probs, fits, la_meas = calib
        r["p_mf_central"] = M.calibrated_mf(r, probs, fits, scale_single=True)
        r["p_mf_high"] = M.calibrated_mf(r, probs, fits, scale_single=False)
        r["est_mf_central"] = r["units"] * r["p_mf_central"]
        r["est_mf_high"] = r["units"] * r["p_mf_high"]
        r["kept_mf_central"] = r["cap_kept"] * r["p_mf_central"]
        r["kept_mf_high"] = r["cap_kept"] * r["p_mf_high"]
        statewide_range(r, la_meas)
        ex = r.groupby(["juris_name", "year"])[["kept_mf_central", "kept_mf_high"]].sum().reset_index()
        jy = jy.merge(ex, on=["juris_name", "year"], how="left")

    # ---- 2. rates: study panel with each variant --------------------------------------
    adj = M.adjusted_juris_year(jy)
    if calib is not None:
        adj["removed_cap_mf_central"] = adj["removed_cap"] + adj["kept_mf_central"].fillna(0)
        adj["removed_cap_mf_high"] = adj["removed_cap"] + adj["kept_mf_high"].fillna(0)
    rem_cols = [c for c in adj.columns if c.startswith("removed_")] + ["adu_units", "units_order2", "units_order3p",
                                                                       "units_order3", "units_order4p"]
    rem = to_geoid(adj, xw, rem_cols)
    check = panel.dropna(subset=["adu_main"]).merge(rem, on=["census_geoid", "year"], how="left")
    check = check[check["year"].between(2018, 2025)]
    out["reconstruction_gap_units"] = float((check["adu_main"] - check["adu_units"].fillna(0)).abs().sum())
    p = M.panel_with_variants(panel, rem)
    for v in ("cap_mf_central", "cap_mf_high"):
        p[f"adu_{v}"] = p["adu_main"] - p.get(f"removed_{v}", pd.Series(0.0, index=p.index)).fillna(0)
    for c in ("units_order2", "units_order3p", "units_order3", "units_order4p"):
        p[f"adu_{c}"] = p[c].fillna(0)
    rates = M.rate_by_year(p, years=range(2014, 2026))
    q = p.dropna(subset=["adu_main"])
    extra = q.groupby("year")[["adu_units_order2", "adu_units_order3p", "adu_units_order3", "adu_units_order4p"]].sum()
    rates = rates.merge(extra.reset_index(), on="year")
    for c in ("order2", "order3p", "order3", "order4p"):
        rates[f"rate_{c}"] = rates[f"adu_units_{c}"] / rates["sf_detached"] * 1000
    rates["rate_order1"] = rates["rate_as_reported"] - rates["rate_order2"] - rates["rate_order3p"]
    rates["k_from_2017_law"] = rates["year"] - 2016
    rates["note"] = np.where(rates["year"] < 2018, "2012-2019 compilation years: no APNs, so no adjustment (all counted as 1st ADUs)", "")
    rates.round(6).to_csv(REF / "ca_mf_lot_adu_share_rates_by_year.csv", index=False)

    # plateaus: all grouped non-holdout (the 3.84), and statewide all jurisdictions
    g = groups[(groups["spec"] == "main") & (groups["wave"] == 3) & groups["group"].isin(["restrictive", "middle", "permissive"])]
    nonhold = set(panel.loc[~panel["in_holdout"], "census_geoid"])
    sets = {"all_grouped_non_holdout (CA_STUDY_RESULTS 3.84)": set(g["census_geoid"]) & nonhold,
            "all_jurisdictions (statewide)": set(panel["census_geoid"])}
    for grp in ("restrictive", "middle", "permissive"):
        sets[f"{grp}_non_holdout"] = set(g.loc[g["group"].eq(grp), "census_geoid"]) & nonhold
    pl = []
    for name, ids in sets.items():
        for v, d in M.pooled_rate(p, ids, PLATEAU).items():
            pl.append(dict(set=name, period="2023-2025", variant=v, adu_numerator=d["numerator"],
                           home_years_denominator=d["denominator"], rate_per_1000=d["rate"]))
    pd.DataFrame(pl).round(6).to_csv(REF / "ca_mf_lot_adu_share_plateau.csv", index=False)

    # ---- 3. order decomposition ---------------------------------------------------------
    dec = []
    for base, label in (((2018,), "2018 (first A2 year)"), ((2014, 2015, 2016), "2014-2016 (compilation; all counted as 1st ADUs)")):
        d = M.order_decomposition(rates, base, PLATEAU).assign(base=label, end="2023-2025")
        dec.append(d)
    # with the 2023 rule in mind: 3rd ADUs from 2023 are within a single-family allowance
    r23 = rates.copy()
    r23["rate_order3_post2023"] = np.where(r23["year"] >= 2023, r23["rate_order3"], 0)
    dec = pd.concat(dec, ignore_index=True)
    e = r23[r23["year"].isin(PLATEAU)].mean(numeric_only=True)
    out["plateau_rate_order3_exactly"] = float(e["rate_order3"])
    out["plateau_rate_order4p"] = float(e["rate_order4p"])
    dec.round(6).to_csv(REF / "ca_mf_lot_adu_share_order_decomposition.csv", index=False)

    # ---- 4. ACS ecological check --------------------------------------------------------
    base = pd.read_parquet(ROOT / "data/processed/ca_regression/ca_dataset.parquet").drop(columns=["adu", "exposure"])
    base = base.merge(mf[["census_geoid", "mf_share"]], on="census_geoid", how="left")
    pq = panel.dropna(subset=["adu_main"])
    eco = []
    fits = {}
    for win in ((2014, 2016), (2018, 2019), (2020, 2022), (2023, 2025)):
        w = pq[pq["year"].between(*win)].groupby("census_geoid").agg(adu=("adu_main", "sum"), hy=("sf_detached", "sum")).reset_index()
        dd = base.merge(w, on="census_geoid")
        dd["exposure"] = dd["hy"] / 1000
        dd = dd[dd["value"].notna() & dd["income"].notna() & dd["mf_share"].notna() & (dd["exposure"] > 0)]
        for sample, sub in (("all", dd), ("excl_los_angeles_city", dd[dd["census_geoid"].ne("0644000")])):
            for spec, terms in M.ECO_SPECS.items():
                f = M.ecological_fit(sub.reset_index(drop=True), terms)
                fits[(win, sample, spec)] = (f, sub.reset_index(drop=True))
                eco.append(dict(window=f"{win[0]}-{win[1]}", sample=sample, spec=spec, n_jurisdictions=f["n"],
                                adu_units=f["adu_total"], coef_mf_share=f["coef_mf_share"], se_mf_share=f["se_mf_share"],
                                dispersion=f["dispersion"], implied_mf_lot_share=f["implied_share"],
                                implied_p10=f["implied_share_p10"], implied_p90=f["implied_share_p90"],
                                kind="level"))
    # difference-in-coefficient: 2023-2025 minus 2018-2019 (MF-structure ADUs broadly allowed from 2020)
    for sample in ("all", "excl_los_angeles_city"):
        for spec in M.ECO_SPECS:
            f1, d1 = fits[((2023, 2025), sample, spec)]
            f0, _ = fits[((2018, 2019), sample, spec)]
            db = f1["coef_mf_share"] - f0["coef_mf_share"]
            se = float(np.hypot(f1["se_mf_share"], f0["se_mf_share"]))
            X, _ = M.R.design(d1, M.ECO_SPECS[spec])
            mu = d1["exposure"].to_numpy() * np.exp(X @ np.array(list(f1["coefs"].values()))[:-1]
                                                     + f1["coef_mf_share"] * d1["mf_share"].to_numpy())
            m = d1["mf_share"].to_numpy()

            def sh(b):
                return float(1 - (mu * np.exp(-b * m)).sum() / mu.sum())
            eco.append(dict(window="2023-2025 minus 2018-2019", sample=sample, spec=spec, n_jurisdictions=f1["n"],
                            adu_units=f1["adu_total"], coef_mf_share=db, se_mf_share=se, dispersion=np.nan,
                            implied_mf_lot_share=sh(db), implied_p10=sh(db - 1.2816 * se), implied_p90=sh(db + 1.2816 * se),
                            kind="difference"))
    pd.DataFrame(eco).round(6).to_csv(REF / "ca_mf_lot_adu_share_acs_ecological.csv", index=False)

    (ROOT / "data/processed/comparison_ca/mf_lot_summary.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


def la_validation(r: pd.DataFrame, out: dict):
    la = r[r["cnty_name"].eq("Los Angeles")].copy()
    la["ain"] = M.la_ain(la["apn"])
    rolls = pd.concat([pd.read_csv(f, dtype=str) for f in sorted(LA_ROLLS.glob("roll_*.csv"))], ignore_index=True)
    rolls["year"] = rolls["RollYear"].astype(int)
    rolls = rolls.drop_duplicates(["AIN", "year"])
    rolls["lot_class"] = M.classify_la_use(rolls["UseCode"], rolls["UseCodeDescChar2"])
    # class at the roll of the permit's report year (lien date 1 January, before the permit)
    la = la.merge(rolls[["AIN", "year", "lot_class", "UseCode", "UseCodeDescChar2"]].rename(columns={"AIN": "ain"}),
                  on=["ain", "year"], how="left")
    first = rolls.sort_values("year").drop_duplicates("AIN")[["AIN", "lot_class"]].rename(
        columns={"AIN": "ain", "lot_class": "lot_class_first_roll"})
    la = la.merge(first, on="ain", how="left")
    la["lot_class"] = la["lot_class"].fillna("unmatched")
    la["lot_class_first_roll"] = la["lot_class_first_roll"].fillna("unmatched")
    la["is_mf"] = la["lot_class"].isin(M.LA_MF_CLASSES)
    la["is_sf"] = la["lot_class"].eq("single_family")
    la["juris"] = np.where(la["juris_name"].eq("LOS ANGELES"), "LOS ANGELES (city)",
                           np.where(la["juris_name"].eq("LOS ANGELES COUNTY"), "LOS ANGELES COUNTY (unincorporated)", la["juris_name"]))

    # use-code inventory (codes, not parcels)
    inv = la.groupby(["lot_class", "UseCode", "UseCodeDescChar2"], dropna=False)["units"].sum().reset_index()
    inv.sort_values("units", ascending=False).to_csv(REF / "ca_mf_lot_adu_share_la_use_codes.csv", index=False)

    def tab(df, by):
        t = df.pivot_table(index=by, columns="lot_class", values="units", aggfunc="sum", fill_value=0)
        for c in M.LA_ASSESSOR_CLASSES:
            if c not in t:
                t[c] = 0
        t = t[list(M.LA_ASSESSOR_CLASSES)]
        t["adu_units"] = t.sum(axis=1)
        t["matched_units"] = t["adu_units"] - t["unmatched"]
        t["match_rate"] = t["matched_units"] / t["adu_units"]
        t["mf_lot_units"] = t[list(M.LA_MF_CLASSES)].sum(axis=1)
        t["share_sf_lot_of_matched"] = t["single_family"] / t["matched_units"]
        t["share_mf_lot_of_matched"] = t["mf_lot_units"] / t["matched_units"]
        t["share_other_of_matched"] = 1 - t["share_sf_lot_of_matched"] - t["share_mf_lot_of_matched"]
        return t.reset_index()

    big = la.groupby("juris")["units"].sum()
    la["juris_group"] = np.where(la["juris"].isin(big[big >= 1000].index), la["juris"], "Other LA County cities")
    a = tab(la, ["juris_group", "year"]).rename(columns={"juris_group": "jurisdiction"})
    b = tab(la, ["year"]).assign(jurisdiction="LA County, all jurisdictions")
    c = tab(la.assign(y="2018-2025"), ["juris_group", "y"]).rename(columns={"juris_group": "jurisdiction", "y": "year"})
    d = tab(la.assign(y="2018-2025"), ["y"]).rename(columns={"y": "year"}).assign(jurisdiction="LA County, all jurisdictions")
    e = tab(la.assign(y="2018-2025"), ["juris", "y"]).rename(columns={"juris": "jurisdiction", "y": "year"})
    e = e[~e["jurisdiction"].isin(a["jurisdiction"])]
    pd.concat([b, a, d, c, e.assign(note="each LA County jurisdiction, 2018-2025")], ignore_index=True).round(6).to_csv(
        REF / "ca_mf_lot_adu_share_la_assessor.csv", index=False)

    # rule check: APN-year band, cap/order, unit-cat flag vs assessor class
    la["rule_band"] = np.where(la["unitcat_mf"], "unitcat_mf", la["band"])
    la["n_bucket"] = la["n_apn_year"].clip(upper=4).fillna(0).astype(int).astype(str).replace({"4": "4+", "0": "unknown"})
    la["period"] = np.where(la["year"] >= 2023, "2023-2025", "2018-2022")
    m = la[la["lot_class"].ne("unmatched")]
    rc = []
    for key, col in (("apn_units_in_year", "n_bucket"), ("rule_band_main_cutoff", "rule_band")):
        for (per, val), grp in m.groupby(["period", col]):
            rc.append(dict(check=key, period=per, value=val, matched_units=grp["units"].sum(),
                           sf_lot_units=grp.loc[grp["is_sf"], "units"].sum(), mf_lot_units=grp.loc[grp["is_mf"], "units"].sum()))
        for (yr, val), grp in m.groupby(["year", col]):
            rc.append(dict(check=key, period=str(yr), value=val, matched_units=grp["units"].sum(),
                           sf_lot_units=grp.loc[grp["is_sf"], "units"].sum(), mf_lot_units=grp.loc[grp["is_mf"], "units"].sum()))
    # cap: of units kept by the cap (1st and 2nd ADUs), how many are on MF lots, by A2 flag
    for per, grp in m.groupby("period"):
        for lab, sel in (("kept_by_cap_all", slice(None)), ("kept_by_cap_not_flagged_definite", ~grp["definite_any"]),
                         ("kept_by_cap_single_band", grp["band"].eq("single") & ~grp["unitcat_mf"])):
            g2 = grp[sel] if not isinstance(sel, slice) else grp
            k = g2["cap_kept"]
            rc.append(dict(check="cap_kept_units", period=per, value=lab, matched_units=k.sum(),
                           sf_lot_units=k[g2["is_sf"]].sum(), mf_lot_units=k[g2["is_mf"]].sum()))
        for o in ("u_order1", "u_order2", "u_order3p"):
            rc.append(dict(check="order_on_parcel", period=per, value=o.removeprefix("u_"), matched_units=grp[o].sum(),
                           sf_lot_units=grp.loc[grp["is_sf"], o].sum(), mf_lot_units=grp.loc[grp["is_mf"], o].sum()))
    for yr, grp in m.groupby("year"):
        k = grp["cap_kept"]
        nf = ~grp["definite_any"]
        rc.append(dict(check="cap_kept_units", period=str(yr), value="kept_by_cap_all", matched_units=k.sum(),
                       sf_lot_units=k[grp["is_sf"]].sum(), mf_lot_units=k[grp["is_mf"]].sum()))
        rc.append(dict(check="cap_kept_units", period=str(yr), value="kept_by_cap_not_flagged_definite", matched_units=k[nf].sum(),
                       sf_lot_units=k[nf & grp["is_sf"]].sum(), mf_lot_units=k[nf & grp["is_mf"]].sum()))
    # recoding check: class at the permit-year roll vs the first available roll (2018)
    for per, grp in m.groupby("period"):
        rc.append(dict(check="first_roll_2018_class", period=per, value="mf_lot_at_2018_roll", matched_units=grp["units"].sum(),
                       sf_lot_units=grp.loc[grp["lot_class_first_roll"].eq("single_family"), "units"].sum(),
                       mf_lot_units=grp.loc[grp["lot_class_first_roll"].isin(M.LA_MF_CLASSES), "units"].sum()))
    rc = pd.DataFrame(rc)
    rc["share_sf_lot"] = rc["sf_lot_units"] / rc["matched_units"]
    rc["share_mf_lot"] = rc["mf_lot_units"] / rc["matched_units"]
    rc.round(6).to_csv(REF / "ca_mf_lot_adu_share_la_rule_check.csv", index=False)

    tot = la["units"].sum()
    out["la_units"] = float(tot)
    out["la_matched_units"] = float(la.loc[la["lot_class"].ne("unmatched"), "units"].sum())
    out["la_mf_units"] = float(la.loc[la["is_mf"], "units"].sum())

    probs, fits = M.la_calibration(m)
    probs.round(6).to_csv(REF / "ca_mf_lot_adu_share_la_calibration_bands.csv", index=False)
    fits.round(6).to_csv(REF / "ca_mf_lot_adu_share_la_calibration_fit.csv", index=False)
    meas = la.groupby("year").apply(lambda x: pd.Series({
        "la_adu_units": x["units"].sum(), "la_matched_units": x.loc[x["lot_class"].ne("unmatched"), "units"].sum(),
        "la_mf_lot_units": x.loc[x["is_mf"], "units"].sum(),
        "la_cap_kept_units": x["cap_kept"].sum(),
        "la_cap_kept_mf_lot_units": x.loc[x["is_mf"], "cap_kept"].sum(),
        "la_cap_kept_matched_units": x.loc[x["lot_class"].ne("unmatched"), "cap_kept"].sum()}), include_groups=False).reset_index()
    return probs, fits, meas


def statewide_range(r: pd.DataFrame, la_meas: pd.DataFrame) -> None:
    """Statewide multifamily-lot share by year. LA County: assessor-measured share of matched units
    applied to all its units. Elsewhere: A2 lower bound (low), LA-calibrated central, LA pooled
    shares without scaling to local multifamily stock (high). Low and high are the smallest and largest
    of the three, so the range always contains the central."""
    r = r.assign(is_la=r["cnty_name"].eq("Los Angeles"))
    rows = []
    for yr, x in r.groupby("year"):
        la, rest = x[x["is_la"]], x[~x["is_la"]]
        mm = la_meas.set_index("year").loc[yr]
        la_mf = mm["la_mf_lot_units"] / mm["la_matched_units"] * mm["la_adu_units"]
        u = x["units"].sum()
        d = dict(year=yr, adu_units=u, la_county_units=mm["la_adu_units"], la_county_matched_units=mm["la_matched_units"],
                 la_county_mf_lot_units_measured=mm["la_mf_lot_units"],
                 la_county_mf_lot_share_of_matched=mm["la_mf_lot_units"] / mm["la_matched_units"],
                 la_county_model_central_units=la["est_mf_central"].sum(),
                 rest_units=rest["units"].sum(),
                 rest_a2_lower_units=rest.loc[rest["definite_any"], "units"].sum(),
                 rest_a2_upper_units=rest.loc[rest["definite_any"] | rest["possible_only"], "units"].sum(),
                 rest_calibrated_central_units=rest["est_mf_central"].sum(),
                 rest_calibrated_high_units=rest["est_mf_high"].sum(),
                 statewide_a2_lower_units=x.loc[x["definite_any"], "units"].sum(),
                 statewide_a2_upper_units=x.loc[x["definite_any"] | x["possible_only"], "units"].sum())
        cands = [la_mf + d["rest_a2_lower_units"], la_mf + d["rest_calibrated_central_units"],
                 la_mf + d["rest_calibrated_high_units"]]
        d["statewide_low_units"] = min(cands)
        d["statewide_central_units"] = cands[1]
        d["statewide_high_units"] = max(cands)
        for k in ("statewide_a2_lower", "statewide_a2_upper", "statewide_low", "statewide_central", "statewide_high"):
            d[f"{k}_share"] = d[f"{k}_units"] / u
        for k in ("rest_a2_lower", "rest_a2_upper", "rest_calibrated_central", "rest_calibrated_high"):
            d[f"{k}_share"] = d[f"{k}_units"] / d["rest_units"]
        d["la_county_model_central_share"] = d["la_county_model_central_units"] / d["la_county_units"]
        rows.append(d)
    t = pd.DataFrame(rows)
    tot = t.drop(columns="year").sum()
    tot_row = {k: tot[k] for k in t.columns if k.endswith("_units")}
    tot_row["year"] = "2018-2025"
    for k in ("statewide_a2_lower", "statewide_a2_upper", "statewide_low", "statewide_central", "statewide_high"):
        tot_row[f"{k}_share"] = tot_row[f"{k}_units"] / tot_row["adu_units"]
    t = pd.concat([t, pd.DataFrame([tot_row])], ignore_index=True)
    t.round(6).to_csv(REF / "ca_mf_lot_adu_share_statewide_range.csv", index=False)


if __name__ == "__main__":
    main()

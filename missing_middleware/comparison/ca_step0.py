"""Step 0 of the California comparison plan: reconcile Census BPS with HCD APR.

Data-quality tables only (docs/gate3/CA_COMPARISON_PLAN.md, "Step 0"). Nothing here
defines permissive/restrictive groups, compares periods around reform waves, or
estimates ramp or spillover.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_inputs as I
from missing_middleware.foundation.parsers import read_bps

YEARS = tuple(range(2018, 2026))
NONADU = ["sfd", "sfa", "u2_4", "u5plus"]
LA_CITY = "0644000"
BOOTSTRAP_SEED = 20261025
BOOTSTRAP_DRAWS = 500
BASELINE_MIN_SF_DETACHED = (5_000, 10_000, 20_000)

# Holdout handling (docs/gate3/CA_COMPARISON_PLAN.md, "Held-out data"). Every step 0 output
# carries one of: `in_holdout` (jurisdiction-grain rows), `jurisdiction_sample` in
# {"non_holdout", "all"} (aggregates that could feed the model; non_holdout is the one to use),
# or `includes_holdout_jurisdictions` = True (state- or county-level descriptive data-quality
# aggregates). Holdout jurisdictions may appear in descriptive data-quality tables; they are
# excluded from every estimate that could feed the model.
SAMPLES = ("non_holdout", "all")


def _samples(p: pd.DataFrame):
    yield "non_holdout", p[~p["in_holdout"]]
    yield "all", p


def _ratio(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b > 0, a / b, np.nan)


# ---------------------------------------------------------------------------
# APR internal checks
# ---------------------------------------------------------------------------

def apr_date_quality(rows: pd.DataFrame) -> pd.DataFrame:
    r = rows[rows["bp_units"].fillna(0) > 0]
    g = r.groupby(["year", "unit_cat", "date_status", "repeat"])["bp_units"].sum().unstack(["date_status", "repeat"], fill_value=0)
    g.columns = [f"{a}{'_repeat' if b else ''}" for a, b in g.columns]
    g = g.T.groupby(level=0).sum().T.reset_index()
    for c in ["date_in_year", "date_missing", "date_earlier", "date_earlier_repeat", "date_later", "date_later_repeat",
              "date_in_year_repeat", "date_missing_repeat"]:
        if c not in g:
            g[c] = 0
    g["bp_units_reported"] = g.drop(columns=["year", "unit_cat"]).sum(axis=1)
    g["bp_units_primary"] = g["date_in_year"] + g["date_in_year_repeat"] + g["date_missing"] + g["date_missing_repeat"]
    g["earlier_repeat_units"] = g["date_earlier_repeat"]
    g["earlier_first_report_units"] = g["date_earlier"]
    g["share_reported_not_primary"] = 1 - _ratio(g["bp_units_primary"], g["bp_units_reported"])
    return g[["year", "unit_cat", "bp_units_reported", "bp_units_primary", "earlier_repeat_units",
              "earlier_first_report_units", "date_later", "date_later_repeat", "date_missing",
              "share_reported_not_primary"]].sort_values(["year", "unit_cat"])


def api_crosscheck(rows: pd.DataFrame, records: list[dict]) -> pd.DataFrame:
    csv = rows.groupby(["year", "unit_cat"]).agg(csv_rows=("bp_units", "size"), csv_bp=("bp_units", "sum")).reset_index()
    api = pd.DataFrame(records).rename(columns={"YEAR": "year", "UNIT_CAT": "unit_cat", "n": "api_rows", "bp": "api_bp"})
    api["year"] = api["year"].astype(int)
    api[["api_rows", "api_bp"]] = api[["api_rows", "api_bp"]].astype(float)
    m = csv.astype({"year": int}).merge(api, on=["year", "unit_cat"], how="outer")
    m["match"] = (m["csv_rows"] == m["api_rows"]) & (m["csv_bp"] == m["api_bp"])
    return m


# ---------------------------------------------------------------------------
# Filing status and the jurisdiction-year panel
# ---------------------------------------------------------------------------

def filing_status(agg: pd.DataFrame, xw: pd.DataFrame, table_a: list[dict], table_d: list[dict]) -> pd.DataFrame:
    """One row per crosswalked HCD jurisdiction x year 2018-2025.

    status: 'a2_rows' (filed, with Table A2 rows), 'filed_no_a2_rows' (rows in Table A or D
    but none in A2: filed with no reportable A2 activity, or an incomplete filing),
    'no_record' (no rows in A, A2 or D: missing or not yet processed). Late filing cannot be
    observed: the open data carry no submission date.
    """
    def ys(recs):
        return {(str(r["JURIS_NAME"]).strip().upper(), int(r["YEAR"])) for r in recs if r.get("YEAR") not in (None, "")}

    a, d = ys(table_a), ys(table_d)
    a2 = set(zip(agg["juris_name"], agg["year"].astype(int)))
    rows = []
    # One row per jurisdiction (census_geoid); any spelling of it counts as filing evidence,
    # and the APR spelling is used as its name.
    x = xw[xw["juris_type"].notna()].sort_values("in_hcd_apr", ascending=False)
    for geoid, grp in x.groupby("census_geoid", sort=True):
        names = list(grp["juris_name"])
        for y in YEARS:
            in_a2 = any((n, y) in a2 for n in names)
            in_a = any((n, y) in a for n in names)
            in_d = any((n, y) in d for n in names)
            st = "a2_rows" if in_a2 else ("filed_no_a2_rows" if (in_a or in_d) else "no_record")
            rows.append({"juris_name": names[0], "census_geoid": geoid, "year": y,
                         "in_table_a2": in_a2, "in_table_a": in_a, "in_table_d": in_d, "filing_status": st})
    return pd.DataFrame(rows)


def bps_to_jurisdiction(bps_place: pd.DataFrame, xw: pd.DataFrame) -> pd.DataFrame:
    """Map BPS place rows to HCD census_geoid. Unincorporated / whole-county rows go to the
    county remainder; a BPS place that is not an HCD jurisdiction (e.g. Mountain House before
    it reports to HCD) is folded into its county remainder and flagged."""
    known = set(xw["census_geoid"].dropna())
    b = bps_place.copy()
    city_geoid = "06" + b["fips_place"]
    uninc = b["fips_place"].isin(["00000", "99990"])
    hcd_city = xw.loc[xw["juris_type"].isin(["city", "city_county"]), "census_geoid"]
    b["census_geoid"] = np.where(~uninc & city_geoid.isin(set(hcd_city)), city_geoid,
                                 "06" + b["county_fips"] + "_UNINC")
    b["bps_mapping"] = np.where(uninc, "county_unincorporated",
                                np.where(city_geoid.isin(set(hcd_city)), "city", "folded_into_county_remainder"))
    b.loc[b["census_geoid"] == "06075_UNINC", "census_geoid"] = "0667000"
    b["known"] = b["census_geoid"].isin(known)
    return b


def bps_missing_cities(xw: pd.DataFrame) -> pd.DataFrame:
    """Cities with no BPS place row in any year 2010-2025 (crosswalk matched_bps False)."""
    m = xw[xw["juris_type"].eq("city") & ~xw["matched_bps"].astype(bool)]
    return m.drop_duplicates("census_geoid")[["census_geoid", "juris_name", "county_fips", "in_hcd_apr"]]


def juris_year_panel(agg: pd.DataFrame, xw: pd.DataFrame, bps_place: pd.DataFrame, den: pd.DataFrame,
                     filers: pd.DataFrame, dedup: pd.DataFrame | None = None,
                     hold: pd.DataFrame | None = None) -> pd.DataFrame:
    xmap = xw.set_index("juris_name")["census_geoid"]
    prim = I.wide_by_unit_cat(agg, "bp_units_primary")
    rep = I.wide_by_unit_cat(agg, "bp_units_reported")
    h = prim.merge(rep[["juris_name", "year"] + [c for c in rep.columns if c not in ("juris_name", "cnty_name", "year")]],
                   on=["juris_name", "year"], suffixes=("", "_reported"))
    if dedup is not None:
        dd = I.wide_by_unit_cat(dedup.rename(columns={"issue_year": "year"}), "bp_units_issue_year_dedup")
        dd = dd.rename(columns={c: f"{c}_dedup" for c in I.UNIT_CAT_CODE.values()})
        h = h.merge(dd.drop(columns="cnty_name"), on=["juris_name", "year"], how="left")
        h[[f"{c}_dedup" for c in I.UNIT_CAT_CODE.values()]] = h[[f"{c}_dedup" for c in I.UNIT_CAT_CODE.values()]].fillna(0)
    h["census_geoid"] = h["juris_name"].map(xmap)
    h = h.drop(columns=["juris_name", "cnty_name"]).groupby(["census_geoid", "year"]).sum().reset_index()
    h["hcd_present"] = True

    b = bps_to_jurisdiction(bps_place[bps_place["year"].isin(YEARS)], xw)
    bcols = ["units_total", "units_total_rep", "1unit_units", "1unit_units_rep", "2units_units", "3_4units_units",
             "5plus_units", "units_2_4"]
    bg = b.groupby(["census_geoid", "year"]).agg(**{c: (c, "sum") for c in bcols},
                                                   bps_rows=("bps_id", "size"),
                                                   bps_months_min=("months_reported", "min"),
                                                   bps_folded_rows=("bps_mapping", lambda s: int((s == "folded_into_county_remainder").sum())))
    bg = bg.rename(columns={c: f"bps_{c}" if not c.startswith("bps") else c for c in bcols}).reset_index()
    bg["bps_present"] = True

    p = h.merge(bg, on=["census_geoid", "year"], how="outer")
    p["hcd_present"] = p["hcd_present"].fillna(False).astype(bool)
    p["bps_present"] = p["bps_present"].fillna(False).astype(bool)
    fs = filers.groupby(["census_geoid", "year"])["filing_status"].first().reset_index()
    p = p.merge(fs, on=["census_geoid", "year"], how="left")
    hcdcols = [c for c in p.columns if c.split("_reported")[0].split("_dedup")[0] in I.UNIT_CAT_CODE.values()]
    # Missing is not zero: HCD unit columns stay NaN where the jurisdiction has no A2 rows.
    p["hcd_nonadu"] = p[NONADU].sum(axis=1, min_count=1)
    p["hcd_nonadu_reported"] = p[[f"{c}_reported" for c in NONADU]].sum(axis=1, min_count=1)
    p["hcd_sf"] = p[["sfd", "sfa"]].sum(axis=1, min_count=1)
    p["hcd_sf_reported"] = p[["sfd_reported", "sfa_reported"]].sum(axis=1, min_count=1)
    extra = ["hcd_nonadu", "hcd_nonadu_reported", "hcd_sf", "hcd_sf_reported"]
    if dedup is not None:
        p["hcd_nonadu_dedup"] = p[[f"{c}_dedup" for c in NONADU]].sum(axis=1, min_count=1)
        p["hcd_sf_dedup"] = p[["sfd_dedup", "sfa_dedup"]].sum(axis=1, min_count=1)
        extra += ["hcd_nonadu_dedup", "hcd_sf_dedup"]
    p.loc[~p["hcd_present"], hcdcols + extra] = np.nan
    p["hcd_sf_plus_adu"] = p["hcd_sf"] + p["adu"]
    p["hcd_nonadu_plus_mh"] = p["hcd_nonadu"] + p["mh"]
    d = den.set_index("geoid")
    p["hu_total_acs"] = p["census_geoid"].map(d["hu_total"])
    p["sf_detached_acs"] = p["census_geoid"].map(d["sf_detached"])
    p["county_fips"] = p["census_geoid"].str[2:5].where(p["census_geoid"].str.endswith("_UNINC"),
                                                         p["census_geoid"].map(xw.drop_duplicates("census_geoid").set_index("census_geoid")["county_fips"]))
    p["juris_name"] = p["census_geoid"].map(xw.drop_duplicates("census_geoid").set_index("census_geoid")["juris_name"])
    p["both_full"] = p["hcd_present"] & p["bps_present"] & (p["bps_months_min"] == 12)
    if hold is not None:
        from missing_middleware.comparison.ca_crosswalk import holdout_flag
        p["in_holdout"] = holdout_flag(p["census_geoid"], hold)
    else:
        p["in_holdout"] = False
    # Cities BPS never lists (bps_missing_city) and their county remainders, whose BPS
    # unincorporated row may include them where the county issues permits under contract.
    miss = bps_missing_cities(xw)
    p["bps_missing_city"] = p["census_geoid"].isin(set(miss["census_geoid"]))
    rem = {f"06{c}_UNINC" for c in miss["county_fips"]}
    p["bps_may_include_cities"] = p["census_geoid"].isin(rem)
    cm = p[p["bps_missing_city"]].groupby(["county_fips", "year"])[["hcd_nonadu", "hcd_sf", "adu"]].sum(min_count=1)
    cm.columns = [f"{c}_bps_missing_cities" for c in cm.columns]
    cm = cm.reset_index().assign(census_geoid=lambda d: "06" + d["county_fips"] + "_UNINC").drop(columns="county_fips")
    p = p.merge(cm, on=["census_geoid", "year"], how="left")
    return p.sort_values(["census_geoid", "year"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def _ols(y, X, names):
    """OLS with classical standard errors. Returns {name: (coef, se)} and R^2."""
    y, X = np.asarray(y, float), np.asarray(X, float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    s2 = resid @ resid / max(n - k, 1)
    cov = s2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    ss_tot = ((y - y.mean()) ** 2).sum()
    return {nm: (b, s) for nm, b, s in zip(names, beta, se)}, 1 - (resid @ resid) / ss_tot if ss_tot else np.nan, n


def table_a_by_year(p: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for samp, pp in _samples(p):
      for y, g in pp.groupby("year"):
        for subset, s in (("all", g), ("both_full_reporting", g[g["both_full"]])):
            rows.append({"jurisdiction_sample": samp, "year": y, "subset": subset, "jurisdictions": len(s),
                         "hcd_nonadu_primary": s["hcd_nonadu"].sum(), "hcd_nonadu_reported": s["hcd_nonadu_reported"].sum(),
                         "hcd_nonadu_issue_year_dedup": s["hcd_nonadu_dedup"].sum(),
                         "hcd_mh": s["mh"].sum(), "bps_units_total": s["bps_units_total"].sum(),
                         "bps_units_total_reported_only": s["bps_units_total_rep"].sum()})
    t = pd.DataFrame(rows)
    t["ratio_hcd_primary_to_bps"] = _ratio(t["hcd_nonadu_primary"], t["bps_units_total"])
    t["ratio_hcd_reported_to_bps"] = _ratio(t["hcd_nonadu_reported"], t["bps_units_total"])
    t["ratio_hcd_dedup_to_bps"] = _ratio(t["hcd_nonadu_issue_year_dedup"], t["bps_units_total"])
    t["ratio_hcd_primary_plus_mh_to_bps"] = _ratio(t["hcd_nonadu_primary"] + t["hcd_mh"], t["bps_units_total"])
    return t


def table_a_by_county(p: pd.DataFrame, counties: pd.DataFrame, fold: pd.DataFrame | None = None) -> pd.DataFrame:
    """County sums of full-reporting jurisdiction-years (descriptive data quality; includes
    holdout jurisdictions, counted in holdout_juris_years). Where the fold test supports it,
    the HCD units of BPS-missing cities are added in the years their county remainder is
    fully reported (hcd_nonadu_folded, ratio_hcd_primary_to_bps_folded)."""
    q = p[p["both_full"]]
    s = q.groupby("county_fips")[["hcd_nonadu", "hcd_nonadu_reported", "bps_units_total"]].sum()
    s["juris_years"] = q.groupby("county_fips").size()
    s["holdout_juris_years"] = q[q["in_holdout"]].groupby("county_fips").size()
    s["holdout_juris_years"] = s["holdout_juris_years"].fillna(0).astype(int)
    s["ratio_hcd_primary_to_bps"] = _ratio(s["hcd_nonadu"], s["bps_units_total"])
    s["ratio_hcd_reported_to_bps"] = _ratio(s["hcd_nonadu_reported"], s["bps_units_total"])
    add = q[q["bps_may_include_cities"]].groupby("county_fips")["hcd_nonadu_bps_missing_cities"].sum()
    s["hcd_nonadu_bps_missing_cities"] = add
    ok = set(fold.loc[fold["fold_supported"], "county_fips"]) if fold is not None else set()
    s["fold_supported"] = s.index.isin(ok)
    s["hcd_nonadu_folded"] = np.where(s["fold_supported"], s["hcd_nonadu"] + s["hcd_nonadu_bps_missing_cities"].fillna(0),
                                      s["hcd_nonadu"])
    s["ratio_hcd_primary_to_bps_folded"] = _ratio(s["hcd_nonadu_folded"], s["bps_units_total"])
    s = s.reset_index().merge(counties[["county_fips", "county_name"]], on="county_fips", how="left")
    s["includes_holdout_jurisdictions"] = True
    return s.sort_values("bps_units_total", ascending=False)


def table_c_bps_missing_cities_fold(p: pd.DataFrame, counties: pd.DataFrame, xw: pd.DataFrame) -> pd.DataFrame:
    """Test of whether BPS counts the BPS-missing cities inside the county unincorporated row.

    Each BPS county file equals the sum of its place rows, so any permits BPS captures for a
    city with no place row must sit in a place row of the same county, most plausibly the
    unincorporated row (county contract permitting). Test, per affected county remainder, on
    the years the remainder is fully reported in both sources: add the cities' HCD units to the
    remainder's HCD units and see whether HCD/BPS moves toward 1, and whether the remainder's
    BPS-minus-HCD excess moves with the cities' HCD units over years. fold_supported = the
    folded non-ADU ratio is closer to 1 (in logs) than the unfolded one. Descriptive only."""
    rows = []
    for g_id, g in p[p["bps_may_include_cities"]].groupby("census_geoid"):
        cf = g_id[2:5]
        miss = bps_missing_cities(xw)
        names = sorted(miss.loc[miss["county_fips"] == cf, "juris_name"])
        f = g[g["both_full"]]
        # All years with both sources present (any BPS months), as a less selective check.
        a = g[g["hcd_present"] & g["bps_present"]]
        ra0 = _ratio(a["hcd_nonadu"].sum(), a["bps_units_total"].sum()).item()
        ra1 = _ratio(a["hcd_nonadu"].sum() + a["hcd_nonadu_bps_missing_cities"].sum(), a["bps_units_total"].sum()).item()
        city_nonadu = f["hcd_nonadu_bps_missing_cities"]
        b, h = f["bps_units_total"].sum(), f["hcd_nonadu"].sum()
        c = city_nonadu.sum()
        b1, sf, csf = f["bps_1unit_units"].sum(), f["hcd_sf"].sum(), f["hcd_sf_bps_missing_cities"].sum()
        r0, r1 = _ratio(h, b).item(), _ratio(h + c, b).item()
        s0, s1 = _ratio(sf, b1).item(), _ratio(sf + csf, b1).item()
        resid = f["bps_units_total"] - f["hcd_nonadu"]
        corr = (np.corrcoef(resid, city_nonadu.fillna(0))[0, 1]
                if len(f) >= 4 and resid.std() > 0 and city_nonadu.fillna(0).std() > 0 else np.nan)
        rows.append({"county_fips": cf, "census_geoid": g_id, "bps_missing_cities": ";".join(names),
                     "n_cities": len(names), "remainder_in_holdout": bool(g["in_holdout"].iloc[0]),
                     "remainder_full_years": len(f),
                     "city_hcd_years_present_in_those_years": int(city_nonadu.notna().sum()),
                     "remainder_hcd_nonadu": h, "cities_hcd_nonadu": c, "remainder_bps_total": b,
                     "ratio_hcd_to_bps_before": r0, "ratio_hcd_to_bps_folded": r1,
                     "remainder_hcd_sf": sf, "cities_hcd_sf": csf, "remainder_bps_1unit": b1,
                     "ratio_hcd_sf_to_bps1_before": s0, "ratio_hcd_sf_to_bps1_folded": s1,
                     "corr_bps_excess_with_city_hcd_over_years": corr,
                     "years_both_present": len(a), "ratio_hcd_to_bps_before_all_years": ra0,
                     "ratio_hcd_to_bps_folded_all_years": ra1,
                     "fold_supported": bool(c > 0 and np.isfinite(r0) and np.isfinite(r1)
                                            and abs(np.log(r1)) < abs(np.log(r0)))})
    out = pd.DataFrame(rows).merge(counties[["county_fips", "county_name"]], on="county_fips", how="left")
    out["includes_holdout_jurisdictions"] = True
    return out.sort_values("county_fips")


def largest(p: pd.DataFrame, n: int = 50) -> list[str]:
    hu = p.drop_duplicates("census_geoid").set_index("census_geoid")["hu_total_acs"].dropna()
    return list(hu.sort_values(ascending=False).index[:n])


def table_a_top50(p: pd.DataFrame) -> pd.DataFrame:
    top = largest(p)
    q = p[p["census_geoid"].isin(top)]
    pooled = q[q["both_full"]].groupby("census_geoid")[["hcd_nonadu", "hcd_nonadu_reported", "bps_units_total"]].sum()
    pooled["full_years"] = q[q["both_full"]].groupby("census_geoid").size()
    pooled["ratio_primary_pooled"] = _ratio(pooled["hcd_nonadu"], pooled["bps_units_total"])
    pooled["ratio_reported_pooled"] = _ratio(pooled["hcd_nonadu_reported"], pooled["bps_units_total"])
    q = q.assign(r=_ratio(q["hcd_nonadu"], q["bps_units_total"]))
    yr = q.pivot_table(index="census_geoid", columns="year", values="r")
    yr.columns = [f"ratio_{c}" for c in yr.columns]
    meta = q.drop_duplicates("census_geoid").set_index("census_geoid")[["juris_name", "hu_total_acs", "in_holdout",
                                                                       "bps_may_include_cities"]]
    out = meta.join(pooled).join(yr).reset_index()
    out["abs_log_ratio"] = np.abs(np.log(out["ratio_primary_pooled"]))
    return out.sort_values("hu_total_acs", ascending=False)


def table_a_mismatches(p: pd.DataFrame, n: int = 40) -> pd.DataFrame:
    q = p[p["hcd_present"] & p["bps_present"]].copy()
    q["diff_primary_minus_bps"] = q["hcd_nonadu"] - q["bps_units_total"]
    q["diff_reported_minus_bps"] = q["hcd_nonadu_reported"] - q["bps_units_total"]
    q["abs_diff"] = q["diff_primary_minus_bps"].abs()
    cols = ["census_geoid", "juris_name", "in_holdout", "year", "hcd_nonadu", "hcd_nonadu_reported", "bps_units_total",
            "bps_units_total_rep", "bps_months_min", "diff_primary_minus_bps", "diff_reported_minus_bps", "filing_status"]
    return q.sort_values("abs_diff", ascending=False)[cols].head(n)


def table_b_by_year(p: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for samp, pp in _samples(p):
      for y, g in pp.groupby("year"):
        s = g[g["both_full"]]
        rows.append({"jurisdiction_sample": samp, "year": y, "jurisdictions": len(s), "bps_1unit": s["bps_1unit_units"].sum(),
                     "bps_2_4": s["bps_units_2_4"].sum(), "bps_5plus": s["bps_5plus_units"].sum(),
                     "hcd_sfd": s["sfd"].sum(), "hcd_sfa": s["sfa"].sum(), "hcd_adu": s["adu"].sum(),
                     "hcd_sf_reported": s["hcd_sf_reported"].sum(), "hcd_adu_reported": s["adu_reported"].sum(),
                     "hcd_sf_dedup": s["hcd_sf_dedup"].sum(), "hcd_adu_dedup": s["adu_dedup"].sum(),
                     "hcd_mh": s["mh"].sum(), "hcd_2_4": s["u2_4"].sum(), "hcd_5plus": s["u5plus"].sum()})
    t = pd.DataFrame(rows)
    t["ratio_bps1_to_hcd_sf"] = _ratio(t["bps_1unit"], t["hcd_sfd"] + t["hcd_sfa"])
    t["ratio_bps1_to_hcd_sf_plus_adu"] = _ratio(t["bps_1unit"], t["hcd_sfd"] + t["hcd_sfa"] + t["hcd_adu"])
    t["ratio_bps1_to_hcd_sf_reported"] = _ratio(t["bps_1unit"], t["hcd_sf_reported"])
    t["ratio_bps1_to_hcd_sf_plus_adu_reported"] = _ratio(t["bps_1unit"], t["hcd_sf_reported"] + t["hcd_adu_reported"])
    t["ratio_bps1_to_hcd_sf_dedup"] = _ratio(t["bps_1unit"], t["hcd_sf_dedup"])
    t["ratio_bps1_to_hcd_sf_plus_adu_dedup"] = _ratio(t["bps_1unit"], t["hcd_sf_dedup"] + t["hcd_adu_dedup"])
    t["bps1_minus_hcd_sf"] = t["bps_1unit"] - t["hcd_sfd"] - t["hcd_sfa"]
    t["bps1_excess_as_share_of_hcd_adu"] = _ratio(t["bps1_minus_hcd_sf"], t["hcd_adu"])
    t["ratio_bps2_4_to_hcd_2_4"] = _ratio(t["bps_2_4"], t["hcd_2_4"])
    t["ratio_bps5_to_hcd_5"] = _ratio(t["bps_5plus"], t["hcd_5plus"])
    return t


def table_b_regressions(p: pd.DataFrame) -> pd.DataFrame:
    """Where do HCD ADUs land in BPS? Coefficients near 1 mean the BPS category moves one for
    one with HCD ADUs; near 0 means BPS does not count them there. Pooled (no intercept),
    within-jurisdiction, and jurisdiction + year fixed-effect versions, on jurisdiction-years
    with full reporting in both sources. Descriptive associations: ADU growth is correlated with
    other construction trends, so coefficients are read alongside the level ratios."""
    q = p[p["both_full"]].copy()
    specs = {
        "bps_1unit ~ hcd_sf + hcd_adu": ("bps_1unit_units", ["hcd_sf", "adu"]),
        "bps_1unit ~ hcd_sf + hcd_adu + hcd_mh": ("bps_1unit_units", ["hcd_sf", "adu", "mh"]),
        "bps_2_4 ~ hcd_2_4 + hcd_adu": ("bps_units_2_4", ["u2_4", "adu"]),
        "bps_5plus ~ hcd_5plus + hcd_adu": ("bps_5plus_units", ["u5plus", "adu"]),
        "bps_total ~ hcd_nonadu + hcd_adu": ("bps_units_total", ["hcd_nonadu", "adu"]),
        "bps_total ~ hcd_nonadu + hcd_adu + hcd_mh": ("bps_units_total", ["hcd_nonadu", "adu", "mh"]),
    }
    rows = []
    nh = q[~q["in_holdout"]]
    for samp, sample, s in (("non_holdout", "full-reporting", nh),
                            ("non_holdout", "excl. City of Los Angeles", nh[nh["census_geoid"] != LA_CITY]),
                            ("all", "full-reporting", q),
                            ("all", "excl. City of Los Angeles", q[q["census_geoid"] != LA_CITY])):
        for label, (yv, xs) in specs.items():
            for kind in ("pooled", "within_jurisdiction", "jurisdiction_and_year_fe"):
                d = s[[yv] + xs + ["census_geoid", "year"]].dropna()
                if kind != "pooled":
                    d = d.copy()
                    # Alternating projections: exact for jurisdiction FE; converges to two-way FE.
                    for _ in range(1 if kind == "within_jurisdiction" else 50):
                        for c in [yv] + xs:
                            d[c] = d[c] - d.groupby("census_geoid")[c].transform("mean")
                            if kind == "jurisdiction_and_year_fe":
                                d[c] = d[c] - d.groupby("year")[c].transform("mean")
                res, r2, n = _ols(d[yv], d[xs], xs)
                row = {"jurisdiction_sample": samp, "sample": sample, "model": label, "kind": kind, "n_juris_years": n, "r2": r2}
                for k, (b, se) in res.items():
                    row[f"coef_{k}"], row[f"se_{k}"] = b, se
                rows.append(row)
    return pd.DataFrame(rows)


def table_b_baseline_adjusted(p: pd.DataFrame) -> pd.DataFrame:
    """Level check net of the BPS-vs-HCD single-family gap that exists without ADUs.

    baseline = BPS 1-unit / HCD SFD+SFA in full-reporting jurisdiction-years with zero HCD ADUs
    (mostly small places, so a rough benchmark). implied_adu_share_in_bps1 =
    (BPS 1-unit - baseline x HCD SF) / HCD ADUs.
    """
    rows = []
    for samp, pp in _samples(p):
      q = pp[pp["both_full"]]
      z = q[q["adu"] == 0]
      base = z["bps_1unit_units"].sum() / z["hcd_sf"].sum()
      for label, s in (("all", q), ("excl. City of Los Angeles", q[q["census_geoid"] != LA_CITY]),
                       ("City of Los Angeles", q[q["census_geoid"] == LA_CITY])):
        if s.empty:
            continue
        b1, sf, adu = s["bps_1unit_units"].sum(), s["hcd_sf"].sum(), s["adu"].sum()
        rows.append({"jurisdiction_sample": samp, "sample": label, "juris_years": len(s), "bps_1unit": b1, "hcd_sf": sf, "hcd_adu": adu,
                     "ratio_bps1_to_sf": b1 / sf, "ratio_bps1_to_sf_plus_adu": b1 / (sf + adu),
                     "baseline_ratio_zero_adu_juris_years": base, "baseline_juris_years": len(z),
                     "implied_adu_share_in_bps1": (b1 - base * sf) / adu if adu else np.nan,
                     "unadjusted_excess_share": (b1 - sf) / adu if adu else np.nan})
    return pd.DataFrame(rows)


MEASURES = {"primary": ("hcd_sf", "adu"), "as_reported": ("hcd_sf_reported", "adu_reported"),
            "issue_year_dedup": ("hcd_sf_dedup", "adu_dedup")}


def _share(b1, sf, adu, zb1, zsf):
    base = zb1 / zsf
    return (b1 - base * sf) / adu, base


def table_b_share_sensitivity(p: pd.DataFrame, regressions: pd.DataFrame | None = None,
                              draws: int = BOOTSTRAP_DRAWS, seed: int = BOOTSTRAP_SEED) -> pd.DataFrame:
    """How sensitive is 'the share of HCD ADUs inside BPS 1-unit' to reasonable choices?

    share = (BPS 1-unit - baseline x HCD SF) / HCD ADU, baseline = BPS 1-unit / HCD SF in
    full-reporting jurisdiction-years with zero HCD ADUs. Variants: the three HCD measures;
    a jurisdiction-cluster bootstrap (percentile interval); baselines restricted to places with
    at least 5k / 10k / 20k ACS one-unit detached homes; a baseline and share computed year by
    year; excluding the City of Los Angeles; and the ADU coefficients of the BPS 1-unit
    regressions. Computed for non-holdout jurisdictions (the figures to use) and all
    jurisdictions (shown beside them). The spread is the finding: no single value is identified.
    """
    rows = []

    def add(samp, analysis, variant, measure, est, lo=np.nan, hi=np.nan, n=np.nan, nb=np.nan, base=np.nan, note=""):
        rows.append({"jurisdiction_sample": samp, "analysis": analysis, "variant": variant, "measure": measure,
                     "estimate": est, "ci_low": lo, "ci_high": hi, "n_juris_years": n,
                     "n_baseline_juris_years": nb, "baseline_ratio": base, "note": note})

    for samp, pp in _samples(p):
        q = pp[pp["both_full"]]
        for la_label, qq in (("all jurisdictions", q), ("excl. City of Los Angeles", q[q["census_geoid"] != LA_CITY])):
            for m, (sfc, aduc) in MEASURES.items():
                z = qq[qq[aduc] == 0]
                est, base = _share(qq["bps_1unit_units"].sum(), qq[sfc].sum(), qq[aduc].sum(),
                                   z["bps_1unit_units"].sum(), z[sfc].sum())
                add(samp, "baseline_adjusted", la_label, m, est, n=len(qq), nb=len(z), base=base)
                if la_label != "all jurisdictions":
                    continue
                # Jurisdiction-cluster bootstrap
                d = qq.assign(_z=qq[aduc] == 0)
                g = d.groupby("census_geoid")
                arr = pd.DataFrame({"b1": g["bps_1unit_units"].sum(), "sf": g[sfc].sum(), "adu": g[aduc].sum(),
                                    "zb1": d[d["_z"]].groupby("census_geoid")["bps_1unit_units"].sum(),
                                    "zsf": d[d["_z"]].groupby("census_geoid")[sfc].sum()}).fillna(0).to_numpy()
                rng = np.random.default_rng(seed)
                n = len(arr)
                w = np.stack([np.bincount(rng.integers(0, n, n), minlength=n) for _ in range(draws)])
                t = w @ arr
                bs, _ = _share(t[:, 0], t[:, 1], t[:, 2], t[:, 3], t[:, 4])
                add(samp, "bootstrap_jurisdiction_cluster", f"{draws} draws, seed {seed}, median and 95% percentile interval",
                    m, float(np.median(bs)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), n=len(qq),
                    nb=len(z), base=base)
                if m != "primary":
                    continue
                # Baselines restricted to larger places
                for k in BASELINE_MIN_SF_DETACHED:
                    zk = z[z["sf_detached_acs"] >= k]
                    est_k, base_k = (_share(qq["bps_1unit_units"].sum(), qq[sfc].sum(), qq[aduc].sum(),
                                            zk["bps_1unit_units"].sum(), zk[sfc].sum()) if len(zk) else (np.nan, np.nan))
                    add(samp, "baseline_min_size", f"baseline from places with >= {k:,} one-unit detached homes", m,
                        est_k, n=len(qq), nb=len(zk), base=base_k)
                add(samp, "baseline_min_size", "median one-unit detached homes in baseline places", m,
                    float(z["sf_detached_acs"].median()), nb=len(z), note="not a share; size of baseline places")
                # Year by year
                for y, qy in qq.groupby("year"):
                    zy = qy[qy[aduc] == 0]
                    est_y, base_y = _share(qy["bps_1unit_units"].sum(), qy[sfc].sum(), qy[aduc].sum(),
                                           zy["bps_1unit_units"].sum(), zy[sfc].sum())
                    add(samp, "by_year", str(int(y)), m, est_y, n=len(qy), nb=len(zy), base=base_y)
    if regressions is not None:
        r = regressions[regressions["model"] == "bps_1unit ~ hcd_sf + hcd_adu"]
        for _, x in r.iterrows():
            add(x["jurisdiction_sample"], "regression_adu_coefficient", f"{x['kind']}; {x['sample']}", "primary",
                x["coef_adu"], x["coef_adu"] - 1.96 * x["se_adu"], x["coef_adu"] + 1.96 * x["se_adu"],
                n=x["n_juris_years"], note=f"HCD SF coefficient {x['coef_hcd_sf']:.2f}; classical SE")
    return pd.DataFrame(rows)


def table_b_top50(p: pd.DataFrame) -> pd.DataFrame:
    top = largest(p)
    rows = []
    for g_id, g in p[p["census_geoid"].isin(top) & p["both_full"]].groupby("census_geoid"):
        sf, adu, b1 = g["hcd_sf"].values, g["adu"].values, g["bps_1unit_units"].values
        rec = {"census_geoid": g_id, "juris_name": g["juris_name"].iloc[0], "in_holdout": bool(g["in_holdout"].iloc[0]),
               "hu_total_acs": g["hu_total_acs"].iloc[0],
               "full_years": len(g), "bps_1unit": b1.sum(), "hcd_sf": sf.sum(), "hcd_adu": adu.sum(),
               "ratio_bps1_to_sf": _ratio(b1.sum(), sf.sum()).item(),
               "ratio_bps1_to_sf_plus_adu": _ratio(b1.sum(), (sf + adu).sum()).item(),
               "ratio_bps1_to_sf_reported": _ratio(b1.sum(), g["hcd_sf_reported"].sum()).item(),
               "ratio_bps1_to_sf_plus_adu_reported": _ratio(b1.sum(), (g["hcd_sf_reported"] + g["adu_reported"]).sum()).item(),
               "ratio_bps_total_to_hcd_nonadu": _ratio(g["bps_units_total"].sum(), g["hcd_nonadu"].sum()).item(),
               "ratio_bps_total_to_hcd_nonadu_plus_adu": _ratio(g["bps_units_total"].sum(), (g["hcd_nonadu"] + adu).sum()).item()}
        if len(g) >= 4:
            rec["corr_bps1_sf"] = np.corrcoef(b1, sf)[0, 1] if np.std(sf) > 0 and np.std(b1) > 0 else np.nan
            rec["corr_bps1_sf_plus_adu"] = np.corrcoef(b1, sf + adu)[0, 1] if np.std(sf + adu) > 0 and np.std(b1) > 0 else np.nan
            res, _, _ = _ols(b1, np.c_[sf, adu], ["sf", "adu"])
            rec["coef_adu_pooled"], rec["se_adu_pooled"] = res["adu"]
        d1, d2 = abs(np.log(rec["ratio_bps1_to_sf"])) if rec["ratio_bps1_to_sf"] > 0 else np.inf, \
            abs(np.log(rec["ratio_bps1_to_sf_plus_adu"])) if rec["ratio_bps1_to_sf_plus_adu"] > 0 else np.inf
        rec["closer_level_match"] = "sf_only" if d1 < d2 else "sf_plus_adu"
        rec["adu_share_of_sf_plus_adu"] = _ratio(adu.sum(), (sf + adu).sum()).item()
        rows.append(rec)
    return pd.DataFrame(rows).sort_values("hu_total_acs", ascending=False)


def table_c_coverage(p: pd.DataFrame, filers: pd.DataFrame, bps_place: pd.DataFrame) -> dict[str, pd.DataFrame]:
    q = p.copy()
    bps_rep = q["bps_present"] & (q["bps_months_min"].fillna(0) > 0)
    q["coverage"] = np.select([q["hcd_present"] & bps_rep, q["hcd_present"] & ~bps_rep, ~q["hcd_present"] & bps_rep],
                              ["both", "hcd_only", "bps_only"], default="neither_with_data")
    cov = pd.concat([s.groupby(["year", "coverage"]).size().unstack(fill_value=0).reset_index()
                     .assign(jurisdiction_sample=samp) for samp, s in _samples(q)], ignore_index=True)
    one = q[q["coverage"].isin(["hcd_only", "bps_only"])][["census_geoid", "juris_name", "in_holdout", "year", "coverage",
                                                           "filing_status", "hcd_nonadu", "adu", "bps_units_total",
                                                           "bps_months_min"]]
    fil = pd.concat([s.groupby(["year", "filing_status"]).size().unstack(fill_value=0).reset_index()
                     .assign(jurisdiction_sample=samp) for samp, s in _samples(filers)], ignore_index=True)
    nr = filers[filers["filing_status"] != "a2_rows"][["juris_name", "census_geoid", "in_holdout", "year", "filing_status",
                                                        "in_table_a", "in_table_d"]]
    b = bps_place[bps_place["year"].isin(range(2010, 2026))]
    imp = b.groupby("year").agg(places=("bps_id", "size"),
                                places_12_months=("months_reported", lambda s: int((s == 12).sum())),
                                places_0_months=("months_reported", lambda s: int((s == 0).sum())),
                                places_partial=("months_reported", lambda s: int(((s > 0) & (s < 12)).sum())),
                                units_total=("units_total", "sum"), units_reported=("units_total_rep", "sum")).reset_index()
    imp["imputed_units"] = imp["units_total"] - imp["units_reported"]
    imp["imputed_share"] = _ratio(imp["imputed_units"], imp["units_total"])
    imp["includes_holdout_jurisdictions"] = True
    return {"c_coverage_by_year": cov, "c_one_source_only": one, "c_apr_filing_by_year": fil,
            "c_apr_not_filed_or_no_a2": nr, "c_bps_imputation_by_year": imp}


def table_d_compilation(comp: pd.DataFrame, agg: pd.DataFrame, xw: pd.DataFrame,
                        hold: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    a = agg[(agg["unit_cat"] == "ADU") & agg["year"].isin([2018, 2019])]
    a = a.groupby(["juris_name", "year"])[["bp_units_primary", "bp_units_reported"]].sum().reset_index()
    xmap = xw.set_index("juris_name")["census_geoid"]
    c = comp[comp["year"].isin([2018, 2019])].assign(census_geoid=lambda d: d["juris_name"].map(xmap))
    a = a.assign(census_geoid=a["juris_name"].map(xmap)).groupby(["census_geoid", "year"])[["bp_units_primary", "bp_units_reported"]].sum().reset_index()
    m = c.merge(a, on=["census_geoid", "year"], how="outer", suffixes=("_comp", "_apr"))
    if hold is not None:
        from missing_middleware.comparison.ca_crosswalk import holdout_flag
        m["in_holdout"] = holdout_flag(m["census_geoid"], hold)
    else:
        m["in_holdout"] = False
    m["in_compilation"] = m["adu_permits"].notna()
    m["in_apr_adu_rows"] = m["bp_units_reported"].notna()
    m["diff_comp_minus_apr_reported"] = m["adu_permits"] - m["bp_units_reported"].fillna(0)
    m["diff_comp_minus_apr_primary"] = m["adu_permits"] - m["bp_units_primary"].fillna(0)
    rows = []
    for samp, mm in _samples(m):
      for y, g in mm.groupby("year"):
        both = g[g["in_compilation"]]
        rp = both["bp_units_reported"].fillna(0)
        rows.append({"jurisdiction_sample": samp, "year": y, "compilation_rows": int(g["in_compilation"].sum()),
                     "apr_juris_with_adu_rows": int(g["in_apr_adu_rows"].sum()),
                     "compilation_total": both["adu_permits"].sum(),
                     "apr_reported_total_all": g["bp_units_reported"].sum(),
                     "apr_primary_total_all": g["bp_units_primary"].sum(),
                     "apr_reported_same_jurisdictions": rp.sum(),
                     "exact_equal_reported": int((both["adu_permits"] == rp).sum()),
                     "exact_equal_primary": int((both["adu_permits"] == both["bp_units_primary"].fillna(0)).sum()),
                     "within_10pct_or_2_reported": int(((both["adu_permits"] - rp).abs() <= np.maximum(2, 0.1 * rp)).sum()),
                     "corr_reported": np.corrcoef(both["adu_permits"], rp)[0, 1],
                     "compilation_positive_apr_zero_or_absent": int(((both["adu_permits"] > 0) & (rp == 0)).sum()),
                     "apr_positive_compilation_zero": int(((both["adu_permits"] == 0) & (rp > 0)).sum())})
    summ = pd.DataFrame(rows)
    m["abs_diff"] = m["diff_comp_minus_apr_reported"].abs()
    top = m.sort_values("abs_diff", ascending=False).head(30).drop(columns="abs_diff")
    return {"d_compilation_vs_apr_summary": summ, "d_compilation_vs_apr_juris": m.drop(columns="abs_diff"),
            "d_compilation_vs_apr_largest_diffs": top}


def all_tables(p, bps_county, counties, comp, agg, xw, filers, bps_place, hold=None) -> dict[str, pd.DataFrame]:
    fold = table_c_bps_missing_cities_fold(p, counties, xw)
    reg = table_b_regressions(p)
    t = {"a_nonadu_by_year": table_a_by_year(p), "a_nonadu_by_county": table_a_by_county(p, counties, fold),
         "a_nonadu_top50": table_a_top50(p), "a_nonadu_largest_mismatches": table_a_mismatches(p),
         "b_one_unit_by_year": table_b_by_year(p), "b_adu_placement_regressions": reg,
         "b_one_unit_baseline_adjusted": table_b_baseline_adjusted(p),
         "b_adu_share_sensitivity": table_b_share_sensitivity(p, reg),
         "b_one_unit_top50": table_b_top50(p), "c_bps_missing_cities_fold": fold}
    if "in_holdout" not in filers:
        filers = filers.assign(in_holdout=False)
    t.update(table_c_coverage(p, filers, bps_place))
    t.update(table_d_compilation(comp, agg, xw, hold))
    # BPS county files vs the sum of BPS places (internal BPS consistency, 2018-2025)
    pc = bps_place[bps_place["year"].isin(YEARS)].groupby(["year", "county_fips"])["units_total"].sum()
    cc = bps_county[bps_county["year"].isin(YEARS)].set_index(["year", "county_fips"])["units_total"]
    t["c_bps_county_vs_places"] = pd.DataFrame({"county_file": cc, "sum_places": pc}).reset_index().assign(
        diff=lambda d: d["county_file"] - d["sum_places"], includes_holdout_jurisdictions=True)
    return t


# ---------------------------------------------------------------------------
# Statewide view: BPS permitted units per 1,000 existing homes, WI and CA
# ---------------------------------------------------------------------------

def statewide_bps_per_1000(ca_state: pd.DataFrame, wi_state_dir: Path, pep: dict) -> pd.DataFrame:
    """Annual BPS units (with Census imputation) per 1,000 PEP housing units (July 1 of the
    same year). 2010-2019 denominators from PEP Vintage 2020; 2020-2025 from Vintage 2025.
    Indexed to each state's own 2014-2016 mean rate (=100). Descriptive only."""
    # The BPS annual state file is national; the California BPS pull already holds 2010-2025.
    wi = pd.concat([read_bps(Path(wi_state_dir) / f"state_{y}.txt", "state", state_fips="55")
                    for y in range(2010, 2026)])
    bps = {"06": ca_state, "55": wi}
    rows = []
    for st, (v20, v25) in pep.items():
        hu = pd.concat([I.read_pep_v2020_state(v20).query("year < 2020").assign(hu_vintage="PEP Vintage 2020"),
                        I.read_pep_v2025_state(v25).assign(hu_vintage="PEP Vintage 2025")])
        b = bps[st][["year", "units_total", "1unit_units", "units_2_4", "5plus_units", "units_total_rep"]]
        m = b.merge(hu[["year", "housing_units", "hu_vintage"]], on="year", how="left")
        m.insert(0, "state", {"06": "California", "55": "Wisconsin"}[st])
        m.insert(1, "state_fips", st)
        rows.append(m)
    out = pd.concat(rows, ignore_index=True)
    out["units_per_1000_homes"] = 1000 * out["units_total"] / out["housing_units"]
    out["one_unit_per_1000_homes"] = 1000 * out["1unit_units"] / out["housing_units"]
    base = out[out["year"].between(2014, 2016)].groupby("state")["units_per_1000_homes"].mean()
    out["index_2014_2016_eq_100"] = 100 * out["units_per_1000_homes"] / out["state"].map(base)
    out["bps_source"] = "Census BPS annual state file (estimates with imputation)"
    out["includes_holdout_jurisdictions"] = True
    out["value_status"] = "calculated"
    return out

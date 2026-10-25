"""ADUs on multifamily lots in California's HCD APR Table A2, and the benchmark cap.

The challenge benchmark is one ADU on a parcel with an existing single-family home.
California law also lets multifamily properties add ADUs (Gov. Code 66323), so Table A2's
ADU counts can include ADUs on multifamily lots. This module measures that from A2 alone,
with three rules, and checks it against one validation-only source (the Los Angeles County
Assessor roll):

1. APN-year rule (``apn_year_band``). ADU units on one APN in one jurisdiction-year.
   Before the cutoff (main 2023-01-01, when HCD began saying a single-family lot could have
   three ADUs; owner-provided): 2 units = "possible" (ADU + JADU was already allowed on a
   single-family lot), 3+ = "definite". From the cutoff: 3 = "possible", 4+ = "definite".
2. Unit-category rule (``mf_unitcat``). The same APN appears in A2, in any year, with
   UNIT_CAT "2 to 4" or "5+" (a multifamily project on the same parcel). Counted as possible
   (the LA County check shows it is right less than half the time).
3. Benchmark cap (``add_order``). At most 2 ADU units per APN, cumulated across 2018-2025 in
   permit order; units beyond 2 are out of benchmark whatever the lot type. The same
   ordering gives each unit its order on the parcel (1st, 2nd, 3rd or later).

Plus an ecological check (``acs_mf_share`` and ``ecological_fits``): across jurisdictions,
the 2023-2025 ADU rate per 1,000 one-unit detached homes regressed on the share of housing
units in 2+-unit structures (ACS B25024), with the pooled model's value, income and size terms.

APNs are read from Table A2 only in memory and never leave this module; every output is a
count by jurisdiction and year.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_inputs as I
from missing_middleware.comparison import ca_regression as R
from missing_middleware.comparison import ca_study as S

MAIN_CUTOFF = pd.Timestamp("2023-01-01")
SENSITIVITY_CUTOFFS = (pd.Timestamp("2021-01-01"), pd.Timestamp("2022-01-01"), pd.Timestamp("2023-01-01"))
CAP = 2
A2_YEARS = tuple(range(2018, 2026))
MF_UNIT_CATS = ("2 to 4", "5+")
_BAD_APN = {"NULL", "NONE", "NA", "TBD", "JADU", "ADU", "UNKNOWN", "VARIOUS", "MULTIPLE", "PENDING", "NOAPN"}


# ---------------------------------------------------------------------------
# Reading Table A2 with APNs (in memory only)
# ---------------------------------------------------------------------------

def normalize_apn(apn: pd.Series) -> pd.Series:
    """Upper-case letters and digits only. Placeholders become NA: fewer than 5 characters,
    one repeated character (0, 0000000000, 9999999999), no digit at all, or a word such as TBD."""
    s = apn.fillna("").astype(str).str.upper().str.replace(r"[^0-9A-Z]", "", regex=True)
    bad = (s.str.len() < 5) | s.str.fullmatch(r"(.)\1*") | ~s.str.contains(r"\d") | s.isin(_BAD_APN)
    return s.mask(bad)


def read_a2_adu_rows(path: str | Path) -> tuple[pd.DataFrame, set]:
    """Table A2 ADU listings in the study's main measure (adu_main), with normalized APNs.

    Same selection as ``ca_study.hcd_adu_outcome``: UNIT_CAT ADU, building-permit units > 0,
    permit dated in the report year or undated, and the permit not excluded by TEXT_RULES.
    Returns (rows, mf_keys): rows has juris_name, cnty_name, year, units, issue_date,
    permit_key, apn; mf_keys is the set of (juris_name, apn) listed with UNIT_CAT 2 to 4 or 5+.
    """
    rows = I.classify_permit_rows(I.read_apr_a2(path))
    raw = pd.read_csv(path, usecols=["APN", "NOTES", "PROJECT_NAME", "BP_ISSUE_DT1"], dtype=str, low_memory=False)
    raw.index = rows.index
    flag = S.classify_adu_text(raw["NOTES"].fillna("") + " | " + raw["PROJECT_NAME"].fillna(""))
    rows["apn"] = normalize_apn(raw["APN"])
    rows["issue_date"] = pd.to_datetime(raw["BP_ISSUE_DT1"], errors="coerce")
    mf = rows[rows["unit_cat"].isin(MF_UNIT_CATS) & rows["apn"].notna()]
    mf_keys = set(zip(mf["juris_name"], mf["apn"]))
    r = rows[rows["unit_cat"].eq("ADU") & rows["bp_units"].fillna(0).gt(0)].copy()
    r["text_flag"] = flag.reindex(r.index).fillna("kept")
    flagged = set(r.loc[r["text_flag"].ne("kept"), "permit_key"])
    r = r[~r["permit_key"].isin(flagged) & r["date_status"].isin(["date_in_year", "date_missing"])]
    out = r[["juris_name", "cnty_name", "year", "bp_units", "issue_date", "permit_key", "apn"]].rename(columns={"bp_units": "units"})
    out["year"] = out["year"].astype(int)
    return out.reset_index(drop=True), mf_keys


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def apn_year_band(rows: pd.DataFrame, cutoff: pd.Timestamp = MAIN_CUTOFF) -> pd.DataFrame:
    """Adds n_apn_year (ADU units on the APN in that jurisdiction-year) and band:
    'unknown_apn', 'single' (within a single-family allowance), 'possible' or 'definite'."""
    r = rows.copy()
    known = r["apn"].notna()
    n = r[known].groupby(["juris_name", "year", "apn"])["units"].transform("sum")
    r["n_apn_year"] = n.reindex(r.index)
    post = pd.to_datetime(r["year"].astype(str) + "-01-01") >= cutoff
    lo = np.where(post, 3, 2)          # first count that is "possible"
    r["band"] = np.select([~known, r["n_apn_year"] >= lo + 1, r["n_apn_year"] >= lo],
                          ["unknown_apn", "definite", "possible"], default="single")
    return r


def mf_unitcat(rows: pd.DataFrame, mf_keys: set) -> pd.Series:
    """True where the jurisdiction-APN also has a 2 to 4 or 5+ listing in A2 (any year)."""
    keys = pd.Series(list(zip(rows["juris_name"], rows["apn"].fillna(""))), index=rows.index, dtype=object)
    return rows["apn"].notna() & keys.map(lambda k: k in mf_keys).astype(bool)


def add_order(rows: pd.DataFrame, cap: int = CAP) -> pd.DataFrame:
    """Order of each ADU unit on its parcel, cumulated across years (jurisdiction + APN), in
    the order report year, permit date, permit key. Adds u_order1, u_order2, u_order3p (units
    that are the parcel's 1st, 2nd, 3rd-or-later ADU; u_order3p = u_order3 + u_order4p), cap_kept, cap_removed and apn_cum (the
    APN's total over all years). Rows with no usable APN cannot be ordered: they count as 1st
    ADUs (cap_kept = units) and are reported separately as unknown."""
    r = rows.copy()
    r["_d"] = r["issue_date"].fillna(pd.to_datetime(r["year"].astype(str) + "-12-31"))
    r = r.sort_values(["juris_name", "apn", "year", "_d", "permit_key"], kind="mergesort")
    known = r["apn"].notna()
    u = r["units"].astype(float)
    g = r[known].groupby(["juris_name", "apn"])["units"]
    before = (g.cumsum() - r.loc[known, "units"]).reindex(r.index).fillna(0)
    start, end = before + 1, before + u
    o1 = ((start <= 1) & (end >= 1)).astype(float)
    o2 = ((start <= 2) & (end >= 2)).astype(float)
    r["u_order1"] = np.where(known, o1, u)
    r["u_order2"] = np.where(known, o2, 0.0)
    o3 = ((start <= 3) & (end >= 3)).astype(float)
    r["u_order3p"] = np.where(known, u - o1 - o2, 0.0)
    r["u_order3"] = np.where(known, o3, 0.0)
    r["u_order4p"] = r["u_order3p"] - r["u_order3"]
    kept = np.minimum(end, cap) - np.minimum(before, cap)
    r["cap_kept"] = np.where(known, kept, u)
    r["cap_removed"] = u - r["cap_kept"]
    r["apn_cum"] = g.transform("sum").reindex(r.index)
    return r.drop(columns="_d").sort_index()


def annotate(rows: pd.DataFrame, mf_keys: set, cutoff: pd.Timestamp = MAIN_CUTOFF) -> pd.DataFrame:
    r = add_order(apn_year_band(rows, cutoff))
    r["unitcat_mf"] = mf_unitcat(r, mf_keys)
    # The unit-category flag is "possible", not "definite": in the LA County Assessor check only
    # 31-44% of the ADU units it flags are on multifamily lots (docs/gate3/MULTIFAMILY_LOT_ADUS.md).
    r["definite_any"] = r["band"].eq("definite")
    r["possible_only"] = (r["band"].eq("possible") | r["unitcat_mf"]) & ~r["definite_any"]
    return r


def summarize(r: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Counts (ADU building-permit units) by group, and shares of all units."""
    u = r["units"].astype(float)
    kept12 = r["cap_kept"].astype(float)
    cols = {
        "adu_units": u,
        "units_unknown_apn": u.where(r["band"].eq("unknown_apn"), 0),
        "units_apn_year_definite": u.where(r["band"].eq("definite"), 0),
        "units_apn_year_possible": u.where(r["band"].eq("possible"), 0),
        "units_unitcat_mf": u.where(r["unitcat_mf"], 0),
        "units_lower_definite": u.where(r["definite_any"], 0),
        "units_upper_definite_plus_possible": u.where(r["definite_any"] | r["possible_only"], 0),
        "units_order1": r["u_order1"], "units_order2": r["u_order2"], "units_order3p": r["u_order3p"],
        "units_order3": r["u_order3"], "units_order4p": r["u_order4p"],
        "units_cap_removed": r["cap_removed"],
        "units_cap_removed_on_definite": r["cap_removed"].where(r["definite_any"], 0),
        "units_kept_on_definite": kept12.where(r["definite_any"], 0),
        "units_kept_on_possible": kept12.where(r["possible_only"], 0),
        "units_apn_cum_ge3": u.where(r["apn_cum"].ge(3), 0),
        "units_apn_cum_ge4": u.where(r["apn_cum"].ge(4), 0),
    }
    t = pd.DataFrame(cols).join(r[by]).groupby(by).sum().reset_index()
    t["units_cap_plus_mf_lower_removed"] = t["units_cap_removed"] + t["units_kept_on_definite"]
    t["units_cap_plus_mf_upper_removed"] = t["units_cap_plus_mf_lower_removed"] + t["units_kept_on_possible"]
    d = t["adu_units"].where(t["adu_units"] > 0)
    for c in ("units_lower_definite", "units_upper_definite_plus_possible", "units_cap_removed",
              "units_cap_plus_mf_lower_removed", "units_cap_plus_mf_upper_removed", "units_unknown_apn",
              "units_order1", "units_order2", "units_order3p"):
        t["share_" + c.removeprefix("units_")] = t[c] / d
    return t


# ---------------------------------------------------------------------------
# Rates: apply adjustments to the study panel
# ---------------------------------------------------------------------------

def adjusted_juris_year(summary_jy: pd.DataFrame) -> pd.DataFrame:
    """Per jurisdiction-year: removed units under each variant (to subtract from adu_main)."""
    s = summary_jy.copy()
    s["removed_mf_lower"] = s["units_lower_definite"]
    s["removed_mf_upper"] = s["units_upper_definite_plus_possible"]
    s["removed_cap"] = s["units_cap_removed"]
    s["removed_cap_mf_lower"] = s["units_cap_plus_mf_lower_removed"]
    s["removed_cap_mf_upper"] = s["units_cap_plus_mf_upper_removed"]
    s["removed_order2p"] = s["units_order2"] + s["units_order3p"]   # 1st ADUs only
    return s


VARIANTS = ("as_reported", "mf_lower", "mf_upper", "cap", "cap_mf_lower", "cap_mf_upper", "order1_only")
# validation-informed variants (LA County calibration), added by the runner when available
EXTRA_VARIANTS = ("cap_mf_central", "cap_mf_high")


def _variants(p: pd.DataFrame) -> list[str]:
    return [v for v in VARIANTS + EXTRA_VARIANTS if f"adu_{v}" in p]


def panel_with_variants(panel: pd.DataFrame, removed_by_geoid_year: pd.DataFrame) -> pd.DataFrame:
    """panel: study_panel (census_geoid, year, adu_main, sf_detached, ...). removed: census_geoid,
    year, removed_* columns. Adds adu_<variant> = adu_main minus removed units (missing stays missing)."""
    p = panel.merge(removed_by_geoid_year, on=["census_geoid", "year"], how="left")
    p["adu_as_reported"] = p["adu_main"]
    for v, col in (("mf_lower", "removed_mf_lower"), ("mf_upper", "removed_mf_upper"), ("cap", "removed_cap"),
                   ("cap_mf_lower", "removed_cap_mf_lower"), ("cap_mf_upper", "removed_cap_mf_upper"),
                   ("order1_only", "removed_order2p")):
        p[f"adu_{v}"] = p["adu_main"] - p[col].fillna(0)
    return p


def rate_by_year(p: pd.DataFrame, years=None) -> pd.DataFrame:
    q = p.dropna(subset=["adu_main"])
    if years is not None:
        q = q[q["year"].isin(years)]
    vs = _variants(p)
    g = q.groupby("year")[[f"adu_{v}" for v in vs] + ["sf_detached"]].sum()
    out = g.reset_index()
    for v in vs:
        out[f"rate_{v}"] = out[f"adu_{v}"] / out["sf_detached"] * 1000
    return out


def pooled_rate(p: pd.DataFrame, geoids, years) -> dict:
    q = p.dropna(subset=["adu_main"])
    q = q[q["census_geoid"].isin(set(geoids)) & q["year"].isin(years)]
    den = float(q["sf_detached"].sum())
    return {v: dict(numerator=float(q[f"adu_{v}"].sum()), denominator=den, rate=float(q[f"adu_{v}"].sum()) / den * 1000)
            for v in _variants(p)}


# ---------------------------------------------------------------------------
# Order decomposition of the rise
# ---------------------------------------------------------------------------

def order_decomposition(rates: pd.DataFrame, base_years, end_years) -> pd.DataFrame:
    """rates: year, rate_order1, rate_order2, rate_order3p (per 1,000 one-unit detached homes).
    Rise from mean(base) to mean(end) split by order."""
    b = rates[rates["year"].isin(base_years)].mean(numeric_only=True)
    e = rates[rates["year"].isin(end_years)].mean(numeric_only=True)
    rows = []
    total = sum(e[f"rate_{k}"] - b[f"rate_{k}"] for k in ("order1", "order2", "order3p"))
    for k in ("order1", "order2", "order3p"):
        rise = e[f"rate_{k}"] - b[f"rate_{k}"]
        rows.append(dict(order=k, base_rate=b[f"rate_{k}"], end_rate=e[f"rate_{k}"], rise=rise,
                         share_of_rise=rise / total if total else np.nan))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Ecological check with ACS B25024
# ---------------------------------------------------------------------------

def acs_mf_share(acs: pd.DataFrame, places: pd.DataFrame) -> pd.DataFrame:
    """Share of housing units in 2+-unit structures (B25024 E004..E009 / E001) per HCD-style
    jurisdiction (incorporated places; county remainders = county minus place parts).
    acs: read_acs_sf output for B25024 (sumlevels 050, 155, 160)."""
    a = acs.copy()
    a["mf2p"] = a[[f"B25024_E00{i}" for i in range(4, 10)]].sum(axis=1)
    a["tot"] = a["B25024_E001"]
    a["placefp"] = np.where(a["sumlevel"].isin(["155", "160"]), a["geoid"].str[2:7], None)
    a["county_fips"] = np.select([a["sumlevel"] == "050", a["sumlevel"] == "155"],
                                 [a["geoid"].str[2:5], a["geoid"].str[7:10]], default=None)
    inc = set(places.loc[places["incorporated"], "placefp"])
    pl = a[(a["sumlevel"] == "160") & a["placefp"].isin(inc)]
    pl = pd.DataFrame({"census_geoid": "06" + pl["placefp"], "mf2p": pl["mf2p"], "tot": pl["tot"]})
    parts = a[(a["sumlevel"] == "155") & a["placefp"].isin(inc)].groupby("county_fips")[["mf2p", "tot"]].sum()
    co = a[a["sumlevel"] == "050"].set_index("county_fips")[["mf2p", "tot"]]
    rem = (co - parts.reindex(co.index).fillna(0)).reset_index()
    rem = rem[rem["county_fips"] != "075"]
    rem["census_geoid"] = "06" + rem["county_fips"] + "_UNINC"
    out = pd.concat([pl, rem[["census_geoid", "mf2p", "tot"]]], ignore_index=True)
    out["mf_share"] = out["mf2p"] / out["tot"].where(out["tot"] > 0)
    return out


ECO_SPECS = {
    "value_income_size": ("log_value", "log_income", "log_homes"),
    "group_value_income_size": ("group", "log_value", "log_income", "log_homes"),
}


def ecological_fit(df: pd.DataFrame, terms: tuple[str, ...], n_draws: int = 2000, seed: int = 20261025) -> dict:
    """Poisson (log link, exposure = 1,000 home-years) of adu on the pooled-model terms plus
    mf_share. Implied multifamily-lot share = 1 - sum(mu with mf_share=0) / sum(mu), with an
    interval from normal draws of the coefficients (robust covariance)."""
    X0, names = R.design(df, terms)
    m = df["mf_share"].to_numpy(float)
    X = np.column_stack([X0, m])
    names = names + ["mf_share"]
    y = df["adu"].to_numpy(float)
    ex = df["exposure"].to_numpy(float)
    b = R.fit_poisson(X, y, ex)
    mu = ex * np.exp(X @ b)
    bread = np.linalg.inv((X.T * mu) @ X)
    cov = bread @ ((X.T * (y - mu) ** 2) @ X) @ bread
    se = np.sqrt(np.diag(cov))
    Xz = X.copy()
    Xz[:, -1] = 0.0

    def implied(beta):
        return 1 - (ex * np.exp(Xz @ beta)).sum() / (ex * np.exp(X @ beta)).sum()

    draws = np.random.default_rng(seed).multivariate_normal(b, cov, size=n_draws)
    sh = np.array([implied(d) for d in draws])
    disp = float(np.sum((y - mu) ** 2 / mu) / max(len(y) - len(b), 1))
    return dict(coef_mf_share=float(b[-1]), se_mf_share=float(se[-1]), n=int(len(y)), dispersion=disp,
                implied_share=float(implied(b)), implied_share_p10=float(np.quantile(sh, 0.1)),
                implied_share_p90=float(np.quantile(sh, 0.9)), adu_total=float(y.sum()),
                coefs=dict(zip(names, b.round(4).tolist())))


# ---------------------------------------------------------------------------
# Los Angeles County Assessor (validation only)
# ---------------------------------------------------------------------------

LA_ASSESSOR_CLASSES = ("single_family", "two_units", "three_four_units", "five_plus_units", "condo_or_pud",
                       "mobile_home", "vacant", "other_use", "unmatched")
LA_MF_CLASSES = ("two_units", "three_four_units", "five_plus_units")


def classify_la_use(use_code: pd.Series, desc2: pd.Series | None = None) -> pd.Series:
    """LA County Assessor 4-character use code -> lot class, read at the roll before the permit.

    First two characters: 01 single-family residence, 02 two units, 03 three units, 04 four
    units, 05 five or more; 07 manufactured home; other 0x (08 rooming house) and any code not
    starting with 0 are other. A trailing V is vacant land; a C in the fourth position of an 01
    code (010C, 01DC) is a condominium. Missing codes are unmatched."""
    c = use_code.fillna("").astype(str).str.strip().str.upper()
    d = (desc2 if desc2 is not None else pd.Series("", index=c.index)).fillna("").astype(str).str.upper()
    cls = np.select(
        [c.eq(""),
         c.str.endswith("V") | d.str.contains("VACANT"),
         (c.str[:2].eq("01") & c.str[3:4].eq("C")) | d.str.contains("CONDO"),
         c.str[:2].eq("07") | d.str.contains("MANUFACTURED") | d.str.contains("MOBILE"),
         c.str[:2].eq("01"), c.str[:2].eq("02"), c.str[:2].isin(["03", "04"]), c.str[:2].eq("05")],
        ["unmatched", "vacant", "condo_or_pud", "mobile_home",
         "single_family", "two_units", "three_four_units", "five_plus_units"],
        default="other_use")
    return pd.Series(cls, index=c.index)


PERIODS = {"2018-2019": (2018, 2019), "2020-2022": (2020, 2022), "2023-2025": (2023, 2025)}


def period_of(year: pd.Series) -> pd.Series:
    out = pd.Series(None, index=year.index, dtype=object)
    for k, (a, b) in PERIODS.items():
        out[year.between(a, b)] = k
    return out


def calib_band(r: pd.DataFrame) -> pd.Series:
    """Band used for calibration: definite, possible (APN-year possible or unit-category flag), single
    (includes unknown APNs)."""
    return pd.Series(np.select([r["definite_any"], r["possible_only"]], ["definite", "possible"], "single"), index=r.index)


def la_calibration(la: pd.DataFrame, min_units: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """From LA County rows matched to the assessor (columns: units or cap_kept, year, juris mf_share,
    is_mf, definite_any, possible_only, juris_name):
    - probs: per period and band, multifamily-lot share of ADU units (pooled over LA County);
    - fits: per period, a unit-weighted line p = a + b * mf_share across LA County jurisdictions
      (>= min_units single-band units) for the single band.
    """
    d = la.assign(period=period_of(la["year"]), cband=calib_band(la))
    d = d[d["period"].notna()]
    probs = d.groupby(["period", "cband"]).apply(
        lambda x: pd.Series({"units": x["units"].sum(), "mf_units": x.loc[x["is_mf"], "units"].sum()}),
        include_groups=False).reset_index()
    probs["p_mf"] = probs["mf_units"] / probs["units"]
    fits = []
    for per, x in d[d["cband"].eq("single")].groupby("period"):
        j = x.groupby("juris_name").apply(lambda y: pd.Series({"u": y["units"].sum(), "m": y.loc[y["is_mf"], "units"].sum(),
                                                                 "mf_share": y["mf_share"].iloc[0]}), include_groups=False)
        j = j[(j["u"] >= min_units) & j["mf_share"].notna()]
        X = np.column_stack([np.ones(len(j)), j["mf_share"]])
        w = j["u"].to_numpy(float)
        a, b = np.linalg.solve((X.T * w) @ X, (X.T * w) @ (j["m"] / j["u"]).to_numpy(float))
        fits.append(dict(period=per, a=float(a), b=float(b), n_jurisdictions=int(len(j)), units=float(w.sum())))
    return probs, pd.DataFrame(fits)


def calibrated_mf(r: pd.DataFrame, probs: pd.DataFrame, fits: pd.DataFrame, scale_single: bool = True) -> pd.Series:
    """Expected multifamily-lot share of each row's units: LA band shares for definite and possible;
    for single, a + b * mf_share of the row's jurisdiction (scale_single, where b > 0) or LA's pooled
    single share. Rows with no ACS multifamily share use the pooled share."""
    per = period_of(r["year"])
    band = calib_band(r)
    pm = probs.set_index(["period", "cband"])["p_mf"]
    p = pd.Series([pm.get((a, b), np.nan) for a, b in zip(per, band)], index=r.index)
    if scale_single:
        # scale only where the LA line slopes upward (2020 onward); before SB 13 the line is flat noise
        f = fits.set_index("period")
        a, b = f["a"].reindex(per).to_numpy(), f["b"].reindex(per).to_numpy()
        lin = np.clip(a + b * r["mf_share"].to_numpy(float), 0, 1)
        use = band.eq("single").to_numpy() & (b > 0) & ~np.isnan(lin)
        p = p.where(~use, lin)
    return p.fillna(0.0)


def la_ain(apn: pd.Series) -> pd.Series:
    """LA County AIN: 10 digits. A2 normalized APNs that are not 10 digits cannot match."""
    s = apn.fillna("")
    return s.where(s.str.fullmatch(r"\d{10}"))


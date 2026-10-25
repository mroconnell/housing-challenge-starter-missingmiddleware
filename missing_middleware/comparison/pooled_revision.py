"""Owner outcome rules as switchable inputs to the pooled model, and the G3F-2 test (AQ-040).

Named input options (docs/gate3/POOLED_REVISION.md):

- California ADU counts (`CA_OPTIONS`):
  * "as_used": the study's main measure (`adu_main`), unchanged;
  * "cap_a2": at most 2 ADU units per parcel (cumulated 2018-2025) plus the A2 APN rule's
    definite multifamily-lot units (3+ ADU units on one APN-year before 2023-01-01, 4+ from
    then), i.e. `units_cap_plus_mf_lower_removed` in reference/ca_mf_lot_adu_share_by_jurisdiction.csv;
  * "cap_la_calibrated": the cap plus the central multifamily-lot share calibrated to the
    Los Angeles County Assessor check (reference/ca_mf_lot_adu_share_la_calibration_*.csv),
    rebuilt per jurisdiction-year from the band counts in the by-jurisdiction file.
  Removals are per jurisdiction-year where the A2 parcel data exist; elsewhere the statewide
  share removed in that year is applied. Years before 2018 (no APNs) are left unchanged.
- Minneapolis: counts x (1 - 0.127), ADUs on duplex lots (MULTIFAMILY_LOT_ADUS.md section 8).
- Vacant-lot new-house ADUs: comparison counts that include ADUs built with a new house
  x (1 - 0.049), the median vacant-lot share across 17 cities (AQ-039). California's APR counts
  and Wisconsin's are not adjusted (neither includes them in this way).

Pure functions of data frames; tests run offline on fixtures.
Units: ADU (second-home) permits or ADU units per 1,000 one-unit detached homes per year.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CA_OPTIONS = ("as_used", "cap_a2", "cap_la_calibrated")
CA_OPTION_LABELS = {
    "as_used": "California as used (study main measure)",
    "cap_a2": "California cap + A2 (2 per parcel; definite A2 APN rule, cutoff 2023-01-01)",
    "cap_la_calibrated": "California cap + LA-calibrated central multifamily-lot share",
}
MINNEAPOLIS_DUPLEX_SHARE = 0.127     # 9 of 71 ADUs on duplex lots, 2021-2025 (12.6% in 2017-2020)
VACANT_LOT_SHARE = 0.049             # median vacant-lot new-house share, 17 cities (AQ-039)
PERIODS = {"2018-2019": (2018, 2019), "2020-2022": (2020, 2022), "2023-2025": (2023, 2025)}


def period_of(year: pd.Series) -> pd.Series:
    out = pd.Series(None, index=year.index, dtype=object)
    for k, (a, b) in PERIODS.items():
        out[year.between(a, b)] = k
    return out


# ---------------------------------------------------------------------------
# California removals per jurisdiction-year
# ---------------------------------------------------------------------------

def removed_cap_a2(jy: pd.DataFrame) -> pd.DataFrame:
    """jy: reference/ca_mf_lot_adu_share_by_jurisdiction.csv. Units removed by the cap plus the
    definite A2 multifamily-lot units the cap keeps."""
    return jy[["juris_name", "year", "adu_units"]].assign(removed=jy["units_cap_plus_mf_lower_removed"].astype(float))


def removed_cap_la_calibrated(jy: pd.DataFrame, bands: pd.DataFrame, fits: pd.DataFrame,
                              mf_share: pd.Series) -> pd.DataFrame:
    """Cap removals plus the expected multifamily-lot units among the units the cap keeps, using
    the LA County calibration (ca_mf_lot.calibrated_mf, scale_single=True), rebuilt from counts:
    kept definite units x LA's definite share, kept possible x LA's possible share, and the other
    kept units (single, incl. unknown APN) x (a + b x the jurisdiction's ACS 2+-unit share) where the
    period's line slopes upward, else LA's pooled single share.
    bands: ..._la_calibration_bands.csv (period, cband, p_mf); fits: ..._la_calibration_fit.csv
    (period, a, b); mf_share: juris_name -> share of housing units in 2+-unit structures."""
    d = jy.copy()
    per = period_of(d["year"].astype(int))
    pm = bands.set_index(["period", "cband"])["p_mf"]
    f = fits.set_index("period")
    p_def = np.array([pm.get((q, "definite"), 0.0) for q in per])
    p_pos = np.array([pm.get((q, "possible"), 0.0) for q in per])
    p_sgl = np.array([pm.get((q, "single"), 0.0) for q in per])
    a = f["a"].reindex(per).to_numpy(float)
    b = f["b"].reindex(per).to_numpy(float)
    m = d["juris_name"].map(mf_share).to_numpy(float)
    lin = np.clip(a + b * m, 0, 1)
    use = (b > 0) & ~np.isnan(lin)
    p_single = np.where(use, lin, p_sgl)
    kept = d["adu_units"] - d["units_cap_removed"]
    k_def, k_pos = d["units_kept_on_definite"], d["units_kept_on_possible"]
    k_sgl = kept - k_def - k_pos
    kept_mf = p_def * k_def + p_pos * k_pos + p_single * k_sgl
    return d[["juris_name", "year", "adu_units"]].assign(removed=d["units_cap_removed"] + kept_mf,
                                                         kept_mf_central=kept_mf)


def to_geoid(removed: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame:
    m = removed.merge(crosswalk[["juris_name", "census_geoid"]], on="juris_name", how="left")
    return m.dropna(subset=["census_geoid"]).groupby(["census_geoid", "year"])[["adu_units", "removed"]].sum().reset_index()


def statewide_factor(removed: pd.DataFrame) -> pd.Series:
    """Statewide share kept by year: 1 - removed / ADU units (ADU units summed over jurisdictions)."""
    g = removed.groupby("year")[["adu_units", "removed"]].sum()
    return 1 - g["removed"] / g["adu_units"]


def adjust_ca_panel(panel: pd.DataFrame, removed_geoid: pd.DataFrame | None, factor_by_year: pd.Series | None,
                    measure: str = "adu_main") -> pd.DataFrame:
    """Study panel with `measure` adjusted: minus removed units where the jurisdiction-year is in
    the A2 parcel data; otherwise times the statewide kept share for that year (years with no
    factor, before 2018, unchanged). Missing counts stay missing. Adds `ca_adjust_basis`."""
    p = panel.copy()
    p["ca_adjust_basis"] = "unchanged"
    if removed_geoid is None:
        return p
    r = removed_geoid.set_index(["census_geoid", "year"])["removed"]
    key = pd.MultiIndex.from_arrays([p["census_geoid"], p["year"].astype(int)])
    rem = pd.Series(r.reindex(key).to_numpy(), index=p.index)
    obs = p[measure].notna()
    by_j = obs & rem.notna()
    p.loc[by_j, measure] = (p.loc[by_j, measure] - rem[by_j]).clip(lower=0)
    p.loc[by_j, "ca_adjust_basis"] = "jurisdiction-year"
    fac = p["year"].astype(int).map(factor_by_year) if factor_by_year is not None else pd.Series(np.nan, index=p.index)
    by_s = obs & ~by_j & fac.notna() & (p[measure] > 0)
    p.loc[by_s, measure] = p.loc[by_s, measure] * fac[by_s]
    p.loc[by_s, "ca_adjust_basis"] = "statewide factor"
    return p


# ---------------------------------------------------------------------------
# Comparison rows outside California
# ---------------------------------------------------------------------------

def adjust_other_rows(rows: pd.DataFrame, vacant_lot: bool = True, minneapolis: bool = True) -> pd.DataFrame:
    """Pooled rows (pooled_regression.Pooled.rows): non-California rows whose counts include ADUs
    built with a new house x (1 - VACANT_LOT_SHARE); Minneapolis x (1 - MINNEAPOLIS_DUPLEX_SHARE)."""
    r = rows.copy()
    nonca = r["cluster"].ne("CA")
    if vacant_lot:
        m = nonca & r["incl_new_house"].astype(bool)
        r.loc[m, "count"] *= 1 - VACANT_LOT_SHARE
    if minneapolis:
        r.loc[r["series"].eq("minneapolis"), "count"] *= 1 - MINNEAPOLIS_DUPLEX_SHARE
    return r


# ---------------------------------------------------------------------------
# G3F-2 scoring helpers
# ---------------------------------------------------------------------------

def rms(e) -> float:
    e = np.asarray(e, float)
    return float(np.sqrt(np.mean(e ** 2)))


def paired_bootstrap_wins(err: pd.DataFrame, n: int = 5000, seed: int = 20261025) -> pd.Series:
    """err: states x configurations (log errors). Resample states with replacement; share of
    resamples in which each configuration has the lowest RMS error."""
    rng = np.random.default_rng(seed)
    E = err.to_numpy(float) ** 2
    k = E.shape[0]
    idx = rng.integers(0, k, size=(n, k))
    msq = E[idx].mean(axis=1)                       # n x configs
    win = np.argmin(msq, axis=1)
    return pd.Series(np.bincount(win, minlength=E.shape[1]) / n, index=err.columns)


def madison_like_wi(places: pd.DataFrame, min_homes=20_000, max_homes=120_000, min_value=250_000,
                    max_value=500_000) -> pd.DataFrame:
    """places: one row per incorporated Wisconsin municipality (name, muni_type, homes, value).
    MADISON_LIKE_CITIES.md section 0: 20,000-120,000 one-unit detached homes, median value
    $250k-$500k (inclusive), incorporated, not the state's largest city (by homes)."""
    p = places[places["muni_type"].isin(["city", "village"])].copy()
    largest = p.loc[p["homes"].idxmax(), "name"]
    p["largest_city"] = p["name"].eq(largest)
    p["madison_like"] = (p["homes"].between(min_homes, max_homes) & p["value"].between(min_value, max_value)
                         & ~p["largest_city"])
    return p

"""Pooled multi-state regression and statewide adoption curve for Wisconsin's with-law rate
(Gate 3 revision, owner direction 2026-10-24).

Why: the California-only regression (ca_regression.py) under-predicts every other state that
passed a statewide ADU law, more so at lower home values (Maine about 4x). Its home-value slope
below $700k (elasticity about 1.7) is far steeper than the slope across states (about 0.17), and
61% of Wisconsin's homes sit below California's 5th-percentile value. This module pools
California with the other statewide-law states and five cities so that the level and the
market slope are set by more than one state.

Two products:

A. Statewide adoption curve (`adoption_curve`): the median observed rate by year since the
   statewide law, across the statewide-law states with post-law data. A level path (the rate
   actually reached each year), applied to Wisconsin's homes minus the current-law baseline.

B. Pooled regression (`fit_pooled`, `loso`, `predict_wi`): one row per jurisdiction-year (or
   state/region-year). Outcome = ADU-type permits per 1,000 one-unit detached homes per year.
   Each row's expected count is the SUM over its member geographies (places or county
   subdivisions) of homes x exp(x'b), so a state's observed rate is modelled from its own
   distribution of home values and incomes, exactly as Wisconsin's statewide rate is
   predicted from its 1,925 areas. Weighted Poisson: each state (cluster) carries the same
   total weight, so California's ~450 places count as one state.

Units everywhere: permits (ADU-type second homes) per 1,000 one-unit detached homes
(ACS 2020-2024 B25024_002) per year. All associations are descriptive, not causal.
Pure functions of data frames so tests run offline on fixtures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

WI_HOMES = 1_839_569
CENTRES = {"value": 500_000.0, "income": 100_000.0, "homes": 10_000.0, "renter_share": 0.3, "pre": 0.5}
VALUE_KNOT = 700_000.0
PRE_OFFSET = 0.1         # log(pre-law rate + 0.1): zeros allowed
TOP_CODES = {"value": 2000001, "rent": 3501, "income": 250001}

# Statewide-law states used for the adoption curve and the leave-one-state-out headline
STATEWIDE_STATES = ("WA", "OR", "RI", "MA", "ME", "UT", "VT")
LOWER_VALUE_STATES = ("ME", "OR", "VT")

# ---------------------------------------------------------------------------
# Row coding: law in force, local reform, years since the statewide law (k)
# ---------------------------------------------------------------------------
# k = 1 is the first (nearly) full year with the statewide law in force. Partial law years
# (Oregon 2018, Rhode Island 2024, Maine 2024 compliance year, reform years) are dropped.
# law = 1: a statewide ADU law in force; local = 1: the city's own ADU-enabling rules in force.
# Hand-coded, one entry per series-year, with the reason in NOTES.

def _span(a, b, law, local, k0=None):
    return {y: (law, local, (None if k0 is None else k0 + (y - a))) for y in range(a, b + 1)}


STATE_CODING = {
    # series id (statewide_states_annual.csv) -> cluster, {year: (law, local, k)}
    "WA_inc_exSeattle": ("WA", {**_span(2019, 2023, 0, 0), **_span(2024, 2026, 1, 0, 1)}),
    "OR_panel32_exPortland": ("OR", _span(2019, 2022, 1, 0, 1)),
    "RI_statewide": ("RI", {**_span(2021, 2023, 0, 0), **_span(2025, 2025, 1, 0, 1)}),
    "MA_statewide": ("MA", _span(2025, 2025, 1, 0, 1)),
    "ME_statewide": ("ME", _span(2025, 2025, 1, 0, 1)),
    "UT_mih": ("UT", _span(2023, 2025, 1, 0, 2)),
    "VT_chittenden": ("VT", _span(2021, 2024, 1, 0, 1)),
}
CITY_CODING = {
    # city (other_cities_annual.csv) -> cluster, place geoid, {year: (law, local, k)}
    "seattle": ("WA", "5363000", {**_span(2016, 2018, 0, 1), **_span(2020, 2023, 0, 1), **_span(2024, 2024, 1, 1, 2)}),
    "portland": ("OR", "4159000", _span(2019, 2025, 1, 1, 1)),
    "austin": ("TX", "4805000", {**_span(2012, 2014, 0, 0), **_span(2016, 2023, 0, 1)}),
    "denver": ("CO", "0820000", {**_span(2016, 2023, 0, 0), **_span(2025, 2025, 1, 1, 1)}),
    "minneapolis": ("MN", "2743000", _span(2017, 2025, 0, 1)),
}
CA_LAW_YEAR = 2020   # the 2019 package (in force 2020-01-01): k = year - 2019
LA_GEOID = "0644000"
LA_EVENT_LAW_YEAR = 2017   # event-time variant: Los Angeles applied state default standards from 2017

NOTES = {
    "WA": "k from enactment 2023-07-23: OFM EY2024 (Apr 2023-Mar 2024, 8 of 12 months after) = 1, EY2025 = 2, "
          "EY2026 = 3. Local compliance only from 2025-06-30 (sensitivity `wa_compliance`). EY2019-2023 = before (law 0). "
          "Seattle: calendar 2016-18 and 2020-23 local rules only; 2024 = k 2 (5-17 months after enactment).",
    "OR": "SB 1051 effective 2018-07-01; 2018 is a half year (dropped); 2019 = 1 ... 2022 = 4. Portland 2019-2025 "
          "(statewide law plus its own rules; 2011-2018 fee-waiver years not used: a fee programme, not a rules reform).",
    "RI": "Effective 2024-06-25; 2024 half year dropped; 2025 = 1. 2021-2023 = before.",
    "MA": "Effective 2025-02-02; 2025 = 1 (11 months). Undercount (293 of 351 towns).",
    "ME": "LD 2003 compliance 2024-01-01 (councils) / 2024-07-01 (town-meeting towns); 2024 transition; 2025 = 1. "
          "Lower bound (182 towns, about 73% of population).",
    "UT": "HB 82 effective 2021-10-01; MIH report years end July: 2023 (Aug 2022-Jul 2023) = 2, 2024 = 3, 2025 = 4. "
          "Internal ADUs only; self-reported.",
    "VT": "Act 179 2020-10-12; 2021 = 1 ... 2024 = 4. Vermont has allowed one ADU by right since 2004, so its "
          "2016-2020 rows are not a no-law period and are not used. Chittenden County only.",
    "CA": "2019 package in force 2020-01-01: 2020 = 1 ... 2025 = 6 (k >= 4 is the plateau bucket). Pre-law "
          "activity = 2017-2019 rate (already under the 2017 law). All 457 grouped jurisdictions, holdout included.",
    "TX": "Austin: 2012-14 before its 2015 rules; 2016-2023 local rules; no statewide law. 2015 reform year dropped.",
    "CO": "Denver: 2016-2023 zone-by-zone (local 0); 2024 dropped (state law enacted 2024-05-13, citywide 2024-12-16); "
          "2025 = 1 under HB24-1152 plus citywide rules.",
    "MN": "Minneapolis: 2017-2025 local rules (2014 ordinance; owner occupancy removed 2021); no statewide law.",
}
PRE_LAW = {   # pre-law activity (per 1,000 homes per year) at series level, for the `pre` variant
    "WA_inc_exSeattle": 0.394, "RI_statewide": 0.229, "VT_chittenden": 0.616,
    "seattle": 1.766, "austin": 0.416, "denver": 0.373,
}

# Measurement
NEW_HOUSE_FACTOR = 0.8      # named sensitivity only: series that include ADUs built with a new house
# Reporting share by series and year (AQ-061, owner decision 2026-10-28: applied in the adopted fit through
# adjust_counts(coverage=True), which divides the count by the share; a series-year not listed counts as 1.0).
# The counts cover only reporting towns while the denominator is every one-unit detached home in the state.
# No town lists for Maine, Massachusetts or Rhode Island are in the repository, so their published reporting shares
# are used (Maine: share of population; Massachusetts and Rhode Island: share of towns). Utah's shares are one-unit
# detached homes (ACS 2020-2024 B25024_002) in the cities, metro townships and unincorporated county areas that
# answered the ADU building-permit question in each MIH report year, / all of Utah's (813,940); computed from the
# extracted MIH lists by statewide_states.ut_reporting_share() and checked in scripts/run_pooled_revision.py.
# Rhode Island 2021-2023 coverage is not stated, so those years are left at 1.0.
COVERAGE = {"ME_statewide": {2025: 0.73},
            "MA_statewide": {2025: 293 / 351},
            "RI_statewide": {2025: 32 / 39},
            "UT_mih": {2023: 0.7951, 2024: 0.8031, 2025: 0.8042}}
# Share of the year the statewide law was in force in a k = 1 calendar year coded as a full year (AQ-061):
# Massachusetts' law took effect 2025-02-02, so 2025 is 11 of 12 months.
PARTIAL_YEAR = {("MA_statewide", 2025): 11 / 12}


def coverage_for(series: str, year: int) -> float:
    return float(COVERAGE.get(series, {}).get(int(year), 1.0))


# ---------------------------------------------------------------------------
# ACS members (places / county subdivisions) with homes, value, income, rent, renter share
# ---------------------------------------------------------------------------

ACS_TABLES = {"b25024": ("B25024_E002", "homes"), "b25077": ("B25077_E001", "value"),
              "b19013": ("B19013_E001", "income"), "b25064": ("B25064_E001", "rent")}


def read_acs_members(paths: dict[str, Path], states: set[str], sumlevels=("040", "050", "060", "160")) -> pd.DataFrame:
    """One scan per table: rows for the given state FIPS and summary levels. Returns geoid,
    sumlevel, homes, value, income, rent, renter_share (NaN where missing; top codes minus one)."""
    frames = []
    for t, path in paths.items():
        keep = []
        with open(path, encoding="utf-8") as f:
            header = f.readline().rstrip("\n").split("|")
            for line in f:
                gid = line.split("|", 1)[0]
                if gid[:3] in sumlevels and gid[3:9] == "0000US" and gid[9:11] in states:
                    keep.append(line.rstrip("\n").split("|"))
        d = pd.DataFrame(keep, columns=header)
        d["sumlevel"] = d["GEO_ID"].str[:3]
        d["geoid"] = d["GEO_ID"].str[9:]
        if t == "b25003":
            tot = pd.to_numeric(d["B25003_E001"], errors="coerce")
            ren = pd.to_numeric(d["B25003_E003"], errors="coerce")
            d["renter_share"] = (ren / tot).where(tot > 0)
            frames.append(d.set_index(["geoid", "sumlevel"])[["renter_share"]])
            continue
        col, name = ACS_TABLES[t]
        v = pd.to_numeric(d[col], errors="coerce")
        v = v.mask(v < 0)
        if name in TOP_CODES:
            v = v.mask(v >= TOP_CODES[name], TOP_CODES[name] - 1)
        d[name] = v
        frames.append(d.set_index(["geoid", "sumlevel"])[[name]])
    return pd.concat(frames, axis=1).reset_index()


def members_for(acs: pd.DataFrame, kind: str, ids, parent: str) -> pd.DataFrame:
    """Member geographies of one denominator. kind: 'cousubs' (ids = state or county FIPS prefix),
    'places' (ids = list of 7-digit place geoids). Missing medians fall back to the parent
    geography (state 040 or county 050 geoid `parent`), flagged in `filled`."""
    if kind == "cousubs":
        m = acs[acs.sumlevel.eq("060") & acs.geoid.str.startswith(ids)].copy()
    elif kind == "places":
        m = acs[acs.sumlevel.eq("160") & acs.geoid.isin(list(ids))].copy()
    else:
        raise ValueError(kind)
    m = m[m["homes"].fillna(0) > 0].copy()
    par = acs[acs.geoid.eq(parent) & acs.sumlevel.isin(["040", "050"])].iloc[0]
    county = acs[acs.sumlevel.eq("050")].set_index("geoid")
    m["filled"] = ""
    for c in ("value", "income", "rent", "renter_share"):
        miss = m[c].isna()
        if kind == "cousubs" and miss.any():     # county subdivision: its county first
            fill = m.loc[miss, "geoid"].str[:5].map(county[c])
            ok = fill.notna()
            m.loc[fill[ok].index, c] = fill[ok]
            m.loc[fill[ok].index, "filled"] += f"{c}_county;"
            miss = m[c].isna()
        m.loc[miss, c] = par[c]
        m.loc[miss, "filled"] += f"{c}_parent;"
    return m[["geoid", "sumlevel", "homes", "value", "income", "rent", "renter_share", "filled"]]


def homes_weighted_market(m: pd.DataFrame) -> dict:
    w = m["homes"].to_numpy(float)
    return {"homes": float(w.sum()),
            **{f"hw_{c}": float(np.average(m[c].to_numpy(float), weights=w)) for c in ("value", "income", "rent", "renter_share")},
            "hw_log_value_gm": float(np.exp(np.average(np.log(m["value"].to_numpy(float)), weights=w))),
            "n_members": int(len(m)), "n_filled": int(m["filled"].ne("").sum())}


# ---------------------------------------------------------------------------
# Pooled dataset
# ---------------------------------------------------------------------------

def state_rows(annual: pd.DataFrame, coding=STATE_CODING) -> pd.DataFrame:
    rows = []
    for sid, (cluster, years) in coding.items():
        a = annual[annual["series"].eq(sid)].set_index("year")
        for y, (law, local, k) in years.items():
            if y not in a.index or pd.isna(a.loc[y, "adu_count"]):
                continue
            rows.append(dict(cluster=cluster, series=sid, group_id=sid, year=int(y), count=float(a.loc[y, "adu_count"]),
                             years=PARTIAL_YEAR.get((sid, int(y)), 1.0), law=law, local=local, k=k, incl_new_house=True,
                             coverage=coverage_for(sid, y), pre_rate=PRE_LAW.get(sid, np.nan)))
    return pd.DataFrame(rows)


def city_rows(annual: pd.DataFrame, coding=CITY_CODING, measure: str = "units_incl_new_house") -> pd.DataFrame:
    rows = []
    for city, (cluster, geoid, years) in coding.items():
        a = annual[annual["city"].eq(city)].set_index("year")
        for y, (law, local, k) in years.items():
            if y not in a.index or pd.isna(a.loc[y, measure]):
                continue
            rows.append(dict(cluster=cluster, series=city, group_id=f"place:{geoid}", year=int(y),
                             count=float(a.loc[y, measure]), years=1.0, law=law, local=local, k=k,
                             incl_new_house=(measure != "adu_units"), coverage=1.0, pre_rate=PRE_LAW.get(city, np.nan)))
    return pd.DataFrame(rows)


def ca_rows(panel: pd.DataFrame, ca: pd.DataFrame, years=range(2020, 2026), law_year: int = CA_LAW_YEAR,
            la_event: bool = False, measure: str = "adu_main") -> tuple[pd.DataFrame, pd.DataFrame]:
    """California jurisdiction-years (all grouped jurisdictions, holdout included) and their
    single-member market rows. `ca` is ca_regression's dataset (market, homes, pre_rate)."""
    p = panel[panel["census_geoid"].isin(ca["census_geoid"]) & panel["year"].isin(list(years))].dropna(subset=[measure])
    pre = ca.set_index("census_geoid")["pre_rate"]
    rows = pd.DataFrame({
        "cluster": "CA", "series": "CA_jurisdictions", "group_id": "ca:" + p["census_geoid"].values,
        "year": p["year"].astype(int).values, "count": p[measure].astype(float).values, "years": 1.0,
        "law": 1, "local": 0, "incl_new_house": True, "coverage": 1.0,
        "pre_rate": p["census_geoid"].map(pre).values})
    first = np.where((p["census_geoid"].values == LA_GEOID) & la_event, LA_EVENT_LAW_YEAR, law_year)
    rows["k"] = p["year"].values - first + 1
    rows = rows[rows["k"] >= 1].reset_index(drop=True)
    mem = pd.DataFrame({"group_id": "ca:" + ca["census_geoid"], "geoid": ca["census_geoid"], "sumlevel": "160",
                        "homes": ca["homes"].astype(float), "value": ca["value"], "income": ca["income"],
                        "rent": ca["rent"], "renter_share": ca["renter_share"], "filled": ca.get("filled", "")})
    return rows, mem


@dataclass
class Pooled:
    rows: pd.DataFrame       # one per area-period: cluster, group_id, year, count, years, law, local, k, ...
    members: pd.DataFrame    # group_id -> member geographies with homes and market values

    def row_homes(self) -> pd.Series:
        return self.rows["group_id"].map(self.members.groupby("group_id")["homes"].sum())


def assemble(parts: list[tuple[pd.DataFrame, pd.DataFrame]]) -> Pooled:
    rows = pd.concat([p[0] for p in parts], ignore_index=True)
    mem = pd.concat([p[1] for p in parts], ignore_index=True).drop_duplicates(["group_id", "geoid"])
    rows = rows[rows["group_id"].isin(mem["group_id"])].reset_index(drop=True)
    rows["k"] = pd.to_numeric(rows["k"], errors="coerce")
    return Pooled(rows, mem)


def adjust_counts(rows: pd.DataFrame, new_house: bool = False, coverage: bool = False) -> pd.DataFrame:
    """Named measurement sensitivities: new_house multiplies every count that includes ADUs built
    with a new house by NEW_HOUSE_FACTOR (California's APR counts are left as is: the study
    excluded the with-new-house ADUs it could identify); coverage divides each series-year's count by
    its reporting share (COVERAGE; applied in the adopted fit since AQ-061)."""
    r = rows.copy()
    if new_house:
        m = r["incl_new_house"].astype(bool) & r["cluster"].ne("CA")
        r.loc[m, "count"] *= NEW_HOUSE_FACTOR
    if coverage:
        r["count"] = r["count"] / r["coverage"]
        r["coverage"] = 1.0          # applied once: a second call (or adoption_curve(coverage=True)) does nothing
    return r


# ---------------------------------------------------------------------------
# Design and weighted Poisson with summed member means
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PSpec:
    name: str
    terms: tuple[str, ...]
    label: str = ""
    ca_carry: str = ""        # the California-only spec this carries forward


BASE = ("law", "local", "k1", "k2", "k3")
PSPECS = (
    PSpec("p_value", ("log_value",) + BASE, "log value", "group_value"),
    PSpec("p_value_size", ("log_value", "log_homes") + BASE, "log value + log size", "group_value_size"),
    PSpec("p_hinge_size", ("log_value", "hinge", "log_homes") + BASE, "log value, second slope below $700k, + log size",
          "group_value_hinge_size (CA main)"),
    PSpec("p_value_income", ("log_value", "log_income") + BASE, "log value + log income", ""),
    PSpec("p_value_income_size", ("log_value", "log_income", "log_homes") + BASE, "log value + log income + log size",
          "group_value_income_size (CA best overall)"),
    PSpec("p_value_income_size_renter", ("log_value", "log_income", "log_homes", "renter_share") + BASE,
          "+ renter share", "renter share (B25003) extra"),
    PSpec("p_value_income_size_pre", ("log_value", "log_income", "log_homes", "pre", "pre_missing") + BASE,
          "+ pre-law activity", "group (pre-law activity)"),
    PSpec("p_ctx", ("value_ctx", "value_dev") + BASE,
          "log value split: state context (between) + place deviation (within)", ""),
    PSpec("p_ctx_size", ("value_ctx", "value_dev", "log_homes") + BASE, "context value split + log size", ""),
    PSpec("p_ctx_income", ("value_ctx", "value_dev", "income_ctx", "income_dev") + BASE,
          "context split of value and income", ""),
    PSpec("p_ctx_income_size", ("value_ctx", "value_dev", "income_ctx", "income_dev", "log_homes") + BASE,
          "context split of value and income + log size", "group_value_income_size, split between/within"),
    PSpec("p_ctx_valinc_size", ("value_ctx", "value_dev", "income_dev", "log_homes") + BASE,
          "context value; within value and income; size", ""),
    PSpec("p_hinge_income_size", ("log_value", "hinge", "log_income", "log_homes") + BASE,
          "hinge + log income + log size", ""),
)
PSPEC_BY_NAME = {s.name: s for s in PSPECS}


def member_frame(p: Pooled) -> pd.DataFrame:
    """Rows expanded to members, with row index `ri` and each state's (cluster's) context:
    homes-weighted mean log value and log income over the cluster's distinct member geographies."""
    r = p.rows.reset_index(drop=True).assign(ri=lambda d: np.arange(len(d)))
    m = r.merge(p.members, on="group_id", how="inner").sort_values("ri", kind="stable").reset_index(drop=True)
    u = m.drop_duplicates(["cluster", "geoid"])
    ctx = u.groupby("cluster").apply(lambda g: pd.Series({
        "ctx_log_value": np.average(np.log(g["value"].astype(float)), weights=g["homes"]),
        "ctx_log_income": np.average(np.log(g["income"].astype(float)), weights=g["homes"])}), include_groups=False)
    return m.join(ctx, on="cluster")


def context(homes, value, income) -> dict:
    """Context of a set of areas (e.g. Wisconsin's 1,925): homes-weighted mean log value / income."""
    h = np.asarray(homes, float)
    return {"ctx_log_value": float(np.average(np.log(np.asarray(value, float)), weights=h)),
            "ctx_log_income": float(np.average(np.log(np.asarray(income, float)), weights=h))}


def design(m: pd.DataFrame, terms: tuple[str, ...]) -> tuple[np.ndarray, list[str]]:
    cols, names = [np.ones(len(m))], ["intercept"]
    v = m["value"].astype(float).to_numpy()
    law = m["law"].astype(float).to_numpy()
    k = m["k"].to_numpy(float)
    for t in terms:
        if t == "log_value":
            c = np.log(v / CENTRES["value"])
        elif t == "value_ctx":      # between-state: the series' typical (homes-weighted log) value
            c = m["ctx_log_value"].to_numpy(float) - np.log(CENTRES["value"])
        elif t == "value_dev":      # within-state: the member's value relative to its series
            c = np.log(v) - m["ctx_log_value"].to_numpy(float)
        elif t == "income_ctx":
            c = m["ctx_log_income"].to_numpy(float) - np.log(CENTRES["income"])
        elif t == "income_dev":
            c = np.log(m["income"].astype(float).to_numpy()) - m["ctx_log_income"].to_numpy(float)
        elif t == "hinge":
            c = np.minimum(np.log(v / VALUE_KNOT), 0.0)
        elif t == "log_income":
            c = np.log(m["income"].astype(float).to_numpy() / CENTRES["income"])
        elif t == "log_homes":
            c = np.log(m["homes"].astype(float).clip(lower=1).to_numpy() / CENTRES["homes"])
        elif t == "renter_share":
            c = m["renter_share"].astype(float).to_numpy() - CENTRES["renter_share"]
        elif t == "law":
            c = law
        elif t == "local":
            c = m["local"].astype(float).to_numpy()
        elif t in ("k1", "k2", "k3"):
            c = law * (k == int(t[1]))
        elif t == "pre":
            pr = m["pre_rate"].astype(float).to_numpy()
            c = law * np.where(np.isnan(pr), 0.0, np.log((np.nan_to_num(pr) + PRE_OFFSET) / CENTRES["pre"]))
        elif t == "pre_dev":        # place's pre-law activity relative to its state (CA places, WI areas)
            lp = np.log(m["pre_rate"].astype(float).to_numpy() + PRE_OFFSET)
            cl = m["cluster"].to_numpy()
            geo = m["geoid"].to_numpy() if "geoid" in m else np.arange(len(m))
            dev = np.zeros(len(m))
            for c in np.unique(cl):
                sel = (cl == c) & ~np.isnan(lp)
                _, first = np.unique(geo[sel], return_index=True)
                if len(first) > 1:
                    idx = np.flatnonzero(sel)[first]
                    mean = np.average(lp[idx], weights=m["homes"].to_numpy(float)[idx])
                    dev[sel] = lp[sel] - mean
            c = law * dev
        elif t == "pre_missing":
            c = law * np.isnan(m["pre_rate"].astype(float).to_numpy())
        elif t == "ca":
            c = (m["cluster"] == "CA").astype(float).to_numpy()
        else:
            raise ValueError(t)
        cols.append(np.nan_to_num(c.astype(float)))
        names.append(t)
    return np.column_stack(cols), names


def cluster_weights(rows: pd.DataFrame, homes: pd.Series, scheme: str = "equal_state") -> np.ndarray:
    """Row weights. equal_state: every cluster's total home-years weigh the same (California's
    places together count as one state; within a state, rows count by homes). homes: no
    reweighting (California dominates). sqrt: cluster weight proportional to sqrt(home-years)."""
    hy = homes.to_numpy(float) * rows["years"].to_numpy(float)
    tot = pd.Series(hy).groupby(rows["cluster"].values).transform("sum").to_numpy()
    if scheme == "equal_state":
        w = 1.0 / tot
    elif scheme == "homes":
        w = np.ones(len(rows))
    elif scheme == "sqrt":
        w = 1.0 / np.sqrt(tot)
    else:
        raise ValueError(scheme)
    return w / w.mean()


@dataclass
class PFit:
    spec: PSpec
    names: list[str]
    beta: np.ndarray
    se_cluster: np.ndarray
    weights: str
    n_rows: int
    n_clusters: int
    clusters: list[str] = field(default_factory=list)

    def coef(self) -> pd.Series:
        return pd.Series(self.beta, index=self.names)


def _mu(X, off, ri, n_rows, beta):
    a = np.exp(X @ beta + off)
    mu = np.bincount(ri, weights=a, minlength=n_rows)
    return a, mu


def fit_pooled(p: Pooled, spec: PSpec, weights: str = "equal_state", maxit: int = 200, tol: float = 1e-9) -> PFit:
    """Weighted Poisson MLE where row r's mean is sum over its members of
    years x homes/1000 x exp(x'b). Fisher scoring with step halving."""
    m = member_frame(p)
    X, names = design(m, spec.terms)
    ri = m["ri"].to_numpy()
    n = len(p.rows)
    off = np.log(m["years"].to_numpy(float) * m["homes"].to_numpy(float) / 1000)
    y = p.rows["count"].to_numpy(float)
    w = cluster_weights(p.rows, p.row_homes(), weights)
    keep = np.ones(X.shape[1], bool)
    keep[1:] = np.abs(X[:, 1:]).sum(axis=0) > 0      # drop terms with no support (e.g. k3 in a tiny fixture)
    X, names = X[:, keep], [nm for nm, kp in zip(names, keep) if kp]
    beta = np.zeros(X.shape[1])
    beta[0] = np.log(max((w * y).sum(), 1e-9) / (w * np.bincount(ri, weights=np.exp(off), minlength=n)).sum())

    def ll(b):
        _, mu = _mu(X, off, ri, n, b)
        return float(np.sum(w * (y * np.log(mu) - mu)))

    cur = ll(beta)
    for _ in range(maxit):
        a, mu = _mu(X, off, ri, n, beta)
        S = np.zeros((n, X.shape[1]))
        np.add.at(S, ri, a[:, None] * X)
        g = (w * (y / mu - 1)) @ S
        info = (S.T * (w / mu)) @ S
        step = np.linalg.solve(info + 1e-10 * np.eye(len(beta)), g)
        t = 1.0
        while t > 1e-6:
            nb = beta + t * step
            nl = ll(nb)
            if nl >= cur - 1e-12:
                break
            t /= 2
        beta, done = nb, abs(nl - cur) < tol * (1 + abs(cur))
        cur = nl
        if done and np.max(np.abs(t * step)) < 1e-7:
            break
    # cluster-robust sandwich (clusters = states)
    a, mu = _mu(X, off, ri, n, beta)
    S = np.zeros((n, X.shape[1]))
    np.add.at(S, ri, a[:, None] * X)
    info = (S.T * (w / mu)) @ S
    sc = (w * (y / mu - 1))[:, None] * S
    cl = p.rows["cluster"].to_numpy()
    U = np.vstack([sc[cl == c].sum(axis=0) for c in np.unique(cl)])
    bread = np.linalg.pinv(info)
    se = np.sqrt(np.clip(np.diag(bread @ (U.T @ U) @ bread), 0, None))
    full_names = names
    return PFit(spec, full_names, beta, se, weights, n, len(np.unique(cl)), sorted(np.unique(cl).tolist()))


def predict_members(fit_: PFit, m: pd.DataFrame) -> np.ndarray:
    """Rate per 1,000 homes per year for each member row."""
    X, names = design(m, fit_.spec.terms)
    idx = [names.index(nm) for nm in fit_.names]
    return np.exp(X[:, idx] @ fit_.beta)


def predict_rows(fit_: PFit, p: Pooled) -> pd.DataFrame:
    """Expected count and rate per row (members summed with their homes)."""
    m = member_frame(p)
    rate = predict_members(fit_, m)
    ex = m["years"].to_numpy(float) * m["homes"].to_numpy(float) / 1000
    mu = np.bincount(m["ri"].to_numpy(), weights=rate * ex, minlength=len(p.rows))
    r = p.rows.reset_index(drop=True).copy()
    r["homes"] = p.row_homes().to_numpy()
    r["pred_count"] = mu
    r["obs_rate"] = r["count"] / (r["years"] * r["homes"]) * 1000
    r["pred_rate"] = mu / (r["years"] * r["homes"]) * 1000
    return r


def subset(p: Pooled, mask: np.ndarray) -> Pooled:
    r = p.rows[mask].reset_index(drop=True)
    return Pooled(r, p.members[p.members["group_id"].isin(r["group_id"])])


# ---------------------------------------------------------------------------
# Leave one state out
# ---------------------------------------------------------------------------

def eval_mask(rows: pd.DataFrame) -> np.ndarray:
    """Rows scored when a cluster is held out: its statewide-law rows; for clusters with no
    statewide-law rows (Austin, Minneapolis), their local-reform rows."""
    has_law = rows.groupby("cluster")["law"].transform("max").eq(1)
    return np.where(has_law, rows["law"].eq(1), rows["local"].eq(1))


def loso(p: Pooled, spec: PSpec, weights: str = "equal_state", clusters=None) -> pd.DataFrame:
    """For each cluster: fit on all other clusters, predict the held-out cluster's scored rows
    (homes-weighted over its years). Returns one row per (cluster, series)."""
    out = []
    ev = eval_mask(p.rows)
    for c in clusters or sorted(p.rows["cluster"].unique()):
        tr = p.rows["cluster"].ne(c).to_numpy()
        te = (~tr) & ev
        if not te.any():
            continue
        f = fit_pooled(subset(p, tr), spec, weights)
        pr = predict_rows(f, subset(p, te))
        for s, g in pr.groupby("series"):
            hy = (g["years"] * g["homes"]).sum() / 1000
            obs, pred = g["count"].sum() / hy, g["pred_count"].sum() / hy
            out.append(dict(spec=spec.name, weights=weights, held_out=c, series=s, years=f"{int(g.year.min())}-{int(g.year.max())}",
                            k=f"{int(g.k.min())}-{int(g.k.max())}" if g["k"].notna().any() else "",
                            n_rows=len(g), obs_rate=obs, pred_rate=pred,
                            ratio_obs_pred=obs / pred if pred > 0 else np.nan,
                            log_error=np.log(pred / obs) if obs > 0 and pred > 0 else np.nan))
    return pd.DataFrame(out)


def loso_summary(lo: pd.DataFrame) -> dict:
    """Headline errors over the statewide-law state series (the state-level series, not the cities)."""
    st = lo[lo["series"].isin(STATE_CODING.keys())]
    e = st["log_error"].to_numpy()
    low = st[st["held_out"].isin(LOWER_VALUE_STATES)]["log_error"].to_numpy()
    by = st.set_index("held_out")["log_error"]
    ca = lo[lo["held_out"].eq("CA")]["log_error"]
    return {"n_states": int(len(e)), "rms_log_error": float(np.sqrt(np.mean(e ** 2))),
            "median_abs_log_error": float(np.median(np.abs(e))), "mean_log_error": float(np.mean(e)),
            "rms_log_error_ME_OR_VT": float(np.sqrt(np.mean(low ** 2))),
            **{f"log_error_{s}": float(by.get(s, np.nan)) for s in STATEWIDE_STATES},
            "log_error_CA": float(ca.iloc[0]) if len(ca) else np.nan}


# ---------------------------------------------------------------------------
# Wisconsin
# ---------------------------------------------------------------------------

T_QUANTILES = {  # two-sided t quantiles for small df (no scipy in the project)
    0.80: {3: 1.638, 4: 1.533, 5: 1.476, 6: 1.440, 7: 1.415, 8: 1.397, 9: 1.383, 10: 1.372},
    0.95: {3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228},
}


def wi_members(wi: pd.DataFrame, law: int = 1, local: int = 0, k: int | None = None) -> pd.DataFrame:
    """Wisconsin areas as single-member rows (columns as member_frame), for prediction."""
    m = pd.DataFrame({"homes": wi["homes"].astype(float).values, "value": wi["value"].values,
                      "income": wi["income"].values, "rent": wi["rent"].values,
                      "renter_share": wi["renter_share"].values, "law": law,
                      "local": (wi["local"].values if "local" in wi and local == -1 else local),
                      "k": k if k is not None else np.nan, "pre_rate": wi["x_rate"].values,
                      "cluster": "WI", "years": 1.0, "geoid": wi["area_id"].values})
    for c, v in context(wi["homes"], wi["value"], wi["income"]).items():
        m[c] = v
    return m


def predict_wi(fit_: PFit, wi: pd.DataFrame, years=(1, 2, 3, 4, 5)) -> pd.DataFrame:
    """Per-area with-law rate by year since the law (k = 1..5; k >= 4 = plateau)."""
    out = pd.DataFrame({"area_id": wi["area_id"].values})
    for k in years:
        out[f"y_k{k}"] = predict_members(fit_, wi_members(wi, 1, 0, k))
    out["y_nolaw"] = predict_members(fit_, wi_members(wi, 0, 0, None))
    return out


def additional(wi: pd.DataFrame, y_by_year: np.ndarray, baseline_by_year: np.ndarray, growth: np.ndarray | None = None,
               per_area_max: bool = True) -> np.ndarray:
    """Additional permits by forecast year. y_by_year: areas x years (realized with-law rate,
    ramp already inside). per_area_max: H x max(y - x g, 0) per area, the engine's rule (no area
    below its current rate); otherwise statewide H x y minus the statewide baseline."""
    H = wi["homes"].to_numpy(float)[:, None]
    if per_area_max:
        x = wi["x_rate"].to_numpy(float)[:, None]
        g = np.ones_like(y_by_year) if growth is None else growth
        return (H * np.maximum(y_by_year - x * g, 0) / 1000).sum(axis=0)
    return (H * y_by_year / 1000).sum(axis=0) - baseline_by_year


def implied_ramp(wi: pd.DataFrame, y_by_year: np.ndarray) -> np.ndarray:
    """Engine-form ramp on the increment, homes-weighted: (ybar_t - xbar) / (ybar_plateau - xbar)."""
    H = wi["homes"].to_numpy(float)
    yb = (H[:, None] * y_by_year).sum(axis=0) / H.sum()
    xb = (H * wi["x_rate"].to_numpy(float)).sum() / H.sum()
    return np.clip((yb - xb) / (yb[-1] - xb), 0, 1)


# ---------------------------------------------------------------------------
# A. Statewide adoption curve
# ---------------------------------------------------------------------------

def adoption_points(rows: pd.DataFrame, homes: pd.Series) -> pd.DataFrame:
    """Observed rate by state and year since the law (state-level series, law rows only)."""
    r = rows.assign(homes=homes.values)
    r = r[r["series"].isin(STATE_CODING.keys()) & r["law"].eq(1)].copy()
    r["rate"] = r["count"] / (r["years"] * r["homes"]) * 1000
    return r[["cluster", "series", "year", "k", "count", "homes", "rate", "incl_new_house", "coverage"]]


def adoption_curve(points: pd.DataFrame, max_k: int = 5, new_house: bool = False, coverage: bool = False) -> pd.DataFrame:
    """Median observed rate by k across states. Years beyond the data hold the last supported
    median (flagged). Named measurement adjustments are optional."""
    p = points.copy()
    if new_house:
        p.loc[p["incl_new_house"].astype(bool), "rate"] *= NEW_HOUSE_FACTOR
    if coverage:
        p["rate"] = p["rate"] / p["coverage"]
    rows, last = [], None
    for k in range(1, max_k + 1):
        g = p[p["k"].eq(k)]
        if len(g):
            last = dict(k=k, n_states=int(g["cluster"].nunique()), states=",".join(sorted(g["cluster"])),
                        median_rate=float(g["rate"].median()), min_rate=float(g["rate"].min()),
                        max_rate=float(g["rate"].max()), mean_rate=float(g["rate"].mean()), basis="observed median")
            rows.append(last)
        else:
            rows.append({**last, "k": k, "basis": f"no state observed; holds year {last['k']} median"})
    return pd.DataFrame(rows)


def apply_curve(rate_by_year: np.ndarray, baseline_by_year: np.ndarray, homes: float = WI_HOMES) -> pd.DataFrame:
    total = homes * np.asarray(rate_by_year) / 1000
    add = total - np.asarray(baseline_by_year)
    return pd.DataFrame({"year": range(1, len(total) + 1), "rate": rate_by_year, "with_law_total": total,
                         "baseline": baseline_by_year, "additional": add})


# ---------------------------------------------------------------------------
# Two-stage (within / between) model: the recommended pooled form
# ---------------------------------------------------------------------------
# Stage 1 (within states): weighted Poisson with one intercept per state (cluster) plus terms that
#   vary inside a state: a place's value / income relative to its state, size, years since the
#   law, law in force (before/after in WA, RI, Denver; Seattle 2024), local reform. California's
#   457 places teach this stage how rates vary between places and over time.
# Stage 2 (between states): each state's intercept (its level with no law and no local reform, at
#   its own typical place) regressed on the state's typical home value / income, every state
#   counting once. The residual spread (tau) is the between-state uncertainty for a new state.
# This is the "within-between" (Mundlak) random-intercept model fitted in two steps; with
# California's over-dispersed counts a random intercept is effectively a free per-state
# intercept, so the two-step form gives the same answer and is easier to explain.

@dataclass(frozen=True)
class TSpec:
    name: str
    within: tuple[str, ...]
    between: tuple[str, ...]
    label: str = ""
    ca_carry: str = ""
    stage2_clusters: tuple[str, ...] | None = None   # None = every cluster


MARKET_TERMS = ("value_dev", "income_dev", "log_homes", "hinge", "renter_share", "log_value", "log_income")


def center_within(X: np.ndarray, names: list[str], m: pd.DataFrame) -> np.ndarray:
    """Centre every market term inside its state (cluster): subtract the homes-weighted mean over
    the state's distinct member geographies, so a state's intercept is its level at its own
    typical place and nothing about a state's geography (e.g. Wisconsin's many small towns)
    leaks into its level."""
    X = X.copy()
    cl = m["cluster"].to_numpy()
    geo = m["geoid"].to_numpy() if "geoid" in m else np.arange(len(m)).astype(str)
    h = m["homes"].to_numpy(float)
    cols = [j for j, nm in enumerate(names) if nm in MARKET_TERMS]
    for c in np.unique(cl):
        sel = np.flatnonzero(cl == c)
        _, first = np.unique(geo[sel], return_index=True)
        idx = sel[first]
        for j in cols:
            X[sel, j] -= np.average(X[idx, j], weights=h[idx])
    return X


def between_design(ctx: pd.DataFrame, terms: tuple[str, ...]) -> np.ndarray:
    cols = [np.ones(len(ctx))]
    for t in terms:
        if t == "value_ctx":
            cols.append(ctx["ctx_log_value"].to_numpy(float) - np.log(CENTRES["value"]))
        elif t == "income_ctx":
            cols.append(ctx["ctx_log_income"].to_numpy(float) - np.log(CENTRES["income"]))
        elif t == "pti_ctx":
            cols.append(ctx["ctx_log_value"].to_numpy(float) - ctx["ctx_log_income"].to_numpy(float) - np.log(5.0))
        elif t == "value_ctx_above600":
            cols.append(np.maximum(ctx["ctx_log_value"].to_numpy(float) - np.log(600_000.0), 0.0))
        else:
            raise ValueError(t)
    return np.column_stack(cols)


@dataclass
class TFit:
    spec: TSpec
    within_names: list[str]
    beta: np.ndarray            # within coefficients (no intercept)
    alpha: pd.Series            # per-cluster intercepts (stage 1)
    ctx: pd.DataFrame           # per-cluster context
    gamma: np.ndarray           # stage-2 coefficients
    tau: float                  # stage-2 residual SD (log scale)
    stage2: pd.DataFrame        # cluster, alpha, fitted, residual
    se_within: np.ndarray
    xtx_inv: np.ndarray         # stage-2 (Z'Z)^-1 for prediction leverage

    def alpha_hat(self, ctx: pd.DataFrame) -> np.ndarray:
        return between_design(ctx, self.spec.between) @ self.gamma

    def leverage(self, ctx: pd.DataFrame) -> np.ndarray:
        Z = between_design(ctx, self.spec.between)
        return np.einsum("ij,jk,ik->i", Z, self.xtx_inv, Z)

    def predict_members(self, m: pd.DataFrame, alpha: np.ndarray | None = None) -> np.ndarray:
        X, names = design(m, self.spec.within)
        X = center_within(X, names, m)
        idx = [names.index(nm) for nm in self.within_names]
        a = self.alpha_hat(m[["ctx_log_value", "ctx_log_income"]]) if alpha is None else alpha
        return np.exp(a + X[:, idx] @ self.beta)


def _scoring(X, off, ri, n, y, w, beta0, maxit=200, tol=1e-10):
    beta = beta0.copy()

    def ll(b):
        _, mu = _mu(X, off, ri, n, b)
        return float(np.sum(w * (y * np.log(mu) - mu)))

    cur = ll(beta)
    for _ in range(maxit):
        a, mu = _mu(X, off, ri, n, beta)
        S = np.zeros((n, X.shape[1]))
        np.add.at(S, ri, a[:, None] * X)
        g = (w * (y / mu - 1)) @ S
        info = (S.T * (w / mu)) @ S
        step = np.linalg.solve(info + 1e-9 * np.eye(len(beta)), g)
        t = 1.0
        while True:
            nb = beta + t * step
            with np.errstate(over="ignore", invalid="ignore"):
                nl = ll(nb)
            if np.isfinite(nl) and nl >= cur - 1e-12:
                break
            t /= 2
            if t < 1e-8:
                nb, nl = beta, cur
                break
        done = abs(nl - cur) < tol * (1 + abs(cur))
        beta, cur = nb, nl
        if done:
            break
    a, mu = _mu(X, off, ri, n, beta)
    S = np.zeros((n, X.shape[1]))
    np.add.at(S, ri, a[:, None] * X)
    info = (S.T * (w / mu)) @ S
    return beta, info, S, mu


def fit_two_stage(p: Pooled, spec: TSpec, weights: str = "equal_state") -> TFit:
    m = member_frame(p)
    Xw, names = design(m, spec.within)
    Xw = center_within(Xw, names, m)
    Xw, names = Xw[:, 1:], names[1:]                    # drop the common intercept
    keep = np.abs(Xw).sum(axis=0) > 0
    Xw, names = Xw[:, keep], [nm for nm, k in zip(names, keep) if k]
    cl = sorted(p.rows["cluster"].unique())
    D = (m["cluster"].to_numpy()[:, None] == np.array(cl)[None, :]).astype(float)
    X = np.hstack([D, Xw])
    ri = m["ri"].to_numpy()
    n = len(p.rows)
    off = np.log(m["years"].to_numpy(float) * m["homes"].to_numpy(float) / 1000)
    y = p.rows["count"].to_numpy(float)
    w = cluster_weights(p.rows, p.row_homes(), weights)
    b0 = np.zeros(X.shape[1])
    for j, c in enumerate(cl):
        rc = p.rows["cluster"].to_numpy() == c
        mc = m["cluster"].to_numpy() == c
        b0[j] = np.log(max(y[rc].sum(), 0.5) / np.exp(off[mc]).sum())
    beta, info, S, mu = _scoring(X, off, ri, n, y, w, b0)
    sc = (w * (y / mu - 1))[:, None] * S
    rcl = p.rows["cluster"].to_numpy()
    U = np.vstack([sc[rcl == c].sum(axis=0) for c in cl])
    bread = np.linalg.pinv(info)
    se = np.sqrt(np.clip(np.diag(bread @ (U.T @ U) @ bread), 0, None))
    alpha = pd.Series(beta[:len(cl)], index=cl)
    ctx = m.drop_duplicates("cluster").set_index("cluster")[["ctx_log_value", "ctx_log_income"]].loc[cl]
    use = cl if spec.stage2_clusters is None else [c for c in cl if c in spec.stage2_clusters]
    Z = between_design(ctx.loc[use], spec.between)
    a = alpha.loc[use].to_numpy()
    ztz_inv = np.linalg.pinv(Z.T @ Z)
    gamma = ztz_inv @ Z.T @ a
    res = a - Z @ gamma
    dof = max(len(use) - Z.shape[1], 1)
    tau = float(np.sqrt(res @ res / dof))
    st2 = pd.DataFrame({"cluster": use, "alpha": a, "fitted": Z @ gamma, "residual": res,
                        "ctx_value": np.exp(ctx.loc[use, "ctx_log_value"].to_numpy()),
                        "ctx_income": np.exp(ctx.loc[use, "ctx_log_income"].to_numpy())})
    return TFit(spec, names, beta[len(cl):], alpha, ctx, gamma, tau, st2, se[len(cl):], ztz_inv)


def predict_rows_ts(f: TFit, p: Pooled) -> pd.DataFrame:
    m = member_frame(p)
    rate = f.predict_members(m)
    ex = m["years"].to_numpy(float) * m["homes"].to_numpy(float) / 1000
    mu = np.bincount(m["ri"].to_numpy(), weights=rate * ex, minlength=len(p.rows))
    r = p.rows.reset_index(drop=True).copy()
    r["homes"] = p.row_homes().to_numpy()
    r["pred_count"] = mu
    return r


def loso_ts(p: Pooled, spec: TSpec, weights: str = "equal_state", clusters=None) -> pd.DataFrame:
    """Leave one state out for the two-stage model: both stages refitted without the state; the
    held-out state's level comes only from stage 2 at its own context."""
    out = []
    ev = eval_mask(p.rows)
    for c in clusters or sorted(p.rows["cluster"].unique()):
        tr = p.rows["cluster"].ne(c).to_numpy()
        te = (~tr) & ev
        if not te.any():
            continue
        f = fit_two_stage(subset(p, tr), spec, weights)
        pr_ = predict_rows_ts(f, subset(p, te))
        for s, g in pr_.groupby("series"):
            hy = (g["years"] * g["homes"]).sum() / 1000
            obs, pred = g["count"].sum() / hy, g["pred_count"].sum() / hy
            out.append(dict(spec=spec.name, weights=weights, held_out=c, series=s,
                            years=f"{int(g.year.min())}-{int(g.year.max())}",
                            k=f"{int(g.k.min())}-{int(g.k.max())}" if g["k"].notna().any() else "",
                            n_rows=len(g), obs_rate=obs, pred_rate=pred,
                            ratio_obs_pred=obs / pred if pred > 0 else np.nan,
                            log_error=np.log(pred / obs) if obs > 0 and pred > 0 else np.nan))
    return pd.DataFrame(out)


def predict_wi_ts(f: TFit, wi: pd.DataFrame, years=(1, 2, 3, 4, 5), local: int = 0) -> pd.DataFrame:
    out = pd.DataFrame({"area_id": wi["area_id"].values})
    for k in years:
        out[f"y_k{k}"] = f.predict_members(wi_members(wi, 1, local, k))
    out["y_nolaw"] = f.predict_members(wi_members(wi, 0, local, None))
    return out


def chain_curve(points: pd.DataFrame, max_k: int = 5) -> pd.DataFrame:
    """Constant-composition sensitivity for the adoption curve: year-1 median, then each later
    year moves by the median year-on-year ratio among states observed in both years (so a
    change in which states are observed does not move the path). Beyond the data: held flat."""
    p = points.pivot_table(index="cluster", columns="k", values="rate")
    level = float(points[points["k"].eq(1)]["rate"].median())
    rows = [dict(k=1, chain_rate=level, n_states_ratio=int(p[1].notna().sum()), ratio=np.nan)]
    for k in range(2, max_k + 1):
        if k in p and (k - 1) in p:
            r = (p[k] / p[k - 1]).dropna()
        else:
            r = pd.Series(dtype=float)
        ratio = float(r.median()) if len(r) else 1.0
        level *= ratio
        rows.append(dict(k=k, chain_rate=level, n_states_ratio=int(len(r)), ratio=ratio))
    return pd.DataFrame(rows)

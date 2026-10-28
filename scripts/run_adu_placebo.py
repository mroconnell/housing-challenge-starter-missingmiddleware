"""ADU placebo test: strong-law (A), weaker-law (B) and no-law placebo (C) places, before and after a statewide
ADU law (real for A and B, fake for C). Plan, fixed before running: docs/adu/PLACEBO_PLAN.md. Results:
docs/adu/PLACEBO_RESULTS.md.

Outcome: ADUs (units where counted) per 1,000 ACS 2020-2024 one-unit detached homes per year. Year 0 (the year
holding the effective date) is dropped; before = years -3..-1, after = +1..+3, at least one year each.

Inputs (all already in the repo): reference/statewide_states_annual.csv, other_cities_annual.csv, other_cities_acs.csv,
madison_adu_permits_by_year.csv, sun_prairie_ / pleasant_prairie_adu_equivalent_by_year.csv,
wi_measured_permits_2022_2025.csv, madison_like_annual.csv. The Wisconsin part reruns the adopted engine
(scripts/run_adu_model.py scenario, levels and Madison path) with only the baseline changed; it needs
data/processed/model_baseline/ and writes nothing to reference/adu_model_*.csv.

Outputs: reference/adu_placebo_series.csv, adu_placebo_eligible.csv, adu_placebo_summary.csv, adu_placebo_wi.csv.
Run: uv run python scripts/run_adu_placebo.py
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
SEED = 20261027
DRAWS = 2000
CAL_YEARS = (2016, 2020, 2023, 2024)   # real year-0s of the A and B series used (CA, VT, WA, RI)
MATERIAL_RATIO = 1.25
MATERIAL_DIFF = 0.10
WINDOW_GAP = 4.0                        # years between before- and after-window centres (L-2 to L+2)
WI_WINDOW_CENTRE = 2023.5               # centre of the 2022-2025 Wisconsin measurement window


@dataclass
class Member:
    homes: float
    counts: dict            # year -> count


@dataclass
class Series:
    sid: str
    group: str              # A, B, C, A_sens, A_sub, level
    label: str
    data_type: str
    members: list = field(default_factory=list)
    rates: dict | None = None   # year -> rate, for series without counts (California non-holdout)
    year0: int | None = None    # real law year 0 (A, B)
    nolaw: tuple | None = None  # (first, last) no-law years usable as placebo (C)
    older_weak_law: bool = False
    reforms: tuple = ()         # local reform years (S2)
    note: str = ""

    @property
    def homes(self) -> float:
        return float(sum(m.homes for m in self.members)) if self.members else float("nan")

    def years(self) -> set:
        if self.rates is not None:
            return set(self.rates)
        ys = set()
        for m in self.members:
            ys |= set(m.counts)
        return ys

    def window(self, years) -> dict | None:
        """Rate over the given years (only years with data). None if no year has data."""
        years = sorted(y for y in years if y in self.years())
        if not years:
            return None
        if self.rates is not None:
            return {"years": years, "count": float("nan"), "home_years_k": float("nan"),
                    "rate": float(np.mean([self.rates[y] for y in years]))}
        cnt = hy = 0.0
        for m in self.members:
            for y in years:
                if y in m.counts:
                    cnt += m.counts[y]
                    hy += m.homes / 1000
        return {"years": years, "count": cnt, "home_years_k": hy, "rate": cnt / hy * 1.0}


def before_after(s: Series, year0: int, limit: tuple | None = None) -> dict | None:
    """Before (-3..-1) and after (+1..+3) windows around year0, optionally restricted to years in `limit`
    (first, last). None unless both windows have at least one year."""
    def ok(y):
        return limit is None or limit[0] <= y <= limit[1]
    b = s.window([y for y in range(year0 - 3, year0) if ok(y)])
    a = s.window([y for y in range(year0 + 1, year0 + 4) if ok(y)])
    if b is None or a is None:
        return None
    d = a["rate"] - b["rate"]
    r = a["rate"] / b["rate"] if b["rate"] > 0 else float("nan")
    return {"before": b, "after": a, "D": d, "R": r}


def eligible_years(s: Series, rule: str) -> list[int]:
    lo, hi = s.nolaw
    cands = CAL_YEARS if rule == "calendar" else range(lo - 2, hi + 1)
    return [L for L in cands if before_after(s, L, s.nolaw) is not None]


def has_reform(s: Series, L: int) -> bool:
    return any(L - 3 <= y <= L + 3 for y in s.reforms)


# ---------------------------------------------------------------- loading
def _counts(df, ycol, ccol):
    return {int(y): float(c) for y, c in zip(df[ycol], df[ccol]) if pd.notna(c)}


def load_series() -> list[Series]:
    st = pd.read_csv(REF / "statewide_states_annual.csv")

    def state(sid, **kw):
        g = st[st.series.eq(sid)]
        return Series(sid=sid, members=[Member(float(g.homes.iloc[0]), _counts(g, "year", "adu_count"))],
                      label=g.geography.iloc[0].replace("\n", " "), **kw)

    oc = pd.read_csv(REF / "other_cities_annual.csv")
    acs = pd.read_csv(REF / "other_cities_acs.csv").set_index("city")

    def city(c, **kw):
        g = oc[oc.city.eq(c) & oc.status.eq("observed")]
        return Series(sid=c, members=[Member(float(acs.loc[c, "homes"]), _counts(g, "year", "adu_units"))],
                      label=acs.loc[c, "place"], data_type="city permits, ADU units excluding ADUs built with a new house",
                      **kw)

    ml = pd.read_csv(REF / "madison_like_annual.csv")

    def ml_members(state_abbr, cities=None):
        g = ml[ml.state.eq(state_abbr) & ml.adu_permits.notna()]
        if cities:
            g = g[g.city.isin(cities)]
        return [Member(float(h.homes.iloc[0]), _counts(h, "year", "adu_permits")) for _, h in g.groupby("city")]

    wim = pd.read_csv(REF / "wi_measured_permits_2022_2025.csv").set_index("place")
    mad = pd.read_csv(REF / "madison_adu_permits_by_year.csv")
    mad = mad[mad.category.eq("second_home_sf_lot") & mad.year.le(2025)]
    small = []
    for f, place in (("sun_prairie", "Sun Prairie city"), ("pleasant_prairie", "Pleasant Prairie village")):
        d = pd.read_csv(REF / f"{f}_adu_equivalent_by_year.csv")
        d = d[d.series.eq("second_home_sf_lot") & d.year.le(2025)].drop_duplicates("year")
        small.append(Member(float(wim.loc[place, "homes"]), _counts(d, "year", "units")))

    ca_nh = Series("CA_nonholdout", "A", "California, CA-study non-holdout grouped jurisdictions",
                   "HCD-reported ADU permits (period rates from CA_STUDY_RESULTS.md section 8)",
                   rates={2014: 0.12, 2015: 0.12, 2016: 0.12, 2017: 0.66, 2018: 1.48, 2019: 1.48}, year0=2016,
                   note="rates only (no counts): 2014-16 period 0.12, 2017 0.66, 2018-19 period 1.48")
    ser = [
        ca_nh,
        state("WA_inc_exSeattle", group="A", data_type="OFM ADU permits, estimate years (Apr-Mar)", year0=2023,
              note="law effective 2023-07-23; local compliance 2025-06-30 or later"),
        state("RI_statewide", group="B", data_type="RI EOH ADU permits, self-reported", year0=2024,
              note="law effective 2024-06-25; only 2025 after"),
        state("VT_chittenden", group="B", data_type="Chittenden RPC ADU inventory by year built", year0=2020,
              note="Act 179 effective 2020-10-12"),
        state("OR_panel32_exPortland", group="A_sens", data_type="DLCD HB 4006 ADU permits, 32 cities", year0=2018,
              note="S3 only: no pre-law year exists, so the 2018 law year stands in for 'before' (2019-2021 after)"),
        Series("CA_madison_like", "A_sub", "California Madison-like cities (15), pooled",
               "HCD-reported ADU permits", members=ml_members("CA"), year0=2016),
    ]
    for c in ("Spokane", "Spokane Valley", "Tacoma", "Vancouver", "Yakima"):
        ser.append(Series(f"WA_{c.replace(' ', '_')}", "A_sub", f"{c}, WA (Madison-like)", "OFM ADU permits, estimate years",
                          members=ml_members("WA", [c]), year0=2023))
    for sid, lab in (("ME_statewide", "level"), ("MA_statewide", "level"), ("UT_mih", "level"), ("NH_conversions", "level")):
        ser.append(state(sid, group=lab, data_type="level only (no before year)"))
    ser.append(Series("OR_madison_like", "level", "Oregon Madison-like cities (4), pooled", "DLCD HB 4006 ADU permits",
                      members=ml_members("OR")))
    # ---- C: no statewide law in the years used
    ser += [
        city("minneapolis", group="C", nolaw=(2017, 2025), reforms=(2020, 2021)),
        city("denver", group="C", nolaw=(2016, 2023), reforms=(2023,)),
        city("austin", group="C", nolaw=(2005, 2023), reforms=(2015,)),
        city("portland", group="C", nolaw=(2005, 2017), reforms=(2010, 2016)),
        Series("madison", "C", "Madison city, WI", "Madison second-home permits on single-family lots (issued)",
               members=[Member(53292.0, _counts(mad, "year", "units"))], nolaw=(2014, 2025), reforms=(2021,)),
        Series("wi_small", "C", "Sun Prairie city and Pleasant Prairie village, WI (pooled)",
               "second-home permits on single-family lots (Sun Prairie applications, Pleasant Prairie issued)",
               members=small, nolaw=(2014, 2025)),
        state("HI_honolulu", group="C", data_type="Honolulu permits flagged ADU", nolaw=(2016, 2023), reforms=(2015,),
              note="moved from B: all data before Hawaii's 2024-05-28 law"),
        state("MD_montgomery", group="C", data_type="Montgomery County permits naming an ADU (keyword count)",
              nolaw=(2019, 2024), reforms=(2019,), note="moved from B: all data before Maryland's 2025-10-01 law"),
        city("seattle", group="C", nolaw=(2005, 2022), older_weak_law=True, reforms=(2009, 2019)),
    ]
    wa_pre = state("WA_inc_exSeattle", group="C", data_type="OFM ADU permits, estimate years (Apr-Mar)",
                   nolaw=(2011, 2023), older_weak_law=True, note="before EHB 1337; 1993 law allowed discretionary permits")
    wa_pre.sid = "WA_inc_exSeattle_prelaw"
    ca_pre = Series("CA_madison_like_prelaw", "C", "California Madison-like cities (15), pooled, before 2017",
                    "HCD-reported ADU permits", members=ml_members("CA"), nolaw=(2012, 2016), older_weak_law=True,
                    note="AB 1866 (2003) ministerial review in force")
    ser += [wa_pre, ca_pre]
    return ser


# ---------------------------------------------------------------- statistics
def group_stats(rows: list[dict], weighted: bool = False) -> dict:
    """rows: per-series dicts with before/after windows. Equal weight: mean D, mean(after)/mean(before).
    Home-weighted: pooled counts / pooled home-years (series without counts are left out)."""
    if not rows:
        return {"D": float("nan"), "ratio": float("nan"), "before": float("nan"), "after": float("nan"), "n": 0}
    if weighted:
        rows = [r for r in rows if not np.isnan(r["before"]["home_years_k"])]
        b = sum(r["before"]["count"] for r in rows) / sum(r["before"]["home_years_k"] for r in rows)
        a = sum(r["after"]["count"] for r in rows) / sum(r["after"]["home_years_k"] for r in rows)
        return {"D": a - b, "ratio": a / b if b else float("nan"), "before": b, "after": a, "n": len(rows)}
    b = float(np.mean([r["before"]["rate"] for r in rows]))
    a = float(np.mean([r["after"]["rate"] for r in rows]))
    return {"D": float(np.mean([r["D"] for r in rows])), "ratio": a / b if b else float("nan"), "before": b, "after": a,
            "n": len(rows)}


def resample(cser: list[Series], rule: str, draws: int = DRAWS, seed: int = SEED, drop_reform: bool = False,
             weighted: bool = False, size: int | None = None) -> tuple[pd.DataFrame, int]:
    """C's group statistics over `draws` placebo draws. size=None: every C series in each draw (the plan).
    size=k (deviation D1): each draw takes k distinct C series at random (among those with an eligible year), so
    the placebo group has as many series as A or B."""
    rng = np.random.default_rng(seed)
    elig = {}
    for s in cser:
        ys = eligible_years(s, rule)
        if drop_reform:
            ys = [L for L in ys if not has_reform(s, L)]
        elig[s.sid] = (s, ys)
    usable = [sid for sid, (_, ys) in elig.items() if ys]
    out, skipped = [], 0
    for _ in range(draws):
        rows = []
        pick = elig if size is None else {k: elig[k] for k in rng.choice(usable, size=size, replace=False)}
        for sid, (s, ys) in pick.items():
            if not ys:
                skipped += 1
                continue
            L = int(rng.choice(ys))
            rows.append(before_after(s, L, s.nolaw))
        out.append(group_stats(rows, weighted))
    return pd.DataFrame(out), skipped


def pct(v, q):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    return float(np.percentile(v, q))


def share_ge(v, x):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    return float((v >= x - 1e-12).mean())


def series_row(s: Series, ba: dict | None, year0, kind: str) -> dict:
    r = {"series": s.sid, "group": s.group, "kind": kind, "label": s.label, "data_type": s.data_type,
         "homes": s.homes, "year0": year0, "older_weak_state_law": s.older_weak_law, "note": s.note}
    if ba is None:
        lvl = s.window(sorted(s.years()))
        r.update({"after_years": "|".join(map(str, sorted(s.years()))), "after_rate": lvl["rate"] if lvl else np.nan,
                  "after_count": lvl["count"] if lvl else np.nan})
        return r
    for k in ("before", "after"):
        w = ba[k]
        r.update({f"{k}_years": "|".join(map(str, w["years"])), f"{k}_count": w["count"],
                  f"{k}_home_years_k": w["home_years_k"], f"{k}_rate": w["rate"]})
    r.update({"D": ba["D"], "R": ba["R"]})
    return r


# ---------------------------------------------------------------- Wisconsin engine cases
def nolaw_median_ratio() -> float:
    """Median after/before ratio of the no-law placebo group C (main case: calendar-matched fake law years, every C
    series in each draw), unrounded. Same draws as the "main" row of reference/adu_placebo_summary.csv."""
    dist, _ = resample([s for s in load_series() if s.group == "C"], "calendar")
    return pct(dist["ratio"], 50)


def rising_growth(areas: pd.DataFrame, growth: pd.DataFrame, ratio: float) -> pd.DataFrame:
    """Baseline growth table g (area_id, year, g) with every place's current-law rate rising proportionally:
    x * ratio^((t - 2023.5) / 4), on top of the adopted g (recently liberalized places' ramps)."""
    from missing_middleware.model import engine as e
    gmap = {(r.area_id, int(r.year)): float(r.g) for r in growth.itertuples()}
    return pd.DataFrame([{"area_id": aid, "year": k,
                          "g": gmap.get((aid, k), 1.0) * ratio ** (((2026 + k) - WI_WINDOW_CENTRE) / WINDOW_GAP)}
                         for aid in areas.area_id for k in e.YEARS])


def wisconsin_cases(trend_cases: list[tuple[str, str, float]]) -> pd.DataFrame:
    """Adopted engine with only the current-law baseline changed. trend_cases: (case, kind, value) with kind
    'ratio' (proportional: x * f^(t-2023.5), f = value^(1/4)) or 'diff' (additive: + value/4 per year)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_adu_model as ram
    from missing_middleware.model import engine as e
    from missing_middleware.model.params import area_paths
    from missing_middleware.paths import PROCESSED

    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")
    growth = pd.read_parquet(PROCESSED / "model_baseline/engine_baseline_growth.parquet")
    scen, levels, apaths = ram.load_scenario(), ram.load_area_levels(), area_paths(ram.PARAMS)
    gmap = {(r.area_id, int(r.year)): float(r.g) for r in growth.itertuples()}

    def totals(out):
        t = e.five_year_totals(out).set_index("path")
        return {p: (float(t.loc[p, "baseline_units"]), float(t.loc[p, "additional_units"])) for p in e.PATHS}

    adopted = totals(e.run(areas, scen, growth, levels, apaths))
    chk = pd.read_csv(REF / "adu_model_statewide.csv").set_index("path")
    for p, (b, a) in adopted.items():
        if abs(a - chk.loc[p, "additional_units"]) > 0.5 or abs(b - chk.loc[p, "baseline_units"]) > 0.5:
            raise SystemExit(f"engine rerun does not reproduce reference/adu_model_statewide.csv for {p}")
    rows = []

    def add(case, kind, value, t):
        for p, (b, a) in t.items():
            b0, a0 = adopted[p]
            rows.append({"case": case, "trend_kind": kind, "trend_value": value, "path": p,
                         "baseline_5yr": b, "additional_5yr": a, "with_law_5yr": b + a,
                         "d_baseline": b - b0, "d_additional": a - a0, "d_with_law": (b + a) - (b0 + a0)})

    add("adopted", "none", np.nan, adopted)
    for case, kind, v in trend_cases:
        a2, g2 = areas.copy(), []
        for ar in areas.itertuples():
            for k in e.YEARS:
                dt = (2026 + k) - WI_WINDOW_CENTRE
                g0 = gmap.get((ar.area_id, k), 1.0)
                if kind == "ratio":
                    g = None    # replaced by rising_growth() below
                else:   # additive: x*g0 + v/4*dt, expressed as a growth factor (x = 0 areas get x_t via g only if x>0)
                    g = g0 + (v / WINDOW_GAP * dt) / ar.x_rate if ar.x_rate > 0 else None
                g2.append({"area_id": ar.area_id, "year": k, "g": g})
        g2 = pd.DataFrame(g2)
        if kind == "ratio":
            g2 = rising_growth(areas, growth, v)
        if kind == "diff":
            # areas with x = 0 cannot carry an additive rise through a multiplicative g; give them a tiny x so
            # that x * g equals the additive rise (x_t = 1e-9 * g)
            zero = a2.x_rate.le(0)
            a2.loc[zero, "x_rate"] = 1e-9
            xmap = dict(zip(a2.area_id, a2.x_rate))
            g2["g"] = [g if g is not None else (v / WINDOW_GAP * ((2026 + k) - WI_WINDOW_CENTRE)) / xmap[aid]
                       for aid, k, g in zip(g2.area_id, g2.year, g2.g)]
        add(case, kind, v, totals(e.run(a2, scen, g2, levels, apaths)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- main
def main(write: bool = True, with_engine: bool = True):
    ser = load_series()
    by = {s.sid: s for s in ser}
    srows, real = [], {}
    for s in ser:
        if s.group in ("A", "B", "A_sub"):
            ba = before_after(s, s.year0)
            real[s.sid] = ba
            srows.append(series_row(s, ba, s.year0, "real law"))
        elif s.group == "level":
            srows.append(series_row(s, None, None, "level only"))
    # S3: Oregon with the 2018 law year as "before", 2019-2021 as after
    orp = by["OR_panel32_exPortland"]
    b, a = orp.window([2018]), orp.window([2019, 2020, 2021])
    real["OR_s3"] = {"before": b, "after": a, "D": a["rate"] - b["rate"], "R": a["rate"] / b["rate"]}
    r = series_row(orp, real["OR_s3"], 2018, "real law (S3: law year as before)")
    srows.append(r)
    cser = [s for s in ser if s.group == "C"]
    erows = []
    for s in cser:
        cal = set(eligible_years(s, "calendar"))
        for L in eligible_years(s, "every"):
            ba = before_after(s, L, s.nolaw)
            rr = series_row(s, ba, L, "placebo")
            rr.update({"calendar_matched": L in cal, "window_has_local_reform": has_reform(s, L)})
            erows.append(rr)
    # Exploratory, added after the first run (PLACEBO_PLAN.md "Changes after writing"): each long A/B series' own
    # pre-law years as placebo (not part of C, not in the decision rule)
    vt_pre = Series("VT_chittenden_prelaw", "X", by["VT_chittenden"].label + ", before Act 179",
                    by["VT_chittenden"].data_type, members=by["VT_chittenden"].members, nolaw=(2010, 2019),
                    note="exploratory own pre-trend (2004 by-right law in force)")
    for s in (vt_pre,):
        for L in eligible_years(s, "every"):
            rr = series_row(s, before_after(s, L, s.nolaw), L, "own pre-law placebo (exploratory)")
            rr.update({"calendar_matched": L in CAL_YEARS, "window_has_local_reform": False})
            erows.append(rr)
    elig = pd.DataFrame(erows)

    A = [real["CA_nonholdout"], real["WA_inc_exSeattle"]]
    B = [real["RI_statewide"], real["VT_chittenden"]]
    cases = {
        "main": dict(A=A, B=B, C=cser, rule="calendar"),
        "S1_never_law_states": dict(A=A, B=B, C=[s for s in cser if not s.older_weak_law], rule="calendar"),
        "S2_drop_local_reform_windows": dict(A=A, B=B, C=cser, rule="calendar", drop_reform=True),
        "S3_oregon_in_A": dict(A=A + [real["OR_s3"]], B=B, C=cser, rule="calendar"),
        "S4_every_year_rule": dict(A=A, B=B, C=cser, rule="every"),
        "S5_home_weighted": dict(A=A, B=B, C=cser, rule="calendar", weighted=True),
        "S6_CA_madison_like": dict(A=[real["CA_madison_like"], real["WA_inc_exSeattle"]], B=B, C=cser, rule="calendar"),
        "S1+S2": dict(A=A, B=B, C=[s for s in cser if not s.older_weak_law], rule="calendar", drop_reform=True),
        # deviations added after the first run (PLACEBO_PLAN.md "Changes after writing"): placebo groups of 2 series,
        # the size of A and of B, instead of all C series averaged together
        "D1_size_matched_2": dict(A=A, B=B, C=cser, rule="calendar", size=2),
        "D1_size_matched_2_every_year": dict(A=A, B=B, C=cser, rule="every", size=2),
    }
    summ, dists = [], {}
    for name, c in cases.items():
        w = c.get("weighted", False)
        dist, skipped = resample(c["C"], c["rule"], drop_reform=c.get("drop_reform", False), weighted=w,
                                 size=c.get("size"))
        dists[name] = dist
        ga, gb = group_stats(c["A"], w), group_stats(c["B"], w)
        for stat in ("D", "ratio"):
            v = dist[stat]
            summ.append({"case": name, "statistic": stat, "A": ga[stat], "B": gb[stat],
                         "A_before": ga["before"], "A_after": ga["after"], "B_before": gb["before"], "B_after": gb["after"],
                         "n_A": ga["n"], "n_B": gb["n"], "n_C_series": len(c["C"]),
                         "C_p05": pct(v, 5), "C_p50": pct(v, 50), "C_p95": pct(v, 95), "C_mean": float(np.nanmean(v)),
                         "C_before_p50": pct(dist["before"], 50), "C_after_p50": pct(dist["after"], 50),
                         "share_C_ge_A": share_ge(v, ga[stat]), "share_C_ge_B": share_ge(v, gb[stat]),
                         "draws": DRAWS, "seed": SEED, "series_skipped_in_draws": skipped, "rule": c["rule"],
                         "weighting": "home-weighted" if w else "equal per series",
                         "C_series_per_draw": str(c.get("size") or "all")})
    summ = pd.DataFrame(summ)
    # single-series spread: every eligible (series, fake year) vs the real A and B series
    m = summ[summ.case.eq("main")].set_index("statistic")
    trend_ratio, trend_d = m.loc["ratio", "C_p50"], m.loc["D", "C_p50"]
    trend_ratio95 = m.loc["ratio", "C_p95"]
    wi = None
    if with_engine:
        wi = wisconsin_cases([("rising baseline, proportional, C median ratio", "ratio", trend_ratio),
                              ("rising baseline, proportional, C 95th-percentile ratio", "ratio", trend_ratio95),
                              ("rising baseline, additive, C median change", "diff", trend_d)])
    if write:
        pd.DataFrame(srows).round(4).to_csv(REF / "adu_placebo_series.csv", index=False)
        elig.round(4).to_csv(REF / "adu_placebo_eligible.csv", index=False)
        summ.round(4).to_csv(REF / "adu_placebo_summary.csv", index=False)
        if wi is not None:
            wi.round({c: 1 for c in wi.columns if c not in ("trend_value",)} | {"trend_value": 4}).to_csv(
                REF / "adu_placebo_wi.csv", index=False)
    return {"series": pd.DataFrame(srows), "eligible": elig, "summary": summ, "wi": wi, "dists": dists}


if __name__ == "__main__":
    res = main(with_engine="--no-engine" not in sys.argv)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    s = res["series"]
    print(s[["series", "group", "year0", "before_years", "before_rate", "after_years", "after_rate", "D", "R"]]
          .round(3).to_string(index=False))
    e = res["eligible"]
    print(e[["series", "year0", "before_rate", "after_rate", "D", "R", "calendar_matched", "window_has_local_reform"]]
          .round(3).to_string(index=False))
    print(res["summary"].drop(columns=["draws", "seed", "rule", "weighting"]).round(3).to_string(index=False))
    if res["wi"] is not None:
        print(res["wi"].round(1).to_string(index=False))

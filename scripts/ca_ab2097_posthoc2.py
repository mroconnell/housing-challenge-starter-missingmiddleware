"""POST HOC (written after the main and side-check results were seen; Ryan 2026-11-05 21:35). Reported only; none of
these changes the main result or the plan's reading rules.

    uv run python scripts/ca_ab2097_posthoc2.py

1. Non-tax-credit homes: homes other than ADUs minus homes in LIHTC-flagged projects (Table A2 financing field),
   main group, main map, headline and lead checks, same method as the main result.
2. City size as a continuous variable in the city-level (BPS) check: change in BPS permits per 1,000 existing homes a
   year (2023-2025 minus 2018-2022) = a + b*share + c*log10(homes) + d*share*log10(homes), weighted by 2020 homes and
   with equal weight. Reported: d, and the share slope (b + d*log10(homes)) at 5,000, 20,000, 100,000 and 500,000
   existing homes. Same for the lead placebo (2021-2022 minus 2018-2020). 90% ranges from 2,000 resamples of places.
3. Trend-adjusted event study, main and placebo groups: a straight line is fitted to each resample's 2018-2022 year
   values (relative to 2022) and the after years are measured against the line's extension; estimate = mean over
   2023-2025 of (value minus line). A line through five years is fragile; reported beside the unadjusted headline.
4. City types, reusing the parking thread's classification unchanged (reference/parking_place_ruca_traits.csv,
   commits 19523fef and bf1b9acc; area_class from RUCA 2010/2020 and Census principal cities, Feb 2013 list main,
   July 2023 list as check): the city-level check's share slope within each area_class, and the main near-vs-ring
   headline within each area_class (jurisdictions joined by BPS id from reference/ca_jurisdiction_crosswalk.csv;
   unincorporated county areas have no class and are left out of this split).

Outputs: reference/ca_ab2097_posthoc2_*.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ca_ab2097_estimate as E  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

UNIT = "homes in issued permits per 1,000 existing homes (2020) per year, 2023-2025 vs 2018-2022"


def place_table(b: pd.DataFrame) -> pd.DataFrame:
    """The city-level check's place table (same construction as ca_ab2097_estimate.dose_check) plus area class."""
    cw = pd.read_csv(REFERENCE / "ca_jurisdiction_crosswalk.csv", dtype=str)
    cities = cw[(cw.juris_type == "city") & cw.placefp.notna()][["juris_name", "placefp", "bps_ids"]]
    bp = []
    for y in E.YEARS:
        d = parsers.read_bps(RAW / "census_bps_ca" / f"place_{y}.txt", "place", state_fips="06")
        d["year"] = y
        bp.append(d[["fips_place", "year", "units_total"]])
    units = pd.concat(bp).groupby(["fips_place", "year"]).units_total.sum().unstack(fill_value=0)
    homes = b.groupby("juris").homes.sum()
    near = b[b.zone_main == "near"].groupby("juris").homes.sum()
    t = cities.assign(homes=cities.juris_name.map(homes), near=cities.juris_name.map(near).fillna(0))
    t = t[(t.homes > 0) & ~t.juris_name.isin(E.PLACEBO | E.DROPPED) & t.placefp.isin(units.index)].copy()
    rate = units.loc[t.placefp].div(t.homes.to_numpy(), axis=0) * 1000
    t["share"] = (t.near / t.homes).to_numpy()
    t["change"] = (rate[E.AFTER].mean(1) - rate[E.BEFORE].mean(1)).to_numpy()
    t["lead"] = (rate[[2021, 2022]].mean(1) - rate[[2018, 2019, 2020]].mean(1)).to_numpy()
    rt = pd.read_csv(REFERENCE / "parking_place_ruca_traits.csv", dtype=str)
    rt = rt[rt.state_fips == "06"].assign(bps=lambda r: r.key.str.split("|").str[1])
    t["bps"] = t.bps_ids.fillna("").str.split(";").str[0].str.strip()
    t = t.merge(rt[["bps", "area_class", "area_class_pc2023"]], on="bps", how="left")
    t["area_class"] = t.area_class.fillna("unmatched")
    return t


def wls(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    sw = np.sqrt(w / w.sum())
    return np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]


def size_interaction(t: pd.DataFrame) -> pd.DataFrame:
    rows = []
    lh = np.log10(t.homes.to_numpy(float))
    X = np.c_[np.ones(len(t)), t.share, lh, t.share * lh]
    rng = np.random.default_rng(E.SEED)
    idx = [rng.integers(0, len(t), len(t)) for _ in range(E.DRAWS)]
    for col in ("change", "lead"):
        y = t[col].to_numpy(float)
        for wname, w in (("homes-weighted", t.homes.to_numpy(float)), ("equal weight", np.ones(len(t)))):
            beta = wls(X, y, w)
            dr = np.array([wls(X[i], y[i], w[i]) for i in idx])
            lo, hi = E.interval(dr[:, 3])
            rows.append({"outcome": col, "weight": wname, "term": "share x log10(homes)", "estimate": beta[3],
                         "low": lo, "high": hi})
            for h in (5_000, 20_000, 100_000, 500_000):
                v, dv = beta[1] + beta[3] * np.log10(h), dr[:, 1] + dr[:, 3] * np.log10(h)
                lo, hi = E.interval(dv)
                rows.append({"outcome": col, "weight": wname, "term": f"share slope at {h:,} existing homes",
                             "estimate": v, "low": lo, "high": hi})
    out = pd.DataFrame(rows)
    out["n_places"] = len(t)
    out["unit"] = "change in BPS permits per 1,000 existing homes a year per 1.0 share of homes within 1/2 mile"
    return out


def by_class(t: pd.DataFrame, b, p, main_j) -> pd.DataFrame:
    rows = []
    for cls, g in t.groupby("area_class"):
        x, y, w = g.share.to_numpy(float), g.change.to_numpy(float), g.homes.to_numpy(float)
        if len(g) < 5 or np.ptp(x) == 0:
            rows.append({"area_class": cls, "check": "city-level share slope (homes-weighted)", "n": len(g),
                         "estimate": np.nan, "note": "too few places or no spread in share"})
            continue
        X = np.c_[np.ones(len(g)), x]
        beta = wls(X, y, w)
        rng = np.random.default_rng(E.SEED)
        dr = np.array([wls(X[i], y[i], w[i])[1] for i in (rng.integers(0, len(g), len(g)) for _ in range(E.DRAWS))])
        lo, hi = E.interval(dr)
        rows.append({"area_class": cls, "check": "city-level share slope (homes-weighted)", "n": len(g),
                     "estimate": beta[1], "low": lo, "high": hi})
    jc = dict(zip(t.juris_name, t.area_class))
    c = E.cells_for(b, "main")
    for cls in sorted(set(jc.values())):
        js = E.with_treated_land(c, [j for j in main_j if jc.get(j) == cls])
        if len(js) < 5:
            rows.append({"area_class": cls, "check": "near vs ring headline (homes other than ADUs)", "n": len(js),
                         "estimate": np.nan, "note": "fewer than 5 jurisdictions"})
            continue
        est, dr = E.event_study(E.group(cls, js), c, E.permits_for(p, "main"), "homes_non_adu")
        e, d = E.period_contrast(est, dr, E.BEFORE, E.AFTER)
        lo, hi = E.interval(d)
        rows.append({"area_class": cls, "check": "near vs ring headline (homes other than ADUs)", "n": len(js),
                     "estimate": e, "low": lo, "high": hi})
    return pd.DataFrame(rows)


def trend_adjusted(est: np.ndarray, dr: np.ndarray) -> tuple[float, np.ndarray]:
    yrs = np.array(E.YEARS, float)
    bi = [E.YEARS.index(y) for y in E.BEFORE]
    ai = [E.YEARS.index(y) for y in E.AFTER]

    def adj(v):
        a, b0 = np.polyfit(yrs[bi], v[bi], 1)
        return float(np.mean(v[ai] - (a * yrs[ai] + b0)))
    return adj(est), np.array([adj(r) for r in dr if np.all(np.isfinite(r))])


def main() -> None:
    b = pd.read_parquet(E.CACHE / "blocks.parquet")
    p = pd.read_parquet(E.CACHE / "permits.parquet")
    p["homes_non_tc"] = p.homes_non_adu - np.minimum(p.lihtc_homes, p.homes_non_adu)
    rep = ab.full_reporters(p)
    c = E.cells_for(b, "main")
    main_j = E.with_treated_land(c, [j for j in rep if j not in E.PLACEBO | E.DROPPED])
    plac_j = E.with_treated_land(c, [j for j in rep if j in E.PLACEBO])
    q = E.permits_for(p, "main")
    rows = []
    # 1 and 3
    for gname, js in (("main", main_j), ("placebo", plac_j)):
        for oc in ("homes_non_tc", "homes_non_adu"):
            est, dr = E.event_study(E.group(gname, js), c, q, oc)
            e, d = E.period_contrast(est, dr, E.BEFORE, E.AFTER)
            lo, hi = E.interval(d)
            rows.append({"case": "headline", "group": gname, "outcome": oc, "estimate": e, "low": lo, "high": hi, "n": len(js)})
            e2, d2 = E.period_contrast(est, dr, [2018, 2019, 2020], [2021, 2022])
            lo, hi = E.interval(d2)
            rows.append({"case": "lead check: 2021-2022 vs 2018-2020", "group": gname, "outcome": oc, "estimate": e2,
                         "low": lo, "high": hi, "n": len(js)})
            ta, dta = trend_adjusted(est, dr)
            lo, hi = E.interval(dta)
            rows.append({"case": "trend-adjusted (line through 2018-2022)", "group": gname, "outcome": oc,
                         "estimate": ta, "low": lo, "high": hi, "n": len(js)})
    a = pd.DataFrame(rows).assign(unit=UNIT, label="POST HOC")
    a.to_csv(REFERENCE / "ca_ab2097_posthoc2_outcomes_trend.csv", index=False)
    print(a.round(3).to_string(index=False))
    # 2 and 4
    t = place_table(b)
    si = size_interaction(t).assign(label="POST HOC")
    si.to_csv(REFERENCE / "ca_ab2097_posthoc2_size.csv", index=False)
    print(si.round(3).to_string(index=False))
    bc = by_class(t, b, q, main_j).assign(label="POST HOC")
    bc.to_csv(REFERENCE / "ca_ab2097_posthoc2_city_types.csv", index=False)
    print(bc.round(3).to_string(index=False))
    print(t.area_class.value_counts().to_string())


if __name__ == "__main__":
    main()

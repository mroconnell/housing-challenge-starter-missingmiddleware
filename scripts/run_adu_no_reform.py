"""ADU no-reform model, round 1 (docs/adu/NO_REFORM_R1_PLAN.md, written before running).

How many ADU permits a place issues with no statewide ADU law. Series: no-law years of state, county and city ADU
series; a city's own reform is a dated trait. Models: B0 same pace (last 3 years), B1 long pace, N1 same pace plus
the other series' trend, N2 pooled level. Tests: forward (origin Y, predict Y+1..Y+5) and held-out places.
Units: ADU permits per 1,000 one-unit detached homes per year (ACS 2020-2024 B25024_002 denominators).
Score: median |log((pred + 0.05) / (actual + 0.05))|.

Run: uv run python scripts/run_adu_no_reform.py
Outputs: reference/adu_no_reform_r1[b]_series.csv, _forward.csv, _scores.csv, _wi.csv (r1 = --uncleaned first run)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402

OFFSET = 0.05
WI_HOMES = 1_839_569
WI_BASELINE = 530.0658          # the tool's 2027-2031 current-law baseline (reference/adu_model_statewide.csv)
STATE_SERIES = {   # series id -> (level, first, last no-law year)
    "WA_inc_exSeattle": ("state", 2011, 2023), "WA_spokane": ("city", 2011, 2023), "RI_statewide": ("state", 2021, 2023),
    "HI_honolulu": ("city", 2016, 2023), "MD_montgomery": ("county", 2019, 2025), "MT_bozeman": ("city", 2020, 2023)}
CITY_SERIES = {    # city -> (place geoid, first, last no-law year, local reform year or None)
    "austin": ("4805000", 2005, 2025, 2015), "denver": ("0820000", 2016, 2023, None),
    "minneapolis": ("2743000", 2005, 2025, 2014), "seattle": ("5363000", 2005, 2023, 2005),
    "portland": ("4159000", 2005, 2017, 2005)}
MADISON = ("5548000", 2014, 2025, 2021)


def place_homes(geoids) -> dict:
    h = {}
    with open(RAW / "census_acs5_2024_tbsf/acsdt5y2024-b25024.dat", encoding="utf-8") as f:
        f.readline()
        for line in f:
            if line.startswith("1600000US") and line[9:16] in geoids:
                h[line[9:16]] = float(line.split("|", 4)[3])
    return h


def panel() -> pd.DataFrame:
    rows = []
    a = pd.read_csv(REFERENCE / "statewide_states_annual.csv")
    for s, (lvl, y0, y1) in STATE_SERIES.items():
        g = a[a.series.eq(s) & a.year.between(y0, y1)]
        for r in g.itertuples():
            rows.append(dict(series=s, level=lvl, year=int(r.year), count=float(r.adu_count), homes=float(r.homes),
                             local=np.nan))
    c = pd.read_csv(REFERENCE / "other_cities_annual.csv")
    geos = [v[0] for v in CITY_SERIES.values()] + [MADISON[0]]
    h = place_homes(geos)
    for city, (gid, y0, y1, ref) in CITY_SERIES.items():
        g = c[c.city.eq(city) & c.year.between(y0, y1)]
        for r in g.itertuples():
            rows.append(dict(series=city, level="city", year=int(r.year), count=float(r.adu_units), homes=h[gid],
                             local=float(ref is not None and r.year >= ref)))
    m = pd.read_csv(PROCESSED / "permits/second_homes_by_year.csv")
    for r in m[m.year.between(MADISON[1], MADISON[2])].itertuples():
        rows.append(dict(series="madison_wi", level="city", year=int(r.year), count=float(r.second_home_sf_lot),
                         homes=h[MADISON[0]], local=float(r.year >= MADISON[3])))
    p = pd.DataFrame(rows).dropna(subset=["count"])
    p["rate"] = p["count"] / p["homes"] * 1000
    return p


CLEAN = True    # round 1b (after the worst-miss trace): no window may span a city's own reform


def local_changes(g: pd.DataFrame, y0: int, y1: int) -> bool:
    """True when the series' local-reform status changes between years y0 and y1 (unknown status never changes)."""
    v = g[g.year.between(y0, y1)]["local"].dropna()
    return v.nunique() > 1


def score(pred, act) -> np.ndarray:
    return np.abs(np.log((np.asarray(pred) + OFFSET) / (np.asarray(act) + OFFSET)))


def trend_growth(p: pd.DataFrame, upto: int, exclude: str) -> float:
    """Median yearly growth of the other series' 3-year mean rates, (Y-2..Y) vs (Y-5..Y-3), data up to `upto`."""
    gs = []
    for s, g in p[p.series.ne(exclude) & p.year.le(upto)].groupby("series"):
        if CLEAN and local_changes(g, upto - 5, upto):
            continue
        g = g.set_index("year")["rate"]
        new, old = g.reindex(range(upto - 2, upto + 1)).dropna(), g.reindex(range(upto - 5, upto - 2)).dropna()
        if len(new) >= 2 and len(old) >= 2:
            gs.append(((new.mean() + OFFSET) / (old.mean() + OFFSET)) ** (1 / 3))
    return float(np.median(gs)) if gs else 1.0


def forward(p: pd.DataFrame) -> pd.DataFrame:
    out = []
    for s, g in p.groupby("series"):
        r = g.set_index("year")["rate"]
        for y in range(2014, 2021):
            past, fut = r[r.index <= y], r.reindex(range(y + 1, y + 6)).dropna()
            if len(past) < 3 or len(fut) < 3:
                continue
            if CLEAN and local_changes(g, y - 2, y + 5):
                continue
            b0 = past.tail(3).mean()
            gr = trend_growth(p, y, s)
            h = float(np.mean(fut.index - y))
            others = p[p.series.ne(s) & p.year.le(y)].groupby("series").apply(
                lambda x: x.sort_values("year")["rate"].tail(3).mean(), include_groups=False)
            out.append(dict(series=s, level=g.level.iloc[0], origin=y, n_future_years=len(fut), actual=fut.mean(),
                            B0=b0, B1=past.mean(), N1=(b0 + OFFSET) * gr ** h - OFFSET, N2=float(others.median()),
                            growth=gr, local_at_origin=g.set_index("year")["local"].get(y, np.nan)))
    return pd.DataFrame(out)


def held_out_places(p: pd.DataFrame) -> pd.DataFrame:
    last3 = p.sort_values("year").groupby("series").apply(lambda x: x["rate"].tail(3).mean(), include_groups=False)
    return pd.DataFrame([dict(series=s, actual=v, N2=float(last3.drop(s).median())) for s, v in last3.items()])


def boot(f: pd.DataFrame, col: str, n=1000, seed=20261031) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    ss = f["series"].unique()
    meds = []
    for _ in range(n):
        pick = rng.choice(ss, len(ss), replace=True)
        d = pd.concat([f[f.series.eq(s)] for s in pick])
        meds.append(np.median(score(d[col], d["actual"])))
    return float(np.percentile(meds, 5)), float(np.percentile(meds, 95))


def main():
    import argparse
    global CLEAN
    a = argparse.ArgumentParser()
    a.add_argument("--uncleaned", action="store_true", help="round 1 as first run: windows may span a local reform")
    CLEAN = not a.parse_args().uncleaned
    tag = "r1" if not CLEAN else "r1b"
    p = panel()
    f = forward(p)
    ho = held_out_places(p)
    rows = []
    for m in ("B0", "B1", "N1", "N2"):
        sc = score(f[m], f["actual"])
        lo, hi = boot(f, m)
        rows.append(dict(test="forward", model=m, median_abs_log=float(np.median(sc)), p05=lo, p95=hi,
                         n_cases=len(f), n_series=f.series.nunique(),
                         mean_log_bias=float(np.mean(np.log((f[m] + OFFSET) / (f["actual"] + OFFSET))))))
    sc = score(ho["N2"], ho["actual"])
    rows.append(dict(test="held-out places", model="N2", median_abs_log=float(np.median(sc)), n_cases=len(ho),
                     n_series=len(ho), mean_log_bias=float(np.mean(np.log((ho.N2 + OFFSET) / (ho.actual + OFFSET))))))
    scores = pd.DataFrame(rows)
    f["B0_abs_log"] = score(f["B0"], f["actual"])
    worst = f.sort_values("B0_abs_log").iloc[-1]

    # Wisconsin 2027-2031
    gr_now = trend_growth(p, 2025, "")
    years_ahead = np.arange(2027, 2032) - 2024           # the tool's current rates describe about 2022-2025
    pooled = float(held_out_places(p)["actual"].median())
    wi = pd.DataFrame([
        dict(model="B0 same pace (the tool today)", total_2027_2031=WI_BASELINE, note="measured and assigned current rates"),
        dict(model="N1 same pace plus trend", total_2027_2031=WI_BASELINE / 5 * float(np.sum(gr_now ** years_ahead)),
             note=f"yearly growth {gr_now:.3f} from the series' latest years"),
        dict(model="N2 pooled level, statewide", total_2027_2031=pooled * WI_HOMES * 5 / 1000,
             note=f"median no-law rate {pooled:.3f} per 1,000 homes per year x {WI_HOMES:,} homes x 5")])
    pd.set_option("display.width", 220)
    p.round(4).to_csv(REFERENCE / f"adu_no_reform_{tag}_series.csv", index=False)
    f.round(4).to_csv(REFERENCE / f"adu_no_reform_{tag}_forward.csv", index=False)
    scores.round(4).to_csv(REFERENCE / f"adu_no_reform_{tag}_scores.csv", index=False)
    wi.round(1).to_csv(REFERENCE / f"adu_no_reform_{tag}_wi.csv", index=False)
    if CLEAN:    # adopted (AQ-065): the engine's current-law baseline rises at this yearly growth from mid-2023
        pd.DataFrame([dict(yearly_growth=round(gr_now, 6), centre_year=2023.5,
                           source="scripts/run_adu_no_reform.py: median yearly growth of no-law series' 3-year mean "
                                  "rates, latest years, no window spanning a local reform (NO_REFORM_R1_RESULTS.md)")]
                     ).to_csv(REFERENCE / "adu_no_reform_trend.csv", index=False)
    print(p.groupby("series").agg(level=("level", "first"), y0=("year", "min"), y1=("year", "max"),
                                  mean_rate=("rate", "mean"), last3=("rate", lambda r: r.tail(3).mean())).round(3))
    print(scores.round(3).to_string(index=False))
    print(ho.round(3).to_string(index=False))
    print("worst B0 forward miss:", worst[["series", "origin", "actual", "B0", "B0_abs_log"]].to_dict())
    print(wi.round(1).to_string(index=False))


if __name__ == "__main__":
    main()

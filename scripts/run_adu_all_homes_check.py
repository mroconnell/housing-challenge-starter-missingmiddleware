"""ADU all-homes cross-check (docs/adu/ALL_HOMES_CHECK_PLAN.md, written before running).

Did all permitted homes rise after a statewide ADU law, against states with no law? Census Building Permits Survey
state annual files; permits per 1,000 existing homes (ACS 2020-2024 B25024 total) per year; outcomes all units and
units in 1-4 unit buildings. Effect = (after - before) minus the comparison states' median change, same years.
Placebo: every comparison state given each law state's dates.

Run: uv run python scripts/run_adu_all_homes_check.py
Outputs: reference/adu_all_homes_check_cases.csv, reference/adu_all_homes_check_summary.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

LAW_YEAR = {"CA": 2020, "OR": 2020, "VT": 2021, "UT": 2022, "ME": 2025, "MA": 2025, "RI": 2025}
FIPS = {"CA": "06", "OR": "41", "VT": "50", "UT": "49", "ME": "23", "MA": "25", "RI": "44", "WI": "55"}
LAST_YEAR = 2025
WI_HOMES = 2_840_960


def permits() -> pd.DataFrame:
    out = []
    for f in sorted((RAW / "census_bps_state").glob("st20[1-2][0-9]a.txt")):
        year = int(f.name[2:6])
        for line in f.read_text(encoding="latin-1").splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) < 18 or not p[0].startswith(str(year)) or not p[1].isdigit():
                continue
            u1, u2, u34, u5 = (float(p[i] or 0) for i in (6, 9, 12, 15))
            out.append(dict(fips=p[1].zfill(2), year=year, all_units=u1 + u2 + u34 + u5, units_1_4=u1 + u2 + u34))
    return pd.DataFrame(out)


def homes() -> pd.Series:
    h = {}
    with open(RAW / "census_acs5_2024_tbsf/acsdt5y2024-b25024.dat", encoding="utf-8") as f:
        f.readline()
        for line in f:
            if line.startswith("0400000US"):
                p = line.split("|", 3)
                h[p[0][9:11]] = float(p[1])
    return pd.Series(h)


def law_fips_by(year_end: int, laws: pd.DataFrame) -> set:
    """States with any statewide ADU law in force by the end of `year_end` (treatment date year <= year_end)."""
    t = pd.to_datetime(laws["treatment_date"].astype(str).str[:10], errors="coerce")
    return set(laws.loc[t.dt.year <= year_end, "abbr"].map(lambda a: STATE_FIPS.get(a)))


STATE_FIPS = {"AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10", "DC": "11",
              "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
              "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30",
              "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
              "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
              "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56"}


def window_change(r: pd.Series, before, after) -> float:
    return float(r.reindex(after).mean() - r.reindex(before).mean())


def main():
    p = permits()
    h = homes()
    p = p[p.fips.isin(h.index) & p.fips.isin(set(STATE_FIPS.values()))].copy()     # 50 states and DC
    laws = pd.read_csv(REFERENCE / "statewide_states_laws.csv")
    rows, plac = [], []
    for outcome in ("all_units", "units_1_4"):
        rate = p.assign(rate=p[outcome] / p.fips.map(h) * 1000).pivot(index="year", columns="fips", values="rate")
        for st, ly in LAW_YEAR.items():
            before = list(range(ly - 3, ly))
            after = [y for y in range(ly, ly + 3) if y <= LAST_YEAR]
            excl = law_fips_by(max(after), laws) | {FIPS[st]}
            comp = [c for c in rate.columns if c not in excl]
            ch = {c: window_change(rate[c], before, after) for c in comp}
            ch = {c: v for c, v in ch.items() if np.isfinite(v)}      # states missing a window year are left out
            med = float(np.median(list(ch.values())))
            own = window_change(rate[FIPS[st]], before, after)
            rows.append(dict(outcome=outcome, state=st, law_year=ly, before=f"{before[0]}-{before[-1]}",
                             after=f"{after[0]}-{after[-1]}", rate_before=float(rate[FIPS[st]].reindex(before).mean()),
                             rate_after=float(rate[FIPS[st]].reindex(after).mean()), change=own,
                             comparison_median_change=med, effect=own - med, n_comparison=len(ch)))
            for c, v in ch.items():
                plac.append(dict(outcome=outcome, case=st, fips=c, effect=v - float(np.median([x for k, x in ch.items() if k != c]))))
    cases = pd.DataFrame(rows)
    pl = pd.DataFrame(plac)
    rng = np.random.default_rng(20261031)
    summ = []
    for outcome, g in cases.groupby("outcome"):
        avg = float(g.effect.mean())
        # placebo: one comparison state per law state's dates, averaged over the 7 cases; 10,000 draws
        pools = [pl[(pl.outcome == outcome) & (pl.case == s)].effect.to_numpy() for s in g.state]
        draws = np.array([np.mean([rng.choice(x) for x in pools]) for _ in range(10_000)])
        summ.append(dict(outcome=outcome, n_states=len(g), average_effect=avg, median_effect=float(g.effect.median()),
                         placebo_p05=float(np.percentile(draws, 5)), placebo_p50=float(np.percentile(draws, 50)),
                         placebo_p95=float(np.percentile(draws, 95)), share_placebo_at_or_above=float((draws >= avg).mean()),
                         wi_homes_2027_2031=avg * WI_HOMES * 5 / 1000))
    s = pd.DataFrame(summ)
    cases.round(4).to_csv(REFERENCE / "adu_all_homes_check_cases.csv", index=False)
    s.round(4).to_csv(REFERENCE / "adu_all_homes_check_summary.csv", index=False)
    pd.set_option("display.width", 220)
    print(cases.round(3).to_string(index=False))
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

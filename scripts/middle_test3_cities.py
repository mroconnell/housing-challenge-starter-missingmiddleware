"""Middle housing Test 3 (supporting only) and its Test 4 fake-year part. Locked plan: docs/middle/TEST_PLAN_LOCKED.md.
Committed before any run.

Cities: Minneapolis, Raleigh, Spokane, Walla Walla, Portland. Statistic: change in rate (after minus before), homes
permitted per 1,000 single-family homes per year (homes moved to each year by one-unit permits, as in Test 1).
Stand-ins: at least 20 cities at 1/2-2x the city's population that never had such a reform, from its own state, then its
Census division, then the nation; never from a state whose law binds by 2025 (OR, CA, WA, ME, VT, MT) or a screened
state, never a candidate city or screened place. Result: the city's percentile among its stand-ins.
Reading: above the 95th percentile = a rise; below the 5th = a fall; otherwise = we do not know.
Data: Census reported-only columns, places reporting 12 months in every window year (main); Spokane uses Census
filled-in columns (flagged) and is checked against Washington OFM permits. Filled-in columns are a sensitivity for all.
Usage: python scripts/middle_test3_cities.py [real|fake]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import middle_test1_states as t1  # noqa: E402
import middle_power_check as pc  # noqa: E402

OUT = t1.OUT
CITIES = {  # key name, state FIPS, BPS name, real windows, fake windows
    "Minneapolis": ("27", "Minneapolis", ((2016, 2017, 2018), tuple(range(2020, 2026))), ((2012, 2013, 2014), (2016, 2017, 2018))),
    "Raleigh": ("37", "Raleigh", ((2018, 2019, 2020), (2022, 2023, 2024, 2025)), ((2012, 2013, 2014), (2016, 2017, 2018))),
    "Spokane": ("53", "Spokane", ((2019, 2020, 2021), (2023, 2024, 2025)), ((2012, 2013, 2014), (2016, 2017, 2018))),
    "Walla Walla": ("53", "Walla Walla", ((2015, 2016, 2017), tuple(range(2019, 2026))), ((2012, 2013, 2014), (2015, 2016, 2017))),
    "Portland": ("41", "Portland", ((2017, 2018, 2019), (2022, 2023, 2024, 2025)), ((2012, 2013, 2014), (2016, 2017, 2018))),
}
NO_STANDIN_STATES = {"41", "06", "53", "23", "50", "30"} | set(pc.SCREENED_STATES)
MEASURES = {k: t1.MEASURES[k] for k in ("M2", "M1", "M3", "M4", "one_unit")}


def run(mode: str) -> None:
    d = t1.load_all(2025 if mode == "real" else 2018)
    homes = pc.sf_homes()
    meta = d.sort_values("year").groupby("key").last()
    info = meta[["state_fips", "region", "name", "pop", "acs_geoid"]].copy()
    info["division"] = meta["division"].astype(str).str.strip()
    info["pop"] = pd.to_numeric(info["pop"], errors="coerce")
    info["screened_place"] = t1.screened_flags(info)
    rows = []
    for city, (st, bname, real_w, fake_w) in CITIES.items():
        win = real_w if mode == "real" else fake_w
        ck = info.index[(info["state_fips"] == st) & (info["name"] == bname)]
        if len(ck) == 0:
            rows.append(dict(mode=mode, city=city, note="not found"))
            continue
        ck = ck[0]
        pop, div = info.at[ck, "pop"], info.at[ck, "division"]
        for data, rep in (("main", city != "Spokane"), ("filled-in (sensitivity)", False)):
            if city == "Spokane" and data == "main":
                label = "main (filled-in, flagged)"
            else:
                label = data
            for m, cols in MEASURES.items():
                pw = t1.place_windows(d, homes, win, cols, rep)
                pw = pw[pw.index.isin(info.index)]
                ch = 1000 * (pw["p_a"] / pw["h_a"] - pw["p_b"] / pw["h_b"])
                if ck not in ch.index:
                    rows.append(dict(mode=mode, city=city, data=label, measure=m, note="city fails data rule"))
                    continue
                elig = info.loc[pw.index]
                ok = (~elig["state_fips"].isin(NO_STANDIN_STATES) & ~elig["screened_place"]
                      & elig["pop"].between(pop / 2, pop * 2)).to_numpy()
                pool = ch[ok]
                scope = "nation"
                for sc, mask in (("state", elig.loc[pool.index, "state_fips"] == st),
                                 ("division", elig.loc[pool.index, "division"] == div)):
                    if mask.sum() >= 20:
                        pool, scope = pool[mask.to_numpy()], sc
                        break
                real = ch[ck]
                pct = float((pool < real).mean() * 100)
                reading = ("rise" if pct > 95 else "fall" if pct < 5 else "we do not know")
                rows.append(dict(mode=mode, city=city, data=label, measure=m, change_per_1000=real,
                                 standins=len(pool), scope=scope, standin_median=pool.median(),
                                 standin_p05=pool.quantile(0.05), standin_p95=pool.quantile(0.95),
                                 relative_to_median=real - pool.median(), percentile=pct, reading=reading))
    r = pd.DataFrame(rows)
    tag = "" if mode == "real" else "_fakeyears"
    r.to_csv(OUT / f"middle_test3_cities{tag}.csv", index=False)
    pd.set_option("display.width", 220)
    print(r.round(2).to_string(index=False))


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "real")

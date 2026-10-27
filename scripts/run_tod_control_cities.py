"""Compare each TOD reform city's whole-city permits with matched cities that made no such reform.

    uv run --all-extras python scripts/fetch_tod_control_cities.py   # Census permits 2000-2025, 2010 home counts
    uv run --all-extras python scripts/run_tod_control_cities.py

Plan: docs/tod/CONTROL_CITIES_PLAN.md (written before running). Results: docs/tod/CONTROL_CITIES_RESULTS.md.
Writes (committed, aggregate public data only):
    reference/tod_control_cities_results.csv   one row per test, method and check
    reference/tod_control_cities_pooled.csv    six cities averaged, with the decision rules
    reference/tod_control_cities_controls.csv  the matched cities and blend weights behind each main estimate
    reference/tod_control_cities_rates.csv     yearly rate, reform city against its ten matched cities
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import control_cities as cc  # noqa: E402

D = RAW / "tod_control_cities"
SCENARIOS = {"little": 0.055, "typical": 0.8, "strong": 5.469}   # % of station-area homes over five years (AQ-050)
CHECKS = {  # name -> (method, k, outcome column, same_metro, fake date)
    "main": ("matched", 10, "units", False, False),
    "blend": ("synth", 10, "units", False, False),
    "k5": ("matched", 5, "units", False, False),
    "k20": ("matched", 20, "units", False, False),
    "five_plus_only": ("matched", 10, "units5", False, False),
    "same_metro_allowed": ("matched", 10, "units", True, False),
    "fake_date": ("matched", 10, "units", False, True),
}


def windows(rf: cc.Reform, fake: bool):
    if not fake:
        return rf.before, rf.after
    y = rf.year - 4
    return (y - 6, y - 1), (y + 1, rf.year - 1)


def joint_draws(rfs, noise, rng) -> np.ndarray:
    """One fake effect per draw for a city; a city with two tests uses the same fake city in both (they share a pool)."""
    if len(rfs) == 1:
        return rng.choice(noise[rfs[0].test][1].to_numpy(), cc.DRAWS)
    common = sorted(set.intersection(*(set(noise[r.test][1].index) for r in rfs)))
    pick = rng.choice(common, cc.DRAWS)
    return np.mean([noise[r.test][1].reindex(pick).to_numpy() for r in rfs], axis=0)


def main() -> None:
    bps = cc.read_bps(D / "bps")
    gaz = cc.read_gazetteer(D / "Gaz_places_national.zip")
    panel, places = cc.link(bps, gaz, cc.read_county_hu(D / "Gaz_counties_national.zip"))
    inv = cc.inventory_geoids(pd.read_csv(REFERENCE / "tod_cases.csv"), gaz)
    net = pd.read_csv(REFERENCE / "tod_net_effect_by_case.csv").set_index("case")
    P = places.set_index("geoid")
    rates = {c: cc.rates(panel, places, c) for c in ("units", "units5")}

    rows, ctl_rows, rate_rows, noise = [], [], [], {}
    for rf in cc.REFORMS:
        city_hu, office_hu = float(P.loc[rf.geoid, "hu10"]), float(P.loc[rf.geoid, "office_hu10"])
        conv = lambda e: cc.to_5yr_share(e, office_hu, city_hu)  # noqa: E731
        nrow = net.loc[rf.net_case]
        own_5yr = 100 * nrow["net_5yr_homes"] / city_hu
        for check, (method, k, col, same_metro, fake) in CHECKS.items():
            before, after = windows(rf, fake)
            R = rates[col]
            pool = cc.eligible(rf, R, places, inv, same_metro=same_metro, before=before, after=after)
            ids = list(pool.index)
            est = cc.estimate(R, rf.geoid, ids, before, after, method, k)
            pl = cc.placebos(R, ids, places, before, after, method, k, same_metro=same_metro)
            lo, hi = est - pl.quantile(0.95), est - pl.quantile(0.05)
            half = (pl.quantile(0.95) - pl.quantile(0.05)) / 2
            share, share_lo, share_hi = conv(est), conv(lo), conv(hi)
            per_home = 100 * share / 100 * city_hu / nrow["treated_area_homes_before"]
            rank = float((pl.abs() >= abs(est)).mean())
            rows.append({
                "test": rf.test, "city": rf.city, "check": check, "method": method, "k": k if method == "matched" else None,
                "outcome": "all homes" if col == "units" else "homes in buildings of 5 or more",
                "before_years": f"{before[0]}-{before[1]}", "after_years": f"{after[0]}-{after[1]}",
                "eligible_places": len(ids), "pool_homes_min": int(pool["hu10"].min()), "pool_homes_max": int(pool["hu10"].max()),
                "city_homes_2010": int(city_hu), "permit_office_homes_2010": int(office_hu),
                "reform_city_rate_before": R.loc[rf.geoid, cc.years(before)].mean(),
                "reform_city_rate_after": R.loc[rf.geoid, cc.years(after)].mean(),
                "effect_per_1000_homes_per_year": est, "effect_low": lo, "effect_high": hi,
                "fake_reform_noise_half_width": half, "share_of_fake_reforms_as_large": rank,
                "city_share_5yr_pct": share, "city_share_5yr_low_pct": share_lo, "city_share_5yr_high_pct": share_hi,
                "smallest_detectable_5yr_pct": conv(half),
                "extra_homes_5yr": share / 100 * city_hu,
                "own_net_case": rf.net_case, "own_net_5yr_homes": nrow["net_5yr_homes"], "own_net_5yr_share_pct": own_5yr,
                "own_net_inside_interval": bool(share_lo <= own_5yr <= share_hi),
                "treated_area_homes_before": nrow["treated_area_homes_before"],
                "per_upzoned_home_5yr_pct": per_home,
                "per_upzoned_home_5yr_low_pct": 100 * share_lo / 100 * city_hu / nrow["treated_area_homes_before"],
                "per_upzoned_home_5yr_high_pct": 100 * share_hi / 100 * city_hu / nrow["treated_area_homes_before"],
            })
            if check == "main":
                noise[rf.test] = (est, pl.map(conv), city_hu)
                ctl = cc.nearest(R, rf.geoid, ids, before, k)
                for g in ctl:
                    ctl_rows.append({"test": rf.test, "method": "ten matched cities", "place": P.loc[g, "place_name"],
                                     "state": P.loc[g, "state"], "homes_2010": int(P.loc[g, "hu10"]), "weight": 1 / k})
                for y in range(before[0], after[1] + 1):
                    rate_rows.append({"test": rf.test, "year": y, "reform_city_rate": R.loc[rf.geoid, y],
                                      "matched_cities_mean_rate": R.loc[ctl, y].mean()})
            if check == "blend":
                _, w = cc.synth(R, rf.geoid, ids, before, after)
                for g, wt in sorted(w.items(), key=lambda t: -t[1]):
                    if wt >= 0.005:
                        ctl_rows.append({"test": rf.test, "method": "weighted blend", "place": P.loc[g, "place_name"],
                                         "state": P.loc[g, "state"], "homes_2010": int(P.loc[g, "hu10"]), "weight": wt})
        print(f"{rf.test}: done")

    res = pd.DataFrame(rows)

    # Six cities averaged (Seattle's two tests first), main check only (plan section 6).
    rng = np.random.default_rng(cc.SEED)
    cities = {}
    for rf in cc.REFORMS:
        cities.setdefault(rf.pooled_city, []).append(rf)
    est_city, home_city, draws_share, draws_home = {}, {}, [], []
    for city, rfs in cities.items():
        nrow = net.loc[cc.POOLED_NET_CASE.get(city, rfs[0].net_case)]
        city_hu = noise[rfs[0].test][2]
        e = np.mean([res[(res.test == r.test) & (res.check == "main")]["city_share_5yr_pct"].iloc[0] for r in rfs])
        est_city[city] = e
        scale = city_hu / nrow["treated_area_homes_before"]
        home_city[city] = e * scale
        d = joint_draws(rfs, noise, rng)
        draws_share.append(d)
        draws_home.append(d * scale)
    pooled_share = float(np.mean(list(est_city.values())))
    pooled_home = float(np.mean(list(home_city.values())))
    ds, dh = np.mean(draws_share, axis=0), np.mean(draws_home, axis=0)
    p_lo, p_hi = pooled_share - np.quantile(ds, 0.95), pooled_share - np.quantile(ds, 0.05)
    h_lo, h_hi = pooled_home - np.quantile(dh, 0.95), pooled_home - np.quantile(dh, 0.05)
    width = h_hi - h_lo
    narrow_enough = width < SCENARIOS["strong"] - SCENARIOS["little"]
    # Scenarios "left out" only mean something once the interval is narrow enough (plan section 7, rule 2).
    excluded = [k for k, v in SCENARIOS.items() if not (h_lo <= v <= h_hi)] if narrow_enough else []
    agree = {}
    for city, rfs in cities.items():
        sub = res[(res.check == "main") & res.test.isin([r.test for r in rfs])]
        if len(rfs) == 1:
            agree[city] = bool(sub["own_net_inside_interval"].iloc[0])
        else:  # Seattle: city estimate and interval from both tests averaged against the city's own net
            nrow = net.loc[cc.POOLED_NET_CASE[city]]
            own = 100 * nrow["net_5yr_homes"] / noise[rfs[0].test][2]
            d = joint_draws(rfs, noise, rng)
            agree[city] = bool(est_city[city] - np.quantile(d, 0.95) <= own <= est_city[city] - np.quantile(d, 0.05))
    pooled = pd.DataFrame([{
        "cities": len(cities), "city_share_5yr_pct": pooled_share, "city_share_5yr_low_pct": p_lo, "city_share_5yr_high_pct": p_hi,
        "per_upzoned_home_5yr_pct": pooled_home, "per_upzoned_home_5yr_low_pct": h_lo, "per_upzoned_home_5yr_high_pct": h_hi,
        "interval_width_points": width, "scenario_gap_points": SCENARIOS["strong"] - SCENARIOS["little"],
        "scenarios_left_out_of_interval": ";".join(excluded) if narrow_enough else "not judged (interval too wide)",
        "rule2_narrowing_passes": bool(narrow_enough and excluded),
        "cities_agreeing": sum(agree.values()), "agreeing_list": ";".join(c for c, v in agree.items() if v),
        "rule1_agreement_passes": sum(agree.values()) >= 4,
        "seed": cc.SEED, "draws": cc.DRAWS,
    }])

    res.round(5).to_csv(REFERENCE / "tod_control_cities_results.csv", index=False)
    pooled.round(5).to_csv(REFERENCE / "tod_control_cities_pooled.csv", index=False)
    pd.DataFrame(ctl_rows).round(5).to_csv(REFERENCE / "tod_control_cities_controls.csv", index=False)
    pd.DataFrame(rate_rows).round(4).to_csv(REFERENCE / "tod_control_cities_rates.csv", index=False)
    print(res[res.check == "main"][["test", "eligible_places", "effect_per_1000_homes_per_year", "city_share_5yr_pct",
                                    "city_share_5yr_low_pct", "city_share_5yr_high_pct", "own_net_5yr_share_pct",
                                    "own_net_inside_interval", "smallest_detectable_5yr_pct"]].round(3).to_string())
    print(pooled.T.to_string())


if __name__ == "__main__":
    main()

"""Parking causal framework, moderators M1-M4 (held-out 5-fold) and ramp R (effect by year since repeal).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md (locked 2026-11-03; M and R details logged before counting).

    uv run python scripts/run_parking_causal_mr.py
Outputs: reference/parking_causal_moderators.csv, reference/parking_causal_ramp.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, DRAWS, FOLDS = 20261103, 2000, 5


def wmedian(v, w):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return v[o][np.searchsorted(c, c[-1] / 2)]


def heldout_contrast(d: pd.DataFrame, col: str, weighted_split: bool = True) -> dict:
    d = d.dropna(subset=[col]).reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    fold = rng.permutation(np.arange(len(d)) % FOLDS)
    hi = np.zeros(len(d), bool)
    for f in range(FOLDS):
        tr = fold != f
        cut = wmedian(d.loc[tr, col].values, d.loc[tr, "weight"].values if weighted_split else np.ones(int(tr.sum())))
        hi[fold == f] = d.loc[fold == f, col].values > cut
    v, w = d["effect"].values, d["weight"].values
    f = lambda m: np.sum(v[m] * w[m]) / np.sum(w[m])  # noqa: E731
    est = f(hi) - f(~hi)
    ih, il = np.where(hi)[0], np.where(~hi)[0]
    bs = np.array([f(rng.choice(ih, len(ih))) - f(rng.choice(il, len(il))) for _ in range(DRAWS)]) if len(ih) and len(il) else np.array([np.nan])
    X = np.column_stack([np.ones(len(d)), d[col].values])
    W = np.sqrt(w)
    slope = np.linalg.lstsq(X * W[:, None], v * W, rcond=None)[0][1]
    lo, up = np.percentile(bs, [5, 95])
    return dict(places=len(d), high=int(hi.sum()), low=int((~hi).sum()), mean_high=f(hi), mean_low=f(~hi), estimate=est,
                p05=lo, p95=up, mde=1.645 * bs.std(ddof=1), full_sample_slope=slope,
                reading="material" if (lo > 0 or up < 0) else "not material (interval includes 0)")


def main() -> None:
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    om = pd.read_csv(REFERENCE / "parking_old_minimums.csv").drop_duplicates("prn_key")
    real = real.merge(om[["prn_key", "old_min_apartment"]], on="prn_key", how="left")
    real["log_homes"] = np.log(real["homes"])
    rows = []
    for m, col, unit in (("M1 old minimum (spaces per apartment)", "old_min_apartment", "high minus low old minimum"),
                         ("M3 city size (log existing homes)", "log_homes", "large minus small cities")):
        r = heldout_contrast(real, col)
        rows.append(dict(moderator=m, contrast=unit, unit="permits per 1,000 existing homes a year", **r))
    # POST HOC (2026-11-03, after the first count; owner allowed plan changes): the home-weighted split put 6 places
    # in "large"; an unweighted median split is shown beside it.
    r = heldout_contrast(real, "log_homes", weighted_split=False)
    rows.append(dict(moderator="M3 city size, POST HOC unweighted median split", contrast="large minus small cities",
                     unit="permits per 1,000 existing homes a year", **r))
    te = pd.read_csv(REFERENCE / "parking_causal_t_e2_summary.csv")
    for m, key in (("M2 repeal alone vs inside a rewrite (= E2)", "E2 repeal alone"), ("M4 good transit, rail or BRT (= T)", "T good transit")):
        t = te[te["test"].str.startswith(key)].iloc[0]
        rows.append(dict(moderator=m, contrast=t["test"], unit=t["unit"], places=int(t["n_a"] + t["n_b"]), estimate=t["estimate"],
                         p05=t["p05"], p95=t["p95"], mde=t["mde"],
                         reading="material" if (t["p05"] > 0 or t["p95"] < 0) else "not material (interval includes 0)"))
    M = pd.DataFrame(rows)
    M["note"] = "four moderators tested, so one false 'material' in four is plausible"
    M.to_csv(REFERENCE / "parking_causal_moderators.csv", index=False)

    # R: ramp by year since repeal
    p = cmp.panel(rpc.read_bps_us())
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    excluded |= set(real["key"])
    ev = []
    for r in real.itertuples():
        e = int(r.event_year)
        pre, _ = cmp.windows(e)
        ctrl, _ = cmp.controls(p, r.key, e, excluded - {r.key}, homes, popn)
        b_t, b_c = cmp._rate(p, [r.key], pre, "units_total", homes), cmp._rate(p, ctrl, pre, "units_total", homes)
        for k in range(1, 6):
            y = e + k
            if y > cmp.LAST_YEAR:
                break
            eff = (cmp._rate(p, [r.key], [y], "units_total", homes) - b_t) - (cmp._rate(p, ctrl, [y], "units_total", homes) - b_c)
            ev.append(dict(key=r.key, place=r.place, k=k, effect=eff, weight=r.weight))
    E = pd.DataFrame(ev).dropna(subset=["effect"])
    R = E.groupby("k").apply(lambda d: pd.Series(dict(places=len(d), effect=np.average(d["effect"], weights=d["weight"]),
                             median=d["effect"].median(), share_positive=(d["effect"] > 0).mean())), include_groups=False).reset_index()
    # same places at every k up to 3 (balanced), to separate ramp from changing membership
    bal = E[E["key"].isin(E[E["k"] == 3]["key"])]
    R["effect_places_with_k3"] = R["k"].map(bal.groupby("k").apply(lambda d: np.average(d["effect"], weights=d["weight"]), include_groups=False))
    R.to_csv(REFERENCE / "parking_causal_ramp.csv", index=False)
    pd.set_option("display.width", 250)
    print(M.drop(columns="note").round(3).to_string(index=False))
    print(R.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

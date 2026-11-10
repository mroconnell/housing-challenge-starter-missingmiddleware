"""Exploratory first-year check (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, "Exploratory: first-year check (after results)").
Done after the results; not locked; it changes no line.

Question: is there a slow start in the first law year at TOD's 11 D-11 reform places, and is it consistent with the
current ramp (New York pooled set: yearly shares 9.8% / 9.3% / 26.4% / 47.9% / 6.6% for 2027-2031)?

Each place's 1/4-mile effect is the central's (run_tod_causal_central_pretrend.quarter_effect: reform stops minus
comparison stops, each against its before-window level, extra new homes per 100 lot acres a year, implausible lots out;
New York and Philadelphia averaged over their rezonings), computed with the after window cut to one year at a time.
The before window is the full real one. Events and permit-year estimates as the central (run_tod_causal_predict.
event_years, filtered as run_tod_station_model.event_windows); after-window hand-check corrections
(run_tod_station_model.event_windows) are spread over the after years in proportion to each lot's raw homes per year
(equal split if the lot has no raw after homes). So the mean of the five yearly effects is exactly the central's
per-place effect (sanity: plain average over 11 places = 33.5373).

Year 1 = first after-window year = reform year + 1 (the reform year is in neither window, as in the central; the ramp's
year 1 is also event year 1). Later years = years 2-5 (every place has a five-year after window).
Ratio = year-1 effect / later-years mean, per place; left out of the ratio when the later-years mean is below 10% of the
central (3.35 per 100 acres a year) - near zero or negative. Pooled: mean of year-1 effects / mean of later-years
effects (all 11 places), and median of place ratios (kept places only). Bootstrap: 2,000 place draws, seed 20261103.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_first_year_check.py

Writes reference/tod_first_year_check.csv (summaries only: no lot rows, no parcel ids).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
from missing_middleware.tod import model as TM  # noqa: E402

import run_tod_causal_central_pretrend as CP  # noqa: E402
import run_tod_causal_predict as P  # noqa: E402
import run_tod_model as R  # noqa: E402
import run_tod_station_model as M  # noqa: E402

OUT = CP.OUT
NEAR_ZERO = 0.10 * CP.SANITY_MEAN          # later-years mean below this -> out of the ratio


def yearly_effects(case: str) -> dict[int, float]:
    """Effect with the after window cut to each single year k = 1..ya (before window unchanged)."""
    D0 = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=CP.LOT_COLS + ["homes_before_win", "homes_after_win"])
    D = M.event_windows(case, D0, "permit_est", OUT)            # full windows, hand checks applied
    yb, ya = M.windows(case)
    a0, a1 = P.cfg(case)["after"]
    E = P.event_years(case, OUT)
    E = E[E.lot_index.isin(D.index)]
    raw = {y: E[E.yr == y].groupby("lot_index").homes.sum().reindex(D.index).fillna(0) for y in range(a0, a1 + 1)}
    raw_after = sum(raw.values())
    full_after = D.homes_after_win
    out = {}
    for k, y in enumerate(range(a0, a1 + 1), start=1):
        # each lot's corrected after total spread by its raw homes per year; equal split if no raw after homes
        share = np.where(raw_after > 0, raw[y] / raw_after.where(raw_after > 0, 1), 1 / ya)
        Dk = D.assign(homes_after_win=full_after * share)
        out[k] = CP.quarter_effect(Dk, yb, 1)
    return out


def build() -> pd.DataFrame:
    rows = []
    for f in sorted(OUT.glob("lots_*.parquet")):
        case = f.stem.removeprefix("lots_")
        place = CP.place_of(case)
        if not place:
            continue
        a0, a1 = P.cfg(case)["after"]
        for k, v in yearly_effects(case).items():
            rows.append({"place": place, "case": case, "year": k, "calendar_year": a0 + k - 1, "effect": v,
                         "full": CP.real_effect(case)})
    return pd.DataFrame(rows)


def main() -> None:
    C = build()
    C = C.dropna(subset=["full"])
    # sanity: the mean of each case's yearly effects reproduces its full-window effect, and 11 places average 33.5373
    chk = C.groupby("case").agg(m=("effect", "mean"), f=("full", "first"))
    assert np.allclose(chk.m, chk.f, atol=1e-9), (chk.m - chk.f).abs().max()
    Y = C.groupby(["place", "year"]).effect.mean().unstack()           # place x year (rezonings averaged)
    full = Y.mean(axis=1)
    assert len(full) == 11 and round(full.mean(), 4) == CP.SANITY_MEAN, full.mean()
    assert Y.shape[1] == 5 and Y.notna().all().all()

    first, later = Y[1], Y[[2, 3, 4, 5]].mean(axis=1)
    keep = later >= NEAR_ZERO
    ratio = (first / later).where(keep)
    places = sorted(Y.index)
    picks = CP.draw_places(places)
    b_first, b_later = CP.boot_means(first, picks), CP.boot_means(later, picks)
    b_ratio_means = b_first / b_later
    kept = sorted(ratio.dropna().index)
    picks_k = CP.draw_places(kept)
    b_med = np.array([np.median(ratio.loc[list(p)].values) for p in picks_k])

    # current ramp (New York pooled set), read from the tool's own code path
    shares = np.array(TM.timing_from_ramp(R.case_params()["ramp"]))
    ramp_ratio = shares[0] / shares[1:].mean()

    rows = []
    cal = C.groupby("place").calendar_year.agg(["min", "max"])
    ncase = C.groupby("place").case.nunique()
    for p in places:
        rows.append({"section": "per place", "name": CP.display(p), "first_year": first[p], "later_years_mean": later[p],
                     "ratio": ratio[p], "full_window": full[p],
                     **{f"year{k}": Y.loc[p, k] for k in range(1, 6)},
                     "rezonings": int(ncase[p]),
                     "note": (f"after years {cal.loc[p, 'min']}-{cal.loc[p, 'max']}" if ncase[p] == 1 else
                              f"after years from {cal.loc[p, 'min']} to {cal.loc[p, 'max']} across rezonings")
                             + ("" if keep[p] else f"; later-years mean below {NEAR_ZERO:.2f}: left out of the ratio")})
    lo, hi = CP.ci(b_ratio_means)
    rows.append({"section": "pooled", "name": "mean of first-year effects / mean of later-years effects (11 places)",
                 "first_year": first.mean(), "later_years_mean": later.mean(), "ratio": first.mean() / later.mean(),
                 "lo90": lo, "hi90": hi, "note": "90% interval: place bootstrap of the ratio of means"})
    lo, hi = CP.ci(b_med)
    rows.append({"section": "pooled", "name": f"median of place ratios ({len(kept)} places)",
                 "ratio": float(np.median(ratio.dropna())), "lo90": lo, "hi90": hi,
                 "note": "90% interval: place bootstrap of the median; left out: "
                         + (", ".join(CP.display(p) for p in places if not keep[p]) or "none")})
    for k in range(1, 6):
        lo, hi = CP.ci(CP.boot_means(Y[k], picks))
        rows.append({"section": "by year (place-equal weight)", "name": f"year {k} after reform", "value": Y[k].mean(),
                     "lo90": lo, "hi90": hi, "share_of_five_years": Y[k].mean() / Y.mean().sum(),
                     "ramp_share": shares[k - 1], "places": 11})
    rows.append({"section": "ramp", "name": "current ramp: year 1 share / mean of years 2-5 shares",
                 "ratio": ramp_ratio, "note": "New York pooled set, run_tod_model.case_params -> "
                 "missing_middleware/tod/model.py ramp_from_gaps / timing_from_ramp; shares "
                 + " / ".join(f"{s:.1%}" for s in shares) + " for 2027-2031"})
    # supplementary (not in the brief): first two years against years 3-5, data and ramp
    e12, e35 = Y[[1, 2]].mean(axis=1), Y[[3, 4, 5]].mean(axis=1)
    lo, hi = CP.ci(CP.boot_means(e12, picks) / CP.boot_means(e35, picks))
    rows.append({"section": "supplementary", "name": "mean of years 1-2 effects / mean of years 3-5 effects (11 places)",
                 "first_year": e12.mean(), "later_years_mean": e35.mean(), "ratio": e12.mean() / e35.mean(),
                 "lo90": lo, "hi90": hi, "note": f"current ramp, same split: {shares[:2].mean() / shares[2:].mean():.3f}"})
    notes = [
        "exploratory, after the results; not locked; changes no line",
        "units: extra new homes per 100 lot acres a year within 1/4 mile, reform stops minus comparison stops, each "
        "against its before-window level (the central's effect); year k = after window cut to that one year",
        "year 1 = reform year + 1 (reform year is in neither window, as in the central and the ramp's event year 1)",
        "after-window hand-check corrections spread over the after years by each lot's raw homes per year",
        f"near zero: later-years mean below 10% of the central ({NEAR_ZERO:.2f})",
        "bootstrap: 2,000 place draws, seed 20261103",
        "sanity: mean of the 5 yearly effects = each place's central effect; plain average over 11 places = 33.5373",
    ]
    rows += [{"section": "note", "note": n} for n in notes]
    O = pd.DataFrame(rows)
    O.round(4).to_csv(REFERENCE / "tod_first_year_check.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 120)
    print(O.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

"""Test C-PT (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, "Test C-PT: pre-trend check on the central", locked 2026-11-03
before any count).

Each D-11 place's 1/4-mile effect is recomputed exactly as for the central (option D: run_tod_station_model.case_effects
("permit_est"), all reform and comparison lots in the band, implausible lots out, per 100 lot acres a year, New York and
Philadelphia averaged over their rezonings; plain average over places = 33.54 -> 10,028) with a fake reform: the before
window is split in half as in T2b-PT and Test P (h = years // 2; first h years "before", last h years "after"; an odd
middle year is left out; before-window hand-check corrections split between the halves in proportion to raw homes,
duplicates 0; run_tod_causal_predict.placebo_windows). The real after window is never read in the fake run: the lot
table is read without its window-total columns and the events are cut to the before window.

Versions:
  real, D-11 (11 places)   sanity: plain average must be 33.5373
  real, same places        the real effects on the places (and rezonings) the fake run has
  fake, same places        the fake reform
Pass rule: the fake average's 90% interval (place bootstrap, 2,000 draws) includes 0. If it fails: trend-adjusted
central = real average - fake average (same places), Wisconsin figure, leave-one-place-out range, paired-bootstrap
interval; the upper (central scaled to a 15% district) gets the same adjustment.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_central_pretrend.py

Writes reference/tod_causal_central_pretrend.csv (summaries only: no lot rows, no parcel ids).
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

import run_tod_causal_predict as P  # noqa: E402
import run_tod_station_model as M  # noqa: E402
from run_tod_optiond import TRAIN  # noqa: E402

OUT = P.OUT
BAND = "0-1/4"
SEED, DRAWS = 20261103, 2000
WI_FACTOR = 4874.1 / 100 * 5 * 1.2269          # 298.97 Wisconsin homes per unit (33.54 x this = 10,028)
UPPER_RATIO = 12521 / 10028                    # upper = central scaled to a 15% district (owner 11:52)
SANITY_MEAN = 33.5373
LOT_COLS = ["group", "band", "homes_existing", "in_reform_area", "implausible", "acres_land"]   # no window totals


def place_of(case: str) -> str | None:
    c = M.city_of(case)
    return c if c in TRAIN else None


def display(place: str) -> str:
    return P._disp(place) if place not in ("New York", "Philadelphia") else place


# ----------------------------------------------------------------------------------------------------------------------
# the central's 1/4-mile effect (formula of run_tod_station_model.case_effects, one band)
# ----------------------------------------------------------------------------------------------------------------------
def quarter_effect(D: pd.DataFrame, yb: int, ya: int) -> float:
    D = D[~D.implausible.fillna(False)]
    D = D[D.band == BAND]
    g = D.groupby("group").agg(e=("homes_existing", "sum"), b=("homes_before_win", "sum"),
                               a=("homes_after_win", "sum"), ac=("acres_land", "sum"))
    if "reform" not in g.index or "comparison" not in g.index:
        return np.nan
    r, c = g.loc["reform"], g.loc["comparison"]
    if r.e <= 0 or c.e <= 0:
        return np.nan
    pr = 100 * (r.a / ya - r.b / yb) / r.ac if r.ac > 0 else np.nan
    pc = 100 * (c.a / ya - c.b / yb) / c.ac if c.ac > 0 else np.nan
    return pr - pc


def real_effect(case: str, src: Path = OUT) -> float:
    D = pd.read_parquet(src / f"lots_{case}.parquet", columns=LOT_COLS + ["homes_before_win", "homes_after_win"])
    if (src / f"events_{case}.parquet").exists():
        D = M.event_windows(case, D, "permit_est", src)
    yb, ya = M.windows(case)
    return quarter_effect(D, yb, ya)


def fake_effect(case: str, src: Path = OUT) -> tuple[float, int]:
    """Fake reform on halves of the before window. Never reads the real after window: the lot table is read without its
    window totals, and placebo_windows uses before-window events and hand checks only. (nan, 0) if it cannot be split."""
    if not (src / f"events_{case}.parquet").exists():
        return np.nan, 0
    D0 = pd.read_parquet(src / f"lots_{case}.parquet", columns=LOT_COLS)
    D, h = P.placebo_windows(case, D0, src)
    if h == 0:
        return np.nan, 0
    return quarter_effect(D, h, h), h


# ----------------------------------------------------------------------------------------------------------------------
def draw_places(places: list[str], seed: int = SEED, draws: int = DRAWS) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    arr = np.array(places, dtype=object)
    return [rng.choice(arr, len(arr), replace=True) for _ in range(draws)]


def boot_means(v: pd.Series, picks: list[np.ndarray]) -> np.ndarray:
    return np.array([v.loc[list(p)].mean() for p in picks])


def ci(x: np.ndarray) -> tuple[float, float]:
    return float(np.quantile(x, .05)), float(np.quantile(x, .95))


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for f in sorted(OUT.glob("lots_*.parquet")):
        case = f.stem.removeprefix("lots_")
        place = place_of(case)
        if not place:
            continue
        b0, b1 = P.cfg(case)["before"]
        fe, h = fake_effect(case)
        rows.append({"place": place, "case": case, "real": real_effect(case), "fake": fe, "h": h,
                     "before_window": f"{b0}-{b1}"})
    C = pd.DataFrame(rows)
    stored = M.case_effects("permit_est")
    stored = stored[(stored.band == BAND) & stored.city.isin(TRAIN)].set_index("case").effect_per_100_acres
    return C, stored


def main() -> None:
    C, stored = build()
    # sanity 1: the formula here reproduces case_effects per case; sanity 2: plain average over 11 places = 33.5373
    chk = C.set_index("case").real.dropna()
    assert set(chk.index) == set(stored.index), (set(chk.index) ^ set(stored.index))
    assert np.allclose(chk.sort_index().values, stored.sort_index().values, atol=1e-9)
    real_all = C.dropna(subset=["real"]).groupby("place").real.mean()
    assert len(real_all) == 11 and round(real_all.mean(), 4) == SANITY_MEAN, real_all.mean()

    ok = C.dropna(subset=["real", "fake"])
    real_same = ok.groupby("place").real.mean()            # same places and same rezonings as the fake run
    fake = ok.groupby("place").fake.mean()
    places = sorted(fake.index)
    left_out = sorted(set(real_all.index) - set(places))
    dropped_cases = C[C.place.isin(places) & C.fake.isna() & C.real.notna()]

    picks = draw_places(places)
    B = {"real, D-11 (11 places)": boot_means(real_all, draw_places(sorted(real_all.index))),
         "real, same places": boot_means(real_same, picks), "fake, same places": boot_means(fake, picks)}
    est = {"real, D-11 (11 places)": real_all.mean(), "real, same places": real_same.mean(),
           "fake, same places": fake.mean()}

    rows = []
    for p in sorted(real_all.index):
        n_cases = int((C.place == p).sum())
        n_fake = int(((C.place == p) & C.fake.notna() & C.real.notna()).sum())
        hs = sorted(set(C.loc[(C.place == p) & (C.h > 0), "h"].astype(int)))
        rows.append({"version": "per place", "row": "place", "name": display(p), "real": real_all[p],
                     "real_same_cases": real_same.get(p, np.nan), "fake": fake.get(p, np.nan),
                     "cases": n_cases, "cases_in_fake": n_fake, "half_years": "/".join(map(str, hs)),
                     "note": "left out (cannot split)" if p in left_out else ""})
    for v, e in est.items():
        lo, hi = ci(B[v])
        n = 11 if v.startswith("real, D-11") else len(places)
        rows.append({"version": v, "row": "average", "name": "plain average", "value": e, "lo90": lo, "hi90": hi,
                     "wisconsin": e * WI_FACTOR, "wisconsin_lo90": lo * WI_FACTOR, "wisconsin_hi90": hi * WI_FACTOR,
                     "places": n})
    lo, hi = ci(B["fake, same places"])
    passed = lo <= 0 <= hi
    rows.append({"version": "fake, same places", "row": "pass_rule", "name": "fake average 90% interval includes 0",
                 "value": est["fake, same places"], "lo90": lo, "hi90": hi,
                 "note": "PASS" if passed else "FAIL"})

    # trend-adjusted central and upper (reported whatever the verdict; the plan uses them only if the check fails)
    adj = est["real, same places"] - est["fake, same places"]
    plo, phi = ci(B["real, same places"] - B["fake, same places"])      # paired: same place picks
    loo = {p: real_same.drop(p).mean() - fake.drop(p).mean() for p in places}
    lo_p, hi_p = min(loo, key=loo.get), max(loo, key=loo.get)
    for name, k in (("central", 1.0), ("upper (central scaled to a 15% district)", UPPER_RATIO)):
        rows.append({"version": "trend-adjusted", "row": name.split()[0], "name": f"{name}: real - fake (same places)",
                     "value": adj, "lo90": plo, "hi90": phi, "wisconsin": adj * WI_FACTOR * k,
                     "wisconsin_lo90": plo * WI_FACTOR * k, "wisconsin_hi90": phi * WI_FACTOR * k,
                     "loo_low": loo[lo_p], "loo_high": loo[hi_p], "wisconsin_loo_low": loo[lo_p] * WI_FACTOR * k,
                     "wisconsin_loo_high": loo[hi_p] * WI_FACTOR * k, "places": len(places),
                     "note": f"leave-one-place-out low without {display(lo_p)}, high without {display(hi_p)}; "
                             + "; ".join(f"without {display(p)} {v:.2f}" for p, v in loo.items())
                             + f"; interval: paired place bootstrap, seed {SEED}; upper ratio 12,521 / 10,028 = {UPPER_RATIO:.4f}"})
    rows.append({"version": "current", "row": "central", "name": "D-11 central (11 places)", "value": real_all.mean(),
                 "wisconsin": real_all.mean() * WI_FACTOR})
    rows.append({"version": "current", "row": "upper", "name": "central scaled to a 15% district",
                 "value": real_all.mean() * UPPER_RATIO, "wisconsin": real_all.mean() * WI_FACTOR * UPPER_RATIO})
    notes = [f"places left out (cannot split the before window): {', '.join(display(p) for p in left_out) or 'none'}"]
    if len(dropped_cases):
        notes.append(f"rezonings left out of both real and fake (cannot split): {len(dropped_cases)} ("
                     + ", ".join(f"{r.case} {r.before_window}" for r in dropped_cases.itertuples()) + ")")
    notes.append("fake windows: before = first h years, after = last h years of the real before window, h = years // 2 "
                 "(odd middle year dropped); before-window hand-check corrections split between halves in proportion to "
                 "raw homes (duplicates 0); same lots, groups and implausible flags as the central; units: extra new "
                 "homes per 100 lot acres a year within 1/4 mile; Wisconsin = x 298.97, extra homes 2027-2031")
    notes.append(f"bootstrap: 2,000 place draws, seed {SEED}; real-same and fake use the same draws (paired)")
    for n in notes:
        rows.append({"version": "all", "row": "note", "note": n})
    O = pd.DataFrame(rows)
    O.round(4).to_csv(REFERENCE / "tod_causal_central_pretrend.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 200)
    print(O.round(2).to_string(index=False))
    print("cases:\n", C.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

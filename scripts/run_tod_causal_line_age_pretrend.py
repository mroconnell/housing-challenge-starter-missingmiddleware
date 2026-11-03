"""Test T2b-PT (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, "Test T2b-PT: pre-trend check on the 2x2 behind the upper line",
locked 2026-11-03 before any count).

The T2b 2x2 (line age x upzoning, stops within 1/4 mile, D-11 + Milwaukee Hop placebo, DUS fix in) rerun with a fake
reform: the before window is split in half (h = years // 2, as Test P; an odd middle year is left out); the first half
is "before", the second half "after". The real after window is never read in the fake run: the fake lot frame is built
from the lot table without its window-total columns and from the per-building events of the before window only
(run_tod_causal_predict.placebo_windows; before-window hand-check corrections split between the halves in proportion to
raw homes). Stops keep their real line-age class and group.

Versions:
  real, T2b main          D-11 + Hop, real windows (sanity: must give 12.5 / -5.3 / 1.8 / 57.5, law effect 45.0)
  real, same places       the real 2x2 on the places (and cases) the fake run has
  fake, same places       the fake reform
Cells, weights and bootstrap as T2b (per case acre-pooled stop change; place = mean over its cases; cell = mean over
places; 2,000 place-cluster draws, seed 20261102, draws with an empty cell dropped).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_line_age_pretrend.py

Writes reference/tod_causal_line_age_pretrend.csv (summaries only: no lot rows, no parcel ids).
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

OUT = P.OUT
SEED, DRAWS = 20261102, 2000                   # as T2b
WI_FACTOR = 4874.1 / 100 * 5 * 1.2269          # 298.97 Wisconsin homes per unit
CELLS = ("new/no", "old/no", "old/up", "new/up")
LOT_COLS = ["group", "stop_id", "band", "implausible", "acres_land"]   # no window-total columns


# ----------------------------------------------------------------------------------------------------------------------
# stop aggregates
# ----------------------------------------------------------------------------------------------------------------------
def _stops(D: pd.DataFrame, ages: pd.DataFrame, place: str, case: str, yb: int, ya: int) -> pd.DataFrame:
    D = D[~D.implausible.fillna(False) & (D.band == "0-1/4")]
    n = D.homes_after_win.astype(float) / ya - D.homes_before_win.astype(float) / yb
    S = pd.DataFrame({"group": D.group.values, "stop_id": D.stop_id.values, "N": n.values,
                      "A": D.acres_land.fillna(0).values}).groupby(["group", "stop_id"], as_index=False)[["N", "A"]].sum()
    S = S.merge(ages, on="stop_id", how="left").fillna({"age": "excl"})
    return S.assign(place=place, case=case)


def real_stops(case: str, place: str, OY: pd.DataFrame, src: Path = OUT) -> pd.DataFrame:
    """Real windows, exactly as T2b (run_tod_causal_line_age.stop_sums)."""
    import run_tod_station_model as SM
    D = pd.read_parquet(src / f"lots_{case}.parquet", columns=LOT_COLS + ["homes_before_win", "homes_after_win"])
    if (src / f"events_{case}.parquet").exists():
        D = SM.event_windows(case, D, "permit_est", src)
    yb, ya = SM.windows(case)
    return _stops(D, P.stop_age(OY, case)[0], place, case, yb, ya)


def fake_stops(case: str, place: str, OY: pd.DataFrame, src: Path = OUT) -> pd.DataFrame | None:
    """Fake reform: halves of the before window. Never reads the real after window: the lot table is read without its
    window totals, and the events are cut to the before window inside placebo_windows. None if it cannot be split."""
    if not (src / f"events_{case}.parquet").exists():
        return None
    D0 = pd.read_parquet(src / f"lots_{case}.parquet", columns=LOT_COLS)
    D, h = P.placebo_windows(case, D0, src)
    if h == 0:
        return None
    return _stops(D, P.stop_age(OY, case)[0], place, case, h, h)


def milwaukee_stops() -> pd.DataFrame:
    M = P.milwaukee_frame()
    return pd.DataFrame({"group": ["comparison"], "stop_id": [0], "N": [(M.ha / M.ya - M.hb / M.yb).sum()],
                         "A": [M.A.sum()], "age": ["new"], "place": [P.MKE], "case": ["milwaukee_placebo"]})


# ----------------------------------------------------------------------------------------------------------------------
# 2x2 as T2b
# ----------------------------------------------------------------------------------------------------------------------
def place_cells(S: pd.DataFrame) -> pd.DataFrame:
    """Per case: acre-pooled change of its stops in the cell (cells with land only); per place: mean over its cases."""
    T = S[S.age != "excl"]
    T = T.assign(cell=T.age + "/" + np.where(T.group == "reform", "up", "no"))
    g = T.groupby(["place", "case", "cell"])[["N", "A"]].sum()
    g = g[g.A > 0]
    g = g.assign(d=100 * g.N / g.A)
    return g.groupby(["place", "cell"]).d.mean().reset_index()


def contrasts(cm: dict) -> dict:
    g = lambda k: cm.get(k, np.nan)  # noqa: E731
    out = {"transit_alone": g("new/no") - g("old/no"), "upzoning_alone": g("old/up") - g("old/no"),
           "interaction": g("new/up") - g("new/no") - g("old/up") + g("old/no")}
    out["law_near_new_lines"] = out["upzoning_alone"] + out["interaction"]    # = new/up - new/no
    return out


def estimate(PC: pd.DataFrame) -> dict:
    cm = PC.groupby("cell").d.mean().to_dict()
    return {**{c: cm.get(c, np.nan) for c in CELLS}, **contrasts(cm)}


def draw_places(places: list[str], seed: int = SEED, draws: int = DRAWS) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    arr = np.array(places, dtype=object)
    return [rng.choice(arr, len(arr), replace=True) for _ in range(draws)]


def bootstrap(PC: pd.DataFrame, picks: list[np.ndarray]) -> tuple[pd.DataFrame, int]:
    by = {p: g for p, g in PC.groupby("place")}
    rows, dropped = [], 0
    for pick in picks:
        B = pd.concat([by[p] for p in pick])
        bcm = B.groupby("cell").d.mean().to_dict()
        if any(c not in bcm for c in CELLS):
            dropped += 1
            rows.append(None)
            continue
        rows.append({**bcm, **contrasts(bcm)})
    return pd.DataFrame([r if r is not None else {} for r in rows]), dropped


def ci(x: pd.Series) -> tuple[float, float]:
    x = x.dropna()
    return float(x.quantile(.05)), float(x.quantile(.95))


def excludes_zero(lo: float, hi: float) -> bool:
    return lo > 0 or hi < 0


# ----------------------------------------------------------------------------------------------------------------------
def build() -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    import run_tod_causal_line_age as LA
    OY = LA.opening_years()
    cases = sorted(p.stem.removeprefix("lots_") for p in OUT.glob("lots_*.parquet"))
    real, fake, notes = [], [], []
    for case in cases:
        place = LA.place_of(case)
        if not place:
            continue
        real.append(real_stops(case, place, OY))
        f = fake_stops(case, place, OY)
        if f is None:
            notes.append(f"{place} ({case}): before window cannot be split (or no events); left out of the fake run")
        else:
            fake.append(f)
        print("built", case, flush=True)
    real.append(milwaukee_stops())
    notes.append(f"{P.MKE}: one before-window total, no years; left out of the fake run")
    return pd.concat(real, ignore_index=True), pd.concat(fake, ignore_index=True), notes


def main() -> None:
    R, F, notes = build()
    PC_real = place_cells(R)
    PC_fake = place_cells(F)
    fake_cases = set(F.case)
    PC_same = place_cells(R[R.case.isin(fake_cases)])           # same places and cases as the fake run
    same_places = sorted(PC_fake.place.unique())
    assert sorted(PC_same.place.unique()) == same_places
    left_out = sorted(set(PC_real.place) - set(same_places))

    rows, est, bs = [], {}, {}
    versions = (("real, T2b main (D-11 + Hop)", PC_real), ("real, same places", PC_same), ("fake, same places", PC_fake))
    for v, PC in versions:
        places = sorted(PC.place.unique())
        e = estimate(PC)
        B, dropped = bootstrap(PC, draw_places(places))   # fresh seed per version, as T2b's main (first) version
        est[v], bs[v] = e, B
        for c in CELLS:
            t = PC[PC.cell == c]
            lo, hi = ci(B[c])
            rows.append({"version": v, "row": "cell", "name": c, "value": e[c], "lo90": lo, "hi90": hi,
                         "places": t.place.nunique(), "place_list": "; ".join(f"{p} {d:.1f}" for p, d in zip(t.place, t.d))})
        for k in ("transit_alone", "upzoning_alone", "interaction", "law_near_new_lines"):
            lo, hi = ci(B[k])
            rows.append({"version": v, "row": "effect", "name": k, "value": e[k], "lo90": lo, "hi90": hi,
                         "wisconsin": e[k] * WI_FACTOR, "wisconsin_lo90": lo * WI_FACTOR, "wisconsin_hi90": hi * WI_FACTOR,
                         "places": len(places), "bootstrap_draws_dropped": dropped})

    # pass rule: fake law effect near new lines and fake interaction, 90% intervals include 0
    fk = "fake, same places"
    verdict = {}
    for k in ("law_near_new_lines", "interaction"):
        lo, hi = ci(bs[fk][k])
        verdict[k] = not excludes_zero(lo, hi)
        rows.append({"version": fk, "row": "pass_rule", "name": k, "value": est[fk][k], "lo90": lo, "hi90": hi,
                     "place_list": "PASS (90% interval includes 0)" if verdict[k] else "FAIL (90% interval excludes 0)"})
    passed = all(verdict.values())
    rows.append({"version": fk, "row": "pass_rule", "name": "overall", "place_list": "PASS" if passed else "FAIL"})

    # trend-adjusted upper (reported whatever the verdict; the plan uses it only if the check fails)
    rs = "real, same places"
    adj = est[rs]["law_near_new_lines"] - est[fk]["law_near_new_lines"]
    # reporting only (not in the lock): paired draws, same place picks for real and fake
    picks = draw_places(same_places, seed=SEED + 1)
    Br, _ = bootstrap(PC_same, picks)
    Bf, _ = bootstrap(PC_fake, picks)
    lo, hi = ci(Br.law_near_new_lines - Bf.law_near_new_lines)
    loo = {}
    for p in same_places:
        a = estimate(PC_same[PC_same.place != p])["law_near_new_lines"]
        b = estimate(PC_fake[PC_fake.place != p])["law_near_new_lines"]
        loo[p] = a - b
    lo_p, hi_p = min(loo, key=loo.get), max(loo, key=loo.get)
    rows.append({"version": "trend-adjusted", "row": "upper", "name": "real law effect near new lines - fake (same places)",
                 "value": adj, "lo90": lo, "hi90": hi, "wisconsin": adj * WI_FACTOR, "wisconsin_lo90": lo * WI_FACTOR,
                 "wisconsin_hi90": hi * WI_FACTOR, "loo_low": loo[lo_p], "loo_high": loo[hi_p],
                 "wisconsin_loo_low": loo[lo_p] * WI_FACTOR, "wisconsin_loo_high": loo[hi_p] * WI_FACTOR,
                 "places": len(same_places),
                 "place_list": f"interval: paired place bootstrap (reporting only, seed {SEED + 1}); leave-one-place-out low "
                               f"without {lo_p}, high without {hi_p}; " + "; ".join(f"without {p} {v:.1f}" for p, v in loo.items())})
    rows.append({"version": "trend-adjusted", "row": "current_upper", "name": "T2b law effect near new lines (owner upper)",
                 "value": est["real, T2b main (D-11 + Hop)"]["law_near_new_lines"],
                 "wisconsin": est["real, T2b main (D-11 + Hop)"]["law_near_new_lines"] * WI_FACTOR})
    for n in notes + [f"places left out of the like-for-like comparison: {', '.join(left_out)}"]:
        rows.append({"version": "all", "row": "note", "place_list": n})
    rows.append({"version": "all", "row": "note", "place_list": "fake windows: before = first h years, after = last h years of the "
                 "real before window, h = years // 2 (Denver's 5-year window drops its middle year); before-window hand-check "
                 "corrections split between the halves in proportion to raw homes (duplicates 0); stops keep their real "
                 "line-age class; units: extra new homes per 100 lot acres a year within 1/4 mile"})
    O = pd.DataFrame(rows)
    O.round(3).to_csv(REFERENCE / "tod_causal_line_age_pretrend.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 20, "display.max_colwidth", 160)
    print(O.round(1).to_string(index=False))
    print("factor", round(WI_FACTOR, 2))


if __name__ == "__main__":
    main()

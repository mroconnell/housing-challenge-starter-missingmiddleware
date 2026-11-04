"""TOD coverage test (docs/UNIFORM_DISPLAY_SPEC.md, "TOD coverage test", locked before it ran; owner approved the run
2026-11-04 16:51).

Question: how often does TOD's place-bootstrap 90% range contain the true average effect, given 11 places?

Check 1, width, two pools (units: extra new homes per 100 lot acres a year within 1/4 mile):
  real  (main, sets the widening): the 11 D-11 real place effects, read exactly as scripts/export_tod_line_draws.py
        (run_tod_causal_central_pretrend.real_effect, mean over a place's cases; mean must be 33.5373).
  fake  (sensitivity): the 10 C-PT fake-years effects in reference/tod_causal_central_pretrend.csv.
  Each pool: 1,000 runs; each run draws 11 places with replacement from the pool and builds the same 2,000-draw place
  bootstrap 90% range (5th to 95th percentile of resampled means). Coverage = share of runs whose range contains the
  pool's mean. One generator per pool, np.random.default_rng(20261103).
Check 2, bias (reported beside): fake mean with its 90% range (run_tod_causal_central_pretrend place bootstrap, seed
  20261103, 2,000 draws), and the fake mean without Seattle Othello.
Widening rule: if the real pool's coverage is below 90%, f = the smallest factor that, widening both ends of each run's
  range away from that run's point estimate (its sample mean), brings coverage to 90% (900 of 1,000 runs). f is then
  applied to the published range 4,866 to 15,361 about its bootstrap point 10,028 (= 33.5373 x 298.97).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_coverage_test.py

Writes reference/tod_coverage_test.csv (summaries only). Reads cached files under data/processed/, never writes there.
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

import run_tod_causal_central_pretrend as C  # noqa: E402

SEED = 20261103
RUNS, DRAWS, N_PLACES = 1000, 2000, 11
TARGET = 0.90
OUT_CSV = REFERENCE / "tod_coverage_test.csv"
CPT_CSV = REFERENCE / "tod_causal_central_pretrend.csv"
# published central range (homes), reference/tod_causal_central_pretrend.csv, "real, D-11 (11 places)"
PUB_POINT, PUB_LO, PUB_HI = 10027.7117, 4865.7167, 15360.5602


# ---------------------------------------------------------------------------------------------------------- pools
def real_pool() -> pd.Series:
    rows = []
    for f in sorted(C.OUT.glob("lots_*.parquet")):
        case = f.stem.removeprefix("lots_")
        place = C.place_of(case)
        if place:
            rows.append({"place": place, "real": C.real_effect(case)})
    s = pd.DataFrame(rows).dropna(subset=["real"]).groupby("place").real.mean()
    assert len(s) == 11 and round(s.mean(), 4) == C.SANITY_MEAN, s.mean()
    return s


def fake_pool(path: Path = CPT_CSV) -> pd.Series:
    t = pd.read_csv(path)
    t = t[(t.version == "per place") & t.fake.notna()]
    s = t.set_index("name").fake.astype(float)
    assert len(s) == 10 and "Saint Paul" not in s.index, s.index.tolist()
    return s


# ---------------------------------------------------------------------------------------------------------- simulation
def simulate(pool: np.ndarray, seed: int = SEED, runs: int = RUNS, draws: int = DRAWS, n: int = N_PLACES) -> pd.DataFrame:
    """Per run: sample mean (point), bootstrap 5th and 95th percentiles of resampled means."""
    rng = np.random.default_rng(seed)
    pool = np.asarray(pool, dtype=float)
    out = np.empty((runs, 3))
    for r in range(runs):
        x = pool[rng.integers(0, len(pool), n)]
        m = x[rng.integers(0, n, (draws, n))].mean(axis=1)
        out[r] = (x.mean(), np.quantile(m, .05), np.quantile(m, .95))
    return pd.DataFrame(out, columns=["point", "lo", "hi"])


def coverage(sim: pd.DataFrame, truth: float, f: float = 1.0) -> float:
    lo = sim.point - f * (sim.point - sim.lo)
    hi = sim.point + f * (sim.hi - sim.point)
    return float(((lo <= truth) & (truth <= hi)).mean())


def needed_factor(sim: pd.DataFrame, truth: float, target: float = TARGET) -> float:
    """Smallest f with coverage(sim, truth, f) >= target. Per run, the f that just reaches the truth; a run whose range
    has zero width on the needed side and misses the truth can never be covered (inf)."""
    below = truth < sim.point
    gap = np.where(below, sim.point - truth, truth - sim.point)
    half = np.where(below, sim.point - sim.lo, sim.hi - sim.point)
    with np.errstate(divide="ignore", invalid="ignore"):
        need = np.where(gap <= 0, 0.0, np.where(half > 0, gap / half, np.inf))
    k = int(np.ceil(target * len(need))) - 1
    return float(max(1.0, np.sort(need)[k]))


def widen(point: float, lo: float, hi: float, f: float) -> tuple[float, float]:
    return point - f * (point - lo), point + f * (hi - point)


# ---------------------------------------------------------------------------------------------------------- main
def main() -> None:
    real = real_pool()
    internal = {C.display(p): p for p in real.index}          # C-PT draws are over sorted internal place names
    fake = fake_pool().rename(index=internal).sort_index()
    assert set(fake.index) <= set(real.index), fake.index.tolist()
    rows = []
    sims = {}
    for name, pool in (("real (main, 11 places)", real), ("fake C-PT (sensitivity, 10 places)", fake)):
        sim = simulate(pool.values)
        truth = float(pool.mean())
        cov = coverage(sim, truth)
        sims[name] = (sim, truth, cov)
        rows.append({"check": "coverage", "pool": name, "measure": "share of 1,000 runs whose 90% range contains the pool mean",
                     "value": cov, "lo90": np.nan, "hi90": np.nan, "unit": "share of runs",
                     "note": f"truth = pool mean {truth:.4f}; runs {RUNS}, draws {DRAWS}, places per run {N_PLACES}, seed {SEED}; "
                             f"runs covered {int(round(cov * RUNS))}; mean range width {float((sim.hi - sim.lo).mean()):.2f}"})

    # bias check: same bootstrap as C-PT on the 10 fake places
    d = C.boot_means(fake, C.draw_places(sorted(fake.index), SEED, DRAWS))
    flo, fhi = C.ci(d)
    rows.append({"check": "bias", "pool": "fake C-PT (10 places)", "measure": "fake mean, place bootstrap 90% range",
                 "value": float(fake.mean()), "lo90": flo, "hi90": fhi, "unit": "homes per 100 lot acres a year",
                 "note": f"2,000 place draws, seed {SEED}; range includes 0: {flo <= 0 <= fhi}"})
    no_oth = fake.drop(internal["Seattle Othello"])
    rows.append({"check": "bias", "pool": "fake C-PT without Seattle Othello (9 places)", "measure": "fake mean",
                 "value": float(no_oth.mean()), "lo90": np.nan, "hi90": np.nan, "unit": "homes per 100 lot acres a year",
                 "note": "plain average"})
    rows.append({"check": "bias", "pool": "real (11 places)", "measure": "real mean (for comparison)",
                 "value": float(real.mean()), "lo90": np.nan, "hi90": np.nan, "unit": "homes per 100 lot acres a year",
                 "note": ""})

    # widening (main pool only)
    sim, truth, cov = sims["real (main, 11 places)"]
    if cov < TARGET:
        f = needed_factor(sim, truth)
        assert coverage(sim, truth, f) >= TARGET and coverage(sim, truth, f * (1 - 1e-9)) < TARGET
        wlo, whi = widen(PUB_POINT, PUB_LO, PUB_HI, f)
        rows.append({"check": "widening", "pool": "real (main, 11 places)", "measure": "widening factor f",
                     "value": f, "lo90": np.nan, "hi90": np.nan, "unit": "factor",
                     "note": f"coverage at f = {coverage(sim, truth, f):.3f}; both ends widened away from each run's sample mean"})
        rows.append({"check": "widening", "pool": "real (main, 11 places)", "measure": "widened Wisconsin 90% range",
                     "value": PUB_POINT, "lo90": wlo, "hi90": whi, "unit": "homes 2027-2031",
                     "note": f"published {PUB_LO:,.0f} to {PUB_HI:,.0f} widened about point {PUB_POINT:,.0f} by f"})
    else:
        rows.append({"check": "widening", "pool": "real (main, 11 places)", "measure": "widening factor f", "value": 1.0,
                     "lo90": np.nan, "hi90": np.nan, "unit": "factor", "note": "coverage at or above 90%: no widening"})

    T = pd.DataFrame(rows)
    T.to_csv(OUT_CSV, index=False, float_format="%.4f")
    print(T.to_string(index=False))


if __name__ == "__main__":
    main()

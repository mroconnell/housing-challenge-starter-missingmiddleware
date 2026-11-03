"""Test C-PT: the fake-reform run on the central never reads after-window homes (offline, synthetic lots and events).

The fake effect must not move whatever the real after window holds: after-window permit events, the lot table's
window-total columns, and after-window hand-check rows are all changed. Changing the before window must move it."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_tod_causal_central_pretrend as CP  # noqa: E402

CASE = "zz_synthetic"
CFG = {"before": (2001, 2006), "after": (2008, 2012)}     # reform 2007; fake before 2001-03, fake after 2004-06


def write_case(src: Path, seed: int = 0, after_scale: float = 1.0, before_scale: float = 1.0, hc_after: float = 5.0) -> None:
    rng = np.random.default_rng(seed)
    n = 200
    lots = pd.DataFrame({"group": np.where(np.arange(n) < 100, "reform", "comparison"),
                         "band": np.where(np.arange(n) % 10 == 9, "1/4-1/2", "0-1/4"), "implausible": np.arange(n) == 7,
                         "homes_existing": rng.integers(1, 20, n).astype(float),
                         "in_reform_area": np.arange(n) < 60, "acres_land": rng.uniform(0.1, 1.0, n),
                         "homes_before_win": rng.integers(0, 9, n).astype(float) * before_scale,
                         "homes_after_win": rng.integers(0, 9, n).astype(float) * after_scale + 1000 * (after_scale != 1)},
                        index=pd.Index(np.arange(n) * 3 + 1))
    lots.to_parquet(src / f"lots_{CASE}.parquet")
    k = 600
    yr = rng.integers(2001, 2013, k)
    homes = rng.integers(1, 12, k).astype(float)
    homes = np.where(yr >= 2007, homes * after_scale, homes * before_scale)
    pd.DataFrame({"lot_index": rng.choice(lots.index, k), "homes": homes, "yr": yr}).to_parquet(src / f"events_{CASE}.parquet")
    pd.DataFrame({"case": [CASE] * 3, "lot_index": [lots.index[3], lots.index[120], lots.index[5]],
                  "window": ["before", "before", "after"], "class": ["wrong count", "duplicate", "wrong count"],
                  "homes_corrected": [2.0 * before_scale, np.nan, hc_after]}).to_csv(src / "hand_check_big_lots.csv", index=False)


def run(src: Path) -> tuple[float, int]:
    ev = lambda case, s=src: pd.read_parquet(s / f"events_{case}.parquet")  # noqa: E731
    with mock.patch.object(CP.P, "cfg", lambda case: CFG), mock.patch.object(CP.P, "event_years", ev), \
            mock.patch.object(CP.P, "OUT", src):
        return CP.fake_effect(CASE, src)


class TestFakeNeverReadsAfterWindow(unittest.TestCase):
    def test_after_window_changes_do_not_move_fake_run(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            write_case(Path(a))
            write_case(Path(b), after_scale=37.0, hc_after=999.0)   # after events, lot window totals, after hand checks
            (ea, ha), (eb, hb) = run(Path(a)), run(Path(b))
            self.assertEqual((ha, hb), (3, 3))
            self.assertTrue(np.isfinite(ea) and ea != 0)
            self.assertEqual(ea, eb)

    def test_before_window_changes_do_move_it(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            write_case(Path(a))
            write_case(Path(b), before_scale=3.0)
            self.assertNotAlmostEqual(run(Path(a))[0], run(Path(b))[0])

    def test_lot_table_read_without_window_totals(self):
        self.assertNotIn("homes_after_win", CP.LOT_COLS)
        self.assertNotIn("homes_before_win", CP.LOT_COLS)
        seen = []
        real_read = pd.read_parquet

        def spy(path, *args, **kw):
            if Path(path).name.startswith("lots_"):
                seen.append(kw.get("columns"))
            return real_read(path, *args, **kw)

        with tempfile.TemporaryDirectory() as a, mock.patch.object(CP.pd, "read_parquet", spy):
            write_case(Path(a))
            run(Path(a))
        self.assertTrue(seen)
        for cols in seen:
            self.assertIsNotNone(cols)
            self.assertNotIn("homes_after_win", cols)

    def test_quarter_effect_formula(self):
        D = pd.DataFrame({"group": ["reform", "comparison"], "band": "0-1/4", "implausible": False,
                          "homes_existing": [10.0, 10.0], "acres_land": [2.0, 4.0],
                          "homes_before_win": [3.0, 6.0], "homes_after_win": [9.0, 6.0]})
        # reform 100*(9/3-3/3)/2 = 100; comparison 100*(6/3-6/3)/4 = 0
        self.assertAlmostEqual(CP.quarter_effect(D, 3, 3), 100.0)


if __name__ == "__main__":
    unittest.main()

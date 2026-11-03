"""Test T2b-PT: the fake-reform run never reads after-window homes (offline, synthetic lots and events).

The fake run must give the same stop sums whatever the real after window holds: after-window permit events, the lot
table's window-total columns, and after-window hand-check rows are all changed and the result must not move. Changing
the before window must move it (the check is live)."""
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

import run_tod_causal_line_age_pretrend as PT  # noqa: E402

CASE = "zz_synthetic"
CFG = {"before": (2001, 2006), "after": (2008, 2012)}     # reform 2007; fake before 2001-03, fake after 2004-06


def write_case(src: Path, seed: int = 0, after_scale: float = 1.0, before_scale: float = 1.0, hc_after: float = 5.0) -> None:
    rng = np.random.default_rng(seed)
    n = 200
    lots = pd.DataFrame({"group": np.where(np.arange(n) < 100, "reform", "comparison"),
                         "stop_id": np.arange(n) // 25, "band": "0-1/4", "implausible": False,
                         "acres_land": rng.uniform(0.1, 1.0, n),
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


def oy() -> pd.DataFrame:
    s = np.arange(8)
    return pd.DataFrame({"case": CASE, "stop_id": s, "oy": [2005, 1980, 2009, np.nan, 2006, 1970, 2000, 2010],
                         "old": False, "reform_year": 2007.0})


def run(src: Path) -> pd.DataFrame:
    ev = lambda case, s=src: pd.read_parquet(s / f"events_{case}.parquet")  # noqa: E731
    with mock.patch.object(PT.P, "cfg", lambda case: CFG), mock.patch.object(PT.P, "event_years", ev), \
            mock.patch.object(PT.P, "OUT", src):
        S = PT.fake_stops(CASE, "Synthetic", oy(), src)
    return S.sort_values(["group", "stop_id"]).reset_index(drop=True)


class TestFakeNeverReadsAfterWindow(unittest.TestCase):
    def test_after_window_changes_do_not_move_fake_run(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            write_case(Path(a))
            write_case(Path(b), after_scale=37.0, hc_after=999.0)   # after events, lot window totals, after hand checks
            Sa, Sb = run(Path(a)), run(Path(b))
            self.assertTrue(np.isfinite(Sa.N).all() and len(Sa) == 8)
            self.assertTrue((Sa.N != 0).any())
            pd.testing.assert_frame_equal(Sa, Sb)
            cells_a, cells_b = PT.place_cells(Sa), PT.place_cells(Sb)
            pd.testing.assert_frame_equal(cells_a, cells_b)

    def test_before_window_changes_do_move_it(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            write_case(Path(a))
            write_case(Path(b), before_scale=3.0)
            self.assertFalse(np.allclose(run(Path(a)).N, run(Path(b)).N))

    def test_lot_table_read_without_window_totals(self):
        self.assertNotIn("homes_after_win", PT.LOT_COLS)
        self.assertNotIn("homes_before_win", PT.LOT_COLS)

    def test_law_effect_is_new_up_minus_new_no(self):
        c = PT.contrasts({"new/no": 12.5, "old/no": -5.3, "old/up": 1.8, "new/up": 57.5})
        self.assertAlmostEqual(c["law_near_new_lines"], 57.5 - 12.5)


if __name__ == "__main__":
    unittest.main()

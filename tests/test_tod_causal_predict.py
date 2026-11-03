"""Test P: the held-out place never enters its own training numbers (offline, synthetic lots).

Changing the held-out place's after-window homes must leave its A, A0 and B predictions unchanged (A uses only its
reform stops' acres; B sets its intercept from its before-window lots only)."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_tod_causal_predict as P  # noqa: E402


def synthetic(seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(6):
        place = f"p{k}"
        for case in (f"{place}_a", f"{place}_b") if k == 0 else (f"{place}_a",):
            for sid in range(8):
                group = "reform" if sid < 4 else "comparison"
                age = ["old", "new", "old", "excl"][sid % 4]
                n = 40
                up = (rng.random(n) < (0.3 if group == "reform" else 0.0)).astype(int)
                hb = rng.poisson(0.3, n) * rng.integers(1, 20, n)
                ha = rng.poisson(0.3 + 0.5 * up + 0.2 * (age == "new"), n) * rng.integers(1, 20, n)
                rows.append(pd.DataFrame({"place": place, "case": case, "group": group, "stop_id": sid,
                                          "sub": rng.integers(0, 2, n), "up": up, "A": rng.uniform(0.05, 1.0, n),
                                          "hb": hb.astype(float), "ha": ha.astype(float), "yb": 6, "ya": 5, "age": age}))
    return pd.concat(rows, ignore_index=True)


def predictions(L: pd.DataFrame, hidden: str) -> tuple[float, float, float, float]:
    S, C = P.aggregate(L)
    R = P.loo(S, C, [hidden]).iloc[0]
    return R.A, R.A0, R.B, R.B_did


class TestHeldOut(unittest.TestCase):
    def test_after_window_of_hidden_place_does_not_move_its_prediction(self):
        L = synthetic()
        for hidden in ("p0", "p3"):
            base = predictions(L, hidden)
            L2 = L.copy()
            m = L2.place == hidden
            L2.loc[m, "ha"] = L2.loc[m, "ha"] * 7 + 13          # change the held-out place's after window
            self.assertTrue(np.all(np.isfinite(base)))
            np.testing.assert_allclose(predictions(L2, hidden), base, rtol=1e-9, atol=1e-9)

    def test_other_places_after_window_does_move_it(self):
        L = synthetic()
        base = predictions(L, "p0")
        L2 = L.copy()
        m = L2.place == "p2"
        L2.loc[m, "ha"] = L2.loc[m, "ha"] * 3 + 5
        self.assertFalse(np.allclose(predictions(L2, "p0")[:3], base[:3]))

    def test_binomial_tail(self):
        self.assertAlmostEqual(P.p_at_least(6), 0.5, places=6)
        self.assertAlmostEqual(round(P.p_at_least(8), 3), 0.113, places=3)


if __name__ == "__main__":
    unittest.main()

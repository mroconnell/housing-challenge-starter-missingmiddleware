"""Test 2b-L cross-fit: a binding line is never chosen with the half it is tested on (offline, synthetic)."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_tod_causal_binding_line as B  # noqa: E402


class TestCrossFit(unittest.TestCase):
    def test_split_is_deterministic_disjoint_and_complete(self):
        stops = [f"s{i}" for i in range(11)]
        a, b = B.split_stops(stops), B.split_stops(list(reversed(stops)))
        self.assertEqual(a, b)                                   # same seed, order-free
        self.assertEqual(set(a), set(stops))
        self.assertEqual(sorted(a.values()).count("A"), 5)
        self.assertEqual(sorted(a.values()).count("B"), 6)

    def test_line_chosen_only_on_the_other_half(self):
        # half A's jumps favour candidate 0.2, half B's favour 0.8
        J = {"A": {0.2: 50.0, 0.5: 10.0, 0.8: 1.0}, "B": {0.2: 1.0, 0.5: 10.0, 0.8: 99.0}}
        calls = []

        def train_jump(half, c):
            calls.append(half)
            return J[half][c]
        cf = B.cross_fit([0.2, 0.5, 0.8], train_jump)
        self.assertEqual(cf["B"][0], 0.2)                        # tested on B, chosen on A
        self.assertEqual(cf["A"][0], 0.8)                        # tested on A, chosen on B
        self.assertEqual(cf["B"][1], J["A"])
        self.assertEqual(cf["A"][1], J["B"])
        self.assertEqual(calls, ["A"] * 3 + ["B"] * 3)

    def test_test_half_outcomes_cannot_move_its_line(self):
        rng = np.random.default_rng(1)
        base = {"A": dict(zip(range(9), rng.normal(size=9))), "B": dict(zip(range(9), rng.normal(size=9)))}
        first = B.cross_fit(range(9), lambda h, c: base[h][c])["B"][0]
        for _ in range(20):                                      # scramble half B's jumps: B's line must not move
            base["B"] = dict(zip(range(9), rng.normal(scale=100, size=9)))
            self.assertEqual(B.cross_fit(range(9), lambda h, c: base[h][c])["B"][0], first)

    def test_no_estimable_candidate(self):
        self.assertIsNone(B.choose_line({0.1: np.nan, 0.2: None}))
        self.assertEqual(B.choose_line({0.1: np.nan, 0.2: -3.0, 0.3: -1.0}), 0.3)

    def test_weighted_cut_points(self):
        v, w = np.array([100.0, 200.0, 300.0, 400.0]), np.array([1.0, 1.0, 1.0, 1.0])
        self.assertEqual(B.wquantile(v, w, 0.5), 200.0)
        self.assertEqual(B.wquantile(v, w, 0.9), 400.0)

    def test_neighbourhood_rate_leaves_own_lot_out(self):
        x, y = np.array([0.0, 100.0, 5000.0]), np.array([0.0, 0.0, 0.0])
        r = B.neighbourhood_rate(x, y, np.array([10.0, 0.0, 7.0]), np.array([1.0, 1.0, 1.0]))
        self.assertAlmostEqual(r[0], 0.0)                         # its only neighbour built nothing
        self.assertAlmostEqual(r[1], 1000.0)                      # 100 x 10 homes / 1 acre
        self.assertTrue(np.isnan(r[2]))                           # no neighbour within 400 m


if __name__ == "__main__":
    unittest.main()

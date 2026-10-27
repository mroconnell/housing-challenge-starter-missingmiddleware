"""Tests for the California AB 2097 test arithmetic (missing_middleware/tod/ab2097.py), on synthetic fixtures."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from missing_middleware.tod import ab2097 as ab


def _a2(rows):
    cols = ["JURIS_NAME", "YEAR", "UNIT_CAT", "NO_BUILDING_PERMITS", "LATITUDE", "LONGITUDE", "STD_ADDRESS", "STREET_ADDRESS"]
    return pd.DataFrame(rows, columns=cols)


def _world(n_j: int = 12, effect: float = 0.0, seed: int = 0):
    """n_j jurisdictions, each with near / ring / beyond land of 1,000 homes and 100 acres. Every jurisdiction has
    one project per area per year with 10 units, plus `effect` extra units near transit per after year.
    Jurisdiction 'LOS ANGELES' also has upzoned near land."""
    rng = np.random.default_rng(seed)
    juris = ["LOS ANGELES"] + [f"CITY{i}" for i in range(1, n_j)]
    cells, perms = [], []
    for j in juris:
        for z in ("near", "ring", "beyond"):
            cells.append({"juris": j, "zone": z, "upz": False, "homes": 1000.0, "acres": 100.0})
        if j == "LOS ANGELES":
            cells.append({"juris": j, "zone": "near", "upz": True, "homes": 1000.0, "acres": 100.0})
        for y in ab.YEARS:
            for z, u in (("near", False), ("ring", False), ("beyond", False)) + ((("near", True),) if j == "LOS ANGELES" else ()):
                units = 10.0 + (effect if (z == "near" and not u and y in ab.AFTER) else 0.0)
                perms.append({"juris": j, "project": f"{j}-{z}-{u}-{y}-{rng.integers(1e9)}", "year": y, "zone": z,
                              "upz": u, "all_units": units, "units_2plus": units / 2})
    return pd.DataFrame(cells), pd.DataFrame(perms)


class TestPermits(unittest.TestCase):
    def test_geocoded_rule(self):
        lat = pd.Series([34.0, 34.0, 34.0, np.nan, 34.0])
        lon = pd.Series([-118.0] * 5)
        std = pd.Series(["1 Main St, Los Angeles, California, 90001", "Main St, Los Angeles, California, 90001",
                         "Sacramento Ca", "1 Main St, Los Angeles, California, 90001", None])
        self.assertEqual(ab.is_geocoded(lat, lon, std).tolist(), [True, True, False, False, False])

    def test_clean_dedup_and_outcomes(self):
        a = _a2([
            ["X CITY", 2020, "5+", 50, 34.0, -118.0, "1 Main St, X, California, 90001", "1 MAIN ST"],
            ["X CITY", 2020, "5+", 50, 34.0, -118.0, "1 Main St, X, California, 90001", "1 Main St."],  # duplicate
            ["X CITY", 2020, "ADU", 1, 34.0, -118.0, "1 Main St, X, California, 90001", "1 MAIN ST"],   # kept: other category
            ["X CITY", 2020, "SFD", 1, 34.0, -118.0, "X Ca", "2 ELM"],                                  # fallback point
            ["X CITY", 2017, "SFD", 1, 34.0, -118.0, "3 Oak, X, California, 90001", "3 OAK"],          # out of window
            ["X CITY", 2021, "2 to 4", 0, 34.0, -118.0, "4 Oak, X, California, 90001", "4 OAK"],       # no permits
        ])
        p, info = ab.clean_permits(a)
        self.assertEqual(len(p), 2)
        self.assertEqual(p["all_units"].sum(), 51)
        self.assertEqual(p["units_2plus"].sum(), 50)
        self.assertEqual(info["duplicate_records_dropped"], 1)
        self.assertEqual(info["units_not_geocoded"], 1)
        self.assertEqual(p["project"].nunique(), 1)   # same address -> one project
        self.assertNotIn("1 MAIN", " ".join(map(str, p.values.ravel())))  # no address written out

    def test_full_reporters(self):
        p = pd.DataFrame({"juris": ["A"] * 8 + ["B"] * 7, "year": ab.YEARS + ab.YEARS[:7]})
        self.assertEqual(ab.full_reporters(p), ["A"])

    def test_zones(self):
        d = np.array([100, 600, 900, 3000])
        self.assertEqual(ab.zone_of(d).tolist(), ["near", "near", "ring", "beyond"])
        self.assertEqual(ab.zone_of(d, near_m=ab.QUARTER_M).tolist(), ["near", "gap", "ring", "beyond"])


class TestEstimates(unittest.TestCase):
    def test_groups_drop_already_and_repealed(self):
        cells, _ = _world()
        extra = pd.DataFrame([{"juris": j, "zone": z, "upz": False, "homes": 1.0, "acres": 1.0}
                              for j in ("SAN FRANCISCO", "SAN JOSE") for z in ("near", "ring")])
        cells = pd.concat([cells, extra])
        rep = sorted(cells.juris.unique())
        g = ab.define_groups(cells, rep)
        self.assertNotIn("SAN FRANCISCO", g["P"].juris)
        self.assertNotIn("SAN JOSE", g["P"].juris)
        self.assertEqual(g["T+P"].juris, ["LOS ANGELES"])
        self.assertIn("SAN JOSE", ab.define_groups(cells, rep, include_repealed=True)["P"].juris)

    def test_did_recovers_effect(self):
        cells, perms = _world(effect=5.0)
        g = ab.define_groups(cells, sorted(cells.juris.unique()))
        r = ab.estimate(g["P"], cells, perms, "all_units", "per_1000_homes", draws=200)
        self.assertAlmostEqual(r["estimate"], 5.0)        # 5 extra units per 1,000 homes per year
        self.assertAlmostEqual(r["low"], 5.0)             # identical jurisdictions -> no spread
        r2 = ab.estimate(g["P"], cells, perms, "all_units", "per_acre", draws=50)
        self.assertAlmostEqual(r2["estimate"], 0.05)      # 5 units per 100 acres
        r3 = ab.estimate(g["P"], cells, perms, "units_2plus", "per_1000_homes", draws=50)
        self.assertAlmostEqual(r3["estimate"], 2.5)
        t = ab.estimate(g["T+P"], cells, perms, "all_units", "per_1000_homes", draws=50)
        self.assertAlmostEqual(t["estimate"], 0.0)
        self.assertTrue(np.isnan(t["low"]))               # one jurisdiction -> no jurisdiction interval
        lo, hi, _ = ab.project_interval(g["T+P"], cells, perms, "all_units", "per_1000_homes", draws=200)
        self.assertLessEqual(lo, 0.0)
        self.assertGreaterEqual(hi, 0.0)

    def test_jurisdiction_interval_matches_cases_style_did(self):
        cells, perms = _world(effect=3.0, seed=2)
        rng = np.random.default_rng(1)
        perms["all_units"] = perms["all_units"] * rng.uniform(0.5, 1.5, len(perms))
        g = ab.define_groups(cells, sorted(cells.juris.unique()))["P"]
        r = ab.estimate(g, cells, perms, "all_units", "per_1000_homes", draws=300)
        ap = ab.to_area_permits(g, perms, "all_units")
        den = ab.denominators(g, cells, "per_1000_homes")
        from missing_middleware.tod import cases
        d = cases.did(ap, den, ab.BEFORE, ab.AFTER, scale=1000.0)["did"]
        self.assertAlmostEqual(r["estimate"], d, places=9)
        self.assertLess(r["low"], r["estimate"])
        self.assertGreater(r["high"], r["estimate"])

    def test_displacement_and_rates(self):
        cells, perms = _world()
        # move 4 units a year from ring to near after the law in every jurisdiction
        m = perms["year"].isin(ab.AFTER)
        perms.loc[m & (perms.zone == "ring"), "all_units"] -= 4
        perms.loc[m & (perms.zone == "near") & ~perms.upz, "all_units"] += 4
        g = ab.define_groups(cells, sorted(cells.juris.unique()))
        r = ab.estimate(g["P"], cells, perms, "all_units", "per_1000_homes", treat=("ring", False), comp=("beyond", False), draws=50)
        self.assertAlmostEqual(r["estimate"], -4.0)
        rates = ab.rates_by_year(g, cells, perms)
        x = rates[(rates.group == "P") & (rates.area == "near") & (rates.outcome == "all_units") & (rates.year == 2024)]
        self.assertAlmostEqual(float(x.units_per_1000_homes.iloc[0]), 14.0)

    def test_drop_largest_and_thin_rule(self):
        cells, perms = _world()
        g = ab.define_groups(cells, sorted(cells.juris.unique()))["P"]
        big = pd.DataFrame([{"juris": "CITY1", "project": "big", "year": 2024, "zone": "near", "upz": False,
                             "all_units": 500.0, "units_2plus": 500.0}])
        p2 = pd.concat([perms, big])
        kept = ab.drop_largest(g, p2, "all_units")
        self.assertNotIn("big", set(kept.project))
        self.assertEqual(ab.usable(9), "too thin")
        self.assertEqual(ab.usable(10), "usable")


if __name__ == "__main__":
    unittest.main()

"""States with statewide ADU laws (missing_middleware/comparison/statewide_states.py).
Offline; tiny synthetic ACS and place-code fixtures in tests/fixtures/statewide_states/,
plus consistency checks on the committed reference/statewide_states_*.csv aggregates."""
import re
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware.comparison import statewide_states as ss

FIX = Path(__file__).parent / "fixtures" / "statewide_states"
REF = Path(__file__).resolve().parent.parent / "reference"
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")


class TestStateList(unittest.TestCase):
    def test_eighteen_states_ten_strong_eight_weaker(self):
        abbrs = [s["abbr"] for s in ss.STATES]
        self.assertEqual(len(abbrs), 18)
        self.assertEqual(len(set(abbrs)), 18)
        strong = {s["abbr"] for s in ss.STATES if s["mercatus_class"] == "strong"}
        weaker = {s["abbr"] for s in ss.STATES if s["mercatus_class"] == "weaker"}
        self.assertEqual(strong, set(ss.STRONG))
        self.assertEqual(weaker, set(ss.WEAKER))
        self.assertEqual(len(strong), 10)
        self.assertEqual(len(weaker), 8)

    def test_rows_complete_and_dated(self):
        for s in ss.STATES:
            self.assertEqual(list(s.keys()), ss.STATE_COLUMNS, s["abbr"])
            self.assertRegex(s["treatment_date"], ISO, s["abbr"])
            self.assertRegex(s["effective_date"], ISO, s["abbr"])
            self.assertIn(s["data_kind"], ss.QUALITY_SCORE, s["abbr"])
            self.assertTrue(s["law_source"].startswith("http"), s["abbr"])
            self.assertTrue(0 <= s["years_after_compliance"] <= s["years_after_effective"] <= 5, s["abbr"])
            if s["data_kind"] == "none":
                self.assertEqual(s["years_after_effective"], 0, s["abbr"])


class TestSeriesAndPeriods(unittest.TestCase):
    def test_series_belong_to_listed_states(self):
        abbrs = {s["abbr"] for s in ss.STATES}
        for sid, s in ss.SERIES.items():
            self.assertIn(s["state"], abbrs, sid)
            self.assertIn(s["status"], ("observed", "source_lead"), sid)
            self.assertTrue(all(isinstance(n, int) and n >= 0 for n in s["counts"].values()), sid)

    def test_periods_reference_observed_years(self):
        for sid, phase, label, y0, y1, _ in ss.PERIODS:
            self.assertIn(sid, ss.SERIES)
            self.assertLessEqual(y0, y1)
            yrs = [y for y in range(y0, y1 + 1) if y in ss.SERIES[sid]["counts"]]
            self.assertTrue(yrs, f"{sid} {label} has no observed year")

    def test_period_rate_arithmetic(self):
        series = {"X": dict(state="WA", geography="g", measure="m", year_basis="cy", denominator=("state", "53"),
                            source="s", status="observed", counts={2020: 10, 2021: 30, 2023: 20})}
        periods = [("X", "after", "2020-2023", 2020, 2023, "1-4")]
        out = ss.period_rates(series, periods, homes={"X": 10_000})
        r = out.iloc[0]
        self.assertEqual(r["years_observed"], 3)  # 2022 missing is not zero
        self.assertEqual(r["adu_count"], 60)
        self.assertAlmostEqual(r["rate"], 1000 * 60 / 3 / 10_000)
        self.assertLess(r["rate_lo"], r["rate"])
        self.assertGreater(r["rate_hi"], r["rate"])


class TestACS(unittest.TestCase):
    def test_denominators_from_fixture(self):
        series = {
            "inc": dict(state="WA", geography="g", measure="m", year_basis="cy", source="s", status="observed",
                        denominator=("places_c1_excluding", ("53", ("5363000",))), counts={2020: 1}),
            "named": dict(state="OR", geography="g", measure="m", year_basis="cy", source="s", status="observed",
                          denominator=("place_names", ("41", ("Albany",))), counts={2020: 1}),
            "st": dict(state="WA", geography="g", measure="m", year_basis="cy", source="s", status="observed",
                       denominator=("state", "53"), counts={2020: 1}),
        }
        acs = ss.acs_geographies(FIX / "b25024.dat", FIX / "b25077.dat", FIX / "b25064.dat", series,
                                 place_codes={"53": FIX / "st53_place.txt", "41": FIX / "st41_place.txt"},
                                 extra_states={"WI": "55"}).set_index("key")
        # incorporated places only (CDP dropped), Seattle excluded: Aberdeen 200 + Spokane 300
        self.assertEqual(acs.loc["inc", "homes"], 500)
        self.assertEqual(acs.loc["inc", "n_geographies"], 2)
        self.assertEqual(acs.loc["inc", "median_value"], round((200000 * 200 + 350000 * 300) / 500))
        self.assertTrue(acs.loc["inc", "market_is_weighted_mean_of_places"])
        self.assertEqual(acs.loc["named", "homes"], 250)  # the city, not the same-named CDP
        self.assertEqual(acs.loc["st", "homes"], 2000)
        self.assertEqual(acs.loc["state_WI", "median_value"], 250000)

    def test_place_name_must_match_once(self):
        with self.assertRaises(ValueError):
            ss.places_by_name(FIX / "st41_place.txt", ("Nowhere",))


class TestRanking(unittest.TestCase):
    def test_market_score(self):
        self.assertAlmostEqual(ss.market_score(250_000, 250_000), 1.0)
        self.assertAlmostEqual(ss.market_score(750_000, 250_000), 0.0)
        self.assertAlmostEqual(ss.market_score(2_000_000, 250_000), 0.0)

    def test_states_without_data_get_no_post_or_market_credit(self):
        states = [s for s in ss.STATES if s["abbr"] in ("IA", "OR")]
        out = ss.rank_states(states, {"IA": 208_000, "OR": 480_000}, wi_value=266_500).set_index("abbr")
        self.assertEqual(out.loc["IA", "s_post_years"], 0)
        self.assertEqual(out.loc["IA", "s_market"], 0)
        self.assertGreater(out.loc["OR", "score"], out.loc["IA", "score"])
        self.assertAlmostEqual(out.loc["IA", "score"], ss.WEIGHTS["law"] * 1.0)


@unittest.skipUnless((REF / "statewide_states_ranking.csv").exists(), "reference tables not built")
class TestReferenceTables(unittest.TestCase):
    def test_reference_tables_consistent(self):
        laws = pd.read_csv(REF / "statewide_states_laws.csv", dtype=str)
        self.assertEqual(len(laws), 18)
        rank = pd.read_csv(REF / "statewide_states_ranking.csv")
        self.assertEqual(len(rank), 17)  # California is the fitting state, not ranked
        self.assertNotIn("CA", set(rank["abbr"]))
        self.assertTrue(rank["score"].is_monotonic_decreasing)
        per = pd.read_csv(REF / "statewide_states_period_rates.csv")
        self.assertEqual(len(per), len(ss.PERIODS) + len(ss.CA_RATES))
        annual = pd.read_csv(REF / "statewide_states_annual.csv")
        self.assertEqual(len(annual), sum(len(s["counts"]) for s in ss.SERIES.values()))
        ok = annual.dropna(subset=["per_1000_homes"])
        self.assertTrue(((ok["per_1000_homes"] - 1000 * ok["adu_count"] / ok["homes"]).abs() < 1e-3).all())


if __name__ == "__main__":
    unittest.main()

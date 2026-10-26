"""Offline tests for the TOD major-transit-stop pipeline (no network).

Fixtures in tests/fixtures/tod/ are synthetic: a tiny GTFS feed, NTM-style route lines and stops in a
local metric frame."""
import csv
import datetime as dt
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.tod import transit as T  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "tod"
REF = ROOT / "reference"


def fixture_zip(tmpdir: Path) -> Path:
    path = tmpdir / "gtfs_small.zip"
    with zipfile.ZipFile(path, "w") as z:
        for f in sorted((FIX / "gtfs_small").glob("*.txt")):
            z.write(f, f"feed/{f.name}")  # in a sub-folder, as some agencies publish
    return path


def table(name):
    with open(FIX / "gtfs_small" / name, newline="") as f:
        return list(csv.DictReader(f))


class TestMadisonRouteDescriptions(unittest.TestCase):
    CASES = {
        "Monday thru Saturday daytime schedule trips operate at least every 15 minutes. Evening and all-day Sunday/Holiday schedule trips operate at least every 30 minutes.": 4.0,
        "Weekday daytime schedule trips operate at least every 15 minutes. Evening and all-day Weekend/Holiday schedule trips operate at least every 30 minutes.": 4.0,
        "Daily schedule trips operate at least every 50 minutes. Additional weekday schedule trips operate at least every 15 minutes from approximately 7 AM until 6 PM. Limited trips operate on Holidays.": 4.0,
        "Weekday schedule trips operate at least every 30 minutes.": 2.0,
        "Weekday daytime schedule trips operate at least every 30 minutes. Evening and all-day Weekend/Holiday schedule trips operate at least every 60 minutes.": 2.0,
        "Daily schedule trips operate at least every 60 minutes. Additional weekday trips operate at least every 30 minutes between Erin and Brooks.": 1.0,
        "Weekday schedule trips operate limited service from approximately 7 AM until 8 AM and 3 PM until 5 PM. No trips operate during Public School Recess or on Public School Holidays.": 0.0,
        "Weekday schedule trips operate at least every 30 minutes from approximately 4 PM until 7 PM. Additional weekday schedule trips operate on Standard service days only from approximately 9 AM until 4 PM.": 0.0,
        "Daily schedule trips operate regularly every 30 minutes from approximately 6 PM until 2 AM. No trips operate during Campus Recess or on Holidays.": 0.0,
        "": 0.0,
    }

    def test_parser(self):
        for desc, want in self.CASES.items():
            with self.subTest(desc=desc[:50]):
                self.assertAlmostEqual(T.madison_trips_per_hour(desc), want)
        self.assertEqual(T.madison_trips_per_hour(None), 0.0)

    def test_only_15_minute_routes_pass_main_case(self):
        passes = {d for d, v in self.CASES.items() if T.qualifies(v, T.MAIN_N)}
        self.assertEqual(len(passes), 3)


class TestGtfsFrequency(unittest.TestCase):
    def test_representative_weekday_skips_removed_service(self):
        day = T.representative_weekday(table("trips.txt"), table("calendar.txt"), table("calendar_dates.txt"), dt.date(2026, 10, 26))
        self.assertEqual(day, dt.date(2026, 10, 28))  # Tue 27 Oct is removed in calendar_dates

    def test_expired_feed_scans_from_feed_start(self):
        day = T.representative_weekday(table("trips.txt"), table("calendar.txt"), table("calendar_dates.txt"), dt.date(2027, 6, 1))
        self.assertEqual(day, dt.date(2026, 10, 1))  # Thursday, first day of the feed

    def test_active_services(self):
        cal, cd = table("calendar.txt"), table("calendar_dates.txt")
        self.assertEqual(T.active_services(cal, cd, dt.date(2026, 10, 28)), {"WK"})
        self.assertEqual(T.active_services(cal, cd, dt.date(2026, 10, 27)), set())
        self.assertEqual(T.active_services(cal, cd, dt.date(2026, 10, 31)), {"SA"})

    def test_trip_start_uses_lowest_stop_sequence(self):
        hours = T.trip_start_hours(table("stop_times.txt"), {"late", "1a70"})
        self.assertEqual(hours, {"late": 6, "1a70": 7})

    def test_one_direction_rule(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            peaks, facts = T.gtfs_route_peaks(fixture_zip(Path(d)), dt.date(2026, 10, 26))
        # Route 1: 4 trips in each of 7:00 and 8:00 in direction 0 (route ids r1 and r1b pooled by name).
        # Route 2: 2 an hour in each direction; adding directions would give 4, the rule gives 2.
        # Route 3: 4 in the 7:00 hour but only 2 in the 8:00 hour. Saturday trips never count.
        self.assertEqual(peaks, {"1": 4, "2": 2, "3": 2})
        self.assertTrue(T.qualifies(peaks["1"], T.MAIN_N))
        self.assertFalse(T.qualifies(peaks["2"], T.HIGH_N))
        self.assertFalse(T.qualifies(peaks["3"], T.HIGH_N))
        self.assertEqual(facts["service_day"], "2026-10-28")
        self.assertEqual((facts["valid_from"], facts["valid_through"]), ("2026-10-01", "2026-12-31"))

    def test_feed_info_dates_win(self):
        lo, hi = T.feed_validity(table("calendar.txt"), [], [{"feed_start_date": "20260101", "feed_end_date": "20260630"}])
        self.assertEqual((lo, hi), (dt.date(2026, 1, 1), dt.date(2026, 6, 30)))


class TestRouteClassification(unittest.TestCase):
    def test_rapid_routes(self):
        self.assertTrue(T.is_rapid("50008", "3", "CN1"))
        self.assertTrue(T.is_rapid("50005", "3", "A"))
        self.assertFalse(T.is_rapid("50005", "3", "B"))      # Route B is not branded rapid
        self.assertTrue(T.is_rapid("55312", "3", ""))        # The Hop is coded as bus
        self.assertTrue(T.is_rapid("50003", "3", "SC"))      # Kenosha streetcar
        self.assertTrue(T.is_rapid("50003", "0", "X"))       # any rail route type
        self.assertFalse(T.is_rapid("50008", "3", "12"))

    def test_amtrak_excluded(self):
        self.assertTrue(T.is_excluded_agency("National Railroad Passenger Corporation (Amtrak)"))
        self.assertFalse(T.is_excluded_agency("Milwaukee County"))
        self.assertFalse(T.is_rapid("99999", "2", "Hiawatha", "Amtrak"))
        src = (ROOT / "scripts" / "fetch_tod_transit.py").read_text()
        self.assertNotIn("amtrak.com", src.lower())
        self.assertNotIn("NTAD_Amtrak_Stations", src)


class TestGeometry(unittest.TestCase):
    def setUp(self):
        import shapely
        self.shapely = shapely
        fc = json.loads((FIX / "routes_small.geojson").read_text())
        self.routes = [f["properties"] for f in fc["features"]]
        self.lines = [shapely.geometry.shape(f["geometry"]) for f in fc["features"]]
        self.stops = json.loads((FIX / "stops_small.json").read_text())
        self.points = [shapely.Point(s["x"], s["y"]) for s in self.stops]

    def _near(self, keep):
        idx = [i for i, r in enumerate(self.routes) if keep(r)]
        return T.stops_near_routes(self.points, [s["ntd_id"] for s in self.stops],
                                   [self.lines[i] for i in idx], [self.routes[i]["ntd_id"] for i in idx])

    def test_definitions_on_synthetic_routes(self):
        def freq(r):
            return T.madison_trips_per_hour(r["route_desc"]) if r["ntd_id"] == "50005" else 0.0
        a = self._near(lambda r: T.is_rapid(r["ntd_id"], r["route_type"], r["route_short_name"], r["agency_name"]))
        b = self._near(lambda r: T.qualifies(freq(r), T.MAIN_N)) | a
        c = self._near(lambda r: T.qualifies(freq(r), T.HIGH_N)) | a
        for i, s in enumerate(self.stops):
            with self.subTest(stop=s["stop_id"]):
                got = "".join(k for k, m in zip("abc", (a, b, c)) if m[i])
                self.assertEqual(got, s["expect"])

    def test_30_metre_tolerance(self):
        line = self.shapely.LineString([(0, 0), (100, 0)])
        pts = [self.shapely.Point(50, 29.9), self.shapely.Point(50, 30.1), self.shapely.Point(129, 0), self.shapely.Point(50, 5)]
        got = T.stops_near_routes(pts, ["x", "x", "x", "y"], [line], ["x"])
        self.assertEqual(got.tolist(), [True, False, True, False])  # last one: right place, other agency

    def test_homes_within_distance(self):
        quarter = 0.25 * T.MILE_M  # 402.336 m
        blocks = [self.shapely.Point(400, 0), self.shapely.Point(405, 0), self.shapely.Point(0, 700)]
        homes = [10, 20, 40]
        stop = [self.shapely.Point(0, 0)]
        self.assertEqual(T.homes_within(blocks, homes, stop, quarter), 10)
        self.assertEqual(T.homes_within(blocks, homes, stop, 0.5 * T.MILE_M), 70)
        self.assertEqual(T.homes_within(blocks, homes, [], quarter), 0)
        m = T.blocks_within_variable(blocks, [self.shapely.Point(0, 0), self.shapely.Point(0, 1000)], [quarter, 0.5 * T.MILE_M])
        self.assertEqual(m.tolist(), [True, False, True])


class TestCompliance(unittest.TestCase):
    MADISON_GTFS_MARKERS = ("transitdata.cityofmadison.com", "mmt_gtfs", "/GTFS/mmt")

    def test_madison_gtfs_never_referenced(self):
        import fetch_tod_transit as fetch
        self.assertNotIn(T.MADISON_NTD_ID, fetch.GTFS_FEEDS)
        for p in (ROOT / "scripts" / "fetch_tod_transit.py", ROOT / "scripts" / "build_tod_stops.py",
                  ROOT / "missing_middleware" / "tod" / "transit.py"):
            text = p.read_text().lower()
            for marker in self.MADISON_GTFS_MARKERS:
                with self.subTest(file=p.name, marker=marker):
                    self.assertNotIn(marker.lower(), text)
        for f in fetch.GTFS_FEEDS.values():
            for u in (f["url"], f.get("fallback") or ""):
                self.assertNotIn("cityofmadison", u)

    def test_mcts_fallback_documented(self):
        import fetch_tod_transit as fetch
        mcts = fetch.GTFS_FEEDS["50008"]
        self.assertIn("mcts.org", mcts["url"])
        self.assertIn("mobilitydatabase.org/mdb-2127", mcts["fallback"])
        self.assertIn("not sponsored by MCTS", mcts["terms"])


class TestCommittedOutputs(unittest.TestCase):
    def setUp(self):
        import pandas as pd
        self.summary = pd.read_csv(REF / "tod_definition_summary.csv").set_index("definition")
        self.muni = pd.read_csv(REF / "tod_near_stop_homes_by_muni.csv", dtype={"area_id": str})
        self.stops = pd.read_csv(REF / "tod_stops.csv", dtype={"ntd_id": str, "stop_id": str})

    def test_main_total_equals_sum_over_munis(self):
        for k in ("main", "high", "rapid_half", "b_half", "c_half", "any_half"):
            with self.subTest(definition=k):
                self.assertEqual(int(self.summary.loc[k, "homes"]), int(self.muni[f"homes_near_{k}"].sum()))
        self.assertEqual(int(self.summary.loc["main", "state_homes_2020"]), int(self.muni["homes_2020"].sum()))

    def test_ladder_is_ordered(self):
        h = self.summary["homes"]
        self.assertLessEqual(h["rapid_half"], h["main"])
        self.assertLessEqual(h["main"], h["high"])
        self.assertLessEqual(h["main"], h["b_half"])
        self.assertLessEqual(h["b_half"], h["c_half"])
        self.assertLessEqual(h["c_half"], h["any_half"])
        self.assertTrue((self.muni["homes_near_main"] <= self.muni["homes_2020"]).all())

    def test_stop_file_matches_summary(self):
        self.assertEqual(int(self.stops["flag_a_rapid"].sum()), int(self.summary.loc["rapid_half", "stops"]))
        self.assertEqual(int(self.stops["flag_b_15min"].sum()), int(self.summary.loc["main", "stops"]))
        self.assertEqual(len(self.stops), int(self.summary.loc["high", "stops"]))
        self.assertTrue(self.muni["area_id"].str.match(r"^muni:55\d{8}$").all())
        # coordinates are rounded to 5 decimal places
        for c in ("lat", "lon"):
            self.assertTrue((self.stops[c].round(5) == self.stops[c]).all())


if __name__ == "__main__":
    unittest.main()

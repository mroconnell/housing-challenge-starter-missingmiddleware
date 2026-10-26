"""Madison TOD overlay test: parsing, permit selection and judging (no geography, no network)."""
import re
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.tod import cases as K
from missing_middleware.tod import madison_test as T

REF = Path(__file__).resolve().parents[1] / "reference"


class TestMadisonTest(unittest.TestCase):


    def test_periods_match_the_prereg(self):
        assert T.BEFORE == [2017, 2018, 2019, 2020, 2021, 2022]
        assert T.AFTER == [2023, 2024, 2025]
        assert T.SHOWN == [2026]
        assert T.AFTER_ROUTE_A == [2024, 2025]


    def test_committed_prediction_is_unchanged(self):
        p = pd.read_csv(REF / "tod_madison_test_predictions.csv")
        a = p[(p.method == "A") & p.variant.str.startswith("main")].iloc[0]
        assert (a.prediction, a.interval90_low, a.interval90_high, a.dose_added_far) == (T.PRED, T.PRED_LOW, T.PRED_HIGH, T.DOSE_OVERLAY)


    def test_map_amendment_filter(self):
        assert T.is_map_amendment("Creating Section 28.022-00729 of the Madison General Ordinances to change the zoning")
        assert T.is_map_amendment("creating Section 28.022 -- 00289 of the Madison General Ordinances")
        assert not T.is_map_amendment("Amending Sections 28.022(3)(b), (c) and 28.022(5) to update numerical references")


    def test_window_rezonings_keeps_passed_map_amendments_in_window(self):
        title = "Creating Section 28.022-00001 of the Madison General Ordinances to change the zoning of property"
        ms = [
            {"MatterId": 1, "MatterStatusName": "Passed", "MatterEnactmentDate": "2019-05-01T00:00:00", "MatterTitle": title},
            {"MatterId": 2, "MatterStatusName": "Passed", "MatterEnactmentDate": "2016-05-01T00:00:00", "MatterTitle": title},
            {"MatterId": 3, "MatterStatusName": "Filed", "MatterEnactmentDate": "2019-05-01T00:00:00", "MatterTitle": title},
            {"MatterId": 4, "MatterStatusName": "Passed", "MatterEnactmentDate": None, "MatterPassedDate": "2025-12-30T00:00:00", "MatterTitle": title},
            {"MatterId": 5, "MatterStatusName": "Passed", "MatterEnactmentDate": "2026-01-02T00:00:00", "MatterTitle": title},
        ]
        assert list(T.window_rezonings(ms).matter_id) == [1, 4]


    def test_address_text_and_split(self):
        t = ("Creating Section 28.022-00729 of the Madison General Ordinances to change the zoning of property located at "
             "1233-1241 Moorland Road from SR-C1 (Suburban Residential-Consistent 1) District to A (Agricultural) District.")
        assert T.address_text(t) == "1233-1241 Moorland Road"
        t2 = ("Creating Section 28.022-00600 ... rezoning property located at 405-407 & 311 West Gorham Street, "
              "408-430 West Johnson Street, 304-318 North Broom Street, 4th Alder District, from DR2 to PD")
        assert T.split_addresses(T.address_text(t2)) == [
            "405-407 West Gorham Street", "311 West Gorham Street", "408-430 West Johnson Street", "304-318 North Broom Street"]
        assert T.split_addresses("1753,1754,  1798, and 1799 Thierer Road; 1745 Parkside Drive") == [
            "1753 Thierer Road", "1754 Thierer Road", "1798 Thierer Road", "1799 Thierer Road", "1745 Parkside Drive"]
        assert T.split_addresses("2002 Tennyson Lane/3804 Packers Avenue") == ["2002 Tennyson Lane", "3804 Packers Avenue"]
        assert T.address_text("Town of Madison properties generally bounded by the Beltline", "Town of Madison Zoning Area 6") == ""


    def test_range_bounds_and_nearest_number(self):
        assert T.range_bounds("754-904 Felland Road") == (754, 904)
        assert T.range_bounds("301 Cross Oaks Drive") is None
        ref = pd.DataFrame({"street_key": ["FELLAND RD"] * 3 + ["OTHER ST"], "house_nbr": [700, 760, 1000, 755]})
        assert T.nearest_on_street(ref, "FELLAND RD", 754) == 1
        assert T.nearest_on_street(ref, "FELLAND RD", 880) is None  # nearest is 120 away, beyond the 50 limit
        assert T.nearest_on_street(ref, "NOPE ST", 1) is None


    def test_test_permits_selects_types_dedupes_and_keeps_window(self):
        raw = pd.DataFrame({
            "permit_id": ["BLDNCC-2020-1", "BLDNCC-2020-1", "BLDNRC-2018-2", "BLDADD-2019-3", "BLDNCC-2016-4", "BLDNRC-2021-5"],
            "permit_type": ["BLDNCC", "BLDNCC", "BLDNRC", "BLDADD", "BLDNCC", "BLDNRC"],
            "issue_date": pd.to_datetime(["2020-03-01", "2021-01-05", "2018-06-01", "2019-01-01", "2016-01-01", "2021-02-02"]),
            "units_raw": [100, 100, 2, 4, 50, 0],
            "source_file": ["a"] * 6, "source_row": range(6), "address_raw": ["x"] * 6,
        })
        d = T.test_permits(raw)
        assert sorted(d.permit_id) == ["BLDNCC-2020-1", "BLDNRC-2018-2"]
        assert d.set_index("permit_id").loc["BLDNCC-2020-1", "year"] == 2020  # earliest issue date
        assert d.units.sum() == 102


    def test_project_ids_and_street_only(self):
        p = T.project_ids(pd.Series(["10|MAIN ST", "10|MAIN ST", "12|MAIN ST"]), pd.Series([2020, 2020, 2021]))
        assert p.nunique() == 2
        assert T.street_only("1234-1240 University Ave Unit 5") == "UNIVERSITY AVE"
        assert T.street_only("12 E Main St") == "E MAIN ST"


    def test_estimate_and_judge(self):
        rows = []
        for y in T.BEFORE:
            rows += [("t1", K.TREAT, y, 10.0), ("c1", K.COMP, y, 10.0)]
        for y in T.AFTER:
            rows += [("t2", K.TREAT, y, 40.0), ("c1", K.COMP, y, 10.0)]
        p = pd.DataFrame(rows, columns=["project", "area", "year", "units"])
        e = T.estimate(p, {K.TREAT: 100.0, K.COMP: 100.0}, interval=False)
        assert abs(e["did"] - 0.3) < 1e-12
        assert T.judge(0.25, 0.1, 0.4).startswith("confirmed")
        assert "above" in T.judge(0.5, 0.1, 0.4)
        assert "below" in T.judge(0.05, 0.1, 0.4)
        assert T.judge(0.2, np.nan, 0.4) == "no interval"


    def test_results_file_has_no_identifiers(self):
        for f in ("tod_madison_test_results.csv", "tod_madison_test_rates_by_year.csv", "tod_madison_test_unmatched.csv"):
            txt = (REF / f).read_text()
            assert not re.search(r"BLD[A-Z]{3}-\d{4}-\d+", txt), f
            assert not re.search(r"\b\d{12}\b", txt), f  # Madison parcel numbers
        u = pd.read_csv(REF / "tod_madison_test_unmatched.csv")
        assert not u.street.astype(str).str.match(r"^\d").any()


if __name__ == "__main__":
    unittest.main()

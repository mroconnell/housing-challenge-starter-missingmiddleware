"""Synthetic-lot tests for the parking lot-fit test (scripts/run_parking_lotfit.py; docs/parking/LOT_FIT_PLAN.md).

No real parcels are read: lots are made up, and rules come from reference/parking_lotfit_rules.csv."""
from __future__ import annotations

import math
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import run_parking_lotfit as LF  # noqa: E402

R = LF.Rules(LF.load_rules())
FT = 0.3048


def rid(place, district, prov, value):
    """The variant group holding this span-variant row."""
    d = R.df
    m = (d.place == place) & (d.district == district) & (d.provision == prov) & (d.value == value) & (d.use == "span_variant")
    assert m.sum() == 1, (place, district, prov, value, int(m.sum()))
    return LF.variant_group(next(d[m].itertuples(index=False)))


class RulesTable(unittest.TestCase):
    def test_every_place_has_an_as_if_district_with_dimensions(self):
        for place in LF.PLACES:
            for n in LF.UNITS:
                d = R.as_if_district(place, n)
                p = LF.resolve(R, place, d, n)
                self.assertGreater(p.min_width + p.min_area, 0, (place, d, n))
                self.assertGreater(p.front + p.rear, 0, (place, d, n))

    def test_used_rows_are_sourced_and_gaps_carry_no_value(self):
        d = R.df
        used = d[d.use.isin(["central", "span_variant"])]
        self.assertTrue((used.status != "").all())
        self.assertTrue(((used.source_doc != "") | (used.source_url != "") | (used.place == "*")).all())
        code = used[used.status == "verified"]
        self.assertTrue((code.source_section != "").all())
        bad = d[d.status.isin(["not_found", "blocked"]) & (d.use != "gap") & (d.provision != "tandem_counts")
                & (d.provision != "driveway_counts") & (d.provision != "setback_parking_rear")
                & (d.provision != "setback_parking_side") & (d.provision != "front_yard_parking")]
        self.assertTrue(bad.empty, bad[["place", "district", "provision", "value"]].to_string())

    def test_garage_size_is_labelled_an_assumption(self):
        d = R.df
        g = d[d.provision.isin(["enclosed_stall_width_ft", "enclosed_stall_depth_ft"])]
        self.assertEqual(set(g.value), {"12", "22"})
        self.assertTrue((g.status == "assumption").all())

    def test_audit_named_as_if_districts(self):
        want = {"Green Bay": "R-1", "Kenosha": "RS-3", "Racine": "R2", "Janesville": "R1"}
        for place, d in want.items():
            self.assertEqual(R.as_if_district(place, 3), d)

    def test_no_conflicting_central_rows(self):
        # get() raises on ties with different values; resolve every place/district/unit/condition combination
        conds = [frozenset(), frozenset({"alley"}), frozenset({"corner"}), frozenset({"tod_overlay"}),
                 frozenset({"lot_area_le_7500", "small_lot_w60_d100"})]
        for place in LF.PLACES:
            for d in R.districts(place) | {"*"}:
                for n in LF.UNITS:
                    for c in conds:
                        LF.resolve(R, place, d, n, c)


class Resolve(unittest.TestCase):
    def test_milwaukee_two_units_have_no_minimum(self):
        p = LF.resolve(R, "Milwaukee", "RT4", 2)
        self.assertEqual(p.stalls, 0)
        lot = LF.Lot(30 * 120, 30, 120)
        self.assertEqual(LF.fit_lot(lot, p), (LF.FITS, "no_minimum"))

    def test_milwaukee_rt4_ratio_rounds_up(self):
        self.assertEqual(LF.resolve(R, "Milwaukee", "RT4", 4).stalls, 3)     # 2.67 rounded up (plan 3.5)
        self.assertFalse(LF.resolve(R, "Milwaukee", "RT4", 4).tandem)          # code: no tandem, no drive stalls

    def test_green_bay_garages_stall_size_and_tandem_by_units(self):
        p3 = LF.resolve(R, "Green Bay", "R-1", 3)
        self.assertEqual((p3.stalls, p3.enclosed, p3.stall_w, p3.stall_d), (6, 3, 8.0, 15.0))
        self.assertTrue(p3.tandem)
        p2 = LF.resolve(R, "Green Bay", "R-1", 2)
        self.assertFalse(p2.tandem)
        self.assertFalse(p2.drive_counts)

    def test_condition_rows_win(self):
        self.assertEqual(LF.resolve(R, "Madison", "TR-V1", 3, frozenset({"tod_overlay"})).stalls, 0)
        self.assertEqual(LF.resolve(R, "Madison", "TR-V1", 3).stalls, 3)
        self.assertEqual(LF.resolve(R, "Eau Claire", "GR", 2, frozenset({"alley"})).min_width, 40)
        self.assertEqual(LF.resolve(R, "Eau Claire", "GR", 2).min_width, 50)
        self.assertEqual(LF.resolve(R, "Milwaukee", "RT4", 3, frozenset({"corner"})).cov_cap, 0.85)
        self.assertTrue(LF.units_allowed(R, "Madison", "TR-C2", 4, frozenset({"tod_overlay"})))
        self.assertFalse(LF.units_allowed(R, "Madison", "TR-C2", 4))

    def test_plan_geometry_variant_only_where_code_is_silent(self):
        v = rid("*", "*", "stall_width_ft", "8.5")
        self.assertEqual(LF.resolve(R, "Green Bay", "R-1", 3, variant=v).stall_w, 8.0)    # code sets 8 ft
        self.assertEqual(LF.resolve(R, "Kenosha", "RS-3", 3, variant=v).stall_w, 8.5)     # code silent

    def test_no_tandem_variant_applies_everywhere(self):
        v = rid("*", "*", "tandem_counts", "no")
        p = LF.resolve(R, "Green Bay", "R-1", 4, variant=v)
        self.assertFalse(p.tandem)
        self.assertFalse(p.drive_counts)

    def test_driveway_never_below_code_minimum(self):
        v = rid("*", "*", "driveway_width_ft", "8")
        self.assertEqual(LF.resolve(R, "Waukesha", "RN-2", 3, variant=v).drive_w, 12.0)
        self.assertEqual(LF.resolve(R, "Waukesha", "RN-2", 3).drive_w, 12.0)
        self.assertEqual(LF.resolve(R, "Waukesha", "RN-2", 2, variant=v).drive_w, 8.0)

    def test_floors_never_above_cap(self):
        p = LF.resolve(R, "Green Bay", "R-1", 3)          # 2.5 stories: 3 planned floors become 2
        self.assertEqual(LF.floors_used(p), 2)
        self.assertEqual(LF.floors_used(LF.resolve(R, "Kenosha", "RS-3", 3)), 3)   # 35 ft / 11 ft = 3


class FitTest(unittest.TestCase):
    def test_too_small_lot_is_other_rules(self):
        p = LF.resolve(R, "Kenosha", "RS-3", 4)          # 3,000 sq ft per unit
        self.assertEqual(LF.fit_lot(LF.Lot(40 * 125, 40, 125), p), (LF.OTHER, "lot_area"))

    def test_large_lot_fits(self):
        p = LF.resolve(R, "Kenosha", "RS-3", 3)          # 6 stalls, no tandem: cross-aisle row of 6
        self.assertEqual(LF.fit_lot(LF.Lot(60 * 150, 60, 150), p)[0], LF.FITS)

    def test_parking_blocks_by_impervious_cap(self):
        p = LF.resolve(R, "Green Bay", "R-1", 4)         # 8 stalls, 4 garages, 50% impervious
        cls, why = LF.fit_lot(LF.Lot(60 * 140, 60, 140), p)
        self.assertEqual(cls, LF.PARKING)
        self.assertEqual(LF.fit_lot(LF.Lot(60 * 140, 60, 140), replace(p, stalls=0, enclosed=0))[0], LF.FITS)

    def test_alley_changes_the_answer(self):
        p_alley = LF.resolve(R, "Eau Claire", "GR", 2, frozenset({"alley"}))
        p_none = LF.resolve(R, "Eau Claire", "GR", 2)
        self.assertEqual(LF.fit_lot(LF.Lot(40 * 110, 40, 110, alley=True), p_alley)[0], LF.FITS)
        self.assertEqual(LF.fit_lot(LF.Lot(40 * 110, 40, 110), p_none), (LF.OTHER, "lot_width"))

    def test_driveway_can_squeeze_the_building(self):
        p = replace(LF.resolve(R, "Kenosha", "RS-3", 2), min_width=0, min_area=0)
        # 30 ft lot: 20 ft buildable; a 10 ft drive in a 5 ft side yard leaves 15 ft < 20 ft minimum building width
        self.assertEqual(LF.fit_lot(LF.Lot(30 * 150, 30, 150), p), (LF.PARKING, "driveway_squeezes_building"))
        self.assertEqual(LF.fit_lot(LF.Lot(30 * 150, 30, 150, alley=True), p)[0], LF.FITS)

    def test_tandem_counting_matters(self):
        base = replace(LF.resolve(R, "Waukesha", "RN-2", 2), drive_counts=False)
        lot = LF.Lot(40 * 92, 40, 92)                    # 4 stalls; 37 ft behind the building: a tandem pair, no aisle row
        p = replace(base, min_width=0, min_area=0)
        self.assertEqual(LF.fit_lot(lot, replace(p, tandem=True))[0], LF.FITS)
        self.assertEqual(LF.fit_lot(lot, replace(p, tandem=False))[0], LF.PARKING)

    def test_alley_never_worse_than_no_alley(self):
        rng = np.random.default_rng(11)
        for place in LF.PLACES:
            for n in LF.UNITS:
                d = R.as_if_district(place, n)
                p = LF.resolve(R, place, d, n)                   # same rules both ways: only the access differs
                for w, dp in zip(rng.uniform(25, 120, 60), rng.uniform(80, 220, 60)):
                    without = LF.fit_lot(LF.Lot(w * dp, w, dp), p)[0]
                    with_alley = LF.fit_lot(LF.Lot(w * dp, w, dp, alley=True), p)[0]
                    if without == LF.FITS:
                        self.assertEqual(with_alley, LF.FITS, (place, n, w, dp))

    def test_rear_setback_lesser_of(self):
        p = LF.resolve(R, "Madison", "TR-V1", 2)          # lesser of 25% of depth or 25 ft
        self.assertAlmostEqual(min(p.rear, p.rear_pct * 80), 20.0)

    def test_rear_setback_parking_variant(self):
        p = replace(LF.resolve(R, "Waukesha", "RN-2", 2), min_area=0, min_width=0)
        lot = LF.Lot(40 * 95, 40, 95)
        self.assertEqual(LF.fit_lot(lot, p)[0], LF.FITS)
        self.assertEqual(LF.fit_lot(lot, replace(p, park_rear_setback=False))[0], LF.PARKING)


class Zoning(unittest.TestCase):
    def test_madison_base_district(self):
        coded = R.districts("Madison")
        self.assertEqual(LF.madison_base_district("WP-27, TR-V1, HIS-UH", coded), "TR-V1")
        self.assertEqual(LF.madison_base_district("HIS-TL, TR-V1", coded), "TR-V1")
        self.assertEqual(LF.madison_base_district("WP-27, PD", coded), "PD")
        self.assertEqual(LF.madison_base_district(None, coded), "")
        self.assertEqual(LF.madison_base_district(float("nan"), coded), "")


class Geometry(unittest.TestCase):
    def rect(self, x0, y0, w, d):
        r = np.array([[x0, y0], [x0 + w, y0], [x0 + w, y0 + d], [x0, y0 + d], [x0, y0]], float)
        return [[r]]

    def test_lot_shapes(self):
        sh = LF.lot_shapes([self.rect(500000, 300000, 10, 40), self.rect(500100, 300000, 20, 20)])
        self.assertAlmostEqual(sh.width_ft[0], 10 / FT, places=3)
        self.assertAlmostEqual(sh.depth_ft[0], 40 / FT, places=3)
        self.assertAlmostEqual(sh.fill[0], 1.0, places=6)
        self.assertAlmostEqual(abs(sh.uy[0]), 1.0, places=6)     # depth axis runs along the long side

    def test_alley_in_rear_half_only(self):
        lots = [self.rect(0, 0, 10, 40), self.rect(20, 0, 10, 40)]
        sh = LF.lot_shapes(lots)
        street = [[np.array([[-50.0, -3.0], [100.0, -3.0]])]]                 # street along the front (y = -3)
        rear_alley = [[np.array([[-50.0, 43.0], [15.0, 43.0]])]]              # behind lot 1 only
        f = LF.alley_flags(lots, sh, rear_alley, street)
        self.assertEqual(list(f), [True, False])
        front_alley = [[np.array([[-50.0, -2.0], [100.0, -2.0]])]]            # alley on the street side: not rear
        self.assertEqual(list(LF.alley_flags(lots, sh, front_alley, street)), [False, False])


class Pipeline(unittest.TestCase):
    def test_synthetic_place_run_and_labels(self):
        lots = LF.synthetic_lots("Milwaukee", n=120, seed=3)
        rows = pd.DataFrame(LF.run_place("Milwaukee", lots, R))
        self.assertEqual(set(rows.version), {"main", "as_if"})
        self.assertEqual(set(rows.alley_bound), set(LF.ALLEY_BOUNDS))
        c2 = rows[(rows.variant == "central") & (rows.split == "regular lots")].pivot_table(
            index=["version", "units"], columns="alley_bound", values="parking_blocks")
        lo, hi = "lower bound: every lot has an alley", "upper bound: no lot has an alley"
        self.assertTrue((c2[lo] <= c2[hi]).all())                              # an alley never adds blocking here
        c = rows[(rows.variant == "central") & (rows.split == "regular lots")]
        self.assertTrue(((c.parking_blocks <= c.fit_without_parking) & (c.fit_without_parking <= c.lots)).all())
        two = c[c.units == 2]
        self.assertTrue((two.parking_blocks == 0).all())                       # no minimum for 2 units
        sp = LF.spans(pd.concat([rows, LF.pooled(rows)], ignore_index=True))
        self.assertTrue((sp.span_label == LF.SPAN_LABEL).all())
        ok = sp.dropna(subset=["central_share"])
        self.assertTrue(((ok.span_low <= ok.central_share + 1e-12) & (ok.central_share <= ok.span_high + 1e-12)).all())

    def test_sanity_label_rule(self):
        lots = LF.synthetic_lots("Milwaukee", n=80, seed=5)
        lots["NR_UNITS"] = "2"
        lots["PARKING_SPACES"] = "40"                                          # absurd: nothing can fit 40 stalls
        s = LF.sanity_milwaukee(lots, R)
        rec = s[(s.basis == "recorded spaces") & (s.units == "2-4")].iloc[0]
        self.assertGreater(rec.share_could_not_fit, 0.5)
        self.assertEqual(rec.label, LF.SANITY_LABEL)
        rule = s[(s.basis == "modelled rules") & (s.units == "2-4")].iloc[0]
        self.assertEqual(int(rule.of_which_parking), 0)                        # 2 units: no minimum in Milwaukee
        lots["PARKING_SPACES"] = np.nan                                        # as in the MPROP file on disk
        s = LF.sanity_milwaukee(lots, R)
        rec = s[(s.basis == "recorded spaces") & (s.units == "2-4")].iloc[0]
        self.assertEqual(int(rec.existing_buildings), 0)
        self.assertTrue(rec.label.startswith("not computable"))

    def test_pooled_is_lot_weighted(self):
        rows = []
        for place, (blocks, fit) in {"A": (1, 10), "B": (9, 30)}.items():
            rows.append({"place": place, "alley_bound": "b", "version": "as_if", "units": 2, "split": "regular lots", "variant": "central",
                         "lots": fit + 5, "other_rules_block": 5, "fit_without_parking": fit,
                         "parking_blocks": blocks, "share_parking_blocks": blocks / fit, "share_other_rules_block": 0})
        p = LF.pooled(pd.DataFrame(rows))
        self.assertAlmostEqual(float(p.share_parking_blocks.iloc[0]), 10 / 40)

    def test_real_run_needs_go_and_synthetic_never_writes_reference(self):
        with self.assertRaises(SystemExit):
            LF.main([])
        with self.assertRaises(SystemExit):
            LF.main(["--synthetic", "--out", str(LF.REFERENCE)])

    def test_synthetic_cli_writes_outputs(self):
        with tempfile.TemporaryDirectory() as t:
            LF.main(["--synthetic", "--places", "Racine", "--workers", "1", "--out", t])
            self.assertTrue((Path(t) / "parking_lotfit_shares.csv").exists())
            self.assertTrue((Path(t) / "parking_lotfit_spans.csv").exists())


if __name__ == "__main__":
    unittest.main()

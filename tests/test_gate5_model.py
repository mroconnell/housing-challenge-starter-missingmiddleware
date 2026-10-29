"""Gate 5 model outputs: unknown-rules variants, legislative-district allocation and reconciliation.

Reads the committed reference tables (offline); the function tests use small synthetic frames.
"""
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
sys.path.insert(0, str(ROOT / "scripts"))

import build_district_allocation as bd  # noqa: E402
import run_unknown_rules_variants as uv  # noqa: E402

PATHS = ("lower", "central", "upper")
YEARS = [str(y) for y in range(2027, 2032)]
STATE_HOMES = 1_839_569


class TestUnknownRulesFunctions(unittest.TestCase):
    AREAS = pd.DataFrame([
        {"area_id": "a", "homes": 1000, "x_rate": 0.06, "at_benchmark": False, "x_basis": uv.UNCODED},
        {"area_id": "b", "homes": 2000, "x_rate": 0.03, "at_benchmark": False, "x_basis": "prohibited_group_rate"},
        {"area_id": "c", "homes": 500, "x_rate": 0.19, "at_benchmark": True, "x_basis": "observed"},
    ])
    RATES = {"prohibited": 0.03, "restricted": 0.06, "benchmark": 0.19}

    def test_adopted_variant_changes_nothing(self):
        pd.testing.assert_frame_equal(uv.variant_areas(self.AREAS, "like_restricted", self.RATES), self.AREAS)

    def test_variants_change_only_uncoded_areas(self):
        for t, (group, _, at_bm, _) in uv.VARIANTS.items():
            a = uv.variant_areas(self.AREAS, t, self.RATES)
            self.assertAlmostEqual(a.loc[0, "x_rate"], self.RATES[group])
            if t != "like_restricted":
                self.assertEqual(bool(a.loc[0, "at_benchmark"]), at_bm)
            pd.testing.assert_frame_equal(a.iloc[1:], self.AREAS.iloc[1:])

    def test_contract_enum_named(self):
        enums = {v[1].split()[0] for v in uv.VARIANTS.values()}
        self.assertTrue({"all_prohibited", "all_compliant"} <= enums)


class TestUnknownRulesOutputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = pd.read_csv(REF / "adu_model_unknown_rules_statewide.csv")
        cls.adopted = pd.read_csv(REF / "adu_model_statewide.csv").set_index("path")

    def row(self, t, p):
        return self.st[self.st.unknown_treatment.eq(t) & self.st.path.eq(p)].iloc[0]

    def test_one_run_group_three_variants(self):
        self.assertEqual(self.st.run_group_id.nunique(), 1)
        self.assertEqual(set(self.st.unknown_treatment), set(uv.VARIANTS))
        self.assertEqual(len(self.st), 9)
        self.assertEqual(self.st[self.st.adopted].unknown_treatment.unique().tolist(), ["like_restricted"])

    def test_adopted_variant_equals_adopted_model(self):
        for p in PATHS:
            r = self.row("like_restricted", p)
            self.assertAlmostEqual(r.baseline_units, self.adopted.loc[p, "baseline_units"], places=3)
            self.assertAlmostEqual(r.additional_units, self.adopted.loc[p, "additional_units"], places=3)

    def test_like_prohibited_matches_earlier_finding(self):
        r = self.row("like_prohibited", "central")
        # AQ-061: the measured cities lowered the prohibited group rate (0.0313 -> 0.0233) and the restricted one
        # (0.0607 -> 0.0515), so the switch moves the baseline a little less than at Gate 5 (-186.36)
        self.assertAlmostEqual(r.d_baseline_units, -178.34, delta=0.05)
        self.assertAlmostEqual(r.d_additional_units, 153.9, delta=0.5)     # AQ-064 refit (AQ-061: 152.2)
        self.assertAlmostEqual(r.d_total_with_law, -24.4, delta=0.5)

    def test_totals_and_ordering(self):
        for t in uv.VARIANTS:
            rs = {p: self.row(t, p) for p in PATHS}
            for r in rs.values():
                self.assertAlmostEqual(r.total_with_law, r.baseline_units + r.additional_units, places=2)
            self.assertLessEqual(rs["lower"].additional_units, rs["central"].additional_units)
            self.assertLessEqual(rs["central"].additional_units, rs["upper"].additional_units)
        # baseline rises with the uncoded places' current-law rate
        b = [self.row(t, "central").baseline_units for t in ("like_prohibited", "like_restricted", "like_benchmark")]
        self.assertEqual(b, sorted(b))

    def test_groupings_reconcile_to_state(self):
        for fn, key in (("by_county", "parent_county_id"), ("by_context", "context_group")):
            g = pd.read_csv(REF / f"adu_model_unknown_rules_{fn}.csv")
            s = g.groupby(["unknown_treatment", "path"])[["baseline_units", "additional_units"]].sum()
            for (t, p), r in s.iterrows():
                st = self.row(t, p)
                self.assertAlmostEqual(r.baseline_units, st.baseline_units, delta=0.05, msg=fn)
                self.assertAlmostEqual(r.additional_units, st.additional_units, delta=0.1, msg=fn)
            h = g[g.path.eq("central")].groupby("unknown_treatment").homes.sum()
            self.assertTrue((h == STATE_HOMES).all(), fn)

    def test_by_area_reconciles(self):
        a = pd.read_csv(REF / "adu_model_unknown_rules_by_area.csv")
        for t, g in a.groupby("unknown_treatment"):
            self.assertEqual(len(g), 1925)
            self.assertAlmostEqual(g.baseline.sum(), self.row(t, "central").baseline_units, delta=1.0)
            for p in PATHS:
                self.assertAlmostEqual(g[f"additional_{p}"].sum(), self.row(t, p).additional_units, delta=1.5)


class TestAllocateFunction(unittest.TestCase):
    def test_split_and_unallocated_row(self):
        vals = pd.DataFrame({"area_id": ["m1", "m2", "m3"], "path": ["central"] * 3, "v": [10.0, 4.0, 1.0]})
        shares = pd.DataFrame({"area_id": ["m1", "m1", "m2"], "district": [1, 2, 2], "share": [0.25, 0.75, 1.0]})
        out = bd.allocate(vals, shares, ["path"]).set_index("district")["v"]
        self.assertAlmostEqual(out["1"], 2.5)
        self.assertAlmostEqual(out["2"], 11.5)
        self.assertAlmostEqual(out[bd.UNALLOCATED], 1.0)       # m3 has no share
        self.assertAlmostEqual(out.sum(), 15.0)

    def test_no_keys(self):
        vals = pd.DataFrame({"area_id": ["m1"], "homes": [100.0]})
        shares = pd.DataFrame({"area_id": ["m1", "m1"], "district": [3, 4], "share": [0.4, 0.6]})
        out = bd.allocate(vals, shares, []).set_index("district")["homes"]
        self.assertAlmostEqual(out["3"], 40.0)
        self.assertAlmostEqual(out[bd.UNALLOCATED], 0.0)


class TestDistrictOutputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asm = pd.read_csv(REF / "adu_model_by_assembly_district.csv", dtype={"district": str})
        cls.sen = pd.read_csv(REF / "adu_model_by_senate_district.csv", dtype={"district": str})
        cls.state = pd.read_csv(REF / "adu_model_statewide.csv").set_index("path")
        by = pd.read_csv(REF / "adu_model_statewide_by_year.csv")
        by["forecast_year"] = (2026 + by.year).astype(str)
        cls.by_year = by.set_index(["path", "forecast_year"])

    def test_district_counts_and_unallocated_row(self):
        for t, n in ((self.asm, 99), (self.sen, 33)):
            d = set(t.district)
            self.assertIn(bd.UNALLOCATED, d)
            self.assertEqual(len(d - {bd.UNALLOCATED}), n)
            self.assertEqual(sorted(int(x) for x in d - {bd.UNALLOCATED}), list(range(1, n + 1)))
            self.assertEqual(len(t), (n + 1) * 3 * 6)

    def test_reconcile_every_path_and_year(self):
        for name, t in (("assembly", self.asm), ("senate", self.sen)):
            g = t.groupby(["path", "forecast_year"])[["baseline_units", "additional_units"]].sum()
            for p in PATHS:
                for y in YEARS:
                    for c in ("baseline_units", "additional_units"):
                        self.assertAlmostEqual(g.loc[(p, y), c], self.by_year.loc[(p, y), c], delta=0.02, msg=(name, p, y, c))
                for c in ("baseline_units", "additional_units"):
                    self.assertAlmostEqual(g.loc[(p, "2027-2031"), c], self.state.loc[p, c], delta=0.05, msg=(name, p, c))

    def test_homes_sum_to_state(self):
        for t in (self.asm, self.sen):
            h = t[t.path.eq("central") & t.forecast_year.eq("2027-2031")].homes.sum()
            self.assertAlmostEqual(h, STATE_HOMES, delta=1.0)

    def test_unallocated_is_zero(self):
        for t in (self.asm, self.sen):
            u = t[t.district.eq(bd.UNALLOCATED)]
            self.assertLess(u[["baseline_units", "additional_units", "homes"]].abs().max().max(), 0.01)

    def test_senate_is_sum_of_its_assembly_districts(self):
        cw = pd.read_csv(REF / "adu_model_district_crosswalk.csv")
        sen_of = cw.drop_duplicates("assembly_district").set_index("assembly_district").senate_district
        self.assertEqual(sorted(sen_of.value_counts().unique().tolist()), [3])
        a = self.asm[self.asm.district.ne(bd.UNALLOCATED) & self.asm.forecast_year.eq("2027-2031")].copy()
        a["senate"] = a.district.astype(int).map(sen_of).astype(str)
        s = a.groupby(["senate", "path"])[["additional_units", "baseline_units"]].sum()
        t = self.sen[self.sen.forecast_year.eq("2027-2031") & self.sen.district.ne(bd.UNALLOCATED)].set_index(["district", "path"])
        for k, r in s.iterrows():
            self.assertAlmostEqual(r.additional_units, t.loc[k, "additional_units"], delta=0.01)

    def test_crosswalk_shares_sum_to_one(self):
        cw = pd.read_csv(REF / "adu_model_district_crosswalk.csv")
        s = cw.groupby("area_id").share.sum()
        self.assertLess((s - 1).abs().max(), 1e-5)
        self.assertTrue(cw.share.between(0, 1).all())
        self.assertAlmostEqual(cw.homes_allocated.sum(), STATE_HOMES, delta=1.0)
        self.assertFalse(cw.columns.str.contains("owner|address", case=False).any())

    def test_rates_consistent(self):
        t = self.asm[self.asm.forecast_year.eq("2027-2031") & self.asm.district.ne(bd.UNALLOCATED)]
        r = t.additional_units / 5 / t.homes * 1000
        self.assertLess((r - t.additional_per_1000_homes_per_year).abs().max(), 1e-3)


class TestGate5Checks(unittest.TestCase):
    def test_trace_reconciles(self):
        tr = pd.read_csv(REF / "gate5_trace.csv")
        allr = tr[tr.x_status.eq("all") & tr.context.eq("all")].iloc[0]
        st = pd.read_csv(REF / "adu_model_statewide.csv").set_index("path")
        self.assertAlmostEqual(allr.additional_central_5yr, st.loc["central", "additional_units"], delta=0.01)
        parts = tr[tr.x_status.ne("all") & tr.context.ne("all")]
        self.assertAlmostEqual(parts.additional_central_5yr.sum(), allr.additional_central_5yr, delta=0.05)
        self.assertAlmostEqual(parts.homes.sum(), STATE_HOMES, delta=1.0)

    def test_context_contrast_reconciles(self):
        cc = pd.read_csv(REF / "gate5_context_contrast.csv").set_index("context")
        parts = cc.drop(index="state")
        self.assertAlmostEqual(parts.additional_central_5yr.sum(), cc.loc["state", "additional_central_5yr"], delta=0.05)
        self.assertEqual(set(parts.index), {"urban", "suburban", "small_community", "rural"})


if __name__ == "__main__":
    unittest.main()

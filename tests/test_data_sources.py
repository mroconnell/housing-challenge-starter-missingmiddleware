"""Offline tests for the data-source sample tools (no network)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_data_dictionaries as build  # noqa: E402
import fetch_samples as fetch  # noqa: E402
from source_catalog import CATALOG  # noqa: E402


class TestFetchHelpers(unittest.TestCase):
    def test_bps_header_joins_two_rows(self):
        h1 = ["Survey", "FIPS", "Region", "Division", "State", "", "1-unit", "", "", "2-units"]
        h2 = ["Date", "State", "Code", "Code", "Name", "Bldgs", "Units", "Value", "Bldgs", "Units", "Value"]
        hdr = fetch.bps_header(h1, h2)
        self.assertEqual(hdr[:5], ["Survey Date", "FIPS State", "Region Code", "Division Code", "State Name"])
        self.assertEqual(hdr[5:8], ["1-unit Bldgs", "1-unit Units", "1-unit Value"])
        self.assertEqual(hdr[8:11], ["2-units Bldgs", "2-units Units", "2-units Value"])

    def test_redact_owner_fields(self):
        rows = [{"Owner": "JANE DOE", "OWNERNME1": "X", "Mailing_Address": "1 Main", "ownerType": "County", "homeowner": "N", "Zone": "R1"}]
        out = fetch.redact(rows)[0]
        self.assertEqual(out["Owner"], "[redacted]")
        self.assertEqual(out["OWNERNME1"], "[redacted]")
        self.assertEqual(out["Mailing_Address"], "[redacted]")
        self.assertEqual(out["ownerType"], "County")
        self.assertEqual(out["homeowner"], "N")
        self.assertEqual(out["Zone"], "R1")

    def test_quadkey(self):
        self.assertEqual(fetch._quadkey(40.7608, -111.8910, 9), "023100000")


class TestCatalog(unittest.TestCase):
    def test_every_fetcher_has_catalog_entry(self):
        self.assertEqual(set(fetch.SOURCES), set(CATALOG))

    def test_catalog_entries_complete(self):
        for sid, info in CATALOG.items():
            for key in ("title", "group", "what", "geography", "access", "caveats"):
                self.assertTrue(info.get(key), f"{sid} missing {key}")

    def test_committed_samples_are_small(self):
        for p in (ROOT / "data" / "sample").glob("*.csv"):
            self.assertLess(p.stat().st_size, 50_000, p.name)

    def test_committed_samples_have_no_owner_names(self):
        for p in (ROOT / "data" / "sample").glob("*.csv"):
            rows = list(build.csv.DictReader(p.open(encoding="utf-8")))
            for r in rows:
                for k, v in r.items():
                    if fetch.PII_FIELDS.search(k or "") and not fetch.PII_KEEP.match(k) and v:
                        self.assertEqual(v, "[redacted]", f"{p.name}:{k}")


class TestBuilder(unittest.TestCase):
    def test_pattern_meanings(self):
        self.assertIn("building permits", build.pattern_meaning("hcd_apr", "BP_LOW_INCOME_DR"))
        self.assertIn("deed restricted", build.pattern_meaning("hcd_apr", "BP_LOW_INCOME_DR"))
        self.assertIn("Reported only", build.pattern_meaning("census_bps", "2-units rep Units"))
        self.assertIn("Location quotient", build.pattern_meaning("bls_qcew", "lq_annual_avg_emplvl"))

    def test_sample_table_escapes_pipes(self):
        md = build.sample_table([{"a": "x|y"}])
        self.assertIn("x\\|y", md)


if __name__ == "__main__":
    unittest.main()

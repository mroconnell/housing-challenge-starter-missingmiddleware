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
        rows = [{"Owner": "JANE DOE", "NAME1": "JOHN DOE", "CARE_OF": "Y", "NAME": "Utah", "OWNERNME1": "X", "Mailing_Address": "1 Main", "ownerType": "County", "homeowner": "N", "Zone": "R1"}]
        out = fetch.redact(rows)[0]
        self.assertEqual(out["Owner"], "[redacted]")
        self.assertEqual(out["OWNERNME1"], "[redacted]")
        self.assertEqual(out["NAME1"], "[redacted]")
        self.assertEqual(out["CARE_OF"], "[redacted]")
        self.assertEqual(out["NAME"], "Utah")
        self.assertEqual(out["Mailing_Address"], "[redacted]")
        self.assertEqual(out["ownerType"], "County")
        self.assertEqual(out["homeowner"], "N")
        self.assertEqual(out["Zone"], "R1")

    def test_esri_to_geojson(self):
        self.assertEqual(fetch._esri_to_geojson({"x": 1, "y": 2}), {"type": "Point", "coordinates": [1, 2]})
        poly = fetch._esri_to_geojson({"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]})
        self.assertEqual(poly["type"], "Polygon")
        self.assertEqual(fetch._count_vertices(poly["coordinates"]), 4)

    def test_xlsx_rows(self):
        import io
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("xl/sharedStrings.xml", '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Wisconsin</t></si></sst>')
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                       '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="C1"><v>2020</v></c></row></sheetData></worksheet>')
        self.assertEqual(fetch.xlsx_rows(buf.getvalue()), [["Wisconsin", "", "2020"]])
        self.assertEqual(fetch._col_letter(fetch._col_index("AB")), "AB")

    def test_dbf_rows(self):
        import struct
        fields = [(b"GEOID", b"C", 10), (b"NAME", b"C", 8)]
        hlen = 32 + 32 * len(fields) + 1
        rlen = 1 + sum(f[2] for f in fields)
        head = struct.pack("<BBBBIHH", 3, 124, 1, 1, 1, hlen, rlen) + b"\0" * 20
        for name, t, n in fields:
            head += name.ljust(11, b"\0") + t + b"\0" * 4 + bytes([n, 0]) + b"\0" * 14
        blob = head + b"\r" + b" " + b"5502548000" + b"Madison " + b"\x1a"
        rows, flds, nrec = fetch.dbf_rows(blob, 5)
        self.assertEqual(nrec, 1)
        self.assertEqual(rows, [{"GEOID": "5502548000", "NAME": "Madison"}])
        self.assertEqual([f["name"] for f in flds], ["GEOID", "NAME"])

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


    def test_geo_samples_small_and_redacted(self):
        for p in (ROOT / "data" / "sample" / "geo").glob("*.geojson"):
            self.assertLess(p.stat().st_size, 200_000, p.name)
            for f in json.loads(p.read_text())["features"]:
                for k, v in (f.get("properties") or {}).items():
                    if fetch.PII_FIELDS.search(k) and not fetch.PII_KEEP.match(k) and v not in (None, ""):
                        self.assertEqual(v, "[redacted]", f"{p.name}:{k}")


class TestBuilder(unittest.TestCase):
    def test_pattern_meanings(self):
        self.assertIn("building permits", build.pattern_meaning("hcd_apr", "BP_LOW_INCOME_DR"))
        self.assertIn("deed restricted", build.pattern_meaning("hcd_apr", "BP_LOW_INCOME_DR"))
        self.assertIn("Reported only", build.pattern_meaning("census_bps", "2-units rep Units"))
        self.assertIn("Location quotient", build.pattern_meaning("bls_qcew", "lq_annual_avg_emplvl"))

    def test_pasda_field_comparison(self):
        meta = {"counties": {
            "AdamsCounty": {"layer_name": "Parcels", "record_count": 10, "field_names": ["OBJECTID", "PIN", "SITUS_ADDR", "ACRES"]},
            "ErieCounty": {"error": "no parcel layer"},
        }}
        md = build.extras("pa_pasda_parcels", meta)
        self.assertIn("| AdamsCounty | Parcels | 10 | 4 | `PIN` | `SITUS_ADDR` | none | none | `ACRES` |", md)
        self.assertIn("ErieCounty | not sampled: no parcel layer", md)

    def test_sample_table_hides_blank_columns(self):
        md = build.sample_table([{"a": "1", "b": ""}, {"a": "2", "b": ""}])
        self.assertIn("`a`", md)
        self.assertNotIn("`b`", md)

    def test_crs_label(self):
        self.assertEqual(build.crs_label({"wkid": 102100, "latestWkid": 3857}), "EPSG:3857 (Esri 102100)")
        self.assertEqual(build.crs_label({"wkid": 2913, "latestWkid": 2913}), "EPSG:2913")
        self.assertEqual(build.crs_label(None), "not stated")

    def test_sample_table_escapes_pipes(self):
        md = build.sample_table([{"a": "x|y"}])
        self.assertIn("x\\|y", md)


if __name__ == "__main__":
    unittest.main()

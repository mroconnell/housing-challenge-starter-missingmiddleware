"""Committed samples and data dictionaries must not carry house numbers or full parcel ids.

Project rule (docs/DATA_COMPLIANCE.md, fix F1): committed files keep ZIP, city, county and street
name, but drop house numbers, unit numbers and owner names; parcel numbers are masked. This scans
every file in data/sample/ and docs/data-sources/ as text, and checks id-like columns directly.
Offline; no network.
"""
import csv
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_samples as fetch  # noqa: E402

SCAN_DIRS = [ROOT / "data" / "sample", ROOT / "docs" / "data-sources"]
SCAN_SUFFIXES = {".csv", ".json", ".geojson", ".md"}

_SUFFIX = (r"(?:ST|STREET|AVE|AVENUE|AV|RD|ROAD|DR|DRIVE|LN|LANE|CT|COURT|CIR|CIRCLE|WAY|BLVD|BOULEVARD|"
           r"PL|PLACE|PKWY|PARKWAY|TRL|TRAIL|TER|TERRACE|HWY|HIGHWAY)")
# "1201 Prune Ave", "7813 NW 146TH TER", "236-238 Palm Ave" (same line only)
HOUSE_STREET = re.compile(
    r"(?<![\w.$#*-])\d{1,6}[A-Z]?(?:-\d{1,6})?[ \t]+(?:[NSEW]{1,2}\.?[ \t]+)?(?:[A-Za-z0-9'.]+[ \t]+){0,3}?"
    + _SUFFIX + r"\b", re.I)
# Utah grid addresses: "2121 N 8800 W"
GRID_ADDRESS = re.compile(r"(?<![\w.-])\d{1,6}[ \t]+[NSEW][ \t]+\d{1,5}[ \t]+[NSEW]\b")
# Wisconsin grid house numbers: "N123W456"
WI_GRID_NUMBER = re.compile(r"\b[NSEW]\d{1,4}[NSEW]\d{1,5}\b")
# Formatted parcel ids: "212-06-095", "25/022/000019", "104001-252-010-000", "40F03-0022M--000"
FORMATTED_ID = re.compile(r"(?<![\w*/.-])[0-9][0-9A-Z]{0,5}(?:-{1,2}[0-9A-Z]{1,6}|/[0-9A-Z]{1,6}){2,}(?![\w*/-])")
# Letter-in-the-middle ids: "1N117AA08200", "0102P00193000000". Not Google plus codes ("7C852FGV+VJFW").
ALNUM_ID = re.compile(r"(?<![\w*])\d{1,5}[A-Z]{1,3}\d{3,}[0-9A-Z]*(?![\w*+])")
DATE = re.compile(r"^(?:\d{4}-\d{1,2}-\d{1,2}(?:T\d+)?|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}/\d{1,2}/\d{1,2})$")
# Strings the patterns catch that are not addresses or ids, with the reason.
ALLOWED = {
    "5 Acre Pl": "ut_parcels SUBDIV_NAME 'Midland 5 Acre Pl' is a subdivision name, not an address",
}

# Columns that hold a parcel, account or record id. Values must be empty, digit-free or masked.
ID_COLUMN = re.compile(
    r"^(?:apn|prior_apn|pin|tmk|tmk_txt|cty_tmk|tlid|primaccnum|altaccnum|ortaxlot|parcel|parcel_?id|parcel_num|"
    r"parcelid|stateid|taxparcelid|xrefparcel|parcel_raw|parcel_key|propid|taxidnum|oldtaxidnu|mapblocklo|defque|"
    r"account|cama_link|link_1|nh_gis_id|pid|displayid|u_id|ptm_id|vgin_qpid|serial_num|jurs_tracking_id)$", re.I)
MASKED = re.compile(r"^.{0,2}\*\*\*$")


def _digits(s):
    return sum(c.isdigit() for c in s)


def scan_text(text):
    """Return address-like and parcel-id-like strings found in text."""
    hits = [m.group(0) for rx in (HOUSE_STREET, GRID_ADDRESS, WI_GRID_NUMBER) for m in rx.finditer(text)]
    for m in FORMATTED_ID.finditer(text):
        s = m.group(0)
        if _digits(s) >= 7 and not DATE.match(s):
            hits.append(s)
    hits += [m.group(0) for m in ALNUM_ID.finditer(text) if len(m.group(0)) >= 8]
    return [h for h in hits if h not in ALLOWED]


def scanned_files():
    for d in SCAN_DIRS:
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix in SCAN_SUFFIXES:
                yield p


def _records(p):
    """(column, value) pairs from a CSV, GeoJSON properties, or record lists in a .meta.json."""
    if p.suffix == ".csv":
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                yield from r.items()
    elif p.suffix == ".geojson":
        for feat in json.loads(p.read_text())["features"]:
            yield from (feat.get("properties") or {}).items()
    elif p.name.endswith(".meta.json"):
        for t in (json.loads(p.read_text()).get("tables") or {}).values():
            for r in (t.get("sample_rows") or []) if isinstance(t, dict) else []:
                yield from r.items()


class TestScanner(unittest.TestCase):
    def test_finds_addresses_and_ids(self):
        for s in ("1201 Prune Ave", "7813 NW 146TH TER", "236-238 Palm Ave", "2121 N 8800 W", "N123W456",
                  "212-06-095", "25/022/000019", "104001-252-010-000", "1N117AA08200", "0102P00193000000"):
            self.assertTrue(scan_text(f"x {s} y"), s)

    def test_ignores_masked_and_street_only(self):
        for s in ("Prune Ave", "NW 146TH TER", "N 8800 W", "13TH AVE", "21***", "10/1/2014", "2026-10-24",
                  "B25024", "[###] Main St", "2026-10-24T05:28:36", "7C852FGV+VJFW", "2 car garage", "MANUFACTURED DWELLING - 2017 SKYLINE"):
            self.assertEqual(scan_text(f"x {s} y"), [], s)


class TestCommittedSamplesPrivacy(unittest.TestCase):
    def test_no_house_numbers_or_parcel_ids_in_text(self):
        found = {}
        for p in scanned_files():
            hits = scan_text(p.read_text(encoding="utf-8", errors="ignore"))
            if hits:
                found[str(p.relative_to(ROOT))] = sorted(set(hits))[:5]
        self.assertEqual(found, {}, "house-number addresses or parcel ids in committed files")

    def test_id_columns_are_masked(self):
        bad = []
        for p in scanned_files():
            if p.suffix not in {".csv", ".geojson"} and not p.name.endswith(".meta.json"):
                continue
            for k, v in _records(p):
                s = "" if v is None else str(v).strip()
                if k and ID_COLUMN.match(k) and re.search(r"\d", s) and not MASKED.match(s):
                    bad.append(f"{p.name}:{k}={s}")
        self.assertEqual(bad, [])

    def test_record_coordinates_are_rounded(self):
        coord = re.compile(r"^(?:lat|latitude|lon|long|longitude)$", re.I)
        for sid in fetch.ADDRESS_REDACTION:
            p = ROOT / "data" / "sample" / f"{sid}.csv"
            if not p.exists():
                continue
            for k, v in _records(p):
                if coord.match(k or "") and v:
                    self.assertLessEqual(len(str(v).split(".")[-1]), 2, f"{sid}:{k}={v}")

    def test_parcel_geometry_is_coarsened(self):
        for sid in fetch.GEO_COARSEN:
            p = ROOT / "data" / "sample" / "geo" / f"{sid}.geojson"
            if not p.exists():
                continue
            for feat in json.loads(p.read_text())["features"]:
                g = feat["geometry"]
                self.assertEqual(g["type"], "Polygon", sid)
                ring = g["coordinates"][0]
                self.assertEqual(len(ring), 5, sid)
                for x, y in ring:
                    self.assertEqual((round(x, 2), round(y, 2)), (x, y), sid)

    def test_remask_is_idempotent(self):
        rows = [{"apn": "212-06-095", "site_address": "7480 E CHRISTMAS CHOLLA DR", "OBJECTID": "5"}]
        once = fetch.redact_locations("az_azgeo", rows)
        self.assertEqual(once, [{"apn": "21***", "site_address": "E CHRISTMAS CHOLLA DR", "OBJECTID": ""}])
        self.assertEqual(fetch.redact_locations("az_azgeo", once), once)
        box = fetch.coarse_box({"type": "Polygon", "coordinates": [[[-89.293, 43.096], [-89.294, 43.097], [-89.293, 43.096]]]})
        self.assertEqual(box["coordinates"][0][0], [-89.3, 43.09])
        self.assertEqual(fetch.coarse_box(box), box)


if __name__ == "__main__":
    unittest.main()

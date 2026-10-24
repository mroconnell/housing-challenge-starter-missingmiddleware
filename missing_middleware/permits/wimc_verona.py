"""Verona, WI (city, Dane Co.) adapter: annual "Construction Report" PDFs.

Source: https://www.veronawi.gov/518/Construction-Reports - one Excel-exported PDF per
calendar year, rows grouped by permit type ("Group: Addition or Alteration - UDC", ...).
Columns differ by year:
  2022, 2025: permit #, permit (issue) date, 12-digit parcel #, address, number of units,
              project type, permit type, description, suite, finished sq ft, cost
  2023:       permit #, date, permit type, description, occupancy, cost, fees
              (no parcel, no address)
  2024:       date, permit type, project type, cost, occupancy, fees
              (NO permit #, NO description, NO parcel/address) - weak year.
No owner/applicant/contractor columns are present in any year.

Parsing uses `pdftotext -bbox` word coordinates and fixed column x-bounds per file
(Excel exports keep column positions constant across pages).
"""
from __future__ import annotations

import re
import subprocess
from html import unescape
from pathlib import Path

import numpy as np
import pandas as pd

from . import classify
from . import fetch_util as fu

META = {
    "slug": "verona",
    "place": "Verona city",
    "geoids": ["5502582600"],
    "source_url": "https://www.veronawi.gov/518/Construction-Reports",
    "source_desc": "annual Construction Report PDFs (all permits, grouped by permit type)",
    "stage": "issued",
    "license": "public record (no stated licence)",
    "method": ("text rule (classify.text_class, SF_TO_TWO_RE) on the permit description plus a "
               "review of every Duplex-group, 'Two Family' occupancy, kitchen/apartment/in-law record; "
               "2024 has no descriptions so only permit type + occupancy can be read."),
}

BASE = "https://www.veronawi.gov/DocumentCenter/View/"
FILES = {2022: "4305", 2023: "4690", 2024: "5148", 2025: "6052"}

# column name -> left x bound (points); a word belongs to the last column whose bound <= its xMin
COLS = {
    2022: [("permit_id", 0), ("date", 100), ("parcel_id", 174), ("address", 236), ("units_raw", 338),
           ("project_type", 354), ("permit_type", 408), ("description", 476), ("suite", 552),
           ("sqft", 600), ("cost", 670)],
    2023: [("permit_id", 0), ("date", 95), ("permit_type", 155), ("description", 206),
           ("occupancy", 286), ("cost", 365), ("fees", 500)],
    2024: [("date", 0), ("permit_type", 140), ("cost", 245), ("occupancy", 322), ("fees", 395)],
    2025: [("permit_id", 0), ("date", 100), ("parcel_id", 170), ("address", 246), ("units_raw", 352),
           ("permit_type", 368), ("description", 445), ("suite", 522), ("sqft", 560), ("cost", 650)],
}
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/20\d\d$")
WORD_RE = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')


def fetch(raw_dir: Path, log=print) -> dict:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    old = {e["file"]: e for e in fu.read_manifest(man_path).get("files", [])}
    entries = []
    for year, doc in FILES.items():
        name = f"construction_report_{year}.pdf"
        path, url = raw_dir / name, BASE + doc
        if path.exists() and name in old:
            entries.append(old[name])
            continue
        log(f"verona: GET {url}")
        data = fu.get(url)
        if not data.startswith(b"%PDF"):
            raise RuntimeError(f"not a PDF: {url}")
        path.write_bytes(data)
        entries.append({"file": name, "year": year, "url": url, "accessed": fu.now_iso(),
                        "sha256": fu.sha256_file(path), "bytes": len(data)})
    fu.write_manifest(man_path, entries, {"source": META["source_url"], "license": META["license"],
                                          "note": "City of Verona annual construction reports"})
    return fu.read_manifest(man_path)


def _words(pdf: Path) -> list[list[tuple]]:
    out = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True,
                         check=True).stdout
    pages = []
    for p in out.split("<page ")[1:]:
        pages.append([(float(a), float(b), float(c), unescape(t)) for a, b, c, _d, t in WORD_RE.findall(p)])
    return pages


def _lines(words: list[tuple], tol: float = 2.0) -> list[list[tuple]]:
    lines: list[list[tuple]] = []
    for w in sorted(words, key=lambda w: (w[1], w[0])):
        if lines and abs(lines[-1][0][1] - w[1]) <= tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(l, key=lambda w: w[0]) for l in lines]


def _col(x: float, cols) -> str:
    name = cols[0][0]
    for n, x0 in cols:
        if x >= x0:
            name = n
    return name


def parse_pdf(pdf: Path, year: int) -> list[dict]:
    cols = COLS[year]
    has_id = cols[0][0] == "permit_id"
    recs, group, cur = [], None, None
    for page in _words(pdf):
        for line in _lines(page):
            texts = [w[3] for w in line]
            if texts[0] == "Group:":
                group = " ".join(texts[1:]) or "(blank)"
                cur = None
                continue
            if texts[0] in ("Page:", "Permit") or "Total:" in texts or "Group" in texts[:2]:
                cur = None if texts[0] != "Permit" else cur
                continue
            first = {}
            for w in line:
                first.setdefault(_col(w[0], cols), w[3])
            is_start = DATE_RE.match(first.get("date", "")) and (
                not has_id or re.fullmatch(r"\d{4,6}", first.get("permit_id", "")))
            if is_start and group is not None:
                cur = {"group": group, "cells": {}, "n": len(recs)}
                recs.append(cur)
            if cur is None:
                continue
            for w in line:
                cur["cells"].setdefault(_col(w[0], cols), []).append(w[3])
    rows = []
    for r in recs:
        c = {k: v for k, v in r["cells"].items()}
        row = {"group": r["group"], "file_year": year}
        row["permit_id"] = c.get("permit_id", [f"{year}-row{r['n']:04d}"])[0] if has_id else f"{year}-row{r['n']:04d}"
        row["date"] = c.get("date", [None])[0]
        row["parcel_id"] = "".join(c.get("parcel_id", [])) or None
        addr = c.get("address", [])
        row["house_nbr"] = addr[0] if addr and re.fullmatch(r"\d+[A-Za-z]?", addr[0]) else None
        row["street"] = " ".join(addr[1:] if row["house_nbr"] else addr).upper() or None
        row["description"] = " ".join(c.get("description", [])) or None
        row["occupancy"] = " ".join(c.get("occupancy", [])) or None
        row["project_type"] = " ".join(c.get("project_type", [])) or None
        u = c.get("units_raw", [])
        row["units_raw"] = float(u[0]) if u and re.fullmatch(r"\d+", u[0]) else np.nan
        rows.append(row)
    return rows


def load(raw_dir: Path) -> pd.DataFrame:
    raw_dir = Path(raw_dir)
    rows = []
    for year in FILES:
        rows += parse_pdf(raw_dir / f"construction_report_{year}.pdf", year)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")
    # the report period (file year) is the reference year; the 2022 report lists 14 permits whose
    # "Permit Date" is in late 2021 (the report window evidently uses another date)
    df["year"] = df["file_year"].astype(int)
    df["permit_type"] = df["group"]
    df["permit_id"] = df["permit_id"].astype(str)
    cols = ["permit_id", "date", "year", "permit_type", "description", "units_raw", "parcel_id",
            "street", "house_nbr", "occupancy", "project_type", "file_year"]
    return df[cols].reset_index(drop=True)


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y in range(2022, 2026):
        d = df[df.year == y]
        months = d.loc[d.date.dt.year == y, "date"].dt.month.nunique()
        note = "annual report 1/1-12/31"
        if y == 2023:
            note += "; no parcel/address columns"
        if y == 2024:
            note += "; NO permit #, description, parcel or address (type, cost, occupancy only)"
        out.append({"year": y, "months_with_records": months, "records": len(d),
                    "complete": bool(months == 12), "note": note})
    return pd.DataFrame(out)


KITCHEN_RE = re.compile(r"kitchen|apartment|\bapt\b|in[- ]?law|living\s+(?:quarters|unit|space)|efficiency"
                        r"|second\s+(?:unit|dwelling)|dwelling\s+unit|two[- ]family|duplex|\bADU\b", re.I)

JUDGMENTS: dict[str, dict] = {
    # manual review of every 2022-2025 candidate (house numbers redacted)
    "18812": {"counts": False, "component": "adu_conversion", "units": 1,
              "why": "unconfirmed: 2025 UDC alteration 'Mother In-Law Suite in Basement' (xxx Breckenridge Rd), "
                     "0 finished sq ft and $1,000 cost; no kitchen stated, so not counted (upper bound 1)"},
    "2024-row0111": {"counts": False, "component": "sf_to_duplex", "units": 1,
                     "why": "unconfirmed: 2024 UDC alteration, occupancy 'Two Family', $595,000; 2024 report has "
                            "no description/address, cannot tell conversion from remodel of an existing duplex"},
    "2024-row0114": {"counts": False, "component": "sf_to_duplex", "units": 1,
                     "why": "unconfirmed: 2024 UDC alteration, occupancy 'Two Family', $20,000; no description in "
                            "2024 report (most likely work inside an existing two-family)"},
    "16319": {"counts": False, "component": None,
              "why": "2023 'Basement finish - living & bathroom' in a Two Family occupancy: finish of an existing "
                     "duplex unit, no new unit or kitchen"},
    "15700": {"counts": False, "component": None,
              "why": "2022 plumbing-only 'Basement and Kitchenette Remodel': remodel of existing space, no unit"},
    "16012": {"counts": False, "component": None,
              "why": "2022 'Kitchen & adding bathroom in basement': kitchen remodel plus bathroom, no unit"},
    "18620": {"counts": False, "component": None,
              "why": "2025 whole-house renovation (basement finish, kitchen and bath updates), no unit"},
    "18587": {"counts": False, "component": None,
              "why": "2025 'Kitchen remodel and adding bathroom in basement', no unit"},
    "18518": {"counts": False, "component": None,
              "why": "2025 room addition above garage with bedroom/bath/closet, no kitchen: not a unit"},
    "18105": {"counts": False, "component": None,
              "why": "2025 garage space closed into living/storage space, no kitchen: not a unit"},
}
UNCONFIRMED_COMPONENT = {k: v["component"] for k, v in JUDGMENTS.items() if v["why"].startswith("unconfirmed")}


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ("description", "occupancy", "permit_type"):
        df[col] = df[col].astype(object).where(df[col].notna(), None)
    comp, units, reason, cand = [], [], [], []
    for r in df.itertuples():
        d = r.description or ""
        c, note = classify.text_class(d)
        rs, cd = "", False
        if c == "adu_legalization":
            rs, cd, c = "legalization of existing unit (excluded)", True, None
        elif c:
            rs, cd = f"ADU text ({note})", True
        elif classify.SF_TO_TWO_RE.search(d):
            c, rs, cd = "sf_to_duplex", "text: single-family to two-family", True
        else:
            c = None
            if note:
                rs, cd = note, True
            if r.permit_type == "Duplex Dwelling":
                rs, cd = "new duplex building (excluded: not a second home on an existing SF lot)", True
            elif (r.occupancy or "").lower().startswith("two family") and "UDC" in (r.permit_type or ""):
                rs, cd = "alteration with occupancy 'Two Family' (no description in 2024; unconfirmed)", True
            elif (r.permit_type or "") in ("Five and More Units", "Three and Four Units", "Signs") \
                    or "ICC" in (r.permit_type or "") or "Commercial" in (r.permit_type or ""):
                pass
            elif KITCHEN_RE.search(d) and re.search(r"basement|lower|second floor|in[- ]?law|apartment|unit", d, re.I):
                rs, cd = "kitchen/apartment wording in alteration (reviewed)", True
        comp.append(c)
        units.append(1 if c else 0)
        reason.append(rs)
        cand.append(cd)
    df["component"], df["units"], df["reason"], df["candidate"] = comp, units, reason, cand
    for pid, j in JUDGMENTS.items():
        m = df.permit_id == pid
        if not m.any():
            continue
        df.loc[m, "candidate"] = True
        df.loc[m, "reason"] = "judgment: " + j["why"]
        if j["counts"]:
            df.loc[m, "component"] = j["component"]
            df.loc[m, "units"] = j.get("units", 1)
        else:
            df.loc[m, "component"] = None
            df.loc[m, "units"] = 0
    df["units"] = df["units"].astype(int)
    return df
